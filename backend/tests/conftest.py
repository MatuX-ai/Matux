"""
backend/tests 全局测试 fixture（Issue #32 批次 1 · L5）

背景
----
CI（GitHub Actions run 42203212762，PR #36 合并后的 main）里有 11 个用例因为
``backend/tests/`` 下**没有 conftest.py** 而以 ERROR 形式报::

    fixture 'client' not found
    fixture 'auth_headers' not found
    fixture 'db_session' not found
    fixture 'mock_db' not found

本文件补齐这些 fixture，使这批用例不再以「fixture 缺失」的方式失败。

提供的 fixture
--------------
===================== ====================================================
fixture                说明
===================== ====================================================
``client``             异步 HTTP 客户端（httpx.AsyncClient + ASGITransport），
                       指向 ``main_ai_edu.app``（唯一在导入期完成路由注册的入口）
``db_session``         内存 SQLite 的同步 Session（``utils.database.Base`` 建表，
                       用例结束后回滚并释放）
``test_user``          ``db_session`` 中的普通用户
``auth_headers``       普通用户的 ``Authorization`` 头
``auth_headers_user``  同 ``auth_headers``（语义别名，普通用户）
``auth_headers_admin`` 管理员的 ``Authorization`` 头
``mock_db``            ``Mock(spec=Session)``，供 service 级单测使用
===================== ====================================================

设计约束
--------
* 只新增**测试基础设施**，不修改任何业务实现；
* 不引入新的第三方依赖（httpx / pytest-asyncio / SQLAlchemy 均已在
  ``backend/requirements.txt`` 中）；
* 认证用户统一落在**应用自身使用的数据库**（``settings.DATABASE_URL``），
  以便 ``get_current_user`` 能按 ``sub`` 查到真实用户；
* 每个 fixture 用独立用户名，避免相互覆盖。

已知边界
--------
* ``main.app`` 在懒加载模式下（``ENABLE_LAZY_LOADING=True``，默认值）导入期
  只注册 system_status 路由，其余路由由 LazyLoader 在 lifespan 期挂载。
  本文件**不会**改写 ``main.app`` 的路由集合（会污染入口契约快照测试），
  因此依赖 ``main.app`` 全量路由的用例仍会 404 —— 那属于 PR-4b 的收敛范围。
"""

from datetime import timedelta
import os
import sys
import tempfile
from typing import Dict, Iterator
from unittest.mock import Mock

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# 保证以 backend/ 为根导入（与 pytest.ini 的 pythonpath = . 保持一致）
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from models.user import User, UserRole  # noqa: E402
from utils.database import Base  # noqa: E402

# ``models/creativity_models.py`` 在**模块导入期**给 User 打关系补丁
# （``User.created_templates`` 等）。该模块不在 ``models/__init__.py`` 里，
# 只有 ``routes/creativity_routes.py`` 会拉起它 —— 若它在 User 的 mapper
# 已经被配置之后才被导入，``PromptTemplate.creator`` 的 back_populates 就会
# 解析失败（``Mapper[User] has no property 'created_templates'``）。
# 这里提前导入，把补丁固定在「任何 ORM 操作之前」。
import models.creativity_models  # noqa: E402,F401  isort:skip
import models.user_license  # noqa: E402,F401  isort:skip
from models.user_license import TokenPackage, TokenPackageType  # noqa: E402

# 认证用固定口令（仅测试环境使用，不具备任何真实权限）
_TEST_PASSWORD = "PytestFixture123!"


# ---------------------------------------------------------------------------
# HTTP 客户端
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def client() -> Iterator[httpx.AsyncClient]:
    """异步 HTTP 客户端。

    用例以 ``await client.post(...)`` 的方式调用，因此这里返回
    ``httpx.AsyncClient``（配合 ``ASGITransport`` 直连 ASGI 应用，不走网络）。

    选用 ``main_ai_edu.app``：它是唯一在**模块导入期**就完成路由注册的入口
    （``register_all_routers(app, mode="lazy", strict=False)``），
    ``main.app`` 在懒加载模式下导入期只有 system_status 路由。
    """
    from main_ai_edu import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as async_client:
        yield async_client


