"""
Leaderboard and user statistics models.

Provides models for leaderboard records, user points, points transactions,
and aggregated user statistics for the iMato learning platform.
"""

import enum

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func as sql_func

from database.db import Base


class LeaderboardPeriod(str, enum.Enum):
    """Leaderboard period type enumeration."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"


class LeaderboardType(str, enum.Enum):
    """Leaderboard type enumeration."""

    TOTAL_POINTS = "total_points"
    STUDY_TIME = "study_time"
    COURSES_COMPLETED = "courses_completed"
    QUIZ_SCORE = "quiz_score"
    ACHIEVEMENTS = "achievements"
    CODE_EXECUTIONS = "code_executions"


class UserPoints(Base):
    """User points tracking model."""

    __tablename__ = "user_points"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="User ID",
    )
    total_points = Column(Integer, default=0, comment="Total accumulated points")
    available_points = Column(Integer, default=0, comment="Available points to spend")
    consumed_points = Column(Integer, default=0, comment="Consumed/spent points")

    points_breakdown = Column(
        JSON,
        default=dict,
        comment="Points breakdown by category (e.g. course, quiz, achievement)",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=sql_func.now())

    # Relationships
    user = relationship("User", backref="points")

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_points": self.total_points,
            "available_points": self.available_points,
            "consumed_points": self.consumed_points,
            "points_breakdown": self.points_breakdown,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


class PointsTransaction(Base):
    """Points transaction history model."""

    __tablename__ = "points_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="User ID",
    )
    transaction_type = Column(
        String(50),
        nullable=False,
        comment="Transaction type: earn, spend, expire, adjust",
    )
    points_amount = Column(Integer, nullable=False, comment="Points amount (positive for earn, negative for spend)")
    balance_after = Column(Integer, nullable=False, comment="Points balance after transaction")

    reason = Column(String(255), comment="Reason for the transaction")
    reference_type = Column(String(100), comment="Related entity type (e.g. course, quiz)")
    reference_id = Column(Integer, comment="Related entity ID")
    description = Column(String(500), comment="Human-readable description")
    extra_metadata = Column(JSON, default=dict, comment="Additional metadata")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", backref="points_transactions")

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "transaction_type": self.transaction_type,
            "points_amount": self.points_amount,
            "balance_after": self.balance_after,
            "reason": self.reason,
            "reference_type": self.reference_type,
            "reference_id": self.reference_id,
            "description": self.description,
            "extra_metadata": self.extra_metadata,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


class LeaderboardRecord(Base):
    """Leaderboard ranking records model."""

    __tablename__ = "leaderboard_records"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="User ID",
    )
    leaderboard_type = Column(
        String(50),
        nullable=False,
        comment="Leaderboard type: total_points, courses_completed, code_executions",
    )
    period = Column(
        String(20),
        nullable=False,
        comment="Period: daily, weekly, monthly, all_time",
    )

    period_start = Column(DateTime(timezone=True), comment="Period start datetime")
    period_end = Column(DateTime(timezone=True), comment="Period end datetime")

    rank = Column(Integer, comment="Current rank")
    score = Column(Float, comment="Score value")
    rank_change = Column(Integer, default=0, comment="Rank change from previous period")
    score_change = Column(Float, default=0.0, comment="Score change from previous period")

    recorded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_leaderboard_period", "period", "leaderboard_type", "period_start"),
        Index("idx_leaderboard_user_period", "user_id", "period", "leaderboard_type"),
        UniqueConstraint(
            "user_id", "leaderboard_type", "period", "period_start",
            name="uq_leaderboard_record",
        ),
    )

    # Relationships
    user = relationship("User", backref="leaderboard_records")

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "leaderboard_type": self.leaderboard_type,
            "period": self.period,
            "period_start": (
                self.period_start.isoformat() if self.period_start is not None else None
            ),
            "period_end": self.period_end.isoformat() if self.period_end is not None else None,
            "rank": self.rank,
            "score": self.score,
            "rank_change": self.rank_change,
            "score_change": self.score_change,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at is not None else None,
        }


class UserStatistics(Base):
    """Aggregated user statistics model."""

    __tablename__ = "user_statistics"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
        comment="User ID",
    )

    # Learning metrics
    total_study_time_minutes = Column(Integer, default=0, comment="Total study time (minutes)")
    courses_completed = Column(Integer, default=0, comment="Number of completed courses")
    quizzes_taken = Column(Integer, default=0, comment="Number of quizzes taken")
    average_quiz_score = Column(Float, default=0.0, comment="Average quiz score")
    code_executions = Column(Integer, default=0, comment="Number of code executions")
    achievements_unlocked = Column(Integer, default=0, comment="Number of unlocked achievements")

    # Streak metrics
    current_streak_days = Column(Integer, default=0, comment="Current consecutive learning days")
    longest_streak_days = Column(Integer, default=0, comment="Longest consecutive learning days")
    total_active_days = Column(Integer, default=0, comment="Total active days")
    last_active_date = Column(DateTime(timezone=True), comment="Last active date")

    # Timestamps
    updated_at = Column(DateTime(timezone=True), onupdate=sql_func.now())

    # Relationships
    user = relationship("User", backref="statistics")

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "total_study_time_minutes": self.total_study_time_minutes,
            "courses_completed": self.courses_completed,
            "quizzes_taken": self.quizzes_taken,
            "average_quiz_score": self.average_quiz_score,
            "code_executions": self.code_executions,
            "achievements_unlocked": self.achievements_unlocked,
            "current_streak_days": self.current_streak_days,
            "longest_streak_days": self.longest_streak_days,
            "total_active_days": self.total_active_days,
            "last_active_date": (
                self.last_active_date.isoformat() if self.last_active_date is not None else None
            ),
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }
