"""
企业API网关性能测试
测试系统的性能表现和负载处理能力
"""

from concurrent.futures import ThreadPoolExecutor
import statistics
import time
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
import pytest

from main import app

client = TestClient(app)


class TestEnterpriseAPIPerformance:
    """企业API性能测试类"""

    def setup_method(self):
        """测试方法前置设置"""
        self.test_client_id = "perf_test_client"
        self.test_device_id = "perf_device_123"

    def test_single_request_response_time(self):
        """测试单个请求响应时间"""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()

        response_time = (end_time - start_time) * 1000  # 转换为毫秒

        assert response.status_code == 200
        assert response_time < 100  # 响应时间应该小于100ms

    def test_concurrent_requests(self):
        """测试并发请求处理能力"""

        def make_request():
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()
            return (end_time - start_time) * 1000, response.status_code

        # 并发执行10个请求
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]

        response_times = [result[0] for result in results]
        status_codes = [result[1] for result in results]

        # 验证所有请求都成功
        assert all(code == 200 for code in status_codes)

        # 验证平均响应时间
        avg_response_time = statistics.mean(response_times)
        assert avg_response_time < 200  # 平均响应时间应该小于200ms

        # 验证最大响应时间
        max_response_time = max(response_times)
        assert max_response_time < 500  # 最大响应时间应该小于500ms

    @pytest.mark.slow
    def test_load_testing(self):
        """负载测试 - 发送大量请求"""
        request_count = 100
        successful_requests = 0
        response_times = []

        for i in range(request_count):
            start_time = time.time()
            response = client.get("/health")
            end_time = time.time()

            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)

            if response.status_code == 200:
                successful_requests += 1

        # 计算性能指标
        success_rate = (successful_requests / request_count) * 100
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = sorted(response_times)[int(0.95 * len(response_times))]

        print(f"\n负载测试结果:")
        print(f"总请求数: {request_count}")
        print(f"成功请求数: {successful_requests}")
        print(f"成功率: {success_rate:.2f}%")
        print(f"平均响应时间: {avg_response_time:.2f}ms")
        print(f"中位数响应时间: {median_response_time:.2f}ms")
        print(f"95th百分位响应时间: {p95_response_time:.2f}ms")

        # 性能断言
        assert success_rate >= 95  # 成功率至少95%
        assert avg_response_time < 100  # 平均响应时间小于100ms
        assert p95_response_time < 300  # 95%的请求响应时间小于300ms

    def test_memory_usage_during_requests(self):
        """测试请求过程中的内存使用情况"""
        import os

        import psutil

        # 获取初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行一系列请求
        for _ in range(50):
            client.get("/health")

        # 获取最终内存使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"\n内存使用情况:")
        print(f"初始内存: {initial_memory:.2f} MB")
        print(f"最终内存: {final_memory:.2f} MB")
        print(f"内存增长: {memory_increase:.2f} MB")

        # 内存增长应该在合理范围内
        assert memory_increase < 10  # 内存增长不超过10MB

    @pytest.mark.parametrize("endpoint", ["/", "/health", "/docs"])
    def test_different_endpoints_performance(self, endpoint):
        """测试不同端点的性能表现"""
        response_times = []

        # 对每个端点执行多次请求
        for _ in range(20):
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()

            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)

            assert response.status_code == 200

        avg_time = statistics.mean(response_times)
        max_time = max(response_times)

        print(f"\n端点 {endpoint} 性能:")
        print(f"平均响应时间: {avg_time:.2f}ms")
        print(f"最大响应时间: {max_time:.2f}ms")

        # 静态内容端点应该更快
        if endpoint in ["/", "/health"]:
            assert avg_time < 50
            assert max_time < 100
        else:
            # 文档端点可能稍慢
            assert avg_time < 200
            assert max_time < 500


class TestDatabasePerformance:
    """数据库性能测试"""

    @patch("utils.database.SessionLocal")
    def test_database_connection_pooling(self, mock_session_local):
        """测试数据库连接池性能"""
        from utils.database import get_db

        # 模拟数据库会话
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        connection_times = []

        # 测试多次数据库连接获取
        for _ in range(50):
            start_time = time.time()
            db_generator = get_db()
            next(db_generator)
            end_time = time.time()

            connection_time = (end_time - start_time) * 1000
            connection_times.append(connection_time)

            # 清理会话
            try:
                next(db_generator, None)
            except StopIteration:
                pass

        avg_connection_time = statistics.mean(connection_times)
        print(f"\n数据库连接性能:")
        print(f"平均连接时间: {avg_connection_time:.2f}ms")

        # 连接获取应该很快
        assert avg_connection_time < 10

    def test_model_serialization_performance(self):
        """测试模型序列化性能"""
        from models.enterprise_models import EnterpriseClient

        # 创建测试数据
        clients = []
        for i in range(1000):
            client = EnterpriseClient(
                client_name=f"Test Client {i}",
                client_id=f"ent_test_{i}",
                redirect_uris=f"https://test{i}.com/callback",
                api_quota_limit=1000 + i,
                contact_email=f"admin{i}@test.com",
            )
            clients.append(client)

        # 测试序列化性能
        start_time = time.time()
        serialized_data = [client.to_dict() for client in clients]
        end_time = time.time()

        serialization_time = (end_time - start_time) * 1000
        print(f"\n模型序列化性能:")
        print(f"序列化1000个对象耗时: {serialization_time:.2f}ms")
        print(f"平均每对象序列化时间: {serialization_time/1000:.4f}ms")

        # 序列化应该高效
        assert serialization_time < 1000  # 1000个对象序列化不超过1秒
        assert len(serialized_data) == 1000


class TestSecurityPerformance:
    """安全组件性能测试"""

    def test_jwt_verification_performance(self):
        """测试JWT验证性能"""
        from utils.jwt_utils import JWTUtil

        jwt_util = JWTUtil()

        # 创建测试令牌
        test_data = {"client_id": "perf_test", "scope": "api:read"}
        token = jwt_util.create_access_token(test_data)

        verification_times = []

        # 测试多次JWT验证
        for _ in range(1000):
            start_time = time.time()
            payload = jwt_util.verify_token(token)
            end_time = time.time()

            verification_time = (end_time - start_time) * 1000
            verification_times.append(verification_time)

            assert payload is not None
            assert payload["client_id"] == "perf_test"

        avg_verification_time = statistics.mean(verification_times)
        print(f"\nJWT验证性能:")
        print(f"平均验证时间: {avg_verification_time:.4f}ms")
        print(f"每秒可验证次数: {1000/avg_verification_time:.0f}")

        # JWT验证应该很快
        assert avg_verification_time < 1  # 平均验证时间小于1ms


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s 显示print输出
