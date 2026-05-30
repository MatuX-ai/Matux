"""
AI-Edu-for-Kids 课程奖励数据模型
支持 AI 通识教育的游戏化积分激励系统
"""

from datetime import datetime
import enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship, validates

from utils.database import Base


class AchievementRarity(str, enum.Enum):
    """成就徽章稀有度"""

    COMMON = "common"  # 普通 🟢
    RARE = "rare"  # 稀有 🔵
    EPIC = "epic"  # 史诗 🟣
    LEGENDARY = "legendary"  # 传说 🔴
    MYTHIC = "mythic"  # 神话 💎


class RewardRuleType(str, enum.Enum):
    """奖励规则类型"""

    THEORY = "theory"  # 理论学习
    PRACTICE = "practice"  # 实践操作
    PROJECT = "project"  # 项目挑战
    ACHIEVEMENT = "achievement"  # 成就解锁
    STREAK = "streak"  # 连胜奖励
    SPECIAL = "special"  # 特殊贡献


class AIEduModule(Base):
    """AI 课程模块模型"""

    __tablename__ = "ai_edu_modules"

    id = Column(Integer, primary_key=True, index=True)
    module_code = Column(String(50), unique=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # 模块分类（对应五大核心模块）
    category = Column(
        String(50)
    )  # basic_concepts/data_perception/algorithms/ethics/interdisciplinary

    # 适用学段
    grade_ranges = Column(JSON)  # [{"min": 1, "max": 2}, {"min": 3, "max": 4}]

    # 课程配置
    expected_lessons = Column(Integer)  # 预期课时数
    expected_duration_minutes = Column(Integer)  # 总时长（分钟）

    # 前置要求
    prerequisites = Column(JSON)  # 前置课程 ID 列表

    # 状态
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    lessons = relationship(
        "AIEduLesson", back_populates="module", cascade="all, delete-orphan"
    )
    reward_rules = relationship("AIEduRewardRule", back_populates="module")


class AIEduLesson(Base):
    """AI 课程课时模型"""

    __tablename__ = "ai_edu_lessons"

    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("ai_edu_modules.id"), nullable=False)
    lesson_code = Column(String(50), unique=True, index=True)
    title = Column(String(200), nullable=False)
    subtitle = Column(String(200))

    # 课程内容
    content_type = Column(String(50))  # theory/practice/hybrid
    content_url = Column(String(500))  # 课件/视频 URL
    resources = Column(
        JSON
    )  # 资源列表 [{type: "video", url: "..."}, {type: "code", path: "..."}]

    # 教学目标
    learning_objectives = Column(JSON)  # 学习目标列表
    knowledge_points = Column(JSON)  # 知识点列表

    # 时间配置
    estimated_duration_minutes = Column(Integer)  # 预计时长

    # 评估配置
    has_quiz = Column(Boolean, default=False)
    quiz_passing_score = Column(Float, default=80.0)  # 及格线
    has_practice = Column(Boolean, default=False)
    practice_type = Column(String(50))  # python/scratch/ar_vr/hardware

    # 奖励配置
    base_points = Column(Integer, default=20)  # 基础积分
    bonus_conditions = Column(JSON)  # 奖励条件配置

    # 状态
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    module = relationship("AIEduModule", back_populates="lessons")
    progress_records = relationship("AIEduLearningProgress", back_populates="lesson")


class AIEduRewardRule(Base):
    """AI 课程奖励规则模型"""

    __tablename__ = "ai_edu_reward_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_code = Column(String(50), unique=True, index=True)
    rule_name = Column(String(100), nullable=False)
    description = Column(Text)

    # 规则分类
    rule_type = Column(Enum(RewardRuleType), nullable=False)
    module_id = Column(Integer, ForeignKey("ai_edu_modules.id"), nullable=True)

    # 积分配置
    base_points = Column(Integer, default=20)
    grade_multipliers = Column(
        JSON, default={"G1-G2": 1.0, "G3-G4": 1.2, "G5-G6": 1.5, "G7-G9": 2.0}
    )  # 学段系数

    # 质量系数配置
    quality_coefficients = Column(
        JSON,
        default={
            "excellent": 1.2,  # 优秀 (>90 分)
            "good": 1.1,  # 良好 (>80 分)
            "pass": 1.0,  # 及格 (>60 分)
        },
    )

    # 时间奖励配置
    time_bonus_enabled = Column(Boolean, default=False)
    standard_time_minutes = Column(Integer, nullable=True)
    time_bonus_rate = Column(Float, default=0.5)  # 每分钟奖励率

    # 连胜奖励配置
    streak_bonus_enabled = Column(Boolean, default=True)
    streak_multipliers = Column(
        JSON, default={3: 1.1, 5: 1.2, 10: 1.3, 20: 1.5, 30: 2.0}
    )

    # 关联成就
    achievement_id = Column(
        Integer, ForeignKey("ai_edu_achievements.id"), nullable=True
    )

    # 触发条件
    trigger_conditions = Column(
        JSON
    )  # [{field: "completion_rate", operator: ">=", value: 0.9}]

    # 优先级和冷却
    priority = Column(Integer, default=100)
    cooldown_seconds = Column(Integer, default=0)

    # 状态
    is_active = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    module = relationship("AIEduModule", back_populates="reward_rules")
    achievement = relationship("AIEduAchievement", back_populates="reward_rules")


