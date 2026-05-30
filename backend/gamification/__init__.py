"""
游戏化规则引擎模块
实现动态任务难度调节和自适应推荐基础框架
"""

__version__ = "1.0.0"
__author__ = "iMato Team"

from .engines.difficulty_engine import DifficultyEngine
from .engines.rule_evaluation_engine import RuleEvaluationEngine

# 模块导出
from .models.difficulty_level import DifficultyLevel, TaskPerformanceMetrics
from .services.difficulty_service import DifficultyService
from .services.rule_engine_service import RuleEngineService

__all__ = [
    "DifficultyLevel",
    "TaskDifficulty",
    "DifficultyService",
    "RuleEngineService",
    "DifficultyEngine",
    "RuleEvaluationEngine",
]
