"""
【P3-D-3】PostgreSQL 后端仓储测试

覆盖：
1. 无 session_factory 时的纯内存模式
2. SQLite 兼容路径（测试 JSONB @> 的降级实现）
3. JSONB upsert 路径（ON CONFLICT） - 用 SQLite/MySQL 通用 fallback
4. find_by_jsonb_path 两种 dialect 路径
5. replace_all + clear + flush

在 SQLite 环境下：dialect 降级为 JSON，仍能完整覆盖 PostgresJsonbRepository 行为
"""

import json
import os
import sys
import threading

import pytest

# 保证 backend 根目录在 path
_BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from sqlalchemy import (  # noqa: E501, E402
    create_engine as create_sync_engine,
    text,
)
from sqlalchemy.orm import sessionmaker  # noqa: E501, E402

from cache.repository.postgres import PostgresJsonbRepository  # noqa: E501, E402
from models.ai_teacher_persistence import (  # noqa: E501, E402
    AiTeacherProfileRow,
    get_row_model_by_name,
)
from utils.database import Base  # noqa: E501, E402


# ==================== Fixtures ====================


@pytest.fixture
def sqlite_engine(tmp_path):
    """独立 SQLite 引擎（不污染全局 engine）"""
    db_path = tmp_path / "test_pg_repo.db"
    engine = create_sync_engine(f"sqlite:///{db_path}", pool_pre_ping=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(sqlite_engine):
    """基于 SQLite 的 sessionmaker（用于测试 SQLite-fallback 路径）"""
    return sessionmaker(bind=sqlite_engine, expire_on_commit=False)


@pytest.fixture
def memory_repo():
    """纯内存模式（无 session_factory）"""
    return PostgresJsonbRepository(name="profiles", session_factory=None)


@pytest.fixture
def sqlite_repo(session_factory):
    """SQLite 模式（验证 SQLite-fallback 路径）"""
    return PostgresJsonbRepository(
        name="profiles", session_factory=session_factory
    )


# ==================== 1. 纯内存模式 ====================


class TestMemoryOnlyMode:
    """无 session_factory 时应工作于纯内存模式"""

    def test_init_no_factory(self, memory_repo):
        assert memory_repo is not None

    def test_get_set_in_memory(self, memory_repo):
        memory_repo.set("user_1", {"name": "Alice", "age": 18})
        assert memory_repo.get("user_1") == {"name": "Alice", "age": 18}

    def test_has_keys_values(self, memory_repo):
        memory_repo.set("a", 1)
        memory_repo.set("b", 2)
        assert memory_repo.has("a") is True
        assert "a" in memory_repo
        assert memory_repo.keys() == ["a", "b"] or set(memory_repo.keys()) == {"a", "b"}
        assert 1 in memory_repo.values()
        assert len(memory_repo) == 2

    def test_delete(self, memory_repo):
        memory_repo.set("a", 1)
        assert memory_repo.delete("a") is True
        assert memory_repo.delete("a") is False
        assert memory_repo.get("a") is None

    def test_clear(self, memory_repo):
        memory_repo.set("a", 1)
        memory_repo.clear()
        assert len(memory_repo) == 0

    def test_replace_all(self, memory_repo):
        memory_repo.replace_all({"x": 1, "y": 2})
        assert memory_repo.get("x") == 1
        assert memory_repo.get("y") == 2

    def test_getitem_raises(self, memory_repo):
        with pytest.raises(KeyError):
            _ = memory_repo["nonexistent"]

    def test_iter(self, memory_repo):
        memory_repo.set("a", 1)
        memory_repo.set("b", 2)
        keys = [k for k in memory_repo]
        assert set(keys) == {"a", "b"}

    def test_snapshot(self, memory_repo):
        memory_repo.set("a", {"nested": True})
        snap = memory_repo.snapshot()
        assert snap == {"a": {"nested": True}}
        # 修改原数据不影响 snapshot
        memory_repo.set("a", {"nested": False})
        assert snap["a"]["nested"] is True

    def test_default_value(self, memory_repo):
        assert memory_repo.get("nonexistent", "default") == "default"


# ==================== 2. SQLite 兼容路径 ====================


class TestSqliteFallback:
    """SQLite 上 PostgresJsonbRepository 走通用 fallback 路径"""

    def test_init_loads_existing_rows(self, session_factory, sqlite_engine):
        """先在表中插入若干行，再 init 应加载到内存"""
        with sqlite_engine.connect() as conn:
            conn.execute(
                text(
                    'INSERT INTO "ai_teacher_profiles" '
                    "(user_id, value, updated_at, created_at) "
                    "VALUES (:u, :v, :ts, :ts2)"
                ),
                {
                    "u": "user_x",
                    "v": json.dumps({"name": "X"}),
                    "ts": "2024-01-01 00:00:00",
                    "ts2": "2024-01-01 00:00:00",
                },
            )
            conn.commit()

        repo = PostgresJsonbRepository(
            name="profiles", session_factory=session_factory
        )
        assert repo.get("user_x") == {"name": "X"}
        assert len(repo) == 1

    def test_set_persists_to_db(self, sqlite_repo, session_factory):
        sqlite_repo.set("u1", {"a": 1})
        # 读 DB
        with session_factory() as s:
            row = (
                s.query(AiTeacherProfileRow).filter_by(user_id="u1").first()
            )
            assert row is not None
            assert row.value == {"a": 1}

    def test_set_updates_existing(self, sqlite_repo, session_factory):
        sqlite_repo.set("u1", {"v": 1})
        sqlite_repo.set("u1", {"v": 2})
        with session_factory() as s:
            rows = s.query(AiTeacherProfileRow).filter_by(user_id="u1").all()
            assert len(rows) == 1
            assert rows[0].value == {"v": 2}

    def test_delete_persists(self, sqlite_repo, session_factory):
        sqlite_repo.set("u1", 1)
        assert sqlite_repo.delete("u1") is True
        with session_factory() as s:
            row = s.query(AiTeacherProfileRow).filter_by(user_id="u1").first()
            assert row is None

    def test_clear_truncates(self, sqlite_repo, session_factory):
        for i in range(5):
            sqlite_repo.set(f"u{i}", i)
        assert len(sqlite_repo) == 5
        sqlite_repo.clear()
        with session_factory() as s:
            count = s.query(AiTeacherProfileRow).count()
            assert count == 0

    def test_replace_all_replaces(self, sqlite_repo, session_factory):
        sqlite_repo.set("old1", 1)
        sqlite_repo.replace_all({"new1": "a", "new2": "b"})
        with session_factory() as s:
            count = s.query(AiTeacherProfileRow).count()
            assert count == 2
        assert sqlite_repo.get("old1") is None
        assert sqlite_repo.get("new1") == "a"


# ==================== 3. JSONB Path Query（SQLite 降级） ====================


class TestJsonbPathQuery:
    """find_by_jsonb_path 的 SQLite 降级路径"""

    def test_find_by_simple_path(self, sqlite_repo):
        sqlite_repo.set("u1", {"status": "active", "tier": "vip"})
        sqlite_repo.set("u2", {"status": "active", "tier": "regular"})
        sqlite_repo.set("u3", {"status": "inactive", "tier": "vip"})

        result = sqlite_repo.find_by_jsonb_path({"status": "active"})
        assert {"u1", "u2"}.issubset(set(sqlite_repo.keys()))
        # SQLite 降级：直接遍历内存
        assert len(result) == 2

    def test_find_by_multi_path(self, sqlite_repo):
        sqlite_repo.set("u1", {"status": "active", "tier": "vip"})
        sqlite_repo.set("u2", {"status": "active", "tier": "regular"})

        result = sqlite_repo.find_by_jsonb_path(
            {"status": "active", "tier": "vip"}
        )
        assert len(result) == 1
        assert result[0] == {"status": "active", "tier": "vip"}

    def test_find_no_match(self, sqlite_repo):
        sqlite_repo.set("u1", {"status": "active"})
        result = sqlite_repo.find_by_jsonb_path({"status": "nope"})
        assert result == []

    def test_find_on_empty(self, sqlite_repo):
        result = sqlite_repo.find_by_jsonb_path({"a": 1})
        assert result == []

    def test_find_non_dict_value_skipped(self, sqlite_repo):
        sqlite_repo.set("u1", "not a dict")
        sqlite_repo.set("u2", {"a": 1})
        result = sqlite_repo.find_by_jsonb_path({"a": 1})
        assert len(result) == 1


# ==================== 4. flush 跨进程同步 ====================


class TestFlush:
    """flush 强制从 DB 重新加载（跨进程同步用）"""

    def test_flush_reloads(self, session_factory, sqlite_engine):
        repo = PostgresJsonbRepository(
            name="profiles", session_factory=session_factory
        )
        # 进程 A 写入
        repo.set("u1", 1)

        # 进程 B 直接改 DB
        with sqlite_engine.connect() as conn:
            conn.execute(
                text(
                    'INSERT OR REPLACE INTO "ai_teacher_profiles" '
                    "(user_id, value, updated_at, created_at) "
                    "VALUES (:u, :v, :ts, :ts2)"
                ),
                {
                    "u": "u2",
                    "v": json.dumps(999),
                    "ts": "2024-01-01 00:00:00",
                    "ts2": "2024-01-01 00:00:00",
                },
            )
            conn.commit()

        # flush 拉取
        repo.flush()
        assert repo.get("u2") == 999


# ==================== 5. 线程安全 ====================


class TestThreadSafety:
    """多线程并发读写"""

    def test_concurrent_set(self, memory_repo):
        def writer(i: int):
            memory_repo.set(f"u{i}", i)

        threads = [
            threading.Thread(target=writer, args=(i,)) for i in range(50)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(memory_repo) == 50

    def test_concurrent_replace_all(self, memory_repo):
        def writer(i: int):
            memory_repo.replace_all({f"u{i}": i})

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # 最终只剩一个 key
        assert len(memory_repo) == 1


# ==================== 6. 工厂注册 ====================


class TestFactoryIntegration:
    """与 get_row_model_by_name 集成"""

    def test_all_7_repos_constructible_memory(self):
        for name in [
            "profiles",
            "sessions",
            "memories",
            "personas",
            "live_settings",
            "event_history",
            "user_history",
        ]:
            repo = PostgresJsonbRepository(name=name, session_factory=None)
            assert repo is not None
            assert len(repo) == 0

    def test_unknown_repo_raises(self):
        with pytest.raises(KeyError):
            get_row_model_by_name("nonexistent_repo")

    def test_event_history_list_storage(self, memory_repo):
        """event_history 仓库存 list 模拟 P3-B 行为"""
        memory_repo.set("records", [{"id": 1, "type": "x"}])
        assert memory_repo.get("records") == [{"id": 1, "type": "x"}]
        # 追加
        events = memory_repo.get("records")
        events.append({"id": 2, "type": "y"})
        memory_repo.set("records", events)
        assert len(memory_repo.get("records")) == 2


# ==================== 7. 边界 ====================


class TestEdgeCases:
    """边界场景"""

    def test_set_none_value(self, memory_repo):
        memory_repo.set("u1", None)
        assert memory_repo.get("u1") is None
        assert memory_repo.has("u1") is True

    def test_set_complex_value(self, memory_repo):
        v = {
            "list": [1, 2, 3],
            "nested": {"a": {"b": {"c": "deep"}}},
            "bool": True,
            "null": None,
        }
        memory_repo.set("u1", v)
        assert memory_repo.get("u1") == v

    def test_replace_all_empty(self, memory_repo):
        memory_repo.set("a", 1)
        memory_repo.replace_all({})
        assert len(memory_repo) == 0

    def test_flush_on_no_factory(self, memory_repo):
        # 不应抛异常
        memory_repo.flush()
        assert len(memory_repo) == 0

    def test_delete_nonexistent(self, memory_repo):
        assert memory_repo.delete("nope") is False


# ==================== 8. 多次构造 ====================


class TestRepeatedConstruction:
    """验证两次构造会重新从 DB 加载（无残留内存）"""

    def test_second_init_loads_db_changes(self, session_factory, sqlite_engine):
        r1 = PostgresJsonbRepository(
            name="profiles", session_factory=session_factory
        )
        r1.set("u1", "alpha")
        del r1

        # 进程外修改
        with sqlite_engine.connect() as conn:
            conn.execute(
                text(
                    'UPDATE "ai_teacher_profiles" SET value=:v '
                    "WHERE user_id=:u"
                ),
                {"u": "u1", "v": json.dumps("beta")},
            )
            conn.commit()

        r2 = PostgresJsonbRepository(
            name="profiles", session_factory=session_factory
        )
        assert r2.get("u1") == "beta"
