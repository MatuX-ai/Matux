"""
租户配置管理API路由（已解耦存根）
提供租户级别配置、功能开关和资源配额管理功能

⚠️ 多租户配置功能已解耦至 OpenMTEduInst 项目
- 此路由保留作为兼容性存根，新功能请在 OpenMTEduInst 中开发
- MatuX 不再需要多租户管理功能
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


@router.get("/health")
async def health():
    return {
        "status": "decoupled",
        "message": "多租户配置已解耦至 OpenMTEduInst 项目"
    }