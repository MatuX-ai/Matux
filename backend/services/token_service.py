"""
Token 管理服务

提供 Token 计费相关的核心业务逻辑：
- 用户余额管理
- Token 套餐购买
- Token 消费扣费
- 月度赠送
- 统计信息
- 成本预估
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from models.user_license import (
    TokenPackage,
    TokenPackageType,
    UserTokenBalance,
    TokenRechargeRecord,
    TokenUsageRecord,
)
from models.user import User

logger = logging.getLogger(__name__)


class TokenService:
    """Token 管理服务类"""

    def __init__(self, db: Session):
        """
        初始化 Token 服务
        
        Args:
            db: 数据库会话
        """
        self.db = db

    # ==================== 余额管理 ====================

    def get_or_create_user_balance(self, user_id: int) -> UserTokenBalance:
        """
        获取或创建用户 Token 余额
        
        Args:
            user_id: 用户 ID
            
        Returns:
            UserTokenBalance: 用户余额对象
        """
        balance = (
            self.db.query(UserTokenBalance)
            .filter(UserTokenBalance.user_id == user_id)
            .first()
        )
        
        if not balance:
            balance = UserTokenBalance(
                user_id=user_id,
                total_tokens=0,
                used_tokens=0,
                remaining_tokens=0,
            )
            self.db.add(balance)
            self.db.commit()
            self.db.refresh(balance)
            logger.info(f"为用户 {user_id} 创建 Token 余额账户")
        
        return balance

    def get_user_balance(self, user_id: int) -> Optional[UserTokenBalance]:
        """
        获取用户 Token 余额
        
        Args:
            user_id: 用户 ID
            
        Returns:
            UserTokenBalance 或 None
        """
        return (
            self.db.query(UserTokenBalance)
            .filter(UserTokenBalance.user_id == user_id)
            .first()
        )

    # ==================== 套餐购买 ====================

    def purchase_token_package(
        self,
        user_id: int,
        package_id: int,
        payment_method: str,
        order_no: str,
    ) -> TokenRechargeRecord:
        """
        购买 Token 套餐
        
        Args:
            user_id: 用户 ID
            package_id: 套餐 ID
            payment_method: 支付方式
            order_no: 订单号
            
        Returns:
            TokenRechargeRecord: 充值记录
            
        Raises:
            ValueError: 套餐不存在或非激活状态
        """
        # 获取套餐信息
        package = (
            self.db.query(TokenPackage)
            .filter(TokenPackage.id == package_id)
            .first()
        )
        
        if not package:
            raise ValueError(f"套餐 {package_id} 不存在")
        
        if not package.is_active:
            raise ValueError(f"套餐 {package.name} 已下架")
        
        # 获取或创建用户余额
        balance = self.get_or_create_user_balance(user_id)
        
        # 创建充值记录
        recharge_record = TokenRechargeRecord(
            user_balance_id=balance.id,
            package_id=package.id,
            token_amount=package.token_count,
            payment_amount=package.price,
            payment_method=payment_method,
            payment_status="pending",
            order_no=order_no,
        )
        
        self.db.add(recharge_record)
        self.db.commit()
        
        logger.info(
            f"用户 {user_id} 购买套餐 {package.name}, "
            f"Token 数量：{package.token_count}, "
            f"金额：{package.price}元，订单号：{order_no}"
        )
        
        return recharge_record

    def confirm_payment(self, order_no: str) -> bool:
        """
        确认支付成功并增加 Token 余额
        
        Args:
            order_no: 订单号
            
        Returns:
            bool: 是否成功
        """
        recharge_record = (
            self.db.query(TokenRechargeRecord)
            .filter(TokenRechargeRecord.order_no == order_no)
            .first()
        )
        
        if not recharge_record:
            logger.error(f"充值记录不存在：{order_no}")
            return False
        
        if recharge_record.payment_status == "success":
            logger.warning(f"订单 {order_no} 已经确认过")
            return True
        
        # 更新充值记录状态
        recharge_record.payment_status = "success"
        recharge_record.payment_time = datetime.utcnow()
        
        # 更新用户余额
        balance = recharge_record.user_balance
        balance.total_tokens += recharge_record.token_amount
        balance.remaining_tokens += recharge_record.token_amount
        
        self.db.commit()
        
        logger.info(
            f"订单 {order_no} 支付确认成功，"
            f"用户 {balance.user_id} 增加 {recharge_record.token_amount} Token"
        )
        
        return True

    # ==================== Token 消费 ====================

    def consume_tokens(
        self,
        user_id: int,
        token_amount: int,
        usage_type: str,
        usage_description: Optional[str] = None,
        resource_id: Optional[int] = None,
        resource_type: Optional[str] = None,
    ) -> bool:
        """
        消费 Token
        
        Args:
            user_id: 用户 ID
            token_amount: 消费数量
            usage_type: 使用类型（如 ai_teacher, course_generation）
            usage_description: 使用描述
            resource_id: 关联资源 ID
            resource_type: 资源类型
            
        Returns:
            bool: 是否成功
            
        Raises:
            ValueError: 余额不足
        """
        balance = self.get_or_create_user_balance(user_id)
        
        if balance.remaining_tokens < token_amount:
            logger.warning(
                f"用户 {user_id} Token 余额不足：剩余 {balance.remaining_tokens}, "
                f"需要 {token_amount}"
            )
            raise ValueError(
                f"Token 余额不足，当前剩余：{balance.remaining_tokens}"
            )
        
        # 扣减余额
        balance.remaining_tokens -= token_amount
        balance.used_tokens += token_amount
        
        # 创建使用记录
        usage_record = TokenUsageRecord(
            user_balance_id=balance.id,
            token_amount=token_amount,
            usage_type=usage_type,
            usage_description=usage_description,
            resource_id=resource_id,
            resource_type=resource_type,
        )
        
        self.db.add(usage_record)
        self.db.commit()
        
        logger.info(
            f"用户 {user_id} 消费 {token_amount} Token, "
            f"类型：{usage_type}, 剩余：{balance.remaining_tokens}"
        )
        
        return True

    # ==================== 月度赠送 ====================

    def get_monthly_bonus_tokens(self, user_id: int) -> int:
        """
        获取用户本月可领取的赠送 Token 数量
        
        Args:
            user_id: 用户 ID
            
        Returns:
            int: 赠送的 Token 数量
        """
        from models.license import LicenseType
        from models.user_license import UserLicense
        
        # 获取用户的许可证信息
        user_license = (
            self.db.query(UserLicense)
            .filter(UserLicense.user_id == user_id)
            .first()
        )
        
        if not user_license or not user_license.license:
            return 0
        
        # 根据许可证类型确定赠送额度
        license_type = user_license.license.license_type
        
        bonus_map = {
            LicenseType.CLOUD_HOSTED: 1000,  # 云托管版每月赠送 1000 Token
            LicenseType.ENTERPRISE: 5000,    # 企业版每月赠送 5000 Token
            LicenseType.WINDOWS_LOCAL: 0,     # Windows 本地版不赠送
            LicenseType.OPEN_SOURCE: 0,       # 开源版不赠送
        }
        
        return bonus_map.get(license_type, 0)

    def claim_monthly_bonus(self, user_id: int) -> bool:
        """
        领取月度赠送 Token
        
        Args:
            user_id: 用户 ID
            
        Returns:
            bool: 是否成功领取
        """
        balance = self.get_or_create_user_balance(user_id)
        
        # 检查是否可以领取
        now = datetime.utcnow()
        if balance.last_bonus_date:
            # 检查是否已经领取过本月的
            if (
                balance.last_bonus_date.year == now.year
                and balance.last_bonus_date.month == now.month
            ):
                logger.info(f"用户 {user_id} 本月已领取过赠送 Token")
                return False
        
        # 计算赠送数量
        bonus_amount = self.get_monthly_bonus_tokens(user_id)
        
        if bonus_amount <= 0:
            logger.info(f"用户 {user_id} 不符合赠送条件")
            return False
        
        # 增加余额
        balance.monthly_bonus_tokens += bonus_amount
        balance.total_tokens += bonus_amount
        balance.remaining_tokens += bonus_amount
        balance.last_bonus_date = now
        
        self.db.commit()
        
        logger.info(
            f"用户 {user_id} 领取月度赠送 Token: {bonus_amount}, "
            f"当前余额：{balance.remaining_tokens}"
        )
        
        return True

    # ==================== 统计信息 ====================

    def get_token_stats(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户 Token 统计信息
        
        Args:
            user_id: 用户 ID
            
        Returns:
            Dict: 统计信息字典
        """
        balance = self.get_user_balance(user_id)
        
        if not balance:
            return {
                "total_tokens": 0,
                "used_tokens": 0,
                "remaining_tokens": 0,
                "total_recharged": 0,
                "total_records": 0,
            }
        
        # 统计充值次数和总量
        recharge_stats = (
            self.db.query(
                func.count(TokenRechargeRecord.id).label("count"),
                func.sum(TokenRechargeRecord.token_amount).label("total"),
            )
            .filter(TokenRechargeRecord.user_balance_id == balance.id)
            .filter(TokenRechargeRecord.payment_status == "success")
            .first()
        )
        
        # 统计使用记录
        usage_stats = (
            self.db.query(
                func.count(TokenUsageRecord.id).label("count"),
                func.sum(TokenUsageRecord.token_amount).label("total"),
            )
            .filter(TokenUsageRecord.user_balance_id == balance.id)
            .first()
        )
        
        return {
            "total_tokens": balance.total_tokens,
            "used_tokens": balance.used_tokens,
            "remaining_tokens": balance.remaining_tokens,
            "monthly_bonus_tokens": balance.monthly_bonus_tokens,
            "last_bonus_date": (
                balance.last_bonus_date.isoformat()
                if balance.last_bonus_date
                else None
            ),
            "total_recharged": recharge_stats.total or 0,
            "recharge_count": recharge_stats.count or 0,
            "total_used": usage_stats.total or 0,
            "usage_count": usage_stats.count or 0,
        }

    # ==================== 成本预估 ====================

    def estimate_course_cost(self, complexity: str) -> int:
        """
        预估课程生成的 Token 成本
        
        Args:
            complexity: 复杂度（simple, medium, complex）
            
        Returns:
            int: 预估 Token 数量
        """
        cost_map = {
            "simple": 50,      # 简单课程
            "medium": 150,     # 中等课程
            "complex": 500,    # 复杂课程
        }
        
        return cost_map.get(complexity.lower(), 100)

    def estimate_ai_chat_cost(self, text_length: int) -> int:
        """
        预估 AI 对话的 Token 成本
        
        Args:
            text_length: 文本长度（字符数）
            
        Returns:
            int: 预估 Token 数量
        """
        # 每 100 字符约 10 tokens
        return max(1, (text_length // 100) * 10)

    def estimate_ai_code_completion_cost(
        self,
        prompt_length: int,
        completion_length: int,
    ) -> int:
        """
        预估 AI 代码补全的 Token 成本
        
        Args:
            prompt_length: 提示词长度
            completion_length: 补全内容长度
            
        Returns:
            int: 预估 Token 数量
        """
        # 输入部分：每 4 字符约 1 token
        # 输出部分：每 1 字符约 1 token
        input_tokens = prompt_length // 4
        output_tokens = completion_length
        
        return input_tokens + output_tokens

    # ==================== 辅助方法 ====================

    def get_available_packages(self) -> List[TokenPackage]:
        """
        获取所有可用的套餐列表
        
        Returns:
            List[TokenPackage]: 套餐列表
        """
        return (
            self.db.query(TokenPackage)
            .filter(TokenPackage.is_active == True)
            .all()
        )

    def get_package_by_id(self, package_id: int) -> Optional[TokenPackage]:
        """
        根据 ID 获取套餐
        
        Args:
            package_id: 套餐 ID
            
        Returns:
            TokenPackage 或 None
        """
        return (
            self.db.query(TokenPackage)
            .filter(TokenPackage.id == package_id)
            .first()
        )

    def get_usage_history(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> List[TokenUsageRecord]:
        """
        获取用户使用历史
        
        Args:
            user_id: 用户 ID
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            List[TokenUsageRecord]: 使用记录列表
        """
        balance = self.get_user_balance(user_id)
        
        if not balance:
            return []
        
        return (
            self.db.query(TokenUsageRecord)
            .filter(TokenUsageRecord.user_balance_id == balance.id)
            .order_by(TokenUsageRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
