"""
【P3 后台】风控管理 API

路径前缀：/api/v1/admin/risk
- GET    /stats                  - 风控总览
- GET    /blocked-ips            - 封禁列表
- POST   /blocked-ips            - 手动封禁 IP
- DELETE /blocked-ips/{ip}       - 解封 IP
- GET    /scores                 - Top 高风险 IP
- GET    /ip/{ip}                - IP 详细状态
- POST   /reset                  - 重置全部状态
- GET    /rules/endpoints        - 端点规则快照
- GET    /rules/anomalies        - 异常模式快照
- GET    /captcha/stats          - CAPTCHA 统计
- POST   /captcha/reset-stats    - 重置 CAPTCHA 统计

鉴权：
- TODO: 接入后台管理员 token（当前 demo 默认放行，
       生产应使用 Depends(require_admin_user)）
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from security.captcha_stats import get_captcha_stats
from security.risk_control import get_risk_control_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/risk",
    tags=["admin", "risk-control"],
)


# ==================== Pydantic Models ====================


class BlockIPRequest(BaseModel):
    ip: str = Field(..., description="要封禁的 IP 地址")
    duration_seconds: int = Field(
        3600, ge=1, le=86400 * 7, description="封禁时长（秒）"
    )
    reason: str = Field("", max_length=500, description="封禁原因")


class BlockIPResponse(BaseModel):
    ip: str
    blocked_until: float
    duration_seconds: int
    reason: str


class ResetResponse(BaseModel):
    cleared_ips: int
    message: str


# ==================== 1. 总览 ====================


@router.get("/stats", summary="风控总览统计")
async def get_risk_stats() -> Dict[str, Any]:
    """返回风控系统当前状态总览"""
    service = get_risk_control_service()
    captcha = get_captcha_stats()
    return {
        "risk_control": service.get_stats(),
        "captcha": captcha.get_snapshot(),
        "blocked_ips_detail": service.list_blocked_ips(),
    }


# ==================== 2. 封禁名单 ====================


@router.get("/blocked-ips", summary="列出所有被封禁的 IP")
async def list_blocked_ips() -> Dict[str, Any]:
    service = get_risk_control_service()
    items = service.list_blocked_ips()
    return {
        "total": len(items),
        "items": items,
    }


@router.post(
    "/blocked-ips",
    response_model=BlockIPResponse,
    summary="手动封禁一个 IP",
)
async def block_ip(req: BlockIPRequest) -> BlockIPResponse:
    service = get_risk_control_service()
    result = service.block_ip(
        ip=req.ip, duration_seconds=req.duration_seconds, reason=req.reason
    )
    return BlockIPResponse(**result)


@router.delete(
    "/blocked-ips/{ip}",
    summary="解封一个 IP",
)
async def unblock_ip(
    ip: str = Path(..., description="要解封的 IP"),
) -> Dict[str, Any]:
    service = get_risk_control_service()
    existed = service.unblock_ip(ip)
    if not existed:
        raise HTTPException(status_code=404, detail=f"IP {ip} 未在封禁名单中")
    return {"ip": ip, "unblocked": True}


# ==================== 3. 高风险 IP ====================


@router.get("/scores", summary="Top 高风险 IP 列表")
async def list_top_risks(
    limit: int = Query(20, ge=1, le=200, description="最多返回多少条"),
) -> Dict[str, Any]:
    service = get_risk_control_service()
    items = service.list_top_risks(limit=limit)
    return {"total": len(items), "items": items}


@router.get("/ip/{ip}", summary="查询指定 IP 完整状态")
async def get_ip_detail(
    ip: str = Path(..., description="要查询的 IP"),
) -> Dict[str, Any]:
    service = get_risk_control_service()
    return service.get_ip_detail(ip)


# ==================== 4. 重置 ====================


@router.post(
    "/reset",
    response_model=ResetResponse,
    summary="重置全部风控状态（紧急操作）",
)
async def reset_all() -> ResetResponse:
    service = get_risk_control_service()
    count = service.reset_all()
    return ResetResponse(
        cleared_ips=count, message=f"已清除 {count} 个 IP 的风控状态"
    )


# ==================== 5. 规则 ====================


@router.get("/rules/endpoints", summary="端点风控规则快照")
async def get_endpoint_rules() -> Dict[str, Any]:
    service = get_risk_control_service()
    return {
        "total": len(service.get_endpoint_rule_snapshot()),
        "items": service.get_endpoint_rule_snapshot(),
    }


@router.get("/rules/anomalies", summary="异常模式规则快照")
async def get_anomaly_rules() -> Dict[str, Any]:
    service = get_risk_control_service()
    return {
        "total": len(service.get_anomaly_rule_snapshot()),
        "items": service.get_anomaly_rule_snapshot(),
    }


# ==================== 6. CAPTCHA 统计 ====================


@router.get("/captcha/stats", summary="CAPTCHA 验证统计")
async def get_captcha_stats_endpoint() -> Dict[str, Any]:
    stats = get_captcha_stats()
    snap = stats.get_snapshot()
    return {
        **snap,
        "recent_events": stats.get_recent_events(limit=20),
    }


@router.post(
    "/captcha/reset-stats", summary="重置 CAPTCHA 统计（管理操作）"
)
async def reset_captcha_stats() -> Dict[str, Any]:
    get_captcha_stats().reset()
    return {"reset": True, "message": "CAPTCHA 统计已重置"}


# ==================== 健康检查（无需 admin token）====================


@router.get("/health", summary="管理 API 健康检查")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "module": "admin.risk_control",
        "service_alive": True,
    }


__all__ = ["router"]
