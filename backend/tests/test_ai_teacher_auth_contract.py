"""P0-1 合规：``ai_teacher_routes`` 的 ``/chat`` 端点鉴权契约测试。

背景
----
1.0.2 合规门禁 G1-b 要求「AI 教师对话端点必须鉴权」。改动前
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
async def test_valid_credentials_pass_auth(client, auth_headers):
    """有效 token → 鉴权层放行（200），绝不允许 401 / 500。"""
    resp = await client.post(CHAT_PATH, json=_body(), headers=auth_headers)
    assert resp.status_code != 401, resp.text
    assert resp.status_code != 500, resp.text
    assert resp.status_code == 200, resp.text


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
