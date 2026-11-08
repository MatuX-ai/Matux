"""PR-3c-2c: ``multimedia_routes`` 鉴权契约测试（15 个鉴权端点）。

背景
----
改动前这 15 处依赖 ``utils.dependencies.get_current_user_sync`` —— 该函数体直接
``raise NotImplementedError``，FastAPI 在依赖解析阶段抛出，因此**任何请求
（含不带 token）都返回 500**，而非 401。同时 ``get_sync_db`` 是
``@contextmanager``，用作 ``Depends`` 会注入 ``_GeneratorContextManager``。

本文件锁定的契约：

============================= ===========================================
场景                           期望
============================= ===========================================
未携带 ``Authorization``        401（15 个端点全部，含被路径遮蔽的端点）
携带无效 token                  401
携带有效 token + 管理员         鉴权层放行：200 / 业务 400 / 404，**不得 500**
============================= ===========================================

401 优先于路径参数 / body 校验：实测被 ``GET /{resource_id}`` 遮蔽的
``GET /statistics``、``GET /search`` 在无 token 时仍是 401，带合法 token 才
落到 422（``path.resource_id`` 解析失败）。

既有缺陷（本 PR 不修，仅记录）
------------------------------
1. **路由顺序遮蔽**：``GET /{resource_id}`` 注册在 ``GET /statistics``、
   ``GET /search`` 之前，后者永远不可达，带合法 token 时返回 422。
   用 ``test_shadowed_endpoints_return_422`` 锁定现状，
   ``test_shadowed_endpoints_should_be_reachable`` 以 ``xfail(strict=True)``
   标记「调整注册顺序后应改为非 422」。
2. ``POST /upload`` 用 ``except Exception -> 500`` 包裹整个上传流程，
   任何业务异常都变成 500（``detail`` 带「上传失败: ...」）。本文件用一个
   能走通的成功替身验证鉴权放行，不触碰真实存储。

设计说明
--------
* 被测应用是**独立 FastAPI app**，只挂载本模块 router：本模块在
  ``core/router_registry.py`` 里是 ``mode="legacy"`` 条目，默认 lazy 入口
  （``main_ai_edu.app``）不挂载它，用 conftest 的 ``client`` 只会得到 404；
* 401 用例走**真实** ``middleware.auth.get_current_user`` 依赖链，不 override；
* 200 用例 override ``utils.database.get_db``（固定管理员的假 AsyncSession）、
  ``get_sync_session``（``MagicMock``）与三个 service 工厂，让业务方法抛
  ``ValueError`` 落到路由的 400 分支，或返回空值落到 404 分支 —— 不触碰真实库。
"""

from contextlib import asynccontextmanager
from datetime import timedelta
import tempfile
from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import FastAPI
import httpx
import pytest

PREFIX = "/api/v1/org/1/multimedia"
INVALID_HEADERS = {"Authorization": "Bearer not-a-valid-jwt"}

_CREATE_FORM = {
    "course_id": "1",
    "title": "contract",
    "media_type": "video",
    "file_name": "contract.mp4",
}
_COMPLETE_FORM = {"file_size": "1", "mime_type": "video/mp4"}
_UPLOAD_FORM = {"course_id": "1", "title": "contract", "media_type": "video"}

# (方法, 相对路径, 请求 kwargs, 管理员期望状态码集合)
# 遮蔽端点（/statistics、/search）与 /upload 单独测试，不在此表。
ENDPOINTS = [
    ("post", "/", {"data": _CREATE_FORM}, (400,)),
    ("get", "/", None, (200,)),
    ("get", "/1", None, (404,)),
    ("put", "/1", {"json": {"title": "contract"}}, (404,)),
    ("delete", "/1", None, (400,)),
    ("post", "/1/upload-url", None, (400,)),
    ("post", "/1/complete-upload", {"data": _COMPLETE_FORM}, (400,)),
    ("post", "/1/transcode", {"json": {"resource_id": 1}}, (400,)),
    ("get", "/transcoding-jobs/j1", None, (404,)),
    ("post", "/1/process-3d", None, (400,)),
    ("get", "/1/preview-3d", None, (400,)),
    ("post", "/1/process-document", {"json": {"resource_id": 1}}, (400,)),
]

