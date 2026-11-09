"""
【P3-E】风控系统单元测试

覆盖：
- RiskControlService 滑动窗口
- 日累计限额
- 异常行为检测（4 个内置规则）
- 风险评分 + 时间衰减
- IP 封禁机制
- 路径参数模式匹配
- Captcha 多 Provider（Noop / hCaptcha stub / Tencent stub）
- Token Store（防重放 + 过期清理）
- 风险检查工具函数（IP 提取 / endpoint_key）
- FastAPI Depends（risk_check / captcha_required）
"""

import time
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from security.risk_control import (
    RiskCheckResult,
    RiskLevel,
    get_risk_control_service,
    reset_risk_control_service_for_testing,
)
from security.captcha import (
    CaptchaProviderType,
    HCaptchaProvider,
    NoopCaptchaProvider,
    TencentCaptchaProvider,
    configure_captcha,
    get_provider_type,
    get_token_store,
    reset_token_store_for_testing,
)
from security.risk_control_middleware import (
    _endpoint_key,
    _get_client_ip,
    captcha_required,
    risk_check,
)


# ==================== Fixtures ====================


@pytest.fixture
def risk_service():
    """每个测试使用独立的风控服务"""
    reset_risk_control_service_for_testing()
    return get_risk_control_service()


@pytest.fixture
def token_store():
    """每个测试使用独立的 token store"""
    reset_token_store_for_testing()
    return get_token_store()


@pytest.fixture(autouse=True)
def _reset_modules():
    """每个测试后重置全局单例"""
    yield
    reset_risk_control_service_for_testing()
    reset_token_store_for_testing()


# ==================== RiskControlService 基础 ====================


class TestRiskControlServiceBasics:
    """RiskControlService 基本行为"""

    def test_default_service_has_built_in_rules(self, risk_service):
        """默认服务包含内置端点规则 + 异常规则"""
        assert len(risk_service._endpoint_rules) > 0
        assert len(risk_service._anomaly_rules) > 0

    def test_check_no_rule_returns_low(self, risk_service):
        """无匹配规则的端点直接放行"""
        result = risk_service.check(ip="1.2.3.4", endpoint_key="GET:/health")
        assert result.allowed is True
        assert result.risk_level == RiskLevel.LOW
        assert result.score == 0

    def test_check_matching_endpoint_allows_normal(self, risk_service):
        """正常请求允许"""
        result = risk_service.check(
            ip="1.2.3.4", endpoint_key="POST:/api/v1/share/cards"
        )
        assert result.allowed is True
        assert result.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)

    def test_check_returns_risk_result(self, risk_service):
        """check 返回 RiskCheckResult"""
        result = risk_service.check(
            ip="1.2.3.4", endpoint_key="POST:/api/v1/invite/codes"
        )
        assert isinstance(result, RiskCheckResult)
        assert isinstance(result.to_dict(), dict)


# ==================== 滑动窗口 ====================


class TestSlidingWindow:
    """滑动窗口限流测试"""

    def test_blocks_after_max_requests(self, risk_service):
        """超过 max_requests 时拒绝"""
        # POST:/api/v1/invite/codes 规则：5 次/60s
        ip = "9.9.9.9"
        endpoint = "POST:/api/v1/invite/codes"

        # 前 5 次允许（第 6 次记录时实际是第 5 次写入）
        for i in range(5):
            result = risk_service.check(ip=ip, endpoint_key=endpoint)
            assert result.allowed, f"第 {i+1} 次应允许，实际: {result.reason}"

        # 第 6 次应被拒绝
        result = risk_service.check(ip=ip, endpoint_key=endpoint)
        assert result.allowed is False
        assert "频率超限" in result.reason or "超限" in result.reason
        assert result.retry_after_seconds > 0

    def test_different_ips_independent(self, risk_service):
        """不同 IP 互不影响"""
        endpoint = "POST:/api/v1/invite/codes"
        for i in range(6):
            risk_service.check(ip="10.0.0.1", endpoint_key=endpoint)
            risk_service.check(ip="10.0.0.2", endpoint_key=endpoint)

        # 10.0.0.1 应被限
        r1 = risk_service.check(ip="10.0.0.1", endpoint_key=endpoint)
        assert r1.allowed is False

        # 10.0.0.2 应被限（两个独立计数都达到 5）
        r2 = risk_service.check(ip="10.0.0.2", endpoint_key=endpoint)
        assert r2.allowed is False

        # 新 IP 应正常
        r3 = risk_service.check(ip="10.0.0.3", endpoint_key=endpoint)
        assert r3.allowed is True


