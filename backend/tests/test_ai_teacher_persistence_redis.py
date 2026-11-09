"""
【P3-D-2】RedisRepository 单元测试

覆盖 RedisRepository 与 SqlAlchemyRepository 行为对齐：
- 基本 CRUD（set/get/delete/has/keys/values/items/len）
- snapshot / replace_all / clear
- Redis Hash 持久化（HSET / HGETALL / HDEL 验证）
- Pub/Sub 消息发布验证
- 优雅降级（Redis 不可用 → 内存模式）
- 防回声（publisher_id 一致时不更新本地）
- 7 张表端到端测试
- 远程事件应用（_apply_remote_*）
- 并发安全

Mock 策略：
- 使用 unittest.mock.MagicMock 模拟 redis.Redis 客户端
- 真实 Redis 实例测试标记为 @pytest.mark.integration（可选）
"""

import json
import threading
from unittest.mock import MagicMock

import pytest

from cache.repository.redis import (
    DEFAULT_CHANNEL,
    DEFAULT_KEY_PREFIX,
    RedisRepository,
)


# ==================== Fixtures ====================


@pytest.fixture
def mock_redis():
    """模拟 Redis 客户端（MagicMock）"""
    client = MagicMock()

    # 模拟 hgetall 返回空 dict
    client.hgetall.return_value = {}

    # 模拟 hset 返回写入字段数
    client.hset.return_value = 1

    # 模拟 hdel 返回删除字段数
    client.hdel.return_value = 1

    # 模拟 publish 返回订阅者数
    client.publish.return_value = 1

    # 模拟 pipeline
    pipe = MagicMock()
    pipe.execute.return_value = [1, 1]  # delete + hset 结果
    client.pipeline.return_value = pipe

    return client


@pytest.fixture
def repo(mock_redis):
    """默认 RedisRepository 实例（mock_redis 客户端）"""
    return RedisRepository(
        name="profiles",
        redis_client=mock_redis,
        enable_pubsub=True,
    )


@pytest.fixture
def repo_no_pubsub(mock_redis):
    """RedisRepository 实例（禁用 Pub/Sub）"""
    return RedisRepository(
        name="sessions",
        redis_client=mock_redis,
        enable_pubsub=False,
    )


# ==================== 基本 CRUD ====================


class TestRedisRepositoryBasics:
    """RedisRepository 基本 CRUD（与 SqlAlchemyRepository 行为一致）"""

    def test_set_and_get(self, repo):
        repo.set("k1", {"a": 1, "b": [1, 2, 3]})
        assert repo.get("k1") == {"a": 1, "b": [1, 2, 3]}

    def test_get_missing_returns_none(self, repo):
        assert repo.get("nonexistent") is None

    def test_get_with_default(self, repo):
        assert repo.get("missing", default="fallback") == "fallback"

    def test_delete(self, repo):
        repo.set("k1", {"a": 1})
        assert repo.delete("k1") is True
        assert repo.get("k1") is None

    def test_delete_missing(self, repo):
        assert repo.delete("nonexistent") is False

    def test_has(self, repo):
        repo.set("k1", {"a": 1})
        assert repo.has("k1") is True
        assert repo.has("missing") is False

    def test_keys_values_items(self, repo):
        repo.set("a", 1)
        repo.set("b", 2)
        repo.set("c", 3)
        assert sorted(repo.keys()) == ["a", "b", "c"]
        assert sorted(repo.values()) == [1, 2, 3]
        keys_items = sorted(k for k, _ in repo.items())
        assert keys_items == ["a", "b", "c"]

    def test_len(self, repo):
        assert len(repo) == 0
        repo.set("a", 1)
        repo.set("b", 2)
        assert len(repo) == 2

    def test_clear(self, repo):
        repo.set("a", 1)
        repo.set("b", 2)
        repo.clear()
        assert len(repo) == 0

    def test_clear_empty(self, repo):
        # 空仓库 clear 不报错
        repo.clear()
        assert len(repo) == 0

    def test_in_operator(self, repo):
        repo.set("k1", 1)
        assert "k1" in repo
        assert "missing" not in repo

    def test_getitem_setitem_delitem(self, repo):
        repo["k1"] = "value1"
        assert repo["k1"] == "value1"
        with pytest.raises(KeyError):
            _ = repo["missing"]
        del repo["k1"]
        with pytest.raises(KeyError):
            _ = repo["k1"]

    def test_iter(self, repo):
        repo.set("a", 1)
        repo.set("b", 2)
        keys = list(repo)
        assert sorted(keys) == ["a", "b"]


