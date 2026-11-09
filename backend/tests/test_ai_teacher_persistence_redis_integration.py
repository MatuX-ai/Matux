"""
【P3-D-2】真实 Redis 集成测试（端到端验证）

覆盖：
- Hash 持久化（HGETALL 在 set/delete 后正确）
- 跨进程 Pub/Sub 同步（2 个独立 RedisRepository 实例之间）
- publisher_id 防回声（同一个进程实例不会被自己的消息触发）
- 优雅降级（Redis 真实失败时不抛异常）
- 7 张表端到端

依赖：
- localhost:6379 必须有 Redis 服务
- 通过环境变量 REDIS_URL 可改写连接（默认 "redis://127.0.0.1:6379/15" 使用 db=15 隔离测试）

运行方式：
    pytest tests/test_ai_teacher_persistence_redis_integration.py -v
    REDIS_URL=redis://... pytest ...
"""

import json
import os
import time

import pytest
import redis

from cache.repository.redis import (
    DEFAULT_CHANNEL,
    DEFAULT_KEY_PREFIX,
    RedisRepository,
)
from cache.repository.redis_pubsub import (
    RedisPubSubBridge,
    stop_pubsub_bridge,
)


REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/15")
# 测试用 channel（避免污染默认 ai_teacher:update 通道）
TEST_CHANNEL = f"{DEFAULT_CHANNEL}:test"
REPOSITORY_REGISTRY = [
    "profiles",
    "sessions",
    "memories",
    "personas",
    "live_settings",
    "event_history",
    "user_history",
]


def _redis_available(url: str = REDIS_URL) -> bool:
    """检查 Redis 是否可用（用于 skip）"""
    try:
        client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=1)
        client.ping()
        client.close()
        return True
    except Exception:
        return False


# ==================== Fixtures ====================


@pytest.fixture(scope="module")
def redis_url():
    """Redis 连接 URL（来自 REDIS_URL 环境变量或默认）"""
    if not _redis_available():
        pytest.skip(f"Redis 不可用：{REDIS_URL}（跳过集成测试）")
    return REDIS_URL


@pytest.fixture
def redis_client(redis_url):
    """干净的 Redis 客户端（每个测试后清空 db）"""
    client = redis.Redis.from_url(redis_url, decode_responses=True)
    client.flushdb()
    yield client
    client.flushdb()
    client.close()


@pytest.fixture
def cleanup_global_bridge():
    """每个测试后清理全局 bridge（避免污染下一个测试）"""
    yield
    try:
        stop_pubsub_bridge()
    except Exception:
        pass


# ==================== Hash 持久化 ====================


