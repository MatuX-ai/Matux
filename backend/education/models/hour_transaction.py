"""
iMato 教育培训管理系统 - 课时流水记录模型
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from backend.database import Base


class HourTransactionType(str, enum.Enum):
    """课时交易类型枚举"""
    PURCHASE = "purchase"        # 购买
    CONSUMPTION = "consumption"  # 消耗 (签到扣减)
    REFUND = "refund"            # 退费
    TRANSFER = "transfer"        # 转课
    ADJUSTMENT = "adjustment"    # 手动调整
    GIFT = "gift"                # 赠送


class HourTransaction(Base):
    """课时流水记录表"""
    __tablename__ = "hour_transactions"

    id = Column(String(36), primary_key=True, index=True)

    # 关联信息
    student_id = Column(String(36), ForeignKey("student_profiles.id"), nullable=False, index=True)
    attendance_record_id = Column(String(36), ForeignKey("attendance_records.id"), nullable=True)

    # 交易类型
    transaction_type = Column(String(50), nullable=False, comment="交易类型")

    # 课时变动
    change_hours = Column(Integer, nullable=False, comment="变动课时数 (正数增加，负数减少)")

    # 余额快照
    balance_before = Column(Integer, nullable=False, comment="变动前余额")
    balance_after = Column(Integer, nullable=False, comment="变动后余额")

    # 关联单据
    related_order_id = Column(String(36), nullable=True, comment="关联订单 ID")
    related_schedule_id = Column(String(36), nullable=True, comment="关联课表 ID")

    # 备注说明
    notes = Column(Text, nullable=True, comment="备注说明")
    operator_id = Column(String(50), nullable=True, comment="操作人 ID")

    # 元数据
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联关系
    student = relationship("StudentProfile", back_populates="hour_transactions")
    attendance_record = relationship("AttendanceRecord", back_populates="hour_transaction")
