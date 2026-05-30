"""
任务调整模型
定义任务难度动态调整的数据结构和规则
"""

from dataclasses import dataclass, field
from datetime import datetime
import enum
from typing import Any, Dict, List, Optional
import uuid


class AdjustmentReason(str, enum.Enum):
    """调整原因枚举"""

    SUCCESS_STREAK = "success_streak"  # 连续成功
    FAILURE_STREAK = "failure_streak"  # 连续失败
    TIME_EFFICIENCY = "time_efficiency"  # 时间效率
    SKILL_IMPROVEMENT = "skill_improvement"  # 技能提升
    MANUAL_OVERRIDE = "manual_override"  # 手动调整
    SYSTEM_RECOMMENDATION = "system_recommendation"  # 系统推荐


class AdjustmentType(str, enum.Enum):
    """调整类型枚举"""

    INCREASE_DIFFICULTY = "increase_difficulty"  # 增加难度
    DECREASE_DIFFICULTY = "decrease_difficulty"  # 降低难度
    MAINTAIN_CURRENT = "maintain_current"  # 维持当前难度


@dataclass
class TaskAdjustmentRule:
    """任务调整规则"""

    rule_id: str
    name: str
    description: str
    condition_type: str  # 条件类型
    threshold: int  # 阈值
    adjustment_type: AdjustmentType
    adjustment_value: float  # 调整数值
    cooldown_period: int  # 冷却期(秒)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "condition_type": self.condition_type,
            "threshold": self.threshold,
            "adjustment_type": self.adjustment_type.value,
            "adjustment_value": self.adjustment_value,
            "cooldown_period": self.cooldown_period,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class UserTaskHistory:
    """用户任务历史记录"""

    user_id: str
    task_id: str
    difficulty_level: str
    success: bool
    completion_time: float  # 完成时间(分钟)
    hint_used: bool
    retry_count: int
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "user_id": self.user_id,
            "task_id": self.task_id,
            "difficulty_level": self.difficulty_level,
            "success": self.success,
            "completion_time": self.completion_time,
            "hint_used": self.hint_used,
            "retry_count": self.retry_count,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DifficultyAdjustment:
    """难度调整记录"""

    adjustment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    task_id: str = ""
    current_difficulty: float = 0.0
    adjusted_difficulty: float = 0.0
    adjustment_reason: AdjustmentReason = AdjustmentReason.SYSTEM_RECOMMENDATION
    adjustment_type: AdjustmentType = AdjustmentType.MAINTAIN_CURRENT
    confidence_score: float = 0.0  # 置信度分数(0-1)
    triggered_rules: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "adjustment_id": self.adjustment_id,
            "user_id": self.user_id,
            "task_id": self.task_id,
            "current_difficulty": self.current_difficulty,
            "adjusted_difficulty": self.adjusted_difficulty,
            "adjustment_reason": self.adjustment_reason.value,
            "adjustment_type": self.adjustment_type.value,
            "confidence_score": self.confidence_score,
            "triggered_rules": self.triggered_rules,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class StreakCounter:
    """连胜/连败计数器"""

    user_id: str
    success_streak: int = 0  # 连续成功次数
    failure_streak: int = 0  # 连续失败次数
    last_activity_time: datetime = field(default_factory=datetime.now)

    def record_success(self) -> bool:
        """记录成功，返回是否触发调整"""
        self.success_streak += 1
        self.failure_streak = 0
        self.last_activity_time = datetime.now()
        return self.success_streak >= 3  # 连续3次成功触发调整

    def record_failure(self) -> bool:
        """记录失败，返回是否触发调整"""
        self.failure_streak += 1
        self.success_streak = 0
        self.last_activity_time = datetime.now()
        return self.failure_streak >= 2  # 连续2次失败触发调整

    def reset_counters(self):
        """重置计数器"""
        self.success_streak = 0
        self.failure_streak = 0
        self.last_activity_time = datetime.now()


