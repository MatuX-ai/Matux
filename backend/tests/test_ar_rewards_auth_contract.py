"""PR-3c-2d: ``ar_rewards`` 鉴权契约测试（5 个端点，本模块零 db 依赖）。

背景
----
改动前 5 个端点全部依赖 ``utils.dependencies.get_current_user_sync`` ——
该函数体直接 ``raise NotImplementedError``，FastAPI 在依赖解析阶段抛出，
因此**任何请求（含不带 token）都返回 500**，而非 401。本 PR 换成
``middleware.auth.get_current_user``。

顺带修正的 2 处既有缺陷（不修则契约测试无法跑通）
--------------------------------------------------
1. ``from ..services.achievement_badge_system import ...`` 是**越界相对导入**
   （``routes.ar_rewards.__package__`` 就是顶层 ``routes``），实测抛
   ``ImportError: attempted relative import beyond top-level package``，
   ``GET /ar/achievements/unlocked`` 恒定 500 → 改为绝对导入。
2. 3 处 ``RewardEvent(...)`` 传的是 ``data=`` 且**缺 ``event_id``**，与
   ``services.reward_event_bus.RewardEvent`` 的 dataclass 签名不符，运行期
   ``TypeError`` 被路由 ``except Exception`` 吞掉 → 恒定 500。改为仓库规范
   写法 ``event_id=... / payload=...``（见同模块 ``publish_simple``）。

本文件锁定的契约
----------------
============================= ===========================================
场景                           期望
============================= ===========================================
未携带 ``Authorization``        401
携带无效 token                  401
携带有效 token                  200
============================= ===========================================

403（已登录但无权限）当前**不可断言**：5 个端点都没有归属校验，
``user_id`` 不参与授权判断。对应用例以 ``xfail(strict=True)`` 占位。

设计说明
--------
* 被测应用是**独立 FastAPI app**，按 ``legacy_routes.py`` 的真实挂载方式
  加 ``prefix="/api/v1"``（模块自带 ``prefix="/ar"``）；
* ``ar_reward_service`` 是模块级单例且会走真实查询，200 用例用
  ``monkeypatch`` 替换成假实现；
* ``achievement_system`` 是纯内存实现，无需替换。
"""

from contextlib import asynccontextmanager
from datetime import timedelta
from types import SimpleNamespace

from fastapi import FastAPI
import httpx
import pytest

PREFIX = "/api/v1/ar"
INVALID_HEADERS = {"Authorization": "Bearer not-a-valid-jwt"}

# (方法, 相对路径, JSON body)
ENDPOINTS = [
    (
        "post",
        "/rewards/scene-completed",
        {
            "event_type": "ar_scene_completed",
            "accuracy": 96.5,
            "components_placed": 4,
            "total_time": 95.0,
            "bonus_points": 120,
            "scene_id": "test_scene_001",
            "timestamp": "2026-11-08T10:00:00",
        },
    ),
    (
        "post",
        "/rewards/component-validated",
        {
            "event_type": "ar_component_validated",
            "component_type": "resistor",
            "accuracy": 92.0,
            "is_first_placement": True,
        },
    ),
    ("get", "/rewards/summary", None),
    ("get", "/achievements/unlocked", None),
    ("post", "/events/test-scene-completion", None),
]

_ENDPOINT_IDS = [f"{m.upper()} {p}" for m, p, _b in ENDPOINTS]


# ---------------------------------------------------------------------------
# 测试替身
# ---------------------------------------------------------------------------
class _FakeResult:
    def __init__(self, user):
        self._user = user

    def scalar_one_or_none(self):
        return self._user


class _FakeAsyncSession:
    def __init__(self, user):
        self._user = user

    async def execute(self, stmt):  # noqa: ARG002 - 固定返回同一用户
        return _FakeResult(self._user)


class _FakeRewardService:
    """只实现被 ``GET /ar/rewards/summary`` 调用的那一个协程。"""

    async def get_user_ar_rewards_summary(self, user_id):
        return {"total_achievements": 0, "user_id": user_id}


def _fake_user():
    from models.user import UserRole

    return SimpleNamespace(
        id=1,
        username="contract_user",
        email="contract@example.com",
        name="contract_user",
        role=UserRole.USER,
        is_active=True,
        is_superuser=False,
    )


