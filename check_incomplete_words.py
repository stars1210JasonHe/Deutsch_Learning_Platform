#!/usr/bin/env python3
"""
检查数据库中不完整的词汇条目
识别缺少翻译、例句或其他重要信息的词汇
"""
import sqlite3
import json
from datetime import datetime

class IncompleteWordsChecker:
    """不完整词汇检查器"""
    
    def __init__(self):
        self.db_path = 'data/app.db'
        self.stats = {
            'total_words': 0,
            'missing_translations': 0,
            'missing_examples': 0,
            'missing_both': 0,
            'incomplete_translations': 0,
            'start_time': datetime.now()
        }
        
    def analyze_database_completeness(self):
        """分析数据库完整性"""
        print("🔍 数据库完整性分析")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 1. 总体统计
            cursor.execute("SELECT COUNT(*) FROM word_lemmas")
            total_words = cursor.fetchone()[0]
            self.stats['total_words'] = total_words
            
            print(f"📊 总体统计:")
            print(f"   总词汇数: {total_words}")
            
            # 2. 检查缺少翻译的词汇
            cursor.execute("""
                SELECT COUNT(DISTINCT wl.id) FROM word_lemmas wl
                LEFT JOIN translations t ON t.lemma_id = wl.id
                WHERE t.id IS NULL
            """)
            missing_translations = cursor.fetchone()[0]
            self.stats['missing_translations'] = missing_translations
            
            print(f"   缺少翻译: {missing_translations} ({missing_translations/total_words*100:.1f}%)")
            
            # 3. 检查缺少例句的词汇
            cursor.execute("""
                SELECT COUNT(DISTINCT wl.id) FROM word_lemmas wl
                LEFT JOIN examples e ON e.lemma_id = wl.id
                WHERE e.id IS NULL OR e.de_text IS NULL OR e.de_text = ''
            """)
            missing_examples = cursor.fetchone()[0]
            self.stats['missing_examples'] = missing_examples
            
            print(f"   缺少例句: {missing_examples} ({missing_examples/total_words*100:.1f}%)")
            
            # 4. 检查既缺少翻译又缺少例句的词汇
            cursor.execute("""
                SELECT COUNT(DISTINCT wl.id) FROM word_lemmas wl
                LEFT JOIN translations t ON t.lemma_id = wl.id
                LEFT JOIN examples e ON e.lemma_id = wl.id
                WHERE t.id IS NULL AND (e.id IS NULL OR e.de_text IS NULL OR e.de_text = '')
            """)
            missing_both = cursor.fetchone()[0]
            self.stats['missing_both'] = missing_both
            
            print(f"   两者都缺少: {missing_both} ({missing_both/total_words*100:.1f}%)")
            
            # 5. 检查不完整翻译（只有一种语言）
            cursor.execute("""
                SELECT COUNT(DISTINCT lemma_id) FROM (
                    SELECT lemma_id,
                           COUNT(CASE WHEN lang_code = 'en' THEN 1 END) as en_count,
                           COUNT(CASE WHEN lang_code = 'zh' THEN 1 END) as zh_count
                    FROM translations
                    GROUP BY lemma_id
                    HAVING en_count = 0 OR zh_count = 0
                )
            """)
            incomplete_translations = cursor.fetchone()[0]
            self.stats['incomplete_translations'] = incomplete_translations
            
            print(f"   不完整翻译: {incomplete_translations} ({incomplete_translations/total_words*100:.1f}%)")
            
        finally:
            conn.close()
    
    def get_sample_incomplete_words(self, category="missing_both", limit=20):
        """获取不完整词汇样本"""
        print(f"\n🔍 {category} 样本词汇 (前{limit}个):")
        print("-" * 40)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if category == "missing_both":
                # 既缺少翻译又缺少例句
                cursor.execute("""
                    SELECT wl.lemma, wl.pos, wl.cefr
                    FROM word_lemmas wl
                    LEFT JOIN translations t ON t.lemma_id = wl.id
                    LEFT JOIN examples e ON e.lemma_id = wl.id
                    WHERE t.id IS NULL AND (e.id IS NULL OR e.de_text IS NULL OR e.de_text = '')
                    ORDER BY wl.frequency DESC NULLS LAST, wl.lemma
                    LIMIT ?
                """, (limit,))
                
            elif category == "missing_translations":
                # 只缺少翻译
                cursor.execute("""
                    SELECT wl.lemma, wl.pos, wl.cefr
                    FROM word_lemmas wl
                    LEFT JOIN translations t ON t.lemma_id = wl.id
                    WHERE t.id IS NULL
                    ORDER BY wl.frequency DESC NULLS LAST, wl.lemma
                    LIMIT ?
                """, (limit,))
                
            elif category == "missing_examples":
                # 只缺少例句
                cursor.execute("""
                    SELECT wl.lemma, wl.pos, wl.cefr
                    FROM word_lemmas wl
                    LEFT JOIN examples e ON e.lemma_id = wl.id
                    WHERE e.id IS NULL OR e.de_text IS NULL OR e.de_text = ''
                    ORDER BY wl.frequency DESC NULLS LAST, wl.lemma
                    LIMIT ?
                """, (limit,))
                
            elif category == "incomplete_translations":
                # 不完整翻译（缺少英文或中文）
                cursor.execute("""
                    SELECT wl.lemma, wl.pos, wl.cefr,
                           COUNT(CASE WHEN t.lang_code = 'en' THEN 1 END) as en_count,
                           COUNT(CASE WHEN t.lang_code = 'zh' THEN 1 END) as zh_count
                    FROM word_lemmas wl
                    LEFT JOIN translations t ON t.lemma_id = wl.id
                    GROUP BY wl.id
                    HAVING en_count = 0 OR zh_count = 0
                    ORDER BY wl.frequency DESC NULLS LAST, wl.lemma
                    LIMIT ?
                """, (limit,))
            
            results = cursor.fetchall()
            
            if results:
                for i, row in enumerate(results, 1):
                    if category == "incomplete_translations":
                        lemma, pos, cefr, en_count, zh_count = row
                        missing = []
                        if en_count == 0:
                            missing.append("EN")
                        if zh_count == 0:
                            missing.append("ZH")
                        print(f"   {i:2}. {lemma} ({pos}) - 缺少: {'/'.join(missing)}")
                    else:
                        lemma, pos, cefr = row
                        cefr_str = f" [{cefr}]" if cefr else ""
                        print(f"   {i:2}. {lemma} ({pos}){cefr_str}")
            else:
                print("   (无样本数据)")
                
        finally:
            conn.close()
    
    def identify_priority_words_to_fix(self):
        """识别优先修复的词汇"""
        print(f"\n🎯 优先修复词汇识别:")
        print("=" * 40)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 高频词汇且缺少完整信息
            cursor.execute("""
                SELECT wl.lemma, wl.pos, wl.cefr, wl.frequency,
                       COUNT(t.id) as translation_count,
                       COUNT(CASE WHEN e.de_text IS NOT NULL AND e.de_text != '' THEN 1 END) as example_count
                FROM word_lemmas wl
                LEFT JOIN translations t ON t.lemma_id = wl.id
                LEFT JOIN examples e ON e.lemma_id = wl.id
                WHERE wl.frequency IS NOT NULL
                GROUP BY wl.id
                HAVING translation_count = 0 OR example_count = 0
                ORDER BY wl.frequency DESC
                LIMIT 30
            """)
            
            priority_words = cursor.fetchall()
            
            if priority_words:
                print("高频不完整词汇 (按频率排序):")
                for i, (lemma, pos, cefr, freq, trans_count, ex_count) in enumerate(priority_words, 1):
                    missing = []
                    if trans_count == 0:
                        missing.append("翻译")
                    if ex_count == 0:
                        missing.append("例句")
                    
                    cefr_str = f" [{cefr}]" if cefr else ""
                    freq_str = f" (频率:{freq})" if freq else ""
                    print(f"   {i:2}. {lemma} ({pos}){cefr_str}{freq_str} - 缺少: {'/'.join(missing)}")
            else:
                print("   未发现高频不完整词汇")
            
            # A1/A2级别的不完整词汇（初学者重要）
            cursor.execute("""
                SELECT wl.lemma, wl.pos, wl.cefr,
                       COUNT(t.id) as translation_count,
                       COUNT(CASE WHEN e.de_text IS NOT NULL AND e.de_text != '' THEN 1 END) as example_count
                FROM word_lemmas wl
                LEFT JOIN translations t ON t.lemma_id = wl.id
                LEFT JOIN examples e ON e.lemma_id = wl.id
                WHERE wl.cefr IN ('A1', 'A2')
                GROUP BY wl.id
                HAVING translation_count = 0 OR example_count = 0
                ORDER BY wl.cefr, wl.lemma
                LIMIT 20
            """)
            
            beginner_words = cursor.fetchall()
            
            print(f"\n初学者级别不完整词汇 (A1/A2):")
            if beginner_words:
                for i, (lemma, pos, cefr, trans_count, ex_count) in enumerate(beginner_words, 1):
                    missing = []
                    if trans_count == 0:
                        missing.append("翻译")
                    if ex_count == 0:
                        missing.append("例句")
                    
                    print(f"   {i:2}. {lemma} ({pos}) [{cefr}] - 缺少: {'/'.join(missing)}")
            else:
                print("   所有A1/A2词汇都完整")
                
        finally:
            conn.close()
    
    def generate_completion_report(self):
        """生成完整性报告"""
        print(f"\n📊 数据库完整性报告")
        print("=" * 50)
        
        total = self.stats['total_words']
        complete_words = total - self.stats['missing_both']
        completion_rate = (complete_words / total * 100) if total > 0 else 0
        
        print(f"总体完整性: {completion_rate:.1f}%")
        print(f"完整词汇: {complete_words}/{total}")
        print()
        
        print(f"问题分布:")
        print(f"• 缺少翻译: {self.stats['missing_translations']} ({self.stats['missing_translations']/total*100:.1f}%)")
        print(f"• 缺少例句: {self.stats['missing_examples']} ({self.stats['missing_examples']/total*100:.1f}%)")
        print(f"• 两者都缺少: {self.stats['missing_both']} ({self.stats['missing_both']/total*100:.1f}%)")
        print(f"• 不完整翻译: {self.stats['incomplete_translations']} ({self.stats['incomplete_translations']/total*100:.1f}%)")
        
        print(f"\n修复建议:")
        if self.stats['missing_both'] > 1000:
            print("⚠️  大量词汇缺少基本信息，建议创建批量修复脚本")
        elif self.stats['missing_both'] > 100:
            print("💡 中等数量不完整词汇，可以分批处理")
        else:
            print("✅ 数据库相对完整，只需少量修复")
            
        # 修复优先级建议
        print(f"\n修复优先级建议:")
        print("1. 优先修复高频词汇（frequency值高的）")
        print("2. 优先修复A1/A2级别词汇（初学者重要）")
        print("3. 优先添加翻译（比例句更重要）")
        print("4. 批量处理同类问题")

def main():
    """主函数"""
    print("🔍 数据库不完整词汇检查器")
    print("=" * 60)
    print(f"⏰ 检查时间: {datetime.now()}")
    print()
    
    checker = IncompleteWordsChecker()
    
    # 分析数据库完整性
    checker.analyze_database_completeness()
    
    # 获取样本数据
    checker.get_sample_incomplete_words("missing_both", 15)
    checker.get_sample_incomplete_words("missing_translations", 10)
    checker.get_sample_incomplete_words("incomplete_translations", 10)
    
    # 识别优先修复词汇
    checker.identify_priority_words_to_fix()
    
    # 生成报告
    checker.generate_completion_report()
    
    print(f"\n🎯 下一步:")
    print("1. 如果需要修复，将创建批量修复脚本")
    print("2. 脚本将使用OpenAI API补充缺失的翻译和例句")
    print("3. 可以按优先级分批处理，避免API过载")

if __name__ == "__main__":
    main()