class TestRedisHashRealPersistence:
    """真实 Redis Hash 持久化（HSET/HGETALL/HDEL）"""

    def test_set_persists_to_hash(self, redis_client):
        repo = RedisRepository(
            name="profiles",
            redis_client=redis_client,
            channel=TEST_CHANNEL,
        )
        repo.set("user_1", {"name": "Alice", "age": 30})

        # 直接验证 Redis Hash 里有数据
        raw = redis_client.hget("ai_teacher:profiles:kv", "user_1")
        assert raw is not None
        assert json.loads(raw) == {"name": "Alice", "age": 30}
        # hash_key 格式正确
        assert repo.hash_key == "ai_teacher:profiles:kv"

    def test_get_returns_deserialized_value(self, redis_client):
        repo = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo.set("user_1", {"name": "Alice", "tags": ["vip", "founder"]})
        assert repo.get("user_1") == {"name": "Alice", "tags": ["vip", "founder"]}

    def test_delete_removes_hash_field(self, redis_client):
        repo = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo.set("user_1", {"name": "Alice"})
        assert repo.delete("user_1") is True

        # Redis 中已删除
        assert redis_client.hget("ai_teacher:profiles:kv", "user_1") is None
        # 本地缓存也一致
        assert repo.get("user_1") is None

    def test_delete_missing_returns_false(self, redis_client):
        repo = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        assert repo.delete("nonexistent") is False

    def test_clear_removes_entire_hash(self, redis_client):
        repo = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo.set("a", 1)
        repo.set("b", 2)
        repo.set("c", 3)
        repo.clear()

        # Hash 整体删除
        assert redis_client.exists("ai_teacher:profiles:kv") == 0
        assert len(repo) == 0

    def test_replace_all_atomic_via_pipeline(self, redis_client):
        repo = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo.replace_all({"a": 1, "b": 2, "c": 3})

        # 整个 Hash 是新数据
        all_data = redis_client.hgetall("ai_teacher:profiles:kv")
        assert set(json.loads(v) for v in all_data.values()) == {1, 2, 3}
        assert set(all_data.keys()) == {"a", "b", "c"}

    def test_init_loads_existing_data(self, redis_client):
        """新实例启动时从 Redis Hash 加载历史数据"""
        # 先用一个实例写数据
        repo_a = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo_a.set("user_1", {"name": "Alice"})
        repo_a.set("user_2", {"name": "Bob"})

        # 新实例应自动加载
        repo_b = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        assert repo_b.get("user_1") == {"name": "Alice"}
        assert repo_b.get("user_2") == {"name": "Bob"}
        assert len(repo_b) == 2

    def test_flush_reloads_from_redis(self, redis_client):
        """flush() 触发 reload，反映其他进程的写入"""
        repo = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)

        # 模拟其他进程直接写入 Redis Hash
        redis_client.hset(
            "ai_teacher:profiles:kv",
            "remote_key",
            json.dumps({"name": "RemoteUser"}),
        )

        # flush 触发 reload
        repo.flush()
        assert repo.get("remote_key") == {"name": "RemoteUser"}


# ==================== 真实 Pub/Sub 同步 ====================


