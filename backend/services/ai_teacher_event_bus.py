"""
【P3-B】AI 教师实时事件总线

进程内 pub/sub 总线，专用于 AI 教师实时推送事件：
- ai_teacher_celebration: 节点 mastered、套装/里程碑达成
- ai_teacher_suggestion: 检测到前置缺失/高原期/能力失衡/概念混淆
- ai_teacher_nudge: 空闲超时、专注下降、长时间未开始新节点

设计要点：
1. 独立命名空间（不与 gameification_event_bus 混入）
2. 支持同步/异步 handler，自动遍历订阅者
3. 历史记录可查询（前端断线回放）
4. publish() 自动通过 ai_edu_progress_ws_manager 推送给 WebSocket

【P3-B 修复】事件历史持久化：
- 历史记录从纯进程内改为持久化仓储（cache.ai_teacher_persistence）
- 重启后历史可恢复（仅恢复最近 N 条，避免无限增长）
- 订阅者 / 全局订阅者 仍为进程内（短生命周期）
"""

import asyncio
import enum
import logging
import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from cache.ai_teacher_persistence import (
    get_event_history_repo,
    get_user_history_repo,
)

logger = logging.getLogger(__name__)


class AiTeacherLiveEventType(str, enum.Enum):
    """AI 教师实时事件类型枚举"""

    CELEBRATION = "ai_teacher_celebration"
    SUGGESTION = "ai_teacher_suggestion"
    NUDGE = "ai_teacher_nudge"


