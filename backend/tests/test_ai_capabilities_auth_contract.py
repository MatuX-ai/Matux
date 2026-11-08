"""PR-3c-2d: ``ai_capabilities_routes`` 鉴权 + 同步 db 依赖契约测试。

背景
----
改动前这 6 个鉴权端点同时依赖 ``utils.dependencies`` 里的两个**空壳**：

* ``get_current_user_sync()`` —— 函数体直接 ``raise NotImplementedError``；
* ``get_sync_db()`` —— 同样是 ``raise NotImplementedError``。

FastAPI 在依赖解析阶段就会抛错，因此**任何请求（含不带 token）都返回 500**
而不是 401。本 PR 把两条依赖分别换成 ``middleware.auth.get_current_user``
（真 async JWT 依赖）与 ``utils.database.get_sync_session``（真 generator
function，``Depends`` 才能正确 close）。

本文件锁定的契约
----------------
============================= ===========================================
场景                           期望
============================= ===========================================
未携带 ``Authorization``        401
携带无效 token                  401
携带有效 token                  200（本模块全部是 Mock 实现，不落库）
``GET /health``（本无鉴权）     200，且不因本次改造受影响
============================= ===========================================

403（已登录但无权限）当前**不可断言**：本模块 6 个鉴权端点都没有 RBAC /
归属校验实现，``user_id`` 不参与授权判断。对应用例以 ``xfail(strict=True)``
占位。

设计说明
--------
* 被测应用是**独立 FastAPI app**，只挂载本模块 router —— 该模块在
  ``core/router_registry.py`` 里是 ``mode="legacy"`` 条目，默认 lazy 入口不挂载；
* 401 用例走**真实** ``middleware.auth.get_current_user`` 依赖链，不 override；
* 200 用例 override ``utils.database.get_db``（固定用户的假 AsyncSession）与
  ``get_sync_session``（``MagicMock``），不触碰真实库。
"""

from contextlib import asynccontextmanager
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
import httpx
import pytest

PREFIX = "/api/v1/ai-capabilities"
INVALID_HEADERS = {"Authorization": "Bearer not-a-valid-jwt"}

# (方法, 相对路径, JSON body)
ENDPOINTS = [
    (
        "post",
        "/vision/analyze",
        {"image_url": "https://example.com/a.jpg", "task_type": "object_detection"},
    ),
    ("post", "/nlp/chat", {"message": "hello"}),
    (
        "post",
        "/ml/predict",
        {"data": {"features": [0.1, 0.2]}, "task_type": "classification"},
    ),
    ("get", "/models/list", None),
    ("get", "/monitoring/dashboard", None),
    ("post", "/monitoring/reset", None),
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


def _fake_user():
    """轻量用户替身，避免构造 ``models.user.User`` 触发 mapper 配置。"""
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
    from routes import ai_capabilities_routes as mod

    app = FastAPI()
    app.include_router(mod.router)
    return app


def _stub_dependencies(app):
    from utils.database import get_db, get_sync_session

    app.dependency_overrides[get_db] = lambda: _FakeAsyncSession(_fake_user())
    app.dependency_overrides[get_sync_session] = lambda: MagicMock()


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


@pytest.mark.parametrize("method,path,body", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_invalid_credentials_returns_401(method, path, body):
    """携带无法解码的 token → 401。"""
    async with _running(_build_app()) as client:
        resp = await _call(client, method, path, body, INVALID_HEADERS)
    assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# 200：有效凭据下鉴权层放行，且业务体可执行
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,body", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_valid_credentials_returns_200(method, path, body):
    """有效 token → 200；任何 5xx 都说明存根/依赖没真正修好。"""
    app = _build_app()
    _stub_dependencies(app)
    async with _running(app) as client:
        resp = await _call(client, method, path, body, _token_headers())
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_health_endpoint_has_no_auth_and_still_works():
    """``GET /health`` 本来就没有鉴权依赖，改造后必须仍然 200。"""
    async with _running(_build_app()) as client:
        resp = await client.get(PREFIX + "/health")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "healthy"


# ---------------------------------------------------------------------------
# 403：租户 / 归属校验尚未实现（xfail 占位）
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="ai_capabilities 的 6 个鉴权端点无 RBAC / 归属校验实现，"
    "user_id 不参与授权判断；普通用户可读他人监控数据当前返回 200。"
    "补归属校验后本用例会 XPASS，届时改为正式断言",
)
@pytest.mark.asyncio
async def test_cross_user_access_denied():
    """普通用户读取全局监控仪表板应 403 —— 当前实现无归属校验。"""
    app = _build_app()
    _stub_dependencies(app)
    async with _running(app) as client:
        resp = await _call(
            client, "get", "/monitoring/dashboard", None, _token_headers()
        )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# 回归护栏
# ---------------------------------------------------------------------------
def test_route_module_has_no_sync_auth_stub():
    """回归护栏：本模块不得再出现同步存根依赖。"""
    from pathlib import Path

    from routes import ai_capabilities_routes as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "get_current_user_sync" not in source
    assert "from utils.dependencies" not in source
    assert source.count("Depends(get_current_user)") == 6
    assert "Depends(get_sync_db)" not in source
    assert source.count("Depends(get_sync_session)") == 6
