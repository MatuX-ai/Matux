"""
【P3 监控】Prometheus 指标定义

定义 backend 系统的核心指标：
- HTTP 请求计数 / 时延（Counter / Histogram）
- 风控拒绝 / 封禁计数
- CAPTCHA 验证计数
- 业务事件（创建分享卡片、邀请码等）

使用：
    from security.metrics import (
        metrics_middleware,
        record_share_card_created,
        record_invite_code_used,
        record_risk_blocked,
    )

    app.add_middleware(metrics_middleware())  # 如需要
"""

import logging
import time

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logger = logging.getLogger(__name__)


# ==================== 指标定义 ====================


# HTTP 请求
http_requests_total = Counter(
    "imatoproject_http_requests_total",
    "HTTP 请求总数（按 method/path/status）",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "imatoproject_http_request_duration_seconds",
    "HTTP 请求处理耗时（秒）",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# 风控
risk_check_total = Counter(
    "imatoproject_risk_check_total",
    "风控检查总数（按 endpoint/result）",
    ["endpoint", "result"],  # result: allowed / captcha_required / blocked
)

risk_blocked_ips = Gauge(
    "imatoproject_risk_blocked_ips",
    "当前封禁 IP 数量",
)

risk_tracked_ips = Gauge(
    "imatoproject_risk_tracked_ips",
    "被追踪的 IP 总数",
)

risk_high_risk_ips = Gauge(
    "imatoproject_risk_high_risk_ips",
    "高风险 IP 数（评分 ≥ 50）",
)

# CAPTCHA
captcha_verifications_total = Counter(
    "imatoproject_captcha_verifications_total",
    "CAPTCHA 验证总数（按 provider/result）",
    ["provider", "result"],  # result: success / failure
)

# 业务事件
share_cards_created_total = Counter(
    "imatoproject_share_cards_created_total",
    "分享卡片创建总数",
)

share_card_track_share_total = Counter(
    "imatoproject_share_card_track_share_total",
    "分享卡片二次传播总数",
)

invite_codes_created_total = Counter(
    "imatoproject_invite_codes_created_total",
    "邀请码创建总数",
)

invite_codes_used_total = Counter(
    "imatoproject_invite_codes_used_total",
    "邀请码使用总数",
)

# 仓储
repository_operations_total = Counter(
    "imatoproject_repository_operations_total",
    "仓储操作总数（按 backend/operation）",
    ["backend", "operation"],  # backend: memory/sqlite/postgres
)

# Redis
redis_operations_total = Counter(
    "imatoproject_redis_operations_total",
    "Redis 操作总数（按 operation/status）",
    ["operation", "status"],  # status: ok / error
)

redis_pubsub_messages_total = Counter(
    "imatoproject_redis_pubsub_messages_total",
    "Pub/Sub 消息总数（按 channel/direction）",
    ["channel", "direction"],  # direction: published / received
)


# ==================== 中间件 ====================


def record_http_request(
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    """记录一次 HTTP 请求"""
    # 路径归一化（去掉 query string + 数字 ID）
    normalized = _normalize_path(path)
    http_requests_total.labels(
        method=method,
        path=normalized,
        status=str(status_code),
    ).inc()
    http_request_duration_seconds.labels(
        method=method, path=normalized
    ).observe(duration_seconds)


def _normalize_path(path: str) -> str:
    """
    路径归一化：减少 cardinality

    - 去掉 query string
    - 把 数字 / UUID 路径参数归一化为 {id}
    """
    if "?" in path:
        path = path.split("?", 1)[0]
    parts = []
    for seg in path.split("/"):
        if not seg:
            continue
        # 全数字或 UUID
        if seg.isdigit() or (
            len(seg) == 36 and seg.count("-") == 4
        ):
            parts.append("{id}")
        else:
            parts.append(seg)
    return "/" + "/".join(parts) if parts else "/"


# ==================== 业务快捷方法 ====================


def record_share_card_created() -> None:
    share_cards_created_total.inc()


def record_share_card_track_share() -> None:
    share_card_track_share_total.inc()


def record_invite_code_created() -> None:
    invite_codes_created_total.inc()


def record_invite_code_used() -> None:
    invite_codes_used_total.inc()


def record_risk_check(
    endpoint: str, allowed: bool, captcha_required: bool, blocked: bool
) -> None:
    if blocked:
        result = "blocked"
    elif captcha_required:
        result = "captcha_required"
    elif allowed:
        result = "allowed"
    else:
        result = "rate_limited"
    risk_check_total.labels(endpoint=endpoint, result=result).inc()


def record_captcha(provider: str, success: bool) -> None:
    captcha_verifications_total.labels(
        provider=provider,
        result="success" if success else "failure",
    ).inc()


def record_repository_op(backend: str, operation: str) -> None:
    repository_operations_total.labels(
        backend=backend, operation=operation
    ).inc()


def record_redis_op(operation: str, ok: bool = True) -> None:
    redis_operations_total.labels(
        operation=operation,
        status="ok" if ok else "error",
    ).inc()


def record_redis_publish(channel: str, count: int = 1) -> None:
    redis_pubsub_messages_total.labels(
        channel=channel, direction="published"
    ).inc(count)


def record_redis_received(channel: str, count: int = 1) -> None:
    redis_pubsub_messages_total.labels(
        channel=channel, direction="received"
    ).inc(count)


def update_risk_gauges(
    tracked_ips: int, blocked_ips: int, high_risk_ips: int
) -> None:
    risk_tracked_ips.set(tracked_ips)
    risk_blocked_ips.set(blocked_ips)
    risk_high_risk_ips.set(high_risk_ips)


# ==================== 导出 ====================


def get_metrics_output() -> bytes:
    """导出 Prometheus 文本格式"""
    # 在导出时更新风控 gauge
    try:
        from security.risk_control import get_risk_control_service

        svc = get_risk_control_service()
        stats = svc.get_stats()
        update_risk_gauges(
            tracked_ips=stats.get("tracked_ips", 0),
            blocked_ips=stats.get("blocked_ips", 0),
            high_risk_ips=stats.get("high_risk_ips", 0),
        )
    except Exception as e:
        logger.debug(f"更新风控 gauge 失败: {e}")
    return generate_latest(REGISTRY)


def get_content_type() -> str:
    return CONTENT_TYPE_LATEST


# ==================== ASGI 中间件（可选）====================


class PrometheusASGIMiddleware:
    """
    简单的 ASGI 计时中间件

    用法：
        app.add_middleware(PrometheusASGIMiddleware)
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.time()
        method = scope.get("method", "GET")
        path = scope.get("path", "/")
        status_holder = {"code": 500}

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                status_holder["code"] = message.get("status", 500)
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
        finally:
            duration = time.time() - start
            try:
                record_http_request(
                    method=method,
                    path=path,
                    status_code=status_holder["code"],
                    duration_seconds=duration,
                )
            except Exception as e:
                logger.debug(f"Prometheus 记录失败: {e}")


# BaseHTTPMiddleware 版本（FastAPI）
try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request as StarletteRequest

    class PrometheusHTTPMiddleware(BaseHTTPMiddleware):
        """FastAPI 风格的 HTTP 中间件"""

        async def dispatch(self, request: StarletteRequest, call_next):
            start = time.time()
            status_code = 500
            try:
                response = await call_next(request)
                status_code = response.status_code
                return response
            finally:
                duration = time.time() - start
                try:
                    record_http_request(
                        method=request.method,
                        path=request.url.path,
                        status_code=status_code,
                        duration_seconds=duration,
                    )
                except Exception as e:
                    logger.debug(f"Prometheus 记录失败: {e}")
except ImportError:  # pragma: no cover
    PrometheusHTTPMiddleware = None  # type: ignore[assignment]


__all__ = [
    "http_requests_total",
    "http_request_duration_seconds",
    "risk_check_total",
    "risk_blocked_ips",
    "risk_tracked_ips",
    "risk_high_risk_ips",
    "captcha_verifications_total",
    "share_cards_created_total",
    "share_card_track_share_total",
    "invite_codes_created_total",
    "invite_codes_used_total",
    "repository_operations_total",
    "redis_operations_total",
    "redis_pubsub_messages_total",
    "record_http_request",
    "record_share_card_created",
    "record_share_card_track_share",
    "record_invite_code_created",
    "record_invite_code_used",
    "record_risk_check",
    "record_captcha",
    "record_repository_op",
    "record_redis_op",
    "record_redis_publish",
    "record_redis_received",
    "get_metrics_output",
    "get_content_type",
    "PrometheusASGIMiddleware",
    "PrometheusHTTPMiddleware",
]
