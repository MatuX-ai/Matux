"""
【P3-A-2】游戏化事件总线

进程内 pub/sub 总线，用于：
- 成就解锁事件
- 节点状态更新事件
- 套装完成事件

事件会被推送给所有 WebSocket 连接（同用户）。
"""

import asyncio
from datetime import datetime
import enum
import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class GamificationEventType(str, enum.Enum):
    """事件类型枚举"""

    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    NODE_STATUS_UPDATED = "node_status_updated"
    SET_COMPLETED = "set_completed"


class GamificationEventBus:
    """
    进程内事件总线（线程安全）

    支持同步 / 异步 handler，自动遍历订阅者。
    设计要点：
    1. 单例模式（gamification_event_bus）
    2. 每个 user_id 独立订阅列表
    3. handler 异常被隔离，不影响其他订阅者
    4. 支持 asyncio.create_task 包装 async handler
    """

    def __init__(self):
        # user_id → List[handler]
        self._subscribers: Dict[int, List[Callable]] = {}
        # event_type → List[handler]（跨用户订阅）
        self._global_subscribers: Dict[GamificationEventType, List[Callable]] = {}
        self._lock = threading.RLock()
        # 事件历史（最近 100 条，仅用于调试 / 测试）
        self._event_history: List[Dict[str, Any]] = []
        self._history_max = 100

    def subscribe(self, user_id: int, handler: Callable) -> None:
        """
        订阅某个用户的事件

        Args:
            user_id: 目标用户 ID
            handler: 签名 (event_type: str, data: dict) -> None
        """
        with self._lock:
            self._subscribers.setdefault(user_id, []).append(handler)
        logger.debug(
            f"📡 用户 {user_id} 订阅事件 (现有 {len(self._subscribers.get(user_id, []))} 个)"
        )

    def subscribe_global(
        self, event_type: GamificationEventType, handler: Callable
    ) -> None:
        """全局订阅某类型事件（不限定 user）"""
        with self._lock:
            self._global_subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(self, user_id: int, handler: Optional[Callable] = None) -> None:
        """
        取消订阅

        Args:
            user_id: 用户 ID
            handler: 不传则清空该用户所有订阅
        """
        with self._lock:
            if user_id not in self._subscribers:
                return
            if handler is None:
                self._subscribers[user_id].clear()
            else:
                try:
                    self._subscribers[user_id].remove(handler)
                except ValueError:
                    pass
            if not self._subscribers[user_id]:
                del self._subscribers[user_id]

    def emit(
        self,
        user_id: int,
        event_type: Union[GamificationEventType, str],
        data: Dict[str, Any],
    ) -> int:
        """
        发送事件给指定用户的所有订阅者

        Returns:
            成功调用的 handler 数
        """
        if isinstance(event_type, GamificationEventType):
            event_type_str = event_type.value
        else:
            event_type_str = event_type

        # 记录历史
        event_record = {
            "type": event_type_str,
            "user_id": user_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        with self._lock:
            self._event_history.append(event_record)
            if len(self._event_history) > self._history_max:
                self._event_history = self._event_history[-self._history_max :]

        # 调用订阅者
        with self._lock:
            user_handlers = list(self._subscribers.get(user_id, []))
            try:
                event_type_enum = GamificationEventType(event_type_str)
                global_handlers = list(
                    self._global_subscribers.get(event_type_enum, [])
                )
            except ValueError:
                global_handlers = []

        success_count = 0
        # 【P3-B】注入 user_id 到 data 副本，方便 global subscribers 路由
        enriched_data = {**data, "user_id": user_id}
        for handler in user_handlers + global_handlers:
            try:
                result = handler(event_type_str, enriched_data)
                if asyncio.iscoroutine(result):
                    # async handler：在事件循环中调度
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(result)
                        else:
                            loop.run_until_complete(result)
                    except RuntimeError:
                        # 没有 event loop → 跳过（测试场景）
                        logger.warning("无法调度 async handler（无 event loop）")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ Event handler 失败: {e}", exc_info=True)

        if success_count > 0:
            logger.debug(
                f"📤 事件 {event_type_str} 推送给用户 {user_id}: " f"{success_count} 个 handler"
            )
        return success_count

    def get_history(
        self, user_id: Optional[int] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取事件历史（调试用）"""
        with self._lock:
            history = list(self._event_history)
        if user_id is not None:
            history = [e for e in history if e["user_id"] == user_id]
        return history[-limit:]

    def clear(self) -> None:
        """清空所有订阅与历史（主要用于测试）"""
        with self._lock:
            self._subscribers.clear()
            self._global_subscribers.clear()
            self._event_history.clear()


# 全局单例
gamification_event_bus = GamificationEventBus()


# ==================== 便捷构造器 ====================


def make_achievement_unlocked_payload(
    user_id: int,
    achievement_id: int,
    name: str,
    rarity: str,
    points: int = 0,
    related_skill_ids: Optional[List[str]] = None,
    icon: Optional[str] = None,
    description: Optional[str] = None,
    unlocked_at: Optional[str] = None,
) -> Dict[str, Any]:
    """构造 achievement_unlocked 事件载荷"""
    return {
        "achievement_id": achievement_id,
        "name": name,
        "rarity": rarity,
        "points": points,
        "related_skill_ids": related_skill_ids or [],
        "icon": icon,
        "description": description,
        "unlocked_at": unlocked_at or datetime.utcnow().isoformat(),
    }


def make_node_status_updated_payload(
    user_id: int,
    skill_id: str,
    old_status: str,
    new_status: str,
    progress: float = 0.0,
    related_achievement_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """构造 node_status_updated 事件载荷"""
    return {
        "skill_id": skill_id,
        "old_status": old_status,
        "new_status": new_status,
        "progress": progress,
        "related_achievement_ids": related_achievement_ids or [],
        "timestamp": datetime.utcnow().isoformat(),
    }


def make_set_completed_payload(
    user_id: int,
    set_id: str,
    set_name: str,
    bonus_reward: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """构造 set_completed 事件载荷"""
    return {
        "set_id": set_id,
        "set_name": set_name,
        "bonus_reward": bonus_reward,
        "timestamp": datetime.utcnow().isoformat(),
    }
