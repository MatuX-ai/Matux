"""
【P3-A-1】成就统计单元测试
"""
import pytest
from unittest.mock import MagicMock

from cache.achievement_stats_cache import (
    AchievementStatsCache,
    achievement_stats_cache,
    get_cached_batch_stats,
    set_cached_batch_stats,
    invalidate_achievement_stats,
    get_single_stats_cache_key,
    get_batch_stats_cache_key,
)


class TestAchievementStatsCache:
    """缓存层单元测试（内存模式）"""

    def setup_method(self):
        achievement_stats_cache.clear()

    def test_set_and_get(self):
        """基本 set/get"""
        cache = AchievementStatsCache()
        cache.set("k1", {"a": 1})
        assert cache.get("k1") == {"a": 1}

    def test_get_missing_returns_none(self):
        cache = AchievementStatsCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self):
        """TTL 过期"""
        import time
        cache = AchievementStatsCache(ttl_seconds=1)
        cache.set("k1", {"a": 1})
        assert cache.get("k1") == {"a": 1}
        time.sleep(1.2)
        assert cache.get("k1") is None

    def test_set_with_custom_ttl(self):
        cache = AchievementStatsCache()
        cache.set("k1", {"a": 1}, ttl=120)
        assert cache.get("k1") == {"a": 1}

    def test_delete(self):
        cache = AchievementStatsCache()
        cache.set("k1", {"a": 1})
        cache.delete("k1")
        assert cache.get("k1") is None

    def test_delete_pattern(self):
        cache = AchievementStatsCache()
        cache.set("a:1", {"a": 1})
        cache.set("a:2", {"a": 2})
        cache.set("b:1", {"a": 3})
        count = cache.delete_pattern("a:")
        assert count == 2
        assert cache.get("a:1") is None
        assert cache.get("a:2") is None
        assert cache.get("b:1") == {"a": 3}

    def test_clear(self):
        cache = AchievementStatsCache()
        cache.set("k1", {"a": 1})
        cache.set("k2", {"a": 2})
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_is_using_redis_false_by_default(self):
        cache = AchievementStatsCache()
        assert cache.is_using_redis() is False

    def test_is_using_redis_true_after_set(self):
        cache = AchievementStatsCache()
        cache.set_redis_client(MagicMock())
        assert cache.is_using_redis() is True

    def test_thread_safety(self):
        """多线程并发读写不应崩溃"""
        import threading
        cache = AchievementStatsCache()

        def writer():
            for i in range(100):
                cache.set(f"k{i}", {"a": i})

        def reader():
            for i in range(100):
                cache.get(f"k{i}")

        threads = [threading.Thread(target=writer) for _ in range(5)]
        threads += [threading.Thread(target=reader) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # 至少最后写的 key 应该存在
        assert cache.get("k99") == {"a": 99}


class TestCacheKeyHelpers:
    """key 生成测试"""

    def test_batch_key(self):
        assert get_batch_stats_cache_key() == "achievement:stats:batch:v1"

    def test_single_key(self):
        assert get_single_stats_cache_key(42) == "achievement:stats:single:42:v1"
        assert get_single_stats_cache_key(0) == "achievement:stats:single:0:v1"


class TestInvalidation:
    """缓存失效测试"""

    def setup_method(self):
        achievement_stats_cache.clear()

    def test_invalidate_specific(self):
        set_cached_batch_stats([{"id": 1}])
        assert get_cached_batch_stats() is not None
        invalidate_achievement_stats(achievement_id=1)
        assert get_cached_batch_stats() is None

    def test_invalidate_all(self):
        set_cached_batch_stats([{"id": 1}])
        invalidate_achievement_stats()
        assert get_cached_batch_stats() is None

    def test_invalidate_idempotent(self):
        # 不存在的 key 不应崩溃
        invalidate_achievement_stats(achievement_id=999)
        invalidate_achievement_stats()


class TestAchievementServiceStats:
    """成就服务统计方法测试（mock DB）"""

    def test_recompute_global_stats_returns_empty_for_missing(self):
        """成就不存在时返回空字典"""
        from services.achievement_service import AchievementService
        db = MagicMock()
        service = AchievementService(db)
        # mock get_achievement 返回 None
        service.get_achievement = MagicMock(return_value=None)
        result = service.recompute_global_stats(999)
        assert result == {}

    def test_recompute_global_stats_calculates_correctly(self):
        """成就在场时正确计算"""
        from services.achievement_service import AchievementService
        db = MagicMock()
        # mock 链
        service = AchievementService(db)

        mock_achievement = MagicMock()
        mock_achievement.id = 1
        service.get_achievement = MagicMock(return_value=mock_achievement)

        # mock query chains
        user_count_query = MagicMock()
        user_count_query.filter.return_value.count.return_value = 100
        holder_count_query = MagicMock()
        holder_count_query.filter.return_value.distinct.return_value.count.return_value = 25

        def query_side_effect(*args, **kwargs):
            # 第一次 query：User，第二次：UserAchievement
            if not service._query_count:
                service._query_count = 1
                return user_count_query
            else:
                return holder_count_query

        service._query_count = 0
        db.query.side_effect = query_side_effect

        result = service.recompute_global_stats(1)
        assert result["global_unlock_rate"] == 0.25
        assert result["total_holders"] == 25
        assert result["total_users"] == 100
        assert mock_achievement.global_unlock_rate == 0.25
        assert mock_achievement.total_holders == 25
        db.commit.assert_called_once()

    def test_recompute_handles_zero_users(self):
        """总用户数为 0 时解锁率为 0"""
        from services.achievement_service import AchievementService
        db = MagicMock()
        service = AchievementService(db)
        service.get_achievement = MagicMock(return_value=MagicMock(id=1))

        user_count_query = MagicMock()
        user_count_query.filter.return_value.count.return_value = 0
        db.query.return_value = user_count_query

        result = service.recompute_global_stats(1)
        assert result["global_unlock_rate"] == 0.0

    def test_recompute_rollback_on_error(self):
        """异常时回滚"""
        from services.achievement_service import AchievementService
        db = MagicMock()
        service = AchievementService(db)
        service.get_achievement = MagicMock(return_value=MagicMock(id=1))

        # 第一次 query 抛错
        db.query.side_effect = Exception("DB error")
        result = service.recompute_global_stats(1)
        assert result == {}
        db.rollback.assert_called_once()


# pytest 配置
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
