"""
动态课程模型（存根）
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DynamicCourseRequestCreate(BaseModel):
    title: str
    description: str
    teacher_id: int
    student_ids: List[int]
    template_id: Optional[int] = None


class DynamicCourseResponseDetail(BaseModel):
    id: int
    title: str
    student_count: int
    status: str
    created_at: datetime


class GeneratedCourse(BaseModel):
    id: int
    title: str
    description: str
    teacher_id: int
    student_ids: List[int]
    status: str
    created_at: datetime


class CourseGenerationLog(BaseModel):
    id: int
    course_id: int
    action: str
    details: Dict[str, Any]
    created_by: int
    created_at: datetime


class CourseGenerationStats(BaseModel):
    total_generations: int
    successful: int
    failed: int
    average_time_seconds: float


class CourseComponentResponse(BaseModel):
    id: int
    course_id: int
    component_type: str
    component_data: Dict[str, Any]
    order: int


class TemplateEvaluation(BaseModel):
    id: int
    template_id: int
    score: float
    feedback: Optional[str] = None
    evaluated_by: int
    evaluated_at: datetime


class CourseQueryParams(BaseModel):
    teacher_id: Optional[int] = None
    student_id: Optional[int] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 20


class BacktestResult(BaseModel):
    id: int
    course_id: int
    scenario: str
    metrics: Dict[str, Any]
    passed: bool
    executed_at: datetime


class StudentProfileCreate(BaseModel):
    student_id: int
    course_id: int
    preferences: Dict[str, Any]
    learning_style: Optional[str] = None
