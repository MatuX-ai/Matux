"""
多租户中间件
负责处理租户识别、上下文设置和权限验证
"""

import logging
import re
from typing import Awaitable, Callable, Optional

from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config.settings import settings
from models.user import User, UserRole
from utils.auth_utils import get_current_user_sync
from utils.database import get_db
from utils.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """多租户中间件类"""

    def __init__(self, get_response: Callable[[Request], Awaitable]):
        self.get_response = get_response

    async def __call__(self, request: Request) -> JSONResponse:
        """
        中间件主处理函数

        Args:
            request: FastAPI 请求对象

        Returns:
            Response: 响应对象
        """
        # ✅ 跳过 OPTIONS 预检请求 (CORS)
        if request.method == "OPTIONS":
            return await self.get_response(request)

        try:
            # 检查是否需要跳过多租户处理的路径
            if self._should_skip_tenant_processing(request):
                return await self.get_response(request)

            # 提取租户ID
            org_id = await self._extract_org_id(request)

            if org_id is None:
                logger.warning(f"无法提取租户ID，路径: {request.url.path}")
                # 对于某些API，可能允许没有租户ID的情况
                if not self._is_public_endpoint(request):
                    raise HTTPException(
                        status_code=400,
                        detail="缺少租户标识(X-Org-ID header 或 URL参数)",
                    )
            else:
                # 验证租户ID格式
                if not self._validate_org_id(org_id):
                    raise HTTPException(
                        status_code=400, detail=f"无效的租户ID格式: {org_id}"
                    )

                # 设置租户上下文
                TenantContext.set_current_tenant(org_id)
                logger.debug(f"设置租户上下文: {org_id}")

            # 处理请求
            response = await self.get_response(request)

            # 清理租户上下文
            TenantContext.clear()

            return response

        except HTTPException as he:
            # 重新抛出HTTP异常
            raise he
        except Exception as e:
            logger.error(f"多租户中间件处理异常: {e}")
            TenantContext.clear()
            raise HTTPException(status_code=500, detail="多租户处理失败")

    async def _extract_org_id(self, request: Request) -> Optional[int]:
        """
        从请求中提取租户ID

        Args:
            request: 请求对象

        Returns:
            Optional[int]: 租户ID，如果无法提取则返回None
        """
        # 方法1: 从URL路径参数获取 (优先级最高)
        org_id = request.path_params.get("org_id")
        if org_id:
            logger.debug(f"从URL路径获取租户ID: {org_id}")
            return int(org_id)

        # 方法2: 从请求头获取
        org_id = request.headers.get("X-Org-ID")
        if org_id:
            logger.debug(f"从请求头获取租户ID: {org_id}")
            return int(org_id)

        # 方法3: 从JWT Token中解析
        token = await self._extract_jwt_token(request)
        if token:
            org_id = self._extract_org_id_from_token(token)
            if org_id:
                logger.debug(f"从JWT Token获取租户ID: {org_id}")
                return org_id

        # 方法4: 从查询参数获取
        org_id = request.query_params.get("org_id")
        if org_id:
            logger.debug(f"从查询参数获取租户ID: {org_id}")
            return int(org_id)

        return None

    async def _extract_jwt_token(self, request: Request) -> Optional[str]:
        """
        从请求中提取JWT token

        Args:
            request: 请求对象

        Returns:
            Optional[str]: JWT token，如果不存在则返回None
        """
        # 从Authorization header获取
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # 移除 'Bearer ' 前缀

        # 从cookie获取
        token = request.cookies.get("access_token")
        if token:
            return token

        return None

    def _extract_org_id_from_token(self, token: str) -> Optional[int]:
        """
        从JWT token中提取租户ID

        Args:
            token: JWT token

        Returns:
            Optional[int]: 租户ID，如果无法提取则返回None
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload.get("org_id")
        except JWTError as e:
            logger.debug(f"JWT解码失败: {e}")
            return None

    def _validate_org_id(self, org_id: int) -> bool:
        """
        验证租户ID的有效性

        Args:
            org_id: 租户ID

        Returns:
            bool: 如果有效返回True，否则返回False
        """
        # 基本验证：必须是正整数
        if not isinstance(org_id, int) or org_id <= 0:
            return False

        # 可以添加更多的验证逻辑，比如检查租户是否存在
        return True

    def _should_skip_tenant_processing(self, request: Request) -> bool:
        """
        判断是否应该跳过多租户处理

        Args:
            request: 请求对象

        Returns:
            bool: 如果应该跳过返回True，否则返回False
        """
        path = request.url.path

        # 跳过健康检查端点
        if path in ["/health", "/"]:
            return True

        # 跳过文档端点
        if path.startswith("/docs") or path.startswith("/redoc"):
            return True

        # 跳过认证相关端点
        if path.startswith("/api/v1/auth"):
            return True

        # 跳过系统管理端点
        skip_patterns = [
            r"^/api/v1/admin/",
            r"^/api/v1/system/",
        ]

        for pattern in skip_patterns:
            if re.match(pattern, path):
                return True

        return False

    def _is_public_endpoint(self, request: Request) -> bool:
        """
        判断是否是公共端点（不需要租户ID）

        Args:
            request: 请求对象

        Returns:
            bool: 如果是公共端点返回True，否则返回False
        """
        path = request.url.path

        public_endpoints = [
            "/",
            "/health",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
        ]

        return path in public_endpoints


# 依赖项函数
async def get_current_org_id(request: Request) -> Optional[int]:
    """
    获取当前请求的租户ID依赖项

    Args:
        request: 请求对象

    Returns:
        Optional[int]: 租户ID
    """
    org_id = request.path_params.get("org_id")
    if org_id:
        return int(org_id)

    org_id = request.headers.get("X-Org-ID")
    if org_id:
        return int(org_id)

    return None


def require_tenant_access(
    org_id: int,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_db),
) -> bool:
    """
    验证用户是否有访问指定租户的权限

    Args:
        org_id: 租户ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        bool: 如果有权限返回True

    Raises:
        HTTPException: 如果没有权限
    """
    # 系统管理员可以访问所有租户
    if current_user.is_superuser or current_user.role == UserRole.ADMIN:
        return True

    # 企业管理员只能访问自己的租户
    if current_user.role == UserRole.ORG_ADMIN:
        # 这里需要检查用户是否属于指定的组织
        # 实现具体的业务逻辑
        pass

    # 普通用户需要检查是否有该租户的访问权限
    # 实现具体的权限检查逻辑

    raise HTTPException(status_code=403, detail="无权访问此租户资源")


# 异常处理器
async def tenant_exception_handler(request: Request, exc: HTTPException):
    """租户相关异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "type": "tenant_error",
            "path": request.url.path,
        },
    )


# 工具函数
def get_tenant_from_context() -> Optional[int]:
    """从上下文中获取当前租户ID"""
    return TenantContext.get_current_tenant()


def set_tenant_context(org_id: int):
    """设置租户上下文"""
    TenantContext.set_current_tenant(org_id)


def clear_tenant_context():
    """清除租户上下文"""
    TenantContext.clear()
