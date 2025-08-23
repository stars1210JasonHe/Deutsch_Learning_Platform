from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.core.security import create_access_token, create_refresh_token, verify_refresh_token, get_password_hash, verify_password
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, Token, RefreshTokenRequest, User as UserSchema

router = APIRouter()


@router.post("/register", response_model=UserSchema)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    # Find user
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token with remember me support
    access_token = create_access_token(
        subject=user.id, 
        remember_me=login_data.remember_me
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(subject=user.id)
    
    # Calculate expires_in based on remember_me
    expires_in = (settings.remember_me_expire_days * 24 * 60) if login_data.remember_me else settings.access_token_expire_minutes
    
    # Set httpOnly cookies for secure token storage
    max_age_seconds = expires_in * 60  # Convert minutes to seconds
    
    # Set access token cookie (environment-aware security)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=max_age_seconds,
        httponly=True,
        secure=settings.https_only,  # Only require HTTPS when configured
        samesite="lax"  # CSRF protection
    )
    
    # Set refresh token cookie with longer expiry
    refresh_max_age = settings.refresh_token_expire_days * 24 * 60 * 60  # Days to seconds
    response.set_cookie(
        key="refresh_token", 
        value=refresh_token,
        max_age=refresh_max_age,
        httponly=True,
        secure=settings.https_only,  # Only require HTTPS when configured
        samesite="lax"
    )
    
    return {
        "access_token": access_token,  # Still return for backwards compatibility
        "refresh_token": refresh_token,
        "token_type": "bearer", 
        "expires_in": expires_in,
        "message": "Tokens set in secure cookies"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        # Verify refresh token
        user_id = verify_refresh_token(refresh_data.refresh_token)
        
        # Find user
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new access token (standard duration)
        access_token = create_access_token(subject=user.id)
        
        # Create new refresh token
        refresh_token = create_refresh_token(subject=user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes
        }
        
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    return current_user


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing secure cookies."""
    # Clear access token cookie (match login settings)
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.https_only,
        samesite="lax"
    )
    
    # Clear refresh token cookie
    response.delete_cookie(
        key="refresh_token", 
        httponly=True,
        secure=settings.https_only,
        samesite="lax"
    )
    
    return {"message": "Successfully logged out"}