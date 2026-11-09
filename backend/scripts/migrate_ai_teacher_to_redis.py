"""
【P3-D-2】AI 教师持久化迁移工具（迁移到 Redis）

支持两种源后端：
- file：P3-B JSON 文件（backend/data/ai_teacher_*.json）
- sql ：P3-D-1 SQLite 数据库（models.ai_teacher_persistence.*Row）

目标后端：
- redis：Redis Hash（Key: ai_teacher:{table}:kv，Field: user_id，Value: JSON）

用法：
    # 默认迁移（从 file 迁移到默认 Redis）
    python -m scripts.migrate_ai_teacher_to_redis

    # dry-run 模式（仅打印报告，不写入 Redis）
    python -m scripts.migrate_ai_teacher_to_redis --dry-run

    # 从 SQLite 迁移到 Redis
    python -m scripts.migrate_ai_teacher_to_redis --source-backend sql

    # 自定义 Redis URL + db
    python -m scripts.migrate_ai_teacher_to_redis \\
        --redis-url redis://127.0.0.1:6379/2 \\
        --backup-dir data/backup_to_redis_20261009/

    # 仅校验（从 Redis 读回并比对源数据，不写入）
    python -m scripts.migrate_ai_teacher_to_redis --verify-only

迁移报告：
- 每张表读取条数、写入条数、校验耗时
- 损坏/缺失文件警告
- 总耗时

回退：
- P3-B / P3-D-1 默认 file backend 即可恢复
- 备份 JSON 保留在 backup_dir
"""

import argparse
import json
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# 7 张表（与 cache/repository/factory.py REPOSITORY_REGISTRY 一致）
TABLE_TO_JSON_FILE = {
    "profiles": "ai_teacher_profiles.json",
    "sessions": "ai_teacher_sessions.json",
    "memories": "ai_teacher_memories.json",
    "personas": "ai_teacher_personas.json",
    "live_settings": "ai_teacher_live_settings.json",
    "event_history": "ai_teacher_event_history.json",
    "user_history": "ai_teacher_user_history.json",
}


# ============================================================
# Source backends
# ============================================================


def _read_file_source(table: str, source_dir: Path) -> Optional[Dict[str, Any]]:
    """从 JSON 文件读取"""
    json_name = TABLE_TO_JSON_FILE[table]
    path = source_dir / json_name
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            return {}
        data = json.loads(raw)
        if not isinstance(data, dict):
            logger.warning(f"  {json_name} 顶层不是 dict，已跳过")
            return {}
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"  {json_name} JSON 损坏：{e}")
        return {}
    except Exception as e:
        logger.warning(f"  {json_name} 读取失败：{e}")
        return {}


def _read_sql_source(table: str) -> Optional[Dict[str, Any]]:
    """从 SQLite + SQLAlchemy 读取（P3-D-1 默认 DB）"""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from models.ai_teacher_persistence import get_row_model_by_name
        from utils.database import SQLALCHEMY_DATABASE_URL
    except Exception as e:
        logger.error(f"无法导入 SQLAlchemy 模型：{e}")
        return None

    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        session_factory = sessionmaker(bind=engine)
        model = get_row_model_by_name(table)
        with session_factory() as session:
            rows = session.query(model).all()
            return {row.user_id: row.value for row in rows}
    except Exception as e:
        logger.warning(f"  SQL {table} 读取失败：{e}")
        return None


# ============================================================
# Target backend (Redis)
# ============================================================


def _create_redis_client(redis_url: str):
    """创建 Redis 客户端"""
    try:
        import redis
        client = redis.Redis.from_url(redis_url, decode_responses=True)
        client.ping()
        return client
    except Exception as e:
        logger.error(f"无法连接 Redis {redis_url}：{e}")
        return None


