"""
教育业务 Pydantic Schema 模块
"""

from .schedule_schema import (
    ClassInfo,
    ClassroomInfo,
    Constraint,
    CourseInfo,
    CourseScheduleResponse,
    ScheduleAdjustmentRequest,
    ScheduleAdjustmentResponse,
    ScheduleConflict,
    ScheduleGenerationOptions,
    ScheduleGenerationRequest,
    ScheduleGenerationResponse,
    ScheduleStatisticsResponse,
    SchedulingConstraints,
    TeacherInfo,
)

__all__ = [
    'CourseInfo',
    'TeacherInfo',
    'ClassroomInfo',
    'ClassInfo',
    'Constraint',
    'SchedulingConstraints',
    'ScheduleGenerationOptions',
    'ScheduleGenerationRequest',
    'ScheduleAdjustmentRequest',
    'ScheduleConflict',
    'CourseScheduleResponse',
    'ScheduleGenerationResponse',
    'ScheduleAdjustmentResponse',
    'ScheduleStatisticsResponse',
]
