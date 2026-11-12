"""P0-3 合规：AI 对话原文不得落盘（会话文件 / 审计日志 / 计费描述）。

背景
----
1.0.2 合规门禁 G1-d 要求「LLM 路径不落盘对话原文」，G1-e 要求
「审计日志不记原文」。改动前：

* ``backend/routes/ai_teacher_routes.py`` 的 ``/chat`` 把 user / assistant
  **原文**写进 ``backend/data/ai_teacher_sessions.json``（保留最近 20 条）；
* ``backend/services/llm_assistant_service.py`` 的 ``_log_conversation``
  把 ``message`` 与 ``reply`` 原文打进日志（``logger.debug``）；
* 同文件的 ``chat()`` 把 ``message[:50]`` 片段打进 INFO 日志，
  并把同一片段写进计费流水 ``usage_description``（落库）；
* ``backend/routes/llm_assistant_routes.py`` 把 ``message[:50]`` 打进日志。

本文件锁定的契约
----------------
* ``AI_LLM_STORE_CONVERSATION`` 默认 False；
* 会话落盘文件不含提问 / 回复原文，但保留元数据（角色 / 长度 / 时间戳）；
* 审计日志与计费描述不含对话原文。
"""

import json
import logging

from cache.ai_teacher_persistence import get_sessions_repo, reset_all_repos_for_testing
from config.settings import settings
import pytest

# 哨兵文本：任何落盘 / 日志内容里都不允许出现
SENTINEL = "P0_SECRET_CONVERSATION_TEXT_9f3a"

CHAT_PATH = "/api/v1/ai-teacher/chat"
ASSISTANT_PATH = "/api/v1/org/1/ai-edu/assistant/chat"


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


# ---------------------------------------------------------------------------
# 默认配置
# ---------------------------------------------------------------------------
def test_store_conversation_disabled_by_default():
    """回归护栏：默认不得落盘对话原文。"""
    assert settings.AI_LLM_STORE_CONVERSATION is False


# ---------------------------------------------------------------------------
# 会话文件：不含原文，但保留元数据
# ---------------------------------------------------------------------------
@pytest.fixture
def isolated_sessions_repo(tmp_path, monkeypatch):
    """把会话仓储重定向到临时目录，并让路由使用这个实例。"""
    monkeypatch.setenv("AI_TEACHER_DATA_DIR", str(tmp_path))
    reset_all_repos_for_testing()
    from routes import ai_teacher_routes as mod

    repo = get_sessions_repo()
    monkeypatch.setattr(mod, "_sessions_repo", repo)
    try:
        yield repo
    finally:
        reset_all_repos_for_testing()


def _seed_session(repo, user_id: str) -> None:
    repo.set(
        user_id,
        {
            "sessionId": "session-test",
            "userId": user_id,
            "recentMessages": [],
            "currentTask": None,
            "startedAt": "2026-11-12T00:00:00",
            "lastActivityAt": "2026-11-12T00:00:00",
        },
    )


