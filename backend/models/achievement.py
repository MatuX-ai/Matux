"""
AI-Edu 成就系统数据模型
支持成就定义、用户成就追踪、徽章展示等功能
"""

import enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.db import Base


class AchievementCategory(str, enum.Enum):
    """成就分类枚举"""

    LEARNING = "learning"  # 学习相关
    CODING = "coding"  # 编程相关
    QUIZ = "quiz"  # 测验相关
    SOCIAL = "social"  # 社交相关
    SPECIAL = "special"  # 特殊成就


class AchievementType(str, enum.Enum):
    """成就类型枚举"""

    CUMULATIVE = "cumulative"  # 累计型（如学习 10 小时）
    SINGLE = "single"  # 单次型（如一次测验满分）
    SEQUENCE = "sequence"  # 序列型（如连续 7 天打卡）
    HIDDEN = "hidden"  # 隐藏成就


class Achievement(Base):
    """成就定义表"""

    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 基本信息
    name = Column(String(100), nullable=False, index=True, comment="成就名称")
    description = Column(String(500), nullable=False, comment="成就描述")
    category = Column(SQLEnum(AchievementCategory), nullable=False, comment="成就分类")
    achievement_type = Column(
        SQLEnum(AchievementType), nullable=False, comment="成就类型"
    )

    # 徽章配置
    badge_icon = Column(String(255), nullable=False, comment="徽章图标 URL/路径")
    badge_color = Column(String(20), default="#FFD700", comment="徽章颜色（十六进制）")
    badge_rarity = Column(
        String(20), default="common", comment="稀有度：common, rare, epic, legendary"
    )

    # 解锁条件（JSON 格式存储复杂条件）
    unlock_condition = Column(JSON, nullable=False, comment="解锁条件配置")
    # 示例结构:
    # {
    #     "type": "cumulative",
    #     "metric": "study_time_minutes",
    #     "threshold": 600,
    #     "operator": ">="
    # }

    # 奖励配置
    points_reward = Column(Integer, default=0, comment="积分奖励")
    bonus_multiplier = Column(Float, default=1.0, comment="奖励倍数（用于特殊成就）")

    # 显示控制
    is_hidden = Column(Boolean, default=False, comment="是否隐藏成就（完成前不可见）")
    is_active = Column(Boolean, default=True, comment="是否启用")
    display_order = Column(Integer, default=0, comment="显示顺序")

    # 统计信息
    total_unlocked = Column(Integer, default=0, comment="总解锁人数")
    unlock_rate = Column(Float, default=0.0, comment="解锁率（百分比）")

    # 时间戳
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), comment="更新时间"
    )

    # 关系
    user_achievements = relationship(
        "UserAchievement", back_populates="achievement", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_achievement_category", "category"),
        Index("idx_achievement_type", "achievement_type"),
        Index("idx_achievement_active", "is_active"),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "achievement_type": self.achievement_type.value,
            "badge_icon": self.badge_icon,
            "badge_color": self.badge_color,
            "badge_rarity": self.badge_rarity,
            "unlock_condition": self.unlock_condition,
            "points_reward": self.points_reward,
            "bonus_multiplier": self.bonus_multiplier,
            "is_hidden": self.is_hidden,
            "is_active": self.is_active,
            "display_order": self.display_order,
            "total_unlocked": self.total_unlocked,
            "unlock_rate": self.unlock_rate,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


class UserAchievement(Base):
    """用户成就表（记录用户解锁的成就）"""

    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联信息
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="用户 ID"
    )
    achievement_id = Column(
        Integer,
        ForeignKey("achievements.id"),
        nullable=False,
        index=True,
        comment="成就 ID",
    )

    # 进度追踪
    progress = Column(Float, default=0.0, comment="完成进度（0-100）")
    current_value = Column(Integer, default=0, comment="当前值")
    target_value = Column(Integer, nullable=False, comment="目标值")

    # 状态
    is_unlocked = Column(Boolean, default=False, index=True, comment="是否已解锁")
    is_claimed = Column(Boolean, default=False, comment="是否已领取奖励")

    # 解锁信息
    unlocked_at = Column(DateTime(timezone=True), nullable=True, comment="解锁时间")
    notification_sent = Column(Boolean, default=False, comment="是否已发送通知")

    # 额外数据
    extra_metadata = Column("metadata", JSON, default=dict, comment="额外元数据")
    # 示例：第一次完成的课程 ID、具体时间等

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    achievement = relationship("Achievement", back_populates="user_achievements")
    user = relationship("User", backref="user_achievements")

    # 唯一约束（同一用户同一成就只能有一条记录）
    __table_args__ = (
        Index("idx_user_achievement_unique", "user_id", "achievement_id", unique=True),
        Index("idx_user_achievement_status", "user_id", "is_unlocked"),
    )

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "achievement_id": self.achievement_id,
            "progress": self.progress,
            "current_value": self.current_value,
            "target_value": self.target_value,
            "is_unlocked": self.is_unlocked,
            "is_claimed": self.is_claimed,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at is not None else None,
            "notification_sent": self.notification_sent,
            "extra_metadata": self.extra_metadata,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
            # 包含成就详情
            "achievement": self.achievement.to_dict() if self.achievement else None,
        }


