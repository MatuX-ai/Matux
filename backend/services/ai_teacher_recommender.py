"""
【P3-B】AI 教师实时推荐引擎

入口：`recommend(trigger_type, user_id, payload)`
- recommend_for_node_status: 节点状态变更 → celebration / suggestion
- recommend_for_achievement: 成就解锁 → celebration
- recommend_for_set_completed: 套装完成 → celebration
- recommend_for_nudge: 主动 nudge 信号 → nudge

每个方法返回 List[AiTeacherLiveEvent]（可能为空，表示当前无需推送）。
所有推荐都生成 `cooldownKey` 用于频控。
"""

import logging
from typing import Any, Dict, List, Optional

from services.ai_teacher_event_bus import (
    make_celebration_payload,
    make_nudge_payload,
    make_suggestion_payload,
)
from services.ai_teacher_text_generator import (
    celebration_text,
    nudge_text,
    suggestion_text,
)

logger = logging.getLogger(__name__)


# ==================== 默认 persona ====================

DEFAULT_PERSONA = {
    "address_mode": "name",
    "nickname": "",
    "language_style": "lively",
    "hint_level": "guided_thinking",
    "encouragement_frequency": "moderate",
    "strictness": "standard",
    "emoji_usage": "moderate",
}


# ==================== Trigger 数据类 ====================


class NodeStatusUpdatedEvent:
    """节点状态更新事件（来自 gameification_event_bus）"""

    def __init__(self, payload: Dict[str, Any]):
        self.skill_id = payload.get("skill_id", "")
        self.old_status = payload.get("old_status", "")
        self.new_status = payload.get("new_status", "")
        self.progress = payload.get("progress", 0.0)
        self.related_achievement_ids = payload.get("related_achievement_ids", [])
        self.timestamp = payload.get("timestamp")


class AchievementUnlockedEvent:
    """成就解锁事件"""

    def __init__(self, payload: Dict[str, Any]):
        self.achievement_id = payload.get("achievement_id")
        self.name = payload.get("name", "")
        self.rarity = payload.get("rarity", "common")
        self.points = payload.get("points", 0)
        self.related_skill_ids = payload.get("related_skill_ids", [])
        self.icon = payload.get("icon")
        self.description = payload.get("description")
        self.unlocked_at = payload.get("unlocked_at")


class SetCompletedEvent:
    """套装完成事件"""

    def __init__(self, payload: Dict[str, Any]):
        self.set_id = payload.get("set_id", "")
        self.set_name = payload.get("set_name", "")
        self.bonus_reward = payload.get("bonus_reward")


class NudgeSignal:
    """调度器产生的 nudge 信号"""

    def __init__(
        self,
        nudge_type: str,
        days_idle: Optional[int] = None,
        skill_name: Optional[str] = None,
    ):
        self.nudge_type = nudge_type
        self.days_idle = days_idle
        self.skill_name = skill_name


# ==================== 推荐器 ====================


