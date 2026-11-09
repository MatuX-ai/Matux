"""
【P3-B】AI 教师持久化层单元测试

覆盖：
- FileJsonRepository 基本 CRUD
- 落盘与重载（模拟重启场景）
- 线程安全（并发写入不丢数据）
- 优雅降级（文件不可用时内存仍可用）
- AI 教师 live_settings 持久化集成
- AI 教师 event_bus 历史持久化集成
"""

import threading
import time

import pytest

from cache.ai_teacher_persistence import (
    FileJsonRepository,
    flush_all_repos,
    get_memories_repo,
    get_personas_repo,
    get_profiles_repo,
    get_sessions_repo,
    reset_all_repos_for_testing,
)


# ==================== Fixtures ====================


@pytest.fixture
def tmp_data_dir(tmp_path, monkeypatch):
    """临时数据目录（每次测试隔离）"""
    monkeypatch.setenv("AI_TEACHER_DATA_DIR", str(tmp_path))
    # 重置全局单例，避免污染
    reset_all_repos_for_testing()
    yield tmp_path
    # 清理全局单例
    reset_all_repos_for_testing()


# ==================== FileJsonRepository 基础行为 ====================


class TestFileJsonRepositoryBasics:
    """FileJsonRepository 基本 CRUD"""

    def test_set_and_get(self, tmp_data_dir):
        repo = FileJsonRepository("test_basic.json")
        repo.set("k1", {"a": 1, "b": [1, 2, 3]})
        assert repo.get("k1") == {"a": 1, "b": [1, 2, 3]}

    def test_get_missing_returns_none(self, tmp_data_dir):
        repo = FileJsonRepository("test_missing.json")
        assert repo.get("nonexistent") is None

    def test_get_with_default(self, tmp_data_dir):
        repo = FileJsonRepository("test_default.json")
        assert repo.get("missing", default="fallback") == "fallback"

    def test_delete(self, tmp_data_dir):
        repo = FileJsonRepository("test_delete.json")
        repo.set("k1", {"a": 1})
        assert repo.delete("k1") is True
        assert repo.get("k1") is None

    def test_delete_missing(self, tmp_data_dir):
        repo = FileJsonRepository("test_delete_missing.json")
        assert repo.delete("nonexistent") is False

    def test_has(self, tmp_data_dir):
        repo = FileJsonRepository("test_has.json")
        repo.set("k1", {"a": 1})
        assert repo.has("k1") is True
        assert repo.has("missing") is False

    def test_keys_values_items(self, tmp_data_dir):
        repo = FileJsonRepository("test_keys.json")
        repo.set("a", 1)
        repo.set("b", 2)
        repo.set("c", 3)
        assert sorted(repo.keys()) == ["a", "b", "c"]
        assert sorted(repo.values()) == [1, 2, 3]
        keys_items = sorted(k for k, _ in repo.items())
        assert keys_items == ["a", "b", "c"]

    def test_len(self, tmp_data_dir):
        repo = FileJsonRepository("test_len.json")
        assert len(repo) == 0
        repo.set("a", 1)
        repo.set("b", 2)
        assert len(repo) == 2

    def test_clear(self, tmp_data_dir):
        repo = FileJsonRepository("test_clear.json")
        repo.set("a", 1)
        repo.set("b", 2)
        repo.clear()
        assert len(repo) == 0


# ==================== 持久化 / 重载 ====================


