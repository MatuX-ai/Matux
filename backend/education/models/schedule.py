"""
课程排课表模型
"""
from sqlalchemy import Column, Integer, String, Time, Date, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from database.session_base import Base
from datetime import datetime

# 前向声明，避免循环导入
type Course = 'Course'
type Teacher = 'Teacher'
type Classroom = 'Classroom'
type Class = 'Class'
type Attendance = 'Attendance'
type User = 'User'


class CourseSchedule(Base):
    """课程排课表 - 核心排课数据模型"""

    __tablename__ = 'courses_schedules'

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 外键关联
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False, index=True)
    classroom_id = Column(Integer, ForeignKey('classrooms.id'), nullable=True, index=True)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=True, index=True)

    # 时间信息
    day_of_week = Column(Integer, nullable=False, comment='星期几 (0-6，0 表示周日)')
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    start_date = Column(Date, nullable=False, comment='开始日期')
    end_date = Column(Date, nullable=False, comment='结束日期')

    # 重复模式：weekly(每周), biweekly(隔周), once(一次性), custom(自定义)
    recurrence_pattern = Column(String(50), default='weekly', nullable=False)

    # 状态标记
    is_confirmed = Column(Boolean, default=False, nullable=False, comment='是否已确认')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否有效')

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # 关系定义
    course = relationship("Course", back_populates="schedules")
    teacher = relationship("Teacher", back_populates="schedules")
    classroom = relationship("Classroom", back_populates="schedules")
    class_group = relationship("Class", back_populates="schedules")
    attendances = relationship("Attendance", back_populates="schedule", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CourseSchedule(id={self.id}, course_id={self.course_id}, day={self.day_of_week}, time={self.start_time}-{self.end_time})>"

    @property
    def duration_minutes(self) -> int:
        """计算课程时长 (分钟)"""
        if not self.start_time or not self.end_time:
            return 0
        start_minutes = self.start_time.hour * 60 + self.start_time.minute
        end_minutes = self.end_time.hour * 60 + self.end_time.minute
        return max(0, end_minutes - start_minutes)

    def has_time_conflict(self, other: 'CourseSchedule') -> bool:
        """判断两个课表是否有时间冲突"""
        if self.day_of_week != other.day_of_week:
            return False

        # 检查时间段是否重叠
        return not (self.end_time <= other.start_time or other.end_time <= self.start_time)


class ScheduleConflict(Base):
    """课表冲突记录表"""

    __tablename__ = 'schedule_conflicts'

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey('courses_schedules.id'), nullable=False)

    # 冲突类型：teacher_conflict, classroom_conflict, student_conflict, capacity_conflict
    conflict_type = Column(String(50), nullable=False)

    # 冲突描述
    description = Column(String(500), nullable=False)

    # 相关课表 ID 列表 (JSON 格式存储)
    related_schedule_ids = Column(String(1000), comment='相关课表 ID 列表')

    # 解决状态：pending, resolved, ignored
    status = Column(String(20), default='pending', nullable=False)

    # 创建时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    def __repr__(self):
        return f"<ScheduleConflict(id={self.id}, type={self.conflict_type}, schedule_id={self.schedule_id})>"
