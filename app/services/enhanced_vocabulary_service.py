"""
增强版词库服务 - 支持在线字段补全
继承原有功能，添加实时完备性检查和自动补全
"""
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.vocabulary_service import VocabularyService
from app.services.lexicon_llm_service import LexiconLLMService
from app.models.user import User
from app.models.word import WordLemma

class EnhancedVocabularyService(VocabularyService):
    """增强版词库服务"""
    
    def __init__(self):
        super().__init__()
        self.llm_service = LexiconLLMService()
    
    def sanitize_for_json(self, data):
        """清理数据中的无效控制字符，使其可以被JSON序列化"""
        if isinstance(data, str):
            # 移除或替换控制字符（保留换行符、制表符、回车符）
            return re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', data)
        elif isinstance(data, dict):
            return {k: self.sanitize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_for_json(item) for item in data]
        else:
            return data
    
    def safe_json_dumps(self, data):
        """安全的JSON序列化，带有错误处理"""
        try:
            sanitized_data = self.sanitize_for_json(data)
            return json.dumps(sanitized_data, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            print(f"   WARNING: JSON serialization failed: {e}")
            # 如果序列化失败，返回一个空的JSON对象
            return "{}"
    
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
    
    async def get_or_create_word_enhanced(
        self,
        db: Session,
        lemma: str,
        user: User,
        force_enrich: bool = False
    ) -> Dict[str, Any]:
        """
        增强版查词：使用EnhancedSearchService进行智能搜索
        """
        try:
            print("DEBUG: get_or_create_word_enhanced called")
            # 直接使用我们的增强查找方法
            existing_word = await self._find_existing_word(db, lemma)
            
            if existing_word:
                # Check if multiple results
                if isinstance(existing_word, dict) and existing_word.get('multiple_results'):
                    print("Multiple results found")
                    from app.services.enhanced_search_service import EnhancedSearchService
                    enhanced_search = EnhancedSearchService()
                    return await enhanced_search.format_multiple_results(
                        existing_word['matches'], 'multiple_pos', lemma
                    )
                else:
                    print("Single result found")
                    await self._log_search_history(db, user, lemma, "word_lookup", from_database=True)
                    return await self._format_word_data(existing_word, from_database=True)
            
            # 如果没找到，使用增强搜索服务进行智能搜索
            print("No direct matches, trying enhanced search")
            from app.services.enhanced_search_service import EnhancedSearchService
            enhanced_search = EnhancedSearchService()
            
            # 使用增强搜索，它会处理inflected forms和redirects
            result = await enhanced_search.search_with_suggestions(
                db=db,
                query=lemma,
                user=user,
                max_suggestions=5
            )
            
            # 如果找到了结果，返回格式化的数据
            if result.get('found'):
                return result
            
            # 如果没找到但有建议，返回建议
            if result.get('suggestions_with_scores'):
                return {
                    'found': False,
                    'original': lemma,
                    'suggestions': result['suggestions_with_scores'],
                    'message': f"'{lemma}' not found. Here are some suggestions:",
                    'source': 'enhanced_search_suggestions'
                }
            
            # 完全没找到，fallback到原逻辑
            return await self.get_or_create_word(db, lemma, user)
            
        except Exception as e:
            print(f"ERROR: Enhanced search failed: {e}")
            # 如果失败，尝试简单的回退逻辑
            try:
                # 查找现有单词
                existing_word = await self._find_existing_word(db, lemma)
                if existing_word:
                    # Check if multiple results
                    if isinstance(existing_word, dict) and existing_word.get('multiple_results'):
                        print("Multiple results found in fallback")
                        from app.services.enhanced_search_service import EnhancedSearchService
                        enhanced_search = EnhancedSearchService()
                        return await enhanced_search.format_multiple_results(
                            existing_word['matches'], 'multiple_pos', lemma
                        )
                    else:
                        await self._log_search_history(db, user, lemma, "word_lookup", from_database=True)
                        return await self._format_word_data(existing_word, from_database=True)
                else:
                    # 如果不存在，返回未找到的响应
                    await self._log_search_history(db, user, lemma, "word_lookup_not_found", from_database=False)
                    return {
                        "found": False,
                        "original": lemma,
                        "suggestions": [],
                        "message": f"'{lemma}' is not a recognized German word.",
                        "source": "fallback_response"
                    }
            except Exception as fallback_error:
                print(f"ERROR: Fallback also failed: {fallback_error}")
                return {
                    "found": False,
                    "original": lemma,
                    "suggestions": [],
                    "message": f"Error analyzing '{lemma}'. Please try again.",
                    "source": "error_response"
                }
    
    async def _find_existing_word(self, db: Session, lemma: str):
        """Override parent method to support multiple results for different POS and proper German umlaut handling"""
        from sqlalchemy.orm import joinedload
        from app.models.word import WordForm
        
        print("DEBUG: Enhanced _find_existing_word called")
        
        all_matches = []
        
        # Get all possible case variants for German text including proper umlaut handling
        variants = self.german_case_variants(lemma)
        print(f"  Trying variants: {variants}")
        
        # Search for all variants
        for variant in variants:
            matches = db.query(WordLemma).options(
                joinedload(WordLemma.translations),
                joinedload(WordLemma.examples),
                joinedload(WordLemma.forms),
                joinedload(WordLemma.verb_props)
            ).filter(WordLemma.lemma == variant).all()
            
            # Add if not already included
            for match in matches:
                if match.id not in [m.id for m in all_matches]:
                    all_matches.append(match)
        
        print(f"  Total matches found: {len(all_matches)}")
        for match in all_matches:
            print(f"    - {match.lemma} ({match.pos}) ID {match.id}")
        
        # If multiple matches, return special indicator
        if len(all_matches) > 1:
            print(f"  Returning multiple matches for choice selection")
            return {"multiple_results": True, "matches": all_matches}
        elif len(all_matches) == 1:
            print(f"  Returning single match")
            return all_matches[0]
        
        # 3. Fallback to inflected forms search (original logic)
        print(f"  No direct matches, trying inflected forms...")
        word_form = db.query(WordForm).filter(WordForm.form == lemma).first()
        if word_form:
            print("  Found inflected form match")
            return word_form.lemma
            
        # 4. Article removal fallback
        lemma_clean = self._clean_lemma(lemma)
        if lemma_clean != lemma:
            print("  Trying cleaned lemma")
            word = db.query(WordLemma).filter(WordLemma.lemma == lemma_clean).first()
            if word:
                print("  Found cleaned match")
                return word
        
        print(f"  No matches found")
        return None
    
    async def _find_enhanced_word(self, db: Session, lemma: str) -> Optional[Dict[str, Any]]:
        """
        查找现有词条，返回增强格式的数据
        """
        # 使用新的查询，包含 sense 和属性数据
        query = text("""
            SELECT 
                wl.id as lemma_id,
                wl.lemma,
                wl.pos as legacy_pos,
                wl.cefr,
                wl.notes,
                ls.id as sense_id,
                ls.upos,
                ls.xpos,
                ls.gender,
                ls.gloss_en,
                ls.gloss_zh,
                ls.confidence,
                ls.source,
                np.gen_sg,
                np.plural,
                np.declension_class,
                np.dative_plural_ends_n,
                vp.separable,
                vp.prefix,
                vp.aux,
                vp.regularity,
                vp.partizip_ii,
                vp.reflexive,
                vp.valency_json
            FROM word_lemmas wl
            LEFT JOIN lemma_senses ls ON ls.lemma_id = wl.id
            LEFT JOIN noun_props np ON np.sense_id = ls.id
            LEFT JOIN verb_props vp ON vp.sense_id = ls.id
            WHERE wl.lemma LIKE :lemma
            ORDER BY ls.confidence DESC
            LIMIT 1
        """)
        
        result = db.execute(query, {"lemma": lemma}).fetchone()
        
        if not result:
            # 尝试词形变位匹配
            form_query = text("""
                SELECT 
                    wl.id as lemma_id,
                    wl.lemma,
                    wl.pos as legacy_pos,
                    wl.cefr,
                    wl.notes,
                    ls.id as sense_id,
                    ls.upos,
                    ls.xpos,
                    ls.gender,
                    ls.gloss_en,
                    ls.gloss_zh,
                    ls.confidence,
                    ls.source,
                    np.gen_sg,
                    np.plural,
                    np.declension_class,
                    np.dative_plural_ends_n,
                    vp.separable,
                    vp.prefix,
                    vp.aux,
                    vp.regularity,
                    vp.partizip_ii,
                    vp.reflexive,
                    vp.valency_json
                FROM word_lemmas wl
                LEFT JOIN lemma_senses ls ON ls.lemma_id = wl.id
                LEFT JOIN noun_props np ON np.sense_id = ls.id
                LEFT JOIN verb_props vp ON vp.sense_id = ls.id
                JOIN word_forms wf ON wf.lemma_id = wl.id
                WHERE wf.form LIKE :form
                ORDER BY ls.confidence DESC
                LIMIT 1
            """)
            
            result = db.execute(form_query, {"form": lemma}).fetchone()
        
        if not result:
            return None
        
        # 转换为字典
        result_dict = dict(result._mapping)
        
        # 获取翻译
        translations = self._get_translations(db, result_dict['sense_id'])
        
        # 获取例句
        examples = self._get_examples(db, result_dict['sense_id'])
        
        # 获取词形变化
        forms = self._get_forms(db, result_dict['sense_id'])
        
        # 构建返回数据
        return self._build_enhanced_result(result_dict, translations, examples, forms)
    
    def _get_translations(self, db: Session, sense_id: int) -> Dict[str, List[str]]:
        """获取翻译"""
        if not sense_id:
            return {"en": [], "zh": []}
        
        from sqlalchemy import text
        query = text("""
            SELECT lang_code, text 
            FROM translations 
            WHERE sense_id = :sense_id
        """)
        
        results = db.execute(query, {"sense_id": sense_id}).fetchall()
        
        translations = {"en": [], "zh": []}
        for row in results:
            lang = row.lang_code
            text = row.text
            if lang in translations:
                translations[lang].append(text)
        
        return translations
    
    def _get_examples(self, db: Session, sense_id: int) -> List[Dict[str, str]]:
        """获取例句"""
        if not sense_id:
            return []
        
        from sqlalchemy import text
        query = text("""
            SELECT de_text, en_text, zh_text 
            FROM examples 
            WHERE sense_id = :sense_id
            LIMIT 3
        """)
        
        results = db.execute(query, {"sense_id": sense_id}).fetchall()
        
        examples = []
        for row in results:
            examples.append({
                "de": row.de_text or "",
                "en": row.en_text or "",
                "zh": row.zh_text or ""
            })
        
        return examples
    
    def _get_forms(self, db: Session, sense_id: int) -> List[Dict[str, Any]]:
        """获取词形变化"""
        if not sense_id:
            return []
        
        from sqlalchemy import text
        query = text("""
            SELECT form, features_json 
            FROM forms_unimorph 
            WHERE sense_id = :sense_id
        """)
        
        results = db.execute(query, {"sense_id": sense_id}).fetchall()
        
        forms = []
        for row in results:
            try:
                features = json.loads(row.features_json) if row.features_json else {}
                forms.append({
                    "form": row.form,
                    "features": features
                })
            except json.JSONDecodeError:
                continue
        
        return forms
    
    def _build_enhanced_result(
        self,
        word_data: Dict[str, Any],
        translations: Dict[str, List[str]],
        examples: List[Dict[str, str]],
        forms: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """构建增强格式的结果"""
        
        upos = word_data.get('upos') or word_data.get('legacy_pos', '').upper()
        
        result = {
            "original": word_data['lemma'],
            "found": True,
            "lemma_id": word_data['lemma_id'],
            "sense_id": word_data['sense_id'],
            "pos": upos.lower(),
            "upos": upos,
            "xpos": word_data.get('xpos'),
            "cefr": word_data.get('cefr'),
            "confidence": word_data.get('confidence', 0.5),
            "source": word_data.get('source', 'database'),
            
            # 释义
            "gloss_en": word_data.get('gloss_en'),
            "gloss_zh": word_data.get('gloss_zh'),
            "translations_en": translations.get('en', []),
            "translations_zh": translations.get('zh', []),
            
            # 例句
            "examples": examples,
            "example": examples[0] if examples else None,
            
            # 词形变化
            "forms": forms,
            
            # 词性特定属性
            "enhanced": True
        }
        
        # 名词属性
        if upos == 'NOUN':
            result.update({
                "gender": word_data.get('gender'),
                "article": self._gender_to_article(word_data.get('gender')),
                "noun_props": {
                    "gen_sg": word_data.get('gen_sg'),
                    "plural": word_data.get('plural'),
                    "declension_class": word_data.get('declension_class'),
                    "dative_plural_ends_n": bool(word_data.get('dative_plural_ends_n'))
                } if any(word_data.get(k) for k in ['gen_sg', 'plural', 'declension_class']) else None
            })
        
        # 动词属性
        elif upos == 'VERB':
            result.update({
                "verb_props": {
                    "separable": bool(word_data.get('separable')),
                    "prefix": word_data.get('prefix'),
                    "aux": word_data.get('aux'),
                    "regularity": word_data.get('regularity'),
                    "partizip_ii": word_data.get('partizip_ii'),
                    "reflexive": bool(word_data.get('reflexive')),
                    "valency": json.loads(word_data.get('valency_json', '{}')) if word_data.get('valency_json') else {}
                } if any(word_data.get(k) for k in ['aux', 'partizip_ii', 'regularity']) else None,
                
                # 构建时态表
                "tables": self._build_verb_tables(forms)
            })
        
        return result
    
    def _gender_to_article(self, gender: Optional[str]) -> Optional[str]:
        """将性别转换为冠词"""
        if not gender:
            return None
        
        gender_map = {
            'masc': 'der',
            'masculine': 'der',
            'fem': 'die',
            'feminine': 'die',
            'neut': 'das',
            'neuter': 'das'
        }
        
        return gender_map.get(gender.lower())
    
    def _build_verb_tables(self, forms: List[Dict[str, Any]]) -> Optional[Dict[str, Dict[str, str]]]:
        """从词形构建动词时态表"""
        if not forms:
            return None
        
        tables = {}
        
        for form_data in forms:
            features = form_data.get('features', {})
            form = form_data.get('form')
            
            if features.get('POS') != 'VERB' or not form:
                continue
            
            tense = features.get('Tense', '').lower()
            person = features.get('Person', '')
            
            if tense and person:
                if tense not in tables:
                    tables[tense] = {}
                tables[tense][person] = form
        
        return tables if tables else None
    
    def _analyze_completeness_gaps(self, word_data: Dict[str, Any]) -> 'CompletenessAnalysis':
        """分析词条的完备性缺口"""
        return CompletenessAnalysis(word_data)
    
    async def _enrich_existing_word(
        self,
        db: Session,
        word_data: Dict[str, Any],
        gaps: 'CompletenessAnalysis'
    ) -> Optional[Dict[str, Any]]:
        """补全现有词条的缺失字段"""
        
        lemma = word_data['original']
        sense_id = word_data.get('sense_id')
        upos = word_data.get('upos')
        
        try:
            enrichment_data = None
            
            # 根据词性调用对应的补全服务
            if upos == 'NOUN' and gaps.needs_noun_enrichment():
                context = {'existing_data': word_data}
                enrichment_data = await self.llm_service.enrich_noun(lemma, context)
                
                if enrichment_data:
                    await self._save_noun_enrichment(db, sense_id, enrichment_data)
            
            elif upos == 'VERB' and gaps.needs_verb_enrichment():
                context = {'existing_data': word_data}
                enrichment_data = await self.llm_service.enrich_verb(lemma, context)
                
                if enrichment_data:
                    await self._save_verb_enrichment(db, sense_id, enrichment_data)
            
            # 重新查询增强后的数据
            if enrichment_data:
                return await self._find_enhanced_word(db, lemma)
        
        except Exception as e:
            print(f"ERROR: Online completion failed: {e}")
        
        return word_data
    
    async def _save_noun_enrichment(self, db: Session, sense_id: int, data: Dict[str, Any]):
        """保存名词补全数据"""
        from sqlalchemy import text
        
        # 更新 lemma_senses
        if data.get('gender') or data.get('gloss_en') or data.get('gloss_zh'):
            update_query = text("""
                UPDATE lemma_senses 
                SET gender = COALESCE(gender, :gender),
                    gloss_en = COALESCE(gloss_en, :gloss_en),
                    gloss_zh = COALESCE(gloss_zh, :gloss_zh),
                    confidence = GREATEST(confidence, 0.8),
                    source = 'openai_enriched'
                WHERE id = :sense_id
            """)
            
            db.execute(update_query, {
                "sense_id": sense_id,
                "gender": data.get('gender'),
                "gloss_en": data.get('gloss_en'),
                "gloss_zh": data.get('gloss_zh')
            })
        
        # 更新名词属性
        noun_props = data.get('noun_props', {})
        if noun_props:
            upsert_props = text("""
                INSERT OR REPLACE INTO noun_props 
                (sense_id, gen_sg, plural, declension_class, dative_plural_ends_n)
                VALUES (:sense_id, :gen_sg, :plural, :declension_class, :dative_plural_ends_n)
            """)
            
            db.execute(upsert_props, {
                "sense_id": sense_id,
                "gen_sg": noun_props.get('gen_sg'),
                "plural": noun_props.get('plural'),
                "declension_class": noun_props.get('declension_class'),
                "dative_plural_ends_n": noun_props.get('dative_plural_ends_n', False)
            })
        
        # 保存词形变化
        forms = data.get('forms', [])
        for form_data in forms:
            insert_form = text("""
                INSERT OR IGNORE INTO forms_unimorph
                (sense_id, form, features_json)
                VALUES (:sense_id, :form, :features_json)
            """)
            
            db.execute(insert_form, {
                "sense_id": sense_id,
                "form": form_data.get('form'),
                "features_json": self.safe_json_dumps(form_data.get('features', {}))
            })
        
        db.commit()
    
    async def _save_verb_enrichment(self, db: Session, sense_id: int, data: Dict[str, Any]):
        """保存动词补全数据"""
        from sqlalchemy import text
        
        # 更新 lemma_senses
        if data.get('gloss_en') or data.get('gloss_zh'):
            update_query = text("""
                UPDATE lemma_senses 
                SET gloss_en = COALESCE(gloss_en, :gloss_en),
                    gloss_zh = COALESCE(gloss_zh, :gloss_zh),
                    confidence = GREATEST(confidence, 0.8),
                    source = 'openai_enriched'
                WHERE id = :sense_id
            """)
            
            db.execute(update_query, {
                "sense_id": sense_id,
                "gloss_en": data.get('gloss_en'),
                "gloss_zh": data.get('gloss_zh')
            })
        
        # 更新动词属性
        upsert_verb = text("""
            INSERT OR REPLACE INTO verb_props 
            (sense_id, separable, prefix, aux, regularity, partizip_ii, reflexive, valency_json)
            VALUES (:sense_id, :separable, :prefix, :aux, :regularity, :partizip_ii, :reflexive, :valency_json)
        """)
        
        db.execute(upsert_verb, {
            "sense_id": sense_id,
            "separable": data.get('separable', False),
            "prefix": data.get('prefix'),
            "aux": data.get('aux'),
            "regularity": data.get('regularity'),
            "partizip_ii": data.get('partizip_ii'),
            "reflexive": data.get('reflexive', False),
            "valency_json": self.safe_json_dumps(data.get('valency', {}))
        })
        
        # 保存动词变位表
        tables = data.get('tables', {})
        for tense, forms in tables.items():
            if isinstance(forms, dict):
                for person, form in forms.items():
                    if form:
                        insert_form = text("""
                            INSERT OR IGNORE INTO forms_unimorph
                            (sense_id, form, features_json)
                            VALUES (:sense_id, :form, :features_json)
                        """)
                        
                        db.execute(insert_form, {
                            "sense_id": sense_id,
                            "form": form,
                            "features_json": self.safe_json_dumps({
                                "POS": "VERB",
                                "Tense": tense.title(),
                                "Person": person
                            })
                        })
        
        db.commit()


class CompletenessAnalysis:
    """完备性分析类"""
    
    def __init__(self, word_data: Dict[str, Any]):
        self.word_data = word_data
        self.upos = word_data.get('upos', '').upper()
        self.confidence = word_data.get('confidence', 0.0)
        
        # 分析各种缺口
        self._analyze_gaps()
    
    def _analyze_gaps(self):
        """分析具体缺口"""
        self.missing_gloss = not self.word_data.get('gloss_en') or not self.word_data.get('gloss_zh')
        self.missing_examples = not self.word_data.get('examples') or len(self.word_data.get('examples', [])) == 0
        
        if self.upos == 'NOUN':
            self.missing_gender = not self.word_data.get('gender')
            noun_props = self.word_data.get('noun_props') or {}
            self.missing_plural = not noun_props.get('plural')
            self.missing_genitive = not noun_props.get('gen_sg')
        else:
            self.missing_gender = False
            self.missing_plural = False
            self.missing_genitive = False
        
        if self.upos == 'VERB':
            verb_props = self.word_data.get('verb_props') or {}
            self.missing_aux = not verb_props.get('aux')
            self.missing_partizip = not verb_props.get('partizip_ii')
            tables = self.word_data.get('tables') or {}
            self.missing_praesens = not tables.get('pres') and not tables.get('praesens')
            self.missing_praeteritum = not tables.get('past') and not tables.get('praeteritum')
        else:
            self.missing_aux = False
            self.missing_partizip = False
            self.missing_praesens = False
            self.missing_praeteritum = False
    
    def has_gaps(self) -> bool:
        """是否有任何缺口"""
        return (
            self.missing_gloss or 
            self.missing_examples or
            self.missing_gender or 
            self.missing_plural or 
            self.missing_genitive or
            self.missing_aux or 
            self.missing_partizip or
            self.missing_praesens or 
            self.missing_praeteritum
        )
    
    def should_enrich(self) -> bool:
        """是否应该进行补全"""
        # 低置信度的总是补全
        if self.confidence < 0.7:
            return True
        
        # 关键字段缺失的进行补全
        critical_gaps = (
            self.missing_gloss or
            (self.upos == 'NOUN' and (self.missing_gender or self.missing_plural)) or
            (self.upos == 'VERB' and (self.missing_aux or self.missing_partizip))
        )
        
        return critical_gaps
    
    def needs_noun_enrichment(self) -> bool:
        """是否需要名词补全"""
        return (
            self.upos == 'NOUN' and 
            (self.missing_gender or self.missing_plural or self.missing_genitive or self.missing_gloss)
        )
    
    def needs_verb_enrichment(self) -> bool:
        """是否需要动词补全"""
        return (
            self.upos == 'VERB' and
            (self.missing_aux or self.missing_partizip or self.missing_praesens or self.missing_praeteritum or self.missing_gloss)
        )
