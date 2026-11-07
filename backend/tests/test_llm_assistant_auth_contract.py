"""PR-3c-2b: ``llm_assistant_routes`` 鉴权契约测试（5 个端点）。

背景
----
改动前这 5 个端点全部依赖 ``utils.dependencies.get_current_user_sync`` ——
该函数体只有 ``raise NotImplementedError``，FastAPI 在依赖解析阶段就抛出，
因此**任何请求（含不带 token）都返回 500**，而非 401。

本文件锁定的契约：

============================= ===========================================
场景                           期望
============================= ===========================================
未携带 ``Authorization``        401
携带无效 token                  401
携带有效 token                  鉴权层通过（200 / 业务 4xx），且 **不得 500**
============================= ===========================================
403 以 ``xfail(strict=True)`` 占位（本模块无 RBAC / 租户隔离实现）。

设计说明
--------
* 401 用例走**真实**依赖链；
* 200 用例 override ``get_sync_session`` + monkeypatch
  ``get_llm_assistant_service``；
* DB 依赖必须是 ``get_sync_session``（真 generator function）；
  ``get_sync_db`` 是 ``@contextmanager``，作为 ``Depends`` 会注入
  ``_GeneratorContextManager`` 本身并导致 500，故 200 用例整体 override。
"""

from unittest.mock import MagicMock

import pytest

PREFIX = "/api/v1/org/1/ai-edu/assistant"
INVALID_HEADERS = {"Authorization": "Bearer not-a-valid-jwt"}

# (方法, 相对路径, 请求体)
ENDPOINTS = [
    ("post", "/chat", {"message": "contract"}),
    ("get", "/history", None),
    ("delete", "/history", None),
    ("get", "/statistics", None),
    ("post", "/feedback", {"message_id": "m-1", "rating": 5}),
]

_ENDPOINT_IDS = [f"{m.upper()} {p}" for m, p, _b in ENDPOINTS]


async def _call(client, method: str, path: str, body, headers=None):
    """按方法发起请求；``body`` 为 None 时不传 body。"""
    kwargs = {"headers": headers} if headers else {}
    if body is not None:
        kwargs["json"] = body
    return await getattr(client, method)(PREFIX + path, **kwargs)


# ---------------------------------------------------------------------------
# 401：未携带凭据 / 携带无效凭据
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("method,path,body", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_missing_credentials_returns_401(client, method, path, body):
    """未携带 Authorization → 401（改动前是 500 NotImplementedError）。"""
    resp = await _call(client, method, path, body)
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


@pytest.mark.parametrize("method,path,body", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_invalid_credentials_returns_401(client, method, path, body):
    """携带无法解码的 token → 401。"""
    resp = await _call(client, method, path, body, INVALID_HEADERS)
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# 200 / 业务 4xx：有效凭据下鉴权层放行
# ---------------------------------------------------------------------------
class _FakeLLMAssistantService:
    """覆盖 5 个端点用到的全部 service 方法。"""

    def __init__(self):
        # ``GET /history`` 直接读 ``service.conversation_history`` 字典
        self.conversation_history = {}

    async def chat(self, user_id, message, current_lesson_context=None):
        return {"reply": "contract"}

    def clear_history(self, user_id):
        return None

    def get_statistics(self):
        return {"total": 0}


@pytest.fixture
def _isolated_route_env(monkeypatch):
    """把路由体里的同步 DB 依赖与 service 工厂替换掉，避免触碰真实库。"""
    from main_ai_edu import app
    from routes import llm_assistant_routes as mod
    from utils.database import get_sync_session

    fake_db = MagicMock()
    app.dependency_overrides[get_sync_session] = lambda: fake_db
    monkeypatch.setattr(
        mod, "get_llm_assistant_service", lambda db: _FakeLLMAssistantService()
    )
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_sync_session, None)


@pytest.mark.parametrize("method,path,body", ENDPOINTS, ids=_ENDPOINT_IDS)
@pytest.mark.asyncio
async def test_valid_credentials_pass_auth(
    client, auth_headers, _isolated_route_env, method, path, body
):
    """有效 token → 鉴权层放行（200 或业务 4xx），绝不允许 500。"""
    resp = await _call(client, method, path, body, auth_headers)
    assert resp.status_code != 401, resp.text
    assert resp.status_code != 500, resp.text
    assert resp.status_code in (200, 400, 404), resp.text


# ---------------------------------------------------------------------------
# 403：租户隔离尚未实现（xfail 占位）
# ---------------------------------------------------------------------------
@pytest.mark.xfail(
    strict=True,
    reason="llm_assistant 路由无 RBAC / 租户隔离实现，org_id 不参与授权判断；"
    "普通用户跨 org 访问当前返回 200。补租户校验后本用例会 XPASS，届时改为正式断言",
)
@pytest.mark.asyncio
async def test_cross_org_access_denied(client, auth_headers, _isolated_route_env):
    """普通用户访问他人 org 的 AI 助手应 403 —— 当前实现无任何 org 校验。"""
    resp = await client.get(
        "/api/v1/org/999999/ai-edu/assistant/history", headers=auth_headers
    )
    assert resp.status_code == 403, resp.text


# ---------------------------------------------------------------------------
# 回归护栏
# ---------------------------------------------------------------------------
def test_route_module_has_no_sync_auth_stub():
    """回归护栏：本模块不得再出现同步存根依赖。"""
    from pathlib import Path

    from routes import llm_assistant_routes as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "get_current_user_sync" not in source
    assert source.count("Depends(get_current_user)") == 5
    # DB 依赖必须是 Depends 专用的 get_sync_session
    # （@contextmanager 版 get_sync_db 会被注入 _GeneratorContextManager → 500）
    assert "Depends(get_sync_db)" not in source
    assert source.count("Depends(get_sync_session)") == 6