@pytest.mark.asyncio
async def test_session_file_contains_no_raw_conversation(
    client, auth_headers, token_user_id, isolated_sessions_repo, tmp_path
):
    """会话文件里不得出现对话原文，但要有元数据（角色 / 长度 / 时间戳）。"""
    user_key = str(token_user_id)
    _seed_session(isolated_sessions_repo, user_key)

    resp = await client.post(
        CHAT_PATH,
        json={
            "user_id": user_key,
            "message": SENTINEL,
            "session_id": "session-test",
            "knowledge_context": "ctx",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text

    isolated_sessions_repo.flush()
    session_file = tmp_path / "ai_teacher_sessions.json"
    assert session_file.exists(), "会话文件应当被落盘（只是不含原文）"

    raw_text = session_file.read_text(encoding="utf-8")
    assert SENTINEL not in raw_text, "会话文件不得包含提问原文"

    payload = json.loads(raw_text)
    entries = payload[user_key]["recentMessages"]
    assert len(entries) == 2
    assert [e["role"] for e in entries] == ["user", "assistant"]
    # 元数据保留：角色 / 长度 / 时间戳
    assert entries[0]["content_length"] == len(SENTINEL)
    assert entries[1]["content_length"] > 0
    assert entries[0]["timestamp"]
    # 原文字段整个不应存在
    assert "content" not in entries[0]
    assert "content" not in entries[1]


@pytest.mark.asyncio
async def test_store_conversation_switch_restores_raw_text(
    client, auth_headers, token_user_id, isolated_sessions_repo, tmp_path, monkeypatch
):
    """显式开启 ``AI_LLM_STORE_CONVERSATION`` 时才写原文（本地调试开关）。"""
    monkeypatch.setattr(settings, "AI_LLM_STORE_CONVERSATION", True)
    user_key = str(token_user_id)
    _seed_session(isolated_sessions_repo, user_key)

    resp = await client.post(
        CHAT_PATH,
        json={
            "user_id": user_key,
            "message": SENTINEL,
            "session_id": "session-test",
            "knowledge_context": "ctx",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text

    isolated_sessions_repo.flush()
    raw_text = (tmp_path / "ai_teacher_sessions.json").read_text(encoding="utf-8")
    assert SENTINEL in raw_text


# ---------------------------------------------------------------------------
# 审计日志：只记元数据
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ai_teacher_chat_log_has_no_raw_conversation(
    client, auth_headers, token_user_id, caplog
):
    """AI 教师 /chat 的审计日志不得包含对话原文。"""
    with caplog.at_level(logging.INFO, logger="routes.ai_teacher_routes"):
        resp = await client.post(
            CHAT_PATH,
            json={
                "user_id": str(token_user_id),
                "message": SENTINEL,
                "session_id": "session-test",
                "knowledge_context": "ctx",
            },
            headers=auth_headers,
        )
    assert resp.status_code == 200, resp.text
    assert SENTINEL not in caplog.text
    # 元数据仍然可审计
    assert "message_len" in caplog.text


@pytest.mark.asyncio
async def test_llm_assistant_service_log_has_no_raw_conversation(caplog):
    """LLM 助手 service 的日志（含 debug 级对话日志）不得包含原文。"""
    from services.llm_assistant_service import LLMAssistantService

    service = LLMAssistantService(None)
    with caplog.at_level(logging.DEBUG, logger="services.llm_assistant_service"):
        await service.chat(user_id=1, message=SENTINEL)

    assert SENTINEL not in caplog.text
    assert "message_length" in caplog.text


@pytest.mark.asyncio
async def test_llm_assistant_route_log_has_no_raw_conversation(
    client, auth_headers, caplog, monkeypatch
):
    """LLM 助手路由的日志不得包含对话原文。"""
    from main_ai_edu import app
    from routes import llm_assistant_routes as mod
    from utils.database import get_sync_session

    class _FakeService:
        async def chat(self, user_id, message, current_lesson_context=None):
            return {"reply": "ok"}

    app.dependency_overrides[get_sync_session] = lambda: None
    monkeypatch.setattr(mod, "get_llm_assistant_service", lambda db: _FakeService())
    try:
        with caplog.at_level(logging.INFO, logger="routes.llm_assistant_routes"):
            resp = await client.post(
                ASSISTANT_PATH, json={"message": SENTINEL}, headers=auth_headers
            )
    finally:
        app.dependency_overrides.pop(get_sync_session, None)

    assert resp.status_code == 200, resp.text
    assert SENTINEL not in caplog.text


# ---------------------------------------------------------------------------
# 回归护栏：源码级
# ---------------------------------------------------------------------------
def test_no_raw_message_truncation_in_logs():
    """回归护栏：不得再出现 ``message[:50]`` 这类原文片段入日志 / 入库。"""
    from pathlib import Path

    backend_root = Path(__file__).resolve().parent.parent
    for relative in (
        "services/llm_assistant_service.py",
        "routes/llm_assistant_routes.py",
        "routes/ai_teacher_routes.py",
    ):
        source = (backend_root / relative).read_text(encoding="utf-8")
        assert "message[:50]" not in source, f"{relative} 仍在记录对话原文片段"