# ==================== Redis Hash 持久化 ====================


class TestRedisHashPersistence:
    """Redis Hash 数据正确性（HSET / HGETALL / HDEL）"""

    def test_set_calls_hset(self, repo, mock_redis):
        repo.set("user_1", {"name": "Alice"})
        # 验证 hset 被调用
        assert mock_redis.hset.called
        args, kwargs = mock_redis.hset.call_args
        # hset(hash_key, field, value) - 参数可能是 positional 或 keyword
        assert args[0] == "ai_teacher:profiles:kv"
        assert args[1] == "user_1"
        # value 应该是 JSON-serialized
        assert json.loads(args[2]) == {"name": "Alice"}

    def test_delete_calls_hdel(self, repo, mock_redis):
        repo.set("user_1", {"name": "Alice"})
        mock_redis.reset_mock()
        repo.delete("user_1")
        # 验证 hdel 被调用
        mock_redis.hdel.assert_called_once()
        args, kwargs = mock_redis.hdel.call_args
        assert args[0] == "ai_teacher:profiles:kv"
        assert args[1] == "user_1"

    def test_clear_calls_delete(self, repo, mock_redis):
        repo.set("a", 1)
        mock_redis.reset_mock()
        repo.clear()
        # 验证 redis.delete 被调用（删除整个 Hash）
        mock_redis.delete.assert_called_once_with("ai_teacher:profiles:kv")

    def test_replace_all_uses_pipeline(self, repo, mock_redis):
        repo.replace_all({"a": 1, "b": 2})
        # 验证 pipeline 被使用
        assert mock_redis.pipeline.called
        pipe = mock_redis.pipeline.return_value
        # 1 次 delete 清空 + N 次 hset 逐个写入（兼容 Redis 3.2/4.x/5.x）
        pipe.delete.assert_called_once()
        assert pipe.hset.call_count == 2  # data 含 2 个 key
        # 验证最后一次 hset 是 b=2
        last_call = pipe.hset.call_args_list[-1]
        assert last_call.args[0] == "ai_teacher:profiles:kv"
        assert last_call.args[1] == "b"
        assert json.loads(last_call.args[2]) == 2

    def test_load_from_redis_on_init(self, mock_redis):
        """初始化时从 Redis 加载历史数据"""
        # 模拟 Redis 中已有数据
        mock_redis.hgetall.return_value = {
            b"user_1": b'{"name": "Alice"}',
            b"user_2": b'{"name": "Bob"}',
        }
        repo = RedisRepository("profiles", redis_client=mock_redis)
        # 验证加载成功
        assert repo.get("user_1") == {"name": "Alice"}
        assert repo.get("user_2") == {"name": "Bob"}
        assert len(repo) == 2

    def test_load_from_redis_str_keys(self, mock_redis):
        """Redis 返回 str 而非 bytes 时也能正确加载"""
        mock_redis.hgetall.return_value = {
            "user_1": '{"name": "Alice"}',
            "user_2": '{"name": "Bob"}',
        }
        repo = RedisRepository("profiles", redis_client=mock_redis)
        assert repo.get("user_1") == {"name": "Alice"}
        assert repo.get("user_2") == {"name": "Bob"}


# ==================== Pub/Sub 通知 ====================


