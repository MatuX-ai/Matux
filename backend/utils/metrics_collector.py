"""
Prometheus指标收集配置
为APM监控提供指标收集功能
"""

import logging

try:
    from prometheus_client import Counter, Gauge, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Prometheus client not available")

logger = logging.getLogger(__name__)


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self._initialized = False
        self._metrics = {}
        self._histogram_buckets = (
            0.005,
            0.01,
            0.025,
            0.05,
            0.075,
            0.1,
            0.25,
            0.5,
            0.75,
            1.0,
            2.5,
            5.0,
            7.5,
            10.0,
            float("inf"),
        )
        self._initialize_metrics()

    def _initialize_metrics(self):
        """初始化Prometheus指标"""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available, metrics collection disabled")
            return

        try:
            # HTTP请求相关指标
            self._metrics["http_requests_total"] = Counter(
                "http_requests_total",
                "Total HTTP requests",
                ["method", "endpoint", "status_code"],
            )

            self._metrics["http_request_duration_seconds"] = Histogram(
                "http_request_duration_seconds",
                "HTTP request duration in seconds",
                ["method", "endpoint"],
                buckets=self._histogram_buckets,
            )

            self._metrics["http_request_errors_total"] = Counter(
                "http_request_errors_total",
                "Total HTTP request errors",
                ["method", "endpoint", "error_type"],
            )

            # 推荐系统相关指标
            self._metrics["recommendation_requests_total"] = Counter(
                "recommendation_requests_total",
                "Total recommendation requests",
                ["algorithm", "user_type"],
            )

            self._metrics["recommendation_duration_seconds"] = Histogram(
                "recommendation_duration_seconds",
                "Recommendation processing duration in seconds",
                ["algorithm"],
                buckets=self._histogram_buckets,
            )

            self._metrics["recommendation_success_total"] = Counter(
                "recommendation_success_total",
                "Successful recommendation requests",
                ["algorithm"],
            )

            self._metrics["recommendation_errors_total"] = Counter(
                "recommendation_errors_total",
                "Failed recommendation requests",
                ["algorithm", "error_type"],
            )

            # AI模型相关指标
            self._metrics["ai_model_calls_total"] = Counter(
                "ai_model_calls_total",
                "Total AI model calls",
                ["model_name", "operation"],
            )

            self._metrics["ai_model_duration_seconds"] = Histogram(
                "ai_model_duration_seconds",
                "AI model call duration in seconds",
                ["model_name"],
                buckets=self._histogram_buckets,
            )

            self._metrics["ai_model_tokens_used"] = Counter(
                "ai_model_tokens_used", "Total tokens used by AI models", ["model_name"]
            )

            # 数据库相关指标
            self._metrics["db_operations_total"] = Counter(
                "db_operations_total",
                "Total database operations",
                ["operation_type", "table"],
            )

            self._metrics["db_operation_duration_seconds"] = Histogram(
                "db_operation_duration_seconds",
                "Database operation duration in seconds",
                ["operation_type"],
                buckets=self._histogram_buckets,
            )

            # 系统指标
            self._metrics["active_users"] = Gauge(
                "active_users", "Number of active users"
            )

            self._metrics["memory_usage_bytes"] = Gauge(
                "memory_usage_bytes", "Current memory usage in bytes"
            )

            self._metrics["cpu_usage_percent"] = Gauge(
                "cpu_usage_percent", "Current CPU usage percentage"
            )

            self._initialized = True
            logger.info("Prometheus metrics initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Prometheus metrics: {e}")

    def record_http_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """记录HTTP请求指标"""
        if not self._initialized:
            return

        try:
            # 记录请求数量
            self._metrics["http_requests_total"].labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).inc()

            # 记录请求持续时间
            self._metrics["http_request_duration_seconds"].labels(
                method=method, endpoint=endpoint
            ).observe(duration)

        except Exception as e:
            logger.warning(f"Failed to record HTTP metrics: {e}")

    def record_http_error(self, method: str, endpoint: str, error_type: str):
        """记录HTTP错误指标"""
        if not self._initialized:
            return

        try:
            self._metrics["http_request_errors_total"].labels(
                method=method, endpoint=endpoint, error_type=error_type
            ).inc()
        except Exception as e:
            logger.warning(f"Failed to record HTTP error metrics: {e}")

    def record_recommendation_request(
        self, algorithm: str, user_type: str, success: bool, duration: float
    ):
        """记录推荐请求指标"""
        if not self._initialized:
            return

        try:
            # 记录请求数量
            self._metrics["recommendation_requests_total"].labels(
                algorithm=algorithm, user_type=user_type
            ).inc()

            # 记录成功或失败
            if success:
                self._metrics["recommendation_success_total"].labels(
                    algorithm=algorithm
                ).inc()
            else:
                self._metrics["recommendation_errors_total"].labels(
                    algorithm=algorithm, error_type="unknown"
                ).inc()

            # 记录处理时间
            self._metrics["recommendation_duration_seconds"].labels(
                algorithm=algorithm
            ).observe(duration)

        except Exception as e:
            logger.warning(f"Failed to record recommendation metrics: {e}")

    def record_ai_model_call(
        self, model_name: str, operation: str, duration: float, tokens_used: int = 0
    ):
        """记录AI模型调用指标"""
        if not self._initialized:
            return

        try:
            # 记录调用次数
            self._metrics["ai_model_calls_total"].labels(
                model_name=model_name, operation=operation
            ).inc()

            # 记录调用持续时间
            self._metrics["ai_model_duration_seconds"].labels(
                model_name=model_name
            ).observe(duration)

            # 记录token使用量
            if tokens_used > 0:
                self._metrics["ai_model_tokens_used"].labels(model_name=model_name).inc(
                    tokens_used
                )

        except Exception as e:
            logger.warning(f"Failed to record AI model metrics: {e}")

    def record_db_operation(
        self, operation_type: str, table: str, duration: float, success: bool = True
    ):
        """记录数据库操作指标"""
        if not self._initialized:
            return

        try:
            # 记录操作次数
            self._metrics["db_operations_total"].labels(
                operation_type=operation_type, table=table
            ).inc()

            # 记录操作持续时间
            self._metrics["db_operation_duration_seconds"].labels(
                operation_type=operation_type
            ).observe(duration)

        except Exception as e:
            logger.warning(f"Failed to record DB metrics: {e}")

    def update_system_metrics(
        self, active_users: int, memory_bytes: int, cpu_percent: float
    ):
        """更新系统指标"""
        if not self._initialized:
            return

        try:
            self._metrics["active_users"].set(active_users)
            self._metrics["memory_usage_bytes"].set(memory_bytes)
            self._metrics["cpu_usage_percent"].set(cpu_percent)
        except Exception as e:
            logger.warning(f"Failed to update system metrics: {e}")


# 全局指标收集器实例
metrics_collector = MetricsCollector()


# 便捷函数
def record_recommendation_metrics(
    algorithm: str, duration: float, success: bool = True, user_type: str = "regular"
):
    """记录推荐指标的便捷函数"""
    metrics_collector.record_recommendation_request(
        algorithm, user_type, success, duration
    )


def record_ai_metrics(
    model_name: str, operation: str, duration: float, tokens_used: int = 0
):
    """记录AI指标的便捷函数"""
    metrics_collector.record_ai_model_call(model_name, operation, duration, tokens_used)


def record_http_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """记录HTTP指标的便捷函数"""
    metrics_collector.record_http_request(method, endpoint, status_code, duration)


def record_db_metrics(operation_type: str, table: str, duration: float):
    """记录数据库指标的便捷函数"""
    metrics_collector.record_db_operation(operation_type, table, duration)