# ---------------------------------------------------------------------------
# 数据库会话
# ---------------------------------------------------------------------------
@pytest.fixture
def db_session() -> Iterator[Session]:
    """内存 SQLite 的同步 Session。

    * 使用 ``StaticPool`` + ``sqlite://``（内存库），保证建表与会话共享同一条连接；
    * 只按 ``utils.database.Base`` 的 metadata 建表 —— 该 Base 覆盖 users /
      token_* / user_licenses 等本文件用例所需的全部模型；
    * 预置两条 Token 套餐（id=2 → 1000 tokens，id=3 → 5000 tokens），
      与 ``tests/test_ai_billing_integration.py`` 的用例约定一致；
    * 用例结束后回滚并释放连接，保证用例之间互不污染。
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    session = testing_session()
    session.add_all(
        [
            TokenPackage(
                id=2,
                name="标准包",
                description="1000 tokens",
                token_count=1000,
                price=10,
                package_type=TokenPackageType.ONE_TIME,
                is_active=True,
            ),
            TokenPackage(
                id=3,
                name="高级包",
                description="5000 tokens",
                token_count=5000,
                price=50,
                package_type=TokenPackageType.ONE_TIME,
                is_active=True,
            ),
        ]
    )
    session.commit()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        engine.dispose()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """``db_session`` 中的普通用户。"""
    user = User(
        username="pytest_user",
        email="pytest_user@example.com",
        hashed_password=_TEST_PASSWORD,
        role=UserRole.USER,
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mock_db() -> Mock:
    """``Mock(spec=Session)`` —— 供 service 级单测使用的假数据库会话。"""
    return Mock(spec=Session)


@pytest.fixture
def sample_model_file() -> Iterator[str]:
    """示例模型文件路径（``tests/test_model_update_service.py`` 使用）。"""
    with tempfile.NamedTemporaryFile(suffix=".tflite", delete=False) as handle:
        handle.write(b"This is a test model file content for testing purposes." * 100)
        handle.flush()
        path = handle.name
    try:
        yield path
    finally:
        if os.path.exists(path):
            os.unlink(path)


# ---------------------------------------------------------------------------
# 认证头
# ---------------------------------------------------------------------------
def _ensure_app_user(
    username: str, email: str, role: UserRole, is_superuser: bool = False
) -> User:
    """在**应用自身使用的数据库**里创建（或重置）一个用户。

    必须落在 ``settings.DATABASE_URL`` 指向的库上：``get_current_user`` 是通过
    ``Depends(get_db)`` 拿会话再按 ``sub`` 查库的，写到别的库会导致 401。
    """
    from utils.database import sync_engine

    session_factory = sessionmaker(bind=sync_engine, expire_on_commit=False)
    session = session_factory()
    try:
        user = session.query(User).filter(User.username == username).first()
        if user is None:
            user = User(
                username=username,
                email=email,
                hashed_password=_TEST_PASSWORD,
                role=role,
                is_active=True,
                is_superuser=is_superuser,
            )
            session.add(user)
        else:
            user.email = email
            user.role = role
            user.is_active = True
            user.is_superuser = is_superuser
        session.commit()
        session.refresh(user)
        return user
    finally:
        session.close()


def _auth_header(
    username: str, email: str, role: UserRole, is_superuser: bool = False
) -> Dict[str, str]:
    """创建用户并返回其 ``Authorization`` 头。"""
    from routes.auth_routes import create_access_token

    _ensure_app_user(username, email, role, is_superuser)
    token = create_access_token({"sub": username}, expires_delta=timedelta(minutes=30))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def _app_database_ready() -> bool:
    """确保应用数据库里存在 ``users`` 等表（会话级，只需建一次）。"""
    from utils.database import sync_engine

    try:
        Base.metadata.create_all(bind=sync_engine)
    except Exception:  # pragma: no cover - 建表失败时由用例自身报错定位
        pass
    return True


@pytest.fixture
def auth_headers(_app_database_ready: bool) -> Dict[str, str]:
    """普通用户的认证头。"""
    return _auth_header(
        "pytest_auth_user", "pytest_auth_user@example.com", UserRole.USER
    )


@pytest.fixture
def auth_headers_user(_app_database_ready: bool) -> Dict[str, str]:
    """普通用户的认证头（``auth_headers`` 的语义别名）。"""
    return _auth_header(
        "pytest_auth_user", "pytest_auth_user@example.com", UserRole.USER
    )


@pytest.fixture
def auth_headers_admin(_app_database_ready: bool) -> Dict[str, str]:
    """管理员的认证头。"""
    return _auth_header(
        "pytest_admin_user",
        "pytest_admin_user@example.com",
        UserRole.ADMIN,
        is_superuser=True,
    )
