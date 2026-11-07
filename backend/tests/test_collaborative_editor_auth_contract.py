"""PR-3c-2c: ``collaborative_editor_routes`` 鉴权契约测试（13 个 HTTP 端点
+ ``tenant_middleware.require_tenant_access`` 这 1 处跨文件依赖）。

背景
----
改动前这 14 处依赖 ``utils.auth_utils.get_current_user_sync`` —— 该函数体直接
``raise NotImplementedError``，FastAPI 在依赖解析阶段抛出，因此**任何请求
（含不带 token）都返回 500**，而非 401。

本文件锁定的契约：

============================= ===========================================
场景                           期望
============================= ===========================================
未携带 ``Authorization``        401
携带无效 token                  401
有效 token + 普通用户           403（仅 ``except HTTPException: raise`` 的端点能透传）
有效 token + 管理员             鉴权层放行（200 / 业务 400 / 404），**不得 500**
============================= ===========================================

与本批次其他 3 个模块不同：本模块**已有**租户校验实现
（``middleware/tenant_middleware.py::require_tenant_access``，非管理员一律
``raise HTTPException(403)``）。13 个 HTTP 端点分三类：

* **2 个透传**（``get_document`` / ``resolve_comment``）：写了
  ``except HTTPException: raise``，403 原样返回 → 正式断言；
* **9 个吞掉**：用 ``except Exception`` 把 403 当普通异常捕获、重包装成 500
  （``detail`` 仍带「无权访问此租户资源」）。这是路由层错误处理的既有缺陷，
  本 PR 不修，用 ``test_tenant_denial_swallowed_by_route_error_handling`` 锁定
  其表现，并用 ``xfail(strict=True)`` 标记「将来补上透传后应改为 403」；
* **2 个无租户校验**（``update_cursor_position`` / ``leave_session``）：只校验
  登录态、直接调 service，普通用户得到业务 400 而非 403 → ``xfail(strict=True)``
  占位「目标契约应为 403」。

``require_tenant_access`` 在路由里是**直接调用**（``validate_course_access``
内部位置传参），不是 ``Depends``，所以它的 ``Depends(...)`` 默认值不会被执行；
本文件用源码护栏锁定它已同步换掉存根，避免将来改成 ``Depends`` 后再次 500。

设计说明
--------
* 被测应用是**独立 FastAPI app**，只挂载本模块 router：本模块在
  ``core/router_registry.py`` 里是 ``mode="legacy"`` 条目，默认 lazy 入口
  （``main_ai_edu.app``）不挂载它，用 conftest 的 ``client`` 只会得到 404；
* 401 用例走**真实** ``middleware.auth.get_current_user`` 依赖链，不 override；
* 200 用例 override ``utils.database.get_db``（固定管理员的假 AsyncSession）与
  ``get_sync_session``（``MagicMock`` 且 ``query().filter().first()`` 返回 ``None``），
  并让 editor service 抛 ``ValueError`` 落到 400 分支 —— 不触碰真实库。

模型层缺陷（本 PR 一并修复，否则无法同会话共存）
----------------------------------------------------
``models/collaborative_editor.py`` 与 ``models/collaboration.py`` 各自定义了同名
mapped class ``CollaborativeDocument`` / ``DocumentComment``，两边都用**裸类名字符串**
写 relationship。只要两个模块在同一进程里被导入，SQLAlchemy 的 class registry 就有
2 个同名候选 → ``configure_mappers()`` 抛 ``InvalidRequestError: Multiple classes
found for path "CollaborativeDocument"``，**整个注册表一起不可用**，连带同一 pytest
会话里所有构造 ``User`` 的测试报 error。

本 PR 修掉的 3 类映射缺陷（详见 PR 描述）：

1. 4 处 ``document_id`` 外键写成 ``collaborative_documents.id``（``models/collaboration.py``
   的表），而关系目标是本模块的 ``collaborative_editor_documents`` → ``NoForeignKeysError``；
2. ``parent_comment_id`` 外键写成 ``document_comments.id``（同样是别的表）→ 改为
   ``collaborative_editor_document_comments.id``；
3. 两个模型模块共 11 处 relationship 用裸类名字符串 → 加模块限定路径
   （``models.collaboration.CollaborativeDocument`` 等），彻底消除同名歧义。

本模块的 5 张表没有任何 alembic 迁移文件（DDL 完全由 ORM 定义驱动），
因此上述外键修正不需要额外的建表变更。

本文件仍用 ``SimpleNamespace`` 充当 ``current_user``（只带 ``id`` /
``email`` / ``role`` / ``is_superuser``），把契约测试聚焦在**鉴权与租户校验**本身。
"""

