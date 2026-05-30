"""
排课管理 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict
import logging

from ..services.scheduling import SchedulingService
from ..schemas.schedule_schema import (
    ScheduleGenerationRequest,
    ScheduleGenerationResponse,
    CourseScheduleResponse,
    ScheduleAdjustmentRequest,
    ScheduleAdjustmentResponse,
    ScheduleStatisticsResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/v1/schedules', tags=['schedules'])


@router.post('/generate', response_model=ScheduleGenerationResponse)
async def generate_schedule(request: ScheduleGenerationRequest):
    """
    生成课表

    使用遗传算法自动生成最优课表安排。

    ## 算法特点:
    - 支持硬约束和软约束
    - 自动检测教师、教室、学生冲突
    - 优化得分 0-100 分

    ## 参数:
    - courses: 课程列表
    - teachers: 教师列表
    - classrooms: 教室列表
    - classes: 班级列表
    - constraints: 约束条件
    - options: 排课选项

    ## 返回:
    - success: 是否成功
    - schedule: 生成的课表
    - conflicts: 冲突列表
    - score: 优化得分
    """
    logger.info(f"收到课表生成请求，课程数：{len(request.courses)}")

    try:
        # 创建服务实例
        scheduling_service = SchedulingService()

        # 转换为字典格式
        courses_data = [course.dict() for course in request.courses]
        teachers_data = [teacher.dict() for teacher in request.teachers]
        classrooms_data = [classroom.dict() for classroom in request.classrooms]
        classes_data = [class_.dict() for class_ in request.classes]

        constraints_data = request.constraints.dict() if request.constraints else {}
        hard_constraints = constraints_data.get('hard_constraints', [])
        soft_constraints = constraints_data.get('soft_constraints', [])

        options_data = request.options.dict() if request.options else {}

        # 生成课表
        result = scheduling_service.generate_schedule(
            courses=courses_data,
            teachers=teachers_data,
            classrooms=classrooms_data,
            classes=classes_data,
            hard_constraints=hard_constraints,
            soft_constraints=soft_constraints,
            options=options_data
        )

        # 检查是否有异常
        if not result['success']:
            logger.warning(f"课表生成失败：{result.get('message')}")

        return ScheduleGenerationResponse(**result)

    except Exception as e:
        logger.error(f"课表生成失败：{str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'课表生成失败：{str(e)}'
        )


@router.get('/conflicts')
async def get_conflicts(schedule_id: int = None):
    """
    获取课表冲突列表

    ## 参数:
    - schedule_id: 课表 ID (可选，不传则返回所有冲突)

    ## 返回:
    - 冲突列表
    """
    # TODO: 实现从数据库查询冲突记录
    return {
        'conflicts': [],
        'total': 0
    }


@router.put('/{schedule_id}/adjust', response_model=ScheduleAdjustmentResponse)
async def adjust_schedule(
    schedule_id: str,
    request: ScheduleAdjustmentRequest
):
    """
    手动调整课表

    允许管理员手动调整课程时间，系统会自动检测新时间是否产生冲突。

    ## 参数:
    - schedule_id: 要调整的课程 ID
    - new_time_slot: 新的时间段 {day_of_week, start_time, end_time}

    ## 返回:
    - success: 是否成功
    - updated_schedule: 更新后的课表
    - new_conflicts: 新产生的冲突
    - message: 提示信息
    """
    logger.info(f"收到课表调整请求，课程 ID: {schedule_id}")

    try:
        # 创建服务实例
        scheduling_service = SchedulingService()

        # TODO: 从数据库查询当前课表
        # 这里使用模拟数据
        current_schedule = []

        # 调整课表
        result = scheduling_service.adjust_schedule(
            schedule_id=schedule_id,
            new_time_slot=request.new_time_slot,
            schedule=current_schedule
        )

        return ScheduleAdjustmentResponse(**result)

    except Exception as e:
        logger.error(f"课表调整失败：{str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'课表调整失败：{str(e)}'
        )


@router.get('/statistics', response_model=ScheduleStatisticsResponse)
async def get_statistics():
    """
    获取课表统计信息

    ## 返回:
    - total_courses: 总课程数
    - by_teacher: 按教师统计
    - by_classroom: 按教室统计
    - by_class: 按班级统计
    - by_day: 按星期统计
    - total_hours: 总课时
    """
    # TODO: 实现统计功能
    return {
        'total_courses': 0,
        'by_teacher': {},
        'by_classroom': {},
        'by_class': {},
        'by_day': {},
        'total_hours': 0.0
    }


@router.get('', response_model=List[CourseScheduleResponse])
async def list_schedules(
    teacher_id: str = None,
    classroom_id: str = None,
    class_id: str = None,
    date_from: str = None,
    date_to: str = None
):
    """
    查询课表列表

    ## 参数:
    - teacher_id: 教师 ID (可选)
    - classroom_id: 教室 ID (可选)
    - class_id: 班级 ID (可选)
    - date_from: 开始日期 (可选)
    - date_to: 结束日期 (可选)

    ## 返回:
    - 课表列表
    """
    # TODO: 实现查询功能
    return []


@router.get('/{schedule_id}', response_model=CourseScheduleResponse)
async def get_schedule(schedule_id: str):
    """
    获取单个课表详情

    ## 参数:
    - schedule_id: 课表 ID

    ## 返回:
    - 课表详情
    """
    # TODO: 实现查询功能
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='课表不存在'
    )