def _token_headers():
    from routes.auth_routes import create_access_token

    token = create_access_token(
        {"sub": "contract_user"}, expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {token}"}


def _build_app():
    from routes import ar_rewards as mod

    app = FastAPI()
    app.include_router(mod.router, prefix="/api/v1")
    return app


def _stub_dependencies(app):
    from utils.database import get_db

    app.dependency_overrides[get_db] = lambda: _FakeAsyncSession(_fake_user())


@asynccontextmanager
async def _running(app):
    transport = httpx.ASGITransport(app=app)
    try:
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


async def _call(client, method, path, body, headers=None):
    kwargs = {"headers": headers} if headers else {}
    if body is not None:
        kwargs["json"] = body
    return await getattr(client, method)(PREFIX + path, **kwargs)


# ---------------------------------------------------------------------------
# 401
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,body", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_missing_credentials_returns_401(method, path, body):
    """未携带 Authorization → 401（改动前是 500 NotImplementedError）。"""
    async with _running(_build_app()) as client:
        resp = await _call(client, method, path, body)
    assert resp.status_code == 401, resp.text


@pytest.mark.parametrize("method,path,body", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_invalid_credentials_returns_401(method, path, body):
    """携带无法解码的 token → 401。"""
    async with _running(_build_app()) as client:
        resp = await _call(client, method, path, body, INVALID_HEADERS)
    assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# 200
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,body", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_valid_credentials_returns_200(method, path, body, monkeypatch):
    """有效 token → 200；任何 5xx 都说明存根/依赖没真正修好。"""
    from routes import ar_rewards as mod

    monkeypatch.setattr(mod, "ar_reward_service", _FakeRewardService())
    app = _build_app()
    _stub_dependencies(app)
    async with _running(app) as client:
        resp = await _call(client, method, path, body, _token_headers())
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_unlocked_achievements_returns_empty_list(monkeypatch):
    """``GET /ar/achievements/unlocked`` 曾经因越界相对导入恒 500，必须 200。"""
    monkeypatch.setattr("routes.ar_rewards.ar_reward_service", _FakeRewardService())
    app = _build_app()
    _stub_dependencies(app)
    async with _running(app) as client:
        resp = await client.get(
            PREFIX + "/achievements/unlocked", headers=_token_headers()
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["data"]["achievements"] == []


@pytest.mark.asyncio
async def test_scene_completed_publishes_event(monkeypatch):
    """``RewardEvent`` 构造签名修正后，事件能被 background task 正常发布。"""
    from routes import ar_rewards as mod

    published = []

    async def _publish(event):
        published.append(event)

    monkeypatch.setattr(mod, "ar_reward_service", _FakeRewardService())
    monkeypatch.setattr(mod.reward_event_bus, "publish", _publish)
    app = _build_app()
    _stub_dependencies(app)
    async with _running(app) as client:
        resp = await _call(
            client,
            "post",
            "/rewards/scene-completed",
            ENDPOINTS[0][2],
            _token_headers(),
        )
    assert resp.status_code == 200, resp.text
    assert len(published) == 1
    event = published[0]
    assert event.event_id
    assert event.payload["scene_id"] == "test_scene_001"


# ---------------------------------------------------------------------------
# 403：归属校验尚未实现（xfail 占位）
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="ar_rewards 的 5 个端点无归属校验，user_id 全部取自 current_user.id，"
    "请求体里的 user_id 字段被忽略；跨用户请求当前返回 200。"
    "补归属校验后本用例会 XPASS",
)
@pytest.mark.asyncio
async def test_cross_user_access_denied(monkeypatch):
    """普通用户为他人写入奖励事件应 403 —— 当前实现无归属校验。"""
    from routes import ar_rewards as mod

    monkeypatch.setattr(mod, "ar_reward_service", _FakeRewardService())
    app = _build_app()
    _stub_dependencies(app)
    body = {
        "event_type": "ar_scene_completed",
        "accuracy": 96.5,
        "components_placed": 4,
        "total_time": 95.0,
        "bonus_points": 120,
        "scene_id": "test_scene_001",
        "timestamp": "2026-11-08T10:00:00",
        "user_id": 999999,
    }
    async with _running(app) as client:
        resp = await _call(
            client, "post", "/rewards/scene-completed", body, _token_headers()
        )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# 回归护栏
# ---------------------------------------------------------------------------
def test_route_module_has_no_sync_auth_stub():
    """回归护栏：本模块不得再出现同步存根依赖。"""
    from pathlib import Path

    from routes import ar_rewards as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "get_current_user_sync" not in source
    assert "from utils.dependencies" not in source
    assert source.count("Depends(get_current_user)") == 5
    assert "Depends(get_sync_db)" not in source
    assert "Depends(get_sync_session)" not in source


def test_route_module_has_no_broken_reward_event_construction():
    """回归护栏：``RewardEvent`` 必须带 ``event_id`` 且用 ``payload=``。"""
    from pathlib import Path

    from routes import ar_rewards as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert source.count("RewardEvent(") == 3
    assert source.count("event_id=") == 3
    assert "            data={" not in source
    assert "from ..services" not in source
