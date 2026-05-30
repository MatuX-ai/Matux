"""
Celery任务熔断器中间件
为Celery任务提供超时控制和熔断降级机制
"""

from enum import Enum
import logging
import time
from typing import Any, Dict, List, Optional

from celery.exceptions import SoftTimeLimitExceeded, TimeLimitExceeded
from prometheus_client import Counter, Enum as PromEnum, Gauge, Histogram

logger = logging.getLogger(__name__)


class TaskCircuitState(Enum):
    """任务熔断器状态枚举"""

    CLOSED = "closed"  # 正常状态，允许任务执行
    OPEN = "open"  # 熔断状态，拒绝任务执行
    HALF_OPEN = "half_open"  # 半开状态，尝试恢复


# Prometheus监控指标
TASK_CB_REQUEST_COUNT = Counter(
    "celery_task_circuit_breaker_requests_total",
    "Total Celery task requests handled by circuit breaker",
    ["task_name", "state", "status"],
)

TASK_CB_FAILURE_RATE = Gauge(
    "celery_task_circuit_breaker_failure_rate",
    "Current Celery task failure rate percentage",
    ["task_name"],
)

TASK_CB_STATE = PromEnum(
    "celery_task_circuit_breaker_state",
    "Current state of Celery task circuit breaker",
    states=["closed", "open", "half_open"],
    labelnames=["task_name"],
)

TASK_CB_LATENCY = Histogram(
    "celery_task_circuit_breaker_duration_seconds",
    "Celery task execution duration through circuit breaker",
    ["task_name", "status"],
)

TASK_CB_TIMEOUT_COUNT = Counter(
    "celery_task_timeouts_total", "Total Celery task timeouts", ["task_name"]
)


class CeleryTaskCircuitBreakerConfig:
    """Celery任务熔断器配置类"""

    def __init__(
        self,
        task_name: str,  # 任务名称
        failure_threshold: int = 3,  # 失败阈值
        timeout: int = 30,  # 熔断超时时间(秒)，默认30秒
        soft_time_limit: int = 25,  # 软超时时间(秒)
        time_limit: int = 60,  # 硬超时时间(秒)
        half_open_attempts: int = 3,  # 半开状态尝试次数
        reset_timeout: int = 60,  # 重置超时时间(秒)
        expected_exceptions: Optional[List[type]] = None,
        enable_timeout_protection: bool = True,  # 是否启用超时保护
        enable_failure_protection: bool = True,  # 是否启用失败保护
    ):
        self.task_name = task_name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.soft_time_limit = soft_time_limit
        self.time_limit = time_limit
        self.half_open_attempts = half_open_attempts
        self.reset_timeout = reset_timeout
        self.enable_timeout_protection = enable_timeout_protection
        self.enable_failure_protection = enable_failure_protection

        # 预期的异常类型（不触发熔断）
        self.expected_exceptions = expected_exceptions or [
            SoftTimeLimitExceeded,
            TimeLimitExceeded,
            KeyboardInterrupt,
            SystemExit,
        ]

        # 初始化监控指标
        TASK_CB_STATE.labels(task_name=task_name).state(TaskCircuitState.CLOSED.value)


