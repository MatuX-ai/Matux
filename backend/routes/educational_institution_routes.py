"""
教育机构管理API路由（已解耦存根）

⚠️ 本模块已解耦至 OpenMTEduInst 项目（STEM教育机构管理工具）
- 目标项目: OpenMTEduInst (FastAPI + Angular)
- 功能包括: 机构/校区/教师/排课/设备管理等
- 此路由保留作为兼容性存根，新功能请在 OpenMTEduInst 中开发
- 避免在 MatuX 中重复开发机构管理相关功能
"""

import logging

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/org/{org_id}", tags=["教育机构管理(已解耦)"])


@router.get("/health")
async def health():
    return {
        "status": "decoupled",
        "message": "本模块已解耦至 OpenMTEduInst 项目，完整功能请在 OpenMTEduInst 中访问"
    }
