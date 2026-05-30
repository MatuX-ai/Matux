"""
APM监控配置模块
配置SkyWalking和OpenTelemetry监控
"""

from contextlib import contextmanager
from functools import wraps
import logging
import os
import time
from typing import Optional

# SkyWalking相关导入
try:
    from skywalking import agent, config
    from skywalking.trace.context import get_context
    from skywalking.trace.tags import Tag

    SKYWALKING_AVAILABLE = True
except ImportError:
    SKYWALKING_AVAILABLE = False
    print("SkyWalking not available, using fallback")

# OpenTelemetry相关导入
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    print("OpenTelemetry not available, using fallback")

logger = logging.getLogger(__name__)


class APMConfig:
    """APM配置类"""

    def __init__(self):
        self.service_name = os.getenv("SERVICE_NAME", "imato-backend")
        self.skywalking_collector = os.getenv("SKYWALKING_COLLECTOR", "localhost:11800")
        self.otel_collector = os.getenv("OTEL_COLLECTOR", "localhost:4317")
        self.enable_tracing = os.getenv("ENABLE_TRACING", "false").lower() == "true"
        self.enable_metrics = os.getenv("ENABLE_METRICS", "false").lower() == "true"
        self.sampling_rate = float(os.getenv("SAMPLING_RATE", "1.0"))


# 全局配置实例
apm_config = APMConfig()


def init_apm():
    """初始化APM监控"""
    if not apm_config.enable_tracing:
        logger.info("APM tracing disabled")
        return

    # 初始化SkyWalking
    if SKYWALKING_AVAILABLE:
        try:
            config.init(
                service_name=apm_config.service_name,
                collector_address=apm_config.skywalking_collector,
                protocol="grpc",
            )
            agent.start()
            logger.info(
                f"SkyWalking APM initialized for service: {apm_config.service_name}"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize SkyWalking: {e}")

    # 初始化OpenTelemetry
    if OTEL_AVAILABLE:
        try:
            tracer_provider = TracerProvider()
            otlp_exporter = OTLPSpanExporter(endpoint=apm_config.otel_collector)
            tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            trace.set_tracer_provider(tracer_provider)
            logger.info(
                f"OpenTelemetry initialized for service: {apm_config.service_name}"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry: {e}")


def trace_endpoint(operation_name: str = None):
    """装饰器：为FastAPI端点添加APM追踪"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取操作名称
            op_name = operation_name or f"{func.__module__}.{func.__name__}"

            start_time = time.time()

            # SkyWalking追踪
            if SKYWALKING_AVAILABLE:
                try:
                    context = get_context()
                    with context.new_local_span(op=op_name) as span:
                        span.tag(Tag(key="component", val="fastapi"))

                        try:
                            result = await func(*args, **kwargs)

                            # 记录成功指标
                            span.tag(Tag(key="status", val="success"))
                            span.tag(
                                Tag(
                                    key="duration_ms",
                                    val=str(int((time.time() - start_time) * 1000)),
                                )
                            )

                            return result

                        except Exception as e:
                            # 记录错误信息
                            span.tag(Tag(key="status", val="error"))
                            span.tag(Tag(key="error", val=str(e)))
                            span.error_occurred = True
                            raise
                except Exception as e:
                    logger.warning(f"SkyWalking tracing failed: {e}")
                    # 回退到原始函数调用
                    return await func(*args, **kwargs)

            # OpenTelemetry追踪
            elif OTEL_AVAILABLE:
                try:
                    tracer = trace.get_tracer(__name__)
                    with tracer.start_as_current_span(op_name) as span:
                        span.set_attribute("component", "fastapi")

                        try:
                            result = await func(*args, **kwargs)

                            # 记录成功指标
                            span.set_attribute("status", "success")
                            span.set_attribute(
                                "duration_ms", int((time.time() - start_time) * 1000)
                            )

                            return result

                        except Exception as e:
                            # 记录错误信息
                            span.set_attribute("status", "error")
                            span.set_attribute("error.message", str(e))
                            span.record_exception(e)
                            raise
                except Exception as e:
                    logger.warning(f"OpenTelemetry tracing failed: {e}")
                    # 回退到原始函数调用
                    return await func(*args, **kwargs)

            else:
                # 无APM时直接调用
                return await func(*args, **kwargs)

        return wrapper

    return decorator


@contextmanager
def trace_operation(operation_name: str, component: str = "custom"):
    """上下文管理器：手动追踪操作"""
    start_time = time.time()

    if SKYWALKING_AVAILABLE:
        try:
            context = get_context()
            with context.new_local_span(op=operation_name) as span:
                span.tag(Tag(key="component", val=component))
                yield span

                # 记录持续时间
                duration_ms = int((time.time() - start_time) * 1000)
                span.tag(Tag(key="duration_ms", val=str(duration_ms)))

        except Exception as e:
            logger.warning(f"SkyWalking operation tracing failed: {e}")
            yield None

    elif OTEL_AVAILABLE:
        try:
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(operation_name) as span:
                span.set_attribute("component", component)
                yield span

                # 记录持续时间
                duration_ms = int((time.time() - start_time) * 1000)
                span.set_attribute("duration_ms", duration_ms)

        except Exception as e:
            logger.warning(f"OpenTelemetry operation tracing failed: {e}")
            yield None
    else:
        yield None


def record_custom_metric(metric_name: str, value: float, tags: Optional[dict] = None):
    """记录自定义指标"""
    tags = tags or {}

    # 如果有Prometheus客户端，记录指标
    try:
        from prometheus_client import Counter, Gauge, Histogram

        # 根据指标名称创建相应的指标类型
        if metric_name.endswith("_count"):
            counter = Counter(
                metric_name, f"Counter for {metric_name}", list(tags.keys())
            )
            counter.labels(**tags).inc(value)
        elif metric_name.endswith("_duration") or metric_name.endswith("_latency"):
            histogram = Histogram(
                metric_name, f"Histogram for {metric_name}", list(tags.keys())
            )
            histogram.labels(**tags).observe(value)
        else:
            gauge = Gauge(metric_name, f"Gauge for {metric_name}", list(tags.keys()))
            gauge.labels(**tags).set(value)

    except ImportError:
        pass  # Prometheus不可用
    except Exception as e:
        logger.warning(f"Failed to record custom metric {metric_name}: {e}")


def shutdown_apm():
    """关闭APM监控"""
    if SKYWALKING_AVAILABLE:
        try:
            agent.stop()
            logger.info("SkyWalking APM stopped")
        except Exception as e:
            logger.warning(f"Failed to stop SkyWalking: {e}")

    if OTEL_AVAILABLE:
        try:
            trace.get_tracer_provider().force_flush()
            logger.info("OpenTelemetry flushed")
        except Exception as e:
            logger.warning(f"Failed to flush OpenTelemetry: {e}")
