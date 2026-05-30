"""
数据访问控制模块
实现多租户环境下的数据隔离和访问控制
"""

import logging
from typing import Any, List, Optional, Type, Union

from fastapi import HTTPException, status
from sqlalchemy.orm import Query

from database.tenant_aware_session import TenantQueryHelper
from models.user import User, UserRole
from utils.tenant_context import TenantContext

logger = logging.getLogger(__name__)


class DataAccessControl:
    """数据访问控制类"""

    @staticmethod
    def filter_by_tenant(query: Query, model_class: Type[Any]) -> Query:
        """
        为查询自动添加租户过滤条件

        Args:
            query: SQLAlchemy查询对象
            model_class: 模型类

        Returns:
            Query: 添加了租户过滤的查询对象
        """
        return TenantQueryHelper.filter_by_tenant(query, model_class)

    @staticmethod
    def validate_tenant_ownership(
        instance: Any, expected_org_id: Optional[int] = None
    ) -> bool:
        """
        验证实例是否属于指定租户

        Args:
            instance: 数据库实例
            expected_org_id: 期望的租户ID，如果为None则使用当前上下文

        Returns:
            bool: 如果属于指定租户返回True，否则返回False

        Raises:
            HTTPException: 如果验证失败
        """
        if not hasattr(instance, "org_id"):
            # 如果实例没有org_id字段，则认为验证通过
            return True

        if expected_org_id is None:
            expected_org_id = TenantContext.get_current_tenant()

        if expected_org_id is None:
            # 没有指定租户ID且上下文也没有，认为验证通过
            return True

        actual_org_id = getattr(instance, "org_id", None)
        is_valid = actual_org_id == expected_org_id

        if not is_valid:
            logger.warning(
                f"租户所有权验证失败: 实例(org_id={actual_org_id}) "
                f"不属于租户({expected_org_id})"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="无权访问此资源"
            )

        return True

    @staticmethod
    def enforce_tenant_isolation(query: Query, user: User) -> Query:
        """
        强制执行租户隔离

        Args:
            query: SQLAlchemy查询对象
            user: 当前用户

        Returns:
            Query: 应用了租户隔离的查询对象
        """
        # 管理员可以访问所有租户的数据
        if user.is_superuser or user.role in [UserRole.ADMIN]:
            return query

        # 获取当前租户
        current_tenant = TenantContext.get_current_tenant()
        if current_tenant is None:
            logger.warning("强制租户隔离时未设置租户上下文")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="缺少租户上下文"
            )

        # 为查询添加租户过滤
        return TenantQueryHelper.apply_tenant_filters_to_query(query)

    @staticmethod
    def check_create_permission(
        user: User, org_id: int, model_class: Type[Any]
    ) -> bool:
        """
        检查用户是否有创建指定类型资源的权限

        Args:
            user: 用户对象
            org_id: 组织ID
            model_class: 要创建的模型类

        Returns:
            bool: 是否有权限

        Raises:
            HTTPException: 如果没有权限
        """
        # 验证租户上下文
        current_tenant = TenantContext.get_current_tenant()
        if current_tenant != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="租户上下文不匹配"
            )

        # 管理员可以创建所有资源
        if user.is_superuser or user.role in [UserRole.ADMIN, UserRole.ORG_ADMIN]:
            return True

        # 普通用户需要特定权限
        required_permission = f"create_{model_class.__name__.lower()}"
        if not DataAccessControl._has_permission(user, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {required_permission}",
            )

        return True

    @staticmethod
    def check_read_permission(user: User, instance: Any) -> bool:
        """
        检查用户是否有读取指定资源的权限

        Args:
            user: 用户对象
            instance: 要读取的实例

        Returns:
            bool: 是否有权限

        Raises:
            HTTPException: 如果没有权限
        """
        # 验证租户所有权
        DataAccessControl.validate_tenant_ownership(instance)

        # 管理员可以读取所有资源
        if user.is_superuser or user.role in [UserRole.ADMIN, UserRole.ORG_ADMIN]:
            return True

        # 普通用户需要特定权限
        model_name = instance.__class__.__name__.lower()
        required_permission = f"read_{model_name}"

        # 对于某些敏感资源，需要额外权限
        sensitive_models = ["user", "organization", "license"]
        if model_name in sensitive_models:
            required_permission = f"manage_{model_name}"

        if not DataAccessControl._has_permission(user, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {required_permission}",
            )

        return True

    @staticmethod
    def check_update_permission(user: User, instance: Any) -> bool:
        """
        检查用户是否有更新指定资源的权限

        Args:
            user: 用户对象
            instance: 要更新的实例

        Returns:
            bool: 是否有权限

        Raises:
            HTTPException: 如果没有权限
        """
        # 验证租户所有权
        DataAccessControl.validate_tenant_ownership(instance)

        # 管理员可以更新所有资源
        if user.is_superuser or user.role in [UserRole.ADMIN, UserRole.ORG_ADMIN]:
            return True

        # 普通用户需要特定权限
        model_name = instance.__class__.__name__.lower()
        required_permission = f"update_{model_name}"

        # 特殊情况：用户可以更新自己的信息
        if model_name == "user" and hasattr(instance, "id") and instance.id == user.id:
            return True

        if not DataAccessControl._has_permission(user, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {required_permission}",
            )

        return True

    @staticmethod
    def check_delete_permission(user: User, instance: Any) -> bool:
        """
        检查用户是否有删除指定资源的权限

        Args:
            user: 用户对象
            instance: 要删除的实例

        Returns:
            bool: 是否有权限

        Raises:
            HTTPException: 如果没有权限
        """
        # 验证租户所有权
        DataAccessControl.validate_tenant_ownership(instance)

        # 管理员可以删除所有资源
        if user.is_superuser or user.role in [UserRole.ADMIN, UserRole.ORG_ADMIN]:
            return True

        # 普通用户通常没有删除权限
        model_name = instance.__class__.__name__.lower()
        required_permission = f"delete_{model_name}"

        if not DataAccessControl._has_permission(user, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少权限: {required_permission}",
            )

        return True

    @staticmethod
    def _has_permission(user: User, permission: str) -> bool:
        """
        检查用户是否具有指定权限

        Args:
            user: 用户对象
            permission: 权限名称

        Returns:
            bool: 是否具有权限
        """
        try:
            # 从用户服务获取权限列表
            import asyncio

            from services.user_license_service import user_license_service

            # 注意：这里可能需要异步处理
            # 在实际使用中，应该确保在异步上下文中调用
            loop = asyncio.get_event_loop()
            user_permissions = loop.run_until_complete(
                user_license_service.get_user_permissions(user.id)
            )

            return permission in user_permissions
        except Exception as e:
            logger.error(f"检查用户权限失败: {e}")
            return False

    @staticmethod
    def get_accessible_org_ids(user: User) -> List[int]:
        """
        获取用户可以访问的组织ID列表

        Args:
            user: 用户对象

        Returns:
            List[int]: 可访问的组织ID列表
        """
        try:
            # 管理员可以访问所有组织
            if user.is_superuser or user.role == UserRole.ADMIN:
                # 查询所有活跃组织
                from sqlalchemy import select

                from models.license import Organization
                from utils.database import get_sync_db

                db_gen = get_sync_db()
                db = next(db_gen)

                try:
                    stmt = select(Organization.id).filter(
                        Organization.is_active == True
                    )
                    result = db.execute(stmt)
                    return [row[0] for row in result.fetchall()]
                finally:
                    next(db_gen, None)

            # 企业管理员可以访问自己的组织
            if user.role == UserRole.ORG_ADMIN:
                # 这里需要实现具体的逻辑来获取管理员关联的组织
                # 简化实现：返回空列表
                return []

            # 普通用户通过许可证关联获取可访问组织
            import asyncio

            from services.user_license_service import user_license_service

            loop = asyncio.get_event_loop()
            user_licenses = loop.run_until_complete(
                user_license_service.get_user_active_licenses(user.id)
            )

            org_ids = list(
                {ul.license.organization_id for ul in user_licenses if ul.license}
            )
            return org_ids

        except Exception as e:
            logger.error(f"获取用户可访问组织失败: {e}")
            return []


