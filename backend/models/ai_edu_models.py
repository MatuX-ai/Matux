"""TODO: docstring"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    text,
)
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AIEduModule(Base):
    """TODO: docstring"""AI è¯¾ç¨è¯¾æ¶è¡?""

    __tablename__ = "ai_edu_lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer, ForeignKey("ai_edu_modules.id"))
    lesson_code = Column(String(50), unique=True, nullable=False)
    title = Column(String(100), nullable=False)
    subtitle = Column(String(200))
    content_type = Column(String(20))  # theory, practice, hybrid
    content_url = Column(String(500))
    resources = Column(JSON)  # [{type, url, title, description}]
    learning_objectives = Column(JSON)
    knowledge_points = Column(JSON)
    estimated_duration_minutes = Column(Integer)
    has_quiz = Column(Boolean, default=False)
    quiz_passing_score = Column(Float, default=60.0)
    has_practice = Column(Boolean, default=False)
    practice_type = Column(String(20))  # python, scratch, etc.
    base_points = Column(Integer, default=20)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)

    def to_dict(self):
        return {
            "id": self.id,
            "module_id": self.module_id,
            "lesson_code": self.lesson_code,
            "title": self.title,
            "subtitle": self.subtitle,
            "content_type": self.content_type,
            "content_url": self.content_url,
            "resources": self.resources,
            "learning_objectives": self.learning_objectives,
            "knowledge_points": self.knowledge_points,
            "estimated_duration_minutes": self.estimated_duration_minutes,
            "has_quiz": self.has_quiz,
            "quiz_passing_score": self.quiz_passing_score,
            "has_practice": self.has_practice,
            "practice_type": self.practice_type,
            "base_points": self.base_points,
            "is_active": self.is_active,
            "display_order": self.display_order,
        }


class AIEduLearningProgress(Base):
    """TODO: docstring"""ç§¯åäº¤æè®°å½è¡?""

    __tablename__ = "ai_edu_points_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    transaction_type = Column(String(10), nullable=False)  # earn, spend
    points_amount = Column(Integer, nullable=False)
    source_type = Column(String(50))  # course_completion, quiz, practice
    source_id = Column(Integer)
    base_points = Column(Integer, default=0)
    quality_bonus = Column(Integer, default=0)
    streak_bonus = Column(Integer, default=0)
    final_points = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, completed, cancelled
    transaction_time = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)

    def to_dict(self):
        return {
            "transaction_id": self.id,
            "user_id": self.user_id,
            "transaction_type": self.transaction_type,
            "points_amount": self.points_amount,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "base_points": self.base_points,
            "quality_bonus": self.quality_bonus,
            "streak_bonus": self.streak_bonus,
            "final_points": self.final_points,
            "status": self.status,
            "transaction_time": self.transaction_time.isoformat(),
            "notes": self.notes,
        }


  # TODO
class AIEduDatabaseManager:
    """TODO: docstring"""

    def __init__(self, db_path: str = None):
        from pathlib import Path

        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "ai_edu_standalone.db"

        self.db_path = db_path
        self.database_url = f"sqlite:///{db_path}"
        self.engine = create_engine(self.database_url, echo=False)

          # TODO
        Base.metadata.create_all(self.engine)

    def get_connection(self):
        """TODO: docstring"""æ§è¡ SQL æ¥è¯¢"""TODO: docstring"""è·åææè¯¾ç¨æ¨¡å?""
        query = "SELECT * FROM ai_edu_modules"
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY display_order"

        result = self.execute_query(query)
        return [dict(row._mapping) for row in result]

    def get_module_by_id(self, module_id: int):
        """TODO: docstring"""
        query = "SELECT * FROM ai_edu_modules WHERE id = :id"
        result = self.execute_query(query, {"id": module_id})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    def get_lessons_by_module(self, module_id: int, active_only=True):
        """TODO: docstring"""è·åç¨æ·å­¦ä¹ è¿åº¦"""
        query = "SELECT * FROM ai_edu_learning_progress WHERE user_id = :user_id"
        params = {"user_id": user_id}

        if lesson_id:
            query += " AND lesson_id = :lesson_id"
            params["lesson_id"] = lesson_id

        result = self.execute_query(query, params)
        return [dict(row._mapping) for row in result]

    def update_or_create_progress(
        self, user_id: int, lesson_id: int, progress_data: dict
    ):
        """æ´æ°æåå»ºå­¦ä¹ è¿åº¦è®°å½?""
          # TODO
        existing = self.get_user_progress(user_id, lesson_id)

        if existing:
              # TODO
            progress_id = existing[0]["id"]
            update_fields = []
            for key, value in progress_data.items():
                if value is not None:
                    update_fields.append(f"{key} = :{key}")

            if update_fields:
                update_fields.append("last_accessed_time = :last_accessed_time")
                progress_data["last_accessed_time"] = datetime.utcnow().isoformat()

                query = f"UPDATE ai_edu_learning_progress SET {', '.join(update_fields)} WHERE id = :id"
                progress_data["id"] = progress_id

                self.execute_query(query, progress_data)
        else:
              # TODO
            progress_data["user_id"] = user_id
            progress_data["lesson_id"] = lesson_id
            progress_data["start_time"] = datetime.utcnow().isoformat()
            progress_data["last_accessed_time"] = datetime.utcnow().isoformat()

            columns = list(progress_data.keys())
            values = [f":{col}" for col in columns]

            query = f"""
                INSERT INTO ai_edu_learning_progress ({', '.join(columns)})
                VALUES ({', '.join(values)})
            """

            self.execute_query(query, progress_data)

        return self.get_user_progress(user_id, lesson_id)[0]

      # TODO

    def add_points_transaction(self, user_id: int, points_data: dict):
        """TODO: docstring"""
        points_data["user_id"] = user_id
        points_data["transaction_time"] = datetime.utcnow().isoformat()

        columns = list(points_data.keys())
        values = [f":{col}" for col in columns]

        query = f"""
            INSERT INTO ai_edu_points_transactions ({', '.join(columns)})
            VALUES ({', '.join(values)})
        """

        self.execute_query(query, points_data)

    def get_user_total_points(self, user_id: int):
        """TODO: docstring"""
            SELECT COALESCE(SUM(final_points), 0) as total
            FROM ai_edu_points_transactions
            WHERE user_id = :user_id AND transaction_type = 'earn' AND status = 'completed'
        """TODO: docstring"""è·åç¨æ·å­¦ä¹ ç»è®¡"""TODO: docstring"""
            SELECT 
                COUNT(*) as total_courses,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_courses,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_courses,
                SUM(CASE WHEN status = 'not_started' THEN 1 ELSE 0 END) as not_started_courses,
                COALESCE(SUM(time_spent_seconds), 0) as total_time_seconds,
                AVG(quiz_score) as avg_quiz_score,
                AVG(code_quality_score) as avg_code_score
            FROM ai_edu_learning_progress
            WHERE user_id = :user_id
        """TODO: docstring"""è·å AI-Edu æ°æ®åºç®¡çå¨åä¾"""
    global _db_manager
    if _db_manager is None:
        _db_manager = AIEduDatabaseManager()
    return _db_manager
