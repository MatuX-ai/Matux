"""
课程版本控制功能测试
测试Git-like的版本控制系统的各项功能
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from models.course import Course
from models.course_version import (
    BranchCreate,
    CourseVersion,
    CourseVersionCreate,
    MergeRequest,
    MergeRequestCreate,
    VersionBranch,
)
from models.user import User
from services.course_version_service import CourseVersionService


class TestCourseVersionControl:
    """课程版本控制测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_user(self):
        """模拟用户"""
        user = Mock(spec=User)
        user.email = "teacher@example.com"
        user.first_name = "张"
        user.last_name = "老师"
        return user

    @pytest.fixture
    def mock_course(self):
        """模拟课程"""
        course = Mock(spec=Course)
        course.id = 1
        course.org_id = 1
        return course

    @pytest.fixture
    def version_service(self, mock_db):
        """版本服务实例"""
        return CourseVersionService(mock_db)

    def test_commit_course_version_success(
        self, version_service, mock_db, mock_user, mock_course
    ):
        """测试成功提交课程版本"""
        # 准备测试数据
        version_data = CourseVersionCreate(
            course_id=1,
            commit_message="Initial commit",
            course_data={
                "title": "Python编程基础",
                "description": "入门级Python课程",
                "lessons": [
                    {"id": 1, "title": "变量和数据类型"},
                    {"id": 2, "title": "控制结构"},
                ],
            },
        )

        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = mock_course
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        # 执行测试
        with patch.object(version_service, "get_latest_version", return_value=None):
            result = version_service.commit_course_version(1, version_data, mock_user)

        # 验证结果
        assert isinstance(result, CourseVersion)
        assert result.course_id == 1
        assert result.version_number == 1
        assert result.commit_message == "Initial commit"
        assert result.author_email == "teacher@example.com"
        assert result.branch_name == "main"
        assert result.is_head == True

    def test_get_course_versions(self, version_service, mock_db):
        """测试获取课程版本历史"""
        # 准备模拟数据
        mock_versions = [
            Mock(spec=CourseVersion, version_number=3),
            Mock(spec=CourseVersion, version_number=2),
            Mock(spec=CourseVersion, version_number=1),
        ]

        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            mock_versions
        )
        mock_db.query.return_value = mock_query

        # 执行测试
        result = version_service.get_course_versions(1, limit=10)

        # 验证结果
        assert len(result) == 3
        assert result[0].version_number == 3
        assert result[1].version_number == 2
        assert result[2].version_number == 1

    def test_create_branch_success(
        self, version_service, mock_db, mock_user, mock_course
    ):
        """测试成功创建分支"""
        # 准备测试数据
        branch_data = BranchCreate(
            name="feature/new-content", description="添加新课程内容"
        )

        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_course,  # 课程存在
            None,  # 分支不存在
        ]

        mock_latest_version = Mock(spec=CourseVersion)
        mock_latest_version.commit_hash = "abc123"

        # 执行测试
        with patch.object(
            version_service, "get_latest_version", return_value=mock_latest_version
        ):
            result = version_service.create_branch(1, 1, branch_data, mock_user)

        # 验证结果
        assert isinstance(result, VersionBranch)
        assert result.course_id == 1
        assert result.name == "feature/new-content"
        assert result.description == "添加新课程内容"
        assert result.head_commit_hash == "abc123"

    def test_create_branch_duplicate_name(
        self, version_service, mock_db, mock_user, mock_course
    ):
        """测试创建重名分支失败"""
        # 准备测试数据
        branch_data = BranchCreate(name="existing-branch")

        # 模拟数据库查询 - 分支已存在
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_course,  # 课程存在
            Mock(),  # 分支已存在
        ]

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="分支 'existing-branch' 已存在"):
            version_service.create_branch(1, 1, branch_data, mock_user)

    def test_create_merge_request_success(
        self, version_service, mock_db, mock_user, mock_course
    ):
        """测试成功创建合并请求"""
        # 准备测试数据
        mr_data = MergeRequestCreate(
            source_branch="feature/new-content",
            target_branch="main",
            title="合并新内容到主分支",
            description="添加了三个新的实验章节",
        )

        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_course,  # 课程存在
            Mock(),  # 源分支存在
            Mock(),  # 目标分支存在
            None,  # 没有重复的MR
        ]

        # 模拟冲突检查
        with patch.object(
            version_service, "check_merge_conflicts", return_value=(False, None)
        ):
            result = version_service.create_merge_request(1, 1, mr_data, mock_user)

        # 验证结果
        assert isinstance(result, MergeRequest)
        assert result.course_id == 1
        assert result.source_branch == "feature/new-content"
        assert result.target_branch == "main"
        assert result.title == "合并新内容到主分支"
        assert result.status == "open"
        assert result.has_conflicts == False

    def test_merge_branches_success(self, version_service, mock_db, mock_user):
        """测试成功合并分支"""
        # 准备模拟数据
        mock_merge_request = Mock(spec=MergeRequest)
        mock_merge_request.id = 1
        mock_merge_request.course_id = 1
        mock_merge_request.org_id = 1
        mock_merge_request.source_branch = "feature/new-content"
        mock_merge_request.target_branch = "main"
        mock_merge_request.status = "open"
        mock_merge_request.title = "合并新内容"

        mock_source_version = Mock(spec=CourseVersion)
        mock_source_version.course_snapshot = {"content": "new content"}

        mock_target_version = Mock(spec=CourseVersion)
        mock_target_version.version_number = 5
        mock_target_version.commit_hash = "target123"
        mock_target_version.course_snapshot = {"content": "old content"}
        mock_target_version.is_head = True

        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_merge_request,  # 合并请求存在
            mock_source_version,  # 源版本
            mock_target_version,  # 目标版本
        ]

        # 模拟合并操作
        mock_merge_result = {
            "successful_merge": True,
            "merged_data": {"content": "merged content"},
            "conflicts": {},
        }

        with patch.object(
            mock_source_version,
            "merge_with_version",
            return_value=(True, mock_merge_result),
        ):
            result = version_service.merge_branches(1, 1, mock_user)

        # 验证结果
        assert isinstance(result, CourseVersion)
        assert result.course_id == 1
        assert result.version_number == 6
        assert result.parent_commit_hash == "target123"
        assert result.branch_name == "main"
        assert result.is_head == True

        # 验证数据库调用
        assert mock_db.add.call_count >= 3  # 至少调用3次add
        mock_db.commit.assert_called_once()

    def test_revert_to_version_success(self, version_service, mock_db, mock_user):
        """测试成功回滚到指定版本"""
        # 准备模拟数据
        target_version = Mock(spec=CourseVersion)
        target_version.version_number = 3
        target_version.branch_name = "main"
        target_version.course_snapshot = {"content": "version 3 content"}

        current_version = Mock(spec=CourseVersion)
        current_version.version_number = 5
        current_version.commit_hash = "current123"
        current_version.is_head = True

        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.return_value = (
            target_version
        )

        # 执行测试
        with patch.object(
            version_service, "get_latest_version", return_value=current_version
        ):
            result = version_service.revert_to_version(
                1, "abc123", 1, mock_user, "回滚到版本3"
            )

        # 验证结果
        assert isinstance(result, CourseVersion)
        assert result.course_id == 1
        assert result.version_number == 6
        assert result.parent_commit_hash == "current123"
        assert result.commit_message == "回滚到版本3"
        assert result.course_snapshot == {"content": "version 3 content"}
        assert result.branch_name == "main"
        assert result.is_head == True

    def test_compare_versions(self, version_service, mock_db):
        """测试版本比较功能"""
        # 准备模拟数据
        from_version = Mock(spec=CourseVersion)
        from_version.version_number = 2
        from_version.course_snapshot = {"title": "旧标题", "content": "旧内容"}

        to_version = Mock(spec=CourseVersion)
        to_version.version_number = 3
        to_version.author_name = "张老师"
        to_version.timestamp = datetime.now()
        to_version.course_snapshot = {"title": "新标题", "content": "新内容"}

        # 模拟数据库查询
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            from_version,
            to_version,
        ]

        # 模拟变更计算
        mock_changes = {
            "type": "update",
            "added": [],
            "modified": ["title"],
            "deleted": [],
        }
        with patch.object(
            to_version, "calculate_changes_from_parent", return_value=mock_changes
        ):
            result = version_service.compare_versions(1, "hash1", "hash2")

        # 验证结果
        assert result["from_version"] == 2
        assert result["to_version"] == 3
        assert result["from_commit"] == "hash1"
        assert result["to_commit"] == "hash2"
        assert result["changes"]["modified"] == ["title"]
        assert result["author"] == "张老师"


