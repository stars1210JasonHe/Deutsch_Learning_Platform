#!/usr/bin/env python3
"""
测试OpenAI相关功能：
1. 数据库中不存在的德语单词 -> OpenAI分析
2. 非德语单词 -> 返回5个相关德语单词建议
"""
import sys
import os
import asyncio
import json
from datetime import datetime

# 添加项目路径
sys.path.append(os.getcwd())

try:
    from app.db.session import SessionLocal
    from app.services.vocabulary_service import VocabularyService
    from app.services.openai_service import OpenAIService
    from app.models.user import User
except ImportError as e:
    print(f"❌ 无法导入应用模块: {e}")
    print("请确保后端服务正在运行")
    sys.exit(1)

class OpenAIFunctionTester:
    """OpenAI功能测试器"""
    
    def __init__(self):
        self.vocabulary_service = VocabularyService()
        self.openai_service = OpenAIService()
        
    async def test_german_word_not_in_database(self):
        """测试：数据库中不存在的德语单词"""
        print("🔍 测试1: 数据库中不存在的德语单词")
        print("=" * 50)
        
        # 选择一些不太可能在数据库中的德语单词
        test_words = [
            "Augenblicklichkeit",  # 暂时性（复合词）
            "verschwindungswinzig", # 极小的（不常用）
            "Katzenjammer",        # 宿醉（俚语）
            "Fernweh"             # 远方思念（德语特有词）
        ]
        
        db = SessionLocal()
        user = db.query(User).first()
        
        if not user:
            print("❌ 数据库中没有用户")
            db.close()
            return
            
        print(f"👤 使用用户: {user.email}")
        print()
        
        for word in test_words:
            print(f"📝 测试词汇: '{word}'")
            
            try:
                # 首先检查是否在数据库中
                existing = await self.vocabulary_service._find_existing_word(db, word)
                if existing:
                    print(f"   ℹ️  词汇已在数据库中，跳过OpenAI测试")
                    continue
                
                # 测试完整的词汇查询流程
                result = await self.vocabulary_service.get_or_create_word(db, word, user)
                
                print(f"   📊 结果分析:")
                print(f"      找到词汇: {'✅' if result.get('found') else '❌'}")
                print(f"      数据源: {result.get('source', 'unknown')}")
                
                if result.get('found'):
                    print(f"      词性: {result.get('pos', 'unknown')}")
                    print(f"      翻译EN: {result.get('translations_en', [])}")
                    print(f"      翻译ZH: {result.get('translations_zh', [])}")
                    
                    example = result.get('example')
                    if example and example.get('de'):
                        print(f"      例句: {example['de']}")
                        
                    print(f"   ✅ OpenAI成功分析德语单词")
                else:
                    print(f"   ❌ OpenAI未能识别为有效德语单词")
                    suggestions = result.get('suggestions', [])
                    if suggestions:
                        print(f"      建议词汇: {[s.get('word') for s in suggestions[:3]]}")
                        
            except Exception as e:
                print(f"   ❌ 测试失败: {e}")
            
            print()
            await asyncio.sleep(1)  # 避免API限制
        
        db.close()
    
    async def test_non_german_word_suggestions(self):
        """测试：非德语单词返回建议"""
        print("🔍 测试2: 非德语单词建议功能")
        print("=" * 50)
        
        # 明显的非德语单词
        test_words = [
            "hello",      # 英语
            "bonjour",    # 法语  
            "hola",       # 西班牙语
            "こんにちは",   # 日语
            "pizza",      # 意大利语（但在德语中也有使用）
            "computer",   # 英语（但德语中有Computer）
            "xyz123",     # 明显不是词汇
            "randomword", # 随机英语词
        ]
        
        db = SessionLocal()
        user = db.query(User).first()
        
        if not user:
            print("❌ 数据库中没有用户")
            db.close()
            return
            
        print(f"👤 使用用户: {user.email}")
        print()
        
        for word in test_words:
            print(f"📝 测试词汇: '{word}'")
            
            try:
                # 直接测试OpenAI服务
                openai_result = await self.openai_service.analyze_word(word)
                
                print(f"   📊 OpenAI响应分析:")
                print(f"      识别为德语: {'✅' if openai_result.get('found') else '❌'}")
                
                if not openai_result.get('found'):
                    suggestions = openai_result.get('suggestions', [])
                    print(f"      建议数量: {len(suggestions)}")
                    
                    if suggestions:
                        print(f"      建议词汇:")
                        for i, suggestion in enumerate(suggestions[:5], 1):
                            word_text = suggestion.get('word', 'N/A')
                            pos = suggestion.get('pos', 'N/A')
                            meaning = suggestion.get('meaning', 'N/A')
                            print(f"        {i}. {word_text} ({pos}) - {meaning}")
                        
                        if len(suggestions) >= 5:
                            print(f"   ✅ 返回了足够的建议词汇 ({len(suggestions)}个)")
                        else:
                            print(f"   ⚠️  建议词汇数量不足 ({len(suggestions)}个，期望5个)")
                    else:
                        print(f"   ❌ 没有返回建议词汇")
                else:
                    print(f"   ⚠️  OpenAI意外地识别为德语词汇")
                    print(f"      词性: {openai_result.get('pos')}")
                    print(f"      翻译: {openai_result.get('translations_en')}")
                    
            except Exception as e:
                print(f"   ❌ 测试失败: {e}")
                import traceback
                print(f"   详细错误: {traceback.format_exc()}")
            
            print()
            await asyncio.sleep(2)  # 更长延迟避免API限制
        
        db.close()
    
    async def test_complete_workflow(self):
        """测试完整的工作流程"""
        print("🔍 测试3: 完整工作流程测试")
        print("=" * 50)
        
        db = SessionLocal()
        user = db.query(User).first()
        
        if not user:
            print("❌ 数据库中没有用户")
            db.close()
            return
        
        # 测试场景
        test_scenarios = [
            {
                "word": "hello",
                "expected": "suggestions",
                "description": "英语单词应返回德语建议"
            },
            {
                "word": "Schadenfreude", 
                "expected": "analysis",
                "description": "罕见德语词应通过OpenAI分析"
            },
            {
                "word": "bezahlen",
                "expected": "database",
                "description": "常见词应从数据库直接返回"
            }
        ]
        
        for scenario in test_scenarios:
            word = scenario["word"]
            expected = scenario["expected"]
            description = scenario["description"]
            
            print(f"📝 场景: {description}")
            print(f"   词汇: '{word}' (期望: {expected})")
            
            try:
                result = await self.vocabulary_service.get_or_create_word(db, word, user)
                
                source = result.get('source', 'unknown')
                found = result.get('found', False)
                
                print(f"   结果: 找到={found}, 来源={source}")
                
                if expected == "database" and source.startswith("database"):
                    print(f"   ✅ 正确从数据库获取")
                elif expected == "analysis" and (source == "openai" or found):
                    print(f"   ✅ 正确通过OpenAI分析")
                elif expected == "suggestions" and not found and result.get('suggestions'):
                    suggestions_count = len(result.get('suggestions', []))
                    print(f"   ✅ 正确返回建议 ({suggestions_count}个)")
                else:
                    print(f"   ⚠️  结果与期望不符")
                    
            except Exception as e:
                print(f"   ❌ 场景测试失败: {e}")
            
            print()
        
        db.close()
    
    def check_openai_availability(self):
        """检查OpenAI服务可用性"""
        print("🔍 检查OpenAI服务可用性")
        print("=" * 30)
        
        if not self.openai_service.client:
            print("   ❌ OpenAI客户端未初始化（可能缺少API密钥）")
            return False
            
        print(f"   ✅ OpenAI客户端已初始化")
        print(f"   🤖 使用模型: {self.openai_service.model}")
        
        # 检查配置
        try:
            from app.core.config import settings
            if settings.openai_api_key:
                print(f"   🔑 API密钥已配置")
            else:
                print(f"   ❌ API密钥未配置")
                return False
                
            if settings.openai_base_url:
                print(f"   🌐 API地址: {settings.openai_base_url}")
            
        except Exception as e:
            print(f"   ⚠️  配置检查失败: {e}")
        
        return True

async def main():
    """主测试函数"""
    print("🧪 OpenAI功能综合测试")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now()}")
    print()
    
    tester = OpenAIFunctionTester()
    
    # 检查服务可用性
    if not tester.check_openai_availability():
        print("❌ OpenAI服务不可用，跳过测试")
        return
    
    print()
    
    # 运行测试
    try:
        await tester.test_complete_workflow()
        await tester.test_non_german_word_suggestions() 
        await tester.test_german_word_not_in_database()
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程出现严重错误: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())