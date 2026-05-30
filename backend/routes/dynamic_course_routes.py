"""
动态课程路由（存根）
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/dynamic-courses", tags=["动态课程"])


@router.get("/health")
async def health():
    return {"status": "ok"}
