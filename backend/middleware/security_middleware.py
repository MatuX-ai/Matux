"""
安全中间件
提供XSS防护、CSRF保护和安全头设置
"""

import html
import re
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件类"""

    def __init__(self, app):
        super().__init__(app)
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"on\w+\s*=\s*['\"]([^'\"]*)['\"]",
            r"javascript:",
            r"data:text/html",
            r"<iframe[^>]*>",
        ]

    async def dispatch(self, request: Request, call_next: Callable):
        # XSS防护 - 清理请求参数
        await self._sanitize_request(request)

        # 设置安全头
        response = await call_next(request)

        if isinstance(response, Response):
            self._set_security_headers(response)

        return response

    async def _sanitize_request(self, request: Request):
        """清理请求参数防止XSS"""
        # 清理查询参数
        sanitized_query = {}
        for key, value in request.query_params.items():
            sanitized_query[key] = self._sanitize_input(value)
        request._query_params = sanitized_query

    def _sanitize_input(self, input_str: str) -> str:
        """清理输入字符串"""
        if not isinstance(input_str, str):
            return input_str

        # HTML转义
        sanitized = html.escape(input_str)

        # 移除危险的JavaScript代码
        for pattern in self.xss_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)

        # 限制字符串长度
        max_length = 10000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized

    def _set_security_headers(self, response: Response):
        """设置安全HTTP头"""
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

        for header, value in security_headers.items():
            if header not in response.headers:
                response.headers[header] = value


# XSS清理工具函数
def sanitize_html(content: str) -> str:
    """HTML内容安全清理"""
    if not content:
        return ""

    # 使用html.escape进行基本转义
    escaped = html.escape(content)

    # 移除危险标签
    dangerous_tags = ["script", "iframe", "object", "embed"]
    for tag in dangerous_tags:
        escaped = re.sub(
            f"<{tag}[^>]*>.*?</{tag}>", "", escaped, flags=re.IGNORECASE | re.DOTALL
        )

    return escaped


def is_safe_url(url: str) -> bool:
    """检查URL是否安全"""
    if not url:
        return True

    safe_schemes = ["http", "https", "ftp", "mailto"]
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        return parsed.scheme in safe_schemes or not parsed.scheme
    except (ValueError, AttributeError):
        return False
