"""
【P3-D-1】AI 教师持久化 ORM 模型

承接 P3-B 的 FileJsonRepository（JSON 文件持久化），
将 7 个仓储数据迁移到 SQLAlchemy ORM + aiosqlite。

7 张表：
1. ai_teacher_profiles       - 学习画像（KV 模型）
2. ai_teacher_sessions       - 会话上下文（KV 模型）
3. ai_teacher_memories       - 长期记忆（KV 模型）
4. ai_teacher_personas       - AI 教师人格配置（KV 模型）
5. ai_teacher_live_settings  - 实时推送设置（KV 模型）
6. ai_teacher_event_history  - 全局事件历史（列表模型）
7. ai_teacher_user_history   - 按用户事件历史（列表模型）

KV 模型：用 user_id 作主键，value 用 JSON 存储
列表模型：用 id 作主键，user_id + created_at 索引，便于按时间裁剪

设计权衡：
- 5 张 KV 模型沿用 P3-B dict 接口（user_id → value）
- 2 张列表模型对应 P3-B 的 _event_history / _user_history（支持 max 上限裁剪）
"""

from datetime import datetime
from typing import Dict

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    String,
)

from utils.database import Base


# ==================== KV 模型（5 张） ====================


class AiTeacherKVRow(Base):
    """
    AI 教师持久化 KV 模型基类

    - 主键：user_id (str，最大 64 位）
    - value：JSON 序列化存储
    - updated_at：最后更新时间
    """

    __abstract__ = True

    user_id = Column(String(64), primary_key=True, index=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AiTeacherProfileRow(AiTeacherKVRow):
    """学习画像"""

    __tablename__ = "ai_teacher_profiles"


class AiTeacherSessionRow(AiTeacherKVRow):
    """会话上下文"""

    __tablename__ = "ai_teacher_sessions"


class AiTeacherMemoryRow(AiTeacherKVRow):
    """长期记忆"""

    __tablename__ = "ai_teacher_memories"


class AiTeacherPersonaRow(AiTeacherKVRow):
    """AI 教师人格配置"""

    __tablename__ = "ai_teacher_personas"


class AiTeacherLiveSettingRow(AiTeacherKVRow):
    """实时推送设置"""

    __tablename__ = "ai_teacher_live_settings"


# ==================== 列表模型（2 张） ====================


class AiTeacherEventHistoryRow(AiTeacherKVRow):
    """
    全局事件历史（200 条上限，KV 模型）

    - 主键：user_id 字段实际用作固定 key "records"
    - value：存整个 list[event]（调用方负责裁剪）
    - 兼容 P3-B 接口：FileJsonRepository.replace_all({"records": [...]})
    """

    __tablename__ = "ai_teacher_event_history"


class AiTeacherUserHistoryRow(AiTeacherKVRow):
    """
    按用户事件历史（每用户 50 条上限，KV 模型）

    - 主键：str(user_id)
    - value：list[event]
    - 兼容 P3-B 接口：FileJsonRepository.set(str(user_id), [...])
    """

    __tablename__ = "ai_teacher_user_history"


# ==================== 仓库 ↔ 表 映射 ====================
#
# 设计说明（【P3-D-1 修正】）：
# - 所有 7 张表均采用 KV 模型（user_id 主键 + JSON value）
# - event_history 使用固定 key "records" 存整个 list（与 P3-B 兼容）
# - user_history 使用 str(user_id) 作为 key 存 list[event]
# - 这样 SqlAlchemyRepository 只需实现一种 KV 接口，
#   与 FileJsonRepository 完全兼容，调用方零修改。

# 用于 factory.py 注册 ORM 实现到表的映射
ALL_TABLE_REGISTRY: Dict[str, type] = {
    "profiles": AiTeacherProfileRow,
    "sessions": AiTeacherSessionRow,
    "memories": AiTeacherMemoryRow,
    "personas": AiTeacherPersonaRow,
    "live_settings": AiTeacherLiveSettingRow,
    "event_history": AiTeacherEventHistoryRow,
    "user_history": AiTeacherUserHistoryRow,
}


def get_row_model_by_name(name: str) -> type:
    """
    根据仓库名获取 ORM 模型类

    支持：profiles / sessions / memories / personas / live_settings /
          event_history / user_history

    Raises:
        KeyError: 未知仓库名
    """
    if name not in ALL_TABLE_REGISTRY:
        raise KeyError(
            f"未知仓库名：{name}。"
            f"有效值：{list(ALL_TABLE_REGISTRY.keys())}"
        )
    return ALL_TABLE_REGISTRY[name]


__all__ = [
    "AiTeacherKVRow",
    "AiTeacherProfileRow",
    "AiTeacherSessionRow",
    "AiTeacherMemoryRow",
    "AiTeacherPersonaRow",
    "AiTeacherLiveSettingRow",
    "AiTeacherEventHistoryRow",
    "AiTeacherUserHistoryRow",
    "ALL_TABLE_REGISTRY",
    "get_row_model_by_name",
]