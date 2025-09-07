import asyncio
import json
import logging
import re
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from app.core.config import settings


class OpenAIService:
    _EXONYM_TO_DE = {
        # Common English → German endonyms (extend as needed)
        "austria": "Österreich",
        "germany": "Deutschland",
        "switzerland": "Schweiz",
        "france": "Frankreich",
        "spain": "Spanien",
        "italy": "Italien",
        "japan": "Japan",
        "china": "China",
        "south korea": "Südkorea",
        "north korea": "Nordkorea",
        "poland": "Polen",
        "belgium": "Belgien",
        "portugal": "Portugal",
        "russia": "Russland",
        "netherlands": "Niederlande",
        "czech republic": "Tschechien",
        "united states": "Vereinigte Staaten",
        "u.s.a.": "USA",
        "usa": "USA",
        "united kingdom": "Vereinigtes Königreich",
        "great britain": "Großbritannien",
    }
    def _normalize_surface(self, s: str) -> str:
        if not isinstance(s, str):
            return ""
        return " ".join(s.strip().split())
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

    def _parse_json_safely(self, content: str, word: str = "") -> Dict[str, Any]:
        """
        Robust JSON parsing with error recovery for malformed OpenAI responses
        """
        if not content or not content.strip():
            return {"found": False, "error": "Empty response"}

        content = content.strip()
        
        try:
            # Try direct parsing first
            return json.loads(content)
        except json.JSONDecodeError as e:
            logging.warning(f"JSON parse error for '{word}': {e}")
            
            try:
                # Attempt to fix common JSON issues
                fixed_content = self._fix_common_json_issues(content)
                return json.loads(fixed_content)
            except json.JSONDecodeError as e2:
                logging.error(f"Failed to fix JSON for '{word}': {e2}")
                # Return a safe fallback
                return {
                    "found": False,
                    "error": f"JSON parsing failed: {str(e)}",
                    "original_content": content[:200] + "..." if len(content) > 200 else content
                }

    def _fix_common_json_issues(self, content: str) -> str:
        """
        Fix common JSON formatting issues from OpenAI responses
        """
        # Remove any text before the first {
        if '{' in content:
            content = content[content.find('{'):]
        
        # Remove any text after the last }
        if '}' in content:
            content = content[:content.rfind('}') + 1]
        
        # Fix unterminated strings by finding unmatched quotes
        # This is a basic fix - more sophisticated parsing could be added
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Skip empty lines or comments
            if not line.strip() or line.strip().startswith('//'):
                continue
                
            # Fix missing quotes around property names
            line = re.sub(r'(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', line)
            
            # Fix unterminated strings at end of line (add closing quote before comma/brace)
            if '"' in line and line.count('"') % 2 == 1:
                # Find the last quote and see if string is unterminated
                last_quote = line.rfind('"')
                after_quote = line[last_quote + 1:].strip()
                if after_quote and after_quote[0] not in ',}]':
                    # Insert closing quote before comma or brace
                    if ',' in after_quote:
                        comma_pos = after_quote.find(',')
                        line = line[:last_quote + 1] + after_quote[:comma_pos] + '"' + after_quote[comma_pos:]
                    elif any(c in after_quote for c in '}]'):
                        for delimiter in '}]':
                            if delimiter in after_quote:
                                delim_pos = after_quote.find(delimiter)
                                line = line[:last_quote + 1] + after_quote[:delim_pos] + '"' + after_quote[delim_pos:]
                                break
                    else:
                        line = line + '"'
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines)

    async def analyze_word(self, word: str, response_format: str = "suggestions") -> Dict[str, Any]:
        """
        Analyze a single German word and return JSON shaped exactly for your DB:
        - Normalize everything into `word_forms`: [{feature_key, feature_value, form}]
        - For verbs also return `verb_props` matching your VerbProps model
        - Include translations + one example for UX

        Args:
            word: The word to analyze
            response_format: "suggestions" for 5 relevant words (flat array) or 
                           "ui_suggestions" for translation UI format (sections)

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
Analyze the German input "{word}" and provide intelligent assistance for German learning.

ANALYSIS APPROACH:
1. If "{word}" is VALID German (exact match or inflected form) → return found: true
2. If "{word}" looks like a GERMAN TYPO → correct it and return found: true  
3. If "{word}" is clearly NOT German → return found: false with suggestions

For VALID German words (including corrected typos), produce:

{{
  "found": true,
  "input_word": "{word}",
  "corrected_from": "{word}" (only if this was a typo correction),
  "lemma": "base lemma (corrected if needed)",
  "pos": "one or more of: noun|verb|vt|vi|vr|aux|modal|adj|adv|prep|det|art|pron|conj|interj|num|vi_impers|vt_impers|vi_prep_obj|vt_prep_obj",

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

For INVALID input (not German or unrecognizable), return:
{{
  "found": false,
  "input_word": "{word}",
  "suggestions": [
    {{"word": "gehen", "reason": "common verb for beginners", "pos": "verb"}},
    {{"word": "trinken", "reason": "essential daily verb", "pos": "verb"}},
    {{"word": "haben", "reason": "auxiliary verb", "pos": "verb"}},
    {{"word": "sein", "reason": "most important German verb", "pos": "verb"}},
    {{"word": "können", "reason": "modal verb", "pos": "verb"}}
  ],
  "message": "'{word}' is not recognized as German"
}}

SMART TYPO CORRECTION PATTERNS:
- Missing letters: "gehn" → "gehen"
- Wrong letters: "triken" → "trinken"  
- Missing umlauts: "konnen" → "können"
- Keyboard errors: "bidt" → "bist"
- Extra letters: "gehhen" → "gehen"
- Case errors: "Ich" → "ich"
- Inflection help: "trinke" → "trinken" (show infinitive)

GERMAN LEARNING CONTEXT AWARENESS:
- Prioritize A1-B2 level vocabulary
- Focus on common words students actually need
- Consider semantic context (verbs suggest related verbs)
- Avoid suggesting obscure or technical terms
- Help with verb conjugation learning patterns

EXAMPLES:
- Input: "gehn" → found: true, corrected_from: "gehn", lemma: "gehen"
- Input: "bist" → found: true (this IS valid German, no correction needed)
- Input: "triken" → found: true, corrected_from: "triken", lemma: "trinken"  
- Input: "xyz123" → found: false, suggestions: [common German learning words]
- Input: "qwerty" → found: false, suggestions: [beginner German vocabulary]

MANDATORY: Suggestions MUST contain exactly 5 German words - no more, no less.

STRICT REQUIREMENTS:
- For persons use EXACT: ich, du, er_sie_es, wir, ihr, sie_Sie
- For tenses use EXACT: praesens, praeteritum, perfekt, plusquamperfekt, futur_i, futur_ii, imperativ, konjunktiv_i, konjunktiv_ii
- Suggestions MUST contain exactly 5 German words
- Focus on German learning context, not random dictionary words
- Consider semantic relationships and learning progression
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
                max_tokens=2500,
            )

            if not resp or not resp.choices or not resp.choices[0].message:
                raise RuntimeError("Invalid OpenAI API response structure")
                
            content = resp.choices[0].message.content
            if not content:
                raise RuntimeError("Empty content from OpenAI API")
                
            data = self._parse_json_safely(content, word)
            # Debug: Check full response
            if not data.get("found"):
                try:
                    print(f"DEBUG - OpenAI returned {len(data.get('suggestions', []))} suggestions for '{word}'")
                except UnicodeEncodeError:
                    print(f"DEBUG - OpenAI returned {len(data.get('suggestions', []))} suggestions (Unicode characters present)")

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
            else:
                # For not found words, validate and ensure exactly 5 suggestions
                suggestions = data.get("suggestions", [])
                print(f"DEBUG - OpenAI raw response for '{word}': found {len(suggestions) if suggestions else 0} suggestions")
                if suggestions:
                    try:
                        validated_suggestions = self._validate_suggestions(suggestions)
                        print(f"DEBUG - After validation for '{word}': {len(validated_suggestions) if validated_suggestions else 0} validated suggestions")
                    except UnicodeEncodeError as e:
                        print(f"DEBUG - Unicode error during validation, using fallback suggestions: {e}")
                        # Use safe fallback suggestions without umlauts
                        validated_suggestions = [
                            {"word": "Hund", "pos": "noun", "meaning": "dog"},
                            {"word": "Haus", "pos": "noun", "meaning": "house"}, 
                            {"word": "gehen", "pos": "verb", "meaning": "to go"},
                            {"word": "gut", "pos": "adj", "meaning": "good"},
                            {"word": "Jahr", "pos": "noun", "meaning": "year"}
                        ]
                    
                    # Ensure exactly 5 suggestions - pad with common German words if needed
                    if len(validated_suggestions) < 5:
                        fallback_words = [
                            {"word": "Hund", "pos": "noun", "meaning": "dog"},
                            {"word": "Haus", "pos": "noun", "meaning": "house"}, 
                            {"word": "gehen", "pos": "verb", "meaning": "to go"},
                            {"word": "schön", "pos": "adj", "meaning": "beautiful"},
                            {"word": "Wasser", "pos": "noun", "meaning": "water"}
                        ]
                        # Add fallback words until we have 5
                        for fallback in fallback_words:
                            if len(validated_suggestions) >= 5:
                                break
                            # Don't add duplicates
                            if not any(s['word'].lower() == fallback['word'].lower() for s in validated_suggestions):
                                validated_suggestions.append(fallback)
                    
                    final_suggestions = validated_suggestions[:5]  # Ensure exactly 5
                else:
                    print(f"DEBUG - No suggestions returned by OpenAI for '{word}'")
                    # Provide 5 default suggestions
                    final_suggestions = [
                        {"word": "der", "pos": "art", "meaning": "the (masculine)"},
                        {"word": "sein", "pos": "verb", "meaning": "to be"},
                        {"word": "haben", "pos": "verb", "meaning": "to have"},
                        {"word": "gut", "pos": "adj", "meaning": "good"},
                        {"word": "Jahr", "pos": "noun", "meaning": "year"}
                    ]

                # Format response based on requested format
                if response_format == "ui_suggestions":
                    # Translation UI format (complex structure with sections)
                    data["ui_suggestions"] = {
                        "query": word,
                        "threshold_applied": 0.0,  # Not applicable for word analysis
                        "scenario": "not_found",
                        "sections": [
                            {
                                "type": "relevant_suggestions",
                                "suggestions": final_suggestions,
                                "display_mode": "multiple",
                                "cta": {
                                    "action": "pick_one_then_lookup",
                                    "lemma_candidates": [s["word"] for s in final_suggestions]
                                }
                            }
                        ],
                        "languages_shown": [],
                        "deduped_translations": [{"german_word": s["word"], "from": ["suggestions"]} for s in final_suggestions]
                    }
                    # Remove the flat suggestions array for ui_suggestions format
                    data.pop("suggestions", None)
                else:
                    # Default: flat suggestions array format (for regular word search)
                    data["suggestions"] = final_suggestions

            # Check for parsing errors and provide detailed feedback
            if data.get("error"):
                error_msg = f"JSON parsing failed for '{word}': {data.get('error')}"
                if data.get("original_content"):
                    error_msg += f" | Content preview: {data.get('original_content')[:100]}..."
                raise RuntimeError(error_msg)

            return data

        except Exception as e:
            print(f"OpenAI API error for word '{word}': {str(e)}")
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
        try:
            print(f"DEBUG - Validating {len(suggestions) if suggestions else 0} suggestions")
        except UnicodeEncodeError:
            print(f"DEBUG - Validating {len(suggestions) if suggestions else 0} suggestions (Unicode characters present)")
        if not suggestions or not isinstance(suggestions, list):
            print("DEBUG - No suggestions or not a list, returning empty")
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
        
        for i, suggestion in enumerate(suggestions):
            try:
                print(f"DEBUG - Processing suggestion {i}")
            except UnicodeEncodeError:
                print(f"DEBUG - Processing suggestion {i} (Unicode characters present)")
            if not isinstance(suggestion, dict):
                print(f"DEBUG - Suggestion {i} not a dict, skipping")
                continue
                
            word = suggestion.get('word', '').strip().lower()
            pos = suggestion.get('pos', '').strip().lower()
            meaning = suggestion.get('meaning', '').strip()
            try:
                print(f"DEBUG - Extracted word with pos='{pos}'")
            except UnicodeEncodeError:
                print(f"DEBUG - Extracted word with pos='{pos}' (Unicode characters present)")
            
            # Skip if missing required fields
            if not word or not pos or not meaning:
                print(f"DEBUG - Suggestion {i} missing required fields, skipping")
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
            
        print(f"DEBUG - Final validated suggestions: {valid_suggestions[:5]}")
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
            
            return self._parse_json_safely(response.choices[0].message.content, "translation")
            
        except Exception as e:
            raise
    async def detect_language_multi(self, text: str, max_langs: int = 5) -> Dict[str, Any]:
        """
        Returns top likely languages for 'text' (not thresholded here).
        {
        "candidates":[
            {"lang":"de","name":"German","confidence":0.92,"is_german":true},
            ...
        ]
        }
        """
        if not self.client:
            raise RuntimeError("OpenAI API key not set; language detection is unavailable")

        user_prompt = f"""
    Analyze the single token: "{text}"

    Return strict JSON with up to {max_langs} likely source languages, sorted by confidence (desc).
    If German is plausible, include it.

    JSON schema:
    {{
    "candidates": [
        {{"lang":"ISO-639-1","name":"Language Name","confidence":0.00,"is_german":true|false}}
    ]
    }}

    Rules:
    - Use ISO 639-1 (de,en,fr,es,it,zh,ru,pl,nl,sv,da,no,fi,cs,tr,pt,ja,ko,ar,he,el, etc.)
    - Confidence in [0,1].
    - JSON only. No extra text.
    """

        resp = await self.client.chat.completions.create(
            model=self.translation_model,
            messages=[
                {"role": "system", "content": "You are a precise language detector for single tokens. Output strict JSON only."},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=400,
        )
        data = self._parse_json_safely(resp.choices[0].message.content, f"lang_multi:{text[:40]}")
        cands = data.get("candidates", [])
        if not isinstance(cands, list):
            cands = []

        cleaned = []
        for c in cands:
            if not isinstance(c, dict):
                continue
            lang = (c.get("lang") or "").strip().lower()
            name = self._normalize_surface(c.get("name", "")) or lang
            try:
                conf = float(c.get("confidence", 0))
            except Exception:
                conf = 0.0
            is_de = bool(c.get("is_german", lang == "de"))
            if lang and 0.0 <= conf <= 1.0:
                cleaned.append({"lang": lang, "name": name, "confidence": conf, "is_german": is_de})

        cleaned.sort(key=lambda x: x["confidence"], reverse=True)
        return {"candidates": cleaned[:max_langs]}
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
            
            return self._parse_json_safely(response.choices[0].message.content, f"language_detection:{text[:20]}")
            
        except Exception as e:
            logging.error(f"Language detection error for text '{text}': {str(e)}")
            raise
    async def translate_ambiguous_to_german_v2(
        self,
        text: str,
        *,
        min_conf: float = 0.90,     # (1) threshold: show >= 0.90 only
        max_langs: int = 3,         # show at most 3 languages
        max_senses: int = 5         # cap meanings
    ) -> Dict[str, Any]:
        """
        Pipeline & UI contract:
        - detect up to 5 languages, keep only those >= min_conf, cap to max_langs
        - classify scenario (a/b/c/d) based on presence of German
        - for each non-German language, translate -> German (capped senses)
        - if German present, add compact German section (click to DB lookup)
        - return JSON the frontend can render directly
        """

        # 1) detect candidates (unfiltered), then threshold & cap
        det = await self.detect_language_multi(text, max_langs=5)
        all_cands = det.get("candidates", [])
        shown = [c for c in all_cands if c.get("confidence", 0.0) >= min_conf]
        shown.sort(key=lambda x: x["confidence"], reverse=True)
        shown = shown[:max_langs]

        has_german = any(c["lang"] == "de" for c in shown)
        non_de = [c for c in shown if c["lang"] != "de"]

        # scenario classification
        # a) only non-German (>=1) and German either absent or below threshold
        # b) 2-3 non-German languages (no German)
        # c) German + exactly 1 other
        # d) German + 2 or 3 others
        if has_german and len(non_de) == 0:
            scenario = "c"  # degenerate: German only (treat as c with zero others)
        elif has_german and len(non_de) == 1:
            scenario = "c"
        elif has_german and len(non_de) >= 2:
            scenario = "d"
        elif not has_german and len(non_de) == 1:
            scenario = "a"
        elif not has_german and len(non_de) >= 2:
            scenario = "b"
        else:
            scenario = "none"  # nobody passed threshold

        sections = []
        dedup = {}

        # 2) If German is confidently detected, add compact German section
        if has_german:
            de_c = next(c for c in shown if c["lang"] == "de")
            sections.append({
                "type": "german_candidate",
                "lang": "de",
                "language_name": de_c["name"],
                "confidence": de_c["confidence"],
                # compact: show the exact query as lemma; clicking triggers DB lookup by lemma
                "lemma": self._normalize_surface(text),
                "display_mode": "compact",   # (c1.1) compact card; user clicks to check DB
                "cta": {"action": "lookup_in_db", "lemma": self._normalize_surface(text)}
            })

        # 3) For each non-German language shown, produce German translations
        for c in non_de:
            lang = c["lang"]
            name = c["name"]
            conf = c["confidence"]

            try:
                tx = await self.translate_to_german(text, source_language=lang)
            except Exception as e:
                logging.warning(f"translate_to_german failed for '{text}' [{lang}]: {e}")
                tx = {"translations": [], "is_ambiguous": False, "source_language": lang}

            translations = tx.get("translations", []) or []

            # cleanup + cap senses
            clean = []
            seen = set()
            for t in translations:
                if not isinstance(t, dict):
                    continue
                gw = self._normalize_surface(t.get("german_word", ""))
                if not gw or gw.lower() in seen:
                    continue
                seen.add(gw.lower())
                clean.append({
                    "german_word": gw,
                    "context": self._normalize_surface(t.get("context", "")),
                    "pos": (t.get("pos") or "").strip().lower() or "noun"
                })
                if len(clean) >= max_senses:
                    break

            has_multiple = len(clean) > 1
            display_mode = "multiple" if has_multiple else "single"

            # dedupe bucket
            for t in clean:
                key = t["german_word"].lower()
                dd = dedup.setdefault(key, {"german_word": t["german_word"], "from": []})
                dd["from"].append(lang)

            # section for this language
            sec = {
                "type": "source_language",
                "lang": lang,
                "language_name": name,
                "confidence": conf,
                "translations": clean,
                "has_multiple": has_multiple,
                "display_mode": display_mode,
            }
            # CTAs
            if has_multiple:
                sec["cta"] = {
                    "action": "pick_one_then_lookup",
                    "lemma_candidates": [t["german_word"] for t in clean]
                }
            elif clean:
                sec["cta"] = {
                    "action": "lookup_in_db",
                    "lemma": clean[0]["german_word"]
                }
            sections.append(sec)

        # 4) Final JSON for UI
        result = {
            "query": text,
            "threshold_applied": min_conf,
            "scenario": scenario,                 # "a" | "b" | "c" | "d" | "none"
            "sections": sections,                 # render these in order
            "languages_shown": [s["lang"] for s in sections],
            "deduped_translations": list(dedup.values()),
        }

        # If nobody passed threshold, tell the UI explicitly
        if scenario == "none":
            result["message"] = "No language passed confidence threshold. You can lower the threshold or try again."

        return result
    async def translate_to_german(self, text: str, source_language: str = None) -> Dict[str, Any]:
        """
        Translate a single word to German with strict constraints:
        - Return genuine German words (no English exonyms)
        - JSON shape: {"translations":[{"german_word","context","pos"}], "is_ambiguous":bool, "source_language": "xx"}
        - Post-validate and autocorrect common exonyms (Austria->Österreich, etc.)
        """
        if not self.client:
            raise RuntimeError("OpenAI API key not set; translation is unavailable")

        src = source_language or "unknown"

        # Strong, explicit prompt (per MD recommendations)
        # Key ideas:
        #  - “GERMAN (Deutsch) ONLY”
        #  - Concrete examples of correct endonyms
        #  - Validation statement that english exonyms are invalid
        prompt = f"""
