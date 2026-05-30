"""
AI 学习助手 API 路由
基于 XEduLLM 的对话式 AI 助手
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from utils.database import get_sync_db
from models.user import User
from utils.dependencies import get_current_user_sync
from services.llm_assistant_service import (
    LLMAssistantService,
    get_llm_assistant_service,
)

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/api/v1/org/{org_id}/ai-edu/assistant", tags=["AI 学习助手"])


@router.post("/chat")
async def chat_with_assistant(
    org_id: int,
    message: str = Body(..., description="学生问题"),
    current_lesson_id: Optional[int] = Body(None, description="当前课程 ID"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    与 AI 学习助手对话

    Args:
        org_id: 组织 ID
        message: 学生问题
        current_lesson_id: 当前课程 ID（可选）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        AI 助手的回答

    Examples:
        POST /api/v1/org/1/ai-edu/assistant/chat
        {
            "message": "什么是卷积神经网络？",
            "current_lesson_id": 5
        }
    """
    try:
        logger.info(f"收到用户{current_user.id}的提问：{message[:50]}...")

        # 1. 获取课程上下文（如果提供）
        lesson_context = None
        if current_lesson_id:
            # 这里应该查询课程信息
            lesson_context = {
                "id": current_lesson_id,
                "title": f"课程{current_lesson_id}",
                "difficulty": "intermediate",
            }

        # 2. 获取助手服务（传入数据库会话以启用 Token 计费）
        service = get_llm_assistant_service(db)

        # 3. 调用对话服务
        response = await service.chat(
            user_id=current_user.id,  # type: ignore[arg-type]
            message=message,
            current_lesson_context=lesson_context,
        )

        return {
            "success": True,
            "data": response,
        }

    except HTTPException as e:
        # Token 余额不足等 HTTP 异常直接抛出
        raise
    except Exception as e:
        logger.error(f"AI 助手对话失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"对话失败：{str(e)}")


@router.get("/history")
async def get_conversation_history(
    org_id: int,
    limit: int = Query(20, ge=1, le=100, description="返回消息数量上限"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取对话历史

    Args:
        org_id: 组织 ID
        limit: 返回消息数量上限
        db: 数据库会话
        current_user: 当前用户

    Returns:
        对话历史列表
    """
    try:
        service = get_llm_assistant_service(db)

        # 获取用户对话历史
        uid: int = current_user.id  # type: ignore[assignment]
        history = service.conversation_history.get(uid, [])[-limit:]

        return {"success": True, "count": len(history), "data": history}

    except Exception as e:
        logger.error(f"获取对话历史失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history")
async def clear_conversation_history(
    org_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    清除对话历史

    Args:
        org_id: 组织 ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        操作结果
    """
    try:
        service = get_llm_assistant_service(db)
        service.clear_history(current_user.id)  # type: ignore[arg-type]

        return {"success": True, "message": "对话历史已清除"}

    except Exception as e:
        logger.error(f"清除对话历史失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_assistant_statistics(
    org_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    获取 AI 助手使用统计

    Args:
        org_id: 组织 ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        统计信息
    """
    try:
        service = get_llm_assistant_service(db)
        stats = service.get_statistics()

        return {"success": True, "data": stats}

    except Exception as e:
        logger.error(f"获取统计信息失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(
    org_id: int,
    message_id: str = Body(..., description="消息 ID"),
    rating: int = Body(..., ge=1, le=5, description="评分 1-5"),
    comment: Optional[str] = Body(None, description="反馈意见"),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """
    提交对 AI 助手的反馈

    Args:
        org_id: 组织 ID
        message_id: 消息 ID
        rating: 评分 1-5
        comment: 反馈意见
        db: 数据库会话
        current_user: 当前用户

    Returns:
        提交结果
    """
    try:
        logger.info(f"收到用户{current_user.id}对消息{message_id}的反馈：评分{rating}")

        # 这里应该保存反馈到数据库
        # 用于后续优化模型

        return {"success": True, "message": "感谢你的反馈！"}

    except Exception as e:
        logger.error(f"提交反馈失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/topics")
async def list_knowledge_base_topics(
    org_id: int,
    category: Optional[str] = Query(None, description="知识类别"),
    db: Session = Depends(get_sync_db),
):
    """
    获取知识库主题列表

    Args:
        org_id: 组织 ID
        category: 知识类别（可选）
        db: 数据库会话

    Returns:
        主题列表
    """
    try:
        service = get_llm_assistant_service(db)

        topics = []
        for cat, items in service.knowledge_base.knowledge_items.items():
            if not category or category == cat:
                for item in items:
                    topics.append(
                        {
                            "category": cat,
                            "question": item["question"],
                            "tags": item["tags"],
                        }
                    )

        return {"success": True, "count": len(topics), "data": topics}

    except Exception as e:
        logger.error(f"获取知识库主题失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
