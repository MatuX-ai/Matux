"""
支付服务核心实现
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.payment import Order, OrderStatus, Payment, PaymentMethod, PaymentStatus
from models.user import User
from models.user_license import TokenPackage, TokenRechargeRecord, UserTokenBalance

logger = logging.getLogger(__name__)


class PaymentService:
    """支付服务类"""

    def __init__(self):
        self.payment_gateways = {
            PaymentMethod.WECHAT_PAY: self._process_wechat_pay,
            PaymentMethod.ALIPAY: self._process_alipay,
            PaymentMethod.BANK_CARD: self._process_bank_card,
            PaymentMethod.BALANCE: self._process_balance_payment,
        }

    async def create_token_order(
        self,
        user_id: str,
        package_id: int,
        payment_method: PaymentMethod,
        db: AsyncSession = None,
    ) -> Order:
        """创建 Token 套餐购买订单
        
        Args:
            user_id: 用户 ID
            package_id: Token 套餐 ID
            payment_method: 支付方式
            db: 数据库会话
            
        Returns:
            Order: 订单对象
        """
        try:
            # 获取套餐信息
            from sqlalchemy import select
            result = await db.execute(
                select(TokenPackage).where(TokenPackage.id == package_id)
            )
            package = result.scalar_one_or_none()
            
            if not package:
                raise ValueError(f"套餐 {package_id} 不存在")
            
            if not package.is_active:
                raise ValueError(f"套餐 {package.name} 已下架")
            
            # 生成订单 ID
            order_id = f"TKN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"
            
            # 创建订单，使用 metadata 存储 Token 套餐信息
            order = Order(
                order_id=order_id,
                user_id=user_id,
                items=[{
                    "type": "token_package",
                    "package_id": package_id,
                    "package_name": package.name,
                    "token_count": package.token_count,
                    "price": package.price,
                    "quantity": 1,
                }],
                total_amount=package.price,
                metadata={
                    "token_package_id": package_id,
                    "token_count": package.token_count,
                    "package_type": package.package_type.value if package.package_type else None,
                },
                note=f"购买 Token 套餐：{package.name}",
            )
            
            db.add(order)
            await db.commit()
            await db.refresh(order)
            
            logger.info(
                f"Token 订单创建成功：{order_id}, "
                f"套餐：{package.name}, "
                f"Token 数量：{package.token_count}, "
                f"金额：{package.price}元"
            )
            return order
            
        except Exception as e:
            await db.rollback()
            logger.error(f"创建 Token 订单失败：{e}")
            raise
    
    async def confirm_token_payment(
        self,
        order_id: str,
        payment_success: bool = True,
        db: AsyncSession = None,
    ) -> bool:
        """确认 Token 订单支付并发放 Token
        
        Args:
            order_id: 订单 ID
            payment_success: 是否支付成功
            db: 数据库会话
            
        Returns:
            bool: 是否成功发放 Token
        """
        try:
            from sqlalchemy import select
            # 获取订单信息
            result = await db.execute(select(Order).where(Order.order_id == order_id))
            order = result.scalar_one_or_none()
            
            if not order:
                raise ValueError(f"订单不存在：{order_id}")
            
            if not order.metadata or order.metadata.get("token_package_id") is None:
                raise ValueError("该订单不是 Token 订单")
            
            if not payment_success:
                # 支付失败，更新订单状态
                order.status = OrderStatus.CANCELLED
                order.payment_status = PaymentStatus.FAILED
                await db.commit()
                logger.warning(f"Token 订单支付失败：{order_id}")
                return False
            
            # 导入 Token 服务
            from services.token_service import TokenService
            token_service = TokenService(db)
            
            # 获取套餐信息
            package_result = await db.execute(
                select(TokenPackage).where(TokenPackage.id == order.metadata["token_package_id"])
            )
            package = package_result.scalar_one_or_none()
            
            if not package:
                raise ValueError("套餐不存在")
            
            # 发放 Token
            balance = token_service.get_or_create_user_balance(order.user_id)
            balance.total_tokens += package.token_count
            balance.remaining_tokens += package.token_count
            
            # 创建充值记录
            recharge_record = TokenRechargeRecord(
                user_balance_id=balance.id,
                package_id=package.id,
                token_amount=package.token_count,
                payment_amount=package.price,
                payment_method="order_payment",
                payment_status="success",
                order_no=order.order_id,
                payment_time=datetime.utcnow(),
            )
            
            db.add(recharge_record)
            
            # 更新订单状态
            order.status = OrderStatus.COMPLETED
            order.payment_status = PaymentStatus.SUCCESS
            order.paid_amount = order.total_amount
            
            await db.commit()
            
            logger.info(
                f"Token 订单支付确认成功：{order_id}, "
                f"用户 {order.user_id} 获得 {package.token_count} Token"
            )
            return True
            
        except Exception as e:
            await db.rollback()
            logger.error(f"确认 Token 支付失败：{e}")
            raise
    
    async def create_order(
        self,
        user_id: str,
        cart_items: List[Dict[str, Any]],
        shipping_address: Optional[Dict[str, Any]] = None,
        note: Optional[str] = None,
        db: AsyncSession = None,
    ) -> Order:
        """创建订单"""
        try:
            # 生成订单ID
            order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

            # 计算总金额
            total_amount = sum(item["quantity"] * item["price"] for item in cart_items)

            # 创建订单对象
            order = Order(
                order_id=order_id,
                user_id=user_id,
                items=cart_items,
                total_amount=total_amount,
                shipping_address=shipping_address,
                note=note,
            )

            db.add(order)
            await db.commit()
            await db.refresh(order)

            logger.info(f"订单创建成功: {order_id}, 金额: {total_amount}")
            return order

        except Exception as e:
            await db.rollback()
            logger.error(f"创建订单失败: {e}")
            raise

    async def process_payment(
        self,
        order_id: str,
        payment_method: PaymentMethod,
        user_id: str,
        db: AsyncSession = None,
    ) -> Payment:
        """处理支付"""
        try:
            # 获取订单信息
            result = await db.execute(select(Order).where(Order.order_id == order_id))
            order = result.scalar_one_or_none()

            if not order:
                raise ValueError(f"订单不存在: {order_id}")

            if order.user_id != user_id:
                raise ValueError("无权操作此订单")

            if order.status != OrderStatus.PENDING_PAYMENT:
                raise ValueError("订单状态不正确")

            # 生成支付ID
            payment_id = f"PMT{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

            # 创建支付记录
            payment = Payment(
                payment_id=payment_id,
                order_id=order_id,
                user_id=user_id,
                amount=order.total_amount,
                payment_method=payment_method,
                status=PaymentStatus.PENDING,
            )

            db.add(payment)
            await db.commit()
            await db.refresh(payment)

            # 调用对应的支付网关
            gateway_processor = self.payment_gateways.get(payment_method)
            if not gateway_processor:
                raise ValueError(f"不支持的支付方式: {payment_method}")

            gateway_response = await gateway_processor(payment, db)

            # 更新支付状态
            if gateway_response.get("success"):
                payment.status = PaymentStatus.SUCCESS
                payment.transaction_id = gateway_response.get("transaction_id")
                payment.payment_proof = gateway_response.get("payment_proof")
                payment.gateway_response = gateway_response
                payment.completed_at = datetime.utcnow()

                # 更新订单状态
                order.payment_status = PaymentStatus.SUCCESS
                order.paid_amount = payment.amount
                order.status = OrderStatus.PENDING_SHIPMENT
                order.updated_at = datetime.utcnow()

                logger.info(f"支付成功: {payment_id}, 金额: {payment.amount}")
            else:
                payment.status = PaymentStatus.FAILED
                payment.gateway_response = gateway_response
                logger.error(
                    f"支付失败: {payment_id}, 错误: {gateway_response.get('error_message')}"
                )

            await db.commit()
            await db.refresh(payment)

            return payment

        except Exception as e:
            await db.rollback()
            logger.error(f"处理支付失败: {e}")
            raise

    async def _process_wechat_pay(
        self, payment: Payment, db: AsyncSession
    ) -> Dict[str, Any]:
        """处理微信支付（模拟）"""
        try:
            # 模拟微信支付处理
            import random

            # 模拟网络延迟
            await asyncio.sleep(random.uniform(0.5, 2.0))

            # 模拟80%成功率
            if random.random() < 0.8:
                return {
                    "success": True,
                    "transaction_id": f"wx{uuid.uuid4().hex[:16]}",
                    "payment_proof": f"wechat_payment_{payment.payment_id}",
                    "redirect_url": None,
                }
            else:
                return {"success": False, "error_message": "微信支付失败，请稍后重试"}

        except Exception as e:
            logger.error(f"微信支付处理异常: {e}")
            return {"success": False, "error_message": str(e)}

    async def _process_alipay(
        self, payment: Payment, db: AsyncSession
    ) -> Dict[str, Any]:
        """处理支付宝支付（模拟）"""
        try:
            import random

            await asyncio.sleep(random.uniform(0.3, 1.5))

            if random.random() < 0.85:
                return {
                    "success": True,
                    "transaction_id": f"alipay{uuid.uuid4().hex[:16]}",
                    "payment_proof": f"alipay_payment_{payment.payment_id}",
                    "redirect_url": None,
                }
            else:
                return {"success": False, "error_message": "支付宝支付失败，请稍后重试"}

        except Exception as e:
            logger.error(f"支付宝支付处理异常: {e}")
            return {"success": False, "error_message": str(e)}

    async def _process_bank_card(
        self, payment: Payment, db: AsyncSession
    ) -> Dict[str, Any]:
        """处理银行卡支付（模拟）"""
        try:
            import random

            await asyncio.sleep(random.uniform(1.0, 3.0))

            if random.random() < 0.75:
                return {
                    "success": True,
                    "transaction_id": f"bank{uuid.uuid4().hex[:16]}",
                    "payment_proof": f"bank_payment_{payment.payment_id}",
                    "redirect_url": None,
                }
            else:
                return {
                    "success": False,
                    "error_message": "银行卡支付失败，请检查卡片信息",
                }

        except Exception as e:
            logger.error(f"银行卡支付处理异常: {e}")
            return {"success": False, "error_message": str(e)}

    async def _process_balance_payment(
        self, payment: Payment, db: AsyncSession
    ) -> Dict[str, Any]:
        """处理余额支付（模拟）"""
        try:
            # 检查用户余额（这里简化处理）
            result = await db.execute(select(User).where(User.id == payment.user_id))
            user = result.scalar_one_or_none()

            if not user:
                return {"success": False, "error_message": "用户不存在"}

            # 模拟余额充足的情况
            import random

            if random.random() < 0.9:  # 90%成功率
                return {
                    "success": True,
                    "transaction_id": f"bal{uuid.uuid4().hex[:16]}",
                    "payment_proof": f"balance_payment_{payment.payment_id}",
                    "redirect_url": None,
                }
            else:
                return {"success": False, "error_message": "余额不足"}

        except Exception as e:
            logger.error(f"余额支付处理异常: {e}")
            return {"success": False, "error_message": str(e)}

    async def get_order(
        self, order_id: str, user_id: str, db: AsyncSession
    ) -> Optional[Order]:
        """获取订单详情"""
        try:
            result = await db.execute(
                select(Order).where(
                    Order.order_id == order_id, Order.user_id == user_id
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取订单失败: {e}")
            raise

    async def get_user_orders(
        self, user_id: str, db: AsyncSession, limit: int = 20, offset: int = 0
    ) -> List[Order]:
        """获取用户订单列表"""
        try:
            result = await db.execute(
                select(Order)
                .where(Order.user_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取用户订单列表失败: {e}")
            raise

    async def cancel_order(self, order_id: str, user_id: str, db: AsyncSession) -> bool:
        """取消订单"""
        try:
            result = await db.execute(
                select(Order).where(
                    Order.order_id == order_id, Order.user_id == user_id
                )
            )
            order = result.scalar_one_or_none()

            if not order:
                return False

            if order.status not in [
                OrderStatus.PENDING_PAYMENT,
                OrderStatus.PENDING_SHIPMENT,
            ]:
                raise ValueError("订单状态不允许取消")

            order.status = OrderStatus.CANCELLED
            order.payment_status = PaymentStatus.CANCELLED
            order.cancelled_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()

            await db.commit()
            logger.info(f"订单已取消: {order_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"取消订单失败: {e}")
            raise

    async def get_payment_statistics(
        self, user_id: str, db: AsyncSession
    ) -> Dict[str, Any]:
        """获取支付统计信息"""
        try:
            # 总订单数
            total_orders_result = await db.execute(
                select(func.count()).select_from(Order).where(Order.user_id == user_id)
            )
            total_orders = total_orders_result.scalar()

            # 总支付金额
            total_amount_result = await db.execute(
                select(func.sum(Payment.amount))
                .select_from(Payment)
                .where(
                    Payment.user_id == user_id, Payment.status == PaymentStatus.SUCCESS
                )
            )
            total_amount = total_amount_result.scalar() or 0

            # 成功支付数
            successful_payments_result = await db.execute(
                select(func.count())
                .select_from(Payment)
                .where(
                    Payment.user_id == user_id, Payment.status == PaymentStatus.SUCCESS
                )
            )
            successful_payments = successful_payments_result.scalar()

            # 按支付方式统计
            payment_method_stats_result = await db.execute(
                select(Payment.payment_method, func.count(), func.sum(Payment.amount))
                .select_from(Payment)
                .where(
                    Payment.user_id == user_id, Payment.status == PaymentStatus.SUCCESS
                )
                .group_by(Payment.payment_method)
            )

            payment_method_stats = []
            for method, count, amount in payment_method_stats_result:
                payment_method_stats.append(
                    {
                        "method": method.value,
                        "count": count,
                        "amount": float(amount or 0),
                    }
                )

            return {
                "total_orders": total_orders,
                "total_amount": float(total_amount),
                "successful_payments": successful_payments,
                "success_rate": round(
                    successful_payments / max(total_orders, 1) * 100, 2
                ),
                "payment_method_stats": payment_method_stats,
            }

        except Exception as e:
            logger.error(f"获取支付统计失败: {e}")
            raise


# 导入asyncio用于sleep
import asyncio
