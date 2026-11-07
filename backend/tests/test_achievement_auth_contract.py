"""PR-3c-2a: ``achievement_routes`` 鉴权契约测试（11 个端点）。

背景
----
改动前这 11 个端点全部依赖 ``utils.dependencies.get_current_user_sync`` ——
该函数体只有 ``raise NotImplementedError``，FastAPI 在依赖解析阶段就抛出，
因此**任何请求（含不带 token）都返回 500**，而非 401。

本文件锁定的契约：

============================= ============================================
场景                           期望
============================= ============================================
未携带 ``Authorization``        401
携带无效 token                 401
携带有效 token                 鉴权层通过（200 / 业务 404），且 **不得 500**
============================= ============================================

403（已登录但无权限）当前**不可断言**：这 11 个端点里 4 个 admin 端点只有
``# TODO: 添加管理员权限检查`` 注释，没有任何 RBAC 实现。对应的
``test_admin_endpoint_denies_normal_user`` 以 ``xfail(strict=True)`` 占位：
将来补上 RBAC 后会变成 XPASS 并提示改为正式断言。

设计说明
--------
* 401 用例走**真实**依赖链，不做任何 override —— 否则测不到鉴权本身；
* 200 用例用 ``dependency_overrides`` + ``monkeypatch`` 隔离数据库与业务层，
  只验证「鉴权通过后请求能进到路由体」，不触碰 ``ai_service.db``；
* 之所以必须隔离：``models.achievement`` 使用 ``database.db.Base``，而
  ``models.leaderboard`` 的同 registry 表有指向 ``users`` 的外键，跨 Base
  无法 ``create_all``，真实 DB 建表会抛 ``NoReferencedTableError``。
"""

from unittest.mock import MagicMock

import pytest

PREFIX = "/api/v1/org/1/achievements"
INVALID_HEADERS = {"Authorization": "Bearer not-a-valid-jwt"}

# (方法, 相对路径, 请求体, 是否读取端点)
ENDPOINTS = [
    ("post", "/admin/create", {"name": "contract"}, False),
    ("put", "/admin/1", {"name": "contract"}, False),
    ("delete", "/admin/1", None, False),
    ("get", "/admin/list", None, True),
    ("get", "/my/list", None, True),
    ("get", "/my/statistics", None, True),
    ("post", "/my/1/claim", None, False),
    (
        "post",
        "/progress/update",
        {"metric_name": "study_time_minutes", "metric_value": 1},
        False,
    ),
    ("get", "/progress/current", None, True),
    ("post", "/admin/initialize", None, False),
    ("get", "/1", None, True),
]

_ENDPOINT_IDS = [f"{m.upper()} {p}" for m, p, _b, _r in ENDPOINTS]


async def _call(client, method: str, path: str, body, headers=None):
    """按方法发起请求；``body`` 为 None 时不传 body。"""
    kwargs = {"headers": headers} if headers else {}
    if body is not None:
        kwargs["json"] = body
    return await getattr(client, method)(PREFIX + path, **kwargs)


# ---------------------------------------------------------------------------
# 401：未携带凭据 / 携带无效凭据
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,body,_read", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_missing_credentials_returns_401(client, method, path, body, _read):
    """未携带 Authorization → 401（改动前是 500 NotImplementedError）。"""
    resp = await _call(client, method, path, body)
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


@pytest.mark.parametrize("method,path,body,_read", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_invalid_credentials_returns_401(client, method, path, body, _read):
    """携带无法解码的 token → 401。"""
    resp = await _call(client, method, path, body, INVALID_HEADERS)
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# 200 / 业务 4xx：有效凭据下鉴权层放行
# ---------------------------------------------------------------------------
class _Record:
    """``to_dict()`` 的最小替身。"""

    id = 1
    is_hidden = False

    def to_dict(self):
        return {"id": 1, "name": "contract"}


class _FakeAchievementService:
    """``_admin/list`` 会访问 ``service.db.query(...).count()``，故保留 db 属性。"""

    def __init__(self):
        self.db = MagicMock()
        self.db.query.return_value.filter.return_value.count.return_value = 0

    def create_achievement(self, data):
        return _Record()

    def update_achievement(self, achievement_id, updates):
        return _Record()

    def delete_achievement(self, achievement_id):
        return True

    def list_achievements(self, **kwargs):
        return []

    def get_user_achievements(self, **kwargs):
        return []

    def get_progress_statistics(self, **kwargs):
        return {"total": 0}

    def claim_achievement_reward(self, **kwargs):
        return {"points": 0}

    def update_progress(self, **kwargs):
        return []

    def initialize_default_achievements(self):
        return 0

    def get_achievement(self, achievement_id):
        return _Record()

    def get_user_achievement(self, user_id, achievement_id):
        return None


@pytest.fixture
def _isolated_route_env(monkeypatch):
    """把路由体里的 DB 依赖与 service 工厂替换掉，避免触碰真实库。"""
    from main_ai_edu import app
    from routes import achievement_routes as mod
    from utils.database import get_sync_session

    fake_db = MagicMock()
    fake_db.query.return_value.filter.return_value.all.return_value = []
    app.dependency_overrides[get_sync_session] = lambda: fake_db
    monkeypatch.setattr(
        mod, "get_achievement_service", lambda db: _FakeAchievementService()
    )
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_sync_session, None)


@pytest.mark.parametrize("method,path,body,_read", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_valid_credentials_pass_auth(
    client, auth_headers, _isolated_route_env, method, path, body, _read
):
    """有效 token → 鉴权层放行（200 或业务 404），绝不允许 500。"""
    resp = await _call(client, method, path, body, auth_headers)
    assert resp.status_code != 401, resp.text
    assert resp.status_code != 500, resp.text
    assert resp.status_code in (200, 404), resp.text


# ---------------------------------------------------------------------------
# 403：RBAC 尚未实现（xfail 占位）
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="admin 端点无 RBAC 实现（源码仅 # TODO: 添加管理员权限检查），"
    "普通用户当前也能通过；补 RBAC 后本用例会 XPASS，届时改为正式断言",
)
@pytest.mark.asyncio
async def test_admin_endpoint_denies_normal_user(
    client, auth_headers, _isolated_route_env
):
    """普通用户访问 ``GET /admin/list`` 应 403 —— 当前实现无权限校验。"""
    resp = await client.get(PREFIX + "/admin/list", headers=auth_headers)
    assert resp.status_code == 403, resp.text


def test_route_module_has_no_sync_auth_stub():
    """回归护栏：本模块不得再出现同步存根依赖。"""
    from pathlib import Path

    from routes import achievement_routes as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "get_current_user_sync" not in source
    assert source.count("Depends(get_current_user)") == 11


def test_sync_session_dependency_is_generator():
    """``get_sync_session`` 必须是真 generator —— FastAPI 才能自动收尾。"""
    import inspect

    from utils.database import get_sync_db, get_sync_session

    assert inspect.isgeneratorfunction(get_sync_session)
    # 反例：``@contextmanager`` 包装后的 get_sync_db 不是 generator function，
    # 直接交给 ``Depends`` 会注入 _GeneratorContextManager 本身。
    assert not inspect.isgeneratorfunction(get_sync_db)


def test_stub_module_still_unimplemented():
    """记录事实：``utils.dependencies`` 的空壳仍在（供 PR-3c-2b/c/d 参考）。"""
    from utils import dependencies

    with pytest.raises(NotImplementedError):
        dependencies.get_current_user_sync()
