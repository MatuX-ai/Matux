"""
学习行为特征数据模型
用于追踪和分析学生的学习行为特征，包括代码调试时长和硬件操作成功率等指标
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from utils.database import Base


class BehaviorCategory(str, Enum):
    """行为类别枚举"""

    CODE_DEBUGGING = "code_debugging"  # 代码调试
    HARDWARE_OPERATION = "hardware_operation"  # 硬件操作
    LEARNING_ACTIVITY = "learning_activity"  # 学习活动
    ASSESSMENT = "assessment"  # 评估测试
    COLLABORATION = "collaboration"  # 协作学习


class BehaviorEventType(str, Enum):
    """行为事件类型枚举"""

    START_DEBUGGING = "start_debugging"  # 开始调试
    END_DEBUGGING = "end_debugging"  # 结束调试
    HARDWARE_CONNECT = "hardware_connect"  # 硬件连接
    HARDWARE_DISCONNECT = "hardware_disconnect"  # 硬件断开
    HARDWARE_OPERATION = "hardware_operation"  # 硬件操作
    OPERATION_SUCCESS = "operation_success"  # 操作成功
    OPERATION_FAILURE = "operation_failure"  # 操作失败
    LESSON_START = "lesson_start"  # 课程开始
    LESSON_COMPLETE = "lesson_complete"  # 课程完成
    EXERCISE_ATTEMPT = "exercise_attempt"  # 练习尝试
    EXERCISE_SUBMIT = "exercise_submit"  # 练习提交


class LearningBehaviorFeature(Base):
    """学习行为特征模型"""

    __tablename__ = "learning_behavior_features"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", use_alter=True), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)

    # 行为基础信息
    category = Column(String(50), nullable=False, index=True)  # 行为类别
    event_type = Column(String(50), nullable=False, index=True)  # 事件类型
    context_id = Column(String(100), index=True)  # 上下文ID（如课程ID、实验ID等）
    session_id = Column(String(100), index=True)  # 会话ID

    # 时间相关特征
    event_timestamp = Column(DateTime, nullable=False, index=True)  # 事件时间戳
    duration_seconds = Column(Integer, default=0)  # 持续时间（秒）
    start_time = Column(DateTime)  # 开始时间
    end_time = Column(DateTime)  # 结束时间

    # 调试相关特征
    debug_duration_seconds = Column(Integer, default=0)  # 代码调试时长（秒）
    debug_attempts = Column(Integer, default=0)  # 调试尝试次数
    breakpoints_used = Column(Integer, default=0)  # 使用断点数量
    debug_commands_executed = Column(Integer, default=0)  # 执行调试命令数
    error_types_encountered = Column(Text)  # 遇到的错误类型（JSON格式）

    # 硬件操作相关特征
    hardware_operation_success_rate = Column(Float, default=0.0)  # 硬件操作成功率
    hardware_operations_count = Column(Integer, default=0)  # 硬件操作总数
    successful_operations = Column(Integer, default=0)  # 成功操作数
    failed_operations = Column(Integer, default=0)  # 失败操作数
    hardware_types_used = Column(Text)  # 使用的硬件类型（JSON格式）
    hardware_connection_duration = Column(Integer, default=0)  # 硬件连接时长（秒）

    # 学习效果特征
    success_indicator = Column(Boolean, default=False)  # 成功标识
    performance_score = Column(Float)  # 性能得分
    difficulty_level = Column(String(20))  # 难度等级
    help_requested = Column(Boolean, default=False)  # 是否请求帮助
    hints_used = Column(Integer, default=0)  # 使用提示次数

    # 环境上下文
    platform = Column(String(50))  # 平台信息
    device_type = Column(String(50))  # 设备类型
    browser_info = Column(String(200))  # 浏览器信息
    ip_address = Column(String(45))  # IP地址

    # 系统字段
    is_processed = Column(Boolean, default=False)  # 是否已处理
    processing_notes = Column(Text)  # 处理备注
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    organization = relationship("Organization")
    student = relationship("Student")

    # 索引
    __table_args__ = (
        Index("idx_behavior_student_category", "student_id", "category"),
        Index("idx_behavior_timestamp", "event_timestamp"),
        Index("idx_behavior_context", "context_id", "session_id"),
        Index("idx_behavior_org_student", "org_id", "student_id"),
    )


class LearningBehaviorSummary(Base):
    """学习行为汇总模型"""

    __tablename__ = "learning_behavior_summaries"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id", use_alter=True), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    period_type = Column(
        String(20), nullable=False, index=True
    )  # 统计周期类型：daily/weekly/monthly

    # 统计时间范围
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False, index=True)

    # 调试行为统计
    total_debug_duration = Column(Integer, default=0)  # 总调试时长（秒）
    avg_debug_duration = Column(Float, default=0.0)  # 平均调试时长（秒）
    debug_sessions_count = Column(Integer, default=0)  # 调试会话数
    total_debug_attempts = Column(Integer, default=0)  # 总调试尝试次数

    # 硬件操作统计
    total_hardware_operations = Column(Integer, default=0)  # 硬件操作总数
    successful_hardware_operations = Column(Integer, default=0)  # 成功硬件操作数
    hardware_success_rate = Column(Float, default=0.0)  # 硬件操作成功率
    unique_hardware_types = Column(Integer, default=0)  # 使用的不同硬件类型数

    # 学习成效统计
    lessons_completed = Column(Integer, default=0)  # 完成课程数
    exercises_attempted = Column(Integer, default=0)  # 尝试练习数
    exercises_completed = Column(Integer, default=0)  # 完成练习数
    average_performance_score = Column(Float, default=0.0)  # 平均性能得分

    # 辅助特征
    help_requests_count = Column(Integer, default=0)  # 请求帮助次数
    hints_used_count = Column(Integer, default=0)  # 使用提示总次数
    collaboration_events = Column(Integer, default=0)  # 协作事件数

    # 系统字段
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    organization = relationship("Organization")
    student = relationship("Student")

    # 索引
    __table_args__ = (
        Index(
            "idx_summary_student_period", "student_id", "period_type", "period_start"
        ),
        Index("idx_summary_org_period", "org_id", "period_type", "period_start"),
    )


from datetime import datetime
from typing import Any, Dict, List

# Pydantic模型定义
from pydantic import BaseModel, Field


class LearningBehaviorCreate(BaseModel):
    """创建学习行为记录的请求模型"""

    student_id: int
    category: BehaviorCategory
    event_type: BehaviorEventType
    context_id: Optional[str] = Field(None, max_length=100)
    session_id: Optional[str] = Field(None, max_length=100)
    event_timestamp: datetime
    duration_seconds: Optional[int] = Field(None, ge=0)
    debug_duration_seconds: Optional[int] = Field(None, ge=0)
    debug_attempts: Optional[int] = Field(None, ge=0)
    breakpoints_used: Optional[int] = Field(None, ge=0)
    debug_commands_executed: Optional[int] = Field(None, ge=0)
    error_types_encountered: Optional[List[str]] = None
    hardware_operation_success_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    hardware_operations_count: Optional[int] = Field(None, ge=0)
    successful_operations: Optional[int] = Field(None, ge=0)
    failed_operations: Optional[int] = Field(None, ge=0)
    hardware_types_used: Optional[List[str]] = None
    hardware_connection_duration: Optional[int] = Field(None, ge=0)
    success_indicator: Optional[bool] = None
    performance_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    difficulty_level: Optional[str] = Field(None, max_length=20)
    help_requested: Optional[bool] = None
    hints_used: Optional[int] = Field(None, ge=0)
    platform: Optional[str] = Field(None, max_length=50)
    device_type: Optional[str] = Field(None, max_length=50)
    browser_info: Optional[str] = Field(None, max_length=200)


class LearningBehaviorUpdate(BaseModel):
    """更新学习行为记录的请求模型"""

    duration_seconds: Optional[int] = Field(None, ge=0)
    debug_duration_seconds: Optional[int] = Field(None, ge=0)
    debug_attempts: Optional[int] = Field(None, ge=0)
    hardware_operation_success_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    success_indicator: Optional[bool] = None
    performance_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    is_processed: Optional[bool] = None
    processing_notes: Optional[str] = None


class LearningBehaviorResponse(BaseModel):
    """学习行为记录响应模型"""

    id: int
    org_id: int
    student_id: int
    category: str
    event_type: str
    context_id: Optional[str]
    session_id: Optional[str]
    event_timestamp: datetime
    duration_seconds: int
    debug_duration_seconds: int
    debug_attempts: int
    hardware_operation_success_rate: float
    hardware_operations_count: int
    successful_operations: int
    success_indicator: bool
    performance_score: Optional[float]
    platform: Optional[str]
    device_type: Optional[str]
    is_processed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class LearningBehaviorSummaryResponse(BaseModel):
    """学习行为汇总响应模型"""

    id: int
    org_id: int
    student_id: int
    period_type: str
    period_start: datetime
    period_end: datetime
    total_debug_duration: int
    avg_debug_duration: float
    debug_sessions_count: int
    total_hardware_operations: int
    successful_hardware_operations: int
    hardware_success_rate: float
    lessons_completed: int
    exercises_completed: int
    average_performance_score: float
    last_updated: datetime
    created_at: datetime

    class Config:
        orm_mode = True


class BehaviorAnalyticsRequest(BaseModel):
    """行为分析请求模型"""

    student_id: Optional[int] = None
    category: Optional[BehaviorCategory] = None
    start_date: datetime
    end_date: datetime
    period_type: str = Field(default="daily", pattern="^(daily|weekly|monthly)$")


class BehaviorAnalyticsResponse(BaseModel):
    """行为分析响应模型"""

    student_id: Optional[int]
    category: Optional[str]
    period_type: str
    start_date: datetime
    end_date: datetime
    total_records: int
    debug_statistics: Dict[str, Any]
    hardware_statistics: Dict[str, Any]
    learning_effectiveness: Dict[str, Any]
    trends: List[Dict[str, Any]]
