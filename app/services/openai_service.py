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
        """
        Analyze a single German word and return JSON shaped exactly for your DB:
        - Normalize everything into `word_forms`: [{feature_key, feature_value, form}]
        - For verbs also return `verb_props` matching your VerbProps model
        - Include translations + one example for UX

        IMPORTANT (schema contract):
        - Persons: ich, du, er_sie_es, wir, ihr, sie_Sie
        - Tenses: praesens, praeteritum, perfekt, plusquamperfekt,
                  futur_i, futur_ii, imperativ, konjunktiv_i, konjunktiv_ii
        - For verbs, encode every cell as: feature_key="tense",
          feature_value=f"{tense}_{person}", form="<conjugated>"
        - Noun article → feature_key="gender", feature_value in {"masc","fem","neut"}, form in {"der","die","das"}
        - Noun plural → feature_key="number", feature_value="plural", form="<Pluralform>"
        - Adjective degrees → feature_key="degree", feature_value in {"positive","comparative","superlative"}
        - Leave out unknown fields entirely (do NOT write 'null' or placeholders)
        """
        if not self.client:
            raise RuntimeError("OpenAI API key not set; word analysis is unavailable")

        # The exact JSON schema we want the model to follow.
        system = (
            "You are a meticulous German lexicon engine. "
            "Always return STRICT JSON that matches the schema. "
            "Never add explanatory text outside JSON. "
            "If something is unknown, OMIT the field."
        )

        # NOTE: This prompt encodes directly into your DB model:
        # - `word_forms` maps to WordForm rows (feature_key, feature_value, form)
        # - `verb_props` maps to VerbProps (aux, partizip_ii, regularity, separable, prefix, reflexive, valency_json)
        # - translations + example are for UX
        user = f"""
Return a single JSON object for the EXACT German word "{word}". Do NOT correct the input.

If the word is VALID German (lemma or inflected form), produce:

{{
  "found": true,
  "input_word": "{word}",
  "lemma": "base lemma as used in dictionaries (preserve German capitalization rules)",
  "pos": "one of: noun|verb|vt|vi|vr|aux|modal|adj|adv|prep|det|art|pron|conj|interj|num|vi_impers|vt_impers|vi_prep_obj|vt_prep_obj",

  "word_forms": [
    // VERBS: encode ALL available cells as tense+person
    // Example: Präsens ich gehe → {{"feature_key":"tense","feature_value":"praesens_ich","form":"gehe"}}
    // Include: praesens, praeteritum, perfekt, plusquamperfekt, futur_i, futur_ii, imperativ, konjunktiv_i, konjunktiv_ii
    // Persons set: ich, du, er_sie_es, wir, ihr, sie_Sie
    // Imperativ only du|ihr|Sie (still encode as tense_imperativ_<person>)
    // If a specific cell truly doesn't exist, omit it.

    // NOUNS:
    // Article (gender): {{"feature_key":"gender","feature_value":"masc|fem|neut","form":"der|die|das"}}
    // Plural (if exists): {{"feature_key":"number","feature_value":"plural","form":"<Plural>"}}

    // ADJECTIVES:
    // Degrees: positive (base form), comparative, superlative
    // Example: {{"feature_key":"degree","feature_value":"comparative","form":"schöner"}}
    //          {{"feature_key":"degree","feature_value":"superlative","form":"am schönsten"}}

    // ADVERBS, PREPOSITIONS, CONJUNCTIONS, PRONOUNS, DETERMINERS, NUMERALS, PARTICLES, INTERJECTIONS:
    // Provide forms only if there are actual inflected forms (e.g., pronoun case forms).
    // Otherwise omit `word_forms` entries for those categories.
    // PRONOUN example (if applicable):
    //   {{"feature_key":"case","feature_value":"nom","form":"ich"}}, {{"feature_key":"case","feature_value":"akk","form":"mich"}}, ...

  ],

  // For verbs only; omit for other POS
  "verb_props": {{
    "aux": "haben|sein",
    "partizip_ii": "gegangen",
    "regularity": "weak|strong|mixed|irregular",
    "separable": 0 or 1,
    "prefix": "if verb has a clear (in)separable prefix else omit",
    "reflexive": 0 or 1,
    "valency_json": "OPTIONAL compact JSON as a string with minimal subcat info, else omit"
  }},

  "translations_en": ["natural, concise English senses"],
  "translations_zh": ["准确、简洁的中文释义"],
  "example": {{"de":"natural German sentence with the lemma", "en":"", "zh":""}}
}}

If "{word}" is NOT valid German, return exactly:
{{
  "found": false,
  "input_word": "{word}",
  "message": "not a recognized German word",
  "suggestions": [
    {{"word":"...", "pos":"noun|verb|adj|...", "meaning":"brief EN gloss"}}
  ]
}}

STRICT RULES:
- JSON only. No extra text.
- For persons use EXACT: ich, du, er_sie_es, wir, ihr, sie_Sie
- For tenses use EXACT: praesens, praeteritum, perfekt, plusquamperfekt, futur_i, futur_ii, imperativ, konjunktiv_i, konjunktiv_ii
- For noun article encode gender via: (gender, masc|fem|neut) + form in der/die/das.
- For plural encode as: (number, plural) + the plural surface form.
- Omit unknown fields entirely (do not set null or empty strings).
"""

        try:
            resp = await self.client.chat.completions.create(
                model=self.analysis_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=1400,
            )

            content = resp.choices[0].message.content
            data = json.loads(content)

            # Minimal sanity normalization to keep DB safe
            if data.get("found") is True:
                # enforce array types
                data["word_forms"] = [wf for wf in data.get("word_forms", []) if isinstance(wf, dict)]
                for wf in data["word_forms"]:
                    # hard trim
                    wf["feature_key"] = (wf.get("feature_key") or "").strip()
                    wf["feature_value"] = (wf.get("feature_value") or "").strip()
                    wf["form"] = (wf.get("form") or "").strip()
                # scrub empty forms
                data["word_forms"] = [wf for wf in data["word_forms"] if wf["feature_key"] and wf["feature_value"] and wf["form"]]

                # verb_props only for verbs
                if data.get("pos","").startswith("v"):
                    vp = data.get("verb_props") or {}
                    # coerce booleans to 0/1 for DB integers if present
                    if "separable" in vp and isinstance(vp["separable"], bool):
                        vp["separable"] = 1 if vp["separable"] else 0
                    if "reflexive" in vp and isinstance(vp["reflexive"], bool):
                        vp["reflexive"] = 1 if vp["reflexive"] else 0
                    data["verb_props"] = vp
                else:
                    data.pop("verb_props", None)

                # translations
                data["translations_en"] = [t for t in data.get("translations_en", []) if isinstance(t, str) and t.strip()]
                data["translations_zh"] = [t for t in data.get("translations_zh", []) if isinstance(t, str) and t.strip()]

            return data

        except Exception as e:
            logging.error(f"OpenAI API error for word '{word}': {str(e)}")
            # Surface helpful diagnostics to your callers
            if "401" in str(e):
                raise RuntimeError(f"Authentication failed. Check API key / account. Error: {str(e)}")
            elif "403" in str(e):
                raise RuntimeError(f"Access forbidden. Permissions/credits? Error: {str(e)}")
            elif "429" in str(e):
                raise RuntimeError(f"Rate limit exceeded. Try later. Error: {str(e)}")
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