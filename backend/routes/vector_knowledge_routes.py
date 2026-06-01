"""
向量知识库 API 路由

提供 RAG 检索增强生成接口：
- 知识库检索
- RAG 上下文生成
- 知识库管理（添加/统计）
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.vector_knowledge_service import get_vector_knowledge_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge-base", tags=["向量知识库"])


# ==================== 请求/响应模型 ====================

class SearchRequest(BaseModel):
    """知识检索请求"""
    query: str = Field(..., min_length=1, max_length=500)
    user_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)
    layer_filter: Optional[str] = None  # global / stage / personal
    stage: Optional[str] = None  # L1 / L2 / L3 / L4


class RAGRequest(BaseModel):
    """RAG 检索请求"""
    query: str = Field(..., min_length=1, max_length=500)
    user_id: str
    profile_seed: Optional[str] = None
    stage: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=10)


class KnowledgeAddRequest(BaseModel):
    """添加知识请求"""
    item_id: str
    content: str = Field(..., min_length=1)
    category: str
    layer: str = "global"  # global / stage / personal
    difficulty: str = "intermediate"
    tags: List[str] = []
    metadata: Optional[Dict[str, Any]] = None


class PersonalKnowledgeAddRequest(BaseModel):
    """添加个人知识请求"""
    user_id: str
    content: str = Field(..., min_length=1)
    tags: List[str] = []
    metadata: Optional[Dict[str, Any]] = None


# ==================== 路由端点 ====================

@router.post("/search")
async def search_knowledge(request: SearchRequest):
    """检索知识库"""
    service = get_vector_knowledge_service()
    results = service.search(
        query=request.query,
        user_id=request.user_id,
        top_k=request.top_k,
        layer_filter=request.layer_filter,
        stage=request.stage,
    )
    return {"results": results, "total": len(results)}


@router.post("/rag")
async def rag_retrieve(request: RAGRequest):
    """
    RAG 检索增强生成（PRD F-08-AI.3）

    分层检索 → 上下文融合 → 返回结构化上下文
    """
    service = get_vector_knowledge_service()
    result = service.rag_retrieve(
        query=request.query,
        user_id=request.user_id,
        profile_seed=request.profile_seed or "",
        stage=request.stage,
        top_k=request.top_k,
    )
    return result.to_dict()


@router.post("/knowledge")
async def add_knowledge(request: KnowledgeAddRequest):
    """添加知识到知识库"""
    from services.vector_knowledge_service import KnowledgeItem

    service = get_vector_knowledge_service()
    item = KnowledgeItem(
        item_id=request.item_id,
        content=request.content,
        category=request.category,
        layer=request.layer,
        difficulty=request.difficulty,
        tags=request.tags,
        metadata=request.metadata,
    )
    item_id = service.add_knowledge(item)
    return {"success": True, "item_id": item_id}


@router.post("/knowledge/personal")
async def add_personal_knowledge(request: PersonalKnowledgeAddRequest):
    """添加个人知识（Layer 3）"""
    service = get_vector_knowledge_service()
    item_id = service.add_personal_knowledge(
        user_id=request.user_id,
        content=request.content,
        tags=request.tags,
        metadata=request.metadata,
    )
    return {"success": True, "item_id": item_id}


@router.get("/stats")
async def get_knowledge_base_stats():
    """获取知识库统计信息"""
    service = get_vector_knowledge_service()
    return service.get_stats()
