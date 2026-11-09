"""
【P3-D-1】数据迁移工具测试

覆盖 scripts/migrate_ai_teacher_to_sqlite.py：
- 完整迁移（7 个 JSON → 7 张表）
- dry-run 不写数据库
- 备份目录创建
- 损坏 JSON 跳过
- 回读一致性
"""

import json
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from models.ai_teacher_persistence import (
    AiTeacherEventHistoryRow,
    AiTeacherProfileRow,
    AiTeacherUserHistoryRow,
)
from scripts.migrate_ai_teacher_to_sqlite import (
    FILE_TO_MODEL,
    _read_json_file,
    migrate,
)


# ==================== Fixtures ====================


@pytest.fixture
def source_dir(tmp_path):
    """准备临时源 JSON 目录（含 7 个文件）"""
    src = tmp_path / "source"
    src.mkdir()

    test_data = {
        "ai_teacher_profiles.json": {
            "user_1": {"name": "Alice", "grade": "G7"},
            "user_2": {"name": "Bob", "grade": "G8"},
        },
        "ai_teacher_sessions.json": {
            "user_1": {"session_id": "s1", "context": "math"},
        },
        "ai_teacher_memories.json": {
            "user_1": {"long_term": ["fact1", "fact2"]},
        },
        "ai_teacher_personas.json": {
            "user_1": {"tone": "friendly", "style": "visual"},
        },
        "ai_teacher_live_settings.json": {
            "user_1": {"celebration_enabled": True},
        },
        "ai_teacher_event_history.json": {
            "records": [
                {"type": "celebration", "payload": {"title": "T1"}},
            ],
        },
        "ai_teacher_user_history.json": {
            "42": [
                {"event_type": "nudge", "payload": {"message": "M1"}},
            ],
        },
    }

    for filename, data in test_data.items():
        (src / filename).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return src


@pytest.fixture
def empty_source(tmp_path):
    """空目录（无任何 JSON）"""
    src = tmp_path / "empty_source"
    src.mkdir()
    return src


@pytest.fixture
def partial_source(tmp_path):
    """只含部分 JSON 文件 + 损坏文件"""
    src = tmp_path / "partial_source"
    src.mkdir()

    # 正常文件
    (src / "ai_teacher_profiles.json").write_text(
        json.dumps({"user_1": {"name": "Alice"}}),
        encoding="utf-8",
    )
    # 损坏 JSON
    (src / "ai_teacher_sessions.json").write_text(
        "{invalid json: broken",
        encoding="utf-8",
    )
    # 空文件
    (src / "ai_teacher_memories.json").write_text(
        "",
        encoding="utf-8",
    )

    return src


# ==================== _read_json_file 单元测试 ====================


class TestReadJsonFile:
    """_read_json_file 错误处理"""

    def test_missing_file_returns_none(self, tmp_path):
        result = _read_json_file(tmp_path / "nonexistent.json")
        assert result is None

    def test_empty_file_returns_empty_dict(self, tmp_path):
        path = tmp_path / "empty.json"
        path.write_text("", encoding="utf-8")
        assert _read_json_file(path) == {}

    def test_valid_dict(self, tmp_path):
        path = tmp_path / "valid.json"
        path.write_text('{"k1": "v1"}', encoding="utf-8")
        assert _read_json_file(path) == {"k1": "v1"}

    def test_corrupted_json_returns_empty(self, tmp_path):
        path = tmp_path / "broken.json"
        path.write_text("{invalid", encoding="utf-8")
        assert _read_json_file(path) == {}

    def test_top_level_not_dict_returns_empty(self, tmp_path):
        path = tmp_path / "list.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        assert _read_json_file(path) == {}


# ==================== migrate() 集成测试 ====================


