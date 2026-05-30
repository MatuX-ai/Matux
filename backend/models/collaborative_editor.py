"""
协作编辑数据模型
实现实时协同编辑和评论批注功能
"""

from datetime import datetime
import hashlib
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from utils.database import Base


class CollaborativeDocument(Base):
    """协作文档模型"""

    __tablename__ = "collaborative_documents"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)

    # 文档信息
    document_name = Column(String(255), nullable=False)  # 文档名称
    document_type = Column(
        String(50), default="richtext"
    )  # 文档类型: richtext/markdown/html
    content = Column(Text, nullable=False)  # 文档内容

    # 版本信息
    version_number = Column(Integer, default=1)  # 版本号
    last_commit_hash = Column(String(64))  # 最后提交哈希

    # 协作设置
    is_locked = Column(Boolean, default=False)  # 是否锁定编辑
    locked_by = Column(Integer, ForeignKey("users.id"))  # 锁定用户ID
    locked_at = Column(DateTime)  # 锁定时间

    # 权限设置
    allow_comments = Column(Boolean, default=True)  # 是否允许评论
    allow_suggestions = Column(Boolean, default=True)  # 是否允许建议

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    course = relationship("Course")
    organization = relationship("Organization")
    locked_user = relationship("User")

    __table_args__ = (
        Index("idx_collab_doc_course", "course_id"),
        Index("idx_collab_doc_org", "org_id"),
    )


