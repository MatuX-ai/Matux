"""
【P3 后台】风控管理 API 测试

使用 FastAPI TestClient，验证所有管理端点：
- /stats
- /blocked-ips (CRUD)
- /scores
- /ip/{ip}
- /reset
- /rules/endpoints
- /rules/anomalies
- /captcha/stats
- /captcha/reset-stats
- /health
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

from routes.admin_risk_control_routes import router as admin_router  # noqa: E501, E402
from security.captcha_stats import (  # noqa: E501, E402
    get_captcha_stats,
    reset_captcha_stats_for_testing,
)
from security.risk_control import (  # noqa: E501, E402
    reset_risk_control_service_for_testing,
    get_risk_control_service,
)


@pytest.fixture
def client():
    app = FastAPI(title="TestApp")
    app.include_router(admin_router)
    # 重置单例
    reset_risk_control_service_for_testing()
    reset_captcha_stats_for_testing()
    with TestClient(app) as c:
        yield c
    reset_risk_control_service_for_testing()
    reset_captcha_stats_for_testing()


# ==================== /health ====================


class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/api/v1/admin/risk/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service_alive"] is True


# ==================== /stats ====================


class TestStats:
    def test_stats_empty(self, client):
        r = client.get("/api/v1/admin/risk/stats")
        assert r.status_code == 200
        data = r.json()
        assert "risk_control" in data
        assert "captcha" in data
        assert data["risk_control"]["tracked_ips"] == 0
        assert data["risk_control"]["blocked_ips"] == 0

    def test_stats_after_traffic(self, client):
        service = get_risk_control_service()
        for i in range(5):
            service.check(ip=f"1.1.1.{i}", endpoint_key="POST:/api/v1/share/cards")
        r = client.get("/api/v1/admin/risk/stats")
        assert r.json()["risk_control"]["tracked_ips"] >= 5


# ==================== /blocked-ips CRUD ====================


class TestBlockedIPs:
    def test_list_empty(self, client):
        r = client.get("/api/v1/admin/risk/blocked-ips")
        assert r.status_code == 200
        assert r.json() == {"total": 0, "items": []}

    def test_block_ip(self, client):
        r = client.post(
            "/api/v1/admin/risk/blocked-ips",
            json={"ip": "192.168.1.100", "duration_seconds": 600, "reason": "test"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["ip"] == "192.168.1.100"
        assert data["duration_seconds"] == 600
        assert data["reason"] == "test"

    def test_list_after_block(self, client):
        client.post(
            "/api/v1/admin/risk/blocked-ips",
            json={"ip": "10.0.0.1", "duration_seconds": 300},
        )
        client.post(
            "/api/v1/admin/risk/blocked-ips",
            json={"ip": "10.0.0.2", "duration_seconds": 600},
        )
        r = client.get("/api/v1/admin/risk/blocked-ips")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        ips = [item["ip"] for item in data["items"]]
        assert "10.0.0.1" in ips
        assert "10.0.0.2" in ips

    def test_unblock_ip(self, client):
        client.post(
            "/api/v1/admin/risk/blocked-ips",
            json={"ip": "1.2.3.4", "duration_seconds": 3600},
        )
        r = client.delete("/api/v1/admin/risk/blocked-ips/1.2.3.4")
        assert r.status_code == 200
        assert r.json()["unblocked"] is True

    def test_unblock_nonexistent(self, client):
        r = client.delete("/api/v1/admin/risk/blocked-ips/0.0.0.0")
        assert r.status_code == 404

    def test_block_validation(self, client):
        # duration too long
        r = client.post(
            "/api/v1/admin/risk/blocked-ips",
            json={"ip": "1.1.1.1", "duration_seconds": 999999999},
        )
        assert r.status_code == 422

    def test_block_missing_ip(self, client):
        r = client.post(
            "/api/v1/admin/risk/blocked-ips",
            json={"duration_seconds": 60},
        )
        assert r.status_code == 422


# ==================== /scores ====================


class TestScores:
    def test_empty(self, client):
        r = client.get("/api/v1/admin/risk/scores")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_top_risks(self, client):
        service = get_risk_control_service()
        # 制造一些失败
        for _ in range(15):
            service.record_failure("1.1.1.1", "POST:/api/v1/share/cards")
        service.record_failure("2.2.2.2", "POST:/api/v1/share/cards")

        r = client.get("/api/v1/admin/risk/scores?limit=5")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 2
        # 第一个应该是分数最高的
        assert data["items"][0]["ip"] in ("1.1.1.1", "2.2.2.2")
        assert data["items"][0]["score"] >= data["items"][1]["score"]

    def test_limit_validation(self, client):
        r = client.get("/api/v1/admin/risk/scores?limit=99999")
        assert r.status_code == 422


# ==================== /ip/{ip} ====================


class TestIPDetail:
    def test_ip_detail(self, client):
        service = get_risk_control_service()
        service.check(ip="5.5.5.5", endpoint_key="POST:/api/v1/share/cards")
        service.check(
            ip="5.5.5.5", endpoint_key="POST:/api/v1/invite/codes"
        )
        r = client.get("/api/v1/admin/risk/ip/5.5.5.5")
        assert r.status_code == 200
        data = r.json()
        assert data["ip"] == "5.5.5.5"
        assert "POST:/api/v1/share/cards" in data["active_endpoints"]
        assert "POST:/api/v1/invite/codes" in data["active_endpoints"]

    def test_blocked_ip_detail(self, client):
        client.post(
            "/api/v1/admin/risk/blocked-ips",
            json={"ip": "9.9.9.9", "duration_seconds": 600},
        )
        r = client.get("/api/v1/admin/risk/ip/9.9.9.9")
        assert r.json()["is_blocked"] is True


# ==================== /reset ====================


class TestReset:
    def test_reset_all(self, client):
        service = get_risk_control_service()
        service.check(ip="1.1.1.1", endpoint_key="POST:/api/v1/share/cards")
        service.check(ip="2.2.2.2", endpoint_key="POST:/api/v1/share/cards")
        client.post(
            "/api/v1/admin/risk/blocked-ips",
            json={"ip": "1.1.1.1", "duration_seconds": 600},
        )

        r = client.post("/api/v1/admin/risk/reset")
        assert r.status_code == 200
        data = r.json()
        assert data["cleared_ips"] >= 2
        # 验证已清空
        r2 = client.get("/api/v1/admin/risk/stats")
        assert r2.json()["risk_control"]["tracked_ips"] == 0


# ==================== /rules ====================


class TestRules:
    def test_endpoint_rules(self, client):
        r = client.get("/api/v1/admin/risk/rules/endpoints")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 6  # 至少 6 个默认规则
        # 第一个规则字段齐全
        rule = data["items"][0]
        assert "method" in rule
        assert "path_pattern" in rule
        assert "max_requests" in rule

    def test_anomaly_rules(self, client):
        r = client.get("/api/v1/admin/risk/rules/anomalies")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 4  # 至少 4 个默认异常规则


# ==================== /captcha/stats ====================


class TestCaptchaStats:
    def test_empty(self, client):
        r = client.get("/api/v1/admin/risk/captcha/stats")
        assert r.status_code == 200
        data = r.json()
        assert data["total_attempts"] == 0
        assert data["total_success"] == 0
        assert data["success_rate_percent"] == 0.0

    def test_record_and_query(self, client):
        from security.captcha import NoopCaptchaProvider

        stats = get_captcha_stats()
        provider = NoopCaptchaProvider()
        stats.record_attempt(provider, success=True, ip="1.1.1.1")
        stats.record_attempt(provider, success=True, ip="2.2.2.2")
        stats.record_attempt(
            provider, success=False, ip="3.3.3.3", error_codes=["invalid-token"]
        )

        r = client.get("/api/v1/admin/risk/captcha/stats")
        data = r.json()
        assert data["total_attempts"] == 3
        assert data["total_success"] == 2
        assert data["total_failure"] == 1
        assert data["success_rate_percent"] == pytest.approx(66.67, abs=0.01)
        assert data["per_error_code"]["invalid-token"] == 1

    def test_recent_events(self, client):
        from security.captcha import NoopCaptchaProvider

        stats = get_captcha_stats()
        provider = NoopCaptchaProvider()
        for i in range(5):
            stats.record_attempt(provider, success=True, ip=f"1.1.1.{i}")

        r = client.get("/api/v1/admin/risk/captcha/stats")
        data = r.json()
        assert len(data["recent_events"]) == 5

    def test_reset_stats(self, client):
        from security.captcha import NoopCaptchaProvider

        stats = get_captcha_stats()
        provider = NoopCaptchaProvider()
        stats.record_attempt(provider, success=True)

        r = client.post("/api/v1/admin/risk/captcha/reset-stats")
        assert r.status_code == 200
        assert get_captcha_stats().get_snapshot()["total_attempts"] == 0
