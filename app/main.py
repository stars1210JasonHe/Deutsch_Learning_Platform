from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.security_middleware import SecurityHeadersMiddleware, RateLimitMiddleware
from app.db.session import engine
from app.db.base import Base
from app.api import auth, words, translate, history, exam, srs, favorites, audio, chat, images, feedback

# Import all models to ensure they are registered with SQLAlchemy
from app.models import user, word, search, exam as exam_models, feedback as feedback_models

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vibe Deutsch API",
    description="OpenAI-powered German learning platform with smart caching",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS with specific, secure settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "accept",
        "accept-language", 
        "content-type",
        "authorization",
        "x-requested-with",
        "x-csrf-token"
    ],
    expose_headers=["x-csrf-token"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(words.router, prefix="/words", tags=["Words"])
app.include_router(translate.router, prefix="/translate", tags=["Translation"])
app.include_router(history.router, prefix="/search", tags=["Search History"])
app.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])

# Phase 2 routers
app.include_router(exam.router, tags=["Exam System"])
app.include_router(srs.router, tags=["Spaced Repetition"])

# Audio system
app.include_router(audio.router, tags=["Audio System"])

# Chat and image generation system
app.include_router(chat.router, prefix="/api", tags=["Chat System"])
app.include_router(images.router, prefix="/api", tags=["Image Generation"])

# Feedback system
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])


@app.get("/")
async def root():
    return {
        "message": "Vibe Deutsch API - OpenAI-powered German learning platform",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/debug/cors")
async def debug_cors():
    return {"allowed_hosts": settings.allowed_hosts}