class CeleryTaskCircuitBreaker:
    """Celery任务熔断器"""

    def __init__(self, config: CeleryTaskCircuitBreakerConfig):
        self.config = config
        self.task_name = config.task_name

        # 状态管理
        self.state = TaskCircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.timeout_count = 0
        self.last_failure_time = None
        self.half_open_attempt_count = 0
        self.state_change_time = time.time()

        logger.info(
            f"Celery task circuit breaker initialized for '{self.task_name}' "
            f"with timeout={config.timeout}s, failure_threshold={config.failure_threshold}"
        )

    def _is_expected_exception(self, exception: Exception) -> bool:
        """判断是否为预期的异常类型"""
        return any(
            isinstance(exception, exc_type)
            for exc_type in self.config.expected_exceptions
        )

    def _calculate_failure_rate(self) -> float:
        """计算失败率"""
        total_requests = self.failure_count + self.success_count
        if total_requests == 0:
            return 0.0
        return (self.failure_count / total_requests) * 100

    def _can_transition_to_open(self) -> bool:
        """判断是否可以转换到OPEN状态"""
        return (
            self.failure_count >= self.config.failure_threshold
            and self.state == TaskCircuitState.CLOSED
        )

    def _can_transition_to_half_open(self) -> bool:
        """判断是否可以转换到HALF_OPEN状态"""
        return (
            self.state == TaskCircuitState.OPEN
            and time.time() - self.state_change_time >= self.config.timeout
        )

    def _can_transition_to_closed(self) -> bool:
        """判断是否可以转换到CLOSED状态"""
        return (
            self.state == TaskCircuitState.HALF_OPEN
            and self.success_count >= self.config.half_open_attempts
        )

    def _transition_state(self, new_state: TaskCircuitState):
        """状态转换"""
        old_state = self.state
        self.state = new_state
        self.state_change_time = time.time()

        # 重置计数器
        if new_state == TaskCircuitState.CLOSED:
            self.failure_count = 0
            self.success_count = 0
            self.timeout_count = 0
        elif new_state == TaskCircuitState.OPEN:
            self.failure_count = 0
            self.success_count = 0
            self.half_open_attempt_count = 0
            self.timeout_count = 0
        elif new_state == TaskCircuitState.HALF_OPEN:
            self.success_count = 0
            self.half_open_attempt_count = 0
            self.failure_count = 0
            self.timeout_count = 0

        logger.info(
            f"Task '{self.task_name}' circuit breaker state transition: "
            f"{old_state.value} -> {new_state.value}"
        )
        TASK_CB_STATE.labels(task_name=self.task_name).state(new_state.value)

    def _handle_closed_state(self):
        """处理CLOSED状态"""

    def _handle_open_state(self) -> bool:
        """处理OPEN状态，返回是否允许执行"""
        logger.warning(f"Task '{self.task_name}' blocked by circuit breaker")

        # 检查是否可以转为半开状态
        if self._can_transition_to_half_open():
            self._transition_state(TaskCircuitState.HALF_OPEN)
            return True
        return False

    def _handle_half_open_state(self):
        """处理HALF_OPEN状态"""
        self.half_open_attempt_count += 1
        logger.info(
            f"Task '{self.task_name}' half-open attempt #{self.half_open_attempt_count}"
        )

    def should_execute(self) -> bool:
        """判断是否应该执行任务"""
        # 状态机处理
        if self.state == TaskCircuitState.CLOSED:
            self._handle_closed_state()
            return True

        elif self.state == TaskCircuitState.OPEN:
            return self._handle_open_state()

        elif self.state == TaskCircuitState.HALF_OPEN:
            self._handle_half_open_state()
            return True

        return True

    def record_success(self, execution_time: float = 0):
        """记录成功执行"""
        if self.state == TaskCircuitState.HALF_OPEN:
            self.success_count += 1
            TASK_CB_REQUEST_COUNT.labels(
                task_name=self.task_name, state=self.state.value, status="success"
            ).inc()
            TASK_CB_LATENCY.labels(task_name=self.task_name, status="success").observe(
                execution_time
            )

            if self._can_transition_to_closed():
                self._transition_state(TaskCircuitState.CLOSED)
        elif self.state == TaskCircuitState.CLOSED:
            self.success_count += 1
            TASK_CB_REQUEST_COUNT.labels(
                task_name=self.task_name, state=self.state.value, status="success"
            ).inc()
            TASK_CB_LATENCY.labels(task_name=self.task_name, status="success").observe(
                execution_time
            )

    def record_failure(self, execution_time: float = 0):
        """记录失败执行"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        # 更新失败率指标
        failure_rate = self._calculate_failure_rate()
        TASK_CB_FAILURE_RATE.labels(task_name=self.task_name).set(failure_rate)
        TASK_CB_REQUEST_COUNT.labels(
            task_name=self.task_name, state=self.state.value, status="failure"
        ).inc()
        TASK_CB_LATENCY.labels(task_name=self.task_name, status="failure").observe(
            execution_time
        )

        # 检查是否需要熔断
        if self.config.enable_failure_protection and self._can_transition_to_open():
            self._transition_state(TaskCircuitState.OPEN)
        elif self.state == TaskCircuitState.HALF_OPEN:
            # HALF_OPEN状态下任何失败都立即回到OPEN
            self._transition_state(TaskCircuitState.OPEN)

    def record_timeout(self):
        """记录超时事件"""
        self.timeout_count += 1
        TASK_CB_TIMEOUT_COUNT.labels(task_name=self.task_name).inc()

        # 超时也计入失败统计
        if self.config.enable_timeout_protection:
            self.record_failure()

    def get_state_info(self) -> Dict[str, Any]:
        """获取当前状态信息"""
        return {
            "task_name": self.task_name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "timeout_count": self.timeout_count,
            "failure_rate": self._calculate_failure_rate(),
            "last_failure_time": self.last_failure_time,
            "state_change_time": self.state_change_time,
        }


# 全局任务熔断器管理器
class TaskCircuitBreakerManager:
    """任务熔断器管理器"""

    def __init__(self):
        self.breakers: Dict[str, CeleryTaskCircuitBreaker] = {}
        self.default_configs: Dict[str, CeleryTaskCircuitBreakerConfig] = {}

    def register_task_config(
        self, task_name: str, config: CeleryTaskCircuitBreakerConfig
    ):
        """注册任务配置"""
        self.default_configs[task_name] = config

    def get_or_create_breaker(self, task_name: str) -> CeleryTaskCircuitBreaker:
        """获取或创建任务熔断器"""
        if task_name not in self.breakers:
            # 使用自定义配置或默认配置
            config = self.default_configs.get(
                task_name, CeleryTaskCircuitBreakerConfig(task_name=task_name)
            )
            self.breakers[task_name] = CeleryTaskCircuitBreaker(config)
        return self.breakers[task_name]

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务熔断器状态"""
        return {
            task_name: breaker.get_state_info()
            for task_name, breaker in self.breakers.items()
        }