from contextlib import asynccontextmanager
from datetime import timedelta
from unittest.mock import MagicMock

from fastapi import FastAPI
import httpx
import pytest

PREFIX = "/api/v1/org/1/courses/1/collaborative-documents"
INVALID_HEADERS = {"Authorization": "Bearer not-a-valid-jwt"}

# (方法, 相对路径, JSON body, 普通用户的租户校验表现)
# "pass"    = 路由写了 ``except HTTPException: raise``，403 原样透传
# "swallow" = 路由用 ``except Exception`` 把 403 重包装成 500
# "none"    = 端点完全没有租户校验，直接进业务层
ENDPOINTS = [
    ("post", "/", {"document_name": "contract"}, "swallow"),
    ("get", "/1", None, "pass"),
    ("put", "/1/content", {"content": "contract"}, "swallow"),
    (
        "post",
        "/1/operations/batch",
        [{"operation_type": "insert", "position": 0, "client_id": "c", "revision": 0}],
        "swallow",
    ),
    ("get", "/1/operations", None, "swallow"),
    (
        "post",
        "/1/comments",
        {"start_position": 0, "end_position": 1, "content": "contract"},
        "swallow",
    ),
    ("get", "/1/comments", None, "swallow"),
    ("put", "/1/comments/1/resolve", None, "pass"),
    (
        "post",
        "/1/suggestions",
        {"start_position": 0, "end_position": 1, "suggested_content": "contract"},
        "swallow",
    ),
    ("put", "/1/suggestions/1/review", {"status": "accepted"}, "swallow"),
    ("post", "/1/sessions", {"client_id": "contract-client"}, "swallow"),
    ("put", "/sessions/contract-session/cursor", {"cursor_position": 0}, "none"),
    ("delete", "/sessions/contract-session", None, "none"),
]

# (方法, 路径, body) —— 401/200 用例共用
CALLS = [e[:3] for e in ENDPOINTS]
PASSTHROUGH_403 = [e[:3] for e in ENDPOINTS if e[3] == "pass"]
SWALLOWED_403 = [e[:3] for e in ENDPOINTS if e[3] == "swallow"]
NO_TENANT_GUARD = [e[:3] for e in ENDPOINTS if e[3] == "none"]

_ENDPOINT_IDS = [f"{m.upper()} {p}" for m, p, _b, _g in ENDPOINTS]
_PASSTHROUGH_IDS = [f"{m.upper()} {p}" for m, p, _b in PASSTHROUGH_403]
_SWALLOWED_IDS = [f"{m.upper()} {p}" for m, p, _b in SWALLOWED_403]
_NO_GUARD_IDS = [f"{m.upper()} {p}" for m, p, _b in NO_TENANT_GUARD]


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


class _FailingEditorService:
    """写方法抛 ``ValueError``（→ 400）；读方法返回空值（→ 200/404）。"""

    def create_document(self, course_id, org_id, doc_data, current_user):
        raise ValueError("contract")

    def get_document(self, document_id, org_id):
        return None

    def update_document_content(self, document_id, org_id, content, current_user):
        raise ValueError("contract")

    def apply_operations(self, document_id, org_id, operations, current_user):
        raise ValueError("contract")

    def get_document_operations(self, document_id, from_revision=0):
        return []

    def create_comment(self, document_id, org_id, comment_data, current_user):
        raise ValueError("contract")

    def get_document_comments(self, document_id):
        return []

    def create_suggestion(self, document_id, org_id, suggestion_data, current_user):
        raise ValueError("contract")

    def review_suggestion(self, suggestion_id, org_id, status, current_user):
        raise ValueError("contract")

    def create_session(self, document_id, org_id, client_id, current_user):
        raise ValueError("contract")

    def update_session_cursor(self, session_id, cursor_position, start, end):
        raise ValueError("contract")

    def end_session(self, session_id):
        raise ValueError("contract")


