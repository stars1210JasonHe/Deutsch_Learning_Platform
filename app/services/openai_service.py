import asyncio
import json
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.core.config import settings


class OpenAIService:
    def __init__(self):
        if not settings.openai_api_key:
            logging.warning("OpenAI API key not set. OpenAI features will be disabled.")
            self.client = None
        else:
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
        self.model = settings.openai_model

    async def analyze_word(self, word: str) -> Dict[str, Any]:
        """Analyze a single word for POS, conjugations, translations"""
        if not self.client:
            # Strict mode: no silent fallback; caller must handle
            raise RuntimeError("OpenAI API key not set; word analysis is unavailable")
        
        try:
            logging.info(f"Analyzing word '{word}' using {settings.openai_base_url}")
            
            prompt = f"""
        IMPORTANT: Analyze the EXACT word "{word}" as provided. Do not auto-correct or substitute it with similar words.

        First, determine if "{word}" is a valid German word (exact match only):
        - Check if it's a valid German lemma, inflected form, or compound word
        - Do NOT consider it valid if it's just similar to a German word
        - Do NOT auto-correct spelling mistakes

        If "{word}" is EXACTLY a valid German word, return:
        {{
            "found": true,
            "input_word": "{word}",
            "pos": "verb|noun|adjective|adverb|preposition|article|pronoun|other",
            "lemma": "base form" (if different from input),
            "article": "der|die|das" (only for nouns, null otherwise),
            "plural": "plural form" (only for nouns, null otherwise),
            "tables": {{
                "praesens": {{"ich": "form", "du": "form", "er_sie_es": "form", "wir": "form", "ihr": "form", "sie_Sie": "form"}},
                "praeteritum": {{"ich": "form", "du": "form", "er_sie_es": "form", "wir": "form", "ihr": "form", "sie_Sie": "form"}},
                "perfekt": {{"aux": "haben|sein", "partizip_ii": "form", "ich": "habe/bin + partizip", "er_sie_es": "hat/ist + partizip"}},
                "plusquamperfekt": {{"ich": "hatte/war + partizip", "du": "hattest/warst + partizip", "er_sie_es": "hatte/war + partizip", "wir": "hatten/waren + partizip", "ihr": "hattet/wart + partizip", "sie_Sie": "hatten/waren + partizip"}},
                "futur1": {{"ich": "werde form", "du": "wirst form", "er_sie_es": "wird form", "wir": "werden form", "ihr": "werdet form", "sie_Sie": "werden form"}},
                "imperativ": {{"du": "imperative_form", "ihr": "imperative_form", "Sie": "imperative_form"}}
            }} (only for verbs, null otherwise),
            "translations_en": ["translation1", "translation2"],
            "translations_zh": ["翻译1", "翻译2"],
            "example": {{"de": "German sentence", "en": "English sentence", "zh": "中文句子"}}
        }}
        
        If "{word}" is NOT a valid German word (including typos, non-German words, gibberish), return:
        {{
            "found": false,
            "input_word": "{word}",
            "suggestions": [
                {{"word": "similar_word1", "pos": "noun", "meaning": "brief explanation"}},
                {{"word": "similar_word2", "pos": "verb", "meaning": "brief explanation"}},
                {{"word": "similar_word3", "pos": "adjective", "meaning": "brief explanation"}},
                {{"word": "similar_word4", "pos": "noun", "meaning": "brief explanation"}},
                {{"word": "similar_word5", "pos": "verb", "meaning": "brief explanation"}}
            ],
            "message": "'{word}' is not a recognized German word. Here are some similar words you might be looking for:"
        }}
        
        Examples:
        - "nim" → found: false (not a valid German word, suggest "nehmen")
        - "gehe" → found: true (valid inflected form of "gehen")
        - "xyz123" → found: false (gibberish)
        """
        
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise German language assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logging.error(f"OpenAI API error for word '{word}': {str(e)}")
            if "401" in str(e):
                raise RuntimeError(f"Authentication failed with OpenRouter. Please check your API key and account status. Error: {str(e)}")
            elif "403" in str(e):
                raise RuntimeError(f"Access forbidden. Your OpenRouter account may lack permissions or credits. Error: {str(e)}")
            elif "429" in str(e):
                raise RuntimeError(f"Rate limit exceeded. Please try again later. Error: {str(e)}")
            else:
                raise RuntimeError(f"API request failed: {str(e)}")

    async def translate_sentence(self, sentence: str) -> Dict[str, Any]:
        """Translate sentence and provide word-by-word gloss"""
        if not self.client:
            raise RuntimeError("OpenAI API key not set; sentence translation is unavailable")
            
        prompt = f"""
        Translate the sentence "{sentence}" and provide a word-by-word gloss.
        Return JSON with this structure:
        {{
            "german": "German translation (if input is not German)",
            "gloss": [
                {{"de": "German_word", "en": "English", "zh": "中文", "note": "grammar note if needed"}},
                ...
            ]
        }}
        
        If the input is German, translate to English/Chinese and provide gloss.
        If the input is English/Chinese, translate to German first, then provide gloss.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a precise German translation assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            raise