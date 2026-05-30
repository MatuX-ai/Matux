"""
iMato 教育培训管理系统 - 学员管理 API 接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.education.models.student import StudentProfile, ParentInfo
from backend.education.schemas.student import (
    StudentProfileSchema,
    StudentProfileCreate,
    StudentProfileUpdate,
    StudentQuery,
    StudentListResponse,
)

router = APIRouter(prefix="/api/v1/students", tags=["学员管理"])


@router.get("", response_model=StudentListResponse)
def get_students(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    grade: Optional[str] = None,
    school: Optional[str] = None,
    status: Optional[str] = None,
    class_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    查询学员列表 (支持分页和筛选)

    Args:
        page: 页码
        page_size: 每页数量
        keyword: 搜索关键词 (姓名/学校)
        grade: 年级筛选
        school: 学校筛选
        status: 状态筛选
        class_id: 班级 ID

    Returns:
        学员列表响应
    """
    # 构建查询条件
    query = db.query(StudentProfile)

    if keyword:
        query = query.filter(
            (StudentProfile.name.contains(keyword)) |
            (StudentProfile.school.contains(keyword))
        )

    if grade:
        query = query.filter(StudentProfile.grade == grade)

    if school:
        query = query.filter(StudentProfile.school.contains(school))

    if status:
        query = query.filter(StudentProfile.status == status)

    if class_id:
        query = query.filter(StudentProfile.current_class_id == class_id)

    # 分页
    total = query.count()
    students = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "list": students,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{student_id}", response_model=StudentProfileSchema)
def get_student(student_id: str, db: Session = Depends(get_db)):
    """
    获取学员详情

    Args:
        student_id: 学员 ID

    Returns:
        学员详情
    """
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    return student


@router.post("", response_model=StudentProfileSchema)
def create_student(
    student_data: StudentProfileCreate,
    db: Session = Depends(get_db),
):
    """
    新增学员

    Args:
        student_data: 学员信息

    Returns:
        创建的学员信息
    """
    # 创建学员档案
    student = StudentProfile(**student_data.dict())
    db.add(student)
    db.commit()
    db.refresh(student)

    # 添加家长信息
    if student_data.parents:
        for parent_data in student_data.parents:
            parent = ParentInfo(**parent_data.dict(), student_id=student.id)
            db.add(parent)

    db.commit()
    db.refresh(student)

    return student


@router.put("/{student_id}", response_model=StudentProfileSchema)
def update_student(
    student_id: str,
    student_data: StudentProfileUpdate,
    db: Session = Depends(get_db),
):
    """
    更新学员信息

    Args:
        student_id: 学员 ID
        student_data: 更新数据

    Returns:
        更新后的学员信息
    """
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    # 更新基本信息
    update_data = student_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field != "parents":  # 家长信息单独处理
            setattr(student, field, value)

    # 更新家长信息
    if student_data.parents is not None:
        # 删除旧的家长信息
        db.query(ParentInfo).filter(ParentInfo.student_id == student_id).delete()

        # 添加新的家长信息
        for parent_data in student_data.parents:
            parent = ParentInfo(**parent_data.dict(), student_id=student_id)
            db.add(parent)

    db.commit()
    db.refresh(student)

    return student


@router.delete("/{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_db)):
    """
    删除学员

    Args:
        student_id: 学员 ID
    """
    student = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    # 删除关联的家长信息
    db.query(ParentInfo).filter(ParentInfo.student_id == student_id).delete()

    # 删除学员
    db.delete(student)
    db.commit()

    return {"message": "删除成功"}


@router.get("/{student_id}/parents", response_model=List[ParentInfo])
def get_student_parents(student_id: str, db: Session = Depends(get_db)):
    """
    获取学员的家长信息

    Args:
        student_id: 学员 ID

    Returns:
        家长信息列表
    """
    parents = db.query(ParentInfo).filter(ParentInfo.student_id == student_id).all()
    return parents