class DataMasking:
    """数据脱敏类"""

    @staticmethod
    def mask_sensitive_data(
        data: Union[dict, list],
        user: User,
        sensitive_fields: Optional[List[str]] = None,
    ) -> Union[dict, list]:
        """
        对敏感数据进行脱敏处理

        Args:
            data: 要脱敏的数据（字典或列表）
            user: 当前用户
            sensitive_fields: 敏感字段列表

        Returns:
            Union[dict, list]: 脱敏后的数据
        """
        # 管理员可以看到完整数据
        if user.is_superuser or user.role in [UserRole.ADMIN, UserRole.ORG_ADMIN]:
            return data

        # 默认敏感字段
        default_sensitive_fields = [
            "password",
            "hashed_password",
            "secret_key",
            "api_key",
            "private_key",
            "credit_card",
            "ssn",
            "phone_number",
        ]

        fields_to_mask = sensitive_fields or default_sensitive_fields

        if isinstance(data, dict):
            masked_data = data.copy()
            for field in fields_to_mask:
                if field in masked_data:
                    masked_data[field] = DataMasking._mask_value(masked_data[field])
            return masked_data

        elif isinstance(data, list):
            return [
                DataMasking.mask_sensitive_data(item, user, sensitive_fields)
                for item in data
            ]

        return data

    @staticmethod
    def _mask_value(value: Any) -> str:
        """
        对单个值进行脱敏

        Args:
            value: 要脱敏的值

        Returns:
            str: 脱敏后的值
        """
        if value is None:
            return None

        str_value = str(value)
        if len(str_value) <= 4:
            return "*" * len(str_value)
        else:
            # 保留前后各2位，中间用*替代
            return str_value[:2] + "*" * (len(str_value) - 4) + str_value[-2:]


# 便捷函数
def require_tenant_access(model_instance: Any, expected_org_id: Optional[int] = None):
    """验证实例的租户访问权限的便捷函数"""
    return DataAccessControl.validate_tenant_ownership(model_instance, expected_org_id)


def filter_query_by_tenant(query: Query, model_class: Type[Any]) -> Query:
    """为查询添加租户过滤的便捷函数"""
    return DataAccessControl.filter_by_tenant(query, model_class)


def enforce_data_isolation(query: Query, user: User) -> Query:
    """强制数据隔离的便捷函数"""
    return DataAccessControl.enforce_tenant_isolation(query, user)