@dataclass
class UserDifficultyProfile:
    """用户难度档案"""

    user_id: str
    current_difficulty_level: float = 5.0  # 当前难度等级(1-10)
    last_adjustment_time: datetime = field(default_factory=datetime.now)
    adjustment_history: List[DifficultyAdjustment] = field(default_factory=list)
    streak_counter: StreakCounter = field(init=False)
    task_history: List[UserTaskHistory] = field(default_factory=list)

    def __post_init__(self):
        self.streak_counter = StreakCounter(user_id=self.user_id)

    def add_task_history(self, history: UserTaskHistory):
        """添加任务历史记录"""
        self.task_history.append(history)
        # 保持历史记录在合理范围内
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]

    def add_adjustment(self, adjustment: DifficultyAdjustment):
        """添加调整记录"""
        self.adjustment_history.append(adjustment)
        self.last_adjustment_time = datetime.now()
        # 保持调整记录在合理范围内
        if len(self.adjustment_history) > 50:
            self.adjustment_history = self.adjustment_history[-50:]

    def get_recent_success_rate(self, window_size: int = 10) -> float:
        """获取近期成功率"""
        if not self.task_history:
            return 0.0

        recent_tasks = self.task_history[-window_size:]
        successful_tasks = sum(1 for task in recent_tasks if task.success)
        return successful_tasks / len(recent_tasks)

    def get_average_completion_time(self, window_size: int = 10) -> float:
        """获取平均完成时间"""
        if not self.task_history:
            return 0.0

        recent_tasks = self.task_history[-window_size:]
        total_time = sum(task.completion_time for task in recent_tasks)
        return total_time / len(recent_tasks) if recent_tasks else 0.0


# 默认调整规则配置
DEFAULT_ADJUSTMENT_RULES = [
    TaskAdjustmentRule(
        rule_id="success_streak_increase",
        name="连续成功提升难度",
        description="用户连续3次成功完成任务时提升难度",
        condition_type="success_streak",
        threshold=3,
        adjustment_type=AdjustmentType.INCREASE_DIFFICULTY,
        adjustment_value=0.5,
        cooldown_period=3600,  # 1小时冷却期
    ),
    TaskAdjustmentRule(
        rule_id="failure_streak_decrease",
        name="连续失败降低难度",
        description="用户连续2次失败时降低难度",
        condition_type="failure_streak",
        threshold=2,
        adjustment_type=AdjustmentType.DECREASE_DIFFICULTY,
        adjustment_value=0.5,
        cooldown_period=1800,  # 30分钟冷却期
    ),
    TaskAdjustmentRule(
        rule_id="high_efficiency_increase",
        name="高效率提升难度",
        description="用户在短时间内高质量完成任务时提升难度",
        condition_type="time_efficiency",
        threshold=80,  # 80%效率阈值
        adjustment_type=AdjustmentType.INCREASE_DIFFICULTY,
        adjustment_value=0.3,
        cooldown_period=7200,  # 2小时冷却期
    ),
]

# 测试代码
if __name__ == "__main__":
    # 测试难度调整记录
    adjustment = DifficultyAdjustment(
        user_id="test_user_001",
        task_id="task_001",
        current_difficulty=5.0,
        adjusted_difficulty=5.5,
        adjustment_reason=AdjustmentReason.SUCCESS_STREAK,
        adjustment_type=AdjustmentType.INCREASE_DIFFICULTY,
        confidence_score=0.85,
        triggered_rules=["success_streak_increase"],
    )

    print("=== 难度调整记录测试 ===")
    print(f"调整ID: {adjustment.adjustment_id}")
    print(f"用户ID: {adjustment.user_id}")
    print(f"调整原因: {adjustment.adjustment_reason.value}")
    print(f"调整类型: {adjustment.adjustment_type.value}")
    print(f"置信度: {adjustment.confidence_score}")

    # 测试用户难度档案
    profile = UserDifficultyProfile(user_id="test_user_001")

    # 添加任务历史
    history = UserTaskHistory(
        user_id="test_user_001",
        task_id="task_001",
        difficulty_level="L3",
        success=True,
        completion_time=25.0,
        hint_used=False,
        retry_count=0,
    )
    profile.add_task_history(history)

    print(f"\n=== 用户档案测试 ===")
    print(f"近期成功率: {profile.get_recent_success_rate():.2f}")
    print(f"平均完成时间: {profile.get_average_completion_time():.2f}")

    # 测试连胜计数器
    print(f"\n=== 连胜计数器测试 ===")
    for i in range(4):
        triggered = profile.streak_counter.record_success()
        print(
            f"第{i+1}次成功: 连胜数={profile.streak_counter.success_streak}, 触发调整={triggered}"
        )

    # 测试失败重置
    profile.streak_counter.record_failure()
    print(
        f"失败后: 连胜数={profile.streak_counter.success_streak}, 连败数={profile.streak_counter.failure_streak}"
    )
