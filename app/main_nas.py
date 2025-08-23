from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.db.session import engine
from app.db.base import Base
from app.api import auth, words, translate, history, exam, srs, favorites, audio, chat, images

# Import all models to ensure they are registered with SQLAlchemy
from app.models import user, word, search, exam as exam_models

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vibe Deutsch API",
    description="OpenAI-powered German learning platform with smart caching",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# Also include auth router with /api prefix for frontend compatibility
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication (API)"])
app.include_router(words.router, prefix="/words", tags=["Words"])
app.include_router(translate.router, prefix="/translate", tags=["Translation"])
# Also include translate router with /api prefix for frontend compatibility  
app.include_router(translate.router, prefix="/api/translate", tags=["Translation (API)"])
app.include_router(history.router, prefix="/search", tags=["Search History"])
# Also include search router with /api prefix for frontend compatibility
app.include_router(history.router, prefix="/api/search", tags=["Search History (API)"])
app.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])

# Phase 2 routers
app.include_router(exam.router, tags=["Exam System"])
app.include_router(srs.router, tags=["Spaced Repetition"])

# Audio system
app.include_router(audio.router, tags=["Audio System"])

# Chat and image generation system
app.include_router(chat.router, prefix="/api", tags=["Chat System"])
app.include_router(images.router, prefix="/api", tags=["Image Generation"])

# Serve static frontend files (must be last)
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/debug/cors")
async def debug_cors():
    return {"allowed_hosts": settings.allowed_hosts}