def _write_to_redis(
    redis_client: Any,
    table: str,
    data: Dict[str, Any],
    dry_run: bool,
) -> int:
    """
    写入一张表到 Redis Hash（ai_teacher:{table}:kv）

    Returns:
        写入条数
    """
    from cache.repository.redis import DEFAULT_KEY_PREFIX

    if not data:
        return 0
    if dry_run:
        return len(data)

    hash_key = f"{DEFAULT_KEY_PREFIX}:{table}:kv"
    written = 0
    pipe = redis_client.pipeline()
    pipe.delete(hash_key)
    for user_id, value in data.items():
        try:
            payload = json.dumps(value, default=str)
            # 单字段 HSET（兼容 Redis 3.2 / 4.x / 5.x）
            pipe.hset(hash_key, user_id, payload)
            written += 1
        except Exception as e:
            logger.warning(f"    序列化失败 user_id={user_id}: {e}")
    pipe.execute()
    return written


def _read_from_redis(
    redis_client: Any,
    table: str,
) -> Dict[str, Any]:
    """
    从 Redis Hash 回读

    Returns:
        Dict[user_id, value]；空 dict 表示无数据
    """
    from cache.repository.redis import DEFAULT_KEY_PREFIX

    hash_key = f"{DEFAULT_KEY_PREFIX}:{table}:kv"
    try:
        raw = redis_client.hgetall(hash_key)
        return {k: json.loads(v) for k, v in raw.items()}
    except Exception as e:
        logger.warning(f"  Redis {hash_key} 读取失败：{e}")
        return {}


# ============================================================
# Backup
# ============================================================


def _backup_file_source(source_dir: Path, backup_dir: Path) -> int:
    """备份源 JSON 文件"""
    backup_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for fname in TABLE_TO_JSON_FILE.values():
        src = source_dir / fname
        if src.exists():
            shutil.copy2(src, backup_dir / fname)
            logger.info(f"  备份 {fname} -> {backup_dir / fname}")
            n += 1
    return n


# ============================================================
# Main migration
# ============================================================


def migrate(
    source_backend: str,
    source_dir: Path,
    redis_url: str,
    backup_dir: Optional[Path] = None,
    dry_run: bool = False,
    verify_only: bool = False,
) -> Dict[str, Any]:
    """
    执行迁移

    Args:
        source_backend: "file" 或 "sql"
        source_dir: JSON 源目录（仅 file 模式使用）
        redis_url: 目标 Redis URL
        backup_dir: 备份目录（默认自动生成）
        dry_run: 仅打印报告不写入
        verify_only: 仅校验 Redis 数据与源数据是否一致
    """
    start_time = time.time()

    logger.info(
        f"{'[DRY-RUN] ' if dry_run else ''}{'[VERIFY-ONLY] ' if verify_only else ''}"
        f"开始迁移 AI 教师持久化数据 → Redis"
    )
    logger.info(f"  源后端: {source_backend}")
    if source_backend == "file":
        logger.info(f"  源目录: {source_dir}")
    logger.info(f"  目标 Redis: {redis_url}")
    if backup_dir:
        logger.info(f"  备份目录: {backup_dir}")

    # 0. 备份（仅 file 源 + 非 dry-run + 非 verify-only）
    if (
        source_backend == "file"
        and backup_dir
        and not dry_run
        and not verify_only
    ):
        existing = [f for f in TABLE_TO_JSON_FILE.values() if (source_dir / f).exists()]
        if existing:
            logger.info(f"备份 {len(existing)} 个 JSON 文件...")
            _backup_file_source(source_dir, backup_dir)

    # 1. 创建 Redis 客户端（verify_only 也需要）
    redis_client = _create_redis_client(redis_url)
    if redis_client is None:
        return {"status": "error", "error": "Redis 连接失败"}

    report: Dict[str, Any] = {
        "source_backend": source_backend,
        "source_dir": str(source_dir) if source_backend == "file" else None,
        "redis_url": redis_url,
        "dry_run": dry_run,
        "verify_only": verify_only,
        "tables": {},
        "total_read": 0,
        "total_written": 0,
        "total_verified": 0,
        "mismatches": 0,
        "elapsed_seconds": 0.0,
    }

    try:
        # 2. 逐表处理
        for table in TABLE_TO_JSON_FILE.keys():
            logger.info(f"\n=== {table} ===")

            # 读取源
            t0 = time.time()
            if source_backend == "file":
                src_data = _read_file_source(table, source_dir)
            else:
                src_data = _read_sql_source(table)

            if src_data is None:
                logger.info(f"  源数据不存在，跳过")
                report["tables"][table] = {
                    "status": "missing",
                    "read": 0,
                    "written": 0,
                }
                continue

            n_read = len(src_data)
            report["total_read"] += n_read
            logger.info(f"  读取: {n_read} 条")

            # 写入 Redis
            if not verify_only:
                t1 = time.time()
                n_written = _write_to_redis(redis_client, table, src_data, dry_run)
                report["total_written"] += n_written
                write_secs = time.time() - t1
                if dry_run:
                    logger.info(f"  [DRY-RUN] 计划写入: {n_written} 条")
                else:
                    logger.info(f"  写入 Redis: {n_written} 条 ({write_secs:.3f}s)")
            else:
                n_written = n_read  # verify_only 不写入

            # 回读校验
            t2 = time.time()
            dst_data = _read_from_redis(redis_client, table)
            n_verified = len(dst_data)
            report["total_verified"] += n_verified
            logger.info(f"  回读: {n_verified} 条 ({time.time() - t2:.3f}s)")

            # 一致性比对（src vs dst）
            mismatches = _diff_keys(src_data, dst_data)
            if mismatches:
                logger.warning(f"  ⚠️  {len(mismatches)} 个 key 不一致：{mismatches[:5]}...")
                report["mismatches"] += len(mismatches)
            else:
                logger.info(f"  ✅ 一致性校验通过（{n_verified} 条）")

            report["tables"][table] = {
                "status": "ok",
                "read": n_read,
                "written": n_written,
                "verified": n_verified,
                "mismatches": len(mismatches),
            }

        elapsed = time.time() - start_time
        report["elapsed_seconds"] = round(elapsed, 3)

        logger.info(
            f"\n{'[DRY-RUN] ' if dry_run else ''}{'[VERIFY-ONLY] ' if verify_only else ''}"
            f"完成：读 {report['total_read']} / 写 {report['total_written']} / "
            f"校验 {report['total_verified']} / 不一致 {report['mismatches']} | "
            f"{elapsed:.3f}s"
        )

    finally:
        try:
            redis_client.close()
        except Exception:
            pass

    return report


