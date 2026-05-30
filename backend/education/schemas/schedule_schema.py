"""
排课模块 Pydantic Schema - 用于请求和响应验证
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any
from datetime import time, date
from enum import Enum


class RecurrencePattern(str, Enum):
    """重复模式枚举"""
    WEEKLY = 'weekly'
    BIWEEKLY = 'biweekly'
    ONCE = 'once'
    CUSTOM = 'custom'


class ConflictType(str, Enum):
    """冲突类型枚举"""
    TEACHER_CONFLICT = 'teacher_conflict'
    CLASSROOM_CONFLICT = 'classroom_conflict'
    STUDENT_CONFLICT = 'student_conflict'
    CAPACITY_CONFLICT = 'capacity_conflict'


# ==================== 基础信息 Schema ====================

class CourseInfo(BaseModel):
    """课程信息"""
    id: str
    name: str
    total_hours: int
    course_type: str
    teacher_ids: Optional[List[str]] = []


class TeacherInfo(BaseModel):
    """教师信息"""
    id: str
    name: str
    available_time_slots: Optional[List[Dict]] = []
    max_weekly_hours: int = 40
    teaching_subjects: Optional[List[str]] = []


class ClassroomInfo(BaseModel):
    """教室信息"""
    id: str
    name: str
    capacity: int
    equipment: Optional[List[str]] = []


class ClassInfo(BaseModel):
    """班级信息"""
    id: str
    name: str
    student_count: int
    students: Optional[List[str]] = []


# ==================== 约束条件 Schema ====================

class Constraint(BaseModel):
    """约束条件"""
    id: str
    type: str
    description: str
    enabled: bool = True


class SchedulingConstraints(BaseModel):
    """排课约束条件"""
    hard_constraints: Optional[List[Constraint]] = []
    soft_constraints: Optional[List[Constraint]] = []


class ScheduleGenerationOptions(BaseModel):
    """排课选项"""
    population_size: int = Field(default=100, ge=50, le=500)
    generations: int = Field(default=1000, ge=100, le=5000)
    mutation_rate: float = Field(default=0.1, ge=0.0, le=1.0)


# ==================== 请求 Schema ====================

class ScheduleGenerationRequest(BaseModel):
    """课表生成请求"""
    courses: List[CourseInfo]
    teachers: List[TeacherInfo]
    classrooms: List[ClassroomInfo]
    classes: List[ClassInfo]
    constraints: Optional[SchedulingConstraints] = None
    options: Optional[ScheduleGenerationOptions] = None

    class Config:
        schema_extra = {
            "example": {
                "courses": [
                    {
                        "id": "C001",
                        "name": "数学",
                        "total_hours": 60,
                        "course_type": "medium_class",
                        "teacher_ids": ["T001"]
                    }
                ],
                "teachers": [
                    {
                        "id": "T001",
                        "name": "张老师",
                        "max_weekly_hours": 20,
                        "teaching_subjects": ["数学"]
                    }
                ],
                "classrooms": [
                    {
                        "id": "R001",
                        "name": "教室 A101",
                        "capacity": 30,
                        "equipment": ["projector", "whiteboard"]
                    }
                ],
                "classes": [
                    {
                        "id": "CL001",
                        "name": "初三 (1) 班",
                        "student_count": 25,
                        "students": ["S001", "S002"]
                    }
                ]
            }
        }


class ScheduleAdjustmentRequest(BaseModel):
    """课表调整请求"""
    schedule_id: str
    new_time_slot: Dict[str, Any] = Field(
        ...,
        description="新的时间段",
        example={"day_of_week": 1, "start_time": "10:00", "end_time": "11:00"}
    )


# ==================== 响应 Schema ====================

class ScheduleConflict(BaseModel):
    """课表冲突"""
    conflict_type: ConflictType
    description: str
    related_schedule_ids: Optional[List[str]] = []
    schedule_id: Optional[str] = None


class CourseScheduleResponse(BaseModel):
    """课程课表响应"""
    id: Optional[str] = None
    course_id: str
    course_name: Optional[str] = None
    teacher_id: str
    teacher_name: Optional[str] = None
    classroom_id: Optional[str] = None
    classroom_name: Optional[str] = None
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    day_of_week: int
    start_time: str
    end_time: str
    recurrence_pattern: RecurrencePattern = RecurrencePattern.WEEKLY
    is_confirmed: bool = False
    has_conflict: bool = False
    conflicts: Optional[List[ScheduleConflict]] = []


class ScheduleGenerationResponse(BaseModel):
    """课表生成响应"""
    success: bool
    schedule: List[CourseScheduleResponse]
    conflicts: List[ScheduleConflict]
    score: float
    message: Optional[str] = None


class ScheduleAdjustmentResponse(BaseModel):
    """课表调整响应"""
    success: bool
    updated_schedule: List[CourseScheduleResponse]
    new_conflicts: List[ScheduleConflict]
    message: str


class ScheduleStatisticsResponse(BaseModel):
    """课表统计响应"""
    total_courses: int
    by_teacher: Dict[str, int]
    by_classroom: Dict[str, int]
    by_class: Dict[str, int]
    by_day: Dict[int, int]
    total_hours: float
