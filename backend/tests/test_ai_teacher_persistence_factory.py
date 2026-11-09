"""
【P3-D-1】仓储工厂单元测试

覆盖：
- backend 切换（file / sql）
- 环境变量优先级
- Settings 优先级
- 7 个仓库名映射
- 单例保证
- 未知仓库名 / backend 错误处理
"""


import pytest

from cache.ai_teacher_persistence import (
    FileJsonRepository,
    SqlAlchemyRepository,
    flush_all_repos,
    reset_all_repos_for_testing,
)
from cache.repository import factory
from cache.repository.factory import (
    REPOSITORY_REGISTRY,
    create_repository,
    get_event_history_repo,
    get_live_settings_repo,
    get_memories_repo,
    get_personas_repo,
    get_profiles_repo,
    get_sessions_repo,
    get_user_history_repo,
)


# ==================== Fixtures ====================


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    """每个测试清理环境变量 + 重置单例"""
    monkeypatch.delenv("AI_TEACHER_PERSISTENCE_BACKEND", raising=False)
    monkeypatch.setenv("AI_TEACHER_DATA_DIR", str(tmp_path))
    reset_all_repos_for_testing()
    yield
    reset_all_repos_for_testing()


# ==================== backend 解析 ====================


class TestBackendResolution:
    """backend 配置解析"""

    def test_default_backend_is_file(self, monkeypatch):
        """未设置时默认 file"""
        monkeypatch.delenv("AI_TEACHER_PERSISTENCE_BACKEND", raising=False)
        # 重置模块的 settings 缓存（如果可能）
        from config import settings as settings_module
        original = settings_module.settings
        settings_module.settings = None
        try:
            backend = factory._resolve_backend()
            assert backend == "file"
        finally:
            settings_module.settings = original

    def test_env_var_overrides_default(self, monkeypatch):
        """环境变量优先"""
        monkeypatch.setenv("AI_TEACHER_PERSISTENCE_BACKEND", "sql")
        backend = factory._resolve_backend()
        assert backend == "sql"

    def test_env_var_case_insensitive(self, monkeypatch):
        """环境变量大小写不敏感"""
        monkeypatch.setenv("AI_TEACHER_PERSISTENCE_BACKEND", "SQL")
        backend = factory._resolve_backend()
        assert backend == "sql"


# ==================== create_repository ====================


class TestCreateRepository:
    """create_repository 工厂函数"""

    def test_create_with_file_backend(self, monkeypatch):
        monkeypatch.setenv("AI_TEACHER_PERSISTENCE_BACKEND", "file")
        repo = create_repository("profiles")
        assert isinstance(repo, FileJsonRepository)
        assert not isinstance(repo, SqlAlchemyRepository)

    def test_create_with_sql_backend(self, monkeypatch):
        monkeypatch.setenv("AI_TEACHER_PERSISTENCE_BACKEND", "sql")
        repo = create_repository("profiles")
        assert isinstance(repo, SqlAlchemyRepository)
        assert not isinstance(repo, FileJsonRepository)

    def test_create_unknown_name_raises(self, monkeypatch):
        """未知仓库名抛 KeyError"""
        monkeypatch.setenv("AI_TEACHER_PERSISTENCE_BACKEND", "file")
        with pytest.raises(KeyError) as exc_info:
            create_repository("unknown_repo")
        assert "未知仓库名" in str(exc_info.value)

    def test_create_all_seven_names_file(self, monkeypatch):
        """7 个仓库名都能创建（file 模式）"""
        monkeypatch.setenv("AI_TEACHER_PERSISTENCE_BACKEND", "file")
        for name in REPOSITORY_REGISTRY.keys():
            repo = create_repository(name)
            assert isinstance(repo, FileJsonRepository)


# ==================== 全局单例 ====================


class TestGlobalRepoSingletons:
    """全局单例 getter"""

    def test_same_name_returns_same_instance_file(self, monkeypatch):
        """同名多次调用返回同一实例（file 模式）"""
        monkeypatch.setenv("AI_TEACHER_PERSISTENCE_BACKEND", "file")
        reset_all_repos_for_testing()
        r1 = get_profiles_repo()
        r2 = get_profiles_repo()
        assert r1 is r2

    def test_different_names_return_different_instances(self, monkeypatch):
        """不同仓库名返回不同实例"""
        monkeypatch.setenv("AI_TEACHER_PERSISTENCE_BACKEND", "file")
        reset_all_repos_for_testing()
        r1 = get_profiles_repo()
        r2 = get_sessions_repo()
        r3 = get_memories_repo()
        assert r1 is not r2
        assert r1 is not r3

    def test_seven_singletons_independent(self, monkeypatch):
        """7 个单例各自独立"""
        monkeypatch.setenv("AI_TEACHER_PERSISTENCE_BACKEND", "file")
        reset_all_repos_for_testing()
        repos = [
            get_profiles_repo(),
            get_sessions_repo(),
            get_memories_repo(),
            get_personas_repo(),
            get_live_settings_repo(),
            get_event_history_repo(),
            get_user_history_repo(),
        ]
        # 全部不同实例
        assert len(set(id(r) for r in repos)) == 7


# ==================== reset_all_repos_for_testing ====================


class TestResetReposForTesting:
    """重置单例后能获取新实例"""

    def test_reset_clears_singleton(self, monkeypatch):
        monkeypatch.setenv("AI_TEACHER_PERSISTENCE_BACKEND", "file")
        reset_all_repos_for_testing()
        r1 = get_profiles_repo()
        reset_all_repos_for_testing()
        r2 = get_profiles_repo()
        # 重置后是新实例
        assert r1 is not r2


# ==================== flush_all_repos ====================


class TestFlushAllReposFactory:
    """flush_all_repos 在 factory 模式下不抛异常"""

    def test_flush_all_file_backend(self, monkeypatch):
        """file 模式 flush 不抛"""
        monkeypatch.setenv("AI_TEACHER_PERSISTENCE_BACKEND", "file")
        reset_all_repos_for_testing()
        get_profiles_repo().set("k1", {"a": 1})
        flush_all_repos()  # 不抛


# ==================== Registry 完整性 ====================


class TestRegistry:
    """REPOSITORY_REGISTRY 完整性"""

    def test_registry_has_seven_entries(self):
        assert len(REPOSITORY_REGISTRY) == 7

    def test_registry_contains_expected_names(self):
        expected = {
            "profiles", "sessions", "memories", "personas",
            "live_settings", "event_history", "user_history",
        }
        assert set(REPOSITORY_REGISTRY.keys()) == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])