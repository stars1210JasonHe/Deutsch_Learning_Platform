"""
词库种子数据 - 预填充常用德语词汇
这样用户搜索时大部分词汇都能从本地数据库直接获取，减少OpenAI API调用
"""
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.word import WordLemma, Translation, Example, WordForm
from app.models.user import User, UserRole
import asyncio


# 常用德语词汇种子数据
SEED_VOCABULARY = [
    {
        "lemma": "sein",
        "pos": "verb",
        "cefr": "A1",
        "ipa": "zaɪn",
        "frequency": 9999,
        "translations_en": ["to be"],
        "translations_zh": ["是", "存在"],
        "example": {
            "de": "Ich bin Student.",
            "en": "I am a student.",
            "zh": "我是学生。"
        },
        "verb_forms": {
            "praesens": {
                "ich": "bin",
                "du": "bist", 
                "er_sie_es": "ist",
                "wir": "sind",
                "ihr": "seid",
                "sie_Sie": "sind"
            },
            "praeteritum": {
                "ich": "war",
                "du": "warst",
                "er_sie_es": "war", 
                "wir": "waren",
                "ihr": "wart",
                "sie_Sie": "waren"
            }
        }
    },
    {
        "lemma": "haben",
        "pos": "verb",
        "cefr": "A1",
        "ipa": "ˈhaːbn̩",
        "frequency": 9998,
        "translations_en": ["to have"],
        "translations_zh": ["有", "拥有"],
        "example": {
            "de": "Ich habe einen Hund.",
            "en": "I have a dog.",
            "zh": "我有一只狗。"
        },
        "verb_forms": {
            "praesens": {
                "ich": "habe",
                "du": "hast",
                "er_sie_es": "hat",
                "wir": "haben", 
                "ihr": "habt",
                "sie_Sie": "haben"
            }
        }
    },
    {
        "lemma": "gehen",
        "pos": "verb", 
        "cefr": "A1",
        "ipa": "ˈɡeːən",
        "frequency": 8000,
        "translations_en": ["to go"],
        "translations_zh": ["去", "走"],
        "example": {
            "de": "Ich gehe nach Hause.",
            "en": "I go home.", 
            "zh": "我回家。"
        },
        "verb_forms": {
            "praesens": {
                "ich": "gehe",
                "du": "gehst",
                "er_sie_es": "geht",
                "wir": "gehen",
                "ihr": "geht", 
                "sie_Sie": "gehen"
            }
        }
    },
    {
        "lemma": "Tisch",
        "pos": "noun",
        "cefr": "A1",
        "ipa": "tɪʃ",
        "frequency": 1500,
        "translations_en": ["table", "desk"],
        "translations_zh": ["桌子", "台子"],
        "example": {
            "de": "Der Tisch ist groß.",
            "en": "The table is big.",
            "zh": "桌子很大。"
        },
        "article": "der",
        "plural": "Tische"
    },
    {
        "lemma": "Haus",
        "pos": "noun",
        "cefr": "A1", 
        "ipa": "haʊs",
        "frequency": 2500,
        "translations_en": ["house", "home"],
        "translations_zh": ["房子", "家"],
        "example": {
            "de": "Das Haus ist schön.",
            "en": "The house is beautiful.",
            "zh": "房子很漂亮。"
        },
        "article": "das",
        "plural": "Häuser"
    },
    {
        "lemma": "Wasser",
        "pos": "noun",
        "cefr": "A1",
        "ipa": "ˈvasɐ",
        "frequency": 3000,
        "translations_en": ["water"],
        "translations_zh": ["水"],
        "example": {
            "de": "Ich trinke Wasser.",
            "en": "I drink water.",
            "zh": "我喝水。"
        },
        "article": "das",
        "plural": "Wässer"
    },
    {
        "lemma": "gut",
        "pos": "adjective",
        "cefr": "A1",
        "ipa": "ɡuːt", 
        "frequency": 5000,
        "translations_en": ["good", "well"],
        "translations_zh": ["好的", "良好的"],
        "example": {
            "de": "Das Essen ist gut.",
            "en": "The food is good.",
            "zh": "食物很好。"
        }
    },
    {
        "lemma": "groß",
        "pos": "adjective",
        "cefr": "A1",
        "ipa": "ɡʁoːs",
        "frequency": 4000,
        "translations_en": ["big", "large", "great"],
        "translations_zh": ["大的", "巨大的"],
        "example": {
            "de": "Berlin ist eine große Stadt.",
            "en": "Berlin is a big city.",
            "zh": "柏林是一个大城市。"
        }
    },
    {
        "lemma": "arbeiten",
        "pos": "verb",
        "cefr": "A1",
        "ipa": "ˈaʁbaɪtn̩",
        "frequency": 3500,
        "translations_en": ["to work"],
        "translations_zh": ["工作"],
        "example": {
            "de": "Ich arbeite in München.",
            "en": "I work in Munich.",
            "zh": "我在慕尼黑工作。"
        },
        "verb_forms": {
            "praesens": {
                "ich": "arbeite",
                "du": "arbeitest",
                "er_sie_es": "arbeitet",
                "wir": "arbeiten",
                "ihr": "arbeitet",
                "sie_Sie": "arbeiten"
            }
        }
    },
    {
        "lemma": "Zeit",
        "pos": "noun",
        "cefr": "A1",
        "ipa": "tsaɪt",
        "frequency": 6000,
        "translations_en": ["time"],
        "translations_zh": ["时间"],
        "example": {
            "de": "Ich habe keine Zeit.",
            "en": "I have no time.",
            "zh": "我没有时间。"
        },
        "article": "die",
        "plural": "Zeiten"
    }
]


