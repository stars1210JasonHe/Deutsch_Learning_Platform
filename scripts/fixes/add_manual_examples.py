#!/usr/bin/env python3
"""
手动添加重要词汇的例句
为bezahlen, kreuzen等关键词汇添加高质量的例句
"""
import sqlite3
from datetime import datetime

class ManualExampleAdder:
    def __init__(self):
        self.db_path = 'data/app.db'
        self.stats = {
            'examples_added': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
        
        # 手动精选的高质量例句
        self.examples = {
            "bezahlen": {
                "de": "Ich muss die Rechnung bezahlen.",
                "en": "I have to pay the bill.",
                "zh": "我必须付账单。"
            },
            "kreuzen": {
                "de": "Die beiden Straßen kreuzen sich hier.",
                "en": "The two streets cross here.",
                "zh": "两条街在这里相交。"
            },
            "arbeiten": {
                "de": "Ich arbeite jeden Tag im Büro.",
                "en": "I work in the office every day.",
                "zh": "我每天在办公室工作。"
            },
            "leben": {
                "de": "Wir leben in einem schönen Haus.",
                "en": "We live in a beautiful house.",
                "zh": "我们住在一座漂亮的房子里。"
            },
            "kaufen": {
                "de": "Ich möchte ein neues Auto kaufen.",
                "en": "I want to buy a new car.",
                "zh": "我想买一辆新车。"
            },
            "verkaufen": {
                "de": "Er will sein altes Fahrrad verkaufen.",
                "en": "He wants to sell his old bicycle.",
                "zh": "他想卖掉他的旧自行车。"
            },
            "schlafen": {
                "de": "Das Baby schläft sehr ruhig.",
                "en": "The baby sleeps very peacefully.",
                "zh": "婴儿睡得很安静。"
            },
            "fahren": {
                "de": "Wir fahren morgen nach Berlin.",
                "en": "We are driving to Berlin tomorrow.",
                "zh": "我们明天开车去柏林。"
            },
            "laufen": {
                "de": "Die Kinder laufen im Park.",
                "en": "The children are running in the park.",
                "zh": "孩子们在公园里跑步。"
            },
            "machen": {
                "de": "Was machst du heute Abend?",
                "en": "What are you doing this evening?",
                "zh": "你今天晚上做什么？"
            },
            "sagen": {
                "de": "Können Sie mir sagen, wie spät es ist?",
                "en": "Can you tell me what time it is?",
                "zh": "您能告诉我现在几点吗？"
            },
            "wissen": {
                "de": "Ich weiß nicht, wo mein Schlüssel ist.",
                "en": "I don't know where my key is.",
                "zh": "我不知道我的钥匙在哪里。"
            },
            "kommen": {
                "de": "Kommst du heute zu mir?",
                "en": "Are you coming to my place today?",
                "zh": "你今天来我这里吗？"
            },
            "geben": {
                "de": "Können Sie mir bitte das Buch geben?",
                "en": "Can you please give me the book?",
                "zh": "您能请给我那本书吗？"
            },
            "nehmen": {
                "de": "Ich nehme den Bus zur Arbeit.",
                "en": "I take the bus to work.",
                "zh": "我坐公交车上班。"
            },
            "denken": {
                "de": "Ich denke oft an meine Familie.",
                "en": "I often think about my family.",
                "zh": "我经常想念我的家人。"
            },
            "finden": {
                "de": "Ich kann meinen Schlüssel nicht finden.",
                "en": "I can't find my key.",
                "zh": "我找不到我的钥匙。"
            },
            "spielen": {
                "de": "Die Kinder spielen im Garten.",
                "en": "The children are playing in the garden.",
                "zh": "孩子们在花园里玩。"
            },
            "lernen": {
                "de": "Ich lerne Deutsch seit zwei Jahren.",
                "en": "I have been learning German for two years.",
                "zh": "我学德语已经两年了。"
            },
            "verstehen": {
                "de": "Verstehen Sie, was ich meine?",
                "en": "Do you understand what I mean?",
                "zh": "您明白我的意思吗？"
            },
            "sprechen": {
                "de": "Sprechen Sie Deutsch?",
                "en": "Do you speak German?",
                "zh": "您会说德语吗？"
            },
            "hören": {
                "de": "Ich höre gerne klassische Musik.",
                "en": "I like listening to classical music.",
                "zh": "我喜欢听古典音乐。"
            },
            "lesen": {
                "de": "Jeden Abend lese ich ein Buch.",
                "en": "Every evening I read a book.",
                "zh": "每天晚上我都读书。"
            },
            "schreiben": {
                "de": "Ich schreibe einen Brief an meinen Freund.",
                "en": "I am writing a letter to my friend.",
                "zh": "我在给我朋友写信。"
            },
            "essen": {
                "de": "Wir essen um zwölf Uhr zu Mittag.",
                "en": "We eat lunch at twelve o'clock.",
                "zh": "我们十二点吃午饭。"
            },
            "trinken": {
                "de": "Möchten Sie etwas trinken?",
                "en": "Would you like something to drink?",
                "zh": "您想喝点什么吗？"
            }
        }
    
    def add_example_for_word(self, lemma, example_data):
        """为指定词汇添加例句"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 首先获取词汇ID
            cursor.execute("SELECT id FROM word_lemmas WHERE lemma = ?", (lemma,))
            result = cursor.fetchone()
            
            if not result:
                print(f"   ❌ 词汇 {lemma} 不存在于数据库中")
                return False
            
            lemma_id = result[0]
            
            # 检查是否已有例句
            cursor.execute("SELECT COUNT(*) FROM examples WHERE lemma_id = ?", (lemma_id,))
            existing_count = cursor.fetchone()[0]
            
            if existing_count > 0:
                print(f"   ℹ️  {lemma} 已有 {existing_count} 个例句，跳过")
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
            
            print(f"   ✅ {lemma} 例句添加成功")
            print(f"      DE: {example_data['de']}")
            print(f"      EN: {example_data['en']}")
            print(f"      ZH: {example_data['zh']}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 添加 {lemma} 例句时出错: {e}")
            self.stats['errors'] += 1
            conn.rollback()
            return False
            
        finally:
            conn.close()
    
    def add_all_examples(self):
        """添加所有预定义的例句"""
        print("🚀 开始添加手动精选的例句")
        print("=" * 50)
        
        print(f"📝 将处理 {len(self.examples)} 个词汇:")
        for lemma in self.examples.keys():
            print(f"   • {lemma}")
        print()
        
        for i, (lemma, example_data) in enumerate(self.examples.items(), 1):
            print(f"[{i}/{len(self.examples)}] 处理: {lemma}")
            self.add_example_for_word(lemma, example_data)
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
        
        # 特别检查bezahlen
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT e.de_text FROM examples e
                JOIN word_lemmas wl ON wl.id = e.lemma_id  
                WHERE wl.lemma = 'bezahlen'
                LIMIT 1
            """)
            bezahlen_example = cursor.fetchone()
            
            if bezahlen_example:
                print(f"\n✅ bezahlen现在有例句: {bezahlen_example[0]}")
                print("🚀 刷新浏览器，搜索'bezahlen'应该能看到例句了!")
            else:
                print(f"\n⚠️  bezahlen仍然没有例句，请检查数据库")
                
        finally:
            conn.close()
    
    def check_current_examples_status(self):
        """检查当前例句状态"""
        print("🔍 检查当前例句状态")
        print("=" * 30)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for lemma in ['bezahlen', 'kreuzen', 'arbeiten', 'leben']:
                cursor.execute("""
                    SELECT COUNT(*) FROM examples e
                    JOIN word_lemmas wl ON wl.id = e.lemma_id
                    WHERE wl.lemma = ?
                """, (lemma,))
                
                count = cursor.fetchone()[0]
                status = "✅" if count > 0 else "❌"
                print(f"   {status} {lemma}: {count} 个例句")
                
        finally:
            conn.close()

def main():
    print("📚 手动例句添加器")
    print("=" * 50)
    
    adder = ManualExampleAdder()
    
    # 检查当前状态
    adder.check_current_examples_status()
    print()
    
    # 添加例句
    adder.add_all_examples()

if __name__ == "__main__":
    main()