"""
硬件认证路由模块
提供硬件认证相关的API端点
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.hardware_certification import (
    BadgeConfig,
    BadgeStyle,
    CertificationRequest,
    CertificationResponse,
    CertificationStatus,
)
from services.badge_generator import badge_generator
from services.hardware_certification_service import hardware_certification_service
from utils.logger import setup_logger

router = APIRouter()
logger = setup_logger("INFO")


@router.post("/certify", response_model=CertificationResponse)
async def certify_hardware(request: CertificationRequest):
    """
    硬件认证接口
    对硬件设备进行认证测试并返回认证结果

    Args:
        request: 认证请求对象

    Returns:
        CertificationResponse: 认证响应结果
    """
    try:
        logger.info(f"收到硬件认证请求: {request.hw_id}")

        # 执行认证验证
        response = hardware_certification_service.verify_certification(request)

        logger.info(f"认证完成: {request.hw_id}, 状态: {response.status}")
        return response

    except Exception as e:
        logger.error(f"硬件认证处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"认证处理失败: {str(e)}")


@router.get("/certification/{hw_id}", response_model=CertificationResponse)
async def get_certification_status(hw_id: str):
    """
    获取硬件认证状态

    Args:
        hw_id: 硬件ID

    Returns:
        CertificationResponse: 认证状态信息
    """
    try:
        # 从服务层获取认证历史
        history = hardware_certification_service.get_certification_history(hw_id)

        if not history:
            raise HTTPException(status_code=404, detail="未找到该硬件的认证记录")

        # 构造响应对象
        response = CertificationResponse(
            hw_id=history["hw_id"],
            status=CertificationStatus(history["status"]),
            badge_url=f"https://badges.imatuproject.org/cert/{hw_id}.svg",
            certified_at=(
                datetime.fromisoformat(history["certified_at"])
                if history.get("certified_at")
                else None
            ),
            expires_at=(
                datetime.fromisoformat(history["expires_at"])
                if history.get("expires_at")
                else None
            ),
            test_summary={},  # 简化处理
            failed_tests=[],
            certificate_id=history.get("certificate_id"),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取认证状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取认证状态失败: {str(e)}")


@router.get("/badge/{hw_id}.svg")
async def get_certification_badge(
    hw_id: str,
    style: BadgeStyle = BadgeStyle.STANDARD,
    show_timestamp: bool = True,
    show_version: bool = True,
):
    """
    获取认证徽章SVG

    Args:
        hw_id: 硬件ID
        style: 徽章样式
        show_timestamp: 是否显示时间戳
        show_version: 是否显示版本信息

    Returns:
        SVG格式的认证徽章
    """
    try:
        # 获取认证状态
        history = hardware_certification_service.get_certification_history(hw_id)

        if not history:
            # 如果没有认证记录，返回默认的"未认证"徽章
            config = BadgeConfig(
                style=style, show_timestamp=show_timestamp, show_version=show_version
            )
            svg_content = badge_generator.generate_badge_svg(
                hw_id=hw_id, status=CertificationStatus.PENDING, config=config
            )
        else:
            # 根据认证状态生成徽章
            status = CertificationStatus(history["status"])
            config = BadgeConfig(
                style=style, show_timestamp=show_timestamp, show_version=show_version
            )

            certified_at = None
            if history.get("certified_at"):
                certified_at = datetime.fromisoformat(history["certified_at"])

            svg_content = badge_generator.generate_badge_svg(
                hw_id=hw_id,
                status=status,
                config=config,
                firmware_version=history.get("firmware_version"),
                certified_at=certified_at,
            )

        return Response(
            content=svg_content,
            media_type="image/svg+xml",
            headers={
                "Cache-Control": "public, max-age=3600",  # 缓存1小时
                "Content-Disposition": f'inline; filename="{hw_id}_badge.svg"',
            },
        )

    except Exception as e:
        logger.error(f"生成徽章失败: {str(e)}")
        # 返回错误徽章
        error_config = BadgeConfig(style=BadgeStyle.STANDARD)
        error_svg = badge_generator.generate_badge_svg(
            hw_id=hw_id, status=CertificationStatus.FAILED, config=error_config
        )

        return Response(content=error_svg, media_type="image/svg+xml")


@router.get("/certifications")
async def list_certifications(
    status: Optional[CertificationStatus] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    列出认证记录

    Args:
        status: 筛选特定状态的认证
        limit: 返回记录数量限制
        offset: 偏移量

    Returns:
        认证记录列表
    """
    try:
        all_certifications = hardware_certification_service.get_all_certifications()

        # 转换为列表并排序
        cert_list = list(all_certifications.values())
        cert_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # 应用筛选条件
        if status:
            cert_list = [cert for cert in cert_list if cert["status"] == status.value]

        # 应用分页
        total = len(cert_list)
        cert_list = cert_list[offset : offset + limit]

        return {
            "certifications": cert_list,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"获取认证列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取认证列表失败: {str(e)}")


@router.delete("/certification/{hw_id}")
async def delete_certification(hw_id: str):
    """
    删除认证记录（仅用于测试环境）

    Args:
        hw_id: 硬件ID

    Returns:
        删除结果
    """
    try:
        # 注意：这只是一个示例，在生产环境中应该有权限控制
        certifications = hardware_certification_service.get_all_certifications()

        if hw_id in certifications:
            del certifications[hw_id]
            logger.info(f"删除认证记录: {hw_id}")
            return {"message": "认证记录已删除"}
        else:
            raise HTTPException(status_code=404, detail="未找到该硬件的认证记录")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除认证记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除认证记录失败: {str(e)}")


@router.get("/stats")
async def get_certification_statistics():
    """
    获取认证统计信息

    Returns:
        认证统计信息
    """
    try:
        certifications = hardware_certification_service.get_all_certifications()

        stats = {
            "total": len(certifications),
            "by_status": {},
            "recent_certifications": [],
        }

        # 按状态统计
        for cert in certifications.values():
            status = cert["status"]
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

        # 最近认证（按创建时间排序，取前10个）
        sorted_certs = sorted(
            certifications.values(), key=lambda x: x.get("created_at", ""), reverse=True
        )[:10]

        stats["recent_certifications"] = [
            {
                "hw_id": cert["hw_id"],
                "status": cert["status"],
                "certified_at": cert.get("certified_at"),
                "firmware_version": cert.get("firmware_version"),
            }
            for cert in sorted_certs
        ]

        return stats

    except Exception as e:
        logger.error(f"获取认证统计失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取认证统计失败: {str(e)}")


# 导入Response用于返回SVG内容
from fastapi.responses import Response
