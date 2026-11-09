"""
【P3-B / P3-D 兼容层】AI 教师持久化层

P3-B：解决 ai_teacher_routes / live_settings / event_bus 中的 mock 存储技术债。
      通过 JSON 文件落盘避免重启丢数据。

P3-D-1：升级为 ORM + SQLite 双模式：
        - file backend（默认，向后兼容 P3-B 行为）
        - sql backend  （P3-D 新增，启用 SQLAlchemy ORM + aiosqlite）

设计目标（两阶段通用）：
1. **跨重启持久化**：避免重启丢数据
2. **进程内缓存**：内存读写，文件/ORM 后台刷新
4. **类型安全**：通过 dataclass 定义 schema，避免运行时 KeyError
5. **P3-D 向后兼容**：调用方代码（routes / services）零修改

模块组织：
- cache.repository.base       - Repository[T] 抽象接口
- cache.repository.file_json  - FileJsonRepository 实现（P3-B 迁移）
- cache.repository.sql        - SqlAlchemyRepository 实现（P3-D 新增）
- cache.repository.factory    - 工厂 + 全局单例
- cache.ai_teacher_persistence - 本模块，向后兼容 shim（保留历史 API 入口）

详见 docs/AI_TEACHER_PERSISTENCE_MIGRATION.md。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

# ==================== 向后兼容 re-export ====================
# 所有持久化操作都通过 cache.repository 抽象层
# 本模块保留 AITeacherProfile dataclass + register_persistence_hooks 兼容旧调用

from cache.repository import (
    FileJsonRepository,
    Repository,
    SqlAlchemyRepository,
    create_repository,
    flush_all_repos,
    get_event_history_repo,
    get_live_settings_repo,
    get_memories_repo,
    get_personas_repo,
    get_profiles_repo,
    get_sessions_repo,
    get_user_history_repo,
    reset_all_repos_for_testing,
)
import logging


# ==================== AI 教师画像 schema（向后兼容）====================


@dataclass
class AITeacherProfile:
    """AI 教师画像持久化条目（仅类型提示，不参与运行时持久化）"""

    user_id: str
    display_name: str
    grade_level: str
    age_group: str
    learning_style: str = "visual"
    preferred_content_type: str = "interactive"
    ability_dimensions: Dict[str, int] = field(default_factory=dict)
    interest_preferences: List[str] = field(default_factory=list)
    knowledge_mastery: Dict[str, float] = field(default_factory=dict)
    total_study_time_minutes: int = 0
    completed_courses_count: int = 0
    average_quiz_score: float = 0.0
    current_streak_days: int = 0
    longest_streak_days: int = 0
    weak_points: List[Dict[str, Any]] = field(default_factory=list)
    error_patterns: Dict[str, int] = field(default_factory=dict)
    attention_profile: Dict[str, Any] = field(default_factory=dict)
    emotional_states: List[Dict[str, Any]] = field(default_factory=list)
    learning_milestones: List[Dict[str, Any]] = field(default_factory=list)
    skill_tree: List[Dict[str, Any]] = field(default_factory=list)
    persona_seed: str = ""
    learning_goals: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """序列化为可落盘 dict"""
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "grade_level": self.grade_level,
            "age_group": self.age_group,
            "learning_style": self.learning_style,
            "preferred_content_type": self.preferred_content_type,
            "ability_dimensions": self.ability_dimensions,
            "interest_preferences": self.interest_preferences,
            "knowledge_mastery": self.knowledge_mastery,
            "total_study_time_minutes": self.total_study_time_minutes,
            "completed_courses_count": self.completed_courses_count,
            "average_quiz_score": self.average_quiz_score,
            "current_streak_days": self.current_streak_days,
            "longest_streak_days": self.longest_streak_days,
            "weak_points": self.weak_points,
            "error_patterns": self.error_patterns,
            "attention_profile": self.attention_profile,
            "emotional_states": self.emotional_states,
            "learning_milestones": self.learning_milestones,
            "skill_tree": self.skill_tree,
            "persona_seed": self.persona_seed,
            "learning_goals": self.learning_goals,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ==================== FastAPI lifespan 钩子 ====================

_hooks_registered = False


def register_persistence_hooks(app: Any) -> None:
    """
    注册 FastAPI 关闭钩子

    在 FastAPI lifespan 中调用，确保：
    - 启动时各实现从磁盘/数据库加载所有数据
    - 关闭时强制 flush 避免数据丢失

    用法（在 main.py lifespan 中）：
        from cache.ai_teacher_persistence import register_persistence_hooks
        register_persistence_hooks(app)

    注意：
    - P3-B 旧实现使用 @app.on_event("shutdown")
    - P3-D 推荐在 lifespan 上下文中直接调用 flush_all_repos()
    """
    global _hooks_registered
    if _hooks_registered:
        return
    _hooks_registered = True

    @app.on_event("shutdown")
    def _shutdown_hook() -> None:  # type: ignore[misc]
        from cache.ai_teacher_persistence import logger  # type: ignore
        logger.info("AI 教师持久化层：关闭前 flush")
        flush_all_repos()


# ==================== 兼容性别名 ====================

# 旧字段名（保留向后兼容，让重构期不破坏旧调用）
PROFILES_REPO = property(lambda: get_profiles_repo())
SESSIONS_REPO = property(lambda: get_sessions_repo())
MEMORIES_REPO = property(lambda: get_memories_repo())
PERSONAS_REPO = property(lambda: get_personas_repo())
LIVE_SETTINGS_REPO = property(lambda: get_live_settings_repo())
EVENT_HISTORY_REPO = property(lambda: get_event_history_repo())
USER_HISTORY_REPO = property(lambda: get_user_history_repo())


# ==================== 模块 logger ====================


logger = logging.getLogger(__name__)


__all__ = [
    # 抽象接口
    "Repository",
    # 实现类（FileJsonRepository / SqlAlchemyRepository 可直接导入）
    "FileJsonRepository",
    "SqlAlchemyRepository",
    # 全局单例 getter
    "get_profiles_repo",
    "get_sessions_repo",
    "get_memories_repo",
    "get_personas_repo",
    "get_live_settings_repo",
    "get_event_history_repo",
    "get_user_history_repo",
    # 工厂
    "create_repository",
    # 工具
    "flush_all_repos",
    "reset_all_repos_for_testing",
    "register_persistence_hooks",
    # 数据类
    "AITeacherProfile",
    # 兼容属性
    "PROFILES_REPO",
    "SESSIONS_REPO",
    "MEMORIES_REPO",
    "PERSONAS_REPO",
    "LIVE_SETTINGS_REPO",
    "EVENT_HISTORY_REPO",
    "USER_HISTORY_REPO",
]