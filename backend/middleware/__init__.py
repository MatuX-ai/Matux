"""
中间件包
"""

# 尝试导入prometheus，如果不可用则使用fallback
try:
    from .circuit_breaker import CircuitBreakerConfig, CircuitBreakerMiddleware
except ImportError:
    # 创建一个fallback版本
    import logging

    logger = logging.getLogger(__name__)
    logger.warning("prometheus_client not available, using fallback circuit breaker")

    class CircuitBreakerConfig:
        def __init__(self, failure_threshold=5, timeout=60, half_open_attempts=3):
            self.failure_threshold = failure_threshold
            self.timeout = timeout
            self.half_open_attempts = half_open_attempts

    class CircuitBreakerMiddleware:
        def __init__(self, app, config=None):
            self.app = app
            logger.info("Using fallback circuit breaker middleware (no monitoring)")

        async def __call__(self, scope, receive, send):
            """ASGI 应用调用"""
            await self.app(scope, receive, send)

from .apm_middleware import APMMiddleware
from .apm_monitoring import init_apm
from .enhanced_permission_middleware import EnhancedPermissionMiddleware as PermissionMiddleware
from .license_middleware import LicenseMiddleware, license_exception_handler

__all__ = [
    'APMMiddleware',
    'init_apm',
    'PermissionMiddleware',
    'LicenseMiddleware',
    'license_exception_handler',
    'CircuitBreakerConfig',
    'CircuitBreakerMiddleware',
]
