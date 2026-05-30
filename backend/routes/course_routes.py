"""
课程路由（存根）
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/courses", tags=["课程"])


@router.get("/health")
async def health():
    return {"status": "ok"}
