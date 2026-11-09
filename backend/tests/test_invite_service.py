"""
【P3-C】邀请码服务测试

测试覆盖：
- 邀请码生成（唯一性 + 默认值）
- 邀请码查询（by_code / by_id / list_by_creator）
- 邀请码使用（注册场景）
- usage_limit 限制
- expires_at 过期
- 邀请记录创建
- 奖励发放（mock）
- is_available / remaining 状态判断
"""

import os
import sys
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# ==================== 测试夹具 ====================


@pytest.fixture(scope="module")
def _setup_mappers():
    """在模块级别修复 mapper 链式错误（一次性）"""
    from sqlalchemy.orm import configure_mappers
    try:
        configure_mappers()
    except Exception:
        pass
    return True


@pytest.fixture
def test_db(_setup_mappers):
    """创建内存测试数据库"""
    engine = create_engine("sqlite:///:memory:")

    # 直接用 raw SQL 建表
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100),
                phone VARCHAR(20),
                hashed_password VARCHAR(100) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                is_active BOOLEAN DEFAULT 1,
                is_superuser BOOLEAN DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL UNIQUE,
                code VARCHAR(50) UNIQUE,
                description TEXT,
                is_system BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                priority INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """))
        conn.execute(text("""
            CREATE TABLE user_roles (
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                assigned_at TIMESTAMP,
                PRIMARY KEY (user_id, role_id)
            )
        """))
        conn.commit()

    # 用 ORM 创建 invite_codes / invite_records
    from models.share import InviteCode, InviteRecord
    from utils.database import Base as UBase
    UBase.metadata.create_all(
        bind=engine,
        tables=[InviteCode.__table__, InviteRecord.__table__],
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    db = TestingSessionLocal()
    db._engine = engine
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def invite_service(test_db):
    """创建邀请服务实例"""
    from services.invite_service import get_invite_service
    return get_invite_service(test_db)


@pytest.fixture
def sample_creator(test_db):
    """插入邀请人（creator）"""
    engine = test_db._engine
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (id, username, email, hashed_password, role, is_active, is_superuser)
            VALUES (1, 'creator', 'creator@example.com', 'fake_hash', 'STUDENT', 1, 0)
        """))
    user = MagicMock()
    user.id = 1
    user.username = "creator"
    return user


