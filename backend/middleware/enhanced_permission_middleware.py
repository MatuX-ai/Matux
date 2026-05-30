"""
增强版权限验证中间件
支持多租户权限控制和细粒度API权限管理
"""

import logging
from typing import Awaitable, Callable, List, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from models.user import User, UserRole
from utils.database import get_sync_db
from utils.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class EnhancedPermissionMiddleware(BaseHTTPMiddleware):
    """增强版权限控制中间件"""

    def __init__(self, app):
        super().__init__(app)
        self.excluded_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/token",
            "/api/v1/auth/register",
            "/health",
            "/favicon.ico",
            "/static/",
        ]

    async def dispatch(self, request: Request, call_next):
        """处理请求的调度方法"""
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

            # 清理租户上下文
            TenantContext.clear()

            return response

        except HTTPException as he:
            # 清理租户上下文
            TenantContext.clear()
            raise he
        except Exception as e:
            logger.error(f"权限中间件处理异常: {e}")
            TenantContext.clear()
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "权限验证内部错误"},
            )

    async def validate_user_permissions(self, user: User, request: Request) -> dict:
        """
        验证用户权限

        Args:
            user: 用户对象
            request: 请求对象

        Returns:
            包含验证结果的字典
        """
        # 检查用户是否被禁用
        if not user.is_active:
            return {"allowed": False, "reason": "用户账号已被禁用"}

        # 检查多租户权限
        tenant_permission_result = await self.validate_tenant_permissions(user, request)
        if not tenant_permission_result["allowed"]:
            return tenant_permission_result

        # 检查API特定权限
        api_permission_result = await self.validate_api_specific_permissions(
            user, request
        )
        if not api_permission_result["allowed"]:
            return api_permission_result

        return {"allowed": True, "reason": "权限验证通过"}

    async def validate_tenant_permissions(self, user: User, request: Request) -> dict:
        """
        验证多租户权限

        Args:
            user: 用户对象
            request: 请求对象

        Returns:
            包含验证结果的字典
        """
        # 从URL中提取org_id
        path_parts = request.url.path.split("/")
        org_id = None

        # 查找org_id参数
        for i, part in enumerate(path_parts):
            if part == "org" and i + 1 < len(path_parts):
                try:
                    org_id = int(path_parts[i + 1])
                    break
                except (ValueError, IndexError):
                    continue

        # 如果没有org_id，且不是公共API，则拒绝访问
        if org_id is None:
            public_apis = ["/api/v1/auth", "/health", "/docs", "/redoc"]

            if not any(request.url.path.startswith(api) for api in public_apis):
                return {"allowed": False, "reason": "缺少租户标识"}

            return {"allowed": True, "reason": "公共API无需租户验证"}

        # 验证用户对该租户的访问权限
        tenant_access_result = await self.check_tenant_access(user, org_id)
        if not tenant_access_result["allowed"]:
            return tenant_access_result

        # 设置租户上下文
        TenantContext.set_current_tenant(org_id)

        return {"allowed": True, "reason": "租户权限验证通过"}

    async def check_tenant_access(self, user: User, org_id: int) -> dict:
        """
        检查用户对指定租户的访问权限

        Args:
            user: 用户对象
            org_id: 组织ID

        Returns:
            包含验证结果的字典
        """
        # 系统管理员可以访问所有租户
        if user.is_superuser or user.role == UserRole.ADMIN:
            return {"allowed": True, "reason": "管理员权限"}

        # 企业管理员只能访问自己的租户
        if user.role == UserRole.ORG_ADMIN:
            # 这里需要查询用户所属的组织
            # 简化实现：假设通过数据库查询验证
            try:
                from sqlalchemy import select

                from models.license import Organization

                # 使用同步数据库会话
                db_gen = get_sync_db()
                db = next(db_gen)

                # 查询用户关联的组织
                stmt = (
                    select(Organization)
                    .join(Organization.users)
                    .filter(Organization.id == org_id, Organization.is_active == True)
                )

                result = db.execute(stmt)
                organization = result.scalar_one_or_none()

                if organization:
                    return {"allowed": True, "reason": "企业管理员权限"}
                else:
                    return {"allowed": False, "reason": "无权访问此租户"}
            except Exception as e:
                logger.error(f"验证企业管理员租户访问权限失败: {e}")
                return {"allowed": False, "reason": "权限验证异常"}
            finally:
                # 确保数据库连接关闭
                try:
                    next(db_gen, None)  # 触发生成器的清理
                except StopIteration:
                    pass

        # 普通用户需要有相应的许可证关联
        try:
            from services.user_license_service import user_license_service

            # 异步验证用户许可证关联
            user_licenses = await user_license_service.get_user_active_licenses(user.id)
            org_ids = {ul.license.organization_id for ul in user_licenses if ul.license}

            if org_id in org_ids:
                return {"allowed": True, "reason": "用户关联的租户"}
            else:
                return {"allowed": False, "reason": "用户未关联此租户"}
        except Exception as e:
            logger.error(f"验证普通用户租户访问权限失败: {e}")
            return {"allowed": False, "reason": "权限验证异常"}

    async def validate_api_specific_permissions(
        self, user: User, request: Request
    ) -> dict:
        """
        验证API特定权限

        Args:
            user: 用户对象
            request: 请求对象

        Returns:
            包含验证结果的字典
        """
        path = request.url.path
        method = request.method

        # 管理员拥有所有API访问权限
        if user.is_superuser or user.role == UserRole.ADMIN:
            return {"allowed": True, "reason": "管理员权限"}

        # 定义API权限映射
        api_permissions = {
            # 课程管理权限
            "/api/v1/org/*/courses": {
                "GET": ["view_courses"],
                "POST": ["create_course"],
                "PUT": ["update_course"],
                "DELETE": ["delete_course"],
            },
            # 选课管理权限
            "/api/v1/org/*/enrollments": {
                "GET": ["view_enrollments"],
                "POST": ["create_enrollment"],
                "PUT": ["update_enrollment"],
                "DELETE": ["delete_enrollment"],
            },
            # 配置管理权限
            "/api/v1/org/*/config": {
                "GET": ["view_config"],
                "POST": ["manage_config"],
                "PUT": ["manage_config"],
                "DELETE": ["manage_config"],
            },
        }

        # 检查是否需要特定权限
        for api_pattern, permissions in api_permissions.items():
            if self._match_api_pattern(path, api_pattern):
                required_permissions = permissions.get(method, [])
                if required_permissions:
                    # 检查用户是否具有所需权限
                    has_permission = await self._check_user_permissions(
                        user, required_permissions
                    )
                    if not has_permission:
                        return {
                            "allowed": False,
                            "reason": f"缺少权限: {', '.join(required_permissions)}",
                            "required_permission": (
                                required_permissions[0]
                                if required_permissions
                                else None
                            ),
                        }

        return {"allowed": True, "reason": "API权限验证通过"}

    def _match_api_pattern(self, path: str, pattern: str) -> bool:
        """匹配API路径模式"""
        if "*" in pattern:
            # 简单的通配符匹配
            prefix = pattern.split("*")[0]
            return path.startswith(prefix)
        return path == pattern

    async def _check_user_permissions(self, user: User, permissions: List[str]) -> bool:
        """检查用户是否具有指定权限"""
        # 管理员拥有所有权限
        if user.is_superuser or user.role == UserRole.ADMIN:
            return True

        # 企业管理员拥有大部分权限
        if user.role == UserRole.ORG_ADMIN:
            return True

        # 普通用户需要检查具体权限
        try:
            from services.user_license_service import user_license_service

            user_permissions = await user_license_service.get_user_permissions(user.id)
            return any(perm in user_permissions for perm in permissions)
        except Exception as e:
            logger.error(f"检查用户权限失败: {e}")
            return False

    async def get_current_user_from_request(self, request: Request) -> Optional[User]:
        """从请求中获取当前用户"""
        # 实现JWT解析逻辑
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # 移除 'Bearer ' 前缀

        try:
            from jose import jwt

            from config.settings import settings

            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            username = payload.get("sub")

            if not username:
                return None

            # 查询用户信息
            db_gen = get_sync_db()
            db = next(db_gen)

            try:
                from sqlalchemy import select

                from models.user import User

                stmt = select(User).filter(
                    User.username == username, User.is_active == True
                )
                result = db.execute(stmt)
                user = result.scalar_one_or_none()

                return user
            finally:
                next(db_gen, None)

        except Exception as e:
            logger.error(f"JWT解析失败: {e}")
            return None

    def should_skip_permission_check(self, path: str) -> bool:
        """判断是否跳过权限检查"""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)


# 保持向后兼容的别名
PermissionMiddleware = EnhancedPermissionMiddleware
