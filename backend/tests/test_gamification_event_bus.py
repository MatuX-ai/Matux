"""
【P3-A-2】游戏化事件总线单元测试
"""
import pytest
from unittest.mock import MagicMock

from services.gamification_event_bus import (
    GamificationEventBus,
    GamificationEventType,
    gamification_event_bus,
    make_achievement_unlocked_payload,
    make_node_status_updated_payload,
    make_set_completed_payload,
)


class TestEventBusBasic:
    """事件总线基本行为测试"""

    def setup_method(self):
        gamification_event_bus.clear()

    def test_subscribe_and_emit(self):
        """订阅 + emit 触发 handler（【P3-B】data 会注入 user_id）"""
        bus = GamificationEventBus()
        handler = MagicMock()
        bus.subscribe(user_id=1, handler=handler)
        bus.emit(user_id=1, event_type="achievement_unlocked", data={"x": 1})
        handler.assert_called_once_with("achievement_unlocked", {"x": 1, "user_id": 1})

    def test_emit_no_subscribers(self):
        """无订阅者时 emit 不应崩溃"""
        bus = GamificationEventBus()
        count = bus.emit(user_id=1, event_type="x", data={})
        assert count == 0

    def test_multiple_subscribers(self):
        """多订阅者都被调用"""
        bus = GamificationEventBus()
        h1 = MagicMock()
        h2 = MagicMock()
        bus.subscribe(user_id=1, handler=h1)
        bus.subscribe(user_id=1, handler=h2)
        count = bus.emit(user_id=1, event_type="x", data={})
        assert count == 2
        h1.assert_called_once()
        h2.assert_called_once()

    def test_per_user_isolation(self):
        """不同用户的订阅相互隔离"""
        bus = GamificationEventBus()
        h1 = MagicMock()
        h2 = MagicMock()
        bus.subscribe(user_id=1, handler=h1)
        bus.subscribe(user_id=2, handler=h2)
        bus.emit(user_id=1, event_type="x", data={"for": 1})
        h1.assert_called_once()
        h2.assert_not_called()

    def test_handler_exception_isolated(self):
        """单个 handler 异常不影响其他 handler"""
        bus = GamificationEventBus()

        def bad_handler(t, d):
            raise ValueError("oops")

        good_handler = MagicMock()
        bus.subscribe(user_id=1, handler=bad_handler)
        bus.subscribe(user_id=1, handler=good_handler)
        count = bus.emit(user_id=1, event_type="x", data={})
        # bad_handler 异常但不影响计数（仍调用了一次）
        assert count >= 1
        good_handler.assert_called_once()

    def test_unsubscribe_specific(self):
        """取消特定 handler"""
        bus = GamificationEventBus()
        h1 = MagicMock()
        h2 = MagicMock()
        bus.subscribe(user_id=1, handler=h1)
        bus.subscribe(user_id=1, handler=h2)
        bus.unsubscribe(user_id=1, handler=h1)
        bus.emit(user_id=1, event_type="x", data={})
        h1.assert_not_called()
        h2.assert_called_once()

    def test_unsubscribe_all(self):
        """不传 handler 取消所有"""
        bus = GamificationEventBus()
        h1 = MagicMock()
        h2 = MagicMock()
        bus.subscribe(user_id=1, handler=h1)
        bus.subscribe(user_id=1, handler=h2)
        bus.unsubscribe(user_id=1)
        count = bus.emit(user_id=1, event_type="x", data={})
        assert count == 0

    def test_unsubscribe_nonexistent_user(self):
        """取消不存在的用户不应崩溃"""
        bus = GamificationEventBus()
        bus.unsubscribe(user_id=999)  # 不报错

    def test_event_history(self):
        """事件历史记录"""
        bus = GamificationEventBus()
        bus.emit(user_id=1, event_type="x", data={"a": 1})
        bus.emit(user_id=1, event_type="y", data={"b": 2})
        history = bus.get_history(user_id=1)
        assert len(history) == 2
        assert history[0]["type"] == "x"
        assert history[1]["type"] == "y"

    def test_event_history_per_user(self):
        """按用户过滤历史"""
        bus = GamificationEventBus()
        bus.emit(user_id=1, event_type="x", data={})
        bus.emit(user_id=2, event_type="y", data={})
        h1 = bus.get_history(user_id=1)
        assert len(h1) == 1
        assert h1[0]["user_id"] == 1

    def test_global_subscribe(self):
        """全局订阅某类型"""
        bus = GamificationEventBus()
        handler = MagicMock()
        bus.subscribe_global(GamificationEventType.ACHIEVEMENT_UNLOCKED, handler)
        # 任何用户的 ACHIEVEMENT_UNLOCKED 都会触发
        bus.emit(user_id=1, event_type="achievement_unlocked", data={})
        bus.emit(user_id=2, event_type="achievement_unlocked", data={})
        assert handler.call_count == 2

    def test_event_type_string_compat(self):
        """event_type 支持字符串（【P3-B】data 会注入 user_id）"""
        bus = GamificationEventBus()
        handler = MagicMock()
        bus.subscribe(user_id=1, handler=handler)
        bus.emit(user_id=1, event_type="achievement_unlocked", data={})
        handler.assert_called_once_with("achievement_unlocked", {"user_id": 1})

    def test_event_type_enum_compat(self):
        """event_type 支持枚举（【P3-B】data 会注入 user_id）"""
        bus = GamificationEventBus()
        handler = MagicMock()
        bus.subscribe(user_id=1, handler=handler)
        bus.emit(
            user_id=1,
            event_type=GamificationEventType.ACHIEVEMENT_UNLOCKED,
            data={},
        )
        handler.assert_called_once_with("achievement_unlocked", {"user_id": 1})


class TestPayloadBuilders:
    """payload 构造器测试"""

    def test_achievement_unlocked_payload(self):
        p = make_achievement_unlocked_payload(
            user_id=1,
            achievement_id=42,
            name="Loop Master",
            rarity="rare",
            points=50,
            related_skill_ids=["py-loop"],
        )
        assert p["achievement_id"] == 42
        assert p["name"] == "Loop Master"
        assert p["rarity"] == "rare"
        assert p["points"] == 50
        assert p["related_skill_ids"] == ["py-loop"]
        assert "unlocked_at" in p

    def test_node_status_updated_payload(self):
        p = make_node_status_updated_payload(
            user_id=1,
            skill_id="py-func",
            old_status="in_progress",
            new_status="mastered",
            progress=1.0,
        )
        assert p["skill_id"] == "py-func"
        assert p["old_status"] == "in_progress"
        assert p["new_status"] == "mastered"
        assert p["progress"] == 1.0
        assert "timestamp" in p

    def test_set_completed_payload(self):
        p = make_set_completed_payload(
            user_id=1,
            set_id="set-python-master",
            set_name="Python Master",
            bonus_reward={"type": "title", "value": "Python 大师"},
        )
        assert p["set_id"] == "set-python-master"
        assert p["set_name"] == "Python Master"
        assert p["bonus_reward"]["type"] == "title"


class TestEventBusConcurrency:
    """并发测试"""

    def test_concurrent_emit(self):
        """并发 emit 不应崩溃"""
        import threading
        bus = GamificationEventBus()
        handler = MagicMock()
        bus.subscribe(user_id=1, handler=handler)

        def emitter():
            for _ in range(50):
                bus.emit(user_id=1, event_type="x", data={})

        threads = [threading.Thread(target=emitter) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # handler 至少被调用 5*50 = 250 次
        assert handler.call_count >= 250


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
