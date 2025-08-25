from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class WordFormBase(BaseModel):
    form: str
    feature_key: str
    feature_value: str


class WordForm(WordFormBase):
    id: int
    lemma_id: int

    class Config:
        from_attributes = True


class TranslationBase(BaseModel):
    lang_code: str
    text: str
    source: Optional[str] = "openai"


class Translation(TranslationBase):
    id: int
    lemma_id: int

    class Config:
        from_attributes = True


class ExampleBase(BaseModel):
    de_text: str
    en_text: Optional[str] = None
    zh_text: Optional[str] = None
    level: Optional[str] = "A1"


class Example(ExampleBase):
    id: int
    lemma_id: int

    class Config:
        from_attributes = True


class WordLemmaBase(BaseModel):
    lemma: str
    pos: Optional[str] = None
    cefr: Optional[str] = None
    ipa: Optional[str] = None
    frequency: Optional[int] = 0
    notes: Optional[str] = None


class WordLemma(WordLemmaBase):
    id: int
    created_at: datetime
    forms: List[WordForm] = []
    translations: List[Translation] = []
    examples: List[Example] = []

    class Config:
        from_attributes = True


class WordAnalysis(BaseModel):
    """Response from OpenAI word analysis"""
    original: str
    pos: Optional[str] = None
    article: Optional[str] = None  # for nouns: der/die/das
    plural: Optional[str] = None   # for nouns
    tables: Optional[Dict[str, Any]] = None  # conjugation/declension tables
    translations_en: List[str] = []
    translations_zh: List[str] = []
    example: Optional[Dict[str, str]] = None  # {de: "", en: "", zh: ""}


class WordSearchRequest(BaseModel):
    q: str
    lang: Optional[str] = "de"


class WordSearchResponse(BaseModel):
    results: List[WordLemma]
    total: int
    cached: bool = False


class TranslationOption(BaseModel):
    german_word: str
    context: str
    pos: str


class TranslateSearchRequest(BaseModel):
    text: str
    translate_mode: bool = True


class LanguageChoice(BaseModel):
    language_code: str
    language_name: str
    meaning: str
    action: str  # "search_german" or "translate_from"


class TranslateSearchResponse(BaseModel):
    original_text: str
    detected_language: str
    detected_language_name: str
    confidence: float
    # Language ambiguity fields
    is_language_ambiguous: bool = False
    language_choices: List[LanguageChoice] = []
    # Translation fields
    german_translations: List[TranslationOption] = []
    is_translation_ambiguous: bool = False
    search_results: Optional[Dict[str, Any]] = None
    selected_translation: Optional[str] = None
    error_message: Optional[str] = None


class TranslationSelectionRequest(BaseModel):
    original_text: str
    selected_german_word: str


class LanguageSelectionRequest(BaseModel):
    original_text: str
    selected_language: str
    selected_action: str  # "search_german" or "translate_from"