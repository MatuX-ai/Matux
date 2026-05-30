"""
Vircadia Avatar 数据模型

定义 iMatu 用户与 Vircadia Avatar 映射关系的数据模型

@author: iMatu Team
@date: 2026-03-03
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class VircadiaUserMapping(BaseModel):
    """iMatu 用户与 Vircadia Avatar 映射关系"""

    imatu_user_id: str = Field(..., description="iMatu 用户 ID")
    vircadia_user_id: str = Field(..., description="Vircadia 用户 ID")
    ready_player_me_id: Optional[str] = Field(None, description="ReadyPlayerMe ID")

    # Avatar 信息
    avatar_url: Optional[str] = Field(None, description="Avatar 模型 URL")
    avatar_metadata: Optional[Dict[str, Any]] = Field(None, description="Avatar 元数据")
    avatar_name: Optional[str] = Field(None, description="Avatar 名称")

    # 时间戳
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="更新时间"
    )
    last_sync_at: Optional[datetime] = Field(None, description="最后同步时间")

    # 同步状态
    sync_status: str = Field(
        default="pending", description="同步状态：pending/synced/failed"
    )
    sync_error: Optional[str] = Field(None, description="同步错误信息")

    class Config:
        table_name = "vircadia_user_mappings"
        json_schema_extra = {
            "example": {
                "imatu_user_id": "user_12345",
                "vircadia_user_id": "vircadia_67890",
                "ready_player_me_id": "rpm_abcde",
                "avatar_url": "https://models.readyplayer.me/user.glb",
                "avatar_name": "My Avatar",
                "sync_status": "synced",
            }
        }


class AvatarMetadata(BaseModel):
    """Avatar 元数据"""

    # 基本信息
    name: str
    description: Optional[str] = None
    version: str = "1.0"

    # 技术规格
    file_format: str = Field(..., description="文件格式：glb/gltf/fbx/vrm")
    file_size_bytes: int = Field(..., description="文件大小（字节）")
    vertices_count: int = Field(..., description="顶点数")
    polygons_count: int = Field(..., description="多边形数")

    # 骨骼和网格
    bones: list = Field(default_factory=list, description="骨骼列表")
    meshes: list = Field(default_factory=list, description="网格列表")
    materials: list = Field(default_factory=list, description="材质列表")

    # 动画
    animations: list = Field(default_factory=list, description="动画列表")
    has_humanoid_rig: bool = Field(default=False, description="是否包含人形绑定")

    # 性能指标
    lod_levels: int = Field(default=1, description="LOD 级别数")
    texture_resolution: Optional[str] = Field(None, description="纹理分辨率")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Test Avatar",
                "file_format": "glb",
                "vertices_count": 15000,
                "bones": ["Hips", "Spine", "Head", "LeftArm", "RightArm"],
                "has_humanoid_rig": True,
            }
        }


class AvatarSyncRequest(BaseModel):
    """Avatar 同步请求"""

    user_id: str
    avatar_url: str
    ready_player_me_id: Optional[str] = None
    metadata: Optional[AvatarMetadata] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_12345",
                "avatar_url": "https://models.readyplayer.me/user.glb",
                "ready_player_me_id": "rpm_abcde",
            }
        }


class AvatarSyncResponse(BaseModel):
    """Avatar 同步响应"""

    success: bool
    message: str
    mapping: Optional[VircadiaUserMapping] = None
    error_code: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Avatar synced successfully",
                "mapping": {
                    "imatu_user_id": "user_12345",
                    "vircadia_user_id": "vircadia_67890",
                },
            }
        }


class ReadyPlayerMeAvatar(BaseModel):
    """ReadyPlayerMe Avatar 信息"""

    id: str
    url: str
    name: str
    thumbnail_url: Optional[str] = None

    # 技术信息
    format: str = "glb"
    lod_count: int = 1
    bone_count: int = 0
    blend_shape_count: int = 0

    # 创建信息
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "rpm_avatar_123",
                "url": "https://models.readyplayer.me/user.glb",
                "name": "My Custom Avatar",
                "format": "glb",
            }
        }