# 全局实例
task_circuit_manager = TaskCircuitBreakerManager()


# 装饰器实现
def task_circuit_breaker(
    failure_threshold: int = 3,
    timeout: int = 30,
    soft_time_limit: int = 25,
    time_limit: int = 60,
    half_open_attempts: int = 3,
    enable_timeout_protection: bool = True,
    enable_failure_protection: bool = True,
):
    """
    Celery任务熔断器装饰器

    Args:
        failure_threshold: 失败阈值
        timeout: 熔断超时时间(秒)
        soft_time_limit: 软超时时间(秒)
        time_limit: 硬超时时间(秒)
        half_open_attempts: 半开状态尝试次数
        enable_timeout_protection: 是否启用超时保护
        enable_failure_protection: 是否启用失败保护
    """

    def decorator(task_func):
        # 获取任务名称
        task_name = getattr(task_func, "name", task_func.__name__)

        # 创建配置
        config = CeleryTaskCircuitBreakerConfig(
            task_name=task_name,
            failure_threshold=failure_threshold,
            timeout=timeout,
            soft_time_limit=soft_time_limit,
            time_limit=time_limit,
            half_open_attempts=half_open_attempts,
            enable_timeout_protection=enable_timeout_protection,
            enable_failure_protection=enable_failure_protection,
        )

        # 注册配置
        task_circuit_manager.register_task_config(task_name, config)

        # 包装原始任务函数
        def wrapper(*args, **kwargs):
            breaker = task_circuit_manager.get_or_create_breaker(task_name)
            start_time = time.time()

            # 检查是否应该执行
            if not breaker.should_execute():
                raise Exception(f"Task '{task_name}' is currently circuit broken")

            try:
                # 设置任务超时
                current_task = kwargs.get("self")  # 如果是绑定任务
                if current_task and hasattr(current_task, "update_state"):
                    current_task.update_state(
                        state="PROGRESS",
                        meta={
                            "timeout_config": {
                                "soft_time_limit": config.soft_time_limit,
                                "time_limit": config.time_limit,
                            }
                        },
                    )

                # 执行任务
                result = task_func(*args, **kwargs)

                # 记录成功
                execution_time = time.time() - start_time
                breaker.record_success(execution_time)

                return result

            except (SoftTimeLimitExceeded, TimeLimitExceeded) as e:
                # 记录超时
                execution_time = time.time() - start_time
                breaker.record_timeout()
                logger.warning(
                    f"Task '{task_name}' timed out after {execution_time:.2f}s"
                )
                raise e

            except Exception as e:
                # 记录失败
                execution_time = time.time() - start_time
                if not breaker._is_expected_exception(e):
                    breaker.record_failure(execution_time)
                raise e

        # 保持原任务属性
        wrapper.__name__ = task_func.__name__
        wrapper.__doc__ = task_func.__doc__

        return wrapper

    return decorator


from celery import Task as BaseTask


class CircuitBreakerTask(BaseTask):
    """带熔断器功能的Celery任务基类"""

    abstract = True

    def __init__(self):
        super().__init__()
        self.circuit_breaker = None

    def apply_async(
        self,
        args=None,
        kwargs=None,
        task_id=None,
        producer=None,
        link=None,
        link_error=None,
        shadow=None,
        **options,
    ):
        """重写apply_async方法，在执行前检查熔断器状态"""
        # 获取或创建熔断器
        self.circuit_breaker = task_circuit_manager.get_or_create_breaker(self.name)

        # 检查是否应该执行
        if not self.circuit_breaker.should_execute():
            # 任务被熔断，返回失败结果
            from celery.exceptions import Retry

            raise Retry(message=f"Task '{self.name}' is currently circuit broken")

        # 调用父类方法继续执行
        return super().apply_async(
            args, kwargs, task_id, producer, link, link_error, shadow, **options
        )

    def on_success(self, retval, task_id, args, kwargs):
        """任务成功回调"""
        if self.circuit_breaker:
            self.circuit_breaker.record_success()
        super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任务失败回调"""
        if self.circuit_breaker:
            # 检查是否为超时异常
            if isinstance(exc, (SoftTimeLimitExceeded, TimeLimitExceeded)):
                self.circuit_breaker.record_timeout()
            elif not self.circuit_breaker._is_expected_exception(exc):
                self.circuit_breaker.record_failure()
        super().on_failure(exc, task_id, args, kwargs, einfo)


# 导出主要类和函数
__all__ = [
    "CeleryTaskCircuitBreaker",
    "CeleryTaskCircuitBreakerConfig",
    "TaskCircuitBreakerManager",
    "task_circuit_manager",
    "task_circuit_breaker",
    "TaskCircuitState",
    "CircuitBreakerTask",
]
