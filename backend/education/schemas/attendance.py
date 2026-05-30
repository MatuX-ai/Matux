"""
iMato 教育培训管理系统 - 签到数据验证模式
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class CheckinStatusEnum(str, Enum):
    """签到状态枚举"""
    SUCCESS = "success"
    FAILED = "failed"
    LATE = "late"
    ABSENT = "absent"


class CheckinRequest(BaseModel):
    """签到请求"""
    token: str = Field(..., description="二维码 Token")
    student_id: str = Field(..., description="学生 ID")
    location: Optional[str] = Field(None, description="位置信息")


class CheckinResponse(BaseModel):
    """签到响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    deducted_hours: int = Field(..., description="扣减课时数")
    remaining_hours: int = Field(..., description="剩余课时数")
    student_name: str = Field(..., description="学生姓名")


class AttendanceRecordSchema(BaseModel):
    """签到记录"""
    id: str
    student_id: str
    course_schedule_id: Optional[str]
    scheduled_time: datetime
    checkin_time: Optional[datetime]
    status: CheckinStatusEnum
    checkin_method: str
    location: Optional[str]
    notes: Optional[str]
    deducted_hours: int

    class Config:
        from_attributes = True


class AttendanceStats(BaseModel):
    """签到统计"""
    total_checkins: int = Field(..., description="总签到次数")
    total_late: int = Field(..., description="迟到次数")
    total_absent: int = Field(..., description="缺勤次数")
    total_deducted_hours: int = Field(..., description="总扣减课时数")
