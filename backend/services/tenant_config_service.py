"""
租户配置管理服务
处理租户级别配置、功能开关和资源配额管理
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from models.tenant_config import (
    DEFAULT_FEATURE_FLAGS,
    DEFAULT_RESOURCE_QUOTAS,
    DEFAULT_TENANT_CONFIGS,
    FeatureFlagCreate,
    FeatureFlagUpdate,
    TenantConfig,
    TenantConfigCreate,
    TenantConfigUpdate,
    TenantFeatureFlag,
    TenantResourceQuota,
)
from models.user import User, UserRole

logger = logging.getLogger(__name__)


class TenantConfigService:
    """租户配置管理服务类"""

    def __init__(self, db: Session):
        self.db = db

    def initialize_tenant_configs(self, org_id: int) -> bool:
        """
        初始化租户默认配置

        Args:
            org_id: 组织ID

        Returns:
            bool: 是否初始化成功
        """
        try:
            # 检查是否已经初始化
            existing_configs = (
                self.db.query(TenantConfig)
                .filter(TenantConfig.org_id == org_id)
                .count()
            )

            if existing_configs > 0:
                logger.info(f"租户 {org_id} 的配置已存在，跳过初始化")
                return True

            # 创建默认配置
            for category, configs in DEFAULT_TENANT_CONFIGS.items():
                for key, config_data in configs.items():
                    full_key = f"{category}.{key}"
                    config = TenantConfig(
                        org_id=org_id,
                        config_key=full_key,
                        config_value=config_data["value"],
                        config_type=config_data["type"],
                        description=config_data["description"],
                        is_active=True,
                    )
                    self.db.add(config)

            # 创建默认功能开关
            for feature_name, feature_data in DEFAULT_FEATURE_FLAGS.items():
                feature_flag = TenantFeatureFlag(
                    org_id=org_id,
                    feature_name=feature_name,
                    is_enabled=feature_data["enabled"],
                    description=feature_data["description"],
                )
                self.db.add(feature_flag)

            # 创建默认资源配额
            for resource_type, quota_data in DEFAULT_RESOURCE_QUOTAS.items():
                resource_quota = TenantResourceQuota(
                    org_id=org_id,
                    resource_type=resource_type,
                    max_limit=quota_data["max_limit"],
                    warning_threshold=quota_data["warning_threshold"],
                    reset_period=quota_data["reset_period"],
                    is_unlimited=False,
                )
                self.db.add(resource_quota)

            self.db.commit()
            logger.info(f"租户 {org_id} 配置初始化成功")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"初始化租户配置失败: {e}")
            return False

    def get_tenant_config(self, org_id: int, config_key: str) -> Optional[TenantConfig]:
        """
        获取租户配置项

        Args:
            org_id: 组织ID
            config_key: 配置键

        Returns:
            Optional[TenantConfig]: 配置项，如果不存在返回None
        """
        try:
            config = (
                self.db.query(TenantConfig)
                .filter(
                    TenantConfig.org_id == org_id,
                    TenantConfig.config_key == config_key,
                    TenantConfig.is_active == True,
                )
                .first()
            )

            return config
        except Exception as e:
            logger.error(f"获取租户配置失败: {e}")
            return None

    def get_tenant_configs(
        self, org_id: int, category: Optional[str] = None
    ) -> List[TenantConfig]:
        """
        获取租户配置列表

        Args:
            org_id: 组织ID
            category: 配置分类筛选

        Returns:
            List[TenantConfig]: 配置列表
        """
        try:
            query = self.db.query(TenantConfig).filter(
                TenantConfig.org_id == org_id, TenantConfig.is_active == True
            )

            if category:
                query = query.filter(TenantConfig.config_key.like(f"{category}.%"))

            configs = query.order_by(TenantConfig.config_key).all()
            return configs
        except Exception as e:
            logger.error(f"获取租户配置列表失败: {e}")
            return []

    def get_config_value(
        self, org_id: int, config_key: str, default_value: Any = None
    ) -> Any:
        """
        获取配置值（带类型转换）

        Args:
            org_id: 组织ID
            config_key: 配置键
            default_value: 默认值

        Returns:
            Any: 配置值
        """
        config = self.get_tenant_config(org_id, config_key)
        if config:
            return config.get_typed_value()
        return default_value

    def create_tenant_config(
        self, org_id: int, config_data: TenantConfigCreate, current_user: User
    ) -> TenantConfig:
        """
        创建租户配置项

        Args:
            org_id: 组织ID
            config_data: 配置数据
            current_user: 当前用户

        Returns:
            TenantConfig: 创建的配置项
        """
        try:
            # 验证权限
            if not self._can_manage_tenant_config(current_user):
                raise ValueError("无权管理租户配置")

            # 检查配置键是否已存在
            existing_config = (
                self.db.query(TenantConfig)
                .filter(
                    TenantConfig.org_id == org_id,
                    TenantConfig.config_key == config_data.config_key,
                )
                .first()
            )

            if existing_config:
                raise ValueError(f"配置键 '{config_data.config_key}' 已存在")

            # 验证JSON格式（如果是JSON类型）
            if config_data.config_type == "json":
                try:
                    json.loads(config_data.config_value)
                except json.JSONDecodeError:
                    raise ValueError("JSON格式无效")

            # 创建配置项
            config = TenantConfig(
                org_id=org_id,
                config_key=config_data.config_key,
                config_value=config_data.config_value,
                config_type=config_data.config_type,
                description=config_data.description,
                is_active=True,
            )

            self.db.add(config)
            self.db.commit()
            self.db.refresh(config)

            logger.info(f"租户配置创建成功: {org_id} - {config.config_key}")
            return config

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建租户配置失败: {e}")
            raise

    def update_tenant_config(
        self,
        org_id: int,
        config_key: str,
        config_update: TenantConfigUpdate,
        current_user: User,
    ) -> Optional[TenantConfig]:
        """
        更新租户配置项

        Args:
            org_id: 组织ID
            config_key: 配置键
            config_update: 更新数据
            current_user: 当前用户

        Returns:
            Optional[TenantConfig]: 更新后的配置项，如果不存在返回None
        """
        try:
            config = self.get_tenant_config(org_id, config_key)
            if not config:
                return None

            # 验证权限
            if not self._can_manage_tenant_config(current_user):
                raise ValueError("无权管理租户配置")

            # 验证JSON格式（如果更新为JSON类型）
            if config_update.config_type == "json" or (
                config_update.config_type is None and config.config_type == "json"
            ):
                value_to_check = config_update.config_value or config.config_value
                if value_to_check:
                    try:
                        json.loads(value_to_check)
                    except json.JSONDecodeError:
                        raise ValueError("JSON格式无效")

            # 更新字段
            update_data = config_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(config, field):
                    setattr(config, field, value)

            config.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(config)

            logger.info(f"租户配置更新成功: {org_id} - {config.config_key}")
            return config

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新租户配置失败: {e}")
            raise

    def delete_tenant_config(
        self, org_id: int, config_key: str, current_user: User
    ) -> bool:
        """
        删除租户配置项

        Args:
            org_id: 组织ID
            config_key: 配置键
            current_user: 当前用户

        Returns:
            bool: 是否删除成功
        """
        try:
            config = self.get_tenant_config(org_id, config_key)
            if not config:
                return False

            # 验证权限
            if not self._can_manage_tenant_config(current_user):
                raise ValueError("无权管理租户配置")

            # 软删除
            config.is_active = False
            config.updated_at = datetime.utcnow()

            self.db.commit()
            logger.info(f"租户配置删除成功: {org_id} - {config_key}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"删除租户配置失败: {e}")
            return False

    def get_feature_flag(
        self, org_id: int, feature_name: str
    ) -> Optional[TenantFeatureFlag]:
        """
        获取功能开关

        Args:
            org_id: 组织ID
            feature_name: 功能名称

        Returns:
            Optional[TenantFeatureFlag]: 功能开关，如果不存在返回None
        """
        try:
            feature_flag = (
                self.db.query(TenantFeatureFlag)
                .filter(
                    TenantFeatureFlag.org_id == org_id,
                    TenantFeatureFlag.feature_name == feature_name,
                )
                .first()
            )

            return feature_flag
        except Exception as e:
            logger.error(f"获取功能开关失败: {e}")
            return None

    def get_feature_flags(
        self, org_id: int, enabled_only: bool = False
    ) -> List[TenantFeatureFlag]:
        """
        获取功能开关列表

        Args:
            org_id: 组织ID
            enabled_only: 是否只返回启用的功能

        Returns:
            List[TenantFeatureFlag]: 功能开关列表
        """
        try:
            query = self.db.query(TenantFeatureFlag).filter(
                TenantFeatureFlag.org_id == org_id
            )

            if enabled_only:
                query = query.filter(TenantFeatureFlag.is_enabled == True)

            feature_flags = query.order_by(TenantFeatureFlag.feature_name).all()
            return feature_flags
        except Exception as e:
            logger.error(f"获取功能开关列表失败: {e}")
            return []

    def is_feature_enabled(self, org_id: int, feature_name: str) -> bool:
        """
        检查功能是否启用

        Args:
            org_id: 组织ID
            feature_name: 功能名称

        Returns:
            bool: 功能是否启用
        """
        feature_flag = self.get_feature_flag(org_id, feature_name)
        return feature_flag.is_enabled if feature_flag else False

    def update_feature_flag(
        self,
        org_id: int,
        feature_name: str,
        feature_update: FeatureFlagUpdate,
        current_user: User,
    ) -> Optional[TenantFeatureFlag]:
        """
        更新功能开关

        Args:
            org_id: 组织ID
            feature_name: 功能名称
            feature_update: 更新数据
            current_user: 当前用户

        Returns:
            Optional[TenantFeatureFlag]: 更新后的功能开关，如果不存在返回None
        """
        try:
            feature_flag = self.get_feature_flag(org_id, feature_name)
            if not feature_flag:
                # 如果不存在，创建新的功能开关
                feature_create = FeatureFlagCreate(
                    feature_name=feature_name,
                    is_enabled=feature_update.is_enabled or False,
                    config=feature_update.config,
                    description=feature_update.description,
                )
                return self.create_feature_flag(org_id, feature_create, current_user)

            # 验证权限
            if not self._can_manage_tenant_config(current_user):
                raise ValueError("无权管理租户配置")

            # 更新字段
            update_data = feature_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(feature_flag, field):
                    setattr(feature_flag, field, value)

            feature_flag.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(feature_flag)

            logger.info(f"功能开关更新成功: {org_id} - {feature_name}")
            return feature_flag

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新功能开关失败: {e}")
            raise

    def create_feature_flag(
        self, org_id: int, feature_data: FeatureFlagCreate, current_user: User
    ) -> TenantFeatureFlag:
        """
        创建功能开关

        Args:
            org_id: 组织ID
            feature_data: 功能开关数据
            current_user: 当前用户

        Returns:
            TenantFeatureFlag: 创建的功能开关
        """
        try:
            # 验证权限
            if not self._can_manage_tenant_config(current_user):
                raise ValueError("无权管理租户配置")

            # 检查功能开关是否已存在
            existing_flag = self.get_feature_flag(org_id, feature_data.feature_name)
            if existing_flag:
                raise ValueError(f"功能开关 '{feature_data.feature_name}' 已存在")

            # 创建功能开关
            feature_flag = TenantFeatureFlag(
                org_id=org_id,
                feature_name=feature_data.feature_name,
                is_enabled=feature_data.is_enabled,
                config=feature_data.config,
                description=feature_data.description,
            )

            self.db.add(feature_flag)
            self.db.commit()
            self.db.refresh(feature_flag)

            logger.info(f"功能开关创建成功: {org_id} - {feature_flag.feature_name}")
            return feature_flag

        except Exception as e:
            self.db.rollback()
            logger.error(f"创建功能开关失败: {e}")
            raise

    def get_resource_quota(
        self, org_id: int, resource_type: str
    ) -> Optional[TenantResourceQuota]:
        """
        获取资源配额

        Args:
            org_id: 组织ID
            resource_type: 资源类型

        Returns:
            Optional[TenantResourceQuota]: 资源配额，如果不存在返回None
        """
        try:
            quota = (
                self.db.query(TenantResourceQuota)
                .filter(
                    TenantResourceQuota.org_id == org_id,
                    TenantResourceQuota.resource_type == resource_type,
                )
                .first()
            )

            return quota
        except Exception as e:
            logger.error(f"获取资源配额失败: {e}")
            return None

    def get_resource_quotas(self, org_id: int) -> List[TenantResourceQuota]:
        """
        获取资源配额列表

        Args:
            org_id: 组织ID

        Returns:
            List[TenantResourceQuota]: 资源配额列表
        """
        try:
            quotas = (
                self.db.query(TenantResourceQuota)
                .filter(TenantResourceQuota.org_id == org_id)
                .order_by(TenantResourceQuota.resource_type)
                .all()
            )

            return quotas
        except Exception as e:
            logger.error(f"获取资源配额列表失败: {e}")
            return []

    def check_resource_availability(
        self, org_id: int, resource_type: str, requested_amount: int = 1
    ) -> Dict[str, Any]:
        """
        检查资源可用性

        Args:
            org_id: 组织ID
            resource_type: 资源类型
            requested_amount: 请求的数量

        Returns:
            Dict[str, Any]: 检查结果
        """
        try:
            quota = self.get_resource_quota(org_id, resource_type)

            if not quota:
                return {"available": True, "message": "未设置资源配额，默认允许使用"}

            if quota.is_unlimited:
                return {"available": True, "message": "资源无限制"}

            new_usage = quota.current_usage + requested_amount
            available = new_usage <= quota.max_limit

            return {
                "available": available,
                "current_usage": quota.current_usage,
                "requested_amount": requested_amount,
                "new_usage": new_usage,
                "max_limit": quota.max_limit,
                "usage_percentage": quota.usage_percentage,
                "is_over_limit": quota.is_over_limit,
                "message": "资源充足" if available else "资源不足",
            }

        except Exception as e:
            logger.error(f"检查资源可用性失败: {e}")
            return {"available": False, "error": str(e)}

    def update_resource_usage(
        self, org_id: int, resource_type: str, amount: int, operation: str = "add"
    ) -> bool:
        """
        更新资源使用量

        Args:
            org_id: 组织ID
            resource_type: 资源类型
            amount: 数量
            operation: 操作类型 ('add' 或 'subtract')

        Returns:
            bool: 是否更新成功
        """
        try:
            quota = self.get_resource_quota(org_id, resource_type)
            if not quota:
                logger.warning(f"资源配额不存在: {org_id} - {resource_type}")
                return False

            if quota.is_unlimited:
                return True

            if operation == "add":
                quota.current_usage += amount
            elif operation == "subtract":
                quota.current_usage = max(0, quota.current_usage - amount)
            else:
                raise ValueError("操作类型必须是 'add' 或 'subtract'")

            quota.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(
                f"资源使用量更新成功: {org_id} - {resource_type} ({operation} {amount})"
            )
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"更新资源使用量失败: {e}")
            return False

    def get_tenant_overview(self, org_id: int) -> Dict[str, Any]:
        """
        获取租户配置概览

        Args:
            org_id: 组织ID

        Returns:
            Dict[str, Any]: 租户配置概览
        """
        try:
            # 获取配置统计
            total_configs = (
                self.db.query(TenantConfig)
                .filter(TenantConfig.org_id == org_id)
                .count()
            )

            active_configs = (
                self.db.query(TenantConfig)
                .filter(TenantConfig.org_id == org_id, TenantConfig.is_active == True)
                .count()
            )

            # 获取功能开关统计
            total_features = (
                self.db.query(TenantFeatureFlag)
                .filter(TenantFeatureFlag.org_id == org_id)
                .count()
            )

            enabled_features = (
                self.db.query(TenantFeatureFlag)
                .filter(
                    TenantFeatureFlag.org_id == org_id,
                    TenantFeatureFlag.is_enabled == True,
                )
                .count()
            )

            # 获取资源配额统计
            quotas = self.get_resource_quotas(org_id)
            over_limit_quotas = [
                q for q in quotas if q.is_over_limit and not q.is_unlimited
            ]
            warning_quotas = [
                q
                for q in quotas
                if q.is_warning_threshold_reached and not q.is_unlimited
            ]

            return {
                "configs": {"total": total_configs, "active": active_configs},
                "features": {"total": total_features, "enabled": enabled_features},
                "quotas": {
                    "total": len(quotas),
                    "over_limit": len(over_limit_quotas),
                    "warning": len(warning_quotas),
                },
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取租户配置概览失败: {e}")
            return {"error": str(e)}

    def _can_manage_tenant_config(self, user: User) -> bool:
        """检查用户是否有管理租户配置的权限"""
        return user.is_superuser or user.role in [UserRole.ADMIN, UserRole.ORG_ADMIN]