# 被 GET /{resource_id} 遮蔽的两个读端点
SHADOWED = [
    ("get", "/statistics", None),
    ("get", "/search", {"params": {"query": "contract"}}),
]

ALL_CALLS = [(m, p) for m, p, *__ in ENDPOINTS] + [(m, p) for m, p, _k in SHADOWED]
ALL_IDS = [f"{m.upper()} {p}" for m, p in ALL_CALLS]
_ENDPOINT_IDS = [f"{m.upper()} {p}" for m, p, _k, _s in ENDPOINTS]
_SHADOWED_IDS = [f"{m.upper()} {p}" for m, p, _k in SHADOWED]


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


class _ValueErrorService:
    """业务方法一律抛 ``ValueError``（路由 400）；``db`` 查询返回空（路由 404）。"""

    def __init__(self):
        self.db = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = None
        self.db.query.return_value.filter.return_value.all.return_value = []
        self.db.query.return_value.filter.return_value.count.return_value = 0

    def __getattr__(self, name):
        def _boom(*args, **kwargs):
            raise ValueError("contract")

        return _boom


class _UploadSuccessService:
    """供 ``POST /upload`` 走通的成功替身：只落地到临时目录。"""

    def __init__(self):
        self.db = MagicMock()
        self.storage_config = SimpleNamespace(
            storage_type="local",
            local_storage_path=tempfile.mkdtemp(prefix="pr3c2c-mm-"),
        )
        self.created = []

    def create_multimedia_resource(self, org_id, resource_data, current_user):
        from datetime import datetime

        from models.multimedia import MediaType

        # 字段集必须覆盖 MultimediaResourceResponse 的全部必填项，否则
        # FastAPI 序列化阶段抛 ResponseValidationError（→ 500）。
        resource = SimpleNamespace(
            id=101,
            org_id=org_id,
            course_id=1,
            lesson_id=None,
            title="contract",
            description=None,
            media_type=MediaType.VIDEO,
            file_name="contract.mp4",
            file_size=None,
            mime_type="video/mp4",
            original_url=None,
            processed_url=None,
            thumbnail_url=None,
            duration_seconds=None,
            video_status=None,
            document_format=None,
            page_count=None,
            is_active=True,
            is_public=False,
            access_level="course",
            view_count=0,
            download_count=0,
            like_count=0,
            is_ready=False,
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 1),
        )
        self.created.append(resource)
        return resource


def _fake_user():
    """轻量管理员替身。

    不用 ``models.user.User`` 实例：构造它会触发 ``configure_mappers()``，
    一旦同一 pytest 会话里已导入 ``models.collaborative_editor``（该模型的关系
    缺外键），就会抛 ``NoForeignKeysError``。
    """
    from models.user import UserRole

    return SimpleNamespace(
        id=2,
        username="contract_admin",
        email="contract_admin@example.com",
        name="contract_admin",
        role=UserRole.ADMIN,
        is_superuser=True,
        is_active=True,
    )


