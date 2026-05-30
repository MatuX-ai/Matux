"""
学员档案模型
"""
from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean, DateTime, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from database.session_base import Base
from datetime import datetime
import enum


class StudentStatus(enum.Enum):
    """学员状态枚举"""
    ENROLLED = '在读'  # 在学
    SUSPENDED = '休学'  # 暂停学习
    GRADUATED = '毕业'  # 已毕业
    WITHDRAWN = '退学'  # 已退学
    TRANSFERRED = '转校'  # 转校


class ParentInfo(Base):
    """家长/监护人信息表"""

    __tablename__ = 'parent_info'

    id = Column(Integer, primary_key=True, index=True)

    # 关联学生
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False, index=True)

    # 基本信息
    name = Column(String(100), nullable=False)
    relationship_type = Column(String(20), nullable=False, comment='与学生关系：父亲/母亲/其他监护人')

    # 联系方式
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    wechat = Column(String(50), nullable=True, comment='微信号')
    qq = Column(String(20), nullable=True, comment='QQ 号')

    # 是否主要联系人
    is_primary = Column(Boolean, default=False, nullable=False)

    # 地址信息
    address = Column(String(500), nullable=True)

    # 备注
    notes = Column(Text, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    student = relationship("Student", back_populates="parents")

    def __repr__(self):
        return f"<ParentInfo(id={self.id}, name='{self.name}', relation='{self.relationship_type}')>"


class StudentProfile(Base):
    """学员档案主表"""

    __tablename__ = 'students'

    # 主键
    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=False, comment='性别：male/female/other')
    birth_date = Column(Date, nullable=True, comment='出生日期')

    # 年级和学校
    grade = Column(String(50), nullable=True, comment='年级 (如：初三)')
    school = Column(String(200), nullable=True, comment='就读学校')

    # 联系方式
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)

    # 身份证信息 (用于 OCR 识别)
    id_card_number = Column(String(18), nullable=True)
    id_card_address = Column(String(500), nullable=True)

    # 头像
    avatar_url = Column(String(500), nullable=True)

    # 学籍状态
    status = Column(SQLEnum(StudentStatus), default=StudentStatus.ENROLLED, nullable=False)
    enrollment_date = Column(Date, nullable=False, comment='入学日期')
    graduation_date = Column(Date, nullable=True, comment='预计毕业日期')
    actual_graduation_date = Column(Date, nullable=True, comment='实际毕业日期')

    # 分班信息
    current_class_id = Column(Integer, ForeignKey('classes.id'), nullable=True, index=True)

    # 课时信息
    total_purchased_hours = Column(Integer, default=0, comment='总购买课时')
    total_consumed_hours = Column(Integer, default=0, comment='总消耗课时')
    remaining_hours = Column(Integer, default=0, comment='剩余课时')

    # 紧急联系人
    emergency_contact = Column(String(100), nullable=True)
    emergency_phone = Column(String(20), nullable=True)

    # 扩展字段 (JSON 格式)
    custom_fields = Column(String(2000), nullable=True, comment='自定义扩展字段')

    # 备注
    notes = Column(Text, nullable=True)

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # 关系定义
    parents = relationship("ParentInfo", back_populates="student", cascade="all, delete-orphan")
    class_group = relationship("Class", back_populates="students")
    attendances = relationship("Attendance", back_populates="student", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StudentProfile(id={self.id}, name='{self.name}', status='{self.status.value}')>"

    @property
    def age(self) -> int:
        """计算年龄"""
        if not self.birth_date:
            return 0
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

    @property
    def is_low_balance_warning(self) -> bool:
        """是否需要课时预警 (剩余课时<5)"""
        return self.remaining_hours < 5

    def get_primary_parent(self) -> ParentInfo | None:
        """获取主要联系人"""
        primary_parents = [p for p in self.parents if p.is_primary]
        return primary_parents[0] if primary_parents else (self.parents[0] if self.parents else None)
