"""
租户上下文管理器
用于在多租户环境中管理和传递租户信息
"""

import contextvars
import logging
from typing import Optional, Union

logger = logging.getLogger(__name__)

# 创建上下文变量存储当前租户ID
current_tenant = contextvars.ContextVar("current_tenant", default=None)


class TenantContext:
    """租户上下文管理器类"""

    @staticmethod
    def set_current_tenant(tenant_id: Union[int, str, None]) -> None:
        """
        设置当前租户ID

        Args:
            tenant_id: 租户ID，可以是整数、字符串或None
        """
        if tenant_id is not None:
            # 确保tenant_id是整数类型
            try:
                tenant_id = int(tenant_id)
            except (ValueError, TypeError):
                logger.warning(f"无效的租户ID格式: {tenant_id}")
                tenant_id = None

        current_tenant.set(tenant_id)
        if tenant_id:
            logger.debug(f"设置当前租户为: {tenant_id}")
        else:
            logger.debug("清除当前租户上下文")

    @staticmethod
    def get_current_tenant() -> Optional[int]:
        """
        获取当前租户ID

        Returns:
            Optional[int]: 当前租户ID，如果没有设置则返回None
        """
        tenant_id = current_tenant.get()
        return tenant_id

    @staticmethod
    def clear() -> None:
        """清除当前租户上下文"""
        current_tenant.set(None)
        logger.debug("租户上下文已清除")

    @staticmethod
    def is_tenant_set() -> bool:
        """
        检查是否设置了租户上下文

        Returns:
            bool: 如果设置了租户上下文返回True，否则返回False
        """
        return current_tenant.get() is not None


class TenantContextManager:
    """租户上下文管理器，支持with语句"""

    def __init__(self, tenant_id: Union[int, str, None]):
        self.tenant_id = tenant_id
        self.previous_tenant = None

    def __enter__(self):
        # 保存当前租户
        self.previous_tenant = TenantContext.get_current_tenant()
        # 设置新租户
        TenantContext.set_current_tenant(self.tenant_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 恢复之前的租户
        TenantContext.set_current_tenant(self.previous_tenant)


# 便捷函数
def get_current_tenant() -> Optional[int]:
    """获取当前租户ID的便捷函数"""
    return TenantContext.get_current_tenant()


def set_current_tenant(tenant_id: Union[int, str, None]) -> None:
    """设置当前租户ID的便捷函数"""
    TenantContext.set_current_tenant(tenant_id)


def with_tenant_context(tenant_id: Union[int, str, None]):
    """创建租户上下文管理器的便捷函数"""
    return TenantContextManager(tenant_id)
