"""TODO: docstring"""

import enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func as sql_func

from database.db import Base

  # TODO


class DiscussionCategory(str, enum.Enum):
    """TODO: docstring"""

    GENERAL = "general"    # TODO
    COURSE_QA = "course_qa"    # TODO
    PROJECT_SHOWCASE = "showcase"    # TODO
    STUDY_GROUP = "study_group"    # TODO
    TECHNICAL = "technical"    # TODO


class PostType(str, enum.Enum):
    """TODO: docstring"""

    QUESTION = "question"    # TODO
    DISCUSSION = "discussion"    # TODO
    TUTORIAL = "tutorial"    # TODO
    SHOWCASE = "showcase"    # TODO
    ANNOUNCEMENT = "announcement"    # TODO


class DocumentPermission(str, enum.Enum):
    """TODO: docstring"""

    PRIVATE = "private"    # TODO
    PUBLIC = "public"    # TODO


class ReviewStatus(str, enum.Enum):
    """TODO: docstring"""è®¨è®ºå¸å­è¡?""

    __tablename__ = "discussion_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)

      # TODO
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="åå¸äº?ID"
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=True,
        index=True,
        comment="å³èè¯¾ç¨ IDï¼å¯éï¼",
    )
    parent_id = Column(
        Integer,
        ForeignKey("discussion_posts.id"),
        nullable=True,
        index=True,
        comment="ç¶å¸å­?IDï¼ç¨äºåå¤ï¼",
    )

      # TODO
    title = Column(String(200), nullable=False, comment="æ é¢")
    content = Column(Text, nullable=False, comment="æ­£æåå®¹")
    category = Column(
        SQLEnum(DiscussionCategory),
        nullable=False,
        default=DiscussionCategory.GENERAL,
        comment="åç±»",
    )
    post_type = Column(
        SQLEnum(PostType), nullable=False, default=PostType.DISCUSSION, comment="ç±»å"
    )
    tags = Column(JSON, default=list, comment="æ ç­¾åè¡¨")

      # TODO
    view_count = Column(Integer, default=0, comment="æµè§æ¬¡æ°")
    like_count = Column(Integer, default=0, comment="ç¹èµæ?)
    comment_count = Column(Integer, default=0, comment="è¯è®ºæ?)
    is_pinned = Column(Boolean, default=False, comment="æ¯å¦ç½®é¡¶")
    is_locked = Column(Boolean, default=False, comment="æ¯å¦éå®ï¼ç¦æ­¢åå¤ï¼")
    is_solved = Column(Boolean, default=False, comment="æ¯å¦å·²è§£å³ï¼é®é¢å¸ï¼")

      # TODO
        DateTime(timezone=True), server_default=sql_func.now(), index=True
    )
    updated_at = Column(DateTime(timezone=True), onupdate=sql_func.now())
    last_activity_at = Column(
        DateTime(timezone=True), onupdate=sql_func.now(), comment="æåæ´»è·æ¶é?
    )

      # TODO
    author = relationship("User", backref="posts")
    course = relationship("Course", backref="posts")
    parent = relationship("DiscussionPost", remote_side=[id], backref="replies")
    comments = relationship(
        "DiscussionComment", back_populates="post", cascade="all, delete-orphan"
    )
    likes = relationship(
        "PostLike", back_populates="post", cascade="all, delete-orphan"
    )

      # TODO
    __table_args__ = (
        Index("idx_post_category_created", "category", "created_at"),
        Index("idx_post_user_created", "user_id", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category.value,
            "post_type": self.post_type.value,
            "tags": self.tags,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "is_pinned": self.is_pinned,
            "is_locked": self.is_locked,
            "is_solved": self.is_solved,
            "user_id": self.user_id,
            "course_id": self.course_id,
            "parent_id": self.parent_id,
            "author": (
                {"id": self.author.id, "username": self.author.username}
                if self.author
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
            "last_activity_at": (
                self.last_activity_at.isoformat() if self.last_activity_at is not None else None
            ),
        }


class DiscussionComment(Base):
    """TODO: docstring"""å¸å­ç¹èµè¡?""

    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(
        Integer, ForeignKey("discussion_posts.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=sql_func.now())

      # TODO
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uix_post_like_unique"),
    )

    post = relationship("DiscussionPost", back_populates="likes")
    user = relationship("User", backref="post_likes")

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


class CommentLike(Base):
    """TODO: docstring"""åä½ææ¡£è¡?""

    __tablename__ = "collaborative_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)

      # TODO
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="åå»ºè?ID"
    )
    group_id = Column(
        Integer,
        ForeignKey("study_groups.id"),
        nullable=True,
        index=True,
        comment="æå±å°ç»?IDï¼å¯éï¼",
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=True,
        index=True,
        comment="å³èè¯¾ç¨ IDï¼å¯éï¼",
    )

      # TODO
    title = Column(String(200), nullable=False, comment="ææ¡£æ é¢")
    content = Column(Text, default="", comment="ææ¡£åå®¹ï¼Markdown æ ¼å¼ï¼?)
    permission = Column(
        SQLEnum(DocumentPermission),
        default=DocumentPermission.PRIVATE,
        comment="æéè®¾ç½®",
    )

      # TODO
    version = Column(Integer, default=1, comment="çæ¬å?)
    last_editor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="æåç¼è¾è?ID",
    )

      # TODO
    collaborators = Column(JSON, default=list, comment="åä½èåè¡?[{user_id, role}]")

      # TODO
        DateTime(timezone=True), server_default=sql_func.now(), index=True
    )
    updated_at = Column(DateTime(timezone=True), onupdate=sql_func.now())

      # TODO
    creator = relationship("User", foreign_keys=[user_id], backref="created_documents")
    last_editor = relationship("User", foreign_keys=[last_editor_id])
    group = relationship("StudyGroup", back_populates="documents")
    versions = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan"
    )
    comments = relationship(
        "DocumentComment", back_populates="document", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "permission": self.permission.value,
            "version": self.version,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "course_id": self.course_id,
            "last_editor_id": self.last_editor_id,
            "collaborators": self.collaborators,
            "creator": (
                {"id": self.creator.id, "username": self.creator.username}
                if self.creator
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


class DocumentVersion(Base):
    """TODO: docstring"""ææ¡£è¯è®ºè¡¨ï¼æ¯æè¡çº§è¯è®ºï¼?""

    __tablename__ = "document_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)

      # TODO
    document_id = Column(
        Integer, ForeignKey("collaborative_documents.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    parent_id = Column(
        Integer, ForeignKey("document_comments.id"), nullable=True, index=True
    )

      # TODO
    content = Column(Text, nullable=False, comment="è¯è®ºåå®¹")
    line_number = Column(Integer, comment="è¡å·ï¼ç¨äºè¡çº§è¯è®ºï¼")
    is_resolved = Column(Boolean, default=False, comment="æ¯å¦å·²è§£å?)

      # TODO
        DateTime(timezone=True), server_default=sql_func.now(), index=True
    )
    updated_at = Column(DateTime(timezone=True), onupdate=sql_func.now())

      # TODO
    document = relationship("CollaborativeDocument", back_populates="comments")
    author = relationship("User", backref="document_comments")
    parent = relationship("DocumentComment", remote_side=[id], backref="replies")

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "line_number": self.line_number,
            "is_resolved": self.is_resolved,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "parent_id": self.parent_id,
            "author": (
                {"id": self.author.id, "username": self.author.username}
                if self.author
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


  # TODO


class StudyGroup(Base):
    """TODO: docstring"""å°ç»æåè¡?""

    __tablename__ = "study_group_members"

    id = Column(Integer, primary_key=True, autoincrement=True)

      # TODO
    group_id = Column(
        Integer, ForeignKey("study_groups.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

      # TODO
    role = Column(String(20), default="member", comment="è§è²ï¼admin/member")
    joined_at = Column(DateTime(timezone=True), server_default=sql_func.now())

      # TODO
    group = relationship("StudyGroup", back_populates="members")
    user = relationship("User", backref="group_memberships")

      # TODO
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uix_group_member_unique"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at is not None else None,
            "user": (
                {"id": self.user.id, "username": self.user.username}
                if self.user
                else None
            ),
        }


  # TODO


class StudyProject(Base):
    """TODO: docstring"""é¡¹ç®ä»»å¡è¡?""

    __tablename__ = "project_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)

      # TODO
    project_id = Column(
        Integer, ForeignKey("study_projects.id"), nullable=False, index=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="è´è´£äº?IDï¼å¯éï¼",
    )

      # TODO
    title = Column(String(200), nullable=False, comment="ä»»å¡æ é¢")
    description = Column(Text, comment="ä»»å¡æè¿°")
    status = Column(String(20), default="todo", comment="ç¶æï¼todo/in_progress/done")
    priority = Column(String(20), default="medium", comment="ä¼åçº§ï¼low/medium/high")
    due_date = Column(DateTime(timezone=True), comment="æªæ­¢æ¥æ")

      # TODO
    updated_at = Column(DateTime(timezone=True), onupdate=sql_func.now())

      # TODO
    project = relationship("StudyProject", back_populates="tasks")
    assignee = relationship("User", backref="assigned_tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date is not None else None,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "assignee": (
                {"id": self.assignee.id, "username": self.assignee.username}
                if self.assignee
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


class PeerReview(Base):
    """åä¼´å®¡æ¥è¡?""

    __tablename__ = "peer_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)

      # TODO
    project_id = Column(
        Integer, ForeignKey("study_projects.id"), nullable=False, index=True
    )
    reviewer_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="å®¡æ¥äº?ID"
    )
    reviewee_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="è¢«å®¡æ¥äºº ID",
    )

      # TODO
    status = Column(
        SQLEnum(ReviewStatus), default=ReviewStatus.PENDING, comment="å®¡æ¥ç¶æ?
    )
    feedback = Column(Text, comment="å®¡æ¥åé¦")
    score = Column(Integer, comment="è¯åï¼?-100ï¼?)
    strengths = Column(JSON, default=list, comment="ä¼ç¹åè¡¨")
    suggestions = Column(JSON, default=list, comment="æ¹è¿å»ºè®®åè¡¨")

      # TODO
        DateTime(timezone=True), server_default=sql_func.now(), index=True
    )
    updated_at = Column(DateTime(timezone=True), onupdate=sql_func.now())

      # TODO
    project = relationship("StudyProject", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id], backref="given_reviews")
    reviewee = relationship(
        "User", foreign_keys=[reviewee_id], backref="received_reviews"
    )

      # TODO
    __table_args__ = (
        UniqueConstraint("project_id", "reviewer_id", name="uix_peer_review_unique"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "reviewer_id": self.reviewer_id,
            "reviewee_id": self.reviewee_id,
            "status": self.status.value,
            "feedback": self.feedback,
            "score": self.score,
            "strengths": self.strengths,
            "suggestions": self.suggestions,
            "reviewer": (
                {"id": self.reviewer.id, "username": self.reviewer.username}
                if self.reviewer
                else None
            ),
            "reviewee": (
                {"id": self.reviewee.id, "username": self.reviewee.username}
                if self.reviewee
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }
