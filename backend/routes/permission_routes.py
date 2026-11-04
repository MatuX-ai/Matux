"""
权限管理API接口（已解耦存根）
提供权限、角色管理及相关操作的RESTful API

⚠️ 多租户权限管理功能已解耦至 OpenMTEduInst 项目
- 此路由保留作为兼容性存根，新功能请在 OpenMTEduInst 中开发
- MatuX 仅保留学生/家长角色基础权限
"""


from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/permissions", tags=["权限管理"])


@router.get("/health")
async def health():
    return {
        "status": "decoupled",
        "message": "多租户权限管理已解耦至 OpenMTEduInst 项目"
    }