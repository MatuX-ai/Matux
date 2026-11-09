"""
【P3 后台】CAPTCHA 统计单元测试
"""

import os
import sys
import threading

import pytest

_BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from security.captcha import NoopCaptchaProvider  # noqa: E501, E402
from security.captcha_stats import (  # noqa: E501, E402
    CaptchaStats,
    record_attempt,
    record_failure,
    record_success,
    reset_captcha_stats_for_testing,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_captcha_stats_for_testing()
    yield
    reset_captcha_stats_for_testing()


class TestCaptchaStatsBasics:
    def test_empty_snapshot(self):
        stats = CaptchaStats()
        snap = stats.get_snapshot()
        assert snap["total_attempts"] == 0
        assert snap["total_success"] == 0
        assert snap["total_failure"] == 0
        assert snap["success_rate_percent"] == 0.0

    def test_record_attempt_success(self):
        stats = CaptchaStats()
        provider = NoopCaptchaProvider()
        stats.record_attempt(provider, success=True, ip="1.1.1.1")
        snap = stats.get_snapshot()
        assert snap["total_attempts"] == 1
        assert snap["total_success"] == 1
        assert snap["total_failure"] == 0
        assert snap["success_rate_percent"] == 100.0
        assert snap["per_provider"]["NoopCaptchaProvider"]["success"] == 1

    def test_record_attempt_failure_with_error_codes(self):
        stats = CaptchaStats()
        provider = NoopCaptchaProvider()
        stats.record_attempt(
            provider, success=False, ip="1.1.1.1",
            error_codes=["invalid-token", "expired"],
        )
        snap = stats.get_snapshot()
        assert snap["total_failure"] == 1
        assert snap["per_error_code"]["invalid-token"] == 1
        assert snap["per_error_code"]["expired"] == 1

    def test_record_success_helper(self):
        record_success(NoopCaptchaProvider(), ip="1.1.1.1")
        from security.captcha_stats import get_captcha_stats
        assert get_captcha_stats().get_snapshot()["total_success"] == 1

    def test_record_failure_helper(self):
        record_failure(NoopCaptchaProvider(), ip="1.1.1.1", error_codes=["x"])
        from security.captcha_stats import get_captcha_stats
        snap = get_captcha_stats().get_snapshot()
        assert snap["total_failure"] == 1
        assert snap["per_error_code"]["x"] == 1

    def test_record_attempt_helper(self):
        record_attempt(NoopCaptchaProvider(), success=True)
        from security.captcha_stats import get_captcha_stats
        assert get_captcha_stats().get_snapshot()["total_attempts"] == 1


class TestRecentEvents:
    def test_recent_events_capped(self):
        stats = CaptchaStats()
        provider = NoopCaptchaProvider()
        for i in range(500):
            stats.record_attempt(provider, success=True, ip=f"1.1.1.{i % 256}")
        # maxlen=200
        events = stats.get_recent_events(limit=1000)
        assert len(events) <= 200

    def test_recent_events_limit(self):
        stats = CaptchaStats()
        provider = NoopCaptchaProvider()
        for _ in range(50):
            stats.record_attempt(provider, success=True)
        events = stats.get_recent_events(limit=10)
        assert len(events) == 10

    def test_recent_window_counting(self):
        stats = CaptchaStats(recent_window=3600)
        provider = NoopCaptchaProvider()
        for _ in range(5):
            stats.record_attempt(provider, success=True)
        for _ in range(3):
            stats.record_attempt(provider, success=False)
        snap = stats.get_snapshot()
        assert snap["recent_success"] == 5
        assert snap["recent_failure"] == 3
        assert snap["recent_window_seconds"] == 3600


class TestReset:
    def test_reset_clears(self):
        stats = CaptchaStats()
        provider = NoopCaptchaProvider()
        stats.record_attempt(provider, success=True)
        stats.record_attempt(provider, success=False, error_codes=["x"])
        stats.reset()
        snap = stats.get_snapshot()
        assert snap["total_attempts"] == 0
        assert snap["per_error_code"] == {}


class TestThreadSafety:
    def test_concurrent_record(self):
        stats = CaptchaStats()
        provider = NoopCaptchaProvider()

        def writer(success: bool):
            for _ in range(100):
                stats.record_attempt(provider, success=success)

        threads = []
        for s in (True, False):
            for _ in range(5):
                t = threading.Thread(target=writer, args=(s,))
                threads.append(t)
                t.start()
        for t in threads:
            t.join()
        snap = stats.get_snapshot()
        assert snap["total_attempts"] == 1000


class TestMultiProvider:
    def test_per_provider_breakdown(self):
        from security.captcha import HCaptchaProvider

        stats = CaptchaStats()
        noop = NoopCaptchaProvider()
        hcap = HCaptchaProvider(secret="test_secret")

        stats.record_attempt(noop, success=True, ip="1.1.1.1")
        stats.record_attempt(noop, success=True, ip="2.2.2.2")
        stats.record_attempt(hcap, success=False, ip="3.3.3.3", error_codes=["expired"])

        snap = stats.get_snapshot()
        assert snap["per_provider"]["NoopCaptchaProvider"]["attempts"] == 2
        assert snap["per_provider"]["NoopCaptchaProvider"]["success"] == 2
        assert snap["per_provider"]["HCaptchaProvider"]["attempts"] == 1
        assert snap["per_provider"]["HCaptchaProvider"]["failure"] == 1
        assert snap["per_error_code"]["expired"] == 1
