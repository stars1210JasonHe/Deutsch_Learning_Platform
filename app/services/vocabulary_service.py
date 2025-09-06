"""
Vocabulary Service - 统一词库管理
先查询本地词库，不存在才调用OpenAI，然后保存到词库
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.word import WordLemma, Translation, Example, WordForm
from app.models.search import SearchHistory
from app.services.openai_service import OpenAIService
from app.models.user import User


class VocabularyService:
    def __init__(self):
        self.openai_service = OpenAIService()
        
        # --- language gate settings ---
        self.LANGUAGE_CONF_THRESHOLD = 0.90
        self.MAX_LANGS_TO_SHOW = 3
        self.MAX_SENSES_PER_LANG = 5
        
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
        user: User,
        skip_language_gate: bool = False
    ) -> Dict[str, Any]:
        """
        统一的单词查询接口：
        1. 先查本地词库
        2. 语言门禁：如果不是"只德语"或存在其他强备选语言 → 返回 UI 建议（不落库）
        3. 不触发门禁或用户已确认德语 → 调用OpenAI分析 + 落库
        4. 记录搜索历史
        """
        
        # 1. 先查本地词库（精确匹配或变位匹配）
        existing_word = await self._find_existing_word(db, lemma)
        
        if existing_word:
            # Check if verb has complete conjugation data
            if existing_word.pos == "verb" and not self._has_complete_verb_conjugations(existing_word):
                print(f"Verb '{lemma}' found in database but missing conjugations, using OpenAI...")
                # Fall through to OpenAI analysis for complete conjugation data
                pass
            else:
                # 记录搜索历史
                await self._log_search_history(db, user, lemma, "word_lookup", from_database=True)
                
                # 返回格式化的词库数据
                return await self._format_word_data(existing_word, from_database=True)
        
        # 2. fallback dictionary (still immediate)
        fallback_data = self._get_fallback_translation(lemma.lower())
        if fallback_data:
            word = await self._save_word_to_database(db, lemma, fallback_data)
            await self._log_search_history(db, user, lemma, "word_lookup", from_database=False)
            return await self._format_word_data(word, from_database=False, openai_data=fallback_data)

        # 3. language gate (scenarios a/b/c/d with threshold 0.90)
        # Skip language gate for regular word search (non-translate mode)
        if not skip_language_gate:
            try:
                gate = await self._language_gate(lemma)
            except Exception as e:
                gate = {"scenario": "none", "error": str(e), "sections": []}

            if self._gate_wants_ui_stop(gate):
                # Hand back suggestions for UI to render, do NOT write to DB yet.
                await self._log_search_history(db, user, lemma, "lang_gate", from_database=False)
                return {
                    "found": False,
                    "original": lemma,
                    "flow": "multi_lang_suggestions",
                    "threshold": self.LANGUAGE_CONF_THRESHOLD,
                    "ui_suggestions": gate,   # render `sections`, use `cta` fields to pick/lookup
                    "source": "lang_gate"
                }

        # 4. Not stopped by the gate → treat as German and analyze+save
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
        """Find by lemma or any inflected form; eager-load all relations used downstream."""
        q = db.query(WordLemma).options(
            joinedload(WordLemma.forms),
            joinedload(WordLemma.translations),
            joinedload(WordLemma.examples),
            joinedload(WordLemma.verb_props),
        )

        # exact lemma
        word = q.filter(WordLemma.lemma.ilike(lemma)).first()
        if word:
            return word

        # by word form
        form = db.query(WordForm).filter(WordForm.form.ilike(lemma)).first()
        if form:
            return q.filter(WordLemma.id == form.lemma_id).first()

        # strip leading article and retry
        lemma_clean = self._clean_lemma(lemma)
        if lemma_clean != lemma:
            return q.filter(WordLemma.lemma.ilike(lemma_clean)).first()

        return None

    def _get_fallback_translation(self, lemma: str) -> Optional[Dict[str, Any]]:
        """Get fallback translation from built-in dictionary"""
        return self.fallback_translations.get(lemma)

    async def _language_gate(self, surface: str) -> Dict[str, Any]:
        """
        Run the multi-language detector/translator aggregator.
        Returns a dict with scenario + sections (UI-ready).
        """
        return await self.openai_service.translate_ambiguous_to_german_v2(
            text=surface,
            min_conf=self.LANGUAGE_CONF_THRESHOLD,
            max_langs=self.MAX_LANGS_TO_SHOW,
            max_senses=self.MAX_SENSES_PER_LANG
        )

    def _gate_wants_ui_stop(self, gate: Dict[str, Any]) -> bool:
        """
        Decide if we should pause and let the UI show choices.
        True -> return suggestions to frontend and DO NOT write DB yet.
        False -> proceed with normal German lookup/creation.
        Rules:
          - If no language passed threshold -> proceed (False).
          - If German not present at/above threshold -> stop for UI (True).
          - If German present AND there are other (non-DE) strong candidates -> stop for UI (True).
          - If only German passed -> proceed (False).
        """
        scenario = gate.get("scenario")
        if scenario == "none":
            return False

        # is there a compact German card?
        has_de = any(
            s.get("type") == "german_candidate" and s.get("lang") == "de"
            for s in gate.get("sections", [])
        )
        non_de_sections = [s for s in gate.get("sections", []) if s.get("type") == "source_language"]

        if not has_de:
            # not confidently German -> let UI choose
            return True

        # German + others above threshold -> let UI choose one
        return len(non_de_sections) > 0

    async def resolve_candidate_and_save(
        self,
        db: Session,
        german_lemma: str,
        user: User
    ) -> Dict[str, Any]:
        """
        User picked a German candidate from the UI suggestions.
        We directly run the normal creation flow WITHOUT the language gate.
        """
        # try DB first
        existing_word = await self._find_existing_word(db, german_lemma)
        if existing_word:
            await self._log_search_history(db, user, german_lemma, "word_lookup", from_database=True)
            return await self._format_word_data(existing_word, from_database=True)

        # not in DB -> analyze + save
        try:
            openai_analysis = await self.openai_service.analyze_word(german_lemma)
        except Exception as openai_error:
            return {
                "found": False,
                "original": german_lemma,
                "message": f"Analysis failed for '{german_lemma}': {openai_error}",
                "suggestions": [],
                "source": "error_fallback"
            }

        if not openai_analysis or not openai_analysis.get("found", True):
            await self._log_search_history(db, user, german_lemma, "word_lookup_not_found", from_database=False)
            return {
                "found": False,
                "original": german_lemma,
                "suggestions": openai_analysis.get("suggestions", []) if openai_analysis else [],
                "message": (openai_analysis.get("message") if openai_analysis else f"'{german_lemma}' not recognized."),
                "source": "openai_suggestions"
            }

        if not openai_analysis.get("pos"):
            raise ValueError("OpenAI returned invalid analysis payload")

        word = await self._save_word_to_database(db, german_lemma, openai_analysis)
        await self._log_search_history(db, user, german_lemma, "word_lookup", from_database=False)
        return await self._format_word_data(word, from_database=False, openai_data=openai_analysis)
    async def _save_word_to_database(self, db: Session, original_query: str, openai_analysis: Dict[str, Any]) -> WordLemma:
        """Save OpenAI analysis to DB (idempotent/upsert-ish)."""
        if not self._validate_openai_analysis(openai_analysis, original_query):
            raise ValueError(f"Invalid OpenAI analysis data for word '{original_query}'")

        # prefer base lemma from AI, fallback to original
        target_lemma = (openai_analysis.get("lemma") or original_query).strip()

        pos = self._normalize_pos(openai_analysis.get("pos", "unknown"))

        # try to find existing lemma (case-insensitive)
        word = db.query(WordLemma).filter(WordLemma.lemma.ilike(target_lemma)).first()
        if word:
            # update POS if empty/mismatched (optional: keep first POS if you want)
            if not word.pos:
                word.pos = pos
        else:
            word = WordLemma(
                lemma=target_lemma,
                pos=pos,
                cefr="A1",
                notes=f"Auto-generated from OpenAI on query: {original_query}"
            )
            db.add(word)
            db.commit()
            db.refresh(word)

        # translations (de-dupe simple)
        source = "fallback" if target_lemma.lower() in self.fallback_translations else "openai"
        for lang, key in (("en","translations_en"), ("zh","translations_zh")):
            for t in openai_analysis.get(key, []) or []:
                t = (t or "").strip()
                if not self._is_valid_translation(t):
                    continue
                exists = db.query(Translation).filter(
                    Translation.lemma_id == word.id,
                    Translation.lang_code == lang,
                    Translation.text == t
                ).first()
                if not exists:
                    db.add(Translation(lemma_id=word.id, lang_code=lang, text=t, source=source))

        # example
        example_data = openai_analysis.get("example")
        if example_data and self._is_valid_example(example_data):
            # avoid duplicating the same example
            exists = db.query(Example).filter(
                Example.lemma_id == word.id,
                Example.de_text == (example_data.get("de") or "").strip()
            ).first()
            if not exists:
                db.add(Example(
                    lemma_id=word.id,
                    de_text=example_data.get("de","").strip(),
                    en_text=example_data.get("en","").strip(),
                    zh_text=example_data.get("zh","").strip(),
                    level="A1"
                ))

        # verb props + forms
        if pos.startswith("v") and openai_analysis.get("verb_props"):
            await self._save_verb_props(db, word.id, openai_analysis["verb_props"])

        if openai_analysis.get("word_forms"):
            await self._save_word_forms_unified(db, word.id, openai_analysis["word_forms"])

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

    # async def _save_verb_props(self, db: Session, lemma_id: int, verb_props: Dict[str, Any]):
    #     """保存动词属性到VerbProps表"""
    #     from app.models.word import VerbProps
        
    #     # 创建VerbProps对象
    #     verb_prop = VerbProps(
    #         lemma_id=lemma_id,
    #         aux=verb_props.get("aux"),
    #         partizip_ii=verb_props.get("partizip_ii"),
    #         regularity=verb_props.get("regularity"),
    #         separable=verb_props.get("separable", 0),
    #         prefix=verb_props.get("prefix"),
    #         reflexive=verb_props.get("reflexive", 0),
    #         valency_json=verb_props.get("valency_json")
    #     )
    #     db.add(verb_prop)
    async def _save_verb_props(self, db: Session, lemma_id: int, verb_props: Dict[str, Any]):
        """Upsert into VerbProps using the correct PK column name."""
        from app.models.word import VerbProps

        # figure out correct FK column name once
        fk_field = "sense_id" if hasattr(VerbProps, "sense_id") else "lemma_id"

        # try to fetch existing
        existing = db.query(VerbProps).filter(getattr(VerbProps, fk_field) == lemma_id).first()

        payload = {
            "aux": verb_props.get("aux"),
            "partizip_ii": verb_props.get("partizip_ii"),
            "regularity": verb_props.get("regularity"),
            "separable": int(verb_props.get("separable", 0)),
            "prefix": verb_props.get("prefix"),
            "reflexive": int(verb_props.get("reflexive", 0)),
            "valency_json": verb_props.get("valency_json"),
        }

        if existing:
            for k, v in payload.items():
                setattr(existing, k, v)
        else:
            row = VerbProps(**{fk_field: lemma_id}, **payload)
            db.add(row)

    async def _save_word_forms_unified(self, db: Session, lemma_id: int, word_forms: list):
        """保存统一的word_forms格式到WordForm表"""
        for wf in word_forms:
            if not isinstance(wf, dict):
                continue
            
            feature_key = wf.get("feature_key", "").strip()
            feature_value = wf.get("feature_value", "").strip()
            form = wf.get("form", "").strip()
            
            # 确保必要字段存在
            if not feature_key or not feature_value or not form:
                continue
                
            # 创建WordForm条目
            word_form = WordForm(
                lemma_id=lemma_id,
                feature_key=feature_key,
                feature_value=feature_value,
                form=form
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
            
            # Extract new grammatical features based on POS
            degree_forms = None
            governance = None
            adv_type = None
            conj_type = None
            pron_info = None
            det_type = None
            num_info = None
            particle_type = None
            interj_register = None
            
            pos_tags = set(tag.strip().lower() for tag in word.pos.split('|'))
            
            if "adj" in pos_tags:
                degree_forms = self._extract_degree_forms(word.forms)
            elif "prep" in pos_tags or "preposition" in pos_tags:
                governance = self._extract_governance(word.forms)
            elif "adv" in pos_tags:
                adv_type = self._extract_adverb_type(word.forms)
            elif "conj" in pos_tags:
                conj_type = self._extract_conjunction_type(word.forms)
            elif "pron" in pos_tags:
                pron_info = self._extract_pronoun_info(word.forms)
            elif "det" in pos_tags:
                det_type = self._extract_determiner_type(word.forms)
            elif "num" in pos_tags or "numeral" in pos_tags:
                num_info = self._extract_numeral_info(word.forms)
            elif "particle" in pos_tags:
                particle_type = self._extract_particle_type(word.forms)
            elif "interj" in pos_tags:
                interj_register = self._extract_interjection_register(word.forms)
            
            return {
                "found": True,  # 重要：前端需要这个字段来显示词汇分析
                "original": word.lemma,
                "pos": word.pos,
                "article": self._extract_article_from_forms(word.forms) if "noun" in pos_tags else None,
                "plural": self._extract_plural_from_forms(word.forms) if "noun" in pos_tags else None,
                "tables": self._format_verb_tables(word.forms) if "verb" in word.pos.lower() and word.forms else None,
                "verb_props": self._format_verb_props(word.verb_props) if "verb" in word.pos.lower() and word.verb_props else None,
                "degree_forms": degree_forms,
                "governance": governance,
                "adv_type": adv_type,
                "conj_type": conj_type,
                "pron_info": pron_info,
                "det_type": det_type,
                "num_info": num_info,
                "particle_type": particle_type,
                "interj_register": interj_register,
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

    def _has_complete_verb_conjugations(self, word: WordLemma) -> bool:
        """Check if a verb has complete conjugation data (at least present tense)"""
        if not word.forms:
            return False
        
        # Check if we have at least present tense conjugations
        present_forms = []
        for form in word.forms:
            if form.feature_key == "tense" and form.feature_value.startswith("praesens_"):
                present_forms.append(form.feature_value)
        
        # Should have at least 4-6 persons for present tense (ich, du, er/sie/es, wir, ihr, sie/Sie)
        return len(present_forms) >= 4

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
            if form.feature_key == "gender" and form.feature_value in ["masc", "fem", "neut"]:
                # 验证是有效的德语冠词
                if form.form.lower() in ["der", "die", "das"]:
                    return form.form.lower()
        
        return None
    
    def _extract_plural_from_forms(self, forms: List[WordForm]) -> Optional[str]:
        """从word_forms表中提取复数形式"""
        if not forms:
            return None
        
        for form in forms:
            if form.feature_key == "number" and form.feature_value == "plural":
                if form.form and len(form.form.strip()) > 0:
                    return form.form.strip()
        
        return None
    
    def _extract_degree_forms(self, forms: List[WordForm]) -> Optional[Dict[str, str]]:
        """Extract positive, comparative, and superlative forms for adjectives"""
        if not forms:
            return None
        
        degree_forms = {}
        for form in forms:
            if form.feature_key == "degree":
                if form.feature_value == "positive":
                    degree_forms["positive"] = form.form
                elif form.feature_value == "comparative":
                    degree_forms["comparative"] = form.form
                elif form.feature_value == "superlative":
                    degree_forms["superlative"] = form.form
        
        return degree_forms if degree_forms else None
    
    def _extract_governance(self, forms: List[WordForm]) -> Optional[str]:
        """Extract case governance for prepositions"""
        if not forms:
            return None
        
        for form in forms:
            if form.feature_key == "governance" and form.feature_value:
                # Map abbreviated case codes to full names
                case_mapping = {
                    "akk": "accusative",
                    "dat": "dative", 
                    "gen": "genitive",
                    "wechsel": "accusative/dative"
                }
                case_code = form.feature_value.strip()
                return case_mapping.get(case_code, case_code)
        
        return None
    
    def _extract_adverb_type(self, forms: List[WordForm]) -> Optional[str]:
        """Extract type classification for adverbs"""
        if not forms:
            return None
        
        for form in forms:
            if form.feature_key == "adv_type" and form.feature_value:
                # Map abbreviated type codes to readable names
                type_mapping = {
                    "temporal": "temporal (time)",
                    "lokal": "locative (place)", 
                    "modal": "modal (manner)",
                    "kausal": "causal (reason)",
                    "grad": "degree (intensity)",
                    "negation": "negation",
                    "pronominal": "pronominal",
                    "satz": "sentence adverb",
                    "modalpartikel": "modal particle",
                    "fokuspartikel": "focus particle"
                }
                type_code = form.feature_value.strip()
                return type_mapping.get(type_code, type_code)
        
        return None
    
    def _extract_conjunction_type(self, forms: List[WordForm]) -> Optional[str]:
        """Extract conjunction type (coordinating/subordinating)"""
        if not forms:
            return None
        
        for form in forms:
            if form.feature_key == "conj_type" and form.feature_value:
                type_mapping = {
                    "coord": "coordinating",
                    "subord": "subordinating"
                }
                return type_mapping.get(form.feature_value.strip(), form.feature_value.strip())
        
        return None
    
    def _extract_pronoun_info(self, forms: List[WordForm]) -> Optional[Dict[str, Any]]:
        """Extract pronoun type and case forms"""
        if not forms:
            return None
        
        pron_info = {}
        
        # Get pronoun type
        for form in forms:
            if form.feature_key == "pron_type" and form.feature_value:
                pron_info["type"] = form.feature_value.strip()
                break
        
        # Get case forms
        cases = {}
        for form in forms:
            if form.feature_key == "case" and form.feature_value and form.form:
                cases[form.feature_value] = form.form
        
        if cases:
            pron_info["cases"] = cases
        
        return pron_info if pron_info else None
    
    def _extract_determiner_type(self, forms: List[WordForm]) -> Optional[str]:
        """Extract determiner/article type"""
        if not forms:
            return None
        
        for form in forms:
            if form.feature_key == "det_type" and form.feature_value:
                return form.feature_value.strip()
        
        return None
    
    def _extract_numeral_info(self, forms: List[WordForm]) -> Optional[Dict[str, Any]]:
        """Extract numeral type and value"""
        if not forms:
            return None
        
        num_info = {}
        
        for form in forms:
            if form.feature_key == "num_type" and form.feature_value:
                num_info["type"] = form.feature_value.strip()
            elif form.feature_key == "num_value" and form.feature_value:
                num_info["value"] = form.feature_value.strip()
        
        return num_info if num_info else None
    
    def _extract_particle_type(self, forms: List[WordForm]) -> Optional[str]:
        """Extract particle type"""
        if not forms:
            return None
        
        for form in forms:
            if form.feature_key == "particle_type" and form.feature_value:
                type_mapping = {
                    "modal": "modal particle",
                    "focus": "focus particle", 
                    "discourse": "discourse particle",
                    "response": "response particle",
                    "intensifier": "intensifier particle"
                }
                return type_mapping.get(form.feature_value.strip(), form.feature_value.strip())
        
        return None
    
    def _extract_interjection_register(self, forms: List[WordForm]) -> Optional[str]:
        """Extract interjection register (formality level)"""
        if not forms:
            return None
        
        for form in forms:
            if form.feature_key == "interj_register" and form.feature_value:
                return form.feature_value.strip()
        
        return None
    
    def _format_verb_props(self, verb_props) -> Optional[Dict[str, Any]]:
        """Format verb properties for frontend display"""
        if not verb_props:
            return None
            
        import json
        
        # Parse valency JSON if available
        valency_data = {}
        if verb_props.valency_json:
            try:
                valency_data = json.loads(verb_props.valency_json)
            except (json.JSONDecodeError, TypeError):
                valency_data = {}
        
        return {
            "separable": bool(verb_props.separable),
            "prefix": verb_props.prefix,
            "aux": verb_props.aux,  # "haben" or "sein"
            "regularity": verb_props.regularity,  # "strong", "weak", "mixed", "irregular"
            "partizip_ii": verb_props.partizip_ii,
            "reflexive": bool(verb_props.reflexive),
            "cases": valency_data.get("cases", []),  # ["accusative", "dative"]
            "preps": valency_data.get("preps", [])   # ["mit", "an"]
        }

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
        
        # 在本地词库中搜索 - 短查询使用精确匹配，长查询使用模糊搜索
        if len(query) >= 6:
            # 长查询允许子字符串搜索（用于复合词）
            words_query = db.query(WordLemma).filter(
                or_(
                    WordLemma.lemma.ilike(f"%{query}%"),
                    WordLemma.pos.ilike(f"%{query}%")
                )
            )
        else:
            # 短查询只进行精确匹配（避免错误的子字符串匹配）
            words_query = db.query(WordLemma).filter(
                or_(
                    WordLemma.lemma.ilike(query),
                    WordLemma.lemma.ilike(query.capitalize()),
                    WordLemma.lemma.ilike(query.upper()),
                    WordLemma.lemma.ilike(query.lower()),
                    WordLemma.pos.ilike(f"%{query}%")  # POS搜索保持模糊匹配
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
        """Normalize POS tags to your allowed set."""
        if not pos:
            return pos

        raw = pos.strip().lower()

        allowed = {
            "noun","adj","adv","prep","pron","det","art","conj","interj","num","particle",
            "verb","vt","vi","vr","aux","modal","vi_impers","vt_impers","vi_prep_obj","vt_prep_obj"
        }

        # canonical map (covers EN/DE labels + common abbreviations)
        m = {
            # nouns
            "n": "noun", "nomen": "noun", "substantiv": "noun",

            # adjectives
            "adjective": "adj", "adjectives": "adj", "adj.": "adj",

            # adverbs
            "adverb": "adv", "adverbs": "adv", "adv.": "adv",

            # prepositions
            "preposition": "prep", "prepositions": "prep", "adposition": "prep", "adp": "prep",
            "präposition": "prep", "präp": "prep",

            # determiners/articles
            "determiner": "det", "determiners": "det",
            "article": "art", "articles": "art", "artikel": "art",

            # pronouns
            "pronoun": "pron", "pronouns": "pron", "pronomen": "pron",

            # conjunctions
            "conjunction": "conj", "conjunctions": "conj", "konjunktion": "conj", "konj": "conj",

            # interjections
            "interjection": "interj", "interjections": "interj", "interjektion": "interj",

            # numerals
            "numeral": "num", "number": "num", "zahlenwort": "num", "zahlwort": "num",

            # particles
            "particle": "particle", "partikel": "particle",

            # verbs – coarse
            "verb": "verb", "v.": "verb",

            # verbs – fine
            "transitive": "vt", "transitive verb": "vt", "vt": "vt", "tr. v.": "vt", "tv": "vt",
            "intransitive": "vi", "intransitive verb": "vi", "vi": "vi", "intr. v.": "vi", "iv": "vi",
            "reflexive": "vr", "reflexive verb": "vr", "refl.": "vr", "vr": "vr",
            "auxiliary": "aux", "aux": "aux",
            "modal": "modal", "modalverb": "modal",

            # complex/impersonal patterns
            "vi impers": "vi_impers", "vi (impers)": "vi_impers", "impersonal intransitive": "vi_impers",
            "vt impers": "vt_impers", "vt (impers)": "vt_impers", "impersonal transitive": "vt_impers",
            "vi+prep obj": "vi_prep_obj", "vt+prep obj": "vt_prep_obj",
        }

        # exact map first
        if raw in m:
            norm = m[raw]
            return norm if norm in allowed else norm

        # heuristic rescue: look for keywords inside free-form labels
        s = raw.replace("-", " ").replace("/", " ")
        if "reflex" in s:
            return "vr"
        if "aux" in s:
            return "aux"
        if "modal" in s:
            return "modal"
        if "transitiv" in s or "transitive" in s:
            return "vt"
        if "intransitiv" in s or "intransitive" in s:
            return "vi"
        if "impers" in s or "impersonal" in s:
            # default to intransitive impersonal if not specified
            return "vi_impers"
        if "prep obj" in s:
            # if we can’t tell vt/vi reliably, default to vi_prep_obj
            return "vi_prep_obj"

        # if the raw tag is already allowed, keep it
        if raw in allowed:
            return raw

        # last resort: fall back by broad family
        if "verb" in s or raw in {"v"}:
            return "verb"
        if raw in {"a", "adj"}:
            return "adj"
        if raw in {"adv"}:
            return "adv"
        if raw in {"prep", "präp"}:
            return "prep"
        if "pron" in s:
            return "pron"
        if "det" in s:
            return "det"
        if "art" in s or "artikel" in s:
            return "art"
        if "conj" in s or "konj" in s:
            return "conj"
        if "interj" in s:
            return "interj"
        if "num" in s or "zahl" in s:
            return "num"
        if "part" in s:
            return "particle"

        # unknown → keep raw (so you can see and fix in data), but you could also return "particle"
        return raw
