#!/usr/bin/env python3
"""
为词汇添加例句 - 使用正确的大小写
"""
import sqlite3
from datetime import datetime

class ExampleAdderWithCorrectCase:
    def __init__(self):
        self.db_path = 'data/app.db'
        self.stats = {
            'examples_added': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def find_word_in_database(self, word_variants):
        """在数据库中查找词汇的正确形式"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for variant in word_variants:
                cursor.execute("SELECT id, lemma FROM word_lemmas WHERE lemma = ?", (variant,))
                result = cursor.fetchone()
                if result:
                    return result[0], result[1]  # id, lemma
            return None, None
        finally:
            conn.close()
    
    def add_example_for_word_variants(self, word_variants, example_data):
        """为词汇添加例句，自动查找正确的大小写形式"""
        lemma_id, correct_lemma = self.find_word_in_database(word_variants)
        
        if not lemma_id:
            print(f"   ❌ 词汇 {word_variants} 都不存在于数据库中")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查是否已有例句
            cursor.execute("SELECT COUNT(*) FROM examples WHERE lemma_id = ?", (lemma_id,))
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                print(f"   ℹ️  {correct_lemma} 已有 {existing_count} 个例句，跳过")
                return False
            
            # 添加例句
            cursor.execute("""
                INSERT INTO examples (lemma_id, de_text, en_text, zh_text)
                VALUES (?, ?, ?, ?)
            """, (
                lemma_id,
                example_data['de'],
                example_data['en'],
                example_data['zh']
            ))
            
            conn.commit()
            self.stats['examples_added'] += 1
            
            print(f"   ✅ {correct_lemma} 例句添加成功")
            print(f"      DE: {example_data['de']}")
            print(f"      EN: {example_data['en']}")
            print(f"      ZH: {example_data['zh']}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 添加 {correct_lemma} 例句时出错: {e}")
            self.stats['errors'] += 1
            conn.rollback()
            return False
            
        finally:
            conn.close()
    
    def add_priority_examples(self):
        """添加优先词汇的例句"""
        print("🚀 为优先词汇添加例句")
        print("=" * 40)
        
        # 词汇及其可能的大小写变体
        priority_words = [
            {
                'variants': ['kreuzen', 'Kreuzen'],
                'example': {
                    "de": "Die beiden Straßen kreuzen sich hier.",
                    "en": "The two streets cross here.", 
                    "zh": "两条街在这里相交。"
                }
            },
            {
                'variants': ['leben', 'Leben'],
                'example': {
                    "de": "Wir leben in einem schönen Haus.",
                    "en": "We live in a beautiful house.",
                    "zh": "我们住在一座漂亮的房子里。"
                }
            },
            {
                'variants': ['kaufen', 'Kaufen'],
                'example': {
                    "de": "Ich möchte ein neues Auto kaufen.",
                    "en": "I want to buy a new car.",
                    "zh": "我想买一辆新车。"
                }
            },
            {
                'variants': ['machen', 'Machen'],
                'example': {
                    "de": "Was machst du heute Abend?",
                    "en": "What are you doing this evening?",
                    "zh": "你今天晚上做什么？"
                }
            },
            {
                'variants': ['sagen', 'Sagen'],
                'example': {
                    "de": "Können Sie mir sagen, wie spät es ist?",
                    "en": "Can you tell me what time it is?",
                    "zh": "您能告诉我现在几点吗？"
                }
            },
            {
                'variants': ['geben', 'Geben'],
                'example': {
                    "de": "Können Sie mir bitte das Buch geben?",
                    "en": "Can you please give me the book?",
                    "zh": "您能请给我那本书吗？"
                }
            },
            {
                'variants': ['kommen', 'Kommen'],
                'example': {
                    "de": "Kommst du heute zu mir?",
                    "en": "Are you coming to my place today?",
                    "zh": "你今天来我这里吗？"
                }
            },
            {
                'variants': ['gehen', 'Gehen'],
                'example': {
                    "de": "Ich gehe jeden Tag zur Arbeit.",
                    "en": "I go to work every day.",
                    "zh": "我每天去上班。"
                }
            },
            {
                'variants': ['sprechen', 'Sprechen'],
                'example': {
                    "de": "Sprechen Sie Deutsch?",
                    "en": "Do you speak German?",
                    "zh": "您会说德语吗？"
                }
            },
            {
                'variants': ['lesen', 'Lesen'],
                'example': {
                    "de": "Jeden Abend lese ich ein Buch.",
                    "en": "Every evening I read a book.",
                    "zh": "每天晚上我都读书。"
                }
            }
        ]
        
        print(f"📝 将处理 {len(priority_words)} 个词汇组...")
        print()
        
        for i, word_data in enumerate(priority_words, 1):
            print(f"[{i}/{len(priority_words)}] 处理: {word_data['variants']}")
            self.add_example_for_word_variants(word_data['variants'], word_data['example'])
            print()
        
        self.print_final_stats()
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"🎉 例句添加完成!")
        print("=" * 30)
        print(f"添加例句: {self.stats['examples_added']}")
        print(f"错误数量: {self.stats['errors']}")
        print(f"总用时: {elapsed}")
        
        # 检查关键词汇的例句状态
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            key_words = ['bezahlen', 'Bezahlen', 'kreuzen', 'Kreuzen']
            print(f"\n📋 关键词汇状态检查:")
            
            for word in key_words:
                cursor.execute("""
                    SELECT e.de_text FROM examples e
                    JOIN word_lemmas wl ON wl.id = e.lemma_id  
                    WHERE wl.lemma = ?
                    LIMIT 1
                """, (word,))
                example = cursor.fetchone()
                
                if example:
                    print(f"   ✅ {word}: {example[0]}")
                    
        finally:
            conn.close()
            
        print(f"\n🚀 刷新浏览器，搜索词汇应该能看到例句了!")

def main():
    print("📚 智能例句添加器")
    print("=" * 50)
    
    adder = ExampleAdderWithCorrectCase()
    adder.add_priority_examples()

if __name__ == "__main__":
    main()