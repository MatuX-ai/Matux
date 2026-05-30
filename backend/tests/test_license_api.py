"""
许可证API路由测试
"""

from datetime import datetime
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
import pytest

from main import app
from models.license import LicenseStatus, LicenseType

client = TestClient(app)


class TestLicenseAPI:
    """许可证API测试类"""

    @patch("routes.license_routes.LicenseService")
    def test_create_organization_success(self, mock_license_service_class):
        """测试成功创建组织"""
        # 模拟服务返回
        mock_service = Mock()
        mock_organization = Mock()
        mock_organization.id = 1
        mock_organization.name = "测试组织"
        mock_organization.contact_email = "test@example.com"
        mock_organization.is_active = True
        mock_organization.created_at = datetime.utcnow()
        mock_organization.updated_at = datetime.utcnow()

        mock_service.create_organization.return_value = mock_organization
        mock_license_service_class.return_value = mock_service

        # 测试数据
        org_data = {
            "name": "测试组织",
            "contact_email": "test@example.com",
            "max_users": 100,
        }

        # 发送请求
        response = client.post("/api/v1/organizations", json=org_data)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "测试组织"
        assert data["contact_email"] == "test@example.com"

    @patch("routes.license_routes.LicenseService")
    def test_create_organization_validation_error(self, mock_license_service_class):
        """测试组织创建验证错误"""
        # 发送无效数据
        invalid_data = {
            "name": "",  # 空名称
            "contact_email": "invalid-email",  # 无效邮箱
        }

        response = client.post("/api/v1/organizations", json=invalid_data)

        # 对于Pydantic验证，可能会返回422而不是400
        assert response.status_code in [400, 422]

    @patch("routes.license_routes.get_db")
    @patch("routes.license_routes.LicenseService")
    def test_list_organizations(self, mock_license_service_class, mock_get_db):
        """测试获取组织列表"""
        # 模拟数据库会话
        mock_db = Mock()
        mock_get_db.return_value.__iter__ = Mock(return_value=iter([mock_db]))

        # 模拟服务
        mock_service = Mock()
        mock_organizations = [
            Mock(id=1, name="组织1", contact_email="org1@example.com"),
            Mock(id=2, name="组织2", contact_email="org2@example.com"),
        ]
        mock_service.list_organizations.return_value = mock_organizations
        mock_license_service_class.return_value = mock_service

        # 发送请求
        response = client.get("/api/v1/organizations")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch("routes.license_routes.LicenseService")
    def test_generate_license_success(self, mock_license_service_class):
        """测试成功生成许可证"""
        # 模拟服务返回
        mock_service = Mock()
        mock_license = Mock()
        mock_license.id = 1
        mock_license.license_key = "LICENSE-TEST-123456"
        mock_license.organization_id = 1
        mock_license.license_type = LicenseType.COMMERCIAL
        mock_license.status = LicenseStatus.ACTIVE
        mock_license.max_users = 10
        mock_license.features = ["feature1"]

        mock_service.create_license.return_value = mock_license
        mock_license_service_class.return_value = mock_service

        # 测试数据
        license_data = {
            "organization_id": 1,
            "license_type": "commercial",
            "duration_days": 365,
            "max_users": 10,
        }

        # 发送请求
        response = client.post("/api/v1/licenses", json=license_data)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["license_key"] == "LICENSE-TEST-123456"
        assert data["organization_id"] == 1

    @patch("routes.license_routes.LicenseService")
    def test_validate_license_valid(self, mock_license_service_class):
        """测试有效许可证验证"""
        # 模拟服务返回
        mock_service = Mock()
        validation_result = {
            "is_valid": True,
            "license_info": {
                "license_key": "LICENSE-VALID-KEY",
                "status": "active",
                "max_users": 10,
            },
        }
        mock_service.validate_license.return_value = validation_result
        mock_license_service_class.return_value = mock_service

        # 发送请求
        response = client.post("/api/v1/licenses/LICENSE-VALID-KEY/validate")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["license_info"]["license_key"] == "LICENSE-VALID-KEY"

    @patch("routes.license_routes.LicenseService")
    def test_validate_license_invalid(self, mock_license_service_class):
        """测试无效许可证验证"""
        # 模拟服务返回无效结果
        mock_service = Mock()
        validation_result = {"is_valid": False, "error": "许可证已过期"}
        mock_service.validate_license.return_value = validation_result
        mock_license_service_class.return_value = mock_service

        # 发送请求
        response = client.post("/api/v1/licenses/LICENSE-INVALID-KEY/validate")

        # 验证响应
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "过期" in data["detail"]

    @patch("routes.license_routes.LicenseService")
    def test_revoke_license_success(self, mock_license_service_class):
        """测试成功撤销许可证"""
        # 模拟服务返回
        mock_service = Mock()
        mock_service.revoke_license.return_value = True
        mock_license_service_class.return_value = mock_service

        # 发送请求
        response = client.post("/api/v1/licenses/LICENSE-TO-REVOKE/revoke")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "撤销" in data["message"]

    @patch("routes.license_routes.LicenseService")
    def test_revoke_license_not_found(self, mock_license_service_class):
        """测试撤销不存在的许可证"""
        # 模拟服务返回False
        mock_service = Mock()
        mock_service.revoke_license.return_value = False
        mock_license_service_class.return_value = mock_service

        # 发送请求
        response = client.post("/api/v1/licenses/LICENSE-NOT-EXIST/revoke")

        # 验证响应
        assert response.status_code == 404

    @patch("routes.license_routes.LicenseService")
    def test_get_statistics(self, mock_license_service_class):
        """测试获取统计信息"""
        # 模拟服务返回
        mock_service = Mock()
        mock_stats = {
            "database_stats": {
                "total_licenses": 100,
                "active_licenses": 80,
                "expired_licenses": 15,
                "revoked_licenses": 5,
            },
            "cache_stats": {"total_licenses": 80},
        }
        mock_service.get_license_statistics.return_value = mock_stats
        mock_license_service_class.return_value = mock_service

        # 发送请求
        response = client.get("/api/v1/statistics")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "database_stats" in data
        assert "cache_stats" in data
        assert data["database_stats"]["total_licenses"] == 100

    @patch("routes.license_routes.LicenseService")
    def test_health_check(self, mock_license_service_class):
        """测试健康检查"""
        # 模拟服务
        mock_service = Mock()
        mock_license_service_class.return_value = mock_service

        # 发送请求
        response = client.get("/api/v1/health")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data


# 集成测试
class TestLicenseIntegration:
    """许可证集成测试"""

    def test_license_lifecycle(self):
        """测试完整的许可证生命周期"""
        # 这是一个高级集成测试示例
        # 在实际环境中需要真实的数据库和Redis

        with patch("routes.license_routes.LicenseService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # 1. 创建组织
            org_response = client.post(
                "/api/v1/organizations",
                json={"name": "集成测试组织", "contact_email": "integration@test.com"},
            )
            assert org_response.status_code == 200
            org_id = org_response.json()["id"]

            # 2. 生成许可证
            license_response = client.post(
                "/api/v1/licenses",
                json={"organization_id": org_id, "duration_days": 30, "max_users": 5},
            )
            assert license_response.status_code == 200
            license_key = license_response.json()["license_key"]

            # 3. 验证许可证
            validate_response = client.post(f"/api/v1/licenses/{license_key}/validate")
            assert validate_response.status_code == 200

            # 4. 撤销许可证
            revoke_response = client.post(f"/api/v1/licenses/{license_key}/revoke")
            assert revoke_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
