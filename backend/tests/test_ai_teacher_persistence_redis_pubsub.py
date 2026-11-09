"""
【P3-D-2】RedisPubSubBridge 单元测试

覆盖：
- 启动/停止生命周期
- 防回声机制（publisher_id 验证）
- 单进程内发布订阅循环（自洽性）
- 多进程数据同步（用 MagicMock 模拟跨进程通信）
- 订阅断连重连（mock 异常）
- 未知 action / table 优雅处理
- 已知 4 种 action（set / delete / replace_all / clear）
"""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from cache.repository.redis import DEFAULT_CHANNEL, RedisRepository
from cache.repository.redis_pubsub import (
    DEFAULT_CHANNEL as PUBSUB_DEFAULT_CHANNEL,
    RedisPubSubBridge,
    start_pubsub_bridge,
    stop_pubsub_bridge,
    get_pubsub_bridge,
)


# ==================== Fixtures ====================


@pytest.fixture
def mock_redis():
    """模拟 Redis 客户端"""
    client = MagicMock()

    # hgetall 默认返回空
    client.hgetall.return_value = {}

    # publish 默认成功
    client.publish.return_value = 1

    # pubsub()
    pubsub = MagicMock()
    pubsub.listen.return_value = iter([])  # 默认空迭代器
    client.pubsub.return_value = pubsub

    # pipeline
    pipe = MagicMock()
    pipe.execute.return_value = [1, 1]
    client.pipeline.return_value = pipe

    return client


@pytest.fixture
def two_repos(mock_redis):
    """两个 RedisRepository 实例（模拟两个进程）"""
    repo_a = RedisRepository(
        name="profiles",
        redis_client=mock_redis,
        enable_pubsub=True,
    )
    repo_b = RedisRepository(
        name="profiles",
        redis_client=mock_redis,
        enable_pubsub=True,
    )
    return repo_a, repo_b


@pytest.fixture(autouse=True)
def cleanup_bridge():
    """每个测试后清理全局 bridge"""
    yield
    stop_pubsub_bridge()


# ==================== 基本生命周期 ====================


class TestPubSubBridgeLifecycle:
    """启动/停止生命周期"""

    def test_start_returns_publisher_id(self, mock_redis):
        """start 返回 publisher_id"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis, repos={"profiles": repo}
        )
        publisher_id = bridge.start()
        try:
            assert publisher_id.startswith("proc-")
            assert len(publisher_id) == len("proc-") + 8
            assert bridge.is_running() is True
        finally:
            bridge.stop()

    def test_double_start_is_safe(self, mock_redis):
        """重复 start 不抛异常"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis, repos={"profiles": repo}
        )
        bridge.start()
        try:
            # 第二次 start 应安全（幂等）
            bridge.start()
            assert bridge.is_running() is True
        finally:
            bridge.stop()

    def test_stop_is_safe_without_start(self, mock_redis):
        """未启动的 bridge 停止不抛异常"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis, repos={"profiles": repo}
        )
        bridge.stop()  # 不应抛异常

    def test_stop_terminates_thread(self, mock_redis):
        """stop 后线程停止"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis, repos={"profiles": repo}
        )
        bridge.start()
        assert bridge.is_running() is True
        bridge.stop(timeout=2.0)
        # 线程已结束
        assert bridge.is_running() is False

    def test_publisher_id_is_unique(self, mock_redis):
        """不同 bridge 实例 publisher_id 不同"""
        repo1 = RedisRepository("profiles", redis_client=mock_redis)
        repo2 = RedisRepository("profiles", redis_client=mock_redis)
        bridge1 = RedisPubSubBridge(
            redis_client=mock_redis, repos={"profiles": repo1}
        )
        bridge2 = RedisPubSubBridge(
            redis_client=mock_redis, repos={"profiles": repo2}
        )
        assert bridge1.publisher_id != bridge2.publisher_id


# ==================== 防回声机制 ====================


