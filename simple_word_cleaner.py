#!/usr/bin/env python3
"""
简化词条清理工具
检测明显的英语词条和问题词条
"""
import sqlite3
import re
from datetime import datetime

class SimpleWordCleaner:
    
    def __init__(self):
        self.db_path = 'data/app.db'
        self.stats = {
            'words_analyzed': 0,
            'english_words_found': 0,
            'plural_words_found': 0,
            'suspicious_words_found': 0,
            'start_time': datetime.now()
        }
    
    def find_obvious_english_words(self):
        """查找明显的英语词条"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        english_patterns = [
            'ing',    # English -ing verbs
            'tion',   # English -tion nouns  
            'ly',     # English -ly adverbs
            'ed',     # English -ed past tense
            'ness',   # English -ness nouns
            'ment',   # English -ment nouns
        ]
        
        obvious_english = [
            'the', 'and', 'or', 'but', 'with', 'for', 'to', 'of', 'in', 'on', 'at',
            'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were',
            'have', 'has', 'had', 'will', 'would', 'could', 'should',
            'about', 'from', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'between', 'among', 'within', 'without'
        ]
        
        try:
            # 查找以英语后缀结尾的词
            english_words = []
            for pattern in english_patterns:
                cursor.execute("""
                    SELECT id, lemma, pos, cefr, frequency 
                    FROM word_lemmas 
                    WHERE lemma LIKE ? AND LENGTH(lemma) > 3
                    ORDER BY lemma
                """, (f'%{pattern}',))
                
                results = cursor.fetchall()
                english_words.extend(results)
            
            # 查找明显的英语词汇
            placeholders = ','.join(['?' for _ in obvious_english])
            cursor.execute(f"""
                SELECT id, lemma, pos, cefr, frequency 
                FROM word_lemmas 
                WHERE lemma IN ({placeholders})
                ORDER BY lemma
            """, obvious_english)
            
            obvious_results = cursor.fetchall()
            english_words.extend(obvious_results)
            
            # 去重
            seen = set()
            unique_english = []
            for word in english_words:
                if word[0] not in seen:  # word[0] is id
                    seen.add(word[0])
                    unique_english.append(word)
            
            print(f"📋 发现 {len(unique_english)} 个可能的英语词条:")
            for word_id, lemma, pos, cefr, freq in unique_english[:20]:  # 显示前20个
                print(f"   • {lemma} ({pos}) - ID: {word_id}")
            
            if len(unique_english) > 20:
                print(f"   ... 还有 {len(unique_english) - 20} 个")
            
            self.stats['english_words_found'] = len(unique_english)
            return unique_english
            
        finally:
            conn.close()
    
    def find_probable_plurals(self):
        """查找可能的复数词条（作为主词条）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 德语复数常见模式
            cursor.execute("""
                SELECT id, lemma, pos, cefr, frequency, notes
                FROM word_lemmas 
                WHERE pos = 'noun'
                AND (
                    -- 以-en结尾的复数（很多德语名词复数）
                    (lemma LIKE '%en' AND LENGTH(lemma) > 4)
                    -- 以-er结尾的复数
                    OR (lemma LIKE '%er' AND LENGTH(lemma) > 4)
                    -- 以-e结尾的复数
                    OR (lemma LIKE '%e' AND LENGTH(lemma) > 3)
                    -- 以-s结尾的复数（外来词）
                    OR lemma LIKE '%s'
                )
                AND (notes IS NULL OR notes NOT LIKE '%plural:%')  -- 不是已知的复数信息
                ORDER BY lemma
                LIMIT 50
            """)
            
            probable_plurals = cursor.fetchall()
            
            print(f"📋 发现 {len(probable_plurals)} 个可能的复数主词条:")
            for word_id, lemma, pos, cefr, freq, notes in probable_plurals:
                print(f"   • {lemma} - ID: {word_id}")
            
            self.stats['plural_words_found'] = len(probable_plurals)
            return probable_plurals
            
        finally:
            conn.close()
    
    def find_suspicious_words(self):
        """查找可疑词条"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查找可疑的词条
            cursor.execute("""
                SELECT id, lemma, pos, cefr, frequency, notes
                FROM word_lemmas 
                WHERE 
                    -- 非常短的词
                    (LENGTH(lemma) < 2)
                    -- 没有等级和频率的词
                    OR (cefr IS NULL AND frequency IS NULL)
                    -- 包含数字的词
                    OR lemma LIKE '%0%' OR lemma LIKE '%1%' OR lemma LIKE '%2%' 
                    OR lemma LIKE '%3%' OR lemma LIKE '%4%' OR lemma LIKE '%5%'
                    OR lemma LIKE '%6%' OR lemma LIKE '%7%' OR lemma LIKE '%8%' OR lemma LIKE '%9%'
                    -- 包含特殊字符的词
                    OR lemma LIKE '%@%' OR lemma LIKE '%#%' OR lemma LIKE '%$%'
                    OR lemma LIKE '%(%' OR lemma LIKE '%)%' OR lemma LIKE '%[%' OR lemma LIKE '%]%'
                ORDER BY LENGTH(lemma), lemma
                LIMIT 30
            """)
            
            suspicious_words = cursor.fetchall()
            
            print(f"📋 发现 {len(suspicious_words)} 个可疑词条:")
            for word_id, lemma, pos, cefr, freq, notes in suspicious_words:
                print(f"   • '{lemma}' ({pos}) - ID: {word_id}")
            
            self.stats['suspicious_words_found'] = len(suspicious_words)
            return suspicious_words
            
        finally:
            conn.close()
    
    def check_word_relationships(self):
        """检查词条关系"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查找可能的单复数对
            print(f"\n🔍 检查单复数关系:")
            
            cursor.execute("""
                SELECT w1.lemma as singular, w2.lemma as plural, w1.id as sing_id, w2.id as plur_id
                FROM word_lemmas w1
                JOIN word_lemmas w2 ON (
                    w2.lemma = w1.lemma || 'e'
                    OR w2.lemma = w1.lemma || 'en' 
                    OR w2.lemma = w1.lemma || 'er'
                    OR w2.lemma = w1.lemma || 's'
                )
                WHERE w1.pos = 'noun' AND w2.pos = 'noun'
                AND w1.id != w2.id
                ORDER BY w1.lemma
                LIMIT 20
            """)
            
            pairs = cursor.fetchall()
            for singular, plural, sing_id, plur_id in pairs:
                print(f"   • {singular} -> {plural} (IDs: {sing_id}, {plur_id})")
            
            return pairs
            
        finally:
            conn.close()
    
    def show_sample_words(self, category, count=10):
        """显示样本词条"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT lemma, pos, cefr, frequency, notes
                FROM word_lemmas 
                ORDER BY RANDOM()
                LIMIT ?
            """, (count,))
            
            words = cursor.fetchall()
            print(f"\n📝 随机样本词条 ({category}):")
            for lemma, pos, cefr, freq, notes in words:
                cefr_str = f"[{cefr}]" if cefr else "[?]"
                freq_str = f"(频率:{freq})" if freq else ""
                notes_str = f" - {notes[:30]}..." if notes else ""
                print(f"   • {lemma} {cefr_str} ({pos}) {freq_str}{notes_str}")
            
        finally:
            conn.close()
    
    def run_analysis(self):
        """运行分析"""
        print("🧹 简化词条分析工具")
        print("=" * 60)
        
        # 1. 查找英语词条
        print("1. 查找英语词条:")
        english_words = self.find_obvious_english_words()
        
        print(f"\n2. 查找可能的复数主词条:")
        plural_words = self.find_probable_plurals()
        
        print(f"\n3. 查找可疑词条:")
        suspicious_words = self.find_suspicious_words()
        
        print(f"\n4. 检查词条关系:")
        pairs = self.check_word_relationships()
        
        # 显示样本
        self.show_sample_words("当前数据库状态", 15)
        
        self.print_final_stats()
        
        return {
            'english_words': english_words,
            'plural_words': plural_words, 
            'suspicious_words': suspicious_words,
            'pairs': pairs
        }
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n📊 分析完成!")
        print("=" * 50)
        print(f"可能的英语词条: {self.stats['english_words_found']}")
        print(f"可能的复数主词条: {self.stats['plural_words_found']}")
        print(f"可疑词条: {self.stats['suspicious_words_found']}")
        print(f"分析用时: {elapsed}")
        
        print(f"\n💡 建议:")
        print("1. 检查上述英语词条，考虑删除")
        print("2. 检查复数主词条，考虑重定向到单数")
        print("3. 检查可疑词条，考虑删除或修正")
        print("4. 验证单复数关系是否正确")

def main():
    cleaner = SimpleWordCleaner()
    return cleaner.run_analysis()

if __name__ == "__main__":
    main()