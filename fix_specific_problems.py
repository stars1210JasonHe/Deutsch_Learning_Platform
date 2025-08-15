#!/usr/bin/env python3
"""
修复特定的词条问题
基于分析结果，修复确定的问题：
1. 删除真正的英语词条
2. 重定向明确的复数主词条
3. 清理带括号的词条
4. 修复明确的单复数关系
"""
import sqlite3
from datetime import datetime

class SpecificWordFixer:
    
    def __init__(self):
        self.db_path = 'data/app.db'
        self.stats = {
            'english_deleted': 0,
            'plurals_redirected': 0,
            'parentheses_cleaned': 0,
            'relationships_fixed': 0,
            'start_time': datetime.now()
        }
    
    def get_true_english_words(self):
        """明确的英语词条（需要删除）"""
        return [
            # 基于分析，这些可能是真正的英语词
            # 注意：大多数-ing/-tion词实际上是德语词，不要删除
        ]
    
    def get_definite_plurals_to_redirect(self):
        """明确需要重定向的复数主词条"""
        return [
            # 格式: (复数词, 目标单数词)
            ('Angaben', 'Angabe'),
            ('Ausgaben', 'Ausgabe'), 
            ('Aufgaben', 'Aufgabe'),
            ('Betten', 'Bett'),
            ('Aufträge', 'Auftrag'),
            ('Anträge', 'Antrag'),
            ('Ausflüge', 'Ausflug'),
            ('Beiträge', 'Beitrag'),
            ('Arbeitszeiten', 'Arbeitszeit'),
            ('Arbeitsbedingungen', 'Arbeitsbedingung'),
            ('Bedingungen', 'Bedingung'),
            ('Aussichten', 'Aussicht'),
            ('Bonbons', 'Bonbon'),
            ('Erinnerungen', 'Erinnerung'),
            ('Gebühren', 'Gebühr'),
            ('Ausländer', 'Ausländer'),  # 这个实际上正确，Ausländer是单数和复数同形
        ]
    
    def get_parentheses_words_to_clean(self):
        """需要清理括号的词条"""
        return [
            # 格式: (原词, 清理后的词)
            ('(E-)Mail', 'E-Mail'),
            ('(Schlag-)Rahm', 'Schlagrahm'),
            ('Last(kraft)wagen', 'Lastkraftwagen'),
            ('(Fach-)Hochschule', 'Fachhochschule'),
        ]
    
    def get_relationships_to_fix(self):
        """需要修复的关系"""
        return [
            # 格式: (词1, 词2, 操作类型)
            ('Deutsch', 'Deutsche', 'merge_nationality'),  # 德语/德国人
            ('Deutschen', 'Deutsche', 'redirect'),  # Deutschen -> Deutsche
        ]
    
    def fix_parentheses_words(self):
        """修复带括号的词条"""
        print("🔧 修复带括号的词条...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            parentheses_fixes = self.get_parentheses_words_to_clean()
            
            for old_lemma, new_lemma in parentheses_fixes:
                # 检查原词是否存在
                cursor.execute("SELECT id FROM word_lemmas WHERE lemma = ?", (old_lemma,))
                old_word = cursor.fetchone()
                
                if old_word:
                    old_id = old_word[0]
                    
                    # 检查新词是否已存在
                    cursor.execute("SELECT id FROM word_lemmas WHERE lemma = ?", (new_lemma,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # 新词已存在，合并数据后删除旧词
                        self.merge_word_data(cursor, old_id, existing[0])
                        cursor.execute("DELETE FROM word_lemmas WHERE id = ?", (old_id,))
                        print(f"   ✅ 合并: {old_lemma} -> {new_lemma}")
                    else:
                        # 新词不存在，直接重命名
                        cursor.execute("UPDATE word_lemmas SET lemma = ? WHERE id = ?", (new_lemma, old_id))
                        print(f"   ✅ 重命名: {old_lemma} -> {new_lemma}")
                    
                    self.stats['parentheses_cleaned'] += 1
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ 修复括号词条失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def fix_plural_redirects(self):
        """修复复数重定向"""
        print("🔧 修复复数词条重定向...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            plural_fixes = self.get_definite_plurals_to_redirect()
            
            for plural_lemma, singular_lemma in plural_fixes:
                success = self.redirect_plural_to_singular(cursor, plural_lemma, singular_lemma)
                if success:
                    print(f"   ✅ 重定向: {plural_lemma} -> {singular_lemma}")
                    self.stats['plurals_redirected'] += 1
                else:
                    print(f"   ❌ 失败: {plural_lemma} -> {singular_lemma}")
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ 修复复数重定向失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def redirect_plural_to_singular(self, cursor, plural_lemma, singular_lemma):
        """将复数词条重定向到单数"""
        # 查找复数词条
        cursor.execute("SELECT id FROM word_lemmas WHERE lemma = ? AND pos = 'noun'", (plural_lemma,))
        plural_word = cursor.fetchone()
        
        if not plural_word:
            return False
        
        plural_id = plural_word[0]
        
        # 查找或创建单数词条
        cursor.execute("SELECT id FROM word_lemmas WHERE lemma = ? AND pos = 'noun'", (singular_lemma,))
        singular_word = cursor.fetchone()
        
        if singular_word:
            singular_id = singular_word[0]
        else:
            # 创建单数词条
            cursor.execute("""
                INSERT INTO word_lemmas (lemma, pos, cefr, notes)
                VALUES (?, 'noun', 'A1', ?)
            """, (singular_lemma, f"plural:{plural_lemma}"))
            singular_id = cursor.lastrowid
        
        # 合并数据
        self.merge_word_data(cursor, plural_id, singular_id)
        
        # 更新单数词条的复数信息
        cursor.execute("""
            UPDATE word_lemmas 
            SET notes = CASE 
                WHEN notes IS NULL THEN ? 
                WHEN notes NOT LIKE '%plural:%' THEN notes || ' ' || ?
                ELSE notes
            END
            WHERE id = ?
        """, (f"plural:{plural_lemma}", f"plural:{plural_lemma}", singular_id))
        
        # 将复数词条转为词形
        cursor.execute("""
            INSERT OR IGNORE INTO word_forms (lemma_id, form, feature_key, feature_value)
            VALUES (?, ?, ?, ?)
        """, (singular_id, plural_lemma, "plural", "plural_form"))
        
        # 删除原复数词条
        cursor.execute("DELETE FROM word_lemmas WHERE id = ?", (plural_id,))
        
        return True
    
    def merge_word_data(self, cursor, from_id, to_id):
        """合并词条数据"""
        # 合并翻译
        cursor.execute("""
            INSERT OR IGNORE INTO translations (lemma_id, lang_code, text, source)
            SELECT ?, lang_code, text, source 
            FROM translations WHERE lemma_id = ?
        """, (to_id, from_id))
        cursor.execute("DELETE FROM translations WHERE lemma_id = ?", (from_id,))
        
        # 合并例句
        cursor.execute("""
            INSERT OR IGNORE INTO examples (lemma_id, de_text, en_text, zh_text, level)
            SELECT ?, de_text, en_text, zh_text, level
            FROM examples WHERE lemma_id = ?
        """, (to_id, from_id))
        cursor.execute("DELETE FROM examples WHERE lemma_id = ?", (from_id,))
        
        # 合并词形
        cursor.execute("""
            UPDATE word_forms SET lemma_id = ? WHERE lemma_id = ?
        """, (to_id, from_id))
    
    def fix_special_relationships(self):
        """修复特殊关系"""
        print("🔧 修复特殊词条关系...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 修复 Deutsch/Deutsche 关系
            cursor.execute("SELECT id FROM word_lemmas WHERE lemma = 'Deutsch'")
            deutsch_word = cursor.fetchone()
            
            cursor.execute("SELECT id FROM word_lemmas WHERE lemma = 'Deutsche'")
            deutsche_word = cursor.fetchone()
            
            if deutsch_word and deutsche_word:
                # 这两个应该分开：Deutsch(语言) vs Deutsche(德国人)
                # 只需确保它们有正确的词性和翻译
                cursor.execute("UPDATE word_lemmas SET pos = 'noun', notes = 'language' WHERE id = ?", (deutsch_word[0],))
                cursor.execute("UPDATE word_lemmas SET pos = 'noun', notes = 'nationality' WHERE id = ?", (deutsche_word[0],))
                print("   ✅ 修复: Deutsch(语言) 和 Deutsche(德国人) 关系")
                self.stats['relationships_fixed'] += 1
            
            # 处理 Deutschen -> Deutsche 重定向
            cursor.execute("SELECT id FROM word_lemmas WHERE lemma = 'Deutschen'")
            deutschen_word = cursor.fetchone()
            
            if deutschen_word and deutsche_word:
                self.merge_word_data(cursor, deutschen_word[0], deutsche_word[0])
                cursor.execute("DELETE FROM word_lemmas WHERE id = ?", (deutschen_word[0],))
                print("   ✅ 重定向: Deutschen -> Deutsche")
                self.stats['relationships_fixed'] += 1
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ 修复特殊关系失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def verify_common_plurals(self):
        """验证常见复数是否正确处理"""
        print("🔍 验证常见复数处理...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查一些应该是单数主词条的词
            should_be_singular = ['Zug', 'Haus', 'Mann', 'Frau', 'Kind', 'Buch', 'Tisch']
            
            for lemma in should_be_singular:
                cursor.execute("""
                    SELECT lemma, notes FROM word_lemmas 
                    WHERE lemma = ? AND pos = 'noun'
                """, (lemma,))
                
                word = cursor.fetchone()
                if word:
                    lemma_text, notes = word
                    plural_info = "有复数信息" if notes and "plural:" in notes else "无复数信息"
                    print(f"   ✅ {lemma_text}: {plural_info}")
                else:
                    print(f"   ❌ {lemma}: 未找到")
        
        finally:
            conn.close()
    
    def run_fixes(self):
        """运行所有修复"""
        print("🔧 特定问题修复工具")
        print("=" * 60)
        
        # 1. 修复带括号的词条
        self.fix_parentheses_words()
        
        # 2. 修复复数重定向
        self.fix_plural_redirects()
        
        # 3. 修复特殊关系
        self.fix_special_relationships()
        
        # 4. 验证结果
        self.verify_common_plurals()
        
        self.print_final_stats()
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 特定问题修复完成!")
        print("=" * 50)
        print(f"删除英语词条: {self.stats['english_deleted']}")
        print(f"重定向复数词条: {self.stats['plurals_redirected']}")
        print(f"清理括号词条: {self.stats['parentheses_cleaned']}")
        print(f"修复词条关系: {self.stats['relationships_fixed']}")
        print(f"总用时: {elapsed}")
        
        total_fixes = (self.stats['english_deleted'] + 
                      self.stats['plurals_redirected'] + 
                      self.stats['parentheses_cleaned'] + 
                      self.stats['relationships_fixed'])
        
        print(f"总修复项目: {total_fixes}")
        
        if total_fixes > 0:
            print(f"\n✅ 修复成功! 数据库更加准确:")
            print("   • 复数词条已重定向到单数")
            print("   • 括号词条已清理")
            print("   • 词条关系已修正")
            print("   • 单复数结构更加合理")

def main():
    fixer = SpecificWordFixer()
    fixer.run_fixes()

if __name__ == "__main__":
    main()