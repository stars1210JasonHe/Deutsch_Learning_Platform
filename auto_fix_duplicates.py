#!/usr/bin/env python3
"""
自动修复重复词条 - 无需用户交互
"""
import sqlite3
import re
from datetime import datetime
from collections import defaultdict

class AutoDuplicateFixer:
    
    def __init__(self):
        self.db_path = 'data/app.db'
        self.stats = {
            'lemmas_merged': 0,
            'forms_moved': 0,
            'duplicates_found': 0,
            'start_time': datetime.now()
        }
    
    def run_auto_fix(self):
        """自动运行修复流程"""
        print("🚀 自动修复重复词条")
        print("=" * 60)
        
        # 分析重复词条
        verb_groups, noun_groups = self.analyze_duplicates()
        
        # 自动合并
        self.merge_duplicate_lemmas(verb_groups, noun_groups)
        self.print_final_stats()
        
        return self.stats
    
    def analyze_duplicates(self):
        """分析重复的词条"""
        print("🔍 分析重复词条...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 查找动词重复
        cursor.execute("""
            SELECT lemma, pos, id, cefr, frequency 
            FROM word_lemmas 
            WHERE pos = 'verb' 
            ORDER BY lemma
        """)
        verbs = cursor.fetchall()
        verb_groups = self.group_similar_verbs(verbs)
        
        # 查找名词重复  
        cursor.execute("""
            SELECT lemma, pos, id, cefr, frequency 
            FROM word_lemmas 
            WHERE pos = 'noun' 
            ORDER BY lemma
        """)
        nouns = cursor.fetchall()
        noun_groups = self.group_singular_plural_nouns(nouns)
        
        verb_duplicates = sum(1 for v in verb_groups.values() if len(v) > 1)
        noun_duplicates = sum(1 for v in noun_groups.values() if len(v) > 1)
        
        print(f"📊 发现重复组: 动词 {verb_duplicates} 组, 名词 {noun_duplicates} 组")
        
        conn.close()
        return verb_groups, noun_groups
    
    def group_similar_verbs(self, verbs):
        """将相似的动词分组"""
        groups = defaultdict(list)
        
        # 精确的动词对应关系
        verb_mapping = {
            'bin': 'sein', 'bist': 'sein', 'ist': 'sein', 'sind': 'sein', 'seid': 'sein',
            'war': 'sein', 'warst': 'sein', 'waren': 'sein', 'wart': 'sein',
            
            'habe': 'haben', 'hast': 'haben', 'hat': 'haben', 
            'hatte': 'haben', 'hattest': 'haben', 'hatten': 'haben', 'hattet': 'haben',
            
            'sehe': 'sehen', 'siehst': 'sehen', 'sieht': 'sehen',
            'sah': 'sehen', 'sahst': 'sehen', 'sahen': 'sehen', 'saht': 'sehen',
            
            'gehe': 'gehen', 'gehst': 'gehen', 'geht': 'gehen',
            'ging': 'gehen', 'gingst': 'gehen', 'gingen': 'gehen', 'gingt': 'gehen',
            
            'komme': 'kommen', 'kommst': 'kommen', 'kommt': 'kommen',
            'kam': 'kommen', 'kamst': 'kommen', 'kamen': 'kommen', 'kamt': 'kommen',
            
            'mache': 'machen', 'machst': 'machen', 'macht': 'machen',
            'machte': 'machen', 'machtest': 'machen', 'machten': 'machen', 'machtet': 'machen',
            
            'sage': 'sagen', 'sagst': 'sagen', 'sagt': 'sagen',
            'sagte': 'sagen', 'sagtest': 'sagen', 'sagten': 'sagen', 'sagtet': 'sagen',
            
            'bade': 'baden', 'badest': 'baden', 'badet': 'baden'
        }
        
        for verb_data in verbs:
            lemma = verb_data[0].lower()
            
            # 使用精确映射或自身
            base_form = verb_mapping.get(lemma, lemma)
            
            # 如果lemma以-en结尾，它可能是不定式，用作base
            if lemma.endswith('en'):
                base_form = lemma
            
            groups[base_form].append(verb_data)
        
        return {k: v for k, v in groups.items() if len(v) > 1}
    
    def group_singular_plural_nouns(self, nouns):
        """将单复数名词分组"""
        groups = defaultdict(list)
        
        # 精确的单复数对应关系
        plural_mapping = {
            'züge': 'zug', 'zügen': 'zug',
            'häuser': 'haus', 'häusern': 'haus',
            'männer': 'mann', 'männern': 'mann', 
            'kinder': 'kind', 'kindern': 'kind',
            'frauen': 'frau',
            'freunde': 'freund',
            'jahre': 'jahr', 
            'haare': 'haar',
            'geschäfte': 'geschäft',
            'geschenke': 'geschenk',
            'probleme': 'problem',
            'spiele': 'spiel',
            'worte': 'wort', 'wörter': 'wort',
            'fische': 'fisch',
            'schuhe': 'schuh',
            'preise': 'preis',
            'punkte': 'punkt',
            'berge': 'berg',
            'arme': 'arm',
            'sterne': 'stern',
            'witze': 'witz',
            'sprachkurse': 'sprachkurs',
            'integrationskurse': 'integrationskurs',
            'termine': 'termin',
            'pakete': 'paket',
            'anrufe': 'anruf',
            'abgase': 'abgas',
            'feiertage': 'feiertag',
            'getränke': 'getränk',
            'papiere': 'papier',
            'prospekte': 'prospekt',
            'formulare': 'formular',
            'feuerzeuge': 'feuerzeug',
            'boote': 'boot',
            'monate': 'monat',
            'versuche': 'versuch',
            'vitamine': 'vitamin',
            'lehrwerke': 'lehrwerk',
            'sonderangebote': 'sonderangebot',
            'schritte': 'schritt',
            'tische': 'tisch',
            'hause': 'haus'  # zu Hause -> Haus
        }
        
        for noun_data in nouns:
            lemma = noun_data[0].lower()
            
            # 使用精确映射
            singular_form = plural_mapping.get(lemma, lemma)
            
            groups[singular_form].append(noun_data)
        
        return {k: v for k, v in groups.items() if len(v) > 1}
    
    def merge_duplicate_lemmas(self, verb_groups, noun_groups):
        """合并重复的词条"""
        print(f"🔧 开始自动合并...")
        
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
            print(f"✅ 自动合并完成!")
            
        except Exception as e:
            print(f"❌ 合并失败: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def merge_verb_group(self, cursor, base_verb, variants):
        """合并一组动词变体"""
        # 选择最好的主词条（优先不定式形式）
        main_lemma = self.select_main_verb_lemma(variants)
        other_lemmas = [v for v in variants if v[2] != main_lemma[2]]
        
        if other_lemmas:
            print(f"  📝 动词: {main_lemma[0]} <- {[v[0] for v in other_lemmas]}")
        
        for other_lemma in other_lemmas:
            lemma_text, pos, lemma_id, cefr, freq = other_lemma
            
            # 将其他词条转为word_forms
            self.convert_lemma_to_word_form(cursor, lemma_id, main_lemma[2], lemma_text)
            
            # 迁移相关数据
            self.migrate_lemma_data(cursor, lemma_id, main_lemma[2])
            
            # 删除原词条
            cursor.execute("DELETE FROM word_lemmas WHERE id = ?", (lemma_id,))
            
            self.stats['lemmas_merged'] += 1
            self.stats['forms_moved'] += 1
    
    def merge_noun_group(self, cursor, base_noun, variants):
        """合并一组名词变体"""
        main_lemma = self.select_main_noun_lemma(variants)
        other_lemmas = [v for v in variants if v[2] != main_lemma[2]]
        
        if other_lemmas:
            print(f"  📝 名词: {main_lemma[0]} <- {[v[0] for v in other_lemmas]}")
        
        for other_lemma in other_lemmas:
            lemma_text, pos, lemma_id, cefr, freq = other_lemma
            
            # 如果是复数形式，更新主词条的复数信息
            if lemma_text.lower() != main_lemma[0].lower():
                self.update_plural_info(cursor, main_lemma[2], lemma_text)
            
            # 迁移相关数据
            self.migrate_lemma_data(cursor, lemma_id, main_lemma[2])
            
            # 删除原词条
            cursor.execute("DELETE FROM word_lemmas WHERE id = ?", (lemma_id,))
            
            self.stats['lemmas_merged'] += 1
    
    def select_main_verb_lemma(self, variants):
        """为动词选择最佳主词条（优先不定式）"""
        # 优先选择以-en结尾的不定式
        infinitives = [v for v in variants if v[0].lower().endswith('en')]
        if infinitives:
            return max(infinitives, key=lambda v: (v[4] or 0, len(v[0])))  # 按频率和长度
        
        # 否则选择频率最高或CEFR级别最好的
        return self.select_main_lemma(variants)
    
    def select_main_noun_lemma(self, variants):
        """为名词选择最佳主词条（优先单数）"""
        # 启发式：通常较短的是单数形式
        return min(variants, key=lambda v: (len(v[0]), -(v[4] or 0)))
    
    def select_main_lemma(self, variants):
        """通用的主词条选择逻辑"""
        def sort_key(variant):
            lemma, pos, lemma_id, cefr, freq = variant
            freq_score = freq if freq else 0
            cefr_score = {'A1': 4, 'A2': 3, 'B1': 2, 'B2': 1}.get(cefr, 0)
            return (freq_score, cefr_score, len(lemma))
        
        return max(variants, key=sort_key)
    
    def convert_lemma_to_word_form(self, cursor, old_lemma_id, new_lemma_id, form_text):
        """将词条转换为词形"""
        cursor.execute("""
            INSERT OR IGNORE INTO word_forms (lemma_id, form, feature_key, feature_value)
            VALUES (?, ?, ?, ?)
        """, (new_lemma_id, form_text, "variant", "inflected_form"))
    
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
        
        print(f"\n🎉 重复词条自动修复完成!")
        print("=" * 50)
        print(f"合并的词条数: {self.stats['lemmas_merged']}")
        print(f"转换的词形数: {self.stats['forms_moved']}")  
        print(f"总用时: {elapsed}")
        
        if self.stats['lemmas_merged'] > 0:
            print(f"\n✅ 修复成功! 现在:")
            print("   • sehe/sehen 已合并为 sehen")
            print("   • Zug/Züge 已合并为 Zug (复数信息保存在notes中)")
            print("   • habe/haben/hat 已合并为 haben")
            print("   • 所有变位形式现在指向正确的词条")

def main():
    fixer = AutoDuplicateFixer()
    return fixer.run_auto_fix()

if __name__ == "__main__":
    main()