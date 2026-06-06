"""
数据库表延迟创建管理器单元测试

测试 LazyTableManager 的注册、分批创建、幂等性
"""

from core.lazy_tables import LazyTableManager
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import os
import sys

_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)


class TestLazyTableManagerRegistration:
    """LazyTableManager 注册功能测试"""

    @pytest.fixture
    def manager(self):
        return LazyTableManager()

    def test_register_module_tables(self, manager):
        manager.register_module_tables(
            "user_mod",
            ["backend.models.user.User", "backend.models.user.UserProfile"],
        )
        assert "user_mod" in manager._module_tables
        assert len(manager._module_tables["user_mod"]) == 2

    def test_register_multiple_modules(self, manager):
        manager.register_module_tables("mod_a", ["models.a.ModelA"])
        manager.register_module_tables("mod_b", ["models.b.ModelB"])
        assert len(manager._module_tables) == 2

    def test_register_overwrites_existing(self, manager):
        manager.register_module_tables("mod", ["old.Model"])
        manager.register_module_tables("mod", ["new.Model1", "new.Model2"])
        assert len(manager._module_tables["mod"]) == 2


class TestLazyTableManagerCreation:
    """LazyTableManager 表创建测试"""

    @pytest.fixture
    def manager(self):
        mgr = LazyTableManager()
        mgr.register_module_tables(
            "test_mod",
            ["backend.models.user.User"],
        )
        return mgr

    @pytest.mark.asyncio
    async def test_create_tables_for_unregistered_module(self, manager):
        """未注册模块应跳过"""
        result = await manager.create_tables_for_module("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_create_tables_idempotent(self, manager):
        """重复创建应幂等"""
        # Mock _do_create_tables 避免实际数据库操作
        with patch.object(manager, "_do_create_tables", new_callable=AsyncMock) as mock_create:
            # 首次创建
            await manager.create_tables_for_module("test_mod")
            assert mock_create.call_count == 1

            # 标记为已创建，第二次应跳过
            manager._created_tables.update(["backend.models.user.User"])
            result = await manager.create_tables_for_module("test_mod")
            assert result is True  # 已全部创建
            assert mock_create.call_count == 1  # 不再调用


class TestLazyTableManagerStats:
    """LazyTableManager 统计信息测试"""

    @pytest.fixture
    def manager(self):
        mgr = LazyTableManager()
        mgr.register_module_tables("mod_a", ["models.a.A1", "models.a.A2"])
        mgr.register_module_tables("mod_b", ["models.b.B1"])
        return mgr

    def test_get_stats(self, manager):
        stats = manager.get_stats()
        assert "modules_registered" in stats
        assert stats["modules_registered"] == 2
        assert stats["tables_registered"] == 3

    def test_module_table_map(self, manager):
        mapping = manager.module_table_map
        assert "mod_a" in mapping
        assert "mod_b" in mapping
