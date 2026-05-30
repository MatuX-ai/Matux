"""
区块链网关鉴权中间件
提供JWT和OAuth2令牌验证，以及细粒度的权限控制
"""

import logging
from typing import List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from models.user import User, UserRole
from services.permission_service import permission_service
from utils.database import get_db

logger = logging.getLogger(__name__)

# HTTP Bearer安全方案
security = HTTPBearer()


class BlockchainGatewayAuth:
    """区块链网关鉴权类"""

    def __init__(self):
        self.required_scopes = {
            "issue_integral": ["blockchain:write", "education:admin"],
            "query_balance": ["blockchain:read"],
            "query_history": ["blockchain:read"],
            "manage_clients": ["blockchain:admin"],
        }

    async def verify_jwt_token(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        """
        验证JWT令牌并返回用户信息

        Args:
            credentials: HTTP认证凭据
            db: 数据库会话

        Returns:
            User: 认证用户对象

        Raises:
            HTTPException: 认证失败
        """
        try:
            # 解码JWT令牌
            payload = jwt.decode(
                credentials.credentials,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )

            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="无效的认证令牌",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 查询用户信息
            stmt = select(User).filter(
                User.username == username, User.is_active == True
            )
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户不存在或已被禁用",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # 预加载用户权限
            user.permissions = await permission_service.get_user_permissions(
                user.id, db
            )

            return user

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="认证令牌已过期",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"JWT验证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="认证服务暂时不可用",
            )

    async def verify_oauth2_token(
        self, credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict:
        """
        验证OAuth2令牌

        Args:
            credentials: HTTP认证凭据

        Returns:
            dict: 令牌信息

        Raises:
            HTTPException: 认证失败
        """
        try:
            # 解码OAuth2令牌
            payload = jwt.decode(
                credentials.credentials,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )

            # 验证令牌类型
            if payload.get("iss") != "blockchain-gateway":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的令牌发行方"
                )

            # 验证过期时间
            if payload.get("exp", 0) < int(
                jwt.api_jwt.datetime_to_epoch(jwt.api_jwt.datetime.utcnow())
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="OAuth2令牌已过期"
                )

            return {
                "client_id": payload.get("sub"),
                "scope": payload.get("scope", ""),
                "expires_at": payload.get("exp"),
            }

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="OAuth2令牌已过期"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的OAuth2令牌"
            )
        except Exception as e:
            logger.error(f"OAuth2验证失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="认证服务暂时不可用",
            )

    def require_role(self, roles: List[UserRole]):
        """
        角色权限装饰器

        Args:
            roles: 允许的角色列表
        """

        def decorator(func):
            async def wrapper(*args, **kwargs):
                current_user = kwargs.get("current_user")
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="未提供用户信息",
                    )

                if current_user.role not in roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"需要角色之一: {[role.value for role in roles]}",
                    )

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def require_permission(self, permission_code: str):
        """
        权限验证装饰器

        Args:
            permission_code: 权限代码
        """

        def decorator(func):
            async def wrapper(*args, **kwargs):
                current_user = kwargs.get("current_user")
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="未提供用户信息",
                    )

                # 检查用户是否有指定权限
                has_permission = any(
                    perm.code == permission_code for perm in current_user.permissions
                )

                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少权限: {permission_code}",
                    )

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def require_scope(self, required_scopes: List[str]):
        """
        OAuth2作用域验证装饰器

        Args:
            required_scopes: 需要的作用域列表
        """

        def decorator(func):
            async def wrapper(*args, **kwargs):
                token_info = kwargs.get("token_info")
                if not token_info:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="未提供令牌信息",
                    )

                token_scopes = token_info.get("scope", "").split()
                if not any(scope in token_scopes for scope in required_scopes):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"需要作用域之一: {required_scopes}",
                    )

                return await func(*args, **kwargs)

            return wrapper

        return decorator

    async def get_user_role(self, user: User) -> str:
        """
        获取用户角色字符串表示

        Args:
            user: 用户对象

        Returns:
            str: 用户角色
        """
        if user.role == UserRole.ADMIN:
            return "admin"
        elif user.role == UserRole.ORG_ADMIN:
            return "education"
        elif user.role == UserRole.PREMIUM:
            return "premium"
        elif user.role == UserRole.USER:
            return "user"
        else:
            return "guest"


# 全局实例
blockchain_auth = BlockchainGatewayAuth()


# 便捷的依赖函数
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前认证用户"""
    return await blockchain_auth.verify_jwt_token(credentials, db)


async def get_oauth2_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """获取OAuth2客户端信息"""
    return await blockchain_auth.verify_oauth2_token(credentials)


def require_education_role():
    """教育局角色要求"""
    return blockchain_auth.require_role([UserRole.ADMIN, UserRole.ORG_ADMIN])


def require_admin_role():
    """管理员角色要求"""
    return blockchain_auth.require_role([UserRole.ADMIN])


def require_blockchain_write_permission():
    """区块链写入权限要求"""
    return blockchain_auth.require_permission("blockchain:write")


def require_blockchain_read_permission():
    """区块链读取权限要求"""
    return blockchain_auth.require_permission("blockchain:read")


def require_oauth2_scope(scopes: List[str]):
    """OAuth2作用域要求"""
    return blockchain_auth.require_scope(scopes)