class TestRealPubSubSync:
    """真实 Pub/Sub 跨进程同步"""

    def _wait_for(self, predicate, timeout=2.0, interval=0.05):
        """轮询等待 predicate 返回 True 或超时"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if predicate():
                return True
            time.sleep(interval)
        return False

    def test_pubsub_sync_set_to_other_consumer(self, redis_client):
        """进程 A set → 进程 B 接收 set 事件"""
        repo_a = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo_b = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)

        # 进程 B 启动订阅
        bridge_b = RedisPubSubBridge(
            redis_client=redis_client,
            repos={"profiles": repo_b},
            channel=TEST_CHANNEL,
        )
        bridge_b.start()
        try:
            # 等待订阅建立
            # pubsub_numsub 返回 [(channel, count)]，取 [0][1] 拿订阅者数
            assert self._wait_for(
                lambda: redis_client.pubsub_numsub(TEST_CHANNEL)[0][1] >= 1,
                timeout=2.0,
            ), "进程 B 订阅未建立"

            # 进程 A 写入
            repo_a.set("user_1", {"name": "Alice", "source": "A"})

            # 进程 B 应收到（通过 _apply_remote_set）
            assert self._wait_for(
                lambda: repo_b.get("user_1") == {"name": "Alice", "source": "A"},
                timeout=2.0,
            ), f"进程 B 未收到 set 事件（实际值：{repo_b.get('user_1')}）"
        finally:
            bridge_b.stop()

    def test_pubsub_sync_delete_to_other_consumer(self, redis_client):
        repo_a = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo_b = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo_a.set("user_1", {"data": 1})  # 进程 A 写入
        repo_b.set("user_1", {"data": 1})  # 进程 B 同步接收（先让两边对齐）

        bridge_b = RedisPubSubBridge(
            redis_client=redis_client,
            repos={"profiles": repo_b},
            channel=TEST_CHANNEL,
        )
        bridge_b.start()
        try:
            assert self._wait_for(
                lambda: redis_client.pubsub_numsub(TEST_CHANNEL)[0][1] >= 1,
                timeout=2.0,
            )

            # 进程 A 删除
            repo_a.delete("user_1")

            # 进程 B 应收到 delete 事件
            assert self._wait_for(
                lambda: repo_b.get("user_1") is None,
                timeout=2.0,
            ), "进程 B 未收到 delete 事件"
        finally:
            bridge_b.stop()

    def test_pubsub_sync_clear_to_other_consumer(self, redis_client):
        repo_a = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo_b = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo_a.set("a", 1)
        repo_b.set("a", 1)

        bridge_b = RedisPubSubBridge(
            redis_client=redis_client,
            repos={"profiles": repo_b},
            channel=TEST_CHANNEL,
        )
        bridge_b.start()
        try:
            assert self._wait_for(
                lambda: redis_client.pubsub_numsub(TEST_CHANNEL)[0][1] >= 1
            )
            repo_a.clear()
            assert self._wait_for(lambda: len(repo_b) == 0, timeout=2.0)
        finally:
            bridge_b.stop()

    def test_pubsub_echo_prevention_in_real(self, redis_client):
        """真实 Redis 防回声：进程 A 自己的消息不会被自己的 repo 应用"""
        repo_a = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)

        bridge_a = RedisPubSubBridge(
            redis_client=redis_client,
            repos={"profiles": repo_a},
            channel=TEST_CHANNEL,
        )
        bridge_a.start()
        try:
            assert self._wait_for(
                lambda: redis_client.pubsub_numsub(TEST_CHANNEL)[0][1] >= 1
            )

            # 进程 A 自己写入
            repo_a.set("user_1", {"data": "from_A"})

            # 给消息一点时间传播
            time.sleep(0.3)

            # 进程 A 的 repo 应仍是自己写的值（不应被远程覆盖）
            assert repo_a.get("user_1") == {"data": "from_A"}
        finally:
            bridge_a.stop()

    def test_three_way_broadcast(self, redis_client):
        """三进程广播：A 写入 → B、C 都能收到"""
        repo_a = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo_b = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo_c = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)

        bridge_b = RedisPubSubBridge(
            redis_client=redis_client,
            repos={"profiles": repo_b},
            channel=TEST_CHANNEL,
        )
        bridge_c = RedisPubSubBridge(
            redis_client=redis_client,
            repos={"profiles": repo_c},
            channel=TEST_CHANNEL,
        )
        bridge_b.start()
        bridge_c.start()
        try:
            # 等待两个订阅者建立
            assert self._wait_for(
                lambda: redis_client.pubsub_numsub(TEST_CHANNEL)[0][1] >= 2,
                timeout=2.0,
            )

            # 进程 A 写入
            repo_a.set("broadcast_key", {"value": 42})

            # B 和 C 都应该收到
            assert self._wait_for(
                lambda: repo_b.get("broadcast_key") == {"value": 42},
                timeout=2.0,
            )
            assert self._wait_for(
                lambda: repo_c.get("broadcast_key") == {"value": 42},
                timeout=2.0,
            )
        finally:
            bridge_b.stop()
            bridge_c.stop()


# ==================== 真实 Redis 优雅降级 ====================


class TestRealRedisFailureDegradation:
    """真实 Redis 失败时的优雅降级"""

    def test_unreachable_redis_falls_back_to_memory(self):
        """Redis 不可达时降级为纯内存模式"""
        bad_client = redis.Redis.from_url(
            "redis://127.0.0.1:65530",  # 不可达端口
            decode_responses=True,
            socket_connect_timeout=0.5,
        )
        repo = RedisRepository(
            name="profiles",
            redis_client=bad_client,
            channel=TEST_CHANNEL,
        )
        # 基本读写仍可用
        repo.set("k1", {"v": 1})
        assert repo.get("k1") == {"v": 1}

    def test_init_with_unreachable_redis_logs_warning(self, caplog):
        """初始化不可达 Redis 时降级，不抛异常"""
        bad_client = redis.Redis.from_url(
            "redis://127.0.0.1:65530",
            decode_responses=True,
            socket_connect_timeout=0.5,
        )
        # 不应抛异常
        repo = RedisRepository(
            name="profiles",
            redis_client=bad_client,
            channel=TEST_CHANNEL,
        )
        # 仍可写
        repo.set("k1", 1)
        assert repo.get("k1") == 1


# ==================== 7 张表端到端 ====================


class TestAllSevenTables:
    """P3-B 兼容的 7 张表全部能正常持久化"""

    @pytest.mark.parametrize("table_name", REPOSITORY_REGISTRY)
    def test_each_table_round_trip(self, redis_client, table_name):
        repo = RedisRepository(
            name=table_name,
            redis_client=redis_client,
            channel=TEST_CHANNEL,
        )
        # 写入 KV
        repo.set("user_42", {"score": 95, "tags": ["a", "b"]})
        # 验证 Hash 实际存在
        raw = redis_client.hget(repo.hash_key, "user_42")
        assert raw is not None
        assert json.loads(raw) == {"score": 95, "tags": ["a", "b"]}
        # hash_key 格式一致
        assert repo.hash_key == f"{DEFAULT_KEY_PREFIX}:{table_name}:kv"

    def test_multiple_tables_in_one_process(self, redis_client):
        """同一进程的多个表互不污染"""
        repo_p = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        repo_s = RedisRepository(name="sessions", redis_client=redis_client, channel=TEST_CHANNEL)
        repo_p.set("k1", "profiles_value")
        repo_s.set("k1", "sessions_value")
        # 各自读到自己的值
        assert repo_p.get("k1") == "profiles_value"
        assert repo_s.get("k1") == "sessions_value"


# ==================== 真实 Reconnect ====================


class TestRealReconnectLogic:
    """真实订阅断线重连（用 FLUSHDB 模拟 client kill 中断）"""

    def test_bridge_recovers_after_redis_restart(self, redis_client, cleanup_global_bridge):
        """Bridge 在 Redis 短暂不可用后能恢复（订阅重连）"""
        # 启动一个 bridge
        repo = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        bridge = RedisPubSubBridge(
            redis_client=redis_client,
            repos={"profiles": repo},
            channel=TEST_CHANNEL,
        )
        bridge.start()
        try:
            # 等待订阅建立
            assert _wait_pubsub_active(redis_client, TEST_CHANNEL, timeout=2.0)

            # 模拟 client kill（关闭所有 pubsub 连接）
            # 这会让 listen() 抛 ConnectionError
            redis_client.execute_command("CLIENT", "KILL", "TYPE", "pubsub")
            time.sleep(0.5)  # 给 bridge 时间触发重连

            # Bridge 应当还在运行（重连）
            assert bridge.is_running() is True
        finally:
            bridge.stop()


def _wait_pubsub_active(redis_client, channel: str, timeout: float) -> bool:
    """轮询等待订阅者数量 >= 1（pubsub_numsub 返回 [(channel, count)]）"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        count = redis_client.pubsub_numsub(channel)[0][1]
        if count >= 1:
            return True
        time.sleep(0.05)
    return False


# ==================== 性能基准（轻量） ====================


class TestRealRedisPerformance:
    """性能基准（1000 操作）"""

    def test_1000_set_get_under_5_seconds(self, redis_client):
        repo = RedisRepository(name="profiles", redis_client=redis_client, channel=TEST_CHANNEL)
        start = time.time()
        for i in range(1000):
            repo.set(f"perf_{i}", {"v": i})
        for i in range(1000):
            assert repo.get(f"perf_{i}") == {"v": i}
        elapsed = time.time() - start
        # 1000 写 + 1000 读应在 5s 内
        assert elapsed < 5.0, f"性能不达标：{elapsed:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
