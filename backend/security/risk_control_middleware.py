"""
【P3-E】风控中间件 + FastAPI 依赖项

职责：
1. RiskControlMiddleware - 全局中间件，统一拦截所有请求进行 IP 限流检查
2. captcha_required()  - FastAPI Depends，在路由中按需启用 CAPTCHA
3. risk_check()       - FastAPI Depends，在路由中进行风控检查

使用：
    from security.risk_control_middleware import (
        RiskControlMiddleware,
        captcha_required,
        risk_check,
    )

    # 方式 1：全局中间件（推荐，对所有路由生效）
    app.add_middleware(RiskControlMiddleware, enabled=True)

    # 方式 2：路由 Depends（仅对特定路由生效）
    @app.post("/api/v1/invite/codes/{code}/use")
    async def use_invite(
        code: str,
        risk: RiskCheckResult = Depends(risk_check),
        captcha: CaptchaVerifyResult = Depends(captcha_required),
    ):
        ...
"""

import logging
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from security.captcha import (
    get_captcha_provider,
    get_token_store,
)
from security.risk_control import (
    RiskCheckResult,
    get_risk_control_service,
)

logger = logging.getLogger(__name__)


# ==================== 工具函数 ====================


def _get_client_ip(request: Request) -> str:
    """获取客户端真实 IP（支持 X-Forwarded-For）"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _endpoint_key(request: Request) -> str:
    """构造 endpoint_key 格式：METHOD:/path"""
    return f"{request.method}:{request.url.path}"


# ==================== 全局中间件 ====================


class RiskControlMiddleware(BaseHTTPMiddleware):
    """
    全局风控中间件

    对所有请求进行 IP 频率检查 + 异常行为检测。
    高风险请求返回 429，可疑请求通过 depends 在路由内升级 CAPTCHA。

    中间件是粗粒度防护，路由 Depends 是细粒度防护。
    """

    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled

    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)

        # 跳过非业务路径
        path = request.url.path
        skip_prefixes = (
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            "/favicon.ico",
        )
        if any(path.startswith(p) for p in skip_prefixes):
            return await call_next(request)

        ip = _get_client_ip(request)
        endpoint = _endpoint_key(request)

        # 调用风控服务
        service = get_risk_control_service()
        result = service.check(ip=ip, endpoint_key=endpoint)

        # 拒绝请求：返回 429
        if not result.allowed:
            headers = {
                "Retry-After": str(result.retry_after_seconds),
                "X-Risk-Level": result.risk_level.value,
                "X-Risk-Score": str(result.score),
            }
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": result.reason,
                    "risk_level": result.risk_level.value,
                    "score": result.score,
                    "retry_after_seconds": result.retry_after_seconds,
                },
                headers=headers,
            )

        # 通过 - 继续处理
        response = await call_next(request)

        # 记录失败/成功（用于异常检测）
        if 400 <= response.status_code < 500:
            service.record_failure(ip=ip, endpoint_key=endpoint)
        elif 200 <= response.status_code < 300:
            service.record_success(ip=ip, endpoint_key=endpoint)

        # 注入风险上下文（响应头）
        response.headers["X-Risk-Level"] = result.risk_level.value
        response.headers["X-Risk-Score"] = str(result.score)
        if result.requires_captcha:
            response.headers["X-Requires-Captcha"] = "1"

        return response


# ==================== FastAPI 依赖项 ====================


async def risk_check(request: Request) -> RiskCheckResult:
    """
    FastAPI Depends：每端点的风控检查

    使用：
        @router.post("/api/v1/invite/codes")
        async def create_invite(
            request: Request,
            risk: RiskCheckResult = Depends(risk_check),
        ):
            ...

    行为：
    - 调用全局风控服务 check()
    - 不允许时抛 429
    - allowed=True 时返回详细结果（score / captcha required）
    """
    ip = _get_client_ip(request)
    endpoint = _endpoint_key(request)
    service = get_risk_control_service()
    result = service.check(ip=ip, endpoint_key=endpoint)

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=result.reason,
            headers={
                "Retry-After": str(result.retry_after_seconds),
                "X-Risk-Level": result.risk_level.value,
            },
        )

    return result


async def captcha_required(
    request: Request,
    risk: RiskCheckResult = Depends(risk_check),
) -> Optional[Dict[str, Any]]:
    """
    FastAPI Depends：按需 CAPTCHA 验证

    使用：
        @router.post("/api/v1/invite/codes")
        async def create_invite(
            request: Request,
            captcha: Optional[Dict] = Depends(captcha_required),
        ):
            ...

    行为：
    1. 先调用 risk_check
    2. 如果 risk.requires_captcha=True，则强制要求请求携带 captcha_token
    3. 验证失败抛 400
    4. 验证成功标记 token 为已用 + 返回 {success, provider}

    从 header `X-Captcha-Token` 读取（也可改为 Body）
    """
    if not risk.requires_captcha:
        # 不需要 CAPTCHA，直接通过
        return None

    token = request.headers.get("X-Captcha-Token") or request.headers.get(
        "captcha-token"
    )
    if not token:
        # 尝试从 query/cookies 找
        token = request.query_params.get("captcha_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此操作需要 CAPTCHA 验证（X-Captcha-Token header）",
            headers={
                "X-Requires-Captcha": "1",
                "X-Captcha-Provider": "required",
            },
        )

    # 检查 token 是否已使用（防重放）
    store = get_token_store()
    if store.is_used(token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CAPTCHA token 已使用或已过期，请重新验证",
        )

    # 调用 provider 验证
    ip = _get_client_ip(request)
    provider = get_captcha_provider()
    result = provider.verify(token=token, ip=ip)

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CAPTCHA 验证失败：{', '.join(result.error_codes)}",
            headers={
                "X-Captcha-Provider": result.provider,
                "X-Captcha-Errors": ",".join(result.error_codes),
            },
        )

    # 标记 token 已使用
    store.mark_used(token)

    return {
        "success": True,
        "provider": result.provider,
        "challenge_ts": result.challenge_ts,
    }


__all__ = [
    "RiskControlMiddleware",
    "risk_check",
    "captcha_required",
    "_get_client_ip",
    "_endpoint_key",
]
