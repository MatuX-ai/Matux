"""
【P3-B】AI 教师实时推送设置

用户级配置：
- 启用总开关
- 3 类事件独立开关（celebration / suggestion / nudge）
- 勿扰时段
- 频控（每小时上限 + 同一 cooldownKey 冷却）

数据存储：【P3-B 修复】从进程内 dict 迁移到持久化仓储 (cache.ai_teacher_persistence)
- 设置：FileJsonRepository（JSON 文件）
- 推送日志 / 冷却记录：进程内 dict（高频写入，不必每次落盘）

P3-D 计划：将 live_settings / push_log / cooldowns 拆为 SQLAlchemy 三张表，
         详见 cache.ai_teacher_persistence 文档。
"""

import logging
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Optional

from cache.ai_teacher_persistence import get_live_settings_repo

logger = logging.getLogger(__name__)


@dataclass
class LiveSettings:
    """AI 教师实时推送用户级设置"""

    user_id: int = 0
    enabled: bool = True
    celebration_enabled: bool = True
    suggestion_enabled: bool = True
    nudge_enabled: bool = True
    # 勿扰时段（24h 制）
    dnd_start_hour: int = 22
    dnd_end_hour: int = 8
    # 频控
    max_per_hour: int = 3
    min_interval_seconds: int = 300  # 同一 cooldownKey 冷却 5 分钟
    updated_at: str = field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    def to_dict(self) -> Dict:
        return asdict(self)


class AITeacherLiveSettingsService:
    """
    用户级 AI 教师实时推送设置服务

    接口：
    - get_settings(user_id)
    - update_settings(user_id, partial)
    - is_in_dnd(user_id, now)
    - can_push(user_id, cooldown_key, event_type, now)

    【P3-B 修复】设置数据从进程内 dict 改为持久化仓储：
    - 重启后用户设置不丢失
    - 多进程部署时可共享（写竞争由 RLock 保护）
    - 频控记录（push_log / cooldowns）仍为进程内（高频短生命周期）
    """

    def __init__(self):
        # 【P3-B 修复】使用持久化仓储替代进程内 dict
        self._store_repo = get_live_settings_repo()
        # 推送频控记录：user_id → [timestamp, ...]
        # 保持进程内（高频写入 + 短生命周期，不必每次落盘）
        self._push_log: Dict[int, list] = {}
        # 冷却记录：user_id → {cooldown_key: timestamp}
        self._cooldowns: Dict[str, float] = {}
        self._lock = threading.RLock()

    def get_settings(self, user_id: int) -> LiveSettings:
        """获取用户设置（不存在则返回默认）"""
        with self._lock:
            key = str(user_id)
            existing = self._store_repo.get(key)
            if existing is None:
                settings = LiveSettings(user_id=user_id)
                self._store_repo.set(key, settings.to_dict())
                return settings
            # 从 dict 重建 dataclass（保留类型安全）
            return LiveSettings(**existing)

    def update_settings(
        self, user_id: int, partial: Dict
    ) -> LiveSettings:
        """更新设置（仅更新提供的字段）"""
        with self._lock:
            current = self.get_settings(user_id)
            allowed_keys = {
                "enabled",
                "celebration_enabled",
                "suggestion_enabled",
                "nudge_enabled",
                "dnd_start_hour",
                "dnd_end_hour",
                "max_per_hour",
                "min_interval_seconds",
            }
            for k, v in partial.items():
                if k in allowed_keys:
                    setattr(current, k, v)
            current.updated_at = datetime.utcnow().isoformat()
            # 【P3-B 修复】持久化写入
            self._store_repo.set(str(user_id), current.to_dict())
            return current

    def is_in_dnd(self, user_id: int, now: Optional[datetime] = None) -> bool:
        """判断当前是否在用户勿扰时段"""
        settings = self.get_settings(user_id)
        if not settings.enabled:
            return True
        now = now or datetime.now()
        hour = now.hour
        start = settings.dnd_start_hour
        end = settings.dnd_end_hour
        if start == end:
            return False
        if start < end:
            # 例如 9-18
            return start <= hour < end
        # 跨夜，例如 22-8
        return hour >= start or hour < end

    def is_type_enabled(self, user_id: int, event_type: str) -> bool:
        """判断某类型事件是否对该用户启用"""
        s = self.get_settings(user_id)
        if event_type == "ai_teacher_celebration":
            return s.celebration_enabled
        if event_type == "ai_teacher_suggestion":
            return s.suggestion_enabled
        if event_type == "ai_teacher_nudge":
            return s.nudge_enabled
        return True

    def can_push(
        self,
        user_id: int,
        cooldown_key: str,
        event_type: str,
        now: Optional[datetime] = None,
    ) -> bool:
        """
        综合判断是否可推送：
        1. 总开关 / 类型开关
        2. 勿扰时段
        3. 每小时上限
        4. 同一 cooldownKey 冷却
        """
        if not self.is_type_enabled(user_id, event_type):
            return False
        if self.is_in_dnd(user_id, now):
            return False

        now = now or datetime.now()
        s = self.get_settings(user_id)
        ts_now = now.timestamp()

        with self._lock:
            # 冷却检查
            full_key = f"{user_id}:{cooldown_key}"
            last_ts = self._cooldowns.get(full_key)
            if last_ts and ts_now - last_ts < s.min_interval_seconds:
                return False

            # 每小时上限
            log = self._push_log.setdefault(user_id, [])
            # 清理 1 小时以外的
            cutoff = ts_now - 3600
            log[:] = [t for t in log if t >= cutoff]
            if len(log) >= s.max_per_hour:
                return False

            return True

    def record_push(
        self,
        user_id: int,
        cooldown_key: str,
        now: Optional[datetime] = None,
    ) -> None:
        """记录一次推送（用于下次频控判断）"""
        now = now or datetime.now()
        ts_now = now.timestamp()
        with self._lock:
            full_key = f"{user_id}:{cooldown_key}"
            self._cooldowns[full_key] = ts_now
            log = self._push_log.setdefault(user_id, [])
            log.append(ts_now)
            cutoff = ts_now - 3600
            log[:] = [t for t in log if t >= cutoff]

    def clear(self) -> None:
        """清空所有（测试）"""
        with self._lock:
            self._store_repo.clear()
            self._push_log.clear()
            self._cooldowns.clear()


# 全局单例
ai_teacher_live_settings = AITeacherLiveSettingsService()