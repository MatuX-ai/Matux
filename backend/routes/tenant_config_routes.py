"""
租户配置管理API路由
提供租户级别配置、功能开关和资源配额管理功能
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from middleware.tenant_middleware import require_tenant_access
from models.tenant_config import (
    FeatureFlagCreate,
    FeatureFlagResponse,
    FeatureFlagUpdate,
    ResourceQuotaResponse,
    TenantConfigCreate,
    TenantConfigResponse,
    TenantConfigUpdate,
)
from models.user import User
from services.tenant_config_service import TenantConfigService
from utils.auth_utils import get_current_user_sync
from utils.database import get_sync_db

logger = logging.getLogger(__name__)

# 创建路由器实例
router = APIRouter(prefix="/api/v1/org/{org_id}/config", tags=["租户配置管理"])


# 依赖项
def get_config_service(db: Session = Depends(get_sync_db)) -> TenantConfigService:
    """获取配置服务实例"""
    return TenantConfigService(db)


def validate_org_access(
    org_id: int = Path(..., description="组织ID"),
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
) -> bool:
    """验证用户对组织的访问权限"""
    return require_tenant_access(org_id, current_user, db)


# 租户配置管理API
@router.post("/initialize", summary="初始化租户配置")
def initialize_tenant_configs(
    org_id: int = Path(..., description="组织ID"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    为指定组织初始化默认配置
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        success = config_service.initialize_tenant_configs(org_id)
        if not success:
            raise HTTPException(status_code=500, detail="初始化租户配置失败")

        return {"message": "租户配置初始化成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"初始化租户配置失败: {e}")
        raise HTTPException(status_code=500, detail=f"初始化租户配置失败: {str(e)}")


@router.get("/overview", summary="获取租户配置概览")
def get_tenant_overview(
    org_id: int = Path(..., description="组织ID"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    获取指定组织的配置概览信息
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        overview = config_service.get_tenant_overview(org_id)
        return overview
    except Exception as e:
        logger.error(f"获取租户配置概览失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取租户配置概览失败: {str(e)}")


# 配置项管理API
@router.post("/configs", response_model=TenantConfigResponse, summary="创建配置项")
def create_tenant_config(
    org_id: int = Path(..., description="组织ID"),
    config_data: TenantConfigCreate = Body(..., description="配置数据"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    为指定组织创建配置项
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        config = config_service.create_tenant_config(org_id, config_data, current_user)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建配置项失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建配置项失败: {str(e)}")


@router.get(
    "/configs", response_model=List[TenantConfigResponse], summary="获取配置项列表"
)
def list_tenant_configs(
    org_id: int = Path(..., description="组织ID"),
    category: Optional[str] = Query(None, description="配置分类筛选"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    获取指定组织的配置项列表
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        configs = config_service.get_tenant_configs(org_id, category)
        return configs
    except Exception as e:
        logger.error(f"获取配置项列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置项列表失败: {str(e)}")


@router.get(
    "/configs/{config_key}",
    response_model=TenantConfigResponse,
    summary="获取配置项详情",
)
def get_tenant_config(
    org_id: int = Path(..., description="组织ID"),
    config_key: str = Path(..., description="配置键"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    获取指定配置项的详细信息
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        config = config_service.get_tenant_config(org_id, config_key)
        if not config:
            raise HTTPException(status_code=404, detail="配置项不存在")

        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取配置项详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取配置项详情失败: {str(e)}")


@router.put(
    "/configs/{config_key}", response_model=TenantConfigResponse, summary="更新配置项"
)
def update_tenant_config(
    org_id: int = Path(..., description="组织ID"),
    config_key: str = Path(..., description="配置键"),
    config_update: TenantConfigUpdate = Body(..., description="配置更新数据"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    更新指定配置项
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        config = config_service.update_tenant_config(
            org_id, config_key, config_update, current_user
        )
        if not config:
            raise HTTPException(status_code=404, detail="配置项不存在")

        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新配置项失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置项失败: {str(e)}")


@router.delete("/configs/{config_key}", summary="删除配置项")
def delete_tenant_config(
    org_id: int = Path(..., description="组织ID"),
    config_key: str = Path(..., description="配置键"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    删除指定配置项
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        success = config_service.delete_tenant_config(org_id, config_key, current_user)
        if not success:
            raise HTTPException(status_code=404, detail="配置项不存在或删除失败")

        return {"message": "配置项删除成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除配置项失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除配置项失败: {str(e)}")


# 功能开关管理API
@router.post("/features", response_model=FeatureFlagResponse, summary="创建功能开关")
def create_feature_flag(
    org_id: int = Path(..., description="组织ID"),
    feature_data: FeatureFlagCreate = Body(..., description="功能开关数据"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    为指定组织创建功能开关
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        feature_flag = config_service.create_feature_flag(
            org_id, feature_data, current_user
        )
        return feature_flag
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建功能开关失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建功能开关失败: {str(e)}")


@router.get(
    "/features", response_model=List[FeatureFlagResponse], summary="获取功能开关列表"
)
def list_feature_flags(
    org_id: int = Path(..., description="组织ID"),
    enabled_only: bool = Query(False, description="是否只返回启用的功能"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    获取指定组织的功能开关列表
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        feature_flags = config_service.get_feature_flags(org_id, enabled_only)
        return feature_flags
    except Exception as e:
        logger.error(f"获取功能开关列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取功能开关列表失败: {str(e)}")


@router.get(
    "/features/{feature_name}",
    response_model=FeatureFlagResponse,
    summary="获取功能开关详情",
)
def get_feature_flag(
    org_id: int = Path(..., description="组织ID"),
    feature_name: str = Path(..., description="功能名称"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    获取指定功能开关的详细信息
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        feature_flag = config_service.get_feature_flag(org_id, feature_name)
        if not feature_flag:
            raise HTTPException(status_code=404, detail="功能开关不存在")

        return feature_flag
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取功能开关详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取功能开关详情失败: {str(e)}")


@router.put(
    "/features/{feature_name}",
    response_model=FeatureFlagResponse,
    summary="更新功能开关",
)
def update_feature_flag(
    org_id: int = Path(..., description="组织ID"),
    feature_name: str = Path(..., description="功能名称"),
    feature_update: FeatureFlagUpdate = Body(..., description="功能开关更新数据"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    更新指定功能开关
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        feature_flag = config_service.update_feature_flag(
            org_id, feature_name, feature_update, current_user
        )
        if not feature_flag:
            raise HTTPException(status_code=404, detail="功能开关不存在")

        return feature_flag
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新功能开关失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新功能开关失败: {str(e)}")


@router.get("/features/{feature_name}/status", summary="检查功能是否启用")
def check_feature_status(
    org_id: int = Path(..., description="组织ID"),
    feature_name: str = Path(..., description="功能名称"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    检查指定功能是否启用
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        is_enabled = config_service.is_feature_enabled(org_id, feature_name)
        return {"feature_name": feature_name, "enabled": is_enabled}
    except Exception as e:
        logger.error(f"检查功能状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查功能状态失败: {str(e)}")


# 资源配额管理API
@router.get(
    "/quotas", response_model=List[ResourceQuotaResponse], summary="获取资源配额列表"
)
def list_resource_quotas(
    org_id: int = Path(..., description="组织ID"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    获取指定组织的资源配额列表
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        quotas = config_service.get_resource_quotas(org_id)
        return quotas
    except Exception as e:
        logger.error(f"获取资源配额列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取资源配额列表失败: {str(e)}")


@router.get(
    "/quotas/{resource_type}",
    response_model=ResourceQuotaResponse,
    summary="获取资源配额详情",
)
def get_resource_quota(
    org_id: int = Path(..., description="组织ID"),
    resource_type: str = Path(..., description="资源类型"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    获取指定资源配额的详细信息
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        quota = config_service.get_resource_quota(org_id, resource_type)
        if not quota:
            raise HTTPException(status_code=404, detail="资源配额不存在")

        return quota
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取资源配额详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取资源配额详情失败: {str(e)}")


@router.get("/quotas/{resource_type}/availability", summary="检查资源可用性")
def check_resource_availability(
    org_id: int = Path(..., description="组织ID"),
    resource_type: str = Path(..., description="资源类型"),
    amount: int = Query(1, ge=1, description="请求的数量"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    检查指定资源的可用性
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        availability = config_service.check_resource_availability(
            org_id, resource_type, amount
        )
        return availability
    except Exception as e:
        logger.error(f"检查资源可用性失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查资源可用性失败: {str(e)}")


@router.post("/quotas/{resource_type}/usage", summary="更新资源使用量")
def update_resource_usage(
    org_id: int = Path(..., description="组织ID"),
    resource_type: str = Path(..., description="资源类型"),
    usage_data: dict = Body(..., description="使用量更新数据"),
    current_user: User = Depends(get_current_user_sync),
    config_service: TenantConfigService = Depends(get_config_service),
    db: Session = Depends(get_sync_db),
):
    """
    更新指定资源的使用量
    """
    try:
        # 验证权限
        validate_org_access(org_id, current_user, db)

        amount = usage_data.get("amount", 1)
        operation = usage_data.get("operation", "add")

        if operation not in ["add", "subtract"]:
            raise HTTPException(
                status_code=400, detail="操作类型必须是 'add' 或 'subtract'"
            )

        success = config_service.update_resource_usage(
            org_id, resource_type, amount, operation
        )
        if not success:
            raise HTTPException(status_code=500, detail="更新资源使用量失败")

        return {"message": "资源使用量更新成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新资源使用量失败: {e}")
        raise HTTPException(status_code=500, detail=f"更新资源使用量失败: {str(e)}")