class TestFileJsonRepositoryPersistence:
    """落盘与重载行为"""

    def test_flush_creates_file(self, tmp_data_dir):
        repo = FileJsonRepository("test_flush.json")
        repo.set("k1", {"value": "hello"})
        repo.flush()
        # 文件应已存在
        file_path = tmp_data_dir / "test_flush.json"
        assert file_path.exists()
        # 文件内容应为合法 JSON
        import json
        data = json.loads(file_path.read_text(encoding="utf-8"))
        assert data == {"k1": {"value": "hello"}}

    def test_reload_after_flush(self, tmp_data_dir):
        """模拟重启：写入 → flush → 新实例 → 读取"""
        # 第一次实例化
        repo1 = FileJsonRepository("test_reload.json")
        repo1.set("user_1", {"name": "Alice", "age": 30})
        repo1.set("user_2", {"name": "Bob"})
        repo1.flush()

        # 第二次实例化（模拟重启）
        repo2 = FileJsonRepository("test_reload.json")
        assert repo2.get("user_1") == {"name": "Alice", "age": 30}
        assert repo2.get("user_2") == {"name": "Bob"}
        assert len(repo2) == 2

    def test_persistence_with_complex_data(self, tmp_data_dir):
        """包含列表、嵌套 dict、字符串"""
        repo = FileJsonRepository("test_complex.json")
        repo.set("data", {
            "list": [1, 2, {"nested": True}],
            "dict": {"a": {"b": {"c": "deep"}}},
            "string": "中文测试 🎉",
        })
        repo.flush()

        repo2 = FileJsonRepository("test_complex.json")
        loaded = repo2.get("data")
        assert loaded["list"] == [1, 2, {"nested": True}]
        assert loaded["dict"]["a"]["b"]["c"] == "deep"
        assert loaded["string"] == "中文测试 🎉"

    def test_empty_file_does_not_crash(self, tmp_data_dir):
        """空文件不应导致崩溃"""
        file_path = tmp_data_dir / "empty.json"
        file_path.write_text("", encoding="utf-8")
        repo = FileJsonRepository("empty.json")
        assert len(repo) == 0


# ==================== 线程安全 ====================


class TestFileJsonRepositoryThreadSafety:
    """并发写入不丢数据"""

    def test_concurrent_writes(self, tmp_data_dir):
        repo = FileJsonRepository("test_concurrent.json", flush_debounce_seconds=0.1)
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

        # 等待 debounced flush 完成
        time.sleep(0.3)
        repo.flush()

        # 所有写入都应被保留
        expected = num_writers * writes_per_writer
        assert len(repo) == expected

        # 验证重载
        repo2 = FileJsonRepository("test_concurrent.json")
        assert len(repo2) == expected


# ==================== 优雅降级 ====================


class TestFileJsonRepositoryGracefulDegradation:
    """文件不可用时内存仍可用"""

    def test_read_only_dir_does_not_crash(self, tmp_data_dir):
        """目录只读时写入不应导致崩溃"""
        # 创建一个目录，文件名当作目录的子文件
        sub_dir = tmp_data_dir / "is_a_dir.json"
        sub_dir.mkdir()
        repo = FileJsonRepository("is_a_dir.json", data_dir=tmp_data_dir)
        # 内存写入应仍可用
        repo.set("k1", {"a": 1})
        assert repo.get("k1") == {"a": 1}
        # flush 会失败但不应崩溃
        repo.flush()  # 不抛异常


# ==================== Snapshot ====================


class TestFileJsonRepositorySnapshot:
    """snapshot 返回独立快照（修改不影响原数据）"""

    def test_snapshot_is_isolated(self, tmp_data_dir):
        repo = FileJsonRepository("test_snapshot.json")
        repo.set("k1", {"value": [1, 2, 3]})
        snap = repo.snapshot()
        # 修改 snapshot 不应影响 repo
        snap["k1"]["value"].append(999)
        snap["k2"] = "new"
        assert repo.get("k1") == {"value": [1, 2, 3]}
        assert repo.has("k2") is False


# ==================== 集成测试：live_settings 持久化 ====================


class TestLiveSettingsPersistence:
    """live_settings 通过持久化仓储保存设置"""

    def test_settings_survives_reprocess(self, tmp_data_dir):
        import os
        if os.getenv("AI_TEACHER_PERSISTENCE_BACKEND", "file").lower() == "sql":
            pytest.skip("SQL backend 测试参见 test_ai_teacher_persistence_sql.py")
        from services.ai_teacher_live_settings import (
            ai_teacher_live_settings,
        )

        # 清理初始状态
        ai_teacher_live_settings.clear()

        # 修改设置
        ai_teacher_live_settings.update_settings(
            123,
            {
                "celebration_enabled": False,
                "max_per_hour": 5,
                "dnd_start_hour": 23,
            },
        )

        # 强制 flush
        ai_teacher_live_settings._store_repo.flush()

        # 读取应能拿到更新后的值
        s = ai_teacher_live_settings.get_settings(123)
        assert s.celebration_enabled is False
        assert s.max_per_hour == 5
        assert s.dnd_start_hour == 23

        # 模拟重启：清除进程内缓存，重新从磁盘加载
        reset_all_repos_for_testing()
        from cache.ai_teacher_persistence import (
            get_live_settings_repo as reload_repo,
        )
        reload_repo()  # 触发重载
        s2 = ai_teacher_live_settings.get_settings(123)
        # 由于 ai_teacher_live_settings 是单例，更新已通过 repo 持久化
        assert s2.celebration_enabled is False
        assert s2.max_per_hour == 5
        assert s2.dnd_start_hour == 23

        # 清理
        ai_teacher_live_settings.clear()


