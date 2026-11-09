"""
【P3-E】风控系统核心服务

功能：
- 滑动窗口精确限流（per-IP, per-endpoint）
- 异常行为检测（短时间大量请求 + 模式匹配）
- 风险评分（多因素累积打分）
- 自动升级（多次异常 → CAPTCHA 挑战 → 临时封禁）

依赖：
- 可选 Redis（提升精度 + 跨进程共享状态）
- 默认使用内存 + threading.Lock（单进程足够）

使用：
    from security.risk_control import RiskControlService, RiskLevel

    service = get_risk_control_service()
    result = service.check(
        ip="1.2.3.4",
        user_id=42,
        endpoint="POST:/api/v1/invite/codes",
    )
    if not result.allowed:
        raise HTTPException(429, detail=result.reason)
    if result.requires_captcha:
        # 前端弹出 CAPTCHA
        pass
"""

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


# ==================== 风险等级 ====================


class RiskLevel(str, Enum):
    """风险等级（从低到高）"""

    LOW = "low"  # 正常请求
    MEDIUM = "medium"  # 可疑行为，需要 CAPTCHA
    HIGH = "high"  # 高风险，拒绝请求
    BLOCKED = "blocked"  # 已封禁


@dataclass
class RiskCheckResult:
    """风控检查结果"""

    allowed: bool
    risk_level: RiskLevel
    score: int  # 0-100 综合风险评分
    reason: str = ""
    requires_captcha: bool = False
    retry_after_seconds: int = 0
    details: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "allowed": self.allowed,
            "risk_level": self.risk_level.value,
            "score": self.score,
            "reason": self.reason,
            "requires_captcha": self.requires_captcha,
            "retry_after_seconds": self.retry_after_seconds,
            "details": self.details,
        }


# ==================== 端点规则 ====================


@dataclass
class EndpointRule:
    """
    单个端点的风控规则

    各字段语义：
    - max_requests / window_seconds：滑动窗口限流（瞬时高频防护）
    - max_daily_requests：日累计阈值（防刷量）
    - captcha_threshold：触发 CAPTCHA 验证的累计风险评分阈值
    - block_threshold：封禁阈值（达到后 1 小时内拒绝）
    """

    method: str  # "GET" / "POST" / "PUT" / "DELETE" / "*"
    path_pattern: str  # "/api/v1/invite/codes/{code}/use"
    max_requests: int = 30  # 滑动窗口最大请求数
    window_seconds: int = 60  # 滑动窗口大小（秒）
    max_daily_requests: int = 500  # 24 小时累计上限
    captcha_threshold: int = 50  # 评分 ≥ 此值 → 触发 CAPTCHA
    block_threshold: int = 200  # 评分 ≥ 此值 → 拒绝


# 默认端点风控规则（P3-C 社交分享 / 邀请码）
DEFAULT_ENDPOINT_RULES: List[EndpointRule] = [
    EndpointRule(
        method="POST",
        path_pattern="/api/v1/share/cards",
        max_requests=10,  # 10 次/分钟 创建
        window_seconds=60,
        max_daily_requests=200,
    ),
    EndpointRule(
        method="POST",
        path_pattern="/api/v1/share/cards/{short_code}/track-view",
        max_requests=120,  # 浏览可宽松（落地页）
        window_seconds=60,
        max_daily_requests=5000,
    ),
    EndpointRule(
        method="POST",
        path_pattern="/api/v1/share/cards/{short_code}/track-share",
        max_requests=20,
        window_seconds=60,
        max_daily_requests=500,
    ),
    EndpointRule(
        method="POST",
        path_pattern="/api/v1/invite/codes",
        max_requests=5,  # 严控：刷邀请码推广
        window_seconds=60,
        max_daily_requests=50,
        captcha_threshold=20,  # 更敏感
    ),
    EndpointRule(
        method="POST",
        path_pattern="/api/v1/invite/codes/{code}/use",
        max_requests=10,
        window_seconds=60,
        max_daily_requests=100,
        captcha_threshold=30,
    ),
    EndpointRule(
        method="GET",
        path_pattern="/api/v1/invite/codes/{code}",
        max_requests=60,  # 查询邀请码（公开）可宽松
        window_seconds=60,
        max_daily_requests=2000,
    ),
]


# ==================== 异常行为模式 ====================


