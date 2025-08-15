#!/usr/bin/env python3
"""
德语词库补全数据库迁移脚本
按照 lexicon-openai-gapfill-claude-spec.md 规范执行非破坏性迁移
"""
import sqlite3
import shutil
import os
from datetime import datetime

def backup_database():
    """备份现有数据库"""
    backup_name = f"data/app_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    if os.path.exists('data/app.db'):
        shutil.copy2('data/app.db', backup_name)
        print(f"✅ 数据库已备份到: {backup_name}")
        return backup_name
    else:
        print("❌ 找不到数据库文件")
        return None

def execute_migration():
    """执行数据库迁移"""
    print("🔧 开始执行数据库迁移...")
    
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    try:
        # 2.1 义项层（支持一词多义/多词性）
        print("创建 lemma_senses 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lemma_senses (
                id INTEGER PRIMARY KEY,
                lemma_id INTEGER NOT NULL REFERENCES word_lemmas(id) ON DELETE CASCADE,
                upos TEXT,
                xpos TEXT,
                gender TEXT,
                sense_label TEXT,
                gloss_en TEXT,
                gloss_zh TEXT,
                notes TEXT,
                confidence REAL,
                source TEXT DEFAULT 'backfill',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2.2 名词属性表
        print("创建 noun_props 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS noun_props (
                sense_id INTEGER PRIMARY KEY REFERENCES lemma_senses(id) ON DELETE CASCADE,
                gen_sg TEXT,
                plural TEXT,
                declension_class TEXT,
                dative_plural_ends_n INTEGER DEFAULT 0
            )
        """)
        
        # 2.3 动词属性表
        print("创建 verb_props 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verb_props (
                sense_id INTEGER PRIMARY KEY REFERENCES lemma_senses(id) ON DELETE CASCADE,
                separable INTEGER DEFAULT 0,
                prefix TEXT,
                aux TEXT,
                regularity TEXT,
                partizip_ii TEXT,
                reflexive INTEGER DEFAULT 0,
                valency_json TEXT
            )
        """)
        
        # 2.4 统一形态存储
        print("创建 forms_unimorph 表...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS forms_unimorph (
                id INTEGER PRIMARY KEY,
                sense_id INTEGER NOT NULL REFERENCES lemma_senses(id) ON DELETE CASCADE,
                form TEXT NOT NULL,
                features_json TEXT NOT NULL,
                UNIQUE (sense_id, form, features_json)
            )
        """)
        
        # 2.5 给现有表添加 sense_id 列（如果不存在）
        print("为 translations 表添加 sense_id 列...")
        try:
            cursor.execute("ALTER TABLE translations ADD COLUMN sense_id INTEGER REFERENCES lemma_senses(id)")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   sense_id 列已存在，跳过")
            else:
                raise
        
        print("为 examples 表添加 sense_id 列...")
        try:
            cursor.execute("ALTER TABLE examples ADD COLUMN sense_id INTEGER REFERENCES lemma_senses(id)")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print("   sense_id 列已存在，跳过")
            else:
                raise
        
        # 2.6 创建兼容视图
        print("创建兼容视图 v_lemma_primary...")
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_lemma_primary AS
            SELECT 
                wl.id AS lemma_id, 
                wl.lemma, 
                wl.pos, 
                wl.cefr, 
                wl.ipa, 
                wl.frequency,
                ls.id AS sense_id, 
                ls.upos, 
                ls.xpos, 
                ls.gender, 
                ls.gloss_en, 
                ls.gloss_zh
            FROM word_lemmas wl
            LEFT JOIN lemma_senses ls ON ls.lemma_id = wl.id
        """)
        
        # 2.7 创建索引以提高查询性能
        print("创建索引...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lemma_senses_lemma_id ON lemma_senses(lemma_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_forms_unimorph_sense_id ON forms_unimorph(sense_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_translations_sense_id ON translations(sense_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_examples_sense_id ON examples(sense_id)")
        
        # 2.8 为现有词条创建基础 sense 记录
        print("为现有词条创建基础 sense 记录...")
        cursor.execute("""
            INSERT OR IGNORE INTO lemma_senses (lemma_id, upos, xpos, source, confidence)
            SELECT 
                id as lemma_id,
                UPPER(pos) as upos,
                CASE 
                    WHEN pos = 'noun' THEN 'NN'
                    WHEN pos = 'verb' THEN 'VVINF'
                    WHEN pos = 'adjective' THEN 'ADJD'
                    WHEN pos = 'adverb' THEN 'ADV'
                    WHEN pos = 'preposition' THEN 'APPR'
                    WHEN pos = 'article' THEN 'ART'
                    WHEN pos = 'pronoun' THEN 'PPER'
                    ELSE 'OTHER'
                END as xpos,
                'migration' as source,
                0.5 as confidence
            FROM word_lemmas
            WHERE id NOT IN (SELECT lemma_id FROM lemma_senses)
        """)
        
        inserted_senses = cursor.rowcount
        print(f"   创建了 {inserted_senses} 个基础 sense 记录")
        
        # 2.9 关联现有的翻译和例句到对应的 sense
        print("关联现有翻译到 sense...")
        cursor.execute("""
            UPDATE translations 
            SET sense_id = (
                SELECT ls.id 
                FROM lemma_senses ls 
                WHERE ls.lemma_id = translations.lemma_id 
                LIMIT 1
            )
            WHERE sense_id IS NULL
        """)
        
        print("关联现有例句到 sense...")
        cursor.execute("""
            UPDATE examples 
            SET sense_id = (
                SELECT ls.id 
                FROM lemma_senses ls 
                WHERE ls.lemma_id = examples.lemma_id 
                LIMIT 1
            )
            WHERE sense_id IS NULL
        """)
        
        conn.commit()
        print("✅ 数据库迁移完成！")
        
        # 显示迁移后的统计信息
        print("\n📊 迁移后的统计信息:")
        tables = ['lemma_senses', 'noun_props', 'verb_props', 'forms_unimorph']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} 条记录")
        
        return True
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_migration():
    """验证迁移结果"""
    print("\n🔍 验证迁移结果...")
    
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    try:
        # 检查新表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%sense%' OR name LIKE '%props%' OR name LIKE '%unimorph%'")
        new_tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['lemma_senses', 'noun_props', 'verb_props', 'forms_unimorph']
        
        print("新创建的表:")
        for table in expected_tables:
            if table in new_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table}: {count} 条记录")
            else:
                print(f"   ❌ {table}: 未找到")
        
        # 检查视图
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='v_lemma_primary'")
        if cursor.fetchone():
            print("   ✅ v_lemma_primary 视图已创建")
        else:
            print("   ❌ v_lemma_primary 视图未找到")
        
        # 检查新增的列
        cursor.execute("PRAGMA table_info(translations)")
        trans_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(examples)")
        example_columns = [col[1] for col in cursor.fetchall()]
        
        if 'sense_id' in trans_columns:
            print("   ✅ translations.sense_id 列已添加")
        else:
            print("   ❌ translations.sense_id 列未找到")
            
        if 'sense_id' in example_columns:
            print("   ✅ examples.sense_id 列已添加")
        else:
            print("   ❌ examples.sense_id 列未找到")
        
        # 检查数据关联
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(t.sense_id) as with_sense
            FROM translations t
        """)
        total, with_sense = cursor.fetchone()
        print(f"   翻译关联: {with_sense}/{total} 条记录已关联到 sense")
        
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(e.sense_id) as with_sense
            FROM examples e
        """)
        total, with_sense = cursor.fetchone()
        print(f"   例句关联: {with_sense}/{total} 条记录已关联到 sense")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        conn.close()

def main():
    """主函数"""
    print("🚀 德语词库补全数据库迁移")
    print("=" * 50)
    
    # 1. 备份数据库
    backup_file = backup_database()
    if not backup_file:
        print("❌ 无法备份数据库，退出")
        return
    
    # 2. 执行迁移
    if execute_migration():
        # 3. 验证迁移
        if verify_migration():
            print("\n🎉 迁移成功完成！")
            print(f"📁 备份文件: {backup_file}")
            print("\n接下来可以运行:")
            print("   1. 批量回填脚本 (backfill_lexicon.py)")
            print("   2. 测试增强的查词服务")
        else:
            print("\n⚠️ 迁移完成但验证失败，请检查数据")
    else:
        print(f"\n❌ 迁移失败，可从备份恢复: {backup_file}")

if __name__ == "__main__":
    main()
