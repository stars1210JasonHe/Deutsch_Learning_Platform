#!/usr/bin/env python3
"""
直接测试增强词库服务的例句功能
模拟实际API调用，验证例句是否正确返回
"""
import sys
import os
from datetime import datetime
import asyncio

# 添加项目路径
sys.path.append(os.getcwd())

try:
    from app.db.session import SessionLocal
    from app.models.user import User
    from app.services.enhanced_vocabulary_service import EnhancedVocabularyService
    from app.services.vocabulary_service import VocabularyService
except ImportError as e:
    print(f"❌ 无法导入应用模块: {e}")
    print("请确保后端服务正在运行")
    sys.exit(1)

class LiveAPITester:
    """实时API测试器"""
    
    def __init__(self):
        self.enhanced_service = EnhancedVocabularyService()
        self.basic_service = VocabularyService()
        
    async def test_word_with_examples(self, word, service_type="enhanced"):
        """测试带有例句的词汇"""
        print(f"🔍 测试词汇: '{word}' (使用{service_type}服务)")
        print("-" * 50)
        
        db = SessionLocal()
        
        # 使用第一个用户进行测试
        user = db.query(User).first()
        if not user:
            print("❌ 数据库中没有用户")
            return None
            
        print(f"👤 使用用户: {user.email}")
        
        try:
            if service_type == "enhanced":
                result = await self.enhanced_service.get_or_create_word_enhanced(
                    db=db,
                    lemma=word,
                    user=user,
                    force_enrich=False
                )
            else:
                result = await self.basic_service.get_or_create_word(
                    db=db,
                    lemma=word,
                    user=user
                )
            
            print(f"📋 API响应:")
            
            # 关键字段检查
            if result.get('found'):
                print(f"   ✅ 找到词汇: {result.get('original', word)}")
                print(f"   📝 词性: {result.get('pos', 'unknown')}")
                
                # 翻译检查
                trans_en = result.get('translations_en', [])
                trans_zh = result.get('translations_zh', [])
                print(f"   🔤 英文翻译: {trans_en}")
                print(f"   🈯 中文翻译: {trans_zh}")
                
                # 例句检查
                example = result.get('example')
                if example and example.get('de'):
                    print(f"   ✅ 例句:")
                    print(f"      DE: {example.get('de')}")
                    print(f"      EN: {example.get('en')}")
                    print(f"      ZH: {example.get('zh')}")
                else:
                    print(f"   ❌ 没有例句")
                
                # 数据源
                print(f"   📊 数据源: {result.get('source', 'unknown')}")
                print(f"   💾 缓存: {result.get('cached', False)}")
                
                return result
            else:
                print(f"   ❌ 词汇未找到")
                suggestions = result.get('suggestions', [])
                if suggestions:
                    print(f"   💡 建议词汇: {[s.get('word') for s in suggestions[:3]]}")
                return result
                
        except Exception as e:
            print(f"   ❌ 测试失败: {e}")
            import traceback
            print(f"   详细错误: {traceback.format_exc()}")
            return None
            
        finally:
            db.close()
    
    async def test_key_words(self):
        """测试关键词汇"""
        print("🚀 开始实时API测试")
        print("=" * 60)
        print(f"⏰ 测试时间: {datetime.now()}")
        print()
        
        test_words = [
            ("bezahlen", "enhanced"),
            ("bezahlen", "basic"), 
            ("kreuzen", "enhanced"),
            ("kreuzen", "basic")
        ]
        
        results = {}
        
        for word, service_type in test_words:
            result = await self.test_word_with_examples(word, service_type)
            results[f"{word}_{service_type}"] = result
            print()
            
        # 总结报告
        print("📊 测试总结:")
        print("=" * 30)
        
        for key, result in results.items():
            word, service = key.rsplit('_', 1)
            if result and result.get('found'):
                has_example = bool(result.get('example') and result.get('example', {}).get('de'))
                has_translations = bool(result.get('translations_en') or result.get('translations_zh'))
                
                status = "✅" if (has_example and has_translations) else "⚠️"
                print(f"   {status} {word} ({service}): 翻译={has_translations}, 例句={has_example}")
            else:
                print(f"   ❌ {word} ({service}): 未找到")
        
        # 检查UI期望效果
        print(f"\n🎯 UI期望效果:")
        bezahlen_enhanced = results.get('bezahlen_enhanced')
        kreuzen_enhanced = results.get('kreuzen_enhanced')
        
        if bezahlen_enhanced and bezahlen_enhanced.get('found'):
            example = bezahlen_enhanced.get('example', {})
            if example.get('de'):
                print(f"   ✅ 搜索 'bezahlen' 应显示例句: {example.get('de')}")
            else:
                print(f"   ❌ 搜索 'bezahlen' 不会显示例句")
        
        if kreuzen_enhanced and kreuzen_enhanced.get('found'):
            example = kreuzen_enhanced.get('example', {})
            if example.get('de'):
                print(f"   ✅ 搜索 'kreuzen' 应显示例句: {example.get('de')}")
            else:
                print(f"   ❌ 搜索 'kreuzen' 不会显示例句")

async def main():
    """主测试函数"""
    tester = LiveAPITester()
    await tester.test_key_words()

if __name__ == "__main__":
    asyncio.run(main())