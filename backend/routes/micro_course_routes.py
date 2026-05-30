"""
微课程转化 API 路由（桩）
O2.3 微课程转化功能模块
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/micro-course", tags=["微课程转化"])


@router.get("/")
async def list_micro_courses():
    """获取微课程列表"""
    return {"success": True, "data": [], "count": 0}
