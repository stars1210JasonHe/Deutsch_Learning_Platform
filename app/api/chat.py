from typing import List, Dict, Any, Optional, Literal, Annotated
from pydantic import BaseModel, Field, validator, StringConstraints
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_current_active_user
from app.services.openai_service import OpenAIService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

# --- Models ------------------------------------------------------------------

Role = Literal["user", "assistant"]  # forbid 'system' from client input

class ChatMessage(BaseModel):
    role: Role
    content: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
    timestamp: Optional[str] = None

class VerbProps(BaseModel):
    separable: Optional[bool] = None
    aux: Optional[Annotated[str, StringConstraints(max_length=10)]] = None  # "sein"/"haben"

class WordData(BaseModel):
    pos: Optional[Annotated[str, StringConstraints(max_length=24)]] = None
    gloss_en: Optional[Annotated[str, StringConstraints(max_length=400)]] = None
    gloss_zh: Optional[Annotated[str, StringConstraints(max_length=400)]] = None
    translations_en: List[Annotated[str, StringConstraints(max_length=64)]] = []
    translations_zh: List[Annotated[str, StringConstraints(max_length=64)]] = []
    article: Optional[Annotated[str, StringConstraints(pattern=r"^(der|die|das)$")]] = None
    plural: Optional[Annotated[str, StringConstraints(max_length=64)]] = None
    verb_props: Optional[VerbProps] = None

    @validator("translations_en", "translations_zh", pre=True)
    def ensure_list(cls, v):
        if v is None:
            return []
        return v[:6]  # cap length to keep prompt small

class WordChatRequest(BaseModel):
    word: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
    word_data: WordData
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
    chat_history: List[ChatMessage] = []
    explain_lang: Literal["en", "zh"] = "en"
    level: Literal["A2", "B1"] = "A2"

class ChatResponse(BaseModel):
    response: str
    usage_info: Optional[Dict[str, Any]] = None
    structured: Optional[Dict[str, Any]] = None  # NEW: predictable UI blocks

# --- Helpers -----------------------------------------------------------------

def _sanitize(s: Optional[str], max_len: int = 400) -> str:
    if not s:
        return ""
    s = s.replace("\n", " ").replace("\r", " ").strip()
    return s[:max_len]

def build_word_context(w: str, d: WordData) -> str:
    parts = [f"Word: {w}"]
    if d.pos: parts.append(f"Part of Speech: {d.pos}")
    if d.gloss_en: parts.append(f"English meaning: {_sanitize(d.gloss_en)}")
    if d.gloss_zh: parts.append(f"Chinese meaning: {_sanitize(d.gloss_zh)}")
    if d.translations_en: parts.append(f"English translations: {', '.join(d.translations_en)}")
    if d.translations_zh: parts.append(f"Chinese translations: {', '.join(d.translations_zh)}")
    if d.article: parts.append(f"Article: {d.article}")
    if d.plural: parts.append(f"Plural: {_sanitize(d.plural, 64)}")
    if d.verb_props:
        if d.verb_props.separable: parts.append("Separable verb: Yes")
        if d.verb_props.aux: parts.append(f"Auxiliary verb: {d.verb_props.aux}")
    return "\n".join(parts)

RESPONSE_SCHEMA = """
Return JSON with:
- answer: string (plain, learner-friendly)
- examples: array of up to 3 short sentences
- mini_practice: string (one cloze or micro-task + solution)
- tips: array of 1-2 bullet lines
"""

def build_system_message(word: str, word_context: str, lang: str, level: str) -> str:
    return f"""You are a friendly German tutor. Target level: {level}. Explain in {"English" if lang=="en" else "Chinese"} with simple wording.

WORD INFO
---------
{word_context}

BEHAVIOR
--------
- Start with a 1-sentence TL;DR.
- Use A2–B1 vocabulary unless asked otherwise.
- Prefer concrete examples (Germany context).
- Keep total under ~1500 tokens.

OUTPUT FORMAT
-------------
{RESPONSE_SCHEMA}
"""

def trim_history(history: List[ChatMessage], max_items: int = 8) -> List[ChatMessage]:
    # keep last N turns to control token usage
    return history[-max_items:]

# --- Route -------------------------------------------------------------------

@router.post("/word", response_model=ChatResponse)
async def chat_about_word(
    request: WordChatRequest,
    current_user: dict = Depends(get_current_active_user),
    openai_service: OpenAIService = Depends(OpenAIService)
):
    try:
        word_context = build_word_context(request.word, request.word_data)
        system_message = build_system_message(
            request.word, word_context, request.explain_lang, request.level
        )

        messages = [{"role": "system", "content": system_message}]
        for msg in trim_history(request.chat_history):
            # roles already validated by Pydantic (no 'system' allowed)
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": request.message})

        try:
            resp = await openai_service.chat_completion(
                messages=messages,
                max_tokens=800,
                temperature=0.7
            )
        except Exception as oe:
            logger.exception("OpenAI error during /chat/word")
            raise HTTPException(status_code=502, detail="LLM upstream error") from oe

        # Robust extraction
        content = (
            resp.get("content")
            or resp.get("choices", [{}])[0].get("message", {}).get("content")
            or ""
        ).strip()

        structured = None
        # Try to parse JSON if model complied; fallback to raw
        try:
            import json
            structured = json.loads(content)
            response_text = structured.get("answer", "")
            # If model included TL;DR inside, fine; else compose something minimal
            if not response_text:
                response_text = content
        except Exception:
            response_text = content

        return ChatResponse(
            response=response_text,
            usage_info=resp.get("usage"),
            structured=structured
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Internal error in /chat/word")
        raise HTTPException(status_code=500, detail="Internal server error during chat")
