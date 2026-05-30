"""
许可证权限控制单元测试
测试基于许可证类型的功能访问限制
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, AsyncMock
from fastapi import HTTPException

from backend.middleware.license_permission import (
    LicensePermissionService,
    require_license_type,
    require_feature,
    PERMISSION_MATRIX,
    UPGRADE_SUGGESTIONS
)
from backend.models.license import LicenseType, License, LicenseStatus


class TestLicensePermissionService:
    """许可证权限服务测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = Mock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """创建服务实例"""
        return LicensePermissionService(mock_db)

    def test_check_feature_permission_allowed(self, service):
        """测试允许访问的功能"""
        # Windows 本地版访问 AI 课程生成应该被允许
        result = service.check_feature_permission(
            "ai_course_generation",
            LicenseType.WINDOWS_LOCAL
        )

        assert result["allowed"] == True
        assert result["reason"] == "权限验证通过"
        assert result["upgrade_suggestion"] == ""

    def test_check_feature_permission_denied(self, service):
        """测试拒绝访问的功能"""
        # 开源版访问 AI 聊天应该被拒绝
        result = service.check_feature_permission(
            "ai_chat_assistant",
            LicenseType.OPEN_SOURCE
        )

        assert result["allowed"] == False
        assert "不支持" in result["reason"]
        assert "升级" in result["upgrade_suggestion"]

    def test_check_feature_permission_cloud_sync(self, service):
        """测试云端同步功能权限"""
        # 云托管版可以访问云端同步
        result = service.check_feature_permission(
            "cloud_sync",
            LicenseType.CLOUD_HOSTED
        )
        assert result["allowed"] == True

        # Windows 本地版不能访问云端同步
        result = service.check_feature_permission(
            "cloud_sync",
            LicenseType.WINDOWS_LOCAL
        )
        assert result["allowed"] == False

    def test_check_feature_permission_offline_mode(self, service):
        """测试离线模式功能权限"""
        # Windows 本地版可以访问离线模式
        result = service.check_feature_permission(
            "offline_mode",
            LicenseType.WINDOWS_LOCAL
        )
        assert result["allowed"] == True

        # 云托管版不能访问离线模式
        result = service.check_feature_permission(
            "offline_mode",
            LicenseType.CLOUD_HOSTED
        )
        assert result["allowed"] == False

        # 企业版可以访问离线模式
        result = service.check_feature_permission(
            "offline_mode",
            LicenseType.ENTERPRISE
        )
        assert result["allowed"] == True

    def test_undefined_feature_default_allowed(self, service):
        """测试未定义功能默认允许"""
        result = service.check_feature_permission(
            "unknown_feature",
            LicenseType.OPEN_SOURCE
        )

        assert result["allowed"] == True
        assert "未设置权限限制" in result["reason"]

    def test_upgrade_suggestions_exist(self):
        """测试升级建议都存在"""
        for license_type, suggestion in UPGRADE_SUGGESTIONS.items():
            assert suggestion is not None
            assert len(suggestion) > 0
            assert isinstance(suggestion, str)


class TestRequireLicenseTypeDecorator:
    """许可证类型装饰器测试"""

    @pytest.mark.asyncio
    async def test_decorator_allows_access(self):
        """测试装饰器允许访问"""
        # 模拟用户和许可证
        mock_user = Mock(id="user123")
        mock_license = Mock()
        mock_license.status = LicenseStatus.ACTIVE
        mock_license.is_active = True
        mock_license.license_type = LicenseType.WINDOWS_LOCAL
        mock_license.is_expired = False

        # 模拟数据库
        mock_db = Mock()
        mock_db.query().filter().first.return_value = mock_license

        # 创建装饰的函数
        @require_license_type(LicenseType.WINDOWS_LOCAL, LicenseType.CLOUD_HOSTED)
        async def protected_function(*args, **kwargs):
            return {"success": True}

        # 调用函数（应该成功）
        try:
            result = await protected_function(
                current_user=mock_user,
                db=mock_db
            )
            assert result["success"] == True
        except HTTPException as e:
            pytest.fail(f"Unexpected HTTPException: {e}")

    @pytest.mark.asyncio
    async def test_decorator_denies_insufficient_license(self):
        """测试装饰器拒绝许可证不足的用户"""
        # 模拟开源版用户
        mock_user = Mock(id="user123")
        mock_license = Mock()
        mock_license.status = LicenseStatus.ACTIVE
        mock_license.is_active = True
        mock_license.license_type = LicenseType.OPEN_SOURCE
        mock_license.is_expired = False

        # 模拟数据库
        mock_db = Mock()
        mock_db.query().filter().first.return_value = mock_license

        # 创建装饰的函数（需要付费版）
        @require_license_type(LicenseType.WINDOWS_LOCAL, LicenseType.CLOUD_HOSTED)
        async def protected_function(*args, **kwargs):
            return {"success": True}

        # 调用函数（应该抛出 403）
        with pytest.raises(HTTPException) as exc_info:
            await protected_function(
                current_user=mock_user,
                db=mock_db
            )

        assert exc_info.value.status_code == 403
        assert "insufficient_license" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_decorator_denies_no_license(self):
        """测试装饰器拒绝无许可证的用户"""
        # 模拟无许可证用户
        mock_user = Mock(id="user123")

        # 模拟数据库（返回 None）
        mock_db = Mock()
        mock_db.query().filter().first.return_value = None

        # 创建装饰的函数
        @require_license_type(LicenseType.WINDOWS_LOCAL)
        async def protected_function(*args, **kwargs):
            return {"success": True}

        # 调用函数（应该抛出 403）
        with pytest.raises(HTTPException) as exc_info:
            await protected_function(
                current_user=mock_user,
                db=mock_db
            )

        assert exc_info.value.status_code == 403
        assert "no_license" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_decorator_denies_expired_license(self):
        """测试装饰器拒绝过期许可证"""
        # 模拟过期许可证
        mock_user = Mock(id="user123")
        mock_license = Mock()
        mock_license.status = LicenseStatus.ACTIVE
        mock_license.is_active = True
        mock_license.license_type = LicenseType.WINDOWS_LOCAL
        mock_license.is_expired = True  # 已过期

        # 模拟数据库
        mock_db = Mock()
        mock_db.query().filter().first.return_value = mock_license

        # 创建装饰的函数
        @require_license_type(LicenseType.WINDOWS_LOCAL)
        async def protected_function(*args, **kwargs):
            return {"success": True}

        # 调用函数（应该抛出 403）
        with pytest.raises(HTTPException) as exc_info:
            await protected_function(
                current_user=mock_user,
                db=mock_db
            )

        assert exc_info.value.status_code == 403
        assert "expired_license" in str(exc_info.value.detail)


