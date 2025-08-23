from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.core.deps import get_current_active_user
from app.services.openai_service import OpenAIService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["images"])

class ImageGenerationRequest(BaseModel):
    word: str
    word_data: Dict[str, Any]
    model: str = "dall-e-2"  # dall-e-2 or dall-e-3
    size: str = "512x512"    # 256x256, 512x512, 1024x1024
    style: str = "educational"  # educational, cartoon, realistic

class ImageResponse(BaseModel):
    image_url: str
    prompt: str
    model: str
    size: str
    usage_info: Optional[Dict[str, Any]] = None

@router.post("/generate", response_model=ImageResponse)
async def generate_word_image(
    request: ImageGenerationRequest,
    current_user: dict = Depends(get_current_active_user),
    openai_service: OpenAIService = Depends(OpenAIService)
):
    """
    Generate an educational image for a German word using DALL-E.
    """
    try:
        # Validate model and size combinations
        if request.model == "dall-e-3":
            valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
            if request.size not in valid_sizes:
                request.size = "1024x1024"  # Default for DALL-E 3
        else:  # dall-e-2
            valid_sizes = ["256x256", "512x512", "1024x1024"]
            if request.size not in valid_sizes:
                request.size = "512x512"  # Default for DALL-E 2

        # Build prompt based on word data and style
        base_info = f"the German word '{request.word}'"
        
        # Add meaning context
        meaning_context = ""
        if request.word_data.get('gloss_en'):
            meaning_context = f" (meaning: {request.word_data['gloss_en']})"
        elif request.word_data.get('translations_en'):
            meaning_context = f" (meaning: {request.word_data['translations_en'][0]})"
            
        # Determine art style
        style_prompts = {
            "educational": "Clean, simple educational illustration style, like a textbook or dictionary illustration",
            "cartoon": "Friendly cartoon style, colorful and approachable, suitable for language learning",
            "realistic": "Semi-realistic digital art style, clear and detailed but not photographic"
        }
        
        style_description = style_prompts.get(request.style, style_prompts["educational"])
        
        # Build the full prompt
        if request.word_data.get('pos') == 'noun' or request.word_data.get('upos') == 'NOUN':
            # For nouns, show the object/concept
            prompt = f"{style_description}. A clear illustration of {base_info}{meaning_context}. The image should help a German language learner understand and remember this noun. Simple background, focus on the main subject."
        elif request.word_data.get('pos') == 'verb' or request.word_data.get('upos') == 'VERB':
            # For verbs, show the action
            prompt = f"{style_description}. An illustration showing the action of {base_info}{meaning_context}. The image should clearly depict someone performing this verb in a way that helps German language learners understand and remember the action. Simple background, clear action."
        elif request.word_data.get('pos') == 'adjective' or request.word_data.get('upos') == 'ADJ':
            # For adjectives, show the quality/characteristic
            prompt = f"{style_description}. An illustration that represents the quality or characteristic of {base_info}{meaning_context}. The image should help German language learners understand and remember this adjective. Visual representation of the quality, simple background."
        else:
            # Generic approach for other word types
            prompt = f"{style_description}. An educational illustration representing {base_info}{meaning_context}. The image should help German language learners understand and remember this word. Clear, simple, and educational."
            
        # Add quality and safety modifiers - explicitly avoid any text in image
        prompt += " High quality, educational content, appropriate for all ages. IMPORTANT: No text, no words, no letters, no labels in the image. Pure visual illustration only."
        
        logger.info(f"Generating image for word '{request.word}' with prompt: {prompt[:100]}...")

        # Generate image using OpenAI service
        try:
            image_data = await openai_service.generate_image(
                prompt=prompt,
                model=request.model,
                size=request.size,
                quality="standard" if request.model == "dall-e-2" else "standard"
            )
            
            return ImageResponse(
                image_url=image_data["url"],
                prompt=prompt,
                model=request.model,
                size=request.size,
                usage_info=image_data.get("usage")
            )
            
        except Exception as openai_error:
            logger.error(f"OpenAI API error in image generation: {openai_error}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate image: {str(openai_error)}"
            )
            
    except Exception as e:
        logger.error(f"Error in image generation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during image generation")