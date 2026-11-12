"""P0-5：统一 JWT ``sub`` 语义为 username（手机号登录链路修复）。

根因
----
手机号登录链路（``modules/auth/auth_service.py`` 的 ``_generate_token_pair``）
签发的 JWT，其 ``sub`` 载荷曾是**用户 id**（``str(user.id)``）；而全仓所有
鉴权依赖都按 **username** 查库：

================================================= =========================
位置                                                查库条件
================================================= =========================
``routes/auth_routes.py`` ``get_current_user``      ``User.username == sub``
``middleware/auth.py`` ``get_current_user``          ``User.username == sub``
``utils/auth_utils.py`` ``get_current_user_sync``    ``User.username == sub``
``routes/ai_edu_websocket_routes.py`` 握手鉴权       ``User.username == sub``
================================================= =========================

``str(user.id)`` 永远不会等于任何 ``User.username`` → 手机号用户持 token
访问任何受保护端点恒 401（前端表现为「登录成功但一调接口就 401」）。

修复
----
1. ``_generate_token_pair`` 统一签发 ``sub = user.username``（与
   ``routes/auth_routes.py`` 的 ``/signin`` / ``/signup`` / ``/token`` 一致），
   并补齐 ``uid = user.id``（``gamification_websocket_routes`` 靠它取用户 id）。
2. ``refresh_access_token`` 改为按 ``uid`` 查库（回退按 ``sub``），
   不再对 ``sub`` 做 ``int()``。
3. ``routes/auth_routes.py`` 的 ``/refresh`` 用查库得到的 ``user.id`` 回填
   ``uid``，保证新令牌对的 ``uid`` 永远可用。
4. ``services/oauth_service.py`` 同一处根因（``sub = str(user.id)``）一并统一。

产品尚未上线，**没有历史 id token 需要兼容** —— 不写 id 回退兼容层。
"""

import ast
from pathlib import Path
from typing import Iterator, List, Tuple

import pytest
import pytest_asyncio

CHAT_PATH = "/api/v1/ai-teacher/chat"

_PHONE = "13900001234"
_PHONE_PASSWORD = "PytestPhone123!"
_PHONE_USERNAME = "pytest_phone_user"


def _body(user_id: str = "", message: str = "hello") -> dict:
    """构造 ``/chat`` 请求体。

    ``knowledge_context`` 传非空值可跳过后端 RAG 检索（否则会触发
    embedding 模型懒加载，最长阻塞 3s），与鉴权断言无关。
    """
    return {
        "user_id": user_id,
        "message": message,
        "session_id": "session-p0-5",
        "knowledge_context": "ctx",
    }


