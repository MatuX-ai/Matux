"""
【P3-D-1】SqlAlchemyRepository 单元测试

覆盖 SqlAlchemyRepository 与 FileJsonRepository 行为对齐：
- 基本 CRUD（set/get/delete/has/keys/values/items/len）
- snapshot / replace_all
- 跨进程持久化（DB reload）
- 线程安全
- 优雅降级（DB 不可用）
- 7 张表各一张端到端测试
"""

import threading

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cache.ai_teacher_persistence import (
    SqlAlchemyRepository,
    flush_all_repos,
    get_profiles_repo,
    get_sessions_repo,
    reset_all_repos_for_testing,
)
from models.ai_teacher_persistence import (
    Base,
    AiTeacherEventHistoryRow,
    AiTeacherLiveSettingRow,
    AiTeacherMemoryRow,
    AiTeacherPersonaRow,
    AiTeacherProfileRow,
    AiTeacherSessionRow,
    AiTeacherUserHistoryRow,
)


# ==================== Fixtures ====================


@pytest.fixture
def tmp_db_path(tmp_path):
    """临时 SQLite DB 文件路径"""
    return tmp_path / "test_ai_teacher.db"


@pytest.fixture
def tmp_db_url(tmp_db_path, monkeypatch):
    """临时 SQLite URL + 创建表 + 设置环境变量"""
    db_url = f"sqlite:///{tmp_db_path}"
    # 创建临时数据库的 schema
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    engine.dispose()

    # monkey-patch SyncSessionLocal 以使用临时数据库
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_db_path}")
    yield db_url

    # 清理全局单例
    reset_all_repos_for_testing()


@pytest.fixture
def clean_globals():
    """每个测试前后清理全局单例"""
    reset_all_repos_for_testing()
    yield
    reset_all_repos_for_testing()


# ==================== SqlAlchemyRepository 基本行为 ====================


