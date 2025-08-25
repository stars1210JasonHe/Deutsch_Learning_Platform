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
            self.image_client = None
        else:
            # Main client for chat/analysis (can use OpenRouter)
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
            
            # Separate client for image generation (always direct OpenAI)
            image_api_key = settings.openai_image_api_key or settings.openai_api_key
            image_base_url = settings.openai_image_base_url or "https://api.openai.com/v1"
            
            if image_api_key:
                self.image_client = AsyncOpenAI(
                    api_key=image_api_key,
                    base_url=image_base_url
                )
            else:
                logging.warning("No API key available for image generation")
                self.image_client = None
        self.model = settings.openai_model
        
        # Feature-specific models with fallback to default
        self.chat_model = settings.openai_chat_model or settings.openai_model
        self.analysis_model = settings.openai_analysis_model or settings.openai_model
        self.translation_model = settings.openai_translation_model or settings.openai_model
        self.exam_model = settings.openai_exam_model or settings.openai_model
        self.image_model = settings.openai_image_model or "dall-e-2"  # Default to DALL-E 2 for images

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

        FOR VERBS: You MUST provide complete conjugation tables with ALL available German tenses:
        - REQUIRED: praesens, praeteritum, perfekt, plusquamperfekt, imperativ (minimum 5)
        - OPTIONAL: futur_i, futur_ii, konjunktiv_i, konjunktiv_ii (include if available)
        - Provide as many tenses as you can for comprehensive language learning

        If "{word}" is EXACTLY a valid German word, return:
        {{
            "found": true,
            "input_word": "{word}",
            "pos": "noun|verb|vt|vi|vr|aux|modal|adj|pron|prep|adv|det|art|particle|conj|interj|num|vi_impers|vt_impers|vi_prep_obj|vt_prep_obj",
            "lemma": "base form" (if different from input),
            "article": "der|die|das" (only for nouns, null otherwise),
            "plural": "plural form" (only for nouns, null otherwise),
            "tables": {{
                "praesens": {{"ich": "form", "du": "form", "er_sie_es": "form", "wir": "form", "ihr": "form", "sie_Sie": "form"}},
                "praeteritum": {{"ich": "form", "du": "form", "er_sie_es": "form", "wir": "form", "ihr": "form", "sie_Sie": "form"}},
                "perfekt": {{"ich": "habe/bin + partizip", "du": "hast/bist + partizip", "er_sie_es": "hat/ist + partizip", "wir": "haben/sind + partizip", "ihr": "habt/seid + partizip", "sie_Sie": "haben/sind + partizip"}},
                "plusquamperfekt": {{"ich": "hatte/war + partizip", "du": "hattest/warst + partizip", "er_sie_es": "hatte/war + partizip", "wir": "hatten/waren + partizip", "ihr": "hattet/wart + partizip", "sie_Sie": "hatten/waren + partizip"}},
                "futur_i": {{"ich": "werde + infinitive", "du": "wirst + infinitive", "er_sie_es": "wird + infinitive", "wir": "werden + infinitive", "ihr": "werdet + infinitive", "sie_Sie": "werden + infinitive"}},
                "futur_ii": {{"ich": "werde + partizip + haben/sein", "du": "wirst + partizip + haben/sein", "er_sie_es": "wird + partizip + haben/sein", "wir": "werden + partizip + haben/sein", "ihr": "werdet + partizip + haben/sein", "sie_Sie": "werden + partizip + haben/sein"}},
                "konjunktiv_i": {{"ich": "subjunctive_i_form", "du": "subjunctive_i_form", "er_sie_es": "subjunctive_i_form", "wir": "subjunctive_i_form", "ihr": "subjunctive_i_form", "sie_Sie": "subjunctive_i_form"}},
                "konjunktiv_ii": {{"ich": "subjunctive_ii_form", "du": "subjunctive_ii_form", "er_sie_es": "subjunctive_ii_form", "wir": "subjunctive_ii_form", "ihr": "subjunctive_ii_form", "sie_Sie": "subjunctive_ii_form"}},
                "imperativ": {{"du": "imperative_form", "ihr": "imperative_form", "Sie": "imperative_form"}}
            }} (include ALL available German tenses for verbs - minimum 5 core tenses required),
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
        
        CRITICAL RULES FOR SUGGESTIONS:
        1. ONLY suggest real, common German words (A1-B2 level preferred)
        2. Suggestions must be phonetically or orthographically similar to "{word}"
        3. NO English words, NO made-up words, NO technical terms
        4. Focus on basic vocabulary: nouns (der/die/das), common verbs, adjectives
        5. Prefer words that German learners would actually need
        6. If "{word}" looks like a typo of a German word, prioritize that word
        7. Maximum 5 suggestions, ranked by similarity and usefulness
        
        Examples:
        - "nim" → found: false (not a valid German word, suggest "nehmen")
        - "gehe" → found: true (valid inflected form of "gehen")
        - "xyz123" → found: false (gibberish)
        """
        
            response = await self.client.chat.completions.create(
                model=self.analysis_model,
                messages=[
                    {"role": "system", "content": "You are a precise German language assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            
            raw_result = json.loads(response.choices[0].message.content)
            
            # Validate and clean suggestions if word not found
            if not raw_result.get("found", True):
                clean_suggestions = self._validate_suggestions(raw_result.get("suggestions", []))
                raw_result["suggestions"] = clean_suggestions
            
            return raw_result
            
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

    def _validate_suggestions(self, suggestions: list) -> list:
        """Validate and filter OpenAI suggestions to ensure quality"""
        if not suggestions or not isinstance(suggestions, list):
            return []
        
        # Common German words that should be prioritized
        german_indicators = {
            'ä', 'ö', 'ü', 'ß', 'der', 'die', 'das', 'ein', 'eine', 'und', 
            'ist', 'hat', 'sein', 'haben', 'werden', 'können', 'müssen', 'sollen'
        }
        
        # Words to filter out (English, technical, inappropriate)
        forbidden_words = {
            'the', 'and', 'or', 'but', 'if', 'then', 'when', 'where', 'what', 'how',
            'you', 'me', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these',
            'api', 'http', 'www', 'com', 'org', 'net', 'html', 'xml', 'json',
            'error', 'null', 'undefined', 'function', 'class', 'object', 'array'
        }
        
        valid_suggestions = []
        seen_words = set()
        
        for suggestion in suggestions:
            if not isinstance(suggestion, dict):
                continue
                
            word = suggestion.get('word', '').strip().lower()
            pos = suggestion.get('pos', '').strip().lower()
            meaning = suggestion.get('meaning', '').strip()
            
            # Skip if missing required fields
            if not word or not pos or not meaning:
                continue
                
            # Skip duplicates
            if word in seen_words:
                continue
                
            # Filter out forbidden words
            if word in forbidden_words:
                continue
                
            # Filter out words that are clearly English
            if pos in ['article', 'preposition'] and word in ['the', 'and', 'or', 'but', 'in', 'on', 'at']:
                continue
                
            # Filter out single characters or very short "words" unless they're German
            if len(word) <= 2 and word not in {'zu', 'im', 'am', 'es', 'er', 'du', 'ja'}:
                continue
                
            # Validate POS tags
            valid_pos = {'noun', 'verb', 'adjective', 'adverb', 'preposition', 'article', 'pronoun'}
            if pos not in valid_pos:
                continue
                
            # Prefer words with German characteristics
            priority_score = 0
            if any(char in word for char in ['ä', 'ö', 'ü', 'ß']):
                priority_score += 2
            if pos == 'noun' and len(word) >= 4:  # German nouns tend to be longer
                priority_score += 1
            if word.endswith(('en', 'er', 'el', 'ig', 'lich', 'ung', 'heit', 'keit', 'schaft')):
                priority_score += 1
                
            valid_suggestions.append({
                'word': suggestion['word'],  # Keep original capitalization
                'pos': pos,
                'meaning': meaning,
                '_priority': priority_score
            })
            seen_words.add(word)
            
            # Limit to 5 suggestions
            if len(valid_suggestions) >= 5:
                break
        
        # Sort by priority score (higher is better) and return
        valid_suggestions.sort(key=lambda x: x.get('_priority', 0), reverse=True)
        
        # Remove internal priority field before returning
        for suggestion in valid_suggestions:
            suggestion.pop('_priority', None)
            
        return valid_suggestions[:5]

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

    async def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect the language of input text"""
        if not self.client:
            raise RuntimeError("OpenAI API key not set; language detection is unavailable")
            
        try:
            prompt = f"""
            Analyze this word: "{text}"
            
            Determine if this word could exist in multiple languages, especially German and another language.
            
            Return JSON with this structure (use JSON null, not string "null"):
            {{
                "detected_language": "most_likely_language_code",
                "confidence": 0.95,
                "language_name": "English|German|Chinese|French|Spanish|Italian|etc",
                "is_german": true|false,
                "is_ambiguous": true|false,
                "alternative_language": "language_code",
                "alternative_language_name": "Language Name", 
                "german_meaning": "brief meaning if German",
                "alternative_meaning": "brief meaning in alternative language"
            }}
            
            IMPORTANT: When a field should be empty, use JSON null (not string "null"). Example:
            - Good: "alternative_language": null
            - Bad: "alternative_language": "null"
            
            Rules:
            - Set is_ambiguous=true ONLY when word could realistically be German AND another language
            - For ambiguous words, always check if one could be German
            - Examples of ambiguous: "hell" (German=bright, English=underworld), "bank" (German=bench, English=financial)  
            - Examples of NOT ambiguous: "hello" (clearly English), "schön" (clearly German)
            - Use ISO 639-1 codes (en, de, zh, fr, es, it, etc)
            - Prioritize common languages for alternatives (English, Chinese, French, Spanish)
            - Only suggest ONE alternative language (the most likely)
            """
            
            response = await self.client.chat.completions.create(
                model=self.translation_model,
                messages=[
                    {"role": "system", "content": "You are a precise language detection assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=200
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logging.error(f"Language detection error for text '{text}': {str(e)}")
            raise

    async def translate_to_german(self, text: str, source_language: str = None) -> Dict[str, Any]:
        """Translate text to German, handling multiple possible translations"""
        if not self.client:
            raise RuntimeError("OpenAI API key not set; translation is unavailable")
            
        try:
            source_info = f" from {source_language}" if source_language else ""
            
            prompt = f"""
            Translate the word "{text}"{source_info} to German.
            
            IMPORTANT: This is for single WORD translation, not sentences.
            If the word has multiple meanings, provide ALL relevant German translations.
            
            Return JSON with this structure:
            {{
                "translations": [
                    {{
                        "german_word": "German translation",
                        "context": "brief context/meaning description", 
                        "pos": "noun|verb|adjective|etc"
                    }}
                ],
                "is_ambiguous": true|false,
                "source_language": "detected_language_code"
            }}
            
            Examples:
            - "bank" → [{{"german_word": "Bank", "context": "financial institution", "pos": "noun"}}, {{"german_word": "Ufer", "context": "river bank", "pos": "noun"}}]
            - "hello" → [{{"german_word": "hallo", "context": "greeting", "pos": "interjection"}}]
            
            If no German translation exists, return empty translations array.
            Set is_ambiguous to true if there are multiple valid translations.
            """
            
            response = await self.client.chat.completions.create(
                model=self.translation_model,
                messages=[
                    {"role": "system", "content": "You are a precise translation assistant specializing in German. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=400
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate translations structure
            if "translations" not in result or not isinstance(result["translations"], list):
                result["translations"] = []
            
            # Ensure each translation has required fields
            valid_translations = []
            for trans in result["translations"]:
                if isinstance(trans, dict) and "german_word" in trans:
                    valid_translations.append({
                        "german_word": trans.get("german_word", ""),
                        "context": trans.get("context", ""),
                        "pos": trans.get("pos", "")
                    })
            
            result["translations"] = valid_translations
            result["is_ambiguous"] = len(valid_translations) > 1
            
            return result
            
        except Exception as e:
            logging.error(f"Translation error for text '{text}': {str(e)}")
            raise

    async def chat_completion(self, messages: list, max_tokens: int = 800, temperature: float = 0.7) -> Dict[str, Any]:
        """General chat completion method for conversational AI"""
        if not self.client:
            raise RuntimeError("OpenAI API key not set; chat completion is unavailable")
            
        try:
            response = await self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None
            }
            
        except Exception as e:
            logging.error(f"OpenAI chat completion error: {str(e)}")
            raise

    async def generate_image(self, prompt: str, model: str = None, size: str = "512x512", quality: str = "standard") -> Dict[str, Any]:
        """Generate an image using DALL-E"""
        if not self.image_client:
            raise RuntimeError("OpenAI API key not set; image generation is unavailable")
            
        try:
            # Use configured image model if not explicitly provided
            if model is None:
                model = self.image_model
                
            # Validate model and size combinations
            if model == "dall-e-3":
                valid_sizes = ["1024x1024", "1792x1024", "1024x1792"]
                if size not in valid_sizes:
                    size = "1024x1024"
            else:  # dall-e-2
                valid_sizes = ["256x256", "512x512", "1024x1024"]
                if size not in valid_sizes:
                    size = "512x512"
                    
            # DALL-E 3 supports quality parameter, DALL-E 2 does not
            params = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "n": 1
            }
            
            if model == "dall-e-3":
                params["quality"] = quality
                
            response = await self.image_client.images.generate(**params)
            
            return {
                "url": response.data[0].url,
                "usage": {
                    "model": model,
                    "size": size,
                    "quality": quality if model == "dall-e-3" else "standard"
                }
            }
            
        except Exception as e:
            logging.error(f"OpenAI image generation error: {str(e)}")
            raise