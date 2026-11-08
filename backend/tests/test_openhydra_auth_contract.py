"""PR-3c-2d: ``openhydra_routes`` 鉴权 + 同步 db 依赖契约测试。

背景
----
改动前本模块 4 个端点依赖 ``utils.dependencies.get_current_user_sync``
（空壳，直接 ``raise NotImplementedError``），其中 ``POST /enter`` 还依赖
同样空壳的 ``utils.dependencies.get_sync_db``。两者都让任何请求变成 500，
本 PR 一并换成 ``middleware.auth.get_current_user`` +
``utils.database.get_sync_session``。

本文件锁定的契约
----------------
=============================== =========================================
场景                             期望
=============================== =========================================
未携带 ``Authorization``          401
携带无效 token                    401
携带有效 token                    200
``GET /health``（本无鉴权）       200，只需要 override OpenHydra 服务
=============================== =========================================

403 说明
--------
本模块 4 个鉴权端点都没有租户校验：``org_id`` 只用于路径与日志，不参与鉴权。
跨 org 访问当前返回 200，对应用例以 ``xfail(strict=True)`` 占位。

设计说明
--------
* 独立 FastAPI app，只挂载本模块 router；
* ``get_openhydra_service`` 返回**模块级单例**（``OpenHydraService``），
  不 override 会真连外部服务，因此 200 用例统一走
  ``app.dependency_overrides[get_openhydra_service]``；
* 401 用例不需要 override —— 服务对象只在依赖解析后、路由体内才被调用。
"""

from contextlib import asynccontextmanager
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
import httpx
import pytest

PREFIX = "/api/v1/org/1/ai-lab"
INVALID_HEADERS = {"Authorization": "Bearer not-a-valid-jwt"}

# (方法, 相对路径, JSON body)
ENDPOINTS = [
    ("post", "/enter", None),
    ("get", "/container/status", None),
    ("post", "/container/stop", None),
    ("post", "/container/extend", None),
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


class _FakeOpenHydraService:
    """覆盖路由用到的 6 个协程，全部为内存实现。"""

    async def get_container(self, user_id):
        return SimpleNamespace(
            container_id="c_contract",
            status="running",
            jupyter_url="http://jupyter.local/c_contract",
        )

    async def create_container(self, config):
        return SimpleNamespace(
            container_id="c_contract",
            jupyter_url="http://jupyter.local/c_contract",
        )

    async def generate_access_token(self, user_id):
        return "contract-token"

    async def get_container_status(self, container_id):
        return {"jupyter_accessible": True, "resource_usage": {"cpu": "10%"}}

    async def stop_container(self, container_id):
        return {"success": True}

    async def extend_container_expiry(self, container_id, additional_hours=0):
        return {"new_expiry": "2026-11-09T00:00:00"}

    async def health_check(self):
        return {"status": "healthy", "service": "openhydra"}


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
    from routes import openhydra_routes as mod

    app = FastAPI()
    app.include_router(mod.router)
    return app


def _stub_dependencies(app):
    from routes import openhydra_routes as mod
    from utils.database import get_db, get_sync_session

    app.dependency_overrides[get_db] = lambda: _FakeAsyncSession(_fake_user())
    app.dependency_overrides[get_sync_session] = lambda: MagicMock()
    app.dependency_overrides[mod.get_openhydra_service] = _FakeOpenHydraService


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


@pytest.mark.asyncio
async def test_health_endpoint_has_no_auth_and_still_works():
    """``GET /health`` 本来就没有鉴权依赖，改造后必须仍然 200。"""
    app = _build_app()
    _stub_dependencies(app)
    async with _running(app) as client:
        resp = await client.get(PREFIX + "/health")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "healthy"


# ---------------------------------------------------------------------------
# 403：租户校验尚未实现（xfail 占位）
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="openhydra 的 org_id 只出现在路径与日志里，不参与鉴权；"
    "跨 org 调用 /enter 当前返回 200。补租户校验后本用例会 XPASS",
)
@pytest.mark.asyncio
async def test_cross_tenant_access_denied():
    """访问他人 org 的 AI 实验室应 403 —— 当前实现无租户校验。"""
    app = _build_app()
    _stub_dependencies(app)
    async with _running(app) as client:
        resp = await client.post(
            "/api/v1/org/999999/ai-lab/enter", headers=_token_headers()
        )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# 回归护栏
# ---------------------------------------------------------------------------
def test_route_module_has_no_sync_auth_stub():
    """回归护栏：本模块不得再出现同步存根依赖。"""
    from pathlib import Path

    from routes import openhydra_routes as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "get_current_user_sync" not in source
    assert "from utils.dependencies" not in source
    assert source.count("Depends(get_current_user)") == 4
    assert "Depends(get_sync_db)" not in source
    assert source.count("Depends(get_sync_session)") == 1