class TestSqlAlchemyRepositoryBasics:
    """SqlAlchemyRepository 基本 CRUD（与 FileJsonRepository 行为一致）"""

    def test_set_and_get(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        repo.set("k1", {"a": 1, "b": [1, 2, 3]})
        assert repo.get("k1") == {"a": 1, "b": [1, 2, 3]}

    def test_get_missing_returns_none(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        assert repo.get("nonexistent") is None

    def test_get_with_default(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        assert repo.get("missing", default="fallback") == "fallback"

    def test_delete(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        repo.set("k1", {"a": 1})
        assert repo.delete("k1") is True
        assert repo.get("k1") is None

    def test_delete_missing(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        assert repo.delete("nonexistent") is False

    def test_has(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        repo.set("k1", {"a": 1})
        assert repo.has("k1") is True
        assert repo.has("missing") is False

    def test_keys_values_items(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        repo.set("a", 1)
        repo.set("b", 2)
        repo.set("c", 3)
        assert sorted(repo.keys()) == ["a", "b", "c"]
        assert sorted(repo.values()) == [1, 2, 3]
        keys_items = sorted(k for k, _ in repo.items())
        assert keys_items == ["a", "b", "c"]

    def test_len(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        assert len(repo) == 0
        repo.set("a", 1)
        repo.set("b", 2)
        assert len(repo) == 2

    def test_clear(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        repo.set("a", 1)
        repo.set("b", 2)
        repo.clear()
        assert len(repo) == 0


# ==================== 持久化 / 重载 ====================


class TestSqlAlchemyRepositoryPersistence:
    """DB 持久化与跨实例 reload"""

    def test_data_persists_across_instances(self, tmp_db_url, clean_globals):
        """第一次实例写入 → 第二次实例能读到"""
        repo1 = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        repo1.set("user_1", {"name": "Alice", "age": 30})
        repo1.set("user_2", {"name": "Bob"})
        # 不调用 flush —— SQL 模式 set 已即时落库

        # 第二次实例化（模拟重启）
        repo2 = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        assert repo2.get("user_1") == {"name": "Alice", "age": 30}
        assert repo2.get("user_2") == {"name": "Bob"}
        assert len(repo2) == 2

    def test_persistence_with_complex_data(self, tmp_db_url, clean_globals):
        """包含列表、嵌套 dict、Unicode 字符串"""
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        complex_value = {
            "list": [1, 2, {"nested": True}],
            "dict": {"a": {"b": {"c": "deep"}}},
            "string": "中文测试 🎉",
        }
        repo.set("data", complex_value)

        repo2 = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        loaded = repo2.get("data")
        assert loaded["list"] == [1, 2, {"nested": True}]
        assert loaded["dict"]["a"]["b"]["c"] == "deep"
        assert loaded["string"] == "中文测试 🎉"

    def test_replace_all(self, tmp_db_url, clean_globals):
        """replace_all 整体替换"""
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        repo.set("old_key", "old_value")
        repo.replace_all({"new_a": 1, "new_b": 2})

        assert repo.get("old_key") is None
        assert repo.get("new_a") == 1
        assert repo.get("new_b") == 2
        assert len(repo) == 2

    def test_snapshot_is_isolated(self, tmp_db_url, clean_globals):
        """snapshot 返回独立快照"""
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        repo.set("k1", {"value": [1, 2, 3]})
        snap = repo.snapshot()
        snap["k1"]["value"].append(999)
        snap["k2"] = "new"
        # 修改 snapshot 不应影响 repo
        assert repo.get("k1") == {"value": [1, 2, 3]}
        assert repo.has("k2") is False


# ==================== 线程安全 ====================


class TestSqlAlchemyRepositoryThreadSafety:
    """并发写入不丢数据"""

    def test_concurrent_writes(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        num_writers = 5
        writes_per_writer = 20

        def writer(writer_id: int) -> None:
            for i in range(writes_per_writer):
                repo.set(f"w{writer_id}_k{i}", {"writer": writer_id, "i": i})

        threads = [
            threading.Thread(target=writer, args=(i,))
            for i in range(num_writers)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected = num_writers * writes_per_writer
        assert len(repo) == expected

        # 验证 DB 持久化
        repo2 = SqlAlchemyRepository("profiles", session_factory=Session(test_db_url=tmp_db_url))
        assert len(repo2) == expected


# ==================== 优雅降级 ====================


class TestSqlAlchemyRepositoryGracefulDegradation:
    """DB 不可用时内存仍可用"""

    def test_invalid_db_path_does_not_crash(self):
        """DB 不可用时仍可读写（仅内存）"""
        # 使用不存在的目录

        # 用不存在的目录构造无效 URL
        bad_factory = sessionmaker(bind=create_engine("sqlite:///:memory:"))
        repo = SqlAlchemyRepository("profiles", session_factory=bad_factory)

        # 内存写入应可用
        repo.set("k1", {"a": 1})
        assert repo.get("k1") == {"a": 1}
        # 删除也可用
        repo.delete("k1")
        assert repo.get("k1") is None


# ==================== 7 张表端到端测试 ====================


class TestAllTablesEndToEnd:
    """每张表一个完整的 set/get 流程"""

    @pytest.mark.parametrize("repo_name,model_class", [
        ("profiles", AiTeacherProfileRow),
        ("sessions", AiTeacherSessionRow),
        ("memories", AiTeacherMemoryRow),
        ("personas", AiTeacherPersonaRow),
        ("live_settings", AiTeacherLiveSettingRow),
        ("event_history", AiTeacherEventHistoryRow),
        ("user_history", AiTeacherUserHistoryRow),
    ])
    def test_table_set_and_get(self, tmp_db_url, clean_globals, repo_name, model_class):
        repo = SqlAlchemyRepository(
            repo_name,
            session_factory=Session(test_db_url=tmp_db_url),
        )
        test_key = "test_user_42"
        test_value = {"name": "Alice", "score": 95, "tags": ["vip"]}
        repo.set(test_key, test_value)

        # 同实例读
        assert repo.get(test_key) == test_value

        # 重载验证持久化
        repo2 = SqlAlchemyRepository(
            repo_name,
            session_factory=Session(test_db_url=tmp_db_url),
        )
        assert repo2.get(test_key) == test_value


# ==================== event_history KV 模式 ====================


class TestEventHistoryKVPattern:
    """event_history 用固定 key "records" 存整个 list（与 P3-B 兼容）"""

    def test_event_history_replace_all(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository(
            "event_history",
            session_factory=Session(test_db_url=tmp_db_url),
        )
        events = [
            {"type": "celebration", "payload": {"title": "T1"}},
            {"type": "nudge", "payload": {"message": "M1"}},
        ]
        # 模拟 event_bus._event_history_repo.replace_all({"records": [...]})
        repo.replace_all({"records": events})

        loaded = repo.get("records")
        assert loaded == events

        # 重载后仍能读到
        repo2 = SqlAlchemyRepository(
            "event_history",
            session_factory=Session(test_db_url=tmp_db_url),
        )
        assert repo2.get("records") == events


class TestUserHistoryKVPattern:
    """user_history 用 str(user_id) 存 list"""

    def test_user_history_set(self, tmp_db_url, clean_globals):
        repo = SqlAlchemyRepository(
            "user_history",
            session_factory=Session(test_db_url=tmp_db_url),
        )
        user_id = 42
        events = [
            {"event_type": "celebration", "payload": {"title": "T1"}},
            {"event_type": "suggestion", "payload": {"topic": "M1"}},
        ]
        # 模拟 event_bus._user_history_repo.set(str(user_id), [...])
        repo.set(str(user_id), events)

        loaded = repo.get(str(user_id))
        assert loaded == events

        # 重载后仍能读到
        repo2 = SqlAlchemyRepository(
            "user_history",
            session_factory=Session(test_db_url=tmp_db_url),
        )
        assert repo2.get(str(user_id)) == events


# ==================== flush_all_repos ====================


class TestFlushAllRepos:
    """flush_all_repos 不抛异常"""

    def test_flush_all_with_sql_backend(self, tmp_db_url, clean_globals):
        """SQL 模式下 flush_all_repos 不抛异常"""
        # 设置一些数据
        get_profiles_repo().set("u1", {"name": "test"})
        get_sessions_repo().set("u1", {"sid": "s1"})
        # flush 不应抛
        flush_all_repos()


# ==================== 辅助函数 ====================


def Session(test_db_url: str):
    """创建测试 session factory"""

    engine = create_engine(test_db_url)
    return sessionmaker(bind=engine, expire_on_commit=False)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])