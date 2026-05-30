"""
企业认证服务
整合OAuth2.0认证和设备白名单检查的核心认证逻辑
"""

from datetime import datetime
import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from config.enterprise_settings import enterprise_settings
from models.enterprise_models import EnterpriseAPILog, EnterpriseClient
from services.device_whitelist_service import device_whitelist_service
from services.enterprise_oauth_service import enterprise_oauth_service
from utils.database import get_db
from utils.security_utils import SecurityUtil

logger = logging.getLogger(__name__)


class EnterpriseAuthService:
    """企业认证服务类"""

    def __init__(self):
        self.oauth_service = enterprise_oauth_service
        self.device_service = device_whitelist_service
        self.security_util = SecurityUtil()

    def authenticate_request(
        self,
        authorization_header: str,
        device_id: str = None,
        ip_address: str = None,
        db: Session = None,
    ) -> Optional[Dict[str, Any]]:
        """
        认证API请求

        Args:
            authorization_header: Authorization头
            device_id: 设备ID
            ip_address: IP地址
            db: 数据库会话

        Returns:
            认证结果字典，如果认证失败返回None
        """
        if db is None:
            db = next(get_db())

        try:
            # 1. 提取和验证访问令牌
            if not authorization_header or not authorization_header.startswith(
                "Bearer "
            ):
                logger.warning("Missing or invalid Authorization header")
                return None

            token = authorization_header[7:]  # 移除 "Bearer " 前缀

            # 2. 验证令牌有效性
            token_payload = self.oauth_service.jwt_util.verify_token(token)
            if not token_payload:
                logger.warning("Invalid or expired token")
                return None

            client_id = token_payload.get("client_id")
            if not client_id:
                logger.warning("Token missing client_id")
                return None

            # 3. 验证企业客户端
            client_info = self.oauth_service.get_client_info(client_id, db)
            if not client_info:
                logger.warning(f"Client not found: {client_id}")
                return None

            if not client_info.get("is_active"):
                logger.warning(f"Client inactive: {client_id}")
                return None

            # 4. 检查API配额
            client = (
                db.query(EnterpriseClient)
                .filter(EnterpriseClient.client_id == client_id)
                .first()
            )

            if not client.has_quota_available():
                logger.warning(f"API quota exceeded for client: {client_id}")
                return {
                    "authenticated": False,
                    "reason": "API quota exceeded",
                    "client_id": client_id,
                }

            # 5. 验证设备白名单（如果启用）
            if enterprise_settings.DEVICE_WHITELIST_ENABLED:
                if not device_id:
                    logger.warning(
                        f"Device ID required but not provided for client: {client_id}"
                    )
                    return {
                        "authenticated": False,
                        "reason": "Device ID required",
                        "client_id": client_id,
                    }

                if not self.device_service.is_device_approved(client_id, device_id, db):
                    logger.warning(
                        f"Device not approved: {device_id} for client: {client_id}"
                    )
                    return {
                        "authenticated": False,
                        "reason": "Device not in whitelist",
                        "client_id": client_id,
                        "device_id": device_id,
                    }

            # 6. 认证成功
            logger.info(f"Authentication successful for client: {client_id}")

            return {
                "authenticated": True,
                "client_id": client_id,
                "device_id": device_id,
                "client_info": client_info,
                "token_payload": token_payload,
            }

        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    def log_api_access(
        self,
        client_id: str,
        device_id: str = None,
        request_info: Dict[str, Any] = None,
        response_info: Dict[str, Any] = None,
        db: Session = None,
    ) -> bool:
        """
        记录API访问日志

        Args:
            client_id: 客户端ID
            device_id: 设备ID
            request_info: 请求信息
            response_info: 响应信息
            db: 数据库会话

        Returns:
            日志记录是否成功
        """
        if db is None:
            db = next(get_db())

        try:
            # 创建访问日志记录
            log_entry = EnterpriseAPILog(
                enterprise_client_id=self._get_client_internal_id(client_id, db),
                device_id=device_id,
                api_endpoint=request_info.get("endpoint") if request_info else None,
                http_method=request_info.get("method") if request_info else None,
                status_code=response_info.get("status_code") if response_info else None,
                response_time=(
                    response_info.get("response_time") if response_info else None
                ),
                request_size=request_info.get("request_size") if request_info else None,
                response_size=(
                    response_info.get("response_size") if response_info else None
                ),
                user_agent=request_info.get("user_agent") if request_info else None,
                ip_address=request_info.get("ip_address") if request_info else None,
                timestamp=datetime.utcnow(),
            )

            db.add(log_entry)
            db.commit()

            # 更新客户端使用计数
            client = (
                db.query(EnterpriseClient)
                .filter(EnterpriseClient.client_id == client_id)
                .first()
            )

            if client:
                client.increment_usage()
                db.commit()

            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error logging API access: {str(e)}")
            return False

    def check_quota(self, client_id: str, db: Session = None) -> bool:
        """
        检查客户端API配额

        Args:
            client_id: 客户端ID
            db: 数据库会话

        Returns:
            是否还有配额
        """
        if db is None:
            db = next(get_db())

        try:
            client = (
                db.query(EnterpriseClient)
                .filter(EnterpriseClient.client_id == client_id)
                .first()
            )

            if not client:
                return False

            return client.has_quota_available()

        except Exception as e:
            logger.error(f"Error checking quota: {str(e)}")
            return False

    def get_client_statistics(
        self, client_id: str, days: int = 30, db: Session = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取客户端使用统计

        Args:
            client_id: 客户端ID
            days: 统计天数
            db: 数据库会话

        Returns:
            统计信息字典
        """
        if db is None:
            db = next(get_db())

        try:
            from datetime import timedelta

            # 计算统计时间段
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # 获取客户端信息
            client = (
                db.query(EnterpriseClient)
                .filter(EnterpriseClient.client_id == client_id)
                .first()
            )

            if not client:
                return None

            # 查询访问日志
            logs = (
                db.query(EnterpriseAPILog)
                .filter(
                    EnterpriseAPILog.enterprise_client_id == client.id,
                    EnterpriseAPILog.timestamp >= start_date,
                    EnterpriseAPILog.timestamp <= end_date,
                )
                .all()
            )

            # 计算统计数据
            total_requests = len(logs)
            successful_requests = len(
                [
                    log
                    for log in logs
                    if log.status_code and 200 <= log.status_code < 300
                ]
            )
            failed_requests = total_requests - successful_requests

            success_rate = (
                (successful_requests / total_requests * 100)
                if total_requests > 0
                else 0
            )

            avg_response_time = (
                sum(log.response_time for log in logs if log.response_time)
                / len([log for log in logs if log.response_time])
                if any(log.response_time for log in logs)
                else 0
            )

            total_data = sum(
                (log.request_size or 0) + (log.response_size or 0) for log in logs
            )

            # 获取活跃设备数
            active_devices = len(set(log.device_id for log in logs if log.device_id))

            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": round(success_rate, 2),
                "average_response_time": round(avg_response_time, 2),
                "total_data_transferred": total_data,
                "active_devices": active_devices,
                "current_usage": client.current_usage,
                "quota_limit": client.api_quota_limit,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting client statistics: {str(e)}")
            return None

    def _get_client_internal_id(self, client_id: str, db: Session) -> Optional[int]:
        """
        获取客户端内部ID

        Args:
            client_id: 客户端ID
            db: 数据库会话

        Returns:
            客户端内部ID
        """
        try:
            client = (
                db.query(EnterpriseClient)
                .filter(EnterpriseClient.client_id == client_id)
                .first()
            )

            return client.id if client else None

        except Exception:
            return None


# 创建全局服务实例
enterprise_auth_service = EnterpriseAuthService()
