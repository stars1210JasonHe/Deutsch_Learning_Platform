"""
German vocabulary enhancement LLM service
Provides strict JSON output for German word morphological analysis
"""
import json
import logging
from typing import Dict, Any, List, Optional
from app.services.openai_service import OpenAIService

class LexiconLLMService:
    """LLM service specialized for lexicon enhancement"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def enrich_noun(self, lemma: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Noun enrichment: get gender, plural, genitive and other complete information
        """
        context = context or {}
        
        system_prompt = """You are a precise German morphology and lexicon engine. 
        You must output ONLY valid JSON following the exact schema provided.
        Never include any explanation, markdown, or text outside the JSON.
        Use only English and basic ASCII characters. No Unicode escapes or special characters."""
        
        user_prompt = f"""{{
    "task": "enrich_noun",
    "lemma": "{lemma}",
    "context": {json.dumps(context)},
    "want_examples": true
}}

Return JSON with this exact structure:
{{
    "upos": "NOUN",
    "xpos": "NN",
    "gender": "masc|fem|neut",
    "noun_props": {{
        "gen_sg": "genitive singular form",
        "plural": "plural form", 
        "declension_class": "strong|weak|mixed",
        "dative_plural_ends_n": true|false
    }},
    "gloss_en": "English translation",
    "gloss_zh": "Chinese translation",
    "example": {{
        "de": "German example sentence",
        "en": "English translation", 
        "zh": "Chinese translation"
    }},
    "forms": [
        {{"form": "singular_nominative", "features": {{"POS": "NOUN", "Number": "Sing", "Case": "Nom"}}}},
        {{"form": "singular_genitive", "features": {{"POS": "NOUN", "Number": "Sing", "Case": "Gen"}}}},
        {{"form": "plural_nominative", "features": {{"POS": "NOUN", "Number": "Plur", "Case": "Nom"}}}},
        {{"form": "plural_dative", "features": {{"POS": "NOUN", "Number": "Plur", "Case": "Dat"}}}}
    ],
    "rationale": "Brief explanation in English"
}}"""
        
        return await self._call_llm_strict_json(system_prompt, user_prompt)
    
    async def enrich_verb(self, lemma: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Verb enrichment: get tense conjugations, auxiliary verbs, separability and other information
        """
        context = context or {}
        
        system_prompt = """You are a precise German verb morphology engine.
        You must output ONLY valid JSON following the exact schema provided.
        Never include any explanation, markdown, or text outside the JSON.
        Use only English and basic ASCII characters. No Unicode escapes or special characters."""
        
        user_prompt = f"""{{
    "task": "enrich_verb",
    "lemma": "{lemma}",
    "context": {json.dumps(context)}
}}

Return JSON with this exact structure:
{{
    "upos": "VERB",
    "xpos": "VVINF",
    "separable": true|false,
    "prefix": "prefix if separable, null otherwise",
    "aux": "haben|sein",
    "regularity": "strong|weak|mixed",
    "partizip_ii": "past participle form",
    "reflexive": true|false,
    "tables": {{
        "praesens": {{
            "ich": "1sg form",
            "du": "2sg form", 
            "er_sie_es": "3sg form",
            "wir": "1pl form",
            "ihr": "2pl form",
            "sie_Sie": "3pl/formal form"
        }},
        "praeteritum": {{
            "ich": "1sg past form",
            "du": "2sg past form",
            "er_sie_es": "3sg past form", 
            "wir": "1pl past form",
            "ihr": "2pl past form",
            "sie_Sie": "3pl/formal past form"
        }}
    }},
    "gloss_en": "English translation",
    "gloss_zh": "Chinese translation",
    "example": {{
        "de": "German example sentence",
        "en": "English translation",
        "zh": "Chinese translation"
    }},
    "valency": {{
        "cases": ["accusative", "dative"],
        "preps": ["mit", "an"]
    }},
    "rationale": "Brief explanation in English"
}}"""
        
        return await self._call_llm_strict_json(system_prompt, user_prompt)
    
    async def disambiguate_lemma(self, lemma: str) -> Dict[str, Any]:
        """
        Homonym disambiguation: return all possible parts of speech and meanings
        """
        system_prompt = """You are a German lexicon disambiguation engine.
        You must output ONLY valid JSON following the exact schema provided.
        Never include any explanation, markdown, or text outside the JSON.
        Use only English and basic ASCII characters. No Unicode escapes or special characters."""
        
        user_prompt = f"""{{
    "task": "disambiguate",
    "lemma": "{lemma}"
}}

Return JSON with this exact structure:
{{
    "senses": [
        {{
            "upos": "NOUN|VERB|ADJ|ADV|...",
            "xpos": "NN|VVINF|ADJD|...",
            "gender": "masc|fem|neut (only for nouns, null otherwise)",
            "gloss_en": "English meaning",
            "gloss_zh": "Chinese meaning",
            "frequency_rank": 1
        }}
    ]
}}"""
        
        return await self._call_llm_strict_json(system_prompt, user_prompt)
    
    async def enrich_adjective(self, lemma: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Adjective enrichment: get comparative, superlative and other information
        """
        context = context or {}
        
        system_prompt = """You are a precise German adjective morphology engine.
        You must output ONLY valid JSON following the exact schema provided.
        Use only English and basic ASCII characters. No Unicode escapes or special characters."""
        
        user_prompt = f"""{{
    "task": "enrich_adjective", 
    "lemma": "{lemma}",
    "context": {json.dumps(context)}
}}

Return JSON with this exact structure:
{{
    "upos": "ADJ",
    "xpos": "ADJD",
    "comparative": "comparative form",
    "superlative": "superlative form",
    "predicative": true|false,
    "attributive": true|false,
    "gloss_en": "English translation",
    "gloss_zh": "Chinese translation",
    "example": {{
        "de": "German example sentence",
        "en": "English translation",
        "zh": "Chinese translation"
    }},
    "rationale": "Brief explanation"
}}"""
        
        return await self._call_llm_strict_json(system_prompt, user_prompt)
    
    async def _call_llm_strict_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Call LLM and ensure strict JSON return with retry mechanism
        """
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = await self.openai_service.client.chat.completions.create(
                    model=self.openai_service.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=2000,
                    temperature=0.1  # Low temperature for more consistent results
                )
                
                content = response.choices[0].message.content.strip()
                
                # Clean possible markdown formatting
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                elif content.startswith('```'):
                    content = content.replace('```', '').strip()
                
                # Clean possible invalid Unicode escapes
                content = self._clean_unicode_escapes(content)
                
                # Parse JSON
                result = json.loads(content)
                
                # Basic validation
                if self._validate_json_structure(result):
                    return result
                else:
                    logging.warning(f"JSON structure validation failed, attempt {attempt + 1}/{max_retries}")
                    
            except json.JSONDecodeError as e:
                logging.warning(f"JSON parsing failed (attempt {attempt + 1}/{max_retries}): {e}")
                logging.debug(f"Raw content: {content}")
                
                # Try more aggressive cleaning
                if attempt == max_retries - 1:  # Last attempt
                    try:
                        cleaned_content = self._aggressive_json_clean(content)
                        result = json.loads(cleaned_content)
                        if self._validate_json_structure(result):
                            return result
                    except:
                        pass
                
            except Exception as e:
                logging.error(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
        
        # All retries failed, return empty result
        logging.error(f"All retries failed, returning empty result")
        return {}
    
    def _validate_json_structure(self, data: Dict[str, Any]) -> bool:
        """
        Validate if returned JSON structure meets expectations
        """
        if not isinstance(data, dict):
            return False
        
        # Validate required fields based on different tasks
        if "upos" in data:
            return True  # Basic validation passed
        elif "senses" in data:
            return isinstance(data["senses"], list) and len(data["senses"]) > 0
        
        return False
    
    def _clean_unicode_escapes(self, content: str) -> str:
        """
        Clean potentially problematic Unicode escape sequences
        """
        import re
        
        # Fix common invalid Unicode escapes
        # Replace invalid \uXXXX sequences
        def fix_unicode_escape(match):
            escape_seq = match.group(0)
            try:
                # Try to parse Unicode escape
                return escape_seq.encode().decode('unicode_escape')
            except:
                # If failed, remove escape symbols
                return escape_seq.replace('\\u', 'u')
        
        # Find and fix all \uXXXX patterns
        content = re.sub(r'\\u[0-9a-fA-F]{0,4}', fix_unicode_escape, content)
        
        # 移除其他可能有问题的转义序列
        content = content.replace('\\"', '"')  # 修复双引号转义
        content = content.replace('\\n', '\n')  # 修复换行符
        content = content.replace('\\t', '\t')  # 修复制表符
        content = content.replace('\\\\', '\\')  # 修复反斜杠
        
        return content
    
    def _aggressive_json_clean(self, content: str) -> str:
        """
        更激进的JSON清理，用于最后的尝试
        """
        import re
        
        # 移除所有无效的Unicode转义
        content = re.sub(r'\\u[^0-9a-fA-F"]', '', content)
        content = re.sub(r'\\u[0-9a-fA-F]{0,3}(?![0-9a-fA-F])', '', content)
        
        # 修复常见的JSON格式问题
        content = re.sub(r',\s*}', '}', content)  # 移除末尾逗号
        content = re.sub(r',\s*]', ']', content)  # 移除末尾逗号
        
        # 确保字符串字段被正确引用
        content = re.sub(r':\s*([^",\[\]{}\s]+)([,}\]])', r': "\1"\2', content)
        
        return content
    
    def get_completeness_score(self, sense_data: Dict[str, Any]) -> float:
        """
        计算词条的完备性评分 (0.0 - 1.0)
        """
        total_fields = 0
        filled_fields = 0
        
        upos = sense_data.get("upos", "").upper()
        
        if upos == "NOUN":
            # 名词必需字段
            noun_fields = ["gender", "gloss_en", "gloss_zh"]
            total_fields += len(noun_fields)
            filled_fields += sum(1 for field in noun_fields if sense_data.get(field))
            
            # 名词属性
            noun_props = sense_data.get("noun_props", {})
            if noun_props:
                prop_fields = ["gen_sg", "plural", "declension_class"]
                total_fields += len(prop_fields)
                filled_fields += sum(1 for field in prop_fields if noun_props.get(field))
                
        elif upos == "VERB":
            # 动词必需字段
            verb_fields = ["aux", "partizip_ii", "gloss_en", "gloss_zh"]
            total_fields += len(verb_fields)
            filled_fields += sum(1 for field in verb_fields if sense_data.get(field))
            
            # 动词变位表
            tables = sense_data.get("tables", {})
            if tables:
                if "praesens" in tables:
                    total_fields += 6  # 6个人称
                    praesens = tables["praesens"]
                    filled_fields += sum(1 for person in ["ich", "du", "er_sie_es", "wir", "ihr", "sie_Sie"] 
                                       if praesens.get(person))
                
                if "praeteritum" in tables:
                    total_fields += 6  # 6个人称
                    praeteritum = tables["praeteritum"]
                    filled_fields += sum(1 for person in ["ich", "du", "er_sie_es", "wir", "ihr", "sie_Sie"]
                                       if praeteritum.get(person))
        
        # 通用字段
        common_fields = ["example"]
        total_fields += len(common_fields)
        filled_fields += sum(1 for field in common_fields if sense_data.get(field))
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
