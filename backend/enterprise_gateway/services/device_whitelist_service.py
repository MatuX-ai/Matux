"""
设备白名单服务
管理企业客户的设备访问权限
"""

from datetime import datetime, timedelta
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from config.enterprise_settings import enterprise_settings
from models.enterprise_models import (
    DeviceApprovalRequest,
    DeviceWhitelist,
    DeviceWhitelistUpdate,
    EnterpriseClient,
)
from utils.database import get_db
from utils.security_utils import SecurityUtil

logger = logging.getLogger(__name__)


class DeviceWhitelistService:
    """设备白名单服务类"""

    def __init__(self):
        self.security_util = SecurityUtil()

    def add_device_to_whitelist(
        self,
        device_request: DeviceApprovalRequest,
        approved_by: int = None,
        db: Session = None,
    ) -> DeviceWhitelist:
        """
        将设备添加到白名单

        Args:
            device_request: 设备审批请求
            approved_by: 审批人ID
            db: 数据库会话

        Returns:
            创建的设备白名单记录
        """
        if db is None:
            db = next(get_db())

        try:
            # 验证企业客户是否存在
            client = (
                db.query(EnterpriseClient)
                .filter(
                    EnterpriseClient.id == device_request.enterprise_client_id,
                    EnterpriseClient.is_active == True,
                )
                .first()
            )

            if not client:
                raise ValueError(
                    f"Enterprise client not found or inactive: {device_request.enterprise_client_id}"
                )

            # 验证IP地址格式
            if (
                device_request.ip_address
                and not self.security_util.validate_ip_address(
                    device_request.ip_address
                )
            ):
                raise ValueError(
                    f"Invalid IP address format: {device_request.ip_address}"
                )

            # 验证MAC地址格式
            if (
                device_request.mac_address
                and not self.security_util.validate_mac_address(
                    device_request.mac_address
                )
            ):
                raise ValueError(
                    f"Invalid MAC address format: {device_request.mac_address}"
                )

            # 设置过期时间
            approval_period = (
                device_request.approval_period_days
                or enterprise_settings.DEFAULT_DEVICE_APPROVAL_PERIOD_DAYS
            )
            expires_at = datetime.utcnow() + timedelta(days=approval_period)

            # 创建设备白名单记录
            device = DeviceWhitelist(
                enterprise_client_id=device_request.enterprise_client_id,
                device_id=device_request.device_id,
                device_name=device_request.device_name,
                ip_address=device_request.ip_address,
                mac_address=device_request.mac_address,
                user_agent=device_request.user_agent,
                is_approved=True,  # 默认批准
                approved_by=approved_by,
                approved_at=datetime.utcnow(),
                expires_at=expires_at,
            )

            # 保存到数据库
            db.add(device)
            db.commit()
            db.refresh(device)

            logger.info(
                f"Added device {device_request.device_id} to whitelist for client {device_request.enterprise_client_id}"
            )

            return device

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add device to whitelist: {str(e)}")
            raise

    def is_device_approved(
        self, client_id: str, device_id: str, db: Session = None
    ) -> bool:
        """
        检查设备是否在白名单中且已批准

        Args:
            client_id: 企业客户端ID
            device_id: 设备ID
            db: 数据库会话

        Returns:
            设备是否已批准
        """
        if db is None:
            db = next(get_db())

        try:
            # 查询设备白名单记录
            device = (
                db.query(DeviceWhitelist)
                .join(EnterpriseClient)
                .filter(
                    EnterpriseClient.client_id == client_id,
                    DeviceWhitelist.device_id == device_id,
                )
                .first()
            )

            if not device:
                logger.debug(
                    f"Device {device_id} not found in whitelist for client {client_id}"
                )
                return False

            # 检查是否已批准且未过期
            return device.is_valid()

        except Exception as e:
            logger.error(f"Error checking device approval: {str(e)}")
            return False

    def get_client_devices(
        self, client_id: str, include_expired: bool = False, db: Session = None
    ) -> List[DeviceWhitelist]:
        """
        获取企业客户的所有设备

        Args:
            client_id: 企业客户端ID
            include_expired: 是否包含已过期设备
            db: 数据库会话

        Returns:
            设备列表
        """
        if db is None:
            db = next(get_db())

        try:
            query = (
                db.query(DeviceWhitelist)
                .join(EnterpriseClient)
                .filter(EnterpriseClient.client_id == client_id)
            )

            if not include_expired:
                # 只返回有效设备
                query = query.filter(
                    DeviceWhitelist.is_approved == True,
                    (DeviceWhitelist.expires_at.is_(None))
                    | (DeviceWhitelist.expires_at > datetime.utcnow()),
                )

            devices = query.all()
            return devices

        except Exception as e:
            logger.error(f"Error getting client devices: {str(e)}")
            return []

    def update_device_approval(
        self,
        device_id: int,
        update_data: DeviceWhitelistUpdate,
        approved_by: int = None,
        db: Session = None,
    ) -> Optional[DeviceWhitelist]:
        """
        更新设备审批状态

        Args:
            device_id: 设备ID
            update_data: 更新数据
            approved_by: 审批人ID
            db: 数据库会话

        Returns:
            更新后的设备记录，如果设备不存在返回None
        """
        if db is None:
            db = next(get_db())

        try:
            device = (
                db.query(DeviceWhitelist)
                .filter(DeviceWhitelist.id == device_id)
                .first()
            )

            if not device:
                return None

            # 更新字段
            if update_data.device_name is not None:
                device.device_name = update_data.device_name

            if update_data.is_approved is not None:
                device.is_approved = update_data.is_approved
                if update_data.is_approved:
                    device.approved_by = approved_by
                    device.approved_at = datetime.utcnow()
                else:
                    device.approved_by = None
                    device.approved_at = None

            if update_data.expires_at is not None:
                device.expires_at = update_data.expires_at

            db.commit()
            db.refresh(device)

            logger.info(f"Updated device approval status for device ID {device_id}")

            return device

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating device approval: {str(e)}")
            return None

    def remove_device_from_whitelist(self, device_id: int, db: Session = None) -> bool:
        """
        从白名单中移除设备

        Args:
            device_id: 设备ID
            db: 数据库会话

        Returns:
            移除是否成功
        """
        if db is None:
            db = next(get_db())

        try:
            device = (
                db.query(DeviceWhitelist)
                .filter(DeviceWhitelist.id == device_id)
                .first()
            )

            if not device:
                return False

            db.delete(device)
            db.commit()

            logger.info(f"Removed device ID {device_id} from whitelist")

            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error removing device from whitelist: {str(e)}")
            return False

    def generate_device_id(self, ip_address: str, user_agent: str) -> str:
        """
        生成设备唯一标识

        Args:
            ip_address: IP地址
            user_agent: 用户代理

        Returns:
            设备ID
        """
        return self.security_util.generate_device_fingerprint(ip_address, user_agent)

    def get_device_by_id(
        self, device_id: int, db: Session = None
    ) -> Optional[DeviceWhitelist]:
        """
        根据ID获取设备信息

        Args:
            device_id: 设备ID
            db: 数据库会话

        Returns:
            设备记录，如果不存在返回None
        """
        if db is None:
            db = next(get_db())

        try:
            device = (
                db.query(DeviceWhitelist)
                .filter(DeviceWhitelist.id == device_id)
                .first()
            )

            return device

        except Exception as e:
            logger.error(f"Error getting device by ID: {str(e)}")
            return None

    def cleanup_expired_devices(self, db: Session = None) -> int:
        """
        清理已过期的设备记录

        Args:
            db: 数据库会话

        Returns:
            清理的设备数量
        """
        if db is None:
            db = next(get_db())

        try:
            expired_devices = (
                db.query(DeviceWhitelist)
                .filter(DeviceWhitelist.expires_at < datetime.utcnow())
                .all()
            )

            count = len(expired_devices)

            for device in expired_devices:
                db.delete(device)

            db.commit()

            logger.info(f"Cleaned up {count} expired devices from whitelist")

            return count

        except Exception as e:
            db.rollback()
            logger.error(f"Error cleaning up expired devices: {str(e)}")
            return 0


# 创建全局服务实例
device_whitelist_service = DeviceWhitelistService()
