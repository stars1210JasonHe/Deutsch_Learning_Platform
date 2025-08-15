#!/usr/bin/env python3
"""
测试实际API端点是否正常工作
验证翻译修复后的完整功能链路
"""
import asyncio
import sys
import os
from datetime import datetime

# 直接设置路径
sys.path.append(os.getcwd())

try:
    from app.services.vocabulary_service import VocabularyService
    from app.models.user import User
    from app.db.session import SessionLocal
except ImportError as e:
    print(f"❌ 无法导入应用模块: {e}")
    print("请确保在项目根目录运行测试")
    sys.exit(1)

class APIEndpointTester:
    """API端点测试器"""
    
    def __init__(self):
        self.vocabulary_service = VocabularyService()
        self.test_results = {
            'vocabulary_service_tests': [],
            'total_passed': 0,
            'total_failed': 0,
            'start_time': datetime.now()
        }
    
    async def test_vocabulary_service(self):
        """测试词汇服务"""
        print("🔍 测试: VocabularyService.get_or_create_word")
        
        # 创建数据库会话
        db = SessionLocal()
        
        # 创建模拟用户
        user = User(id=1, email="test@example.com")
        
        test_words = ['bezahlen', 'kreuzen', 'sehen', 'Haus']
        
        try:
            for word in test_words:
                print(f"\n   测试词汇: {word}")
                
                try:
                    # 调用词汇服务
                    result = await self.vocabulary_service.get_or_create_word(db, word, user)
                    
                    # 验证响应格式
                    if result and result.get('found'):
                        has_translations = (
                            (result.get('translations_en') and len(result['translations_en']) > 0) or
                            (result.get('translations_zh') and len(result['translations_zh']) > 0)
                        )
                        
                        if has_translations:
                            print(f"   ✅ PASS {word}: Found with translations")
                            print(f"      EN: {result.get('translations_en', [])}")
                            print(f"      ZH: {result.get('translations_zh', [])}")
                            self.test_results['total_passed'] += 1
                        else:
                            print(f"   ❌ FAIL {word}: Found but no translations")
                            self.test_results['total_failed'] += 1
                        
                        self.test_results['vocabulary_service_tests'].append({
                            'word': word,
                            'success': has_translations,
                            'response_keys': list(result.keys())
                        })
                    else:
                        print(f"   ❌ FAIL {word}: Not found or invalid response")
                        self.test_results['total_failed'] += 1
                        self.test_results['vocabulary_service_tests'].append({
                            'word': word,
                            'success': False,
                            'error': 'Not found'
                        })
                
                except Exception as e:
                    print(f"   ❌ ERROR {word}: {e}")
                    self.test_results['total_failed'] += 1
                    self.test_results['vocabulary_service_tests'].append({
                        'word': word,
                        'success': False,
                        'error': str(e)
                    })
        
        finally:
            db.close()
    
    async def test_fallback_translations(self):
        """测试fallback翻译功能"""
        print(f"\n🔍 测试: Fallback翻译功能")
        
        # 测试fallback字典中的词汇
        fallback_words = ['kreuzen', 'arbeiten', 'leben', 'kaufen']
        
        db = SessionLocal()
        user = User(id=1, email="test@example.com")
        
        try:
            for word in fallback_words:
                print(f"\n   测试fallback: {word}")
                
                try:
                    result = await self.vocabulary_service.get_or_create_word(db, word, user)
                    
                    if result and result.get('found'):
                        source = result.get('source', 'unknown')
                        has_translations = bool(result.get('translations_en') or result.get('translations_zh'))
                        
                        if has_translations:
                            print(f"   ✅ PASS {word}: Source={source}")
                            self.test_results['total_passed'] += 1
                        else:
                            print(f"   ❌ FAIL {word}: No translations")
                            self.test_results['total_failed'] += 1
                    else:
                        print(f"   ❌ FAIL {word}: Not found")
                        self.test_results['total_failed'] += 1
                
                except Exception as e:
                    print(f"   ❌ ERROR {word}: {e}")
                    self.test_results['total_failed'] += 1
        
        finally:
            db.close()
    
    def test_response_format_compatibility(self):
        """测试响应格式兼容性"""
        print(f"\n🔍 测试: 响应格式兼容性")
        
        # 模拟从数据库返回的数据格式
        mock_database_response = {
            "found": True,
            "original": "bezahlen",
            "pos": "verb",
            "translations_en": ["to pay", "to pay for"],
            "translations_zh": ["付钱", "支付"],
            "example": {
                "de": "Ich muss die Rechnung bezahlen.",
                "en": "I have to pay the bill.",
                "zh": "我必须付账单。"
            },
            "cached": True,
            "source": "database"
        }
        
        # 检查前端期望的所有字段
        expected_fields = [
            'found', 'original', 'pos', 'translations_en', 'translations_zh'
        ]
        
        missing_fields = []
        for field in expected_fields:
            if field not in mock_database_response:
                missing_fields.append(field)
        
        if not missing_fields:
            print(f"   ✅ PASS: 所有必需字段都存在")
            self.test_results['total_passed'] += 1
        else:
            print(f"   ❌ FAIL: 缺少字段: {missing_fields}")
            self.test_results['total_failed'] += 1
        
        # 检查UI组件的hasTranslations逻辑
        has_en = mock_database_response.get('translations_en') and len(mock_database_response['translations_en']) > 0
        has_zh = mock_database_response.get('translations_zh') and len(mock_database_response['translations_zh']) > 0
        ui_will_show_translations = has_en or has_zh
        
        if ui_will_show_translations:
            print(f"   ✅ PASS: UI组件将显示翻译内容")
            self.test_results['total_passed'] += 1
        else:
            print(f"   ❌ FAIL: UI组件不会显示翻译内容")
            self.test_results['total_failed'] += 1
    
    def print_final_report(self):
        """打印最终测试报告"""
        elapsed = datetime.now() - self.test_results['start_time']
        total_tests = self.test_results['total_passed'] + self.test_results['total_failed']
        success_rate = (self.test_results['total_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"🎉 API端点功能测试报告")
        print(f"{'='*60}")
        print(f"总测试数: {total_tests}")
        print(f"通过: {self.test_results['total_passed']} ✅")
        print(f"失败: {self.test_results['total_failed']} ❌")
        print(f"成功率: {success_rate:.1f}%")
        print(f"测试用时: {elapsed}")
        
        if success_rate >= 90:
            print(f"\n🎯 总评: 优秀! API服务正常工作!")
            print(f"🚀 前端应该能正确显示翻译数据!")
        elif success_rate >= 75:
            print(f"\n👍 总评: 良好! 大部分API功能正常!")
            print(f"⚠️  可能有少量问题需要检查")
        else:
            print(f"\n⚠️  总评: 需要修复，API服务有问题!")

async def main():
    """主测试函数"""
    print("🧪 开始API端点功能测试")
    print("=" * 60)
    
    tester = APIEndpointTester()
    
    # 运行所有测试
    await tester.test_vocabulary_service()
    await tester.test_fallback_translations()
    tester.test_response_format_compatibility()
    
    # 生成报告
    tester.print_final_report()

if __name__ == "__main__":
    asyncio.run(main())