"""
OpenHydra AI 沙箱环境 API路由
提供容器管理、Jupyter 环境访问等 RESTful API
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.settings import settings
from models.user import User
from services.openhydra_service import (
    ContainerConfig,
    OpenHydraService,
    OpenHydraServiceError,
)
from utils.dependencies import get_current_user_sync, get_sync_db

logger = logging.getLogger(__name__)

# 从配置初始化 OpenHydra 服务
openhydra_service = OpenHydraService(
    base_url=settings.OPENHYDRA_API_URL, api_key=settings.OPENHYDRA_API_KEY
)

router = APIRouter(
    prefix="/api/v1/org/{org_id}/ai-lab",
    tags=["AI 实验室"],
    responses={404: {"description": "Not found"}},
)


# ==================== 请求/响应模型 ====================


class CreateContainerRequest(BaseModel):
    """创建容器请求"""

    cpu: float = Field(default=2.0, description="CPU 核心数", ge=0.5, le=8.0)
    memory: str = Field(default="4Gi", description="内存大小")
    gpu: float = Field(default=0.0, description="GPU 配额", ge=0.0, le=1.0)
    image: str = Field(default="xedu/notebook:latest", description="容器镜像")
    volumes: Optional[List[str]] = Field(default=None, description="挂载卷列表")


class ContainerResponse(BaseModel):
    """容器响应"""

    container_id: str
    user_id: str
    status: str
    jupyter_url: str
    created_at: str
    expires_at: str
    resources: dict

    class Config:
        from_attributes = True


class EnterLabResponse(BaseModel):
    """进入实验室响应"""

    success: bool
    container_id: str
    jupyter_url: str
    access_token: str
    message: str


class ContainerStatusResponse(BaseModel):
    """容器状态响应"""

    container_id: str
    status: str
    is_running: bool
    jupyter_accessible: bool
    resource_usage: dict


# ==================== 依赖注入 ====================


def get_openhydra_service() -> OpenHydraService:
    """获取 OpenHydra 服务实例"""
    return openhydra_service


# ==================== API路由 ====================


@router.post("/enter", response_model=EnterLabResponse)
async def enter_ai_lab(
    org_id: int,
    request: Optional[CreateContainerRequest] = None,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
    service: OpenHydraService = Depends(get_openhydra_service),
):
    """
    进入 AI 实验室

    一键为学生创建或恢复专属 AI 实训环境

    Args:
        org_id: 组织 ID
        request: 容器配置（可选，使用默认值）
        current_user: 当前用户
        db: 数据库会话
        service: OpenHydra 服务

    Returns:
        EnterLabResponse: 进入实验室结果

    Raises:
        HTTPException: 创建或获取容器失败
    """
    try:
        user_id_str = str(current_user.id)

        # 1. 检查用户是否已有运行中的容器
        existing_container = await service.get_container(user_id_str)

        if existing_container and existing_container.status == "running":
            # 容器已存在且运行中，直接返回访问信息
            logger.info(
                f"用户 {current_user.id} 已有运行中的容器：{existing_container.container_id}"
            )

            # 生成新的访问 Token
            access_token = await service.generate_access_token(user_id_str)

            return EnterLabResponse(
                success=True,
                container_id=existing_container.container_id,
                jupyter_url=existing_container.jupyter_url,
                access_token=access_token,
                message="继续实验",
            )

        # 2. 容器不存在或未运行，创建新容器
        if request is None:
            request = CreateContainerRequest()

        config = ContainerConfig(
            user_id=user_id_str,
            cpu=request.cpu,
            memory=request.memory,
            gpu=request.gpu,
            image=request.image,
            volumes=request.volumes,
        )

        logger.info(f"为用户 {current_user.id} 创建新容器")
        container_info = await service.create_container(config)

        # 3. 生成访问 Token
        access_token = await service.generate_access_token(user_id_str)

        logger.info(f"容器创建成功：{container_info.container_id}")

        return EnterLabResponse(
            success=True,
            container_id=container_info.container_id,
            jupyter_url=container_info.jupyter_url,
            access_token=access_token,
            message="开始实验",
        )

    except OpenHydraServiceError as e:
        logger.error(f"OpenHydra 服务错误：{e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI 实验室服务暂时不可用：{str(e)}",
        )
    except Exception as e:
        logger.error(f"意外错误：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误：{str(e)}",
        )


@router.get("/container/status", response_model=ContainerStatusResponse)
async def get_container_status(
    org_id: int,
    current_user: User = Depends(get_current_user_sync),
    service: OpenHydraService = Depends(get_openhydra_service),
):
    """
    获取容器状态

    查询用户专属容器的运行状态和资源使用情况

    Args:
        org_id: 组织 ID
        current_user: 当前用户
        service: OpenHydra 服务

    Returns:
        ContainerStatusResponse: 容器状态信息
    """
    try:
        user_id_str = str(current_user.id)

        # 获取容器信息
        container = await service.get_container(user_id_str)

        if not container:
            # 容器不存在
            return ContainerStatusResponse(
                container_id="",
                status="not_found",
                is_running=False,
                jupyter_accessible=False,
                resource_usage={},
            )

        # 获取详细状态
        status_detail = await service.get_container_status(container.container_id)

        return ContainerStatusResponse(
            container_id=container.container_id,
            status=container.status,
            is_running=container.status == "running",
            jupyter_accessible=status_detail.get("jupyter_accessible", False),
            resource_usage=status_detail.get("resource_usage", {}),
        )

    except OpenHydraServiceError as e:
        logger.error(f"OpenHydra 服务错误：{e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"获取容器状态失败：{str(e)}",
        )
    except Exception as e:
        logger.error(f"意外错误：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误：{str(e)}",
        )


@router.post("/container/stop")
async def stop_container(
    org_id: int,
    current_user: User = Depends(get_current_user_sync),
    service: OpenHydraService = Depends(get_openhydra_service),
):
    """
    停止容器

    手动停止用户的 AI 实训容器（节省资源）

    Args:
        org_id: 组织 ID
        current_user: 当前用户
        service: OpenHydra 服务

    Returns:
        Dict: 停止结果
    """
    try:
        user_id_str = str(current_user.id)

        # 获取容器
        container = await service.get_container(user_id_str)

        if not container:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="未找到运行中的容器"
            )

        # 停止容器
        result = await service.stop_container(container.container_id)

        logger.info(f"容器已停止：{container.container_id}")

        return {
            "success": True,
            "message": "容器已停止",
            "container_id": container.container_id,
        }

    except OpenHydraServiceError as e:
        logger.error(f"OpenHydra 服务错误：{e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"停止容器失败：{str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"意外错误：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误：{str(e)}",
        )


@router.post("/container/extend")
async def extend_container(
    org_id: int = Path(..., description="组织 ID"),
    hours: int = Body(default=4, description="延长的时间（小时）", ge=1, le=24),
    current_user: User = Depends(get_current_user_sync),
    service: OpenHydraService = Depends(get_openhydra_service),
):
    """
    延长容器有效期

    当容器即将过期时，可申请延长使用时间

    Args:
        org_id: 组织 ID
        hours: 延长的时间（小时）
        current_user: 当前用户
        service: OpenHydra 服务

    Returns:
        Dict: 延期结果
    """
    try:
        user_id_str = str(current_user.id)

        # 获取容器
        container = await service.get_container(user_id_str)

        if not container:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="未找到运行中的容器"
            )

        # 延长有效期
        result = await service.extend_container_expiry(
            container.container_id, additional_hours=hours
        )

        logger.info(f"容器已延期：{container.container_id} (+{hours}小时)")

        return {
            "success": True,
            "message": f"容器已延期 {hours} 小时",
            "new_expiry": result.get("new_expiry"),
            "container_id": container.container_id,
        }

    except OpenHydraServiceError as e:
        logger.error(f"OpenHydra 服务错误：{e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"延期失败：{str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"意外错误：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器错误：{str(e)}",
        )


@router.get("/health")
async def health_check(service: OpenHydraService = Depends(get_openhydra_service)):
    """
    健康检查

    检查 OpenHydra 服务的连接状态

    Returns:
        Dict: 健康状态
    """
    health_status = await service.health_check()

    if health_status["status"] != "healthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health_status
        )

    return health_status
