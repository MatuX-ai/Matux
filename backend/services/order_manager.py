"""
订单状态管理和处理服务
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.payment import Order, OrderStatus, Payment, PaymentStatus
from services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class OrderManager:
    """订单管理器"""

    def __init__(self):
        self.notification_service = NotificationService()

    async def process_pending_payments(self, db: AsyncSession):
        """处理待支付订单（自动取消超时订单）"""
        try:
            # 查找超过30分钟仍未支付的订单
            cutoff_time = datetime.utcnow() - timedelta(minutes=30)

            result = await db.execute(
                select(Order).where(
                    and_(
                        Order.status == OrderStatus.PENDING_PAYMENT,
                        Order.created_at < cutoff_time,
                    )
                )
            )
            pending_orders = result.scalars().all()

            cancelled_count = 0
            for order in pending_orders:
                await self.cancel_order_due_to_timeout(order.order_id, db)
                cancelled_count += 1

            if cancelled_count > 0:
                logger.info(f"自动取消了 {cancelled_count} 个超时未支付订单")

        except Exception as e:
            logger.error(f"处理待支付订单失败: {e}")

    async def cancel_order_due_to_timeout(self, order_id: str, db: AsyncSession):
        """因超时取消订单"""
        try:
            result = await db.execute(select(Order).where(Order.order_id == order_id))
            order = result.scalar_one_or_none()

            if not order:
                return

            # 更新订单状态
            order.status = OrderStatus.CANCELLED
            order.payment_status = PaymentStatus.CANCELLED
            order.cancelled_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()

            # 发送通知
            await self.notification_service.send_order_cancelled_notification(
                user_id=order.user_id,
                order_id=order.order_id,
                reason="支付超时自动取消",
            )

            await db.commit()
            logger.info(f"订单 {order_id} 因超时被自动取消")

        except Exception as e:
            await db.rollback()
            logger.error(f"取消超时订单失败: {e}")

    async def confirm_shipment(
        self, order_id: str, tracking_number: str, db: AsyncSession
    ):
        """确认发货"""
        try:
            result = await db.execute(select(Order).where(Order.order_id == order_id))
            order = result.scalar_one_or_none()

            if not order:
                raise ValueError("订单不存在")

            if order.status != OrderStatus.PENDING_SHIPMENT:
                raise ValueError("订单状态不允许发货")

            # 更新订单状态
            order.status = OrderStatus.SHIPPED
            order.tracking_number = tracking_number
            order.shipped_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()

            # 发送发货通知
            await self.notification_service.send_shipment_notification(
                user_id=order.user_id,
                order_id=order.order_id,
                tracking_number=tracking_number,
            )

            await db.commit()
            logger.info(f"订单 {order_id} 发货确认完成，运单号: {tracking_number}")

        except Exception as e:
            await db.rollback()
            logger.error(f"确认发货失败: {e}")
            raise

    async def complete_order(self, order_id: str, db: AsyncSession):
        """完成订单"""
        try:
            result = await db.execute(select(Order).where(Order.order_id == order_id))
            order = result.scalar_one_or_none()

            if not order:
                raise ValueError("订单不存在")

            if order.status != OrderStatus.SHIPPED:
                raise ValueError("只有已发货订单才能完成")

            # 更新订单状态
            order.status = OrderStatus.COMPLETED
            order.completed_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()

            # 发送订单完成通知
            await self.notification_service.send_order_completed_notification(
                user_id=order.user_id, order_id=order.order_id
            )

            await db.commit()
            logger.info(f"订单 {order_id} 已完成")

        except Exception as e:
            await db.rollback()
            logger.error(f"完成订单失败: {e}")
            raise

    async def process_refund(
        self, payment_id: str, refund_amount: float, reason: str, db: AsyncSession
    ):
        """处理退款"""
        try:
            result = await db.execute(
                select(Payment).where(Payment.payment_id == payment_id)
            )
            payment = result.scalar_one_or_none()

            if not payment:
                raise ValueError("支付记录不存在")

            if payment.status != PaymentStatus.SUCCESS:
                raise ValueError("只有成功的支付才能退款")

            # 更新支付状态
            payment.status = PaymentStatus.REFUNDING
            payment.refund_amount = refund_amount
            payment.refund_reason = reason
            payment.refund_requested_at = datetime.utcnow()
            payment.updated_at = datetime.utcnow()

            # 更新关联订单状态
            result = await db.execute(
                select(Order).where(Order.order_id == payment.order_id)
            )
            order = result.scalar_one_or_none()

            if order:
                order.status = OrderStatus.CANCELLED
                order.payment_status = PaymentStatus.REFUNDING
                order.cancelled_at = datetime.utcnow()
                order.updated_at = datetime.utcnow()

            # 发送退款申请通知
            await self.notification_service.send_refund_notification(
                user_id=payment.user_id,
                order_id=payment.order_id,
                amount=refund_amount,
                reason=reason,
            )

            await db.commit()
            logger.info(f"退款申请已提交: 支付ID {payment_id}, 金额 {refund_amount}")

        except Exception as e:
            await db.rollback()
            logger.error(f"处理退款失败: {e}")
            raise

    async def get_order_analytics(
        self, user_id: str, db: AsyncSession, days: int = 30
    ) -> Dict[str, Any]:
        """获取订单分析数据"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # 获取订单统计
            total_orders_result = await db.execute(
                select(func.count())
                .select_from(Order)
                .where(and_(Order.user_id == user_id, Order.created_at >= cutoff_date))
            )
            total_orders = total_orders_result.scalar()

            # 获取支付成功订单
            successful_orders_result = await db.execute(
                select(func.count())
                .select_from(Order)
                .where(
                    and_(
                        Order.user_id == user_id,
                        Order.payment_status == PaymentStatus.SUCCESS,
                        Order.created_at >= cutoff_date,
                    )
                )
            )
            successful_orders = successful_orders_result.scalar()

            # 获取总消费金额
            total_amount_result = await db.execute(
                select(func.sum(Order.total_amount))
                .select_from(Order)
                .where(
                    and_(
                        Order.user_id == user_id,
                        Order.payment_status == PaymentStatus.SUCCESS,
                        Order.created_at >= cutoff_date,
                    )
                )
            )
            total_amount = total_amount_result.scalar() or 0

            # 按状态统计
            status_stats_result = await db.execute(
                select(Order.status, func.count())
                .select_from(Order)
                .where(and_(Order.user_id == user_id, Order.created_at >= cutoff_date))
                .group_by(Order.status)
            )

            status_stats = {}
            for status, count in status_stats_result:
                status_stats[status.value] = count

            # 按日期统计（近7天）
            daily_stats_result = await db.execute(
                select(
                    func.date(Order.created_at).label("date"),
                    func.count().label("count"),
                    func.sum(Order.total_amount).label("amount"),
                )
                .select_from(Order)
                .where(
                    and_(
                        Order.user_id == user_id,
                        Order.created_at >= datetime.utcnow() - timedelta(days=7),
                    )
                )
                .group_by(func.date(Order.created_at))
                .order_by(func.date(Order.created_at))
            )

            daily_stats = []
            for row in daily_stats_result:
                daily_stats.append(
                    {
                        "date": row.date.isoformat(),
                        "order_count": row.count,
                        "total_amount": float(row.amount or 0),
                    }
                )

            return {
                "period_days": days,
                "total_orders": total_orders,
                "successful_orders": successful_orders,
                "success_rate": round(
                    successful_orders / max(total_orders, 1) * 100, 2
                ),
                "total_amount": float(total_amount),
                "status_distribution": status_stats,
                "daily_statistics": daily_stats,
            }

        except Exception as e:
            logger.error(f"获取订单分析数据失败: {e}")
            raise


# 导入必要的函数
from sqlalchemy import func