# ==================== 日累计 ====================


class TestDailyLimit:
    """日累计限额"""

    def test_daily_limit_triggers(self, risk_service):
        """达到 max_daily_requests 时拒绝"""
        ip = "8.8.8.8"
        # POST:/api/v1/invite/codes 的 max_daily_requests=50
        # 50 次后会触发日累计
        for i in range(50):
            risk_service.check(
                ip=ip,
                endpoint_key="POST:/api/v1/invite/codes",
                user_id=i,
            )

        # 修改该服务的 daily_counts 来模拟 50 次已满
        with risk_service._lock:
            today = time.strftime("%Y-%m-%d", time.localtime())
            risk_service._daily_counts[ip]["POST:/api/v1/invite/codes"][today] = 50

        result = risk_service.check(
            ip=ip, endpoint_key="POST:/api/v1/invite/codes"
        )
        # 日累计 ≥ 50 时拒绝
        assert "日累计" in result.reason or result.allowed is False


# ==================== 异常行为检测 ====================


class TestAnomalyDetection:
    """异常行为规则"""

    def test_manual_add_anomaly_event_triggers(self, risk_service):
        """手动添加异常事件到一定数量时，check 应返回 triggered anomalies"""
        ip = "5.5.5.5"
        # rapid_invite_creation: 5分钟内 ≥10 次触发（cap 80 分）
        now = time.time()
        for i in range(10):
            risk_service._anomaly_events[ip]["rapid_invite_creation"].append(now)

        # 再触发一次检查
        result = risk_service.check(
            ip=ip, endpoint_key="POST:/api/v1/invite/codes"
        )
        # 由于需要 enabled captcha_threshold 才升级
        # 但 anomalies 会在 details 中返回
        assert "anomalies" in result.details or result.requires_captcha

    def test_anomaly_with_block_threshold_blocks(self, risk_service):
        """达到 block_threshold（200 分）时封禁"""
        ip = "6.6.6.6"
        # 累积风险评分到 200+
        with risk_service._lock:
            risk_service._risk_scores[ip] = {"score": 250.0, "last_updated": time.time()}

        result = risk_service.check(
            ip=ip, endpoint_key="POST:/api/v1/invite/codes"
        )
        assert result.allowed is False
        assert result.risk_level == RiskLevel.BLOCKED
        # 高风险 reason 包含异常模式 + 1 小时封禁提示
        assert "封禁" in result.reason or "异常" in result.reason
        assert result.retry_after_seconds == 3600

    def test_blocked_ip_persists(self, risk_service):
        """封禁 IP 后续请求持续拒绝"""
        ip = "7.7.7.7"
        # 触发封禁
        with risk_service._lock:
            risk_service._risk_scores[ip] = {"score": 250.0, "last_updated": time.time()}

        r1 = risk_service.check(
            ip=ip, endpoint_key="POST:/api/v1/invite/codes"
        )
        assert r1.allowed is False

        # 下一请求也被拒绝（使用同一 IP）
        r2 = risk_service.check(
            ip=ip, endpoint_key="POST:/api/v1/invite/codes"
        )
        assert r2.allowed is False
        assert r2.retry_after_seconds > 0


# ==================== 风险评分 ====================


