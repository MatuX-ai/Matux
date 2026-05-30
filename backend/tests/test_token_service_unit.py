"""
Token 服务单元测试
测试 Token 管理的核心业务逻辑
"""

from models.user import User
from services.token_service import TokenService
from models.user_license import TokenPackage, TokenPackageType, UserTokenBalance
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 使用 SQLite 内存数据库进行测试
from config.settings import Settings
settings = Settings()
settings.DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """创建测试数据库会话（禁用外键检查）"""
    engine = create_engine("sqlite:///:memory:")

    # 禁用外键检查以避免依赖问题
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.close()

    # 直接导入 Base 并创建所有需要的表
    from database import Base as DatabaseBase
    from models.user import User
    from models.user_license import TokenPackage, TokenPackageType, UserTokenBalance, TokenRechargeRecord, TokenUsageRecord

    # 创建所有表（不检查外键）
    DatabaseBase.metadata.create_all(bind=engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def token_service(db_session):
    """创建 Token 服务实例"""
    return TokenService(db_session)


@pytest.fixture
def test_user(db_session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_packages(db_session):
    """创建测试套餐"""
    packages = [
        TokenPackage(
            name="免费体验包",
            package_type=TokenPackageType.FREE,
            token_count=100,
            price=0.0,
            valid_days=30,
            is_active=True
        ),
        TokenPackage(
            name="标准套餐",
            package_type=TokenPackageType.STANDARD,
            token_count=1000,
            price=99.0,
            valid_days=365,
            is_active=True
        ),
        TokenPackage(
            name="高级套餐",
            package_type=TokenPackageType.PREMIUM,
            token_count=3000,
            price=249.0,
            valid_days=365,
            is_active=True
        ),
    ]

    for pkg in packages:
        db_session.add(pkg)

    db_session.commit()
    return packages


class TestTokenServiceBasic:
    """Token 服务基础功能测试"""

    def test_get_or_create_user_balance(self, token_service, test_user):
        """测试获取或创建用户余额"""
        # 首次获取应该创建新余额
        balance = token_service.get_or_create_user_balance(test_user.id)

        assert balance is not None
        assert balance.user_id == test_user.id
        assert balance.total_tokens == 0
        assert balance.remaining_tokens == 0

        # 再次获取应该返回同一对象
        balance2 = token_service.get_or_create_user_balance(test_user.id)
        assert balance.id == balance2.id

    def test_get_available_packages(self, token_service, test_packages):
        """测试获取可用套餐"""
        packages = token_service.get_available_packages()

        assert len(packages) == 3
        assert packages[0].price <= packages[1].price <= packages[2].price


class TestTokenPurchase:
    """Token 购买测试"""

    def test_purchase_package_success(self, token_service, test_user, test_packages):
        """测试购买套餐成功"""
        package = test_packages[1]  # 标准套餐
        order_no = "TEST_ORDER_001"

        record = token_service.purchase_token_package(
            user_id=test_user.id,
            package_id=package.id,
            payment_method="wechat",
            order_no=order_no
        )

        assert record is not None
        assert record.order_no == order_no
        assert record.token_amount == package.token_count
        assert record.payment_amount == package.price

        # 验证用户余额更新
        balance = token_service.get_or_create_user_balance(test_user.id)
        assert balance.total_tokens == package.token_count
        assert balance.remaining_tokens == package.token_count

    def test_purchase_inactive_package(self, token_service, test_user, db_session):
        """测试购买已停售的套餐"""
        # 创建已停售套餐
        package = TokenPackage(
            name="停售套餐",
            package_type=TokenPackageType.STANDARD,
            token_count=500,
            price=49.0,
            is_active=False
        )
        db_session.add(package)
        db_session.commit()

        # 应该抛出异常
        with pytest.raises(ValueError, match="无效的套餐"):
            token_service.purchase_token_package(
                user_id=test_user.id,
                package_id=package.id,
                payment_method="wechat",
                order_no="TEST_ORDER_002"
            )


class TestTokenConsumption:
    """Token 消费测试"""

    def test_consume_tokens_success(self, token_service, test_user, test_packages):
        """测试消费 Token 成功"""
        # 先购买套餐
        token_service.purchase_token_package(
            user_id=test_user.id,
            package_id=test_packages[1].id,
            payment_method="wechat",
            order_no="ORDER_001"
        )

        # 消费 Token
        success, message = token_service.consume_tokens(
            user_id=test_user.id,
            token_amount=100,
            usage_type="ai_teacher",
            usage_description="AI 对话测试"
        )

        assert success is True
        assert "成功" in message

        # 验证余额更新
        balance = token_service.get_or_create_user_balance(test_user.id)
        assert balance.remaining_tokens == 900  # 1000 - 100
        assert balance.used_tokens == 100

    def test_consume_insufficient_balance(self, token_service, test_user):
        """测试余额不足"""
        # 直接消费（余额为 0）
        success, message = token_service.consume_tokens(
            user_id=test_user.id,
            token_amount=100,
            usage_type="ai_teacher"
        )

        assert success is False
        assert "不足" in message

    def test_consume_exact_balance(self, token_service, test_user, test_packages):
        """测试刚好消费完所有 Token"""
        # 购买套餐
        token_service.purchase_token_package(
            user_id=test_user.id,
            package_id=test_packages[0].id,  # 免费包 100 tokens
            payment_method="wechat",
            order_no="ORDER_002"
        )

        # 消费全部 Token
        success, message = token_service.consume_tokens(
            user_id=test_user.id,
            token_amount=100,
            usage_type="course_generation"
        )

        assert success is True
        balance = token_service.get_or_create_user_balance(test_user.id)
        assert balance.remaining_tokens == 0
        assert balance.used_tokens == 100


class TestMonthlyBonus:
    """月度赠送测试"""

    def test_grant_monthly_bonus(self, token_service, test_user, db_session):
        """测试发放月度赠送 Token"""
        # 创建有月度赠送的余额
        balance = UserTokenBalance(
            user_id=test_user.id,
            total_tokens=0,
            remaining_tokens=0,
            monthly_bonus_tokens=100,
            last_bonus_date=None
        )
        db_session.add(balance)
        db_session.commit()

        # 发放月度 Token
        bonus = token_service.get_monthly_bonus_tokens(test_user.id)

        assert bonus == 100

        # 验证余额更新
        balance = token_service.get_or_create_user_balance(test_user.id)
        assert balance.remaining_tokens == 100
        assert balance.last_bonus_date is not None

    def test_no_duplicate_bonus(self, token_service, test_user, db_session):
        """测试不会重复发放月度 Token"""
        # 创建刚领取过的余额
        balance = UserTokenBalance(
            user_id=test_user.id,
            total_tokens=100,
            remaining_tokens=100,
            monthly_bonus_tokens=100,
            last_bonus_date=datetime.utcnow()
        )
        db_session.add(balance)
        db_session.commit()

        # 再次尝试领取
        bonus = token_service.get_monthly_bonus_tokens(test_user.id)

        assert bonus == 0  # 不应该再发放


class TestTokenStats:
    """Token 统计测试"""

    def test_get_token_stats(self, token_service, test_user, test_packages):
        """测试获取 Token 统计信息"""
        # 购买套餐
        token_service.purchase_token_package(
            user_id=test_user.id,
            package_id=test_packages[1].id,
            payment_method="wechat",
            order_no="STATS_ORDER_001"
        )

        # 消费 Token
        token_service.consume_tokens(
            user_id=test_user.id,
            token_amount=50,
            usage_type="ai_teacher",
            usage_description="测试消费"
        )

        # 获取统计
        stats = token_service.get_token_stats(test_user.id)

        assert stats["total_tokens"] == 1000
        assert stats["used_tokens"] == 50
        assert stats["remaining_tokens"] == 950
        assert stats["month_usage"] == 50
        assert len(stats["recent_recharges"]) == 1
        assert len(stats["recent_usages"]) == 1


class TestCostEstimation:
    """成本预估测试"""

    def test_estimate_course_cost(self, token_service):
        """测试课程生成成本预估"""
        assert token_service.estimate_course_cost("simple") == 50
        assert token_service.estimate_course_cost("medium") == 150
        assert token_service.estimate_course_cost("complex") == 500
        assert token_service.estimate_course_cost("unknown") == 100  # 默认值

    def test_estimate_ai_chat_cost(self, token_service):
        """测试 AI 对话成本预估"""
        assert token_service.estimate_ai_chat_cost(50) == 10   # 最少 10 tokens
        assert token_service.estimate_ai_chat_cost(
            100) == 10  # 100 字符 = 10 tokens
        assert token_service.estimate_ai_chat_cost(
            500) == 50  # 500 字符 = 50 tokens


class TestUsageSummary:
    """使用汇总测试"""

    def test_get_usage_summary_by_type(self, token_service, test_user, test_packages):
        """测试按类型统计使用情况"""
        # 购买套餐
        token_service.purchase_token_package(
            user_id=test_user.id,
            package_id=test_packages[1].id,
            payment_method="wechat",
            order_no="SUMMARY_ORDER_001"
        )

        # 多种类型的消费
        token_service.consume_tokens(
            user_id=test_user.id,
            token_amount=100,
            usage_type="ai_teacher",
            usage_description="AI 对话"
        )

        token_service.consume_tokens(
            user_id=test_user.id,
            token_amount=50,
            usage_type="course_generation",
            usage_description="课程生成"
        )

        token_service.consume_tokens(
            user_id=test_user.id,
            token_amount=30,
            usage_type="ai_teacher",
            usage_description="更多 AI 对话"
        )

        # 获取汇总
        summary = token_service.get_usage_summary_by_type(
            test_user.id, days=30)

        assert summary["ai_teacher"] == 130  # 100 + 30
        assert summary["course_generation"] == 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