def _token_headers():
    from routes.auth_routes import create_access_token

    token = create_access_token(
        {"sub": "contract_admin"}, expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {token}"}


def _build_app():
    from routes import multimedia_routes as mod

    app = FastAPI()
    app.include_router(mod.router)
    return app


def _stub_dependencies(app, service_factory):
    from routes import multimedia_routes as mod
    from utils.database import get_db, get_sync_session

    service = service_factory()
    app.dependency_overrides[get_db] = lambda: _FakeAsyncSession(_fake_user())
    app.dependency_overrides[get_sync_session] = lambda: service.db
    app.dependency_overrides[mod.get_multimedia_service] = lambda: service
    app.dependency_overrides[mod.get_3d_service] = lambda: service
    app.dependency_overrides[mod.get_document_service] = lambda: service
    return service


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


async def _call(client, method, path, req_kwargs=None, headers=None):
    kwargs = dict(req_kwargs) if req_kwargs else {}
    if headers:
        kwargs["headers"] = headers
    return await getattr(client, method)(PREFIX + path, **kwargs)


# ---------------------------------------------------------------------------
# 401：未携带凭据 / 携带无效凭据（15 个端点，含被遮蔽的 2 个）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path", ALL_CALLS, ids=ALL_IDS)
@pytest.mark.asyncio
async def test_missing_credentials_returns_401(method, path):
    """未携带 Authorization → 401（改动前是 500 NotImplementedError）。"""
    async with _running(_build_app()) as client:
        resp = await _call(client, method, path)
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


@pytest.mark.parametrize("method,path", ALL_CALLS, ids=ALL_IDS)
@pytest.mark.asyncio
async def test_invalid_credentials_returns_401(method, path):
    """携带无法解码的 token → 401（401 优先于 body / 路径参数校验）。"""
    async with _running(_build_app()) as client:
        resp = await _call(client, method, path, None, INVALID_HEADERS)
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# 200 / 业务 4xx：管理员通过鉴权，进入路由体
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,req_kwargs,expected", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_admin_credentials_pass_auth(method, path, req_kwargs, expected):
    """有效 token 的管理员 → 鉴权层放行，落到预期的业务状态码，绝不允许 500。"""
    app = _build_app()
    _stub_dependencies(app, _ValueErrorService)
    async with _running(app) as client:
        resp = await _call(client, method, path, req_kwargs, _token_headers())
    assert resp.status_code != 401, resp.text
    assert resp.status_code != 500, resp.text
    assert resp.status_code in expected, resp.text


@pytest.mark.asyncio
async def test_direct_file_upload_passes_auth():
    """``POST /upload`` 鉴权放行后能走完上传流程（落地到临时目录，不触碰真实存储）。"""
    app = _build_app()
    _stub_dependencies(app, _UploadSuccessService)
    files = {"file": ("contract.mp4", b"contract-bytes", "video/mp4")}
    async with _running(app) as client:
        resp = await _call(
            client,
            "post",
            "/upload",
            {"data": _UPLOAD_FORM, "files": files},
            _token_headers(),
        )
    assert resp.status_code != 401, resp.text
    assert resp.status_code != 500, resp.text
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# 路由顺序遮蔽（既有缺陷）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,req_kwargs", SHADOWED, ids=_SHADOWED_IDS)
@pytest.mark.asyncio
async def test_shadowed_endpoints_return_422(method, path, req_kwargs):
    """``GET /{resource_id}`` 注册在前，把 /statistics、/search 遮蔽成 422。

    锁定既有缺陷表现：路径参数 ``resource_id`` 拿到非数字字符串，解析失败。
    """
    app = _build_app()
    _stub_dependencies(app, _ValueErrorService)
    async with _running(app) as client:
        resp = await _call(client, method, path, req_kwargs, _token_headers())
    assert resp.status_code == 422, resp.text
    assert "resource_id" in resp.text, resp.text


@pytest.mark.xfail(
    strict=True,
    reason="GET /{resource_id} 注册在 /statistics、/search 之前，后者不可达；"
    "调整注册顺序后本用例会 XPASS，届时把两条路由纳入正式 200 断言",
)
@pytest.mark.parametrize("method,path,req_kwargs", SHADOWED, ids=_SHADOWED_IDS)
@pytest.mark.asyncio
async def test_shadowed_endpoints_should_be_reachable(method, path, req_kwargs):
    """目标契约：/statistics、/search 应能被路由到（非 422）。"""
    app = _build_app()
    _stub_dependencies(app, _ValueErrorService)
    async with _running(app) as client:
        resp = await _call(client, method, path, req_kwargs, _token_headers())
    assert resp.status_code != 422, resp.text


# ---------------------------------------------------------------------------
# 回归护栏
# ---------------------------------------------------------------------------
def test_route_module_has_no_sync_auth_stub():
    """回归护栏：本模块不得再出现同步存根依赖。"""
    from pathlib import Path

    from routes import multimedia_routes as mod

    source = Path(mod.__file__).read_text(encoding="utf-8-sig")
    assert "get_current_user_sync" not in source
    assert "Depends(get_sync_db)" not in source
    assert source.count("Depends(get_current_user)") == 15
    assert source.count("Depends(get_sync_session)") == 3