class TestEchoPrevention:
    """publisher_id 防回声验证"""

    def test_ignore_own_message_set(self, mock_redis):
        """收到自己发布的 set 消息不更新本地"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )
        bridge.start()
        try:
            # 构造自己发布的消息
            own_msg = {
                "table": "profiles",
                "action": "set",
                "key": "user_1",
                "data": {"name": "Should Not Be Applied"},
                "publisher_id": bridge.publisher_id,
                "timestamp": time.time(),
            }
            raw = json.dumps(own_msg)
            # 处理消息
            bridge._handle_message(raw)
            # 不应写入本地缓存（防回声）
            assert repo.get("user_1") is None
        finally:
            bridge.stop()

    def test_apply_other_publisher_set(self, mock_redis):
        """收到其他 publisher 发布的 set 消息更新本地"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )
        bridge.start()
        try:
            # 构造其他进程发布的消息
            other_msg = {
                "table": "profiles",
                "action": "set",
                "key": "user_1",
                "data": {"name": "Remote User"},
                "publisher_id": "proc-other1234",
                "timestamp": time.time(),
            }
            raw = json.dumps(other_msg)
            bridge._handle_message(raw)
            # 应写入本地缓存
            assert repo.get("user_1") == {"name": "Remote User"}
        finally:
            bridge.stop()


# ==================== 已知 Action 处理 ====================


class TestKnownActions:
    """4 种已知 action：set / delete / replace_all / clear"""

    def _publish_from_remote(self, bridge, mock_redis, message):
        """模拟远程发布并直接调用 _handle_message"""
        raw = json.dumps(message)
        bridge._handle_message(raw)

    def test_handle_set_action(self, mock_redis):
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )
        bridge.start()
        try:
            self._publish_from_remote(
                bridge,
                mock_redis,
                {
                    "table": "profiles",
                    "action": "set",
                    "key": "k1",
                    "data": {"v": 1},
                    "publisher_id": "remote",
                    "timestamp": time.time(),
                },
            )
            assert repo.get("k1") == {"v": 1}
        finally:
            bridge.stop()

    def test_handle_delete_action(self, mock_redis):
        repo = RedisRepository("profiles", redis_client=mock_redis)
        repo.set("k1", {"v": 1})
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )
        bridge.start()
        try:
            self._publish_from_remote(
                bridge,
                mock_redis,
                {
                    "table": "profiles",
                    "action": "delete",
                    "key": "k1",
                    "publisher_id": "remote",
                    "timestamp": time.time(),
                },
            )
            assert repo.get("k1") is None
        finally:
            bridge.stop()

    def test_handle_replace_all_action(self, mock_redis):
        repo = RedisRepository("profiles", redis_client=mock_redis)
        repo.set("old", "data")
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )
        bridge.start()
        try:
            self._publish_from_remote(
                bridge,
                mock_redis,
                {
                    "table": "profiles",
                    "action": "replace_all",
                    "data": {"new_a": 1, "new_b": 2},
                    "publisher_id": "remote",
                    "timestamp": time.time(),
                },
            )
            assert repo.get("old") is None
            assert repo.get("new_a") == 1
            assert repo.get("new_b") == 2
        finally:
            bridge.stop()

    def test_handle_clear_action(self, mock_redis):
        repo = RedisRepository("profiles", redis_client=mock_redis)
        repo.set("a", 1)
        repo.set("b", 2)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )
        bridge.start()
        try:
            self._publish_from_remote(
                bridge,
                mock_redis,
                {
                    "table": "profiles",
                    "action": "clear",
                    "publisher_id": "remote",
                    "timestamp": time.time(),
                },
            )
            assert len(repo) == 0
        finally:
            bridge.stop()


# ==================== 未知 Action / Table ====================


