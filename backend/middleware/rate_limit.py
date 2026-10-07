"""
API 速率限制中间件
【P2修复】基于滑动窗口算法的全局 API 速率限制
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitConfig:
    """速率限制配置"""

    def __init__(
        self,
        requests: int = 100,
        window_seconds: int = 60,
        key_func: Optional[callable] = None,
        exclude_paths: Optional[List[str]] = None,
    ):
        self.requests = requests  # 时间窗口内允许的最大请求数
        self.window_seconds = window_seconds  # 时间窗口（秒）
        self.key_func = key_func  # 生成限流 key 的函数
        self.exclude_paths = exclude_paths or []  # 排除的路径


class SlidingWindowRateLimiter:
    """
    滑动窗口速率限制器
    使用滑动窗口算法实现精确的速率限制
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # 存储请求时间戳: {key: [timestamp1, timestamp2, ...]}
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def _cleanup_old_requests(self, key: str, now: float) -> None:
        """清理过期的请求记录"""
        cutoff = now - self.window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]

    def is_allowed(self, key: str) -> Tuple[bool, int, int]:
        """
        检查请求是否允许
        返回: (是否允许, 剩余请求数, 剩余时间秒)
        """
        now = time.time()
        self._cleanup_old_requests(key, now)

        current_count = len(self.requests[key])
        remaining = max(0, self.max_requests - current_count)

        if current_count < self.max_requests:
            # 允许请求，记录时间戳
            self.requests[key].append(now)
            return True, remaining - 1, 0

        # 不允许，计算需要等待的时间
        oldest = self.requests[key][0]
        wait_time = int(oldest + self.window_seconds - now)
        return False, 0, max(0, wait_time)

    def record_request(self, key: str) -> None:
        """记录一次请求"""
        now = time.time()
        self._cleanup_old_requests(key, now)
        self.requests[key].append(now)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    API 速率限制中间件
    【P2修复】防止暴力破解和 DDoS 攻击
    """

    def __init__(
        self,
        app,
        config: Optional[RateLimitConfig] = None,
    ):
        super().__init__(app)
        self.config = config or RateLimitConfig()

        # 根据配置创建限流器
        self.limiter = SlidingWindowRateLimiter(
            max_requests=self.config.requests,
            window_seconds=self.config.window_seconds,
        )

        # 如果没有指定 key_func，使用默认的 IP 限流
        self._key_func = self.config.key_func or self._default_key_func

    @staticmethod
    def _default_key_func(request: Request) -> str:
        """默认的限流 key 生成函数：使用 IP 地址"""
        # 优先使用 X-Forwarded-For 头（代理环境）
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # 取第一个 IP（客户端真实 IP）
            return forwarded.split(",")[0].strip()

        # 使用客户端 IP
        if request.client:
            return request.client.host

        return "unknown"

    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查是否排除该路径
        path = request.url.path
        for exclude_path in self.config.exclude_paths:
            if path.startswith(exclude_path):
                return await call_next(request)

        # 生成限流 key
        key = self._key_func(request)

        # 检查是否允许请求
        allowed, remaining, retry_after = self.limiter.is_allowed(key)

        if not allowed:
            # 返回 429 Too Many Requests
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"请求过于频繁，请 {retry_after} 秒后重试",
                    "retry_after": retry_after,
                    "remaining": 0,
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.config.requests),
                    "X-RateLimit-Remaining": "0",
                },
            )

        # 执行请求
        response = await call_next(request)

        # 在响应头中添加限流信息
        response.headers["X-RateLimit-Limit"] = str(self.config.requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response
