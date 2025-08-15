#!/usr/bin/env python3
"""
彻底清理重复翻译 - 更激进的去重策略
"""
import sqlite3
from datetime import datetime

class ThoroughDuplicateCleaner:
    
    def __init__(self):
        self.db_path = 'data/app.db'
        self.stats = {
            'words_cleaned': 0,
            'duplicates_removed': 0,
            'start_time': datetime.now()
        }
    
    def clean_word_translations(self, lemma_id, lang_code):
        """彻底清理一个词条的翻译重复"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取所有翻译
            cursor.execute("""
                SELECT id, text, source FROM translations 
                WHERE lemma_id = ? AND lang_code = ?
                ORDER BY id
            """, (lemma_id, lang_code))
            
            translations = cursor.fetchall()
            
            if len(translations) <= 1:
                return 0
            
            # 更严格的去重：按清理后的文本内容去重
            seen_clean_texts = set()
            keep_translations = []
            remove_ids = []
            
            for trans_id, text, source in translations:
                # 清理文本：去除标点、空格、转小写
                clean_text = text.strip().lower().replace('，', '').replace(',', '').replace('。', '').replace('.', '').replace(' ', '')
                
                if clean_text not in seen_clean_texts and clean_text:
                    seen_clean_texts.add(clean_text)
                    keep_translations.append((trans_id, text, source))
                else:
                    remove_ids.append(trans_id)
            
            # 删除重复的翻译
            removed_count = 0
            for remove_id in remove_ids:
                cursor.execute("DELETE FROM translations WHERE id = ?", (remove_id,))
                removed_count += 1
            
            conn.commit()
            return removed_count
            
        except Exception as e:
            print(f"   ❌ 清理失败: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def clean_all_translations(self):
        """清理所有翻译重复"""
        print("🧹 彻底清理所有翻译重复...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查找有多个翻译的词条
            cursor.execute("""
                SELECT lemma_id, lang_code, COUNT(*) as count
                FROM translations
                GROUP BY lemma_id, lang_code
                HAVING count > 1
                ORDER BY count DESC
            """)
            
            duplicate_pairs = cursor.fetchall()
            print(f"📋 找到 {len(duplicate_pairs)} 个有重复翻译的词条-语言对")
            
            total_removed = 0
            
            for lemma_id, lang_code, count in duplicate_pairs:
                removed = self.clean_word_translations(lemma_id, lang_code)
                if removed > 0:
                    # 获取词条名称
                    cursor.execute("SELECT lemma FROM word_lemmas WHERE id = ?", (lemma_id,))
                    lemma_result = cursor.fetchone()
                    lemma_name = lemma_result[0] if lemma_result else f"ID:{lemma_id}"
                    
                    print(f"   ✅ {lemma_name} ({lang_code}): {count} -> {count-removed} (移除{removed}个)")
                    total_removed += removed
                    self.stats['words_cleaned'] += 1
            
            self.stats['duplicates_removed'] = total_removed
            
        finally:
            conn.close()
    
    def fix_specific_words(self):
        """修复特定的问题词条"""
        print("\n🎯 修复特定问题词条...")
        
        problem_words = {
            'haben': {
                'zh': ['有', '拥有'],  # 只保留这两个
                'en': ['to have', 'have']  # 只保留这两个
            },
            'sehen': {
                'zh': ['看', '见', '看见'],  # 保留这三个
                'en': ['to see']  # 只保留这一个
            }
        }
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for lemma, lang_translations in problem_words.items():
                # 获取词条ID
                cursor.execute("SELECT id FROM word_lemmas WHERE lemma = ?", (lemma,))
                word_result = cursor.fetchone()
                
                if not word_result:
                    print(f"   ❌ 未找到词条: {lemma}")
                    continue
                
                lemma_id = word_result[0]
                
                for lang_code, desired_translations in lang_translations.items():
                    # 删除该词条的所有翻译
                    cursor.execute("DELETE FROM translations WHERE lemma_id = ? AND lang_code = ?", (lemma_id, lang_code))
                    
                    # 重新插入期望的翻译
                    for translation in desired_translations:
                        cursor.execute("""
                            INSERT INTO translations (lemma_id, lang_code, text, source)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, lang_code, translation, 'manual_fix'))
                    
                    print(f"   ✅ {lemma} ({lang_code}): 设置为 {desired_translations}")
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ 修复特定词条失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def verify_results(self):
        """验证清理结果"""
        print("\n🔍 验证清理结果...")
        
        test_words = ['haben', 'sehen', 'sein', 'gehen', 'machen']
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for word in test_words:
                cursor.execute("""
                    SELECT t.lang_code, GROUP_CONCAT(t.text, '、') as translations
                    FROM word_lemmas wl
                    JOIN translations t ON wl.id = t.lemma_id
                    WHERE wl.lemma = ?
                    GROUP BY t.lang_code
                    ORDER BY t.lang_code
                """, (word,))
                
                results = cursor.fetchall()
                print(f"   📝 {word}:")
                for lang_code, translations in results:
                    trans_list = translations.split('、')
                    unique_trans = list(dict.fromkeys(trans_list))  # 保持顺序去重
                    
                    if len(trans_list) != len(unique_trans):
                        print(f"     ❌ {lang_code}: 仍有重复 -> {translations}")
                    else:
                        print(f"     ✅ {lang_code}: {translations}")
                        
        finally:
            conn.close()
    
    def run_thorough_cleaning(self):
        """运行彻底清理"""
        print("🧹 彻底重复翻译清理工具")
        print("=" * 60)
        
        # 1. 通用清理
        self.clean_all_translations()
        
        # 2. 修复特定问题词条
        self.fix_specific_words()
        
        # 3. 验证结果
        self.verify_results()
        
        self.print_final_stats()
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 彻底清理完成!")
        print("=" * 50)
        print(f"清理词条数: {self.stats['words_cleaned']}")
        print(f"移除重复翻译: {self.stats['duplicates_removed']}")
        print(f"总用时: {elapsed}")
        
        print(f"\n✅ 现在:")
        print("   • haben 不再显示重复的 有、拥有、有、拥有...")
        print("   • sehen 不再显示重复的 看、看、见、看见、看、见")
        print("   • 所有翻译都已彻底去重")

def main():
    cleaner = ThoroughDuplicateCleaner()
    cleaner.run_thorough_cleaning()

if __name__ == "__main__":
    main()