def _fake_user(is_superuser: bool):
    """轻量用户替身。

    不用 ``models.user.User`` 实例：构造它会触发 ``configure_mappers()``，进而
    撞上本模块 ``models.collaborative_editor`` 的既有外键缺陷（见模块 docstring）。
    鉴权契约只依赖 ``id`` / ``email`` / ``role`` / ``is_superuser`` 四项。
    """
    from types import SimpleNamespace

    from models.user import UserRole

    if is_superuser:
        return SimpleNamespace(
            id=2,
            username="contract_admin",
            email="contract_admin@example.com",
            name="contract_admin",
            role=UserRole.ADMIN,
            is_superuser=True,
            is_active=True,
        )
    return SimpleNamespace(
        id=1,
        username="contract_user",
        email="contract@example.com",
        name="contract_user",
        role=UserRole.USER,
        is_superuser=False,
        is_active=True,
    )


def _token_headers():
    from routes.auth_routes import create_access_token

    token = create_access_token(
        {"sub": "contract_user"}, expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {token}"}


def _build_app():
    from routes import collaborative_editor_routes as mod

    app = FastAPI()
    app.include_router(mod.router)
    return app


def _stub_dependencies(app, is_superuser: bool = True):
    """鉴权链用假 AsyncSession，业务层与 DB 用假对象，均不触碰真实库。"""
    from routes import collaborative_editor_routes as mod
    from utils.database import get_db, get_sync_session

    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: _FakeAsyncSession(
        _fake_user(is_superuser)
    )
    app.dependency_overrides[get_sync_session] = lambda: fake_db
    app.dependency_overrides[mod.get_collaborative_editor_service] = (
        _FailingEditorService
    )


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
@pytest.mark.parametrize("method,path,body", CALLS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_missing_credentials_returns_401(method, path, body):
    """未携带 Authorization → 401（改动前是 500 NotImplementedError）。"""
    async with _running(_build_app()) as client:
        resp = await _call(client, method, path, body)
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


@pytest.mark.parametrize("method,path,body", CALLS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_invalid_credentials_returns_401(method, path, body):
    """携带无法解码的 token → 401。"""
    async with _running(_build_app()) as client:
        resp = await _call(client, method, path, body, INVALID_HEADERS)
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# 403：普通用户被 require_tenant_access 拒绝
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,body", PASSTHROUGH_403, ids=_PASSTHROUGH_IDS)
@pytest.mark.asyncio
async def test_normal_user_denied_with_403_passthrough(method, path, body):
    """写了 ``except HTTPException: raise`` 的端点 → 403 原样透传。"""
    app = _build_app()
    _stub_dependencies(app, is_superuser=False)
    async with _running(app) as client:
        resp = await _call(client, method, path, body, _token_headers())
    assert resp.status_code == 403, resp.text
    assert resp.status_code != 500


@pytest.mark.parametrize(
    "method,path,body", SWALLOWED_403, ids=_SWALLOWED_IDS
)
@pytest.mark.asyncio
async def test_tenant_denial_swallowed_by_route_error_handling(method, path, body):
    """其余端点把 403 当普通异常捕获，重包装成 500 —— 锁定既有缺陷表现。

    断言 detail 仍带「无权访问此租户资源」，证明 403 确实被 raise 过、只是被
    路由的 ``except Exception`` 吞掉并重包装。这是**既有缺陷**，本 PR 不修；
    将来补上 ``except HTTPException: raise`` 后，下面的 xfail 会 XPASS 提醒改断言。
    """
    app = _build_app()
    _stub_dependencies(app, is_superuser=False)
    async with _running(app) as client:
        resp = await _call(client, method, path, body, _token_headers())
    assert resp.status_code == 500, resp.text
    assert "无权访问此租户资源" in resp.text, resp.text


@pytest.mark.xfail(
    strict=True,
    reason="11 个端点用 except Exception 把 403 重包装成 500，未写 "
    "except HTTPException: raise；待路由层补透传后本用例会 XPASS，"
    "届时改为正式 403 断言",
)
@pytest.mark.parametrize(
    "method,path,body", SWALLOWED_403, ids=_SWALLOWED_IDS
)
@pytest.mark.asyncio
async def test_swallowed_endpoints_should_be_403(method, path, body):
    """目标契约：普通用户访问这些端点应得到 403，而非 500（当前不满足）。"""
    app = _build_app()
    _stub_dependencies(app, is_superuser=False)
    async with _running(app) as client:
        resp = await _call(client, method, path, body, _token_headers())
    assert resp.status_code == 403, resp.text


@pytest.mark.parametrize("method,path,body", NO_TENANT_GUARD, ids=_NO_GUARD_IDS)
@pytest.mark.asyncio
async def test_no_tenant_guard_falls_through_to_business(method, path, body):
    """2 个会话端点没有租户校验：普通用户直接进业务层（400），不报 403/500。"""
    app = _build_app()
    _stub_dependencies(app, is_superuser=False)
    async with _running(app) as client:
        resp = await _call(client, method, path, body, _token_headers())
    assert resp.status_code != 401, resp.text
    assert resp.status_code != 500, resp.text
    assert resp.status_code == 400, resp.text


@pytest.mark.xfail(
    strict=True,
    reason="update_cursor_position / leave_session 没有 validate_course_access，"
    "普通用户直接进业务层（当前 400）；补租户校验后本用例会 XPASS，"
    "届时改为正式 403 断言",
)
@pytest.mark.parametrize("method,path,body", NO_TENANT_GUARD, ids=_NO_GUARD_IDS)
@pytest.mark.asyncio
async def test_no_tenant_guard_endpoints_should_be_403(method, path, body):
    """目标契约：普通用户访问会话端点应得到 403（当前无租户校验）。"""
    app = _build_app()
    _stub_dependencies(app, is_superuser=False)
    async with _running(app) as client:
        resp = await _call(client, method, path, body, _token_headers())
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# 200 / 业务 4xx：管理员通过租户校验，鉴权层放行
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,body", CALLS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_admin_credentials_pass_auth(method, path, body):
    """有效 token 的管理员 → 鉴权与租户校验均放行，绝不允许 500。"""
    app = _build_app()
    _stub_dependencies(app, is_superuser=True)
    async with _running(app) as client:
        resp = await _call(client, method, path, body, _token_headers())
    assert resp.status_code != 401, resp.text
    assert resp.status_code != 403, resp.text
    assert resp.status_code != 500, resp.text
    assert resp.status_code in (200, 400, 404), resp.text


# ---------------------------------------------------------------------------
# 回归护栏
# ---------------------------------------------------------------------------
def test_route_module_has_no_sync_auth_stub():
    """回归护栏：路由模块不得再出现同步存根依赖。"""
    from pathlib import Path

    from routes import collaborative_editor_routes as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "get_current_user_sync" not in source
    assert source.count("Depends(get_current_user)") == 14
    assert "Depends(get_sync_db)" not in source
    assert source.count("Depends(get_sync_session)") == 14


def test_tenant_middleware_require_tenant_access_has_no_stub():
    """回归护栏：``require_tenant_access`` 的默认依赖不得再是同步存根。

    该函数当前被路由**直接调用**（位置传参），默认值不执行；一旦有人改成
    ``Depends(require_tenant_access)``，默认值就会生效 —— 必须保证它不是存根。
    """
    from pathlib import Path

    from middleware import tenant_middleware as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "get_current_user_sync" not in source
    assert source.count("Depends(get_current_user)") == 1
    assert source.count("Depends(get_sync_session)") == 1
