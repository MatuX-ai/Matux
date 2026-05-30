"""
教师信息模型
"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, DateTime, Numeric, Text
from sqlalchemy.orm import relationship
from database.session_base import Base
from datetime import datetime


class Teacher(Base):
    """教师信息表"""

    __tablename__ = 'teachers'

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=True, comment='性别：male/female')
    birth_date = Column(Date, nullable=True)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)

    # 身份证信息
    id_card_number = Column(String(18), nullable=True)

    # 入职信息
    hire_date = Column(Date, nullable=False)
    employment_type = Column(String(20), default='full_time', comment='员工类型：full_time/part_time')

    # 薪酬配置
    base_salary = Column(Numeric(10, 2), default=0, comment='底薪 (元/月)')
    position_allowance = Column(Numeric(10, 2), default=0, comment='岗位津贴 (元/月)')

    # 教学资质
    teacher_certificate = Column(String(500), nullable=True, comment='教师资格证编号')
    qualifications = Column(Text, nullable=True, comment='资质证书 (JSON 格式)')

    # 教学信息
    teaching_subjects = Column(String(500), nullable=True, comment='教授科目 (JSON 数组)')
    max_weekly_hours = Column(Integer, default=40, comment='最大周课时量')
    preferred_teaching_times = Column(String(1000), nullable=True, comment='偏好授课时间段 (JSON)')

    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), default='active', comment='状态：active/inactive/resigned')

    # 头像
    avatar_url = Column(String(500), nullable=True)

    # 备注
    notes = Column(Text, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # 关系定义
    schedules = relationship("CourseSchedule", back_populates="teacher")
    teaching_records = relationship("TeachingRecord", back_populates="teacher", cascade="all, delete-orphan")
    salaries = relationship("TeacherSalary", back_populates="teacher", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Teacher(id={self.id}, name='{self.name}', type='{self.employment_type}')>"

    @property
    def total_monthly_hours(self) -> float:
        """计算月授课总时长"""
        # 这个可以通过关联的 teaching_records 统计
        return sum(record.hours for record in self.teaching_records if record.month.startswith(datetime.now().strftime('%Y-%m')))


class TeachingRecord(Base):
    """教师授课记录表 - 用于统计课时费和绩效"""

    __tablename__ = 'teaching_records'

    id = Column(Integer, primary_key=True, index=True)

    # 关联
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False, index=True)
    schedule_id = Column(Integer, ForeignKey('courses_schedules.id'), nullable=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    class_id = Column(Integer, ForeignKey('classes.id'), nullable=True)

    # 授课信息
    teaching_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, nullable=False)

    # 课程类型和班级规模 (用于计算课时费)
    course_type = Column(String(50), nullable=False, comment='课程类型：one_on_one/small_class/medium_class/large_class')
    class_size = Column(Integer, nullable=False, comment='学生人数')

    # 课时费标准
    hourly_rate = Column(Numeric(10, 2), default=0, comment='课时费标准 (元/小时)')
    teaching_income = Column(Numeric(10, 2), default=0, comment='本次课时费')

    # 月份 (用于月度统计)
    month = Column(String(7), nullable=False, index=True, comment='YYYY-MM')

    # 状态
    status = Column(String(20), default='completed', comment='状态：completed/cancelled/makeup')
    is_confirmed = Column(Boolean, default=False, comment='是否已确认')

    # 备注
    notes = Column(Text, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    confirmed_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # 关系
    teacher = relationship("Teacher", back_populates="teaching_records")
    course = relationship("Course")
    class_group = relationship("Class")

    def __repr__(self):
        return f"<TeachingRecord(id={self.id}, teacher_id={self.teacher_id}, date={self.teaching_date}, hours={self.duration_minutes/60})>"


class TeacherSalary(Base):
    """教师工资表"""

    __tablename__ = 'teacher_salaries'

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey('teachers.id'), nullable=False, index=True)
    month = Column(String(7), nullable=False, unique=True, comment='YYYY-MM')

    # 工资组成部分
    base_salary = Column(Numeric(10, 2), default=0, comment='基本工资')
    teaching_income = Column(Numeric(10, 2), default=0, comment='课时费总收入')
    performance_bonus = Column(Numeric(10, 2), default=0, comment='绩效奖金')
    attendance_bonus = Column(Numeric(10, 2), default=0, comment='出勤率奖')
    renewal_bonus = Column(Numeric(10, 2), default=0, comment='续班率奖')
    competition_bonus = Column(Numeric(10, 2), default=0, comment='竞赛指导奖')

    # 扣款项
    late_deduction = Column(Numeric(10, 2), default=0, comment='迟到/早退扣款')
    accident_deduction = Column(Numeric(10, 2), default=0, comment='教学事故扣款')
    complaint_deduction = Column(Numeric(10, 2), default=0, comment='投诉扣款')
    other_deductions = Column(Numeric(10, 2), default=0, comment='其他扣款')

    # 应发工资
    gross_salary = Column(Numeric(10, 2), default=0, comment='应发工资')

    # 扣除社保/公积金等
    social_security = Column(Numeric(10, 2), default=0)
    housing_fund = Column(Numeric(10, 2), default=0)
    tax = Column(Numeric(10, 2), default=0)

    # 实发工资
    net_salary = Column(Numeric(10, 2), default=0, comment='实发工资')

    # 发放状态
    status = Column(String(20), default='pending', comment='状态：pending/calculated/paid')
    paid_date = Column(Date, nullable=True)
    paid_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # 备注
    notes = Column(Text, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    teacher = relationship("Teacher", back_populates="salaries")

    def __repr__(self):
        return f"<TeacherSalary(id={self.id}, teacher_id={self.teacher_id}, month={self.month}, net_salary={self.net_salary})>"
