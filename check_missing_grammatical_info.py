#!/usr/bin/env python3
"""
检查数据库中缺少的语法信息
- 名词: 冠词(articles), 复数(plurals)
- 动词: 变位表(conjugation tables)
"""
import sqlite3
from datetime import datetime

def check_grammatical_completeness():
    """检查语法信息完整性"""
    print("🔍 语法信息完整性检查")
    print("=" * 60)
    print(f"⏰ 检查时间: {datetime.now()}")
    print()
    
    conn = sqlite3.connect('data/app.db')
    cursor = conn.cursor()
    
    try:
        # 1. 统计总数
        cursor.execute("SELECT COUNT(*) FROM word_lemmas WHERE pos = 'noun'")
        total_nouns = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM word_lemmas WHERE pos = 'verb'")
        total_verbs = cursor.fetchone()[0]
        
        print(f"📊 总体统计:")
        print(f"   名词总数: {total_nouns}")
        print(f"   动词总数: {total_verbs}")
        
        # 2. 检查名词冠词
        cursor.execute("""
            SELECT COUNT(*) FROM word_lemmas 
            WHERE pos = 'noun' 
            AND (notes IS NULL OR notes NOT LIKE '%article:%')
        """)
        nouns_missing_articles = cursor.fetchone()[0]
        
        print(f"\n🔍 名词冠词检查:")
        print(f"   缺少冠词: {nouns_missing_articles}/{total_nouns} ({nouns_missing_articles/total_nouns*100:.1f}%)")
        
        # 3. 检查名词复数 (目前可能没有存储)
        # 假设复数信息存储在notes中作为 "plural:单词s"
        cursor.execute("""
            SELECT COUNT(*) FROM word_lemmas 
            WHERE pos = 'noun' 
            AND (notes IS NULL OR notes NOT LIKE '%plural:%')
        """)
        nouns_missing_plurals = cursor.fetchone()[0]
        
        print(f"   缺少复数: {nouns_missing_plurals}/{total_nouns} ({nouns_missing_plurals/total_nouns*100:.1f}%)")
        
        # 4. 检查动词变位
        cursor.execute("""
            SELECT COUNT(DISTINCT lemma_id) FROM word_forms 
            WHERE lemma_id IN (SELECT id FROM word_lemmas WHERE pos = 'verb')
        """)
        verbs_with_forms = cursor.fetchone()[0]
        verbs_missing_forms = total_verbs - verbs_with_forms
        
        print(f"\n🔍 动词变位检查:")
        print(f"   有变位表: {verbs_with_forms}/{total_verbs} ({verbs_with_forms/total_verbs*100:.1f}%)")
        print(f"   缺少变位: {verbs_missing_forms}/{total_verbs} ({verbs_missing_forms/total_verbs*100:.1f}%)")
        
        # 5. 检查动词变位完整性 (应该有现在时的6种人称)
        cursor.execute("""
            SELECT wl.lemma, COUNT(wf.id) as form_count
            FROM word_lemmas wl
            LEFT JOIN word_forms wf ON wf.lemma_id = wl.id AND wf.feature_value LIKE 'praesens_%'
            WHERE wl.pos = 'verb'
            GROUP BY wl.id
            HAVING form_count < 6
            ORDER BY form_count DESC
            LIMIT 10
        """)
        incomplete_verb_conjugations = cursor.fetchall()
        
        print(f"   不完整变位示例:")
        for lemma, count in incomplete_verb_conjugations:
            print(f"     • {lemma}: {count}/6 现在时人称")
        
        # 6. 样本检查 - 显示完整的条目
        print(f"\n📝 完整条目样本:")
        
        # 完整的名词例子
        cursor.execute("""
            SELECT wl.lemma, wl.notes 
            FROM word_lemmas wl
            WHERE wl.pos = 'noun' 
            AND wl.notes LIKE '%article:%'
            LIMIT 3
        """)
        complete_nouns = cursor.fetchall()
        
        print(f"   完整名词:")
        for lemma, notes in complete_nouns:
            article = extract_from_notes(notes, 'article')
            plural = extract_from_notes(notes, 'plural') 
            print(f"     • {lemma}: {article} {lemma}" + (f", 复数: {plural}" if plural else ""))
        
        # 完整的动词例子
        cursor.execute("""
            SELECT wl.lemma, COUNT(wf.id) as forms
            FROM word_lemmas wl
            JOIN word_forms wf ON wf.lemma_id = wl.id
            WHERE wl.pos = 'verb'
            GROUP BY wl.id
            HAVING forms >= 6
            LIMIT 3
        """)
        complete_verbs = cursor.fetchall()
        
        print(f"   完整动词:")
        for lemma, form_count in complete_verbs:
            print(f"     • {lemma}: {form_count} 个变位形式")
            
            # 显示现在时变位
            cursor.execute("""
                SELECT feature_value, form FROM word_forms 
                WHERE lemma_id = (SELECT id FROM word_lemmas WHERE lemma = ?) 
                AND feature_value LIKE 'praesens_%'
                ORDER BY 
                    CASE feature_value
                        WHEN 'praesens_ich' THEN 1
                        WHEN 'praesens_du' THEN 2  
                        WHEN 'praesens_er_sie_es' THEN 3
                        WHEN 'praesens_wir' THEN 4
                        WHEN 'praesens_ihr' THEN 5
                        WHEN 'praesens_sie_Sie' THEN 6
                    END
            """, (lemma,))
            
            forms = cursor.fetchall()
            if forms:
                print(f"       现在时: ", end="")
                form_strs = []
                for feature, form in forms:
                    person = feature.replace('praesens_', '')
                    form_strs.append(f"{person}:{form}")
                print(", ".join(form_strs))
        
        # 7. 优先修复建议
        print(f"\n🎯 修复优先级建议:")
        
        # 高频或A1/A2级别的缺失项
        cursor.execute("""
            SELECT lemma, pos, cefr, frequency, notes
            FROM word_lemmas 
            WHERE pos IN ('noun', 'verb')
            AND (
                (pos = 'noun' AND (notes IS NULL OR notes NOT LIKE '%article:%'))
                OR (pos = 'verb' AND id NOT IN (SELECT DISTINCT lemma_id FROM word_forms))
            )
            AND (cefr IN ('A1', 'A2') OR frequency IS NOT NULL)
            ORDER BY 
                CASE WHEN cefr IN ('A1', 'A2') THEN 1 ELSE 2 END,
                frequency DESC NULLS LAST
            LIMIT 15
        """)
        
        priority_fixes = cursor.fetchall()
        print(f"   高优先级修复 (A1/A2或高频词):")
        for lemma, pos, cefr, freq, notes in priority_fixes:
            missing = []
            if pos == 'noun' and (not notes or 'article:' not in notes):
                missing.append('冠词')
            if pos == 'noun' and (not notes or 'plural:' not in notes):
                missing.append('复数')
            if pos == 'verb':
                # 检查是否有变位
                cursor.execute("SELECT COUNT(*) FROM word_forms WHERE lemma_id = (SELECT id FROM word_lemmas WHERE lemma = ?)", (lemma,))
                if cursor.fetchone()[0] == 0:
                    missing.append('变位')
            
            cefr_str = f" [{cefr}]" if cefr else ""
            freq_str = f" (频率:{freq})" if freq else ""
            print(f"     • {lemma} ({pos}){cefr_str}{freq_str} - 缺少: {'/'.join(missing)}")
            
    finally:
        conn.close()

