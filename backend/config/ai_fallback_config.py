"""
AI 功能降级开关配置
控制 AI 功能的 Token 计费行为
"""

import os
from typing import Dict, Set


class AIFallbackConfig:
    """AI 功能降级配置"""

    # 降级开关：True=启用计费，False=禁用计费（免费模式）
    BILLING_ENABLED = os.getenv("AI_BILLING_ENABLED", "true").lower() == "true"

    # 按功能类型的降级开关
    FEATURE_FALLBACK: Dict[str, bool] = {
        "ai_teacher": True,           # AI 教师对话
        "course_generation": True,    # 课程生成
        "recommendation": True,       # 智能推荐
        "image_generation": False,    # 图像生成（高级功能）
        "code_generation": True,      # 代码生成
    }

    # 免费额度（每日赠送）
    DAILY_FREE_TOKENS = {
        "ai_teacher": 50,             # 每日 50 tokens 免费对话
        "course_generation": 0,       # 课程生成无免费额度
        "recommendation": 100,        # 每日 100 tokens 免费推荐
    }

    # Token 不足时的降级策略
    FALLBACK_STRATEGIES = {
        "ai_teacher": "allow_with_warning",     # 允许但警告
        "course_generation": "block",           # 阻止
        "recommendation": "use_cache",          # 使用缓存结果
        "image_generation": "block",            # 阻止
        "code_generation": "allow_with_warning"  # 允许但警告
    }

    @classmethod
    def is_feature_enabled(cls, feature_type: str) -> bool:
        """检查功能是否启用"""
        if not cls.BILLING_ENABLED:
            return True
        return cls.FEATURE_FALLBACK.get(feature_type, False)

    @classmethod
    def get_fallback_strategy(cls, feature_type: str) -> str:
        """获取降级策略"""
        return cls.FALLBACK_STRATEGIES.get(feature_type, "block")

    @classmethod
    def get_daily_free_tokens(cls, feature_type: str) -> int:
        """获取每日免费 Token 额度"""
        return cls.DAILY_FREE_TOKENS.get(feature_type, 0)


# 全局配置实例
ai_fallback_config = AIFallbackConfig()
