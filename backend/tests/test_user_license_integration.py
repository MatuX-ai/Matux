"""
用户与许可证对接功能集成测试
测试用户系统与许可证系统的完整对接功能
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.permission_middleware import (
    LicensePermissionValidator,
    require_admin,
    require_role,
)
from models.license import License, LicenseStatus, LicenseType, Organization
from models.user import User, UserRole
from models.user_license import UserLicense, UserLicenseStatus
from services.user_license_service import user_license_service


@pytest.fixture
def mock_db_session():
    """创建模拟数据库会话"""
    return Mock(spec=AsyncSession)


@pytest.fixture
def sample_user():
    """创建示例用户"""
    user = User()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = UserRole.USER
    user.is_active = True
    user.is_superuser = False
    return user


@pytest.fixture
def sample_admin_user():
    """创建示例管理员用户"""
    user = User()
    user.id = 2
    user.username = "admin"
    user.email = "admin@example.com"
    user.role = UserRole.ADMIN
    user.is_active = True
    user.is_superuser = True
    return user


@pytest.fixture
def sample_org_admin_user():
    """创建示例企业管理员用户"""
    user = User()
    user.id = 3
    user.username = "orgadmin"
    user.email = "orgadmin@example.com"
    user.role = UserRole.ORG_ADMIN
    user.is_active = True
    user.is_superuser = False
    return user


@pytest.fixture
def sample_organization():
    """创建示例组织"""
    org = Organization()
    org.id = 1
    org.name = "测试公司"
    org.contact_email = "contact@testcompany.com"
    org.is_active = True
    return org


@pytest.fixture
def sample_license(sample_organization):
    """创建示例许可证"""
    license_obj = License()
    license_obj.id = 1
    license_obj.license_key = "TEST-LICENSE-KEY-12345"
    license_obj.organization_id = sample_organization.id
    license_obj.organization = sample_organization
    license_obj.license_type = LicenseType.ENTERPRISE
    license_obj.status = LicenseStatus.ACTIVE
    license_obj.issued_at = datetime.utcnow()
    license_obj.expires_at = datetime.utcnow() + timedelta(days=365)
    license_obj.max_users = 100
    license_obj.max_devices = 50
    license_obj.features = ["feature1", "feature2", "feature3"]
    license_obj.is_active = True
    return license_obj


@pytest.fixture
def sample_user_license(sample_user, sample_license):
    """创建示例用户许可证关联"""
    user_license = UserLicense()
    user_license.id = 1
    user_license.user_id = sample_user.id
    user_license.license_id = sample_license.id
    user_license.user = sample_user
    user_license.license = sample_license
    user_license.role = UserRole.USER
    user_license.status = UserLicenseStatus.ACTIVE
    user_license.can_manage = False
    user_license.can_use = True
    user_license.can_view = True
    user_license.assigned_at = datetime.utcnow()
    user_license.expires_at = datetime.utcnow() + timedelta(days=365)
    return user_license


class TestUserLicenseModels:
    """用户许可证模型测试"""

    def test_user_license_creation(self, sample_user_license):
        """测试用户许可证关联创建"""
        assert sample_user_license.user_id == 1
        assert sample_user_license.license_id == 1
        assert sample_user_license.role == UserRole.USER
        assert sample_user_license.status == UserLicenseStatus.ACTIVE
        assert sample_user_license.can_use is True
        assert sample_user_license.is_expired is False
        assert sample_user_license.is_accessible is True

    def test_user_license_expiration(self):
        """测试用户许可证过期检查"""
        user_license = UserLicense()
        user_license.expires_at = datetime.utcnow() - timedelta(days=1)
        assert user_license.is_expired is True

        user_license.expires_at = datetime.utcnow() + timedelta(days=1)
        assert user_license.is_expired is False

    def test_user_has_role_methods(
        self, sample_user, sample_admin_user, sample_org_admin_user
    ):
        """测试用户角色检查方法"""
        # 普通用户
        assert sample_user.has_role(UserRole.USER) is True
        assert sample_user.has_role(UserRole.ADMIN) is False
        assert sample_user.has_any_role([UserRole.USER, UserRole.PREMIUM]) is True
        assert sample_user.can_manage_licenses() is False
        assert sample_user.is_admin() is False

        # 管理员用户
        assert sample_admin_user.has_role(UserRole.ADMIN) is True
        assert sample_admin_user.can_manage_licenses() is True
        assert sample_admin_user.is_admin() is True

        # 企业管理员用户
        assert sample_org_admin_user.has_role(UserRole.ORG_ADMIN) is True
        assert sample_org_admin_user.can_manage_licenses() is True
        assert sample_org_admin_user.is_admin() is True


class TestUserLicenseService:
    """用户许可证服务测试"""

    @pytest.mark.asyncio
    async def test_sync_user_with_sentinel_success(self, sample_user, mock_db_session):
        """测试成功同步用户到Sentinel"""
        with (
            patch.object(
                user_license_service, "get_user_active_licenses"
            ) as mock_get_licenses,
            patch.object(
                user_license_service, "store_tenant_info_in_redis"
            ) as mock_store_redis,
        ):

            # 模拟用户许可证数据
            mock_user_license = Mock()
            mock_user_license.license = Mock()
            mock_user_license.license.is_valid = True
            mock_user_license.license.id = 1
            mock_user_license.license.license_key = "TEST-LICENSE-123"
            mock_user_license.license.license_type = Mock(value="enterprise")
            mock_user_license.license.organization_id = 1
            mock_user_license.license.organization = Mock(name="测试公司")
            mock_user_license.license.expires_at = datetime.utcnow() + timedelta(
                days=365
            )
            mock_user_license.license.max_users = 100
            mock_user_license.license.features = ["feature1", "feature2"]
            mock_user_license.role = Mock(value="user")
            mock_user_license.can_manage = False
            mock_user_license.can_use = True
            mock_user_license.can_view = True
            mock_user_license.assigned_at = datetime.utcnow()

            mock_get_licenses.return_value = [mock_user_license]
            mock_store_redis.return_value = True

            result = await user_license_service.sync_user_with_sentinel(
                sample_user, mock_db_session
            )

            assert result["success"] is True
            assert result["user_id"] == sample_user.id
            assert len(result["tenant_info"]["licenses"]) == 1
            assert "feature1" in result["tenant_info"]["features"]
            assert "use_license" in result["tenant_info"]["permissions"]

    @pytest.mark.asyncio
    async def test_assign_license_to_user_success(
        self, sample_user, sample_admin_user, sample_license, mock_db_session
    ):
        """测试成功为用户分配许可证"""
        with (
            patch.object(mock_db_session, "execute") as mock_execute,
            patch.object(mock_db_session, "add") as mock_add,
            patch.object(mock_db_session, "commit") as mock_commit,
            patch.object(mock_db_session, "refresh") as mock_refresh,
            patch.object(user_license_service, "sync_user_with_sentinel") as mock_sync,
        ):

            # 模拟数据库查询结果
            mock_user_result = Mock()
            mock_user_result.scalar_one_or_none.return_value = sample_user
            mock_license_result = Mock()
            mock_license_result.scalar_one_or_none.return_value = sample_license
            mock_existing_result = Mock()
            mock_existing_result.scalar_one_or_none.return_value = None

            mock_execute.side_effect = [
                mock_user_result,  # 用户查询
                mock_license_result,  # 许可证查询
                mock_existing_result,  # 重复检查查询
            ]

            mock_sync.return_value = {"success": True}

            result = await user_license_service.assign_license_to_user(
                user_id=sample_user.id,
                license_id=sample_license.id,
                assigning_user=sample_admin_user,
                role=UserRole.USER,
                can_manage=False,
                can_use=True,
                db=mock_db_session,
            )

            assert result["success"] is True
            assert "user_license_id" in result
            assert result["sync_result"]["success"] is True

    @pytest.mark.asyncio
    async def test_assign_license_no_permission(
        self, sample_user, sample_user_license, mock_db_session
    ):
        """测试无权限分配许可证"""
        result = await user_license_service.assign_license_to_user(
            user_id=sample_user.id,
            license_id=1,
            assigning_user=sample_user,  # 普通用户无分配权限
            db=mock_db_session,
        )

        assert result["success"] is False
        assert "无权分配许可证" in result["error"]


class TestPermissionMiddleware:
    """权限中间件测试"""

    @pytest.mark.asyncio
    async def test_license_access_validation_admin(
        self, sample_admin_user, sample_license
    ):
        """测试管理员许可证访问权限"""
        with patch(
            "services.user_license_service.user_license_service"
        ) as mock_service:
            mock_service.validate_user_license_access.return_value = {
                "allowed": True,
                "reason": "管理员权限",
            }

            result = await LicensePermissionValidator.validate_license_access(
                sample_admin_user, sample_license.license_key, "use_license"
            )

            assert result["allowed"] is True
            assert result["reason"] == "管理员权限"

    @pytest.mark.asyncio
    async def test_license_access_validation_normal_user(
        self, sample_user, sample_license
    ):
        """测试普通用户许可证访问权限"""
        with patch(
            "services.user_license_service.user_license_service"
        ) as mock_service:
            mock_service.validate_user_license_access.return_value = {
                "allowed": True,
                "license_info": {"license_key": sample_license.license_key},
            }

            result = await LicensePermissionValidator.validate_license_access(
                sample_user, sample_license.license_key, "use_license"
            )

            assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_organization_access_validation(
        self, sample_org_admin_user, mock_db_session
    ):
        """测试组织访问权限验证"""
        with patch.object(
            user_license_service, "get_user_active_licenses"
        ) as mock_get_licenses:
            # 模拟用户拥有的许可证
            mock_user_license = Mock()
            mock_user_license.license = Mock()
            mock_user_license.license.organization_id = 1

            mock_get_licenses.return_value = [mock_user_license]

            result = await LicensePermissionValidator.validate_organization_access(
                sample_org_admin_user, organization_id=1, db=mock_db_session
            )

            assert result["allowed"] is True


class TestPermissionDecorators:
    """权限装饰器测试"""

    @pytest.mark.asyncio
    async def test_require_admin_decorator_success(self, sample_admin_user):
        """测试管理员权限装饰器成功情况"""

        @require_admin
        async def protected_function(current_user):
            return "success"

        result = await protected_function(current_user=sample_admin_user)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_require_admin_decorator_failure(self, sample_user):
        """测试管理员权限装饰器失败情况"""

        @require_admin
        async def protected_function(current_user):
            return "success"

        with pytest.raises(Exception) as exc_info:
            await protected_function(current_user=sample_user)

        assert "需要角色之一" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_require_role_decorator_multiple_roles(self, sample_org_admin_user):
        """测试多角色权限装饰器"""

        @require_role([UserRole.ADMIN, UserRole.ORG_ADMIN])
        async def protected_function(current_user):
            return "success"

        result = await protected_function(current_user=sample_org_admin_user)
        assert result == "success"


class TestAPIIntegration:
    """API集成测试"""

    def test_user_license_routes_structure(self):
        """测试用户许可证路由结构"""
        from routes.user_license_routes import router

        routes = [route.path for route in router.routes]
        expected_routes = [
            "/{user_id}/licenses",
            "/{user_id}/licenses",
            "/{user_id}/licenses/{license_id}",
            "/{user_id}/licenses/{license_id}",
            "/{user_id}/licenses/{license_id}",
            "/me/licenses",
        ]

        for expected_route in expected_routes:
            # 检查路由是否存在于路由器中
            route_exists = any(expected_route in route_path for route_path in routes)
            assert route_exists, f"路由 {expected_route} 不存在"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
