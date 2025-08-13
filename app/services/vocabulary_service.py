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
        
        # 2. 本地不存在，调用OpenAI分析
        try:
            print(f"Word '{lemma}' not found in database, calling OpenAI...")
        except UnicodeEncodeError:
            print("Word not found in database, calling OpenAI...")
        
        openai_analysis = await self.openai_service.analyze_word(lemma)
        
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
        
        # 保存有效的英文翻译
        for trans in translations_en:
            if self._is_valid_translation(trans):
                translation = Translation(
                    lemma_id=word.id,
                    lang_code="en",
                    text=trans.strip(),
                    source="openai"
                )
                db.add(translation)
        
        # 保存有效的中文翻译
        for trans in translations_zh:
            if self._is_valid_translation(trans):
                translation = Translation(
                    lemma_id=word.id,
                    lang_code="zh",
                    text=trans.strip(),
                    source="openai"
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
            return {
                "original": word.lemma,
                "pos": word.pos,
                "article": self._extract_article_from_notes(word.notes) if word.pos == "noun" else None,
                "plural": None,  # TODO: 从数据库提取
                "tables": self._format_verb_tables(word.forms) if word.pos == "verb" and word.forms else None,
                "translations_en": [t.text for t in word.translations if t.lang_code == "en"],
                "translations_zh": [t.text for t in word.translations if t.lang_code == "zh"],
                "example": self._format_example(word.examples[0]) if word.examples else None,
                "cached": True,
                "source": "database"
            }
        else:
            # 使用OpenAI原始数据，但确保有original字段
            formatted_data = {
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

    def _format_verb_tables(self, forms: List[WordForm]) -> Dict[str, Any]:
        """从WordForm列表格式化动词表"""
        tables = {}
        
        for form in forms:
            if form.feature_key == "tense":
                tense_person = form.feature_value
                if "_" in tense_person:
                    tense, person = tense_person.split("_", 1)
                    if tense not in tables:
                        tables[tense] = {}
                    tables[tense][person] = form.form
        
        return tables if tables else None

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
            print(f"❌ 验证失败: 分析结果为空或格式错误 - {original_query}")
            return False
        
        # 验证词性
        pos = analysis.get("pos", "").strip()
        valid_pos = ["noun", "verb", "adjective", "adverb", "interjection", "pronoun", "preposition", "conjunction", "article", "other"]
        if not pos or pos not in valid_pos:
            print(f"❌ 验证失败: 无效的词性 '{pos}' - {original_query}")
            return False
        
        # 验证翻译 - 至少要有一个有效的翻译
        translations_en = analysis.get("translations_en", [])
        translations_zh = analysis.get("translations_zh", [])
        
        valid_en_count = sum(1 for trans in translations_en if self._is_valid_translation(trans))
        valid_zh_count = sum(1 for trans in translations_zh if self._is_valid_translation(trans))
        
        if valid_en_count == 0 and valid_zh_count == 0:
            print(f"❌ 验证失败: 没有有效的翻译 - {original_query}")
            return False
        
        print(f"✅ 验证通过: {original_query} ({pos}) - EN: {valid_en_count}, ZH: {valid_zh_count}")
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