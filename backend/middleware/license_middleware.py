"""
许可证验证中间件和安全控制
提供API级别的许可证验证和权限控制
"""

from functools import wraps
import logging
from typing import Callable, List, Optional

from fastapi import HTTPException, Request
from fastapi.security import (  # noqa: F401,E501
    HTTPAuthorizationCredentials, HTTPBearer
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from services.license_service import \
    LicenseService  # type: ignore[import-untyped]
from utils.database import AsyncSessionLocal  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class LicenseMiddleware(BaseHTTPMiddleware):
    """许可证验证中间件"""

    def __init__(
        self, app,
        exclude_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.exclude_paths: List[str] = (
            exclude_paths if exclude_paths is not None else [
                "/docs",
                "/redoc",
                "/openapi.json",
                "/health",
                "/api/v1/health",
                "/api/v1/auth/token",      # ✅ 登录接口豁免
                "/api/v1/auth/register",   # ✅ 注册接口豁免
                "/api/v1/finance",         # ✅ 财务管理接口豁免（开发环境）
                "/api/v1/local-knowledge-graph",  # ✅ 本地知识图谱接口豁免
            ])

    async def dispatch(self, request: Request, call_next):
        # ✅ 跳过 OPTIONS 预检请求 (CORS)
        if request.method == "OPTIONS":
            return await call_next(request)

        # 检查是否需要跳过验证
        if self._should_exclude(request.url.path):
            return await call_next(request)

        # 获取许可证密钥
        license_key = self._extract_license_key(request)

        if not license_key:
            return JSONResponse(status_code=401, content={"detail": "缺少许可证密钥"})

        # 验证许可证
        license_service = LicenseService()

        try:
            async with AsyncSessionLocal() as db:
                validation_result = license_service.validate_api_license(
                    org_id=0,  # placeholder org_id
                    feature="api_access",
                    db=db,  # type: ignore[arg-type]
                )

                if not validation_result:
                    logger.warning(
                        f"许可证验证失败: {license_key}"
                    )
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "许可证验证失败"},
                    )

                # 将许可证信息添加到请求状态中
                request.state.license_info = {
                    "license_key": license_key,
                    "status": "active",
                    "features": ["api_access"],
                }
                logger.info(f"许可证验证成功: {license_key}")

        except Exception as e:
            logger.error(f"许可证验证异常: {e}")
            return JSONResponse(
                status_code=500, content={"detail": "许可证验证服务暂时不可用"}
            )

        # 继续处理请求
        response = await call_next(request)
        return response

    def _should_exclude(self, path: str) -> bool:
        """检查路径是否应该排除验证"""
        return any(
            path == exclude_path or path.startswith(exclude_path)
            for exclude_path in self.exclude_paths
        )

    def _extract_license_key(self, request: Request) -> Optional[str]:
        """从请求中提取许可证密钥"""
        # 1. 从Header中获取
        license_key = request.headers.get("X-License-Key")
        if license_key:
            return license_key

        # 2. 从Authorization header中获取 (Bearer token格式)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # 移除 "Bearer " 前缀

        # 3. 从查询参数中获取
        license_key = request.query_params.get("license_key")
        if license_key:
            return license_key

        return None


class LicenseSecurity(HTTPBearer):
    """许可证安全验证类"""

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(  # type: ignore[override]
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        return await super().__call__(request)


def license_required(
    required_features: Optional[List[str]] = None,
    required_status: str = "active",
):
    """
    许可证验证装饰器

    Args:
        required_features: 需要的功能列表
        required_status: 需要的许可证状态
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or next(
                (arg for arg in args if isinstance(arg, Request)), None
            )

            if not request:
                raise HTTPException(status_code=500, detail="无法获取请求对象")

            # 检查许可证信息
            license_info = getattr(request.state, "license_info", None)
            if not license_info:
                raise HTTPException(status_code=403, detail="许可证验证失败")

            # 检查许可证状态
            if license_info.get("status") != required_status:
                raise HTTPException(
                    status_code=403,
                    detail=f"许可证状态无效: {license_info.get('status')}",
                )

            # 检查功能权限
            if required_features:
                license_features = license_info.get("features", [])
                missing_features = [
                    f for f in required_features if f not in license_features
                ]
                if missing_features:
                    raise HTTPException(
                        status_code=403,
                        detail=f"缺少必需功能: {', '.join(missing_features)}",
                    )

            # 检查用户数量限制
            max_users = license_info.get("max_users", 0)
            current_users = license_info.get("current_users", 0)
            if current_users >= max_users:
                raise HTTPException(status_code=403, detail="已达到最大用户数限制")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def rate_limit_by_license(
    max_requests: int = 1000, window_seconds: int = 3600
):
    """
    基于许可证的速率限制装饰器

    Args:
        max_requests: 最大请求数
        window_seconds: 时间窗口（秒）
    """
    from collections import defaultdict
    import time

    # 简单的内存存储（生产环境应使用Redis）
    request_counts = defaultdict(list)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request") or next(
                (arg for arg in args if isinstance(arg, Request)), None
            )

            if not request:
                return await func(*args, **kwargs)

            license_info = getattr(request.state, "license_info", None)
            if not license_info:
                return await func(*args, **kwargs)

            license_key = license_info.get("license_key")
            current_time = time.time()

            # 清理过期的请求记录
            request_counts[license_key] = [
                req_time
                for req_time in request_counts[license_key]
                if current_time - req_time < window_seconds
            ]

            # 检查是否超过限制
            if len(request_counts[license_key]) >= max_requests:
                raise HTTPException(
                    status_code=429,
                    detail=f"超过许可证请求限制 ({max_requests} 次/{window_seconds}秒)",
                )

            # 记录本次请求
            request_counts[license_key].append(current_time)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# 预定义的许可证验证装饰器
def enterprise_license_required(func: Callable):
    """企业版许可证要求"""
    return license_required(
        required_features=["enterprise_features"], required_status="active"
    )(func)


def education_license_required(func: Callable):
    """教育版许可证要求"""
    return license_required(
        required_features=["education_features"], required_status="active"
    )(func)


def api_access_required(func: Callable):
    """API访问权限要求"""
    return license_required(
        required_features=["api_access"], required_status="active"
    )(func)


# 异常处理器
async def license_exception_handler(request: Request, exc: Exception):
    """许可证相关异常处理器

    仅处理许可证相关的 401/403 异常，其他 HTTP 异常（如 404）正常传递。
    """
    status_code = getattr(exc, 'status_code', 500)
    detail = getattr(exc, 'detail', str(exc))

    # 仅处理许可证相关的异常（401/403 且 detail 包含许可证关键词）
    license_keywords = ['许可证', 'license', 'api_access', '权限验证']
    is_license_error = (
        status_code in (401, 403)
        and any(kw in str(detail).lower() for kw in license_keywords)
    )

    if not is_license_error:
        # 非许可证错误，使用标准 HTTP 异常响应
        from starlette.responses import JSONResponse as StarletteJSON
        return StarletteJSON(
            status_code=status_code,
            content={"detail": detail},
        )

    logger.warning(f"许可证异常: {detail} - Path: {request.url.path}")
    return JSONResponse(
        status_code=status_code,
        content={
            "error": "许可证验证失败",
            "message": detail,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        },
    )
