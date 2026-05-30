"""
权限分级中间件
实现基于角色和许可证的访问控制
"""

import logging
from typing import Awaitable, Callable, List

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from models.user import User, UserRole
from services.user_license_service import user_license_service

logger = logging.getLogger(__name__)


class PermissionMiddleware(BaseHTTPMiddleware):
    """权限控制中间件"""

    def __init__(self, app):
        super().__init__(app)
        self.excluded_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/token",
            "/api/v1/auth/register",
            "/health",
        ]

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable]
    ):
        # ✅ 跳过 OPTIONS 预检请求 (CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # 检查是否需要跳过权限验证
        if self.should_skip_permission_check(request.url.path):
            return await call_next(request)

        try:
            # 获取当前用户
            current_user = (
                request.state.current_user
                if hasattr(request.state, "current_user")
                else None
            )

            if not current_user:
                # 尝试从认证头获取用户
                current_user = await self.get_current_user_from_request(request)
                if current_user:
                    request.state.current_user = current_user

            if current_user:
                # 验证用户权限
                permission_result = await self.validate_user_permissions(
                    current_user, request
                )

                if not permission_result["allowed"]:
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "detail": permission_result["reason"],
                            "required_permission": permission_result.get(
                                "required_permission"
                            ),
                        },
                    )

            # 继续处理请求
            response = await call_next(request)
            return response

        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"权限中间件处理异常: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "权限验证内部错误"},
            )

    def should_skip_permission_check(self, path: str) -> bool:
        """判断是否跳过权限检查"""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)


class LicensePermissionValidator:
    """许可证权限验证器"""

    @staticmethod
    async def validate_license_access(
        user: User,
        license_key: str,
        required_permission: str = "use_license",
        db: AsyncSession = None,
    ) -> dict:
        """
        验证用户对特定许可证的访问权限

        Args:
            user: 用户对象
            license_key: 许可证密钥
            required_permission: 所需权限 ('use_license', 'manage_license')
            db: 数据库会话

        Returns:
            包含验证结果的字典
        """
        try:
            # 对于管理员用户，允许访问所有许可证
            if user.is_admin():
                return {
                    "allowed": True,
                    "reason": "管理员权限",
                    "user_role": user.role.value if user.role else "unknown",
                }

            # 验证普通用户的许可证权限
            result = await user_license_service.validate_user_license_access(
                user.id, license_key, required_permission
            )

            return result

        except Exception as e:
            logger.error(f"验证用户 {user.username} 许可证权限失败: {e}")
            return {"allowed": False, "reason": f"权限验证异常: {str(e)}"}

    @staticmethod
    async def validate_organization_access(
        user: User,
        organization_id: int,
        required_role: UserRole = None,
        db: AsyncSession = None,
    ) -> dict:
        """
        验证用户对企业/组织的访问权限

        Args:
            user: 用户对象
            organization_id: 组织ID
            required_role: 所需最低角色
            db: 数据库会话

        Returns:
            包含验证结果的字典
        """
        try:
            # 管理员可以访问所有组织
            if user.is_admin():
                return {"allowed": True, "reason": "管理员权限"}

            # 企业管理员只能访问自己的组织
            if user.role == UserRole.ORG_ADMIN:
                # 这里需要查询用户所属的组织
                # 简化实现：假设通过许可证关联确定组织
                user_licenses = await user_license_service.get_user_active_licenses(
                    user.id, db
                )
                org_ids = {
                    ul.license.organization_id for ul in user_licenses if ul.license
                }

                if organization_id in org_ids:
                    return {"allowed": True, "reason": "企业管理员权限"}
                else:
                    return {"allowed": False, "reason": "无权访问此组织"}

            # 普通用户需要有相应的许可证关联
            user_licenses = await user_license_service.get_user_active_licenses(
                user.id, db
            )
            org_ids = {ul.license.organization_id for ul in user_licenses if ul.license}

            if organization_id in org_ids:
                return {"allowed": True, "reason": "用户关联的组织"}
            else:
                return {"allowed": False, "reason": "用户未关联此组织"}

        except Exception as e:
            logger.error(f"验证用户 {user.username} 组织权限失败: {e}")
            return {"allowed": False, "reason": f"权限验证异常: {str(e)}"}


def require_permission(permission: str):
    """权限装饰器工厂函数"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取当前用户（从依赖注入或其他方式）
            current_user = kwargs.get("current_user") or args[0] if args else None

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证的用户"
                )

            # 验证权限
            if not await has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少权限: {permission}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def has_permission(user: User, permission: str) -> bool:
    """检查用户是否具有指定权限"""
    # 管理员拥有所有权限
    if user.is_admin():
        return True

    # 从Redis获取用户的权限信息
    tenant_info = await user_license_service.get_user_tenant_info(user.id)
    if tenant_info:
        user_permissions = tenant_info.get("permissions", [])
        return permission in user_permissions

    return False


def require_role(required_roles: List[UserRole]):
    """角色要求装饰器"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user") or args[0] if args else None

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证的用户"
                )

            if not current_user.has_any_role(required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要角色之一: {[role.value for role in required_roles]}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# 预定义的权限装饰器
require_admin = require_role([UserRole.ADMIN])
require_org_admin = require_role([UserRole.ADMIN, UserRole.ORG_ADMIN])
require_premium = require_role([UserRole.ADMIN, UserRole.ORG_ADMIN, UserRole.PREMIUM])
