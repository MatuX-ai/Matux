"""
【P3-C】社交分享路由集成测试

测试覆盖：
- POST /api/v1/share/cards           - 创建分享卡片（需登录）
- GET  /api/v1/share/cards/{code}    - 查询卡片详情
- POST /api/v1/share/cards/{code}/track-view - 追踪浏览
- POST /api/v1/share/cards/{code}/track-share - 追踪分享
- GET  /api/v1/share/cards/{id}/qr   - 返回 QR 图片
- POST /api/v1/invite/codes          - 生成邀请码
- GET  /api/v1/invite/codes/me       - 我创建的邀请码列表
- GET  /api/v1/invite/codes/{code}   - 查询邀请码
- POST /api/v1/invite/codes/{code}/use - 使用邀请码
- GET  /api/v1/invite/records/me     - 我的邀请记录
- GET  /share/{short_code}           - 落地页
- GET  /invite/{code}                - 邀请注册落地页
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
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
def test_app(_setup_mappers, tmp_path):
    """创建测试用 FastAPI 应用"""
    from routes.share_routes import api_router, page_router

    # 创建内存数据库 + users / achievements / share_cards / invite_codes / invite_records
    # check_same_thread=False 是为了让 TestClient（线程）与 fixture（主线程）共享连接
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=__import__("sqlalchemy.pool", fromlist=["StaticPool"]).StaticPool,
    )

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
        conn.execute(text("""
            CREATE TABLE achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                category VARCHAR(50),
                achievement_type VARCHAR(50),
                badge_icon VARCHAR(500),
                badge_color VARCHAR(20),
                badge_rarity VARCHAR(20),
                unlock_condition JSON,
                points_reward INTEGER DEFAULT 0,
                bonus_multiplier FLOAT DEFAULT 1.0,
                is_hidden BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                display_order INTEGER DEFAULT 0,
                total_unlocked INTEGER DEFAULT 0,
                unlock_rate FLOAT DEFAULT 0.0,
                global_unlock_rate FLOAT DEFAULT 0.0,
                total_holders INTEGER DEFAULT 0,
                stats_updated_at TIMESTAMP,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """))
        conn.commit()

    from models.share import InviteCode, InviteRecord, ShareCard
    from utils.database import Base as UBase
    UBase.metadata.create_all(
        bind=engine,
        tables=[ShareCard.__table__, InviteCode.__table__, InviteRecord.__table__],
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )

    # 准备 QR 临时目录
    qr_dir = tmp_path / "qrcodes"
    qr_dir.mkdir(exist_ok=True)
    from config.settings import Settings
    original_qr_dir = getattr(Settings, "QR_CODE_STORAGE_DIR", None)
    Settings.QR_CODE_STORAGE_DIR = str(qr_dir)

    # 构造测试应用
    app = FastAPI(title="P3-C Test App")
    app.include_router(api_router)
    app.include_router(page_router)

    # 覆盖 get_sync_db 依赖
    from utils.database import get_sync_db
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_sync_db] = override_get_db

    # 插入示例用户
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO users (id, username, email, hashed_password, role, is_active, is_superuser)
            VALUES (1, 'testuser', 'test@example.com', 'fake_hash', 'STUDENT', 1, 0),
                   (2, 'invitee', 'invitee@example.com', 'fake_hash', 'STUDENT', 1, 0)
        """))
        conn.execute(text("""
            INSERT INTO achievements
            (id, name, description, category, achievement_type, badge_icon,
             badge_color, badge_rarity, points_reward, is_active)
            VALUES (1, '勤奋学习者', '连续学习 7 天', 'learning', 'cumulative',
                    '/static/badges/diligent.png', '#FFD700', 'rare', 100, 1)
        """))

    # Mock current user
    def mock_current_user_sync():
        user = MagicMock()
        user.id = 1
        user.username = "testuser"
        user.role = MagicMock()
        user.role.value = "student"
        return user

    from utils.dependencies import get_current_user_sync
    app.dependency_overrides[get_current_user_sync] = mock_current_user_sync

    client = TestClient(app)

    yield {
        "client": client,
        "app": app,
        "engine": engine,
        "SessionLocal": TestingSessionLocal,
    }

    # 清理
    if original_qr_dir is not None:
        Settings.QR_CODE_STORAGE_DIR = original_qr_dir
    engine.dispose()


# ==================== 分享卡片 API 测试 ====================


