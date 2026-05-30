"""
财务管理数据模型
包含学费、薪酬、定价、消课等财务相关表结构
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
import enum

from database import Base


class TransactionType(str, enum.Enum):
    """交易类型枚举"""
    tuition_fee = "tuition_fee"
    material_fee = "material_fee"
    exam_fee = "exam_fee"
    refund = "refund"
    salary = "salary"
    bonus = "bonus"
    expense = "expense"
    donation = "donation"
    other_income = "other_income"
    other_expense = "other_expense"


class TransactionStatus(str, enum.Enum):
    """交易状态枚举"""
    pending = "pending"
    confirmed = "confirmed"
    paid = "paid"
    cancelled = "cancelled"
    overdue = "overdue"


class PaymentMethod(str, enum.Enum):
    """支付方式枚举"""
    cash = "cash"
    bank_transfer = "bank_transfer"
    wechat = "wechat"
    alipay = "alipay"
    credit_card = "credit_card"
    installment = "installment"


class FinancialTransaction(Base):
    """财务交易记录表"""
    __tablename__ = "financial_transactions"

    id = Column(String(50), primary_key=True, index=True)
    org_id = Column(Integer, nullable=False, index=True)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.pending)
    description = Column(Text)

    # 关联实体信息（JSON格式存储）
    related_entity = Column(JSON)

    payment_method = Column(Enum(PaymentMethod))
    transaction_date = Column(DateTime, default=datetime.utcnow)
    due_date = Column(DateTime)
    paid_date = Column(DateTime)
    remark = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PaymentStatus(str, enum.Enum):
    """缴费状态枚举"""
    unpaid = "unpaid"
    partial = "partial"
    full_paid = "full_paid"
    refunded = "refunded"
    partially_refunded = "partially_refunded"


class TuitionRecord(Base):
    """学费记录表"""
    __tablename__ = "tuition_records"

    id = Column(String(50), primary_key=True, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    student_name = Column(String(100), nullable=False)
    course_id = Column(Integer, nullable=False, index=True)
    course_name = Column(String(200), nullable=False)

    original_price = Column(Float, nullable=False)
    discount_amount = Column(Float, default=0)
    final_amount = Column(Float, nullable=False)
    paid_amount = Column(Float, default=0)
    remaining_amount = Column(Float, nullable=False)

    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.unpaid)
    enrollment_date = Column(DateTime, default=datetime.utcnow)

    # 付款计划（JSON格式）
    payment_plan = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PricingStrategy(str, enum.Enum):
    """定价策略枚举"""
    fixed = "fixed"
    tiered = "tiered"
    dynamic = "dynamic"
    market_based = "market_based"


class CoursePricing(Base):
    """课程定价表"""
    __tablename__ = "course_pricings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, nullable=False, index=True)
    course_name = Column(String(200), nullable=False)

    base_price = Column(Float, nullable=False)
    pricing_strategy = Column(Enum(PricingStrategy), default=PricingStrategy.fixed)

    # 阶梯价格、折扣规则等（JSON格式）
    tiered_prices = Column(JSON)
    discount_rules = Column(JSON)
    early_bird_discount = Column(JSON)
    group_discount = Column(JSON)

    is_active = Column(Integer, default=1)
    effective_date = Column(DateTime)
    expiry_date = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SalaryStatus(str, enum.Enum):
    """薪酬状态枚举"""
    draft = "draft"
    pending = "pending"
    approved = "approved"
    calculating = "calculating"
    ready_to_pay = "ready_to_pay"
    paid = "paid"
    error = "error"


class TeacherSalary(Base):
    """教师薪酬表"""
    __tablename__ = "teacher_salaries"

    id = Column(String(50), primary_key=True, index=True)
    teacher_id = Column(Integer, nullable=False, index=True)
    teacher_name = Column(String(100), nullable=False)
    org_id = Column(Integer, nullable=False, index=True)

    base_salary = Column(Float, default=0)
    performance_salary = Column(Float, default=0)
    bonus = Column(Float, default=0)
    deduction = Column(Float, default=0)
    total_salary = Column(Float, nullable=False)

    tax = Column(Float, default=0)
    social_security = Column(Float, default=0)
    actual_salary = Column(Float, nullable=False)

    salary_month = Column(String(7), nullable=False, index=True)  # YYYY-MM
    status = Column(Enum(SalaryStatus), default=SalaryStatus.draft)

    working_hours = Column(Float, default=0)
    class_count = Column(Integer, default=0)
    student_count = Column(Integer, default=0)
    evaluation_score = Column(Float)

    remark = Column(Text)
    paid_date = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ConsumptionType(str, enum.Enum):
    """消课类型枚举"""
    normal_class = "normal_class"
    makeup_class = "makeup_class"
    trial_class = "trial_class"
    activity_class = "activity_class"
    online_class = "online_class"


class ConsumptionStatus(str, enum.Enum):
    """消课状态枚举"""
    scheduled = "scheduled"
    completed = "completed"
    absent = "absent"
    leave = "leave"
    cancelled = "cancelled"


class CourseConsumption(Base):
    """消课记录表"""
    __tablename__ = "course_consumptions"

    id = Column(String(50), primary_key=True, index=True)
    student_id = Column(Integer, nullable=False, index=True)
    student_name = Column(String(100), nullable=False)
    course_id = Column(Integer, nullable=False, index=True)
    course_name = Column(String(200), nullable=False)

    schedule_id = Column(Integer)
    consumed_hours = Column(Float, nullable=False)
    remaining_hours = Column(Float, nullable=False)
    total_hours = Column(Float, nullable=False)

    consumption_date = Column(DateTime, nullable=False, index=True)
    consumption_type = Column(Enum(ConsumptionType), default=ConsumptionType.normal_class)
    status = Column(Enum(ConsumptionStatus), default=ConsumptionStatus.scheduled)

    teacher_id = Column(Integer)
    teacher_name = Column(String(100))
    classroom_id = Column(Integer)
    classroom_name = Column(String(100))

    note = Column(Text)
    confirmed_by = Column(Integer)
    confirmed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