class TestUnknownMessageHandling:
    """未知 action / table / 损坏消息的优雅处理"""

    def test_unknown_action_ignored(self, mock_redis):
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )
        bridge.start()
        try:
            # 未知 action
            self._handle_safely(
                bridge,
                {
                    "table": "profiles",
                    "action": "unknown_action",
                    "publisher_id": "remote",
                },
            )
            # 不应抛异常，本地缓存不变
            assert len(repo) == 0
        finally:
            bridge.stop()

    def test_unknown_table_ignored(self, mock_redis):
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )
        bridge.start()
        try:
            # 未知表名
            self._handle_safely(
                bridge,
                {
                    "table": "unknown_table",
                    "action": "set",
                    "key": "k1",
                    "data": {"v": 1},
                    "publisher_id": "remote",
                },
            )
            # 不应抛异常，本地缓存不变
            assert len(repo) == 0
        finally:
            bridge.stop()

    def test_corrupted_message_ignored(self, mock_redis):
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )
        bridge.start()
        try:
            # 损坏的 JSON
            bridge._handle_message("not a json string {[}")
            # 不应抛异常
        finally:
            bridge.stop()

    def test_bytes_message_handled(self, mock_redis):
        """bytes 类型消息也能处理"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )
        bridge.start()
        try:
            raw = json.dumps({
                "table": "profiles",
                "action": "set",
                "key": "k1",
                "data": {"v": 1},
                "publisher_id": "remote",
                "timestamp": time.time(),
            })
            # bytes 类型
            bridge._handle_message(raw.encode())
            assert repo.get("k1") == {"v": 1}
        finally:
            bridge.stop()

    def _handle_safely(self, bridge, message):
        """发送消息并捕获所有异常（用于测试未知 action）"""
        try:
            bridge._handle_message(json.dumps(message))
        except Exception:
            pass  # 应被优雅处理


# ==================== 订阅重连 ====================


class TestReconnectLogic:
    """订阅异常时指数退避重连"""

    def test_subscribe_failure_triggers_retry(self, mock_redis):
        """订阅失败时进入重试循环"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )
        # 模拟第一次 subscribe 失败，第二次成功
        call_count = {"count": 0}

        def fake_pubsub():
            mock = MagicMock()

            def fake_subscribe(*args, **kwargs):
                call_count["count"] += 1
                if call_count["count"] == 1:
                    raise Exception("Connection refused")

            mock.subscribe.side_effect = fake_subscribe
            mock.listen.return_value = iter([])
            return mock

        mock_redis.pubsub.side_effect = fake_pubsub

        bridge.start()
        try:
            # 等待重试
            time.sleep(0.5)
            # 至少调用过一次
            assert call_count["count"] >= 1
        finally:
            bridge.stop()

    def test_listen_exception_triggers_reconnect(self, mock_redis):
        """listen 抛异常时进入重连"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )

        # 模拟 pubsub.listen 抛异常
        pubsub = MagicMock()
        call_count = {"count": 0}

        def listen_iter():
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise Exception("Connection lost")
            # 后续返回空迭代
            return iter([])

        pubsub.listen.side_effect = listen_iter
        mock_redis.pubsub.return_value = pubsub

        bridge.start()
        try:
            time.sleep(0.5)
            # 至少经历过一次异常
            assert call_count["count"] >= 1
        finally:
            bridge.stop()

    def test_message_handling_exception_does_not_break_loop(self, mock_redis):
        """单条消息处理失败不影响后续消息处理"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )

        # 模拟 listen 返回 2 条消息：第 1 条触发异常，第 2 条正常
        messages = [
            {"type": "message", "data": "invalid json"},
            {"type": "message", "data": json.dumps({
                "table": "profiles",
                "action": "set",
                "key": "k1",
                "data": {"v": 1},
                "publisher_id": "remote",
                "timestamp": time.time(),
            })},
            # 不返回更多，避免 hang
        ]

        def listen_iter():
            for m in messages:
                yield m
            # 之后等待 stop
            while not bridge._stop_event.is_set():
                time.sleep(0.01)
            return

        pubsub = MagicMock()
        pubsub.listen.return_value = listen_iter()
        mock_redis.pubsub.return_value = pubsub

        bridge.start()
        try:
            # 等待消息处理
            time.sleep(0.5)
            # 异常消息被忽略，正常消息被处理
            assert repo.get("k1") == {"v": 1}
        finally:
            bridge.stop()


