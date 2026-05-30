"""
Token 管理 API 路由
提供 Token 套餐、余额、使用记录等管理功能
"""

import logging
from typing import Optional, cast

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from utils.database import get_sync_db
from models.user import User
from models.token_schemas import (
    CostEstimateRequest,
    CostEstimateResponse,
    PurchaseTokenRequest,
    PurchaseTokenResponse,
    TokenPackageResponse,
    TokenStatsResponse,
    TokenUsageListResponse,
    TokenUsageRecordResponse,
    UserBalanceResponse,
)
from utils.dependencies import get_current_user_sync
from services.token_service import TokenService

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1/token", tags=["Token 管理"])


def get_token_service(db: Session = Depends(get_sync_db)) -> TokenService:
    """获取 Token 服务实例"""
    return TokenService(db)


@router.get("/packages", response_model=list[TokenPackageResponse])
async def get_token_packages(
    db: Session = Depends(get_sync_db),
    token_service: TokenService = Depends(get_token_service)
):
    """
    获取所有可用的 Token 套餐列表

    Returns:
        List[TokenPackageResponse]: 套餐列表
    """
    try:
        packages = token_service.get_available_packages()
        return packages
    except Exception as e:
        logger.error(f"获取套餐列表失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取套餐列表失败：{str(e)}")


@router.post("/purchase", response_model=PurchaseTokenResponse)
async def purchase_token_package(
    request: PurchaseTokenRequest,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
    token_service: TokenService = Depends(get_token_service)
):
    """
    购买 Token 套餐

    Args:
        request: 购买请求（套餐 ID、支付方式）
        current_user: 当前用户
        db: 数据库会话
        token_service: Token 服务

    Returns:
        PurchaseTokenResponse: 购买结果
    """
    try:
        logger.info(f"用户 {current_user.id} 请求购买套餐 {request.package_id}")

        # 验证套餐是否存在
        package = token_service.get_package_by_id(request.package_id)
        if not package:
            raise HTTPException(
                status_code=404,
                detail=f"套餐不存在或已停售：{request.package_id}"
            )

        # 生成订单号
        import datetime
        order_no = f"ORDER_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{current_user.id}"

        # 购买套餐
        recharge_record = token_service.purchase_token_package(
            user_id=cast(int, current_user.id),
            package_id=request.package_id,
            payment_method=request.payment_method,
            order_no=order_no
        )

        return PurchaseTokenResponse(
            success=True,
            message="购买成功",
            order_no=cast(str, recharge_record.order_no),
            token_amount=cast(int, recharge_record.token_amount),
            payment_amount=cast(float, recharge_record.payment_amount),
            payment_status=cast(str, recharge_record.payment_status)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"购买套餐失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"购买失败：{str(e)}")


@router.get("/balance", response_model=UserBalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
    token_service: TokenService = Depends(get_token_service)
):
    """
    查询用户 Token 余额

    Args:
        current_user: 当前用户
        db: 数据库会话
        token_service: Token 服务

    Returns:
        UserBalanceResponse: 余额信息
    """
    try:
        balance = token_service.get_or_create_user_balance(cast(int, current_user.id))

        return UserBalanceResponse(
            user_id=cast(int, current_user.id),
            total_tokens=cast(int, balance.total_tokens),
            used_tokens=cast(int, balance.used_tokens),
            remaining_tokens=cast(int, balance.remaining_tokens),
            monthly_bonus_tokens=balance.monthly_bonus_tokens,
            last_bonus_date=balance.last_bonus_date
        )

    except Exception as e:
        logger.error(f"查询余额失败：{e}")
        raise HTTPException(status_code=500, detail=f"查询余额失败：{str(e)}")


@router.get("/usage", response_model=TokenUsageListResponse)
async def get_usage_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    usage_type: Optional[str] = Query(None, description="使用类型筛选"),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
    token_service: TokenService = Depends(get_token_service)
):
    """
    获取用户 Token 使用记录

    Args:
        page: 页码
        page_size: 每页数量
        usage_type: 使用类型筛选
        current_user: 当前用户
        db: 数据库会话
        token_service: Token 服务

    Returns:
        TokenUsageListResponse: 使用记录列表
    """
    try:
        from sqlalchemy import desc
        from models.user_license import TokenUsageRecord

        # 查询总数
        query = db.query(TokenUsageRecord).filter(
            TokenUsageRecord.user_balance_id == current_user.id
        )

        if usage_type:
            query = query.filter(TokenUsageRecord.usage_type == usage_type)

        total = query.count()

        # 分页查询
        records = query.order_by(
            desc(TokenUsageRecord.created_at)
        ).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        # 转换为响应模型
        records_response = [
            TokenUsageRecordResponse(
                id=cast(int, r.id),
                token_amount=cast(int, r.token_amount),
                usage_type=cast(str, r.usage_type),
                usage_description=cast(str, r.usage_description) if r.usage_description is not None else None,
                resource_id=cast(int, r.resource_id) if r.resource_id is not None else None,
                resource_type=cast(str, r.resource_type) if r.resource_type is not None else None,
                created_at=r.created_at  # type: ignore[arg-type]
            )
            for r in records
        ]

        return TokenUsageListResponse(
            total=total,
            page=page,
            page_size=page_size,
            records=records_response
        )

    except Exception as e:
        logger.error(f"获取使用记录失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取使用记录失败：{str(e)}")