def _diff_keys(src: Dict[str, Any], dst: Dict[str, Any]) -> list:
    """
    比对 src vs dst 的 key 集合差异

    Returns:
        不一致的 key 列表（src 中存在但 dst 中不存在 + 反之）
    """
    if not src and not dst:
        return []
    src_keys = set(src.keys())
    dst_keys = set(dst.keys())
    return sorted(src_keys ^ dst_keys)  # 对称差集


# ============================================================
# CLI
# ============================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="P3-D-2 AI 教师持久化 file/sql → Redis 迁移工具"
    )
    parser.add_argument(
        "--source-backend",
        choices=["file", "sql"],
        default="file",
        help="源后端（默认: file）",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("data"),
        help="源 JSON 目录（仅 file 模式，默认: data/）",
    )
    parser.add_argument(
        "--redis-url",
        type=str,
        default="redis://127.0.0.1:6379/0",
        help="目标 Redis URL（默认: redis://127.0.0.1:6379/0）",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="备份目录（默认: data/backup_to_redis_<timestamp>/）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印报告，不写入 Redis",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="仅校验 Redis 与源数据一致性，不写入",
    )
    args = parser.parse_args()

    if args.source_backend == "file" and not args.source_dir.exists():
        logger.error(f"源目录不存在：{args.source_dir}")
        return 1

    backup_dir = args.backup_dir
    if (
        backup_dir is None
        and args.source_backend == "file"
        and not args.dry_run
        and not args.verify_only
    ):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = args.source_dir / f"backup_to_redis_{ts}"

    try:
        report = migrate(
            source_backend=args.source_backend,
            source_dir=args.source_dir,
            redis_url=args.redis_url,
            backup_dir=backup_dir,
            dry_run=args.dry_run,
            verify_only=args.verify_only,
        )
        print("\n" + "=" * 60)
        print("迁移报告")
        print("=" * 60)
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        # 出现 mismatches 返回 2
        if report.get("mismatches", 0) > 0:
            return 2
        return 0
    except Exception as e:
        logger.error(f"迁移失败：{e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
