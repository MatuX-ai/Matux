"""
数据库工具模块
"""

from typing import AsyncGenerator, Generator

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

from config.settings import settings  # type: ignore[import-untyped]
from database.tenant_aware_session import (  # type: ignore[import-not-found]
    TenantAwareSession,
)

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


def get_sync_db() -> Generator[TenantAwareSession, None, None]:
    """
    数据库会话依赖项（同步）
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
    from models.license import Organization, License  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.user import User  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.ar_vr_content import ARVRContent  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.content_store import ContentItem  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.course_version import CourseVersion  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.dynamic_course import GeneratedCourse  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.hardware_certification import HardwareCertificationDB  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.hardware_module import HardwareModule  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.learning_source import LearningSource  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.payment import Payment  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.permission import Permission  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.subscription import SubscriptionPlan  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.subscription_fsm import SubscriptionFSM  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.unified_learning_record import UnifiedLearningRecord  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.user_license import UserLicense  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.user_organization import UserOrganization  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.ai_request import AIRequest  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.course import Course, CourseLesson, CourseAssignment  # type: ignore[import-untyped]  # noqa: F401,E501
    from models.user_guardian import UserGuardian  # type: ignore[import-untyped]  # noqa: F401,E501
    from modules.learning.models import StudentCourseAggregation  # type: ignore[import-not-found]  # noqa: F401,E501
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
