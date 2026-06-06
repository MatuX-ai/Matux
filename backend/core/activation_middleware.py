"""
路由激活中间件

拦截 HTTP 请求，判断目标路由所属模块是否已激活。
若未激活则自动触发激活流程，激活期间返回 503 状态码。
"""

import json
import logging
from typing import Any, Callable, Dict

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

from .module_spec import ModuleState, ModuleTier

logger = logging.getLogger(__name__)

# 不需要激活检查的路径白名单
WHITELIST_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics",
    "/registry/stats",
    "/registry/modules",
    "/test/faulty",
    "/test/success",
}

# 白名单路径前缀
WHITELIST_PREFIXES = (
    "/api/v1/system/",    # 系统状态 API
    "/api/v1/auth/",      # 认证 API（Tier 0）
    "/docs",
    "/redoc",
)


class ModuleActivationMiddleware:
    """
    路由级懒加载激活中间件

    工作流程：
    1. 请求进入时，匹配 URL 前缀找到对应模块
    2. 若模块状态为 UNLOADED，触发异步激活
    3. 激活期间返回 503 + Retry-After 头
    4. 激活失败返回 503 + 模块错误信息
    5. 激活成功后请求正常处理
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # 仅处理 HTTP 请求
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # 白名单路径直接放行
        if self._is_whitelisted(path):
            await self.app(scope, receive, send)
            return

        # 查找对应模块
        try:
            from core.lazy_loader import get_lazy_loader

            loader = get_lazy_loader()
        except RuntimeError:
            # LazyLoader 未初始化，直接放行
            await self.app(scope, receive, send)
            return

        module_name = loader.find_module_by_path(path)

        # 未注册的路由直接放行（可能是已解耦存根或其他）
        if module_name is None:
            await self.app(scope, receive, send)
            return

        spec = loader.get_module(module_name)
        if spec is None:
            await self.app(scope, receive, send)
            return

        # Tier 0 模块始终放行
        if spec.tier == ModuleTier.TIER_0_CORE:
            await self.app(scope, receive, send)
            return

        # 检查模块状态
        if spec.state == ModuleState.ACTIVE:
            # 已激活，直接放行
            await self.app(scope, receive, send)
            return

        elif spec.state == ModuleState.DEGRADED:
            # 降级运行，放行但添加提示头
            await self._send_with_degraded_header(
                scope, receive, send, module_name, spec.error_message
            )
            return

        elif spec.state == ModuleState.LOADING:
            # 正在加载，返回 503
            response = self._loading_response(module_name)
            await response(scope, receive, send)
            return

        elif spec.state == ModuleState.FAILED:
            # 加载失败，返回 503
            response = self._failed_response(module_name, spec.error_message)
            await response(scope, receive, send)
            return

        elif spec.state == ModuleState.DISABLED:
            # 已禁用，返回 503
            response = self._disabled_response(module_name)
            await response(scope, receive, send)
            return

        elif spec.state == ModuleState.UNLOADED:
            # 未加载，触发自动激活
            try:
                success = await loader.activate(module_name)
                if success or spec.state == ModuleState.DEGRADED:
                    # 激活成功或降级运行，放行请求
                    await self.app(scope, receive, send)
                else:
                    response = self._failed_response(
                        module_name, spec.error_message
                    )
                    await response(scope, receive, send)
            except Exception as e:
                logger.error(f"自动激活失败: {module_name} - {e}")
                response = self._failed_response(module_name, str(e))
                await response(scope, receive, send)
            return

        # 未知状态，直接放行
        await self.app(scope, receive, send)

    # ==================== 辅助方法 ====================

    def _is_whitelisted(self, path: str) -> bool:
        """检查路径是否在白名单中"""
        if path in WHITELIST_PATHS:
            return True
        for prefix in WHITELIST_PREFIXES:
            if path.startswith(prefix):
                return True
        return False

    def _loading_response(self, module_name: str) -> JSONResponse:
        """模块加载中响应"""
        return JSONResponse(
            status_code=503,
            content={
                "status": "module_loading",
                "message": f"功能模块 '{module_name}' 正在启动，请稍候...",
                "module": module_name,
                "retry_after": 3,
            },
            headers={"Retry-After": "3"},
        )

    def _failed_response(
        self, module_name: str, error: str | None
    ) -> JSONResponse:
        """模块加载失败响应"""
        return JSONResponse(
            status_code=503,
            content={
                "status": "module_unavailable",
                "message": f"功能模块 '{module_name}' 暂时不可用",
                "module": module_name,
                "error": error,
                "retry_after": 60,
            },
            headers={"Retry-After": "60"},
        )

    def _disabled_response(self, module_name: str) -> JSONResponse:
        """模块已禁用响应"""
        return JSONResponse(
            status_code=503,
            content={
                "status": "module_disabled",
                "message": f"功能模块 '{module_name}' 已被管理员禁用",
                "module": module_name,
            },
        )

    async def _send_with_degraded_header(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        module_name: str,
        reason: str | None,
    ) -> None:
        """降级模式下放行请求，但添加降级提示头"""

        async def send_with_header(message: Dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"x-module-degraded"] = module_name.encode()
                if reason:
                    headers[b"x-module-degraded-reason"] = reason.encode()
                message["headers"] = list(headers.items())
            await send(message)

        await self.app(scope, receive, send_with_header)