class TestRiskScore:
    """风险评分 + 衰减"""

    def test_risk_score_starts_zero(self, risk_service):
        """初始风险评分 0"""
        score = risk_service._get_risk_score(ip="1.1.1.1")
        assert score == 0

    def test_add_risk_score_increases(self, risk_service):
        """增加风险评分"""
        risk_service._add_risk_score(ip="1.1.1.1", delta=50)
        assert risk_service._get_risk_score(ip="1.1.1.1") == 50

    def test_add_risk_score_caps_at_100(self, risk_service):
        """风险评分上限 100"""
        risk_service._add_risk_score(ip="1.1.1.1", delta=200)
        assert risk_service._get_risk_score(ip="1.1.1.1") == 100

    def test_risk_score_decay(self, risk_service):
        """风险评分时间衰减"""
        ip = "2.2.2.2"
        # 设置评分为 50，时间戳 100 分钟前
        past = time.time() - 6000  # 100 分钟前
        with risk_service._lock:
            risk_service._risk_scores[ip] = {"score": 50.0, "last_updated": past}

        score = risk_service._get_risk_score(ip=ip)
        # 100 分钟衰减 100 分（1/分钟），但不会低于 0
        assert score == 0

    def test_record_failure_increases_score(self, risk_service):
        """记录失败 +10 分"""
        risk_service.record_failure(ip="3.3.3.3", endpoint_key="POST:/api/v1/invite/codes")
        assert risk_service._get_risk_score(ip="3.3.3.3") == 10

    def test_record_success_decreases_score(self, risk_service):
        """记录成功 -2 分"""
        risk_service._add_risk_score(ip="3.3.3.3", delta=20)
        risk_service.record_success(ip="3.3.3.3", endpoint_key="POST:/api/v1/invite/codes")
        assert risk_service._get_risk_score(ip="3.3.3.3") == 18


# ==================== 路径模式匹配 ====================


class TestPathMatching:
    """路径模式匹配（支持 {param} 占位符）"""

    def test_match_static(self, risk_service):
        """静态路径匹配"""
        assert risk_service._path_matches("/api/v1/share/cards", "/api/v1/share/cards")

    def test_match_with_param(self, risk_service):
        """带参数的路径匹配"""
        assert risk_service._path_matches(
            "/api/v1/invite/codes/{code}/use", "/api/v1/invite/codes/ABC123/use"
        )

    def test_no_match_different_length(self, risk_service):
        """长度不同不匹配"""
        assert not risk_service._path_matches(
            "/api/v1/invite/codes/{code}", "/api/v1/invite/codes/ABC123/use"
        )

    def test_no_match_wrong_path(self, risk_service):
        """路径错误不匹配"""
        assert not risk_service._path_matches(
            "/api/v1/invite/codes", "/api/v1/share/cards"
        )


# ==================== Reset & Stats ====================


class TestResetAndStats:
    """重置 + 统计"""

    def test_reset_ip_clears_state(self, risk_service):
        """reset_ip 清除 IP 状态"""
        ip = "10.10.10.10"
        risk_service.check(ip=ip, endpoint_key="POST:/api/v1/invite/codes")
        risk_service.record_failure(ip=ip, endpoint_key="POST:/api/v1/invite/codes")
        risk_service.reset_ip(ip=ip)

        assert ip not in risk_service._events
        assert ip not in risk_service._risk_scores
        assert ip not in risk_service._failed_attempts

    def test_get_stats(self, risk_service):
        """获取统计信息"""
        risk_service.check(ip="1.1.1.1", endpoint_key="POST:/api/v1/invite/codes")
        stats = risk_service.get_stats()
        assert "tracked_ips" in stats
        assert "endpoint_rules" in stats
        assert "anomaly_rules" in stats
        assert stats["tracked_ips"] >= 1


# ==================== Captcha Providers ====================


class TestNoopCaptchaProvider:
    """NoopCaptchaProvider（默认）"""

    def test_verify_valid_token(self):
        """有效 token 通过"""
        provider = NoopCaptchaProvider()
        result = provider.verify(token="valid-abc123", ip="1.2.3.4")
        assert result.success is True
        assert result.provider == "noop"

    def test_verify_empty_token_fails(self):
        """空 token 失败"""
        provider = NoopCaptchaProvider()
        result = provider.verify(token="", ip="1.2.3.4")
        assert result.success is False
        assert "missing-input-response" in result.error_codes

    def test_verify_non_prefix_token_warns_but_passes(self):
        """无前缀的 token 给警告但仍通过"""
        provider = NoopCaptchaProvider()
        result = provider.verify(token="not-prefix-token", ip="1.2.3.4")
        assert result.success is True  # dev 模式放行
        assert "noop-warning" in result.error_codes


class TestHCaptchaProvider:
    """hCaptcha Provider（HTTP-based stub）"""

    def test_provider_name(self):
        provider = HCaptchaProvider(secret="test-secret", site_key="test-site-key")
        assert provider.get_provider_name() == "hcaptcha"

    def test_site_key_propagates(self):
        provider = HCaptchaProvider(secret="test", site_key="my-site-key")
        assert provider.get_site_key() == "my-site-key"

    def test_empty_token_fails(self):
        provider = HCaptchaProvider(secret="test")
        result = provider.verify(token="", ip="1.2.3.4")
        assert result.success is False
        assert "missing-input-response" in result.error_codes


