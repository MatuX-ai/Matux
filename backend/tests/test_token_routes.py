"""
Token 管理 API 路由测试
验证 Token 相关的 RESTful API 功能
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 导入主应用
from main_ai_edu import app

# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_token_routes.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# 创建测试客户端
@pytest.fixture(scope="module")
def client():
    """创建测试客户端"""
    # 创建所有表
    from models.user_license import Base
    Base.metadata.create_all(bind=engine)

    # 覆盖依赖
    from routes.token_routes import get_sync_db
    app.dependency_overrides[get_sync_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # 清理
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


class TestTokenRoutes:
    """Token 路由测试类"""

    def test_get_token_packages(self, client):
        """测试获取套餐列表"""
        response = client.get("/api/v1/token/packages")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # 如果有数据，验证结构
        if len(data) > 0:
            first_package = data[0]
            assert "id" in first_package
            assert "name" in first_package
            assert "token_count" in first_package
            assert "price" in first_package

    def test_estimate_ai_teacher_cost(self, client):
        """测试 AI 对话成本预估"""
        request_data = {
            "feature_type": "ai_teacher",
            "params": {
                "message_length": 200
            }
        }

        response = client.post(
            "/api/v1/token/estimate",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["feature_type"] == "ai_teacher"
        assert data["estimated_tokens"] > 0
        assert "description" in data

    def test_estimate_course_generation_cost(self, client):
        """测试课程生成成本预估"""
        request_data = {
            "feature_type": "course_generation",
            "params": {
                "complexity": "medium"
            }
        }

        response = client.post(
            "/api/v1/token/estimate",
            json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["feature_type"] == "course_generation"
        assert data["estimated_tokens"] == 150  # medium 复杂度
        assert "description" in data

    def test_estimate_invalid_feature_type(self, client):
        """测试无效功能类型的成本预估"""
        request_data = {
            "feature_type": "invalid_feature",
            "params": {}
        }

        response = client.post(
            "/api/v1/token/estimate",
            json=request_data
        )

        assert response.status_code == 400

    def test_get_package_by_id(self, client):
        """测试根据 ID 获取套餐"""
        # 这个测试需要数据库中有套餐数据
        # 暂时跳过，等待完整的数据库初始化
        pytest.skip("需要预置套餐数据")

    def test_purchase_requires_auth(self, client):
        """测试购买操作需要认证"""
        request_data = {
            "package_id": 1,
            "payment_method": "wechat"
        }

        response = client.post(
            "/api/v1/token/purchase",
            json=request_data
        )

        # 应该返回 401 未授权
        assert response.status_code == 401

    def test_balance_requires_auth(self, client):
        """测试余额查询需要认证"""
        response = client.get("/api/v1/token/balance")

        # 应该返回 401 未授权
        assert response.status_code == 401

    def test_usage_history_requires_auth(self, client):
        """测试使用记录查询需要认证"""
        response = client.get("/api/v1/token/usage")

        # 应该返回 401 未授权
        assert response.status_code == 401

    def test_stats_requires_auth(self, client):
        """测试统计信息需要认证"""
        response = client.get("/api/v1/token/stats")

        # 应该返回 401 未授权
        assert response.status_code == 401


class TestTokenRoutesWithAuth:
    """带认证的 Token 路由测试（需要实现认证模拟）"""

    @pytest.mark.skip(reason="需要实现认证模拟")
    def test_purchase_token_package(self):
        """测试购买 Token 套餐（带认证）"""
        pass

    @pytest.mark.skip(reason="需要实现认证模拟")
    def test_get_user_balance(self):
        """测试查询用户余额（带认证）"""
        pass

    @pytest.mark.skip(reason="需要实现认证模拟")
    def test_get_usage_history(self):
        """测试获取使用记录（带认证）"""
        pass

    @pytest.mark.skip(reason="需要实现认证模拟")
    def test_get_token_stats(self):
        """测试获取统计信息（带认证）"""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
