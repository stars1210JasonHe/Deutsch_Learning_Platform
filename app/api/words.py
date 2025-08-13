from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.word import WordSearchResponse
from app.services.vocabulary_service import VocabularyService

router = APIRouter()
vocabulary_service = VocabularyService()


@router.get("/", response_model=dict)
async def search_words(
    q: str = Query(..., description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search for words in vocabulary database"""
    
    result = await vocabulary_service.search_words(
        db=db,
        query=q,
        user=current_user,
        skip=skip,
        limit=limit
    )
    
    return result


@router.get("/{lemma}", response_model=dict)
async def get_word_details(
    lemma: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed word information (from database or OpenAI)"""
    
    result = await vocabulary_service.get_or_create_word(
        db=db,
        lemma=lemma,
        user=current_user
    )
    
    return result