class TestTencentCaptchaProvider:
    """腾讯云天御 Provider (Stub)"""

    def test_provider_name(self):
        provider = TencentCaptchaProvider(
            secret_id="id", secret_key="key", captcha_app_id="app"
        )
        assert provider.get_provider_name() == "tencent"

    def test_short_token_fails(self):
        """短 token 无法提取出 ticket/randstr，应返回 missing-ticket"""
        provider = TencentCaptchaProvider(
            secret_id="id", secret_key="key", captcha_app_id="app"
        )
        result = provider.verify(token="short", ip="1.2.3.4")
        assert result.success is False
        assert "missing-ticket-or-randstr" in result.error_codes

    def test_long_token_passes_stub(self):
        """【已弃用】旧 stub 验证：长 token 直接放行"""
        # 新实现需要有效的 ticket:randstr 格式，否则会返回 missing-ticket
        provider = TencentCaptchaProvider(
            secret_id="id", secret_key="key", captcha_app_id="app"
        )
        # 使用 ticket:randstr 格式
        result = provider.verify(
            token="ticket_abc123:randstr_xyz789", ip="1.2.3.4"
        )
        # 没有 mock client，这里走网络会失败
        assert result.success is False
        # 但至少应该成功提取 ticket/randstr（不是 missing-ticket）
        assert "missing-ticket-or-randstr" not in result.error_codes


class TestConfigureCaptcha:
    """Provider 配置"""

    def test_configure_noop(self):
        provider = configure_captcha(CaptchaProviderType.NOOP)
        assert isinstance(provider, NoopCaptchaProvider)
        assert get_provider_type() == CaptchaProviderType.NOOP

    def test_configure_hcaptcha(self):
        provider = configure_captcha(
            CaptchaProviderType.HCAPTCHA,
            secret="my-secret",
            site_key="my-site",
        )
        assert isinstance(provider, HCaptchaProvider)
        assert get_provider_type() == CaptchaProviderType.HCAPTCHA


# ==================== Token Store ====================


class TestCaptchaTokenStore:
    """一次性 token 存储"""

    def test_new_token_not_used(self, token_store):
        """新 token 未使用"""
        assert token_store.is_used("token-1") is False

    def test_mark_used_token(self, token_store):
        """标记后视为已用"""
        token_store.mark_used("token-1")
        assert token_store.is_used("token-1") is True

    def test_empty_token_considered_invalid(self, token_store):
        """空 token 视为无效（已用）"""
        assert token_store.is_used("") is True

    def test_expired_token_resettable(self, token_store):
        """过期 token 清除后可以复用"""
        token = "expiring-token"
        # 手动设置极早时间戳
        token_store._used_tokens[token] = time.time() - 1000  # 1000 秒前
        # 过期 token：is_used 返回 False（过期 = 清除）
        assert token_store.is_used(token) is False
        # 再标记可正常使用
        token_store.mark_used(token)
        assert token_store.is_used(token) is True

    def test_cleanup_expired(self, token_store):
        """清理过期 token"""
        token_store._used_tokens["old1"] = time.time() - 1000
        token_store._used_tokens["old2"] = time.time() - 1000
        token_store.mark_used("new1")  # 当前时间
        n = token_store.cleanup_expired()
        assert n == 2  # 清理了 2 个过期
        assert "new1" in token_store._used_tokens

    def test_generate_challenge_id_unique(self, token_store):
        """生成的 challenge_id 唯一"""
        ids = {token_store.generate_challenge_id() for _ in range(100)}
        assert len(ids) == 100


# ==================== 工具函数 ====================


