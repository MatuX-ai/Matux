"""
AI-Edu intelligent recommendation system data models
Supports user profiles, course features, recommendation records, etc.
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
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database.db import Base


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

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="learning_profile")
    recommendations = relationship(
        "RecommendationRecord", back_populates="user_profile"
    )

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
    user_profile = relationship("UserLearningProfile", backref="recommendations")

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
