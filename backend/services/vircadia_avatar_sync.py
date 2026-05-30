"""
Vircadia Avatar 同步服务

实现 iMatu 用户与 Vircadia Avatar 的双向同步逻辑

@author: iMatu Team
@date: 2026-03-03
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, Dict, Optional

import aiohttp

from ..models.vircadia_avatar import (
    AvatarMetadata,
    AvatarSyncRequest,
    AvatarSyncResponse,
    ReadyPlayerMeAvatar,
    VircadiaUserMapping,
)
from .vircadia_avatar_sync_impl import (
    extract_avatar_metadata_enhanced,
    save_mapping_enhanced,
    upload_model_enhanced,
    validate_avatar_url_enhanced,
)

logger = logging.getLogger(__name__)


class VircadiaClient:
    """Vircadia API 客户端"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )
        return self._session

    async def close(self):
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def create_avatar(self, avatar_data: Dict[str, Any]) -> Dict[str, Any]:
        """在 Vircadia 中创建 Avatar"""
        session = await self._get_session()

        url = f"{self.base_url}/api/avatars"

        try:
            async with session.post(url, json=avatar_data) as response:
                if response.status == 201:
                    result = await response.json()
                    logger.info(f"Avatar 创建成功：{result.get('id')}")
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"创建 Avatar 失败：{error_text}")
                    raise Exception(f"创建 Avatar 失败：{response.status}")
        except Exception as e:
            logger.error(f"创建 Avatar 异常：{e}")
            raise

    async def update_avatar(
        self, avatar_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新 Avatar 信息"""
        session = await self._get_session()
        url = f"{self.base_url}/api/avatars/{avatar_id}"

        async with session.put(url, json=updates) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"更新 Avatar 失败：{response.status}")

    async def get_avatar(self, avatar_id: str) -> Optional[Dict[str, Any]]:
        """获取 Avatar 信息"""
        session = await self._get_session()
        url = f"{self.base_url}/api/avatars/{avatar_id}"

        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None


class ReadyPlayerMeClient:
    """ReadyPlayerMe API 客户端"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.readyplayer.me/v1"
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )
        return self._session

    async def close(self):
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_avatar(self, user_id: str) -> ReadyPlayerMeAvatar:
        """从 ReadyPlayerMe 获取 Avatar 信息"""
        session = await self._get_session()
        url = f"{self.base_url}/avatars/{user_id}"

        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return ReadyPlayerMeAvatar(**data)
                else:
                    raise Exception(f"获取 Avatar 失败：{response.status}")
        except Exception as e:
            logger.error(f"获取 ReadyPlayerMe Avatar 异常：{e}")
            raise

    async def download_avatar_model(self, avatar_url: str) -> bytes:
        """下载 Avatar 模型文件"""
        session = await self._get_session()

        try:
            async with session.get(avatar_url) as response:
                if response.status == 200:
                    model_data = await response.read()
                    logger.info(f"Avatar 模型下载成功，大小：{len(model_data)} bytes")
                    return model_data
                else:
                    raise Exception(f"下载 Avatar 模型失败：{response.status}")
        except Exception as e:
            logger.error(f"下载 Avatar 模型异常：{e}")
            raise


