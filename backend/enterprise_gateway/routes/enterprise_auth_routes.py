"""
企业认证路由
提供OAuth2.0企业认证相关的API端点
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.enterprise_models import (
    EnterpriseClientCreate,
    EnterpriseClientUpdate,
    OAuthTokenRequest,
    OAuthTokenResponse,
)
from services.enterprise_oauth_service import enterprise_oauth_service
from utils.database import get_db

router = APIRouter()


@router.post("/oauth/token", response_model=OAuthTokenResponse)
async def oauth_token(token_request: OAuthTokenRequest, db: Session = Depends(get_db)):
    """
    OAuth2.0令牌端点
    支持client_credentials和refresh_token授权类型

    Args:
        token_request: 令牌请求对象
        db: 数据库会话

    Returns:
        OAuth2.0令牌响应
    """
    try:
        token_response = enterprise_oauth_service.exchange_token(token_request, db)

        if not token_response:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client credentials",
            )

        return token_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token exchange failed: {str(e)}",
        )


@router.post("/oauth/revoke")
async def oauth_revoke(token: str, client_id: str, db: Session = Depends(get_db)):
    """
    OAuth2.0令牌撤销端点

    Args:
        token: 要撤销的令牌
        client_id: 客户端ID
        db: 数据库会话

    Returns:
        撤销结果
    """
    try:
        success = enterprise_oauth_service.revoke_token(token, client_id, db)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token revocation failed",
            )

        return {"success": True, "message": "Token revoked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token revocation error: {str(e)}",
        )


@router.get("/oauth/introspect")
async def oauth_introspect(token: str, db: Session = Depends(get_db)):
    """
    OAuth2.0令牌内省端点

    Args:
        token: 要内省的令牌
        db: 数据库会话

    Returns:
        令牌信息
    """
    try:
        token_info = enterprise_oauth_service.introspect_token(token)

        if not token_info:
            return {"active": False}

        return token_info

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token introspection failed: {str(e)}",
        )


@router.post("/clients", response_model=dict)
async def create_enterprise_client(
    client_data: EnterpriseClientCreate,
    current_client_id: str = Depends(lambda: "admin_client"),  # 简化实现
    db: Session = Depends(get_db),
):
    """
    创建企业客户端

    Args:
        client_data: 客户端创建数据
        current_client_id: 当前操作的客户端ID
        db: 数据库会话

    Returns:
        创建的客户端信息
    """
    try:
        client = enterprise_oauth_service.create_enterprise_client(
            client_name=client_data.client_name,
            redirect_uris=client_data.redirect_uris,
            api_quota_limit=client_data.api_quota_limit,
            contact_email=client_data.contact_email,
            company_info=client_data.company_info,
            db=db,
        )

        # 返回客户端信息（不包含密钥）
        return {
            "success": True,
            "message": "Enterprise client created successfully",
            "client_info": {
                "id": client.id,
                "client_name": client.client_name,
                "client_id": client.client_id,
                "redirect_uris": client.redirect_uris,
                "is_active": client.is_active,
                "api_quota_limit": client.api_quota_limit,
                "contact_email": client.contact_email,
                "created_at": (
                    client.created_at.isoformat() if client.created_at else None
                ),
            },
            "credentials": {
                "client_id": client.client_id,
                "client_secret": "********",  # 不在响应中返回实际密钥
            },
            "next_steps": [
                "Store the client credentials securely",
                "Use the client_id and client_secret to obtain access tokens",
                "Configure your application to use the enterprise API gateway",
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create enterprise client: {str(e)}",
        )


@router.get("/clients/{client_id}", response_model=dict)
async def get_client_info(client_id: str, db: Session = Depends(get_db)):
    """
    获取客户端信息

    Args:
        client_id: 客户端ID
        db: 数据库会话

    Returns:
        客户端信息
    """
    try:
        client_info = enterprise_oauth_service.get_client_info(client_id, db)

        if not client_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )

        return client_info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client info: {str(e)}",
        )


@router.put("/clients/{client_id}", response_model=dict)
async def update_client(
    client_id: str,
    update_data: EnterpriseClientUpdate,
    current_client_id: str = Depends(lambda: "admin_client"),  # 简化实现
    db: Session = Depends(get_db),
):
    """
    更新客户端信息

    Args:
        client_id: 客户端ID
        update_data: 更新数据
        current_client_id: 当前操作的客户端ID
        db: 数据库会话

    Returns:
        更新结果
    """
    try:
        # 这里应该实现客户端更新逻辑
        # 为简化起见，只实现配额更新

        if update_data.api_quota_limit is not None:
            success = enterprise_oauth_service.update_client_quota(
                client_id, update_data.api_quota_limit, db
            )

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
                )

        return {"success": True, "message": "Client updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client: {str(e)}",
        )


@router.get("/oauth/.well-known/openid-configuration")
async def openid_configuration():
    """
    OpenID Connect发现文档
    提供OAuth2.0/OpenID Connect配置信息

    Returns:
        OpenID Connect配置信息
    """
    return {
        "issuer": "https://enterprise.api.imato.com",
        "authorization_endpoint": "https://enterprise.api.imato.com/api/enterprise/oauth/authorize",
        "token_endpoint": "https://enterprise.api.imato.com/api/enterprise/oauth/token",
        "revocation_endpoint": "https://enterprise.api.imato.com/api/enterprise/oauth/revoke",
        "introspection_endpoint": "https://enterprise.api.imato.com/api/enterprise/oauth/introspect",
        "response_types_supported": ["code", "token"],
        "grant_types_supported": ["client_credentials", "refresh_token"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_basic",
            "client_secret_post",
        ],
        "scopes_supported": ["api:read", "api:write", "api:admin"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "token_endpoint_auth_signing_alg_values_supported": ["RS256"],
    }
