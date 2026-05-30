"""
AI-Edu 协作学习系统单元测试
测试覆盖：讨论区、协作文档、学习小组、项目管理
"""

from datetime import datetime, timedelta
import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import Base
from models.collaboration import (
    CollaborativeDocument,
    DiscussionComment,
    DiscussionPost,
    DocumentVersion,
    PeerReview,
    PostLike,
    StudyGroup,
    StudyGroupMember,
)
from services.collaboration_service import (
    CollaborationService,
    get_collaboration_service,
)

# ==================== 测试夹具 ====================


@pytest.fixture
def test_db():
    """创建测试数据库"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def collaboration_service(test_db):
    """创建协作学习服务实例"""
    return get_collaboration_service(test_db)


@pytest.fixture
def sample_user():
    """示例用户数据"""
    return {"id": 1, "username": "test_user"}


# ==================== 讨论区测试 ====================


class TestDiscussionForum:
    """讨论区测试"""

    def test_create_post(self, collaboration_service, sample_user):
        """测试创建帖子"""
        post = collaboration_service.create_post(
            user_id=sample_user["id"],
            title="Test Post",
            content="This is a test post",
            category="general",
        )

        assert post is not None
        assert post.title == "Test Post"
        assert post.content == "This is a test post"

    def test_get_posts(self, collaboration_service, sample_user, test_db):
        """测试获取帖子列表"""
        # 创建多个帖子
        for i in range(5):
            collaboration_service.create_post(
                user_id=sample_user["id"],
                title=f"Post {i}",
                content=f"Content {i}",
                category="general",
            )

        posts = collaboration_service.get_posts(limit=10)
        assert len(posts) == 5

    def test_like_post(self, collaboration_service, sample_user, test_db):
        """测试点赞帖子"""
        post = collaboration_service.create_post(
            user_id=sample_user["id"],
            title="Like Test",
            content="Test content",
            category="general",
        )

        # 点赞
        result = collaboration_service.like_post(post.id, sample_user["id"])
        assert result is True

        # 验证点赞数
        updated_post = collaboration_service.get_post(post.id)
        assert updated_post.like_count == 1

        # 重复点赞应该返回 False
        result2 = collaboration_service.like_post(post.id, sample_user["id"])
        assert result2 is False

    def test_create_comment(self, collaboration_service, sample_user, test_db):
        """测试创建评论"""
        post = collaboration_service.create_post(
            user_id=sample_user["id"],
            title="Comment Test",
            content="Test content",
            category="general",
        )

        comment = collaboration_service.create_comment(
            post_id=post.id, user_id=sample_user["id"], content="This is a comment"
        )

        assert comment is not None
        assert comment.content == "This is a comment"

        # 验证帖子评论数增加
        updated_post = collaboration_service.get_post(post.id)
        assert updated_post.comment_count == 1

    def test_increment_view_count(self, collaboration_service, sample_user, test_db):
        """测试增加浏览次数"""
        post = collaboration_service.create_post(
            user_id=sample_user["id"],
            title="View Test",
            content="Test content",
            category="general",
        )

        # 增加浏览
        collaboration_service.increment_view_count(post.id)
        collaboration_service.increment_view_count(post.id)

        updated_post = collaboration_service.get_post(post.id)
        assert updated_post.view_count == 2


# ==================== 协作文档测试 ====================


class TestCollaborativeDocument:
    """协作文档测试"""

    def test_create_document(self, collaboration_service, sample_user):
        """测试创建文档"""
        doc = collaboration_service.create_document(
            user_id=sample_user["id"],
            title="Test Document",
            content="# Test Content",
            permission="private",
        )

        assert doc is not None
        assert doc.title == "Test Document"
        assert doc.version == 1

    def test_update_document(self, collaboration_service, sample_user, test_db):
        """测试更新文档"""
        doc = collaboration_service.create_document(
            user_id=sample_user["id"],
            title="Update Test",
            content="Initial content",
            permission="private",
        )

        # 更新文档
        updated_doc = collaboration_service.update_document(
            doc_id=doc.id,
            user_id=sample_user["id"],
            content="Updated content",
            change_summary="Test update",
        )

        assert updated_doc.content == "Updated content"
        assert updated_doc.version == 2

    def test_document_version_history(
        self, collaboration_service, sample_user, test_db
    ):
        """测试文档版本历史"""
        doc = collaboration_service.create_document(
            user_id=sample_user["id"],
            title="Version Test",
            content="v1",
            permission="private",
        )

        # 多次更新
        collaboration_service.update_document(
            doc.id, sample_user["id"], "v2", "Update to v2"
        )
        collaboration_service.update_document(
            doc.id, sample_user["id"], "v3", "Update to v3"
        )

        # 获取版本历史
        versions = collaboration_service.get_document_versions(doc.id)
        assert len(versions) == 3
        assert versions[0].version_number == 3
        assert versions[1].version_number == 2
        assert versions[2].version_number == 1

    def test_add_collaborator(self, collaboration_service, sample_user, test_db):
        """测试添加协作者"""
        doc = collaboration_service.create_document(
            user_id=sample_user["id"],
            title="Collaborator Test",
            content="Content",
            permission="private",
        )

        # 添加协作者
        collaboration_service.add_collaborator(
            doc_id=doc.id,
            user_id=sample_user["id"],
            collaborator_user_id=2,
            role="editor",
        )

        # 验证协作者已添加
        updated_doc = collaboration_service.get_document(doc.id)
        assert len(updated_doc.collaborators) == 2

    def test_document_permission_check(
        self, collaboration_service, sample_user, test_db
    ):
        """测试文档权限检查"""
        # 创建私有文档
        doc = collaboration_service.create_document(
            user_id=sample_user["id"],
            title="Private Doc",
            content="Private content",
            permission="private",
        )

        # 非协作者尝试更新（应该失败）
        with pytest.raises(Exception):
            collaboration_service.update_document(
                doc_id=doc.id,
                user_id=999,  # 不同用户
                content="Hacked content",
                change_summary="Hack attempt",
            )


# ==================== 学习小组测试 ====================


class TestStudyGroup:
    """学习小组测试"""

    def test_create_study_group(self, collaboration_service, sample_user):
        """测试创建学习小组"""
        group = collaboration_service.create_study_group(
            creator_id=sample_user["id"],
            name="Test Group",
            description="A test study group",
            org_id=1,
            max_members=10,
        )

        assert group is not None
        assert group.name == "Test Group"
        assert group.member_count == 1  # 创建者自动加入

    def test_join_study_group(self, collaboration_service, sample_user, test_db):
        """测试加入学习小组"""
        group = collaboration_service.create_study_group(
            creator_id=sample_user["id"],
            name="Join Test Group",
            description="Test",
            org_id=1,
            max_members=5,
        )

        # 新成员加入
        collaboration_service.join_study_group(group.id, 2)

        # 验证人数增加
        updated_group = collaboration_service.get_study_groups(
            user_id=sample_user["id"]
        )[0]
        assert updated_group.member_count == 2

    def test_group_member_limit(self, collaboration_service, sample_user, test_db):
        """测试小组成员限制"""
        group = collaboration_service.create_study_group(
            creator_id=sample_user["id"],
            name="Limited Group",
            description="Test",
            org_id=1,
            max_members=2,
        )

        # 第一个成员加入成功
        collaboration_service.join_study_group(group.id, 2)

        # 第二个成员应该失败（已满）
        with pytest.raises(ValueError) as exc_info:
            collaboration_service.join_study_group(group.id, 3)

        assert "已满" in str(exc_info.value)

    def test_duplicate_member_join(self, collaboration_service, sample_user, test_db):
        """测试重复加入小组"""
        group = collaboration_service.create_study_group(
            creator_id=sample_user["id"],
            name="No Duplicate Group",
            description="Test",
            org_id=1,
        )

        # 第一次加入成功
        collaboration_service.join_study_group(group.id, 2)

        # 第二次加入应该失败
        with pytest.raises(ValueError) as exc_info:
            collaboration_service.join_study_group(group.id, 2)

        assert "已经是小组成员" in str(exc_info.value)

    def test_get_group_members(self, collaboration_service, sample_user, test_db):
        """测试获取小组成员"""
        group = collaboration_service.create_study_group(
            creator_id=sample_user["id"],
            name="Members Test Group",
            description="Test",
            org_id=1,
        )

        # 添加成员
        collaboration_service.join_study_group(group.id, 2)
        collaboration_service.join_study_group(group.id, 3)

        members = collaboration_service.get_group_members(group.id)
        assert len(members) == 3  # 创建者 + 2 个成员


# ==================== 同伴审查测试 ====================


class TestPeerReview:
    """同伴审查测试"""

    def test_create_peer_review(self, collaboration_service, sample_user, test_db):
        """测试创建同伴审查"""
        # 先创建小组和项目
        group = collaboration_service.create_study_group(
            creator_id=sample_user["id"],
            name="Review Group",
            description="Test",
            org_id=1,
        )

        project = collaboration_service.create_project(
            group_id=group.id,
            user_id=sample_user["id"],
            title="Review Project",
            description="Test project",
        )

        # 创建审查
        review = collaboration_service.create_peer_review(
            project_id=project.id,
            reviewer_id=2,
            reviewee_id=sample_user["id"],
            feedback="Good work!",
            score=85,
        )

        assert review is not None
        assert review.feedback == "Good work!"
        assert review.score == 85

    def test_get_peer_reviews(self, collaboration_service, sample_user, test_db):
        """测试获取审查列表"""
        # 创建小组和项目
        group = collaboration_service.create_study_group(
            creator_id=sample_user["id"],
            name="Reviews Group",
            description="Test",
            org_id=1,
        )

        project = collaboration_service.create_project(
            group_id=group.id,
            user_id=sample_user["id"],
            title="Multiple Reviews Project",
            description="Test",
        )

        # 创建多个审查
        collaboration_service.create_peer_review(
            project_id=project.id,
            reviewer_id=2,
            reviewee_id=sample_user["id"],
            feedback="Review 1",
            score=80,
        )

        collaboration_service.create_peer_review(
            project_id=project.id,
            reviewer_id=3,
            reviewee_id=sample_user["id"],
            feedback="Review 2",
            score=90,
        )

        reviews = collaboration_service.get_peer_reviews(project_id=project.id)
        assert len(reviews) == 2

    def test_duplicate_peer_review_prevention(
        self, collaboration_service, sample_user, test_db
    ):
        """测试防止重复审查"""
        # 创建小组和项目
        group = collaboration_service.create_study_group(
            creator_id=sample_user["id"],
            name="Unique Review Group",
            description="Test",
            org_id=1,
        )

        project = collaboration_service.create_project(
            group_id=group.id,
            user_id=sample_user["id"],
            title="Unique Review Project",
            description="Test",
        )

        # 第一次审查成功
        collaboration_service.create_peer_review(
            project_id=project.id,
            reviewer_id=2,
            reviewee_id=sample_user["id"],
            feedback="First review",
            score=75,
        )

        # 同一审查人再次审查应该失败（唯一约束）
        with pytest.raises(Exception):
            collaboration_service.create_peer_review(
                project_id=project.id,
                reviewer_id=2,
                reviewee_id=sample_user["id"],
                feedback="Duplicate review",
                score=80,
            )


# ==================== 边界条件测试 ====================


class TestEdgeCases:
    """边界条件测试"""

    def test_empty_post_title(self, collaboration_service, sample_user):
        """测试空标题"""
        with pytest.raises(Exception):
            collaboration_service.create_post(
                user_id=sample_user["id"],
                title="",
                content="Content without title",
                category="general",
            )

    def test_invalid_category(self, collaboration_service, sample_user):
        """测试无效分类"""
        with pytest.raises(ValueError):
            collaboration_service.create_post(
                user_id=sample_user["id"],
                title="Invalid Category",
                content="Content",
                category="invalid_category",
            )

    def test_zero_max_members(self, collaboration_service, sample_user):
        """测试零最大成员数"""
        with pytest.raises(Exception):
            collaboration_service.create_study_group(
                creator_id=sample_user["id"],
                name="Zero Members",
                description="Test",
                org_id=1,
                max_members=0,
            )

    def test_negative_score_review(self, collaboration_service, sample_user, test_db):
        """测试负分审查"""
        group = collaboration_service.create_study_group(
            creator_id=sample_user["id"],
            name="Negative Score Group",
            description="Test",
            org_id=1,
        )

        project = collaboration_service.create_project(
            group_id=group.id,
            user_id=sample_user["id"],
            title="Negative Score Project",
            description="Test",
        )

        # 负分应该能创建（虽然不合理但技术上允许）
        review = collaboration_service.create_peer_review(
            project_id=project.id,
            reviewer_id=2,
            reviewee_id=sample_user["id"],
            feedback="Very bad",
            score=-10,
        )

        assert review.score == -10


# ==================== 性能测试 ====================


class TestPerformance:
    """性能测试"""

    def test_bulk_post_creation(self, collaboration_service, sample_user):
        """测试批量创建帖子性能"""
        import time

        start_time = time.time()

        # 创建 50 个帖子
        for i in range(50):
            collaboration_service.create_post(
                user_id=sample_user["id"],
                title=f"Bulk Post {i}",
                content=f"Content {i}",
                category="general",
            )

        end_time = time.time()
        duration = end_time - start_time

        # 应该在合理时间内完成
        assert duration < 5.0  # 5 秒内

    def test_concurrent_document_updates(
        self, collaboration_service, sample_user, test_db
    ):
        """测试并发文档更新"""
        import threading

        doc = collaboration_service.create_document(
            user_id=sample_user["id"],
            title="Concurrent Update Test",
            content="Initial",
            permission="private",
        )

        errors = []

        def update_thread():
            try:
                for i in range(10):
                    collaboration_service.update_document(
                        doc_id=doc.id,
                        user_id=sample_user["id"],
                        content=f"Update {i}",
                        change_summary=f"Update {i}",
                    )
            except Exception as e:
                errors.append(e)

        # 创建多个线程
        threads = [threading.Thread(target=update_thread) for _ in range(3)]

        # 启动线程
        for t in threads:
            t.start()

        # 等待完成
        for t in threads:
            t.join()

        # 验证结果
        assert len(errors) == 0

        # 最终版本号应该是最后一个线程的更新
        final_doc = collaboration_service.get_document(doc.id)
        assert final_doc.version >= 10


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
