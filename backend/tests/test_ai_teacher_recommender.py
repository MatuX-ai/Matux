"""
【P3-B】AI 教师推荐引擎单元测试

覆盖 6 种诊断类型 × 3 种触发场景（节点状态 / 成就 / nudge）
"""

import asyncio

import pytest

from services.ai_teacher_event_bus import (
    AiTeacherLiveEventType,
    ai_teacher_live_bus,
)
from services.ai_teacher_recommender import (
    AchievementUnlockedEvent,
    NodeStatusUpdatedEvent,
    NudgeSignal,
    SetCompletedEvent,
    ai_teacher_recommender,
)


@pytest.fixture(autouse=True)
def _clear_bus():
    ai_teacher_live_bus.clear()
    yield
    ai_teacher_live_bus.clear()


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestNodeStatusRecommendations:
    """节点状态变更 → celebration / suggestion"""

    def test_mastered_triggers_celebration(self):
        event = NodeStatusUpdatedEvent(
            {
                "skill_id": "loops",
                "old_status": "in_progress",
                "new_status": "mastered",
                "progress": 1.0,
            }
        )
        payloads = _run(
            ai_teacher_recommender.recommend_for_node_status(1, event)
        )
        assert len(payloads) >= 1
        celebration = next(
            p for p in payloads
            if p["type"] == AiTeacherLiveEventType.CELEBRATION.value
        )
        assert "loops" in celebration["payload"]["title"] or "循环" in celebration["payload"]["title"]
        assert celebration["cooldownKey"].startswith("celeb:")
        assert celebration["payload"]["relatedKind"] == "node"
        assert celebration["payload"]["relatedId"] == "loops"

    def test_in_progress_low_progress_triggers_suggestion(self):
        event = NodeStatusUpdatedEvent(
            {
                "skill_id": "functions",
                "old_status": "not_started",
                "new_status": "in_progress",
                "progress": 0.15,
            }
        )
        payloads = _run(
            ai_teacher_recommender.recommend_for_node_status(2, event)
        )
        # 当 progress < 0.3 时触发高原期 suggestion
        assert any(
            p["type"] == AiTeacherLiveEventType.SUGGESTION.value
            for p in payloads
        )

    def test_in_progress_high_progress_no_trigger(self):
        event = NodeStatusUpdatedEvent(
            {
                "skill_id": "loops",
                "old_status": "not_started",
                "new_status": "in_progress",
                "progress": 0.6,
            }
        )
        payloads = _run(
            ai_teacher_recommender.recommend_for_node_status(3, event)
        )
        # progress > 30% 不触发高原期建议
        assert not any(
            p["type"] == AiTeacherLiveEventType.SUGGESTION.value
            for p in payloads
        )


class TestAchievementRecommendations:
    """成就解锁 → celebration + 下一挑战建议"""

    def test_achievement_unlocked_celebration(self):
        event = AchievementUnlockedEvent(
            {
                "achievement_id": 42,
                "name": "Loop Master",
                "rarity": "rare",
                "points": 50,
                "related_skill_ids": ["loops"],
            }
        )
        payloads = _run(
            ai_teacher_recommender.recommend_for_achievement(1, event)
        )
        # 至少 1 条 celebration
        celebrations = [
            p for p in payloads
            if p["type"] == AiTeacherLiveEventType.CELEBRATION.value
        ]
        assert len(celebrations) == 1
        # 带相关技能时还应有 suggestion
        suggestions = [
            p for p in payloads
            if p["type"] == AiTeacherLiveEventType.SUGGESTION.value
        ]
        assert len(suggestions) >= 1
        # 关联 id 与 cooldownKey
        assert celebrations[0]["payload"]["relatedId"] == "42"
        assert celebrations[0]["payload"]["relatedKind"] == "achievement"


