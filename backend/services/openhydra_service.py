"""
OpenHydra AI 沙箱环境服务
提供容器生命周期管理、用户认证集成、Jupyter 环境管理等功能
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ContainerConfig:
    """容器配置模型"""

    user_id: str
    cpu: float = 2.0
    memory: str = "4Gi"
    gpu: float = 0.0
    image: str = "xedu/notebook:latest"
    volumes: Optional[List[str]] = None


@dataclass
class ContainerInfo:
    """容器信息模型"""

    container_id: str
    user_id: str
    status: str  # 'running', 'stopped', 'pending'
    jupyter_url: str
    created_at: datetime
    expires_at: datetime
    resources: Dict[str, Any]


class OpenHydraServiceError(Exception):
    """OpenHydra 服务异常"""

    pass


class OpenHydraService:
    """
    OpenHydra AI 沙箱环境服务

    功能:
    1. 容器生命周期管理（创建、启动、停止、删除）
    2. Jupyter 访问 Token 生成
    3. 容器状态监控
    4. 用户会话管理
    """

    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        """
        初始化 OpenHydra 服务

        Args:
            base_url: OpenHydra API 基础 URL
            api_key: API 密钥
            timeout: HTTP 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

        # HTTP 客户端（异步）
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 异步客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def create_container(self, config: ContainerConfig) -> ContainerInfo:
        """
        为用户创建专属 AI 实训容器

        Args:
            config: 容器配置

        Returns:
            ContainerInfo: 容器信息

        Raises:
            OpenHydraServiceError: 创建失败时抛出
        """
        try:
            client = await self._get_client()

            # 构建请求载荷
            payload = {
                "user_id": config.user_id,
                "image": config.image,
                "resources": {
                    "cpu": config.cpu,
                    "memory": config.memory,
                    "gpu": config.gpu,
                },
                "volumes": config.volumes or [f"user-data-{config.user_id}"],
            }

            # 调用 OpenHydra API
            response = await client.post("/api/v1/containers", json=payload)

            if response.status_code != 201:
                raise OpenHydraServiceError(
                    f"创建容器失败：HTTP {response.status_code} - {response.text}"
                )

            data = response.json()

            # 解析响应
            container_info = ContainerInfo(
                container_id=data["container_id"],
                user_id=config.user_id,
                status=data["status"],
                jupyter_url=data["jupyter_url"],
                created_at=datetime.fromisoformat(data["created_at"]),
                expires_at=datetime.fromisoformat(data["expires_at"]),
                resources=data["resources"],
            )

            logger.info(
                f"容器创建成功：{container_info.container_id} (用户：{config.user_id})"
            )
            return container_info

        except httpx.HTTPError as e:
            logger.error(f"HTTP 错误：{e}")
            raise OpenHydraServiceError(f"容器创建失败：{str(e)}")
        except Exception as e:
            logger.error(f"意外错误：{e}")
            raise OpenHydraServiceError(f"容器创建失败：{str(e)}")

    async def get_container(self, user_id: str) -> Optional[ContainerInfo]:
        """
        获取用户的容器信息

        Args:
            user_id: 用户 ID

        Returns:
            Optional[ContainerInfo]: 容器信息，不存在则返回 None
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/api/v1/containers/user/{user_id}")

            if response.status_code == 404:
                return None

            if response.status_code != 200:
                raise OpenHydraServiceError(
                    f"获取容器失败：HTTP {response.status_code}"
                )

            data = response.json()

            return ContainerInfo(
                container_id=data["container_id"],
                user_id=data["user_id"],
                status=data["status"],
                jupyter_url=data["jupyter_url"],
                created_at=datetime.fromisoformat(data["created_at"]),
                expires_at=datetime.fromisoformat(data["expires_at"]),
                resources=data["resources"],
            )

        except httpx.HTTPError as e:
            logger.error(f"HTTP 错误：{e}")
            raise OpenHydraServiceError(f"获取容器失败：{str(e)}")

    async def start_container(self, container_id: str) -> Dict[str, Any]:
        """
        启动容器

        Args:
            container_id: 容器 ID

        Returns:
            Dict: 启动结果
        """
        try:
            client = await self._get_client()
            response = await client.post(f"/api/v1/containers/{container_id}/start")

            if response.status_code != 200:
                raise OpenHydraServiceError(
                    f"启动容器失败：HTTP {response.status_code}"
                )

            result = response.json()
            logger.info(f"容器启动成功：{container_id}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP 错误：{e}")
            raise OpenHydraServiceError(f"容器启动失败：{str(e)}")

    async def stop_container(self, container_id: str) -> Dict[str, Any]:
        """
        停止容器

        Args:
            container_id: 容器 ID

        Returns:
            Dict: 停止结果
        """
        try:
            client = await self._get_client()
            response = await client.post(f"/api/v1/containers/{container_id}/stop")

            if response.status_code != 200:
                raise OpenHydraServiceError(
                    f"停止容器失败：HTTP {response.status_code}"
                )

            result = response.json()
            logger.info(f"容器停止成功：{container_id}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP 错误：{e}")
            raise OpenHydraServiceError(f"容器停止失败：{str(e)}")

    async def delete_container(self, container_id: str) -> Dict[str, Any]:
        """
        删除容器

        Args:
            container_id: 容器 ID

        Returns:
            Dict: 删除结果
        """
        try:
            client = await self._get_client()
            response = await client.delete(f"/api/v1/containers/{container_id}")

            if response.status_code != 200:
                raise OpenHydraServiceError(
                    f"删除容器失败：HTTP {response.status_code}"
                )

            result = response.json()
            logger.info(f"容器删除成功：{container_id}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP 错误：{e}")
            raise OpenHydraServiceError(f"容器删除失败：{str(e)}")

    async def generate_access_token(self, user_id: str, expiry_hours: int = 8) -> str:
        """
        生成 Jupyter 访问 Token

        Args:
            user_id: 用户 ID
            expiry_hours: Token 有效期（小时）

        Returns:
            str: Jupyter 访问 Token
        """
        try:
            client = await self._get_client()

            payload = {"user_id": user_id, "expiry_hours": expiry_hours}

            response = await client.post("/api/v1/users/tokens", json=payload)

            if response.status_code != 200:
                raise OpenHydraServiceError(
                    f"生成 Token 失败：HTTP {response.status_code}"
                )

            data = response.json()
            token = data["token"]

            logger.info(f"Token 生成成功：用户 {user_id}")
            return token

        except httpx.HTTPError as e:
            logger.error(f"HTTP 错误：{e}")
            raise OpenHydraServiceError(f"Token 生成失败：{str(e)}")

    async def get_container_status(self, container_id: str) -> Dict[str, Any]:
        """
        获取容器状态

        Args:
            container_id: 容器 ID

        Returns:
            Dict: 容器状态信息
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/api/v1/containers/{container_id}/status")

            if response.status_code != 200:
                raise OpenHydraServiceError(
                    f"获取状态失败：HTTP {response.status_code}"
                )

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP 错误：{e}")
            raise OpenHydraServiceError(f"获取容器状态失败：{str(e)}")

    async def list_user_containers(self, user_id: str) -> List[ContainerInfo]:
        """
        列出用户的所有容器

        Args:
            user_id: 用户 ID

        Returns:
            List[ContainerInfo]: 容器列表
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/api/v1/containers/user/{user_id}/list")

            if response.status_code != 200:
                raise OpenHydraServiceError(
                    f"获取容器列表失败：HTTP {response.status_code}"
                )

            containers_data = response.json()
            containers = []

            for data in containers_data:
                containers.append(
                    ContainerInfo(
                        container_id=data["container_id"],
                        user_id=data["user_id"],
                        status=data["status"],
                        jupyter_url=data["jupyter_url"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        expires_at=datetime.fromisoformat(data["expires_at"]),
                        resources=data["resources"],
                    )
                )

            return containers

        except httpx.HTTPError as e:
            logger.error(f"HTTP 错误：{e}")
            raise OpenHydraServiceError(f"获取容器列表失败：{str(e)}")

    async def extend_container_expiry(
        self, container_id: str, additional_hours: int
    ) -> Dict[str, Any]:
        """
        延长容器有效期

        Args:
            container_id: 容器 ID
            additional_hours: 延长的时间（小时）

        Returns:
            Dict: 延期结果
        """
        try:
            client = await self._get_client()

            payload = {
                "container_id": container_id,
                "additional_hours": additional_hours,
            }

            response = await client.post(
                f"/api/v1/containers/{container_id}/extend", json=payload
            )

            if response.status_code != 200:
                raise OpenHydraServiceError(f"延期失败：HTTP {response.status_code}")

            result = response.json()
            logger.info(f"容器延期成功：{container_id} (+{additional_hours}小时)")
            return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP 错误：{e}")
            raise OpenHydraServiceError(f"容器延期失败：{str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            Dict: 服务健康状态
        """
        try:
            client = await self._get_client()
            response = await client.get("/health")

            if response.status_code != 200:
                return {
                    "status": "unhealthy",
                    "service": "openhydra",
                    "error": f"HTTP {response.status_code}",
                }

            data = response.json()
            return {"status": "healthy", "service": "openhydra", "details": data}

        except httpx.HTTPError as e:
            logger.error(f"HTTP 错误：{e}")
            return {"status": "unhealthy", "service": "openhydra", "error": str(e)}
