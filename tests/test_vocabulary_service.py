"""
VocabularyService 测试模块
测试搜索、缓存、OpenAI集成等功能
"""
import pytest
import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.user import User, UserRole
from app.models.word import WordLemma, Translation, Example, WordForm
from app.services.vocabulary_service import VocabularyService
from app.core.security import get_password_hash


# 测试数据库
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


class TestVocabularyService:
    """VocabularyService 测试类"""
    
    @classmethod
    def setup_class(cls):
        """设置测试环境"""
        # 创建测试数据库表
        Base.metadata.create_all(bind=test_engine)
        cls.db = TestSessionLocal()
        cls.vocab_service = VocabularyService()
        
        # 创建测试用户
        cls.test_user = User(
            email="test@vocabulary.com",
            password_hash=get_password_hash("test123"),
            role=UserRole.USER
        )
        cls.db.add(cls.test_user)
        cls.db.commit()
        cls.db.refresh(cls.test_user)
        
        print("✅ 测试环境设置完成")

    @classmethod
    def teardown_class(cls):
        """清理测试环境"""
        cls.db.close()
        # 删除测试数据库文件
        try:
            os.remove("./test.db")
            print("✅ 测试数据库已清理")
        except FileNotFoundError:
            pass

    def setup_method(self):
        """每个测试前的设置"""
        # 清理所有词汇数据
        self.db.query(WordForm).delete()
        self.db.query(Example).delete()
        self.db.query(Translation).delete()
        self.db.query(WordLemma).delete()
        self.db.commit()

    async def test_search_empty_database(self):
        """测试空数据库搜索"""
        print("\n🧪 测试: 空数据库搜索")
        
        # 确认数据库为空
        count = self.db.query(WordLemma).count()
        assert count == 0, f"数据库应该为空，但找到了 {count} 个词汇"
        
        # 搜索不存在的词汇
        result = await self.vocab_service.get_or_create_word(
            self.db, "Hallo", self.test_user
        )
        
        # 验证结果
        assert result is not None, "搜索结果不应该为空"
        assert result["original"] == "Hallo", f"期望 'Hallo'，实际得到 {result['original']}"
        assert result["source"] in ["openai", "database"], f"无效的来源: {result['source']}"
        
        print(f"   ✅ 搜索结果: {result['original']} ({result['pos']})")
        print(f"   ✅ 来源: {result['source']}")

    async def test_search_existing_word(self):
        """测试搜索已存在的词汇"""
        print("\n🧪 测试: 搜索已存在的词汇")
        
        # 预先添加一个词汇
        test_word = WordLemma(
            lemma="gehen",
            pos="verb",
            cefr="A1",
            notes="Test word"
        )
        self.db.add(test_word)
        self.db.commit()
        self.db.refresh(test_word)
        
        # 添加翻译
        en_trans = Translation(
            lemma_id=test_word.id,
            lang_code="en",
            text="to go",
            source="test"
        )
        zh_trans = Translation(
            lemma_id=test_word.id,
            lang_code="zh",
            text="去",
            source="test"
        )
        self.db.add(en_trans)
        self.db.add(zh_trans)
        self.db.commit()
        
        # 搜索这个词汇
        result = await self.vocab_service.get_or_create_word(
            self.db, "gehen", self.test_user
        )
        
        # 验证结果
        assert result is not None, "搜索结果不应该为空"
        assert result["original"] == "gehen", f"期望 'gehen'，实际得到 {result['original']}"
        assert result["source"] == "database", f"应该从数据库获取，实际来源: {result['source']}"
        assert result["cached"] is True, "应该标记为缓存"
        assert "to go" in result["translations_en"], "应该包含英文翻译 'to go'"
        assert "去" in result["translations_zh"], "应该包含中文翻译 '去'"
        
        print(f"   ✅ 找到已存在词汇: {result['original']}")
        print(f"   ✅ 英文翻译: {result['translations_en']}")
        print(f"   ✅ 中文翻译: {result['translations_zh']}")

    async def test_case_insensitive_search(self):
        """测试不区分大小写的搜索"""
        print("\n🧪 测试: 不区分大小写搜索")
        
        # 添加小写词汇
        test_word = WordLemma(
            lemma="hallo",
            pos="interjection",
            cefr="A1",
            notes="Test greeting"
        )
        self.db.add(test_word)
        self.db.commit()
        
        # 用大写搜索
        result = await self.vocab_service.get_or_create_word(
            self.db, "HALLO", self.test_user
        )
        
        # 验证找到了小写版本
        assert result is not None, "应该找到词汇"
        assert result["source"] == "database", "应该从数据库找到"
        
        print(f"   ✅ 大写搜索 'HALLO' 找到小写词汇 '{result['original']}'")

    async def test_search_with_article(self):
        """测试带冠词的搜索"""
        print("\n🧪 测试: 带冠词的搜索")
        
        # 添加不带冠词的名词
        test_word = WordLemma(
            lemma="Tisch",
            pos="noun",
            cefr="A1",
            notes="Test noun"
        )
        self.db.add(test_word)
        self.db.commit()
        self.db.refresh(test_word)
        
        # 添加冠词信息
        article_form = WordForm(
            lemma_id=test_word.id,
            form="der Tisch",
            feature_key="article",
            feature_value="der"
        )
        self.db.add(article_form)
        self.db.commit()
        
        # 用带冠词的形式搜索
        result = await self.vocab_service.get_or_create_word(
            self.db, "der Tisch", self.test_user
        )
        
        # 验证结果
        assert result is not None, "应该找到词汇"
        assert result["original"] == "Tisch", f"应该返回lemma 'Tisch'，实际: {result['original']}"
        
        print(f"   ✅ 搜索 'der Tisch' 找到词汇 '{result['original']}'")

    async def test_word_forms_search(self):
        """测试词形变位搜索"""
        print("\n🧪 测试: 词形变位搜索")
        
        # 添加动词及其变位
        test_verb = WordLemma(
            lemma="gehen",
            pos="verb",
            cefr="A1",
            notes="Test verb"
        )
        self.db.add(test_verb)
        self.db.commit()
        self.db.refresh(test_verb)
        
        # 添加变位形式
        verb_form = WordForm(
            lemma_id=test_verb.id,
            form="geht",
            feature_key="tense",
            feature_value="praesens_er_sie_es"
        )
        self.db.add(verb_form)
        self.db.commit()
        
        # 用变位形式搜索
        result = await self.vocab_service.get_or_create_word(
            self.db, "geht", self.test_user
        )
        
        # 验证找到了原形
        assert result is not None, "应该找到词汇"
        assert result["original"] == "gehen", f"应该找到原形 'gehen'，实际: {result['original']}"
        
        print(f"   ✅ 搜索变位 'geht' 找到原形 '{result['original']}'")

    async def test_search_results_format(self):
        """测试搜索结果格式"""
        print("\n🧪 测试: 搜索结果格式")
        
        result = await self.vocab_service.get_or_create_word(
            self.db, "test", self.test_user
        )
        
        # 验证必需字段
        required_fields = [
            "original", "pos", "translations_en", "translations_zh", 
            "cached", "source"
        ]
        
        for field in required_fields:
            assert field in result, f"缺少必需字段: {field}"
        
        # 验证类型
        assert isinstance(result["translations_en"], list), "translations_en应该是列表"
        assert isinstance(result["translations_zh"], list), "translations_zh应该是列表"
        assert isinstance(result["cached"], bool), "cached应该是布尔值"
        
        print("   ✅ 搜索结果格式验证通过")

    def test_search_history_logging(self):
        """测试搜索历史记录"""
        print("\n🧪 测试: 搜索历史记录")
        
        # 这个测试需要在异步函数外运行
        async def _test():
            await self.vocab_service.get_or_create_word(
                self.db, "Geschichte", self.test_user
            )
            
            # 检查搜索历史
            from app.models.search import SearchHistory
            history_count = self.db.query(SearchHistory).filter(
                SearchHistory.user_id == self.test_user.id
            ).count()
            
            assert history_count > 0, "应该记录搜索历史"
            
            print(f"   ✅ 搜索历史记录数: {history_count}")
        
        # 运行异步测试
        asyncio.run(_test())

    async def test_bulk_search(self):
        """测试批量搜索性能"""
        print("\n🧪 测试: 批量搜索")
        
        test_words = ["Hallo", "Tschüss", "danke", "bitte", "ja", "nein"]
        results = []
        
        for word in test_words:
            result = await self.vocab_service.get_or_create_word(
                self.db, word, self.test_user
            )
            results.append(result)
        
        # 验证所有词汇都有结果
        assert len(results) == len(test_words), f"期望 {len(test_words)} 个结果，得到 {len(results)} 个"
        
        for i, result in enumerate(results):
            assert result is not None, f"第 {i} 个搜索结果为空"
            assert result["original"] == test_words[i], f"期望 {test_words[i]}，得到 {result['original']}"
        
        print(f"   ✅ 批量搜索 {len(test_words)} 个词汇完成")

    async def test_search_words_function(self):
        """测试search_words函数"""
        print("\n🧪 测试: search_words函数")
        
        # 先添加一些测试数据
        test_words_data = [
            ("Hallo", "interjection", "hello", "你好"),
            ("guten", "adjective", "good", "好的"),
            ("Tag", "noun", "day", "天"),
        ]
        
        for lemma, pos, en_trans, zh_trans in test_words_data:
            word = WordLemma(lemma=lemma, pos=pos, cefr="A1", notes="Test")
            self.db.add(word)
            self.db.commit()
            self.db.refresh(word)
            
            self.db.add(Translation(lemma_id=word.id, lang_code="en", text=en_trans, source="test"))
            self.db.add(Translation(lemma_id=word.id, lang_code="zh", text=zh_trans, source="test"))
        
        self.db.commit()
        
        # 测试搜索
        result = await self.vocab_service.search_words(
            self.db, "gu", self.test_user  # 应该找到 "guten"
        )
        
        # 验证结果
        assert result is not None, "搜索结果不应该为空"
        assert "results" in result, "结果中应该包含 'results' 字段"
        assert "total" in result, "结果中应该包含 'total' 字段"
        assert result["total"] >= 1, f"应该至少找到1个结果，实际: {result['total']}"
        
        print(f"   ✅ 模糊搜索 'gu' 找到 {result['total']} 个结果")


