"""
游戏化API模块初始化
"""

from .difficulty_api import router as difficulty_router
from .rule_config_api import router as rule_config_router
from .task_adjustment_api import router as task_adjustment_router

__all__ = ["difficulty_router", "rule_config_router", "task_adjustment_router"]
