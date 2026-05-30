"""
企业认证中间件
实现企业级API访问控制和安全过滤
"""

import logging
import time
from typing import Awaitable, Callable

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from services.enterprise_auth_service import enterprise_auth_service
from utils.logger import log_security_event
from utils.security_utils import SecurityUtil

logger = logging.getLogger(__name__)


class EnterpriseAuthMiddleware(BaseHTTPMiddleware):
    """企业认证中间件类"""

    def __init__(self, app):
        super().__init__(app)
        self.auth_service = enterprise_auth_service
        self.security_util = SecurityUtil()
        self.excluded_paths = [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/favicon.ico",
            "/static/",
            "/api/enterprise/oauth/token",  # 允许令牌端点无需认证
            "/api/enterprise/oauth/authorize",  # 允许授权端点
        ]

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        中间件主处理逻辑

        Args:
            request: HTTP请求对象
            call_next: 下一个处理器

        Returns:
            HTTP响应对象
        """
        start_time = time.time()

        # 检查是否需要跳过认证
        if self._should_skip_authentication(request.url.path):
            return await call_next(request)

        try:
            # 提取认证信息
            auth_header = request.headers.get("Authorization")
            device_id = self._extract_device_id(request)
            ip_address = self.security_util.get_client_ip(request)

            # 执行认证
            auth_result = self.auth_service.authenticate_request(
                auth_header, device_id, ip_address
            )

            if not auth_result or not auth_result.get("authenticated"):
                # 认证失败，记录安全事件
                log_security_event(
                    logger,
                    "AUTHENTICATION_FAILED",
                    (
                        auth_result.get("client_id", "unknown")
                        if auth_result
                        else "unknown"
                    ),
                    "WARNING",
                    {
                        "reason": (
                            auth_result.get("reason")
                            if auth_result
                            else "No auth header"
                        ),
                        "device_id": device_id,
                        "ip_address": ip_address,
                        "path": request.url.path,
                    },
                )

                # 返回适当的错误响应
                if auth_result and auth_result.get("reason") == "API quota exceeded":
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": "API quota exceeded. Please contact your administrator."
                        },
                    )
                elif (
                    auth_result
                    and auth_result.get("reason") == "Device not in whitelist"
                ):
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "detail": "Device not authorized. Please contact your administrator."
                        },
                    )
                else:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "detail": "Invalid or missing authentication credentials"
                        },
                    )

            # 认证成功，将认证信息附加到请求状态
            request.state.enterprise_client_id = auth_result["client_id"]
            request.state.enterprise_device_id = auth_result.get("device_id")
            request.state.enterprise_client_info = auth_result["client_info"]

            # 记录请求开始信息
            request_start_info = {
                "endpoint": request.url.path,
                "method": request.method,
                "user_agent": request.headers.get("User-Agent"),
                "ip_address": ip_address,
                "request_size": (
                    len(await request.body())
                    if request.method in ["POST", "PUT", "PATCH"]
                    else 0
                ),
            }

            # 继续处理请求
            response = await call_next(request)

            # 计算响应时间
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒

            # 记录API访问日志
            response_info = {
                "status_code": response.status_code,
                "response_time": response_time,
                "response_size": int(response.headers.get("content-length", 0)),
            }

            self.auth_service.log_api_access(
                auth_result["client_id"],
                auth_result.get("device_id"),
                request_start_info,
                response_info,
            )

            # 添加企业网关相关信息到响应头
            response.headers["X-Enterprise-Gateway"] = "iMato Enterprise API Gateway"
            response.headers["X-Response-Time"] = f"{response_time:.2f}ms"

            return response

        except HTTPException:
            # 重新抛出HTTP异常
            raise
        except Exception as e:
            logger.error(f"Enterprise auth middleware error: {str(e)}")
            # 记录安全事件
            log_security_event(
                logger,
                "MIDDLEWARE_ERROR",
                "unknown",
                "ERROR",
                {
                    "error": str(e),
                    "path": request.url.path,
                    "ip_address": self.security_util.get_client_ip(request),
                },
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error during authentication"},
            )

    def _should_skip_authentication(self, path: str) -> bool:
        """
        判断是否应该跳过认证检查

        Args:
            path: 请求路径

        Returns:
            是否跳过认证
        """
        return any(path.startswith(excluded) for excluded in self.excluded_paths)

    def _extract_device_id(self, request: Request) -> str:
        """
        从请求中提取设备ID

        Args:
            request: HTTP请求对象

        Returns:
            设备ID
        """
        # 优先从自定义头获取
        device_id = request.headers.get("X-Device-ID")
        if device_id:
            return device_id

        # 从用户代理生成设备指纹
        user_agent = request.headers.get("User-Agent", "")
        ip_address = self.security_util.get_client_ip(request)

        return self.security_util.generate_device_fingerprint(ip_address, user_agent)


# 保持向后兼容的别名
EnterpriseAuthenticationMiddleware = EnterpriseAuthMiddleware