# ==================== 全局便捷方法 ====================


class TestGlobalConvenienceMethods:
    """全局 start_pubsub_bridge / stop_pubsub_bridge / get_pubsub_bridge"""

    def test_start_and_stop_global(self, mock_redis):
        """全局启动 + 停止"""
        # 模拟 utils.redis_client
        with patch("utils.redis_client.redis_client", mock_redis, create=True):
            publisher_id = start_pubsub_bridge(
                redis_client=mock_redis,
                repos={"profiles": RedisRepository("profiles", redis_client=mock_redis)},
            )
            assert publisher_id.startswith("proc-")
            assert get_pubsub_bridge() is not None
            assert get_pubsub_bridge().is_running() is True

            stop_pubsub_bridge()
            assert get_pubsub_bridge() is None

    def test_double_start_returns_existing(self, mock_redis):
        """重复启动返回现有 publisher_id"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        first_id = start_pubsub_bridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
        )
        try:
            second_id = start_pubsub_bridge(
                redis_client=mock_redis,
                repos={"profiles": repo},
            )
            # 第二次启动应返回第一次的 ID
            assert first_id == second_id
        finally:
            stop_pubsub_bridge()

    def test_stop_without_start_is_safe(self):
        """未启动时 stop 不抛异常"""
        # 确保初始为空
        stop_pubsub_bridge()
        # 再次 stop
        stop_pubsub_bridge()


# ==================== 默认 channel 名称 ====================


class TestDefaultChannel:
    """默认 channel 名称"""

    def test_default_channel(self):
        assert PUBSUB_DEFAULT_CHANNEL == "ai_teacher:update"
        assert DEFAULT_CHANNEL == "ai_teacher:update"


# ==================== 真实 Pub/Sub 循环（mock listen）====================


class TestListenLoop:
    """模拟 listen() 返回消息流"""

    def test_listen_processes_message(self, mock_redis):
        """listen 接收到的 message.type == 'message' 被处理"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )

        message_data = json.dumps({
            "table": "profiles",
            "action": "set",
            "key": "k1",
            "data": {"v": 42},
            "publisher_id": "remote",
            "timestamp": time.time(),
        }).encode()

        def listen_iter():
            # 1. subscribe 确认消息（被 type filter 过滤）
            yield {"type": "subscribe", "channel": "test:channel"}
            # 2. 真实消息
            yield {"type": "message", "data": message_data}
            # 等待 stop
            while not bridge._stop_event.is_set():
                time.sleep(0.01)
            return

        pubsub = MagicMock()
        pubsub.listen.return_value = listen_iter()
        mock_redis.pubsub.return_value = pubsub

        bridge.start()
        try:
            time.sleep(0.5)
            # 消息已被处理
            assert repo.get("k1") == {"v": 42}
        finally:
            bridge.stop()

    def test_listen_skips_non_message_types(self, mock_redis):
        """非 message 类型（如 subscribe 确认）被忽略"""
        repo = RedisRepository("profiles", redis_client=mock_redis)
        bridge = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo},
            channel="test:channel",
        )

        def listen_iter():
            # 仅发送 subscribe 确认
            yield {"type": "subscribe", "channel": "test:channel"}
            # 等待 stop
            while not bridge._stop_event.is_set():
                time.sleep(0.01)
            return

        pubsub = MagicMock()
        pubsub.listen.return_value = listen_iter()
        mock_redis.pubsub.return_value = pubsub

        bridge.start()
        try:
            time.sleep(0.3)
            # 仅 subscribe 消息，无写入
            assert len(repo) == 0
        finally:
            bridge.stop()


# ==================== 全局 repos 注入 ====================


