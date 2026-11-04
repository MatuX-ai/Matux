"""
AI-Edu intelligent recommendation system data models
Supports user profiles, course features, recommendation records, etc.
"""

import enum
from datetime import datetime

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
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from utils.database import Base


class LearningStyle(str, enum.Enum):
    """Learning style enumeration"""

    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING = "reading"


class SkillLevel(str, enum.Enum):
    """Skill level enumeration"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class UserLearningProfile(Base):
    """User learning profile table"""

    __tablename__ = "user_learning_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Basic info
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
        comment="User ID",
    )
    grade_level = Column(String(20), comment="Grade level (e.g. G1-G12)")
    age_group = Column(String(20), comment="Age group (e.g. 6-8, 9-12)")

    # Learning style
    learning_style = Column(
        SQLEnum(LearningStyle), default=LearningStyle.VISUAL, comment="Learning style"
    )
    preferred_content_type = Column(
        String(50), default="video", comment="Preferred content type (video/text/interactive)"
    )

    # Ability dimensions (JSON multi-dimensional assessment)
    ability_dimensions = Column(JSON, default=dict, comment="Ability dimension assessment")

    # Interest preferences (JSON)
    interest_preferences = Column(JSON, default=list, comment="Interest preference list")

    # Knowledge mastery (JSON)
    knowledge_mastery = Column(JSON, default=dict, comment="Knowledge point mastery")

    # Learning statistics
    total_study_time_minutes = Column(Integer, default=0, comment="Total study time (minutes)")
    completed_courses_count = Column(Integer, default=0, comment="Completed courses count")
    average_quiz_score = Column(Float, default=0.0, comment="Average quiz score")
    current_streak_days = Column(Integer, default=0, comment="Current consecutive study days")
    longest_streak_days = Column(Integer, default=0, comment="Longest consecutive study days")

    # Learning goals
    learning_goals = Column(JSON, default=list, comment="Learning goals list")

    # Recommendation weights config (JSON)
    recommendation_weights = Column(JSON, default=dict, comment="Recommendation algorithm weights")

    # Behavior-oriented fields consumed by ai_service.recommendation_service
    learning_preferences = Column(
        JSON, default=dict, comment="Learning preference config"
    )
    skill_levels = Column(
        JSON, default=dict, comment="Skill level map (knowledge point -> level)"
    )
    interests = Column(JSON, default=list, comment="Interest list")
    learning_history_vector = Column(
        JSON, default=list, comment="Learning history feature vector"
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_updated = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="Last profile update time",
    )

    # Relationships
    user = relationship("User", backref="learning_profile")

    # Indexes
    __table_args__ = (
        Index("idx_user_profile_user", "user_id"),
        Index("idx_user_profile_grade", "grade_level"),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "grade_level": self.grade_level,
            "age_group": self.age_group,
            "learning_style": (
                self.learning_style.value if self.learning_style is not None else None
            ),
            "preferred_content_type": self.preferred_content_type,
            "ability_dimensions": self.ability_dimensions,
            "interest_preferences": self.interest_preferences,
            "knowledge_mastery": self.knowledge_mastery,
            "total_study_time_minutes": self.total_study_time_minutes,
            "completed_courses_count": self.completed_courses_count,
            "average_quiz_score": self.average_quiz_score,
            "current_streak_days": self.current_streak_days,
            "longest_streak_days": self.longest_streak_days,
            "learning_goals": self.learning_goals,
            "recommendation_weights": self.recommendation_weights,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


class CourseFeature(Base):
    """Course feature table"""

    __tablename__ = "course_features"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Association info
    course_id = Column(Integer, nullable=False, index=True, comment="Course ID")
    lesson_id = Column(Integer, nullable=True, comment="Lesson ID (optional)")

    # Difficulty tags
    difficulty_level = Column(Integer, default=1, comment="Difficulty level (1-5)")
    difficulty_description = Column(String(100), comment="Difficulty description")

    # Knowledge point tags
    knowledge_points = Column(JSON, default=list, comment="Knowledge point tag list")

    # Skill categories
    skill_categories = Column(JSON, default=list, comment="Skill category list")

    # Prerequisites
    prerequisites = Column(JSON, default=list, comment="Prerequisite course ID list")

    # Next courses
    next_courses = Column(JSON, default=list, comment="Next recommended course ID list")

    # Content features
    content_type = Column(
        String(50), default="video", comment="Content type (video/text/interactive/mixed)"
    )
    estimated_duration_minutes = Column(Integer, default=30, comment="Estimated duration (minutes)")
    language = Column(String(20), default="zh-CN", comment="Language")

    # Quality metrics
    average_rating = Column(Float, default=0.0, comment="Average rating (0-5)")
    completion_rate = Column(Float, default=0.0, comment="Completion rate (0-1)")
    student_count = Column(Integer, default=0, comment="Student count")

    # Popular tags
    tags = Column(JSON, default=list, comment="Tag list")

    # Metadata
    course_metadata = Column(JSON, default=dict, comment="Additional metadata")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_course_feature_course", "course_id"),
        Index("idx_course_feature_difficulty", "difficulty_level"),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "lesson_id": self.lesson_id,
            "difficulty_level": self.difficulty_level,
            "difficulty_description": self.difficulty_description,
            "knowledge_points": self.knowledge_points,
            "skill_categories": self.skill_categories,
            "prerequisites": self.prerequisites,
            "next_courses": self.next_courses,
            "content_type": self.content_type,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "language": self.language,
            "average_rating": self.average_rating,
            "completion_rate": self.completion_rate,
            "student_count": self.student_count,
            "tags": self.tags,
            "metadata": self.course_metadata,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


class RecommendationAlgorithm(str, enum.Enum):
    """Recommendation algorithm type enumeration"""

    COLLABORATIVE_FILTERING = "collaborative_filtering"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"
    POPULARITY = "popularity"
    KNOWLEDGE_GRAPH = "knowledge_graph"


class RecommendationRecord(Base):
    """Recommendation record table (for tracking recommendation effectiveness and A/B testing)"""

    __tablename__ = "recommendation_records"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Association info
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="User ID"
    )
    course_id = Column(Integer, nullable=False, index=True, comment="Recommended course ID")

    # Recommendation algorithm info
    algorithm_type = Column(
        SQLEnum(RecommendationAlgorithm), nullable=False, comment="Recommendation algorithm type"
    )
    recommendation_score = Column(Float, default=0.0, comment="Recommendation score (0-1)")

    # Recommendation reason (JSON)
    reason = Column(JSON, default=dict, comment="Recommendation reason")

    # Recommendation context
    context = Column(JSON, default=dict, comment="Recommendation context info")

    # User feedback
    user_clicked = Column(Boolean, default=False, index=True, comment="User clicked")
    user_completed = Column(Boolean, default=False, comment="User completed course")
    user_rating = Column(Integer, comment="User rating (1-5)")
    feedback_text = Column(Text, comment="User text feedback")

    # Timestamps
    clicked_at = Column(DateTime(timezone=True), nullable=True, comment="Click time")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="Completion time")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    # 注：RecommendationRecord 与 UserLearningProfile 之间没有直接外键
    # （前者只持有指向 users.id 的 user_id），因此不建立 ORM relationship。

    # Indexes
    __table_args__ = (
        Index("idx_recommendation_user_course", "user_id", "course_id", unique=False),
        Index("idx_recommendation_algorithm", "algorithm_type"),
        Index("idx_recommendation_clicked", "user_clicked"),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "algorithm_type": self.algorithm_type.value,
            "recommendation_score": self.recommendation_score,
            "reason": self.reason,
            "context": self.context,
            "user_clicked": self.user_clicked,
            "user_completed": self.user_completed,
            "user_rating": self.user_rating,
            "feedback_text": self.feedback_text,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at is not None else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at is not None else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


class LearningRecord(Base):
    """User learning record table (per-lesson learning behavior log)"""

    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Association info
    user_id = Column(Integer, nullable=False, index=True, comment="User ID")
    course_id = Column(Integer, nullable=False, index=True, comment="Course ID")
    lesson_id = Column(Integer, nullable=True, index=True, comment="Lesson ID (optional)")

    # Learning behavior
    progress = Column(Float, default=0.0, comment="Learning progress (0-1)")
    time_spent = Column(Integer, default=0, comment="Time spent (minutes)")
    completion_status = Column(
        String(20),
        default="in_progress",
        index=True,
        comment="Completion status (in_progress/completed)",
    )

    # Ratings
    difficulty_rating = Column(Integer, comment="Difficulty rating (1-5)")
    interest_rating = Column(Integer, comment="Interest rating (1-5)")

    # Timestamps
    timestamp = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        index=True,
        comment="Event time",
    )

    # Indexes
    __table_args__ = (
        Index("idx_learning_record_user_course", "user_id", "course_id"),
        Index("idx_learning_record_user_status", "user_id", "completion_status"),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "lesson_id": self.lesson_id,
            "progress": self.progress,
            "time_spent": self.time_spent,
            "completion_status": self.completion_status,
            "difficulty_rating": self.difficulty_rating,
            "interest_rating": self.interest_rating,
            "timestamp": self.timestamp.isoformat() if self.timestamp is not None else None,
        }


class RecommendationFeedback(Base):
    """Recommendation feedback table (collected from real-time user actions)"""

    __tablename__ = "recommendation_feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Association info
    user_id = Column(Integer, nullable=False, index=True, comment="User ID")
    recommended_course_id = Column(
        String(64), nullable=True, index=True, comment="Recommended course ID"
    )

    # Feedback payload
    feedback_type = Column(
        String(50), nullable=False, index=True, comment="Feedback type"
    )
    context = Column(JSON, default=dict, comment="Feedback context")

    # Timestamps
    timestamp = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        index=True,
        comment="Feedback time",
    )

    # Indexes
    __table_args__ = (
        Index("idx_recommendation_feedback_user_type", "user_id", "feedback_type"),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "recommended_course_id": self.recommended_course_id,
            "feedback_type": self.feedback_type,
            "context": self.context,
            "timestamp": self.timestamp.isoformat() if self.timestamp is not None else None,
        }


class PretrainedModel(Base):
    """Pretrained model table (transfer learning / model compression registry)"""

    __tablename__ = "pretrained_models"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Model identity
    model_name = Column(String(100), nullable=False, index=True, comment="Model name")
    model_version = Column(String(50), nullable=False, comment="Model version")
    base_model = Column(String(100), comment="Base model")
    dataset_source = Column(String(200), comment="Training dataset source")

    # Training state
    training_status = Column(
        String(20),
        default="pending",
        index=True,
        comment="Training status (pending/training/completed/failed)",
    )
    training_progress = Column(Float, default=0.0, comment="Training progress (0-100)")

    # Model artifacts
    model_path = Column(String(500), comment="Model storage path")
    model_size = Column(Integer, default=0, comment="Model size (bytes)")
    compression_method = Column(String(50), comment="Compression method")
    compression_ratio = Column(Float, comment="Compression ratio")

    # Evaluation metrics
    accuracy_before = Column(Float, comment="Accuracy before transfer learning")
    accuracy_after = Column(Float, comment="Accuracy after transfer learning")

    # Extra info
    metadata_info = Column(JSON, default=dict, comment="Additional metadata")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index("idx_pretrained_model_status", "training_status", "created_at"),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "base_model": self.base_model,
            "dataset_source": self.dataset_source,
            "training_status": self.training_status,
            "training_progress": self.training_progress,
            "model_path": self.model_path,
            "model_size": self.model_size,
            "compression_method": self.compression_method,
            "compression_ratio": self.compression_ratio,
            "accuracy_before": self.accuracy_before,
            "accuracy_after": self.accuracy_after,
            "metadata_info": self.metadata_info,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


class ColdStartRecommendationLog(Base):
    """Cold start recommendation log table (audit trail for new-user recommendations)"""

    __tablename__ = "cold_start_recommendation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Association info
    user_id = Column(Integer, nullable=False, index=True, comment="User ID")
    model_id = Column(
        Integer, nullable=True, index=True, comment="Pretrained model ID"
    )

    # Recommendation payload
    recommended_courses = Column(
        JSON, default=list, comment="Recommended course list"
    )
    coverage_score = Column(
        Float, default=0.0, comment="Recommendation coverage score"
    )

    # Metrics
    response_time_ms = Column(Integer, default=0, comment="Response time (milliseconds)")
    is_cold_start = Column(
        Integer, default=1, comment="Whether it is a cold start recommendation"
    )

    # Timestamps
    recommendation_timestamp = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        index=True,
        comment="Recommendation time",
    )

    # Indexes
    __table_args__ = (
        Index("idx_cold_start_log_user_model", "user_id", "model_id"),
    )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "model_id": self.model_id,
            "recommended_courses": self.recommended_courses,
            "coverage_score": self.coverage_score,
            "response_time_ms": self.response_time_ms,
            "is_cold_start": self.is_cold_start,
            "recommendation_timestamp": (
                self.recommendation_timestamp.isoformat()
                if self.recommendation_timestamp is not None
                else None
            ),
        }


# ==================== Helper functions ====================


def calculate_user_similarity(profile1: dict, profile2: dict) -> float:
    """
    Calculate similarity between two user profiles (simplified cosine similarity)
    Returns:
        Similarity score (0-1)
    """
    features = []

    # Interest preference similarity
    interests1 = set(
        i.get("category") for i in profile1.get("interest_preferences", [])
    )
    interests2 = set(
        i.get("category") for i in profile2.get("interest_preferences", [])
    )

    if interests1 and interests2:
        intersection = len(interests1 & interests2)
        union = len(interests1 | interests2)
        interest_similarity = intersection / union if union > 0 else 0
        features.append(interest_similarity)

    # Learning style similarity
    if profile1.get("learning_style") == profile2.get("learning_style"):
        features.append(1.0)
    else:
        features.append(0.0)

    # Difficulty preference similarity
    avg_difficulty1 = sum(
        d.get("score", 0) for d in profile1.get("ability_dimensions", {}).values()
    ) / max(len(profile1.get("ability_dimensions", {})), 1)
    avg_difficulty2 = sum(
        d.get("score", 0) for d in profile2.get("ability_dimensions", {}).values()
    ) / max(len(profile2.get("ability_dimensions", {})), 1)

    difficulty_similarity = 1 - abs(avg_difficulty1 - avg_difficulty2) / 100
    features.append(difficulty_similarity)

    # Calculate average similarity
    if features:
        return sum(features) / len(features)
    return 0.0
