"""
APM监控中间件
为FastAPI应用提供APM监控功能
"""

import logging
import time
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .apm_monitoring import record_custom_metric, trace_operation

logger = logging.getLogger(__name__)


class APMMiddleware(BaseHTTPMiddleware):
    """APM监控中间件"""

    def __init__(self, app, service_name: str = "imato-backend"):
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """处理请求并添加APM监控"""
        start_time = time.time()

        # 获取请求信息
        method = request.method
        url_path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # 构造操作名称
        operation_name = f"{method} {url_path}"

        try:
            # 使用APM追踪整个请求
            with trace_operation(operation_name, "http") as span:
                # 设置请求相关标签
                if span:
                    # SkyWalking标签设置
                    try:
                        from skywalking.trace.tags import Tag

                        span.tag(Tag(key="http.method", val=method))
                        span.tag(Tag(key="http.url", val=str(request.url)))
                        span.tag(Tag(key="http.client_ip", val=client_ip))
                    except (ImportError, AttributeError):
                        pass

                    # OpenTelemetry 属性设置
                    try:
                        span.set_attribute("http.method", method)
                        span.set_attribute("http.url", str(request.url))
                        span.set_attribute("http.client_ip", client_ip)
                    except (AttributeError, RuntimeError):
                        pass

                # 处理请求
                response = await call_next(request)

                # 记录响应信息
                duration_ms = int((time.time() - start_time) * 1000)
                status_code = response.status_code

                if span:
                    # 设置响应相关标签
                    try:
                        from skywalking.trace.tags import Tag

                        span.tag(Tag(key="http.status_code", val=str(status_code)))
                        span.tag(Tag(key="duration_ms", val=str(duration_ms)))
                    except:
                        pass

                    try:
                        span.set_attribute("http.status_code", status_code)
                        span.set_attribute("duration_ms", duration_ms)
                    except:
                        pass

                # 记录指标
                self._record_http_metrics(method, url_path, status_code, duration_ms)

                return response

        except Exception as e:
            # 记录错误
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(f"APM Middleware error for {operation_name}: {e}")

            # 记录错误指标
            self._record_error_metrics(method, url_path, str(e), duration_ms)

            # 重新抛出异常让上层处理
            raise

    def _record_http_metrics(
        self, method: str, path: str, status_code: int, duration_ms: int
    ):
        """记录HTTP请求指标"""
        try:
            # 请求计数
            record_custom_metric(
                "http_requests_total",
                1,
                {"method": method, "path": path, "status_code": str(status_code)},
            )

            # 请求延迟
            record_custom_metric(
                "http_request_duration_ms",
                duration_ms,
                {"method": method, "path": path},
            )

            # 按状态码分类的计数
            status_family = f"{status_code // 100}xx"
            record_custom_metric(
                f"http_responses_{status_family}_total",
                1,
                {"method": method, "path": path},
            )

        except Exception as e:
            logger.warning(f"Failed to record HTTP metrics: {e}")

    def _record_error_metrics(
        self, method: str, path: str, error_msg: str, duration_ms: int
    ):
        """记录错误指标"""
        try:
            # 错误计数
            record_custom_metric(
                "http_request_errors_total",
                1,
                {
                    "method": method,
                    "path": path,
                    "error": error_msg[:100],  # 限制错误消息长度
                },
            )

            # 错误延迟
            record_custom_metric(
                "http_request_error_duration_ms",
                duration_ms,
                {"method": method, "path": path},
            )

        except Exception as e:
            logger.warning(f"Failed to record error metrics: {e}")


# 特定于推荐系统的监控装饰器
def monitor_recommendation_endpoint(func):
    """推荐系统端点监控装饰器"""
    from functools import wraps

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            # 执行原函数
            result = await func(*args, **kwargs)

            # 记录成功指标
            duration_ms = int((time.time() - start_time) * 1000)
            record_custom_metric("recommendation_success_total", 1)
            record_custom_metric("recommendation_duration_ms", duration_ms)

            return result

        except Exception as e:
            # 记录错误指标
            duration_ms = int((time.time() - start_time) * 1000)
            record_custom_metric(
                "recommendation_errors_total", 1, {"error": str(e)[:100]}
            )
            record_custom_metric("recommendation_error_duration_ms", duration_ms)
            raise

    return wrapper


# 数据库操作监控装饰器
def monitor_db_operation(operation_name: str):
    """数据库操作监控装饰器"""

    def decorator(func):
        from functools import wraps

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # 记录数据库操作指标
                duration_ms = int((time.time() - start_time) * 1000)
                record_custom_metric(
                    f"db_{operation_name}_duration_ms",
                    duration_ms,
                    {"operation": operation_name},
                )

                return result

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                record_custom_metric(
                    f"db_{operation_name}_errors_total",
                    1,
                    {"operation": operation_name, "error": str(e)[:100]},
                )
                raise

        return wrapper

    return decorator


# AI模型调用监控装饰器
def monitor_ai_operation(model_name: str):
    """AI模型调用监控装饰器"""

    def decorator(func):
        from functools import wraps

        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # 记录AI操作指标
                duration_ms = int((time.time() - start_time) * 1000)
                record_custom_metric(
                    "ai_model_call_duration_ms", duration_ms, {"model": model_name}
                )

                # 如果返回结果包含tokens信息，也记录
                if hasattr(result, "tokens_used"):
                    record_custom_metric(
                        "ai_model_tokens_used",
                        result.tokens_used,
                        {"model": model_name},
                    )

                return result

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                record_custom_metric(
                    "ai_model_errors_total",
                    1,
                    {"model": model_name, "error": str(e)[:100]},
                )
                raise

        return wrapper

    return decorator
