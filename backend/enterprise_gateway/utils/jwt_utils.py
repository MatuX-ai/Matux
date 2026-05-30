"""
企业网关JWT工具模块
提供JWT令牌的生成、验证和管理功能
"""

from datetime import datetime, timedelta
import secrets
import string
from typing import Any, Dict, Optional

import jwt

from config.enterprise_settings import enterprise_settings


class JWTUtil:
    """JWT工具类"""

    @staticmethod
    def generate_client_secret(length: int = 32) -> str:
        """
        生成安全的客户端密钥

        Args:
            length: 密钥长度

        Returns:
            生成的客户端密钥
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def generate_client_id(prefix: str = "ent_") -> str:
        """
        生成唯一的客户端ID

        Args:
            prefix: ID前缀

        Returns:
            生成的客户端ID
        """
        timestamp = int(datetime.utcnow().timestamp())
        random_part = secrets.token_hex(8)
        return f"{prefix}{timestamp}_{random_part}"

    @staticmethod
    def create_access_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        创建访问令牌

        Args:
            data: 要编码的数据
            expires_delta: 过期时间增量

        Returns:
            JWT访问令牌
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                hours=enterprise_settings.ENTERPRISE_TOKEN_EXPIRE_HOURS
            )

        to_encode.update(
            {"exp": expire, "iat": datetime.utcnow(), "iss": "enterprise-gateway"}
        )

        encoded_jwt = jwt.encode(
            to_encode,
            enterprise_settings.ENTERPRISE_JWT_SECRET,
            algorithm=enterprise_settings.ENTERPRISE_JWT_ALGORITHM,
        )

        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌

        Args:
            token: JWT令牌

        Returns:
            解码后的令牌数据，如果验证失败返回None
        """
        try:
            payload = jwt.decode(
                token,
                enterprise_settings.ENTERPRISE_JWT_SECRET,
                algorithms=[enterprise_settings.ENTERPRISE_JWT_ALGORITHM],
                issuer="enterprise-gateway",
            )

            # 检查令牌是否过期
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                return None

            return payload
        except jwt.PyJWTError:
            return None

    @staticmethod
    def extract_client_id(token: str) -> Optional[str]:
        """
        从令牌中提取客户端ID

        Args:
            token: JWT令牌

        Returns:
            客户端ID，如果提取失败返回None
        """
        payload = JWTUtil.verify_token(token)
        if payload:
            return payload.get("client_id")
        return None

    @staticmethod
    def extract_scopes(token: str) -> Optional[list]:
        """
        从令牌中提取作用域

        Args:
            token: JWT令牌

        Returns:
            作用域列表，如果提取失败返回None
        """
        payload = JWTUtil.verify_token(token)
        if payload:
            scopes = payload.get("scope", "")
            return scopes.split() if scopes else []
        return None

    @staticmethod
    def create_refresh_token(client_id: str) -> str:
        """
        创建刷新令牌

        Args:
            client_id: 客户端ID

        Returns:
            刷新令牌
        """
        data = {"client_id": client_id, "type": "refresh"}

        # 刷新令牌有效期更长
        expires_delta = timedelta(days=30)

        return JWTUtil.create_access_token(data, expires_delta)

    @staticmethod
    def is_refresh_token(token: str) -> bool:
        """
        检查令牌是否为刷新令牌

        Args:
            token: JWT令牌

        Returns:
            是否为刷新令牌
        """
        payload = JWTUtil.verify_token(token)
        if payload:
            return payload.get("type") == "refresh"
        return False
