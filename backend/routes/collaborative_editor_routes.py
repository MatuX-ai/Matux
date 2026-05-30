"""
协作编辑API路由
提供实时协同编辑、评论批注等接口
"""

from datetime import datetime
import json
import logging
from typing import Dict, List, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlalchemy.orm import Session

from middleware.tenant_middleware import require_tenant_access
from models.collaborative_editor import (
    CollaborativeDocumentCreate,
    CollaborativeDocumentResponse,
    DocumentComment,
    DocumentCommentCreate,
    DocumentCommentResponse,
    DocumentOperationCreate,
    DocumentOperationResponse,
    DocumentSessionResponse,
    DocumentSuggestionCreate,
    DocumentSuggestionResponse,
)
from models.user import User
from services.collaborative_editor_service import (
    CollaborativeEditorService,
    get_collaborative_editor_service,
)
from utils.auth_utils import get_current_user_sync
from utils.database import get_sync_db

logger = logging.getLogger(__name__)

# 创建路由器实例
router = APIRouter(
    prefix="/api/v1/org/{org_id}/courses/{course_id}/collaborative-documents",
    tags=["协作编辑"],
)


# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.document_sessions: Dict[str, List[str]] = (
            {}
        )  # document_id -> [session_ids]

    async def connect(self, websocket: WebSocket, document_id: str, session_id: str):
        await websocket.accept()
        if document_id not in self.active_connections:
            self.active_connections[document_id] = []
        self.active_connections[document_id].append(websocket)

        if document_id not in self.document_sessions:
            self.document_sessions[document_id] = []
        self.document_sessions[document_id].append(session_id)

        logger.info(f"WebSocket连接建立: document={document_id}, session={session_id}")

    def disconnect(self, websocket: WebSocket, document_id: str, session_id: str):
        if document_id in self.active_connections:
            if websocket in self.active_connections[document_id]:
                self.active_connections[document_id].remove(websocket)
            if not self.active_connections[document_id]:  # 如果该文档没有连接了
                del self.active_connections[document_id]

        if document_id in self.document_sessions:
            if session_id in self.document_sessions[document_id]:
                self.document_sessions[document_id].remove(session_id)
            if not self.document_sessions[document_id]:  # 如果该文档没有会话了
                del self.document_sessions[document_id]

        logger.info(f"WebSocket连接断开: document={document_id}, session={session_id}")

    async def broadcast(
        self, document_id: str, message: str, exclude_session: Optional[str] = None
    ):
        """广播消息给指定文档的所有连接"""
        if document_id in self.active_connections:
            for connection in self.active_connections[document_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"发送WebSocket消息失败: {e}")


manager = ConnectionManager()


# 依赖项
def validate_course_access(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
) -> bool:
    """验证用户对课程的访问权限"""
    return require_tenant_access(org_id, current_user, db)


