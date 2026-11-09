"""
【P3-B】AI 教师触发器单元测试

覆盖：
- 订阅正常生效（gamification emit → AI 教师事件触发）
- 频控阻断（同一 cooldownKey 短时间内第二次触发被丢弃）
- 设置禁用时不推送
- 卸载后不再触发
"""

import pytest

from services.ai_teacher_event_bus import (
    AiTeacherLiveEventType,
    ai_teacher_live_bus,
)
from services.ai_teacher_live_settings import (
    ai_teacher_live_settings,
)
from services.ai_teacher_triggers import (
    register,
    reset_for_test,
    unregister,
)
from services.gamification_event_bus import (
    GamificationEventType,
    gamification_event_bus,
)


@pytest.fixture(autouse=True)
def _clean_state():
    """每个测试前清空所有状态"""
    ai_teacher_live_bus.clear()
    ai_teacher_live_settings.clear()
    gamification_event_bus.clear()
    reset_for_test()
    yield
    ai_teacher_live_bus.clear()
    ai_teacher_live_settings.clear()
    gamification_event_bus.clear()
    reset_for_test()


class TestTriggerRegistration:
    """注册 / 反注册"""

    def test_register_creates_handlers(self):
        register()
        # 验证：handler 已注册到 gamification_event_bus 的 global 订阅
        assert GamificationEventType.NODE_STATUS_UPDATED in gamification_event_bus._global_subscribers
        assert GamificationEventType.ACHIEVEMENT_UNLOCKED in gamification_event_bus._global_subscribers
        assert GamificationEventType.SET_COMPLETED in gamification_event_bus._global_subscribers

    def test_register_is_idempotent(self):
        register()
        first_count = sum(
            len(handlers)
            for handlers in gamification_event_bus._global_subscribers.values()
        )
        register()  # 第二次应跳过
        second_count = sum(
            len(handlers)
            for handlers in gamification_event_bus._global_subscribers.values()
        )
        assert first_count == second_count


class TestNodeStatusTrigger:
    """节点状态变更触发器"""

    def test_node_status_emits_celebration(self):
        register()
        # 订阅 AI 教师事件总线
        received = []
        ai_teacher_live_bus.subscribe(1, lambda evt: received.append(evt))

        gamification_event_bus.emit(
            user_id=1,
            event_type=GamificationEventType.NODE_STATUS_UPDATED,
            data={
                "skill_id": "loops",
                "old_status": "in_progress",
                "new_status": "mastered",
                "progress": 1.0,
            },
        )

        # 等待异步任务完成
        import time
        time.sleep(0.1)

        celebrations = [
            e for e in received
            if e["type"] == AiTeacherLiveEventType.CELEBRATION.value
        ]
        assert len(celebrations) >= 1

    def test_cooldown_blocks_second_push(self):
        """同一 cooldownKey 在 min_interval 内第二次被拒绝"""
        register()
        received = []
        ai_teacher_live_bus.subscribe(1, lambda evt: received.append(evt))

        # 把冷却时间调小
        ai_teacher_live_settings.update_settings(
            1, {"min_interval_seconds": 60}
        )

        # 第一次 emit
        gamification_event_bus.emit(
            user_id=1,
            event_type=GamificationEventType.NODE_STATUS_UPDATED,
            data={
                "skill_id": "loops",
                "old_status": "in_progress",
                "new_status": "mastered",
                "progress": 1.0,
            },
        )
        import time
        time.sleep(0.1)

        # 第二次 emit（同一 skill_id 冷却中）
        gamification_event_bus.emit(
            user_id=1,
            event_type=GamificationEventType.NODE_STATUS_UPDATED,
            data={
                "skill_id": "loops",
                "old_status": "mastered",
                "new_status": "mastered",
                "progress": 1.0,
            },
        )
        time.sleep(0.1)

        celebrations = [
            e for e in received
            if e["type"] == AiTeacherLiveEventType.CELEBRATION.value
        ]
        # 应该只有 1 条
        assert len(celebrations) == 1


class TestTypeDisabled:
    """某类事件设置禁用时不推送"""

    def test_celebration_disabled_no_push(self):
        register()
        ai_teacher_live_settings.update_settings(
            1, {"celebration_enabled": False}
        )
        received = []
        ai_teacher_live_bus.subscribe(1, lambda evt: received.append(evt))

        gamification_event_bus.emit(
            user_id=1,
            event_type=GamificationEventType.ACHIEVEMENT_UNLOCKED,
            data={
                "achievement_id": 1,
                "name": "test",
                "rarity": "common",
                "points": 10,
            },
        )
        import time
        time.sleep(0.1)

        assert not any(
            e["type"] == AiTeacherLiveEventType.CELEBRATION.value
            for e in received
        )


class TestTriggerUnregister:
    """unregister 行为"""

    def test_unregister_clears_handlers(self):
        register()
        unregister()
        # _registered_handlers 清空
        from services import ai_teacher_triggers
        assert ai_teacher_triggers._registered_handlers == {}


class TestLiveSettingsService:
    """settings 服务单测"""

    def test_default_settings(self):
        s = ai_teacher_live_settings.get_settings(999)
        assert s.enabled is True
        assert s.celebration_enabled is True
        assert s.max_per_hour == 3

    def test_update_partial(self):
        ai_teacher_live_settings.update_settings(
            1, {"enabled": False, "max_per_hour": 10}
        )
        s = ai_teacher_live_settings.get_settings(1)
        assert s.enabled is False
        assert s.max_per_hour == 10
        # 其他字段保持默认
        assert s.celebration_enabled is True

    def test_can_push_dnd_blocks(self):
        ai_teacher_live_settings.update_settings(
            1, {"dnd_start_hour": 0, "dnd_end_hour": 24}
        )
        # 整段勿扰
        result = ai_teacher_live_settings.can_push(
            1, "test_key", "ai_teacher_celebration"
        )
        assert result is False

    def test_can_push_cooldown_blocks(self):
        ai_teacher_live_settings.update_settings(
            1, {"min_interval_seconds": 600}
        )
        ai_teacher_live_settings.record_push(1, "test_key")
        # 立即再次询问应被阻止
        result = ai_teacher_live_settings.can_push(
            1, "test_key", "ai_teacher_celebration"
        )
        assert result is False

    def test_can_push_hour_limit(self):
        ai_teacher_live_settings.update_settings(
            1, {"max_per_hour": 2, "min_interval_seconds": 0}
        )
        ai_teacher_live_settings.record_push(1, "key_a")
        ai_teacher_live_settings.record_push(1, "key_b")
        # 第三次应被阻止
        result = ai_teacher_live_settings.can_push(
            1, "key_c", "ai_teacher_celebration"
        )
        assert result is False

    def test_type_specific_block(self):
        ai_teacher_live_settings.update_settings(
            1, {"suggestion_enabled": False}
        )
        result = ai_teacher_live_settings.can_push(
            1, "k", "ai_teacher_suggestion"
        )
        assert result is False
        # celebration 不受影响
        result = ai_teacher_live_settings.can_push(
            1, "k", "ai_teacher_celebration"
        )
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])