class TestRequireFeatureDecorator:
    """功能权限装饰器测试"""

    @pytest.mark.asyncio
    async def test_feature_decorator_allows_access(self):
        """测试功能装饰器允许访问"""
        # 模拟云托管版用户
        mock_user = Mock(id="user123")
        mock_license = Mock()
        mock_license.status = LicenseStatus.ACTIVE
        mock_license.is_active = True
        mock_license.license_type = LicenseType.CLOUD_HOSTED
        mock_license.is_expired = False

        # 模拟数据库
        mock_db = Mock()
        mock_db.query().filter().first.return_value = mock_license

        # 创建装饰的函数（云托管版可以访问 cloud_sync）
        @require_feature("cloud_sync")
        async def protected_function(*args, **kwargs):
            return {"success": True}

        # 调用函数（应该成功）
        try:
            result = await protected_function(
                current_user=mock_user,
                db=mock_db
            )
            assert result["success"] == True
        except HTTPException as e:
            pytest.fail(f"Unexpected HTTPException: {e}")

    @pytest.mark.asyncio
    async def test_feature_decorator_denies_access(self):
        """测试功能装饰器拒绝访问"""
        # 模拟开源版用户
        mock_user = Mock(id="user123")
        mock_license = Mock()
        mock_license.status = LicenseStatus.ACTIVE
        mock_license.is_active = True
        mock_license.license_type = LicenseType.OPEN_SOURCE
        mock_license.is_expired = False

        # 模拟数据库
        mock_db = Mock()
        mock_db.query().filter().first.return_value = mock_license

        # 创建装饰的函数（开源版不能访问 cloud_sync）
        @require_feature("cloud_sync")
        async def protected_function(*args, **kwargs):
            return {"success": True}

        # 调用函数（应该抛出 403）
        with pytest.raises(HTTPException) as exc_info:
            await protected_function(
                current_user=mock_user,
                db=mock_db
            )

        assert exc_info.value.status_code == 403
        assert "feature_not_allowed" in str(exc_info.value.detail)


class TestPermissionMatrix:
    """权限矩阵完整性测试"""

    def test_all_license_types_covered(self):
        """测试所有许可证类型都在矩阵中定义"""
        all_license_types = set(LicenseType)

        for feature, permissions in PERMISSION_MATRIX.items():
            defined_types = set(permissions.keys())
            missing_types = all_license_types - defined_types

            assert len(missing_types) == 0, \
                f"Feature '{feature}' missing license types: {missing_types}"

    def test_boolean_values_only(self):
        """测试权限矩阵只包含布尔值"""
        for feature, permissions in PERMISSION_MATRIX.items():
            for license_type, allowed in permissions.items():
                assert isinstance(allowed, bool), \
                    f"Feature '{feature}' has non-boolean value for {license_type}"

    def test_key_features_defined(self):
        """测试关键功能都已定义"""
        required_features = [
            "course_management",
            "user_management",
            "ai_course_generation",
            "ai_chat_assistant",
            "offline_mode",
            "cloud_sync",
            "token_billing"
        ]

        for feature in required_features:
            assert feature in PERMISSION_MATRIX, \
                f"Required feature '{feature}' not defined in permission matrix"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
