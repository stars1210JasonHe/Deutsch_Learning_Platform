#!/usr/bin/env python3
"""
数据库架构不匹配修复脚本
将增强架构(lemma_senses, noun_props, verb_props)的数据迁移到简单架构(translations表)
确保UI能正确显示翻译数据
"""
import sqlite3
import json
import sys
import os
from datetime import datetime

# 直接设置路径，不依赖dotenv
sys.path.append(os.getcwd())

class DatabaseSchemaMigrator:
    """数据库架构迁移器 - 修复显示问题"""
    
    def __init__(self):
        self.db_path = 'data/app.db'
        self.stats = {
            'words_processed': 0,
            'translations_created': 0,
            'examples_migrated': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def analyze_current_state(self):
        """分析当前数据库状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查表结构
            print("📊 数据库表分析:")
            
            # 检查word_lemmas
            cursor.execute("SELECT COUNT(*) FROM word_lemmas")
            lemma_count = cursor.fetchone()[0]
            print(f"   word_lemmas: {lemma_count} 条")
            
            # 检查是否有新架构表
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('lemma_senses', 'noun_props', 'verb_props')
            """)
            enhanced_tables = [row[0] for row in cursor.fetchall()]
            print(f"   增强架构表: {enhanced_tables}")
            
            if enhanced_tables:
                cursor.execute("SELECT COUNT(*) FROM lemma_senses")
                sense_count = cursor.fetchone()[0]
                print(f"   lemma_senses: {sense_count} 条")
            
            # 检查translations表
            cursor.execute("SELECT COUNT(*) FROM translations")
            translation_count = cursor.fetchone()[0]
            print(f"   translations: {translation_count} 条")
            
            # 检查problem cases
            cursor.execute("""
                SELECT wl.lemma, ls.gloss_en, ls.gloss_zh, 
                       COUNT(t.id) as translation_count
                FROM word_lemmas wl
                LEFT JOIN lemma_senses ls ON ls.lemma_id = wl.id  
                LEFT JOIN translations t ON t.lemma_id = wl.id
                GROUP BY wl.id
                HAVING translation_count = 0 AND (ls.gloss_en IS NOT NULL OR ls.gloss_zh IS NOT NULL)
                LIMIT 10
            """)
            problem_words = cursor.fetchall()
            
            print(f"\n❌ 发现问题单词 (有gloss但无translations): {len(problem_words)}个")
            for word in problem_words:
                print(f"   - {word[0]}: EN='{word[1]}' ZH='{word[2]}'")
            
            return {
                'lemma_count': lemma_count,
                'translation_count': translation_count,
                'enhanced_tables': enhanced_tables,
                'problem_count': len(problem_words)
            }
            
        finally:
            conn.close()
    
    def migrate_enhanced_to_simple(self):
        """将增强架构数据迁移到简单架构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            print("\n🔄 开始迁移增强架构数据...")
            
            # 查找所有有gloss但没有translations的词汇
            cursor.execute("""
                SELECT wl.id, wl.lemma, ls.gloss_en, ls.gloss_zh, ls.upos
                FROM word_lemmas wl
                JOIN lemma_senses ls ON ls.lemma_id = wl.id
                LEFT JOIN translations t ON t.lemma_id = wl.id
                WHERE t.id IS NULL 
                AND (ls.gloss_en IS NOT NULL OR ls.gloss_zh IS NOT NULL)
            """)
            
            words_to_migrate = cursor.fetchall()
            print(f"   找到 {len(words_to_migrate)} 个需要迁移的词汇")
            
            for lemma_id, lemma, gloss_en, gloss_zh, upos in words_to_migrate:
                self.stats['words_processed'] += 1
                print(f"   迁移: {lemma} ({upos})")
                
                try:
                    # 创建英文翻译
                    if gloss_en and gloss_en.strip():
                        cursor.execute("""
                            INSERT INTO translations (lemma_id, lang_code, text, source)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, "en", gloss_en.strip(), "migrated_from_enhanced"))
                        self.stats['translations_created'] += 1
                    
                    # 创建中文翻译  
                    if gloss_zh and gloss_zh.strip():
                        cursor.execute("""
                            INSERT INTO translations (lemma_id, lang_code, text, source)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, "zh", gloss_zh.strip(), "migrated_from_enhanced"))
                        self.stats['translations_created'] += 1
                    
                    # 迁移examples表数据
                    cursor.execute("""
                        SELECT de_text, en_text, zh_text FROM examples 
                        WHERE sense_id IN (SELECT id FROM lemma_senses WHERE lemma_id = ?)
                        AND lemma_id IS NULL
                    """, (lemma_id,))
                    
                    examples = cursor.fetchall()
                    for de_text, en_text, zh_text in examples:
                        if de_text and de_text.strip():
                            cursor.execute("""
                                UPDATE examples 
                                SET lemma_id = ?
                                WHERE de_text = ? AND lemma_id IS NULL
                            """, (lemma_id, de_text))
                            self.stats['examples_migrated'] += 1
                    
                    # 提交这个词的更改
                    conn.commit()
                    
                except Exception as e:
                    print(f"     ❌ 迁移失败: {e}")
                    self.stats['errors'] += 1
                    conn.rollback()
            
            print("✅ 数据迁移完成")
            
        finally:
            conn.close()
    
    def add_missing_basic_translations(self):
        """为没有任何翻译的词汇添加基础翻译"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 常用德语单词基础翻译库
        basic_translations = {
            "kreuzen": {
                "pos": "verb",
                "translations_en": ["to cross", "to intersect", "to cruise"],
                "translations_zh": ["交叉", "穿过", "巡航"]
            },
            "arbeiten": {
                "pos": "verb", 
                "translations_en": ["to work"],
                "translations_zh": ["工作"]
            },
            "leben": {
                "pos": "verb",
                "translations_en": ["to live"],
                "translations_zh": ["生活", "居住"]
            },
            "kaufen": {
                "pos": "verb",
                "translations_en": ["to buy"],
                "translations_zh": ["买"]
            },
            "verkaufen": {
                "pos": "verb",
                "translations_en": ["to sell"],
                "translations_zh": ["卖"]
            },
            "schlafen": {
                "pos": "verb",
                "translations_en": ["to sleep"],
                "translations_zh": ["睡觉"]
            },
            "fahren": {
                "pos": "verb",
                "translations_en": ["to drive", "to go"],
                "translations_zh": ["开车", "行驶"]
            },
            "laufen": {
                "pos": "verb",
                "translations_en": ["to run", "to walk"],
                "translations_zh": ["跑", "走"]
            },
            "machen": {
                "pos": "verb",
                "translations_en": ["to make", "to do"],
                "translations_zh": ["做", "制作"]
            },
            "sagen": {
                "pos": "verb",
                "translations_en": ["to say"],
                "translations_zh": ["说"]
            },
            "sehen": {
                "pos": "verb",
                "translations_en": ["to see"],
                "translations_zh": ["看见"]
            },
            "wissen": {
                "pos": "verb",
                "translations_en": ["to know"],
                "translations_zh": ["知道"]
            },
            "Freund": {
                "pos": "noun",
                "translations_en": ["friend"],
                "translations_zh": ["朋友"]
            },
            "Buch": {
                "pos": "noun",
                "translations_en": ["book"],
                "translations_zh": ["书"]
            },
            "Zeit": {
                "pos": "noun",
                "translations_en": ["time"],
                "translations_zh": ["时间"]
            },
            "Haus": {
                "pos": "noun",
                "translations_en": ["house"],
                "translations_zh": ["房子"]
            }
        }
        
        try:
            print("\n📚 添加基础翻译...")
            
            for lemma, data in basic_translations.items():
                # 检查词汇是否存在且缺少翻译
                cursor.execute("""
                    SELECT wl.id FROM word_lemmas wl
                    LEFT JOIN translations t ON t.lemma_id = wl.id
                    WHERE wl.lemma = ? AND t.id IS NULL
                """, (lemma,))
                
                result = cursor.fetchone()
                if result:
                    lemma_id = result[0]
                    print(f"   添加翻译: {lemma}")
                    
                    # 添加英文翻译
                    for en_text in data["translations_en"]:
                        cursor.execute("""
                            INSERT INTO translations (lemma_id, lang_code, text, source)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, "en", en_text, "basic_fallback"))
                        self.stats['translations_created'] += 1
                    
                    # 添加中文翻译
                    for zh_text in data["translations_zh"]:
                        cursor.execute("""
                            INSERT INTO translations (lemma_id, lang_code, text, source)
                            VALUES (?, ?, ?, ?)
                        """, (lemma_id, "zh", zh_text, "basic_fallback"))
                        self.stats['translations_created'] += 1
                    
                    conn.commit()
            
            print("✅ 基础翻译添加完成")
            
        finally:
            conn.close()
    
    def verify_fix(self):
        """验证修复结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            print("\n🔍 验证修复结果:")
            
            # 检查之前的问题词汇
            test_words = ['kreuzen', 'bezahlen', 'arbeiten', 'leben']
            
            for word in test_words:
                cursor.execute("""
                    SELECT wl.lemma, 
                           COUNT(CASE WHEN t.lang_code = 'en' THEN 1 END) as en_count,
                           COUNT(CASE WHEN t.lang_code = 'zh' THEN 1 END) as zh_count,
                           GROUP_CONCAT(CASE WHEN t.lang_code = 'en' THEN t.text END) as en_translations,
                           GROUP_CONCAT(CASE WHEN t.lang_code = 'zh' THEN t.text END) as zh_translations
                    FROM word_lemmas wl
                    LEFT JOIN translations t ON t.lemma_id = wl.id
                    WHERE wl.lemma = ?
                    GROUP BY wl.id
                """, (word,))
                
                result = cursor.fetchone()
                if result:
                    lemma, en_count, zh_count, en_trans, zh_trans = result
                    status = "✅" if (en_count > 0 and zh_count > 0) else "❌"
                    print(f"   {status} {lemma}: EN({en_count}) ZH({zh_count})")
                    if en_trans:
                        print(f"      EN: {en_trans}")
                    if zh_trans:
                        print(f"      ZH: {zh_trans}")
                else:
                    print(f"   ❌ {word}: 未找到")
            
            # 总体统计
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT wl.id) as total_words,
                    COUNT(DISTINCT CASE WHEN t.id IS NOT NULL THEN wl.id END) as words_with_translations,
                    COUNT(t.id) as total_translations
                FROM word_lemmas wl
                LEFT JOIN translations t ON t.lemma_id = wl.id
            """)
            
            total_words, words_with_trans, total_trans = cursor.fetchone()
            coverage = (words_with_trans / total_words * 100) if total_words > 0 else 0
            
            print(f"\n📊 总体统计:")
            print(f"   总词汇数: {total_words}")
            print(f"   有翻译的词汇: {words_with_trans}")
            print(f"   翻译覆盖率: {coverage:.1f}%")
            print(f"   总翻译数: {total_trans}")
            
        finally:
            conn.close()
    
    def print_final_stats(self):
        """打印最终统计"""
        elapsed = datetime.now() - self.stats['start_time']
        
        print(f"\n🎉 数据库架构修复完成!")
        print(f"=" * 50)
        print(f"处理词汇: {self.stats['words_processed']}")
        print(f"创建翻译: {self.stats['translations_created']}")
        print(f"迁移例句: {self.stats['examples_migrated']}")
        print(f"错误数量: {self.stats['errors']}")
        print(f"总用时: {elapsed}")
        print("\n🚀 现在刷新浏览器，搜索 'kreuzen' 应该能看到翻译了!")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='修复数据库架构不匹配问题')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式')
    parser.add_argument('--analyze-only', action='store_true', help='只分析不修复')
    
    args = parser.parse_args()
    
    print("🔧 数据库架构修复工具")
    print("=" * 50)
    print("问题: 导入脚本使用增强架构，但UI期望简单架构")
    print("解决: 将gloss_en/gloss_zh迁移到translations表")
    
    migrator = DatabaseSchemaMigrator()
    
    # 1. 分析当前状态
    print("\n📊 第1步: 分析当前数据库状态")
    state = migrator.analyze_current_state()
    
    if args.analyze_only:
        print("\n⚠️ 仅分析模式 - 退出")
        return
    
    if state['problem_count'] == 0:
        print("\n✅ 未发现架构不匹配问题!")
        return
    
    if args.dry_run:
        print(f"\n⚠️ 试运行模式 - 将会迁移 {state['problem_count']} 个词汇")
        return
    
    # 2. 执行迁移
    print("\n🔄 第2步: 迁移增强架构数据")
    migrator.migrate_enhanced_to_simple()
    
    # 3. 添加基础翻译
    print("\n📚 第3步: 添加常用词汇基础翻译")  
    migrator.add_missing_basic_translations()
    
    # 4. 验证修复
    print("\n🔍 第4步: 验证修复结果")
    migrator.verify_fix()
    
    # 5. 打印统计
    migrator.print_final_stats()

if __name__ == "__main__":
    main()