class TestPubSubPublish:
    """Pub/Sub 消息发布验证"""

    def test_set_publishes_event(self, repo, mock_redis):
        repo.set("user_1", {"name": "Alice"})
        # 验证 publish 被调用
        mock_redis.publish.assert_called_once()
        args, kwargs = mock_redis.publish.call_args
        # publish(channel, message)
        channel = args[0]
        message = json.loads(args[1])
        assert channel == DEFAULT_CHANNEL
        assert message["table"] == "profiles"
        assert message["action"] == "set"
        assert message["key"] == "user_1"
        assert message["data"] == {"name": "Alice"}
        assert message["publisher_id"] == repo.publisher_id
        assert "timestamp" in message

    def test_delete_publishes_event(self, repo, mock_redis):
        repo.set("user_1", 1)
        mock_redis.reset_mock()
        repo.delete("user_1")
        mock_redis.publish.assert_called_once()
        args, kwargs = mock_redis.publish.call_args
        message = json.loads(args[1])
        assert message["action"] == "delete"
        assert message["key"] == "user_1"

    def test_clear_publishes_event(self, repo, mock_redis):
        repo.set("a", 1)
        mock_redis.reset_mock()
        repo.clear()
        mock_redis.publish.assert_called_once()
        args, kwargs = mock_redis.publish.call_args
        message = json.loads(args[1])
        assert message["action"] == "clear"
        assert message["key"] is None

    def test_replace_all_publishes_event(self, repo, mock_redis):
        repo.replace_all({"a": 1, "b": 2})
        mock_redis.publish.assert_called_once()
        args, kwargs = mock_redis.publish.call_args
        message = json.loads(args[1])
        assert message["action"] == "replace_all"
        assert message["data"] == {"a": 1, "b": 2}

    def test_pubsub_disabled_no_publish(self, repo_no_pubsub, mock_redis):
        """enable_pubsub=False 时不发布"""
        repo_no_pubsub.set("k1", 1)
        mock_redis.publish.assert_not_called()

    def test_no_publish_when_redis_unavailable(self):
        """Redis 不可用时不发布"""
        repo = RedisRepository("profiles", redis_client=None, enable_pubsub=True)
        # 不应抛异常
        repo.set("k1", 1)
        repo.delete("k1")
        repo.clear()

    def test_publish_failure_does_not_raise(self, repo, mock_redis):
        """publish 失败时不抛异常（仅警告）"""
        mock_redis.publish.side_effect = Exception("publish failed")
        # 不应抛异常
        repo.set("k1", 1)
        # 本地写入仍然成功
        assert repo.get("k1") == 1


# ==================== 远程事件应用 ====================


class TestRemoteEventApplication:
    """_apply_remote_* 方法（被 PubSubBridge 调用）"""

    def test_apply_remote_set(self, repo):
        repo._apply_remote_set("user_1", {"name": "Remote Alice"})
        assert repo.get("user_1") == {"name": "Remote Alice"}

    def test_apply_remote_delete(self, repo):
        repo.set("user_1", {"name": "Alice"})
        repo._apply_remote_delete("user_1")
        assert repo.get("user_1") is None

    def test_apply_remote_delete_missing(self, repo):
        # 不存在的 key 不抛异常
        repo._apply_remote_delete("nonexistent")

    def test_apply_remote_replace_all(self, repo):
        repo.set("old", "data")
        repo._apply_remote_replace_all({"new_a": 1, "new_b": 2})
        assert repo.get("old") is None
        assert repo.get("new_a") == 1
        assert repo.get("new_b") == 2

    def test_apply_remote_clear(self, repo):
        repo.set("a", 1)
        repo.set("b", 2)
        repo._apply_remote_clear()
        assert len(repo) == 0

    def test_remote_apply_does_not_republish(self, repo, mock_redis):
        """远程应用事件不应触发本地发布（防回声）"""
        # 注意：当前实现 _apply_remote_* 不会调用 _publish
        # （防回声由 PubSubBridge 的 publisher_id 过滤实现）
        mock_redis.reset_mock()
        repo._apply_remote_set("user_1", {"data": 1})
        repo._apply_remote_delete("user_1")
        repo._apply_remote_replace_all({})
        repo._apply_remote_clear()
        # 远程操作不应触发任何 publish
        mock_redis.publish.assert_not_called()


# ==================== 优雅降级 ====================


