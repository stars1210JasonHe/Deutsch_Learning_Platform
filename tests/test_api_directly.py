#!/usr/bin/env python3
"""
直接测试API端点，避免SQLAlchemy关系问题
测试OpenAI功能：非数据库词汇和非德语词汇建议
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.getcwd())

try:
    from app.services.openai_service import OpenAIService
    from app.core.config import settings
except ImportError as e:
    print(f"❌ 无法导入应用模块: {e}")
    sys.exit(1)

class DirectAPITester:
    """直接API测试器"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    def check_openai_config(self):
        """检查OpenAI配置"""
        print("🔍 检查OpenAI配置")
        print("=" * 30)
        
        if not self.openai_service.client:
            print("   ❌ OpenAI客户端未初始化")
            return False
        
        print("   ✅ OpenAI客户端已初始化")
        print(f"   🤖 模型: {self.openai_service.model}")
        print(f"   🌐 API地址: {settings.openai_base_url}")
        print(f"   🔑 API密钥: {'已配置' if settings.openai_api_key else '未配置'}")
        
        return bool(settings.openai_api_key)
    
    async def test_non_german_words(self):
        """测试非德语单词建议功能"""
        print("🔍 测试1: 非德语单词建议功能")
        print("=" * 50)
        
        test_words = [
            "hello",      # 英语问候语
            "computer",   # 英语技术词汇
            "pizza",      # 意大利语（国际通用）
            "bonjour",    # 法语问候语
            "12345",      # 数字（非词汇）
        ]
        
        for word in test_words:
            print(f"\n📝 测试词汇: '{word}'")
            
            try:
                result = await self.openai_service.analyze_word(word)
                
                print(f"   📊 OpenAI分析结果:")
                print(f"      识别为德语词汇: {'✅ Yes' if result.get('found') else '❌ No'}")
                
                if not result.get('found'):
                    # 测试建议功能
                    suggestions = result.get('suggestions', [])
                    message = result.get('message', '')
                    
                    print(f"      建议词汇数量: {len(suggestions)}")
                    print(f"      消息: {message}")
                    
                    if suggestions:
                        print(f"      具体建议:")
                        for i, suggestion in enumerate(suggestions[:5], 1):
                            word_text = suggestion.get('word', 'N/A')
                            pos = suggestion.get('pos', 'N/A') 
                            meaning = suggestion.get('meaning', 'N/A')
                            print(f"        {i}. {word_text} ({pos}) - {meaning}")
                        
                        if len(suggestions) >= 5:
                            print(f"      ✅ 建议数量充足 ({len(suggestions)} ≥ 5)")
                        else:
                            print(f"      ⚠️  建议数量不足 ({len(suggestions)} < 5)")
                    else:
                        print(f"      ❌ 未返回建议词汇")
                else:
                    print(f"      ⚠️  意外识别为德语词汇")
                    print(f"         词性: {result.get('pos')}")
                    print(f"         翻译: {result.get('translations_en')}")
                
            except Exception as e:
                print(f"   ❌ 测试失败: {e}")
                import traceback
                print(f"   详细: {traceback.format_exc()}")
            
            # 延迟避免API限制
            await asyncio.sleep(1.5)
    
    async def test_rare_german_words(self):
        """测试罕见德语单词的OpenAI分析"""
        print("🔍 测试2: 罕见德语单词OpenAI分析")
        print("=" * 50)
        
        # 选择一些不太可能在基础词汇库中的德语单词
        test_words = [
            "Fernweh",              # 远方思念
            "Verschlimmbessern",    # 越修越坏
            "Fremdschämen",         # 替别人感到羞耻
            "Backpfeifengesicht",   # 欠扁的脸
            "Zungenbrecher",        # 绕口令
        ]
        
        for word in test_words:
            print(f"\n📝 测试词汇: '{word}'")
            
            try:
                result = await self.openai_service.analyze_word(word)
                
                print(f"   📊 OpenAI分析结果:")
                found = result.get('found')
                print(f"      识别为德语词汇: {'✅ Yes' if found else '❌ No'}")
                
                if found:
                    print(f"      词性: {result.get('pos', 'unknown')}")
                    
                    # 检查翻译
                    trans_en = result.get('translations_en', [])
                    trans_zh = result.get('translations_zh', [])
                    print(f"      英文翻译: {trans_en}")
                    print(f"      中文翻译: {trans_zh}")
                    
                    # 检查例句
                    example = result.get('example')
                    if example and example.get('de'):
                        print(f"      例句DE: {example['de']}")
                        print(f"      例句EN: {example['en']}")
                        print(f"      例句ZH: {example['zh']}")
                        print(f"      ✅ 包含完整例句")
                    else:
                        print(f"      ⚠️  缺少例句")
                    
                    print(f"      ✅ OpenAI成功分析罕见德语词汇")
                else:
                    suggestions = result.get('suggestions', [])
                    if suggestions:
                        print(f"      返回了 {len(suggestions)} 个建议词汇")
                        print(f"      建议: {[s.get('word') for s in suggestions[:3]]}")
                    print(f"      ❌ OpenAI未识别为德语词汇")
                    
            except Exception as e:
                print(f"   ❌ 测试失败: {e}")
            
            # 延迟避免API限制
            await asyncio.sleep(2)
    
    async def test_mixed_scenarios(self):
        """测试混合场景"""
        print("🔍 测试3: 混合场景测试")
        print("=" * 50)
        
        scenarios = [
            {
                "word": "hello",
                "expected_found": False,
                "expected_suggestions": True,
                "description": "英语单词 → 德语建议"
            },
            {
                "word": "Haus",
                "expected_found": True,
                "expected_suggestions": False,
                "description": "常见德语单词 → 直接分析"
            },
            {
                "word": "xyz123",
                "expected_found": False,
                "expected_suggestions": True,
                "description": "无意义字符 → 德语建议"
            },
            {
                "word": "Schadenfreude",
                "expected_found": True,
                "expected_suggestions": False,
                "description": "复杂德语单词 → 直接分析"
            }
        ]
        
        for scenario in scenarios:
            word = scenario["word"]
            expected_found = scenario["expected_found"]
            expected_suggestions = scenario["expected_suggestions"]
            description = scenario["description"]
            
            print(f"\n📝 场景: {description}")
            print(f"   词汇: '{word}'")
            print(f"   期望: 找到={expected_found}, 建议={expected_suggestions}")
            
            try:
                result = await self.openai_service.analyze_word(word)
                
                actual_found = result.get('found', False)
                actual_suggestions = bool(result.get('suggestions'))
                
                print(f"   实际: 找到={actual_found}, 建议={actual_suggestions}")
                
                # 验证结果
                found_correct = (actual_found == expected_found)
                suggestions_correct = (actual_suggestions == expected_suggestions)
                
                if found_correct and suggestions_correct:
                    print(f"   ✅ 场景测试通过")
                else:
                    print(f"   ⚠️  场景测试部分不符合预期")
                    if not found_correct:
                        print(f"      找到状态不匹配")
                    if not suggestions_correct:
                        print(f"      建议状态不匹配")
                
                # 显示具体内容
                if actual_found:
                    print(f"      词性: {result.get('pos')}")
                    print(f"      翻译: {result.get('translations_en', [])}")
                
                if actual_suggestions:
                    suggestions = result.get('suggestions', [])
                    print(f"      建议数量: {len(suggestions)}")
                    if suggestions:
                        print(f"      前3个建议: {[s.get('word') for s in suggestions[:3]]}")
                        
            except Exception as e:
                print(f"   ❌ 场景测试失败: {e}")
            
            await asyncio.sleep(1.5)

async def main():
    """主测试函数"""
    print("🧪 直接API测试 - OpenAI功能验证")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now()}")
    print()
    
    tester = DirectAPITester()
    
    # 检查配置
    if not tester.check_openai_config():
        print("\n❌ OpenAI配置不完整，无法进行测试")
        return
    
    print()
    
    try:
        # 运行测试
        await tester.test_mixed_scenarios()
        await tester.test_non_german_words()
        await tester.test_rare_german_words()
        
        print("\n🎉 所有测试完成")
        print("💡 如果看到错误，可能需要:")
        print("   1. 检查API密钥是否有效")
        print("   2. 检查网络连接")
        print("   3. 检查API配额")
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())