#!/usr/bin/env python3
"""
测试大小写不敏感的词汇查找
"""
import sqlite3

def test_case_insensitive_search():
    """测试大小写不敏感搜索功能"""
    print("🔍 测试大小写不敏感搜索")
    print("=" * 40)
    
    db_path = 'data/app.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 测试用例：小写搜索，应该找到大写的记录
        test_cases = [
            ('bezahlen', 'bezahlen'),  # 直接匹配
            ('kreuzen', 'Kreuzen'),    # 大小写匹配
            ('Bezahlen', 'bezahlen'),  # 反向匹配
            ('KREUZEN', 'Kreuzen'),    # 全大写匹配
        ]
        
        for search_term, expected_lemma in test_cases:
            print(f"\n📝 搜索: '{search_term}' (期望找到: '{expected_lemma}')")
            
            # 使用LIKE进行大小写不敏感搜索
            cursor.execute("""
                SELECT wl.lemma, wl.pos,
                       GROUP_CONCAT(CASE WHEN t.lang_code = 'en' THEN t.text END) as translations_en,
                       GROUP_CONCAT(CASE WHEN t.lang_code = 'zh' THEN t.text END) as translations_zh,
                       e.de_text, e.en_text, e.zh_text
                FROM word_lemmas wl
                LEFT JOIN translations t ON t.lemma_id = wl.id
                LEFT JOIN examples e ON e.lemma_id = wl.id
                WHERE wl.lemma LIKE ? COLLATE NOCASE
                GROUP BY wl.id
                LIMIT 1
            """, (search_term,))
            
            result = cursor.fetchone()
            if result:
                lemma, pos, trans_en, trans_zh, ex_de, ex_en, ex_zh = result
                print(f"   ✅ 找到: {lemma} ({pos})")
                print(f"      翻译EN: {trans_en}")
                print(f"      翻译ZH: {trans_zh}")
                if ex_de:
                    print(f"      例句DE: {ex_de}")
                    print(f"      例句EN: {ex_en}")
                    print(f"      例句ZH: {ex_zh}")
                else:
                    print(f"      例句: 无")
                
                # 验证搜索结果
                if lemma.lower() == expected_lemma.lower():
                    print(f"   ✅ 搜索成功匹配期望结果")
                else:
                    print(f"   ⚠️  搜索结果与期望不符")
            else:
                print(f"   ❌ 未找到匹配结果")
        
        # 测试API响应格式
        print(f"\n🎯 模拟API响应格式测试:")
        for search_term, expected_lemma in [('kreuzen', 'Kreuzen')]:
            cursor.execute("""
                SELECT wl.lemma, wl.pos,
                       GROUP_CONCAT(CASE WHEN t.lang_code = 'en' THEN t.text END) as translations_en,
                       GROUP_CONCAT(CASE WHEN t.lang_code = 'zh' THEN t.text END) as translations_zh,
                       e.de_text, e.en_text, e.zh_text
                FROM word_lemmas wl
                LEFT JOIN translations t ON t.lemma_id = wl.id
                LEFT JOIN examples e ON e.lemma_id = wl.id
                WHERE wl.lemma LIKE ? COLLATE NOCASE
                GROUP BY wl.id
                LIMIT 1
            """, (search_term,))
            
            result = cursor.fetchone()
            if result:
                lemma, pos, trans_en, trans_zh, ex_de, ex_en, ex_zh = result
                
                # 构建预期的API响应
                api_response = {
                    "found": True,
                    "original": search_term,  # 用户搜索的原始词
                    "lemma": lemma,          # 数据库中的标准形式
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
                
                print(f"\n   API响应格式预览 (搜索 '{search_term}'):")
                import json
                print(json.dumps(api_response, ensure_ascii=False, indent=4))
                
                # 验证关键字段
                has_translations = len(api_response["translations_en"]) > 0 or len(api_response["translations_zh"]) > 0
                has_example = api_response["example"] is not None
                
                print(f"\n   🎯 字段验证:")
                print(f"      有翻译: {'✅' if has_translations else '❌'}")
                print(f"      有例句: {'✅' if has_example else '❌'}")
                print(f"      UI应该显示: {'✅ 完整内容' if has_translations and has_example else '⚠️ 部分内容'}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    test_case_insensitive_search()