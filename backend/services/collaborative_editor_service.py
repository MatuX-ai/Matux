"""
协作编辑服务
实现Operational Transformation算法和实时协同编辑功能
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

from fastapi import Depends
from sqlalchemy.orm import Session

from models.collaborative_editor import (
    CollaborativeDocument,
    CollaborativeDocumentCreate,
    DocumentComment,
    DocumentCommentCreate,
    DocumentOperation,
    DocumentOperationCreate,
    DocumentSession,
    DocumentSuggestion,
    DocumentSuggestionCreate,
)
from models.user import User
from utils.database import get_sync_db

logger = logging.getLogger(__name__)


class OperationalTransformation:
    """Operational Transformation算法实现"""

    @staticmethod
    def transform(op1: Dict[str, Any], op2: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换操作op1使其能与op2并发执行

        Args:
            op1: 第一个操作
            op2: 第二个操作

        Returns:
            转换后的操作
        """
        if op1["operation_type"] == "insert" and op2["operation_type"] == "insert":
            return OperationalTransformation._transform_insert_insert(op1, op2)
        elif op1["operation_type"] == "insert" and op2["operation_type"] == "delete":
            return OperationalTransformation._transform_insert_delete(op1, op2)
        elif op1["operation_type"] == "delete" and op2["operation_type"] == "insert":
            return OperationalTransformation._transform_delete_insert(op1, op2)
        elif op1["operation_type"] == "delete" and op2["operation_type"] == "delete":
            return OperationalTransformation._transform_delete_delete(op1, op2)
        else:
            return op1

    @staticmethod
    def _transform_insert_insert(
        op1: Dict[str, Any], op2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """转换两个插入操作"""
        pos1, pos2 = op1["position"], op2["position"]

        if pos1 < pos2:
            # op1在op2之前，不需要调整
            return op1
        elif pos1 > pos2:
            # op1在op2之后，需要调整位置
            return {**op1, "position": pos1 + len(op2["content"])}
        else:
            # 同一位置插入，根据客户端ID决定顺序
            if op1.get("client_id", "") < op2.get("client_id", ""):
                return op1
            else:
                return {**op1, "position": pos1 + len(op2["content"])}

    @staticmethod
    def _transform_insert_delete(
        op1: Dict[str, Any], op2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """转换插入和删除操作"""
        insert_pos = op1["position"]
        delete_pos = op2["position"]
        delete_len = len(op2["content"]) if op2["content"] else 1

        if insert_pos <= delete_pos:
            # 插入在删除之前，不需要调整
            return op1
        else:
            # 插入在删除之后，需要调整位置
            return {**op1, "position": insert_pos - delete_len}

    @staticmethod
    def _transform_delete_insert(
        op1: Dict[str, Any], op2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """转换删除和插入操作"""
        delete_pos = op1["position"]
        insert_pos = op2["position"]
        delete_len = len(op1["content"]) if op1["content"] else 1

        if insert_pos <= delete_pos:
            # 插入在删除之前，不需要调整
            return op1
        elif insert_pos >= delete_pos + delete_len:
            # 插入在删除范围之后，需要调整位置
            return {**op1, "position": insert_pos - len(op2["content"])}
        else:
            # 插入在删除范围内，调整删除操作
            overlap_start = max(delete_pos, insert_pos)
            overlap_end = min(delete_pos + delete_len, insert_pos + len(op2["content"]))
            overlap_end - overlap_start

            return (
                {
                    **op1,
                    "position": delete_pos,
                    "content": op1["content"][: overlap_start - delete_pos]
                    + op1["content"][overlap_end - delete_pos :],
                }
                if op1["content"]
                else op1
            )

    @staticmethod
    def _transform_delete_delete(
        op1: Dict[str, Any], op2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """转换两个删除操作"""
        pos1, pos2 = op1["position"], op2["position"]
        len1 = len(op1["content"]) if op1["content"] else 1
        len2 = len(op2["content"]) if op2["content"] else 1

        if pos1 + len1 <= pos2:
            # op1完全在op2之前
            return op1
        elif pos2 + len2 <= pos1:
            # op2完全在op1之前
            return {**op1, "position": pos1 - len2}
        else:
            # 操作重叠，需要合并删除范围
            start = min(pos1, pos2)
            max(pos1 + len1, pos2 + len2)

            return {**op1, "position": start, "content": ""}  # 重叠部分被完全删除


class CollaborativeEditorService:
    """协作编辑服务主类"""

    def __init__(self, db: Session):
        self.db = db
        self.ot = OperationalTransformation()

    def create_document(
        self,
        course_id: int,
        org_id: int,
        doc_data: CollaborativeDocumentCreate,
        current_user: User,
    ) -> CollaborativeDocument:
        """创建协作文档"""
        try:
            document = CollaborativeDocument(
                course_id=course_id,
                org_id=org_id,
                document_name=doc_data.document_name,
                document_type=doc_data.document_type,
                content=doc_data.content,
                allow_comments=doc_data.allow_comments,
                allow_suggestions=doc_data.allow_suggestions,
                version_number=1,
            )

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            logger.info(f"创建协作文档: {document.id} by user {current_user.id}")
            return document

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建文档失败: {e}")
            raise

    def get_document(
        self, document_id: int, org_id: int
    ) -> Optional[CollaborativeDocument]:
        """获取文档"""
        return (
            self.db.query(CollaborativeDocument)
            .filter(
                CollaborativeDocument.id == document_id,
                CollaborativeDocument.org_id == org_id,
            )
            .first()
        )

    def update_document_content(
        self, document_id: int, org_id: int, new_content: str, current_user: User
    ) -> CollaborativeDocument:
        """更新文档内容"""
        document = self.get_document(document_id, org_id)
        if not document:
            raise ValueError("文档不存在")

        # 检查锁定状态
        if document.is_locked and document.locked_by != current_user.id:
            raise ValueError("文档已被其他用户锁定")

        document.content = new_content
        document.version_number += 1
        document.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(document)

        return document

    def apply_operations(
        self,
        document_id: int,
        org_id: int,
        operations: List[DocumentOperationCreate],
        current_user: User,
    ) -> Tuple[List[DocumentOperation], str]:
        """
        应用操作序列到文档

        Returns:
            (转换后的操作列表, 更新后的文档内容)
        """
        document = self.get_document(document_id, org_id)
        if not document:
            raise ValueError("文档不存在")

        # 检查锁定状态
        if document.is_locked and document.locked_by != current_user.id:
            raise ValueError("文档已被其他用户锁定")

        # 获取当前最新版本的操作
        latest_revision = self._get_latest_revision(document_id)

        # 对每个操作进行OT转换
        transformed_operations = []
        document_content = document.content

        for op_data in operations:
            # 创建操作对象
            operation = DocumentOperation(
                document_id=document_id,
                user_id=current_user.id,
                operation_type=op_data.operation_type,
                position=op_data.position,
                content=op_data.content,
                client_id=op_data.client_id,
                revision=latest_revision + 1,
            )

            # 应用操作到文档内容
            document_content = self._apply_operation_to_content(
                document_content, operation
            )

            self.db.add(operation)
            transformed_operations.append(operation)

        # 更新文档内容和版本
        document.content = document_content
        document.version_number += 1
        document.updated_at = datetime.utcnow()

        self.db.commit()

        # 刷新操作对象
        for op in transformed_operations:
            self.db.refresh(op)

        return transformed_operations, document_content

    def _get_latest_revision(self, document_id: int) -> int:
        """获取文档的最新修订版本号"""
        latest_op = (
            self.db.query(DocumentOperation)
            .filter(DocumentOperation.document_id == document_id)
            .order_by(DocumentOperation.revision.desc())
            .first()
        )

        return latest_op.revision if latest_op else 0

    def _apply_operation_to_content(
        self, content: str, operation: DocumentOperation
    ) -> str:
        """将操作应用到文档内容"""
        pos = operation.position

        if operation.operation_type == "insert":
            if pos >= len(content):
                return content + (operation.content or "")
            else:
                return content[:pos] + (operation.content or "") + content[pos:]

        elif operation.operation_type == "delete":
            delete_len = len(operation.content) if operation.content else 1
            if pos >= len(content):
                return content
            elif pos + delete_len >= len(content):
                return content[:pos]
            else:
                return content[:pos] + content[pos + delete_len :]

        elif operation.operation_type == "update":
            # 更新操作视为删除+插入
            delete_len = (
                len(operation.content or "") if hasattr(operation, "old_content") else 1
            )
            insert_content = operation.content or ""

            if pos >= len(content):
                return content + insert_content
            elif pos + delete_len >= len(content):
                return content[:pos] + insert_content
            else:
                return content[:pos] + insert_content + content[pos + delete_len :]

        return content

    def get_document_operations(
        self, document_id: int, from_revision: int = 0
    ) -> List[DocumentOperation]:
        """获取文档的操作历史"""
        return (
            self.db.query(DocumentOperation)
            .filter(
                DocumentOperation.document_id == document_id,
                DocumentOperation.revision > from_revision,
            )
            .order_by(DocumentOperation.revision.asc())
            .all()
        )

    def create_comment(
        self,
        document_id: int,
        org_id: int,
        comment_data: DocumentCommentCreate,
        current_user: User,
    ) -> DocumentComment:
        """创建文档评论"""
        document = self.get_document(document_id, org_id)
        if not document:
            raise ValueError("文档不存在")

        if not document.allow_comments:
            raise ValueError("此文档不允许添加评论")

        # 验证位置有效性
        if comment_data.end_position > len(document.content):
            raise ValueError("评论位置超出文档范围")

        # 提取被引用的内容
        referenced_content = (
            document.content[comment_data.start_position : comment_data.end_position]
            if comment_data.referenced_content is None
            else comment_data.referenced_content
        )

        comment = DocumentComment(
            document_id=document_id,
            user_id=current_user.id,
            start_position=comment_data.start_position,
            end_position=comment_data.end_position,
            content=comment_data.content,
            comment_type=comment_data.comment_type,
            referenced_content=referenced_content,
        )

        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)

        return comment

    def get_document_comments(self, document_id: int) -> List[DocumentComment]:
        """获取文档的所有评论"""
        return (
            self.db.query(DocumentComment)
            .filter(
                DocumentComment.document_id == document_id,
                DocumentComment.parent_comment_id.is_(None),  # 只获取顶级评论
            )
            .order_by(DocumentComment.created_at.asc())
            .all()
        )

    def create_suggestion(
        self,
        document_id: int,
        org_id: int,
        suggestion_data: DocumentSuggestionCreate,
        current_user: User,
    ) -> DocumentSuggestion:
        """创建文档建议"""
        document = self.get_document(document_id, org_id)
        if not document:
            raise ValueError("文档不存在")

        if not document.allow_suggestions:
            raise ValueError("此文档不允许添加建议")

        # 验证位置有效性
        if suggestion_data.end_position > len(document.content):
            raise ValueError("建议位置超出文档范围")

        # 提取原始内容
        original_content = (
            document.content[
                suggestion_data.start_position : suggestion_data.end_position
            ]
            if suggestion_data.original_content is None
            else suggestion_data.original_content
        )

        suggestion = DocumentSuggestion(
            document_id=document_id,
            user_id=current_user.id,
            start_position=suggestion_data.start_position,
            end_position=suggestion_data.end_position,
            original_content=original_content,
            suggested_content=suggestion_data.suggested_content,
            suggestion_reason=suggestion_data.suggestion_reason,
        )

        self.db.add(suggestion)
        self.db.commit()
        self.db.refresh(suggestion)

        return suggestion

    def review_suggestion(
        self, suggestion_id: int, org_id: int, status: str, current_user: User
    ) -> DocumentSuggestion:
        """审核建议"""
        suggestion = (
            self.db.query(DocumentSuggestion)
            .join(CollaborativeDocument)
            .filter(
                DocumentSuggestion.id == suggestion_id,
                CollaborativeDocument.org_id == org_id,
            )
            .first()
        )

        if not suggestion:
            raise ValueError("建议不存在")

        suggestion.status = status
        suggestion.reviewed_at = datetime.utcnow()
        suggestion.reviewed_by = current_user.id

        self.db.commit()
        self.db.refresh(suggestion)

        return suggestion

    def create_session(
        self, document_id: int, org_id: int, client_id: str, current_user: User
    ) -> DocumentSession:
        """创建文档会话"""
        document = self.get_document(document_id, org_id)
        if not document:
            raise ValueError("文档不存在")

        # 检查是否已有活跃会话
        existing_session = (
            self.db.query(DocumentSession)
            .filter(
                DocumentSession.document_id == document_id,
                DocumentSession.user_id == current_user.id,
                DocumentSession.is_active == True,
            )
            .first()
        )

        if existing_session:
            # 更新现有会话
            existing_session.last_activity = datetime.utcnow()
            existing_session.client_id = client_id
            self.db.commit()
            self.db.refresh(existing_session)
            return existing_session

        # 创建新会话
        session = DocumentSession(
            document_id=document_id, user_id=current_user.id, client_id=client_id
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def update_session_cursor(
        self,
        session_id: str,
        cursor_position: int,
        selection_start: Optional[int] = None,
        selection_end: Optional[int] = None,
    ) -> DocumentSession:
        """更新会话光标位置"""
        session = (
            self.db.query(DocumentSession)
            .filter(
                DocumentSession.session_id == session_id,
                DocumentSession.is_active == True,
            )
            .first()
        )

        if not session:
            raise ValueError("会话不存在或已结束")

        session.cursor_position = cursor_position
        session.selection_start = selection_start
        session.selection_end = selection_end
        session.last_activity = datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)

        return session

    def end_session(self, session_id: str) -> DocumentSession:
        """结束会话"""
        session = (
            self.db.query(DocumentSession)
            .filter(DocumentSession.session_id == session_id)
            .first()
        )

        if not session:
            raise ValueError("会话不存在")

        session.is_active = False
        session.left_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)

        return session

    def get_active_sessions(self, document_id: int) -> List[DocumentSession]:
        """获取文档的活跃会话"""
        return (
            self.db.query(DocumentSession)
            .filter(
                DocumentSession.document_id == document_id,
                DocumentSession.is_active == True,
            )
            .all()
        )


# 依赖注入函数
def get_collaborative_editor_service(
    db: Session = Depends(get_sync_db),
) -> CollaborativeEditorService:
    """获取协作编辑服务实例"""
    return CollaborativeEditorService(db)
