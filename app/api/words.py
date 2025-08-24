from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.schemas.word import WordSearchResponse, TranslateSearchRequest, TranslateSearchResponse, TranslationSelectionRequest, TranslationOption
from app.services.vocabulary_service import VocabularyService
from app.services.openai_service import OpenAIService

router = APIRouter()
vocabulary_service = VocabularyService()
openai_service = OpenAIService()


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


@router.post("/translate-search", response_model=TranslateSearchResponse)
async def translate_search(
    request: TranslateSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Translate word to German and search vocabulary database"""
    
    try:
        # Step 1: Detect language
        language_result = await openai_service.detect_language(request.text)
        
        detected_lang = language_result.get("detected_language", "unknown")
        detected_name = language_result.get("language_name", "Unknown")
        confidence = language_result.get("confidence", 0.0)
        is_german = language_result.get("is_german", False)
        
        # Check if language detection failed
        if detected_lang == "unknown" or confidence < 0.5:
            return TranslateSearchResponse(
                original_text=request.text,
                detected_language=detected_lang,
                detected_language_name=detected_name,
                confidence=confidence,
                error_message="Unable to detect language. Please try a different word or switch to normal search mode."
            )
        
        # Step 2: Handle German input (skip translation)
        if is_german or detected_lang == "de":
            search_result = await vocabulary_service.search_words(
                db=db,
                query=request.text,
                user=current_user,
                skip=0,
                limit=10
            )
            
            return TranslateSearchResponse(
                original_text=request.text,
                detected_language="de",
                detected_language_name="German",
                confidence=confidence,
                german_translations=[TranslationOption(
                    german_word=request.text,
                    context="already German",
                    pos="detected"
                )],
                search_results=search_result,
                selected_translation=request.text
            )
        
        # Step 3: Translate to German
        translation_result = await openai_service.translate_to_german(
            request.text, detected_lang
        )
        
        translations = translation_result.get("translations", [])
        
        # Check if no translations found
        if not translations:
            return TranslateSearchResponse(
                original_text=request.text,
                detected_language=detected_lang,
                detected_language_name=detected_name,
                confidence=confidence,
                error_message="No German translation found for this word. Please try a synonym or check spelling."
            )
        
        # Convert to TranslationOption objects
        german_options = [
            TranslationOption(
                german_word=trans["german_word"],
                context=trans.get("context", ""),
                pos=trans.get("pos", "")
            )
            for trans in translations
        ]
        
        is_ambiguous = len(german_options) > 1
        
        # Step 4: If not ambiguous, search immediately
        search_results = None
        selected_translation = None
        
        if not is_ambiguous:
            selected_translation = german_options[0].german_word
            search_results = await vocabulary_service.search_words(
                db=db,
                query=selected_translation,
                user=current_user,
                skip=0,
                limit=10
            )
        
        return TranslateSearchResponse(
            original_text=request.text,
            detected_language=detected_lang,
            detected_language_name=detected_name,
            confidence=confidence,
            german_translations=german_options,
            is_ambiguous=is_ambiguous,
            search_results=search_results,
            selected_translation=selected_translation
        )
        
    except Exception as e:
        return TranslateSearchResponse(
            original_text=request.text,
            detected_language="error",
            detected_language_name="Error",
            confidence=0.0,
            error_message=f"Translation failed: {str(e)}"
        )


@router.post("/translate-search-select", response_model=TranslateSearchResponse)
async def translate_search_select(
    request: TranslationSelectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search for selected German translation"""
    
    try:
        # For selected translations, try exact match first
        search_results = await vocabulary_service.get_or_create_word(
            db=db,
            lemma=request.selected_german_word,
            user=current_user
        )
        
        # If exact match found, format as search results
        if search_results and search_results.get('found', False):
            search_results = {
                "results": [search_results],
                "total": 1,
                "cached": search_results.get('cached', False)
            }
        else:
            # Fall back to fuzzy search if no exact match
            search_results = await vocabulary_service.search_words(
                db=db,
                query=request.selected_german_word,
                user=current_user,
                skip=0,
                limit=10
            )
        
        return TranslateSearchResponse(
            original_text=request.original_text,
            detected_language="selection",
            detected_language_name="User Selection",
            confidence=1.0,
            german_translations=[TranslationOption(
                german_word=request.selected_german_word,
                context="user selected",
                pos="selected"
            )],
            search_results=search_results,
            selected_translation=request.selected_german_word
        )
        
    except Exception as e:
        return TranslateSearchResponse(
            original_text=request.original_text,
            detected_language="error",
            detected_language_name="Error",
            confidence=0.0,
            error_message=f"Search failed: {str(e)}"
        )