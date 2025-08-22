from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.core.deps import get_current_active_user
from app.services.openai_service import OpenAIService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None

class WordChatRequest(BaseModel):
    word: str
    word_data: Dict[str, Any]
    message: str
    chat_history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    response: str
    usage_info: Optional[Dict[str, Any]] = None

@router.post("/word", response_model=ChatResponse)
async def chat_about_word(
    request: WordChatRequest,
    current_user: dict = Depends(get_current_active_user),
    openai_service: OpenAIService = Depends(OpenAIService)
):
    """
    Chat about a specific German word with context and educational focus.
    """
    try:
        # Prepare context about the word
        word_context = f"""
Word: {request.word}
Part of Speech: {request.word_data.get('pos', 'unknown')}
"""
        
        # Add meanings if available
        if request.word_data.get('gloss_en'):
            word_context += f"English meaning: {request.word_data['gloss_en']}\n"
        if request.word_data.get('gloss_zh'):
            word_context += f"Chinese meaning: {request.word_data['gloss_zh']}\n"
            
        # Add translations
        if request.word_data.get('translations_en'):
            word_context += f"English translations: {', '.join(request.word_data['translations_en'])}\n"
        if request.word_data.get('translations_zh'):
            word_context += f"Chinese translations: {', '.join(request.word_data['translations_zh'])}\n"
            
        # Add grammatical info
        if request.word_data.get('article'):
            word_context += f"Article: {request.word_data['article']}\n"
        if request.word_data.get('plural'):
            word_context += f"Plural: {request.word_data['plural']}\n"
            
        # Add verb properties
        if request.word_data.get('verb_props'):
            verb_props = request.word_data['verb_props']
            if verb_props.get('separable'):
                word_context += f"Separable verb: Yes\n"
            if verb_props.get('aux'):
                word_context += f"Auxiliary verb: {verb_props['aux']}\n"
                
        # Prepare system message
        system_message = f"""You are a friendly and knowledgeable assistant helping someone learn German. You are currently discussing the German word "{request.word}".

Word Information:
{word_context}

You should be helpful and answer any reasonable questions the user has. This includes:
- Grammar explanations and conjugations
- Word usage and examples
- Cultural context and background
- Related vocabulary and expressions
- Pronunciation guidance
- General questions about the word or related topics
- Comparisons with other languages
- Etymology and word origins
- Practical usage scenarios

Feel free to engage in natural conversation while being educational. Don't restrict yourself only to strict language learning - be conversational and helpful with any aspect related to the word or general questions. Always aim to be encouraging and provide useful information."""

        # Prepare conversation history
        messages = [{"role": "system", "content": system_message}]
        
        # Add chat history
        for msg in request.chat_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
            
        # Add current user message
        messages.append({
            "role": "user", 
            "content": request.message
        })

        # Get response from OpenAI
        try:
            response_data = await openai_service.chat_completion(
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )
            
            response_text = response_data.get('content', 'I apologize, but I encountered an error. Please try again.')
            usage_info = response_data.get('usage')
            
            return ChatResponse(
                response=response_text,
                usage_info=usage_info
            )
            
        except Exception as openai_error:
            logger.error(f"OpenAI API error in word chat: {openai_error}")
            return ChatResponse(
                response="I'm sorry, I'm having trouble responding right now. Please try again in a moment."
            )
            
    except Exception as e:
        logger.error(f"Error in word chat: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during chat")