class AiTeacherLiveBus:
    """
    进程内 AI 教师实时事件总线（线程安全）

    与 GamificationEventBus 不同：AI 教师事件有"何时推送"约束（勿扰/频控），
    此处只做"事件分发 + 持久化历史"工作，频控由 live_settings 完成。
    """

    def __init__(self):
        # user_id → List[handler]
        self._subscribers: Dict[int, List[Callable]] = {}
        # event_type → List[handler]（跨用户订阅，如测试/调试）
        self._global_subscribers: Dict[AiTeacherLiveEventType, List[Callable]] = {}
        self._lock = threading.RLock()
        # 事件历史（最近 200 条）——【P3-B 修复】持久化
        self._event_history_repo = get_event_history_repo()
        self._history_max = 200
        self._event_history: List[Dict[str, Any]] = []
        # 历史按用户分片缓存（前端断线重连时回放）——【P3-B 修复】持久化
        self._user_history_repo = get_user_history_repo()
        self._user_history_max = 50
        self._user_history_cache: Dict[int, List[Dict[str, Any]]] = {}

        # 启动时从磁盘重建内存列表（仅保留最近 N 条）
        self._rebuild_in_memory_history()

    def _rebuild_in_memory_history(self) -> None:
        """
        从持久化仓储重建进程内历史快照
        - 仅保留最近 history_max / user_history_max 条
        - 失败时安全降级（空历史）
        """
        try:
            raw = self._event_history_repo.snapshot()
            if isinstance(raw, dict):
                # 旧格式兼容：可能存为 {"records": [...]} 或直接是 list
                records = raw.get("records", []) if isinstance(raw.get("records"), list) else []
                # 若整个 dict 是 list-like dict 则尝试按 sorted keys
                if not records and raw:
                    # 兼容旧 dump：key 为整型索引
                    try:
                        records = [raw[str(i)] for i in range(len(raw))]
                    except Exception:
                        records = []
                self._event_history: List[Dict[str, Any]] = records[-self._history_max:]
                logger.debug(
                    f"📜 AI 教师事件历史从磁盘恢复：{len(self._event_history)} 条"
                )
        except Exception as e:
            logger.warning(f"⚠️ 事件历史重建失败：{e}")
            self._event_history = []

    def _rebuild_user_history(self, user_id: int) -> None:
        """从持久化仓储重建某用户的内存历史"""
        try:
            raw = self._user_history_repo.get(str(user_id), [])
            if isinstance(raw, list):
                self._user_history_cache.setdefault(
                    int(user_id), raw[-self._user_history_max:]
                )
        except Exception as e:
            logger.warning(f"⚠️ 用户 {user_id} 历史重建失败：{e}")
            self._user_history_cache.setdefault(int(user_id), [])

    def subscribe(self, user_id: int, handler: Callable) -> None:
        """
        订阅某个用户的 AI 教师事件

        Args:
            user_id: 目标用户 ID
            handler: 签名 (event: dict) -> None
        """
        with self._lock:
            self._subscribers.setdefault(user_id, []).append(handler)
        logger.debug(
            f"📡 用户 {user_id} 订阅 AI 教师事件 "
            f"(现有 {len(self._subscribers.get(user_id, []))} 个)"
        )

    def subscribe_global(
        self, event_type: AiTeacherLiveEventType, handler: Callable
    ) -> None:
        """全局订阅某类型 AI 教师事件（不限定 user）"""
        with self._lock:
            self._global_subscribers.setdefault(event_type, []).append(handler)

    def unsubscribe(
        self, user_id: int, handler: Optional[Callable] = None
    ) -> None:
        """取消订阅"""
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

    def publish(self, event: Dict[str, Any]) -> int:
        """
        发布 AI 教师事件，自动广播到该用户的订阅者与 WebSocket

        Returns:
            成功调用的 handler 数
        """
        user_id = event.get("userId")
        if user_id is None:
            logger.warning("⚠️ AI 教师事件缺少 userId，跳过")
            return 0

        # 记录历史（全局 + 用户）——【P3-B 修复】持久化
        record = {
            **event,
            "_published_at": datetime.utcnow().isoformat(),
        }
        with self._lock:
            self._event_history.append(record)
            if len(self._event_history) > self._history_max:
                self._event_history = self._event_history[-self._history_max :]

            user_hist = self._user_history_cache.setdefault(int(user_id), [])
            user_hist.append(record)
            if len(user_hist) > self._user_history_max:
                user_hist[:] = user_hist[-self._user_history_max :]

        # 持久化写入（debounced，由仓储内部调度）
        try:
            self._event_history_repo.replace_all(
                {"records": list(self._event_history)}
            )
            self._user_history_repo.set(
                str(int(user_id)), list(user_hist)
            )
        except Exception as e:
            logger.warning(f"⚠️ AI 教师事件历史持久化失败：{e}")

        # 调用订阅者
        with self._lock:
            user_handlers = list(self._subscribers.get(int(user_id), []))
            event_type_str = event.get("type", "")
            try:
                event_type_enum = AiTeacherLiveEventType(event_type_str)
                global_handlers = list(
                    self._global_subscribers.get(event_type_enum, [])
                )
            except ValueError:
                global_handlers = []

        success_count = 0
        for handler in user_handlers + global_handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(result)
                        else:
                            loop.run_until_complete(result)
                    except RuntimeError:
                        logger.warning("无法调度 async handler（无 event loop）")
                success_count += 1
            except Exception as e:
                logger.error(f"❌ AI 教师 event handler 失败: {e}", exc_info=True)

        # 推送到 WebSocket（通过 ai_edu 学习进度连接管理器复用通道）
        try:
            from routes.ai_edu_websocket_routes import manager as ws_manager

            message = {
                "type": event.get("type"),
                "data": event,
                "timestamp": datetime.utcnow().isoformat(),
            }
            asyncio.create_task(
                ws_manager.broadcast_to_user(int(user_id), message)
            )
        except Exception as e:
            logger.debug(f"WebSocket 推送失败（可能尚未启动）: {e}")

        if success_count > 0:
            logger.debug(
                f"📤 AI 教师事件 {event.get('type')} 推送给用户 {user_id}: "
                f"{success_count} 个 handler"
            )
        return success_count

    def get_history(
        self, user_id: Optional[int] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取事件历史（前端断线回放用）"""
        with self._lock:
            if user_id is not None:
                uid = int(user_id)
                # 缓存未命中时按需重建
                if uid not in self._user_history_cache:
                    self._rebuild_user_history(uid)
                history = list(self._user_history_cache.get(uid, []))
            else:
                history = list(self._event_history)
        return history[-limit:]

    def clear(self) -> None:
        """清空所有订阅与历史（主要用于测试）"""
        with self._lock:
            self._subscribers.clear()
            self._global_subscribers.clear()
            self._event_history.clear()
            self._user_history_cache.clear()
        # 同时清空持久化仓储
        try:
            self._event_history_repo.clear()
            self._user_history_repo.clear()
        except Exception:
            pass


# 全局单例
ai_teacher_live_bus = AiTeacherLiveBus()


# ==================== 便捷构造器 ====================


def make_celebration_payload(
    user_id: int,
    title: str,
    message: str,
    emoji: str = "🎉",
    related_id: Optional[str] = None,
    related_kind: Optional[str] = None,  # "node" | "achievement" | "set"
    cta_label: Optional[str] = None,
    cta_route: Optional[str] = None,
) -> Dict[str, Any]:
    """构造 ai_teacher_celebration 事件载荷"""
    import uuid

    return {
        "id": f"celeb_{uuid.uuid4().hex[:12]}",
        "type": AiTeacherLiveEventType.CELEBRATION.value,
        "userId": int(user_id),
        "payload": {
            "title": title,
            "message": message,
            "emoji": emoji,
            "relatedId": related_id,
            "relatedKind": related_kind,
            "ctaLabel": cta_label,
            "ctaRoute": cta_route,
        },
        "ttlMs": 12 * 60 * 1000,  # 12 分钟
        "cooldownKey": f"celeb:{related_kind}:{related_id}" if related_id else f"celeb:{user_id}",
        "createdAt": datetime.utcnow().isoformat(),
    }


def make_suggestion_payload(
    user_id: int,
    diagnosis_type: str,
    severity: str,
    title: str,
    message: str,
    related_skill_id: Optional[str] = None,
    recommended_courses: Optional[List[str]] = None,
    cta_label: Optional[str] = None,
    cta_route: Optional[str] = None,
) -> Dict[str, Any]:
    """构造 ai_teacher_suggestion 事件载荷"""
    import uuid

    return {
        "id": f"sug_{uuid.uuid4().hex[:12]}",
        "type": AiTeacherLiveEventType.SUGGESTION.value,
        "userId": int(user_id),
        "payload": {
            "diagnosisType": diagnosis_type,
            "severity": severity,
            "title": title,
            "message": message,
            "relatedSkillId": related_skill_id,
            "recommendedCourses": recommended_courses or [],
            "ctaLabel": cta_label,
            "ctaRoute": cta_route,
        },
        "ttlMs": 8 * 60 * 1000,  # 8 分钟
        "cooldownKey": (
            f"sug:{diagnosis_type}:{related_skill_id}"
            if related_skill_id
            else f"sug:{diagnosis_type}:{user_id}"
        ),
        "createdAt": datetime.utcnow().isoformat(),
    }


def make_nudge_payload(
    user_id: int,
    nudge_type: str,  # "comeback" | "miss_you" | "take_break" | "try_new"
    title: str,
    message: str,
    suggested_skill_id: Optional[str] = None,
    cta_label: Optional[str] = None,
    cta_route: Optional[str] = None,
) -> Dict[str, Any]:
    """构造 ai_teacher_nudge 事件载荷"""
    import uuid

    return {
        "id": f"nudge_{uuid.uuid4().hex[:12]}",
        "type": AiTeacherLiveEventType.NUDGE.value,
        "userId": int(user_id),
        "payload": {
            "nudgeType": nudge_type,
            "title": title,
            "message": message,
            "suggestedSkillId": suggested_skill_id,
            "ctaLabel": cta_label,
            "ctaRoute": cta_route,
        },
        "ttlMs": 6 * 60 * 1000,  # 6 分钟
        "cooldownKey": f"nudge:{nudge_type}:{user_id}",
        "createdAt": datetime.utcnow().isoformat(),
    }