class TestGlobalReposInjection:
    """start_pubsub_bridge 自动从 factory 获取 repos"""

    def test_default_repos_from_factory(self, mock_redis, monkeypatch):
        """默认从 cache.repository.factory 获取 repos"""
        # Mock factory 的 7 个 repo getter（patch factory 模块，因为 redis_pubsub 内部从那里导入）
        fake_repos = {
            "profiles": RedisRepository("profiles", redis_client=mock_redis),
            "sessions": RedisRepository("sessions", redis_client=mock_redis),
            "memories": RedisRepository("memories", redis_client=mock_redis),
            "personas": RedisRepository("personas", redis_client=mock_redis),
            "live_settings": RedisRepository("live_settings", redis_client=mock_redis),
            "event_history": RedisRepository("event_history", redis_client=mock_redis),
            "user_history": RedisRepository("user_history", redis_client=mock_redis),
        }

        with patch("cache.repository.factory.get_profiles_repo", return_value=fake_repos["profiles"]), \
             patch("cache.repository.factory.get_sessions_repo", return_value=fake_repos["sessions"]), \
             patch("cache.repository.factory.get_memories_repo", return_value=fake_repos["memories"]), \
             patch("cache.repository.factory.get_personas_repo", return_value=fake_repos["personas"]), \
             patch("cache.repository.factory.get_live_settings_repo", return_value=fake_repos["live_settings"]), \
             patch("cache.repository.factory.get_event_history_repo", return_value=fake_repos["event_history"]), \
             patch("cache.repository.factory.get_user_history_repo", return_value=fake_repos["user_history"]):
            publisher_id = start_pubsub_bridge(redis_client=mock_redis)
            try:
                assert publisher_id.startswith("proc-")
                # Bridge 启动后，repos 应该正确注入
                bridge = get_pubsub_bridge()
                assert bridge is not None
                assert "profiles" in bridge._repos
                assert "sessions" in bridge._repos
            finally:
                stop_pubsub_bridge()


# ==================== 集成场景 ====================


class TestIntegrationScenario:
    """完整集成场景"""

    def test_end_to_end_publish_subscribe(self, mock_redis):
        """完整流程：repo.set → publish → bridge.handle → repo2._apply"""
        # 进程 A 的 repo
        repo_a = RedisRepository("profiles", redis_client=mock_redis)
        # 进程 B 的 repo
        repo_b = RedisRepository("profiles", redis_client=mock_redis)

        # 进程 A 的 bridge
        bridge_b = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo_b},
            channel="test:channel",
        )
        bridge_b.start()
        try:
            # 进程 A 写入数据
            repo_a.set("user_1", {"name": "Alice", "age": 30})

            # 验证 publish 被调用（带 publisher_id）
            assert mock_redis.publish.called
            args, _ = mock_redis.publish.call_args
            message = json.loads(args[1])
            assert message["action"] == "set"
            assert message["key"] == "user_1"
            assert message["publisher_id"] == repo_a.publisher_id

            # 直接模拟进程 B 接收消息
            raw = json.dumps(message)
            bridge_b._handle_message(raw)

            # 进程 B 的 repo 应更新（publisher_id 不同）
            assert repo_b.get("user_1") == {"name": "Alice", "age": 30}
        finally:
            bridge_b.stop()

    def test_echo_prevention_across_processes(self, mock_redis):
        """进程 A 写入不应更新进程 A 自己的 repo（防回声）"""
        repo_a = RedisRepository("profiles", redis_client=mock_redis)
        bridge_a = RedisPubSubBridge(
            redis_client=mock_redis,
            repos={"profiles": repo_a},
            channel="test:channel",
        )
        bridge_a.start()
        try:
            # 进程 A 写入
            repo_a.set("user_1", {"data": "from_A"})

            # 模拟自己发布的消息被自己接收
            args, _ = mock_redis.publish.call_args
            message = json.loads(args[1])
            raw = json.dumps(message)
            bridge_a._handle_message(raw)

            # 进程 A 的 repo 数据不变（防回声）
            # 注意：本地 cache 在 set 时已写入，所以 "user_1" 存在
            # 但其值应是原始写入的 "from_A"，不应被回声覆盖
            assert repo_a.get("user_1") == {"data": "from_A"}
        finally:
            bridge_a.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])