class TestGracefulDegradation:
    """Redis 不可用时仅内存模式"""

    def test_no_redis_client_init(self):
        """redis_client=None 时正常初始化"""
        repo = RedisRepository("profiles", redis_client=None)
        assert repo.is_using_redis() is False
        repo.set("k1", {"a": 1})
        assert repo.get("k1") == {"a": 1}

    def test_no_redis_set_get(self):
        """无 Redis 时基本读写可用"""
        repo = RedisRepository("profiles", redis_client=None)
        repo.set("k1", 1)
        repo.set("k2", [1, 2, 3])
        assert repo.get("k1") == 1
        assert repo.get("k2") == [1, 2, 3]

    def test_no_redis_delete(self):
        """无 Redis 时删除可用"""
        repo = RedisRepository("profiles", redis_client=None)
        repo.set("k1", 1)
        assert repo.delete("k1") is True
        assert repo.get("k1") is None

    def test_no_redis_clear(self):
        """无 Redis 时 clear 可用"""
        repo = RedisRepository("profiles", redis_client=None)
        repo.set("a", 1)
        repo.set("b", 2)
        repo.clear()
        assert len(repo) == 0

    def test_no_redis_replace_all(self):
        """无 Redis 时 replace_all 可用"""
        repo = RedisRepository("profiles", redis_client=None)
        repo.replace_all({"a": 1, "b": 2})
        assert repo.get("a") == 1
        assert repo.get("b") == 2

    def test_redis_load_failure_does_not_raise(self, mock_redis):
        """hgetall 失败时不抛异常（仅内存模式）"""
        mock_redis.hgetall.side_effect = Exception("Redis connection refused")
        # 不应抛异常
        repo = RedisRepository("profiles", redis_client=mock_redis)
        assert len(repo) == 0

    def test_redis_set_failure_does_not_raise(self, repo, mock_redis):
        """hset 失败时不抛异常（本地写入仍成功）"""
        mock_redis.hset.side_effect = Exception("Redis connection refused")
        repo.set("k1", {"a": 1})
        # 本地写入仍然成功
        assert repo.get("k1") == {"a": 1}

    def test_redis_delete_failure_does_not_raise(self, repo, mock_redis):
        """hdel 失败时不抛异常（本地删除仍成功）"""
        repo.set("k1", 1)
        mock_redis.hdel.side_effect = Exception("Redis connection refused")
        result = repo.delete("k1")
        # 本地删除仍然成功
        assert result is True
        assert repo.get("k1") is None

    def test_redis_clear_failure_does_not_raise(self, repo, mock_redis):
        """delete hash 失败时不抛异常"""
        repo.set("a", 1)
        mock_redis.delete.side_effect = Exception("Redis connection refused")
        # 不应抛异常
        repo.clear()
        assert len(repo) == 0

    def test_redis_replace_all_failure_does_not_raise(self, repo, mock_redis):
        """pipeline 失败时不抛异常（本地替换仍成功）"""
        mock_redis.pipeline.return_value.execute.side_effect = Exception(
            "Redis connection refused"
        )
        repo.replace_all({"a": 1})
        # 本地替换仍然成功
        assert repo.get("a") == 1


# ==================== Snapshot / 隔离性 ====================


class TestSnapshot:
    """snapshot 独立性"""

    def test_snapshot_returns_copy(self, repo):
        repo.set("k1", {"value": [1, 2, 3]})
        snap = repo.snapshot()
        snap["k1"]["value"].append(999)
        snap["k2"] = "new"
        # 修改 snapshot 不应影响 repo
        assert repo.get("k1") == {"value": [1, 2, 3]}
        assert repo.has("k2") is False

    def test_snapshot_is_dict(self, repo):
        repo.set("k1", 1)
        snap = repo.snapshot()
        assert isinstance(snap, dict)
        assert snap == {"k1": 1}


# ==================== 线程安全 ====================


class TestThreadSafety:
    """并发写入不丢数据"""

    def test_concurrent_writes(self, mock_redis):
        repo = RedisRepository("profiles", redis_client=mock_redis)
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


# ==================== flush ====================


class TestFlush:
    """flush 行为"""

    def test_flush_reloads_from_redis(self, mock_redis):
        """flush 从 Redis 重新加载"""
        # 初始为空
        mock_redis.hgetall.return_value = {}
        repo = RedisRepository("profiles", redis_client=mock_redis)
        repo.set("local_only", "value1")

        # 模拟 Redis 现在有数据（其他进程写入）
        mock_redis.hgetall.return_value = {
            b"remote_1": b'{"data": "remote_data"}',
        }

        # flush 触发 reload
        repo.flush()
        assert repo.get("remote_1") == {"data": "remote_data"}

    def test_flush_without_redis_is_noop(self):
        """无 Redis 时 flush 不报错"""
        repo = RedisRepository("profiles", redis_client=None)
        repo.set("k1", 1)
        # 不应抛异常
        repo.flush()


# ==================== 7 张表端到端 ====================


class TestAllTablesEndToEnd:
    """每张表一个完整的 set/get 流程"""

    @pytest.mark.parametrize("table_name", [
        "profiles",
        "sessions",
        "memories",
        "personas",
        "live_settings",
        "event_history",
        "user_history",
    ])
    def test_table_set_and_get(self, mock_redis, table_name):
        repo = RedisRepository(table_name, redis_client=mock_redis)
        test_key = "test_user_42"
        test_value = {"name": "Alice", "score": 95, "tags": ["vip"]}
        repo.set(test_key, test_value)

        # 同实例读
        assert repo.get(test_key) == test_value

        # hash_key 格式正确
        assert repo.hash_key == f"{DEFAULT_KEY_PREFIX}:{table_name}:kv"


# ==================== event_history KV 模式 ====================


