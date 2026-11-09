"""
【P3 监控】Prometheus 指标测试

覆盖：
1. Counter/Histogram 基础记录
2. 业务事件快捷方法
3. 路径归一化
4. /metrics 端点（HTTP GET）
5. ASGI 中间件记录
6. gauge 更新（风控状态）
"""

import os
import sys

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from routes.metrics_routes import router as metrics_router  # noqa: E501, E402
from security import metrics as m  # noqa: E501, E402
from security.metrics import (  # noqa: E501, E402
    PrometheusHTTPMiddleware,
    get_metrics_output,
    record_captcha,
    record_invite_code_created,
    record_invite_code_used,
    record_redis_op,
    record_redis_publish,
    record_redis_received,
    record_repository_op,
    record_risk_check,
    record_share_card_created,
    record_share_card_track_share,
)


# ==================== 1. 基础记录 ====================


class TestRecordRiskCheck:
    def test_allowed(self):
        before = m.risk_check_total.labels(
            endpoint="POST:/api/v1/share/cards", result="allowed"
        )._value.get()
        record_risk_check(
            endpoint="POST:/api/v1/share/cards",
            allowed=True, captcha_required=False, blocked=False,
        )
        after = m.risk_check_total.labels(
            endpoint="POST:/api/v1/share/cards", result="allowed"
        )._value.get()
        assert after == before + 1

    def test_captcha_required(self):
        before = m.risk_check_total.labels(
            endpoint="POST:/api/v1/invite/codes", result="captcha_required"
        )._value.get()
        record_risk_check(
            endpoint="POST:/api/v1/invite/codes",
            allowed=True, captcha_required=True, blocked=False,
        )
        after = m.risk_check_total.labels(
            endpoint="POST:/api/v1/invite/codes", result="captcha_required"
        )._value.get()
        assert after == before + 1

    def test_blocked(self):
        before = m.risk_check_total.labels(
            endpoint="POST:/api/v1/invite/codes", result="blocked"
        )._value.get()
        record_risk_check(
            endpoint="POST:/api/v1/invite/codes",
            allowed=False, captcha_required=False, blocked=True,
        )
        after = m.risk_check_total.labels(
            endpoint="POST:/api/v1/invite/codes", result="blocked"
        )._value.get()
        assert after == before + 1

    def test_rate_limited(self):
        before = m.risk_check_total.labels(
            endpoint="POST:/api/v1/share/cards", result="rate_limited"
        )._value.get()
        record_risk_check(
            endpoint="POST:/api/v1/share/cards",
            allowed=False, captcha_required=False, blocked=False,
        )
        after = m.risk_check_total.labels(
            endpoint="POST:/api/v1/share/cards", result="rate_limited"
        )._value.get()
        assert after == before + 1


class TestRecordCaptcha:
    def test_success(self):
        before = m.captcha_verifications_total.labels(
            provider="NoopCaptchaProvider", result="success"
        )._value.get()
        record_captcha(provider="NoopCaptchaProvider", success=True)
        after = m.captcha_verifications_total.labels(
            provider="NoopCaptchaProvider", result="success"
        )._value.get()
        assert after == before + 1

    def test_failure(self):
        before = m.captcha_verifications_total.labels(
            provider="HCaptchaProvider", result="failure"
        )._value.get()
        record_captcha(provider="HCaptchaProvider", success=False)
        after = m.captcha_verifications_total.labels(
            provider="HCaptchaProvider", result="failure"
        )._value.get()
        assert after == before + 1


class TestBusinessEvents:
    def test_share_card(self):
        before = m.share_cards_created_total._value.get()
        record_share_card_created()
        record_share_card_created()
        assert m.share_cards_created_total._value.get() == before + 2

    def test_track_share(self):
        before = m.share_card_track_share_total._value.get()
        record_share_card_track_share()
        assert m.share_card_track_share_total._value.get() == before + 1

    def test_invite_create(self):
        before = m.invite_codes_created_total._value.get()
        record_invite_code_created()
        assert m.invite_codes_created_total._value.get() == before + 1

    def test_invite_use(self):
        before = m.invite_codes_used_total._value.get()
        record_invite_code_used()
        assert m.invite_codes_used_total._value.get() == before + 1


