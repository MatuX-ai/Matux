"""
支付系统API路由
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from models.payment import OrderStatus, PaymentMethod, PaymentStatus
from models.user import User
from routes.auth_routes import get_current_user
from services.payment_service import PaymentService
from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["支付系统"])

# 支付服务实例
payment_service = PaymentService()


@router.post("/checkout")
async def checkout(
    items: List[dict],
    payment_method: PaymentMethod,
    shipping_address: Optional[dict] = None,
    note: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    结账支付

    Args:
        items: 购物车项目列表
        payment_method: 支付方式
        shipping_address: 收货地址
        note: 用户备注
        current_user: 当前用户
        db: 数据库会话
    """
    try:
        # 验证购物车项目
        if not items:
            raise HTTPException(status_code=400, detail="购物车不能为空")

        # 验证支付方式
        if payment_method not in PaymentMethod:
            raise HTTPException(status_code=400, detail="不支持的支付方式")

        # 创建订单
        order = await payment_service.create_order(
            user_id=current_user.id,
            cart_items=items,
            shipping_address=shipping_address,
            note=note,
            db=db,
        )

        # 处理支付
        payment = await payment_service.process_payment(
            order_id=order.order_id,
            payment_method=payment_method,
            user_id=current_user.id,
            db=db,
        )

        return {
            "order_id": order.order_id,
            "payment_id": payment.payment_id,
            "amount": payment.amount,
            "status": payment.status.value,
            "payment_method": payment.payment_method.value,
            "transaction_id": payment.transaction_id,
            "message": (
                "支付成功" if payment.status == PaymentStatus.SUCCESS else "支付失败"
            ),
        }

    except ValueError as e:
        logger.error(f"结账失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"结账异常: {e}")
        raise HTTPException(status_code=500, detail="支付处理失败")


@router.get("/orders/{order_id}")
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取订单详情

    Args:
        order_id: 订单ID
        current_user: 当前用户
        db: 数据库会话
    """
    try:
        order = await payment_service.get_order(order_id, current_user.id, db)

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        return {
            "order_id": order.order_id,
            "items": order.items,
            "total_amount": order.total_amount,
            "paid_amount": order.paid_amount,
            "status": order.status.value,
            "payment_status": order.payment_status.value,
            "shipping_address": order.shipping_address,
            "note": order.note,
            "created_at": order.created_at.isoformat(),
            "updated_at": order.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取订单详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取订单详情失败")


@router.get("/orders")
async def get_user_orders(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户订单列表

    Args:
        limit: 每页数量
        offset: 偏移量
        current_user: 当前用户
        db: 数据库会话
    """
    try:
        orders = await payment_service.get_user_orders(
            user_id=current_user.id, db=db, limit=limit, offset=offset
        )

        order_list = []
        for order in orders:
            order_list.append(
                {
                    "order_id": order.order_id,
                    "total_amount": order.total_amount,
                    "paid_amount": order.paid_amount,
                    "status": order.status.value,
                    "payment_status": order.payment_status.value,
                    "item_count": len(order.items),
                    "created_at": order.created_at.isoformat(),
                }
            )

        return {
            "orders": order_list,
            "total": len(order_list),
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"获取订单列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取订单列表失败")


@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    取消订单

    Args:
        order_id: 订单ID
        current_user: 当前用户
        db: 数据库会话
    """
    try:
        success = await payment_service.cancel_order(order_id, current_user.id, db)

        if not success:
            raise HTTPException(status_code=404, detail="订单不存在或无法取消")

        return {"message": "订单取消成功", "order_id": order_id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消订单失败: {e}")
        raise HTTPException(status_code=500, detail="取消订单失败")


@router.get("/statistics")
async def get_payment_statistics(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """
    获取支付统计信息

    Args:
        current_user: 当前用户
        db: 数据库会话
    """
    try:
        stats = await payment_service.get_payment_statistics(current_user.id, db)

        return {"user_id": current_user.id, "statistics": stats}

    except Exception as e:
        logger.error(f"获取支付统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取支付统计失败")


@router.post("/simulate-payment")
async def simulate_payment(
    order_id: str,
    payment_method: PaymentMethod,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    模拟支付（用于测试）

    Args:
        order_id: 订单ID
        payment_method: 支付方式
        current_user: 当前用户
        db: 数据库会话
    """
    try:
        # 验证订单存在且属于当前用户
        order = await payment_service.get_order(order_id, current_user.id, db)

        if not order:
            raise HTTPException(status_code=404, detail="订单不存在")

        if order.status != OrderStatus.PENDING_PAYMENT:
            raise HTTPException(status_code=400, detail="订单状态不允许支付")

        # 处理支付
        payment = await payment_service.process_payment(
            order_id=order_id,
            payment_method=payment_method,
            user_id=current_user.id,
            db=db,
        )

        return {
            "payment_id": payment.payment_id,
            "order_id": order_id,
            "amount": payment.amount,
            "status": payment.status.value,
            "payment_method": payment.payment_method.value,
            "transaction_id": payment.transaction_id,
            "message": (
                "模拟支付成功"
                if payment.status == PaymentStatus.SUCCESS
                else "模拟支付失败"
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"模拟支付失败: {e}")
        raise HTTPException(status_code=500, detail="模拟支付处理失败")


@router.get("/payment-methods")
async def get_payment_methods():
    """
    获取支持的支付方式
    """
    return {
        "payment_methods": [
            {
                "method": method.value,
                "name": method.name.replace("_", " ").title(),
                "description": f"{method.name.replace('_', ' ').title()}支付",
            }
            for method in PaymentMethod
        ]
    }


@router.get("/payment-status/{payment_id}")
async def get_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取支付状态

    Args:
        payment_id: 支付ID
        current_user: 当前用户
        db: 数据库会话
    """
    try:
        from sqlalchemy import select

        from models.payment import Payment

        result = await db.execute(
            select(Payment).where(
                Payment.payment_id == payment_id, Payment.user_id == current_user.id
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise HTTPException(status_code=404, detail="支付记录不存在")

        return {
            "payment_id": payment.payment_id,
            "order_id": payment.order_id,
            "amount": payment.amount,
            "status": payment.status.value,
            "payment_method": payment.payment_method.value,
            "transaction_id": payment.transaction_id,
            "created_at": payment.created_at.isoformat(),
            "completed_at": (
                payment.completed_at.isoformat() if payment.completed_at else None
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取支付状态失败: {e}")
        raise HTTPException(status_code=500, detail="获取支付状态失败")