class AITeacherRecommender:
    """
    推荐引擎：根据触发事件生成 AI 教师实时事件

    所有方法都返回 List[Dict]，调用方负责 publish + 频控。
    """

    # 触发节点状态更改成 celebration 的状态
    CELEBRATION_STATUSES = {"mastered"}
    # 触发 suggestion（高原期）的阈值：开始 ≤7 天且进度 <30%
    PLATEAU_DAYS_THRESHOLD = 7
    PLATEAU_PROGRESS_THRESHOLD = 0.3

    def __init__(self):
        # 节点名映射（mock，可后续从 DB 读取）
        self._skill_name_map = {
            "python_basics": "Python 基础",
            "conditions": "条件判断",
            "loops": "循环",
            "functions": "函数",
            "oop": "面向对象",
            "led_control": "LED 控制",
            "sensors": "传感器入门",
            "robotics": "机器人编程",
            "blockly_basics": "Blockly 入门",
        }
        self._achievement_name_map: Dict[Any, str] = {}

    def _skill_name(self, skill_id: str) -> str:
        return self._skill_name_map.get(skill_id, skill_id)

    # ========== 节点状态更新 ==========

    async def recommend_for_node_status(
        self, user_id: int, event: NodeStatusUpdatedEvent
    ) -> List[Dict[str, Any]]:
        """节点状态更新 → 可能 celebration / suggestion"""
        results: List[Dict[str, Any]] = []
        skill_name = self._skill_name(event.skill_id)

        # 1. mastered → celebration
        if event.new_status in self.CELEBRATION_STATUSES:
            text = celebration_text(
                DEFAULT_PERSONA,
                title=skill_name,
                description=f"你成功掌握了「{skill_name}」的 {progress_str(event.progress)} 进度！",
            )
            payload = make_celebration_payload(
                user_id=user_id,
                title=text["title"],
                message=text["message"],
                emoji="🎉",
                related_id=event.skill_id,
                related_kind="node",
                cta_label="查看下一个节点",
                cta_route=f"/learning-map/node/{event.skill_id}",
            )
            results.append(payload)

        # 2. in_progress 持续 7 天 + 进度<30% → suggestion（高原期）
        # 注：实际持续天数需要平台数据。这里按"入参 days_in_status"判定。
        elif event.new_status == "in_progress":
            days_in_status = (event.payload_days if hasattr(event, "payload_days") else 0) \
                if isinstance(getattr(event, "payload", None), int) else 0
            # 简化为：progress < 30% 即视为潜在高原（实际天数需扩展 data 来源）
            if event.progress < self.PLATEAU_PROGRESS_THRESHOLD:
                text = suggestion_text(
                    DEFAULT_PERSONA,
                    diagnosis_type="learning_plateau",
                    description=f"「{skill_name}」的进度似乎有些停滞（{progress_str(event.progress)}）。",
                    action="换个 Blockly 任务或休息一下，再来挑战。",
                )
                payload = make_suggestion_payload(
                    user_id=user_id,
                    diagnosis_type="learning_plateau",
                    severity=text["severity"],
                    title=text["title"],
                    message=text["message"],
                    related_skill_id=event.skill_id,
                    recommended_courses=[f"review_{event.skill_id}"],
                    cta_label="查看复习内容",
                    cta_route=f"/learning-map/node/{event.skill_id}",
                )
                results.append(payload)

        return results

    # ========== 成就解锁 ==========

    async def recommend_for_achievement(
        self, user_id: int, event: AchievementUnlockedEvent
    ) -> List[Dict[str, Any]]:
        """成就解锁 → celebration（必发）+ 下一挑战建议"""
        results: List[Dict[str, Any]] = []

        rarity_emoji = {
            "common": "🥉",
            "rare": "🥈",
            "epic": "🥇",
            "legendary": "🏆",
        }.get(event.rarity, "🎖️")

        text = celebration_text(
            DEFAULT_PERSONA,
            title=event.name or "成就解锁",
            description=f"稀有度：{event.rarity} · 积分 +{event.points}",
            emoji_hint=rarity_emoji,
        )

        payload = make_celebration_payload(
            user_id=user_id,
            title=text["title"],
            message=text["message"],
            emoji=rarity_emoji,
            related_id=str(event.achievement_id) if event.achievement_id is not None else None,
            related_kind="achievement",
            cta_label="查看成就墙",
            cta_route="/achievements",
        )
        results.append(payload)

        # 附加建议：下一挑战
        if event.related_skill_ids:
            skill_id = event.related_skill_ids[0]
            skill_name = self._skill_name(skill_id)
            sug_text = suggestion_text(
                DEFAULT_PERSONA,
                diagnosis_type="prerequisite_missing",
                description=f"你刚解锁了「{event.name}」，下一步可以挑战「{skill_name}」。",
                action=f"继续深入学习「{skill_name}」的相关项目。",
            )
            sug_payload = make_suggestion_payload(
                user_id=user_id,
                diagnosis_type="prerequisite_missing",
                severity="info",
                title=sug_text["title"],
                message=sug_text["message"],
                related_skill_id=skill_id,
                recommended_courses=[skill_id],
                cta_label="开始挑战",
                cta_route=f"/learning-map/node/{skill_id}",
            )
            results.append(sug_payload)

        return results

    # ========== 套装完成 ==========

    async def recommend_for_set_completed(
        self, user_id: int, event: SetCompletedEvent
    ) -> List[Dict[str, Any]]:
        """套装完成 → celebration（强提示）"""
        results: List[Dict[str, Any]] = []
        text = celebration_text(
            DEFAULT_PERSONA,
            title=event.set_name,
            description="恭喜完成整套学习！你的坚持让 AI 老师也很自豪。",
            emoji_hint="🏆",
        )
        payload = make_celebration_payload(
            user_id=user_id,
            title=text["title"],
            message=text["message"],
            emoji="🏆",
            related_id=event.set_id,
            related_kind="set",
            cta_label="查看套装详情",
            cta_route=f"/learning-map/set/{event.set_id}",
        )
        results.append(payload)
        return results

    # ========== 主动 nudge ==========

    async def recommend_for_nudge(
        self, user_id: int, signal: NudgeSignal
    ) -> List[Dict[str, Any]]:
        """调度器触发 nudge（comeback / miss_you / take_break / try_new）"""
        text = nudge_text(
            DEFAULT_PERSONA,
            nudge_type=signal.nudge_type,
            days_idle=signal.days_idle,
            skill_name=signal.skill_name,
        )
        payload = make_nudge_payload(
            user_id=user_id,
            nudge_type=signal.nudge_type,
            title=text["title"],
            message=text["message"],
            suggested_skill_id=None,
            cta_label="去学习" if signal.nudge_type in ("comeback", "miss_you", "try_new") else "休息",
            cta_route="/learning-map" if signal.nudge_type in ("comeback", "miss_you", "try_new") else None,
        )
        return [payload]


def progress_str(progress: float) -> str:
    """进度百分比字符串"""
    return f"{int(progress * 100)}%"


# 全局单例
ai_teacher_recommender = AITeacherRecommender()