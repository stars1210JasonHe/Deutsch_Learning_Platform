#!/usr/bin/env python3
"""
Vibe Deutsch 测试运行器
运行所有测试模块并生成报告
"""
import sys
import os
import asyncio
import time
sys.path.append(os.path.dirname(__file__))

from tests.test_vocabulary_service import run_all_tests as run_vocab_tests
from tests.test_api_endpoints import run_all_api_tests


async def run_quick_functionality_test():
    """快速功能测试 - 测试关键路径"""
    
    print("🚀 快速功能测试")
    print("=" * 60)
    
    from app.db.session import SessionLocal
    from app.models.user import User, UserRole
    from app.services.vocabulary_service import VocabularyService
    from app.core.security import get_password_hash
    
    db = SessionLocal()
    vocab_service = VocabularyService()
    
    try:
        # 创建或获取测试用户
        test_user = db.query(User).filter(User.email == "quicktest@example.com").first()
        if not test_user:
            test_user = User(
                email="quicktest@example.com",
                password_hash=get_password_hash("test123"),
                role=UserRole.USER
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        print("✅ 测试用户准备就绪")
        
        # 测试关键词汇搜索
        test_words = ["Hallo", "Guten Tag", "Danke", "Bitte"]
        
        for word in test_words:
            try:
                print(f"\n🔍 测试搜索: {word}")
                
                start_time = time.time()
                result = await vocab_service.get_or_create_word(db, word, test_user)
                end_time = time.time()
                
                if result:
                    print(f"   ✅ 成功! 用时: {end_time - start_time:.2f}秒")
                    print(f"   词汇: {result['original']}")
                    print(f"   词性: {result['pos']}")
                    print(f"   来源: {result['source']}")
                    print(f"   英文翻译: {result['translations_en']}")
                    print(f"   中文翻译: {result['translations_zh']}")
                else:
                    print(f"   ❌ 搜索失败，返回空结果")
                    
            except Exception as e:
                print(f"   ❌ 搜索出错: {e}")
        
        # 测试搜索历史
        try:
            history_result = await vocab_service.search_words(db, "Hall", test_user, limit=5)
            if history_result and history_result.get("total", 0) > 0:
                print(f"\n✅ 模糊搜索测试成功，找到 {history_result['total']} 个结果")
            else:
                print(f"\n⚠️ 模糊搜索没有找到结果")
        except Exception as e:
            print(f"\n❌ 模糊搜索测试失败: {e}")
        
        # 数据库统计
        from app.models.word import WordLemma
        from app.models.search import SearchHistory
        
        total_words = db.query(WordLemma).count()
        total_searches = db.query(SearchHistory).filter(
            SearchHistory.user_id == test_user.id
        ).count()
        
        print(f"\n📊 数据库统计:")
        print(f"   词汇总数: {total_words}")
        print(f"   用户搜索次数: {total_searches}")
        
    finally:
        db.close()


def run_database_integrity_test():
    """数据库完整性测试"""
    
    print("\n🗄️ 数据库完整性测试")
    print("=" * 40)
    
    from app.db.session import SessionLocal
    from app.models.word import WordLemma, Translation, Example, WordForm
    from app.models.user import User
    from app.models.search import SearchHistory, SearchCache
    
    db = SessionLocal()
    
    try:
        # 检查所有表是否存在且可访问
        tables_to_check = [
            ("用户", User),
            ("词汇", WordLemma),
            ("翻译", Translation),
            ("例句", Example),
            ("词形", WordForm),
            ("搜索历史", SearchHistory),
            ("搜索缓存", SearchCache),
        ]
        
        all_good = True
        
        for table_name, model_class in tables_to_check:
            try:
                count = db.query(model_class).count()
                print(f"   ✅ {table_name}表: {count} 条记录")
            except Exception as e:
                print(f"   ❌ {table_name}表错误: {e}")
                all_good = False
        
        if all_good:
            print("✅ 数据库完整性检查通过")
        else:
            print("❌ 数据库完整性检查失败")
        
        return all_good
        
    finally:
        db.close()


def run_openai_integration_test():
    """OpenAI集成测试"""
    
    print("\n🤖 OpenAI集成测试")
    print("=" * 40)
    
    from app.services.openai_service import OpenAIService
    from app.core.config import settings
    
    if not settings.openai_api_key:
        print("⚠️ OpenAI API密钥未设置，跳过集成测试")
        return False
    
    openai_service = OpenAIService()
    
    async def _test():
        try:
            # 测试简单词汇分析
            result = await openai_service.analyze_word("Test")
            
            if result and result.get("pos"):
                print("✅ OpenAI词汇分析工作正常")
                print(f"   测试词: Test")
                print(f"   词性: {result.get('pos')}")
                print(f"   英文翻译: {result.get('translations_en', [])}")
                return True
            else:
                print("❌ OpenAI词汇分析返回无效结果")
                return False
                
        except Exception as e:
            print(f"❌ OpenAI集成测试失败: {e}")
            return False
    
    return asyncio.run(_test())


async def run_comprehensive_tests():
    """运行综合测试套件"""
    
    print("🧪 Vibe Deutsch 综合测试套件")
    print("=" * 60)
    
    start_time = time.time()
    
    # 1. 数据库完整性测试
    db_ok = run_database_integrity_test()
    
    # 2. OpenAI集成测试
    openai_ok = run_openai_integration_test()
    
    # 3. 快速功能测试
    await run_quick_functionality_test()
    
    # 4. 词汇服务测试
    print(f"\n{'=' * 60}")
    await run_vocab_tests()
    
    # 5. API端点测试
    print(f"\n{'=' * 60}")
    run_all_api_tests()
    
    end_time = time.time()
    
    # 测试总结
    print(f"\n{'=' * 60}")
    print("🎯 测试总结")
    print("=" * 60)
    
    print(f"   总测试时间: {end_time - start_time:.2f} 秒")
    print(f"   数据库完整性: {'✅' if db_ok else '❌'}")
    print(f"   OpenAI集成: {'✅' if openai_ok else '⚠️'}")
    print("   词汇服务测试: 详见上方结果")
    print("   API端点测试: 详见上方结果")
    
    print(f"\n🎉 测试完成! 请查看上方详细结果")


def main():
    """主函数"""
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "quick":
            print("运行快速测试...")
            asyncio.run(run_quick_functionality_test())
        elif test_type == "vocab":
            print("运行词汇服务测试...")
            asyncio.run(run_vocab_tests())
        elif test_type == "api":
            print("运行API端点测试...")
            run_all_api_tests()
        elif test_type == "db":
            print("运行数据库完整性测试...")
            run_database_integrity_test()
        elif test_type == "openai":
            print("运行OpenAI集成测试...")
            run_openai_integration_test()
        else:
            print(f"未知测试类型: {test_type}")
            print("可用选项: quick, vocab, api, db, openai, 或无参数运行全部测试")
    else:
        # 运行所有测试
        asyncio.run(run_comprehensive_tests())


if __name__ == "__main__":
    main()