"""
企业赞助管理API路由
提供赞助活动管理、品牌曝光统计、积分转换等RESTful API接口
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from middleware.auth import get_current_user
from models.license import Organization
from models.sponsorship import (
    BrandExposure,
    ExposureRecordCreate,
    PointConversionRule,
    Sponsorship,
    SponsorshipCreate,
    SponsorshipResponse,
    SponsorshipStatus,
    SponsorshipUpdate,
)
from models.user import User
from services.sponsorship_service import SponsorshipService, get_sponsorship_service
from utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sponsorship", tags=["企业赞助管理"])


# 依赖注入
def get_sponsorship_service_dependency(
    db: Session = Depends(get_db),
) -> SponsorshipService:
    """获取赞助服务实例"""
    return get_sponsorship_service(db)


def verify_organization_access(
    org_id: int = Path(..., description="组织ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Organization:
    """
    验证用户对组织的访问权限

    Args:
        org_id: 组织ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        Organization: 组织对象

    Raises:
        HTTPException: 权限验证失败
    """
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="组织不存在")

    # 这里应该实现具体的权限验证逻辑
    # 目前简化处理，假设用户可以访问所有组织
    return organization


# 赞助活动管理API


@router.post(
    "/organizations/{org_id}/sponsorships",
    response_model=SponsorshipResponse,
    summary="创建赞助活动",
)
async def create_sponsorship(
    org_id: int = Path(..., description="组织ID"),
    sponsorship_data: SponsorshipCreate = Body(..., description="赞助活动数据"),
    sponsorship_service: SponsorshipService = Depends(
        get_sponsorship_service_dependency
    ),
    organization: Organization = Depends(verify_organization_access),
):
    """
    创建新的赞助活动

    权限要求: 组织管理员或以上权限

    Args:
        org_id: 组织ID
        sponsorship_data: 赞助活动创建数据
        sponsorship_service: 赞助服务实例
        organization: 组织对象

    Returns:
        SponsorshipResponse: 创建的赞助活动

    Raises:
        HTTPException: 创建失败
    """
    try:
        sponsorship = sponsorship_service.create_sponsorship(org_id, sponsorship_data)
        return sponsorship
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建赞助活动失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建赞助活动失败")


@router.get(
    "/organizations/{org_id}/sponsorships",
    response_model=List[SponsorshipResponse],
    summary="获取赞助活动列表",
)
async def list_sponsorships(
    org_id: int = Path(..., description="组织ID"),
    status: Optional[str] = Query(None, description="活动状态筛选"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    sponsorship_service: SponsorshipService = Depends(
        get_sponsorship_service_dependency
    ),
    organization: Organization = Depends(verify_organization_access),
):
    """
    获取组织的赞助活动列表

    支持状态筛选和分页

    Args:
        org_id: 组织ID
        status: 活动状态筛选
        skip: 跳过记录数
        limit: 返回记录数
        sponsorship_service: 赞助服务实例
        organization: 组织对象

    Returns:
        List[SponsorshipResponse]: 赞助活动列表
    """
    try:
        query = sponsorship_service.db.query(Sponsorship).filter(
            Sponsorship.org_id == org_id
        )

        if status:
            query = query.filter(Sponsorship.status == status)

        sponsorships = query.offset(skip).limit(limit).all()
        return sponsorships
    except Exception as e:
        logger.error(f"获取赞助活动列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取赞助活动列表失败")


@router.get(
    "/sponsorships/{sponsorship_id}",
    response_model=SponsorshipResponse,
    summary="获取赞助活动详情",
)
async def get_sponsorship(
    sponsorship_id: int = Path(..., description="赞助活动ID"),
    sponsorship_service: SponsorshipService = Depends(
        get_sponsorship_service_dependency
    ),
    current_user: User = Depends(get_current_user),
):
    """
    获取赞助活动详细信息

    Args:
        sponsorship_id: 赞助活动ID
        sponsorship_service: 赞助服务实例
        current_user: 当前用户

    Returns:
        SponsorshipResponse: 赞助活动详情

    Raises:
        HTTPException: 活动不存在或无权限
    """
    try:
        sponsorship = sponsorship_service.get_sponsorship(sponsorship_id)
        if not sponsorship:
            raise HTTPException(status_code=404, detail="赞助活动不存在")

        # 验证权限
        # 这里应该实现具体的权限检查逻辑
        return sponsorship
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取赞助活动详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取赞助活动详情失败")


@router.put(
    "/sponsorships/{sponsorship_id}",
    response_model=SponsorshipResponse,
    summary="更新赞助活动",
)
async def update_sponsorship(
    sponsorship_id: int = Path(..., description="赞助活动ID"),
    update_data: SponsorshipUpdate = Body(..., description="更新数据"),
    sponsorship_service: SponsorshipService = Depends(
        get_sponsorship_service_dependency
    ),
    current_user: User = Depends(get_current_user),
):
    """
    更新赞助活动信息

    权限要求: 活动创建者或组织管理员

    Args:
        sponsorship_id: 赞助活动ID
        update_data: 更新数据
        sponsorship_service: 赞助服务实例
        current_user: 当前用户

    Returns:
        SponsorshipResponse: 更新后的赞助活动

    Raises:
        HTTPException: 更新失败
    """
    try:
        # 获取原始活动以验证权限
        original_sponsorship = sponsorship_service.get_sponsorship(sponsorship_id)
        if not original_sponsorship:
            raise HTTPException(status_code=404, detail="赞助活动不存在")

        # 验证权限（简化处理）
        sponsorship = sponsorship_service.update_sponsorship(
            sponsorship_id, original_sponsorship.org_id, update_data
        )
        return sponsorship
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新赞助活动失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新赞助活动失败")


# 品牌曝光管理API


@router.post(
    "/sponsorships/{sponsorship_id}/exposures",
    response_model=Dict[str, Any],
    summary="记录品牌曝光",
)
async def record_brand_exposure(
    sponsorship_id: int = Path(..., description="赞助活动ID"),
    exposure_data: ExposureRecordCreate = Body(..., description="曝光数据"),
    sponsorship_service: SponsorshipService = Depends(
        get_sponsorship_service_dependency
    ),
    current_user: User = Depends(get_current_user),
):
    """
    记录品牌曝光数据并计算相应积分

    Args:
        sponsorship_id: 赞助活动ID
        exposure_data: 曝光记录数据
        sponsorship_service: 赞助服务实例
        current_user: 当前用户

    Returns:
        Dict: 曝光记录和积分信息

    Raises:
        HTTPException: 记录失败
    """
    try:
        exposure = sponsorship_service.record_brand_exposure(
            sponsorship_id, exposure_data
        )

        return {
            "exposure_id": exposure.id,
            "points_earned": abs(
                exposure.sponsorship.total_points_earned
                - (
                    exposure.sponsorship.total_points_earned
                    - sponsorship_service._calculate_exposure_points(exposure_data)
                )
            ),
            "message": "品牌曝光记录成功",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"记录品牌曝光失败: {str(e)}")
        raise HTTPException(status_code=500, detail="记录品牌曝光失败")


@router.get(
    "/sponsorships/{sponsorship_id}/exposures",
    response_model=List[Dict[str, Any]],
    summary="获取曝光记录列表",
)
async def list_brand_exposures(
    sponsorship_id: int = Path(..., description="赞助活动ID"),
    exposure_type: Optional[str] = Query(None, description="曝光类型筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回记录数"),
    sponsorship_service: SponsorshipService = Depends(
        get_sponsorship_service_dependency
    ),
    current_user: User = Depends(get_current_user),
):
    """
    获取赞助活动的品牌曝光记录列表

    Args:
        sponsorship_id: 赞助活动ID
        exposure_type: 曝光类型筛选
        start_date: 开始日期
        end_date: 结束日期
        skip: 跳过记录数
        limit: 返回记录数
        sponsorship_service: 赞助服务实例
        current_user: 当前用户

    Returns:
        List[Dict]: 曝光记录列表
    """
    try:
        query = sponsorship_service.db.query(BrandExposure).filter(
            BrandExposure.sponsorship_id == sponsorship_id
        )

        if exposure_type:
            query = query.filter(BrandExposure.exposure_type == exposure_type)

        if start_date:
            query = query.filter(BrandExposure.exposed_at >= start_date)

        if end_date:
            query = query.filter(BrandExposure.exposed_at <= end_date)

        exposures = query.offset(skip).limit(limit).all()

        # 转换为字典格式并添加计算字段
        result = []
        for exp in exposures:
            exp_dict = {
                "id": exp.id,
                "exposure_type": exp.exposure_type,
                "platform": exp.platform,
                "placement": exp.placement,
                "view_count": exp.view_count,
                "click_count": exp.click_count,
                "ctr": exp.ctr,
                "engagement_rate": exp.engagement_rate,
                "exposed_at": exp.exposed_at.isoformat(),
            }
            result.append(exp_dict)

        return result
    except Exception as e:
        logger.error(f"获取曝光记录列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取曝光记录列表失败")


# 积分管理API


@router.get(
    "/sponsorships/{sponsorship_id}/points/balance",
    response_model=Dict[str, float],
    summary="获取积分余额",
)
async def get_points_balance(
    sponsorship_id: int = Path(..., description="赞助活动ID"),
    sponsorship_service: SponsorshipService = Depends(
        get_sponsorship_service_dependency
    ),
    current_user: User = Depends(get_current_user),
):
    """
    获取赞助活动的当前积分余额

    Args:
        sponsorship_id: 赞助活动ID
        sponsorship_service: 赞助服务实例
        current_user: 当前用户

    Returns:
        Dict: 积分余额信息
    """
    try:
        balance = sponsorship_service.get_available_points(sponsorship_id)
        return {"available_points": balance}
    except Exception as e:
        logger.error(f"获取积分余额失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取积分余额失败")


@router.get(
    "/points/conversion-rules",
    response_model=List[Dict[str, Any]],
    summary="获取积分转换规则",
)
async def list_conversion_rules(
    is_active: Optional[bool] = Query(True, description="是否仅显示激活规则"),
    category: Optional[str] = Query(None, description="适用类别筛选"),
    db: Session = Depends(get_db),
):
    """
    获取可用的积分转换规则列表

    Args:
        is_active: 是否仅显示激活规则
        category: 适用类别筛选
        db: 数据库会话

    Returns:
        List[Dict]: 转换规则列表
    """
    try:
        query = db.query(PointConversionRule)

        if is_active is not None:
            query = query.filter(PointConversionRule.is_active == is_active)

        if category:
            query = query.filter(
                PointConversionRule.applicable_categories.contains([category])
            )

        rules = query.all()

        result = []
        for rule in rules:
            rule_dict = {
                "id": rule.id,
                "name": rule.name,
                "points_required": rule.points_required,
                "reward_type": rule.reward_type,
                "reward_value": rule.reward_value,
                "min_sponsorship_amount": rule.min_sponsorship_amount,
                "validity_period_days": rule.validity_period_days,
                "is_active": rule.is_active,
            }
            result.append(rule_dict)

        return result
    except Exception as e:
        logger.error(f"获取转换规则失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取转换规则失败")


@router.post(
    "/sponsorships/{sponsorship_id}/points/convert",
    response_model=Dict[str, Any],
    summary="转换积分",
)
async def convert_points(
    sponsorship_id: int = Path(..., description="赞助活动ID"),
    rule_id: int = Body(..., embed=True, description="转换规则ID"),
    quantity: int = Body(1, ge=1, le=10, description="转换数量"),
    sponsorship_service: SponsorshipService = Depends(
        get_sponsorship_service_dependency
    ),
    current_user: User = Depends(get_current_user),
):
    """
    将积分转换为指定奖励

    Args:
        sponsorship_id: 赞助活动ID
        rule_id: 转换规则ID
        quantity: 转换数量
        sponsorship_service: 赞助服务实例
        current_user: 当前用户

    Returns:
        Dict: 转换结果

    Raises:
        HTTPException: 转换失败
    """
    try:
        transactions = sponsorship_service.convert_points(
            sponsorship_id, rule_id, quantity
        )

        return {
            "success": True,
            "transactions_count": len(transactions),
            "message": f"成功转换 {quantity} 次积分",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"积分转换失败: {str(e)}")
        raise HTTPException(status_code=500, detail="积分转换失败")


# 分析报表API


@router.get(
    "/organizations/{org_id}/analytics",
    response_model=Dict[str, Any],
    summary="获取赞助分析数据",
)
async def get_sponsorship_analytics(
    org_id: int = Path(..., description="组织ID"),
    start_date: Optional[datetime] = Query(None, description="分析开始日期"),
    end_date: Optional[datetime] = Query(None, description="分析结束日期"),
    sponsorship_service: SponsorshipService = Depends(
        get_sponsorship_service_dependency
    ),
    organization: Organization = Depends(verify_organization_access),
):
    """
    获取组织赞助活动的综合分析数据

    包括：总体统计、趋势分析、表现排名等

    Args:
        org_id: 组织ID
        start_date: 分析开始日期
        end_date: 分析结束日期
        sponsorship_service: 赞助服务实例
        organization: 组织对象

    Returns:
        Dict: 分析数据
    """
    try:
        analytics_data = sponsorship_service.get_sponsorship_analytics(
            org_id, start_date, end_date
        )
        return analytics_data
    except Exception as e:
        logger.error(f"获取分析数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取分析数据失败")


@router.get(
    "/organizations/{org_id}/dashboard",
    response_model=Dict[str, Any],
    summary="获取仪表板数据",
)
async def get_dashboard_data(
    org_id: int = Path(..., description="组织ID"),
    days: int = Query(30, ge=1, le=365, description="数据天数"),
    sponsorship_service: SponsorshipService = Depends(
        get_sponsorship_service_dependency
    ),
    organization: Organization = Depends(verify_organization_access),
):
    """
    获取组织赞助管理仪表板的汇总数据

    Args:
        org_id: 组织ID
        days: 数据天数
        sponsorship_service: 赞助服务实例
        organization: 组织对象

    Returns:
        Dict: 仪表板数据
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 获取关键指标
        sponsorships = (
            sponsorship_service.db.query(Sponsorship)
            .filter(Sponsorship.org_id == org_id)
            .all()
        )

        total_sponsorship = sum(s.sponsor_amount for s in sponsorships)
        active_count = len(
            [s for s in sponsorships if s.status == SponsorshipStatus.ACTIVE.value]
        )
        total_exposures = sum(s.total_exposures for s in sponsorships)
        available_points = sum(
            sponsorship_service.get_available_points(s.id) for s in sponsorships
        )

        # 获取最近的曝光数据
        recent_exposures = (
            sponsorship_service.db.query(BrandExposure)
            .join(Sponsorship)
            .filter(
                and_(
                    Sponsorship.org_id == org_id, BrandExposure.exposed_at >= start_date
                )
            )
            .count()
        )

        dashboard_data = {
            "summary": {
                "total_sponsorships": len(sponsorships),
                "active_sponsorships": active_count,
                "total_sponsorship_amount": total_sponsorship,
                "total_exposures": total_exposures,
                "recent_exposures": recent_exposures,
                "available_points": available_points,
            },
            "recent_activities": [],  # 可以扩展为最近活动列表
            "trends": {},  # 可以扩展为趋势数据
        }

        return dashboard_data
    except Exception as e:
        logger.error(f"获取仪表板数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取仪表板数据失败")
