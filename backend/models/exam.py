"""
Exam Models - 测验系统数据模型

包含测验、题目、答题记录、作弊事件等核心模型
支持多种题型（单选、多选、判断、简答、编程题）
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from utils.database import Base


class QuestionType(str, enum.Enum):
    """题目类型"""
    SINGLE_CHOICE = "single_choice"       # 单选题
    MULTIPLE_CHOICE = "multiple_choice"   # 多选题
    TRUE_FALSE = "true_false"             # 判断题
    SHORT_ANSWER = "short_answer"         # 简答题
    CODING = "coding"                     # 编程题


class ExamDifficulty(str, enum.Enum):
    """测验难度"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    ADAPTIVE = "adaptive"  # 自适应难度


class ExamStatus(str, enum.Enum):
    """测验状态"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AttemptStatus(str, enum.Enum):
    """答题记录状态"""
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"
    TIMED_OUT = "timed_out"
    VOIDED = "voided"  # 因作弊作废


class CheatType(str, enum.Enum):
    """作弊类型"""
    SCREEN_SWITCH = "screen_switch"             # 切换屏幕
    TAB_SWITCH = "tab_switch"                   # 切换标签页
    TIME_ANOMALY = "time_anomaly"               # 答题时间异常
    COPY_PASTE = "copy_paste"                   # 复制粘贴
    MULTI_DEVICE = "multi_device"              # 多设备登录
    SUSPICIOUS_IP = "suspicious_ip"            # 可疑 IP
    KEYBOARD_SHORTCUT = "keyboard_shortcut"    # 可疑快捷键


# ============ 测验 ============


class Exam(Base):
    """测验"""
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="测验标题")
    description = Column(Text, nullable=True, comment="测验说明")
    course_id = Column(Integer, nullable=True, index=True, comment="关联课程 ID")
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    difficulty = Column(Enum(ExamDifficulty), default=ExamDifficulty.MEDIUM)
    status = Column(Enum(ExamStatus), default=ExamStatus.DRAFT)

    # 时间配置
    duration_minutes = Column(Integer, default=30, comment="考试时长（分钟）")
    start_time = Column(DateTime(timezone=True), nullable=True, comment="开始时间（null=立即开始）")
    end_time = Column(DateTime(timezone=True), nullable=True, comment="截止时间")
    time_warning_minutes = Column(Integer, default=5, comment="时间提醒（分钟）")

    # 评分配置
    passing_score = Column(Float, default=60.0, comment="及格分数")
    max_attempts = Column(Integer, default=1, comment="最大尝试次数")
    shuffle_questions = Column(Boolean, default=True, comment="是否随机题目顺序")
    shuffle_options = Column(Boolean, default=True, comment="是否随机选项顺序")
    show_result_immediately = Column(Boolean, default=False, comment="是否立即显示结果")

    # 防作弊配置
    anti_cheat_enabled = Column(Boolean, default=True, comment="是否启用防作弊")
    max_screen_switches = Column(Integer, default=3, comment="最大允许切换屏幕次数")
    min_answer_seconds = Column(Integer, default=3, comment="每题最少答题秒数")
    restrict_paste = Column(Boolean, default=True, comment="禁止粘贴")
    restrict_copy = Column(Boolean, default=True, comment="禁止复制")
    fullscreen_required = Column(Boolean, default=True, comment="需要全屏模式")

    # 统计
    total_questions = Column(Integer, default=0)
    total_score = Column(Float, default=100.0)
    attempt_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    attempts = relationship("ExamAttempt", back_populates="exam", cascade="all, delete-orphan")
    creator = relationship("User", backref="created_exams")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "course_id": self.course_id,
            "difficulty": self.difficulty.value if self.difficulty else None,
            "status": self.status.value if self.status else None,
            "duration_minutes": self.duration_minutes,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "passing_score": self.passing_score,
            "max_attempts": self.max_attempts,
            "shuffle_questions": self.shuffle_questions,
            "anti_cheat_enabled": self.anti_cheat_enabled,
            "total_questions": self.total_questions,
            "total_score": self.total_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============ 题目 ============


class Question(Base):
    """题目"""
    __tablename__ = "exam_questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    question_type = Column(Enum(QuestionType), nullable=False)
    title = Column(Text, nullable=False, comment="题目内容")
    description = Column(Text, nullable=True, comment="题目说明/提示")
    options = Column(JSON, nullable=True, comment="选项列表（JSON 数组）")
    correct_answer = Column(Text, nullable=True, comment="正确答案")
    score = Column(Float, default=10.0, comment="分值")
    order_index = Column(Integer, default=0, comment="排序序号")
    explanation = Column(Text, nullable=True, comment="答案解析")
    tags = Column(JSON, nullable=True, comment="标签（JSON 数组）")
    difficulty = Column(Enum(ExamDifficulty), default=ExamDifficulty.MEDIUM)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    exam = relationship("Exam", back_populates="questions")

    def to_dict(self, include_answer: bool = False) -> dict:
        result = {
            "id": self.id,
            "exam_id": self.exam_id,
            "question_type": self.question_type.value if self.question_type else None,
            "title": self.title,
            "description": self.description,
            "options": self.options,
            "score": self.score,
            "order_index": self.order_index,
            "explanation": self.explanation,
            "difficulty": self.difficulty.value if self.difficulty else None,
        }
        if include_answer:
            result["correct_answer"] = self.correct_answer
        return result


# ============ 答题记录 ============


class ExamAttempt(Base):
    """答题记录"""
    __tablename__ = "exam_attempts"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(AttemptStatus), default=AttemptStatus.IN_PROGRESS)

    # 答题数据
    answers = Column(JSON, nullable=True, comment="答题内容（JSON：question_id -> answer）")
    score = Column(Float, nullable=True, comment="得分")
    total_score = Column(Float, nullable=True, comment="总分")
    percentage = Column(Float, nullable=True, comment="百分比")

    # 时间记录
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    time_spent_seconds = Column(Integer, nullable=True, comment="耗时（秒）")

    # 设备/IP 记录
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_fingerprint = Column(String(255), nullable=True)

    # 评分信息
    auto_graded = Column(Boolean, default=False)
    graded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    graded_at = Column(DateTime(timezone=True), nullable=True)
    grader_notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    exam = relationship("Exam", back_populates="attempts")
    user = relationship("User", foreign_keys=[user_id], backref="exam_attempts")
    grader = relationship("User", foreign_keys=[graded_by])
    cheat_events = relationship("CheatEvent", back_populates="attempt", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "exam_id": self.exam_id,
            "user_id": self.user_id,
            "status": self.status.value if self.status else None,
            "score": self.score,
            "total_score": self.total_score,
            "percentage": self.percentage,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "time_spent_seconds": self.time_spent_seconds,
            "auto_graded": self.auto_graded,
            "cheat_events_count": len(self.cheat_events) if self.cheat_events else 0,
        }


# ============ 作弊事件 ============


class CheatEvent(Base):
    """作弊事件记录"""
    __tablename__ = "cheat_events"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    cheat_type = Column(Enum(CheatType), nullable=False)
    severity = Column(Integer, default=1, comment="严重程度 1-5")
    details = Column(JSON, nullable=True, comment="详细数据")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Relationships
    attempt = relationship("ExamAttempt", back_populates="cheat_events")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "attempt_id": self.attempt_id,
            "cheat_type": self.cheat_type.value if self.cheat_type else None,
            "severity": self.severity,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
