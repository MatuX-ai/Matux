"""
订阅状态机实现
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, Optional

from .subscription import SubscriptionStatus, UserSubscription

logger = logging.getLogger(__name__)


class SubscriptionFSM:
    """
    订阅有限状态机
    管理订阅的生命周期状态转换
    """

    def __init__(self, subscription: UserSubscription):
        self.subscription = subscription
        self.state = subscription.status
        self.transitions = self._build_transitions()

    def _build_transitions(self) -> Dict[SubscriptionStatus, list]:
        """构建状态转换映射"""
        return {
            SubscriptionStatus.TRIAL: [
                SubscriptionStatus.ACTIVE,  # 试用转正式
                SubscriptionStatus.EXPIRED,  # 试用过期
                SubscriptionStatus.CANCELLED,  # 试用期间取消
                SubscriptionStatus.SUSPENDED,  # 试用期间暂停
            ],
            SubscriptionStatus.ACTIVE: [
                SubscriptionStatus.GRACE_PERIOD,  # 进入宽限期
                SubscriptionStatus.CANCELLED,  # 主动取消
                SubscriptionStatus.SUSPENDED,  # 暂停
                SubscriptionStatus.TRIAL,  # 降级到试用（特殊情况）
            ],
            SubscriptionStatus.GRACE_PERIOD: [
                SubscriptionStatus.ACTIVE,  # 宽限期内恢复
                SubscriptionStatus.EXPIRED,  # 宽限期结束
                SubscriptionStatus.CANCELLED,  # 宽限期内取消
            ],
            SubscriptionStatus.PENDING: [
                SubscriptionStatus.TRIAL,  # 开始试用
                SubscriptionStatus.ACTIVE,  # 直接激活
                SubscriptionStatus.CANCELLED,  # 支付失败取消
            ],
            SubscriptionStatus.SUSPENDED: [
                SubscriptionStatus.ACTIVE,  # 恢复订阅
                SubscriptionStatus.CANCELLED,  # 暂停期间取消
                SubscriptionStatus.EXPIRED,  # 暂停期间过期
            ],
            SubscriptionStatus.CANCELLED: [SubscriptionStatus.PENDING],  # 重新订阅
            SubscriptionStatus.EXPIRED: [SubscriptionStatus.PENDING],  # 重新订阅
        }

    def can_transition(self, target_state: SubscriptionStatus) -> bool:
        """检查是否可以进行状态转换"""
        if self.state not in self.transitions:
            return False

        return target_state in self.transitions[self.state]

    def transition(
        self,
        target_state: SubscriptionStatus,
        reason: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        执行状态转换

        Args:
            target_state: 目标状态
            reason: 转换原因
            metadata: 附加元数据

        Returns:
            bool: 转换是否成功
        """
        if not self.can_transition(target_state):
            logger.warning(f"无效的状态转换: {self.state} -> {target_state}")
            return False

        # 记录转换历史
        transition_record = {
            "from_state": self.state.value,
            "to_state": target_state.value,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "metadata": metadata or {},
        }

        # 更新订阅对象
        old_state = self.state
        self.subscription.status = target_state
        self.state = target_state

        # 执行特定状态转换的业务逻辑
        self._handle_state_specific_logic(target_state, old_state, metadata)

        # 记录转换日志
        logger.info(
            f"订阅状态转换: {self.subscription.subscription_id} "
            f"从 {old_state.value} 到 {target_state.value} - {reason}"
        )

        return True

    def _handle_state_specific_logic(
        self,
        new_state: SubscriptionStatus,
        old_state: SubscriptionStatus,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """处理特定状态转换的业务逻辑"""

        # 试用期相关逻辑
        if old_state == SubscriptionStatus.TRIAL:
            self.subscription.trial_used = True
            if hasattr(self.subscription, "trial_end_date"):
                self.subscription.trial_end_date = datetime.utcnow()

        # 宽限期相关逻辑
        elif new_state == SubscriptionStatus.GRACE_PERIOD:
            # 设置默认宽限期（7天）
            grace_days = metadata.get("grace_days", 7) if metadata else 7
            self.subscription.grace_period_end = datetime.utcnow() + timedelta(
                days=grace_days
            )

        # 暂停相关逻辑
        elif new_state == SubscriptionStatus.SUSPENDED:
            metadata.get("reason", "user_requested") if metadata else "user_requested"
            # 可以在这里添加暂停的具体业务逻辑

        # 激活相关逻辑
        elif new_state == SubscriptionStatus.ACTIVE:
            # 清除暂停状态相关的时间限制
            if old_state == SubscriptionStatus.SUSPENDED:
                # 恢复订阅的正常计费周期
                self._recalculate_billing_dates()

    def _recalculate_billing_dates(self):
        """重新计算计费日期"""
        if not self.subscription.next_billing_date:
            return

        # 根据订阅计划重新计算下次计费日期
        plan = self.subscription.plan
        if plan and plan.billing_cycle:
            # 这里可以根据具体的计费周期重新计算
            pass

    def check_auto_transitions(self) -> bool:
        """
        检查并执行自动状态转换
        例如：试用期结束自动转为正式订阅或过期

        Returns:
            bool: 是否发生了状态转换
        """
        current_time = datetime.utcnow()
        changed = False

        # 检查试用期结束
        if (
            self.state == SubscriptionStatus.TRIAL
            and hasattr(self.subscription, "trial_end_date")
            and self.subscription.trial_end_date
            and current_time >= self.subscription.trial_end_date
        ):

            # 如果设置了自动转为正式订阅且支付成功
            if (
                hasattr(self.subscription, "auto_convert_to_paid")
                and self.subscription.auto_convert_to_paid
                and self._check_payment_status()
            ):
                changed = self.transition(
                    SubscriptionStatus.ACTIVE,
                    "试用期结束自动转为正式订阅",
                    {"auto_conversion": True},
                )
            else:
                changed = self.transition(
                    SubscriptionStatus.EXPIRED,
                    "试用期结束",
                    {"reason": "trial_expired"},
                )

        # 检查宽限期结束
        elif (
            self.state == SubscriptionStatus.GRACE_PERIOD
            and self.subscription.grace_period_end
            and current_time >= self.subscription.grace_period_end
        ):

            changed = self.transition(
                SubscriptionStatus.EXPIRED,
                "宽限期结束",
                {"reason": "grace_period_expired"},
            )

        # 检查订阅到期
        elif (
            self.state == SubscriptionStatus.ACTIVE
            and self.subscription.end_date
            and current_time >= self.subscription.end_date
        ):

            # 如果启用了自动续费且支付成功
            if self.subscription.auto_renew and self._attempt_auto_renewal():
                changed = True
            else:
                # 进入宽限期
                changed = self.transition(
                    SubscriptionStatus.GRACE_PERIOD,
                    "订阅到期进入宽限期",
                    {"reason": "subscription_expired"},
                )

        return changed

    def _check_payment_status(self) -> bool:
        """检查支付状态"""
        # 这里应该集成实际的支付状态检查逻辑
        # 暂时返回True作为示例
        return True

    def _attempt_auto_renewal(self) -> bool:
        """尝试自动续费"""
        # 这里应该集成实际的自动续费逻辑
        # 包括调用支付网关、创建支付记录等
        try:
            # 示例逻辑
            if self._process_payment():
                # 更新订阅周期
                self._extend_subscription_period()
                return self.transition(
                    SubscriptionStatus.ACTIVE, "自动续费成功", {"auto_renewal": True}
                )
        except Exception as e:
            logger.error(f"自动续费失败: {e}")

        return False

    def _process_payment(self) -> bool:
        """处理支付"""
        # 实际的支付处理逻辑
        return True

    def _extend_subscription_period(self):
        """延长订阅周期"""
        if self.subscription.plan and self.subscription.plan.billing_cycle:
            # 根据计费周期计算新的结束日期
            billing_cycle = self.subscription.plan.billing_cycle
            current_end = self.subscription.end_date or datetime.utcnow()

            if billing_cycle == "monthly":
                new_end = current_end + timedelta(days=30)
            elif billing_cycle == "yearly":
                new_end = current_end + timedelta(days=365)
            else:
                new_end = current_end + timedelta(days=30)  # 默认按月计算

            self.subscription.end_date = new_end
            self.subscription.next_billing_date = new_end
            self.subscription.renewal_count += 1

    def get_valid_transitions(self) -> list:
        """获取当前状态下允许的所有转换"""
        return self.transitions.get(self.state, [])

    def get_state_info(self) -> Dict[str, Any]:
        """获取当前状态信息"""
        return {
            "current_state": self.state.value,
            "subscription_id": self.subscription.subscription_id,
            "valid_transitions": [
                state.value for state in self.get_valid_transitions()
            ],
            "auto_transitions_enabled": True,
        }


# 便捷函数
def create_subscription_fsm(subscription: UserSubscription) -> SubscriptionFSM:
    """创建订阅状态机实例"""
    return SubscriptionFSM(subscription)


def process_subscription_lifecycle(subscription: UserSubscription) -> bool:
    """
    处理订阅生命周期的自动转换

    Args:
        subscription: 订阅对象

    Returns:
        bool: 是否发生了状态变化
    """
    fsm = create_subscription_fsm(subscription)
    return fsm.check_auto_transitions()
