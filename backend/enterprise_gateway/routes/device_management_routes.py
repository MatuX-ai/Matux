"""
设备管理路由
提供设备白名单管理的API端点
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from models.enterprise_models import DeviceApprovalRequest, DeviceWhitelistUpdate
from services.device_whitelist_service import device_whitelist_service
from utils.database import get_db
from utils.security_utils import SecurityUtil

router = APIRouter()
security_util = SecurityUtil()


@router.post("/devices/approve", response_model=dict)
async def approve_device(
    device_request: DeviceApprovalRequest,
    current_client_id: str = Depends(
        lambda: "admin_client"
    ),  # 简化实现，实际应该从认证中获取
    db: Session = Depends(get_db),
):
    """
    审批设备加入白名单

    Args:
        device_request: 设备审批请求
        current_client_id: 当前操作的客户端ID
        db: 数据库会话

    Returns:
        审批结果
    """
    try:
        # 验证操作权限（简化实现）
        # 实际应该检查当前用户是否有管理权限

        device = device_whitelist_service.add_device_to_whitelist(
            device_request, approved_by=1, db=db  # 简化实现
        )

        return {
            "success": True,
            "message": "Device approved successfully",
            "device_id": device.id,
            "device_info": device.to_dict(),
        }

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve device: {str(e)}",
        )


@router.get("/devices/{client_id}", response_model=List[dict])
async def get_client_devices(
    client_id: str,
    include_expired: bool = Query(False, description="是否包含已过期设备"),
    db: Session = Depends(get_db),
):
    """
    获取企业客户的设备列表

    Args:
        client_id: 企业客户端ID
        include_expired: 是否包含已过期设备
        db: 数据库会话

    Returns:
        设备列表
    """
    try:
        devices = device_whitelist_service.get_client_devices(
            client_id, include_expired=include_expired, db=db
        )

        return [device.to_dict() for device in devices]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get devices: {str(e)}",
        )


@router.get("/devices/detail/{device_id}", response_model=dict)
async def get_device_detail(device_id: int, db: Session = Depends(get_db)):
    """
    获取设备详细信息

    Args:
        device_id: 设备ID
        db: 数据库会话

    Returns:
        设备详细信息
    """
    try:
        device = device_whitelist_service.get_device_by_id(device_id, db)

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
            )

        return device.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get device detail: {str(e)}",
        )


@router.put("/devices/{device_id}", response_model=dict)
async def update_device_approval(
    device_id: int,
    update_data: DeviceWhitelistUpdate,
    current_client_id: str = Depends(lambda: "admin_client"),  # 简化实现
    db: Session = Depends(get_db),
):
    """
    更新设备审批状态

    Args:
        device_id: 设备ID
        update_data: 更新数据
        current_client_id: 当前操作的客户端ID
        db: 数据库会话

    Returns:
        更新结果
    """
    try:
        device = device_whitelist_service.update_device_approval(
            device_id, update_data, approved_by=1, db=db  # 简化实现
        )

        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
            )

        return {
            "success": True,
            "message": "Device updated successfully",
            "device_info": device.to_dict(),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update device: {str(e)}",
        )


@router.delete("/devices/{device_id}", response_model=dict)
async def remove_device(
    device_id: int,
    current_client_id: str = Depends(lambda: "admin_client"),  # 简化实现
    db: Session = Depends(get_db),
):
    """
    从白名单中移除设备

    Args:
        device_id: 设备ID
        current_client_id: 当前操作的客户端ID
        db: 数据库会话

    Returns:
        删除结果
    """
    try:
        success = device_whitelist_service.remove_device_from_whitelist(device_id, db)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Device not found"
            )

        return {"success": True, "message": "Device removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove device: {str(e)}",
        )


@router.post("/devices/generate-id", response_model=dict)
async def generate_device_id(ip_address: str, user_agent: str):
    """
    生成设备ID

    Args:
        ip_address: IP地址
        user_agent: 用户代理

    Returns:
        生成的设备ID
    """
    try:
        # 验证IP地址格式
        if not security_util.validate_ip_address(ip_address):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid IP address format",
            )

        device_id = device_whitelist_service.generate_device_id(ip_address, user_agent)

        return {"device_id": device_id, "generated_at": datetime.utcnow().isoformat()}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate device ID: {str(e)}",
        )


@router.post("/devices/cleanup", response_model=dict)
async def cleanup_expired_devices(
    current_client_id: str = Depends(lambda: "admin_client"),  # 简化实现
    db: Session = Depends(get_db),
):
    """
    清理已过期的设备记录

    Args:
        current_client_id: 当前操作的客户端ID
        db: 数据库会话

    Returns:
        清理结果
    """
    try:
        count = device_whitelist_service.cleanup_expired_devices(db)

        return {
            "success": True,
            "message": f"Cleaned up {count} expired devices",
            "cleaned_count": count,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup expired devices: {str(e)}",
        )