@router.get("/stats", response_model=TokenStatsResponse)
async def get_token_stats(
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
    token_service: TokenService = Depends(get_token_service)
):
    """
    获取用户 Token 统计信息

    Args:
        current_user: 当前用户
        db: 数据库会话
        token_service: Token 服务

    Returns:
        TokenStatsResponse: 统计信息
    """
    try:
        stats = token_service.get_token_stats(cast(int, current_user.id))

        return TokenStatsResponse(
            total_tokens=stats["total_tokens"],
            used_tokens=stats["used_tokens"],
            remaining_tokens=stats["remaining_tokens"],
            monthly_bonus=stats["monthly_bonus"],
            last_bonus_date=stats["last_bonus_date"],
            month_usage=stats["month_usage"],
            total_spent=stats["total_spent"],
            recent_recharges=stats["recent_recharges"],
            recent_usages=stats["recent_usages"]
        )

    except Exception as e:
        logger.error(f"获取统计信息失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败：{str(e)}")


@router.post("/estimate", response_model=CostEstimateResponse)
async def estimate_cost(
    request: CostEstimateRequest,
    db: Session = Depends(get_sync_db),
    token_service: TokenService = Depends(get_token_service)
):
    """
    预估 AI 功能的 Token 消耗

    Args:
        request: 成本预估请求
        db: 数据库会话
        token_service: Token 服务

    Returns:
        CostEstimateResponse: 预估结果
    """
    try:
        feature_type = request.feature_type.lower()
        params = request.params

        if feature_type == "ai_teacher":
            # AI 对话：按消息长度估算
            message_length = params.get("message_length", 100)
            estimated_tokens = token_service.estimate_ai_chat_cost(
                message_length)
            description = f"AI 对话预估：约 {estimated_tokens} tokens (基于 {message_length} 字符)"

        elif feature_type == "course_generation":
            # 课程生成：按复杂度估算
            complexity = params.get("complexity", "medium")
            estimated_tokens = token_service.estimate_course_cost(complexity)
            description = f"课程生成预估：{estimated_tokens} tokens (复杂度：{complexity})"

        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的功能类型：{feature_type}"
            )

        return CostEstimateResponse(
            success=True,
            feature_type=feature_type,
            estimated_tokens=estimated_tokens,
            description=description
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"成本预估失败：{e}")
        raise HTTPException(status_code=500, detail=f"成本预估失败：{str(e)}")


@router.get("/package/{package_id}", response_model=TokenPackageResponse)
async def get_package_by_id(
    package_id: int,
    db: Session = Depends(get_sync_db),
    token_service: TokenService = Depends(get_token_service)
):
    """
    根据 ID 获取 Token 套餐详情

    Args:
        package_id: 套餐 ID
        db: 数据库会话
        token_service: Token 服务

    Returns:
        TokenPackageResponse: 套餐详情
    """
    try:
        package = token_service.get_package_by_id(package_id)

        if not package:
            raise HTTPException(
                status_code=404,
                detail=f"套餐不存在：{package_id}"
            )

        return package

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取套餐详情失败：{e}")
        raise HTTPException(status_code=500, detail=f"获取套餐详情失败：{str(e)}")
