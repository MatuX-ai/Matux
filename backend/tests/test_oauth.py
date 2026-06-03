"""
OAuth 认证服务测试

覆盖以下测试场景：
1. 授权 URL 生成
2. code 交换令牌
3. 用户信息获取
4. 完整登录流程
5. 账户绑定与管理
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models.oauth_account import OAuthAccount, OAuthProvider
from services.oauth_service import OAuthService


@pytest.fixture
def oauth_service():
    """OAuth 服务实例"""
    return OAuthService()


class TestOAuthAuthorize:
    """测试 OAuth 授权 URL 生成"""

    def test_github_authorize_url(self, oauth_service):
        """测试 GitHub 授权 URL 生成"""
        url = oauth_service.get_authorize_url(
            provider="github",
            redirect_uri="http://localhost:4200/auth/callback",
            state="test_state_123",
        )
        assert "github.com" in url
        assert "client_id" in url
        assert "redirect_uri" in url
        assert "state=test_state_123" in url
        assert "scope=user%3Aemail" in url

    def test_google_authorize_url(self, oauth_service):
        """测试 Google 授权 URL 生成"""
        url = oauth_service.get_authorize_url(
            provider="google",
            redirect_uri="http://localhost:4200/auth/callback",
            state="test_state_456",
        )
        assert "accounts.google.com" in url
        assert "response_type=code" in url
        assert "openid" in url

    def test_invalid_provider(self, oauth_service):
        """测试不支持的提供商"""
        with pytest.raises(ValueError, match="不支持的 OAuth 提供商"):
            oauth_service.get_authorize_url(
                provider="invalid",
                redirect_uri="http://localhost:4200/auth/callback",
            )


class TestOAuthCallback:
    """测试 OAuth 回调处理"""

    @patch("services.oauth_service.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_github_callback_flow(self, mock_httpx, oauth_service):
        """测试完整的 GitHub OAuth 登录流程"""
        # Mock HTTP 响应
        mock_client = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value = mock_client

        # Mock token 交换
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {
            "access_token": "gho_test_token",
            "token_type": "bearer",
            "scope": "user:email",
        }
        mock_token_response.text = '{"access_token":"gho_test_token"}'

        # Mock 用户信息
        mock_user_response = MagicMock()
        mock_user_response.json.return_value = {
            "id": 12345,
            "login": "testuser",
            "email": "test@example.com",
            "avatar_url": "https://avatars.githubusercontent.com/u/12345",
        }

        # 设置 mock 返回顺序
        mock_client.post.return_value = mock_token_response
        mock_client.request.return_value = mock_user_response

        # Mock 数据库 session
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        # 执行回调
        result = await oauth_service.oauth_login(
            db=mock_db,
            provider="github",
            code="test_code",
            redirect_uri="http://localhost:4200/auth/callback",
        )

        assert result["token_type"] == "bearer"
        assert result["user"]["username"] == "testuser"

    @patch("services.oauth_service.httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_wechat_callback_flow(self, mock_httpx, oauth_service):
        """测试微信扫码登录流程"""
        mock_client = AsyncMock()
        mock_httpx.return_value.__aenter__.return_value = mock_client

        # Mock token 响应
        mock_token_response = MagicMock()
        mock_token_response.json.return_value = {
            "access_token": "wechat_token",
            "openid": "o_abc123",
            "expires_in": 7200,
        }
        mock_token_response.text = '{"access_token":"wechat_token","openid":"o_abc123"}'

        # Mock 用户信息
        mock_user_response = MagicMock()
        mock_user_response.json.return_value = {
            "openid": "o_abc123",
            "nickname": "微信用户",
            "headimgurl": "https://wx.qlogo.cn/mmopen/vi_32/abc",
            "sex": 1,
        }

        mock_client.post.return_value = mock_token_response
        mock_client.request.return_value = mock_user_response

        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        mock_db.execute.return_value.scalars.return_value.all.return_value = []

        result = await oauth_service.oauth_login(
            db=mock_db,
            provider="wechat",
            code="wechat_code",
            redirect_uri="http://localhost:4200/auth/callback",
        )

        assert result["token_type"] == "bearer"
        assert result["user"]["username"] == "微信用户"


class TestOAuthBind:
    """测试 OAuth 账号绑定"""

    @pytest.mark.asyncio
    async def test_bind_oauth_account(self, oauth_service):
        """测试绑定第三方账号"""
        mock_db = AsyncMock()

        # Mock 查询返回 None（未绑定）
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        with patch("services.oauth_service.httpx.AsyncClient") as mock_httpx:
            mock_client = AsyncMock()
            mock_httpx.return_value.__aenter__.return_value = mock_client

            mock_token_response = MagicMock()
            mock_token_response.json.return_value = {"access_token": "test_token"}
            mock_token_response.text = '{"access_token":"test_token"}'

            mock_user_response = MagicMock()
            mock_user_response.json.return_value = {
                "id": 999,
                "login": "bind_user",
                "email": "bind@example.com",
            }

            mock_client.post.return_value = mock_token_response
            mock_client.request.return_value = mock_user_response

            account = await oauth_service.bind_oauth_account(
                db=mock_db,
                user_id=1,
                provider="github",
                code="bind_code",
                redirect_uri="http://localhost:4200/auth/callback",
            )

            assert account.user_id == 1
            assert account.provider == OAuthProvider.GITHUB
            assert account.provider_username == "bind_user"

    @pytest.mark.asyncio
    async def test_unbind_oauth_account(self, oauth_service):
        """测试解绑第三方账号"""
        mock_db = AsyncMock()

        # Mock 存在绑定记录
        mock_account = MagicMock(spec=OAuthAccount)
        mock_account.id = 1
        mock_account.user_id = 1
        mock_account.is_active = True
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_account

        result = await oauth_service.unbind_oauth_account(
            db=mock_db, user_id=1, oauth_account_id=1
        )

        assert result is True
        assert mock_account.is_active is False
        mock_db.commit.assert_called_once()


class TestUserInfoNormalization:
    """测试用户信息标准化"""

    def test_github_normalization(self, oauth_service):
        """测试 GitHub 用户信息标准化"""
        raw = {"id": 123, "login": "github_user", "email": "github@test.com", "avatar_url": "https://avatars.com/1"}
        token_data = {"access_token": "token"}

        result = oauth_service._normalize_user_info("github", raw, token_data)

        assert result["provider"] == "github"
        assert result["provider_account_id"] == "123"
        assert result["username"] == "github_user"
        assert result["email"] == "github@test.com"

    def test_google_normalization(self, oauth_service):
        """测试 Google 用户信息标准化"""
        raw = {"id": "google_abc", "name": "Google User", "email": "google@gmail.com", "picture": "https://pic.com/1"}
        token_data = {"access_token": "token"}

        result = oauth_service._normalize_user_info("google", raw, token_data)

        assert result["provider"] == "google"
        assert result["provider_account_id"] == "google_abc"
        assert result["username"] == "Google User"
        assert result["email"] == "google@gmail.com"

    def test_wechat_normalization(self, oauth_service):
        """测试微信用户信息标准化"""
        raw = {"openid": "wx_openid", "nickname": "微信用户", "headimgurl": "https://wx.com/1"}
        token_data = {"openid": "wx_openid", "access_token": "token"}

        result = oauth_service._normalize_user_info("wechat", raw, token_data)

        assert result["provider"] == "wechat"
        assert result["provider_account_id"] == "wx_openid"
        assert result["username"] == "微信用户"
        assert result["email"] == ""  # 微信不返回 email
