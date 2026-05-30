"""
Vircadia Avatar 管理路由

提供 Avatar URL 验证、元数据提取、上传等功能
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl

from services.vircadia_avatar_sync_impl import (
    AvatarMetadataExtractor,
    AvatarURLValidator,
    extract_avatar_metadata_enhanced,
    validate_avatar_url_enhanced,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vircadia/avatar", tags=["Vircadia Avatar 管理"])


# ==================== 数据模型 ====================


class AvatarURLValidationRequest(BaseModel):
    """Avatar URL 验证请求"""

    url: str
    check_accessibility: bool = True


class AvatarURLValidationResponse(BaseModel):
    """Avatar URL 验证响应"""

    valid: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class AvatarMetadataRequest(BaseModel):
    """Avatar 元数据提取请求"""

    url: str


class AvatarMetadataResponse(BaseModel):
    """Avatar 元数据响应"""

    success: bool
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ==================== API 端点 ====================


@router.post("/validate", response_model=AvatarURLValidationResponse)
async def validate_avatar_url(request: AvatarURLValidationRequest):
    """
    验证 Avatar URL 有效性

    Args:
        request: 验证请求

    Returns:
        验证结果
    """
    try:
        # 执行验证
        is_valid, error_message = await AvatarURLValidator.validate(request.url)

        if is_valid:
            return AvatarURLValidationResponse(
                valid=True,
                message="✅ Avatar URL 验证通过",
                details={
                    "url": request.url,
                    "supported_formats": [".glb", ".gltf", ".fbx"],
                    "max_file_size_mb": 50,
                },
            )
        else:
            return AvatarURLValidationResponse(
                valid=False, message=f"❌ {error_message}", details={"url": request.url}
            )

    except Exception as e:
        logger.error(f"Avatar URL 验证异常：{e}", exc_info=True)
        return AvatarURLValidationResponse(
            valid=False,
            message=f"❌ 验证过程发生错误：{str(e)}",
            details={"url": request.url},
        )


@router.post("/metadata", response_model=AvatarMetadataResponse)
async def extract_avatar_metadata(request: AvatarMetadataRequest):
    """
    提取 Avatar 元数据

    Args:
        request: 元数据提取请求

    Returns:
        元数据信息
    """
    try:
        # 先验证 URL
        is_valid, error = await AvatarURLValidator.validate(request.url)
        if not is_valid:
            return AvatarMetadataResponse(
                success=False, metadata=None, error=f"URL 验证失败：{error}"
            )

        # 提取元数据
        metadata = await AvatarMetadataExtractor.extract(request.url)

        if metadata:
            return AvatarMetadataResponse(success=True, metadata=metadata, error=None)
        else:
            return AvatarMetadataResponse(
                success=False, metadata=None, error="元数据提取失败"
            )

    except Exception as e:
        logger.error(f"Avatar 元数据提取异常：{e}", exc_info=True)
        return AvatarMetadataResponse(success=False, metadata=None, error=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "Vircadia Avatar Service",
        "features": {
            "url_validation": True,
            "metadata_extraction": True,
            "storage_upload": True,
        },
    }
