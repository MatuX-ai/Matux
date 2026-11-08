"""PR-3c-2d: ``ar_lab_routes`` 鉴权 + 同步 db 依赖契约测试。

背景
----
改动前本模块有 5 个端点依赖 ``utils.dependencies.get_current_user_sync``
（空壳，直接 ``raise NotImplementedError``），其中 4 个同时依赖
``utils.database.get_sync_db`` —— 而后者是 ``@contextmanager``，**不能**
直接交给 ``Depends``：FastAPI 会把 ``_GeneratorContextManager`` 当作会话注入。
两类坏法都表现为「任何请求都 500」，本 PR 一并换成
``middleware.auth.get_current_user`` + ``utils.database.get_sync_session``。

本文件锁定的契约
----------------
=============================== =========================================
场景                             期望
=============================== =========================================
未携带 ``Authorization``          401
携带无效 token                    401
携带有效 token                    200（本模块全部是内存 Mock，不落库）
5 个**本无鉴权**的读端点          仍然 200（缺口用 xfail 记录，不在本 PR 修）
=============================== =========================================

403 说明
--------
本模块 4 个鉴权端点都没有租户校验：``org_id`` 由
``Depends(lambda: 1)`` 占位（既有缺陷），路径里的 ``{org_id}`` 不参与鉴权。
因此跨租户访问当前返回 200，对应 ``xfail(strict=True)`` 占位。

设计说明
--------
* 独立 FastAPI app，只挂载本模块 router；
* 401 走真实 ``middleware.auth.get_current_user`` 依赖链；
* 200 override ``utils.database.get_db`` + ``get_sync_session``。
"""

from contextlib import asynccontextmanager
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
import httpx
import pytest

PREFIX = "/api/v1/org/1/ar-lab"
INVALID_HEADERS = {"Authorization": "Bearer not-a-valid-jwt"}

# 5 个带鉴权的端点：(方法, 相对路径, JSON body)
ENDPOINTS = [
    ("post", "/hardware/connect", {"port": "COM3"}),
    ("post", "/hardware/disconnect", None),
    ("post", "/experiments/start", {"name": "contract"}),
    ("post", "/experiments/stop", None),
    ("post", "/unity/builds/upload", None),
]

# 5 个**无鉴权**的读端点（既有缺口，本 PR 不扩大鉴权面）
OPEN_ENDPOINTS = [
    ("get", "/hardware/ports"),
    ("get", "/sensor-data/latest"),
    ("get", "/sensor-data/history"),
    ("get", "/experiments/history"),
    ("get", "/unity/builds"),
]

_ENDPOINT_IDS = [f"{m.upper()} {p}" for m, p, _b in ENDPOINTS]
_OPEN_IDS = [f"{m.upper()} {p}" for m, p in OPEN_ENDPOINTS]


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
    from routes import ar_lab_routes as mod

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
async def test_valid_credentials_returns_200(method, path, body):
    """有效 token → 200；任何 5xx 都说明存根/依赖没真正修好。"""
    app = _build_app()
    _stub_dependencies(app)
    async with _running(app) as client:
        resp = await _call(client, method, path, body, _token_headers())
    assert resp.status_code == 200, resp.text


@pytest.mark.parametrize("method,path", OPEN_ENDPOINTS, ids=_OPEN_IDS)
@pytest.mark.asyncio
async def test_open_endpoints_still_work(method, path):
    """5 个无鉴权读端点保持原样 200（本 PR 不扩大鉴权面）。"""
    async with _running(_build_app()) as client:
        resp = await client.get(PREFIX + path)
    assert resp.status_code == 200, resp.text


@pytest.mark.xfail(
    strict=True,
    reason="ar_lab 的 5 个读端点完全没有鉴权依赖，任意匿名请求可读取他人"
    "实验历史 / 传感器数据 / Unity 构建列表。补鉴权后本用例会 XPASS，"
    "届时改为正式 401 断言（登记在 Issue #32 的后续批次）",
)
@pytest.mark.parametrize("method,path", OPEN_ENDPOINTS, ids=_OPEN_IDS)
@pytest.mark.asyncio
async def test_open_endpoints_should_require_auth(method, path):
    """匿名访问应当 401 —— 当前实现无任何鉴权依赖。"""
    async with _running(_build_app()) as client:
        resp = await client.get(PREFIX + path)
    assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# 403：租户校验尚未实现（xfail 占位）
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="ar_lab 的 org_id 由 Depends(lambda: 1) 占位，路径 {org_id} 不参与鉴权；"
    "跨 org 访问硬件连接当前返回 200。补租户校验后本用例会 XPASS",
)
@pytest.mark.asyncio
async def test_cross_tenant_access_denied():
    """访问他人 org 的 ar-lab 应 403 —— 当前实现无租户校验。"""
    app = _build_app()
    _stub_dependencies(app)
    async with _running(app) as client:
        resp = await client.post(
            "/api/v1/org/999999/ar-lab/hardware/connect",
            json={"port": "COM3"},
            headers=_token_headers(),
        )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# 回归护栏
# ---------------------------------------------------------------------------
def test_route_module_has_no_sync_auth_stub():
    """回归护栏：本模块不得再出现同步存根依赖。"""
    from pathlib import Path

    from routes import ar_lab_routes as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "get_current_user_sync" not in source
    assert "from utils.dependencies" not in source
    assert source.count("Depends(get_current_user)") == 5
    assert "Depends(get_sync_db)" not in source
    assert source.count("Depends(get_sync_session)") == 4