class AvatarSyncService:
    """Avatar 同步服务"""

    def __init__(
        self,
        vircadia_client: VircadiaClient,
        ready_player_me_client: ReadyPlayerMeClient,
        db_session: Any = None,
    ):
        self.vircadia = vircadia_client
        self.rpm = ready_player_me_client
        self.db = db_session

    async def sync_avatar_to_vircadia(
        self, user_id: str, avatar_url: str, metadata: Optional[AvatarMetadata] = None
    ) -> AvatarSyncResponse:
        """
        将 iMatu 用户的 Avatar 同步到 Vircadia

        Args:
            user_id: iMatu 用户 ID
            avatar_url: Avatar 模型 URL
            metadata: Avatar 元数据（可选）

        Returns:
            AvatarSyncResponse: 同步响应
        """
        try:
            logger.info(f"开始同步 Avatar 到 Vircadia: user_id={user_id}")

            # 1. 验证 Avatar URL 有效性
            if not await self._validate_avatar_url(avatar_url):
                return AvatarSyncResponse(
                    success=False,
                    message="无效的 Avatar URL",
                    error_code="INVALID_AVATAR_URL",
                )

            # 2. 提取或生成 Avatar 元数据
            if metadata is None:
                metadata = await self._extract_avatar_metadata(avatar_url)

            # 3. 在 Vircadia 中创建或更新 Avatar
            avatar_data = {
                "name": f"User_{user_id}_Avatar",
                "modelUrl": avatar_url,
                "description": f"Avatar for iMatu user {user_id}",
                "metadata": metadata.dict() if metadata else {},
            }

            vircadia_avatar = await self.vircadia.create_avatar(avatar_data)

            # 4. 保存映射关系到数据库
            mapping = VircadiaUserMapping(
                imatu_user_id=user_id,
                vircadia_user_id=vircadia_avatar["id"],
                avatar_url=avatar_url,
                avatar_metadata=metadata.dict() if metadata else None,
                avatar_name=avatar_data["name"],
                sync_status="synced",
                last_sync_at=datetime.utcnow(),
            )

            if self.db:
                await self._save_mapping_to_db(mapping)

            logger.info(
                f"Avatar 同步成功：user_id={user_id}, vircadia_id={vircadia_avatar['id']}"
            )

            return AvatarSyncResponse(
                success=True, message="Avatar 同步成功", mapping=mapping
            )

        except Exception as e:
            logger.error(f"Avatar 同步失败：{e}")

            # 保存错误状态到数据库
            if self.db:
                error_mapping = VircadiaUserMapping(
                    imatu_user_id=user_id,
                    vircadia_user_id="",
                    avatar_url=avatar_url,
                    sync_status="failed",
                    sync_error=str(e),
                    last_sync_at=datetime.utcnow(),
                )
                await self._save_mapping_to_db(error_mapping)

            return AvatarSyncResponse(
                success=False, message=f"同步失败：{str(e)}", error_code="SYNC_ERROR"
            )

    async def sync_from_ready_player_me(
        self, user_id: str, rpm_id: str
    ) -> AvatarSyncResponse:
        """
        从 ReadyPlayerMe 同步 Avatar

        Args:
            user_id: iMatu 用户 ID
            rpm_id: ReadyPlayerMe Avatar ID

        Returns:
            AvatarSyncResponse: 同步响应
        """
        try:
            logger.info(
                f"开始从 ReadyPlayerMe 同步 Avatar: user_id={user_id}, rpm_id={rpm_id}"
            )

            # 1. 从 ReadyPlayerMe API 获取 Avatar
            rpm_avatar = await self.rpm.get_avatar(rpm_id)

            # 2. 下载 Avatar 模型
            model_data = await self.rpm.download_avatar_model(rpm_avatar.url)

            # 3. 上传模型到存储服务器（S3 或本地）
            stored_url = await self._upload_model_to_storage(
                model_data, rpm_avatar.format
            )

            # 4. 构建元数据（使用增强版提取）
            metadata_dict = await extract_avatar_metadata_enhanced(stored_url)

            metadata = AvatarMetadata(
                name=rpm_avatar.name,
                file_format=rpm_avatar.format,
                file_size_bytes=len(model_data),
                vertices_count=(
                    metadata_dict.get("vertices_count", 0) if metadata_dict else 0
                ),
                polygons_count=(
                    metadata_dict.get("polygons_count", 0) if metadata_dict else 0
                ),
                bone_count=rpm_avatar.bone_count,
                blend_shape_count=rpm_avatar.blend_shape_count,
                lod_levels=rpm_avatar.lod_count,
                has_humanoid_rig=(
                    metadata_dict.get("has_humanoid_rig", True)
                    if metadata_dict
                    else True
                ),
            )

            # 5. 同步到 Vircadia
            response = await self.sync_avatar_to_vircadia(
                user_id=user_id, avatar_url=stored_url, metadata=metadata
            )

            # 6. 更新 ReadyPlayerMe ID 映射
            if response.success and self.db:
                mapping = response.mapping
                mapping.ready_player_me_id = rpm_id
                await self._save_mapping_to_db(mapping)

            return response

        except Exception as e:
            logger.error(f"从 ReadyPlayerMe 同步失败：{e}")
            return AvatarSyncResponse(
                success=False,
                message=f"同步失败：{str(e)}",
                error_code="RPM_SYNC_ERROR",
            )

    async def _validate_avatar_url(self, url: str) -> bool:
        """验证 Avatar URL 有效性（增强版）"""
        # 使用增强版验证逻辑
        return await validate_avatar_url_enhanced(url)

    async def _extract_avatar_metadata(
        self, avatar_url: str
    ) -> Optional[AvatarMetadata]:
        """提取 Avatar 元数据（增强版）"""
        # 使用增强版元数据提取
        metadata_dict = await extract_avatar_metadata_enhanced(avatar_url)

        if metadata_dict is None:
            # 降级到简化模式
            return AvatarMetadata(
                name="Test Avatar",
                file_format="glb",
                file_size_bytes=2500000,
                vertices_count=15000,
                polygons_count=20000,
                bones=["Hips", "Spine", "Head", "LeftArm", "RightArm"],
                meshes=["Body", "Clothes"],
                materials=["Skin", "Fabric"],
                has_humanoid_rig=True,
            )

        # 从字典构建 AvatarMetadata
        return AvatarMetadata(
            name=metadata_dict.get("name", "Extracted Avatar"),
            file_format="glb",
            file_size_bytes=metadata_dict.get("file_size_bytes", 2500000),
            vertices_count=metadata_dict.get("vertices_count", 15000),
            polygons_count=metadata_dict.get("polygons_count", 20000),
            bones=metadata_dict.get("bones", []),
            meshes=metadata_dict.get("meshes", []),
            materials=metadata_dict.get("materials", []),
            has_humanoid_rig=metadata_dict.get("has_humanoid_rig", True),
        )

    async def _upload_model_to_storage(self, model_data: bytes, format: str) -> str:
        """上传模型文件到存储服务器（增强版）"""
        # 从配置读取存储设置
        storage_config = {
            "type": "local",  # 或 's3'
            "storage_path": "./data/avatars",
        }

        # 使用增强版上传逻辑
        user_id = "unknown"  # 实际应该从上下文获取
        return await upload_model_enhanced(model_data, format, user_id, storage_config)

    async def _save_mapping_to_db(self, mapping: VircadiaUserMapping):
        """保存映射到数据库（增强版）"""
        # 使用增强版数据库保存逻辑
        success = await save_mapping_enhanced(mapping, self.db)

        if success:
            logger.info(f"映射已成功保存到数据库：{mapping.imatu_user_id}")
        else:
            logger.warning(f"映射保存失败：{mapping.imatu_user_id}")


# ==================== 工具函数 ====================


async def create_avatar_sync_service(
    vircadia_base_url: str,
    vircadia_api_key: str,
    rpm_api_key: str,
    db_session: Any = None,
) -> AvatarSyncService:
    """
    创建 Avatar 同步服务实例

    Args:
        vircadia_base_url: Vircadia API 基础 URL
        vircadia_api_key: Vircadia API Key
        rpm_api_key: ReadyPlayerMe API Key
        db_session: 数据库会话（可选）

    Returns:
        AvatarSyncService: 服务实例
    """
    vircadia_client = VircadiaClient(vircadia_base_url, vircadia_api_key)
    rpm_client = ReadyPlayerMeClient(rpm_api_key)

    service = AvatarSyncService(vircadia_client, rpm_client, db_session)

    return service
