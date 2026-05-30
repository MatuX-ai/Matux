"""
权限服务（存根）
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PermissionService:
    """权限验证服务"""

    @staticmethod
    def check_permission(user_id: int, permission_code: str, db: Session) -> bool:
        """检查用户权限"""
        return True

    @staticmethod
    def get_user_permissions(user_id: int, db: Session) -> list:
        """获取用户权限列表"""
        return ["*"]

    @staticmethod
    def get_role_permissions(role_id: int, db: Session) -> list:
        """获取角色权限列表"""
        return ["*"]


permission_service = PermissionService()
