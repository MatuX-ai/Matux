"""
【P3-D-1】AI 教师持久化迁移工具

从 P3-B JSON 文件迁移到 P3-D SQLAlchemy ORM + SQLite。

用法：
    # 默认迁移（从 data/ 读取 JSON，写入 ai_service.db）
    python -m scripts.migrate_ai_teacher_to_sqlite

    # dry-run 模式（不写入，仅打印报告）
    python -m scripts.migrate_ai_teacher_to_sqlite --dry-run

    # 自定义路径
    python -m scripts.migrate_ai_teacher_to_sqlite \\
        --source-dir data/ \\
        --target-db ai_service.db \\
        --backup-dir data/backup_20261009/

迁移报告：
- 每个 JSON 文件读取条数
- 每个表写入条数
- 损坏/缺失文件警告
- 总耗时

回退：
- 备份 JSON 文件保留在 backup_dir
- 切回 file backend 即可恢复（P3-B 默认）
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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.ai_teacher_persistence import (
    AiTeacherEventHistoryRow,
    AiTeacherLiveSettingRow,
    AiTeacherMemoryRow,
    AiTeacherPersonaRow,
    AiTeacherProfileRow,
    AiTeacherSessionRow,
    AiTeacherUserHistoryRow,
    Base,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# 文件名 → ORM 模型的映射
FILE_TO_MODEL: Dict[str, Any] = {
    "ai_teacher_profiles.json": AiTeacherProfileRow,
    "ai_teacher_sessions.json": AiTeacherSessionRow,
    "ai_teacher_memories.json": AiTeacherMemoryRow,
    "ai_teacher_personas.json": AiTeacherPersonaRow,
    "ai_teacher_live_settings.json": AiTeacherLiveSettingRow,
    "ai_teacher_event_history.json": AiTeacherEventHistoryRow,
    "ai_teacher_user_history.json": AiTeacherUserHistoryRow,
}


def _resolve_target_db_url(target_db: str) -> str:
    """解析目标数据库 URL（统一转 sqlite:///）"""
    if target_db.startswith("sqlite:///") or target_db.startswith("sqlite+aiosqlite:///"):
        return target_db
    # 简单文件名转 sqlite URL
    return f"sqlite:///{Path(target_db).resolve()}"


def _backup_source_files(source_dir: Path, backup_dir: Path, files: list) -> None:
    """备份源 JSON 文件"""
    backup_dir.mkdir(parents=True, exist_ok=True)
    for filename in files:
        src = source_dir / filename
        if src.exists():
            dst = backup_dir / filename
            shutil.copy2(src, dst)
            logger.info(f"  备份 {filename} -> {dst}")


def _read_json_file(path: Path) -> Optional[Dict[str, Any]]:
    """
    读取 JSON 文件，返回顶层 dict

    Returns:
        - None：文件不存在
        - {}：文件存在但为空或损坏（已警告）
        - Dict：正常读取
    """
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        if not raw.strip():
            return {}
        data = json.loads(raw)
        if not isinstance(data, dict):
            logger.warning(f"{path.name} 顶层不是 dict，已跳过")
            return {}
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"{path.name} JSON 损坏：{e}")
        return {}
    except Exception as e:
        logger.warning(f"{path.name} 读取失败：{e}")
        return {}


def _migrate_one_file(
    session_factory: Any,
    model_class: Any,
    data: Dict[str, Any],
    dry_run: bool,
) -> int:
    """迁移一个 JSON 文件到一张表，返回写入条数"""
    if not data:
        logger.info(f"  {model_class.__tablename__}: 0 条（空数据）")
        return 0

    if dry_run:
        logger.info(
            f"  {model_class.__tablename__}: {len(data)} 条（dry-run，未写入）"
        )
        return len(data)

    written = 0
    try:
        with session_factory() as session:
            for key, value in data.items():
                # 检查是否已存在（避免覆盖）
                existing = (
                    session.query(model_class).filter_by(user_id=key).first()
                )
                if existing is None:
                    row = model_class(user_id=key, value=value)
                    session.add(row)
                    written += 1
                else:
                    logger.debug(f"  跳过已存在 key={key}")
            session.commit()
        logger.info(f"  {model_class.__tablename__}: 写入 {written} 条（跳过 {len(data) - written} 条已存在）")
    except Exception as e:
        logger.error(f"  {model_class.__tablename__} 写入失败：{e}")
        raise
    return written


