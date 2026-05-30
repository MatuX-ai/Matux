"""
企业赞助管理核心服务
提供赞助活动管理、品牌曝光统计、积分转换等核心业务功能
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from models.license import Organization
from models.sponsorship import (
    BrandExposure,
    ExposureRecordCreate,
    ExposureType,
    PointConversionRule,
    PointTransaction,
    PointTransactionType,
    Sponsorship,
    SponsorshipCreate,
    SponsorshipStatus,
    SponsorshipUpdate,
)
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)


class SponsorshipService:
    """赞助管理核心服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.cache_prefix = "sponsorship:"
        self.cache_ttl = 3600  # 1小时缓存

    def create_sponsorship(
        self, org_id: int, sponsorship_data: SponsorshipCreate
    ) -> Sponsorship:
        """
        创建新的赞助活动

        Args:
            org_id: 组织ID
            sponsorship_data: 赞助活动数据

        Returns:
            Sponsorship: 创建的赞助活动对象

        Raises:
            ValueError: 数据验证失败
            SQLAlchemyError: 数据库操作失败
        """
        try:
            # 验证组织是否存在
            organization = (
                self.db.query(Organization).filter(Organization.id == org_id).first()
            )
            if not organization:
                raise ValueError(f"组织ID {org_id} 不存在")

            # 创建赞助活动
            sponsorship = Sponsorship(
                org_id=org_id,
                name=sponsorship_data.name,
                description=sponsorship_data.description,
                sponsor_amount=sponsorship_data.sponsor_amount,
                currency=sponsorship_data.currency,
                start_date=sponsorship_data.start_date,
                end_date=sponsorship_data.end_date,
                exposure_types=sponsorship_data.exposure_types,
                target_audience=sponsorship_data.target_audience or {},
                branding_guidelines=getattr(
                    sponsorship_data, "branding_guidelines", {}
                ),
                status=SponsorshipStatus.ACTIVE.value,
            )

            self.db.add(sponsorship)
            self.db.flush()  # 获取ID但不提交

            # 更新组织赞助统计数据
            organization.total_sponsorship_amount += sponsorship.sponsor_amount
            organization.active_sponsorships += 1

            self.db.commit()
            self.db.refresh(sponsorship)

            # 清除相关缓存
            self._clear_organization_cache(org_id)

            logger.info(f"成功创建赞助活动: {sponsorship.name} (ID: {sponsorship.id})")
            return sponsorship

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建赞助活动失败: {str(e)}")
            raise

    def get_sponsorship(
        self, sponsorship_id: int, org_id: int = None
    ) -> Optional[Sponsorship]:
        """
        获取赞助活动详情

        Args:
            sponsorship_id: 赞助活动ID
            org_id: 组织ID（可选，用于权限验证）

        Returns:
            Optional[Sponsorship]: 赞助活动对象
        """
        cache_key = f"{self.cache_prefix}sponsorship:{sponsorship_id}"

        try:
            # 尝试从缓存获取
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"从缓存获取赞助活动 {sponsorship_id}")
                # 这里应该反序列化缓存数据

            # 从数据库查询
            query = self.db.query(Sponsorship).filter(Sponsorship.id == sponsorship_id)

            if org_id:
                query = query.filter(Sponsorship.org_id == org_id)

            sponsorship = query.first()

            if sponsorship:
                # 缓存结果
                # 这里应该序列化对象数据
                redis_client.setex(cache_key, self.cache_ttl, str(sponsorship.__dict__))

            return sponsorship

        except Exception as e:
            logger.error(f"获取赞助活动失败: {str(e)}")
            return None

    def update_sponsorship(
        self, sponsorship_id: int, org_id: int, update_data: SponsorshipUpdate
    ) -> Optional[Sponsorship]:
        """
        更新赞助活动

        Args:
            sponsorship_id: 赞助活动ID
            org_id: 组织ID
            update_data: 更新数据

        Returns:
            Optional[Sponsorship]: 更新后的赞助活动对象
        """
        try:
            sponsorship = (
                self.db.query(Sponsorship)
                .filter(
                    and_(Sponsorship.id == sponsorship_id, Sponsorship.org_id == org_id)
                )
                .first()
            )

            if not sponsorship:
                raise ValueError(f"赞助活动 {sponsorship_id} 不存在或无权限访问")

            # 更新字段
            update_fields = update_data.dict(exclude_unset=True)
            for field, value in update_fields.items():
                setattr(sponsorship, field, value)

            sponsorship.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(sponsorship)

            # 清除缓存
            self._clear_sponsorship_cache(sponsorship_id)
            self._clear_organization_cache(org_id)

            logger.info(f"成功更新赞助活动: {sponsorship_id}")
            return sponsorship

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新赞助活动失败: {str(e)}")
            raise

    def record_brand_exposure(
        self, sponsorship_id: int, exposure_data: ExposureRecordCreate
    ) -> BrandExposure:
        """
        记录品牌曝光数据

        Args:
            sponsorship_id: 赞助活动ID
            exposure_data: 曝光数据

        Returns:
            BrandExposure: 创建的曝光记录
        """
        try:
            # 验证赞助活动存在
            sponsorship = (
                self.db.query(Sponsorship)
                .filter(Sponsorship.id == sponsorship_id)
                .first()
            )
            if not sponsorship:
                raise ValueError(f"赞助活动 {sponsorship_id} 不存在")

            # 创建曝光记录
            exposure = BrandExposure(
                sponsorship_id=sponsorship_id,
                exposure_type=exposure_data.exposure_type,
                platform=exposure_data.platform,
                placement=exposure_data.placement,
                view_count=exposure_data.view_count,
                click_count=exposure_data.click_count,
                engagement_count=getattr(exposure_data, "engagement_count", 0),
                conversion_count=getattr(exposure_data, "conversion_count", 0),
                duration_seconds=getattr(exposure_data, "duration_seconds", 0),
                geo_location=getattr(exposure_data, "geo_location", {}),
            )

            self.db.add(exposure)
            self.db.flush()

            # 更新赞助活动统计
            sponsorship.total_exposures += exposure_data.view_count

            # 计算并增加积分
            points_earned = self._calculate_exposure_points(exposure_data)
            if points_earned > 0:
                self._record_point_transaction(
                    sponsorship_id=sponsorship_id,
                    transaction_type=PointTransactionType.EARNED.value,
                    points_amount=points_earned,
                    description=f"品牌曝光积分奖励 - {exposure_data.exposure_type}",
                    reference_id=f"EXP-{exposure.id}",
                )
                sponsorship.total_points_earned += points_earned

            self.db.commit()
            self.db.refresh(exposure)

            # 更新组织统计数据
            self._update_organization_stats(sponsorship.org_id)
            # 清除缓存
            self._clear_sponsorship_cache(sponsorship_id)

            logger.info(
                f"成功记录品牌曝光: {exposure_data.exposure_type} (ID: {exposure.id})"
            )
            return exposure

        except Exception as e:
            self.db.rollback()
            logger.error(f"记录品牌曝光失败: {str(e)}")
            raise

    def convert_points(
        self, sponsorship_id: int, rule_id: int, quantity: int = 1
    ) -> List[PointTransaction]:
        """
        转换积分

        Args:
            sponsorship_id: 赞助活动ID
            rule_id: 转换规则ID
            quantity: 转换数量

        Returns:
            List[PointTransaction]: 积分交易记录列表
        """
        try:
            # 获取赞助活动和转换规则
            sponsorship = (
                self.db.query(Sponsorship)
                .filter(Sponsorship.id == sponsorship_id)
                .first()
            )
            rule = (
                self.db.query(PointConversionRule)
                .filter(PointConversionRule.id == rule_id)
                .first()
            )

            if not sponsorship:
                raise ValueError(f"赞助活动 {sponsorship_id} 不存在")
            if not rule:
                raise ValueError(f"转换规则 {rule_id} 不存在")
            if not rule.is_active:
                raise ValueError("转换规则已停用")

            # 检查赞助金额是否满足最低要求
            if sponsorship.sponsor_amount < rule.min_sponsorship_amount:
                raise ValueError(
                    f"赞助金额不足，最低要求 {rule.min_sponsorship_amount}"
                )

            # 检查积分余额
            available_points = self.get_available_points(sponsorship_id)
            required_points = rule.points_required * quantity

            if available_points < required_points:
                raise ValueError(
                    f"积分余额不足，需要 {required_points}，当前 {available_points}"
                )

            # 检查转换限制
            if rule.max_conversions_per_user > 0:
                conversion_count = self._get_user_conversion_count(
                    sponsorship_id, rule_id
                )
                if conversion_count + quantity > rule.max_conversions_per_user:
                    raise ValueError(
                        f"超过个人转换限制，最多 {rule.max_conversions_per_user} 次"
                    )

            # 执行转换
            transactions = []
            for i in range(quantity):
                # 扣除积分
                deduction = self._record_point_transaction(
                    sponsorship_id=sponsorship_id,
                    transaction_type=PointTransactionType.CONVERTED.value,
                    points_amount=-rule.points_required,
                    description=f"积分转换 - {rule.name}",
                    reference_id=f"CVR-{rule_id}-{i+1}",
                )
                transactions.append(deduction)

            self.db.commit()

            # 清除缓存
            self._clear_sponsorship_cache(sponsorship_id)
            self._clear_organization_cache(sponsorship.org_id)

            logger.info(f"成功转换积分: {quantity} x {rule.name}")
            return transactions

        except Exception as e:
            self.db.rollback()
            logger.error(f"积分转换失败: {str(e)}")
            raise

    def get_sponsorship_analytics(
        self, org_id: int, start_date: datetime = None, end_date: datetime = None
    ) -> Dict[str, Any]:
        """
        获取赞助活动分析数据

        Args:
            org_id: 组织ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Dict[str, Any]: 分析数据
        """
        cache_key = f"{self.cache_prefix}analytics:{org_id}:{start_date}:{end_date}"

        try:
            # 尝试从缓存获取
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.debug(f"从缓存获取分析数据 for org {org_id}")
                # 返回反序列化的缓存数据

            # 设置默认时间范围
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)

            # 查询赞助活动数据
            sponsorships = (
                self.db.query(Sponsorship)
                .filter(
                    and_(
                        Sponsorship.org_id == org_id,
                        Sponsorship.created_at >= start_date,
                        Sponsorship.created_at <= end_date,
                    )
                )
                .all()
            )

            # 计算统计指标
            total_sponsorship_amount = sum(s.sponsor_amount for s in sponsorships)
            total_exposures = sum(s.total_exposures for s in sponsorships)
            total_points_earned = sum(s.total_points_earned for s in sponsorships)
            active_sponsorships = len(
                [s for s in sponsorships if s.status == SponsorshipStatus.ACTIVE.value]
            )

            # 计算平均转化率
            total_conversion_rate = 0.0
            active_count = 0
            for s in sponsorships:
                if s.total_exposures > 0:
                    total_conversion_rate += s.conversion_rate
                    active_count += 1

            avg_conversion_rate = (
                total_conversion_rate / active_count if active_count > 0 else 0.0
            )

            analytics_data = {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "summary": {
                    "total_sponsorships": len(sponsorships),
                    "active_sponsorships": active_sponsorships,
                    "total_amount": total_sponsorship_amount,
                    "total_exposures": total_exposures,
                    "total_points_earned": total_points_earned,
                    "average_conversion_rate": round(avg_conversion_rate, 2),
                },
                "trends": self._get_exposure_trends(org_id, start_date, end_date),
                "top_performing": self._get_top_performing_sponsorships(
                    org_id, start_date, end_date
                ),
            }

            # 缓存结果
            # 应该序列化数据后缓存
            redis_client.setex(cache_key, self.cache_ttl, str(analytics_data))

            return analytics_data

        except Exception as e:
            logger.error(f"获取分析数据失败: {str(e)}")
            return {}

    def get_available_points(self, sponsorship_id: int) -> float:
        """
        获取可用积分余额

        Args:
            sponsorship_id: 赞助活动ID

        Returns:
            float: 可用积分余额
        """
        try:
            result = (
                self.db.query(func.sum(PointTransaction.points_amount))
                .filter(PointTransaction.sponsorship_id == sponsorship_id)
                .scalar()
            )

            return float(result) if result else 0.0

        except Exception as e:
            logger.error(f"获取积分余额失败: {str(e)}")
            return 0.0

    def _calculate_exposure_points(self, exposure_data: ExposureRecordCreate) -> float:
        """
        计算曝光应得积分

        Args:
            exposure_data: 曝光数据

        Returns:
            float: 应得积分
        """
        # 基础积分计算公式
        base_points = exposure_data.view_count * 0.1  # 每次展示0.1积分

        # 根据曝光类型调整系数
        type_multipliers = {
            ExposureType.BANNER.value: 1.0,
            ExposureType.SIDEBAR.value: 0.8,
            ExposureType.POPUP.value: 1.2,
            ExposureType.EMAIL.value: 1.5,
            ExposureType.SOCIAL_MEDIA.value: 1.3,
            ExposureType.CONTENT_INTEGRATION.value: 2.0,
        }

        multiplier = type_multipliers.get(exposure_data.exposure_type, 1.0)
        points = base_points * multiplier

        # 根据互动情况进行加成
        if exposure_data.click_count > 0:
            click_rate = exposure_data.click_count / exposure_data.view_count
            if click_rate > 0.05:  # 点击率超过5%
                points *= 1.5

        if (
            hasattr(exposure_data, "engagement_count")
            and exposure_data.engagement_count > 0
        ):
            engagement_bonus = exposure_data.engagement_count * 0.5
            points += engagement_bonus

        return round(points, 2)

    def _record_point_transaction(
        self,
        sponsorship_id: int,
        transaction_type: str,
        points_amount: float,
        description: str,
        reference_id: str = None,
    ) -> PointTransaction:
        """
        记录积分交易

        Args:
            sponsorship_id: 赞助活动ID
            transaction_type: 交易类型
            points_amount: 积分数额
            description: 描述
            reference_id: 关联ID

        Returns:
            PointTransaction: 积分交易记录
        """
        # 获取当前余额
        current_balance = self.get_available_points(sponsorship_id)

        transaction = PointTransaction(
            sponsorship_id=sponsorship_id,
            transaction_type=transaction_type,
            points_amount=points_amount,
            balance_before=current_balance,
            balance_after=current_balance + points_amount,
            description=description,
            reference_id=reference_id,
        )

        self.db.add(transaction)
        return transaction

    def _get_user_conversion_count(self, sponsorship_id: int, rule_id: int) -> int:
        """
        获取用户的转换次数

        Args:
            sponsorship_id: 赞助活动ID
            rule_id: 规则ID

        Returns:
            int: 转换次数
        """
        # 这里应该根据实际业务逻辑实现
        # 目前简化处理，返回固定值
        return 0

    def _get_exposure_trends(
        self, org_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        获取曝光趋势数据

        Args:
            org_id: 组织ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[Dict[str, Any]]: 趋势数据
        """
        # 简化实现，返回示例数据
        return [
            {
                "date": (start_date + timedelta(days=i)).strftime("%Y-%m-%d"),
                "exposures": 100 + i * 10,
            }
            for i in range((end_date - start_date).days + 1)
        ]

    def _get_top_performing_sponsorships(
        self, org_id: int, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        获取表现最好的赞助活动

        Args:
            org_id: 组织ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[Dict[str, Any]]: 表现数据
        """
        sponsorships = (
            self.db.query(Sponsorship)
            .filter(
                and_(
                    Sponsorship.org_id == org_id,
                    Sponsorship.created_at >= start_date,
                    Sponsorship.created_at <= end_date,
                )
            )
            .order_by(Sponsorship.total_exposures.desc())
            .limit(5)
            .all()
        )

        return [
            {
                "id": s.id,
                "name": s.name,
                "exposures": s.total_exposures,
                "points_earned": s.total_points_earned,
                "conversion_rate": s.conversion_rate,
            }
            for s in sponsorships
        ]

    def _update_organization_stats(self, org_id: int):
        """
        更新组织赞助统计数据

        Args:
            org_id: 组织ID
        """
        try:
            organization = (
                self.db.query(Organization).filter(Organization.id == org_id).first()
            )
            if organization:
                # 更新总曝光次数
                total_exposures = (
                    self.db.query(func.sum(Sponsorship.total_exposures))
                    .filter(Sponsorship.org_id == org_id)
                    .scalar()
                    or 0
                )

                # 更新累积积分
                total_points = (
                    self.db.query(func.sum(Sponsorship.total_points_earned))
                    .filter(Sponsorship.org_id == org_id)
                    .scalar()
                    or 0.0
                )

                organization.total_brand_exposures = int(total_exposures)
                organization.accumulated_points = float(total_points)

                self.db.commit()

        except Exception as e:
            logger.error(f"更新组织统计数据失败: {str(e)}")
            self.db.rollback()

    def _clear_sponsorship_cache(self, sponsorship_id: int):
        """清除赞助活动相关缓存"""
        keys_to_delete = [
            f"{self.cache_prefix}sponsorship:{sponsorship_id}",
            f"{self.cache_prefix}analytics:*",  # 清除所有分析缓存
        ]

        for key_pattern in keys_to_delete:
            # Redis删除操作
            redis_client.delete(key_pattern)

    def _clear_organization_cache(self, org_id: int):
        """清除组织相关缓存"""
        keys_to_delete = [
            f"{self.cache_prefix}analytics:{org_id}:*",
            f"{self.cache_prefix}organization:{org_id}",
        ]

        for key_pattern in keys_to_delete:
            # Redis删除操作
            redis_client.delete(key_pattern)


# 工厂函数
def get_sponsorship_service(db: Session) -> SponsorshipService:
    """获取赞助服务实例"""
    return SponsorshipService(db)
