#!/usr/bin/env python3
"""
简化的实时测试 - 直接测试数据库查询
模拟API响应格式，验证例句是否正确包含
"""
import sqlite3
import json

def test_api_response_format():
    """测试实际的API响应格式"""
    print("🔍 实时测试: API响应格式")
    print("=" * 50)
    
    db_path = 'data/app.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        test_words = ['bezahlen', 'kreuzen']
        
        for word in test_words:
            print(f"\n📝 测试词汇: '{word}'")
            print("-" * 30)
            
            # 模拟enhanced_vocabulary_service的查询逻辑
            cursor.execute("""
                SELECT wl.id, wl.lemma, wl.pos,
                       GROUP_CONCAT(CASE WHEN t.lang_code = 'en' THEN t.text END) as translations_en,
                       GROUP_CONCAT(CASE WHEN t.lang_code = 'zh' THEN t.text END) as translations_zh,
                       e.de_text, e.en_text, e.zh_text
                FROM word_lemmas wl
                LEFT JOIN translations t ON t.lemma_id = wl.id
                LEFT JOIN examples e ON e.lemma_id = wl.id
                WHERE wl.lemma LIKE ? COLLATE NOCASE
                GROUP BY wl.id
                LIMIT 1
            """, (word,))
            
            result = cursor.fetchone()
            
            if result:
                lemma_id, lemma, pos, trans_en, trans_zh, ex_de, ex_en, ex_zh = result
                
                # 构建模拟的API响应（模仿enhanced_vocabulary_service）
                api_response = {
                    "found": True,
                    "original": word,
                    "lemma": lemma,
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
                
                print("📋 模拟API响应:")
                print(json.dumps(api_response, ensure_ascii=False, indent=2))
                
                # 验证关键功能
                has_translations = bool(api_response["translations_en"] or api_response["translations_zh"])
                has_example = api_response["example"] is not None
                
                print(f"\n🎯 功能验证:")
                print(f"   翻译可用: {'✅' if has_translations else '❌'}")
                print(f"   例句可用: {'✅' if has_example else '❌'}")
                
                if has_example:
                    print(f"   例句内容:")
                    print(f"     DE: {api_response['example']['de']}")
                    print(f"     EN: {api_response['example']['en']}")
                    print(f"     ZH: {api_response['example']['zh']}")
                
                # UI显示预测
                print(f"\n🖥️  UI显示预测:")
                if has_translations and has_example:
                    print("   ✅ WordResult组件将显示完整内容（翻译+例句）")
                    print("   ✅ 不会显示'Translation data is being processed'")
                elif has_translations:
                    print("   ⚠️  WordResult组件将显示翻译，但缺少例句")
                else:
                    print("   ❌ WordResult组件可能显示fallback信息")
                    
            else:
                print(f"❌ 词汇 '{word}' 未在数据库中找到")
        
        # 测试整体状态
        print(f"\n📊 整体状态检查:")
        
        cursor.execute("""
            SELECT COUNT(*) FROM word_lemmas wl
            INNER JOIN translations t ON t.lemma_id = wl.id
            WHERE wl.lemma IN ('bezahlen', 'Kreuzen')
        """)
        words_with_translations = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM word_lemmas wl
            INNER JOIN examples e ON e.lemma_id = wl.id
            WHERE wl.lemma IN ('bezahlen', 'Kreuzen')
              AND e.de_text IS NOT NULL
        """)
        words_with_examples = cursor.fetchone()[0]
        
        print(f"   关键词汇有翻译: {words_with_translations}/2")
        print(f"   关键词汇有例句: {words_with_examples}/2")
        
        if words_with_translations == 2 and words_with_examples == 2:
            print(f"\n🎉 状态: 优秀！所有关键功能都可用")
            print(f"🚀 用户搜索应该能看到完整的翻译和例句")
        elif words_with_translations == 2:
            print(f"\n⚠️  状态: 翻译可用，但例句可能不完整")
        else:
            print(f"\n❌ 状态: 数据不完整，需要修复")
            
        # 具体的用户体验预测
        print(f"\n👤 用户体验预测:")
        print(f"1. 用户搜索 'bezahlen':")
        
        cursor.execute("""
            SELECT wl.lemma, e.de_text FROM word_lemmas wl
            LEFT JOIN examples e ON e.lemma_id = wl.id
            WHERE wl.lemma LIKE 'bezahlen' COLLATE NOCASE
            LIMIT 1
        """)
        bezahlen_result = cursor.fetchone()
        
        if bezahlen_result and bezahlen_result[1]:
            print(f"   ✅ 应该看到例句: '{bezahlen_result[1]}'")
        else:
            print(f"   ❌ 不会看到例句")
            
        print(f"2. 用户搜索 'kreuzen':")
        
        cursor.execute("""
            SELECT wl.lemma, e.de_text FROM word_lemmas wl
            LEFT JOIN examples e ON e.lemma_id = wl.id
            WHERE wl.lemma LIKE '%kreuzen%' COLLATE NOCASE
            LIMIT 1
        """)
        kreuzen_result = cursor.fetchone()
        
        if kreuzen_result and kreuzen_result[1]:
            print(f"   ✅ 应该看到例句: '{kreuzen_result[1]}'")
        else:
            print(f"   ❌ 不会看到例句")
            
    finally:
        conn.close()

def test_server_is_running():
    """检查服务器是否在运行"""
    print("🔍 检查服务器状态:")
    
    import subprocess
    import socket
    
    # 检查端口8000是否被占用
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()
    
    if result == 0:
        print("   ✅ 端口8000可访问，服务器运行中")
        
        # 尝试基本的健康检查
        try:
            import urllib.request
            with urllib.request.urlopen('http://localhost:8000/docs', timeout=5) as response:
                if response.getcode() == 200:
                    print("   ✅ API文档可访问 (http://localhost:8000/docs)")
                    print("   💡 后端服务正常运行，前端可以连接")
        except Exception as e:
            print(f"   ⚠️  API访问测试失败: {e}")
    else:
        print("   ❌ 端口8000不可访问，服务器可能未运行")

if __name__ == "__main__":
    print("🧪 简化实时测试")
    print("=" * 60)
    
    test_server_is_running()
    print()
    test_api_response_format()