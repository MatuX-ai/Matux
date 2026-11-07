"""PR-3c-2c: ``unified_learning_record_routes`` 鉴权契约测试（4 个鉴权端点）。

背景
----
改动前这 4 个端点依赖 ``utils.auth_utils.get_current_user_sync`` —— 该函数体
直接 ``raise NotImplementedError``，FastAPI 在依赖解析阶段抛出，因此**任何请求
（含不带 token）都返回 500**，而非 401。

本文件锁定的契约：

============================= ===========================================
场景                           期望
============================= ===========================================
未携带 ``Authorization``        401
携带无效 token                  401
携带有效 token                  鉴权层通过（200 / 业务 400），且 **不得 500**
============================= ===========================================

403（已登录但无权限）当前**不可断言**：4 个鉴权端点都没有 RBAC / 归属校验实现，
``user_id`` 不参与授权判断。对应 ``test_cross_user_access_denied`` 以
``xfail(strict=True)`` 占位。

补充事实（不在本 PR 修复范围，仅记录）
--------------------------------------
本模块另有 3 个**完全没有鉴权依赖**的读端点：
``GET /unified-learning-records/{record_id}``、``GET /unified-learning-records/user/{user_id}``、
``GET /unified-learning/progress/{user_id}`` —— 任意匿名请求都能读到他人学习记录。
它们不属于本 PR 的 37 处存根，改动会扩大鉴权面，故留待后续 issue。

设计说明
--------
* 被测应用是**独立 FastAPI app**，只挂载本模块 router：这些 2c 模块在
  ``core/router_registry.py`` 里都是 ``mode="legacy"`` 条目，默认 lazy 入口
  （``main_ai_edu.app``）不挂载它们，用 conftest 的 ``client`` 只会得到 404；
* 401 用例走**真实** ``middleware.auth.get_current_user`` 依赖链，不 override；
* 200 用例 override ``utils.database.get_db``（固定用户的假 AsyncSession）与
  ``get_sync_session``（``MagicMock``），并让 service 抛 ``ValueError`` 落到路由的
  400 分支 —— 只验证「鉴权通过后请求能进到路由体」，不触碰真实库。
"""

from contextlib import asynccontextmanager
from datetime import timedelta
from unittest.mock import MagicMock

from fastapi import FastAPI
import httpx
import pytest

PREFIX = "/api/v1"
INVALID_HEADERS = {"Authorization": "Bearer not-a-valid-jwt"}

# (方法, 相对路径, JSON body)
ENDPOINTS = [
    ("post", "/unified-learning-records", {"user_id": 1, "learning_source_id": 1}),
    (
        "put",
        "/unified-learning-records/1",
        {"progress_percentage": 10.0},
    ),
    ("delete", "/unified-learning-records/1", None),
    (
        "post",
        "/unified-learning-records/sync-from-enrollment",
        {"enrollment_id": 1, "user_id": 1, "learning_source_id": 1},
    ),
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
    """``get_current_user`` 只用到 ``execute(stmt).scalar_one_or_none()``。"""

    def __init__(self, user):
        self._user = user

    async def execute(self, stmt):  # noqa: ARG002 - 固定返回同一用户
        return _FakeResult(self._user)


class _FailingService:
    """写方法抛 ``ValueError`` 命中路由的 400 分支；读方法返回空值。"""

    def create_record(self, data, current_user):
        raise ValueError("contract")

    def get_record(self, record_id):
        return None

    def get_user_records(self, **kwargs):
        return []

    def update_record(self, record_id, data):
        raise ValueError("contract")

    def delete_record(self, record_id, soft=True):
        return True

    def get_user_progress_stats(self, user_id):
        return {}

    def sync_from_enrollment(self, enrollment_id, user_id, learning_source_id):
        raise ValueError("contract")


def _fake_user():
    """轻量用户替身。

    不用 ``models.user.User`` 实例：构造它会触发 ``configure_mappers()``，一旦
    同一 pytest 会话里已导入 ``models.collaborative_editor``（该模型的关系缺外键，
    见 ``test_collaborative_editor_auth_contract.py``），就会抛
    ``NoForeignKeysError``。本模块路由只把 ``current_user`` 透传给 service，
    不读任何属性。
    """
    from types import SimpleNamespace

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
    from routes import unified_learning_record_routes as mod

    app = FastAPI()
    app.include_router(mod.router)
    return app


def _stub_dependencies(app):
    """鉴权链用假 AsyncSession，业务层用假 service，均不触碰真实库。"""
    from routes import unified_learning_record_routes as mod
    from utils.database import get_db, get_sync_session

    app.dependency_overrides[get_db] = lambda: _FakeAsyncSession(_fake_user())
    app.dependency_overrides[get_sync_session] = lambda: MagicMock()
    app.dependency_overrides[mod.get_service] = _FailingService


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
# 401：未携带凭据 / 携带无效凭据
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,body", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_missing_credentials_returns_401(method, path, body):
    """未携带 Authorization → 401（改动前是 500 NotImplementedError）。"""
    async with _running(_build_app()) as client:
        resp = await _call(client, method, path, body)
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


@pytest.mark.parametrize("method,path,body", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_invalid_credentials_returns_401(method, path, body):
    """携带无法解码的 token → 401。"""
    async with _running(_build_app()) as client:
        resp = await _call(client, method, path, body, INVALID_HEADERS)
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# 200 / 业务 4xx：有效凭据下鉴权层放行
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,body", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_valid_credentials_pass_auth(method, path, body):
    """有效 token → 鉴权层放行（200 或业务 400），绝不允许 500。"""
    app = _build_app()
    _stub_dependencies(app)
    async with _running(app) as client:
        resp = await _call(client, method, path, body, _token_headers())
    assert resp.status_code != 401, resp.text
    assert resp.status_code != 500, resp.text
    assert resp.status_code in (200, 400), resp.text


# ---------------------------------------------------------------------------
# 403：租户 / 归属校验尚未实现（xfail 占位）
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="unified_learning_record 的 4 个鉴权端点无 RBAC / 归属校验实现，"
    "user_id 不参与授权判断；普通用户写他人记录当前返回 200/400。"
    "补归属校验后本用例会 XPASS，届时改为正式断言",
)
@pytest.mark.asyncio
async def test_cross_user_access_denied():
    """普通用户写入他人 user_id 的学习记录应 403 —— 当前实现无归属校验。"""
    app = _build_app()
    _stub_dependencies(app)
    body = {"user_id": 999999, "learning_source_id": 1}
    async with _running(app) as client:
        resp = await _call(
            client, "post", "/unified-learning-records", body, _token_headers()
        )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# 回归护栏
# ---------------------------------------------------------------------------
def test_route_module_has_no_sync_auth_stub():
    """回归护栏：本模块不得再出现同步存根依赖。"""
    from pathlib import Path

    from routes import unified_learning_record_routes as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "get_current_user_sync" not in source
    assert source.count("Depends(get_current_user)") == 4
    assert "Depends(get_sync_db)" not in source
    assert source.count("Depends(get_sync_session)") == 1
