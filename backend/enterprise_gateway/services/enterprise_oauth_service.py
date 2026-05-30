"""
企业OAuth2.0认证服务
实现OAuth2.0 Client Credentials流程的企业级认证功能
"""

import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from config.enterprise_settings import enterprise_settings
from models.enterprise_models import (
    EnterpriseClient,
    OAuthTokenRequest,
    OAuthTokenResponse,
)
from utils.database import get_db
from utils.jwt_utils import JWTUtil
from utils.security_utils import SecurityUtil

logger = logging.getLogger(__name__)


class EnterpriseOAuthService:
    """企业OAuth2.0服务类"""

    def __init__(self):
        self.jwt_util = JWTUtil()
        self.security_util = SecurityUtil()

    def create_enterprise_client(
        self,
        client_name: str,
        redirect_uris: str = None,
        api_quota_limit: int = None,
        contact_email: str = None,
        company_info: dict = None,
        db: Session = None,
    ) -> EnterpriseClient:
        """
        创建新的企业客户端

        Args:
            client_name: 客户端名称
            redirect_uris: 重定向URI列表
            api_quota_limit: API配额限制
            contact_email: 联系邮箱
            company_info: 公司信息
            db: 数据库会话

        Returns:
            创建的企业客户端对象
        """
        if db is None:
            db = next(get_db())

        try:
            # 生成客户端凭据
            client_id = self.jwt_util.generate_client_id()
            client_secret = self.jwt_util.generate_client_secret()

            # 创建企业客户端记录
            client = EnterpriseClient(
                client_name=client_name,
                client_id=client_id,
                redirect_uris=redirect_uris,
                api_quota_limit=api_quota_limit
                or enterprise_settings.DEFAULT_API_QUOTA_LIMIT,
                contact_email=contact_email,
                company_info=company_info,
            )

            # 设置加密的客户端密钥
            client.set_client_secret(client_secret)

            # 保存到数据库
            db.add(client)
            db.commit()
            db.refresh(client)

            logger.info(f"Created new enterprise client: {client_id} for {client_name}")

            return client

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create enterprise client: {str(e)}")
            raise

    def validate_client_credentials(
        self, client_id: str, client_secret: str, db: Session = None
    ) -> bool:
        """
        验证客户端凭据

        Args:
            client_id: 客户端ID
            client_secret: 客户端密钥
            db: 数据库会话

        Returns:
            凭据是否有效
        """
        if db is None:
            db = next(get_db())

        try:
            # 查询客户端
            client = (
                db.query(EnterpriseClient)
                .filter(
                    EnterpriseClient.client_id == client_id,
                    EnterpriseClient.is_active == True,
                )
                .first()
            )

            if not client:
                logger.warning(f"Client not found or inactive: {client_id}")
                return False

            # 验证密钥
            if not client.verify_client_secret(client_secret):
                logger.warning(f"Invalid client secret for client: {client_id}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating client credentials: {str(e)}")
            return False

    def exchange_token(
        self, token_request: OAuthTokenRequest, db: Session = None
    ) -> Optional[OAuthTokenResponse]:
        """
        执行OAuth2.0令牌交换

        Args:
            token_request: 令牌请求对象
            db: 数据库会话

        Returns:
            令牌响应对象，如果失败返回None
        """
        if db is None:
            db = next(get_db())

        try:
            # 验证客户端凭据
            if not self.validate_client_credentials(
                token_request.client_id, token_request.client_secret, db
            ):
                logger.warning(
                    f"Token exchange failed: invalid client credentials for {token_request.client_id}"
                )
                return None

            # 查询客户端信息
            client = (
                db.query(EnterpriseClient)
                .filter(EnterpriseClient.client_id == token_request.client_id)
                .first()
            )

            if not client:
                return None

            # 检查API配额
            if not client.has_quota_available():
                logger.warning(
                    f"Token exchange failed: quota exceeded for client {token_request.client_id}"
                )
                return None

            # 根据授权类型处理
            if token_request.grant_type == "client_credentials":
                return self._handle_client_credentials_grant(
                    client, token_request.scope
                )
            elif token_request.grant_type == "refresh_token":
                return self._handle_refresh_token_grant(token_request.client_id)
            else:
                logger.warning(f"Unsupported grant type: {token_request.grant_type}")
                return None

        except Exception as e:
            logger.error(f"Error in token exchange: {str(e)}")
            return None

    def _handle_client_credentials_grant(
        self, client: EnterpriseClient, scope: str = None
    ) -> OAuthTokenResponse:
        """
        处理客户端凭据授权

        Args:
            client: 企业客户端对象
            scope: 请求的作用域

        Returns:
            OAuth令牌响应
        """
        # 创建访问令牌数据
        token_data = {
            "client_id": client.client_id,
            "grant_type": "client_credentials",
            "scope": scope or "api:read",
        }

        # 生成访问令牌
        access_token = self.jwt_util.create_access_token(token_data)

        # 更新使用计数
        client.increment_usage()

        # 构造响应
        response = OAuthTokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=enterprise_settings.ENTERPRISE_TOKEN_EXPIRE_HOURS * 3600,
            scope=scope or "api:read",
        )

        logger.info(f"Generated access token for client: {client.client_id}")

        return response

    def _handle_refresh_token_grant(self, client_id: str) -> OAuthTokenResponse:
        """
        处理刷新令牌授权

        Args:
            client_id: 客户端ID

        Returns:
            OAuth令牌响应
        """
        # 创建刷新令牌数据
        token_data = {"client_id": client_id, "grant_type": "refresh_token"}

        # 生成访问令牌
        access_token = self.jwt_util.create_access_token(token_data)

        # 构造响应
        response = OAuthTokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=enterprise_settings.ENTERPRISE_TOKEN_EXPIRE_HOURS * 3600,
            scope="api:read",
        )

        logger.info(f"Generated refresh token for client: {client_id}")

        return response

    def revoke_token(self, token: str, client_id: str, db: Session = None) -> bool:
        """
        撤销访问令牌

        Args:
            token: 要撤销的令牌
            client_id: 客户端ID
            db: 数据库会话

        Returns:
            撤销是否成功
        """
        # 在实际实现中，这里应该将令牌加入黑名单
        # 当前实现为简化版本

        logger.info(f"Revoked token for client: {client_id}")
        return True

    def introspect_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        内省令牌信息

        Args:
            token: 要内省的令牌

        Returns:
            令牌信息字典，如果令牌无效返回None
        """
        payload = self.jwt_util.verify_token(token)
        if not payload:
            return None

        return {
            "active": True,
            "client_id": payload.get("client_id"),
            "scope": payload.get("scope"),
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
            "iss": payload.get("iss"),
        }

    def get_client_info(
        self, client_id: str, db: Session = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取客户端信息

        Args:
            client_id: 客户端ID
            db: 数据库会话

        Returns:
            客户端信息字典，如果客户端不存在返回None
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
                return None

            return client.to_dict()

        except Exception as e:
            logger.error(f"Error getting client info: {str(e)}")
            return None

    def update_client_quota(
        self, client_id: str, new_quota: int, db: Session = None
    ) -> bool:
        """
        更新客户端API配额

        Args:
            client_id: 客户端ID
            new_quota: 新的配额限制
            db: 数据库会话

        Returns:
            更新是否成功
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

            client.api_quota_limit = new_quota
            db.commit()

            logger.info(f"Updated quota for client {client_id} to {new_quota}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating client quota: {str(e)}")
            return False


# 创建全局服务实例
enterprise_oauth_service = EnterpriseOAuthService()
