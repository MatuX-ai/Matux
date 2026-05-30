"""
教育业务 Pydantic Schema 模块
"""

from .schedule_schema import (
    CourseInfo,
    TeacherInfo,
    ClassroomInfo,
    ClassInfo,
    Constraint,
    SchedulingConstraints,
    ScheduleGenerationOptions,
    ScheduleGenerationRequest,
    ScheduleAdjustmentRequest,
    ScheduleConflict,
    CourseScheduleResponse,
    ScheduleGenerationResponse,
    ScheduleAdjustmentResponse,
    ScheduleStatisticsResponse,
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
