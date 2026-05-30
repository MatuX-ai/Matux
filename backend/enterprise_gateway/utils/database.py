"""
企业网关数据库工具模块
提供数据库连接和会话管理功能
"""

from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from config.enterprise_settings import enterprise_settings

# 创建数据库引擎
engine = create_engine(
    enterprise_settings.ENTERPRISE_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=enterprise_settings.DEBUG,
)

# 创建异步数据库引擎（如果需要）
try:
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    async_engine = create_async_engine(
        enterprise_settings.ENTERPRISE_DATABASE_URL.replace(
            "postgresql://", "postgresql+asyncpg://"
        ),
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=enterprise_settings.DEBUG,
    )
except ImportError:
    async_engine = None

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[Session, None]:
    """
    获取异步数据库会话
    用于异步依赖注入
    """
    if async_engine is None:
        raise RuntimeError("Async database engine not available")

    async with AsyncSession(async_engine) as session:
        yield session


async def create_enterprise_tables():
    """
    创建企业网关相关的数据库表
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def create_enterprise_tables_sync():
    """
    同步创建企业网关相关的数据库表
    """
    Base.metadata.create_all(bind=engine)


async def drop_enterprise_tables():
    """
    删除企业网关相关的数据库表
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def drop_enterprise_tables_sync():
    """
    同步删除企业网关相关的数据库表
    """
    Base.metadata.drop_all(bind=engine)