class TestEventHistoryKVPattern:
    """event_history 用固定 key "records" 存整个 list（与 P3-B 兼容）"""

    def test_event_history_replace_all(self, mock_redis):
        repo = RedisRepository("event_history", redis_client=mock_redis)
        events = [
            {"type": "celebration", "payload": {"title": "T1"}},
            {"type": "nudge", "payload": {"message": "M1"}},
        ]
        # 模拟 event_bus.replace_all({"records": [...]})
        repo.replace_all({"records": events})
        assert repo.get("records") == events


class TestUserHistoryKVPattern:
    """user_history 用 str(user_id) 存 list"""

    def test_user_history_set(self, mock_redis):
        repo = RedisRepository("user_history", redis_client=mock_redis)
        user_id = 42
        events = [
            {"event_type": "celebration", "payload": {"title": "T1"}},
            {"event_type": "suggestion", "payload": {"topic": "M1"}},
        ]
        repo.set(str(user_id), events)
        assert repo.get(str(user_id)) == events


# ==================== Hash Key 自定义 ====================


class TestHashKeyCustomization:
    """自定义 key_prefix 和 channel"""

    def test_custom_key_prefix(self, mock_redis):
        repo = RedisRepository(
            "profiles",
            redis_client=mock_redis,
            key_prefix="custom",
        )
        repo.set("k1", 1)
        args, _ = mock_redis.hset.call_args
        assert args[0] == "custom:profiles:kv"

    def test_custom_channel(self, mock_redis):
        repo = RedisRepository(
            "profiles",
            redis_client=mock_redis,
            channel="custom:events",
        )
        repo.set("k1", 1)
        args, _ = mock_redis.publish.call_args
        assert args[0] == "custom:events"

    def test_name_property(self, repo):
        assert repo.name == "profiles"

    def test_hash_key_property(self, repo):
        assert repo.hash_key == "ai_teacher:profiles:kv"

    def test_channel_property(self, repo):
        assert repo.channel == DEFAULT_CHANNEL

    def test_publisher_id_unique(self, mock_redis):
        repo1 = RedisRepository("profiles", redis_client=mock_redis)
        repo2 = RedisRepository("profiles", redis_client=mock_redis)
        assert repo1.publisher_id != repo2.publisher_id
        assert repo1.publisher_id.startswith("proc-")


# ==================== is_using_redis ====================


class TestIsUsingRedis:
    """is_using_redis 健康检查"""

    def test_using_redis_with_client(self, repo):
        assert repo.is_using_redis() is True

    def test_not_using_redis_without_client(self):
        repo = RedisRepository("profiles", redis_client=None)
        assert repo.is_using_redis() is False


# ==================== replace_all 边界情况 ====================


class TestReplaceAllEdgeCases:
    """replace_all 边界情况"""

    def test_replace_all_with_empty_dict(self, repo):
        repo.set("old", "value")
        repo.replace_all({})
        assert len(repo) == 0
        assert repo.get("old") is None

    def test_replace_all_replaces_existing(self, repo):
        repo.set("k1", "old")
        repo.replace_all({"k1": "new", "k2": "extra"})
        assert repo.get("k1") == "new"
        assert repo.get("k2") == "extra"
        assert len(repo) == 2


# ==================== 数据类型兼容性 ====================


class TestDataTypeCompatibility:
    """各种数据类型正确处理"""

    def test_string_value(self, repo):
        repo.set("k1", "hello")
        assert repo.get("k1") == "hello"

    def test_int_value(self, repo):
        repo.set("k1", 42)
        assert repo.get("k1") == 42

    def test_float_value(self, repo):
        repo.set("k1", 3.14)
        assert repo.get("k1") == 3.14

    def test_bool_value(self, repo):
        repo.set("k1", True)
        assert repo.get("k1") is True

    def test_list_value(self, repo):
        repo.set("k1", [1, 2, 3])
        assert repo.get("k1") == [1, 2, 3]

    def test_nested_dict(self, repo):
        repo.set("k1", {"a": {"b": {"c": "deep"}}})
        assert repo.get("k1") == {"a": {"b": {"c": "deep"}}}

    def test_unicode_value(self, repo):
        repo.set("k1", "中文测试 🎉")
        assert repo.get("k1") == "中文测试 🎉"

    def test_datetime_serialized_to_redis(self, repo, mock_redis):
        """datetime 通过 default=str 序列化为字符串（写入 Redis 时）"""
        from datetime import datetime

        dt = datetime(2024, 1, 1, 12, 0, 0)
        repo.set("k1", {"ts": dt})
        # 验证 Redis 端确实被序列化为字符串
        args, _ = mock_redis.hset.call_args
        # args[2] 是 JSON payload
        payload = json.loads(args[2])
        assert "2024-01-01" in payload["ts"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])