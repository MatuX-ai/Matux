"""
教育业务 API 路由模块
"""

from .schedules import router as schedules_router
from .students import router as students_router
from .teachers import router as teachers_router

__all__ = [
    'schedules_router',
    'students_router',
    'teachers_router',
]