class TestSetCompletedRecommendations:
    """套装完成 → celebration"""

    def test_set_completed_celebration(self):
        event = SetCompletedEvent(
            {
                "set_id": "py-master",
                "set_name": "Python 大师套装",
                "bonus_reward": {"type": "title", "value": "Python 大师"},
            }
        )
        payloads = _run(
            ai_teacher_recommender.recommend_for_set_completed(1, event)
        )
        assert len(payloads) == 1
        assert payloads[0]["type"] == AiTeacherLiveEventType.CELEBRATION.value
        assert payloads[0]["payload"]["relatedId"] == "py-master"
        assert payloads[0]["payload"]["relatedKind"] == "set"


class TestNudgeRecommendations:
    """nudge 信号 → nudge"""

    def test_comeback_nudge(self):
        signal = NudgeSignal(nudge_type="comeback", days_idle=2)
        payloads = _run(
            ai_teacher_recommender.recommend_for_nudge(1, signal)
        )
        assert len(payloads) == 1
        assert payloads[0]["type"] == AiTeacherLiveEventType.NUDGE.value
        assert payloads[0]["payload"]["nudgeType"] == "comeback"
        assert "2" in payloads[0]["payload"]["message"]

    def test_miss_you_nudge(self):
        signal = NudgeSignal(nudge_type="miss_you", days_idle=5)
        payloads = _run(
            ai_teacher_recommender.recommend_for_nudge(2, signal)
        )
        assert len(payloads) == 1
        assert "5" in payloads[0]["payload"]["message"]

    def test_take_break_nudge(self):
        signal = NudgeSignal(nudge_type="take_break")
        payloads = _run(
            ai_teacher_recommender.recommend_for_nudge(3, signal)
        )
        assert len(payloads) == 1
        assert "休息" in payloads[0]["payload"]["title"] or "换" in payloads[0]["payload"]["message"]

    def test_try_new_nudge(self):
        signal = NudgeSignal(nudge_type="try_new", skill_name="机器人编程")
        payloads = _run(
            ai_teacher_recommender.recommend_for_nudge(4, signal)
        )
        assert "机器人编程" in payloads[0]["payload"]["message"]


class TestCooldownKeyGeneration:
    """cooldownKey 唯一性与幂等性"""

    def test_celebration_cooldown_includes_related_id(self):
        event = NodeStatusUpdatedEvent(
            {"skill_id": "loops", "old_status": "x", "new_status": "mastered", "progress": 1.0}
        )
        payloads = _run(ai_teacher_recommender.recommend_for_node_status(1, event))
        assert any("celeb:node:loops" == p["cooldownKey"] for p in payloads)

    def test_suggestion_cooldown_includes_diagnosis(self):
        event = NodeStatusUpdatedEvent(
            {"skill_id": "functions", "old_status": "x", "new_status": "in_progress", "progress": 0.1}
        )
        payloads = _run(ai_teacher_recommender.recommend_for_node_status(2, event))
        sug = next(
            p for p in payloads
            if p["type"] == AiTeacherLiveEventType.SUGGESTION.value
        )
        assert sug["cooldownKey"].startswith("sug:")
        assert "learning_plateau" in sug["cooldownKey"]

    def test_nudge_cooldown_per_user(self):
        signal = NudgeSignal(nudge_type="comeback", days_idle=1)
        payloads_a = _run(ai_teacher_recommender.recommend_for_nudge(1, signal))
        payloads_b = _run(ai_teacher_recommender.recommend_for_nudge(2, signal))
        assert payloads_a[0]["cooldownKey"] != payloads_b[0]["cooldownKey"]


class TestEventIdempotency:
    """事件 id 唯一性（前端去重依赖）"""

    def test_event_ids_are_unique(self):
        signal = NudgeSignal(nudge_type="comeback", days_idle=1)
        payloads = [
            _run(ai_teacher_recommender.recommend_for_nudge(1, signal))
            for _ in range(5)
        ]
        ids = [p[0]["id"] for p in payloads]
        assert len(set(ids)) == 5  # 全部唯一


if __name__ == "__main__":
    pytest.main([__file__, "-v"])