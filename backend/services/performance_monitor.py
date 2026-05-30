"""
AI 能力组件性能监控服务
监控模型调用延迟、QPS、成功率等指标
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
import logging
import threading
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """指标数据点"""

    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class ModelMetrics:
    """模型性能指标"""

    model_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_inference_time_ms: float = 0.0
    last_request_time: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests * 100

    @property
    def avg_inference_time_ms(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_inference_time_ms / self.successful_requests

    @property
    def qps(self) -> float:
        """计算每秒请求数（最近 1 分钟）"""
        if not self.last_request_time:
            return 0.0

        now = datetime.utcnow()
        time_diff = (now - self.last_request_time).total_seconds()
        if time_diff < 60:
            return self.total_requests / max(time_diff, 1)
        return 0.0


class PerformanceMonitor:
    """
    性能监控器

    功能:
    1. 记录模型调用指标
    2. 计算 QPS、延迟、成功率
    3. 提供实时监控数据
    4. 支持告警阈值
    """

    _instance: Optional["PerformanceMonitor"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "PerformanceMonitor":
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.model_metrics: Dict[str, ModelMetrics] = {}
        self.metrics_history: Dict[str, List[MetricPoint]] = defaultdict(list)
        self.history_max_size = 1000  # 每个指标最多保留的点数
        self._lock = threading.Lock()

        logger.info("✅ 性能监控器初始化完成")

    def record_request(
        self,
        model_name: str,
        inference_time_ms: float,
        success: bool = True,
        task_type: Optional[str] = None,
    ):
        """
        记录一次模型调用

        Args:
            model_name: 模型名称
            inference_time_ms: 推理耗时 (ms)
            success: 是否成功
            task_type: 任务类型
        """
        with self._lock:
            now = datetime.utcnow()

            # 更新模型指标
            if model_name not in self.model_metrics:
                self.model_metrics[model_name] = ModelMetrics(model_name=model_name)

            metrics = self.model_metrics[model_name]
            metrics.total_requests += 1
            metrics.last_request_time = now

            if success:
                metrics.successful_requests += 1
                metrics.total_inference_time_ms += inference_time_ms
            else:
                metrics.failed_requests += 1

            # 记录历史数据
            point = MetricPoint(
                timestamp=now,
                value=inference_time_ms,
                labels={
                    "model": model_name,
                    "task_type": task_type or "unknown",
                    "success": str(success),
                },
            )

            history = self.metrics_history[model_name]
            history.append(point)

            # 限制历史数据大小
            if len(history) > self.history_max_size:
                history.pop(0)

            # 记录日志
            status = "✅" if success else "❌"
            logger.debug(f"{status} {model_name}: {inference_time_ms:.2f}ms")

    def get_model_metrics(self, model_name: str) -> Optional[ModelMetrics]:
        """获取模型性能指标"""
        with self._lock:
            return self.model_metrics.get(model_name)

    def get_all_models_metrics(self) -> Dict[str, Dict]:
        """获取所有模型的性能指标"""
        with self._lock:
            result = {}
            for name, metrics in self.model_metrics.items():
                result[name] = {
                    "model_name": metrics.model_name,
                    "total_requests": metrics.total_requests,
                    "successful_requests": metrics.successful_requests,
                    "failed_requests": metrics.failed_requests,
                    "success_rate": metrics.success_rate,
                    "avg_inference_time_ms": round(metrics.avg_inference_time_ms, 2),
                    "qps": round(metrics.qps, 2),
                    "last_request_time": (
                        metrics.last_request_time.isoformat()
                        if metrics.last_request_time
                        else None
                    ),
                }
            return result

    def get_latency_percentile(self, model_name: str, percentile: float) -> float:
        """
        获取延迟百分位数

        Args:
            model_name: 模型名称
            percentile: 百分位 (0-100)

        Returns:
            延迟值 (ms)
        """
        with self._lock:
            history = self.metrics_history.get(model_name, [])
            if not history:
                return 0.0

            # 只取最近的数据点
            values = sorted([p.value for p in history[-100:]])
            if not values:
                return 0.0

            index = int(len(values) * percentile / 100)
            return values[min(index, len(values) - 1)]

    def get_health_status(self) -> Dict:
        """获取服务健康状态"""
        with self._lock:
            total_requests = sum(m.total_requests for m in self.model_metrics.values())
            total_success = sum(
                m.successful_requests for m in self.model_metrics.values()
            )

            overall_success_rate = (
                total_success / total_requests * 100 if total_requests > 0 else 0.0
            )

            avg_latency = sum(
                m.avg_inference_time_ms for m in self.model_metrics.values()
            ) / max(len(self.model_metrics), 1)

            return {
                "status": "healthy" if overall_success_rate > 95 else "degraded",
                "total_models": len(self.model_metrics),
                "total_requests_24h": total_requests,
                "overall_success_rate": round(overall_success_rate, 2),
                "avg_latency_ms": round(avg_latency, 2),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def reset_metrics(self, model_name: Optional[str] = None):
        """重置指标"""
        with self._lock:
            if model_name:
                if model_name in self.model_metrics:
                    del self.model_metrics[model_name]
                if model_name in self.metrics_history:
                    del self.metrics_history[model_name]
            else:
                self.model_metrics.clear()
                self.metrics_history.clear()


# 全局监控实例
performance_monitor = PerformanceMonitor()


def monitor_performance(model_name: str, task_type: Optional[str] = None):
    """
    性能监控装饰器

    用法:
        @monitor_performance(model_name='yolov5', task_type='object_detection')
        async def vision_analyze(request):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True

            try:
                result = await func(*args, **kwargs)

                # 从响应中提取推理时间
                inference_time = getattr(result, "inference_time_ms", 0.0)

                performance_monitor.record_request(
                    model_name=model_name,
                    inference_time_ms=inference_time,
                    success=success,
                    task_type=task_type,
                )

                return result

            except Exception as e:
                success = False
                inference_time = (time.time() - start_time) * 1000

                performance_monitor.record_request(
                    model_name=model_name,
                    inference_time_ms=inference_time,
                    success=success,
                    task_type=task_type,
                )

                raise

        return wrapper

    return decorator
