"""
AI-Edu 协作学习 API 路由
提供讨论区、协作文档、小组项目、同伴审查等功能
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from utils.database import get_sync_db
from models.user import User
from utils.dependencies import get_current_user_sync
from services.collaboration_service import (
    CollaborationService,
    get_collaboration_service,
)

logger = logging.getLogger(__name__)

# 创建路由器
discussion_router = APIRouter(
    prefix="/api/v1/org/{org_id}/collaboration/discussion", tags=["协作学习 - 讨论区"]
)

document_router = APIRouter(
    prefix="/api/v1/org/{org_id}/collaboration/document", tags=["协作学习 - 协作文档"]
)

group_router = APIRouter(
    prefix="/api/v1/org/{org_id}/collaboration/group", tags=["协作学习 - 学习小组"]
)

project_router = APIRouter(
    prefix="/api/v1/org/{org_id}/collaboration/project", tags=["协作学习 - 项目管理"]
)


# ==================== 讨论区 API ====================


@discussion_router.post("/posts")
async def create_post(
    org_id: int,
    title: str,
    content: str,
    category: str,
    post_type: str = "discussion",
    course_id: Optional[int] = None,
    tags: Optional[List[str]] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """创建帖子"""
    try:
        service = get_collaboration_service(db)
        post = service.create_post(
            user_id=current_user.id,  # type: ignore[arg-type]
            title=title,
            content=content,
            category=category,
            post_type=post_type,
            course_id=course_id,
            tags=tags,
        )

        return {"success": True, "data": post.to_dict()}

    except Exception as e:
        logger.error(f"创建帖子失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@discussion_router.get("/posts")
async def get_posts(
    org_id: int,
    category: Optional[str] = None,
    course_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order_by: str = "last_activity",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """获取帖子列表"""
    try:
        service = get_collaboration_service(db)
        posts = service.get_posts(
            category=category,
            course_id=course_id,
            limit=limit,
            offset=offset,
            order_by=order_by,
        )

        return {
            "success": True,
            "count": len(posts),
            "data": [post.to_dict() for post in posts],
        }

    except Exception as e:
        logger.error(f"获取帖子列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@discussion_router.get("/posts/{post_id}")
async def get_post(
    org_id: int,
    post_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """获取帖子详情"""
    try:
        service = get_collaboration_service(db)
        post = service.get_post(post_id)

        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # 增加浏览次数
        service.increment_view_count(post_id)

        # 获取评论
        comments = service.get_comments(post_id)

        return {
            "success": True,
            "data": {
                "post": post.to_dict(),
                "comments": [c.to_dict() for c in comments],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取帖子详情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@discussion_router.post("/posts/{post_id}/like")
async def like_post(
    org_id: int,
    post_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """点赞帖子"""
    try:
        service = get_collaboration_service(db)
        liked = service.like_post(post_id, current_user.id)  # type: ignore[arg-type]

        if liked:
            return {"success": True, "message": "点赞成功"}
        else:
            return {"success": False, "message": "已经点赞过"}

    except Exception as e:
        logger.error(f"点赞失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@discussion_router.post("/posts/{post_id}/comments")
async def create_comment(
    org_id: int,
    post_id: int,
    content: str,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """创建评论"""
    try:
        service = get_collaboration_service(db)
        comment = service.create_comment(
            post_id=post_id,
            user_id=current_user.id,  # type: ignore[arg-type]
            content=content,
            parent_id=parent_id,
        )

        return {"success": True, "data": comment.to_dict()}

    except Exception as e:
        logger.error(f"创建评论失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 协作文档 API ====================


@document_router.post("/documents")
async def create_document(
    org_id: int,
    title: str,
    content: str = "",
    group_id: Optional[int] = None,
    course_id: Optional[int] = None,
    permission: str = "private",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """创建协作文档"""
    try:
        service = get_collaboration_service(db)
        doc = service.create_document(
            user_id=current_user.id,  # type: ignore[arg-type]
            title=title,
            content=content,
            group_id=group_id,
            course_id=course_id,
            permission=permission,
        )

        return {"success": True, "data": doc.to_dict()}

    except Exception as e:
        logger.error(f"创建文档失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@document_router.get("/documents")
async def get_documents(
    org_id: int,
    group_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """获取文档列表"""
    try:
        service = get_collaboration_service(db)
        documents = service.get_documents(
            user_id=current_user.id, group_id=group_id, limit=limit  # type: ignore[arg-type]
        )

        return {
            "success": True,
            "count": len(documents),
            "data": [doc.to_dict() for doc in documents],
        }

    except Exception as e:
        logger.error(f"获取文档列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@document_router.get("/documents/{doc_id}")
async def get_document(
    org_id: int,
    doc_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """获取文档详情"""
    try:
        service = get_collaboration_service(db)
        doc = service.get_document(doc_id)

        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 检查权限
        if doc.permission.value != "public":
            is_collaborator = any(
                c.get("user_id") == current_user.id for c in doc.collaborators
            )
            if not is_collaborator and doc.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="没有查看权限")

        # 获取版本历史
        versions = service.get_document_versions(doc_id, limit=10)

        # 获取评论
        comments = (
            service.get_document_comments(doc_id)  # type: ignore[attr-defined]
            if hasattr(service, "get_document_comments")
            else []
        )

        return {
            "success": True,
            "data": {
                "document": doc.to_dict(),
                "versions": [v.to_dict() for v in versions],
                "comments": [c.to_dict() for c in comments] if comments else [],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档详情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@document_router.put("/documents/{doc_id}")
async def update_document(
    org_id: int,
    doc_id: int,
    content: str,
    change_summary: Optional[str] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """更新文档内容"""
    try:
        service = get_collaboration_service(db)
        doc = service.update_document(
            doc_id=doc_id,
            user_id=current_user.id,  # type: ignore[arg-type]
            content=content,
            change_summary=change_summary,
        )

        return {"success": True, "data": doc.to_dict()}

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新文档失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@document_router.post("/documents/{doc_id}/collaborators")
async def add_collaborator(
    org_id: int,
    doc_id: int,
    collaborator_user_id: int,
    role: str = "editor",
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """添加协作者"""
    try:
        service = get_collaboration_service(db)
        service.add_collaborator(
            doc_id=doc_id,
            user_id=current_user.id,  # type: ignore[arg-type]
            collaborator_user_id=collaborator_user_id,
            role=role,
        )

        return {"success": True, "message": "添加协作者成功"}

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"添加协作者失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@document_router.post("/documents/{doc_id}/comments")
async def add_document_comment(
    org_id: int,
    doc_id: int,
    content: str,
    line_number: Optional[int] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """添加文档评论"""
    try:
        service = get_collaboration_service(db)
        comment = service.add_document_comment(
            doc_id=doc_id,
            user_id=current_user.id,  # type: ignore[arg-type]
            content=content,
            line_number=line_number,
        )

        return {"success": True, "data": comment.to_dict()}

    except Exception as e:
        logger.error(f"添加文档评论失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 学习小组 API ====================


@group_router.post("/groups")
async def create_study_group(
    org_id: int,
    name: str,
    description: str,
    max_members: int = 10,
    is_private: bool = False,
    course_id: Optional[int] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """创建学习小组"""
    try:
        service = get_collaboration_service(db)
        group = service.create_study_group(
            creator_id=current_user.id,  # type: ignore[arg-type]
            name=name,
            description=description,
            org_id=org_id,
            course_id=course_id,
            max_members=max_members,
            is_private=is_private,
        )

        return {"success": True, "data": group.to_dict()}

    except Exception as e:
        logger.error(f"创建学习小组失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@group_router.get("/groups")
async def get_study_groups(
    org_id: int,
    course_id: Optional[int] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """获取用户参与的小组"""
    try:
        service = get_collaboration_service(db)
        groups = service.get_study_groups(
            user_id=current_user.id, org_id=org_id, course_id=course_id  # type: ignore[arg-type]
        )

        return {
            "success": True,
            "count": len(groups),
            "data": [group.to_dict() for group in groups],
        }

    except Exception as e:
        logger.error(f"获取小组列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@group_router.post("/groups/{group_id}/join")
async def join_study_group(
    org_id: int,
    group_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """加入学习小组"""
    try:
        service = get_collaboration_service(db)
        service.join_study_group(group_id, current_user.id)  # type: ignore[arg-type]

        return {"success": True, "message": "加入小组成功"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"加入小组失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@group_router.get("/groups/{group_id}/members")
async def get_group_members(
    org_id: int,
    group_id: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """获取小组成员"""
    try:
        service = get_collaboration_service(db)
        members = service.get_group_members(group_id)

        return {
            "success": True,
            "count": len(members),
            "data": [member.to_dict() for member in members],
        }

    except Exception as e:
        logger.error(f"获取成员列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 项目管理 API ====================


@project_router.post("/projects")
async def create_project(
    org_id: int,
    group_id: int,
    title: str,
    description: str,
    course_id: Optional[int] = None,
    repository_url: Optional[str] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """创建学习项目"""
    try:
        service = get_collaboration_service(db)
        project = service.create_project(
            group_id=group_id,
            user_id=current_user.id,  # type: ignore[arg-type]
            title=title,
            description=description,
            course_id=course_id,
            repository_url=repository_url,
        )

        return {"success": True, "data": project.to_dict()}

    except Exception as e:
        logger.error(f"创建项目失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.get("/projects")
async def get_projects(
    org_id: int,
    group_id: Optional[int] = None,
    user_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """获取项目列表"""
    try:
        service = get_collaboration_service(db)
        projects = service.get_projects(
            group_id=group_id, user_id=user_id or current_user.id, status=status  # type: ignore[arg-type]
        )

        return {
            "success": True,
            "count": len(projects),
            "data": [project.to_dict() for project in projects],
        }

    except Exception as e:
        logger.error(f"获取项目列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.put("/projects/{project_id}/progress")
async def update_project_progress(
    org_id: int,
    project_id: int,
    progress_percentage: int,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """更新项目进度"""
    try:
        service = get_collaboration_service(db)
        service.update_project_progress(project_id, progress_percentage)

        return {"success": True, "message": "进度更新成功"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新项目进度失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.post("/projects/{project_id}/tasks")
async def create_task(
    org_id: int,
    project_id: int,
    title: str,
    description: str,
    priority: str = "medium",
    due_date: Optional[str] = None,
    assignee_id: Optional[int] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """创建项目任务"""
    try:
        service = get_collaboration_service(db)
        service.create_task(
            project_id=project_id,
            user_id=current_user.id,  # type: ignore[arg-type]
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            assignee_id=assignee_id,
        )

        return {"success": True, "message": "任务创建成功"}

    except Exception as e:
        logger.error(f"创建任务失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.get("/projects/{project_id}/tasks")
async def get_tasks(
    org_id: int,
    project_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """获取任务列表"""
    try:
        service = get_collaboration_service(db)
        tasks = service.get_tasks(project_id=project_id, status=status)

        return {
            "success": True,
            "count": len(tasks),
            "data": [task.to_dict() for task in tasks],
        }

    except Exception as e:
        logger.error(f"获取任务列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.put("/tasks/{task_id}/status")
async def update_task_status(
    org_id: int,
    task_id: int,
    status: str,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """更新任务状态"""
    try:
        service = get_collaboration_service(db)
        service.update_task_status(task_id, status)

        return {"success": True, "message": "状态更新成功"}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新任务状态失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 同伴审查 API ====================


@project_router.post("/reviews")
async def create_peer_review(
    org_id: int,
    project_id: int,
    reviewee_id: int,
    feedback: str,
    score: Optional[int] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """创建同伴审查"""
    try:
        service = get_collaboration_service(db)
        review = service.create_peer_review(
            project_id=project_id,
            reviewer_id=current_user.id,  # type: ignore[arg-type]
            reviewee_id=reviewee_id,
            feedback=feedback,
            score=score,
        )

        return {"success": True, "data": review.to_dict()}

    except Exception as e:
        logger.error(f"创建审查失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@project_router.get("/reviews")
async def get_peer_reviews(
    org_id: int,
    project_id: Optional[int] = None,
    reviewee_id: Optional[int] = None,
    db: Session = Depends(get_sync_db),
    current_user: User = Depends(get_current_user_sync),
):
    """获取审查列表"""
    try:
        service = get_collaboration_service(db)
        reviews = service.get_peer_reviews(
            project_id=project_id, reviewer_id=current_user.id, reviewee_id=reviewee_id  # type: ignore[arg-type]
        )

        return {
            "success": True,
            "count": len(reviews),
            "data": [review.to_dict() for review in reviews],
        }

    except Exception as e:
        logger.error(f"获取审查列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