class AchievementProgress(Base):
    """成就进度临时表（用于实时追踪，定期同步到 UserAchievement）"""

    __tablename__ = "achievement_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联信息
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(
        Integer, ForeignKey("achievements.id"), nullable=False, index=True
    )

    # 指标数据
    metric_name = Column(
        String(100), nullable=False, comment="指标名称（如 study_time_minutes）"
    )
    metric_value = Column(Integer, default=0, comment="指标值")

    # 时间维度
    period_type = Column(
        String(20),
        default="all_time",
        comment="周期类型：daily, weekly, monthly, all_time",
    )
    period_start = Column(DateTime(timezone=True), comment="周期开始时间")
    period_end = Column(DateTime(timezone=True), comment="周期结束时间")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 唯一约束
    __table_args__ = (
        Index(
            "idx_progress_user_metric",
            "user_id",
            "metric_name",
            "period_type",
            unique=True,
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "achievement_id": self.achievement_id,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "period_type": self.period_type,
            "period_start": (
                self.period_start.isoformat() if self.period_start is not None else None
            ),
            "period_end": self.period_end.isoformat() if self.period_end is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


# ==================== 预定义成就模板 ====================

DEFAULT_ACHIEVEMENTS = [
    # 学习相关成就
    {
        "name": "勤奋学习者",
        "description": "累计学习时长达到 10 小时",
        "category": "learning",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/diligent_learner.png",
        "badge_color": "#FFD700",
        "badge_rarity": "common",
        "unlock_condition": {
            "type": "cumulative",
            "metric": "study_time_minutes",
            "threshold": 600,
            "operator": ">=",
        },
        "points_reward": 100,
        "is_hidden": False,
    },
    {
        "name": "持之以恒",
        "description": "连续学习 7 天",
        "category": "learning",
        "achievement_type": "sequence",
        "badge_icon": "/badges/consistent.png",
        "badge_color": "#C0C0C0",
        "badge_rarity": "rare",
        "unlock_condition": {
            "type": "sequence",
            "metric": "consecutive_days",
            "threshold": 7,
            "operator": ">=",
        },
        "points_reward": 200,
        "is_hidden": False,
    },
    # 编程相关成就
    {
        "name": "代码新手",
        "description": "第一次成功执行代码",
        "category": "coding",
        "achievement_type": "single",
        "badge_icon": "/badges/first_code.png",
        "badge_color": "#CD7F32",
        "badge_rarity": "common",
        "unlock_condition": {
            "type": "single",
            "event": "code_executed_successfully",
            "count": 1,
        },
        "points_reward": 50,
        "is_hidden": False,
    },
    {
        "name": "调试大师",
        "description": "成功解决 100 个代码错误",
        "category": "coding",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/debug_master.png",
        "badge_color": "#E5E4E2",
        "badge_rarity": "epic",
        "unlock_condition": {
            "type": "cumulative",
            "metric": "errors_fixed",
            "threshold": 100,
            "operator": ">=",
        },
        "points_reward": 500,
        "is_hidden": False,
    },
    # 测验相关成就
    {
        "name": "学霸附体",
        "description": "单次测验获得满分",
        "category": "quiz",
        "achievement_type": "single",
        "badge_icon": "/badges/perfect_quiz.png",
        "badge_color": "#FFD700",
        "badge_rarity": "rare",
        "unlock_condition": {
            "type": "single",
            "event": "quiz_perfect_score",
            "condition": {"score": 100},
        },
        "points_reward": 150,
        "is_hidden": False,
    },
    # 隐藏成就
    {
        "name": "深夜程序员",
        "description": "？？？",
        "category": "special",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/night_coder.png",
        "badge_color": "#8B00FF",
        "badge_rarity": "legendary",
        "unlock_condition": {
            "type": "cumulative",
            "metric": "coding_after_midnight",
            "threshold": 10,
            "operator": ">=",
        },
        "points_reward": 300,
        "is_hidden": True,
    },
]
