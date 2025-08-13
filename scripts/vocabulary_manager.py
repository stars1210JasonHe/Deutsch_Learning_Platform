"""
词汇管理脚本 - 用于批量管理词库
"""
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.session import SessionLocal
from app.models.word import WordLemma, Translation, Example
from app.services.openai_service import OpenAIService


class VocabularyManager:
    def __init__(self):
        self.db = SessionLocal()
        self.openai_service = OpenAIService()

    async def batch_add_words(self, word_list: list[str]):
        """批量添加词汇到数据库"""
        
        print(f"📚 开始批量添加 {len(word_list)} 个词汇...")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for word in word_list:
            try:
                word = word.strip()
                if not word:
                    continue
                
                # 检查是否已存在
                existing = self.db.query(WordLemma).filter(
                    WordLemma.lemma.ilike(word)
                ).first()
                
                if existing:
                    print(f"⏩ '{word}' 已存在，跳过")
                    skip_count += 1
                    continue
                
                # 调用OpenAI分析
                print(f"🔍 分析词汇: {word}")
                analysis = await self.openai_service.analyze_word(word)
                
                # 创建词条
                lemma = WordLemma(
                    lemma=analysis.get("lemma", word),
                    pos=analysis.get("pos"),
                    notes=f"Batch imported via OpenAI analysis"
                )
                
                self.db.add(lemma)
                self.db.commit()
                self.db.refresh(lemma)
                
                # 添加翻译
                translations_en = analysis.get("translations_en", [])
                translations_zh = analysis.get("translations_zh", [])
                
                for trans in translations_en:
                    translation = Translation(
                        lemma_id=lemma.id,
                        lang_code="en",
                        text=trans,
                        source="openai_batch"
                    )
                    self.db.add(translation)
                
                for trans in translations_zh:
                    translation = Translation(
                        lemma_id=lemma.id,
                        lang_code="zh", 
                        text=trans,
                        source="openai_batch"
                    )
                    self.db.add(translation)
                
                # 添加例句
                example_data = analysis.get("example")
                if example_data:
                    example = Example(
                        lemma_id=lemma.id,
                        de_text=example_data.get("de", ""),
                        en_text=example_data.get("en", ""),
                        zh_text=example_data.get("zh", ""),
                        level="A1"
                    )
                    self.db.add(example)
                
                self.db.commit()
                print(f"✅ 添加成功: {word} ({analysis.get('pos', 'unknown')})")
                success_count += 1
                
                # 避免API速率限制
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ 处理 '{word}' 时出错: {e}")
                error_count += 1
                self.db.rollback()
        
        print(f"\n📊 批量添加完成:")
        print(f"   - 成功添加: {success_count}")
        print(f"   - 跳过已存在: {skip_count}")
        print(f"   - 错误: {error_count}")
        
        self.db.close()

    def show_stats(self):
        """显示词库统计信息"""
        
        total_words = self.db.query(WordLemma).count()
        total_translations = self.db.query(Translation).count()
        total_examples = self.db.query(Example).count()
        
        verbs = self.db.query(WordLemma).filter(WordLemma.pos == "verb").count()
        nouns = self.db.query(WordLemma).filter(WordLemma.pos == "noun").count()
        adjectives = self.db.query(WordLemma).filter(WordLemma.pos == "adjective").count()
        
        print("📊 词库统计信息:")
        print(f"   - 词汇总数: {total_words}")
        print(f"   - 翻译总数: {total_translations}")
        print(f"   - 例句总数: {total_examples}")
        print(f"   - 动词: {verbs}")
        print(f"   - 名词: {nouns}") 
        print(f"   - 形容词: {adjectives}")
        
        # 显示最近添加的词汇
        recent_words = self.db.query(WordLemma).order_by(
            WordLemma.created_at.desc()
        ).limit(10).all()
        
        print(f"\n📝 最近添加的词汇:")
        for word in recent_words:
            print(f"   - {word.lemma} ({word.pos or 'unknown'})")
        
        self.db.close()

    async def import_from_file(self, file_path: str):
        """从文件导入词汇列表"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                words = [line.strip() for line in f.readlines() if line.strip()]
            
            print(f"📁 从文件 {file_path} 读取到 {len(words)} 个词汇")
            await self.batch_add_words(words)
            
        except FileNotFoundError:
            print(f"❌ 文件不存在: {file_path}")
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")


# 一些常用词汇列表供参考
COMMON_GERMAN_WORDS = [
    # A1级别基础动词
    "machen", "sagen", "kommen", "sehen", "wissen", "geben", "stehen", "lassen",
    "finden", "bleiben", "liegen", "fahren", "nehmen", "tun", "denken", "sprechen",
    
    # A1级别基础名词  
    "Mann", "Frau", "Kind", "Jahr", "Tag", "Hand", "Welt", "Leben", "Stadt",
    "Auge", "Frage", "Arbeit", "Ende", "Land", "Teil", "Weg", "Seite",
    
    # A1级别基础形容词
    "neu", "alt", "klein", "deutsch", "eigen", "recht", "social", "jung",
    "hoch", "lang", "wenig", "möglich", "weit", "wichtig", "früh", "politisch",
    
    # A2级别词汇
    "verstehen", "bringen", "helfen", "zeigen", "lernen", "spielen", "leben",
    "kaufen", "essen", "trinken", "schlafen", "lachen", "weinen", "lieben"
]


async def main():
    """主函数"""
    
    if len(sys.argv) < 2:
        print("词汇管理工具使用方法:")
        print("  python vocabulary_manager.py stats          # 显示统计信息")
        print("  python vocabulary_manager.py add_common     # 添加常用词汇")
        print("  python vocabulary_manager.py import <file>  # 从文件导入")
        print("  python vocabulary_manager.py add <word1> <word2> ...  # 添加指定词汇")
        return
    
    manager = VocabularyManager()
    command = sys.argv[1]
    
    if command == "stats":
        manager.show_stats()
        
    elif command == "add_common":
        await manager.batch_add_words(COMMON_GERMAN_WORDS)
        
    elif command == "import" and len(sys.argv) > 2:
        file_path = sys.argv[2]
        await manager.import_from_file(file_path)
        
    elif command == "add" and len(sys.argv) > 2:
        words = sys.argv[2:]
        await manager.batch_add_words(words)
        
    else:
        print("❌ 无效的命令")


if __name__ == "__main__":
    asyncio.run(main())