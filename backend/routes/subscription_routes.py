"""
订阅系统 API 路由
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from models.payment import PaymentMethod
from models.subscription import (
    BillingCycle,
    SubscriptionPayment,
    SubscriptionPlan,
    SubscriptionPlanType,
    SubscriptionStatus,
    UserSubscription,
)
from models.user import User
from routes.auth_routes import get_current_user
from services.subscription_service import subscription_service
from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subscriptions", tags=["订阅系统"])


# Pydantic schemas for request/response

class SubscriptionPlanCreate(BaseModel):
    """创建订阅计划请求模型"""
    name: str
    description: str = ""
    plan_type: SubscriptionPlanType
    price: float
    billing_cycle: BillingCycle
    currency: str = "CNY"
    features: Optional[dict] = None
    limits: Optional[dict] = None
    is_popular: bool = False
    is_active: bool = True
    trial_period_days: int = 0
    setup_fee: float = 0.0


class SubscriptionPlanResponse(BaseModel):
    """订阅计划响应模型"""
    id: int
    plan_id: str
    name: str
    description: Optional[str]
    plan_type: SubscriptionPlanType
    price: float
    billing_cycle: BillingCycle
    currency: Optional[str]
    features: Optional[dict]
    limits: Optional[dict]
    is_popular: bool
    is_active: bool
    trial_period_days: int
    setup_fee: float

    class Config:
        from_attributes = True


class UserSubscriptionResponse(BaseModel):
    """用户订阅响应模型"""
    id: int
    subscription_id: str
    user_id: str
    plan_id: str
    status: SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime]
    next_billing_date: Optional[datetime]
    cancelled_at: Optional[datetime]
    trial_start_date: Optional[datetime]
    trial_end_date: Optional[datetime]
    grace_period_end: Optional[datetime]
    auto_renew: bool
    renewal_count: int
    has_trial: bool
    trial_used: bool
    upgrade_history: Optional[dict]
    downgrade_history: Optional[dict]
    price_snapshot: Optional[float]
    currency_snapshot: Optional[str]
    custom_config: Optional[dict]
    custom_metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionPaymentResponse(BaseModel):
    """订阅支付响应模型"""
    id: int
    payment_id: str
    subscription_id: str
    amount: float
    currency: Optional[str]
    payment_method: Optional[str]
    billing_cycle_start: datetime
    billing_cycle_end: datetime
    status: str
    transaction_id: Optional[str]
    payment_proof: Optional[str]
    gateway_response: Optional[dict]
    notification_received: bool
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.post("/plans", response_model=SubscriptionPlanResponse)
async def create_subscription_plan(
    name: str = Body(..., description="计划名称"),
    description: str = Body("", description="计划描述"),
    plan_type: SubscriptionPlanType = Body(..., description="计划类型"),
    price: float = Body(..., gt=0, description="价格"),
    billing_cycle: BillingCycle = Body(..., description="计费周期"),
    features: List[str] = Body(default=[], description="功能列表"),
    limits: dict = Body(default={}, description="限制配置"),
    trial_period_days: int = Body(default=0, ge=0, description="试用期天数"),
    setup_fee: float = Body(default=0.0, ge=0, description="开通费用"),
    currency: str = Body(default="CNY", description="货币单位"),
    is_popular: bool = Body(default=False, description="是否推荐"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建订阅计划（管理员权限）
    """
    try:
        # 验证管理员权限（简化实现，实际应用中需要更严格的权限控制）
        if not hasattr(current_user, "is_admin") or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        plan = await subscription_service.create_subscription_plan(
            name=name,
            description=description,
            plan_type=plan_type,
            price=price,
            billing_cycle=billing_cycle,
            features=features,
            limits=limits,
            trial_period_days=trial_period_days,
            setup_fee=setup_fee,
            currency=currency,
            is_popular=is_popular,
            db=db,
        )

        return plan

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建订阅计划失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(
    is_active: Optional[bool] = Query(True, description="是否只返回激活的计划"),
    plan_type: Optional[SubscriptionPlanType] = Query(None, description="计划类型筛选"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取订阅计划列表
    """
    try:
        plans = await subscription_service.get_subscription_plans(
            is_active=is_active, plan_type=plan_type, db=db
        )
        return plans
    except Exception as e:
        logger.error(f"获取订阅计划失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("", response_model=UserSubscriptionResponse)
async def create_subscription(
    plan_id: str = Body(..., description="订阅计划ID"),
    payment_method: PaymentMethod = Body(..., description="支付方式"),
    auto_renew: bool = Body(default=True, description="是否自动续费"),
    custom_config: dict = Body(default={}, description="自定义配置"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    用户订阅
    """
    try:
        subscription = await subscription_service.subscribe_user(
            user_id=current_user.id,
            plan_id=plan_id,
            payment_method=payment_method,
            auto_renew=auto_renew,
            custom_config=custom_config,
            db=db,
        )

        return subscription

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"用户订阅失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("", response_model=List[UserSubscriptionResponse])
async def get_user_subscriptions(
    status: Optional[SubscriptionStatus] = Query(None, description="订阅状态筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户的订阅列表
    """
    try:
        subscriptions = await subscription_service.get_user_subscriptions(
            user_id=current_user.id, status=status, db=db
        )
        return subscriptions
    except Exception as e:
        logger.error(f"获取用户订阅失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/{subscription_id}", response_model=UserSubscriptionResponse)
async def get_subscription_detail(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取订阅详情
    """
    try:
        from sqlalchemy import select

        query = select(UserSubscription).where(
            UserSubscription.subscription_id == subscription_id
        )

        # 非管理员只能查看自己的订阅
        if not (hasattr(current_user, "is_admin") and current_user.is_admin):
            query = query.where(UserSubscription.user_id == current_user.id)

        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(status_code=404, detail="订阅不存在")

        return subscription

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订阅详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    取消订阅
    """
    try:
        # 非管理员只能取消自己的订阅
        user_id = current_user.id
        if not (hasattr(current_user, "is_admin") and current_user.is_admin):
            user_id = current_user.id
        else:
            user_id = None  # 管理员可以取消任意订阅

        subscription = await subscription_service.cancel_subscription(
            subscription_id=subscription_id, user_id=user_id, db=db
        )

        return {
            "message": "订阅已成功取消",
            "subscription_id": subscription.subscription_id,
            "cancelled_at": (
                subscription.cancelled_at.isoformat()
                if subscription.cancelled_at
                else None
            ),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"取消订阅失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/{subscription_id}/payments", response_model=List[SubscriptionPaymentResponse])
async def get_subscription_payments(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取订阅的支付记录
    """
    try:
        from sqlalchemy import select

        # 验证订阅所有权
        subscription_query = select(UserSubscription).where(
            UserSubscription.subscription_id == subscription_id
        )

        if not (hasattr(current_user, "is_admin") and current_user.is_admin):
            subscription_query = subscription_query.where(
                UserSubscription.user_id == current_user.id
            )

        subscription_result = await db.execute(subscription_query)
        subscription = subscription_result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(status_code=404, detail="订阅不存在或无权访问")

        # 获取支付记录
        payments_query = (
            select(SubscriptionPayment)
            .where(SubscriptionPayment.subscription_id == subscription_id)
            .order_by(SubscriptionPayment.created_at.desc())
        )

        payments_result = await db.execute(payments_query)
        payments = payments_result.scalars().all()

        return list(payments)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订阅支付记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.post("/{subscription_id}/reactivate")
async def reactivate_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    重新激活订阅（仅限管理员）
    """
    try:
        # 验证管理员权限
        if not (hasattr(current_user, "is_admin") and current_user.is_admin):
            raise HTTPException(status_code=403, detail="需要管理员权限")

        from sqlalchemy import select

        # 获取订阅
        query = select(UserSubscription).where(
            UserSubscription.subscription_id == subscription_id
        )
        result = await db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(status_code=404, detail="订阅不存在")

        if subscription.status != SubscriptionStatus.CANCELLED:
            raise HTTPException(status_code=400, detail="只能重新激活已取消的订阅")

        # 重新激活订阅
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.cancelled_at = None
        subscription.auto_renew = True

        await db.commit()
        await db.refresh(subscription)

        return {
            "message": "订阅已成功重新激活",
            "subscription_id": subscription.subscription_id,
            "status": subscription.status.value,
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"重新激活订阅失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/user/{user_id}/subscriptions", response_model=List[UserSubscriptionResponse])
async def get_user_subscriptions_admin(
    user_id: str,
    status: Optional[SubscriptionStatus] = Query(None, description="订阅状态筛选"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    管理员获取指定用户的订阅列表
    """
    try:
        # 验证管理员权限
        if not (hasattr(current_user, "is_admin") and current_user.is_admin):
            raise HTTPException(status_code=403, detail="需要管理员权限")

        subscriptions = await subscription_service.get_user_subscriptions(
            user_id=user_id, status=status, db=db
        )

        return subscriptions

    except Exception as e:
        logger.error(f"获取用户订阅失败: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")


# 导出路由器
__all__ = ["router"]