@dataclass
class AnomalyRule:
    """异常行为检测规则"""

    name: str
    description: str
    window_seconds: int  # 检测窗口
    threshold: int  # 触发阈值
    score_delta: int  # 触发后风险评分增量


DEFAULT_ANOMALY_RULES: List[AnomalyRule] = [
    AnomalyRule(
        name="rapid_invite_creation",
        description="短时间大量生成邀请码",
        window_seconds=300,  # 5 分钟
        threshold=10,
        score_delta=80,
    ),
    AnomalyRule(
        name="rapid_share_card_creation",
        description="短时间大量创建分享卡片",
        window_seconds=300,
        threshold=20,
        score_delta=60,
    ),
    AnomalyRule(
        name="rapid_invite_use",
        description="频繁使用不同邀请码（机器人）",
        window_seconds=120,  # 2 分钟
        threshold=15,
        score_delta=100,
    ),
    AnomalyRule(
        name="consecutive_failures",
        description="连续失败（多次 4xx 请求）",
        window_seconds=60,
        threshold=10,
        score_delta=40,
    ),
]


# ==================== 风控服务 ====================


class RiskControlService:
    """
    风控服务（单例 + 滑动窗口 + 风险评分）

    数据结构：
    - _events[ip][endpoint]：deque[float] 滑动窗口请求时间戳
    - _daily_counts[ip][endpoint][date]：int 日累计计数
    - _risk_scores[ip]：int 当前风险评分（带时间衰减）
    - _failed_attempts[ip]：deque[float] 失败请求时间戳
    """

    def __init__(
        self,
        endpoint_rules: Optional[List[EndpointRule]] = None,
        anomaly_rules: Optional[List[AnomalyRule]] = None,
    ):
        self._endpoint_rules = endpoint_rules or DEFAULT_ENDPOINT_RULES
        self._anomaly_rules = anomaly_rules or DEFAULT_ANOMALY_RULES

        # 滑动窗口：[ip][endpoint] -> deque[ts]
        self._events: Dict[str, Dict[str, Deque[float]]] = defaultdict(
            lambda: defaultdict(deque)
        )

        # 日累计：[ip][endpoint][date] -> int
        self._daily_counts: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(int))
        )

        # 风险评分：[ip] -> {score, last_updated}
        self._risk_scores: Dict[str, Dict[str, float]] = {}

        # 失败请求：[ip] -> deque[ts]
        self._failed_attempts: Dict[str, Deque[float]] = defaultdict(deque)

        # 封禁名单：[ip] -> expire_ts
        self._blocked_ips: Dict[str, float] = {}

        # 端点调用统计：[ip][anomaly_rule_name] -> deque[ts]
        self._anomaly_events: Dict[str, Dict[str, Deque[float]]] = defaultdict(
            lambda: defaultdict(deque)
        )

        self._lock = threading.RLock()
        logger.info(
            f"RiskControlService initialized "
            f"({len(self._endpoint_rules)} endpoint rules, "
            f"{len(self._anomaly_rules)} anomaly rules)"
        )

    # ---------- 公开 API ----------

    def check(
        self,
        ip: str,
        endpoint_key: str,  # "POST:/api/v1/invite/codes"
        user_id: Optional[int] = None,
    ) -> RiskCheckResult:
        """
        风控检查（在路由执行前调用）

        Args:
            ip: 客户端 IP（必填）
            endpoint_key: "METHOD:/path" 格式
            user_id: 可选，用于登录用户的复合 key

        Returns:
            RiskCheckResult - 包含是否允许 / 风险等级 / 评分 / 是否需要 CAPTCHA
        """
        with self._lock:
            now = time.time()

            # 1. 检查封禁名单
            block_expire = self._blocked_ips.get(ip)
            if block_expire is not None:
                if now < block_expire:
                    retry_after = int(block_expire - now)
                    return RiskCheckResult(
                        allowed=False,
                        risk_level=RiskLevel.BLOCKED,
                        score=100,
                        reason=f"IP 已被临时封禁 {retry_after}s",
                        retry_after_seconds=retry_after,
                    )
                else:
                    del self._blocked_ips[ip]

            # 2. 查找匹配的端点规则
            rule = self._match_endpoint_rule(endpoint_key)
            if rule is None:
                # 无规则限制（如 /health, /metrics），直接放行
                return RiskCheckResult(
                    allowed=True,
                    risk_level=RiskLevel.LOW,
                    score=0,
                )

            # 3. 滑动窗口限流
            allowed_remaining = self._check_sliding_window(ip, endpoint_key, rule, now)
            if allowed_remaining < 0:
                # 计算重试等待时间
                events = self._events[ip][endpoint_key]
                oldest = events[0] if events else now
                retry_after = int(oldest + rule.window_seconds - now)
                return RiskCheckResult(
                    allowed=False,
                    risk_level=RiskLevel.MEDIUM,
                    score=self._get_risk_score(ip),
                    reason=f"请求频率超限（{rule.max_requests}/{rule.window_seconds}s）",
                    retry_after_seconds=max(1, retry_after),
                    details={
                        "max_requests": rule.max_requests,
                        "window_seconds": rule.window_seconds,
                    },
                )

            # 4. 日累计检查
            today = time.strftime("%Y-%m-%d", time.localtime(now))
            daily_count = self._daily_counts[ip][endpoint_key][today]
            if daily_count >= rule.max_daily_requests:
                return RiskCheckResult(
                    allowed=False,
                    risk_level=RiskLevel.HIGH,
                    score=self._get_risk_score(ip),
                    reason=f"日累计超过上限（{rule.max_daily_requests}/day）",
                    retry_after_seconds=86400,
                    details={"daily_count": daily_count},
                )

            # 5. 检查异常行为模式（基于历史数据）
            anomalies = self._check_anomalies(ip, now)

            # 6. 累计当前请求到滑动窗口 + 日计数
            self._events[ip][endpoint_key].append(now)
            self._daily_counts[ip][endpoint_key][today] = daily_count + 1

            # 7. 计算风险评分
            base_score = self._get_risk_score(ip) + sum(a["score_delta"] for a in anomalies)

            # 8. 评估最终风险等级
            requires_captcha = (
                base_score >= rule.captcha_threshold or len(anomalies) > 0
            )

            if base_score >= rule.block_threshold:
                # 高风险：封禁 1 小时
                self._blocked_ips[ip] = now + 3600
                return RiskCheckResult(
                    allowed=False,
                    risk_level=RiskLevel.BLOCKED,
                    score=min(base_score, 100),
                    reason=f"触发异常模式：{', '.join(a['name'] for a in anomalies)}",
                    retry_after_seconds=3600,
                    details={"anomalies": [a["name"] for a in anomalies]},
                )

            risk_level = (
                RiskLevel.MEDIUM if requires_captcha else RiskLevel.LOW
            )

            return RiskCheckResult(
                allowed=True,
                risk_level=risk_level,
                score=base_score,
                requires_captcha=requires_captcha,
                details={
                    "remaining_window": allowed_remaining,
                    "daily_count": daily_count + 1,
                    "anomalies": [a["name"] for a in anomalies],
                },
            )

    def record_failure(self, ip: str, endpoint_key: str) -> None:
        """
        记录一次失败请求（4xx），用于异常检测

        调用时机：路由返回 4xx 响应时
        """
        with self._lock:
            now = time.time()
            self._failed_attempts[ip].append(now)
            self._add_risk_score(ip, delta=10, now=now)
            # 触发 consecutive_failures 异常
            self._anomaly_events[ip]["consecutive_failures"].append(now)

    def record_success(self, ip: str, endpoint_key: str) -> None:
        """
        记录一次成功请求，降低风险评分（成功就减分）
        """
        with self._lock:
            # 成功请求轻度降低风险评分
            self._add_risk_score(ip, delta=-2, now=time.time())

    def reset_ip(self, ip: str) -> None:
        """重置某个 IP 的所有风控状态（管理员操作）"""
        with self._lock:
            self._events.pop(ip, None)
            self._daily_counts.pop(ip, None)
            self._risk_scores.pop(ip, None)
            self._failed_attempts.pop(ip, None)
            self._blocked_ips.pop(ip, None)
            self._anomaly_events.pop(ip, None)
            logger.info(f"Reset risk control state for IP: {ip}")

    def get_stats(self) -> Dict:
        """获取风控统计（监控用）"""
        with self._lock:
            return {
                "tracked_ips": len(self._events),
                "blocked_ips": len(self._blocked_ips),
                "high_risk_ips": sum(
                    1 for s in self._risk_scores.values() if s["score"] >= 50
                ),
                "endpoint_rules": len(self._endpoint_rules),
                "anomaly_rules": len(self._anomaly_rules),
            }

    # ---------- 【P3 后台】管理类 API ----------

    def block_ip(
        self, ip: str, duration_seconds: int = 3600, reason: str = ""
    ) -> Dict:
        """
        管理员手动封禁 IP

        Returns:
            封禁详情 dict
        """
        with self._lock:
            now = time.time()
            expire = now + max(1, int(duration_seconds))
            self._blocked_ips[ip] = expire
            self._add_risk_score(ip, delta=100, now=now)
            logger.info(
                f"Admin block IP: {ip} for {duration_seconds}s, reason={reason}"
            )
            return {
                "ip": ip,
                "blocked_until": expire,
                "duration_seconds": duration_seconds,
                "reason": reason,
            }

    def unblock_ip(self, ip: str) -> bool:
        """管理员解封 IP"""
        with self._lock:
            existed = ip in self._blocked_ips
            self._blocked_ips.pop(ip, None)
            if existed:
                self._risk_scores.pop(ip, None)
                logger.info(f"Admin unblock IP: {ip}")
            return existed

    def list_blocked_ips(self) -> List[Dict]:
        """列出所有被封禁的 IP（自动清理已过期）"""
        with self._lock:
            now = time.time()
            live = []
            for ip, expire in list(self._blocked_ips.items()):
                if expire > now:
                    live.append(
                        {
                            "ip": ip,
                            "expires_at": expire,
                            "remaining_seconds": int(expire - now),
                        }
                    )
                else:
                    del self._blocked_ips[ip]
            return sorted(live, key=lambda x: x["expires_at"])

    def list_top_risks(self, limit: int = 20) -> List[Dict]:
        """按当前风险评分列出 Top-N IP"""
        with self._lock:
            entries = []
            now = time.time()
            for ip, info in self._risk_scores.items():
                score = max(0, int(info["score"]))
                if score <= 0:
                    continue
                entries.append(
                    {
                        "ip": ip,
                        "score": score,
                        "last_updated": info.get("last_updated", now),
                        "is_blocked": ip in self._blocked_ips,
                    }
                )
            entries.sort(key=lambda x: x["score"], reverse=True)
            return entries[: max(1, limit)]

    def get_ip_detail(self, ip: str) -> Dict:
        """查询指定 IP 的完整风控状态"""
        with self._lock:
            now = time.time()
            score = self._get_risk_score(ip)
            blocked_until = self._blocked_ips.get(ip)
            return {
                "ip": ip,
                "risk_score": score,
                "is_blocked": blocked_until is not None and blocked_until > now,
                "blocked_until": blocked_until,
                "active_endpoints": list(self._events.get(ip, {}).keys()),
                "daily_count": sum(
                    sum(d.values()) for d in self._daily_counts.get(ip, {}).values()
                ),
                "failed_attempts_1h": self._count_recent(
                    self._failed_attempts.get(ip), now, 3600
                ),
                "anomaly_history": {
                    name: len(events)
                    for name, events in self._anomaly_events.get(ip, {}).items()
                },
            }

    @staticmethod
    def _count_recent(
        events: Optional["Deque[float]"], now: float, window: int
    ) -> int:
        if events is None:
            return 0
        cutoff = now - window
        return sum(1 for ts in events if ts >= cutoff)

    def reset_all(self) -> int:
        """重置全部风控状态（管理员紧急操作）"""
        with self._lock:
            count = len(self._events)
            self._events.clear()
            self._daily_counts.clear()
            self._risk_scores.clear()
            self._failed_attempts.clear()
            self._blocked_ips.clear()
            self._anomaly_events.clear()
            logger.warning(f"Admin reset ALL risk control state ({count} IPs cleared)")
            return count

    def get_endpoint_rule_snapshot(self) -> List[Dict]:
        """导出当前所有端点风控规则"""
        return [
            {
                "method": r.method,
                "path_pattern": r.path_pattern,
                "max_requests": r.max_requests,
                "window_seconds": r.window_seconds,
                "max_daily_requests": r.max_daily_requests,
                "captcha_threshold": r.captcha_threshold,
                "block_threshold": r.block_threshold,
            }
            for r in self._endpoint_rules
        ]

    def get_anomaly_rule_snapshot(self) -> List[Dict]:
        """导出当前所有异常模式规则"""
        return [
            {
                "name": r.name,
                "description": r.description,
                "window_seconds": r.window_seconds,
                "threshold": r.threshold,
                "score_delta": r.score_delta,
            }
            for r in self._anomaly_rules
        ]

    def get_captcha_stats(self) -> Dict:
        """导出 CAPTCHA 验证统计（如有中间件计数器）"""
        with self._lock:
            return {
                "tracked_ips": len(self._events),
                "high_risk_ips": sum(
                    1 for s in self._risk_scores.values() if s["score"] >= 50
                ),
                "blocked_ips": len(self._blocked_ips),
                "endpoint_rules": len(self._endpoint_rules),
                "anomaly_rules": len(self._anomaly_rules),
            }

    # ---------- 内部方法 ----------

    def _match_endpoint_rule(self, endpoint_key: str) -> Optional[EndpointRule]:
        """根据 endpoint_key 查找规则（支持路径参数）"""
        try:
            method, path = endpoint_key.split(":", 1)
        except ValueError:
            return None

        for rule in self._endpoint_rules:
            if rule.method != method and rule.method != "*":
                continue
            # 简单模式匹配：支持 {param} 占位符
            if self._path_matches(rule.path_pattern, path):
                return rule
        return None

    @staticmethod
    def _path_matches(pattern: str, path: str) -> bool:
        """路径模式匹配：/api/v1/invite/codes/{code}/use 匹配 /api/v1/invite/codes/ABC123/use"""
        pattern_parts = pattern.split("/")
        path_parts = path.split("/")
        if len(pattern_parts) != len(path_parts):
            return False
        for p, actual in zip(pattern_parts, path_parts):
            if p.startswith("{") and p.endswith("}"):
                continue  # 参数占位符
            if p != actual:
                return False
        return True

    def _check_sliding_window(
        self,
        ip: str,
        endpoint_key: str,
        rule: EndpointRule,
        now: float,
    ) -> int:
        """
        检查滑动窗口，返回剩余允许数（-1 表示已超限）

        同时清理过期记录（避免内存泄漏）
        """
        events = self._events[ip][endpoint_key]
        cutoff = now - rule.window_seconds
        # 清理过期（左侧过期）
        while events and events[0] < cutoff:
            events.popleft()
        # 检查是否超过上限
        if len(events) >= rule.max_requests:
            return -1
        return rule.max_requests - len(events) - 1

    def _check_anomalies(self, ip: str, now: float) -> List[Dict]:
        """检查所有异常模式规则，返回触发的异常列表"""
        triggered = []
        events = self._anomaly_events[ip]
        for rule in self._anomaly_rules:
            rule_events = events.get(rule.name)
            if rule_events is None:
                continue
            # 清理过期
            cutoff = now - rule.window_seconds
            while rule_events and rule_events[0] < cutoff:
                rule_events.popleft()
            if len(rule_events) >= rule.threshold:
                triggered.append(
                    {
                        "name": rule.name,
                        "description": rule.description,
                        "score_delta": rule.score_delta,
                        "count": len(rule_events),
                    }
                )
        return triggered

    def _get_risk_score(self, ip: str) -> int:
        """获取 IP 当前风险评分（带时间衰减）"""
        info = self._risk_scores.get(ip)
        if info is None:
            return 0
        score = info["score"]
        # 时间衰减：每分钟 -1 分（最低 0）
        last = info.get("last_updated", time.time())
        decay = int((time.time() - last) / 60)
        return max(0, int(score) - decay)

    def _add_risk_score(self, ip: str, delta: int, now: Optional[float] = None) -> None:
        """增减 IP 风险评分"""
        now = now or time.time()
        info = self._risk_scores.setdefault(ip, {"score": 0.0, "last_updated": now})
        info["score"] = max(0, min(100, info["score"] + delta))
        info["last_updated"] = now


# ==================== 全局单例 ====================


_service: Optional[RiskControlService] = None
_service_lock = threading.Lock()


def get_risk_control_service() -> RiskControlService:
    """获取全局风控服务实例（单例）"""
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = RiskControlService()
    return _service


def reset_risk_control_service_for_testing() -> None:
    """重置全局风控服务（仅用于测试）"""
    global _service
    with _service_lock:
        _service = None


__all__ = [
    "RiskLevel",
    "RiskCheckResult",
    "EndpointRule",
    "AnomalyRule",
    "RiskControlService",
    "get_risk_control_service",
    "reset_risk_control_service_for_testing",
    "DEFAULT_ENDPOINT_RULES",
    "DEFAULT_ANOMALY_RULES",
]
