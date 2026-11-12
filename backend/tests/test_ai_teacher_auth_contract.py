"""P0-1 / P0-2 合规：``ai_teacher_routes`` 的 ``/chat`` 端点鉴权与归属契约测试。

背景
----
1.0.2 合规门禁 G1-b 要求「AI 教师对话端点必须鉴权」，G1-c 要求
「``user_id`` 归属校验（== token 主体）」。改动前
``backend/routes/ai_teacher_routes.py`` 的 ``/chat`` 既没有
``Depends(get_current_user)``，也没有任何 token 校验 —— 本机任意进程都能
以任意 ``user_id`` 调用，并把对话原文写入会话文件。

本文件锁定的契约
----------------
============================= ===========================================
场景                           期望
============================= ===========================================
未携带 ``Authorization``        401
携带无效 token                  401
携带有效 token                  200（鉴权层放行）
``user_id`` 与 token 主体不一致   403（且不得读写任何会话）
``user_id`` 为空 / 一致          200，实际使用 token 主体的 ``user_id``
============================= ===========================================
"""

import pytest

CHAT_PATH = "/api/v1/ai-teacher/chat"
INVALID_HEADERS = {"Authorization": "Bearer not-a-valid-jwt"}


def _body(user_id: str = "1", message: str = "hello") -> dict:
    """构造 /chat 请求体。

    ``knowledge_context`` 传非空值可跳过后端 RAG 检索（否则会触发
    embedding 模型懒加载，最长阻塞 3s），与鉴权断言无关。
    """
    return {
        "user_id": user_id,
        "message": message,
        "session_id": "session-test",
        "knowledge_context": "ctx",
    }


# ---------------------------------------------------------------------------
# 401：未携带凭据 / 携带无效凭据
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_credentials_returns_401(client):
    """未携带 Authorization → 401（改动前是 200，任意进程可匿名调用）。"""
    resp = await client.post(CHAT_PATH, json=_body())
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


@pytest.mark.asyncio
async def test_invalid_credentials_returns_401(client):
    """携带无法解码的 token → 401。"""
    resp = await client.post(CHAT_PATH, json=_body(), headers=INVALID_HEADERS)
    assert resp.status_code == 401, resp.text
    assert resp.status_code != 500


@pytest.mark.asyncio
async def test_malformed_authorization_header_returns_401(client):
    """Authorization 头格式非法（无 Bearer 前缀）→ 401。"""
    resp = await client.post(
        CHAT_PATH, json=_body(), headers={"Authorization": "invalid-header"}
    )
    assert resp.status_code == 401, resp.text


# ---------------------------------------------------------------------------
# 200：有效凭据下鉴权层放行
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_valid_credentials_pass_auth(client, auth_headers, token_user_id):
    """有效 token → 鉴权层放行（200），绝不允许 401 / 500。"""
    resp = await client.post(
        CHAT_PATH, json=_body(user_id=str(token_user_id)), headers=auth_headers
    )
    assert resp.status_code != 401, resp.text
    assert resp.status_code != 500, resp.text
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# 403：user_id 归属校验（实际生效的 user_id 必须等于 token 主体）
# ---------------------------------------------------------------------------
class _RecordingSessionsRepo:
    """会话仓储替身：记录 ``/chat`` 实际用到的 ``user_id``。"""

    def __init__(self):
        self.store = {}
        self.get_keys = []
        self.set_keys = []

    def get(self, key, default=None):
        self.get_keys.append(key)
        return self.store.get(key, default)

    def set(self, key, value):
        self.set_keys.append(key)
        self.store[key] = value


@pytest.fixture
def token_user_id(auth_headers):
    """解析 ``auth_headers`` 对应用户在应用库中的数值 id。"""
    from models.user import User
    from sqlalchemy.orm import sessionmaker
    from utils.database import sync_engine

    session_factory = sessionmaker(bind=sync_engine, expire_on_commit=False)
    session = session_factory()
    try:
        user = session.query(User).filter(User.username == "pytest_auth_user").first()
        assert user is not None, "auth_headers fixture 应当已在应用库创建用户"
        return user.id
    finally:
        session.close()


@pytest.fixture
def sessions_spy(monkeypatch):
    """把路由里的会话仓储替换为可记录调用的替身。"""
    from routes import ai_teacher_routes as mod

    spy = _RecordingSessionsRepo()
    monkeypatch.setattr(mod, "_sessions_repo", spy)
    return spy


@pytest.mark.asyncio
async def test_mismatched_user_id_returns_403(client, auth_headers, token_user_id):
    """body 的 user_id 与 token 主体不一致 → 403（无法冒用他人身份）。"""
    resp = await client.post(
        CHAT_PATH,
        json=_body(user_id=str(token_user_id + 100000)),
        headers=auth_headers,
    )
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_mismatched_user_id_does_not_touch_session(
    client, auth_headers, token_user_id, sessions_spy
):
    """归属校验失败时不得读写任何用户的会话。"""
    resp = await client.post(
        CHAT_PATH,
        json=_body(user_id=str(token_user_id + 100000)),
        headers=auth_headers,
    )
    assert resp.status_code == 403, resp.text
    assert sessions_spy.get_keys == []
    assert sessions_spy.set_keys == []


@pytest.mark.asyncio
async def test_effective_user_id_taken_from_token(
    client, auth_headers, token_user_id, sessions_spy
):
    """实际生效的 user_id 来自 token 主体，而不是请求体。"""
    resp = await client.post(
        CHAT_PATH, json=_body(user_id=str(token_user_id)), headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert sessions_spy.get_keys == [str(token_user_id)]


@pytest.mark.asyncio
async def test_empty_user_id_falls_back_to_token_subject(
    client, auth_headers, token_user_id, sessions_spy
):
    """body 未给 user_id（空串）时，以 token 主体为准，不报错。"""
    resp = await client.post(CHAT_PATH, json=_body(user_id=""), headers=auth_headers)
    assert resp.status_code == 200, resp.text
    assert sessions_spy.get_keys == [str(token_user_id)]


# ---------------------------------------------------------------------------
# P0-4：响应必须携带离线模式标记
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_chat_response_marks_offline_mode(client, auth_headers, token_user_id):
    """【P0-4】200 响应必须带 ``is_mock`` 标记。

    当前 ``/chat`` 仍是本地规则模板回复（尚未接入 LLM），
    必须显式告诉前端「这是离线模式」，否则前端角标无从判定。
    """
    resp = await client.post(
        CHAT_PATH, json=_body(user_id=str(token_user_id)), headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload.get("is_mock") is True, payload
    assert payload.get("model") == "mock-ai-teacher", payload


# ---------------------------------------------------------------------------
# 回归护栏
# ---------------------------------------------------------------------------
def test_route_module_declares_auth_dependency():
    """回归护栏：``/chat`` 必须声明鉴权依赖。"""
    from pathlib import Path

    from routes import ai_teacher_routes as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    assert "Depends(get_current_user)" in source
    # 同步存根依赖（NotImplementedError）不得回流
    assert "get_current_user_sync" not in source
