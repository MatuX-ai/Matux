"""
权限系统单元测试
测试RBAC权限管理的各项功能
"""

from unittest.mock import AsyncMock, Mock, patch

from fastapi import HTTPException
import pytest

from models.permission import Permission, Role, UserRoleAssignment
from models.user import User, UserRole
from services.permission_service import permission_service
from utils.decorators import admin_required, require_permission, require_role


@pytest.fixture
def sample_user():
    """创建测试用户"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.role = UserRole.USER
    user.is_active = True
    user.is_superuser = False
    return user


@pytest.fixture
def sample_admin_user():
    """创建测试管理员用户"""
    user = Mock(spec=User)
    user.id = 2
    user.username = "admin"
    user.email = "admin@example.com"
    user.role = UserRole.ADMIN
    user.is_active = True
    user.is_superuser = True
    return user


@pytest.fixture
def sample_permissions():
    """创建测试权限"""
    perms = []
    for i, code in enumerate(["user.read", "user.write", "user.delete"]):
        perm = Mock(spec=Permission)
        perm.id = i + 1
        perm.code = code
        perm.name = f"权限{i+1}"
        perm.category = "user"
        perm.action = code.split(".")[1]
        perms.append(perm)
    return perms


@pytest.fixture
def sample_roles(sample_permissions):
    """创建测试角色"""
    role = Mock(spec=Role)
    role.id = 1
    role.code = "test_role"
    role.name = "测试角色"
    role.description = "用于测试的角色"
    role.is_system = False
    role.is_active = True
    role.priority = 50
    role.permissions = sample_permissions
    return role


class TestPermissionModels:
    """权限模型测试"""

    def test_user_has_permission(self, sample_user, sample_permissions):
        """测试用户权限检查"""
        # 设置用户权限
        sample_user.get_permissions.return_value = sample_permissions

        # 测试存在的权限
        assert sample_user.has_permission("user.read") is True

        # 测试不存在的权限
        assert sample_user.has_permission("user.manage") is False

    def test_user_has_any_permission(self, sample_user, sample_permissions):
        """测试用户任一权限检查"""
        sample_user.get_permissions.return_value = sample_permissions

        # 测试包含任一权限
        assert sample_user.has_any_permission(["user.read", "user.manage"]) is True

        # 测试不包含任何权限
        assert sample_user.has_any_permission(["user.manage", "user.admin"]) is False

    def test_user_has_all_permissions(self, sample_user, sample_permissions):
        """测试用户所有权限检查"""
        sample_user.get_permissions.return_value = sample_permissions

        # 测试包含所有权限
        assert sample_user.has_all_permissions(["user.read", "user.write"]) is True

        # 测试不包含所有权限
        assert sample_user.has_all_permissions(["user.read", "user.manage"]) is False


class TestPermissionService:
    """权限服务测试"""

    @pytest.mark.asyncio
    async def test_initialize_system_permissions(self):
        """测试初始化系统权限"""
        with patch("services.permission_service.get_async_db") as mock_get_db:
            # 模拟数据库会话
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            # 模拟查询结果（权限不存在）
            mock_db.execute.return_value.scalar_one_or_none.return_value = None

            # 执行初始化
            permission_map = await permission_service.initialize_system_permissions(
                mock_db
            )

            # 验证权限被创建
            assert len(permission_map) > 0
            mock_db.add.assert_called()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_system_roles(self):
        """测试初始化系统角色"""
        with patch("services.permission_service.get_async_db") as mock_get_db:
            # 模拟数据库会话
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            # 模拟权限映射
            with patch.object(
                permission_service, "initialize_system_permissions"
            ) as mock_init_perms:
                mock_init_perms.return_value = {"user.read": 1, "user.write": 2}

                # 模拟查询结果（角色不存在）
                mock_db.execute.return_value.scalar_one_or_none.return_value = None

                # 执行初始化
                role_map = await permission_service.initialize_system_roles(mock_db)

                # 验证角色被创建
                assert len(role_map) > 0
                mock_db.add.assert_called()
                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_role_to_user_success(self, sample_user, sample_roles):
        """测试成功分配角色给用户"""
        with patch("services.permission_service.get_async_db") as mock_get_db:
            # 模拟数据库会话
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            # 模拟查询结果
            mock_db.execute.side_effect = [
                AsyncMock(
                    scalar_one_or_none=Mock(return_value=sample_roles)
                ),  # 角色查询
                AsyncMock(
                    scalar_one_or_none=Mock(return_value=sample_user)
                ),  # 用户查询
                AsyncMock(scalar_one_or_none=Mock(return_value=None)),  # 分配检查
            ]

            # 执行分配
            assignment = await permission_service.assign_role_to_user(
                user_id=1, role_code="test_role", assigned_by=2, db=mock_db
            )

            # 验证结果
            assert assignment is not None
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_role_to_user_duplicate(self, sample_user, sample_roles):
        """测试重复分配角色"""
        with patch("services.permission_service.get_async_db") as mock_get_db:
            # 模拟数据库会话
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            # 模拟已有分配记录
            existing_assignment = Mock(spec=UserRoleAssignment)
            existing_assignment.is_active = True
            existing_assignment.expires_at = None

            mock_db.execute.side_effect = [
                AsyncMock(
                    scalar_one_or_none=Mock(return_value=sample_roles)
                ),  # 角色查询
                AsyncMock(
                    scalar_one_or_none=Mock(return_value=sample_user)
                ),  # 用户查询
                AsyncMock(
                    scalar_one_or_none=Mock(return_value=existing_assignment)
                ),  # 分配检查
            ]

            # 执行分配应该抛出异常
            with pytest.raises(HTTPException) as exc_info:
                await permission_service.assign_role_to_user(
                    user_id=1, role_code="test_role", assigned_by=2, db=mock_db
                )

            assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_revoke_role_from_user_success(self, sample_user, sample_roles):
        """测试成功撤销用户角色"""
        with patch("services.permission_service.get_async_db") as mock_get_db:
            # 模拟数据库会话
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            # 模拟分配记录
            assignment = Mock(spec=UserRoleAssignment)
            assignment.role = sample_roles
            assignment.is_active = True

            mock_db.execute.return_value.scalar_one_or_none.return_value = assignment

            # 执行撤销
            result = await permission_service.revoke_role_from_user(
                user_id=1, role_code="test_role", revoked_by=2, db=mock_db
            )

            # 验证结果
            assert result is True
            assert assignment.is_active is False
            assert assignment.revoked_at is not None
            mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_permissions(self, sample_user, sample_permissions):
        """测试获取用户权限"""
        with patch("services.permission_service.get_async_db") as mock_get_db:
            # 模拟数据库会话
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            # 模拟分配记录
            assignment = Mock(spec=UserRoleAssignment)
            assignment.role_id = 1

            # 模拟查询结果
            mock_db.execute.side_effect = [
                AsyncMock(
                    scalars=Mock(return_value=Mock(all=Mock(return_value=[assignment])))
                ),  # 分配查询
                AsyncMock(
                    scalars=Mock(
                        return_value=Mock(all=Mock(return_value=sample_permissions))
                    )
                ),  # 权限查询
            ]

            # 执行查询
            permissions = await permission_service.get_user_permissions(1, mock_db)

            # 验证结果
            assert len(permissions) == len(sample_permissions)
            assert permissions == sample_permissions

    @pytest.mark.asyncio
    async def test_check_user_permission(self, sample_user, sample_permissions):
        """测试检查用户权限"""
        with patch.object(permission_service, "get_user_permissions") as mock_get_perms:
            mock_get_perms.return_value = sample_permissions

            # 测试存在的权限
            result = await permission_service.check_user_permission(1, "user.read")
            assert result is True

            # 测试不存在的权限
            result = await permission_service.check_user_permission(1, "user.manage")
            assert result is False

    @pytest.mark.asyncio
    async def test_log_permission_change(self):
        """测试记录权限变更日志"""
        with patch("services.permission_service.get_async_db") as mock_get_db:
            # 模拟数据库会话
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            # 执行日志记录
            log_entry = await permission_service.log_permission_change(
                user_id=1,
                target_user_id=2,
                action_type="assign_role",
                resource_type="role",
                role_code="test_role",
                description="测试分配角色",
                db=mock_db,
            )

            # 验证结果
            assert log_entry is not None
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()


class TestPermissionDecorators:
    """权限装饰器测试"""

    @pytest.mark.asyncio
    async def test_require_role_success(self, sample_admin_user):
        """测试角色权限装饰器成功情况"""

        # 创建测试函数
        @require_role(UserRole.ADMIN)
        async def test_function(current_user=None):
            return "success"

        # 执行测试
        result = await test_function(current_user=sample_admin_user)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_require_role_failure(self, sample_user):
        """测试角色权限装饰器失败情况"""

        # 创建测试函数
        @require_role(UserRole.ADMIN)
        async def test_function(current_user=None):
            return "success"

        # 执行测试应该抛出异常
        with pytest.raises(HTTPException) as exc_info:
            await test_function(current_user=sample_user)

        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_require_permission_success(self, sample_user, sample_permissions):
        """测试权限装饰器成功情况"""
        # 模拟权限服务
        with patch("utils.decorators.permission_service") as mock_service:
            mock_service.check_user_has_all_permissions.return_value = True

            # 创建测试函数
            @require_permission("user.read")
            async def test_function(current_user=None, db=None):
                return "success"

            # 执行测试
            result = await test_function(current_user=sample_user, db=AsyncMock())
            assert result == "success"

    @pytest.mark.asyncio
    async def test_require_permission_failure(self, sample_user):
        """测试权限装饰器失败情况"""
        # 模拟权限服务
        with patch("utils.decorators.permission_service") as mock_service:
            mock_service.check_user_has_all_permissions.return_value = False

            # 创建测试函数
            @require_permission("user.manage")
            async def test_function(current_user=None, db=None):
                return "success"

            # 执行测试应该抛出异常
            with pytest.raises(HTTPException) as exc_info:
                await test_function(current_user=sample_user, db=AsyncMock())

            assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_required(self, sample_admin_user, sample_user):
        """测试管理员权限装饰器"""

        # 创建测试函数
        @admin_required()
        async def test_function(current_user=None):
            return "success"

        # 管理员应该成功
        result = await test_function(current_user=sample_admin_user)
        assert result == "success"

        # 普通用户应该失败
        with pytest.raises(HTTPException) as exc_info:
            await test_function(current_user=sample_user)

        assert exc_info.value.status_code == 403


class TestPermissionIntegration:
    """权限系统集成测试"""

    @pytest.mark.asyncio
    async def test_full_permission_flow(self):
        """测试完整的权限流程"""
        with patch("services.permission_service.get_async_db") as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value.__aiter__.return_value = [mock_db]

            # 1. 初始化权限系统
            with patch.object(
                permission_service, "initialize_system_permissions"
            ) as mock_init_perms:
                mock_init_perms.return_value = {"user.read": 1, "user.write": 2}

                with patch.object(
                    permission_service, "initialize_system_roles"
                ) as mock_init_roles:
                    mock_init_roles.return_value = {"admin": 1, "user": 2}

                    # 2. 创建用户和角色
                    user = Mock(spec=User)
                    user.id = 1
                    user.username = "testuser"
                    user.role = UserRole.USER

                    role = Mock(spec=Role)
                    role.id = 2
                    role.code = "user"
                    role.name = "普通用户"

                    # 3. 分配角色
                    mock_db.execute.side_effect = [
                        AsyncMock(
                            scalar_one_or_none=Mock(return_value=role)
                        ),  # 角色查询
                        AsyncMock(
                            scalar_one_or_none=Mock(return_value=user)
                        ),  # 用户查询
                        AsyncMock(
                            scalar_one_or_none=Mock(return_value=None)
                        ),  # 分配检查
                    ]

                    assignment = await permission_service.assign_role_to_user(
                        user_id=1, role_code="user", assigned_by=1, db=mock_db
                    )

                    assert assignment is not None

                    # 4. 检查权限
                    mock_service = AsyncMock()
                    mock_service.check_user_permission.return_value = True

                    has_permission = await permission_service.check_user_permission(
                        1, "user.read", mock_db
                    )

                    assert has_permission is True

                    # 5. 记录日志
                    log_entry = await permission_service.log_permission_change(
                        user_id=1,
                        target_user_id=1,
                        action_type="test_action",
                        resource_type="test_resource",
                        description="集成测试",
                        db=mock_db,
                    )

                    assert log_entry is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
