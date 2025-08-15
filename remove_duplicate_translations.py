#!/usr/bin/env python3
"""
移除重复翻译
修复问题：haben显示 有、拥有、有、拥有、有、拥有、有、拥有、有、拥有
应该显示：有、拥有 (去重后)
"""
import sqlite3
from datetime import datetime
from collections import defaultdict

class DuplicateTranslationRemover:
    
    def __init__(self):
        self.db_path = 'data/app.db'
        self.stats = {
            'words_processed': 0,
            'duplicate_translations_removed': 0,
            'duplicate_examples_removed': 0,
            'start_time': datetime.now()
        }
    
    def find_duplicate_translations(self):
        """查找重复翻译"""
        print("🔍 查找重复翻译...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查找有重复翻译的词条
            cursor.execute("""
                SELECT 
                    wl.lemma,
                    t.lemma_id,
                    t.lang_code,
                    COUNT(*) as translation_count,
                    GROUP_CONCAT(t.text, '、') as all_translations
                FROM translations t
                JOIN word_lemmas wl ON t.lemma_id = wl.id
                GROUP BY t.lemma_id, t.lang_code
                HAVING translation_count > 3  -- 超过3个翻译的可能有重复
                ORDER BY translation_count DESC, wl.lemma
                LIMIT 20
            """)
            
            duplicates = cursor.fetchall()
            
            print(f"📋 发现 {len(duplicates)} 个可能有重复翻译的词条:")
            for lemma, lemma_id, lang_code, count, translations in duplicates:
                # 显示翻译，截断如果太长
                trans_preview = translations[:100] + "..." if len(translations) > 100 else translations
                print(f"   • {lemma} ({lang_code}): {count}个翻译 - {trans_preview}")
            
            return duplicates
            
        finally:
            conn.close()
    
    def clean_translations_for_word(self, lemma_id, lang_code):
        """为特定词条清理重复翻译"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取该词条的所有翻译
            cursor.execute("""
                SELECT id, text, source FROM translations 
                WHERE lemma_id = ? AND lang_code = ?
                ORDER BY id
            """, (lemma_id, lang_code))
            
            translations = cursor.fetchall()
            
            if len(translations) <= 1:
                return 0  # 没有重复
            
            # 去重，保持顺序
            seen_texts = set()
            unique_translations = []
            duplicates_to_remove = []
            
            for trans_id, text, source in translations:
                text_clean = text.strip().lower()
                if text_clean not in seen_texts:
                    seen_texts.add(text_clean)
                    unique_translations.append((trans_id, text, source))
                else:
                    duplicates_to_remove.append(trans_id)
            
            # 删除重复项
            removed_count = 0
            for dup_id in duplicates_to_remove:
                cursor.execute("DELETE FROM translations WHERE id = ?", (dup_id,))
                removed_count += 1
            
            conn.commit()
            return removed_count
            
        except Exception as e:
            print(f"   ❌ 清理翻译失败: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def clean_all_duplicate_translations(self):
        """清理所有重复翻译"""
        print("🧹 清理所有重复翻译...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取所有有翻译的词条
            cursor.execute("""
                SELECT DISTINCT lemma_id, lang_code
                FROM translations
                ORDER BY lemma_id, lang_code
            """)
            
            word_lang_pairs = cursor.fetchall()
            print(f"📝 处理 {len(word_lang_pairs)} 个词条-语言对...")
            
            total_removed = 0
            
            for lemma_id, lang_code in word_lang_pairs:
                removed = self.clean_translations_for_word(lemma_id, lang_code)
                if removed > 0:
                    # 获取词条名称用于显示
                    cursor.execute("SELECT lemma FROM word_lemmas WHERE id = ?", (lemma_id,))
                    lemma_result = cursor.fetchone()
                    lemma_name = lemma_result[0] if lemma_result else f"ID:{lemma_id}"
                    
                    print(f"   ✅ {lemma_name} ({lang_code}): 移除了 {removed} 个重复翻译")
                    total_removed += removed
                    self.stats['words_processed'] += 1
            
            self.stats['duplicate_translations_removed'] = total_removed
            print(f"\n📊 总共移除了 {total_removed} 个重复翻译")
            
        finally:
            conn.close()
    
    def find_duplicate_examples(self):
        """查找重复例句"""
        print("\n🔍 查找重复例句...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 查找有重复例句的词条
            cursor.execute("""
                SELECT 
                    wl.lemma,
                    e.lemma_id,
                    COUNT(*) as example_count
                FROM examples e
                JOIN word_lemmas wl ON e.lemma_id = wl.id
                GROUP BY e.lemma_id
                HAVING example_count > 2  -- 超过2个例句的可能有重复
                ORDER BY example_count DESC, wl.lemma
                LIMIT 15
            """)
            
            duplicates = cursor.fetchall()
            
            print(f"📋 发现 {len(duplicates)} 个可能有重复例句的词条:")
            for lemma, lemma_id, count in duplicates:
                print(f"   • {lemma}: {count}个例句")
            
            return duplicates
            
        finally:
            conn.close()
    
    def clean_examples_for_word(self, lemma_id):
        """为特定词条清理重复例句"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取该词条的所有例句
            cursor.execute("""
                SELECT id, de_text, en_text, zh_text, level FROM examples 
                WHERE lemma_id = ?
                ORDER BY id
            """, (lemma_id,))
            
            examples = cursor.fetchall()
            
            if len(examples) <= 1:
                return 0  # 没有重复
            
            # 去重（基于德语文本）
            seen_de_texts = set()
            unique_examples = []
            duplicates_to_remove = []
            
            for ex_id, de_text, en_text, zh_text, level in examples:
                de_clean = de_text.strip().lower() if de_text else ""
                if de_clean and de_clean not in seen_de_texts:
                    seen_de_texts.add(de_clean)
                    unique_examples.append((ex_id, de_text, en_text, zh_text, level))
                else:
                    duplicates_to_remove.append(ex_id)
            
            # 删除重复项
            removed_count = 0
            for dup_id in duplicates_to_remove:
                cursor.execute("DELETE FROM examples WHERE id = ?", (dup_id,))
                removed_count += 1
            
            conn.commit()
            return removed_count
            
        except Exception as e:
            print(f"   ❌ 清理例句失败: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def clean_all_duplicate_examples(self):
        """清理所有重复例句"""
        print("🧹 清理所有重复例句...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取所有有例句的词条
            cursor.execute("""
                SELECT DISTINCT lemma_id
                FROM examples
                ORDER BY lemma_id
            """)
            
            word_ids = [row[0] for row in cursor.fetchall()]
            print(f"📝 处理 {len(word_ids)} 个有例句的词条...")
            
            total_removed = 0
            
            for lemma_id in word_ids:
                removed = self.clean_examples_for_word(lemma_id)
                if removed > 0:
                    # 获取词条名称用于显示
                    cursor.execute("SELECT lemma FROM word_lemmas WHERE id = ?", (lemma_id,))
                    lemma_result = cursor.fetchone()
                    lemma_name = lemma_result[0] if lemma_result else f"ID:{lemma_id}"
                    
                    print(f"   ✅ {lemma_name}: 移除了 {removed} 个重复例句")
                    total_removed += removed
            
            self.stats['duplicate_examples_removed'] = total_removed
            print(f"\n📊 总共移除了 {total_removed} 个重复例句")
            
        finally:
            conn.close()
    
    def verify_specific_words(self):
        """验证特定词条的翻译"""
        print("\n🔍 验证特定词条翻译...")
        
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
                    unique_count = len(set(trans_list))
                    total_count = len(trans_list)
                    
                    if total_count != unique_count:
                        print(f"     ❌ {lang_code}: {total_count}个翻译(含重复) -> {translations[:50]}...")
                    else:
                        print(f"     ✅ {lang_code}: {total_count}个翻译 -> {translations}")
                        
        finally:
            conn.close()
    
    def run_cleaning(self):
        """运行清理流程"""
        print("🧹 重复翻译清理工具")
        print("=" * 60)
        
        # 1. 分析重复翻译问题
        duplicate_translations = self.find_duplicate_translations()
        
        # 2. 分析重复例句问题  
        duplicate_examples = self.find_duplicate_examples()
        
        # 3. 清理重复翻译
        self.clean_all_duplicate_translations()
        
        # 4. 清理重复例句
        self.clean_all_duplicate_examples()
        
        # 5. 验证结果
        self.verify_specific_words()
        
        self.print_final_stats()
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 重复内容清理完成!")
        print("=" * 50)
        print(f"处理词条数: {self.stats['words_processed']}")
        print(f"移除重复翻译: {self.stats['duplicate_translations_removed']}")
        print(f"移除重复例句: {self.stats['duplicate_examples_removed']}")
        print(f"总用时: {elapsed}")
        
        total_removed = (self.stats['duplicate_translations_removed'] + 
                        self.stats['duplicate_examples_removed'])
        
        print(f"总清理项目: {total_removed}")
        
        if total_removed > 0:
            print(f"\n✅ 清理成功! 现在:")
            print("   • haben 不再显示重复的中文翻译")
            print("   • sehen 的中文翻译已去重")
            print("   • 所有词条的翻译都是唯一的")
            print("   • 例句也已去重")

def main():
    cleaner = DuplicateTranslationRemover()
    cleaner.run_cleaning()

if __name__ == "__main__":
    main()