def extract_from_notes(notes, key):
    """从notes中提取信息"""
    if not notes or f"{key}:" not in notes:
        return None
    
    part = notes.split(f"{key}:")[1].strip()
    value = part.split()[0] if part else ""
    return value if value else None

def check_ui_display_capability():
    """检查UI显示能力"""
    print(f"\n🖥️  UI显示能力检查:")
    print("=" * 40)
    
    # 检查WordResult组件
    try:
        with open('/mnt/e/LanguageLearning/frontend/src/components/WordResult.vue', 'r') as f:
            content = f.read()
            
        # 检查是否显示冠词
        has_article_display = 'article' in content.lower()
        print(f"   显示冠词: {'✅' if has_article_display else '❌'}")
        
        # 检查是否显示复数
        has_plural_display = 'plural' in content.lower()
        print(f"   显示复数: {'✅' if has_plural_display else '❌'}")
        
        # 检查是否显示动词变位表
        has_conjugation_display = 'tables' in content and 'praesens' in content
        print(f"   显示动词变位: {'✅' if has_conjugation_display else '❌'}")
        
        if not (has_article_display and has_plural_display and has_conjugation_display):
            print(f"\n   ⚠️  需要更新UI组件以显示完整语法信息")
            
    except Exception as e:
        print(f"   ❌ 无法检查UI文件: {e}")

if __name__ == "__main__":
    check_grammatical_completeness()
    check_ui_display_capability()
    
    print(f"\n📋 总结:")
    print("1. 数据库部分支持语法信息存储")
    print("2. 需要补充缺失的冠词、复数和动词变位")
    print("3. 需要更新UI以显示这些信息")
    print("4. 后端API已支持返回这些数据")