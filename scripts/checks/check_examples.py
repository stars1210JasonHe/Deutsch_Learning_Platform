#!/usr/bin/env python3
"""
检查数据库中的例句情况
分析为什么UI没有显示例句
"""
import sqlite3
import json

def check_examples_in_database():
    """检查数据库中的例句数据"""
    print("🔍 检查数据库例句状态")
    print("=" * 50)
    
    db_path = 'data/app.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 检查bezahlen的例句
        print("📊 1. 检查'bezahlen'的例句:")
        cursor.execute("""
            SELECT wl.lemma, e.de_text, e.en_text, e.zh_text
            FROM word_lemmas wl
            LEFT JOIN examples e ON e.lemma_id = wl.id
            WHERE wl.lemma = 'bezahlen'
        """)
        
        bezahlen_examples = cursor.fetchall()
        if bezahlen_examples:
            for lemma, de_text, en_text, zh_text in bezahlen_examples:
                if de_text:
                    print(f"   ✅ 找到例句:")
                    print(f"      DE: {de_text}")
                    print(f"      EN: {en_text}")
                    print(f"      ZH: {zh_text}")
                else:
                    print(f"   ❌ {lemma}: 没有例句数据")
        else:
            print("   ❌ bezahlen: 表中没有记录")
        
        # 2. 检查examples表的整体情况
        print(f"\n📊 2. Examples表整体统计:")
        cursor.execute("SELECT COUNT(*) FROM examples")
        total_examples = cursor.fetchone()[0]
        print(f"   总例句数: {total_examples}")
        
        cursor.execute("SELECT COUNT(*) FROM examples WHERE de_text IS NOT NULL AND de_text != ''")
        valid_examples = cursor.fetchone()[0]
        print(f"   有效例句数: {valid_examples}")
        
        # 3. 检查有多少词汇有例句
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT wl.id) as total_words,
                COUNT(DISTINCT CASE WHEN e.de_text IS NOT NULL AND e.de_text != '' THEN wl.id END) as words_with_examples
            FROM word_lemmas wl
            LEFT JOIN examples e ON e.lemma_id = wl.id
        """)
        total_words, words_with_examples = cursor.fetchone()
        coverage = (words_with_examples / total_words * 100) if total_words > 0 else 0
        
        print(f"   总词汇数: {total_words}")
        print(f"   有例句的词汇数: {words_with_examples}")
        print(f"   例句覆盖率: {coverage:.1f}%")
        
        # 4. 检查一些常见词汇的例句情况
        print(f"\n📊 3. 常见词汇例句检查:")
        test_words = ['bezahlen', 'kreuzen', 'sehen', 'Haus', 'arbeiten', 'haben', 'sein']
        
        for word in test_words:
            cursor.execute("""
                SELECT COUNT(*) FROM examples e
                JOIN word_lemmas wl ON wl.id = e.lemma_id
                WHERE wl.lemma = ? AND e.de_text IS NOT NULL AND e.de_text != ''
            """, (word,))
            
            example_count = cursor.fetchone()[0]
            status = "✅" if example_count > 0 else "❌"
            print(f"   {status} {word}: {example_count} 个例句")
        
        # 5. 显示一些实际的例句样本
        print(f"\n📊 4. 例句样本:")
        cursor.execute("""
            SELECT wl.lemma, e.de_text, e.en_text, e.zh_text
            FROM examples e
            JOIN word_lemmas wl ON wl.id = e.lemma_id
            WHERE e.de_text IS NOT NULL AND e.de_text != ''
            LIMIT 3
        """)
        
        samples = cursor.fetchall()
        for lemma, de_text, en_text, zh_text in samples:
            print(f"   📝 {lemma}:")
            print(f"      DE: {de_text}")
            print(f"      EN: {en_text}")
            print(f"      ZH: {zh_text}")
            print()
            
        return {
            'total_examples': total_examples,
            'valid_examples': valid_examples,
            'words_with_examples': words_with_examples,
            'coverage': coverage,
            'bezahlen_has_examples': any(row[1] for row in bezahlen_examples if row[1])
        }
    
    finally:
        conn.close()

def check_api_response_format():
    """检查API响应格式是否包含例句"""
    print("🔍 检查API响应格式")
    print("=" * 30)
    
    # 模拟vocabulary_service的响应格式
    db_path = 'data/app.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT wl.lemma, wl.pos,
                   GROUP_CONCAT(CASE WHEN t.lang_code = 'en' THEN t.text END) as translations_en,
                   GROUP_CONCAT(CASE WHEN t.lang_code = 'zh' THEN t.text END) as translations_zh,
                   e.de_text, e.en_text, e.zh_text
            FROM word_lemmas wl
            LEFT JOIN translations t ON t.lemma_id = wl.id
            LEFT JOIN examples e ON e.lemma_id = wl.id
            WHERE wl.lemma = 'bezahlen'
            GROUP BY wl.id
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            lemma, pos, trans_en, trans_zh, ex_de, ex_en, ex_zh = result
            
            # 构建API响应格式
            api_response = {
                "found": True,
                "original": lemma,
                "pos": pos,
                "translations_en": trans_en.split(',') if trans_en else [],
                "translations_zh": trans_zh.split(',') if trans_zh else [],
                "example": {
                    "de": ex_de,
                    "en": ex_en, 
                    "zh": ex_zh
                } if ex_de else None,
                "cached": True,
                "source": "database"
            }
            
            print(f"📋 API响应格式预览:")
            print(json.dumps(api_response, ensure_ascii=False, indent=2))
            
            has_example = api_response.get('example') is not None
            print(f"\n🎯 有例句: {'✅ Yes' if has_example else '❌ No'}")
            
            return api_response
    
    finally:
        conn.close()

if __name__ == "__main__":
    stats = check_examples_in_database()
    print("\n" + "="*50)
    api_response = check_api_response_format()
    
    print(f"\n🎯 总结:")
    if stats['bezahlen_has_examples']:
        print("✅ bezahlen在数据库中有例句，问题可能在UI显示逻辑")
    else:
        print("❌ bezahlen缺少例句，需要生成")
    
    print(f"📊 整体例句覆盖率: {stats['coverage']:.1f}%")
    if stats['coverage'] < 50:
        print("⚠️  需要大量生成例句")