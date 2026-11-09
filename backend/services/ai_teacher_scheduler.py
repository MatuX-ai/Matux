"""
【P3-B】AI 教师调度器

后台 asyncio 任务：
- 每 60s 扫描一次"需要 nudge"的用户
- 数据源：复用 LearningProgressConnectionManager.user_learning_states
- 规则：
  - 空闲 > 24h：nudge(type=comeback)
  - 空闲 > 72h：nudge(type=miss_you)
  - 专注下降：nudge(type=take_break)
- 所有 nudge 走 live_settings.can_push 频控
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from services.ai_teacher_event_bus import ai_teacher_live_bus
from services.ai_teacher_live_settings import ai_teacher_live_settings
from services.ai_teacher_recommender import NudgeSignal, ai_teacher_recommender

logger = logging.getLogger(__name__)


class AITeacherScheduler:
    """
    后台调度器：扫描学习状态，调用 recommender 推送 nudge

    启动：start() 在 lifespan 中调用，返回 asyncio.Task
    停止：stop() 取消任务
    """

    SCAN_INTERVAL_SECONDS = 60
    COMEBACK_DAYS = 1  # >24h
    MISS_YOU_DAYS = 3  # >72h

    def __init__(self):
        self._task: Optional[asyncio.Task] = None
        self._running = False
        # 上一周期专注度快照（用户id → tab_switch_frequency）
        self._prev_focus: Dict[str, int] = {}

    async def start(self) -> None:
        """启动后台扫描任务"""
        if self._running:
            logger.info("AI 教师调度器已在运行")
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("✅ AI 教师调度器已启动")

    async def stop(self) -> None:
        """停止后台扫描任务"""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.warning(f"调度器停止异常: {e}")
            self._task = None
        logger.info("ℹ️  AI 教师调度器已停止")

    async def _run_loop(self) -> None:
        """主循环"""
        logger.info("📊 AI 教师调度器主循环开始")
        try:
            while self._running:
                try:
                    await self._scan_once()
                except Exception as e:
                    logger.error(f"调度器扫描失败: {e}", exc_info=True)
                await asyncio.sleep(self.SCAN_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            logger.info("调度器循环被取消")
            raise

    async def _scan_once(self) -> None:
        """单次扫描"""
        # 拉取所有用户学习状态
        user_states = self._collect_user_states()
        if not user_states:
            return

        now = datetime.utcnow()
        for user_id, info in user_states.items():
            await self._maybe_nudge(user_id, info, now)

    def _collect_user_states(self) -> Dict[int, Dict[str, Any]]:
        """收集所有有学习状态的用户"""
        result: Dict[int, Dict[str, Any]] = {}
        try:
            from routes.ai_edu_websocket_routes import manager

            states = getattr(manager, "user_learning_states", {}) or {}
            for user_id, state in states.items():
                last_update = state.get("last_update")
                if not last_update:
                    continue
                result[user_id] = {
                    "last_update": last_update,
                    "tab_switch_frequency": state.get("tab_switch_frequency", 0),
                    "lesson_id": state.get("lesson_id"),
                    "progress": state.get("progress", 0),
                }
        except Exception as e:
            logger.debug(f"collect_user_states 异常: {e}")
        return result

    async def _maybe_nudge(
        self,
        user_id: int,
        info: Dict[str, Any],
        now: datetime,
    ) -> None:
        """根据状态判断是否需要 nudge"""
        last_update = info.get("last_update")
        if not last_update:
            return
        # last_update 是 datetime 或 ISO 字符串
        if isinstance(last_update, str):
            try:
                last_update_dt = datetime.fromisoformat(
                    last_update.replace("Z", "+00:00")
                )
            except ValueError:
                return
        else:
            last_update_dt = last_update

        idle_seconds = (now - last_update_dt.replace(tzinfo=None)).total_seconds()
        idle_days = idle_seconds / 86400

        # nudge 类型选择（按强度递增）
        nudge_type: Optional[str] = None
        if idle_days >= self.MISS_YOU_DAYS:
            nudge_type = "miss_you"
        elif idle_days >= self.COMEBACK_DAYS:
            nudge_type = "comeback"

        # 专注下降检测（tabSwitchFrequency 上升 >50%）
        prev = self._prev_focus.get(str(user_id), 0)
        cur = info.get("tab_switch_frequency", 0)
        focus_jumped = False
        if prev > 0 and cur > prev * 1.5:
            focus_jumped = True
        self._prev_focus[str(user_id)] = cur

        if focus_jumped and not nudge_type:
            nudge_type = "take_break"

        if not nudge_type:
            return

        # 频控
        cooldown_key = f"nudge:{nudge_type}:{user_id}"
        if not ai_teacher_live_settings.can_push(
            user_id, cooldown_key, "ai_teacher_nudge"
        ):
            return

        # 生成并发布
        days_idle = int(idle_days) if idle_days >= 1 else 1
        signal = NudgeSignal(
            nudge_type=nudge_type, days_idle=days_idle
        )
        try:
            payloads = await ai_teacher_recommender.recommend_for_nudge(
                user_id, signal
            )
            for payload in payloads:
                ai_teacher_live_bus.publish(payload)
            ai_teacher_live_settings.record_push(user_id, cooldown_key)
            logger.debug(
                f"📤 nudge 已推送 user={user_id} type={nudge_type} "
                f"days_idle={days_idle}"
            )
        except Exception as e:
            logger.error(f"nudge 生成失败: {e}", exc_info=True)


# 全局单例
ai_teacher_scheduler = AITeacherScheduler()