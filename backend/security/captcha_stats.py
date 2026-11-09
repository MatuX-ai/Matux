"""
【P3 后台】CAPTCHA 验证统计

- 记录验证尝试/成功/失败
- 按 provider / 错误码维度统计
- 用于管理面板展示与 Prometheus 上报

线程安全（threading.RLock）
"""

import logging
import threading
import time
from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Optional

from security.captcha import CaptchaProvider

logger = logging.getLogger(__name__)


# ==================== 数据结构 ====================


class CaptchaStats:
    """CAPTCHA 验证计数器（线程安全）"""

    def __init__(self, recent_window: int = 3600):
        """
        Args:
            recent_window: 统计"最近 N 秒"窗口大小（默认 1 小时）
        """
        self._lock = threading.RLock()
        # 总累计
        self._total_attempts: int = 0
        self._total_success: int = 0
        self._total_failure: int = 0
        # 按 provider
        self._per_provider: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"attempts": 0, "success": 0, "failure": 0}
        )
        # 按错误码
        self._per_error_code: Dict[str, int] = defaultdict(int)
        # 最近事件（用于实时面板）
        self._recent_events: Deque[Dict[str, Any]] = deque(maxlen=200)
        self._recent_window = recent_window

    def record_attempt(
        self,
        provider: CaptchaProvider,
        success: bool,
        ip: str = "",
        error_codes: Optional[List[str]] = None,
    ) -> None:
        with self._lock:
            self._total_attempts += 1
            provider_name = type(provider).__name__
            self._per_provider[provider_name]["attempts"] += 1

            if success:
                self._total_success += 1
                self._per_provider[provider_name]["success"] += 1
            else:
                self._total_failure += 1
                self._per_provider[provider_name]["failure"] += 1
                for code in error_codes or []:
                    self._per_error_code[code] += 1

            self._recent_events.append(
                {
                    "ts": time.time(),
                    "provider": provider_name,
                    "success": success,
                    "ip": ip,
                    "error_codes": error_codes or [],
                }
            )

    def record_success(
        self, provider: CaptchaProvider, ip: str = ""
    ) -> None:
        self.record_attempt(provider=provider, success=True, ip=ip)

    def record_failure(
        self, provider: CaptchaProvider,
        ip: str = "",
        error_codes: Optional[List[str]] = None,
    ) -> None:
        self.record_attempt(
            provider=provider, success=False, ip=ip, error_codes=error_codes
        )

    def get_snapshot(self) -> Dict[str, Any]:
        """导出当前统计快照"""
        with self._lock:
            success_rate = 0.0
            if self._total_attempts > 0:
                success_rate = round(
                    self._total_success / self._total_attempts * 100, 2
                )
            now = time.time()
            cutoff = now - self._recent_window
            recent_success = sum(
                1 for e in self._recent_events
                if e["ts"] >= cutoff and e["success"]
            )
            recent_failure = sum(
                1 for e in self._recent_events
                if e["ts"] >= cutoff and not e["success"]
            )
            return {
                "total_attempts": self._total_attempts,
                "total_success": self._total_success,
                "total_failure": self._total_failure,
                "success_rate_percent": success_rate,
                "recent_window_seconds": self._recent_window,
                "recent_success": recent_success,
                "recent_failure": recent_failure,
                "per_provider": dict(self._per_provider),
                "per_error_code": dict(self._per_error_code),
            }

    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._recent_events)[-max(1, limit):]

    def reset(self) -> None:
        with self._lock:
            self._total_attempts = 0
            self._total_success = 0
            self._total_failure = 0
            self._per_provider.clear()
            self._per_error_code.clear()
            self._recent_events.clear()
            logger.warning("CaptchaStats reset by admin")


# ==================== 全局单例 ====================


_stats: Optional[CaptchaStats] = None
_stats_lock = threading.Lock()


def get_captcha_stats() -> CaptchaStats:
    global _stats
    if _stats is None:
        with _stats_lock:
            if _stats is None:
                _stats = CaptchaStats()
    return _stats


def reset_captcha_stats_for_testing() -> None:
    global _stats
    with _stats_lock:
        _stats = None


# ==================== 快捷 API ====================


def record_attempt(
    provider: CaptchaProvider,
    success: bool,
    ip: str = "",
    error_codes: Optional[List[str]] = None,
) -> None:
    get_captcha_stats().record_attempt(
        provider=provider, success=success, ip=ip, error_codes=error_codes
    )


def record_success(provider: CaptchaProvider, ip: str = "") -> None:
    get_captcha_stats().record_success(provider=provider, ip=ip)


def record_failure(
    provider: CaptchaProvider,
    ip: str = "",
    error_codes: Optional[List[str]] = None,
) -> None:
    get_captcha_stats().record_failure(
        provider=provider, ip=ip, error_codes=error_codes
    )


__all__ = [
    "CaptchaStats",
    "get_captcha_stats",
    "reset_captcha_stats_for_testing",
    "record_attempt",
    "record_success",
    "record_failure",
]
