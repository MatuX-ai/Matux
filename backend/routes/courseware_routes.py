"""
课件图谱闭包表 - API 路由

提供课件节点层级管理的 RESTful API 接口
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from utils.database import get_db
from schemas.courseware_closure import (
    BatchNodeCreate,
    BatchNodeCreateResponse,
    BatchDeleteResponse,
    CoursewareNodeCreate,
    CoursewareNodeListResponse,
    CoursewareNodeMove,
    CoursewareNodeResponse,
    CoursewareNodeUpdate,
    CoursewareSubtreeResponse,
    CoursewareTreeNode,
    HierarchyResponse,
    LevelNodesResponse,
    NodePath,
    ClosureValidationResult,
    MigrationResult,
    RollbackResult,
)
from services.courseware_service import CoursewareService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/courseware", tags=["课件图谱"])


def get_service(db: AsyncSession = Depends(get_db)) -> CoursewareService:
    return CoursewareService(db)


# ==================== 节点 CRUD ====================

@router.post("/nodes", response_model=CoursewareNodeResponse, status_code=201)
async def create_node(
    data: CoursewareNodeCreate,
    service: CoursewareService = Depends(get_service),
):
    """创建课件节点"""
    node = await service.create_node(data.model_dump())
    if node is None:
        raise HTTPException(status_code=500, detail="创建节点失败")
    return node


@router.get("/nodes/{node_id}", response_model=CoursewareNodeResponse)
async def get_node(
    node_id: int,
    service: CoursewareService = Depends(get_service),
):
    """获取课件节点"""
    node = await service.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"节点不存在: {node_id}")
    return node


@router.put("/nodes/{node_id}", response_model=CoursewareNodeResponse)
async def update_node(
    node_id: int,
    data: CoursewareNodeUpdate,
    service: CoursewareService = Depends(get_service),
):
    """更新课件节点"""
    node = await service.update_node(node_id, data.model_dump(exclude_none=True))
    if node is None:
        raise HTTPException(status_code=404, detail=f"节点不存在: {node_id}")
    return node


@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: int,
    cascade: bool = Query(default=True, description="是否级联删除所有后代"),
    service: CoursewareService = Depends(get_service),
):
    """删除课件节点"""
    success = await service.delete_node(node_id, cascade=cascade)
    if not success:
        raise HTTPException(status_code=404, detail=f"节点不存在: {node_id}")
    return {"success": True, "message": "节点已删除"}


@router.put("/nodes/{node_id}/move")
async def move_node(
    node_id: int,
    data: CoursewareNodeMove,
    service: CoursewareService = Depends(get_service),
):
    """移动节点到新的父节点下"""
    success = await service.move_node(node_id, data.new_parent_id)
    if not success:
        raise HTTPException(status_code=400, detail="移动节点失败，可能存在循环引用或节点不存在")
    return {"success": True, "message": "节点已移动"}


# ==================== 层级查询 ====================

@router.get("/nodes/{node_id}/hierarchy", response_model=HierarchyResponse)
async def get_hierarchy(
    node_id: int,
    service: CoursewareService = Depends(get_service),
):
    """获取节点的完整层级信息（祖先+后代+子节点）"""
    result = await service.get_hierarchy(node_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"节点不存在: {node_id}")
    return result


@router.get("/nodes/{node_id}/ancestors")
async def get_ancestors(
    node_id: int,
    service: CoursewareService = Depends(get_service),
):
    """获取节点的所有祖先节点"""
    ancestors = await service.get_ancestors(node_id)
    return {"node_id": node_id, "ancestors": ancestors, "count": len(ancestors)}


@router.get("/nodes/{node_id}/descendants")
async def get_descendants(
    node_id: int,
    max_depth: Optional[int] = Query(None, ge=1, description="最大层级深度"),
    service: CoursewareService = Depends(get_service),
):
    """获取节点的所有后代节点"""
    descendants = await service.get_descendants(node_id, max_depth=max_depth)
    return {"node_id": node_id, "descendants": descendants, "count": len(descendants)}


@router.get("/nodes/{node_id}/level/{level}", response_model=LevelNodesResponse)
async def get_nodes_at_level(
    node_id: int,
    level: int,
    service: CoursewareService = Depends(get_service),
):
    """获取指定节点下特定层级的节点"""
    return await service.get_nodes_at_level(node_id, level)


@router.get("/nodes/{node_id}/path", response_model=NodePath)
async def get_path(
    node_id: int,
    service: CoursewareService = Depends(get_service),
):
    """获取从根节点到指定节点的完整路径"""
    result = await service.get_path(node_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"节点不存在: {node_id}")
    return result


@router.get("/nodes/{node_id}/subtree", response_model=CoursewareSubtreeResponse)
async def get_subtree(
    node_id: int,
    service: CoursewareService = Depends(get_service),
):
    """获取节点的完整子树"""
    result = await service.get_subtree(node_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"节点不存在: {node_id}")
    return result


# ==================== 列表查询 ====================

@router.get("/nodes")
async def list_nodes(
    course_id: Optional[int] = Query(None, description="课程ID"),
    node_type: Optional[str] = Query(None, description="节点类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: CoursewareService = Depends(get_service),
):
    """分页列出节点"""
    return await service.list_nodes(
        course_id=course_id,
        node_type=node_type,
        is_active=is_active,
        skip=skip,
        limit=limit,
    )


@router.get("/roots")
async def get_roots(
    course_id: Optional[int] = Query(None, description="课程ID"),
    service: CoursewareService = Depends(get_service),
):
    """获取根节点列表"""
    roots = await service.get_roots(course_id=course_id)
    return {"roots": roots, "count": len(roots)}


# ==================== 批量操作 ====================

@router.post("/nodes/batch", response_model=BatchNodeCreateResponse, status_code=201)
async def batch_create_nodes(
    data: BatchNodeCreate,
    service: CoursewareService = Depends(get_service),
):
    """批量创建节点"""
    return await service.batch_create_nodes(data)


@router.delete("/nodes/batch", response_model=BatchDeleteResponse)
async def batch_delete_nodes(
    node_ids: list[int],
    cascade: bool = Query(default=True),
    service: CoursewareService = Depends(get_service),
):
    """批量删除节点"""
    deleted = 0
    errors = []
    for node_id in node_ids:
        try:
            success = await service.delete_node(node_id, cascade=cascade)
            if success:
                deleted += 1
            else:
                errors.append({"node_id": node_id, "error": "节点不存在"})
        except Exception as e:
            errors.append({"node_id": node_id, "error": str(e)})
    return BatchDeleteResponse(deleted=deleted, errors=errors)


# ==================== 一致性验证 ====================

@router.get("/validate", response_model=ClosureValidationResult)
async def validate_closure(
    service: CoursewareService = Depends(get_service),
):
    """验证闭包表数据一致性"""
    return await service.validate()


@router.post("/repair")
async def repair_closure(
    service: CoursewareService = Depends(get_service),
):
    """修复闭包表常见问题"""
    repaired = await service.repair()
    return {"success": True, "repaired": repaired}