"""
数据库工具模块
"""

from contextlib import contextmanager
from typing import AsyncGenerator, Generator

from config.settings import settings  # type: ignore[import-untyped]
from database.tenant_aware_session import (  # type: ignore[import-not-found]
    TenantAwareSession,
)
from sqlalchemy import (  # noqa: E501
    create_engine as create_sync_engine,
)
from sqlalchemy.engine import Engine as SyncEngine
from sqlalchemy.ext.asyncio import (  # noqa: E501
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 创建异步引擎
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL, echo=settings.DEBUG, pool_pre_ping=True
)

# 创建同步引擎（从异步引擎获取同步版本）
_sync_url = settings.DATABASE_URL.replace(  # noqa: E501
    "+aiosqlite", ""
).replace("+asyncpg", "")
sync_engine: SyncEngine
try:
    sync_engine = create_sync_engine(
        _sync_url, echo=settings.DEBUG, pool_pre_ping=True
    )
except Exception:
    sync_engine = (  # type: ignore[assignment]
        engine.sync_engine
        if hasattr(engine, "sync_engine")
        else create_sync_engine("sqlite:///:memory:")
    )

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(  # noqa: E501
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

# 创建租户感知的同步会话工厂
SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=TenantAwareSession,
    expire_on_commit=False,
)

# 创建基类
Base = declarative_base()


async def get_engine() -> AsyncEngine:
    """获取异步数据库引擎"""
    return engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话依赖项（异步）
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话依赖项（异步）- 别名
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@contextmanager
def get_sync_db() -> Generator[TenantAwareSession, None, None]:
    """
    数据库会话依赖项（同步）
    """
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_sync_session() -> Generator[TenantAwareSession, None, None]:
    """同步会话依赖（FastAPI ``Depends`` 专用）。

    与 :func:`get_sync_db` 的区别：后者是 ``@contextmanager``，只能配合
    ``with`` 语句使用；FastAPI 的 ``Depends`` 需要**真正的 generator
    function** 才能自动 ``close()``。直接把 ``@contextmanager`` 包装后的
    函数交给 ``Depends``，FastAPI 会把它当普通同步依赖调用，最终注入给路由
    的是 ``_GeneratorContextManager`` 本身 —— 任何 ``db.query(...)`` 都会抛
    ``AttributeError``，请求变成 500。
    """
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


async def create_db_and_tables() -> None:
    """
    创建数据库表
    """
    # 导入所有模型以确保它们被注册到 Base.metadata
    # 按依赖顺序导入：先导入基础模型，再导入依赖模型
    # fmt: off
    from models.ai_request import (  # type: ignore[import-untyped]  # noqa: F401,E501
        AIRequest,
    )
    from models.ar_vr_content import (  # type: ignore[import-untyped]  # noqa: F401,E501
        ARVRContent,
    )
    from models.content_store import (  # type: ignore[import-untyped]  # noqa: F401,E501
        ContentItem,
    )
    from models.course import (  # type: ignore[import-untyped]  # noqa: F401,E501
        Course,
        CourseAssignment,
        CourseLesson,
    )
    from models.course_version import (  # type: ignore[import-untyped]  # noqa: F401,E501
        CourseVersion,
    )
    from models.dynamic_course import (  # type: ignore[import-untyped]  # noqa: F401,E501
        GeneratedCourse,
    )
    from models.error_log import (  # type: ignore[import-untyped]  # noqa: F401,E501
        FrontendErrorLog,
    )
    from models.hardware_certification import (  # type: ignore[import-untyped]  # noqa: F401,E501
        HardwareCertificationDB,
    )
    from models.hardware_module import (  # type: ignore[import-untyped]  # noqa: F401,E501
        HardwareModule,
    )
    from models.learning_source import (  # type: ignore[import-untyped]  # noqa: F401,E501
        LearningSource,
    )
    from models.license import (  # type: ignore[import-untyped]  # noqa: F401,E501
        License,
        Organization,
    )
    from models.payment import (  # type: ignore[import-untyped]  # noqa: F401,E501
        Payment,
    )
    from models.permission import (  # type: ignore[import-untyped]  # noqa: F401,E501
        Permission,
    )
    from models.subscription import (  # type: ignore[import-untyped]  # noqa: F401,E501
        SubscriptionPlan,
    )
    from models.subscription_fsm import (  # type: ignore[import-untyped]  # noqa: F401,E501
        SubscriptionFSM,
    )
    from models.unified_learning_record import (  # type: ignore[import-untyped]  # noqa: F401,E501
        UnifiedLearningRecord,
    )
    from models.user import User  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.user_guardian import (  # type: ignore[import-untyped]  # noqa: F401,E501
        UserGuardian,
    )
    from models.user_license import (  # type: ignore[import-untyped]  # noqa: F401,E501
        UserLicense,
    )
    from models.user_organization import (  # type: ignore[import-untyped]  # noqa: F401,E501
        UserOrganization,
    )
    from modules.learning.models import (  # type: ignore[import-not-found]  # noqa: F401,E501
        StudentCourseAggregation,
    )

    # fmt: on

    async with engine.begin() as conn:
        # 导入所有模型以确保它们被注册
        # 使用 run_sync 运行同步的 SQLAlchemy 操作
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception as e:
            # 如果创建失败，记录错误但继续
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"创建表时出错 (将继续): {e}")


async def close_db() -> None:
    """
    关闭数据库连接
    """
    await engine.dispose()
