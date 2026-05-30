"""
企业网关安全工具模块
提供安全相关的实用工具函数
"""

import hashlib
import hmac
import re
import secrets
from typing import Tuple


class SecurityUtil:
    """安全工具类"""

    @staticmethod
    def generate_device_fingerprint(
        ip_address: str, user_agent: str, accept_language: str = ""
    ) -> str:
        """
        生成设备指纹

        Args:
            ip_address: IP地址
            user_agent: 用户代理
            accept_language: 接受的语言

        Returns:
            设备指纹哈希值
        """
        # 组合设备信息
        device_info = f"{ip_address}|{user_agent}|{accept_language}"

        # 生成SHA256哈希
        fingerprint = hashlib.sha256(device_info.encode("utf-8")).hexdigest()

        return fingerprint

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """
        验证IP地址格式

        Args:
            ip: IP地址字符串

        Returns:
            是否为有效IP地址
        """
        # IPv4正则表达式
        ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}$"

        # IPv6正则表达式
        ipv6_pattern = r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$"

        if re.match(ipv4_pattern, ip):
            # 验证IPv4每个段都在0-255范围内
            parts = ip.split(".")
            return all(0 <= int(part) <= 255 for part in parts)
        elif re.match(ipv6_pattern, ip):
            return True
        else:
            return False

    @staticmethod
    def validate_mac_address(mac: str) -> bool:
        """
        验证MAC地址格式

        Args:
            mac: MAC地址字符串

        Returns:
            是否为有效MAC地址
        """
        # MAC地址正则表达式（支持多种格式）
        mac_patterns = [
            r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$",  # AA:BB:CC:DD:EE:FF 或 AA-BB-CC-DD-EE-FF
            r"^([0-9A-Fa-f]{4}\.){2}([0-9A-Fa-f]{4})$",  # AABB.CCDD.EEFF
            r"^([0-9A-Fa-f]{12})$",  # AABBCCDDEEFF
        ]

        return any(re.match(pattern, mac) for pattern in mac_patterns)

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """
        清理输入字符串，防止注入攻击

        Args:
            input_str: 输入字符串

        Returns:
            清理后的字符串
        """
        if not input_str:
            return ""

        # 移除潜在危险字符
        dangerous_chars = [
            "<",
            ">",
            '"',
            "'",
            "&",
            ";",
            "`",
            "|",
            "*",
            "?",
            "~",
            "^",
            "(",
            ")",
            "[",
            "]",
            "{",
            "}",
        ]

        sanitized = input_str
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        # 限制长度
        return sanitized[:1000]  # 限制最大长度

    @staticmethod
    def generate_nonce(length: int = 32) -> str:
        """
        生成随机nonce值

        Args:
            length: nonce长度

        Returns:
            随机nonce字符串
        """
        return secrets.token_urlsafe(length)[:length]

    @staticmethod
    def calculate_hmac_signature(
        message: str, secret: str, algorithm: str = "sha256"
    ) -> str:
        """
        计算HMAC签名

        Args:
            message: 要签名的消息
            secret: 密钥
            algorithm: 算法类型

        Returns:
            HMAC签名
        """
        hmac_obj = hmac.new(
            secret.encode("utf-8"), message.encode("utf-8"), getattr(hashlib, algorithm)
        )
        return hmac_obj.hexdigest()

    @staticmethod
    def verify_hmac_signature(
        message: str, signature: str, secret: str, algorithm: str = "sha256"
    ) -> bool:
        """
        验证HMAC签名

        Args:
            message: 原始消息
            signature: 提供的签名
            secret: 密钥
            algorithm: 算法类型

        Returns:
            签名是否有效
        """
        expected_signature = SecurityUtil.calculate_hmac_signature(
            message, secret, algorithm
        )
        return hmac.compare_digest(expected_signature, signature)

    @staticmethod
    def is_rate_limited(
        client_id: str, window_minutes: int = 60, max_requests: int = 1000
    ) -> Tuple[bool, int]:
        """
        检查客户端是否触发速率限制

        Args:
            client_id: 客户端ID
            window_minutes: 时间窗口（分钟）
            max_requests: 最大请求数

        Returns:
            (是否受限, 剩余请求数)
        """
        # 这里应该集成Redis或其他缓存系统来实现真正的速率限制
        # 当前实现为简化版本

        # 模拟实现 - 实际应该查询缓存
        current_requests = 0  # 应该从缓存获取
        remaining = max_requests - current_requests

        is_limited = current_requests >= max_requests
        return is_limited, max(0, remaining)

    @staticmethod
    def get_client_ip(request) -> str:
        """
        从请求中获取真实客户端IP

        Args:
            request: FastAPI请求对象

        Returns:
            客户端IP地址
        """
        # 检查常见的代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For可能包含多个IP，取第一个
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 如果没有代理头，使用直接连接的IP
        return request.client.host if request.client else "unknown"

    @staticmethod
    def validate_redirect_uri(redirect_uri: str, allowed_uris: str) -> bool:
        """
        验证重定向URI是否在允许列表中

        Args:
            redirect_uri: 请求的重定向URI
            allowed_uris: 允许的URI列表（逗号分隔）

        Returns:
            URI是否有效
        """
        if not allowed_uris:
            return False

        allowed_list = [uri.strip() for uri in allowed_uris.split(",")]
        return redirect_uri in allowed_list