# ---------------------------------------------------------------------------
# fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def phone_user(_app_database_ready):
    """在**应用自身数据库**里创建一个「只有手机号」的用户。

    必须落在 ``settings.DATABASE_URL`` 指向的库上：``get_current_user`` 走
    ``Depends(get_db)`` 按 ``sub`` 查库，写到别的库必然 401。
    """
    from models.user import User, UserRole
    from modules.auth.auth_service import hash_password
    from sqlalchemy.orm import sessionmaker
    from utils.database import sync_engine

    session_factory = sessionmaker(bind=sync_engine, expire_on_commit=False)
    session = session_factory()
    try:
        session.query(User).filter(
            (User.username == _PHONE_USERNAME) | (User.phone == _PHONE)
        ).delete(synchronize_session=False)
        session.commit()
        user = User(
            username=_PHONE_USERNAME,
            email=None,
            phone=_PHONE,
            hashed_password=hash_password(_PHONE_PASSWORD),
            role=UserRole.USER,
            is_active=True,
            is_superuser=False,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        yield user
    finally:
        session.query(User).filter(User.phone == _PHONE).delete(
            synchronize_session=False
        )
        session.commit()
        session.close()


@pytest_asyncio.fixture
async def phone_tokens(phone_user):
    """走**统一认证服务**的手机号登录链路，拿到真实签发的令牌对。

    ``modules/auth/auth_routes.py`` 的 ``POST /api/v1/unified-auth/login/phone``
    就是直接调用这个服务方法；这里不经过 HTTP，是因为 ``unified_auth``
    路由在 ``core/router_registry.py`` 里是 ``mode="legacy"`` —— 桌面端入口
    （``main_ai_edu``）不注册它，但**签发逻辑完全是同一条代码路径**。
    """
    from modules.auth.auth_service import unified_auth_service
    from utils.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        tokens = await unified_auth_service.login_by_phone(
            db=session, phone=_PHONE, password=_PHONE_PASSWORD
        )
    assert tokens is not None, "手机号登录应当成功"
    return tokens


@pytest.fixture
def username_user_id(auth_headers):
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
# 1. 签发口径：sub 必须是 username
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_phone_login_token_sub_is_username(phone_tokens, phone_user):
    """手机号登录签发的 token，其 ``sub`` 必须是 username（不能是 id）。"""
    from modules.auth.auth_service import decode_token

    payload = decode_token(phone_tokens["access_token"])
    assert payload is not None
    assert payload["sub"] == phone_user.username, payload
    assert payload["sub"] != str(phone_user.id), payload
    # uid 必须带上：gamification WebSocket 优先读 uid 取用户 id
    assert payload.get("uid") == phone_user.id, payload


# ---------------------------------------------------------------------------
# 2. 手机号登录用户可以访问受保护端点（修复前恒 401）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_phone_login_user_can_access_protected_endpoint(
    client, phone_tokens, phone_user
):
    """手机号登录用户持 token 访问 ``/chat`` → 200（修复前是 401）。"""
    headers = {"Authorization": "Bearer %s" % phone_tokens["access_token"]}
    resp = await client.post(
        CHAT_PATH, json=_body(user_id=str(phone_user.id)), headers=headers
    )
    assert resp.status_code != 401, resp.text
    assert resp.status_code != 500, resp.text
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# 3. 用户名登录链路不回归
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_username_login_still_works(client, auth_headers, username_user_id):
    """用户名口径的 token 依旧能访问受保护端点（不回归）。"""
    resp = await client.post(
        CHAT_PATH, json=_body(user_id=str(username_user_id)), headers=auth_headers
    )
    assert resp.status_code != 401, resp.text
    assert resp.status_code != 500, resp.text
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# 4. 刷新令牌链路
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_refresh_token_preserves_sub(phone_tokens, phone_user):
    """刷新令牌后，新 token 的 ``sub`` 仍是 username。"""
    from modules.auth.auth_service import decode_token, unified_auth_service
    from utils.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        refreshed = await unified_auth_service.refresh_access_token(
            db=session, refresh_token=phone_tokens["refresh_token"]
        )
    assert refreshed is not None, "刷新令牌应当成功"

    payload = decode_token(refreshed["access_token"])
    assert payload is not None
    assert payload["sub"] == phone_user.username, payload
    assert payload["sub"] != str(phone_user.id), payload
    assert payload.get("uid") == phone_user.id, payload


# ---------------------------------------------------------------------------
# 5. 统一认证服务的「用户名登录」链路同样统一到 username
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unified_username_login_token_sub_is_username(phone_user):
    """``login_by_username`` 走的是同一条签发路径 → ``sub`` 同样是 username。"""
    from modules.auth.auth_service import decode_token, unified_auth_service
    from utils.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        tokens = await unified_auth_service.login_by_username(
            db=session, username=phone_user.username, password=_PHONE_PASSWORD
        )
    assert tokens is not None, "用户名登录应当成功"

    payload = decode_token(tokens["access_token"])
    assert payload is not None
    assert payload["sub"] == phone_user.username, payload
    assert payload.get("uid") == phone_user.id, payload


# ---------------------------------------------------------------------------
# 6. 回归护栏：不允许再出现 id 口径的 sub
# ---------------------------------------------------------------------------
_SKIP_PREFIXES = (
    "tests/",
    "gamification/",
    "venv/",
    "build/",
    "dist/",
    "migrations/",
    "scripts/",
    "__pycache__/",
)


def _iter_python_sources(backend_root: Path) -> Iterator[Tuple[str, Path]]:
    """遍历 backend/ 下的 Python 源文件（跳过测试与构建产物目录）。"""
    for path in backend_root.rglob("*.py"):
        rel = path.relative_to(backend_root).as_posix()
        if rel.startswith(_SKIP_PREFIXES):
            continue
        yield rel, path


def _is_id_subject(value: ast.AST) -> bool:
    """判断一个 dict 值是否是「id 口径」的 sub（如 ``str(user.id)``）。"""
    if not (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == "str"
        and value.args
    ):
        return False
    arg = value.args[0]
    if isinstance(arg, ast.Attribute):
        return arg.attr == "id"
    return isinstance(arg, ast.Name) and arg.id.endswith("_id")


def _find_id_sub_issuers(backend_root: Path) -> List[str]:
    """找出所有把 ``sub`` 写成 id 口径的签发点。"""
    offenders: List[str] = []
    for rel, path in _iter_python_sources(backend_root):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values):
                if not (isinstance(key, ast.Constant) and key.value == "sub"):
                    continue
                if _is_id_subject(value):
                    offenders.append("%s:%d" % (rel, node.lineno))
    return offenders


def test_no_issuer_uses_user_id_as_sub():
    """回归护栏：全仓签发方不得再写 ``"sub": str(user.id)`` 这类 id 口径。"""
    backend_root = Path(__file__).resolve().parent.parent
    offenders = _find_id_sub_issuers(backend_root)
    assert offenders == [], offenders