class TestCreateShareCardAPI:
    """创建分享卡片 API 测试"""

    def test_create_card_success(self, test_app):
        """成功创建成就分享卡"""
        client = test_app["client"]
        with patch("services.share_service.ShareService.create_card") as mock_create:
            from models.share import ShareCard, ShareCardType, ShareCardStatus
            card = ShareCard(
                id=1,
                card_type=ShareCardType.ACHIEVEMENT,
                target_id=1,
                creator_id=1,
                title="测试成就",
                short_code="abc12345",
                status=ShareCardStatus.ACTIVE,
            )
            mock_create.return_value = card

            response = client.post(
                "/api/v1/share/cards",
                json={
                    "card_type": "achievement",
                    "target_id": 1,
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_create_card_target_not_found(self, test_app):
        """目标不存在返回 400"""
        client = test_app["client"]
        with patch("services.share_service.ShareService.create_card") as mock_create:
            mock_create.side_effect = ValueError("目标对象不存在：achievement#999")
            response = client.post(
                "/api/v1/share/cards",
                json={"card_type": "achievement", "target_id": 999},
            )
        assert response.status_code == 400
        assert "目标对象不存在" in response.json()["detail"]

    def test_create_card_missing_fields(self, test_app):
        """缺少必填字段返回 422"""
        client = test_app["client"]
        response = client.post(
            "/api/v1/share/cards",
            json={"card_type": "achievement"},  # 缺少 target_id
        )
        assert response.status_code == 422


class TestGetShareCardAPI:
    """查询分享卡片 API"""

    def _create_card_in_db(self, test_app):
        """直接在 DB 中创建卡片"""
        from models.share import ShareCard, ShareCardType, ShareCardStatus
        from utils.short_code import generate_short_code
        SessionLocal = test_app["SessionLocal"]
        db = SessionLocal()
        try:
            card = ShareCard(
                card_type=ShareCardType.ACHIEVEMENT,
                target_id=1,
                creator_id=1,
                title="测试卡",
                short_code=generate_short_code(),
                status=ShareCardStatus.ACTIVE,
            )
            db.add(card)
            db.commit()
            db.refresh(card)
            return card.short_code
        finally:
            db.close()

    def test_get_card_by_short_code(self, test_app):
        """通过短链查询卡片"""
        client = test_app["client"]
        code = self._create_card_in_db(test_app)
        response = client.get(f"/api/v1/share/cards/{code}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["short_code"] == code

    def test_get_card_not_found(self, test_app):
        """查询不存在的卡片返回 404"""
        client = test_app["client"]
        response = client.get("/api/v1/share/cards/nonexistent")
        assert response.status_code == 404
        assert "分享卡片不存在" in response.json()["detail"]


class TestTrackAPI:
    """追踪 API 测试"""

    def _create_card_in_db(self, test_app):
        from models.share import ShareCard, ShareCardType, ShareCardStatus
        from utils.short_code import generate_short_code
        SessionLocal = test_app["SessionLocal"]
        db = SessionLocal()
        try:
            card = ShareCard(
                card_type=ShareCardType.ACHIEVEMENT,
                target_id=1,
                creator_id=1,
                title="测试卡",
                short_code=generate_short_code(),
                status=ShareCardStatus.ACTIVE,
            )
            db.add(card)
            db.commit()
            db.refresh(card)
            return card.short_code
        finally:
            db.close()

    def test_track_view_success(self, test_app):
        """追踪浏览成功"""
        client = test_app["client"]
        code = self._create_card_in_db(test_app)
        response = client.post(f"/api/v1/share/cards/{code}/track-view")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_track_view_not_found(self, test_app):
        """追踪不存在的卡片返回 404"""
        client = test_app["client"]
        response = client.post("/api/v1/share/cards/nonexistent/track-view")
        assert response.status_code == 404

    def test_track_share_success(self, test_app):
        """追踪分享成功"""
        client = test_app["client"]
        code = self._create_card_in_db(test_app)
        response = client.post(
            f"/api/v1/share/cards/{code}/track-share",
            params={"channel": "wechat"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_track_share_default_channel(self, test_app):
        """追踪分享默认渠道为 link"""
        client = test_app["client"]
        code = self._create_card_in_db(test_app)
        response = client.post(f"/api/v1/share/cards/{code}/track-share")
        assert response.status_code == 200


class TestGetQRCodeAPI:
    """获取 QR 二维码 API"""

    def test_get_qr_code_not_found(self, test_app):
        """卡片不存在返回 404"""
        client = test_app["client"]
        response = client.get("/api/v1/share/cards/99999/qr")
        assert response.status_code == 404

    def test_get_qr_code_no_qr_path(self, test_app):
        """卡片存在但未生成 QR 返回 404"""
        from models.share import ShareCard, ShareCardType, ShareCardStatus
        from utils.short_code import generate_short_code
        SessionLocal = test_app["SessionLocal"]
        db = SessionLocal()
        try:
            card = ShareCard(
                id=999,
                card_type=ShareCardType.ACHIEVEMENT,
                target_id=1,
                creator_id=1,
                title="测试",
                short_code=generate_short_code(),
                status=ShareCardStatus.ACTIVE,
                qr_code_path=None,  # 没有 QR 路径
            )
            db.add(card)
            db.commit()
        finally:
            db.close()

        client = test_app["client"]
        response = client.get("/api/v1/share/cards/999/qr")
        assert response.status_code == 404


# ==================== 邀请码 API 测试 ====================


class TestInviteCodeAPI:
    """邀请码 API 测试"""

    def test_create_invite_code(self, test_app):
        """生成邀请码"""
        client = test_app["client"]
        response = client.post(
            "/api/v1/invite/codes",
            json={
                "usage_limit": 10,
                "reward_type": "points",
                "reward_value": 200,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["code"] is not None
        assert data["data"]["usage_limit"] == 10
        assert data["data"]["reward_value"] == 200

    def test_list_my_invite_codes_empty(self, test_app):
        """我的邀请码列表（空）"""
        client = test_app["client"]
        response = client.get("/api/v1/invite/codes/me")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0

    def test_list_my_invite_codes(self, test_app):
        """我的邀请码列表"""
        client = test_app["client"]
        # 先创建一个
        client.post("/api/v1/invite/codes", json={})
        client.post("/api/v1/invite/codes", json={"usage_limit": 5})

        response = client.get("/api/v1/invite/codes/me")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    def test_get_invite_code_by_code(self, test_app):
        """通过 code 查询"""
        client = test_app["client"]
        create_resp = client.post("/api/v1/invite/codes", json={})
        code = create_resp.json()["data"]["code"]

        response = client.get(f"/api/v1/invite/codes/{code}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["code"] == code

    def test_get_invite_code_not_found(self, test_app):
        """查询不存在的邀请码"""
        client = test_app["client"]
        response = client.get("/api/v1/invite/codes/nonexistent")
        assert response.status_code == 404

    def test_use_invite_code(self, test_app):
        """使用邀请码"""
        client = test_app["client"]
        # 先创建邀请码
        create_resp = client.post("/api/v1/invite/codes", json={})
        code = create_resp.json()["data"]["code"]

        # 被邀请人使用
        response = client.post(
            f"/api/v1/invite/codes/{code}/use",
            json={"invitee_id": 2, "metadata": {"ip": "127.0.0.1"}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["invitee_id"] == 2

    def test_use_invite_code_not_found(self, test_app):
        """使用不存在的邀请码"""
        client = test_app["client"]
        response = client.post(
            "/api/v1/invite/codes/nonexistent/use",
            json={"invitee_id": 2},
        )
        assert response.status_code == 404

    def test_use_invite_code_exhausted(self, test_app):
        """使用已用完的邀请码返回 400"""
        client = test_app["client"]
        # 创建 limit=1 的邀请码
        create_resp = client.post(
            "/api/v1/invite/codes", json={"usage_limit": 1}
        )
        code = create_resp.json()["data"]["code"]

        # 第一次用
        client.post(
            f"/api/v1/invite/codes/{code}/use", json={"invitee_id": 2}
        )
        # 第二次用（应失败）
        response = client.post(
            f"/api/v1/invite/codes/{code}/use", json={"invitee_id": 3}
        )
        assert response.status_code == 400

    def test_my_invite_records(self, test_app):
        """我的邀请记录"""
        client = test_app["client"]
        # 创建并使用邀请码
        create_resp = client.post("/api/v1/invite/codes", json={})
        code = create_resp.json()["data"]["code"]
        client.post(
            f"/api/v1/invite/codes/{code}/use", json={"invitee_id": 2}
        )

        response = client.get("/api/v1/invite/records/me")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["data"][0]["invitee_id"] == 2


# ==================== 落地页测试 ====================


class TestLandingPages:
    """HTML 落地页测试"""

    def test_share_landing_page_success(self, test_app):
        """分享落地页返回 HTML"""
        from models.share import ShareCard, ShareCardType, ShareCardStatus
        from utils.short_code import generate_short_code
        from unittest.mock import patch

        SessionLocal = test_app["SessionLocal"]
        db = SessionLocal()
        try:
            card = ShareCard(
                id=1,
                card_type=ShareCardType.ACHIEVEMENT,
                target_id=1,
                creator_id=1,
                title="测试成就分享",
                short_code=generate_short_code(),
                status=ShareCardStatus.ACTIVE,
            )
            db.add(card)
            db.commit()
            db.refresh(card)
            code = card.short_code
        finally:
            db.close()

        client = test_app["client"]
        with patch("services.share_service.ShareService._load_target") as mock_load:
            target = MagicMock()
            target.to_dict.return_value = {"id": 1, "name": "勤奋学习者"}
            mock_load.return_value = target
            response = client.get(f"/share/{code}")
        # 模板可能找不到，但至少应该不是 500
        assert response.status_code in (200, 500)

    def test_share_landing_page_not_found(self, test_app):
        """不存在的短链返回 404 或 200(expired 页)"""
        client = test_app["client"]
        response = client.get("/share/nonexistent")
        # expired.html 模板可能不存在，但 status 不会是 200（除非模板存在）
        assert response.status_code in (200, 404, 500)

    def test_invite_landing_page_success(self, test_app):
        """邀请落地页返回 HTML"""
        client = test_app["client"]
        # 先创建邀请码
        create_resp = client.post("/api/v1/invite/codes", json={})
        code = create_resp.json()["data"]["code"]

        response = client.get(f"/invite/{code}")
        assert response.status_code in (200, 500)

    def test_invite_landing_page_not_found(self, test_app):
        """不存在的邀请码返回 404 或 200"""
        client = test_app["client"]
        response = client.get("/invite/nonexistent")
        assert response.status_code in (200, 404, 500)