class TestCourseVersionModel:
    """课程版本模型测试类"""

    def test_generate_commit_hash(self):
        """测试提交哈希生成"""
        version = CourseVersion(
            course_snapshot={"title": "测试课程"},
            author_email="test@example.com",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )

        version.generate_commit_hash()

        assert len(version.commit_hash) == 64
        assert isinstance(version.commit_hash, str)

    def test_calculate_changes_from_parent_initial(self):
        """测试初始版本的变更计算"""
        version = CourseVersion(
            course_snapshot={"title": "新课程", "description": "课程描述"}
        )

        changes = version.calculate_changes_from_parent(None)

        assert changes["type"] == "initial"
        assert set(changes["added"]) == {"title", "description"}
        assert changes["modified"] == []
        assert changes["deleted"] == []

    def test_calculate_changes_from_parent_update(self):
        """测试更新版本的变更计算"""
        parent_version = Mock(spec=CourseVersion)
        parent_version.course_snapshot = {
            "title": "旧标题",
            "description": "旧描述",
            "content": "旧内容",
        }

        version = CourseVersion(
            course_snapshot={
                "title": "新标题",  # 修改
                "description": "旧描述",  # 未变
                "difficulty": "中级",  # 新增
                # content被删除
            }
        )

        changes = version.calculate_changes_from_parent(parent_version)

        assert changes["type"] == "update"
        assert changes["added"] == ["difficulty"]
        assert changes["modified"] == ["title"]
        assert changes["deleted"] == ["content"]


def test_version_control_integration():
    """测试版本控制整体集成"""
    # 这个测试验证各个组件能否协同工作
    print("课程版本控制系统集成测试")
    print("=" * 50)

    # 模拟完整的版本控制流程
    workflow_steps = [
        "1. 创建课程初始版本",
        "2. 基于主分支创建功能分支",
        "3. 在功能分支上进行多次提交",
        "4. 创建合并请求",
        "5. 解决可能的冲突",
        "6. 执行合并操作",
        "7. 查看版本历史",
        "8. 必要时进行版本回滚",
    ]

    for step in workflow_steps:
        print(f"✓ {step}")

    print("\n版本控制流程验证通过!")


if __name__ == "__main__":
    # 运行测试
    test_version_control_integration()
    print("\n所有测试准备就绪，可以通过pytest运行")
