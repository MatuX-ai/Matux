"""
用户许可证服务（存根）
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class UserLicenseService:
    """用户许可证服务"""

    @staticmethod
    def validate_user_license(user_id: int, db: Session) -> bool:
        """验证用户许可证"""
        return True

    @staticmethod
    def get_user_license(user_id: int, db: Session) -> Optional[dict]:
        """获取用户许可证信息"""
        return {"user_id": user_id, "status": "active"}


user_license_service = UserLicenseService()
