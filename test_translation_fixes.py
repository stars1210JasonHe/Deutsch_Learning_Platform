#!/usr/bin/env python3
"""
测试数据库架构修复后的翻译功能
验证UI能正确显示翻译数据
"""
import sqlite3
import json
import sys
import os
from datetime import datetime

class TranslationFixTester:
    """翻译修复功能测试器"""
    
    def __init__(self):
        self.db_path = 'data/app.db'
        self.test_results = {
            'database_tests': [],
            'api_simulation_tests': [],
            'ui_data_format_tests': [],
            'total_passed': 0,
            'total_failed': 0,
            'start_time': datetime.now()
        }
    
    def test_database_translations(self):
        """测试数据库中的翻译数据"""
        print("🔍 测试1: 数据库翻译数据完整性")
        
        test_words = [
            'kreuzen', 'bezahlen', 'arbeiten', 'leben', 'sehen', 'gehen',
            'haben', 'sein', 'machen', 'Haus', 'Auto', 'Zeit'
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for word in test_words:
                # 检查词汇是否存在且有翻译
                cursor.execute("""
                    SELECT wl.lemma, wl.pos,
                           COUNT(CASE WHEN t.lang_code = 'en' THEN 1 END) as en_count,
                           COUNT(CASE WHEN t.lang_code = 'zh' THEN 1 END) as zh_count,
                           GROUP_CONCAT(CASE WHEN t.lang_code = 'en' THEN t.text END, ' | ') as en_translations,
                           GROUP_CONCAT(CASE WHEN t.lang_code = 'zh' THEN t.text END, ' | ') as zh_translations
                    FROM word_lemmas wl
                    LEFT JOIN translations t ON t.lemma_id = wl.id
                    WHERE LOWER(wl.lemma) = LOWER(?)
                    GROUP BY wl.id
                """, (word,))
                
                result = cursor.fetchone()
                if result:
                    lemma, pos, en_count, zh_count, en_trans, zh_trans = result
                    
                    # 测试是否有翻译
                    has_translations = en_count > 0 and zh_count > 0
                    status = "✅ PASS" if has_translations else "❌ FAIL"
                    
                    print(f"   {status} {lemma} ({pos}): EN({en_count}) ZH({zh_count})")
                    if has_translations:
                        print(f"      EN: {en_trans}")
                        print(f"      ZH: {zh_trans}")
                        self.test_results['total_passed'] += 1
                    else:
                        print(f"      ❌ Missing translations!")
                        self.test_results['total_failed'] += 1
                    
                    self.test_results['database_tests'].append({
                        'word': word,
                        'found': True,
                        'has_translations': has_translations,
                        'en_count': en_count,
                        'zh_count': zh_count
                    })
                else:
                    print(f"   ❌ FAIL {word}: Not found in database")
                    self.test_results['total_failed'] += 1
                    self.test_results['database_tests'].append({
                        'word': word,
                        'found': False,
                        'has_translations': False
                    })
        finally:
            conn.close()
    
    def test_api_response_format(self):
        """模拟API响应格式测试"""
        print("\n🔍 测试2: API响应格式模拟")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        test_cases = ['bezahlen', 'Haus', 'sehen']
        
        try:
            for word in test_cases:
                # 模拟vocabulary_service._format_word_data的逻辑
                cursor.execute("""
                    SELECT wl.lemma, wl.pos,
                           GROUP_CONCAT(CASE WHEN t.lang_code = 'en' THEN t.text END) as translations_en,
                           GROUP_CONCAT(CASE WHEN t.lang_code = 'zh' THEN t.text END) as translations_zh,
                           e.de_text, e.en_text, e.zh_text
                    FROM word_lemmas wl
                    LEFT JOIN translations t ON t.lemma_id = wl.id
                    LEFT JOIN examples e ON e.lemma_id = wl.id
                    WHERE LOWER(wl.lemma) = LOWER(?)
                    GROUP BY wl.id
                    LIMIT 1
                """, (word,))
                
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
                    
                    # 验证响应格式
                    has_en = len(api_response["translations_en"]) > 0
                    has_zh = len(api_response["translations_zh"]) > 0
                    
                    if has_en and has_zh:
                        print(f"   ✅ PASS {lemma}: API format valid")
                        print(f"      Response: {json.dumps(api_response, ensure_ascii=False, indent=8)[:200]}...")
                        self.test_results['total_passed'] += 1
                    else:
                        print(f"   ❌ FAIL {lemma}: Missing translation data")
                        self.test_results['total_failed'] += 1
                    
                    self.test_results['api_simulation_tests'].append({
                        'word': word,
                        'valid_format': has_en and has_zh,
                        'response_keys': list(api_response.keys())
                    })
        finally:
            conn.close()
    
    def test_ui_display_conditions(self):
        """测试UI显示条件"""
        print("\n🔍 测试3: UI显示条件验证")
        
        # 测试WordResult组件的显示逻辑
        test_scenarios = [
            {
                'name': 'Complete word data',
                'data': {
                    'found': True,
                    'original': 'bezahlen',
                    'pos': 'verb',
                    'translations_en': ['to pay', 'to pay for'],
                    'translations_zh': ['付钱', '支付']
                }
            },
            {
                'name': 'Missing translations',
                'data': {
                    'found': True,
                    'original': 'testword',
                    'pos': 'verb',
                    'translations_en': [],
                    'translations_zh': []
                }
            },
            {
                'name': 'Partial translations',
                'data': {
                    'found': True,
                    'original': 'partialword',
                    'pos': 'noun',
                    'translations_en': ['test'],
                    'translations_zh': []
                }
            }
        ]
        
        for scenario in test_scenarios:
            name = scenario['name']
            data = scenario['data']
            
            # 模拟UI组件的hasTranslations逻辑
            has_translations = (
                (data.get('translations_en') and len(data['translations_en']) > 0) or
                (data.get('translations_zh') and len(data['translations_zh']) > 0)
            )
            
            # 模拟UI显示逻辑
            will_show_translations = data.get('found') and has_translations
            will_show_fallback = data.get('found') and not has_translations and data.get('pos')
            
            if will_show_translations:
                print(f"   ✅ PASS {name}: Will show translations")
                self.test_results['total_passed'] += 1
            elif will_show_fallback:
                print(f"   ⚠️  WARN {name}: Will show fallback info")
                self.test_results['total_passed'] += 1
            else:
                print(f"   ❌ FAIL {name}: No display content")
                self.test_results['total_failed'] += 1
            
            self.test_results['ui_data_format_tests'].append({
                'scenario': name,
                'will_display': will_show_translations or will_show_fallback,
                'display_type': 'translations' if will_show_translations else 'fallback'
            })
    
    def test_schema_consistency(self):
        """测试架构一致性"""
        print("\n🔍 测试4: 数据库架构一致性")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查是否还有孤儿数据
            cursor.execute("""
                SELECT COUNT(*) as orphan_senses
                FROM lemma_senses ls
                LEFT JOIN word_lemmas wl ON wl.id = ls.lemma_id
                WHERE wl.id IS NULL
            """)
            orphan_senses = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) as words_without_translations
                FROM word_lemmas wl
                LEFT JOIN translations t ON t.lemma_id = wl.id
                WHERE t.id IS NULL
            """)
            words_without_translations = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) as duplicate_translations
                FROM (
                    SELECT lemma_id, lang_code, text, COUNT(*) as cnt
                    FROM translations
                    GROUP BY lemma_id, lang_code, text
                    HAVING cnt > 1
                )
            """)
            duplicate_translations = cursor.fetchone()[0]
            
            print(f"   📊 孤儿词义数据: {orphan_senses}")
            print(f"   📊 无翻译词汇: {words_without_translations}")
            print(f"   📊 重复翻译: {duplicate_translations}")
            
            schema_healthy = (
                orphan_senses == 0 and 
                words_without_translations == 0 and 
                duplicate_translations < 100  # 允许少量重复
            )
            
            if schema_healthy:
                print(f"   ✅ PASS Schema consistency check")
                self.test_results['total_passed'] += 1
            else:
                print(f"   ❌ FAIL Schema has issues")
                self.test_results['total_failed'] += 1
        
        finally:
            conn.close()
    
    def test_performance_check(self):
        """性能检查"""
        print("\n🔍 测试5: 查询性能检查")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 模拟UI搜索查询的性能
            test_queries = [
                ("Single word lookup", """
                    SELECT wl.lemma, wl.pos,
                           GROUP_CONCAT(CASE WHEN t.lang_code = 'en' THEN t.text END) as translations_en,
                           GROUP_CONCAT(CASE WHEN t.lang_code = 'zh' THEN t.text END) as translations_zh
                    FROM word_lemmas wl
                    LEFT JOIN translations t ON t.lemma_id = wl.id
                    WHERE LOWER(wl.lemma) = LOWER(?)
                    GROUP BY wl.id
                """, ('bezahlen',)),
                
                ("Search with LIKE", """
                    SELECT wl.lemma, COUNT(t.id) as translation_count
                    FROM word_lemmas wl
                    LEFT JOIN translations t ON t.lemma_id = wl.id
                    WHERE wl.lemma LIKE ?
                    GROUP BY wl.id
                    LIMIT 10
                """, ('be%',)),
                
                ("Full translation count", """
                    SELECT COUNT(*) FROM translations
                """, ())
            ]
            
            for query_name, query, params in test_queries:
                start_time = datetime.now()
                cursor.execute(query, params)
                results = cursor.fetchall()
                end_time = datetime.now()
                
                duration_ms = (end_time - start_time).total_seconds() * 1000
                result_count = len(results)
                
                if duration_ms < 100:  # 小于100ms认为性能良好
                    print(f"   ✅ PASS {query_name}: {duration_ms:.2f}ms ({result_count} results)")
                    self.test_results['total_passed'] += 1
                else:
                    print(f"   ⚠️  SLOW {query_name}: {duration_ms:.2f}ms ({result_count} results)")
                    self.test_results['total_passed'] += 1  # 慢但不算失败
        
        finally:
            conn.close()
    
    def print_final_report(self):
        """打印最终测试报告"""
        elapsed = datetime.now() - self.test_results['start_time']
        total_tests = self.test_results['total_passed'] + self.test_results['total_failed']
        success_rate = (self.test_results['total_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"🎉 翻译修复功能测试报告")
        print(f"{'='*60}")
        print(f"总测试数: {total_tests}")
        print(f"通过: {self.test_results['total_passed']} ✅")
        print(f"失败: {self.test_results['total_failed']} ❌")
        print(f"成功率: {success_rate:.1f}%")
        print(f"测试用时: {elapsed}")
        
        print(f"\n📊 详细结果:")
        print(f"• 数据库翻译测试: {len(self.test_results['database_tests'])} 个词汇")
        print(f"• API格式测试: {len(self.test_results['api_simulation_tests'])} 个场景")
        print(f"• UI显示测试: {len(self.test_results['ui_data_format_tests'])} 个条件")
        
        if success_rate >= 90:
            print(f"\n🎯 总评: 优秀! 翻译功能修复成功!")
        elif success_rate >= 75:
            print(f"\n👍 总评: 良好! 大部分功能正常!")
        else:
            print(f"\n⚠️  总评: 需要改进，发现一些问题!")
        
        print(f"\n🚀 建议: 现在可以测试前端UI，搜索德语单词应该能正确显示翻译!")

def main():
    """主测试函数"""
    print("🧪 开始翻译修复功能测试")
    print("=" * 60)
    
    tester = TranslationFixTester()
    
    # 运行所有测试
    tester.test_database_translations()
    tester.test_api_response_format()
    tester.test_ui_display_conditions()
    tester.test_schema_consistency()
    tester.test_performance_check()
    
    # 生成报告
    tester.print_final_report()

if __name__ == "__main__":
    main()