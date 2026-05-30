"""
AI服务后端测试用例
"""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
import pytest

from backend.main import app

client = TestClient(app)


@pytest.fixture
def mock_ai_response():
    """模拟AI响应"""
    return {
        "code": "def hello_world():\n    print('Hello, World!')",
        "provider": "openai",
        "model": "gpt-4-turbo",
        "tokens_used": 42,
        "processing_time": 1.23,
    }


class TestAuthRoutes:
    """认证路由测试"""

    def test_register_user(self):
        """测试用户注册"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_login_success(self):
        """测试登录成功"""
        # 先注册用户
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )

        # 测试登录
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_failure(self):
        """测试登录失败"""
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "nonexistent", "password": "wrongpassword"},
        )

        assert response.status_code == 401

    def test_get_current_user(self):
        """测试获取当前用户信息"""
        # 先登录获取令牌
        login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "testuser", "password": "testpassword123"},
        )
        token = login_response.json()["access_token"]

        # 使用令牌获取用户信息
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"


class TestAIRoutes:
    """AI路由测试"""

    @pytest.fixture
    def auth_headers(self):
        """获取认证头"""
        # 注册并登录用户
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "aiuser",
                "email": "ai@example.com",
                "password": "aipassword123",
            },
        )

        login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "aiuser", "password": "aipassword123"},
        )
        token = login_response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    def test_generate_code_success(self, auth_headers, mock_ai_response):
        """测试代码生成成功"""
        with patch(
            "backend.ai_service.ai_manager.AIManager.generate_code"
        ) as mock_generate:
            mock_generate.return_value = mock_ai_response

            response = client.post(
                "/api/v1/generate-code",
                json={
                    "prompt": "创建一个hello world函数",
                    "provider": "openai",
                    "language": "python",
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == mock_ai_response["code"]
            assert data["provider"] == "openai"

    def test_generate_code_unauthorized(self):
        """测试未授权的代码生成"""
        response = client.post(
            "/api/v1/generate-code", json={"prompt": "创建一个hello world函数"}
        )

        assert response.status_code == 401

    def test_generate_code_invalid_input(self, auth_headers):
        """测试无效输入"""
        response = client.post(
            "/api/v1/generate-code",
            json={"prompt": "", "provider": "invalid_provider"},  # 空提示词
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_get_available_models(self, auth_headers):
        """测试获取可用模型"""
        response = client.get("/api/v1/models", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) > 0

        # 检查模型数据结构
        model = data["models"][0]
        assert "provider" in model
        assert "model_name" in model
        assert "description" in model

    def test_get_usage_stats(self, auth_headers):
        """测试获取使用统计"""
        response = client.get("/api/v1/usage-stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_requests" in data
        assert "successful_requests" in data
        assert "success_rate" in data

    def test_get_recent_requests(self, auth_headers):
        """测试获取最近请求"""
        response = client.get("/api/v1/recent-requests?limit=5", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAIManager:
    """AI管理器测试"""

    @pytest.mark.asyncio
    async def test_openai_generation(self, mock_ai_response):
        """测试OpenAI代码生成"""
        from backend.ai_service.ai_manager import AIManager

        with patch("backend.ai_service.ai_manager.ChatOpenAI") as mock_chat:
            # 模拟ChatOpenAI响应
            mock_instance = AsyncMock()
            mock_instance.agenerate.return_value = AsyncMock(
                generations=[[AsyncMock(text=mock_ai_response["code"])]],
                llm_output={"token_usage": {"total_tokens": 42}},
            )
            mock_chat.return_value = mock_instance

            manager = AIManager()
            result = await manager._call_openai(
                AsyncMock(prompt="test prompt", language="python"), "gpt-4-turbo"
            )

            assert result["code"] == mock_ai_response["code"]
            assert result["tokens_used"] == 42

    @pytest.mark.asyncio
    async def test_lingma_generation(self, mock_ai_response):
        """测试Lingma代码生成"""
        from backend.ai_service.ai_manager import AIManager

        with patch("backend.ai_service.ai_manager.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = AsyncMock(
                status_code=200,
                json=AsyncMock(
                    return_value={
                        "choices": [{"message": {"content": mock_ai_response["code"]}}],
                        "usage": {"total_tokens": 42},
                    }
                ),
                raise_for_status=AsyncMock(),
            )
            mock_client.return_value.__aenter__.return_value = mock_instance

            manager = AIManager()
            result = await manager._call_lingma(
                AsyncMock(prompt="test prompt"), "lingma-code-pro"
            )

            assert result["code"] == mock_ai_response["code"]


class TestRateLimiting:
    """速率限制测试"""

    def test_rate_limit_exceeded(self, auth_headers):
        """测试速率限制"""
        # 快速发送多个请求
        responses = []
        for i in range(150):  # 超过限制
            response = client.post(
                "/api/v1/generate-code",
                json={"prompt": f"test prompt {i}"},
                headers=auth_headers,
            )
            responses.append(response)

        # 检查是否有429响应
        rate_limit_responses = [r for r in responses if r.status_code == 429]
        assert len(rate_limit_responses) > 0


class TestErrorHandling:
    """错误处理测试"""

    def test_invalid_json(self, auth_headers):
        """测试无效JSON"""
        response = client.post(
            "/api/v1/generate-code",
            content='{"invalid": json}',  # 无效JSON
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_database_error(self, auth_headers):
        """测试数据库错误"""
        with patch("backend.utils.database.AsyncSessionLocal") as mock_session:
            mock_session.side_effect = Exception("Database connection failed")

            response = client.post(
                "/api/v1/generate-code", json={"prompt": "test"}, headers=auth_headers
            )

            # 应该返回500错误
            assert response.status_code == 500


# 集成测试
class TestIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 用户注册
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "workflow_user",
                "email": "workflow@example.com",
                "password": "workflow123",
            },
        )
        assert register_response.status_code == 200

        # 2. 用户登录
        login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "workflow_user", "password": "workflow123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. 获取可用模型
        models_response = client.get("/api/v1/models", headers=headers)
        assert models_response.status_code == 200

        # 4. 生成代码
        with patch(
            "backend.ai_service.ai_manager.AIManager.generate_code"
        ) as mock_generate:
            mock_generate.return_value = {
                "code": "def test_func(): pass",
                "provider": "openai",
                "model": "gpt-4-turbo",
                "tokens_used": 10,
                "processing_time": 0.5,
            }

            generate_response = client.post(
                "/api/v1/generate-code",
                json={"prompt": "创建测试函数", "provider": "openai"},
                headers=headers,
            )
            assert generate_response.status_code == 200

            # 5. 检查使用统计
            stats_response = client.get("/api/v1/usage-stats", headers=headers)
            assert stats_response.status_code == 200

            # 6. 检查请求历史
            history_response = client.get("/api/v1/recent-requests", headers=headers)
            assert history_response.status_code == 200


if __name__ == "__main__":
    pytest.main(["-v", "--tb=short", __file__])