@pytest.fixture
def sample_invitee(test_db):
    """插入被邀请人（invitee）"""
    engine = test_db._engine
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (id, username, email, hashed_password, role, is_active, is_superuser)
            VALUES (2, 'invitee', 'invitee@example.com', 'fake_hash', 'STUDENT', 1, 0)
        """))
    user = MagicMock()
    user.id = 2
    user.username = "invitee"
    return user


# ==================== 生成邀请码测试 ====================


class TestCreateInviteCode:
    """创建邀请码测试"""

    def test_create_code_default_values(self, invite_service, sample_creator):
        """创建邀请码使用默认值"""
        from models.share import InviteCodeStatus, RewardType

        invite = invite_service.create_code(creator_id=sample_creator.id)

        assert invite.id is not None
        assert invite.creator_id == sample_creator.id
        assert invite.code is not None
        assert len(invite.code) == 8
        assert invite.usage_limit is None  # 默认无限
        assert invite.used_count == 0
        assert invite.reward_type == RewardType.POINTS
        assert invite.reward_value == 100
        assert invite.status == InviteCodeStatus.ACTIVE
        assert invite.expires_at is None

    def test_create_code_with_usage_limit(self, invite_service, sample_creator):
        """创建带使用上限的邀请码"""
        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            usage_limit=5,
        )
        assert invite.usage_limit == 5
        assert invite.remaining() == 5

    def test_create_code_with_custom_reward(self, invite_service, sample_creator):
        """自定义奖励"""
        from models.share import RewardType

        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            reward_type=RewardType.DISCOUNT,
            reward_value=50,
        )
        assert invite.reward_type == RewardType.DISCOUNT
        assert invite.reward_value == 50

    def test_create_code_with_channel(self, invite_service, sample_creator):
        """指定推广渠道"""
        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            channel="wechat",
        )
        assert invite.channel == "wechat"

    def test_create_code_with_expires_at(self, invite_service, sample_creator):
        """设置过期时间"""
        future = datetime.utcnow() + timedelta(days=7)
        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            expires_at=future,
        )
        assert invite.expires_at is not None

    def test_codes_are_unique(self, invite_service, sample_creator):
        """邀请码必须唯一"""
        codes = set()
        for _ in range(20):
            invite = invite_service.create_code(creator_id=sample_creator.id)
            assert invite.code not in codes
            codes.add(invite.code)
        assert len(codes) == 20


# ==================== 查询测试 ====================


class TestInviteCodeQueries:
    """邀请码查询测试"""

    def test_get_by_code(self, invite_service, sample_creator):
        """通过 code 查询"""
        invite = invite_service.create_code(creator_id=sample_creator.id)
        found = invite_service.get_by_code(invite.code)
        assert found is not None
        assert found.id == invite.id

    def test_get_by_code_not_found(self, invite_service):
        """查询不存在的 code"""
        found = invite_service.get_by_code("nonexistent")
        assert found is None

    def test_get_by_id(self, invite_service, sample_creator):
        """通过 ID 查询"""
        invite = invite_service.create_code(creator_id=sample_creator.id)
        found = invite_service.get_by_id(invite.id)
        assert found is not None
        assert found.code == invite.code

    def test_list_by_creator(self, invite_service, sample_creator):
        """列出我创建的所有邀请码"""
        for _ in range(3):
            invite_service.create_code(creator_id=sample_creator.id)
        invites = invite_service.list_by_creator(sample_creator.id)
        assert len(invites) == 3

    def test_list_by_creator_empty(self, invite_service, sample_invitee):
        """其他用户的邀请码不返回"""
        # 没有为 sample_invitee 创建任何邀请码
        invites = invite_service.list_by_creator(sample_invitee.id)
        assert len(invites) == 0


# ==================== 使用邀请码测试 ====================


class TestUseInviteCode:
    """使用邀请码测试"""

    def test_use_code_success(self, invite_service, sample_creator, sample_invitee):
        """成功使用邀请码"""
        invite = invite_service.create_code(creator_id=sample_creator.id)
        record = invite_service.use_code(
            code=invite.code,
            invitee_id=sample_invitee.id,
        )

        assert record.id is not None
        assert record.inviter_id == sample_creator.id
        assert record.invitee_id == sample_invitee.id
        assert record.code_id == invite.id
        assert record.registered_at is not None
        assert record.status == "rewarded"  # mock 奖励立即发放

        # 邀请码使用次数 +1
        refreshed = invite_service.get_by_code(invite.code)
        assert refreshed.used_count == 1

    def test_use_code_with_metadata(self, invite_service, sample_creator, sample_invitee):
        """使用邀请码时附带元数据"""
        invite = invite_service.create_code(creator_id=sample_creator.id)
        metadata = {"ip": "127.0.0.1", "device": "iOS"}
        record = invite_service.use_code(
            code=invite.code,
            invitee_id=sample_invitee.id,
            metadata=metadata,
        )
        assert record.extra_metadata == metadata

    def test_use_code_not_found_raises(self, invite_service, sample_invitee):
        """使用不存在的邀请码抛 InviteCodeNotFound"""
        from services.invite_service import InviteCodeNotFound

        with pytest.raises(InviteCodeNotFound):
            invite_service.use_code(
                code="nonexistent",
                invitee_id=sample_invitee.id,
            )

    def test_use_code_exhausted_raises(self, invite_service, sample_creator, sample_invitee):
        """使用上限已满抛 InviteCodeAlreadyExhausted"""
        from services.invite_service import InviteCodeAlreadyExhausted
        from models.user import UserRole
        from models.user import User

        # 创建 limit=2 的邀请码
        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            usage_limit=2,
        )
        # 创建多个被邀请人
        for invitee_id in [3, 4, 5]:
            invitee_user = User(
                id=invitee_id,
                username=f"invitee{invitee_id}",
                email=f"i{invitee_id}@example.com",
                hashed_password="fake",
                role=UserRole.STUDENT,
            )
            invite_service.db.add(invitee_user)
        invite_service.db.commit()

        # 用满 2 次
        invite_service.use_code(invite.code, invitee_id=3)
        invite_service.use_code(invite.code, invitee_id=4)

        # 第三次应该抛异常
        with pytest.raises(InviteCodeAlreadyExhausted):
            invite_service.use_code(invite.code, invitee_id=5)

    def test_use_code_expired_raises(self, invite_service, sample_creator, sample_invitee):
        """使用过期邀请码抛 InviteCodeExpired"""
        from services.invite_service import InviteCodeExpired

        # 创建已过期的邀请码
        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        with pytest.raises(InviteCodeExpired):
            invite_service.use_code(
                code=invite.code,
                invitee_id=sample_invitee.id,
            )

        # 邀请码应被标记为 expired
        refreshed = invite_service.get_by_code(invite.code)
        assert refreshed.status == "expired"

    def test_use_code_disabled_raises(self, invite_service, sample_creator, sample_invitee):
        """使用 disabled 邀请码抛 InviteCodeNotFound"""
        from services.invite_service import InviteCodeNotFound
        from models.share import InviteCodeStatus

        invite = invite_service.create_code(creator_id=sample_creator.id)
        invite.status = InviteCodeStatus.DISABLED
        invite_service.db.commit()

        with pytest.raises(InviteCodeNotFound):
            invite_service.use_code(
                code=invite.code,
                invitee_id=sample_invitee.id,
            )

    def test_use_code_marks_exhausted_when_full(
        self, invite_service, sample_creator
    ):
        """用满后自动标记为 exhausted"""
        from models.user import User, UserRole
        from models.share import InviteCodeStatus

        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            usage_limit=1,
        )
        # 创建被邀请人
        invitee = User(
            id=10,
            username="invitee10",
            email="i10@example.com",
            hashed_password="fake",
            role=UserRole.STUDENT,
        )
        invite_service.db.add(invitee)
        invite_service.db.commit()

        invite_service.use_code(invite.code, invitee_id=10)

        refreshed = invite_service.get_by_code(invite.code)
        assert refreshed.status == InviteCodeStatus.EXHAUSTED
        assert refreshed.used_count == 1
        assert refreshed.remaining() == 0


# ==================== 邀请记录测试 ====================


class TestInviteRecords:
    """邀请记录测试"""

    def test_records_created_on_use(self, invite_service, sample_creator, sample_invitee):
        """使用邀请码时创建记录"""
        invite = invite_service.create_code(creator_id=sample_creator.id)
        invite_service.use_code(invite.code, invitee_id=sample_invitee.id)

        records = invite_service.list_records_by_inviter(sample_creator.id)
        assert len(records) == 1
        assert records[0].inviter_id == sample_creator.id
        assert records[0].invitee_id == sample_invitee.id
        assert records[0].code_id == invite.id

    def test_records_ordered_desc(self, invite_service, sample_creator):
        """邀请记录按时间倒序"""
        from models.user import User, UserRole
        import time

        invite = invite_service.create_code(creator_id=sample_creator.id)
        # 创建多个被邀请人
        for i in range(3):
            u = User(
                id=100 + i,
                username=f"u{i}",
                email=f"u{i}@example.com",
                hashed_password="fake",
                role=UserRole.STUDENT,
            )
            invite_service.db.add(u)
        invite_service.db.commit()

        invite_service.use_code(invite.code, invitee_id=100)
        time.sleep(1.1)  # SQLite CURRENT_TIMESTAMP 是秒级精度，确保时间不同
        invite_service.use_code(invite.code, invitee_id=101)
        time.sleep(1.1)
        invite_service.use_code(invite.code, invitee_id=102)

        records = invite_service.list_records_by_inviter(sample_creator.id)
        assert len(records) == 3
        # 最新记录在前
        assert records[0].invitee_id == 102
        assert records[1].invitee_id == 101
        assert records[2].invitee_id == 100


# ==================== 状态判断测试 ====================


class TestInviteCodeStatus:
    """邀请码状态判断测试"""

    def test_is_available_new(self, invite_service, sample_creator):
        """新创建的邀请码可用"""
        invite = invite_service.create_code(creator_id=sample_creator.id)
        assert invite.is_available() is True

    def test_is_available_exhausted(self, invite_service, sample_creator):
        """用满后不可用"""
        from models.share import InviteCodeStatus

        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            usage_limit=1,
        )
        invite.status = InviteCodeStatus.EXHAUSTED
        assert invite.is_available() is False

    def test_is_available_expired(self, invite_service, sample_creator):
        """过期后不可用"""
        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        assert invite.is_available() is False

    def test_is_available_disabled(self, invite_service, sample_creator):
        """disabled 不可用"""
        from models.share import InviteCodeStatus
        invite = invite_service.create_code(creator_id=sample_creator.id)
        invite.status = InviteCodeStatus.DISABLED
        assert invite.is_available() is False

    def test_remaining_unlimited(self, invite_service, sample_creator):
        """无限邀请码 remaining = None"""
        invite = invite_service.create_code(creator_id=sample_creator.id)
        assert invite.remaining() is None

    def test_remaining_decrements(self, invite_service, sample_creator, sample_invitee):
        """remaining 随使用递减"""
        from models.user import User, UserRole

        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            usage_limit=5,
        )
        assert invite.remaining() == 5

        # 创建额外被邀请人
        for i in range(3, 6):
            u = User(
                id=i,
                username=f"u{i}",
                email=f"u{i}@example.com",
                hashed_password="fake",
                role=UserRole.STUDENT,
            )
            invite_service.db.add(u)
        invite_service.db.commit()

        invite_service.use_code(invite.code, invitee_id=3)
        # 重新查询以获取最新状态
        refreshed = invite_service.get_by_code(invite.code)
        assert refreshed.remaining() == 4

    def test_remaining_zero_when_full(self, invite_service, sample_creator):
        """用满后 remaining = 0"""
        from models.share import InviteCodeStatus

        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            usage_limit=2,
        )
        invite.used_count = 2
        invite.status = InviteCodeStatus.EXHAUSTED
        assert invite.remaining() == 0


# ==================== to_dict 测试 ====================


class TestInviteCodeToDict:
    """to_dict 序列化测试"""

    def test_to_dict_unlimited(self, invite_service, sample_creator):
        """无限邀请码的 to_dict"""
        invite = invite_service.create_code(creator_id=sample_creator.id)
        d = invite.to_dict()

        for key in [
            "id", "code", "creator_id", "usage_limit", "used_count",
            "remaining", "reward_type", "reward_value", "status",
            "is_available", "created_at",
        ]:
            assert key in d, f"缺少字段：{key}"

        assert d["usage_limit"] is None
        assert d["remaining"] is None

    def test_to_dict_limited(self, invite_service, sample_creator):
        """有限邀请码的 to_dict"""
        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            usage_limit=10,
        )
        d = invite.to_dict()
        assert d["usage_limit"] == 10
        assert d["remaining"] == 10


# ==================== 奖励发放测试 ====================


class TestReward:
    """奖励发放测试"""

    def test_reward_triggered_on_use(self, invite_service, sample_creator, sample_invitee):
        """使用邀请码时触发奖励发放（mock）"""
        from models.share import InviteRecordStatus

        invite = invite_service.create_code(
            creator_id=sample_creator.id,
            reward_type="points",
            reward_value=200,
        )
        record = invite_service.use_code(
            code=invite.code,
            invitee_id=sample_invitee.id,
        )
        # mock 奖励立即发放，记录状态为 rewarded
        assert record.status == InviteRecordStatus.REWARDED
        assert record.rewarded_at is not None
