"""TODO: docstring"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from utils.database import Base


class UserGuardian(Base):
    """TODO: docstring"""

    __tablename__ = "user_guardians"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="å­¦çç¨æ·ID"
    )
    guardian_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="çæ¤äººç¨æ·ID"
    )
    relation_type = Column(
        String(50), nullable=True, comment="å³ç³»ï¼father/mother/guardian/other"
    )
    is_primary = Column(Boolean, default=False, comment="æ¯å¦ä¸ºä¸»è¦çæ¤äºº")
    is_active = Column(Boolean, default=True, comment="å³èæ¯å¦ææ")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

      # TODO
    student = relationship("User", foreign_keys="UserGuardian.student_id", backref="guardian_links")
    guardian = relationship("User", foreign_keys="UserGuardian.guardian_id", backref="ward_links")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "guardian_id": self.guardian_id,
            "relationship": self.relation_type,
            "is_primary": self.is_primary,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


# ============ Pydantic Schemas ============


class GuardianBindRequest(BaseModel):
    """TODO: docstring"""

    student_phone: str = Field(..., description="Student phone number")
    relationship: Optional[str] = Field(None, description="å³ç³»ï¼father/mother/guardian")
    is_primary: bool = Field(default=False, description="æ¯å¦ä¸ºä¸»è¦çæ¤äºº")


class GuardianBindResponse(BaseModel):
    """TODO: docstring"""

    id: int
    student_id: int
    guardian_id: int
    relationship: Optional[str]
    is_primary: bool
    message: str


class StudentGuardianInfo(BaseModel):
    """TODO: docstring"""

    student_id: int
    student_name: str
    student_phone: Optional[str]
    relationship: Optional[str]
    is_primary: bool