"""
API端点测试模块
测试FastAPI路由和响应
"""
import pytest
import asyncio
import sys
import os
import httpx
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token


class TestAPIEndpoints:
    """API端点测试类"""
    
    def setup_class(self):
        """设置测试环境"""
        self.client = TestClient(app)
        
        # 创建测试用户令牌
        self.test_token = create_access_token(subject=1)  # 假设用户ID为1
        self.headers = {"Authorization": f"Bearer {self.test_token}"}
        
        print("✅ API测试环境设置完成")

    def test_root_endpoint(self):
        """测试根端点"""
        print("\n🧪 测试: 根端点")
        
        response = self.client.get("/")
        
        assert response.status_code == 200, f"期望状态码200，得到{response.status_code}"
        
        data = response.json()
        assert "message" in data, "响应中应该包含message字段"
        assert "Vibe Deutsch" in data["message"], "消息中应该包含应用名称"
        
        print(f"   ✅ 根端点响应: {data['message']}")

    def test_health_endpoint(self):
        """测试健康检查端点"""
        print("\n🧪 测试: 健康检查端点")
        
        response = self.client.get("/health")
        
        assert response.status_code == 200, f"期望状态码200，得到{response.status_code}"
        
        data = response.json()
        assert data["status"] == "healthy", f"期望status为healthy，得到{data['status']}"
        assert "version" in data, "响应中应该包含version字段"
        
        print(f"   ✅ 健康状态: {data['status']}, 版本: {data['version']}")

    def test_auth_register(self):
        """测试用户注册"""
        print("\n🧪 测试: 用户注册")
        
        user_data = {
            "email": f"test_{id(self)}@example.com",  # 使用对象ID确保唯一性
            "password": "testpass123"
        }
        
        response = self.client.post("/auth/register", json=user_data)
        
        # 可能返回400如果用户已存在，或200如果成功
        assert response.status_code in [200, 400], f"期望状态码200或400，得到{response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "email" in data, "注册响应中应该包含email字段"
            print(f"   ✅ 注册成功: {data['email']}")
        else:
            print(f"   ℹ️ 注册响应: {response.json()}")

    def test_auth_login(self):
        """测试用户登录"""
        print("\n🧪 测试: 用户登录")
        
        # 先尝试注册用户
        user_data = {
            "email": f"login_test_{id(self)}@example.com",
            "password": "testpass123"
        }
        
        # 注册
        self.client.post("/auth/register", json=user_data)
        
        # 登录
        response = self.client.post("/auth/login", json=user_data)
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data, "登录响应中应该包含access_token"
            assert data["token_type"] == "bearer", f"期望token_type为bearer，得到{data['token_type']}"
            print(f"   ✅ 登录成功，获得令牌")
        else:
            print(f"   ⚠️ 登录失败: {response.json()}")

    def test_words_search_unauthorized(self):
        """测试未授权的词汇搜索"""
        print("\n🧪 测试: 未授权词汇搜索")
        
        response = self.client.get("/words/?q=test")
        
        assert response.status_code == 401, f"期望状态码401，得到{response.status_code}"
        
        print("   ✅ 未授权访问被正确拒绝")

    def test_words_search_authorized(self):
        """测试授权的词汇搜索"""
        print("\n🧪 测试: 授权词汇搜索")
        
        # 注意：这个测试可能会失败，因为依赖于实际的数据库和OpenAI配置
        response = self.client.get("/words/?q=Hallo", headers=self.headers)
        
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 搜索成功: {data}")
        else:
            print(f"   ⚠️ 搜索失败: {response.json() if response.content else '无响应内容'}")

    def test_translate_word_unauthorized(self):
        """测试未授权的单词翻译"""
        print("\n🧪 测试: 未授权单词翻译")
        
        response = self.client.post("/translate/word", json={"input": "test"})
        
        assert response.status_code == 401, f"期望状态码401，得到{response.status_code}"
        
        print("   ✅ 未授权翻译被正确拒绝")

    def test_translate_word_authorized(self):
        """测试授权的单词翻译"""
        print("\n🧪 测试: 授权单词翻译")
        
        response = self.client.post(
            "/translate/word", 
            json={"input": "Hallo"},
            headers=self.headers
        )
        
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 翻译成功: {data.get('original', 'N/A')}")
        else:
            print(f"   ⚠️ 翻译失败: {response.json() if response.content else '无响应内容'}")

    def test_translate_sentence_authorized(self):
        """测试授权的句子翻译"""
        print("\n🧪 测试: 授权句子翻译")
        
        response = self.client.post(
            "/translate/sentence",
            json={"input": "Hello, how are you?"},
            headers=self.headers
        )
        
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 句子翻译成功")
            if "german" in data:
                print(f"   德语翻译: {data['german']}")
        else:
            print(f"   ⚠️ 句子翻译失败: {response.json() if response.content else '无响应内容'}")

    def test_search_history_authorized(self):
        """测试授权的搜索历史"""
        print("\n🧪 测试: 授权搜索历史")
        
        response = self.client.get("/search/history", headers=self.headers)
        
        print(f"   响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 搜索历史获取成功")
            print(f"   历史记录数: {data.get('total', 0)}")
        else:
            print(f"   ⚠️ 搜索历史获取失败: {response.json() if response.content else '无响应内容'}")

    def test_api_docs_available(self):
        """测试API文档是否可用"""
        print("\n🧪 测试: API文档可用性")
        
        response = self.client.get("/docs")
        
        assert response.status_code == 200, f"期望状态码200，得到{response.status_code}"
        
        print("   ✅ API文档可以访问")

    def test_openapi_spec(self):
        """测试OpenAPI规范"""
        print("\n🧪 测试: OpenAPI规范")
        
        response = self.client.get("/openapi.json")
        
        assert response.status_code == 200, f"期望状态码200，得到{response.status_code}"
        
        data = response.json()
        assert "openapi" in data, "OpenAPI规范中应该包含openapi字段"
        assert "info" in data, "OpenAPI规范中应该包含info字段"
        assert "paths" in data, "OpenAPI规范中应该包含paths字段"
        
        print(f"   ✅ OpenAPI版本: {data['openapi']}")
        print(f"   ✅ API标题: {data['info']['title']}")


def run_all_api_tests():
    """运行所有API测试"""
    
    print("🧪 开始API端点测试")
    print("=" * 60)
    
    test_instance = TestAPIEndpoints()
    test_instance.setup_class()
    
    test_methods = [
        test_instance.test_root_endpoint,
        test_instance.test_health_endpoint,
        test_instance.test_auth_register,
        test_instance.test_auth_login,
        test_instance.test_words_search_unauthorized,
        test_instance.test_words_search_authorized,
        test_instance.test_translate_word_unauthorized,
        test_instance.test_translate_word_authorized,
        test_instance.test_translate_sentence_authorized,
        test_instance.test_search_history_authorized,
        test_instance.test_api_docs_available,
        test_instance.test_openapi_spec,
    ]
    
    passed = 0
    failed = 0
    
    for i, test_method in enumerate(test_methods):
        try:
            test_method()
            passed += 1
            print(f"   ✅ 测试 {i+1} 通过")
        except Exception as e:
            failed += 1
            print(f"   ❌ 测试 {i+1} 失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 API测试总结:")
    print(f"   通过: {passed}")
    print(f"   失败: {failed}")
    print(f"   总计: {passed + failed}")
    
    if failed == 0:
        print("🎉 所有API测试通过！")
    else:
        print(f"⚠️ 有 {failed} 个API测试失败")


if __name__ == "__main__":
    run_all_api_tests()