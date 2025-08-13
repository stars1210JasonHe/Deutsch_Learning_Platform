from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.translate import (
    TranslateWordRequest, TranslateWordResponse,
    TranslateSentenceRequest, TranslateSentenceResponse
)
from pydantic import BaseModel
from app.services.cache_service import CacheService
from app.services.openai_service import OpenAIService

router = APIRouter()
openai_service = OpenAIService()


class SelectSuggestionRequest(BaseModel):
    selected_word: str


@router.post("/word", response_model=dict)
async def translate_word(
    request: TranslateWordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Translate and analyze a single word (uses vocabulary database)"""
    
    query_text = request.input.strip()
    
    # 使用统一词库服务
    from app.services.vocabulary_service import VocabularyService
    vocabulary_service = VocabularyService()
    
    result = await vocabulary_service.get_or_create_word(
        db=db,
        lemma=query_text,
        user=current_user
    )
    
    return result


@router.post("/sentence", response_model=TranslateSentenceResponse)
async def translate_sentence(
    request: TranslateSentenceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Translate sentence and provide word-by-word gloss"""
    
    query_text = request.input.strip()
    
    # Check cache first
    cached_response = await CacheService.get_cached_response(
        db, query_text, "sentence_translation"
    )
    
    if cached_response:
        # Log search history
        cache_entry_id = await CacheService.cache_response(
            db, query_text, "sentence_translation", cached_response
        )
        await CacheService.log_search_history(
            db, current_user, query_text, "sentence_translation", cache_entry_id
        )
        
        return TranslateSentenceResponse(**cached_response, cached=True)
    
    # Get OpenAI translation
    translation = await openai_service.translate_sentence(query_text)
    
    response_data = {
        "original": query_text,
        "german": translation.get("german", ""),
        "gloss": translation.get("gloss", []),
        "cached": False
    }
    
    # Cache the response
    cache_id = await CacheService.cache_response(
        db, query_text, "sentence_translation", response_data
    )
    
    # Log search history
    await CacheService.log_search_history(
        db, current_user, query_text, "sentence_translation", cache_id
    )
    
    return TranslateSentenceResponse(**response_data)


@router.post("/word/select", response_model=dict)
async def select_suggested_word(
    request: SelectSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Select a suggested word and get its full analysis"""
    
    selected_word = request.selected_word.strip()
    
    # 使用统一词库服务分析选中的词汇
    from app.services.vocabulary_service import VocabularyService
    vocabulary_service = VocabularyService()
    
    result = await vocabulary_service.get_or_create_word(
        db=db,
        lemma=selected_word,
        user=current_user
    )
    
    return result