class TestRedisOps:
    def test_redis_op_ok(self):
        before = m.redis_operations_total.labels(
            operation="get", status="ok"
        )._value.get()
        record_redis_op(operation="get", ok=True)
        assert m.redis_operations_total.labels(
            operation="get", status="ok"
        )._value.get() == before + 1

    def test_redis_op_error(self):
        before = m.redis_operations_total.labels(
            operation="set", status="error"
        )._value.get()
        record_redis_op(operation="set", ok=False)
        assert m.redis_operations_total.labels(
            operation="set", status="error"
        )._value.get() == before + 1

    def test_pubsub_publish(self):
        before = m.redis_pubsub_messages_total.labels(
            channel="test_ch", direction="published"
        )._value.get()
        record_redis_publish("test_ch", count=3)
        assert m.redis_pubsub_messages_total.labels(
            channel="test_ch", direction="published"
        )._value.get() == before + 3

    def test_pubsub_received(self):
        before = m.redis_pubsub_messages_total.labels(
            channel="test_ch", direction="received"
        )._value.get()
        record_redis_received("test_ch", count=2)
        assert m.redis_pubsub_messages_total.labels(
            channel="test_ch", direction="received"
        )._value.get() == before + 2


class TestRepositoryOps:
    def test_repo_op(self):
        before = m.repository_operations_total.labels(
            backend="postgres", operation="get"
        )._value.get()
        record_repository_op(backend="postgres", operation="get")
        assert m.repository_operations_total.labels(
            backend="postgres", operation="get"
        )._value.get() == before + 1


# ==================== 2. 路径归一化 ====================


class TestPathNormalization:
    def test_strip_query(self):
        norm = m._normalize_path("/api/v1/share/cards/123?foo=bar")
        assert norm == "/api/v1/share/cards/{id}"

    def test_numeric_id(self):
        norm = m._normalize_path("/api/v1/share/cards/456")
        assert norm == "/api/v1/share/cards/{id}"

    def test_uuid(self):
        uuid = "12345678-1234-1234-1234-123456789012"
        norm = m._normalize_path(f"/api/v1/share/cards/{uuid}")
        assert norm == "/api/v1/share/cards/{id}"

    def test_short_code_preserved(self):
        # 短码不是纯数字也不是 UUID，保持原样
        norm = m._normalize_path("/api/v1/share/cards/abc123")
        assert norm == "/api/v1/share/cards/abc123"

    def test_root(self):
        assert m._normalize_path("/") == "/"


# ==================== 3. /metrics 端点 ====================


class TestMetricsEndpoint:
    def test_endpoint_returns_prometheus_text(self):
        app = FastAPI()
        app.include_router(metrics_router)
        client = TestClient(app)
        r = client.get("/metrics")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/plain")
        # 应该包含至少一个 imatoproject 指标
        assert b"imatoproject_" in r.content

    def test_endpoint_with_data(self):
        # 先记录一些数据
        record_share_card_created()
        record_invite_code_used()
        app = FastAPI()
        app.include_router(metrics_router)
        client = TestClient(app)
        r = client.get("/metrics")
        assert r.status_code == 200
        text = r.content.decode("utf-8")
        assert "imatoproject_share_cards_created_total" in text
        assert "imatoproject_invite_codes_used_total" in text


# ==================== 4. 中间件 ====================


class TestHTTPMiddleware:
    def test_middleware_records_request(self):
        app = FastAPI()
        if PrometheusHTTPMiddleware is not None:
            app.add_middleware(PrometheusHTTPMiddleware)
        else:
            pytest.skip("starlette BaseHTTPMiddleware 不可用")

        @app.get("/test/path")
        def handler():
            return {"ok": True}

        client = TestClient(app)
        before = m.http_requests_total.labels(
            method="GET", path="/test/path", status="200"
        )._value.get()
        r = client.get("/test/path")
        assert r.status_code == 200
        after = m.http_requests_total.labels(
            method="GET", path="/test/path", status="200"
        )._value.get()
        assert after >= before + 1

    def test_middleware_records_404(self):
        app = FastAPI()
        if PrometheusHTTPMiddleware is not None:
            app.add_middleware(PrometheusHTTPMiddleware)
        else:
            pytest.skip("starlette BaseHTTPMiddleware 不可用")

        client = TestClient(app)
        before = m.http_requests_total.labels(
            method="GET", path="/no-such-path", status="404"
        )._value.get()
        client.get("/no-such-path")
        after = m.http_requests_total.labels(
            method="GET", path="/no-such-path", status="404"
        )._value.get()
        assert after == before + 1


# ==================== 5. get_metrics_output 直接调用 ====================


class TestGetMetricsOutput:
    def test_returns_bytes(self):
        output = get_metrics_output()
        assert isinstance(output, bytes)
        assert b"imatoproject_" in output

    def test_contains_help_lines(self):
        output = get_metrics_output().decode("utf-8")
        # Prometheus 文本格式：每条指标都有 # HELP 和 # TYPE
        assert "# HELP imatoproject_http_requests_total" in output
        assert "# TYPE imatoproject_http_requests_total counter" in output

    def test_risk_gauges_updated(self):
        # 调用一次以触发 gauge 更新
        output = get_metrics_output().decode("utf-8")
        # 至少应该有 0
        assert "imatoproject_risk_blocked_ips" in output
