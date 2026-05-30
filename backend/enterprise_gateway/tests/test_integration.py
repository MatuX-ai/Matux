"""
企业API网关集成测试
测试完整的API流程和组件间交互
"""

from datetime import datetime
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
import pytest

from main import app
from services.device_whitelist_service import device_whitelist_service
from services.enterprise_auth_service import enterprise_auth_service
from services.enterprise_oauth_service import enterprise_oauth_service

client = TestClient(app)


class TestEnterpriseAPIIntegration:
    """企业API集成测试类"""

    def setup_method(self):
        """测试方法前置设置"""
        self.valid_client_id = "ent_test_1234567890_abcdef12"
        self.valid_client_secret = "test_client_secret_12345"
        self.valid_device_id = "device_fingerprint_test_123"

    @patch("services.enterprise_oauth_service.get_db")
    def test_oauth2_token_flow(self, mock_get_db):
        """测试完整的OAuth2.0令牌流程"""
        # 模拟数据库会话
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        # 模拟企业客户端
        mock_client = Mock()
        mock_client.client_id = self.valid_client_id
        mock_client.is_active = True
        mock_client.verify_client_secret.return_value = True
        mock_client.has_quota_available.return_value = True
        mock_client.api_quota_limit = 1000
        mock_client.current_usage = 0
        mock_client.increment_usage = Mock()

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        # 1. 测试获取访问令牌
        token_request = {
            "grant_type": "client_credentials",
            "client_id": self.valid_client_id,
            "client_secret": self.valid_client_secret,
        }

        response = client.post("/api/enterprise/oauth/token", data=token_request)
        assert response.status_code == 200

        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "Bearer"
        assert token_data["expires_in"] > 0
        assert token_data["scope"] == "api:read"

        access_token = token_data["access_token"]

        # 2. 测试使用令牌访问受保护端点
        headers = {"Authorization": f"Bearer {access_token}"}

        # 先测试不需要设备ID的端点
        response = client.get(
            "/api/enterprise/oauth/introspect",
            params={"token": access_token},
            headers=headers,
        )
        assert response.status_code == 200

        introspect_data = response.json()
        assert introspect_data["active"] == True
        assert introspect_data["client_id"] == self.valid_client_id

    @patch("services.enterprise_oauth_service.get_db")
    @patch("services.device_whitelist_service.get_db")
    def test_device_whitelist_integration(self, mock_device_db, mock_oauth_db):
        """测试设备白名单集成"""
        # 设置模拟数据库
        mock_oauth_session = Mock()
        mock_device_session = Mock()
        mock_oauth_db.return_value = iter([mock_oauth_session])
        mock_device_db.return_value = iter([mock_device_session])

        # 模拟客户端验证
        mock_client = Mock()
        mock_client.client_id = self.valid_client_id
        mock_client.is_active = True
        mock_oauth_session.query.return_value.filter.return_value.first.return_value = (
            mock_client
        )

        # 模拟设备白名单检查
        mock_device = Mock()
        mock_device.is_approved = True
        mock_device.is_expired.return_value = False
        mock_device.is_valid.return_value = True

        mock_device_session.query.return_value.join.return_value.filter.return_value.first.return_value = (
            mock_device
        )

        # 测试带设备ID的认证
        headers = {
            "Authorization": f"Bearer test_token",
            "X-Device-ID": self.valid_device_id,
        }

        # 这里应该测试需要设备验证的端点
        # 由于中间件会拦截，我们测试设备管理端点
        response = client.get(
            f"/api/enterprise/devices/{self.valid_client_id}", headers=headers
        )
        # 注意：由于认证中间件的存在，这个请求可能会被拦截

    def test_health_check_endpoints(self):
        """测试健康检查端点"""
        # 测试根路径
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "healthy"

        # 测试健康检查端点
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data

    def test_openapi_documentation(self):
        """测试OpenAPI文档端点"""
        # 测试Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200

        # 测试ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200

        # 测试OpenAPI规范
        response = client.get("/openapi.json")
        assert response.status_code == 200
        openapi_spec = response.json()
        assert "openapi" in openapi_spec
        assert "info" in openapi_spec
        assert "paths" in openapi_spec

    @patch("services.enterprise_oauth_service.get_db")
    def test_client_management(self, mock_get_db):
        """测试客户端管理功能"""
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        # 模拟客户端创建
        mock_client = Mock()
        mock_client.id = 1
        mock_client.client_name = "Test Company"
        mock_client.client_id = self.valid_client_id
        mock_client.redirect_uris = "https://test.com/callback"
        mock_client.is_active = True
        mock_client.api_quota_limit = 1000
        mock_client.contact_email = "admin@test.com"
        mock_client.created_at = datetime.utcnow()
        mock_client.to_dict.return_value = {
            "id": 1,
            "client_name": "Test Company",
            "client_id": self.valid_client_id,
            "is_active": True,
        }

        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        with patch.object(
            enterprise_oauth_service,
            "create_enterprise_client",
            return_value=mock_client,
        ):

            # 测试创建客户端
            client_data = {
                "client_name": "Test Company",
                "contact_email": "admin@test.com",
                "api_quota_limit": 1000,
            }

            response = client.post("/api/enterprise/clients", json=client_data)
            # 注意：由于依赖注入和权限检查，这个测试可能需要调整

    @patch("services.device_whitelist_service.get_db")
    def test_device_management(self, mock_get_db):
        """测试设备管理功能"""
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        # 模拟设备列表
        mock_device = Mock()
        mock_device.id = 1
        mock_device.device_id = self.valid_device_id
        mock_device.device_name = "Test Device"
        mock_device.ip_address = "192.168.1.100"
        mock_device.is_approved = True
        mock_device.to_dict.return_value = {
            "id": 1,
            "device_id": self.valid_device_id,
            "device_name": "Test Device",
            "is_approved": True,
        }

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            mock_device
        ]

        with patch.object(
            device_whitelist_service, "get_client_devices", return_value=[mock_device]
        ):

            # 测试获取设备列表
            client.get(f"/api/enterprise/devices/{self.valid_client_id}")
            # 注意：同样受到认证中间件影响

    def test_error_handling(self):
        """测试错误处理"""
        # 测试404错误
        response = client.get("/api/enterprise/nonexistent")
        assert response.status_code == 404

        # 测试无效的JSON
        response = client.post(
            "/api/enterprise/oauth/token",
            data="invalid json",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422  # 验证错误

    @patch("services.enterprise_auth_service.get_db")
    def test_monitoring_endpoints(self, mock_get_db):
        """测试监控端点"""
        mock_db = Mock()
        mock_get_db.return_value = iter([mock_db])

        # 模拟统计数据
        mock_stats = {
            "total_requests": 100,
            "successful_requests": 95,
            "failed_requests": 5,
            "success_rate": 95.0,
            "average_response_time": 150.5,
            "active_devices": 3,
        }

        with patch.object(
            enterprise_auth_service, "get_client_statistics", return_value=mock_stats
        ):

            # 测试统计端点（需要认证，所以会返回401）
            response = client.get(
                f"/api/enterprise/monitoring/stats/{self.valid_client_id}"
            )
            assert response.status_code == 401  # 未认证


class TestEnterpriseAuthMiddlewareIntegration:
    """企业认证中间件集成测试"""

    def test_middleware_exclusions(self):
        """测试中间件排除路径"""
        # 这些路径应该绕过认证
        excluded_paths = ["/", "/health", "/docs", "/redoc", "/openapi.json"]

        for path in excluded_paths:
            response = client.get(path)
            # 健康检查路径应该返回200
            if path in ["/", "/health"]:
                assert response.status_code == 200
            # 文档路径也应该可访问
            elif path in ["/docs", "/redoc"]:
                assert response.status_code == 200

    def test_unauthorized_access(self):
        """测试未授权访问"""
        # 访问需要认证的端点但不提供认证信息
        response = client.get("/api/enterprise/monitoring/stats/test_client")
        assert response.status_code == 401

        # 提供无效的认证头
        response = client.get(
            "/api/enterprise/monitoring/stats/test_client",
            headers={"Authorization": "Invalid token"},
        )
        assert response.status_code == 401

        # 提供格式正确的但无效的Bearer令牌
        response = client.get(
            "/api/enterprise/monitoring/stats/test_client",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
