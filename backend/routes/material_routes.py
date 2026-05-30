"""
统一课件库路由（存根）
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/materials", tags=["统一课件库"])


@router.get("/health")
async def health():
    return {"status": "ok"}