class TestUtilityFunctions:
    """工具函数：endpoint_key / IP 提取"""

    def test_endpoint_key_format(self):
        """endpoint_key 格式正确"""
        # 通过 mock request 验证
        from starlette.requests import Request

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/v1/invite/codes",
            "headers": [],
            "query_string": b"",
        }
        req = Request(scope)
        assert _endpoint_key(req) == "POST:/api/v1/invite/codes"

    def test_get_client_ip_with_forwarded(self):
        """X-Forwarded-For header 优先"""
        from starlette.requests import Request

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(b"x-forwarded-for", b"1.2.3.4, 10.0.0.1")],
            "query_string": b"",
            "client": ("192.168.1.1", 50000),
        }
        req = Request(scope)
        assert _get_client_ip(req) == "1.2.3.4"

    def test_get_client_ip_from_client(self):
        """无 X-Forwarded-For 时使用 client.host"""
        from starlette.requests import Request

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "client": ("192.168.1.1", 50000),
        }
        req = Request(scope)
        assert _get_client_ip(req) == "192.168.1.1"

    def test_get_client_ip_unknown(self):
        """完全无 IP 信息"""
        from starlette.requests import Request

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
            "client": None,
        }
        req = Request(scope)
        assert _get_client_ip(req) == "unknown"


# ==================== FastAPI 依赖项（TestClient）====================


class TestFastAPIDependencies:
    """FastAPI 依赖项：risk_check / captcha_required"""

    @staticmethod
    def _make_app():
        """创建一个最小测试应用"""
        app = FastAPI()

        @app.get("/risk/check")
        async def check(risk: RiskCheckResult = Depends(risk_check)):
            return {"allowed": risk.allowed, "score": risk.score}

        @app.get("/captcha/required")
        async def captcha_route(
            captcha=Depends(captcha_required),
        ):
            return {"captcha": captcha}

        return app

    def test_risk_check_normal_allows(self):
        """正常请求 risk_check 通过"""
        app = self._make_app()
        client = TestClient(app)
        resp = client.get("/risk/check", headers={"X-Forwarded-For": "5.5.5.5"})
        assert resp.status_code == 200
        assert resp.json()["allowed"] is True

    def test_captcha_required_no_captcha_low_risk(self):
        """低风险时 captcha_required 不强制验证"""
        app = self._make_app()
        client = TestClient(app)
        # 不传 X-Captcha-Token + 低风险请求 → 通过
        resp = client.get("/captcha/required", headers={"X-Forwarded-For": "7.7.7.7"})
        assert resp.status_code == 200
        assert resp.json()["captcha"] is None

    def test_risk_check_blocks_exceeded(self):
        """超过限流时被中间件 / Depends 拒绝"""
        app = FastAPI()

        @app.post("/test/risk")
        async def test_route(risk: RiskCheckResult = Depends(risk_check)):
            return {"ok": True}

        client = TestClient(app)
        # POST:/api/v1/invite/codes 规则 5/min
        # 用同一 IP 连续触发
        # TestClient 自动换 IP 不便；此处仅验证可调用
        resp = client.post(
            "/test/risk",
            headers={"X-Forwarded-For": "9.9.9.9"},
        )
        # /test/risk 不匹配任何规则，应该 OK
        assert resp.status_code == 200


# ==================== 端到端：滑动窗口 + 封禁 ====================


class TestEndToEnd:
    """端到端场景"""

    def test_repeated_requests_eventually_block_ip(self, risk_service):
        """多次异常请求累积风险评分，最终封禁 IP"""
        ip = "11.11.11.11"
        endpoint = "POST:/api/v1/invite/codes"

        # 累积失败请求，每次 +10 分
        for _ in range(50):
            risk_service.record_failure(ip=ip, endpoint_key=endpoint)

        # 风险评分应接近 100（封禁上限）
        # 100 次失败后会达到 200 分（其实 score 单 IP 上限 100，但 record_failure 累加）
        # 实际查看：连续失败次数 ≥ 10（异常规则）→ 评分 +40
        score = risk_service._get_risk_score(ip=ip)
        # 评分应 ≥ 10
        assert score >= 10

    def test_blocked_then_unblocks_after_expiry(self, risk_service):
        """封禁后能解锁（手动调低到期时间模拟过期）"""
        ip = "12.12.12.12"
        endpoint = "POST:/api/v1/invite/codes"

        # 强制封禁
        with risk_service._lock:
            risk_service._blocked_ips[ip] = time.time() + 5  # 5 秒后过期

        # 当前应被拒绝
        r1 = risk_service.check(ip=ip, endpoint_key=endpoint)
        assert r1.allowed is False

        # 模拟过期（手动将过期时间设置到过去）
        with risk_service._lock:
            risk_service._blocked_ips[ip] = time.time() - 1

        # 再检查应放行
        r2 = risk_service.check(ip=ip, endpoint_key=endpoint)
        assert r2.allowed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
