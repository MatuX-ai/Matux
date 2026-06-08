"""
OpenSciEDU 公共课程 API 路由

提供与 OpenSciEDU 平台集成的 REST API 接口
支持课程目录、知识图谱和搜索功能

基于 PRD F-18: OpenSciEDU 公共课程自动接入
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.opensciedu_service import (
    CourseDetail,
    CourseListResponse,
    CourseCategory,
    KnowledgeGraphData,
    SearchResult,
    get_opensciedu_service,
    OpenSciEDUService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/opensciedu", tags=["OpenSciEDU 公共课程"])


# ==================== 依赖注入 ====================

def get_opensciedu() -> OpenSciEDUService:
    """获取 OpenSciEDU 服务实例"""
    return get_opensciedu_service()


# ==================== 请求/响应模型 ====================

class CourseListRequest(BaseModel):
    """课程列表请求"""
    page: int = 1
    page_size: int = 20
    category: Optional[str] = None
    difficulty: Optional[str] = None
    sort_by: str = "created_at"


class SearchRequest(BaseModel):
    """搜索请求"""
    keyword: str
    page: int = 1
    page_size: int = 20


class ApiResponse(BaseModel):
    """通用 API 响应"""
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None


# ==================== API 路由 ====================

@router.get("/courses", response_model=CourseListResponse)
async def get_public_courses(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(default=None, description="分类筛选"),
    difficulty: Optional[str] = Query(default=None, description="难度筛选"),
    sort_by: str = Query(default="created_at", description="排序字段"),
    service: OpenSciEDUService = Depends(get_opensciedu)
) -> CourseListResponse:
    """
    获取公共课程列表

    从 OpenSciEDU 平台获取公开课程目录
    """
    try:
        result = await service.get_public_courses(
            page=page,
            page_size=page_size,
            category=category,
            difficulty=difficulty,
            sort_by=sort_by
        )
        return result
    except Exception as e:
        logger.error(f"获取课程列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取课程列表失败: {str(e)}")


@router.get("/courses/{course_id}", response_model=CourseDetail)
async def get_course_detail(
    course_id: str,
    service: OpenSciEDUService = Depends(get_opensciedu)
) -> CourseDetail:
    """
    获取课程详情

    Args:
        course_id: 课程 ID
    """
    result = await service.get_course_detail(course_id)

    if result is None:
        raise HTTPException(status_code=404, detail=f"课程不存在: {course_id}")

    return result


@router.get("/knowledge-graph", response_model=KnowledgeGraphData)
async def get_knowledge_graph(
    refresh: bool = Query(default=False, description="强制刷新缓存"),
    service: OpenSciEDUService = Depends(get_opensciedu)
) -> KnowledgeGraphData:
    """
    获取知识图谱

    返回 OpenSciEDU 平台的知识点关系图谱
    """
    result = await service.get_knowledge_graph(force_refresh=refresh)

    if result is None:
        raise HTTPException(status_code=503, detail="知识图谱服务暂不可用")

    return result


@router.get("/search", response_model=SearchResult)
async def search_courses(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    service: OpenSciEDUService = Depends(get_opensciedu)
) -> SearchResult:
    """
    搜索课程

    Args:
        keyword: 搜索关键词
        page: 页码
        page_size: 每页数量
    """
    try:
        result = await service.search_courses(
            keyword=keyword,
            page=page,
            page_size=page_size
        )
        return result
    except Exception as e:
        logger.error(f"搜索课程失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/categories", response_model=list[CourseCategory])
async def get_categories(
    service: OpenSciEDUService = Depends(get_opensciedu)
) -> list[CourseCategory]:
    """
    获取课程分类列表
    """
    try:
        categories = await service.get_categories()
        return categories
    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分类失败: {str(e)}")


@router.get("/health")
async def health_check(
    service: OpenSciEDUService = Depends(get_opensciedu)
) -> dict:
    """
    健康检查

    检查 OpenSciEDU API 连接状态
    """
    is_healthy = await service.health_check()

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "opensciedu",
        "api_url": service.api_url
    }


@router.post("/cache/clear")
async def clear_cache(
    service: OpenSciEDUService = Depends(get_opensciedu)
) -> dict:
    """
    清除缓存

    清除 OpenSciEDU 服务的本地缓存
    """
    service.clear_cache()
    logger.info("OpenSciEDU 缓存已清除")

    return {
        "success": True,
        "message": "缓存已清除"
    }
