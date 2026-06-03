"""
OAuth Service - 第三方登录集成服务

支持 GitHub/Google/WeChat/QQ 四种 OAuth 2.0 提供商
实现授权码模式（Authorization Code Grant）的完整流程：
1. 生成授权 URL（前端跳转）
2. 接收回调 code，通过 code 换取 access_token
3. 通过 access_token 获取用户信息
4. 查找或创建本地用户
"""

import json
import secrets
from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from models.oauth_account import OAuthAccount, OAuthProvider
from models.user import User, UserRole
from modules.auth.auth_service import (
    UnifiedAuthService,
    create_access_token,
    create_refresh_token,
    hash_password,
)


class OAuthProviderConfig:
    """OAuth 提供商配置"""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        authorize_url: str,
        token_url: str,
        userinfo_url: str,
        scopes: list[str],
        userinfo_method: str = "GET",
        userinfo_headers: Optional[dict] = None,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.authorize_url = authorize_url
        self.token_url = token_url
        self.userinfo_url = userinfo_url
        self.scopes = scopes
        self.userinfo_method = userinfo_method
        self.userinfo_headers = userinfo_headers or {}


class OAuthService:
    """OAuth 认证服务"""

    # ============ 提供商配置 ============

    @staticmethod
    def _get_provider_config(provider: str) -> OAuthProviderConfig:
        """获取提供商配置（优先使用环境变量，否则使用默认值）"""
        configs = {
            "github": OAuthProviderConfig(
                client_id=settings.GITHUB_CLIENT_ID,
                client_secret=settings.GITHUB_CLIENT_SECRET,
                authorize_url="https://github.com/login/oauth/authorize",
                token_url="https://github.com/login/oauth/access_token",
                userinfo_url="https://api.github.com/user",
                scopes=["user:email"],
            ),
            "google": OAuthProviderConfig(
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
                scopes=["openid", "email", "profile"],
            ),
            "wechat": OAuthProviderConfig(
                client_id=settings.WECHAT_APP_ID,
                client_secret=settings.WECHAT_APP_SECRET,
                authorize_url="https://open.weixin.qq.com/connect/qrconnect",
                token_url="https://api.weixin.qq.com/sns/oauth2/access_token",
                userinfo_url="https://api.weixin.qq.com/sns/userinfo",
                scopes=["snsapi_login"],
                userinfo_method="GET",
                userinfo_headers={"Accept": "application/json"},
            ),
            "qq": OAuthProviderConfig(
                client_id=settings.QQ_APP_ID,
                client_secret=settings.QQ_APP_KEY,
                authorize_url="https://graph.qq.com/oauth2.0/authorize",
                token_url="https://graph.qq.com/oauth2.0/token",
                userinfo_url="https://graph.qq.com/user/get_user_info",
                scopes=["get_user_info"],
                userinfo_method="GET",
            ),
        }
        if provider not in configs:
            raise ValueError(f"不支持的 OAuth 提供商: {provider}")
        return configs[provider]

    # ============ 步骤1: 生成授权 URL ============

    def get_authorize_url(
        self, provider: str, redirect_uri: str, state: Optional[str] = None
    ) -> str:
        """生成 OAuth 授权 URL（前端跳转使用）"""
        config = self._get_provider_config(provider)
        state = state or secrets.token_urlsafe(32)

        params = {
            "client_id": config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(config.scopes),
            "state": state,
        }

        # 微信需要额外参数
        if provider == "wechat":
            params["appid"] = config.client_id
            params.pop("client_id")

        base_url = config.authorize_url
        return f"{base_url}?{urlencode(params)}"

    # ============ 步骤2: code 交换 access_token ============

    async def _exchange_code_for_token(
        self, provider: str, code: str, redirect_uri: str
    ) -> dict:
        """用授权码交换访问令牌"""
        config = self._get_provider_config(provider)

        data = {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }

        # 微信使用 appid/secret 而非 client_id/client_secret
        if provider == "wechat":
            data["appid"] = config.client_id
            data["secret"] = config.client_secret
            data.pop("client_id")
            data.pop("client_secret")

        async with httpx.AsyncClient(timeout=30.0) as client:
            # GitHub 返回格式特殊
            if provider == "github":
                headers = {"Accept": "application/json"}
                resp = await client.post(config.token_url, json=data, headers=headers)
            elif provider == "qq":
                # QQ 返回 query string 格式
                resp = await client.post(config.token_url, data=data)
                content = resp.text
                # 尝试解析 query string
                if "access_token" in content:
                    # 检查是否有 callback 包装
                    if "callback" in content:
                        import re
                        match = re.search(r'\((.+)\)', content)
                        if match:
                            content = match.group(1)
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(content)
                    return {k: v[0] for k, v in parsed.items()}
                return json.loads(content) if content else {}
            else:
                resp = await client.post(config.token_url, data=data)

            token_data = resp.json() if resp.text else {}

            # 错误处理
            if "error" in token_data:
                raise ValueError(
                    f"OAuth token exchange failed: {token_data.get('error_description', token_data['error'])}"
                )

            return token_data

    # ============ 步骤3: 获取用户信息 ============

    async def _get_user_info(self, provider: str, token_data: dict) -> dict:
        """通过访问令牌获取用户信息"""
        config = self._get_provider_config(provider)
        access_token = token_data.get("access_token", "")

        if not access_token:
            raise ValueError("Access token not found in token response")

        headers = {"Authorization": f"Bearer {access_token}"}
        headers.update(config.userinfo_headers)

        params = {}
        # 微信需要额外参数
        if provider == "wechat":
            params["access_token"] = access_token
            params["openid"] = token_data.get("openid", "")
        # QQ 需要额外参数
        elif provider == "qq":
            params["access_token"] = access_token
            params["oauth_consumer_key"] = config.client_id
            params["openid"] = token_data.get("openid", "")

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method=config.userinfo_method,
                url=config.userinfo_url,
                headers=headers,
                params=params if params else None,
            )
            user_info = resp.json() if resp.text else {}

            # 标准化用户信息字段
            return self._normalize_user_info(provider, user_info, token_data)

    @staticmethod
    def _normalize_user_info(provider: str, raw: dict, token_data: dict) -> dict:
        """将各提供商返回的用户信息标准化为统一格式"""
        normalized = {
            "provider": provider,
            "provider_account_id": "",
            "username": "",
            "email": "",
            "avatar_url": "",
        }

        if provider == "github":
            # 获取 GitHub 邮箱（需要额外 API 调用）
            normalized["provider_account_id"] = str(raw.get("id", ""))
            normalized["username"] = raw.get("login", "")
            normalized["email"] = raw.get("email", "")
            normalized["avatar_url"] = raw.get("avatar_url", "")

        elif provider == "google":
            normalized["provider_account_id"] = raw.get("id", "")
            normalized["username"] = raw.get("name", "")
            normalized["email"] = raw.get("email", "")
            normalized["avatar_url"] = raw.get("picture", "")

        elif provider == "wechat":
            normalized["provider_account_id"] = raw.get("openid", "")
            normalized["username"] = raw.get("nickname", "")
            normalized["avatar_url"] = raw.get("headimgurl", "")
            # 微信不返回 email

        elif provider == "qq":
            normalized["provider_account_id"] = token_data.get("openid", "")
            normalized["username"] = raw.get("nickname", "")
            normalized["avatar_url"] = raw.get("figureurl_qq_2", raw.get("figureurl_qq_1", ""))

        return normalized

    # ============ 步骤4: 登录/注册流程 ============

    async def oauth_login(
        self,
        db: AsyncSession,
        provider: str,
        code: str,
        redirect_uri: str,
    ) -> dict:
        """完整的 OAuth 登录流程

        1. 用 code 交换 access_token
        2. 获取用户信息
        3. 查找或创建本地用户
        4. 生成 JWT 令牌
        """
        # 验证提供商
        try:
            provider_enum = OAuthProvider(provider)
        except ValueError:
            raise ValueError(f"不支持的 OAuth 提供商: {provider}")

        # 步骤 2: code 交换 token
        token_data = await self._exchange_code_for_token(provider, code, redirect_uri)

        # 步骤 3: 获取用户信息
        user_info = await self._get_user_info(provider, token_data)

        provider_account_id = user_info["provider_account_id"]
        if not provider_account_id:
            raise ValueError("无法获取第三方账户 ID")

        # 步骤 4: 查找已有绑定
        stmt = select(OAuthAccount).filter(
            OAuthAccount.provider == provider_enum,
            OAuthAccount.provider_account_id == provider_account_id,
            OAuthAccount.is_active == True,
        )
        result = await db.execute(stmt)
        oauth_account = result.scalar_one_or_none()

        user: User

        if oauth_account:
            # 已有绑定，更新信息
            user = await self._get_user_by_id(db, oauth_account.user_id)
            if not user:
                raise ValueError("绑定的用户不存在")

            # 更新 OAuth 账户信息
            oauth_account.access_token = token_data.get("access_token", "")
            oauth_account.refresh_token = token_data.get("refresh_token", "")
            oauth_account.provider_username = user_info["username"]
            oauth_account.provider_avatar_url = user_info["avatar_url"]
            oauth_account.provider_email = user_info["email"] or oauth_account.provider_email
            oauth_account.last_login_at = datetime.utcnow()

        else:
            # 无绑定，创建新用户并绑定
            user = await self._find_or_create_user(db, user_info)
            oauth_account = OAuthAccount(
                user_id=user.id,
                provider=provider_enum,
                provider_account_id=provider_account_id,
                provider_username=user_info["username"],
                provider_avatar_url=user_info["avatar_url"],
                provider_email=user_info["email"],
                access_token=token_data.get("access_token", ""),
                refresh_token=token_data.get("refresh_token", ""),
                is_primary=True,
                is_active=True,
                last_login_at=datetime.utcnow(),
            )
            db.add(oauth_account)

        await db.commit()
        await db.refresh(user)
        await db.refresh(oauth_account)

        # 生成 JWT 令牌
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "provider": provider,
            "role": user.role.value if user.role else "user",
        }

        return {
            "access_token": create_access_token(payload),
            "refresh_token": create_refresh_token(payload),
            "token_type": "bearer",
            "user": user.to_dict(),
        }

    async def _get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        stmt = select(User).filter(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def _find_or_create_user(self, db: AsyncSession, user_info: dict) -> User:
        """查找或创建用户"""
        # 优先通过邮箱查找
        email = user_info.get("email")
        if email:
            stmt = select(User).filter(User.email == email)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                return user

        # 创建新用户
        username = user_info.get("username", f"oauth_{user_info['provider_account_id'][:8]}")
        # 确保用户名唯一
        base_username = username
        counter = 0
        while True:
            check_stmt = select(User).filter(User.username == username)
            check_result = await db.execute(check_stmt)
            if not check_result.scalar_one_or_none():
                break
            counter += 1
            username = f"{base_username}_{counter}"

        # 生成随机密码（OAuth 用户不需要密码登录）
        import secrets as sec
        random_password = sec.token_urlsafe(32)

        user = User(
            username=username,
            email=email,
            phone=None,
            hashed_password=hash_password(random_password),
            role=UserRole.STUDENT,
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        await db.flush()
        return user

    # ============ 账户绑定管理 ============

    async def bind_oauth_account(
        self,
        db: AsyncSession,
        user_id: int,
        provider: str,
        code: str,
        redirect_uri: str,
    ) -> OAuthAccount:
        """为已有用户绑定第三方账号"""
        provider_enum = OAuthProvider(provider)
        token_data = await self._exchange_code_for_token(provider, code, redirect_uri)
        user_info = await self._get_user_info(provider, token_data)

        provider_account_id = user_info["provider_account_id"]

        # 检查是否已被其他用户绑定
        stmt = select(OAuthAccount).filter(
            OAuthAccount.provider == provider_enum,
            OAuthAccount.provider_account_id == provider_account_id,
            OAuthAccount.is_active == True,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing and existing.user_id != user_id:
            raise ValueError("该第三方账号已被其他用户绑定")

        # 创建或更新绑定
        if existing:
            existing.access_token = token_data.get("access_token", "")
            existing.refresh_token = token_data.get("refresh_token", "")
            existing.provider_username = user_info["username"]
            existing.provider_avatar_url = user_info["avatar_url"]
            oauth_account = existing
        else:
            oauth_account = OAuthAccount(
                user_id=user_id,
                provider=provider_enum,
                provider_account_id=provider_account_id,
                provider_username=user_info["username"],
                provider_avatar_url=user_info["avatar_url"],
                provider_email=user_info["email"],
                access_token=token_data.get("access_token", ""),
                refresh_token=token_data.get("refresh_token", ""),
                is_active=True,
            )
            db.add(oauth_account)

        await db.commit()
        await db.refresh(oauth_account)
        return oauth_account

    async def unbind_oauth_account(
        self, db: AsyncSession, user_id: int, oauth_account_id: int
    ) -> bool:
        """解绑第三方账号"""
        stmt = select(OAuthAccount).filter(
            OAuthAccount.id == oauth_account_id,
            OAuthAccount.user_id == user_id,
            OAuthAccount.is_active == True,
        )
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        if not account:
            return False

        account.is_active = False
        await db.commit()
        return True

    async def get_user_oauth_accounts(
        self, db: AsyncSession, user_id: int
    ) -> list[dict]:
        """获取用户绑定的所有第三方账号"""
        stmt = select(OAuthAccount).filter(
            OAuthAccount.user_id == user_id,
            OAuthAccount.is_active == True,
        )
        result = await db.execute(stmt)
        accounts = result.scalars().all()
        return [a.to_dict() for a in accounts]


# 全局服务实例
oauth_service = OAuthService()