def run_async_test(test_func):
    """运行异步测试函数"""
    return asyncio.run(test_func())


# 运行所有测试的主函数
async def run_all_tests():
    """运行所有测试"""
    
    print("🧪 开始VocabularyService测试")
    print("=" * 60)
    
    test_instance = TestVocabularyService()
    test_instance.setup_class()
    
    try:
        test_methods = [
            test_instance.test_search_empty_database,
            test_instance.test_search_existing_word,
            test_instance.test_case_insensitive_search,
            test_instance.test_search_with_article,
            test_instance.test_word_forms_search,
            test_instance.test_search_results_format,
            test_instance.test_bulk_search,
            test_instance.test_search_words_function,
        ]
        
        passed = 0
        failed = 0
        
        for i, test_method in enumerate(test_methods):
            try:
                test_instance.setup_method()  # 重置测试环境
                await test_method()
                passed += 1
                print(f"   ✅ 测试 {i+1} 通过")
            except Exception as e:
                failed += 1
                print(f"   ❌ 测试 {i+1} 失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 运行同步测试
        try:
            test_instance.setup_method()
            test_instance.test_search_history_logging()
            passed += 1
            print(f"   ✅ 搜索历史测试通过")
        except Exception as e:
            failed += 1
            print(f"   ❌ 搜索历史测试失败: {e}")
        
        print(f"\n📊 测试总结:")
        print(f"   通过: {passed}")
        print(f"   失败: {failed}")
        print(f"   总计: {passed + failed}")
        
        if failed == 0:
            print("🎉 所有测试通过！")
        else:
            print(f"⚠️ 有 {failed} 个测试失败")
            
    finally:
        test_instance.teardown_class()


if __name__ == "__main__":
    asyncio.run(run_all_tests())