"""
课程版本路由（存根）
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/course-versions", tags=["课程版本"])


@router.get("/health")
async def health():
    return {"status": "ok"}
