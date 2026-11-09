"""
路由激活中间件

拦截 HTTP 请求，判断目标路由所属模块是否已激活。
若未激活则自动触发激活流程，激活期间返回 503 状态码。
"""

import logging
from typing import Any, Dict, List, Optional

from starlette.responses import JSONResponse
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

        await self._dispatch(scope, receive, send, loader, path)

    async def _dispatch(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        loader: Any,
        path: str,
    ) -> None:
        """按最长前缀优先逐个尝试候选模块，任一可用即放行

        同一前缀可能对应多个模块（Issue #42-A），因此需要遍历候选，
        而不是只看首个命中项。
        """
        candidates = self._resolve_candidates(loader, path)

        # 未注册的路由直接放行（可能是已解耦存根或其他）
        if not candidates:
            await self.app(scope, receive, send)
            return

        # 首个「不可用」的候选及其错误详情，供全部候选都不可用时返回 503
        blocked: Optional[tuple] = None

        for module_name in candidates:
            served, info = await self._try_candidate(
                scope, receive, send, loader, module_name
            )
            if served:
                return
            blocked = blocked or info

        if blocked is None:
            # 候选模块都没有规格描述，直接放行
            await self.app(scope, receive, send)
            return

        await self._reject(scope, receive, send, *blocked)

    async def _try_candidate(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        loader: Any,
        module_name: str,
    ) -> tuple:
        """尝试放行或激活单个候选模块

        Returns:
            ``(是否已放行, 不可用详情)``。不可用详情为
            ``(module_name, spec, error)``，仅在未放行时提供。
        """
        spec = loader.get_module(module_name)
        if spec is None:
            return False, None

        # Tier 0 模块始终放行
        if spec.tier == ModuleTier.TIER_0_CORE:
            await self.app(scope, receive, send)
            return True, None

        # 检查模块状态
        if spec.state == ModuleState.ACTIVE:
            # 已激活，直接放行
            await self.app(scope, receive, send)
            return True, None

        if spec.state == ModuleState.DEGRADED:
            # 降级运行，放行但添加提示头
            await self._send_with_degraded_header(
                scope, receive, send, module_name, spec.error_message
            )
            return True, None

        if spec.state == ModuleState.UNLOADED:
            # 未加载，触发自动激活
            try:
                success = await loader.activate(module_name)
            except Exception as e:
                logger.error(f"自动激活失败: {module_name} - {e}")
                return False, (module_name, spec, str(e))
            if success or spec.state == ModuleState.DEGRADED:
                # 激活成功或降级运行，放行请求
                await self.app(scope, receive, send)
                return True, None
            return False, (module_name, spec, None)

        # LOADING / FAILED / DISABLED：交给调用方继续尝试下一个候选
        return False, (module_name, spec, None)

    async def _reject(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        module_name: str,
        spec: Any,
        error: Optional[str],
    ) -> None:
        """全部候选都不可用时，按首个阻塞候选的状态返回 503"""
        if spec.state == ModuleState.LOADING:
            # 正在加载，返回 503
            response = self._loading_response(module_name)
        elif spec.state == ModuleState.DISABLED:
            # 已禁用，返回 503
            response = self._disabled_response(module_name)
        else:
            # 加载失败 / 激活失败，返回 503
            response = self._failed_response(
                module_name, error or spec.error_message
            )
        await response(scope, receive, send)

    # ==================== 辅助方法 ====================

    def _resolve_candidates(self, loader: Any, path: str) -> List[str]:
        """解析路径命中的候选模块列表（最长前缀优先）

        优先使用支持多候选的 ``find_modules_by_path``；旧版 loader（或测试
        替身）只提供单值的 ``find_module_by_path`` 时回退，保证兼容。
        """
        resolver = getattr(loader, "find_modules_by_path", None)
        if callable(resolver):
            names = resolver(path)
            if isinstance(names, (list, tuple)) and names:
                return list(names)
        single = loader.find_module_by_path(path)
        return [single] if single else []

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
