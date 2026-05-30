from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DecayType(Enum):
    """衰减类型"""

    LINEAR = "linear"  # 线性衰减
    EXPONENTIAL = "exponential"  # 指数衰减
    LOGARITHMIC = "logarithmic"  # 对数衰减
    STEP = "step"  # 阶梯式衰减


@dataclass
class DecayRule:
    """衰减规则"""

    rule_id: str
    name: str
    decay_type: DecayType
    decay_rate: float  # 衰减率 (0.0 - 1.0)
    grace_period_days: int  # 宽限天数
    min_threshold: int  # 最小阈值
    max_daily_decay: int  # 每日最大衰减量
    active_hours: List[int]  # 活跃时间段 [0-23]
    is_active: bool


@dataclass
class UserDecayProfile:
    """用户衰减档案"""

    user_id: int
    last_activity_date: datetime
    current_points: int
    decayed_points: int
    decay_history: List[Dict[str, Any]]
    exemption_until: Optional[datetime]  # 免疫期截止时间


class IntegralDecayCalculator:
    """积分衰减计算器"""

    def __init__(self):
        self.decay_rules: Dict[str, DecayRule] = {}
        self.user_profiles: Dict[int, UserDecayProfile] = {}
        self._initialize_default_rules()

    def _initialize_default_rules(self):
        """初始化默认衰减规则"""
        # 普通用户衰减规则
        self.decay_rules["standard"] = DecayRule(
            rule_id="standard",
            name="标准衰减规则",
            decay_type=DecayType.EXPONENTIAL,
            decay_rate=0.02,  # 每日2%衰减
            grace_period_days=7,
            min_threshold=100,
            max_daily_decay=50,
            active_hours=list(range(8, 22)),  # 8:00-22:00活跃
            is_active=True,
        )

        # VIP用户衰减规则
        self.decay_rules["vip"] = DecayRule(
            rule_id="vip",
            name="VIP用户衰减规则",
            decay_type=DecayType.LINEAR,
            decay_rate=0.01,  # 每日1%衰减
            grace_period_days=14,
            min_threshold=200,
            max_daily_decay=30,
            active_hours=list(range(6, 24)),  # 6:00-24:00活跃
            is_active=True,
        )

        # 新手保护规则
        self.decay_rules["beginner"] = DecayRule(
            rule_id="beginner",
            name="新手保护规则",
            decay_type=DecayType.STEP,
            decay_rate=0.0,  # 不衰减
            grace_period_days=30,
            min_threshold=50,
            max_daily_decay=0,
            active_hours=list(range(24)),  # 全天候
            is_active=True,
        )

    def calculate_daily_decay(
        self,
        user_id: int,
        current_points: int,
        user_level: str = "standard",
        today: Optional[datetime] = None,
    ) -> int:
        """计算每日衰减积分"""
        if today is None:
            today = datetime.now()

        # 获取用户档案
        profile = self._get_or_create_profile(user_id, current_points, today)

        # 获取适用的衰减规则
        rule = self._get_applicable_rule(user_level)
        if not rule or not rule.is_active:
            return 0

        # 检查宽限期
        days_since_activity = (today.date() - profile.last_activity_date.date()).days
        if days_since_activity < rule.grace_period_days:
            return 0

        # 检查免疫期
        if profile.exemption_until and today <= profile.exemption_until:
            return 0

        # 检查活跃时间
        if today.hour not in rule.active_hours:
            return 0

        # 计算基础衰减量
        base_decay = self._calculate_base_decay(
            rule, current_points, days_since_activity
        )

        # 应用最小阈值限制
        max_decay = max(0, current_points - rule.min_threshold)
        actual_decay = min(base_decay, max_decay, rule.max_daily_decay)

        # 记录衰减历史
        self._record_decay_history(profile, today, actual_decay, rule.rule_id)

        logger.debug(f"用户{user_id}今日衰减: {actual_decay}积分 (规则: {rule.name})")

        return actual_decay

    def _get_or_create_profile(
        self, user_id: int, current_points: int, today: datetime
    ) -> UserDecayProfile:
        """获取或创建用户档案"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserDecayProfile(
                user_id=user_id,
                last_activity_date=today,
                current_points=current_points,
                decayed_points=0,
                decay_history=[],
                exemption_until=None,
            )
        else:
            # 更新当前积分
            self.user_profiles[user_id].current_points = current_points

        return self.user_profiles[user_id]

    def _get_applicable_rule(self, user_level: str) -> Optional[DecayRule]:
        """获取适用的衰减规则"""
        # 优先级: beginner > vip > standard
        priority_order = ["beginner", "vip", "standard"]

        for rule_key in priority_order:
            if rule_key in self.decay_rules:
                rule = self.decay_rules[rule_key]
                # 根据用户等级匹配规则
                if (
                    (rule_key == "beginner" and user_level == "beginner")
                    or (rule_key == "vip" and user_level == "vip")
                    or (rule_key == "standard")
                ):
                    return rule

        return self.decay_rules.get("standard")

    def _calculate_base_decay(
        self, rule: DecayRule, points: int, days_inactive: int
    ) -> int:
        """计算基础衰减量"""
        if rule.decay_type == DecayType.LINEAR:
            return int(points * rule.decay_rate)

        elif rule.decay_type == DecayType.EXPONENTIAL:
            # 指数衰减: points * (1 - rate)^days
            decay_factor = math.pow(1 - rule.decay_rate, days_inactive)
            decay_amount = points * (1 - decay_factor)
            return int(decay_amount)

        elif rule.decay_type == DecayType.LOGARITHMIC:
            # 对数衰减: 更温和的长期衰减
            if days_inactive <= 1:
                return int(points * rule.decay_rate)
            decay_factor = math.log(days_inactive + 1) / (days_inactive + 1)
            return int(points * decay_factor * rule.decay_rate)

        elif rule.decay_type == DecayType.STEP:
            # 阶梯式衰减: 达到一定天数后开始衰减
            if days_inactive <= rule.grace_period_days:
                return 0
            step_days = days_inactive - rule.grace_period_days
            steps = step_days // 3  # 每3天一个阶梯
            return int(points * rule.decay_rate * steps)

        return 0

    def _record_decay_history(
        self, profile: UserDecayProfile, date: datetime, decay_amount: int, rule_id: str
    ):
        """记录衰减历史"""
        history_entry = {
            "date": date.date().isoformat(),
            "decay_amount": decay_amount,
            "remaining_points": profile.current_points - decay_amount,
            "rule_id": rule_id,
            "timestamp": datetime.now().isoformat(),
        }

        profile.decay_history.append(history_entry)
        profile.decayed_points += decay_amount

        # 保持历史记录在合理范围内
        if len(profile.decay_history) > 365:  # 最多保留一年记录
            profile.decay_history = profile.decay_history[-365:]

    def update_user_activity(
        self, user_id: int, activity_date: Optional[datetime] = None
    ):
        """更新用户活动日期"""
        if activity_date is None:
            activity_date = datetime.now()

        if user_id in self.user_profiles:
            self.user_profiles[user_id].last_activity_date = activity_date
            logger.debug(f"用户{user_id}活动日期已更新至: {activity_date.date()}")

    def grant_exemption(self, user_id: int, days: int):
        """授予用户免疫期"""
        exemption_end = datetime.now() + timedelta(days=days)

        if user_id in self.user_profiles:
            self.user_profiles[user_id].exemption_until = exemption_end
        else:
            # 创建临时档案
            self.user_profiles[user_id] = UserDecayProfile(
                user_id=user_id,
                last_activity_date=datetime.now(),
                current_points=0,
                decayed_points=0,
                decay_history=[],
                exemption_until=exemption_end,
            )

        logger.info(f"用户{user_id}获得{days}天免疫期，截止: {exemption_end.date()}")

    def get_decay_projection(
        self, user_id: int, days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """获取衰减预测"""
        if user_id not in self.user_profiles:
            return []

        profile = self.user_profiles[user_id]
        projections = []
        current_points = profile.current_points

        for day in range(1, days_ahead + 1):
            future_date = datetime.now() + timedelta(days=day)
            projected_decay = self.calculate_daily_decay(
                user_id, current_points, "standard", future_date
            )

            current_points = max(0, current_points - projected_decay)

            projections.append(
                {
                    "date": future_date.date().isoformat(),
                    "projected_points": current_points,
                    "daily_decay": projected_decay,
                    "cumulative_decay": profile.current_points - current_points,
                }
            )

        return projections

    def get_user_decay_summary(self, user_id: int) -> Dict[str, Any]:
        """获取用户衰减摘要"""
        if user_id not in self.user_profiles:
            return {"error": "用户档案不存在"}

        profile = self.user_profiles[user_id]
        days_inactive = (datetime.now().date() - profile.last_activity_date.date()).days

        return {
            "user_id": user_id,
            "current_points": profile.current_points,
            "decayed_points": profile.decayed_points,
            "days_since_last_activity": days_inactive,
            "total_decay_events": len(profile.decay_history),
            "average_daily_decay": profile.decayed_points
            / max(1, len(profile.decay_history)),
            "exemption_active": profile.exemption_until
            and datetime.now() <= profile.exemption_until,
            "exemption_until": (
                profile.exemption_until.isoformat() if profile.exemption_until else None
            ),
            "recent_decay_history": (
                profile.decay_history[-10:] if profile.decay_history else []
            ),
        }

    def bulk_calculate_decay(
        self, user_points: Dict[int, int], user_levels: Dict[int, str]
    ) -> Dict[int, int]:
        """批量计算衰减"""
        decay_results = {}
        today = datetime.now()

        for user_id, points in user_points.items():
            user_level = user_levels.get(user_id, "standard")
            decay_amount = self.calculate_daily_decay(
                user_id, points, user_level, today
            )
            decay_results[user_id] = decay_amount

        return decay_results

    def add_custom_rule(self, rule: DecayRule) -> bool:
        """添加自定义衰减规则"""
        if rule.rule_id in self.decay_rules:
            return False

        self.decay_rules[rule.rule_id] = rule
        logger.info(f"添加自定义衰减规则: {rule.name}")
        return True

    def disable_rule(self, rule_id: str) -> bool:
        """禁用衰减规则"""
        if rule_id in self.decay_rules:
            self.decay_rules[rule_id].is_active = False
            logger.info(f"衰减规则已禁用: {rule_id}")
            return True
        return False

    def get_all_rules(self) -> List[Dict[str, Any]]:
        """获取所有衰减规则"""
        return [
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "decay_type": rule.decay_type.value,
                "decay_rate": rule.decay_rate,
                "grace_period_days": rule.grace_period_days,
                "min_threshold": rule.min_threshold,
                "max_daily_decay": rule.max_daily_decay,
                "active_hours": rule.active_hours,
                "is_active": rule.is_active,
            }
            for rule in self.decay_rules.values()
        ]


# 全局实例
decay_calculator = IntegralDecayCalculator()