async def seed_vocabulary_database():
    """填充词库数据库"""
    
    db = SessionLocal()
    
    try:
        print("🌱 开始填充词库数据...")
        
        for word_data in SEED_VOCABULARY:
            # 检查词汇是否已存在
            existing = db.query(WordLemma).filter(
                WordLemma.lemma == word_data["lemma"]
            ).first()
            
            if existing:
                print(f"⏩ 词汇 '{word_data['lemma']}' 已存在，跳过")
                continue
            
            # 创建词条
            word = WordLemma(
                lemma=word_data["lemma"],
                pos=word_data["pos"],
                cefr=word_data.get("cefr"),
                ipa=word_data.get("ipa"),
                frequency=word_data.get("frequency", 0),
                notes=f"Seed data - {word_data['pos']}"
            )
            
            db.add(word)
            db.commit()
            db.refresh(word)
            
            # 添加翻译
            for lang, translations in [
                ("en", word_data.get("translations_en", [])),
                ("zh", word_data.get("translations_zh", []))
            ]:
                for translation_text in translations:
                    translation = Translation(
                        lemma_id=word.id,
                        lang_code=lang,
                        text=translation_text,
                        source="seed_data"
                    )
                    db.add(translation)
            
            # 添加例句
            example_data = word_data.get("example")
            if example_data:
                example = Example(
                    lemma_id=word.id,
                    de_text=example_data.get("de", ""),
                    en_text=example_data.get("en", ""),
                    zh_text=example_data.get("zh", ""),
                    level=word_data.get("cefr", "A1")
                )
                db.add(example)
            
            # 添加动词变位
            verb_forms = word_data.get("verb_forms", {})
            for tense, forms in verb_forms.items():
                for person, form in forms.items():
                    word_form = WordForm(
                        lemma_id=word.id,
                        form=form,
                        feature_key="tense",
                        feature_value=f"{tense}_{person}"
                    )
                    db.add(word_form)
            
            # 添加名词信息（冠词、复数）
            if word_data["pos"] == "noun":
                article = word_data.get("article")
                plural = word_data.get("plural")
                
                if article:
                    article_form = WordForm(
                        lemma_id=word.id,
                        form=f"{article} {word_data['lemma']}",
                        feature_key="article",
                        feature_value=article
                    )
                    db.add(article_form)
                
                if plural:
                    plural_form = WordForm(
                        lemma_id=word.id,
                        form=plural,
                        feature_key="number",
                        feature_value="plural"
                    )
                    db.add(plural_form)
            
            db.commit()
            print(f"✅ 添加词汇: {word_data['lemma']} ({word_data['pos']})")
        
        print(f"🎉 词库初始化完成！总共添加了 {len(SEED_VOCABULARY)} 个词汇")
        
        # 显示统计信息
        total_words = db.query(WordLemma).count()
        total_translations = db.query(Translation).count()
        total_examples = db.query(Example).count()
        
        print(f"📊 数据库统计:")
        print(f"   - 词汇总数: {total_words}")
        print(f"   - 翻译总数: {total_translations}")
        print(f"   - 例句总数: {total_examples}")
        
    except Exception as e:
        print(f"❌ 词库初始化失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(seed_vocabulary_database())