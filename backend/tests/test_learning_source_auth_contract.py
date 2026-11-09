"""PR-3c-2c: ``learning_source_routes`` 鉴权契约测试（3 个鉴权端点）。

背景
----
改动前这 3 个端点依赖 ``utils.auth_utils.get_current_user_sync`` —— 该函数体
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

403（已登录但无权限）当前**不可断言**：本模块 3 个鉴权端点都没有 RBAC /
租户隔离实现，``user_id`` 不参与授权判断。对应 ``test_cross_user_access_denied``
以 ``xfail(strict=True)`` 占位，将来补上校验会 XPASS 并提示改为正式断言。

设计说明
--------
* 被测应用是**独立 FastAPI app**，只挂载本模块 router。原因：这 4 个 2c 模块在
  ``core/router_registry.py`` 里都是 ``mode="legacy"`` 条目，默认 lazy 入口
  （``main_ai_edu.app``）不挂载它们，用 conftest 的 ``client`` 只会拿到 404，
  测不到鉴权；
* 401 用例走**真实** ``middleware.auth.get_current_user`` 依赖链：``oauth2_scheme``
  在解析阶段即拒绝，不 override 任何依赖；
* 200 用例 override ``utils.database.get_db``（返回固定用户的假 AsyncSession）与
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
    ("post", "/learning-sources", {"user_id": 1, "source_type": "self_study", "name": "contract"}),
    ("put", "/learning-sources/1", {"name": "contract-updated"}),
    ("delete", "/learning-sources/1", None),
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
    """所有业务方法抛 ``ValueError``，命中路由的 400 分支。"""

    def create_learning_source(self, source_data, current_user):
        raise ValueError("contract")

    def get_learning_source(self, source_id):
        return None

    def get_user_learning_sources(self, **kwargs):
        return []

    def update_learning_source(self, source_id, source_data):
        raise ValueError("contract")

    def delete_learning_source(self, source_id, soft=True):
        return True

    def get_source_stats(self, user_id):
        return {}


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
    from routes import learning_source_routes as mod

    app = FastAPI()
    app.include_router(mod.router)
    return app


def _stub_dependencies(app):
    """鉴权链用假 AsyncSession，业务层用假 service，均不触碰真实库。"""
    from routes import learning_source_routes as mod
    from utils.database import get_db, get_sync_session

    app.dependency_overrides[get_db] = lambda: _FakeAsyncSession(_fake_user())
    app.dependency_overrides[get_sync_session] = lambda: MagicMock()
    app.dependency_overrides[mod.get_learning_source_service] = _FailingService


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
    reason="learning_source 的 3 个鉴权端点无 RBAC / 归属校验实现，"
    "user_id 不参与授权判断；普通用户跨 user 访问当前返回 200/400。"
    "补归属校验后本用例会 XPASS，届时改为正式断言",
)
@pytest.mark.asyncio
async def test_cross_user_access_denied():
    """普通用户操作他人 user_id 的学习来源应 403 —— 当前实现无任何归属校验。"""
    app = _build_app()
    _stub_dependencies(app)
    body = {"user_id": 999999, "source_type": "self_study", "name": "contract"}
    async with _running(app) as client:
        resp = await _call(client, "post", "/learning-sources", body, _token_headers())
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# 回归护栏
# ---------------------------------------------------------------------------
def test_route_module_has_no_sync_auth_stub():
    """回归护栏：本模块不得再出现同步存根依赖。"""
    from pathlib import Path

    from routes import learning_source_routes as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "get_current_user_sync" not in source
    assert source.count("Depends(get_current_user)") == 3
    # DB 依赖必须是 Depends 专用的 get_sync_session
    # （@contextmanager 版 get_sync_db 会被注入 _GeneratorContextManager → 500）
    assert "Depends(get_sync_db)" not in source
    assert source.count("Depends(get_sync_session)") == 1
