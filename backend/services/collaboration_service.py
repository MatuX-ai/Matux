"""
AI-Edu 协作学习服务
提供讨论区、协作文档、小组项目、同伴审查等功能
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.orm import Session

from models.collaboration import (
    CollaborativeDocument,
    CommentLike,
    DiscussionCategory,
    DiscussionComment,
    DiscussionPost,
    DocumentComment,
    DocumentPermission,
    DocumentVersion,
    PeerReview,
    PostLike,
    PostType,
    ProjectTask,
    ReviewStatus,
    StudyGroup,
    StudyGroupMember,
    StudyProject,
)
from models.user import User

logger = logging.getLogger(__name__)


class CollaborationService:
    """协作学习服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 讨论区服务 ====================

    def create_post(
        self,
        user_id: int,
        title: str,
        content: str,
        category: str,
        post_type: str = "discussion",
        course_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> DiscussionPost:
        """创建帖子"""
        try:
            post = DiscussionPost(
                user_id=user_id,
                title=title,
                content=content,
                category=DiscussionCategory(category),
                post_type=PostType(post_type),
                course_id=course_id,
                tags=tags or [],
            )
            self.db.add(post)
            self.db.commit()
            self.db.refresh(post)

            logger.info(f"✅ 用户 {user_id} 创建了帖子：{title}")
            return post

        except Exception as e:
            logger.error(f"❌ 创建帖子失败：{e}")
            self.db.rollback()
            raise

    def get_posts(
        self,
        category: Optional[str] = None,
        course_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "last_activity",
    ) -> List[DiscussionPost]:
        """获取帖子列表"""
        query = self.db.query(DiscussionPost).filter(
            DiscussionPost.parent_id.is_(None)  # 只获取主帖
        )

        if category:
            query = query.filter(
                DiscussionPost.category == DiscussionCategory(category)
            )

        if course_id:
            query = query.filter(DiscussionPost.course_id == course_id)

        # 排序
        if order_by == "latest":
            query = query.order_by(desc(DiscussionPost.created_at))
        elif order_by == "popular":
            query = query.order_by(desc(DiscussionPost.like_count))
        else:  # last_activity
            query = query.order_by(desc(DiscussionPost.last_activity_at))

        return query.offset(offset).limit(limit).all()

    def get_post(self, post_id: int) -> Optional[DiscussionPost]:
        """获取帖子详情"""
        return (
            self.db.query(DiscussionPost).filter(DiscussionPost.id == post_id).first()
        )

    def increment_view_count(self, post_id: int):
        """增加浏览次数"""
        post = self.get_post(post_id)
        if post:
            post.view_count += 1
            self.db.commit()

    def like_post(self, post_id: int, user_id: int) -> bool:
        """点赞帖子"""
        try:
            # 检查是否已点赞
            existing = (
                self.db.query(PostLike)
                .filter(and_(PostLike.post_id == post_id, PostLike.user_id == user_id))
                .first()
            )

            if existing:
                return False  # 已经点赞过

            # 创建点赞记录
            like = PostLike(post_id=post_id, user_id=user_id)
            self.db.add(like)

            # 更新帖子点赞数
            post = self.get_post(post_id)
            post.like_count += 1
            self.db.commit()

            logger.info(f"✅ 用户 {user_id} 点赞了帖子 {post_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 点赞失败：{e}")
            self.db.rollback()
            raise

    def create_comment(
        self, post_id: int, user_id: int, content: str, parent_id: Optional[int] = None
    ) -> DiscussionComment:
        """创建评论"""
        try:
            comment = DiscussionComment(
                post_id=post_id, user_id=user_id, content=content, parent_id=parent_id
            )
            self.db.add(comment)
            self.db.commit()
            self.db.refresh(comment)

            # 更新帖子评论数
            post = self.get_post(post_id)
            post.comment_count += 1
            self.db.commit()

            logger.info(f"✅ 用户 {user_id} 添加了评论到帖子 {post_id}")
            return comment

        except Exception as e:
            logger.error(f"❌ 创建评论失败：{e}")
            self.db.rollback()
            raise

    def get_comments(self, post_id: int, limit: int = 100) -> List[DiscussionComment]:
        """获取帖子评论"""
        return (
            self.db.query(DiscussionComment)
            .filter(DiscussionComment.post_id == post_id)
            .order_by(asc(DiscussionComment.created_at))
            .limit(limit)
            .all()
        )

    # ==================== 协作文档服务 ====================

    def create_document(
        self,
        user_id: int,
        title: str,
        content: str = "",
        group_id: Optional[int] = None,
        course_id: Optional[int] = None,
        permission: str = "private",
    ) -> CollaborativeDocument:
        """创建协作文档"""
        try:
            doc = CollaborativeDocument(
                user_id=user_id,
                title=title,
                content=content,
                group_id=group_id,
                course_id=course_id,
                permission=DocumentPermission(permission),
                collaborators=[{"user_id": user_id, "role": "owner"}],
            )
            self.db.add(doc)
            self.db.commit()
            self.db.refresh(doc)

            # 创建初始版本
            version = DocumentVersion(
                document_id=doc.id,
                user_id=user_id,
                version_number=1,
                content=content,
                change_summary="创建文档",
            )
            self.db.add(version)
            self.db.commit()

            logger.info(f"✅ 用户 {user_id} 创建了文档：{title}")
            return doc

        except Exception as e:
            logger.error(f"❌ 创建文档失败：{e}")
            self.db.rollback()
            raise

    def update_document(
        self,
        doc_id: int,
        user_id: int,
        content: str,
        change_summary: Optional[str] = None,
    ) -> CollaborativeDocument:
        """更新文档内容"""
        try:
            doc = (
                self.db.query(CollaborativeDocument)
                .filter(CollaborativeDocument.id == doc_id)
                .first()
            )

            if not doc:
                raise ValueError(f"文档不存在：{doc_id}")

            # 检查权限
            if doc.permission != DocumentPermission.PUBLIC:
                # 检查是否是协作者
                is_collaborator = any(
                    c.get("user_id") == user_id for c in doc.collaborators
                )
                if not is_collaborator:
                    raise PermissionError("没有编辑权限")

            # 更新文档
            doc.content = content
            doc.version += 1
            doc.last_editor_id = user_id

            # 创建新版本
            version = DocumentVersion(
                document_id=doc.id,
                user_id=user_id,
                version_number=doc.version,
                content=content,
                change_summary=change_summary or f"更新到版本 {doc.version}",
            )
            self.db.add(version)
            self.db.commit()
            self.db.refresh(doc)

            logger.info(f"✅ 用户 {user_id} 更新了文档 {doc_id} 到版本 {doc.version}")
            return doc

        except Exception as e:
            logger.error(f"❌ 更新文档失败：{e}")
            self.db.rollback()
            raise

    def get_document(self, doc_id: int) -> Optional[CollaborativeDocument]:
        """获取文档详情"""
        return (
            self.db.query(CollaborativeDocument)
            .filter(CollaborativeDocument.id == doc_id)
            .first()
        )

    def get_documents(
        self, user_id: int, group_id: Optional[int] = None, limit: int = 50
    ) -> List[CollaborativeDocument]:
        """获取文档列表"""
        query = self.db.query(CollaborativeDocument)

        # 查询用户有权限查看的文档
        conditions = [
            CollaborativeDocument.user_id == user_id,  # 自己创建的
            CollaborativeDocument.permission == DocumentPermission.PUBLIC,  # 公开的
        ]

        # 如果是小组成员，查看小组文档
        if group_id:
            conditions.append(CollaborativeDocument.group_id == group_id)

        query = query.filter(or_(*conditions))
        query = query.order_by(desc(CollaborativeDocument.updated_at))

        return query.limit(limit).all()

    def add_collaborator(
        self, doc_id: int, user_id: int, collaborator_user_id: int, role: str = "editor"
    ):
        """添加协作者"""
        try:
            doc = self.get_document(doc_id)
            if not doc:
                raise ValueError("文档不存在")

            # 检查当前用户是否有权限
            is_owner = any(
                c.get("user_id") == user_id and c.get("role") == "owner"
                for c in doc.collaborators
            )
            if not is_owner:
                raise PermissionError("只有所有者可以添加协作者")

            # 添加协作者
            doc.collaborators.append({"user_id": collaborator_user_id, "role": role})

            self.db.commit()
            logger.info(
                f"✅ 用户 {user_id} 添加了协作者 {collaborator_user_id} 到文档 {doc_id}"
            )

        except Exception as e:
            logger.error(f"❌ 添加协作者失败：{e}")
            self.db.rollback()
            raise

    def get_document_versions(
        self, doc_id: int, limit: int = 20
    ) -> List[DocumentVersion]:
        """获取文档版本历史"""
        return (
            self.db.query(DocumentVersion)
            .filter(DocumentVersion.document_id == doc_id)
            .order_by(desc(DocumentVersion.version_number))
            .limit(limit)
            .all()
        )

    def add_document_comment(
        self,
        doc_id: int,
        user_id: int,
        content: str,
        line_number: Optional[int] = None,
        parent_id: Optional[int] = None,
    ) -> DocumentComment:
        """添加文档评论"""
        try:
            comment = DocumentComment(
                document_id=doc_id,
                user_id=user_id,
                content=content,
                line_number=line_number,
                parent_id=parent_id,
            )
            self.db.add(comment)
            self.db.commit()
            self.db.refresh(comment)

            logger.info(f"✅ 用户 {user_id} 添加了文档评论到文档 {doc_id}")
            return comment

        except Exception as e:
            logger.error(f"❌ 添加文档评论失败：{e}")
            self.db.rollback()
            raise

    # ==================== 学习小组服务 ====================

    def create_study_group(
        self,
        creator_id: int,
        name: str,
        description: str,
        org_id: int,
        course_id: Optional[int] = None,
        max_members: int = 10,
        is_private: bool = False,
    ) -> StudyGroup:
        """创建学习小组"""
        try:
            group = StudyGroup(
                creator_id=creator_id,
                name=name,
                description=description,
                org_id=org_id,
                course_id=course_id,
                max_members=max_members,
                is_private=is_private,
                member_count=1,
            )
            self.db.add(group)
            self.db.commit()
            self.db.refresh(group)

            # 创建者自动成为管理员
            member = StudyGroupMember(
                group_id=group.id, user_id=creator_id, role="admin"
            )
            self.db.add(member)
            self.db.commit()

            logger.info(f"✅ 用户 {creator_id} 创建了学习小组：{name}")
            return group

        except Exception as e:
            logger.error(f"❌ 创建学习小组失败：{e}")
            self.db.rollback()
            raise

    def join_study_group(self, group_id: int, user_id: int, role: str = "member"):
        """加入学习小组"""
        try:
            # 检查是否已是成员
            existing = (
                self.db.query(StudyGroupMember)
                .filter(
                    and_(
                        StudyGroupMember.group_id == group_id,
                        StudyGroupMember.user_id == user_id,
                    )
                )
                .first()
            )

            if existing:
                raise ValueError("已经是小组成员")

            # 检查人数限制
            group = self.db.query(StudyGroup).filter(StudyGroup.id == group_id).first()
            if group.member_count >= group.max_members:
                raise ValueError("小组已满员")

            # 添加成员
            member = StudyGroupMember(group_id=group_id, user_id=user_id, role=role)
            self.db.add(member)

            # 更新小组人数
            group.member_count += 1
            self.db.commit()

            logger.info(f"✅ 用户 {user_id} 加入了学习小组 {group_id}")

        except Exception as e:
            logger.error(f"❌ 加入学习小组失败：{e}")
            self.db.rollback()
            raise

    def get_study_groups(
        self,
        user_id: int,
        org_id: Optional[int] = None,
        course_id: Optional[int] = None,
    ) -> List[StudyGroup]:
        """获取用户参与的小组"""
        query = (
            self.db.query(StudyGroup)
            .join(StudyGroupMember)
            .filter(StudyGroupMember.user_id == user_id)
        )

        if org_id:
            query = query.filter(StudyGroup.org_id == org_id)

        if course_id:
            query = query.filter(StudyGroup.course_id == course_id)

        return query.all()

    def get_group_members(self, group_id: int) -> List[StudyGroupMember]:
        """获取小组成员"""
        return (
            self.db.query(StudyGroupMember)
            .filter(StudyGroupMember.group_id == group_id)
            .all()
        )

    # ==================== 项目管理服务 ====================

    def create_project(
        self,
        group_id: int,
        user_id: int,
        title: str,
        description: str,
        course_id: Optional[int] = None,
        repository_url: Optional[str] = None,
    ) -> StudyProject:
        """创建学习项目"""
        try:
            project = StudyProject(
                group_id=group_id,
                user_id=user_id,
                title=title,
                description=description,
                course_id=course_id,
                repository_url=repository_url,
            )
            self.db.add(project)
            self.db.commit()
            self.db.refresh(project)

            logger.info(f"✅ 用户 {user_id} 创建了项目：{title}")
            return project

        except Exception as e:
            logger.error(f"❌ 创建项目失败：{e}")
            self.db.rollback()
            raise

    def get_projects(
        self,
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[StudyProject]:
        """获取项目列表"""
        query = self.db.query(StudyProject)

        if group_id:
            query = query.filter(StudyProject.group_id == group_id)

        if user_id:
            query = query.filter(StudyProject.user_id == user_id)

        if status:
            query = query.filter(StudyProject.status == status)

        return query.order_by(desc(StudyProject.created_at)).all()

    def update_project_progress(self, project_id: int, progress_percentage: int):
        """更新项目进度"""
        try:
            project = (
                self.db.query(StudyProject)
                .filter(StudyProject.id == project_id)
                .first()
            )

            if not project:
                raise ValueError(f"项目不存在：{project_id}")

            project.progress_percentage = min(100, max(0, progress_percentage))
            self.db.commit()

            logger.info(f"✅ 项目 {project_id} 进度更新为 {progress_percentage}%")

        except Exception as e:
            logger.error(f"❌ 更新项目进度失败：{e}")
            self.db.rollback()
            raise

    # ==================== 任务管理服务 ====================

    def create_task(
        self,
        project_id: int,
        user_id: int,
        title: str,
        description: str,
        priority: str = "medium",
        due_date: Optional[str] = None,
        assignee_id: Optional[int] = None,
    ):
        """创建项目任务"""
        try:
            from datetime import datetime

            task = ProjectTask(
                project_id=project_id,
                user_id=user_id,
                title=title,
                description=description,
                priority=priority,
                due_date=datetime.fromisoformat(due_date) if due_date else None,
            )

            if assignee_id:
                task.user_id = assignee_id

            self.db.add(task)
            self.db.commit()

            logger.info(f"✅ 创建了任务：{title}")

        except Exception as e:
            logger.error(f"❌ 创建任务失败：{e}")
            self.db.rollback()
            raise

    def get_tasks(
        self,
        project_id: Optional[int] = None,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> List[ProjectTask]:
        """获取任务列表"""
        query = self.db.query(ProjectTask)

        if project_id:
            query = query.filter(ProjectTask.project_id == project_id)

        if user_id:
            query = query.filter(ProjectTask.user_id == user_id)

        if status:
            query = query.filter(ProjectTask.status == status)

        return query.order_by(ProjectTask.due_date).all()

    def update_task_status(self, task_id: int, status: str):
        """更新任务状态"""
        try:
            task = self.db.query(ProjectTask).filter(ProjectTask.id == task_id).first()

            if not task:
                raise ValueError(f"任务不存在：{task_id}")

            task.status = status
            self.db.commit()

            logger.info(f"✅ 任务 {task_id} 状态更新为 {status}")

        except Exception as e:
            logger.error(f"❌ 更新任务状态失败：{e}")
            self.db.rollback()
            raise

    # ==================== 同伴审查服务 ====================

    def create_peer_review(
        self,
        project_id: int,
        reviewer_id: int,
        reviewee_id: int,
        feedback: str,
        score: Optional[int] = None,
    ) -> PeerReview:
        """创建同伴审查"""
        try:
            review = PeerReview(
                project_id=project_id,
                reviewer_id=reviewer_id,
                reviewee_id=reviewee_id,
                feedback=feedback,
                score=score,
                status=ReviewStatus.COMPLETED if feedback else ReviewStatus.PENDING,
            )
            self.db.add(review)
            self.db.commit()
            self.db.refresh(review)

            logger.info(
                f"✅ 用户 {reviewer_id} 审查了用户 {reviewee_id} 的项目 {project_id}"
            )
            return review

        except Exception as e:
            logger.error(f"❌ 创建审查失败：{e}")
            self.db.rollback()
            raise

    def get_peer_reviews(
        self,
        project_id: Optional[int] = None,
        reviewer_id: Optional[int] = None,
        reviewee_id: Optional[int] = None,
    ) -> List[PeerReview]:
        """获取审查列表"""
        query = self.db.query(PeerReview)

        if project_id:
            query = query.filter(PeerReview.project_id == project_id)

        if reviewer_id:
            query = query.filter(PeerReview.reviewer_id == reviewer_id)

        if reviewee_id:
            query = query.filter(PeerReview.reviewee_id == reviewee_id)

        return query.order_by(desc(PeerReview.created_at)).all()

    def request_peer_review(
        self, project_id: int, reviewee_id: int, potential_reviewers: List[int]
    ) -> List[PeerReview]:
        """请求同伴审查（分配给多个潜在审查人）"""
        reviews = []
        for reviewer_id in potential_reviewers:
            try:
                review = PeerReview(
                    project_id=project_id,
                    reviewer_id=reviewer_id,
                    reviewee_id=reviewee_id,
                    status=ReviewStatus.PENDING,
                )
                self.db.add(review)
                reviews.append(review)
            except Exception as e:
                logger.warning(f"审查人 {reviewer_id} 已存在，跳过")

        self.db.commit()
        return reviews


def get_collaboration_service(db: Session) -> CollaborationService:
    """获取协作学习服务实例"""
    return CollaborationService(db)
