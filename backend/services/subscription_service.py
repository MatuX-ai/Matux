"""
订阅服务核心实现
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.payment import PaymentMethod, PaymentStatus
from models.subscription import (
    BillingCycle,
    SubscriptionPayment,
    SubscriptionPlan,
    SubscriptionPlanType,
    SubscriptionStatus,
    UserSubscription,
)
from services.payment_gateway import PaymentGatewayFactory
from utils.logger import get_logger

logger = get_logger(__name__)


class SubscriptionService:
    """订阅服务类"""

    def __init__(self):
        self.payment_gateways = PaymentGatewayFactory

    async def create_subscription_plan(
        self,
        name: str,
        description: str,
        plan_type: SubscriptionPlanType,
        price: float,
        billing_cycle: BillingCycle,
        features: List[str] = None,
        limits: Dict[str, Any] = None,
        trial_period_days: int = 0,
        setup_fee: float = 0.0,
        currency: str = "CNY",
        is_popular: bool = False,
        db: AsyncSession = None,
    ) -> SubscriptionPlan:
        """创建订阅计划"""
        try:
            # 生成计划ID
            plan_id = f"PLAN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

            plan = SubscriptionPlan(
                plan_id=plan_id,
                name=name,
                description=description,
                plan_type=plan_type,
                price=price,
                billing_cycle=billing_cycle,
                currency=currency,
                features=features or [],
                limits=limits or {},
                trial_period_days=trial_period_days,
                setup_fee=setup_fee,
                is_popular=is_popular,
            )

            db.add(plan)
            await db.commit()
            await db.refresh(plan)

            logger.info(f"创建订阅计划成功: {plan_id}")
            return plan

        except IntegrityError as e:
            await db.rollback()
            logger.error(f"创建订阅计划失败 - 重复ID: {str(e)}")
            raise ValueError("计划ID已存在")
        except Exception as e:
            await db.rollback()
            logger.error(f"创建订阅计划失败: {str(e)}")
            raise

    async def get_subscription_plans(
        self,
        is_active: bool = True,
        plan_type: Optional[SubscriptionPlanType] = None,
        db: AsyncSession = None,
    ) -> List[SubscriptionPlan]:
        """获取订阅计划列表"""
        try:
            query = select(SubscriptionPlan)

            conditions = []
            if is_active is not None:
                conditions.append(SubscriptionPlan.is_active == is_active)
            if plan_type:
                conditions.append(SubscriptionPlan.plan_type == plan_type)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(
                SubscriptionPlan.is_popular.desc(), SubscriptionPlan.price.asc()
            )

            result = await db.execute(query)
            plans = result.scalars().all()

            return list(plans)

        except Exception as e:
            logger.error(f"获取订阅计划失败: {str(e)}")
            raise

    async def subscribe_user(
        self,
        user_id: str,
        plan_id: str,
        payment_method: PaymentMethod,
        auto_renew: bool = True,
        custom_config: Dict[str, Any] = None,
        db: AsyncSession = None,
    ) -> UserSubscription:
        """用户订阅"""
        try:
            # 验证计划是否存在且激活
            plan_query = select(SubscriptionPlan).where(
                and_(
                    SubscriptionPlan.plan_id == plan_id,
                    SubscriptionPlan.is_active == True,
                )
            )
            plan_result = await db.execute(plan_query)
            plan = plan_result.scalar_one_or_none()

            if not plan:
                raise ValueError("订阅计划不存在或未激活")

            # 检查用户是否已有相同计划的有效订阅
            existing_query = select(UserSubscription).where(
                and_(
                    UserSubscription.user_id == user_id,
                    UserSubscription.plan_id == plan_id,
                    UserSubscription.status.in_(
                        [SubscriptionStatus.ACTIVE, SubscriptionStatus.PENDING]
                    ),
                )
            )
            existing_result = await db.execute(existing_query)
            existing_subscription = existing_result.scalar_one_or_none()

            if existing_subscription:
                raise ValueError("用户已有该计划的有效订阅")

            # 生成订阅ID
            subscription_id = f"SUB{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

            # 计算订阅周期
            start_date = datetime.utcnow()
            end_date = self._calculate_end_date(
                start_date, plan.billing_cycle, plan.trial_period_days
            )
            next_billing_date = self._calculate_next_billing_date(
                end_date, plan.billing_cycle
            )

            # 创建订阅记录
            subscription = UserSubscription(
                subscription_id=subscription_id,
                user_id=user_id,
                plan_id=plan_id,
                status=SubscriptionStatus.PENDING,
                start_date=start_date,
                end_date=end_date,
                next_billing_date=next_billing_date,
                auto_renew=auto_renew,
                price_snapshot=plan.price,
                currency_snapshot=plan.currency,
                custom_config=custom_config or {},
            )

            db.add(subscription)
            await db.commit()
            await db.refresh(subscription)

            # 如果有试用期，直接激活；否则需要支付
            if plan.trial_period_days > 0:
                subscription.status = SubscriptionStatus.ACTIVE
                await db.commit()
                logger.info(f"用户订阅试用期开始: {subscription_id}")
            else:
                # 处理首期支付
                await self._process_initial_payment(
                    subscription, plan, payment_method, db
                )

            logger.info(f"用户订阅创建成功: {subscription_id}")
            return subscription

        except Exception as e:
            await db.rollback()
            logger.error(f"用户订阅失败: {str(e)}")
            raise

    async def cancel_subscription(
        self, subscription_id: str, user_id: str = None, db: AsyncSession = None
    ) -> UserSubscription:
        """取消订阅"""
        try:
            query = select(UserSubscription).where(
                UserSubscription.subscription_id == subscription_id
            )
            if user_id:
                query = query.where(UserSubscription.user_id == user_id)

            result = await db.execute(query)
            subscription = result.scalar_one_or_none()

            if not subscription:
                raise ValueError("订阅不存在")

            if subscription.status != SubscriptionStatus.ACTIVE:
                raise ValueError("只能取消激活中的订阅")

            # 更新订阅状态
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.utcnow()
            subscription.auto_renew = False

            await db.commit()
            await db.refresh(subscription)

            logger.info(f"订阅已取消: {subscription_id}")
            return subscription

        except Exception as e:
            await db.rollback()
            logger.error(f"取消订阅失败: {str(e)}")
            raise

    async def get_user_subscriptions(
        self,
        user_id: str,
        status: Optional[SubscriptionStatus] = None,
        db: AsyncSession = None,
    ) -> List[UserSubscription]:
        """获取用户订阅列表"""
        try:
            query = select(UserSubscription).where(UserSubscription.user_id == user_id)

            if status:
                query = query.where(UserSubscription.status == status)

            query = query.order_by(UserSubscription.created_at.desc())

            result = await db.execute(query)
            subscriptions = result.scalars().all()

            return list(subscriptions)

        except Exception as e:
            logger.error(f"获取用户订阅失败: {str(e)}")
            raise

    async def process_recurring_payments(
        self, db: AsyncSession = None
    ) -> List[SubscriptionPayment]:
        """处理循环支付（定时任务调用）"""
        try:
            # 查找需要处理的订阅
            today = datetime.utcnow().date()
            query = select(UserSubscription).where(
                and_(
                    UserSubscription.status == SubscriptionStatus.ACTIVE,
                    UserSubscription.next_billing_date <= today,
                    UserSubscription.auto_renew == True,
                )
            )

            result = await db.execute(query)
            subscriptions = result.scalars().all()

            processed_payments = []

            for subscription in subscriptions:
                try:
                    payment = await self._process_subscription_payment(subscription, db)
                    if payment:
                        processed_payments.append(payment)
                except Exception as e:
                    logger.error(
                        f"处理订阅支付失败 {subscription.subscription_id}: {str(e)}"
                    )
                    continue

            logger.info(f"处理了 {len(processed_payments)} 个循环支付")
            return processed_payments

        except Exception as e:
            logger.error(f"处理循环支付失败: {str(e)}")
            raise

    async def _process_initial_payment(
        self,
        subscription: UserSubscription,
        plan: SubscriptionPlan,
        payment_method: PaymentMethod,
        db: AsyncSession,
    ) -> SubscriptionPayment:
        """处理初始支付"""
        try:
            # 生成支付ID
            payment_id = f"SUMPAY{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

            # 创建支付记录
            payment_record = SubscriptionPayment(
                payment_id=payment_id,
                subscription_id=subscription.subscription_id,
                amount=plan.price + plan.setup_fee,
                currency=plan.currency,
                payment_method=payment_method.value,
                billing_cycle_start=subscription.start_date,
                billing_cycle_end=subscription.end_date,
                status=PaymentStatus.PENDING.value,
            )

            db.add(payment_record)
            await db.commit()
            await db.refresh(payment_record)

            # 调用支付网关
            gateway_response = self.payment_gateways.create_payment(
                payment_method.value,
                payment_record.amount,
                subscription.subscription_id,
                subject=f"{plan.name} 订阅费用",
            )

            if gateway_response.get("success"):
                # 支付成功，激活订阅
                payment_record.status = PaymentStatus.SUCCESS.value
                payment_record.transaction_id = gateway_response.get("transaction_id")
                payment_record.payment_proof = gateway_response.get("payment_proof")
                payment_record.gateway_response = gateway_response
                payment_record.processed_at = datetime.utcnow()

                subscription.status = SubscriptionStatus.ACTIVE

                await db.commit()
                logger.info(f"初始支付成功: {payment_id}")
            else:
                # 支付失败
                payment_record.status = PaymentStatus.FAILED.value
                payment_record.gateway_response = gateway_response
                await db.commit()
                logger.warning(f"初始支付失败: {payment_id}")

            return payment_record

        except Exception as e:
            await db.rollback()
            logger.error(f"处理初始支付失败: {str(e)}")
            raise

    async def _process_subscription_payment(
        self, subscription: UserSubscription, db: AsyncSession
    ) -> Optional[SubscriptionPayment]:
        """处理订阅支付"""
        try:
            # 获取订阅计划
            plan_query = select(SubscriptionPlan).where(
                SubscriptionPlan.plan_id == subscription.plan_id
            )
            plan_result = await db.execute(plan_query)
            plan = plan_result.scalar_one_or_none()

            if not plan:
                logger.error(f"订阅计划不存在: {subscription.plan_id}")
                return None

            # 生成新的计费周期
            new_start_date = subscription.next_billing_date
            new_end_date = self._calculate_end_date(new_start_date, plan.billing_cycle)
            new_next_billing_date = self._calculate_next_billing_date(
                new_end_date, plan.billing_cycle
            )

            # 生成支付ID
            payment_id = f"SUMPAY{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"

            # 创建支付记录
            payment_record = SubscriptionPayment(
                payment_id=payment_id,
                subscription_id=subscription.subscription_id,
                amount=plan.price,
                currency=plan.currency,
                payment_method="auto_renew",  # 自动续费
                billing_cycle_start=new_start_date,
                billing_cycle_end=new_end_date,
                status=PaymentStatus.PENDING.value,
            )

            db.add(payment_record)

            # 更新订阅周期
            subscription.start_date = new_start_date
            subscription.end_date = new_end_date
            subscription.next_billing_date = new_next_billing_date
            subscription.renewal_count += 1

            await db.commit()
            await db.refresh(payment_record)

            # 这里可以集成实际的自动扣费逻辑
            # 暂时标记为成功（实际应用中需要调用支付网关）
            payment_record.status = PaymentStatus.SUCCESS.value
            payment_record.processed_at = datetime.utcnow()

            await db.commit()

            logger.info(f"订阅支付处理成功: {payment_id}")
            return payment_record

        except Exception as e:
            await db.rollback()
            logger.error(f"处理订阅支付失败: {str(e)}")
            return None

    def _calculate_end_date(
        self, start_date: datetime, billing_cycle: BillingCycle, trial_days: int = 0
    ) -> datetime:
        """计算结束日期"""
        if trial_days > 0:
            return start_date + timedelta(days=trial_days)

        cycle_map = {
            BillingCycle.WEEKLY: timedelta(weeks=1),
            BillingCycle.MONTHLY: timedelta(days=30),
            BillingCycle.QUARTERLY: timedelta(days=90),
            BillingCycle.YEARLY: timedelta(days=365),
            BillingCycle.CUSTOM: timedelta(days=30),  # 默认30天
        }

        return start_date + cycle_map.get(billing_cycle, timedelta(days=30))

    def _calculate_next_billing_date(
        self, current_end_date: datetime, billing_cycle: BillingCycle
    ) -> datetime:
        """计算下次计费日期"""
        cycle_map = {
            BillingCycle.WEEKLY: timedelta(weeks=1),
            BillingCycle.MONTHLY: timedelta(days=30),
            BillingCycle.QUARTERLY: timedelta(days=90),
            BillingCycle.YEARLY: timedelta(days=365),
            BillingCycle.CUSTOM: timedelta(days=30),
        }

        return current_end_date + cycle_map.get(billing_cycle, timedelta(days=30))


# 导出服务实例
subscription_service = SubscriptionService()
