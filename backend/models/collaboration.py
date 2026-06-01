"""
协作学习数据模型

包含讨论区、协作文档、学习小组、项目任务、同伴审查等模型
"""

import enum
from datetime import datetime

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
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from utils.database import Base


# ==================== 枚举定义 ====================


class DiscussionCategory(str, enum.Enum):
    """讨论区分类"""

    GENERAL = "general"
    COURSE_QA = "course_qa"
    PROJECT_SHOWCASE = "showcase"
    STUDY_GROUP = "study_group"
    TECHNICAL = "technical"


class PostType(str, enum.Enum):
    """帖子类型"""

    QUESTION = "question"
    DISCUSSION = "discussion"
    TUTORIAL = "tutorial"
    SHOWCASE = "showcase"
    ANNOUNCEMENT = "announcement"


class DocumentPermission(str, enum.Enum):
    """文档权限"""

    PRIVATE = "private"
    PUBLIC = "public"


class ReviewStatus(str, enum.Enum):
    """审查状态"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# ==================== 讨论区模型 ====================


class DiscussionPost(Base):
    """讨论帖模型"""

    __tablename__ = "discussion_posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="发帖人ID"
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=True,
        index=True,
        comment="关联课程 ID（可选）",
    )
    parent_id = Column(
        Integer,
        ForeignKey("discussion_posts.id"),
        nullable=True,
        index=True,
        comment="父帖子ID（用于回复）",
    )

    title = Column(String(200), nullable=False, comment="标题")
    content = Column(Text, nullable=False, comment="正文内容")
    category = Column(
        SQLEnum(DiscussionCategory),
        nullable=False,
        default=DiscussionCategory.GENERAL,
        comment="分类",
    )
    post_type = Column(
        SQLEnum(PostType), nullable=False, default=PostType.DISCUSSION, comment="类型"
    )
    tags = Column(JSON, default=list, comment="标签列表")

    view_count = Column(Integer, default=0, comment="浏览次数")
    like_count = Column(Integer, default=0, comment="点赞数")
    comment_count = Column(Integer, default=0, comment="评论数")
    is_pinned = Column(Boolean, default=False, comment="是否置顶")
    is_locked = Column(Boolean, default=False, comment="是否锁定（禁止回复）")
    is_solved = Column(Boolean, default=False, comment="是否已解决（问题帖）")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_activity_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="最后活跃时间"
    )

    # 关联关系
    author = relationship("User", backref="posts")
    course = relationship("Course", backref="posts")
    parent = relationship("DiscussionPost", remote_side=[
                          id], backref="replies")
    comments = relationship(
        "DiscussionComment", back_populates="post", cascade="all, delete-orphan"
    )
    likes = relationship(
        "PostLike", back_populates="post", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_post_category_created", "category", "created_at"),
        Index("idx_post_user_created", "user_id", "created_at"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category.value if self.category else None,
            "post_type": self.post_type.value if self.post_type else None,
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


class PostLike(Base):
    """帖子点赞模型"""

    __tablename__ = "post_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(
        Integer, ForeignKey("discussion_posts.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    post = relationship("DiscussionPost", back_populates="likes")
    user = relationship("User", backref="post_likes")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uix_post_like_unique"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


class DiscussionComment(Base):
    """讨论评论模型"""

    __tablename__ = "discussion_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(
        Integer, ForeignKey("discussion_posts.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False, index=True)
    parent_id = Column(
        Integer,
        ForeignKey("discussion_comments.id"),
        nullable=True,
        index=True,
        comment="父评论ID（用于回复）",
    )
    content = Column(Text, nullable=False, comment="评论内容")
    created_at = Column(DateTime(timezone=True),
                        server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    post = relationship("DiscussionPost", back_populates="comments")
    author = relationship("User", backref="discussion_comments")
    parent = relationship("DiscussionComment", remote_side=[
                          id], backref="replies")

    def to_dict(self):
        return {
            "id": self.id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "parent_id": self.parent_id,
            "content": self.content,
            "author": (
                {"id": self.author.id, "username": self.author.username}
                if self.author
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


class CommentLike(Base):
    """评论点赞模型"""

    __tablename__ = "comment_likes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(
        Integer, ForeignKey("discussion_comments.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    comment = relationship("DiscussionComment", backref="likes")
    user = relationship("User", backref="comment_likes")

    __table_args__ = (
        UniqueConstraint("comment_id", "user_id",
                         name="uix_comment_like_unique"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "comment_id": self.comment_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


# ==================== 协作文档模型 ====================


class CollaborativeDocument(Base):
    """协作文档模型"""

    __tablename__ = "collaborative_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="创建者ID"
    )
    group_id = Column(
        Integer,
        ForeignKey("study_groups.id"),
        nullable=True,
        index=True,
        comment="所属小组ID（可选）",
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=True,
        index=True,
        comment="关联课程 ID（可选）",
    )

    title = Column(String(200), nullable=False, comment="文档标题")
    content = Column(Text, default="", comment="文档内容（Markdown 格式）")
    permission = Column(
        SQLEnum(DocumentPermission),
        default=DocumentPermission.PRIVATE,
        comment="权限设置",
    )

    version = Column(Integer, default=1, comment="版本号")
    last_editor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="最后编辑者ID",
    )

    collaborators = Column(
        JSON, default=list, comment="协作者列表[{user_id, role}]")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    creator = relationship("User", foreign_keys=[
                           user_id], backref="created_documents")
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
            "permission": self.permission.value if self.permission else None,
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
    """文档版本历史模型"""

    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        Integer, ForeignKey("collaborative_documents.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False, index=True)
    version_number = Column(Integer, nullable=False, comment="版本号")
    content = Column(Text, comment="版本内容")
    change_summary = Column(String(500), comment="变更摘要")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    document = relationship("CollaborativeDocument", back_populates="versions")
    author = relationship("User", backref="document_versions")

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "version_number": self.version_number,
            "content": self.content,
            "change_summary": self.change_summary,
            "author": (
                {"id": self.author.id, "username": self.author.username}
                if self.author
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


class DocumentComment(Base):
    """文档评论/批注模型"""

    __tablename__ = "document_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(
        Integer, ForeignKey("collaborative_documents.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False, index=True)
    parent_id = Column(
        Integer,
        ForeignKey("document_comments.id"),
        nullable=True,
        index=True,
        comment="父评论ID",
    )

    content = Column(Text, nullable=False, comment="评论内容")
    line_number = Column(Integer, nullable=True, comment="行号（用于行级评论）")
    is_resolved = Column(Boolean, default=False, comment="是否已解决")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    document = relationship("CollaborativeDocument", back_populates="comments")
    author = relationship("User", backref="document_comments")
    parent = relationship("DocumentComment", remote_side=[
                          id], backref="replies")

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "parent_id": self.parent_id,
            "content": self.content,
            "line_number": self.line_number,
            "is_resolved": self.is_resolved,
            "author": (
                {"id": self.author.id, "username": self.author.username}
                if self.author
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


# ==================== 学习小组模型 ====================


class StudyGroup(Base):
    """学习小组模型"""

    __tablename__ = "study_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="创建者ID"
    )
    name = Column(String(100), nullable=False, comment="小组名称")
    description = Column(Text, comment="小组描述")
    org_id = Column(
        Integer, ForeignKey("organizations.id"), nullable=False, index=True, comment="所属机构ID"
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=True,
        index=True,
        comment="关联课程 ID（可选）",
    )
    max_members = Column(Integer, default=10, comment="最大成员数")
    member_count = Column(Integer, default=0, comment="当前成员数")
    is_private = Column(Boolean, default=False, comment="是否私密小组")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    creator = relationship("User", foreign_keys=[
                           creator_id], backref="created_groups")
    members = relationship(
        "StudyGroupMember", back_populates="group", cascade="all, delete-orphan"
    )
    documents = relationship(
        "CollaborativeDocument", back_populates="group", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "org_id": self.org_id,
            "course_id": self.course_id,
            "max_members": self.max_members,
            "member_count": self.member_count,
            "is_private": self.is_private,
            "creator_id": self.creator_id,
            "creator": (
                {"id": self.creator.id, "username": self.creator.username}
                if self.creator
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


class StudyGroupMember(Base):
    """小组成员模型"""

    __tablename__ = "study_group_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(
        Integer, ForeignKey("study_groups.id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False, index=True)

    role = Column(String(20), default="member", comment="角色：admin/member")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联关系
    group = relationship("StudyGroup", back_populates="members")
    user = relationship("User", backref="group_memberships")

    __table_args__ = (
        UniqueConstraint("group_id", "user_id",
                         name="uix_group_member_unique"),
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


# ==================== 项目管理模型 ====================


class StudyProject(Base):
    """学习项目模型"""

    __tablename__ = "study_projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(
        Integer, ForeignKey("study_groups.id"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="创建者ID"
    )
    title = Column(String(200), nullable=False, comment="项目标题")
    description = Column(Text, comment="项目描述")
    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=True,
        index=True,
        comment="关联课程 ID（可选）",
    )
    repository_url = Column(String(500), comment="代码仓库地址")
    status = Column(
        String(20), default="planning", comment="状态：planning/active/completed/archived"
    )
    progress_percentage = Column(Integer, default=0, comment="进度百分比（0-100）")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    group = relationship("StudyGroup", backref="projects")
    creator = relationship("User", foreign_keys=[
                           user_id], backref="created_projects")
    tasks = relationship(
        "ProjectTask", back_populates="project", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "PeerReview", back_populates="project", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "group_id": self.group_id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "course_id": self.course_id,
            "repository_url": self.repository_url,
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "creator": (
                {"id": self.creator.id, "username": self.creator.username}
                if self.creator
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


class ProjectTask(Base):
    """项目任务模型"""

    __tablename__ = "project_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("study_projects.id"), nullable=False, index=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
        comment="负责人ID（可选）",
    )

    title = Column(String(200), nullable=False, comment="任务标题")
    description = Column(Text, comment="任务描述")
    status = Column(
        String(20), default="todo", comment="状态：todo/in_progress/done"
    )
    priority = Column(
        String(20), default="medium", comment="优先级：low/medium/high"
    )
    due_date = Column(DateTime(timezone=True), nullable=True, comment="截止日期")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    project = relationship("StudyProject", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[
                            user_id], backref="assigned_tasks")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date is not None else None,
            "assignee": (
                {"id": self.assignee.id, "username": self.assignee.username}
                if self.assignee
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None,
        }


# ==================== 同伴审查模型 ====================


class PeerReview(Base):
    """同伴审查表"""

    __tablename__ = "peer_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)

    project_id = Column(
        Integer, ForeignKey("study_projects.id"), nullable=False, index=True
    )
    reviewer_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="审查人ID"
    )
    reviewee_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
        comment="被审查人ID",
    )

    status = Column(
        SQLEnum(ReviewStatus), default=ReviewStatus.PENDING, comment="审查状态"
    )
    feedback = Column(Text, comment="审查反馈")
    score = Column(Integer, comment="评分（0-100）")
    strengths = Column(JSON, default=list, comment="优点列表")
    suggestions = Column(JSON, default=list, comment="改进建议列表")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联关系
    project = relationship("StudyProject", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[
                            reviewer_id], backref="given_reviews")
    reviewee = relationship(
        "User", foreign_keys=[reviewee_id], backref="received_reviews"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "reviewer_id",
                         name="uix_peer_review_unique"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "reviewer_id": self.reviewer_id,
            "reviewee_id": self.reviewee_id,
            "status": self.status.value if self.status else None,
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