class DocumentOperation(Base):
    """文档操作记录模型 - 用于OT算法"""

    __tablename__ = "document_operations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer, ForeignKey("collaborative_documents.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 操作信息
    operation_type = Column(String(20), nullable=False)  # insert/delete/update
    position = Column(Integer, nullable=False)  # 操作位置
    content = Column(Text)  # 操作内容
    operation_id = Column(String(64), unique=True)  # 操作唯一标识

    # OT相关信息
    client_id = Column(String(50))  # 客户端ID
    revision = Column(Integer, nullable=False)  # 版本号
    timestamp = Column(DateTime, default=datetime.utcnow)  # 时间戳

    # 转换后的操作
    transformed_operation = Column(JSON)  # 转换后的操作数据

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    document = relationship("CollaborativeDocument")
    user = relationship("User")

    __table_args__ = (
        Index("idx_doc_op_document_revision", "document_id", "revision"),
        Index("idx_doc_op_timestamp", "timestamp"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.operation_id:
            self.generate_operation_id()

    def generate_operation_id(self):
        """生成操作唯一标识"""
        content_str = f"{self.document_id}{self.user_id}{self.operation_type}{self.position}{self.content}{self.timestamp.isoformat()}"
        self.operation_id = hashlib.sha256(content_str.encode()).hexdigest()


class DocumentComment(Base):
    """文档评论模型"""

    __tablename__ = "document_comments"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer, ForeignKey("collaborative_documents.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 评论位置
    start_position = Column(Integer, nullable=False)  # 开始位置
    end_position = Column(Integer, nullable=False)  # 结束位置

    # 评论内容
    content = Column(Text, nullable=False)  # 评论内容
    comment_type = Column(
        String(20), default="comment"
    )  # 评论类型: comment/suggestion/question

    # 引用信息
    referenced_content = Column(Text)  # 被引用的内容片段

    # 状态
    is_resolved = Column(Boolean, default=False)  # 是否已解决
    resolved_at = Column(DateTime)  # 解决时间
    resolved_by = Column(Integer, ForeignKey("users.id"))  # 解决者ID

    # 回复
    parent_comment_id = Column(Integer, ForeignKey("document_comments.id"))  # 父评论ID
    replies_count = Column(Integer, default=0)  # 回复数量

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    document = relationship("CollaborativeDocument")
    user = relationship("User", foreign_keys=[user_id])
    resolver = relationship("User", foreign_keys=[resolved_by])
    parent_comment = relationship("DocumentComment", remote_side=[id])
    replies = relationship("DocumentComment", back_populates="parent_comment")

    __table_args__ = (
        Index("idx_doc_comment_document", "document_id"),
        Index("idx_doc_comment_user", "user_id"),
        Index("idx_doc_comment_position", "start_position", "end_position"),
    )


class DocumentSuggestion(Base):
    """文档建议模型"""

    __tablename__ = "document_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer, ForeignKey("collaborative_documents.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 建议位置
    start_position = Column(Integer, nullable=False)
    end_position = Column(Integer, nullable=False)

    # 建议内容
    original_content = Column(Text)  # 原始内容
    suggested_content = Column(Text, nullable=False)  # 建议内容
    suggestion_reason = Column(Text)  # 建议理由

    # 状态
    status = Column(String(20), default="pending")  # pending/accepted/rejected
    reviewed_at = Column(DateTime)  # 审核时间
    reviewed_by = Column(Integer, ForeignKey("users.id"))  # 审核者ID

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    document = relationship("CollaborativeDocument")
    user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        Index("idx_doc_suggestion_document", "document_id"),
        Index("idx_doc_suggestion_status", "status"),
    )


class DocumentSession(Base):
    """文档会话模型 - 跟踪在线用户"""

    __tablename__ = "document_sessions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer, ForeignKey("collaborative_documents.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # 会话信息
    session_id = Column(String(64), unique=True)  # 会话ID
    client_id = Column(String(50))  # 客户端标识
    cursor_position = Column(Integer, default=0)  # 光标位置
    selection_start = Column(Integer)  # 选区开始
    selection_end = Column(Integer)  # 选区结束

    # 状态
    is_active = Column(Boolean, default=True)  # 是否活跃
    last_activity = Column(DateTime, default=datetime.utcnow)  # 最后活动时间

    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime)  # 离开会话时间

    # 关系
    document = relationship("CollaborativeDocument")
    user = relationship("User")

    __table_args__ = (
        Index("idx_doc_session_document", "document_id"),
        Index("idx_doc_session_user", "user_id"),
        Index("idx_doc_session_active", "is_active"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.session_id:
            self.generate_session_id()

    def generate_session_id(self):
        """生成会话ID"""
        content_str = f"{self.document_id}{self.user_id}{self.joined_at.isoformat()}"
        self.session_id = hashlib.sha256(content_str.encode()).hexdigest()


from typing import Any, Dict, List, Optional

# Pydantic模型定义
from pydantic import BaseModel, Field, validator


class CollaborativeDocumentCreate(BaseModel):
    """创建协作文档的请求模型"""

    document_name: str = Field(..., min_length=1, max_length=255)
    document_type: str = Field(default="richtext", pattern="^(richtext|markdown|html)$")
    content: str = ""
    allow_comments: bool = True
    allow_suggestions: bool = True

    @validator("document_name")
    def validate_document_name(cls, v):
        if not v.strip():
            raise ValueError("文档名称不能为空")
        return v.strip()


class CollaborativeDocumentResponse(BaseModel):
    """协作文档响应模型"""

    id: int
    course_id: int
    org_id: int
    document_name: str
    document_type: str
    content: str
    version_number: int
    last_commit_hash: Optional[str]
    is_locked: bool
    locked_by: Optional[int]
    allow_comments: bool
    allow_suggestions: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DocumentOperationCreate(BaseModel):
    """创建文档操作的请求模型"""

    operation_type: str = Field(..., pattern="^(insert|delete|update)$")
    position: int = Field(..., ge=0)
    content: Optional[str] = None
    client_id: str = Field(..., min_length=1, max_length=50)
    revision: int = Field(..., ge=0)

    @validator("content")
    def validate_content_for_insert(cls, v, values):
        if values.get("operation_type") == "insert" and not v:
            raise ValueError("插入操作必须提供内容")
        return v


class DocumentOperationResponse(BaseModel):
    """文档操作响应模型"""

    id: int
    document_id: int
    user_id: int
    operation_type: str
    position: int
    content: Optional[str]
    operation_id: str
    client_id: str
    revision: int
    timestamp: datetime
    transformed_operation: Optional[Dict[str, Any]]

    class Config:
        orm_mode = True


class DocumentCommentCreate(BaseModel):
    """创建文档评论的请求模型"""

    start_position: int = Field(..., ge=0)
    end_position: int = Field(..., ge=0)
    content: str = Field(..., min_length=1, max_length=2000)
    comment_type: str = Field(
        default="comment", pattern="^(comment|suggestion|question)$"
    )
    referenced_content: Optional[str] = None

    @validator("end_position")
    def validate_positions(cls, v, values):
        if "start_position" in values and v < values["start_position"]:
            raise ValueError("结束位置不能小于开始位置")
        return v


class DocumentCommentResponse(BaseModel):
    """文档评论响应模型"""

    id: int
    document_id: int
    user_id: int
    start_position: int
    end_position: int
    content: str
    comment_type: str
    referenced_content: Optional[str]
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]
    parent_comment_id: Optional[int]
    replies_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DocumentSuggestionCreate(BaseModel):
    """创建文档建议的请求模型"""

    start_position: int = Field(..., ge=0)
    end_position: int = Field(..., ge=0)
    original_content: Optional[str] = None
    suggested_content: str = Field(..., min_length=1)
    suggestion_reason: Optional[str] = Field(None, max_length=1000)

    @validator("end_position")
    def validate_positions(cls, v, values):
        if "start_position" in values and v < values["start_position"]:
            raise ValueError("结束位置不能小于开始位置")
        return v


class DocumentSuggestionResponse(BaseModel):
    """文档建议响应模型"""

    id: int
    document_id: int
    user_id: int
    start_position: int
    end_position: int
    original_content: Optional[str]
    suggested_content: str
    suggestion_reason: Optional[str]
    status: str
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DocumentSessionResponse(BaseModel):
    """文档会话响应模型"""

    id: int
    document_id: int
    user_id: int
    session_id: str
    client_id: Optional[str]
    cursor_position: int
    selection_start: Optional[int]
    selection_end: Optional[int]
    is_active: bool
    last_activity: datetime
    joined_at: datetime
    left_at: Optional[datetime]

    class Config:
        orm_mode = True


class OTTransformRequest(BaseModel):
    """OT转换请求模型"""

    client_id: str
    operations: List[DocumentOperationCreate]
    base_revision: int


class OTTransformResponse(BaseModel):
    """OT转换响应模型"""

    transformed_operations: List[DocumentOperationResponse]
    new_revision: int
    document_content: str
