"""
Enhanced Search Service - Addresses user feedback and concerns
"""
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.models.word import WordLemma, Translation, Example, WordForm
from app.models.user import User
from app.services.openai_service import OpenAIService
import re

class EnhancedSearchService:
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def search_with_suggestions(
        self, 
        db: Session, 
        query: str, 
        user: User,
        max_suggestions: int = 5
    ) -> Dict[str, Any]:
        """
        Enhanced search that returns similarity scores and multiple suggestions
        """
        
        # Step 1: Detect input language and handle cross-language queries
        input_language = self.detect_input_language(query)
        
        if input_language != 'german':
            # Handle non-German input (e.g., Chinese "走" should translate to German)
            return await self.handle_cross_language_search(db, query, input_language, user)
        
        # Step 2: Multi-level German word search
        search_results = await self.comprehensive_german_search(db, query, user)
        
        # Step 3: If no exact match, provide ranked suggestions with similarity scores
        if not search_results.get('found'):
            suggestions = await self.get_ranked_suggestions(db, query, max_suggestions)
            search_results['suggestions_with_scores'] = suggestions
        
        return search_results
    
    def detect_input_language(self, text: str) -> str:
        """Detect the language of input text"""
        
        # Check for Chinese characters
        if re.search(r'[\u4e00-\u9fff]', text):
            return 'chinese'
        
        # Check for common non-German patterns
        if re.search(r'[а-яё]', text, re.IGNORECASE):  # Cyrillic
            return 'russian'
        
        if re.search(r'[αβγδεζηθικλμνξοπρστυφχψω]', text, re.IGNORECASE):  # Greek
            return 'greek'
        
        # Check for English-specific patterns (common English words not in German)
        english_indicators = ['the', 'and', 'you', 'that', 'this', 'have', 'with', 'for', 'not', 'are', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'how', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were']
        if text.lower() in english_indicators:
            return 'english'
        
        # Check for German-specific patterns
        german_indicators = ['der', 'die', 'das', 'ein', 'eine', 'und', 'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'auf', 'für', 'mit', 'zu', 'von', 'bei', 'nach', 'über', 'durch', 'ohne', 'um']
        if text.lower() in german_indicators:
            return 'german'
        
        # Check for German character patterns (ä, ö, ü, ß)
        if re.search(r'[äöüß]', text, re.IGNORECASE):
            return 'german'
        
        # Default to German for Latin script
        return 'german'
    
    async def handle_cross_language_search(
        self, 
        db: Session, 
        query: str, 
        input_language: str, 
        user: User
    ) -> Dict[str, Any]:
        """Handle searches in non-German languages"""
        
        # Use OpenAI to translate to German first
        translation_prompt = f"""
        The user searched for "{query}" in {input_language}. 
        Please translate this to German and return a JSON response:
        
        {{
            "german_translation": "German translation of the word/phrase",
            "confidence": 0.95,  // confidence level 0.0-1.0
            "alternative_translations": ["alt1", "alt2", "alt3"],
            "original_language": "{input_language}",
            "original_text": "{query}"
        }}
        
        If the input is not a real word or cannot be translated, return:
        {{
            "german_translation": null,
            "confidence": 0.0,
            "message": "Unable to translate '{query}' to German",
            "original_language": "{input_language}",
            "original_text": "{query}"
        }}
        """
        
        try:
            translation_result = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": "You are a precise multilingual translator. Always respond with valid JSON."},
                    {"role": "user", "content": translation_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=500
            )
            
            import json
            translation_data = json.loads(translation_result.choices[0].message.content)
            
            if translation_data.get('german_translation'):
                # Search for the German translation
                german_query = translation_data['german_translation']
                result = await self.comprehensive_german_search(db, german_query, user)
                
                # Add translation context to result
                result['translation_context'] = {
                    'original_query': query,
                    'original_language': input_language,
                    'german_translation': german_query,
                    'confidence': translation_data.get('confidence', 0.5),
                    'alternatives': translation_data.get('alternative_translations', [])
                }
                
                return result
            else:
                return {
                    'found': False,
                    'original': query,
                    'message': f"Unable to translate '{query}' from {input_language} to German",
                    'source': 'translation_failed'
                }
                
        except Exception as e:
            return {
                'found': False,
                'original': query,
                'message': f"Translation error: {str(e)}",
                'source': 'translation_error'
            }
    
    async def comprehensive_german_search(
        self, 
        db: Session, 
        query: str, 
        user: User
    ) -> Dict[str, Any]:
        """Comprehensive search through all German word formats"""
        
        # 1. Direct lemma match
        result = await self.search_direct_lemma(db, query)
        if result:
            # Check if we have multiple results (different POS)
            if isinstance(result, list) and len(result) > 1:
                return await self.format_multiple_results(result, 'multiple_pos', query)
            else:
                # Single result
                single_result = result[0] if isinstance(result, list) else result
                return await self.format_found_result(single_result, 'direct_lemma', query)
        
        # 2. Inflected form search (gehe -> gehen)
        result = await self.search_inflected_forms(db, query)
        if result:
            return await self.format_found_result(result, 'inflected_form', query)
        
        # 3. Article removal (der Tisch -> Tisch)
        result = await self.search_without_articles(db, query)
        if result:
            return await self.format_found_result(result, 'article_removed', query)
        
        # 4. Compound word variations
        result = await self.search_compound_variations(db, query)
        if result:
            return await self.format_found_result(result, 'compound_variation', query)
        
        # 5. Case variations and partial matches
        result = await self.search_case_variations(db, query)
        if result:
            return await self.format_found_result(result, 'case_variation', query)
        
        # 6. If still not found, try smart typo detection (replaces old OpenAI validation)
        return await self.search_with_smart_typo_detection(db, query, user)
    
    def german_case_variants(self, text: str) -> List[str]:
        """Generate proper German case variants handling umlauts correctly"""
        variants = []
        
        # Original text
        variants.append(text)
        
        # Python's built-in case conversions
        variants.extend([
            text.lower(),
            text.upper(), 
            text.capitalize(),
            text.title()
        ])
        
        # Manual German character mappings for problematic umlauts
        umlaut_mappings = {
            'ä': 'Ä', 'ö': 'Ö', 'ü': 'Ü', 'ß': 'ß',
            'Ä': 'ä', 'Ö': 'ö', 'Ü': 'ü'
        }
        
        # Create additional variants with manual umlaut case conversion
        for variant in list(variants):
            manual_variant = ''
            for char in variant:
                if char in umlaut_mappings:
                    manual_variant += umlaut_mappings[char]
                else:
                    manual_variant += char
            if manual_variant not in variants:
                variants.append(manual_variant)
        
        # Remove duplicates while preserving order
        unique_variants = []
        for variant in variants:
            if variant not in unique_variants:
                unique_variants.append(variant)
        
        return unique_variants

    async def search_direct_lemma(self, db: Session, query: str) -> Optional[WordLemma]:
        """Direct lemma search - now returns multiple results if multiple POS exist"""
        from sqlalchemy.orm import joinedload
        
        all_matches = []
        
        # Get all possible case variants for German text including proper umlaut handling
        variants = self.german_case_variants(query)
        
        print(f"DEBUG: search_direct_lemma for '{query}', trying variants: {variants}")
        
        # Search for all variants
        for variant in variants:
            matches = db.query(WordLemma).options(
                joinedload(WordLemma.translations),
                joinedload(WordLemma.examples),
                joinedload(WordLemma.forms)
            ).filter(WordLemma.lemma == variant).all()
            
            # Add if not already included
            for match in matches:
                if match.id not in [m.id for m in all_matches]:
                    all_matches.append(match)
        
        print(f"DEBUG: search_direct_lemma for '{query}' found {len(all_matches)} matches")
        for match in all_matches:
            print(f"  - {match.lemma} ({match.pos}) ID {match.id}")
        
        # Return multiple results if found, single result, or None
        if len(all_matches) > 1:
            return all_matches  # Multiple results - will trigger choice selector
        elif len(all_matches) == 1:
            return all_matches[0]  # Single result
        else:
            return None  # No results
    
    async def search_inflected_forms(self, db: Session, query: str) -> Optional[WordLemma]:
        """Search through all inflected forms"""
        from sqlalchemy.orm import joinedload
        word_form = db.query(WordForm).options(
            joinedload(WordForm.lemma).joinedload(WordLemma.translations),
            joinedload(WordForm.lemma).joinedload(WordLemma.examples),
            joinedload(WordForm.lemma).joinedload(WordLemma.forms)
        ).filter(WordForm.form.ilike(query)).first()
        return word_form.lemma if word_form else None
    
    async def search_without_articles(self, db: Session, query: str) -> Optional[WordLemma]:
        """Search after removing German articles"""
        from sqlalchemy.orm import joinedload
        clean_query = self.remove_german_articles(query)
        if clean_query != query:
            return db.query(WordLemma).options(
                joinedload(WordLemma.translations),
                joinedload(WordLemma.examples),
                joinedload(WordLemma.forms)
            ).filter(WordLemma.lemma.ilike(clean_query)).first()
        return None
    
    async def search_compound_variations(self, db: Session, query: str) -> Optional[WordLemma]:
        """Search for compound word variations - only for words starting or ending with query"""
        from sqlalchemy.orm import joinedload
        
        # Only search compound words if query is likely a valid German word component
        # and only match at word boundaries (start/end of compound words)
        if len(query) >= 6:
            # Search for words that START with the query (e.g., "haus" -> "Hausfrau")
            result = db.query(WordLemma).options(
                joinedload(WordLemma.translations),
                joinedload(WordLemma.examples),
                joinedload(WordLemma.forms)
            ).filter(
                WordLemma.lemma.ilike(f'{query}%')
            ).first()
            
            if result:
                return result
                
            # Search for words that END with the query (e.g., "haus" -> "Krankenhaus")
            result = db.query(WordLemma).options(
                joinedload(WordLemma.translations),
                joinedload(WordLemma.examples),
                joinedload(WordLemma.forms)
            ).filter(
                WordLemma.lemma.ilike(f'%{query}')
            ).first()
            
            return result
        return None
    
    async def search_case_variations(self, db: Session, query: str) -> Optional[WordLemma]:
        """Search with different case variations"""
        from sqlalchemy.orm import joinedload
        variations = [
            query.lower(),
            query.upper(),
            query.capitalize(),
            query.title()
        ]
        
        for variation in variations:
            if variation != query:
                result = db.query(WordLemma).options(
                    joinedload(WordLemma.translations),
                    joinedload(WordLemma.examples),
                    joinedload(WordLemma.forms)
                ).filter(WordLemma.lemma.ilike(variation)).first()
                if result:
                    return result
        return None
    
    async def get_ranked_suggestions(
        self, 
        db: Session, 
        query: str, 
        max_suggestions: int = 5
    ) -> List[Dict[str, Any]]:
        """Get intelligent AI-powered suggestions instead of ridiculous similarity matching"""
        
        if len(query) < 2:
            return []
        
        try:
            # Use OpenAI to get intelligent suggestions
            print(f"Getting AI suggestions for '{query}'...")
            
            system_prompt = f"""You are a German language expert. A user searched for "{query}" but it wasn't found in our German vocabulary database.

Provide 3-5 intelligent suggestions for what they might have meant. Consider:

1. Common German words that sound similar
2. Possible typos of German words  
3. Inflected forms they might have meant (like "bist" -> suggest "sein")
4. Related German vocabulary

Return ONLY a JSON array of suggestions:
[
  {{"word": "german_word", "reason": "why you suggest this", "pos": "noun/verb/etc"}},
  {{"word": "another_word", "reason": "explanation", "pos": "pos"}}
]

Focus on useful, relevant German vocabulary. NO English words. NO made-up words."""

            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User searched: {query}"}
                ],
                max_tokens=400,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            # Parse AI response
            import json
            try:
                ai_suggestions = json.loads(ai_response)
            except json.JSONDecodeError:
                print(f"Failed to parse AI suggestions: {ai_response}")
                return []
            
            # Convert AI suggestions to our format and validate against database
            suggestions = []
            
            for ai_suggestion in ai_suggestions[:max_suggestions]:
                word = ai_suggestion.get('word', '').strip()
                reason = ai_suggestion.get('reason', '').strip()
                pos = ai_suggestion.get('pos', 'unknown').strip()
                
                if not word:
                    continue
                
                # Check if the suggested word exists in our database
                existing_word = db.query(WordLemma).filter(WordLemma.lemma.ilike(word)).first()
                
                if existing_word:
                    # Get translations for existing words
                    translations = db.query(Translation).filter(
                        Translation.lemma_id == existing_word.id,
                        Translation.lang_code == 'en'
                    ).limit(2).all()
                    
                    translation_preview = [t.text for t in translations] if translations else []
                    
                    suggestions.append({
                        'word': existing_word.lemma,
                        'pos': existing_word.pos or pos,
                        'meaning': ', '.join(translation_preview) if translation_preview else reason,
                        'source': 'ai_suggestion'
                    })
                else:
                    # Include AI suggestion even if not in database
                    suggestions.append({
                        'word': word,
                        'pos': pos,
                        'meaning': reason,
                        'source': 'ai_suggestion_new'
                    })
            
            print(f"Generated {len(suggestions)} AI-powered suggestions for '{query}'")
            return suggestions
            
        except Exception as e:
            print(f"AI suggestion error for '{query}': {e}")
            # Fallback to empty suggestions instead of broken similarity search
            return []
    
    def get_confidence_level(self, similarity: float) -> str:
        """Convert similarity score to confidence level"""
        if similarity >= 0.9:
            return "very_high"
        elif similarity >= 0.8:
            return "high"
        elif similarity >= 0.6:
            return "medium"
        elif similarity >= 0.4:
            return "low"
        else:
            return "very_low"
    
    async def search_with_smart_typo_detection(
        self, 
        db: Session, 
        query: str, 
        user: User
    ) -> Dict[str, Any]:
        """Smart AI-powered typo detection for translate mode with German learning context"""
        
        enhanced_prompt = f"""
        You are a German language tutor. Analyze the input "{query}" in German learning context.
        
        ANALYSIS APPROACH:
        1. If "{query}" is valid German → mark found: true
        2. If "{query}" looks like a German typo → provide corrections
        3. If "{query}" is clearly not German → mark found: false
        
        For VALID German words, return:
        {{
            "found": true,
            "input_word": "{query}",
            "lemma": "base form",
            "pos": "noun|verb|adjective|adverb",
            "article": "der|die|das",
            "translations_en": ["meaning1", "meaning2"],
            "translations_zh": ["翻译1", "翻译2"],
            "example": {{"de": "German sentence", "en": "English", "zh": "中文"}}
        }}
        
        For LIKELY TYPOS, provide context-aware corrections:
        {{
            "found": false,
            "input_word": "{query}",
            "likely_typo": true,
            "smart_corrections": [
                {{
                    "corrected_word": "gehen",
                    "typo_pattern": "missing_letter_e",
                    "confidence": 0.95,
                    "explanation": "'{query}' is likely 'gehen' with missing 'e'",
                    "learning_context": "common infinitive verb",
                    "semantic_field": "movement_verbs"
                }}
            ]
        }}
        
        For NON-GERMAN input:
        {{
            "found": false,
            "input_word": "{query}",
            "likely_typo": false,
            "reason": "not_german_pattern",
            "contextual_suggestions": [
                {{"word": "gehen", "reason": "basic movement verb", "level": "A1"}},
                {{"word": "haben", "reason": "essential auxiliary verb", "level": "A1"}},
                {{"word": "sein", "reason": "most important German verb", "level": "A1"}}
            ]
        }}
        
        TYPO PATTERNS to recognize:
        - Missing letters: "gehn" → "gehen"
        - Wrong letters: "triken" → "trinken"
        - Missing umlauts: "konnen" → "können" 
        - Keyboard errors: "bidt" → "bist"
        - Extra letters: "gehhen" → "gehen"
        
        CONTEXT AWARENESS RULES:
        - For verbs: suggest related verbs or infinitive forms
        - For nouns: consider semantic fields (animals, food, family, etc.)
        - Focus on German learning vocabulary (A1-B2 level)
        - Avoid suggesting unrelated words even if similar spelling
        - Consider what German students actually need to learn
        
        EXAMPLES:
        - "bist" → found: true (valid German, 2nd person singular of 'sein')
        - "gehn" → corrected_word: "gehen", learning_context: "basic movement verb"
        - "triken" → corrected_word: "trinken", learning_context: "daily activity verb"
        """
        
        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": "You are a German language expert specializing in student learning context. Focus on meaningful corrections and suggestions. Always respond with valid JSON."},
                    {"role": "user", "content": enhanced_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
                temperature=0.1
            )
            
            import json
            analysis = json.loads(response.choices[0].message.content)
            
            if analysis.get('found'):
                # Valid German word
                saved_word = await self.save_openai_analysis(db, query, analysis, user)
                return await self.format_found_result(saved_word, 'ai_validated_word', query)
                
            elif analysis.get('likely_typo'):
                # Process context-aware typo corrections
                corrections = analysis.get('smart_corrections', [])
                validated_suggestions = []
                
                for correction in corrections[:4]:
                    word = correction.get('corrected_word', '').strip()
                    if word:
                        existing_word = db.query(WordLemma).filter(
                            WordLemma.lemma.ilike(word)
                        ).first()
                        
                        if existing_word:
                            translations = [t.text for t in existing_word.translations if t.lang_code == 'en'][:2]
                            
                            validated_suggestions.append({
                                'word': existing_word.lemma,
                                'pos': existing_word.pos,
                                'meaning': ', '.join(translations) if translations else correction.get('explanation', ''),
                                'explanation': correction.get('explanation', ''),
                                'learning_context': correction.get('learning_context', ''),
                                'confidence': correction.get('confidence', 0.8),
                                'source': 'ai_context_aware_typo'
                            })
                
                return {
                    'found': False,
                    'original': query,
                    'likely_typo': True,
                    'smart_suggestions': validated_suggestions,
                    'message': f"'{query}' not found. Did you mean one of these contextually relevant words?",
                    'source': 'ai_smart_typo_detection'
                }
                
            else:
                # Not German - provide learning-focused suggestions
                contextual_suggestions = analysis.get('contextual_suggestions', [])
                validated_suggestions = []
                
                for suggestion in contextual_suggestions[:5]:
                    word = suggestion.get('word', '').strip()
                    if word:
                        existing_word = db.query(WordLemma).filter(
                            WordLemma.lemma.ilike(word)
                        ).first()
                        
                        if existing_word:
                            translations = [t.text for t in existing_word.translations if t.lang_code == 'en'][:2]
                            
                            validated_suggestions.append({
                                'word': existing_word.lemma,
                                'pos': existing_word.pos,
                                'meaning': ', '.join(translations) if translations else suggestion.get('reason', ''),
                                'learning_level': suggestion.get('level', 'A2'),
                                'reason': suggestion.get('reason', 'common German word'),
                                'source': 'ai_learning_suggestion'
                            })
                
                return {
                    'found': False,
                    'original': query,
                    'likely_typo': False,
                    'contextual_suggestions': validated_suggestions,
                    'message': f"'{query}' doesn't appear to be German. Here are some common German words to learn:",
                    'source': 'ai_learning_focused'
                }
                
        except Exception as e:
            print(f"Smart typo detection error: {e}")
            return {
                'found': False,
                'original': query,
                'message': f"Analysis error: {str(e)}",
                'source': 'ai_error'
            }
    
    def remove_german_articles(self, text: str) -> str:
        """Remove German articles from text"""
        text = text.strip()
        articles = ['der ', 'die ', 'das ', 'ein ', 'eine ', 'einen ', 'einem ', 'einer ']
        
        for article in articles:
            if text.lower().startswith(article.lower()):
                return text[len(article):].strip()
        
        return text
    
    def calculate_similarity(self, word1: str, word2: str) -> float:
        """Calculate similarity using Levenshtein distance"""
        if word1 == word2:
            return 1.0
        
        len1, len2 = len(word1), len(word2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Dynamic programming matrix for edit distance
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if word1[i-1] == word2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(
                        dp[i-1][j] + 1,     # deletion
                        dp[i][j-1] + 1,     # insertion
                        dp[i-1][j-1] + 1    # substitution
                    )
        
        edit_distance = dp[len1][len2]
        max_len = max(len1, len2)
        
        return 1.0 - (edit_distance / max_len)
    
    async def format_multiple_results(
        self,
        words: List[WordLemma],
        search_method: str,
        original_query: str
    ) -> Dict[str, Any]:
        """Format multiple word results for user selection"""
        
        choices = []
        
        for word in words:
            # Get basic info for each choice
            from app.models.word import Translation
            
            # Get first few translations
            translations_en = []
            translations_zh = []
            
            for translation in word.translations:
                if translation.lang_code == 'en' and len(translations_en) < 3:
                    translations_en.append(translation.text)
                elif translation.lang_code == 'zh' and len(translations_zh) < 3:
                    translations_zh.append(translation.text)
            
            # Get article for nouns
            article = ""
            if word.pos.lower() == 'noun':
                for form in word.forms:
                    if form.feature_key == 'article':
                        article = form.form
                        break
            
            choice_data = {
                'lemma_id': word.id,
                'lemma': word.lemma,
                'pos': word.pos,
                'display_name': f"{article} {word.lemma}".strip() if article else word.lemma,
                'pos_display': self.get_pos_display_name(word.pos),
                'translations_en': translations_en,
                'translations_zh': translations_zh,
                'preview': self.get_word_preview(word)
            }
            
            choices.append(choice_data)
        
        return {
            'found': True,
            'multiple_choices': True,
            'original_query': original_query,
            'search_method': search_method,
            'choices': choices,
            'message': f"'{original_query}' has multiple meanings. Please select the one you want:",
            'choice_count': len(choices)
        }
    
    def get_pos_display_name(self, pos: str) -> str:
        """Get user-friendly display name for part of speech"""
        pos_map = {
            'noun': 'Noun (名词)',
            'verb': 'Verb (动词)', 
            'adjective': 'Adjective (形容词)',
            'adverb': 'Adverb (副词)',
            'preposition': 'Preposition (介词)',
            'pronoun': 'Pronoun (代词)',
            'conjunction': 'Conjunction (连词)',
            'interjection': 'Interjection (感叹词)'
        }
        return pos_map.get(pos.lower(), pos.capitalize())
    
    def get_word_preview(self, word: WordLemma) -> str:
        """Get a brief preview of the word for selection"""
        if word.pos.lower() == 'noun':
            # For nouns, show article + lemma
            article = ""
            for form in word.forms:
                if form.feature_key == 'article':
                    article = form.form
                    break
            return f"{article} {word.lemma}".strip()
        elif word.pos.lower() == 'verb':
            # For verbs, show infinitive
            return f"zu {word.lemma}"
        else:
            return word.lemma
    
    async def format_found_result(
        self, 
        word: WordLemma, 
        search_method: str, 
        original_query: str
    ) -> Dict[str, Any]:
        """Format a found word result"""
        
        # Get translations, examples, and word forms
        from app.models.word import Translation, Example, WordForm
        
        translations_en = []
        translations_zh = []
        example = None
        word_forms = {}
        
        # Get translations from database
        translations = word.translations if hasattr(word, 'translations') and word.translations else []
        for trans in translations:
            if trans.lang_code == 'en':
                translations_en.append(trans.text)
            elif trans.lang_code == 'zh':
                translations_zh.append(trans.text)
        
        # Get example from database  
        examples = word.examples if hasattr(word, 'examples') and word.examples else []
        if examples:
            example = {
                'de': examples[0].de_text,
                'en': examples[0].en_text,
                'zh': examples[0].zh_text
            }
        
        # Get word forms (conjugations/declensions) from database
        forms = word.forms if hasattr(word, 'forms') and word.forms else []
        article = None
        plural = None
        noun_props = {}
        verb_props = {}
        tables = {}
        
        for form in forms:
            if form.feature_key and form.feature_value:
                if form.feature_key not in word_forms:
                    word_forms[form.feature_key] = {}
                word_forms[form.feature_key][form.feature_value] = form.form
                
                # Extract article for nouns
                if form.feature_key == 'article' and (word.pos == 'noun' or word.pos == 'NOUN'):
                    article = form.form
                
                # Extract plural for nouns
                if form.feature_key == 'plural' and (word.pos == 'noun' or word.pos == 'NOUN'):
                    plural = form.form
                    noun_props['plural'] = form.form
                
                # Extract verb properties
                if form.feature_key == 'separable' and (word.pos == 'verb' or word.pos == 'VERB'):
                    verb_props['separable'] = form.form == 'true'
                if form.feature_key == 'aux' and (word.pos == 'verb' or word.pos == 'VERB'):
                    verb_props['aux'] = form.form
                if form.feature_key == 'partizip_ii' and (word.pos == 'verb' or word.pos == 'VERB'):
                    verb_props['partizip_ii'] = form.form
        
        # Build tables for verbs from tense data
        if (word.pos == 'verb' or word.pos == 'VERB') and 'tense' in word_forms:
            tense_data = word_forms['tense']
            
            # Build Präsens table
            if any(key.startswith('praesens_') for key in tense_data.keys()):
                tables['praesens'] = {
                    'ich': tense_data.get('praesens_ich'),
                    'du': tense_data.get('praesens_du'),
                    'er_sie_es': tense_data.get('praesens_er_sie_es'),
                    'wir': tense_data.get('praesens_wir'),
                    'ihr': tense_data.get('praesens_ihr'),
                    'sie_Sie': tense_data.get('praesens_sie_Sie')
                }
            
            # Build Präteritum table
            if any(key.startswith('praeteritum_') for key in tense_data.keys()):
                tables['praeteritum'] = {
                    'ich': tense_data.get('praeteritum_ich'),
                    'du': tense_data.get('praeteritum_du'),
                    'er_sie_es': tense_data.get('praeteritum_er_sie_es'),
                    'wir': tense_data.get('praeteritum_wir'),
                    'ihr': tense_data.get('praeteritum_ihr'),
                    'sie_Sie': tense_data.get('praeteritum_sie_Sie')
                }
            
            # Build Perfekt table
            if any(key.startswith('perfekt_') for key in tense_data.keys()):
                tables['perfekt'] = {
                    'ich': tense_data.get('perfekt_ich'),
                    'du': tense_data.get('perfekt_du'),
                    'er_sie_es': tense_data.get('perfekt_er_sie_es'),
                    'wir': tense_data.get('perfekt_wir'),
                    'ihr': tense_data.get('perfekt_ihr'),
                    'sie_Sie': tense_data.get('perfekt_sie_Sie')
                }
            
            # Build other tenses similarly
            if any(key.startswith('plusquamperfekt_') for key in tense_data.keys()):
                tables['plusquamperfekt'] = {
                    'ich': tense_data.get('plusquamperfekt_ich'),
                    'du': tense_data.get('plusquamperfekt_du'),
                    'er_sie_es': tense_data.get('plusquamperfekt_er_sie_es'),
                    'wir': tense_data.get('plusquamperfekt_wir'),
                    'ihr': tense_data.get('plusquamperfekt_ihr'),
                    'sie_Sie': tense_data.get('plusquamperfekt_sie_Sie')
                }
            
            if any(key.startswith('futur_i_') for key in tense_data.keys()):
                tables['futur_i'] = {
                    'ich': tense_data.get('futur_i_ich'),
                    'du': tense_data.get('futur_i_du'),
                    'er_sie_es': tense_data.get('futur_i_er_sie_es'),
                    'wir': tense_data.get('futur_i_wir'),
                    'ihr': tense_data.get('futur_i_ihr'),
                    'sie_Sie': tense_data.get('futur_i_sie_Sie')
                }
            
            if any(key.startswith('futur_ii_') for key in tense_data.keys()):
                tables['futur_ii'] = {
                    'ich': tense_data.get('futur_ii_ich'),
                    'du': tense_data.get('futur_ii_du'),
                    'er_sie_es': tense_data.get('futur_ii_er_sie_es'),
                    'wir': tense_data.get('futur_ii_wir'),
                    'ihr': tense_data.get('futur_ii_ihr'),
                    'sie_Sie': tense_data.get('futur_ii_sie_Sie')
                }
            
            # Build imperative table
            if any(key.startswith('imperativ_') for key in tense_data.keys()):
                tables['imperativ'] = {
                    'du': tense_data.get('imperativ_du'),
                    'ihr': tense_data.get('imperativ_ihr'),
                    'Sie': tense_data.get('imperativ_Sie')
                }
            
            # Build subjunctive tables
            if any(key.startswith('konjunktiv_i_') for key in tense_data.keys()):
                tables['konjunktiv_i'] = {
                    'ich': tense_data.get('konjunktiv_i_ich'),
                    'du': tense_data.get('konjunktiv_i_du'),
                    'er_sie_es': tense_data.get('konjunktiv_i_er_sie_es'),
                    'wir': tense_data.get('konjunktiv_i_wir'),
                    'ihr': tense_data.get('konjunktiv_i_ihr'),
                    'sie_Sie': tense_data.get('konjunktiv_i_sie_Sie')
                }
            
            if any(key.startswith('konjunktiv_ii_') for key in tense_data.keys()):
                tables['konjunktiv_ii'] = {
                    'ich': tense_data.get('konjunktiv_ii_ich'),
                    'du': tense_data.get('konjunktiv_ii_du'),
                    'er_sie_es': tense_data.get('konjunktiv_ii_er_sie_es'),
                    'wir': tense_data.get('konjunktiv_ii_wir'),
                    'ihr': tense_data.get('konjunktiv_ii_ihr'),
                    'sie_Sie': tense_data.get('konjunktiv_ii_sie_Sie')
                }
        
        return {
            'found': True,
            'original': original_query,
            'lemma': word.lemma,
            'pos': word.pos,
            'upos': word.pos.upper() if word.pos else None,
            'article': article,  # Now extracted from WordForm data
            'plural': plural,    # Now extracted from WordForm data
            'cefr': word.cefr,
            'frequency': word.frequency if hasattr(word, 'frequency') else None,
            'gloss_en': None,
            'gloss_zh': None,
            'translations_en': translations_en,
            'translations_zh': translations_zh,
            'example': example,
            'word_forms': word_forms,
            'tables': tables if tables else None,  # Structured conjugation tables
            'noun_props': noun_props if noun_props else None,  # Noun properties
            'verb_props': verb_props if verb_props else None,  # Verb properties
            'search_method': search_method,
            'cached': True,
            'source': 'database',
            'pipeline_results': {
                f'level_found_{search_method}': True
            },
            'processing_time_ms': 50
        }
    
    async def save_openai_analysis(
        self, 
        db: Session, 
        query: str, 
        analysis: Dict[str, Any], 
        user: User
    ) -> WordLemma:
        """Save OpenAI analysis to database"""
        from app.models.word import Translation, Example
        
        # Create new word lemma
        new_word = WordLemma(
            lemma=analysis.get('lemma', query),
            pos=analysis.get('pos', 'unknown'),
            cefr='A1',  # Default CEFR level
            frequency=1  # Default frequency as integer
        )
        
        db.add(new_word)
        db.commit()
        db.refresh(new_word)
        
        # Add translations
        translations_en = analysis.get('translations_en', [])
        translations_zh = analysis.get('translations_zh', [])
        
        for trans_text in translations_en:
            translation = Translation(
                lemma_id=new_word.id,
                lang_code='en',
                text=trans_text
            )
            db.add(translation)
        
        for trans_text in translations_zh:
            translation = Translation(
                lemma_id=new_word.id,
                lang_code='zh',
                text=trans_text
            )
            db.add(translation)
        
        # Add example if provided
        example_data = analysis.get('example')
        if example_data:
            example = Example(
                lemma_id=new_word.id,
                de_text=example_data.get('de', ''),
                en_text=example_data.get('en', ''),
                zh_text=example_data.get('zh', '')
            )
            db.add(example)
        
        db.commit()
        return new_word