class TestMigrateIntegration:
    """完整迁移流程"""

    def test_full_migration_seven_files(self, source_dir, tmp_path):
        """7 个 JSON 文件 → 7 张表完整迁移"""
        target_db = tmp_path / "target.db"
        backup_dir = tmp_path / "backup"

        report = migrate(
            source_dir=source_dir,
            target_db=str(target_db),
            backup_dir=backup_dir,
            dry_run=False,
        )

        # 报告：7 个文件都迁移成功
        assert report["dry_run"] is False
        # profiles:2, sessions:1, memories:1, personas:1, live_settings:1, event_history:1, user_history:1 = 8
        assert report["total_written"] == 8

        # 检查报告里的文件状态
        for filename in FILE_TO_MODEL.keys():
            assert filename in report["files"]
            assert report["files"][filename]["status"] == "ok"

        # 验证 DB 中有表
        engine = create_engine(f"sqlite:///{target_db}")
        conn = engine.connect()
        table_count = conn.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name LIKE 'ai_teacher%'")
        ).scalar()
        assert table_count == 7
        conn.close()
        engine.dispose()

    def test_dry_run_does_not_write(self, source_dir, tmp_path):
        """dry-run 模式不写入数据库"""
        target_db = tmp_path / "dry_run_target.db"
        # 不提供 backup_dir（dry-run 不应备份）
        report = migrate(
            source_dir=source_dir,
            target_db=str(target_db),
            backup_dir=None,
            dry_run=True,
        )

        assert report["dry_run"] is True
        # 数据库文件可能不存在
        assert not target_db.exists() or target_db.stat().st_size < 1024

    def test_backup_creates_copy(self, source_dir, tmp_path):
        """备份目录创建并复制源文件"""
        target_db = tmp_path / "target.db"
        backup_dir = tmp_path / "backup"

        migrate(
            source_dir=source_dir,
            target_db=str(target_db),
            backup_dir=backup_dir,
            dry_run=False,
        )

        # 备份目录应包含所有源文件
        assert backup_dir.exists()
        for filename in FILE_TO_MODEL.keys():
            assert (backup_dir / filename).exists()
            # 内容一致
            original = (source_dir / filename).read_text(encoding="utf-8")
            backup = (backup_dir / filename).read_text(encoding="utf-8")
            assert original == backup

    def test_corrupted_json_skipped(self, partial_source, tmp_path):
        """损坏 JSON 跳过 + 报告"""
        target_db = tmp_path / "target.db"
        report = migrate(
            source_dir=partial_source,
            target_db=str(target_db),
            backup_dir=tmp_path / "backup",
            dry_run=False,
        )

        # profiles: ok, sessions: corrupted (空 dict), memories: empty (空 dict)
        assert report["files"]["ai_teacher_profiles.json"]["status"] == "ok"
        # 损坏 + 空文件都是 dict 但没有内容
        assert report["files"]["ai_teacher_sessions.json"]["read"] == 0
        assert report["files"]["ai_teacher_memories.json"]["read"] == 0


class TestMigrateReadbackConsistency:
    """迁移后从 DB 回读，验证一致性"""

    def test_round_trip_data(self, source_dir, tmp_path):
        target_db = tmp_path / "target.db"
        migrate(
            source_dir=source_dir,
            target_db=str(target_db),
            backup_dir=None,
            dry_run=False,
        )

        # 从 DB 回读
        engine = create_engine(f"sqlite:///{target_db}")
        SessionLocal = sessionmaker(bind=engine)

        with SessionLocal() as session:
            # profiles
            rows = session.query(AiTeacherProfileRow).all()
            profile_dict = {r.user_id: r.value for r in rows}
            assert profile_dict["user_1"]["name"] == "Alice"
            assert profile_dict["user_2"]["grade"] == "G8"

            # event_history
            rows = session.query(AiTeacherEventHistoryRow).all()
            event_dict = {r.user_id: r.value for r in rows}
            assert event_dict["records"][0]["type"] == "celebration"

            # user_history
            rows = session.query(AiTeacherUserHistoryRow).all()
            user_dict = {r.user_id: r.value for r in rows}
            assert user_dict["42"][0]["event_type"] == "nudge"

        engine.dispose()


# ==================== 命令行入口测试 ====================


class TestCLI:
    """命令行入口可调用"""

    def test_dry_run_via_cli(self, source_dir, tmp_path):
        """python -m scripts.migrate_ai_teacher_to_sqlite --dry-run"""
        target_db = tmp_path / "cli_target.db"
        result = subprocess.run(
            [
                sys.executable, "-m", "scripts.migrate_ai_teacher_to_sqlite",
                "--source-dir", str(source_dir),
                "--target-db", str(target_db),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        # dry-run 应成功
        assert result.returncode == 0
        assert "DRY-RUN" in result.stderr or "DRY-RUN" in result.stdout

    def test_missing_source_dir_returns_error(self, tmp_path):
        """源目录不存在返回非 0"""
        nonexistent = tmp_path / "nonexistent"
        result = subprocess.run(
            [
                sys.executable, "-m", "scripts.migrate_ai_teacher_to_sqlite",
                "--source-dir", str(nonexistent),
                "--target-db", str(tmp_path / "out.db"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])