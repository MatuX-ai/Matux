"""
用户许可证路由（存根）
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/user-licenses", tags=["用户许可证"])


@router.get("/health")
async def health():
    return {"status": "ok"}
