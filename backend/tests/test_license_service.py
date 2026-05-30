"""
许可证服务单元测试
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from models.license import LicenseCreate, LicenseStatus, LicenseType
from services.license_service import LicenseService
from utils.redis_client import redis_license_store


class TestLicenseService:
    """许可证服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)

    @pytest.fixture
    def license_service(self, mock_db):
        """创建许可证服务实例"""
        return LicenseService(mock_db)

    def test_generate_license_key(self, license_service):
        """测试许可证密钥生成"""
        license_key = license_service._generate_license_key()

        # 验证密钥格式
        assert license_key is not None
        assert isinstance(license_key, str)
        assert len(license_key) > 10  # 至少包含前缀和基本长度

        # 验证包含正确的分隔符
        parts = license_key.split("-")
        assert len(parts) == 3
        assert parts[0] == "LICENSE"  # 默认前缀

    def test_validate_license_key_format_valid(self, license_service):
        """测试有效许可证密钥格式验证"""
        # 创建一个有效的测试密钥
        test_key = "LICENSE-ABCDEF123456-1A2B"
        with patch.object(
            license_service, "_validate_license_key_format", return_value=True
        ):
            result = license_service._validate_license_key_format(test_key)
            assert result == True

    def test_validate_license_key_format_invalid(self, license_service):
        """测试无效许可证密钥格式验证"""
        invalid_keys = [
            "",  # 空字符串
            "INVALID-FORMAT",  # 格式错误
            "LICENSE-TOO-SHORT-X",  # 长度不够
            "LICENSE-WRONG-PREFIX-123456-ABC",  # 前缀错误
        ]

        for invalid_key in invalid_keys:
            result = license_service._validate_license_key_format(invalid_key)
            assert result == False

    @patch("services.license_service.datetime")
    def test_create_organization_success(self, mock_datetime, license_service, mock_db):
        """测试成功创建组织"""
        # 模拟当前时间
        mock_now = datetime(2026, 1, 1)
        mock_datetime.utcnow.return_value = mock_now

        # 模拟数据库操作
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_organization = Mock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = mock_organization

        # 测试数据
        org_data = {
            "name": "测试组织",
            "contact_email": "test@example.com",
            "max_users": 100,
        }

        # 执行测试
        result = license_service.create_organization(org_data)

        # 验证结果
        assert result == mock_organization
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_organization_duplicate_email(self, license_service, mock_db):
        """测试重复邮箱创建组织"""
        # 模拟已存在的组织
        existing_org = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = existing_org

        org_data = {
            "name": "测试组织",
            "contact_email": "existing@example.com",
            "max_users": 100,
        }

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="邮箱已存在"):
            license_service.create_organization(org_data)

    @patch("services.license_service.datetime")
    @patch.object(redis_license_store, "store_license")
    def test_create_license_success(
        self, mock_store_license, mock_datetime, license_service, mock_db
    ):
        """测试成功创建许可证"""
        # 模拟时间
        mock_now = datetime(2026, 1, 1)
        mock_datetime.utcnow.return_value = mock_now

        # 模拟组织存在
        mock_organization = Mock()
        mock_organization.id = 1
        mock_organization.name = "测试组织"
        mock_organization.is_active = True
        mock_organization.license_count = 0

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_organization,  # 组织查询
            None,  # 许可证密钥唯一性检查
        ]

        # 模拟许可证创建
        mock_license = Mock()
        mock_license.id = 1
        mock_license.license_key = "LICENSE-TEST-KEY-1234"
        mock_license.organization_id = 1
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = mock_license

        # 测试数据
        license_create = LicenseCreate(
            organization_id=1,
            license_type=LicenseType.COMMERCIAL,
            duration_days=365,
            max_users=10,
            max_devices=5,
        )

        # 执行测试
        result = license_service.create_license(license_create)

        # 验证结果
        assert result == mock_license
        assert result.license_key.startswith("LICENSE-")
        mock_db.commit.assert_called()
        mock_store_license.assert_called_once()

    def test_create_license_organization_not_found(self, license_service, mock_db):
        """测试组织不存在时创建许可证"""
        # 模拟组织不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        license_create = LicenseCreate(
            organization_id=999,  # 不存在的组织ID
            license_type=LicenseType.COMMERCIAL,
            duration_days=365,
        )

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="指定的组织不存在"):
            license_service.create_license(license_create)

    @patch.object(redis_license_store, "get_license")
    @patch.object(redis_license_store, "store_license")
    def test_validate_license_cache_hit_valid(
        self, mock_store_license, mock_get_license, license_service, mock_db
    ):
        """测试缓存命中且有效的情况"""
        # 模拟缓存中的有效许可证
        cached_license = {
            "license_key": "LICENSE-VALID-KEY",
            "status": "active",
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }
        mock_get_license.return_value = cached_license

        # 执行测试
        result = license_service.validate_license("LICENSE-VALID-KEY")

        # 验证结果
        assert result["is_valid"] == True
        assert result["license_info"] == cached_license
        mock_get_license.assert_called_once_with("LICENSE-VALID-KEY")
        mock_db.query.assert_not_called()  # 不应该查询数据库

    @patch.object(redis_license_store, "get_license")
    def test_validate_license_cache_miss_then_db_valid(
        self, mock_get_license, license_service, mock_db
    ):
        """测试缓存未命中但从数据库找到有效许可证"""
        # 模拟缓存未命中
        mock_get_license.return_value = None

        # 模拟数据库中的有效许可证
        mock_license = Mock()
        mock_license.id = 1
        mock_license.license_key = "LICENSE-DB-VALID"
        mock_license.status = LicenseStatus.ACTIVE
        mock_license.is_expired = False
        mock_license.is_active = True
        mock_license.expires_at = datetime.utcnow() + timedelta(days=30)
        mock_license.issued_at = datetime.utcnow()
        mock_license.max_users = 10
        mock_license.current_users = 5
        mock_license.features = ["feature1", "feature2"]

        mock_db.query.return_value.filter.return_value.first.return_value = mock_license

        # 执行测试
        result = license_service.validate_license("LICENSE-DB-VALID")

        # 验证结果
        assert result["is_valid"] == True
        assert result["license_info"] is not None
        assert result["license_info"]["license_key"] == "LICENSE-DB-VALID"

    def test_validate_license_not_found(self, license_service, mock_db):
        """测试许可证不存在"""
        # 模拟缓存和数据库都找不到许可证
        with patch.object(redis_license_store, "get_license", return_value=None):
            mock_db.query.return_value.filter.return_value.first.return_value = None

            result = license_service.validate_license("LICENSE-NOT-EXIST")

            assert result["is_valid"] == False
            assert result["error"] == "许可证不存在"

    def test_validate_license_expired(self, license_service, mock_db):
        """测试许可证过期"""
        # 模拟缓存未命中
        with patch.object(redis_license_store, "get_license", return_value=None):
            # 模拟数据库中的过期许可证
            mock_license = Mock()
            mock_license.status = LicenseStatus.ACTIVE
            mock_license.is_expired = True
            mock_license.is_active = True

            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_license
            )

            result = license_service.validate_license("LICENSE-EXPIRED")

            assert result["is_valid"] == False
            assert result["error"] == "许可证已过期"
            # 验证状态被更新
            assert mock_license.status == LicenseStatus.EXPIRED

    def test_revoke_license_success(self, license_service, mock_db):
        """测试成功撤销许可证"""
        with patch.object(redis_license_store, "delete_license") as mock_delete_license:
            # 模拟存在的许可证
            mock_license = Mock()
            mock_license.organization_id = 1

            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_license
            )

            # 执行测试
            result = license_service.revoke_license("LICENSE-TO-REVOKE")

            # 验证结果
            assert result == True
            assert mock_license.status == LicenseStatus.REVOKED
            assert mock_license.is_active == False
            mock_db.commit.assert_called_once()
            mock_delete_license.assert_called_once_with("LICENSE-TO-REVOKE")

    def test_revoke_license_not_found(self, license_service, mock_db):
        """测试撤销不存在的许可证"""
        # 模拟许可证不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = license_service.revoke_license("LICENSE-NOT-EXIST")

        assert result == False
        mock_db.commit.assert_not_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
