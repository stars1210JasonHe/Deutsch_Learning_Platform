from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
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


class SelectWordChoiceRequest(BaseModel):
    lemma_id: int
    original_query: str


class WordEnhancementRequest(BaseModel):
    input: str
    force_enrich: bool = False


@router.post("/word", response_model=dict)
async def translate_word(
    request: TranslateWordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Translate and analyze a single word (uses enhanced vocabulary database)"""
    
    query_text = request.input.strip()
    
    # Normalize UTF-8 encoding to handle German umlauts properly
    import unicodedata
    query_text = unicodedata.normalize('NFC', query_text)
    
    try:
        # Safe logging with Unicode handling
        try:
            logging.debug(f"translate_word API called for query (normalized)")
            logging.debug(f"Input repr: {repr(query_text)}")
            logging.debug(f"User ID: {current_user.id}")
        except UnicodeEncodeError:
            logging.debug("translate_word API called for query with special characters")
        
        # 使用增强词库服务
        from app.services.enhanced_vocabulary_service import EnhancedVocabularyService
        vocabulary_service = EnhancedVocabularyService()
        logging.debug("Using EnhancedVocabularyService")
        logging.debug(f"Service type: {type(vocabulary_service)}")
        
        result = await vocabulary_service.get_or_create_word_enhanced(
            db=db,
            lemma=query_text,
            user=current_user,
            force_enrich=False
        )
        logging.debug(f"Result from enhanced service: found={result.get('found')}, multiple_choices={result.get('multiple_choices')}")
        logging.debug(f"Full result keys: {list(result.keys())}")
        
        return result
        
    except RuntimeError as e:
        logging.error("Word analysis failed: %s", str(e))
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logging.error("Unexpected error analyzing word: %s", str(e))
        logging.error("Full traceback: %s", error_trace)
        raise HTTPException(status_code=500, detail=f"Internal server error occurred during word analysis: {str(e)}")


@router.post("/word/enhanced", response_model=dict)
async def translate_word_enhanced(
    request: WordEnhancementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Enhanced word analysis with similarity scores, cross-language support, and multiple results"""
    
    query_text = request.input.strip()
    
    # Normalize UTF-8 encoding to handle German umlauts properly
    import unicodedata
    query_text = unicodedata.normalize('NFC', query_text)
    
    try:
        # 使用增强词库服务
        from app.services.enhanced_vocabulary_service import EnhancedVocabularyService
        vocabulary_service = EnhancedVocabularyService()
        
        result = await vocabulary_service.get_or_create_word_enhanced(
            db=db,
            lemma=query_text,
            user=current_user,
            force_enrich=request.force_enrich
        )
        
        return result
        
    except RuntimeError as e:
        logging.error(f"Enhanced word analysis failed for '{query_text}': {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error in enhanced analysis '{query_text}': {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred during enhanced word analysis")


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
    
    try:
        # Get OpenAI translation
        translation = await openai_service.translate_sentence(query_text)
    except RuntimeError as e:
        logging.error(f"Sentence translation failed for '{query_text}': {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error translating sentence '{query_text}': {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred during sentence translation")
    
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
    
    try:
        # 使用增强词库服务分析选中的词汇 - 保持与主搜索一致的格式
        from app.services.enhanced_vocabulary_service import EnhancedVocabularyService
        vocabulary_service = EnhancedVocabularyService()
        
        result = await vocabulary_service.get_or_create_word_enhanced(
            db=db,
            lemma=selected_word,
            user=current_user,
            force_enrich=False
        )
        
        return result
        
    except RuntimeError as e:
        logging.error(f"Selected word analysis failed for '{selected_word}': {str(e)}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logging.error(f"Unexpected error analyzing selected word '{selected_word}': {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred during word analysis")


@router.post("/word/choice", response_model=dict)
async def select_word_choice(
    request: SelectWordChoiceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Select a specific word choice from multiple POS results"""
    
    try:
        # Get the specific word by lemma_id and use Enhanced format for consistency
        from app.models.word import WordLemma
        from app.services.enhanced_vocabulary_service import EnhancedVocabularyService
        from sqlalchemy.orm import joinedload
        
        # Load word with all relationships for proper formatting
        word = db.query(WordLemma).options(
            joinedload(WordLemma.translations),
            joinedload(WordLemma.examples),
            joinedload(WordLemma.forms),
            joinedload(WordLemma.verb_props)
        ).filter(WordLemma.id == request.lemma_id).first()
        
        if not word:
            raise HTTPException(status_code=404, detail=f"Word with ID {request.lemma_id} not found")
        
        # Format the specific word using Enhanced format
        vocabulary_service = EnhancedVocabularyService()
        result = await vocabulary_service.format_database_word_enhanced(
            word=word,
            original_query=request.original_query
        )
        
        # Log search history
        await CacheService.log_search_history(
            db, current_user, request.original_query, "word_choice_selection", None
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error selecting word choice {request.lemma_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error occurred during word selection")