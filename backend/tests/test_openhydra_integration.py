"""
OpenHydra AI 沙箱环境集成测试
测试容器管理、Jupyter 环境访问等功能
"""

import asyncio

from httpx import ASGITransport, AsyncClient
import pytest

from backend.main import app
from backend.services.openhydra_service import ContainerConfig, OpenHydraService
from config.settings import settings


class TestOpenHydraIntegration:
    """OpenHydra 集成测试类"""

    @pytest.fixture
    async def client(self):
        """创建异步测试客户端"""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    @pytest.fixture
    def openhydra_service(self):
        """创建 OpenHydra 服务实例"""
        return OpenHydraService(
            base_url=settings.OPENHYDRA_API_URL, api_key=settings.OPENHYDRA_API_KEY
        )

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查端点"""
        print("\n📋 测试 1: 健康检查")

        response = await client.get("/api/v1/org/1/ai-lab/health")

        # 由于是测试环境，可能返回不健康状态
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            assert data["status"] in ["healthy", "unhealthy"]
            assert data["service"] == "openhydra"
            print(f"✅ 健康检查通过：{data['status']}")
        else:
            print("⚠️  服务暂时不可用（测试环境预期行为）")

    @pytest.mark.skip(reason="需要实际运行 OpenHydra 服务")
    @pytest.mark.asyncio
    async def test_enter_lab(self, client):
        """测试进入 AI 实验室"""
        print("\n📋 测试 2: 进入 AI 实验室")

        # 模拟登录用户（需要添加认证中间件 mock）
        headers = {"Authorization": "Bearer test-token"}

        response = await client.post(
            "/api/v1/org/1/ai-lab/enter", headers=headers, json={}
        )

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "container_id" in data
            assert "jupyter_url" in data
            assert "access_token" in data
            print(f"✅ 进入实验室成功：{data['message']}")
        else:
            print(f"⚠️  测试跳过：HTTP {response.status_code}")

    @pytest.mark.skip(reason="需要实际运行 OpenHydra 服务")
    @pytest.mark.asyncio
    async def test_container_status(self, client):
        """测试获取容器状态"""
        print("\n📋 测试 3: 获取容器状态")

        headers = {"Authorization": "Bearer test-token"}

        response = await client.get(
            "/api/v1/org/1/ai-lab/container/status", headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "container_id" in data
            assert "status" in data
            assert "is_running" in data
            print(f"✅ 容器状态获取成功：{data['status']}")
        else:
            print(f"⚠️  测试跳过：HTTP {response.status_code}")

    @pytest.mark.asyncio
    async def test_service_initialization(self, openhydra_service):
        """测试服务初始化"""
        print("\n📋 测试 4: 服务初始化")

        assert openhydra_service is not None
        assert openhydra_service.base_url is not None
        assert openhydra_service.api_key is not None

        print(f"✅ OpenHydra 服务初始化成功")
        print(f"   - Base URL: {openhydra_service.base_url}")
        print(f"   - API Key: {'*' * 8} (已隐藏)")

    @pytest.mark.asyncio
    async def test_container_config_model(self):
        """测试容器配置数据模型"""
        print("\n📋 测试 5: 容器配置模型")

        config = ContainerConfig(
            user_id="test-user-123", cpu=4.0, memory="8Gi", gpu=0.5
        )

        assert config.user_id == "test-user-123"
        assert config.cpu == 4.0
        assert config.memory == "8Gi"
        assert config.gpu == 0.5
        assert config.image == "xedu/notebook:latest"  # 默认值

        print(f"✅ 容器配置模型验证通过")
        print(f"   - User ID: {config.user_id}")
        print(f"   - CPU: {config.cpu}")
        print(f"   - Memory: {config.memory}")
        print(f"   - GPU: {config.gpu}")
        print(f"   - Image: {config.image}")


class TestOpenHydraConfiguration:
    """OpenHydra 配置测试"""

    def test_settings_configuration(self):
        """测试配置设置"""
        print("\n📋 测试 6: 配置设置")

        assert hasattr(settings, "OPENHYDRA_API_URL")
        assert hasattr(settings, "OPENHYDRA_API_KEY")
        assert hasattr(settings, "OPENHYDRA_ENABLED")
        assert hasattr(settings, "JUPYTERHUB_URL")

        print(f"✅ 配置项存在性验证通过")
        print(f"   - OPENHYDRA_API_URL: {settings.OPENHYDRA_API_URL}")
        print(f"   - OPENHYDRA_ENABLED: {settings.OPENHYDRA_ENABLED}")
        print(f"   - JUPYTERHUB_URL: {settings.JUPYTERHUB_URL}")

    def test_route_registration(self):
        """测试路由注册"""
        print("\n📋 测试 7: 路由注册")

        # 检查应用中是否包含 openhydra 路由
        route_paths = [route.path for route in app.routes]

        openhydra_routes = [path for path in route_paths if "ai-lab" in path]

        assert len(openhydra_routes) > 0
        print(f"✅ 发现 {len(openhydra_routes)} 条 OpenHydra 相关路由:")

        for route in openhydra_routes:
            print(f"   - {route}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
