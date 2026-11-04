"""
Supabase 数据库连接工具
提供与 Supabase PostgreSQL 数据库的连接和会话管理
"""

from contextlib import asynccontextmanager
import os
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

# 从环境变量获取数据库URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Please configure your Supabase database connection."
    )

# 将 postgresql:// 转换为 postgresql+asyncpg:// 用于异步连接
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# ============================================
# 同步引擎和会话
# ============================================
sync_engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DEBUG", "False").lower() == "true",
)

SyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

# ============================================
# 异步引擎和会话
# ============================================
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=os.getenv("DEBUG", "False").lower() == "true",
    poolclass=NullPool,  # Vercel serverless 环境需要
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================
# 依赖注入函数
# ============================================

def get_sync_db() -> Generator[Session, None, None]:
    """
    获取同步数据库会话
    用于 FastAPI 依赖注入
    """
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话
    用于 FastAPI 依赖注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ============================================
# 上下文管理器
# ============================================

@asynccontextmanager
async def get_db_context():
    """
    异步数据库会话上下文管理器
    用法:
        async with get_db_context() as db:
            # 使用 db 进行数据库操作
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================
# 表管理
# ============================================

async def create_tables():
    """
    创建所有数据库表
    在应用启动时调用
    """
    from backend.utils.database import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """
    删除所有数据库表
    谨慎使用！仅用于开发/测试环境
    """
    from backend.utils.database import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ============================================
# 健康检查
# ============================================

async def check_database_health() -> dict:
    """
    检查数据库连接健康状态
    返回连接状态和响应时间
    """
    import time

    result = {
        "status": "unhealthy",
        "database": "supabase",
        "response_time_ms": 0,
        "error": None,
    }

    try:
        start_time = time.time()

        async with AsyncSessionLocal() as session:
            # 执行简单查询测试连接
            await session.execute("SELECT 1")

        elapsed_time = (time.time() - start_time) * 1000
        result["status"] = "healthy"
        result["response_time_ms"] = round(elapsed_time, 2)

    except Exception as e:
        result["error"] = str(e)

    return result