Translate this {src} word to GERMAN (Deutsch) as a single WORD (not a sentence): "{text}"

CRITICAL REQUIREMENTS:
- Output MUST be an ACTUAL German word (Endonym), NEVER English.
- If the correct German form includes umlauts/ß, use them (ä, ö, ü, ß).
- Return JSON only.

Examples of CORRECT German country names (do NOT output English):
- Austria → Österreich
- Germany → Deutschland
- Switzerland → Schweiz
- France → Frankreich
- United States → Vereinigte Staaten / USA
- Netherlands → Niederlande

Return JSON:
{{
  "translations": [
    {{
      "german_word": "GERMAN_WORD_ONLY",
      "context": "brief meaning or domain",
      "pos": "noun|verb|adjective|interj|adv|prep|det|pron|conj|num"
    }}
  ],
  "is_ambiguous": true|false,
  "source_language": "{src}"
}}

VALIDATION:
- "german_word" MUST be German. English exonyms (e.g., "Austria") are invalid.
- If you are unsure, pick the most common German endonym used by native speakers.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.translation_model,
                messages=[
                    {"role": "system", "content": "You are a precise German lexicon translator. Output strict JSON, no commentary."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,       # more deterministic (per MD)
                max_tokens=600         # allow enough room (per MD)
            )

            raw = self._parse_json_safely(response.choices[0].message.content, f"translate_to_german:{text[:40]}")
            # Normalize structure
            translations = raw.get("translations") if isinstance(raw, dict) else None
            if not isinstance(translations, list):
                translations = []

            cleaned: list[Dict[str, str]] = []
            for item in translations:
                if not isinstance(item, dict):
                    continue
                gw = (item.get("german_word") or "").strip()
                ctx = (item.get("context") or "").strip()
                pos = (item.get("pos") or "").strip().lower()

                if not gw:
                    continue

                # First, correct very common English exonyms (Austria, Germany, …)
                exonym_key = gw.lower()
                if exonym_key in self._EXONYM_TO_DE:
                    gw = self._EXONYM_TO_DE[exonym_key]

                # If still looks English, reject it
                if not self._looks_like_german_word(gw):
                    continue

                gw = self._normalize_german_output(gw, pos=pos or "noun")

                cleaned.append({
                    "german_word": gw,
                    "context": ctx,
                    "pos": pos or "noun"
                })

            # If nothing survived, try a reinforced retry once
            if not cleaned:
                retry_prompt = f"""
Your previous answer contained a non-German form. Try again.

Task: Translate the {src} word to an ACTUAL German word (Deutsch), one word only.
Word: "{text}"

Rules:
- English forms are invalid. For example, output "Österreich" not "Austria".
- Use umlauts/ß when correct.
- JSON only.

Return JSON:
{{
  "translations": [{{"german_word":"...", "context":"", "pos":"noun|verb|adj|..."}}]],
  "is_ambiguous": false,
  "source_language": "{src}"
}}
"""
                response2 = await self.client.chat.completions.create(
                    model=self.translation_model,
                    messages=[
                        {"role": "system", "content": "You are a strict German translator. Output JSON only."},
                        {"role": "user", "content": retry_prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                    max_tokens=400
                )
                raw2 = self._parse_json_safely(response2.choices[0].message.content, f"translate_to_german:retry:{text[:40]}")
                translations2 = raw2.get("translations") if isinstance(raw2, dict) else None
                if isinstance(translations2, list):
                    for item in translations2:
                        if not isinstance(item, dict):
                            continue
                        gw = (item.get("german_word") or "").strip()
                        ctx = (item.get("context") or "").strip()
                        pos = (item.get("pos") or "").strip().lower()
                        if not gw:
                            continue
                        # Exonym correction + validation
                        exonym_key = gw.lower()
                        if exonym_key in self._EXONYM_TO_DE:
                            gw = self._EXONYM_TO_DE[exonym_key]
                        if not self._looks_like_german_word(gw):
                            continue
                        gw = self._normalize_german_output(gw, pos=pos or "noun")
                        cleaned.append({
                            "german_word": gw,
                            "context": ctx,
                            "pos": pos or "noun"
                        })

            result = {
                "translations": cleaned,
                "is_ambiguous": len(cleaned) > 1,
                "source_language": src
            }

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
    def _looks_like_german_word(self, w: str) -> bool:
        """
        Lightweight check that a token is plausibly German (not English).
        This is heuristic by design; we prefer false negatives to false positives.
        """
        if not w or not isinstance(w, str):
            return False
        s = w.strip()

        # Obvious German signals
        if any(ch in s for ch in "äöüÄÖÜß"):
            return True

        # Common German morphology/orthography signals
        lower = s.lower()
        germanish_suffixes = (
            "ung", "heit", "keit", "schaft", "tion", "tät", "chen", "lein", "lich", "ig", "bar",
            "ieren", "en", "eln", "ern", "keit", "nis"
        )
        if any(lower.endswith(suf) for suf in germanish_suffixes):
            return True

        # Capitalized single-word nouns (not perfect, but useful)
        if " " not in s and s[:1].isupper():
            return True

        # Reject obvious English stopwords/exonyms (handled elsewhere too)
        english_stops = {"the","and","or","a","an","is","are"}
        if lower in english_stops:
            return False

        # Default: neutral (allow)
        return True

    def _normalize_german_output(self, word: str, pos: str = "") -> str:
        """
        Normalize spacing and capitalization for DB search & display.
        - Keep proper capitalization (German nouns capitalized, country names usually capitalized).
        - Preserve umlauts/ß if present.
        """
        if not word:
            return word
        s = " ".join(word.strip().split())
        # For single-token nouns or proper names, Titlecase is usually correct
        if pos and pos.lower() in {"noun"} and " " not in s:
            return s[:1].upper() + s[1:]
        return s
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