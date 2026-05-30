"""
教育机构管理API路由
整合教师、学生、教室、课程安排等核心功能
"""

from datetime import date, datetime
import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from middleware.tenant_middleware import require_tenant_access
from models.classroom import (
    ClassroomCreate,
    ClassroomResponse,
    ClassScheduleCreate,
    ClassScheduleResponse,
)
from models.student import StudentCreate, StudentResponse
from models.teacher import TeacherCreate, TeacherResponse
from models.user import User
from services.educational_institution_service import EducationalInstitutionService
from utils.auth_utils import get_current_user_sync
from utils.database import get_sync_db

logger = logging.getLogger(__name__)

# 创建路由器实例
router = APIRouter(prefix="/api/v1/org/{org_id}", tags=["教育机构管理"])


# 依赖项
def get_institution_service(
    db: Session = Depends(get_sync_db),
) -> EducationalInstitutionService:
    """获取教育机构服务实例"""
    return EducationalInstitutionService(db)


def validate_org_access(
    org_id: int = Path(..., description="组织ID"),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
) -> bool:
    """验证用户对组织的访问权限"""
    return require_tenant_access(org_id, current_user, db)


# ==================== 教师管理API ====================


@router.post("/teachers", response_model=TeacherResponse, summary="创建教师档案")
def create_teacher(
    org_id: int = Path(..., description="组织ID"),
    teacher_data: TeacherCreate = Body(..., description="教师创建数据"),
    current_user: User = Depends(get_current_user_sync),
    institution_service: EducationalInstitutionService = Depends(
        get_institution_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    为指定组织创建教师档案
    """
    try:
        validate_org_access(org_id, current_user, db)
        teacher = institution_service.create_teacher(org_id, teacher_data, current_user)
        return teacher
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建教师档案失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建教师档案失败: {str(e)}")


@router.get("/teachers/schedule/{teacher_id}", summary="获取教师课表")
def get_teacher_schedule(
    org_id: int = Path(..., description="组织ID"),
    teacher_id: int = Path(..., description="教师ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user_sync),
    institution_service: EducationalInstitutionService = Depends(
        get_institution_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    获取指定教师的课程时间安排
    """
    try:
        validate_org_access(org_id, current_user, db)
        schedule = institution_service.get_teacher_schedule(
            org_id, teacher_id, start_date, end_date
        )
        return {"schedule": schedule}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取教师课表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取教师课表失败: {str(e)}")


# ==================== 学生管理API ====================


@router.post("/students", response_model=StudentResponse, summary="创建学生档案")
def create_student(
    org_id: int = Path(..., description="组织ID"),
    student_data: StudentCreate = Body(..., description="学生创建数据"),
    current_user: User = Depends(get_current_user_sync),
    institution_service: EducationalInstitutionService = Depends(
        get_institution_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    为指定组织创建学生档案
    """
    try:
        validate_org_access(org_id, current_user, db)
        student = institution_service.create_student(org_id, student_data, current_user)
        return student
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建学生档案失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建学生档案失败: {str(e)}")


@router.get("/students/schedule/{student_id}", summary="获取学生课表")
def get_student_schedule(
    org_id: int = Path(..., description="组织ID"),
    student_id: int = Path(..., description="学生ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user_sync),
    institution_service: EducationalInstitutionService = Depends(
        get_institution_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    获取指定学生的课程时间安排
    """
    try:
        validate_org_access(org_id, current_user, db)
        schedule = institution_service.get_student_schedule(
            org_id, student_id, start_date, end_date
        )
        return {"schedule": schedule}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取学生课表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取学生课表失败: {str(e)}")


# ==================== 教室管理API ====================


@router.post("/classrooms", response_model=ClassroomResponse, summary="创建教室")
def create_classroom(
    org_id: int = Path(..., description="组织ID"),
    classroom_data: ClassroomCreate = Body(..., description="教室创建数据"),
    current_user: User = Depends(get_current_user_sync),
    institution_service: EducationalInstitutionService = Depends(
        get_institution_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    为指定组织创建教室
    """
    try:
        validate_org_access(org_id, current_user, db)

        # 这里需要实现教室创建逻辑
        # 暂时返回模拟数据
        classroom = ClassroomResponse(
            id=1,
            org_id=org_id,
            room_number=classroom_data.room_number,
            building=classroom_data.building,
            floor=classroom_data.floor,
            capacity=classroom_data.capacity,
            room_type=classroom_data.room_type,
            has_projector=classroom_data.has_projector,
            has_computer=classroom_data.has_computer,
            has_audio_system=classroom_data.has_audio_system,
            has_whiteboard=classroom_data.has_whiteboard,
            equipment_list=classroom_data.equipment_list,
            is_available=True,
            maintenance_status=None,
            notes=classroom_data.notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        return classroom

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建教室失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建教室失败: {str(e)}")


@router.get("/classrooms/available", summary="获取可用教室")
def get_available_classrooms(
    org_id: int = Path(..., description="组织ID"),
    capacity: int = Query(1, ge=1, description="所需容纳人数"),
    date: Optional[date] = Query(None, description="查询日期"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_user_sync),
    institution_service: EducationalInstitutionService = Depends(
        get_institution_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    获取满足条件的可用教室列表
    """
    try:
        validate_org_access(org_id, current_user, db)
        available_rooms = institution_service.get_available_classrooms(
            org_id, capacity, date, start_time, end_time
        )
        return {"available_classrooms": available_rooms}
    except Exception as e:
        logger.error(f"获取可用教室失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取可用教室失败: {str(e)}")


# ==================== 排课管理API ====================


@router.post("/schedules", response_model=ClassScheduleResponse, summary="安排课程")
def schedule_class(
    org_id: int = Path(..., description="组织ID"),
    schedule_data: ClassScheduleCreate = Body(..., description="课程安排数据"),
    current_user: User = Depends(get_current_user_sync),
    institution_service: EducationalInstitutionService = Depends(
        get_institution_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    为指定组织安排课程时间
    """
    try:
        validate_org_access(org_id, current_user, db)
        schedule = institution_service.schedule_class(
            org_id, schedule_data, current_user
        )
        return schedule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"安排课程失败: {e}")
        raise HTTPException(status_code=500, detail=f"安排课程失败: {str(e)}")


# ==================== 综合查询API ====================


@router.get("/overview", summary="获取机构概览")
def get_institution_overview(
    org_id: int = Path(..., description="组织ID"),
    current_user: User = Depends(get_current_user_sync),
    institution_service: EducationalInstitutionService = Depends(
        get_institution_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    获取教育机构的综合概览信息
    """
    try:
        validate_org_access(org_id, current_user, db)
        overview = institution_service.get_institution_overview(org_id)
        return overview
    except Exception as e:
        logger.error(f"获取机构概览失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取机构概览失败: {str(e)}")


@router.get("/dashboard", summary="获取管理仪表板数据")
def get_management_dashboard(
    org_id: int = Path(..., description="组织ID"),
    current_user: User = Depends(get_current_user_sync),
    institution_service: EducationalInstitutionService = Depends(
        get_institution_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    获取教育机构管理仪表板数据
    """
    try:
        validate_org_access(org_id, current_user, db)

        # 获取各种统计数据
        overview = institution_service.get_institution_overview(org_id)

        # 获取今日课程安排
        today = date.today()
        today_schedules = institution_service.get_teacher_schedule(
            org_id, 0, today, today
        )  # 简化实现

        # 获取近期活动（示例数据）
        recent_activities = [
            {"type": "new_student", "count": 5, "period": "本周"},
            {"type": "course_completion", "count": 3, "period": "本月"},
            {"type": "maintenance_due", "count": 2, "period": "近期"},
        ]

        return {
            "overview": overview,
            "today_schedules": len(today_schedules),
            "recent_activities": recent_activities,
            "alerts": [],  # 可以添加预警信息
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"获取管理仪表板数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取管理仪表板数据失败: {str(e)}")
