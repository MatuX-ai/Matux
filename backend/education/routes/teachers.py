"""
教师管理 API 路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

router = APIRouter(prefix='/api/v1/teachers', tags=['teachers'])


@router.get('')
async def list_teachers(
    page: int = 1,
    page_size: int = 20,
    keyword: str = None,
    employment_type: str = None,
    status: str = None
):
    """查询教师列表"""
    # TODO: 实现查询功能
    return {'total': 0, 'list': [], 'page': page, 'page_size': page_size}


@router.post('')
async def create_teacher(teacher_data: dict):
    """创建教师档案"""
    # TODO: 实现创建功能
    return {'id': 'generated_id', 'message': '创建成功'}


@router.get('/{teacher_id}')
async def get_teacher(teacher_id: str):
    """获取教师详情"""
    # TODO: 实现查询功能
    raise HTTPException(status_code=404, detail='教师不存在')


@router.put('/{teacher_id}')
async def update_teacher(teacher_id: str, teacher_data: dict):
    """更新教师信息"""
    # TODO: 实现更新功能
    return {'message': '更新成功'}


@router.delete('/{teacher_id}')
async def delete_teacher(teacher_id: str):
    """删除教师"""
    # TODO: 实现删除功能
    return {'message': '删除成功'}


@router.get('/{teacher_id}/workload')
async def get_workload(teacher_id: str, month: str = None):
    """获取教师工作量统计"""
    # TODO: 实现统计功能
    return {
        'teacher_id': teacher_id,
        'total_classes': 0,
        'total_hours': 0,
        'monthly_income': 0
    }


@router.get('/{teacher_id}/salary')
async def get_salary(teacher_id: str, month: str = None):
    """获取教师工资"""
    # TODO: 实现查询功能
    return {
        'teacher_id': teacher_id,
        'month': month or '2026-03',
        'base_salary': 0,
        'teaching_income': 0,
        'net_salary': 0
    }