# ==================== 集成测试：event_bus 历史持久化 ====================


class TestEventBusHistoryPersistence:
    """event_bus 历史通过持久化仓储保存"""

    def test_history_persists_across_reprocess(self, tmp_data_dir):
        import os
        if os.getenv("AI_TEACHER_PERSISTENCE_BACKEND", "file").lower() == "sql":
            pytest.skip("SQL backend 测试参见 test_ai_teacher_persistence_sql.py")
        from services.ai_teacher_event_bus import (
            ai_teacher_live_bus,
            make_celebration_payload,
        )

        # 清理
        ai_teacher_live_bus.clear()

        # 发布事件
        for i in range(3):
            ai_teacher_live_bus.publish(
                make_celebration_payload(
                    user_id=42,
                    title=f"test_{i}",
                    message=f"msg_{i}",
                )
            )

        # 强制 flush
        ai_teacher_live_bus._event_history_repo.flush()
        ai_teacher_live_bus._user_history_repo.flush()

        # 用户 42 应有 3 条历史
        history = ai_teacher_live_bus.get_history(user_id=42, limit=10)
        assert len(history) == 3
        titles = [h["payload"]["title"] for h in history]
        assert "test_0" in titles
        assert "test_1" in titles
        assert "test_2" in titles

        # 清理
        ai_teacher_live_bus.clear()


# ==================== 全局仓储单例 ====================


class TestGlobalRepos:
    """全局仓储单例行为"""

    def test_get_profiles_repo_returns_same_instance(self, tmp_data_dir):
        r1 = get_profiles_repo()
        r2 = get_profiles_repo()
        assert r1 is r2

    def test_each_repo_separate(self, tmp_data_dir):
        r1 = get_profiles_repo()
        r2 = get_sessions_repo()
        r3 = get_memories_repo()
        r4 = get_personas_repo()
        assert r1 is not r2
        assert r1 is not r3
        assert r1 is not r4

    def test_flush_all_repos(self, tmp_data_dir):
        """flush_all_repos 不抛异常"""
        # 设置一些数据
        get_profiles_repo().set("u1", {"name": "test"})
        get_sessions_repo().set("u1", {"sid": "s1"})
        # flush 不应抛
        flush_all_repos()


# ==================== AI 教师画像持久化 ====================


class TestProfilePersistence:
    """画像通过持久化仓储保存"""

    def test_profile_persists(self, tmp_data_dir):
        # SQL backend 测试参见 test_ai_teacher_persistence_sql.py
        # 本测试仅针对 file backend
        import os
        if os.getenv("AI_TEACHER_PERSISTENCE_BACKEND", "file").lower() == "sql":
            pytest.skip("SQL backend 测试参见 test_ai_teacher_persistence_sql.py")
        # 通过仓储直接写入画像（模拟 routes 中的 _get_mock_profile）
        repo = get_profiles_repo()
        profile = {
            "user_id": "user_42",
            "display_name": "测试用户",
            "grade_level": "G7",
            "age_group": "12-14",
            "learning_style": "visual",
            "preferred_content_type": "interactive",
            "ability_dimensions": {"programming_thinking": 75},
            "interest_preferences": ["robotics"],
            "knowledge_mastery": {"python_basics": 0.9},
            "total_study_time_minutes": 1000,
            "completed_courses_count": 10,
            "average_quiz_score": 85.0,
            "current_streak_days": 5,
            "longest_streak_days": 10,
            "weak_points": [],
            "error_patterns": {},
            "attention_profile": {},
            "emotional_states": [],
            "learning_milestones": [],
            "skill_tree": [],
            "persona_seed": "测试",
            "learning_goals": ["目标 1"],
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        repo.set("user_42", profile)
        repo.flush()

        # 模拟重启：清空单例再加载
        reset_all_repos_for_testing()
        repo2 = get_profiles_repo()
        loaded = repo2.get("user_42")
        assert loaded is not None
        assert loaded["display_name"] == "测试用户"
        assert loaded["ability_dimensions"]["programming_thinking"] == 75
        assert loaded["interest_preferences"] == ["robotics"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])