"""
SRS (Spaced Repetition System) API Endpoints - Phase 2
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.services.srs_service import SRSService

router = APIRouter(prefix="/srs", tags=["srs"])


# Pydantic models
class AddWordRequest(BaseModel):
    lemma_id: int
    initial_quality: Optional[int] = 3


class AddWordByLemmaRequest(BaseModel):
    lemma: str
    initial_quality: Optional[int] = 3


class ReviewCardRequest(BaseModel):
    card_id: int
    quality: int  # 0-5 scale (0=total blackout, 5=perfect recall)
    response_time_ms: Optional[int] = None


class StartSessionRequest(BaseModel):
    session_type: str = "srs_review"


class EndSessionRequest(BaseModel):
    session_id: int
    questions_answered: int = 0
    correct_answers: int = 0
    topics_covered: Optional[List[str]] = None
    words_practiced: Optional[List[int]] = None


# SRS review endpoints
@router.get("/due-cards")
async def get_due_cards(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get cards due for review"""
    
    srs_service = SRSService()
    
    due_cards = srs_service.get_due_cards(
        db=db,
        user=current_user,
        limit=limit
    )
    
    return {
        "cards": due_cards,
        "count": len(due_cards)
    }


@router.post("/review-card")
async def review_card(
    request: ReviewCardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit a card review"""
    
    if not 0 <= request.quality <= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quality must be between 0 and 5"
        )
    
    srs_service = SRSService()
    
    result = srs_service.review_card(
        db=db,
        user=current_user,
        card_id=request.card_id,
        quality=request.quality,
        response_time_ms=request.response_time_ms
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result


@router.post("/add-word")
async def add_word_to_srs(
    request: AddWordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a word to SRS deck"""
    
    srs_service = SRSService()
    
    result = srs_service.add_word_to_srs(
        db=db,
        user=current_user,
        lemma_id=request.lemma_id,
        initial_quality=request.initial_quality
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return result


@router.post("/add-word-by-lemma")
async def add_word_to_srs_by_lemma(
    request: AddWordByLemmaRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a word to SRS deck by lemma string"""
    
    from app.models.word import WordLemma
    
    # Find the word in the database by lemma
    word = db.query(WordLemma).filter(
        WordLemma.lemma.ilike(request.lemma)
    ).first()
    
    if not word:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Word '{request.lemma}' not found in vocabulary database"
        )
    
    srs_service = SRSService()
    
    result = srs_service.add_word_to_srs(
        db=db,
        user=current_user,
        lemma_id=word.id,
        initial_quality=request.initial_quality
    )
    
    if "error" in result:
        if "already exists" in result["error"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Word '{request.lemma}' already exists in your SRS deck"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
    
    return result


@router.get("/stats")
async def get_srs_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's SRS statistics"""
    
    srs_service = SRSService()
    
    stats = srs_service.get_srs_stats(db=db, user=current_user)
    
    return stats


# Learning session endpoints
@router.post("/session/start")
async def start_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a learning session"""
    
    srs_service = SRSService()
    
    session = srs_service.create_learning_session(
        db=db,
        user=current_user,
        session_type=request.session_type
    )
    
    return session


@router.post("/session/end")
async def end_session(
    request: EndSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """End a learning session"""
    
    srs_service = SRSService()
    
    result = srs_service.end_learning_session(
        db=db,
        session_id=request.session_id,
        questions_answered=request.questions_answered,
        correct_answers=request.correct_answers,
        topics_covered=request.topics_covered,
        words_practiced=request.words_practiced
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result["error"]
        )
    
    return result


# Progress tracking endpoints
@router.get("/progress")
async def get_user_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed user progress"""
    
    from app.models.exam import UserProgress
    
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id
    ).first()
    
    if not progress:
        # Create default progress record
        progress = UserProgress(user_id=current_user.id)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    return {
        "current_level": progress.current_level,
        "total_words_learned": progress.total_words_learned,
        "vocabulary_size": progress.vocabulary_size,
        "average_accuracy": round(progress.average_accuracy * 100, 1),
        "study_streak_days": progress.study_streak_days,
        "total_study_time_hours": progress.total_study_time_hours,
        "daily_goal_minutes": progress.daily_goal_minutes,
        "weekly_goal_cards": progress.weekly_goal_cards,
        "achievements_unlocked": progress.achievements_unlocked,
        "level_milestones": progress.level_milestones,
        "last_updated": progress.updated_at.isoformat() if progress.updated_at else None
    }


@router.post("/progress/update-goals")
async def update_learning_goals(
    daily_goal_minutes: Optional[int] = None,
    weekly_goal_cards: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user's learning goals"""
    
    from app.models.exam import UserProgress
    
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id
    ).first()
    
    if not progress:
        progress = UserProgress(user_id=current_user.id)
        db.add(progress)
    
    if daily_goal_minutes is not None:
        progress.daily_goal_minutes = max(1, daily_goal_minutes)
    
    if weekly_goal_cards is not None:
        progress.weekly_goal_cards = max(1, weekly_goal_cards)
    
    db.commit()
    
    return {
        "success": True,
        "daily_goal_minutes": progress.daily_goal_minutes,
        "weekly_goal_cards": progress.weekly_goal_cards
    }


@router.get("/dashboard")
async def get_learning_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive learning dashboard data"""
    
    srs_service = SRSService()
    
    # Get SRS stats
    srs_stats = srs_service.get_srs_stats(db=db, user=current_user)
    
    # Get recent learning sessions
    from app.models.exam import LearningSession
    from datetime import datetime, timedelta
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_sessions = db.query(LearningSession).filter(
        LearningSession.user_id == current_user.id,
        LearningSession.started_at >= week_ago
    ).order_by(LearningSession.started_at.desc()).limit(10).all()
    
    sessions_data = []
    for session in recent_sessions:
        sessions_data.append({
            "id": session.id,
            "type": session.session_type,
            "started_at": session.started_at.isoformat(),
            "duration_seconds": session.duration_seconds,
            "questions_answered": session.questions_answered,
            "correct_answers": session.correct_answers,
            "accuracy_percentage": session.accuracy_percentage
        })
    
    # Calculate weekly study time
    weekly_study_time = sum(
        session.duration_seconds or 0 for session in recent_sessions
    ) / 3600  # Convert to hours
    
    # Get user progress
    from app.models.exam import UserProgress
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id
    ).first()
    
    dashboard_data = {
        "srs_stats": srs_stats,
        "recent_sessions": sessions_data,
        "weekly_study_time_hours": round(weekly_study_time, 1),
        "progress": {
            "current_level": progress.current_level if progress else "A1",
            "vocabulary_size": progress.vocabulary_size if progress else 0,
            "average_accuracy": round(progress.average_accuracy * 100, 1) if progress else 0,
            "study_streak": progress.study_streak_days if progress else 0
        }
    }
    
    return dashboard_data


@router.delete("/card/{card_id}")
async def remove_card(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a card from SRS deck"""
    
    from app.models.exam import SRSCard
    
    card = db.query(SRSCard).filter(
        SRSCard.id == card_id,
        SRSCard.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Soft delete by setting inactive
    card.is_active = False
    db.commit()
    
    return {"success": True, "message": "Card removed from deck"}