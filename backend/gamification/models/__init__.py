"""
游戏化模型模块初始化
"""

from .difficulty_level import (
    DebuggingSession,
    DifficultyCalculator,
    DifficultyLevel,
    HardwareOperationMetric,
    TaskPerformanceMetrics,
)
from .rule_engine import (
    PREDEFINED_RULE_TEMPLATES,
    GamificationRule,
    RuleAction,
    RuleActionType,
    RuleCondition,
    RuleConditionType,
    RuleEngineConfig,
    RuleExecutionContext,
    RuleOperator,
)
from .task_adjustment import (
    DEFAULT_ADJUSTMENT_RULES,
    AdjustmentReason,
    AdjustmentType,
    DifficultyAdjustment,
    StreakCounter,
    TaskAdjustmentRule,
    UserDifficultyProfile,
    UserTaskHistory,
)

__all__ = [
    # 难度等级相关
    "DifficultyLevel",
    "HardwareOperationMetric",
    "DebuggingSession",
    "TaskPerformanceMetrics",
    "DifficultyCalculator",
    # 任务调整相关
    "AdjustmentReason",
    "AdjustmentType",
    "TaskAdjustmentRule",
    "UserTaskHistory",
    "DifficultyAdjustment",
    "StreakCounter",
    "UserDifficultyProfile",
    "DEFAULT_ADJUSTMENT_RULES",
    # 规则引擎相关
    "RuleConditionType",
    "RuleOperator",
    "RuleActionType",
    "RuleCondition",
    "RuleAction",
    "GamificationRule",
    "RuleExecutionContext",
    "RuleEngineConfig",
    "PREDEFINED_RULE_TEMPLATES",
]