class AIEduAchievement(Base):
    """AI 课程成就徽章模型"""

    __tablename__ = "ai_edu_achievements"

    id = Column(Integer, primary_key=True, index=True)
    achievement_code = Column(String(50), unique=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon_url = Column(String(255))

    # 稀有度
    rarity = Column(Enum(AchievementRarity), default=AchievementRarity.COMMON)

    # 解锁条件
    unlock_conditions = Column(
        JSON
    )  # [{type: "complete_course", count: 10, module_id: null}]

    # 奖励
    points_reward = Column(Integer, default=100)
    integral_reward = Column(Integer, default=0)
    special_rewards = Column(JSON)  # 特殊奖励 [{type: "badge", "name": "限定头像框"}]

    # 统计
    unlocked_count = Column(Integer, default=0)

    # 分类
    category = Column(String(50))  # learning/skill/special/streak

    # 状态
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    reward_rules = relationship("AIEduRewardRule", back_populates="achievement")
    user_achievements = relationship(
        "UserAIEduAchievement", back_populates="achievement"
    )


class UserAIEduAchievement(Base):
    """用户 AI 课程成就记录"""

    __tablename__ = "user_ai_edu_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(
        Integer, ForeignKey("ai_edu_achievements.id"), nullable=False
    )

    # 解锁信息
    unlocked_at = Column(DateTime, default=datetime.utcnow)
    progress_data = Column(JSON)  # 进度数据 {completed_courses: 5, target: 10}

    # 奖励发放
    points_claimed = Column(Boolean, default=False)
    claimed_at = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    achievement = relationship("AIEduAchievement", back_populates="user_achievements")


class AIEduLearningProgress(Base):
    """AI 课程学习进度模型"""

    __tablename__ = "ai_edu_learning_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("ai_edu_lessons.id"), nullable=False)

    # 进度信息
    progress_percentage = Column(Integer, default=0)  # 0-100
    status = Column(
        String(20), default="not_started"
    )  # not_started/in_progress/completed

    # 时间统计
    time_spent_seconds = Column(Integer, default=0)
    start_time = Column(DateTime, nullable=True)
    completion_time = Column(DateTime, nullable=True)
    last_accessed_time = Column(DateTime, default=datetime.utcnow)

    # 学习质量
    quiz_score = Column(Float, nullable=True)
    code_quality_score = Column(Float, nullable=True)
    attempt_count = Column(Integer, default=1)

    # 获得的奖励
    points_earned = Column(Integer, default=0)
    achievements_unlocked = Column(JSON, default=list)

    # 评价反馈
    user_rating = Column(Integer)  # 1-5 星
    feedback = Column(Text)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    lesson = relationship("AIEduLesson", back_populates="progress_records")


class AIEduPointsTransaction(Base):
    """AI 课程积分交易记录"""

    __tablename__ = "ai_edu_points_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 交易信息
    transaction_type = Column(String(50))  # earn/spend/bonus
    points_amount = Column(Integer, nullable=False)

    # 来源信息
    source_type = Column(String(50))  # course/practice/project/achievement/streak
    source_id = Column(Integer, nullable=True)  # 关联的课程/项目 ID
    source_description = Column(String(255))

    # 计算详情
    base_points = Column(Integer, default=0)
    grade_multiplier = Column(Float, default=1.0)
    quality_bonus = Column(Integer, default=0)
    streak_bonus = Column(Integer, default=0)
    final_points = Column(Integer)

    # 区块链信息
    blockchain_tx_hash = Column(String(100), nullable=True)
    block_number = Column(Integer, nullable=True)

    # 状态
    status = Column(String(20), default="pending")  # pending/completed/failed

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)


class AIEduStreakCounter(Base):
    """AI 课程连胜计数器"""

    __tablename__ = "ai_edu_streak_counters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 连胜类型
    streak_type = Column(String(50))  # daily_login/course_completion/practice_success

    # 计数信息
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    last_activity_date = Column(DateTime, nullable=True)

    # 奖励信息
    total_bonus_earned = Column(Integer, default=0)
    last_reward_date = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


from typing import Any, Dict, List, Optional

# 响应模型
from pydantic import BaseModel, Field


class RewardCalculationRequest(BaseModel):
    """奖励计算请求"""

    user_id: int = Field(..., description="用户 ID")
    rule_code: str = Field(..., description="规则代码")
    lesson_id: Optional[int] = Field(None, description="课程 ID")
    completion_data: Dict[str, Any] = Field(
        default_factory=dict, description="完成数据"
    )


class RewardCalculationResponse(BaseModel):
    """奖励计算响应"""

    base_points: int = Field(..., description="基础积分")
    grade_multiplier: float = Field(1.0, description="学段系数")
    quality_bonus: int = Field(0, description="质量奖金")
    streak_bonus: int = Field(0, description="连胜奖金")
    total_points: int = Field(..., description="总积分")
    breakdown: Dict[str, int] = Field(default_factory=dict, description="明细")


class IssueRewardRequest(BaseModel):
    """发放奖励请求"""

    user_id: int = Field(..., description="用户 ID")
    points: int = Field(..., description="积分数")
    source_type: str = Field(..., description="来源类型")
    source_id: Optional[int] = Field(None, description="来源ID")
    description: str = Field(..., description="描述")