# 文档管理API
@router.post("/", response_model=CollaborativeDocumentResponse, summary="创建协作文档")
def create_document(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    doc_data: CollaborativeDocumentCreate = Body(..., description="文档创建数据"),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    创建新的协作文档
    """
    try:
        # 验证权限
        validate_course_access(org_id, course_id, current_user, db)

        document = editor_service.create_document(
            course_id, org_id, doc_data, current_user
        )
        return document
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建文档失败: {str(e)}")


@router.get(
    "/{document_id}",
    response_model=CollaborativeDocumentResponse,
    summary="获取文档详情",
)
def get_document(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    document_id: int = Path(..., description="文档ID"),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    获取指定协作文档的详细信息
    """
    try:
        # 验证权限
        validate_course_access(org_id, course_id, current_user, db)

        document = editor_service.get_document(document_id, org_id)
        if not document:
            raise HTTPException(status_code=404, detail="文档不存在")

        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档失败: {str(e)}")


@router.put(
    "/{document_id}/content",
    response_model=CollaborativeDocumentResponse,
    summary="更新文档内容",
)
def update_document_content(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    document_id: int = Path(..., description="文档ID"),
    content: str = Body(..., embed=True, description="新文档内容"),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    直接更新文档内容（非实时协作方式）
    """
    try:
        # 验证权限
        validate_course_access(org_id, course_id, current_user, db)

        document = editor_service.update_document_content(
            document_id, org_id, content, current_user
        )
        return document
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新文档内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新文档内容失败: {str(e)}")


# 实时协作API
@router.post("/{document_id}/operations/batch", summary="批量应用操作")
def apply_operations_batch(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    document_id: int = Path(..., description="文档ID"),
    operations: List[DocumentOperationCreate] = Body(..., description="操作列表"),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    批量应用文档操作，支持OT算法转换
    """
    try:
        # 验证权限
        validate_course_access(org_id, course_id, current_user, db)

        transformed_ops, new_content = editor_service.apply_operations(
            document_id, org_id, operations, current_user
        )

        # 广播操作给其他用户
        operation_data = {
            "type": "operations_applied",
            "document_id": document_id,
            "operations": [
                {
                    "id": op.id,
                    "operation_type": op.operation_type,
                    "position": op.position,
                    "content": op.content,
                    "client_id": op.client_id,
                    "user_id": op.user_id,
                    "timestamp": op.timestamp.isoformat(),
                }
                for op in transformed_ops
            ],
            "new_content": new_content,
            "sender": current_user.email,
        }

        import asyncio

        asyncio.create_task(
            manager.broadcast(str(document_id), json.dumps(operation_data))
        )

        return {
            "success": True,
            "transformed_operations": transformed_ops,
            "new_content": new_content,
            "new_version": editor_service.get_document(
                document_id, org_id
            ).version_number,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"应用操作失败: {e}")
        raise HTTPException(status_code=500, detail=f"应用操作失败: {str(e)}")


@router.get(
    "/{document_id}/operations",
    response_model=List[DocumentOperationResponse],
    summary="获取操作历史",
)
def get_document_operations(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    document_id: int = Path(..., description="文档ID"),
    from_revision: int = Query(0, description="起始修订版本"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    获取文档的操作历史记录
    """
    try:
        # 验证权限
        validate_course_access(org_id, course_id, current_user, db)

        operations = editor_service.get_document_operations(document_id, from_revision)
        return operations[:limit]
    except Exception as e:
        logger.error(f"获取操作历史失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取操作历史失败: {str(e)}")


# 评论API
@router.post(
    "/{document_id}/comments",
    response_model=DocumentCommentResponse,
    summary="添加评论",
)
def create_comment(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    document_id: int = Path(..., description="文档ID"),
    comment_data: DocumentCommentCreate = Body(..., description="评论数据"),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    在文档指定位置添加评论
    """
    try:
        # 验证权限
        validate_course_access(org_id, course_id, current_user, db)

        comment = editor_service.create_comment(
            document_id, org_id, comment_data, current_user
        )

        # 广播评论给其他用户
        comment_data_broadcast = {
            "type": "comment_added",
            "document_id": document_id,
            "comment": {
                "id": comment.id,
                "user_id": comment.user_id,
                "user_name": current_user.name,
                "content": comment.content,
                "start_position": comment.start_position,
                "end_position": comment.end_position,
                "comment_type": comment.comment_type,
                "created_at": comment.created_at.isoformat(),
            },
        }

        import asyncio

        asyncio.create_task(
            manager.broadcast(str(document_id), json.dumps(comment_data_broadcast))
        )

        return comment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加评论失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加评论失败: {str(e)}")


@router.get(
    "/{document_id}/comments",
    response_model=List[DocumentCommentResponse],
    summary="获取文档评论",
)
def get_document_comments(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    document_id: int = Path(..., description="文档ID"),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    获取文档的所有评论
    """
    try:
        # 验证权限
        validate_course_access(org_id, course_id, current_user, db)

        comments = editor_service.get_document_comments(document_id)
        return comments
    except Exception as e:
        logger.error(f"获取评论失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取评论失败: {str(e)}")


@router.put("/{document_id}/comments/{comment_id}/resolve", summary="解决评论")
def resolve_comment(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    document_id: int = Path(..., description="文档ID"),
    comment_id: int = Path(..., description="评论ID"),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    标记评论为已解决
    """
    try:
        # 验证权限
        validate_course_access(org_id, course_id, current_user, db)

        comment = (
            db.query(DocumentComment)
            .filter(
                DocumentComment.id == comment_id,
                DocumentComment.document_id == document_id,
            )
            .first()
        )

        if not comment:
            raise HTTPException(status_code=404, detail="评论不存在")

        comment.is_resolved = True
        comment.resolved_at = datetime.utcnow()
        comment.resolved_by = current_user.id

        db.commit()

        # 广播评论解决状态
        resolve_data = {
            "type": "comment_resolved",
            "document_id": document_id,
            "comment_id": comment_id,
            "resolved_by": current_user.email,
        }

        import asyncio

        asyncio.create_task(
            manager.broadcast(str(document_id), json.dumps(resolve_data))
        )

        return {"success": True, "message": "评论已标记为已解决"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解决评论失败: {e}")
        raise HTTPException(status_code=500, detail=f"解决评论失败: {str(e)}")


# 建议API
@router.post(
    "/{document_id}/suggestions",
    response_model=DocumentSuggestionResponse,
    summary="添加建议",
)
def create_suggestion(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    document_id: int = Path(..., description="文档ID"),
    suggestion_data: DocumentSuggestionCreate = Body(..., description="建议数据"),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    在文档指定位置添加修改建议
    """
    try:
        # 验证权限
        validate_course_access(org_id, course_id, current_user, db)

        suggestion = editor_service.create_suggestion(
            document_id, org_id, suggestion_data, current_user
        )

        # 广播建议给其他用户
        suggestion_data_broadcast = {
            "type": "suggestion_added",
            "document_id": document_id,
            "suggestion": {
                "id": suggestion.id,
                "user_id": suggestion.user_id,
                "user_name": current_user.name,
                "original_content": suggestion.original_content,
                "suggested_content": suggestion.suggested_content,
                "start_position": suggestion.start_position,
                "end_position": suggestion.end_position,
                "reason": suggestion.suggestion_reason,
                "created_at": suggestion.created_at.isoformat(),
            },
        }

        import asyncio

        asyncio.create_task(
            manager.broadcast(str(document_id), json.dumps(suggestion_data_broadcast))
        )

        return suggestion
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"添加建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"添加建议失败: {str(e)}")


@router.put("/{document_id}/suggestions/{suggestion_id}/review", summary="审核建议")
def review_suggestion(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    document_id: int = Path(..., description="文档ID"),
    suggestion_id: int = Path(..., description="建议ID"),
    status: str = Body(
        ..., embed=True, pattern="^(accepted|rejected)$", description="审核结果"
    ),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    审核并处理文档建议
    """
    try:
        # 验证权限
        validate_course_access(org_id, course_id, current_user, db)

        suggestion = editor_service.review_suggestion(
            suggestion_id, org_id, status, current_user
        )

        # 广播审核结果
        review_data = {
            "type": "suggestion_reviewed",
            "document_id": document_id,
            "suggestion_id": suggestion_id,
            "status": status,
            "reviewed_by": current_user.email,
        }

        import asyncio

        asyncio.create_task(
            manager.broadcast(str(document_id), json.dumps(review_data))
        )

        return {"success": True, "suggestion": suggestion}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"审核建议失败: {e}")
        raise HTTPException(status_code=500, detail=f"审核建议失败: {str(e)}")


# 会话管理API
@router.post(
    "/{document_id}/sessions",
    response_model=DocumentSessionResponse,
    summary="加入文档会话",
)
def join_session(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    document_id: int = Path(..., description="文档ID"),
    client_id: str = Body(..., embed=True, description="客户端标识"),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    加入文档协作会话
    """
    try:
        # 验证权限
        validate_course_access(org_id, course_id, current_user, db)

        session = editor_service.create_session(
            document_id, org_id, client_id, current_user
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"加入会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"加入会话失败: {str(e)}")


@router.put("/sessions/{session_id}/cursor", summary="更新光标位置")
def update_cursor_position(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    session_id: str = Path(..., description="会话ID"),
    cursor_position: int = Body(..., ge=0, embed=True, description="光标位置"),
    selection_start: Optional[int] = Body(
        None, ge=0, embed=True, description="选区开始位置"
    ),
    selection_end: Optional[int] = Body(
        None, ge=0, embed=True, description="选区结束位置"
    ),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    更新用户在文档中的光标位置和选区
    """
    try:
        session = editor_service.update_session_cursor(
            session_id, cursor_position, selection_start, selection_end
        )

        # 广播光标更新
        cursor_data = {
            "type": "cursor_update",
            "session_id": session_id,
            "user_id": session.user_id,
            "user_name": current_user.name,
            "cursor_position": cursor_position,
            "selection_start": selection_start,
            "selection_end": selection_end,
        }

        import asyncio

        asyncio.create_task(
            manager.broadcast(
                str(session.document_id), json.dumps(cursor_data), session_id
            )
        )

        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新光标位置失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新光标位置失败: {str(e)}")


@router.delete("/sessions/{session_id}", summary="离开文档会话")
def leave_session(
    org_id: int = Path(..., description="组织ID"),
    course_id: int = Path(..., description="课程ID"),
    session_id: str = Path(..., description="会话ID"),
    current_user: User = Depends(get_current_user_sync),
    editor_service: CollaborativeEditorService = Depends(
        get_collaborative_editor_service
    ),
    db: Session = Depends(get_sync_db),
):
    """
    离开文档协作会话
    """
    try:
        session = editor_service.end_session(session_id)

        # 广播用户离开消息
        leave_data = {
            "type": "user_left",
            "session_id": session_id,
            "user_id": session.user_id,
            "user_name": (
                current_user.name
                if hasattr(current_user, "name")
                else current_user.email
            ),
        }

        import asyncio

        asyncio.create_task(
            manager.broadcast(str(session.document_id), json.dumps(leave_data))
        )

        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"离开会话失败: {e}")
        raise HTTPException(status_code=500, detail=f"离开会话失败: {str(e)}")


# WebSocket端点
@router.websocket("/{document_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    document_id: int = Path(..., description="文档ID"),
    session_id: str = Query(..., description="会话ID"),
):
    """
    WebSocket实时协作连接端点
    """
    await manager.connect(websocket, str(document_id), session_id)

    try:
        while True:
            data = await websocket.receive_text()
            # 处理收到的消息
            json.loads(data)

            # 可以在这里添加消息处理逻辑
            # 例如：心跳检测、用户状态同步等

    except WebSocketDisconnect:
        manager.disconnect(websocket, str(document_id), session_id)
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
        manager.disconnect(websocket, str(document_id), session_id)
