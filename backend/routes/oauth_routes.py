"""
OAuth 认证路由 - 第三方登录

提供 OAuth 2.0 授权码模式的完整 API 端点：
- GET  /oauth/{provider}/authorize - 获取授权 URL
- POST /oauth/{provider}/callback  - 回调处理（code 交换 token）
- GET  /oauth/accounts            - 获取用户绑定的第三方账号
- POST /oauth/{provider}/bind     - 为当前用户绑定第三方账号
- POST /oauth/accounts/{id}/unbind - 解绑第三方账号
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.auth import get_current_user
from models.user import User
from services.oauth_service import oauth_service
from utils.database import get_db

router = APIRouter(prefix="/api/v1/oauth", tags=["OAuth 认证"])


# ============ Request/Response Models ============


class AuthorizeResponse(BaseModel):
    """授权 URL 响应"""
    authorize_url: str
    state: str


class CallbackRequest(BaseModel):
    """OAuth 回调请求"""
    code: str = Field(..., description="授权码")
    state: str = Field(..., description="状态参数（防 CSRF）")
    redirect_uri: str = Field(..., description="回调地址")


class BindRequest(BaseModel):
    """绑定第三方账号请求"""
    code: str = Field(..., description="授权码")
    redirect_uri: str = Field(..., description="回调地址")


class TokenResponse(BaseModel):
    """令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


# ============ API 端点 ============


@router.get("/{provider}/authorize", response_model=AuthorizeResponse, summary="获取 OAuth 授权 URL")
async def get_authorize_url(
    provider: str,
    redirect_uri: str = Query(..., description="回调地址"),
):
    """生成 OAuth 提供商授权 URL，前端跳转到此 URL 进行授权"""
    try:
        state = __import__("secrets").token_urlsafe(32)
        authorize_url = oauth_service.get_authorize_url(
            provider, redirect_uri, state)
        return AuthorizeResponse(authorize_url=authorize_url, state=state)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{provider}/callback", response_model=TokenResponse, summary="OAuth 回调处理")
async def oauth_callback(
    provider: str,
    req: CallbackRequest,
    db: AsyncSession = Depends(get_db),
):
    """处理 OAuth 授权回调

    用授权码交换令牌并登录/注册用户
    前端在收到回调后，将 code 和 state 发送到此端点
    """
    try:
        result = await oauth_service.oauth_login(
            db=db,
            provider=provider,
            code=req.code,
            redirect_uri=req.redirect_uri,
        )
        return TokenResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"OAuth 认证失败: {str(e)}",
        )


@router.post("/{provider}/bind", summary="绑定第三方账号到当前用户")
async def bind_oauth_account(
    provider: str,
    req: BindRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """为当前登录用户绑定第三方账号"""
    try:
        account = await oauth_service.bind_oauth_account(
            db=db,
            user_id=current_user.id,
            provider=provider,
            code=req.code,
            redirect_uri=req.redirect_uri,
        )
        return {"message": "绑定成功", "account": account.to_dict()}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/accounts", summary="获取用户绑定的第三方账号列表")
async def get_oauth_accounts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户绑定的所有第三方账号"""
    accounts = await oauth_service.get_user_oauth_accounts(
        db=db, user_id=current_user.id
    )
    return {"accounts": accounts}


@router.post("/accounts/{account_id}/unbind", summary="解绑第三方账号")
async def unbind_oauth_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """解绑指定的第三方账号"""
    success = await oauth_service.unbind_oauth_account(
        db=db, user_id=current_user.id, oauth_account_id=account_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="未找到该绑定记录",
        )
    return {"message": "解绑成功"}
