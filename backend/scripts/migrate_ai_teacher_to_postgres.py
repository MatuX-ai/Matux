"""
【P3-D-3】AI 教师持久化数据迁移：SQLite → PostgreSQL

将 7 张 KV 表的全部数据从 SQLite 迁移到 PostgreSQL。
- 自动建表（基于 SQLAlchemy ORM）
- 自动建 GIN 索引
- 批量 INSERT
- 校验行数一致性

用法：
    python scripts/migrate_ai_teacher_to_postgres.py \\
        --sqlite-url sqlite+aiosqlite:///./ai_service.db \\
        --postgres-url postgresql+asyncpg://user:pass@host:5432/dbname \\
        --batch-size 500
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from typing import Dict, List

# 保证 backend 根目录在 sys.path
import os

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from sqlalchemy import create_engine as create_sync_engine, inspect, text  # noqa: E501, E402
from sqlalchemy.dialects.postgresql import insert as pg_insert  # noqa: E501, E402

from models.ai_teacher_persistence import (  # noqa: E501, E402
    ALL_TABLE_REGISTRY,
)
from utils.database import Base  # noqa: E501, E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("migrate_pg")


def build_sync_url(url: str) -> str:
    """把 aiosqlite/asyncpg 异步 URL 转换为同步 URL"""
    return (
        url.replace("+aiosqlite", "")
        .replace("+asyncpg", "")
    )


def is_postgres(url: str) -> bool:
    return url.startswith("postgresql://") or url.startswith("postgres://")


def test_connection(url: str) -> bool:
    """尝试连接数据库，确认可访问"""
    try:
        engine = create_sync_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception as e:
        logger.error(f"无法连接 {url}: {e}")
        return False


def list_tables(engine) -> List[str]:
    insp = inspect(engine)
    return insp.get_table_names()


def ensure_postgres_schema(engine) -> None:
    """在 PostgreSQL 上创建所有 ORM 表 + GIN 索引"""
    logger.info("创建/校验 PostgreSQL 表结构（create_all）")
    Base.metadata.create_all(engine)

    insp = inspect(engine)
    pg_tables = set(insp.get_table_names())
    for name, model_cls in ALL_TABLE_REGISTRY.items():
        table = model_cls.__tablename__
        if table not in pg_tables:
            logger.warning(f"  [SKIP] 表 {table} 不在 PG schema")
            continue
        idx = f"idx_{table}_value_gin"
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_indexes WHERE indexname = :idx"),
                {"idx": idx},
            ).scalar()
            if not exists:
                conn.execute(
                    text(
                        f'CREATE INDEX IF NOT EXISTS "{idx}" '
                        f'ON "{table}" USING gin (value jsonb_path_ops)'
                    )
                )
                conn.commit()
                logger.info(f"  [OK] 创建 GIN 索引 {idx}")
            else:
                logger.info(f"  [EXIST] GIN 索引 {idx}")


def read_sqlite_table(sqlite_engine, model_cls) -> List[Dict]:
    """从 SQLite 读取一整表数据，转为 dict 列表"""
    insp = inspect(sqlite_engine)
    table = model_cls.__tablename__
    if table not in insp.get_table_names():
        logger.info(f"  [EMPTY] SQLite 表 {table} 不存在")
        return []
    with sqlite_engine.connect() as conn:
        rows = conn.execute(text(f'SELECT user_id, value, updated_at FROM "{table}"')).fetchall()
    return [
        {
            "user_id": r[0],
            "value": r[1] if isinstance(r[1], (dict, list)) else json.loads(r[1] or "null"),
            "updated_at": r[2] or datetime.utcnow(),
        }
        for r in rows
    ]


def write_postgres_table(
    pg_engine,
    model_cls,
    rows: List[Dict],
    batch_size: int = 500,
) -> int:
    """批量 upsert 到 PostgreSQL"""
    if not rows:
        return 0

    written = 0
    with pg_engine.begin() as conn:
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            pg_rows = [
                {
                    "user_id": r["user_id"],
                    "value": json.loads(json.dumps(r["value"], default=str)),
                    "updated_at": r["updated_at"],
                }
                for r in batch
            ]
            stmt = pg_insert(model_cls).values(pg_rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=["user_id"],
                set_={
                    "value": stmt.excluded.value,
                    "updated_at": stmt.excluded.updated_at,
                },
            )
            conn.execute(stmt)
            written += len(batch)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AI Teacher 数据迁移：SQLite → PostgreSQL"
    )
    parser.add_argument(
        "--sqlite-url",
        default="sqlite:///./ai_service.db",
        help="源 SQLite URL (默认 ./ai_service.db)",
    )
    parser.add_argument(
        "--postgres-url",
        required=True,
        help="目标 PostgreSQL URL (postgresql://user:pass@host:5432/dbname)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="批量写入大小 (默认 500)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印计划，不实际写入",
    )
    parser.add_argument(
        "--skip-gin",
        action="store_true",
        help="跳过 GIN 索引创建（节省时间）",
    )
    args = parser.parse_args()

    logger.info("=" * 70)
    logger.info("AI Teacher 数据迁移：SQLite → PostgreSQL")
    logger.info(f"  源:      {args.sqlite_url}")
    logger.info(f"  目标:    {args.postgres_url}")
    logger.info(f"  批量:    {args.batch_size}")
    logger.info(f"  Dry-run: {args.dry_run}")
    logger.info("=" * 70)

    # Step 1: 校验连接
    logger.info("Step 1: 校验两端连接")
    if not test_connection(args.sqlite_url):
        logger.error("SQLite 连接失败")
        return 1
    if not is_postgres(args.postgres_url) and not args.dry_run:
        logger.error("postgres-url 必须以 postgresql:// 开头")
        return 1
    if not args.dry_run and not test_connection(args.postgres_url):
        logger.error("PostgreSQL 连接失败")
        return 1
    logger.info("  [OK] 两端均可连接")

    sqlite_engine = create_sync_engine(args.sqlite_url, pool_pre_ping=True)
    if args.dry_run:
        logger.info("Step 2 (DRY): 仅展示将迁移的表")
        total = 0
        for name, model_cls in ALL_TABLE_REGISTRY.items():
            rows = read_sqlite_table(sqlite_engine, model_cls)
            logger.info(f"  - {model_cls.__tablename__}: {len(rows)} 行")
            total += len(rows)
        logger.info(f"总行数: {total}")
        return 0

    pg_engine = create_sync_engine(args.postgres_url, pool_pre_ping=True)

    # Step 2: 建表 + 索引
    logger.info("Step 2: 在 PG 上建表 + GIN 索引")
    if args.skip_gin:
        Base.metadata.create_all(pg_engine)
    else:
        ensure_postgres_schema(pg_engine)

    # Step 3: 逐表迁移
    logger.info("Step 3: 开始逐表迁移")
    stats: Dict[str, Dict[str, int]] = {}
    start = time.time()
    for name, model_cls in ALL_TABLE_REGISTRY.items():
        rows = read_sqlite_table(sqlite_engine, model_cls)
        sqlite_count = len(rows)
        try:
            written = write_postgres_table(
                pg_engine, model_cls, rows, args.batch_size
            )
        except Exception as e:
            logger.error(f"  [FAIL] {model_cls.__tablename__}: {e}")
            stats[model_cls.__tablename__] = {
                "source": sqlite_count,
                "written": 0,
                "verified": 0,
            }
            continue

        # Step 4: 校验
        verified = 0
        try:
            with pg_engine.connect() as conn:
                verified = conn.execute(
                    text(f'SELECT COUNT(*) FROM "{model_cls.__tablename__}"')
                ).scalar()
        except Exception as e:
            logger.warning(f"  [WARN] 校验失败: {e}")

        stats[model_cls.__tablename__] = {
            "source": sqlite_count,
            "written": written,
            "verified": verified or 0,
        }
        logger.info(
            f"  [{name}] source={sqlite_count}, written={written}, "
            f"verified={verified}"
        )

    elapsed = time.time() - start
    logger.info("=" * 70)
    logger.info("迁移完成（耗时 %.1fs）", elapsed)
    total_source = sum(s["source"] for s in stats.values())
    total_written = sum(s["written"] for s in stats.values())
    total_verified = sum(s["verified"] for s in stats.values())
    logger.info(f"  源总行数:    {total_source}")
    logger.info(f"  写入行数:    {total_written}")
    logger.info(f"  校验行数:    {total_verified}")
    if total_source == total_written == total_verified:
        logger.info("  [OK] 行数完全一致")
        rc = 0
    else:
        logger.warning("  [WARN] 行数不一致，请检查")
        rc = 1

    sqlite_engine.dispose()
    pg_engine.dispose()
    return rc


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
