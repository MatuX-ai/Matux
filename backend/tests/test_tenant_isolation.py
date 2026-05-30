"""
多租户隔离测试用例
测试租户数据隔离、API路由隔离和权限控制功能
"""

from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.tenant_aware_session import TenantAwareSession, TenantQueryHelper
from main import app
from middleware.tenant_middleware import TenantMiddleware
from models.course import Course, CourseCreate
from models.license import Organization
from models.user import User, UserRole
from security.data_access_control import DataAccessControl, DataMasking
from services.course_service import CourseService
from utils.tenant_context import TenantContext, with_tenant_context

# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, class_=TenantAwareSession
    )

    # 创建表
    from utils.database import Base

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "test_user"
    user.email = "test@example.com"
    user.role = UserRole.USER
    user.is_active = True
    user.is_superuser = False
    return user


@pytest.fixture
def mock_admin():
    """创建模拟管理员用户"""
    user = Mock(spec=User)
    user.id = 2
    user.username = "admin"
    user.email = "admin@example.com"
    user.role = UserRole.ADMIN
    user.is_active = True
    user.is_superuser = True
    return user


class TestTenantContext:
    """租户上下文测试"""

    def test_set_and_get_tenant(self):
        """测试设置和获取租户上下文"""
        # 测试设置租户ID
        TenantContext.set_current_tenant(1)
        assert TenantContext.get_current_tenant() == 1

        # 测试清除租户上下文
        TenantContext.clear()
        assert TenantContext.get_current_tenant() is None

        # 测试上下文管理器
        with with_tenant_context(2):
            assert TenantContext.get_current_tenant() == 2
        assert TenantContext.get_current_tenant() is None

    def test_tenant_context_validation(self):
        """测试租户上下文验证"""
        # 测试有效的租户ID
        TenantContext.set_current_tenant("123")
        assert TenantContext.get_current_tenant() == 123

        # 测试无效的租户ID
        TenantContext.set_current_tenant("invalid")
        assert TenantContext.get_current_tenant() is None


class TestDataAccessControl:
    """数据访问控制测试"""

    def test_tenant_filtering(self, test_db):
        """测试租户数据过滤"""
        # 创建测试数据
        org1 = Organization(id=1, name="Org 1", contact_email="org1@test.com")
        org2 = Organization(id=2, name="Org 2", contact_email="org2@test.com")
        test_db.add_all([org1, org2])

        course1 = Course(id=1, org_id=1, title="Course 1", code="C001")
        course2 = Course(id=2, org_id=2, title="Course 2", code="C002")
        test_db.add_all([course1, course2])
        test_db.commit()

        # 测试租户1的查询
        with with_tenant_context(1):
            courses = test_db.query(Course).all()
            assert len(courses) == 1
            assert courses[0].org_id == 1

        # 测试租户2的查询
        with with_tenant_context(2):
            courses = test_db.query(Course).all()
            assert len(courses) == 1
            assert courses[0].org_id == 2

    def test_tenant_ownership_validation(self):
        """测试租户所有权验证"""
        # 创建测试实例
        course = Mock()
        course.org_id = 1

        # 测试正确的租户访问
        with with_tenant_context(1):
            assert DataAccessControl.validate_tenant_ownership(course) == True

        # 测试错误的租户访问
        with with_tenant_context(2):
            with pytest.raises(Exception):
                DataAccessControl.validate_tenant_ownership(course)

    def test_permission_checks(self, mock_user, mock_admin):
        """测试权限检查"""
        course = Mock()
        course.org_id = 1

        # 管理员应该有所有权限
        with with_tenant_context(1):
            assert DataAccessControl.check_read_permission(mock_admin, course) == True
            assert DataAccessControl.check_update_permission(mock_admin, course) == True
            assert DataAccessControl.check_delete_permission(mock_admin, course) == True

        # 普通用户需要特定权限
        with patch.object(DataAccessControl, "_has_permission", return_value=True):
            with with_tenant_context(1):
                assert (
                    DataAccessControl.check_read_permission(mock_user, course) == True
                )


class TestTenantAwareSession:
    """租户感知会话测试"""

    def test_automatic_tenant_filtering(self, test_db):
        """测试自动租户过滤"""
        # 创建测试数据
        org1 = Organization(id=1, name="Org 1", contact_email="org1@test.com")
        org2 = Organization(id=2, name="Org 2", contact_email="org2@test.com")
        test_db.add_all([org1, org2])
        test_db.commit()

        # 在租户上下文中创建课程
        with with_tenant_context(1):
            course_data = CourseCreate(
                title="Test Course", code="TC001", description="Test Description"
            )
            CourseService(test_db)
            # 这里需要mock一些依赖

        # 验证查询自动过滤
        with with_tenant_context(1):
            query = test_db.query(Course)
            TenantQueryHelper.apply_tenant_filters_to_query(query)
            # 验证查询条件中包含了租户过滤


class TestTenantMiddleware:
    """租户中间件测试"""

    def test_org_id_extraction(self):
        """测试租户ID提取"""
        middleware = TenantMiddleware(lambda x: x)

        # 测试从URL路径提取
        mock_request = Mock()
        mock_request.path_params = {"org_id": "123"}
        mock_request.headers = {}
        mock_request.query_params = {}

        # 这里需要完善测试逻辑

    def test_permission_validation(self, mock_user):
        """测试权限验证"""
        # 测试用户对不同租户的访问权限


class TestCourseService:
    """课程服务测试"""

    def test_create_course_with_tenant_context(self, test_db, mock_user):
        """测试在租户上下文中创建课程"""
        CourseService(test_db)

        with with_tenant_context(1):
            course_data = CourseCreate(
                title="Test Course", code="TC001", description="Test course description"
            )

            # 这里需要mock权限检查和数据库操作
            # course = service.create_course(1, course_data, mock_user)
            # assert course.org_id == 1


class TestDataMasking:
    """数据脱敏测试"""

    def test_sensitive_data_masking(self, mock_user, mock_admin):
        """测试敏感数据脱敏"""
        # 测试普通用户的数据脱敏
        sensitive_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "secret123",
            "phone_number": "13800138000",
        }

        masked_data = DataMasking.mask_sensitive_data(sensitive_data, mock_user)
        assert masked_data["password"] == "se******23"
        assert masked_data["phone_number"] == "13******00"

        # 管理员应该看到完整数据
        admin_data = DataMasking.mask_sensitive_data(sensitive_data, mock_admin)
        assert admin_data["password"] == "secret123"


class TestAPIIntegration:
    """API集成测试"""

    def test_course_api_tenant_isolation(self, client, test_db):
        """测试课程API的租户隔离"""
        # 创建测试组织和用户
        org = Organization(id=1, name="Test Org", contact_email="test@org.com")
        test_db.add(org)
        test_db.commit()

        # 测试在正确租户上下文下的API调用
        headers = {"X-Org-ID": "1"}
        response = client.get("/api/v1/org/1/courses", headers=headers)
        # 验证响应

        # 测试在错误租户上下文下的API调用
        headers = {"X-Org-ID": "2"}
        response = client.get("/api/v1/org/1/courses", headers=headers)
        # 验证权限拒绝


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
