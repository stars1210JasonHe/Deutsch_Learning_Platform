#!/usr/bin/env python3
"""
修复重复词条问题
处理类似情况：
- sehen (不定式) 和 sehe (第一人称) 应该指向同一个词条
- Zug (单数) 和 Züge (复数) 应该指向同一个词条
- 动词变位形式应该存在word_forms表中，而不是单独的lemmas
"""
import sqlite3
import re
from datetime import datetime
from collections import defaultdict

class DuplicateLemmaFixer:
    
    def __init__(self):
        self.db_path = 'data/app.db'
        self.stats = {
            'lemmas_merged': 0,
            'forms_moved': 0,
            'duplicates_found': 0,
            'start_time': datetime.now()
        }
    
    def analyze_duplicates(self):
        """分析重复的词条"""
        print("🔍 分析重复词条")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. 查找可能的动词重复（基于相似性）
        cursor.execute("""
            SELECT lemma, pos, id, cefr, frequency 
            FROM word_lemmas 
            WHERE pos = 'verb' 
            ORDER BY lemma
        """)
        verbs = cursor.fetchall()
        
        verb_groups = self.group_similar_verbs(verbs)
        
        print(f"📊 发现 {len(verb_groups)} 组可能重复的动词:")
        for i, (base_verb, variants) in enumerate(verb_groups.items(), 1):
            if len(variants) > 1:
                print(f"  {i}. {base_verb} 组:")
                for lemma, pos, lemma_id, cefr, freq in variants:
                    cefr_str = f"[{cefr}]" if cefr else ""
                    freq_str = f"(频率:{freq})" if freq else ""
                    print(f"     • {lemma} {cefr_str} {freq_str} (ID: {lemma_id})")
        
        # 2. 查找可能的名词重复（单复数）
        cursor.execute("""
            SELECT lemma, pos, id, cefr, frequency 
            FROM word_lemmas 
            WHERE pos = 'noun' 
            ORDER BY lemma
        """)
        nouns = cursor.fetchall()
        
        noun_groups = self.group_singular_plural_nouns(nouns)
        
        print(f"\n📊 发现 {len(noun_groups)} 组可能重复的名词:")
        for i, (base_noun, variants) in enumerate(noun_groups.items(), 1):
            if len(variants) > 1:
                print(f"  {i}. {base_noun} 组:")
                for lemma, pos, lemma_id, cefr, freq in variants:
                    cefr_str = f"[{cefr}]" if cefr else ""
                    freq_str = f"(频率:{freq})" if freq else ""
                    print(f"     • {lemma} {cefr_str} {freq_str} (ID: {lemma_id})")
        
        conn.close()
        return verb_groups, noun_groups
    
    def group_similar_verbs(self, verbs):
        """将相似的动词分组"""
        groups = defaultdict(list)
        
        for verb_data in verbs:
            lemma = verb_data[0]
            
            # 找到可能的基础形式
            base_form = self.get_verb_base_form(lemma)
            groups[base_form].append(verb_data)
        
        # 只返回有多个变体的组
        return {k: v for k, v in groups.items() if len(v) > 1}
    
    def get_verb_base_form(self, verb):
        """推断动词的基础形式（不定式）"""
        # 常见德语动词变位规律
        verb = verb.lower()
        
        # 如果以-en结尾，可能是不定式
        if verb.endswith('en'):
            return verb
        
        # 一些常见的变位形式转换
        conversions = {
            # 强变位动词
            'bin': 'sein',
            'bist': 'sein', 
            'ist': 'sein',
            'sind': 'sein',
            'seid': 'sein',
            'war': 'sein',
            'warst': 'sein',
            'waren': 'sein',
            'wart': 'sein',
            
            'habe': 'haben',
            'hast': 'haben',
            'hat': 'haben',
            'hatte': 'haben',
            'hattest': 'haben',
            'hatten': 'haben',
            'hattet': 'haben',
            
            'sehe': 'sehen',
            'siehst': 'sehen',
            'sieht': 'sehen',
            'sah': 'sehen',
            'sahst': 'sehen',
            'sahen': 'sehen',
            'saht': 'sehen',
            
            'gehe': 'gehen',
            'gehst': 'gehen',
            'geht': 'gehen',
            'ging': 'gehen',
            'gingst': 'gehen',
            'gingen': 'gehen',
            'gingt': 'gehen',
            
            'komme': 'kommen',
            'kommst': 'kommen',
            'kommt': 'kommen',
            'kam': 'kommen',
            'kamst': 'kommen',
            'kamen': 'kommen',
            'kamt': 'kommen',
        }
        
        if verb in conversions:
            return conversions[verb]
        
        # 规律变位：去掉人称词尾，加-en
        # 第一人称通常去-e加-en
        if verb.endswith('e') and len(verb) > 2:
            base = verb[:-1] + 'en'
            return base
        
        # 其他形式尝试重构
        if verb.endswith(('st', 't')):  # du/er形式
            # 这比较复杂，暂时返回原形
            pass
        
        return verb
    
    def group_singular_plural_nouns(self, nouns):
        """将单复数名词分组"""
        groups = defaultdict(list)
        
        for noun_data in nouns:
            lemma = noun_data[0]
            
            # 找到可能的单数形式
            singular_form = self.get_singular_form(lemma)
            groups[singular_form].append(noun_data)
        
        return {k: v for k, v in groups.items() if len(v) > 1}
    
    def get_singular_form(self, noun):
        """推断名词的单数形式"""
        noun_lower = noun.lower()
        
        # 常见复数规律
        plural_patterns = [
            # -e复数
            ('züge', 'zug'),
            ('tage', 'tag'),
            ('jahre', 'jahr'),
            
            # -er复数  
            ('kinder', 'kind'),
            ('männer', 'mann'),
            ('häuser', 'haus'),
            
            # -en复数
            ('frauen', 'frau'),
            ('straßen', 'straße'),
            
            # -s复数
            ('autos', 'auto'),
            ('büros', 'büro'),
        ]
        
        for plural, singular in plural_patterns:
            if noun_lower == plural:
                return singular
        
        # 一般规律：如果以复数标记结尾，尝试去掉
        if noun_lower.endswith('e') and len(noun_lower) > 2:
            singular_candidate = noun_lower[:-1]
            # 检查是否是合理的单数形式
            return singular_candidate
        
        return noun_lower
    
    def merge_duplicate_lemmas(self, verb_groups, noun_groups):
        """合并重复的词条"""
        print(f"\n🔧 开始合并重复词条")
        print("=" * 50)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 合并动词组
            for base_verb, variants in verb_groups.items():
                if len(variants) > 1:
                    self.merge_verb_group(cursor, base_verb, variants)
            
            # 合并名词组  
            for base_noun, variants in noun_groups.items():
                if len(variants) > 1:
                    self.merge_noun_group(cursor, base_noun, variants)
            
            conn.commit()
            print(f"\n✅ 合并完成!")
            
        except Exception as e:
            print(f"❌ 合并失败: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def merge_verb_group(self, cursor, base_verb, variants):
        """合并一组动词变体"""
        # 找到最好的主词条（优先级：频率 > CEFR级别 > 最长的词）
        main_lemma = self.select_main_lemma(variants)
        other_lemmas = [v for v in variants if v[2] != main_lemma[2]]  # v[2] is id
        
        print(f"📝 合并动词组 '{base_verb}' -> 主词条: {main_lemma[0]} (ID: {main_lemma[2]})")
        
        for other_lemma in other_lemmas:
            lemma_text, pos, lemma_id, cefr, freq = other_lemma
            print(f"   🔄 将 '{lemma_text}' 转为词形...")
            
            # 将其他词条转为word_forms
            self.convert_lemma_to_word_form(cursor, lemma_id, main_lemma[2], lemma_text)
            
            # 迁移相关数据
            self.migrate_lemma_data(cursor, lemma_id, main_lemma[2])
            
            # 删除原词条
            cursor.execute("DELETE FROM word_lemmas WHERE id = ?", (lemma_id,))
            
            self.stats['lemmas_merged'] += 1
            self.stats['forms_moved'] += 1
    
    def merge_noun_group(self, cursor, base_noun, variants):
        """合并一组名词变体（单复数）"""
        main_lemma = self.select_main_lemma(variants)
        other_lemmas = [v for v in variants if v[2] != main_lemma[2]]
        
        print(f"📝 合并名词组 '{base_noun}' -> 主词条: {main_lemma[0]} (ID: {main_lemma[2]})")
        
        for other_lemma in other_lemmas:
            lemma_text, pos, lemma_id, cefr, freq = other_lemma
            print(f"   🔄 将 '{lemma_text}' 信息合并到主词条...")
            
            # 对于名词，如果是复数形式，更新主词条的notes添加复数信息
            if lemma_text.lower() != main_lemma[0].lower():
                self.update_plural_info(cursor, main_lemma[2], lemma_text)
            
            # 迁移相关数据
            self.migrate_lemma_data(cursor, lemma_id, main_lemma[2])
            
            # 删除原词条
            cursor.execute("DELETE FROM word_lemmas WHERE id = ?", (lemma_id,))
            
            self.stats['lemmas_merged'] += 1
    
    def select_main_lemma(self, variants):
        """选择最佳的主词条"""
        # 排序规则：1. 频率高 2. CEFR级别低 3. 词长（不定式通常更长）
        def sort_key(variant):
            lemma, pos, lemma_id, cefr, freq = variant
            
            # 频率权重
            freq_score = freq if freq else 0
            
            # CEFR权重 (A1=4, A2=3, B1=2, B2=1, 其他=0)
            cefr_score = {'A1': 4, 'A2': 3, 'B1': 2, 'B2': 1}.get(cefr, 0)
            
            # 词长权重（不定式通常更长）
            length_score = len(lemma)
            
            return (freq_score, cefr_score, length_score)
        
        return max(variants, key=sort_key)
    
    def convert_lemma_to_word_form(self, cursor, old_lemma_id, new_lemma_id, form_text):
        """将词条转换为词形"""
        cursor.execute("""
            INSERT INTO word_forms (lemma_id, form, feature_key, feature_value)
            VALUES (?, ?, ?, ?)
        """, (new_lemma_id, form_text, "variant", "lemma_variant"))
        
    def update_plural_info(self, cursor, main_lemma_id, plural_form):
        """更新主词条的复数信息"""
        cursor.execute("""
            UPDATE word_lemmas 
            SET notes = CASE 
                WHEN notes IS NULL THEN ? 
                WHEN notes NOT LIKE '%plural:%' THEN notes || ' ' || ?
                ELSE notes
            END
            WHERE id = ?
        """, (f"plural:{plural_form}", f"plural:{plural_form}", main_lemma_id))
    
    def migrate_lemma_data(self, cursor, old_lemma_id, new_lemma_id):
        """迁移词条相关的所有数据"""
        
        # 迁移翻译数据（避免重复）
        cursor.execute("""
            INSERT OR IGNORE INTO translations (lemma_id, lang_code, text, source)
            SELECT ?, lang_code, text, source 
            FROM translations 
            WHERE lemma_id = ?
        """, (new_lemma_id, old_lemma_id))
        
        cursor.execute("DELETE FROM translations WHERE lemma_id = ?", (old_lemma_id,))
        
        # 迁移例句数据
        cursor.execute("""
            INSERT OR IGNORE INTO examples (lemma_id, de_text, en_text, zh_text, level)
            SELECT ?, de_text, en_text, zh_text, level
            FROM examples 
            WHERE lemma_id = ?
        """, (new_lemma_id, old_lemma_id))
        
        cursor.execute("DELETE FROM examples WHERE lemma_id = ?", (old_lemma_id,))
        
        # 迁移词形数据
        cursor.execute("""
            UPDATE word_forms 
            SET lemma_id = ? 
            WHERE lemma_id = ?
        """, (new_lemma_id, old_lemma_id))
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 重复词条修复完成!")
        print("=" * 50)
        print(f"合并的词条数: {self.stats['lemmas_merged']}")
        print(f"转换的词形数: {self.stats['forms_moved']}")
        print(f"总用时: {elapsed}")
        
        if self.stats['lemmas_merged'] > 0:
            print(f"\n✅ 修复成功! 现在:")
            print("   • 动词变位形式指向正确的不定式词条")
            print("   • 名词单复数形式已合并")
            print("   • 数据库结构更加清晰")

def main():
    print("🚀 重复词条修复工具")
    print("=" * 60)
    print("将合并重复的词条：")
    print("• 动词变位形式 (sehe -> sehen)")  
    print("• 名词单复数 (Züge -> Zug)")
    print()
    
    fixer = DuplicateLemmaFixer()
    
    # 分析重复词条
    verb_groups, noun_groups = fixer.analyze_duplicates()
    
    # 询问是否继续合并
    print(f"\n💡 发现重复词条组:")
    print(f"   动词组: {sum(1 for v in verb_groups.values() if len(v) > 1)}")
    print(f"   名词组: {sum(1 for v in noun_groups.values() if len(v) > 1)}")
    
    response = input("\n是否继续合并？(y/n): ").lower().strip()
    
    if response == 'y':
        # 执行合并
        fixer.merge_duplicate_lemmas(verb_groups, noun_groups)
        fixer.print_final_stats()
    else:
        print("取消合并操作。")

if __name__ == "__main__":
    main()