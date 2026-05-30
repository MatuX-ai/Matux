"""
iMato 教育培训管理系统 - 签到记录模型
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from backend.database import Base


class CheckinStatus(str, enum.Enum):
    """签到状态枚举"""
    SUCCESS = "success"  # 签到成功
    FAILED = "failed"    # 签到失败
    LATE = "late"        # 迟到
    ABSENT = "absent"    # 缺勤


class AttendanceRecord(Base):
    """签到记录表"""
    __tablename__ = "attendance_records"

    id = Column(String(36), primary_key=True, index=True)

    # 关联信息
    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False, index=True)
    course_schedule_id = Column(String(36), ForeignKey("course_schedules.id"), nullable=True, index=True)

    # 签到时间
    scheduled_time = Column(DateTime, nullable=False, comment="计划签到时间")
    checkin_time = Column(DateTime, nullable=True, comment="实际签到时间")

    # 签到状态
    status = Column(SQLEnum(CheckinStatus), default=CheckinStatus.SUCCESS, nullable=False)

    # 签到方式
    checkin_method = Column(String(50), nullable=False, comment="签到方式：qr_code/manual/system")

    # 位置信息 (可选)
    location = Column(String(200), nullable=True, comment="签到地点")

    # 备注
    notes = Column(String(500), nullable=True, comment="备注说明")

    # 课时扣减
    deducted_hours = Column(Integer, default=0, comment="本次扣减课时数")

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(50), nullable=True, comment="创建人 (操作员 ID)")

    # 关联关系
    student = relationship("StudentProfile", back_populates="attendance_records")
    course_schedule = relationship("CourseSchedule", back_populates="attendance_records")


class QRCodeToken(Base):
    """二维码 Token 表 (用于动态二维码)"""
    __tablename__ = "qr_code_tokens"

    id = Column(String(36), primary_key=True, index=True)

    # Token 内容
    token = Column(String(255), unique=True, nullable=False, index=True)

    # 关联信息
    course_schedule_id = Column(String(36), ForeignKey("course_schedules.id"), nullable=True)
    teacher_id = Column(String(36), ForeignKey("teachers.id"), nullable=False)

    # 有效期
    expires_at = Column(DateTime, nullable=False)

    # 使用状态
    is_used = Column(Boolean, default=False, nullable=False)
    used_at = Column(DateTime, nullable=True)
    used_by_student_id = Column(String(36), nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联关系
    teacher = relationship("Teacher", back_populates="qr_tokens")
