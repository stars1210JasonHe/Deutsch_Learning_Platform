"""
Vocabulary Service - 统一词库管理
先查询本地词库，不存在才调用OpenAI，然后保存到词库
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.word import WordLemma, Translation, Example, WordForm
from app.models.search import SearchHistory
from app.services.openai_service import OpenAIService
from app.models.user import User


class VocabularyService:
    def __init__(self):
        self.openai_service = OpenAIService()
        # Simple fallback dictionary for common German words
        self.fallback_translations = {
            "bezahlen": {
                "pos": "verb",
                "translations_en": ["to pay", "to pay for"],
                "translations_zh": ["付钱", "支付"],
                "example": {"de": "Ich muss die Rechnung bezahlen.", "en": "I have to pay the bill.", "zh": "我必须付账单。"}
            },
            "blühen": {
                "pos": "verb", 
                "translations_en": ["to bloom", "to flower", "to flourish"],
                "translations_zh": ["开花", "盛开", "繁荣"],
                "example": {"de": "Die Rosen blühen schön.", "en": "The roses bloom beautifully.", "zh": "玫瑰花开得很美。"}
            },
            "essen": {
                "pos": "verb",
                "translations_en": ["to eat"],
                "translations_zh": ["吃"],
                "example": {"de": "Wir essen zusammen.", "en": "We eat together.", "zh": "我们一起吃饭。"}
            },
            "trinken": {
                "pos": "verb",
                "translations_en": ["to drink"],
                "translations_zh": ["喝"],
                "example": {"de": "Ich trinke Wasser.", "en": "I drink water.", "zh": "我喝水。"}
            },
            "gehen": {
                "pos": "verb",
                "translations_en": ["to go", "to walk"],
                "translations_zh": ["去", "走"],
                "example": {"de": "Wir gehen nach Hause.", "en": "We go home.", "zh": "我们回家。"}
            },
            "kommen": {
                "pos": "verb",
                "translations_en": ["to come"],
                "translations_zh": ["来"],
                "example": {"de": "Kommst du mit?", "en": "Are you coming along?", "zh": "你一起来吗？"}
            },
            "sein": {
                "pos": "verb",
                "translations_en": ["to be"],
                "translations_zh": ["是", "存在"],
                "example": {"de": "Ich bin müde.", "en": "I am tired.", "zh": "我累了。"}
            },
            "haben": {
                "pos": "verb", 
                "translations_en": ["to have"],
                "translations_zh": ["有"],
                "example": {"de": "Ich habe Zeit.", "en": "I have time.", "zh": "我有时间。"}
            },
            "sprechen": {
                "pos": "verb",
                "translations_en": ["to speak", "to talk"],
                "translations_zh": ["说话", "讲"],
                "example": {"de": "Sprechen Sie Deutsch?", "en": "Do you speak German?", "zh": "您说德语吗？"}
            },
            "lernen": {
                "pos": "verb",
                "translations_en": ["to learn"],
                "translations_zh": ["学习"],
                "example": {"de": "Ich lerne Deutsch.", "en": "I am learning German.", "zh": "我在学德语。"}
            },
            "Haus": {
                "pos": "noun",
                "article": "das",
                "translations_en": ["house", "home"],
                "translations_zh": ["房子", "家"],
                "example": {"de": "Das Haus ist groß.", "en": "The house is big.", "zh": "房子很大。"}
            },
            "Auto": {
                "pos": "noun",
                "article": "das", 
                "translations_en": ["car"],
                "translations_zh": ["汽车"],
                "example": {"de": "Mein Auto ist rot.", "en": "My car is red.", "zh": "我的车是红色的。"}
            },
            "Wasser": {
                "pos": "noun",
                "article": "das",
                "translations_en": ["water"],
                "translations_zh": ["水"],
                "example": {"de": "Das Wasser ist kalt.", "en": "The water is cold.", "zh": "水很冷。"}
            },
            "Zeit": {
                "pos": "noun",
                "article": "die",
                "translations_en": ["time"],
                "translations_zh": ["时间"],
                "example": {"de": "Ich habe keine Zeit.", "en": "I don't have time.", "zh": "我没有时间。"}
            },
            "machen": {
                "pos": "verb",
                "translations_en": ["to make", "to do"],
                "translations_zh": ["做", "制作"],
                "example": {"de": "Was machst du?", "en": "What are you doing?", "zh": "你在做什么？"}
            },
            "sagen": {
                "pos": "verb",
                "translations_en": ["to say", "to tell"],
                "translations_zh": ["说", "告诉"],
                "example": {"de": "Was sagst du?", "en": "What do you say?", "zh": "你说什么？"}
            },
            "sehen": {
                "pos": "verb",
                "translations_en": ["to see"],
                "translations_zh": ["看见"],
                "example": {"de": "Ich kann dich sehen.", "en": "I can see you.", "zh": "我能看见你。"}
            },
            "wissen": {
                "pos": "verb",
                "translations_en": ["to know"],
                "translations_zh": ["知道"],
                "example": {"de": "Ich weiß es nicht.", "en": "I don't know.", "zh": "我不知道。"}
            },
            "gut": {
                "pos": "adjective",
                "translations_en": ["good", "well"],
                "translations_zh": ["好", "良好"],
                "example": {"de": "Das ist gut.", "en": "That is good.", "zh": "这很好。"}
            },
            "groß": {
                "pos": "adjective",
                "translations_en": ["big", "large", "tall"],
                "translations_zh": ["大", "高"],
                "example": {"de": "Das ist sehr groß.", "en": "That is very big.", "zh": "那个很大。"}
            },
            "klein": {
                "pos": "adjective", 
                "translations_en": ["small", "little"],
                "translations_zh": ["小"],
                "example": {"de": "Das Haus ist klein.", "en": "The house is small.", "zh": "房子很小。"}
            }
        }

    async def get_or_create_word(
        self, 
        db: Session, 
        lemma: str, 
        user: User
    ) -> Dict[str, Any]:
        """
        统一的单词查询接口：
        1. 先查本地词库
        2. 不存在则调用OpenAI分析
        3. 保存到词库供后续使用
        4. 记录用户搜索历史
        """
        
        # 1. 先查本地词库（精确匹配或变位匹配）
        existing_word = await self._find_existing_word(db, lemma)
        
        if existing_word:
            # 记录搜索历史
            await self._log_search_history(db, user, lemma, "word_lookup", from_database=True)
            
            # 返回格式化的词库数据
            return await self._format_word_data(existing_word, from_database=True)
        
        # 2. 本地不存在，先尝试fallback字典，然后调用OpenAI分析
        fallback_data = self._get_fallback_translation(lemma.lower())
        
        if fallback_data:
            print(f"Using fallback translation for '{lemma}'")
            # 创建并保存fallback数据到数据库
            word = await self._save_word_to_database(db, lemma, fallback_data)
            await self._log_search_history(db, user, lemma, "word_lookup", from_database=False)
            return await self._format_word_data(word, from_database=False, openai_data=fallback_data)
        
        # 3. 没有fallback，调用OpenAI分析
        try:
            print(f"Word '{lemma}' not found in database, calling OpenAI...")
        except UnicodeEncodeError:
            print("Word not found in database, calling OpenAI...")
        
        try:
            openai_analysis = await self.openai_service.analyze_word(lemma)
        except Exception as openai_error:
            print(f"OpenAI failed for '{lemma}': {openai_error}")
            # OpenAI failed, try fallback for similar words or return not found
            return {
                "found": False,
                "original": lemma,
                "message": f"Translation for '{lemma}' is not available. Please check your spelling or try a different word.",
                "suggestions": [],
                "source": "error_fallback"
            }
        
        # 检查OpenAI是否找到了有效的词汇
        if not openai_analysis:
            raise ValueError("OpenAI returned no analysis")
        
        # 如果OpenAI没有找到词汇，返回建议
        if not openai_analysis.get("found", True):
            await self._log_search_history(db, user, lemma, "word_lookup_not_found", from_database=False)
            return {
                "found": False,
                "original": lemma,
                "suggestions": openai_analysis.get("suggestions", []),
                "message": openai_analysis.get("message", f"'{lemma}' is not a recognized German word."),
                "source": "openai_suggestions"
            }
        
        # 验证找到的词汇数据
        if not openai_analysis.get("pos"):
            raise ValueError("OpenAI returned invalid analysis payload for word")
        
        # 3. 保存到本地词库
        word = await self._save_word_to_database(db, lemma, openai_analysis)
        
        # 4. 记录搜索历史
        await self._log_search_history(db, user, lemma, "word_lookup", from_database=False)
        
        # 5. 返回统一格式数据
        return await self._format_word_data(word, from_database=False, openai_data=openai_analysis)

    async def _find_existing_word(self, db: Session, lemma: str) -> Optional[WordLemma]:
        """查找现有单词（支持变位查找）"""
        
        # 直接匹配lemma
        word = db.query(WordLemma).filter(WordLemma.lemma.ilike(lemma)).first()
        if word:
            return word
        
        # 查找词形变位（如gehe -> gehen）
        word_form = db.query(WordForm).filter(WordForm.form.ilike(lemma)).first()
        if word_form:
            return word_form.lemma
            
        # 去除冠词后匹配（如der Tisch -> Tisch）
        lemma_clean = self._clean_lemma(lemma)
        if lemma_clean != lemma:
            word = db.query(WordLemma).filter(WordLemma.lemma.ilike(lemma_clean)).first()
            if word:
                return word
        
        return None
    
    def _get_fallback_translation(self, lemma: str) -> Optional[Dict[str, Any]]:
        """Get fallback translation from built-in dictionary"""
        return self.fallback_translations.get(lemma)

    async def _save_word_to_database(
        self, 
        db: Session, 
        original_query: str, 
        openai_analysis: Dict[str, Any]
    ) -> WordLemma:
        """将OpenAI分析结果保存到词库"""
        
        # 验证OpenAI分析结果
        if not self._validate_openai_analysis(openai_analysis, original_query):
            raise ValueError(f"Invalid OpenAI analysis data for word '{original_query}' - skipping database insertion")
        
        # 提取主要信息，使用原始查询作为lemma
        lemma = original_query.strip()
        pos = openai_analysis.get("pos", "unknown")
        
        # 创建词条
        word = WordLemma(
            lemma=lemma,
            pos=pos,
            cefr="A1",  # 默认级别
            notes=f"Auto-generated from OpenAI on query: {original_query}"
        )
        
        db.add(word)
        db.commit()
        db.refresh(word)
        
        # 保存翻译（验证后）
        translations_en = openai_analysis.get("translations_en", [])
        translations_zh = openai_analysis.get("translations_zh", [])
        
        # Determine source (fallback or openai)
        source = "fallback" if lemma.lower() in self.fallback_translations else "openai"
        
        # 保存有效的英文翻译
        for trans in translations_en:
            if self._is_valid_translation(trans):
                translation = Translation(
                    lemma_id=word.id,
                    lang_code="en",
                    text=trans.strip(),
                    source=source
                )
                db.add(translation)
        
        # 保存有效的中文翻译
        for trans in translations_zh:
            if self._is_valid_translation(trans):
                translation = Translation(
                    lemma_id=word.id,
                    lang_code="zh",
                    text=trans.strip(),
                    source=source
                )
                db.add(translation)
        
        # 保存例句（验证后）
        example_data = openai_analysis.get("example")
        if example_data and self._is_valid_example(example_data):
            example = Example(
                lemma_id=word.id,
                de_text=example_data.get("de", "").strip(),
                en_text=example_data.get("en", "").strip(),
                zh_text=example_data.get("zh", "").strip(),
                level="A1"  # 默认级别，可以后续改进
            )
            db.add(example)
        
        # 保存动词变位表（如果是动词且变位表有效）
        if pos == "verb" and "tables" in openai_analysis:
            tables = openai_analysis["tables"]
            if self._is_valid_verb_tables(tables):
                await self._save_verb_forms(db, word.id, tables)
        
        db.commit()
        return word

    async def _save_verb_forms(self, db: Session, lemma_id: int, tables: Dict[str, Any]):
        """保存动词变位表"""
        
        for tense, forms in tables.items():
            if isinstance(forms, dict):
                for person, form in forms.items():
                    if form and person != "aux" and person != "partizip_ii":
                        word_form = WordForm(
                            lemma_id=lemma_id,
                            form=form,
                            feature_key="tense",
                            feature_value=f"{tense}_{person}"
                        )
                        db.add(word_form)

    async def _format_word_data(
        self, 
        word: WordLemma, 
        from_database: bool = True,
        openai_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """统一格式化词汇数据"""
        
        if from_database:
            # 从数据库格式化
            translations_en = [t.text for t in word.translations if t.lang_code == "en"]
            translations_zh = [t.text for t in word.translations if t.lang_code == "zh"]
            
            # 如果数据库中没有翻译，尝试使用fallback
            if not translations_en and not translations_zh:
                fallback_data = self._get_fallback_translation(word.lemma.lower())
                if fallback_data:
                    translations_en = fallback_data.get("translations_en", [])
                    translations_zh = fallback_data.get("translations_zh", [])
            
            return {
                "found": True,  # 重要：前端需要这个字段来显示词汇分析
                "original": word.lemma,
                "pos": word.pos,
                "article": self._extract_article_from_forms(word.forms) if word.pos == "noun" else None,
                "plural": self._extract_plural_from_forms(word.forms) if word.pos == "noun" else None,
                "tables": self._format_verb_tables(word.forms) if word.pos == "verb" and word.forms else None,
                "translations_en": translations_en,
                "translations_zh": translations_zh,
                "example": self._format_example(word.examples[0]) if word.examples else None,
                "cached": True,
                "source": "database"
            }
        else:
            # 使用OpenAI原始数据，但确保有original字段
            formatted_data = {
                "found": openai_data.get("found", True),  # 来自OpenAI的数据应该已经包含found字段
                "original": word.lemma,
                "pos": openai_data.get("pos", "unknown"),
                "article": openai_data.get("article"),
                "plural": openai_data.get("plural"),
                "tables": openai_data.get("tables"),
                "translations_en": openai_data.get("translations_en", []),
                "translations_zh": openai_data.get("translations_zh", []),
                "example": openai_data.get("example"),
                "cached": False,
                "source": "openai"
            }
            return formatted_data

    async def _log_search_history(
        self, 
        db: Session, 
        user: User, 
        query: str, 
        query_type: str,
        from_database: bool = True
    ):
        """记录搜索历史"""
        
        history_entry = SearchHistory(
            user_id=user.id,
            query_text=query,
            query_type=f"{query_type}_{'db' if from_database else 'api'}",
            cached_result_id=None  # 不再使用cache表
        )
        
        db.add(history_entry)
        db.commit()

    def _clean_lemma(self, lemma: str) -> str:
        """清理lemma（去除冠词等）"""
        lemma = lemma.strip()
        
        # 去除德语冠词
        articles = ["der ", "die ", "das ", "Der ", "Die ", "Das "]
        for article in articles:
            if lemma.startswith(article):
                return lemma[len(article):]
        
        return lemma

    def _extract_article(self, lemma: str) -> Optional[str]:
        """从lemma中提取冠词（保留作为备用方法）"""
        lemma = lemma.strip()
        articles = ["der", "die", "das"]
        
        for article in articles:
            if lemma.lower().startswith(f"{article} "):
                return article
        
        return None
    
    def _extract_article_from_notes(self, notes: Optional[str]) -> Optional[str]:
        """从notes字段中提取冠词"""
        if not notes:
            return None
        
        # 查找 article:der/die/das 格式
        if "article:" in notes:
            article_part = notes.split("article:")[1].strip()
            # 取第一个单词（去除可能的其他内容）
            article = article_part.split()[0] if article_part else ""
            
            # 验证是有效的德语冠词
            if article.lower() in ["der", "die", "das"]:
                return article.lower()
        
        return None
    
    def _extract_plural_from_notes(self, notes: Optional[str]) -> Optional[str]:
        """从notes字段中提取复数形式"""
        if not notes:
            return None
        
        # 查找 plural:复数形式 格式
        if "plural:" in notes:
            plural_part = notes.split("plural:")[1].strip()
            # 取第一个单词（去除可能的其他内容）
            plural = plural_part.split()[0] if plural_part else ""
            
            if plural and len(plural) > 0:
                return plural
        
        return None
    
    def _extract_article_from_forms(self, forms: List[WordForm]) -> Optional[str]:
        """从word_forms表中提取冠词"""
        if not forms:
            return None
        
        for form in forms:
            if form.feature_key == "article" and form.feature_value == "article":
                # 验证是有效的德语冠词
                if form.form.lower() in ["der", "die", "das"]:
                    return form.form.lower()
        
        return None
    
    def _extract_plural_from_forms(self, forms: List[WordForm]) -> Optional[str]:
        """从word_forms表中提取复数形式"""
        if not forms:
            return None
        
        for form in forms:
            if form.feature_key == "plural" and form.feature_value == "plural":
                if form.form and len(form.form.strip()) > 0:
                    return form.form.strip()
        
        return None

    def _format_verb_tables(self, forms: List[WordForm]) -> Dict[str, Any]:
        """从WordForm列表格式化动词表 - 支持所有时态的动态显示"""
        tables = {}
        
        # Tense normalization mapping for frontend compatibility
        tense_mapping = {
            # Keep standard tenses as-is
            'praesens': 'praesens',
            'praeteritum': 'praeteritum', 
            'perfekt': 'perfekt',
            'plusquamperfekt': 'plusquamperfekt',
            'imperativ': 'imperativ',
            
            # Normalize futur variants
            'futur1': 'futur_i',
            'futur_i': 'futur_i',
            'futur_ii': 'futur_ii',
            'futur2': 'futur_ii',
            
            # Normalize konjunktiv
            'konjunktiv_i': 'konjunktiv_i',
            'konjunktiv_ii': 'konjunktiv_ii',
            
            # Legacy support
            'futur': 'futur_i',
            'konjunktiv': 'konjunktiv_ii'  # Default to II if not specified
        }
        
        for form in forms:
            if form.feature_key == "tense":
                tense_person = form.feature_value
                if "_" in tense_person:
                    # Parse tense and person with special handling for er_sie_es pattern
                    tense, person = self._parse_tense_person(tense_person)
                    
                    # Normalize tense name for frontend consistency
                    normalized_tense = tense_mapping.get(tense, tense)
                    
                    if normalized_tense not in tables:
                        tables[normalized_tense] = {}
                    
                    tables[normalized_tense][person] = form.form
        
        return tables if tables else None

    def _parse_tense_person(self, tense_person: str) -> tuple[str, str]:
        """Parse tense_person patterns with special handling for complex cases"""
        
        # Known person patterns that contain underscores
        complex_persons = ["er_sie_es", "sie_Sie"]
        
        # Check if any complex person is at the end
        for complex_person in complex_persons:
            if tense_person.endswith("_" + complex_person):
                tense = tense_person[:-len("_" + complex_person)]
                return tense, complex_person
        
        # Standard parsing for simple cases
        parts = tense_person.split("_")
        
        if len(parts) == 2:
            # Simple pattern: praesens_ich, imperativ_du  
            return parts[0], parts[1]
        elif len(parts) == 3 and parts[0] in ["futur", "konjunktiv"]:
            # Complex pattern: futur_i_ich, konjunktiv_ii_du
            tense = f"{parts[0]}_{parts[1]}"
            person = parts[2]
            return tense, person
        else:
            # Fallback: last part is person, everything else is tense
            person = parts[-1]
            tense = "_".join(parts[:-1])
            return tense, person

    def _format_example(self, example: Example) -> Dict[str, str]:
        """格式化例句"""
        return {
            "de": example.de_text,
            "en": example.en_text or "",
            "zh": example.zh_text or ""
        }

    def _validate_openai_analysis(self, analysis: Dict[str, Any], original_query: str) -> bool:
        """验证OpenAI分析结果是否有效"""
        
        # 基础验证
        if not analysis or not isinstance(analysis, dict):
            print(f"ERROR: Validation failed: Analysis result empty or invalid format - {original_query}")
            return False
        
        # 验证和标准化词性
        pos = analysis.get("pos", "").strip()
        pos = self._normalize_pos(pos)  # Normalize POS to standard categories
        analysis["pos"] = pos  # Update analysis with normalized POS
        # Expanded POS categories for Collins Dictionary support
        valid_pos = [
            # Basic categories (existing)
            "noun", "adj", "pron", "prep", "adv", "det", "particle",
            
            # Verb categories (Collins Dictionary style)
            "verb",      # general verb (for backward compatibility) 
            "vt",        # transitive verb
            "vi",        # intransitive verb
            "vr",        # reflexive verb
            "aux",       # auxiliary verb
            "modal",     # modal verb
            
            # Additional categories
            "conj",      # conjunction
            "interj",    # interjection
            "num",       # numeral
            "art",       # article (specific determiner type)
            
            # SubPOS categories for complex verbs
            "vi_impers",     # impersonal intransitive
            "vt_impers",     # impersonal transitive  
            "vi_prep_obj",   # intransitive with prep object
            "vt_prep_obj"    # transitive with prep object
        ]
        if not pos or pos not in valid_pos:
            print(f"ERROR: Validation failed: Invalid POS '{pos}' - {original_query}")
            return False
        
        # 验证翻译 - 至少要有一个有效的翻译
        translations_en = analysis.get("translations_en", [])
        translations_zh = analysis.get("translations_zh", [])
        
        valid_en_count = sum(1 for trans in translations_en if self._is_valid_translation(trans))
        valid_zh_count = sum(1 for trans in translations_zh if self._is_valid_translation(trans))
        
        if valid_en_count == 0 and valid_zh_count == 0:
            print(f"ERROR: Validation failed: No valid translations - {original_query}")
            return False
        
        print(f"SUCCESS: Validation passed: {original_query} ({pos}) - EN: {valid_en_count}, ZH: {valid_zh_count}")
        return True

    def _is_valid_translation(self, translation: Any) -> bool:
        """验证单个翻译是否有效"""
        if not isinstance(translation, str):
            return False
        
        translation = translation.strip()
        
        # 检查长度
        if len(translation) == 0 or len(translation) > 200:
            return False
        
        # 检查是否包含有效字符
        if not any(c.isalpha() or c.isdigit() for c in translation):
            return False
        
        # 过滤明显无效的翻译
        invalid_patterns = [
            "...", "???", "---", "n/a", "null", "none", "undefined",
            "error", "invalid", "无效", "错误", "未知"
        ]
        
        for pattern in invalid_patterns:
            if pattern in translation.lower():
                return False
        
        return True

    def _is_valid_example(self, example: Dict[str, Any]) -> bool:
        """验证例句是否有效"""
        if not isinstance(example, dict):
            return False
        
        de_text = example.get("de", "").strip()
        en_text = example.get("en", "").strip()
        zh_text = example.get("zh", "").strip()
        
        # 德语例句必须存在且有意义
        if not de_text or len(de_text) < 3:
            return False
        
        # 至少要有一个翻译
        if not en_text and not zh_text:
            return False
        
        # 检查例句长度
        if len(de_text) > 500:
            return False
        
        return True

    def _is_valid_verb_tables(self, tables: Dict[str, Any]) -> bool:
        """验证动词变位表是否有效"""
        if not isinstance(tables, dict) or not tables:
            return False
        
        # 检查是否有至少一个有效的时态
        valid_tenses = 0
        for tense, forms in tables.items():
            if isinstance(forms, dict) and forms:
                # 检查是否有有效的变位形式
                valid_forms = 0
                for person, form in forms.items():
                    if (isinstance(form, str) and 
                        form.strip() and 
                        person not in ["aux", "partizip_ii"] and
                        len(form.strip()) > 0):
                        valid_forms += 1
                
                if valid_forms > 0:
                    valid_tenses += 1
        
        return valid_tenses > 0

    async def search_words(
        self, 
        db: Session, 
        query: str, 
        user: User,
        skip: int = 0,
        limit: int = 10
    ) -> Dict[str, Any]:
        """搜索词汇（支持模糊匹配）"""
        
        # 在本地词库中模糊搜索
        words_query = db.query(WordLemma).filter(
            or_(
                WordLemma.lemma.ilike(f"%{query}%"),
                WordLemma.pos.ilike(f"%{query}%")
            )
        )
        
        total = words_query.count()
        words = words_query.offset(skip).limit(limit).all()
        
        # 记录搜索历史
        await self._log_search_history(db, user, query, "word_search")
        
        results = []
        for word in words:
            formatted = await self._format_word_data(word, from_database=True)
            results.append(formatted)
        
        return {
            "results": results,
            "total": total,
            "cached": True,
            "source": "database_search"
        }
    
    def _normalize_pos(self, pos: str) -> str:
        """Normalize POS tags to our standard 8 categories"""
        if not pos:
            return pos
            
        pos = pos.lower().strip()
        
        # Map old/inconsistent POS tags to our expanded Collins Dictionary categories
        pos_mapping = {
            # Adjectives
            'adjective': 'adj',
            'adjectives': 'adj',
            
            # Pronouns  
            'pronoun': 'pron',
            'pronouns': 'pron',
            
            # Prepositions
            'preposition': 'prep',
            'prepositions': 'prep',
            'adposition': 'prep',
            'adp': 'prep',
            
            # Adverbs
            'adverb': 'adv',
            'adverbs': 'adv',
            
            # Determiners vs Articles (Collins distinction)
            'determiner': 'det',
            'article': 'art',        # Specific type: der, die, das
            'articles': 'art',
            
            # Verbs - Collins Dictionary style
            'verb': 'verb',          # Keep general for backward compatibility
            'transitive': 'vt',      # Transitive verb
            'intransitive': 'vi',    # Intransitive verb
            'reflexive': 'vr',       # Reflexive verb
            'auxiliary': 'aux',      # Auxiliary verb (haben, sein, werden)
            'modal': 'modal',        # Modal verbs (können, müssen, etc.)
            
            # Complex verb subtypes
            'vi impers': 'vi_impers',       # Impersonal intransitive
            'vt impers': 'vt_impers',       # Impersonal transitive
            'vi+prep obj': 'vi_prep_obj',   # Intransitive with prep object
            'vt+prep obj': 'vt_prep_obj',   # Transitive with prep object
            
            # Other Collins categories
            'conjunction': 'conj',    # Now separate category
            'interjection': 'interj', # Now separate category  
            'numeral': 'num',        # Now separate category
            'number': 'num',
            
            # Legacy mappings (fallback to particle for unknown)
            'other': 'particle',
        }
        
        return pos_mapping.get(pos, pos)