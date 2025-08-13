from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class TranslateWordRequest(BaseModel):
    input: str


class TranslateWordResponse(BaseModel):
    original: str
    pos: Optional[str] = None
    article: Optional[str] = None
    plural: Optional[str] = None
    tables: Optional[Dict[str, Any]] = None
    translations_en: List[str] = []
    translations_zh: List[str] = []
    example: Optional[Dict[str, str]] = None
    cached: bool = False


class TranslateSentenceRequest(BaseModel):
    input: str


class GlossItem(BaseModel):
    de: str
    en: str
    zh: str
    note: Optional[str] = None


class TranslateSentenceResponse(BaseModel):
    original: str
    german: str
    gloss: List[GlossItem] = []
    cached: bool = False