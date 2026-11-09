"""
【P3-B】AI 教师触发器

订阅 gamification_event_bus 的 3 类事件：
- NODE_STATUS_UPDATED → 推荐引擎 → celebration / suggestion
- ACHIEVEMENT_UNLOCKED → 推荐引擎 → celebration
- SET_COMPLETED → 推荐引擎 → celebration

每个 handler：
1. 通过 live_settings.can_push 决定是否触发
2. 调 recommender 生成事件
3. 调 ai_teacher_event_bus.publish
4. record_push 更新频控

提供：
- register()：在 FastAPI lifespan 启动时调用
- unregister()：关闭时清理订阅
"""

import asyncio
import logging
from typing import Any, Dict

from services.ai_teacher_event_bus import ai_teacher_live_bus
from services.ai_teacher_live_settings import ai_teacher_live_settings
from services.ai_teacher_recommender import (
    AchievementUnlockedEvent,
    NodeStatusUpdatedEvent,
    SetCompletedEvent,
    ai_teacher_recommender,
)
from services.gamification_event_bus import (
    GamificationEventType,
    gamification_event_bus,
)

logger = logging.getLogger(__name__)


# 跟踪注册的 handler，便于 unregister
_registered_handlers: Dict[str, Any] = {}


def _schedule(coro) -> None:
    """
    在当前或新建的事件循环中调度 async coroutine

    - 有运行中的 loop → create_task
    - 有 loop 但未运行 → run_until_complete
    - 无 loop（测试） → asyncio.run
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        asyncio.run(coro)


def _dispatch(
    event_type: str,
    data: dict[str, Any],
    coro_factory,
) -> None:
    """通用分派：从 data 解析 user_id 并调度 async 任务"""
    user_id = data.get("user_id")
    if user_id is None:
        logger.warning(f"⚠️ handler 缺少 user_id (event={event_type})")
        return
    _schedule(coro_factory(int(user_id), data))


def _handle_node_status(event_type: str, data: dict[str, Any]) -> None:
    """节点状态更新 → celebration / suggestion"""
    user_id = data.get("user_id")
    if user_id is None:
        return
    user_id = int(user_id)

    if not (
        ai_teacher_live_settings.is_type_enabled(
            user_id, "ai_teacher_celebration"
        )
        or ai_teacher_live_settings.is_type_enabled(
            user_id, "ai_teacher_suggestion"
        )
    ):
        return

    event = NodeStatusUpdatedEvent(data)

    async def _runner(uid: int, _evt=event):
        try:
            payloads = await ai_teacher_recommender.recommend_for_node_status(
                uid, _evt
            )
            await _publish_with_throttle(uid, payloads)
        except Exception as e:
            logger.error(f"❌ recommend_for_node_status 失败: {e}", exc_info=True)

    _schedule(_runner(user_id))


def _handle_achievement(event_type: str, data: dict[str, Any]) -> None:
    """成就解锁 → celebration"""
    user_id = data.get("user_id")
    if user_id is None:
        return
    user_id = int(user_id)

    if not ai_teacher_live_settings.is_type_enabled(
        user_id, "ai_teacher_celebration"
    ):
        return

    event = AchievementUnlockedEvent(data)

    async def _runner(uid: int, _evt=event):
        try:
            payloads = await ai_teacher_recommender.recommend_for_achievement(
                uid, _evt
            )
            await _publish_with_throttle(uid, payloads)
        except Exception as e:
            logger.error(f"❌ recommend_for_achievement 失败: {e}", exc_info=True)

    _schedule(_runner(user_id))


def _handle_set_completed(event_type: str, data: dict[str, Any]) -> None:
    """套装完成 → celebration"""
    user_id = data.get("user_id")
    if user_id is None:
        return
    user_id = int(user_id)

    if not ai_teacher_live_settings.is_type_enabled(
        user_id, "ai_teacher_celebration"
    ):
        return

    event = SetCompletedEvent(data)

    async def _runner(uid: int, _evt=event):
        try:
            payloads = await ai_teacher_recommender.recommend_for_set_completed(
                uid, _evt
            )
            await _publish_with_throttle(uid, payloads)
        except Exception as e:
            logger.error(f"❌ recommend_for_set_completed 失败: {e}", exc_info=True)

    _schedule(_runner(user_id))


async def _publish_with_throttle(user_id: int, payloads) -> None:
    """逐个推送事件，过频控后发布"""
    for payload in payloads or []:
        evt_type = payload.get("type", "")
        cooldown_key = payload.get("cooldownKey", "")
        if not ai_teacher_live_settings.can_push(
            user_id, cooldown_key, evt_type
        ):
            logger.debug(
                f"🚫 推送被频控阻止 user={user_id} cooldown={cooldown_key}"
            )
            continue
        ai_teacher_live_bus.publish(payload)
        ai_teacher_live_settings.record_push(user_id, cooldown_key)


# ==================== 注册 / 反注册 ====================


def register() -> None:
    """
    在 FastAPI lifespan 启动阶段调用，把 3 个 handler 挂到游戏化事件总线
    的 global 订阅。注意：gamification_event_bus.emit() 会在调用 handler
    时把 user_id 注入到 data 副本（见 gamification_event_bus.P3-B 修改），
    所以 global handler 可以从 data 中读到 user_id。
    """
    if _registered_handlers:
        logger.info("AI 教师触发器已注册，跳过重复")
        return

    def _global_node(event_type: str, data: Dict[str, Any]):
        _handle_node_status(event_type, data)

    def _global_achievement(event_type: str, data: Dict[str, Any]):
        _handle_achievement(event_type, data)

    def _global_set(event_type: str, data: Dict[str, Any]):
        _handle_set_completed(event_type, data)

    gamification_event_bus.subscribe_global(
        GamificationEventType.NODE_STATUS_UPDATED, _global_node
    )
    gamification_event_bus.subscribe_global(
        GamificationEventType.ACHIEVEMENT_UNLOCKED, _global_achievement
    )
    gamification_event_bus.subscribe_global(
        GamificationEventType.SET_COMPLETED, _global_set
    )

    _registered_handlers["node"] = _global_node
    _registered_handlers["achievement"] = _global_achievement
    _registered_handlers["set"] = _global_set

    logger.info("✅ AI 教师触发器已注册（3 类事件）")


def unregister() -> None:
    """清理订阅（lifespan 关闭）

    注意：gamification_event_bus 没有 unsubscribe_global 接口；
    但 _registered_handlers 仍可用于后续重入检测。
    """
    global _registered_handlers
    if not _registered_handlers:
        return
    _registered_handlers.clear()
    logger.info("ℹ️  AI 教师触发器已反注册")


def reset_for_test() -> None:
    """仅供测试：清空 handler 跟踪 dict"""
    global _registered_handlers
    _registered_handlers = {}


# ==================== 便捷接口（供 scheduler 直接 publish）==================


async def publish_nudge_signal(user_id: int, nudge_type: str, **kwargs) -> None:
    """由 scheduler 调用：生成 nudge 并走 fanout"""
    from services.ai_teacher_recommender import NudgeSignal

    signal = NudgeSignal(nudge_type=nudge_type, **kwargs)
    payloads = await ai_teacher_recommender.recommend_for_nudge(user_id, signal)
    await _publish_with_throttle(user_id, payloads)