def migrate(
    source_dir: Path,
    target_db: str,
    backup_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    执行迁移

    Returns:
        dict 包含每个文件的迁移条数 + 总耗时
    """
    start_time = time.time()
    target_db_url = _resolve_target_db_url(target_db)

    logger.info(f"{'[DRY-RUN] ' if dry_run else ''}开始迁移 AI 教师持久化数据")
    logger.info(f"  源目录: {source_dir}")
    logger.info(f"  目标 DB: {target_db_url}")
    if backup_dir:
        logger.info(f"  备份目录: {backup_dir}")

    # 1. 备份源 JSON
    if backup_dir and not dry_run:
        existing_files = [
            f for f in FILE_TO_MODEL.keys()
            if (source_dir / f).exists()
        ]
        if existing_files:
            logger.info(f"备份 {len(existing_files)} 个 JSON 文件...")
            _backup_source_files(source_dir, backup_dir, existing_files)

    # 2. 创建目标数据库 schema
    target_engine = create_engine(target_db_url)
    if not dry_run:
        # 仅迁移 ai_teacher_persistence 模型（不影响全局 schema）
        Base.metadata.create_all(target_engine)
    target_session_factory = sessionmaker(bind=target_engine)

    # 3. 逐文件迁移
    report: Dict[str, Any] = {
        "files": {},
        "total_written": 0,
        "elapsed_seconds": 0.0,
        "dry_run": dry_run,
    }

    for filename, model_class in FILE_TO_MODEL.items():
        json_path = source_dir / filename
        data = _read_json_file(json_path)

        if data is None:
            logger.info(f"  {filename}: 文件不存在，跳过")
            report["files"][filename] = {"status": "missing", "written": 0}
            continue

        logger.info(f"  {filename}: 读取 {len(data)} 条")
        try:
            written = _migrate_one_file(
                target_session_factory, model_class, data, dry_run
            )
            report["files"][filename] = {
                "status": "ok",
                "read": len(data),
                "written": written,
            }
            report["total_written"] += written
        except Exception as e:
            report["files"][filename] = {
                "status": "error",
                "error": str(e),
                "read": len(data),
                "written": 0,
            }

    # 4. 关闭连接
    target_engine.dispose()

    elapsed = time.time() - start_time
    report["elapsed_seconds"] = round(elapsed, 3)

    logger.info(
        f"{'[DRY-RUN] ' if dry_run else ''}迁移完成："
        f"{report['total_written']} 条写入，{elapsed:.3f}s"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="P3-D-1 AI 教师持久化 JSON -> SQLite 迁移工具"
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=Path("data"),
        help="源 JSON 目录（默认: data/）",
    )
    parser.add_argument(
        "--target-db",
        type=str,
        default="ai_service.db",
        help="目标 SQLite DB 路径（默认: ai_service.db）",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="备份目录（默认: data/backup_<timestamp>/）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅打印报告，不写入数据库",
    )
    args = parser.parse_args()

    if not args.source_dir.exists():
        logger.error(f"源目录不存在：{args.source_dir}")
        return 1

    backup_dir = args.backup_dir
    if backup_dir is None and not args.dry_run:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = args.source_dir / f"backup_{ts}"

    try:
        report = migrate(
            source_dir=args.source_dir,
            target_db=args.target_db,
            backup_dir=backup_dir,
            dry_run=args.dry_run,
        )
        print("\n" + "=" * 60)
        print("迁移报告")
        print("=" * 60)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        logger.error(f"迁移失败：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())