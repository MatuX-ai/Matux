"""
统一课件库路由（已解耦存根）

⚠️ 本模块已解耦至 OpenMTSciEd 项目（开放STEM教育资源平台）
- 目标项目: OpenMTSciEd (Next.js + Neo4j)
- API端点: localhost:3000/api/v1
- 功能包括: 教程/课件/知识图谱/硬件项目资源等
- 此路由保留作为兼容性存根，新功能请在 OpenMTSciEd 中开发
- 避免在 MatuX 中重复开发课件管理相关功能
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/materials", tags=["统一课件库"])


@router.get("/health")
async def health():
    return {"status": "ok"}
