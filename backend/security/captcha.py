"""
【P3-E】CAPTCHA 适配器接口与多 Provider 实现

设计：
- CaptchaProvider 抽象基类（verify + get_challenge_url）
- NoopCaptchaProvider（默认，dev 环境）— 接受任何非空 token
- HCaptchaProvider（生产可用）— 调用 hCaptcha verify API
- TencentCaptchaProvider（国内可用）— 腾讯云天御
- RedisCaptchaTokenStore（一次性 token 防重放）

使用：
    from security.captcha import (
        CaptchaProvider,
        get_captcha_provider,
        verify_captcha_token,
    )

    provider = get_captcha_provider()
    if not provider.verify(token=req.captcha_token, ip=request.client.host):
        raise HTTPException(400, "CAPTCHA 验证失败")
"""

import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ==================== Provider 类型 ====================


class CaptchaProviderType(str, Enum):
    """CAPTCHA Provider 类型"""

    NOOP = "noop"  # 开发/测试：接受任何 token
    HCAPTCHA = "hcaptcha"  # hCaptcha（国际）
    TENCENT = "tencent"  # 腾讯云天御（国内）
    RECAPTCHA = "recaptcha"  # Google reCAPTCHA


@dataclass
class CaptchaVerifyResult:
    """CAPTCHA 验证结果"""

    success: bool
    provider: str
    error_codes: list = None
    challenge_ts: Optional[str] = None
    hostname: Optional[str] = None
    raw: Dict[str, Any] = None

    def __post_init__(self):
        if self.error_codes is None:
            self.error_codes = []
        if self.raw is None:
            self.raw = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "provider": self.provider,
            "error_codes": self.error_codes,
            "challenge_ts": self.challenge_ts,
            "hostname": self.hostname,
        }


# ==================== 抽象基类 ====================


class CaptchaProvider(ABC):
    """CAPTCHA Provider 抽象基类"""

    @abstractmethod
    def verify(
        self,
        token: str,
        ip: str = "",
        **kwargs,
    ) -> CaptchaVerifyResult:
        """
        验证 CAPTCHA token

        Args:
            token: 客户端提交的一次性 CAPTCHA 凭证
            ip: 客户端 IP（用于风控日志）

        Returns:
            CaptchaVerifyResult（success=False 表示验证失败）
        """
        ...

    def get_site_key(self) -> Optional[str]:
        """前端 site_key（用于渲染 CAPTCHA widget）"""
        return None

    def get_provider_name(self) -> str:
        """Provider 名称"""
        return self.__class__.__name__


# ==================== No-op Provider（默认）====================


class NoopCaptchaProvider(CaptchaProvider):
    """
    开发 / 测试用 CAPTCHA Provider

    - 接受任何非空 token
    - 不发起任何外部请求
    - 生产环境切勿使用
    """

    def verify(self, token: str, ip: str = "", **kwargs) -> CaptchaVerifyResult:
        # 仅校验非空；可设置 prefix "valid-" 才视为通过
        prefix = kwargs.get("noop_prefix", "valid-")
        if not token:
            return CaptchaVerifyResult(
                success=False,
                provider="noop",
                error_codes=["missing-input-response"],
            )
        if not token.startswith(prefix):
            return CaptchaVerifyResult(
                success=True,  # 仍然放行，仅警告
                provider="noop",
                error_codes=["noop-warning"],
                raw={"warning": f"expected prefix {prefix!r}"},
            )
        return CaptchaVerifyResult(
            success=True,
            provider="noop",
            challenge_ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )


# ==================== hCaptcha Provider ====================


class HCaptchaProvider(CaptchaProvider):
    """
    hCaptcha Provider

    配置：
        CAPTCHA_HCAPTCHA_SECRET: hCaptcha 后端密钥
        CAPTCHA_HCAPTCHA_SITE_KEY: 前端 site_key

    接口文档：https://docs.hcaptcha.com/
    验证 endpoint: https://api.hcaptcha.com/siteverify
    """

    VERIFY_URL = "https://api.hcaptcha.com/siteverify"

    def __init__(self, secret: str, site_key: Optional[str] = None):
        self._secret = secret
        self._site_key = site_key

    def get_site_key(self) -> Optional[str]:
        return self._site_key

    def get_provider_name(self) -> str:
        return "hcaptcha"

    def verify(self, token: str, ip: str = "", **kwargs) -> CaptchaVerifyResult:
        if not token:
            return CaptchaVerifyResult(
                success=False,
                provider="hcaptcha",
                error_codes=["missing-input-response"],
            )
        try:
            import urllib.request
            import urllib.parse

            data = urllib.parse.urlencode(
                {"secret": self._secret, "response": token, "remoteip": ip}
            ).encode()
            req = urllib.request.Request(
                self.VERIFY_URL,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                raw = json.loads(resp.read().decode())

            success = bool(raw.get("success"))
            return CaptchaVerifyResult(
                success=success,
                provider="hcaptcha",
                error_codes=raw.get("error-codes", []),
                challenge_ts=raw.get("challenge_ts"),
                hostname=raw.get("hostname"),
                raw=raw,
            )
        except Exception as e:
            logger.warning(f"hCaptcha verify error: {e}")
            return CaptchaVerifyResult(
                success=False,
                provider="hcaptcha",
                error_codes=["network-error"],
            )


# ==================== Google reCAPTCHA Provider ====================


class ReCaptchaProvider(HCaptchaProvider):
    """Google reCAPTCHA v3（继承 hCaptcha 的接口模式）"""

    VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"

    def get_provider_name(self) -> str:
        return "recaptcha"


# ==================== 腾讯云天御 Provider ====================


class TencentCaptchaProvider(CaptchaProvider):
    """
    腾讯云天御 CAPTCHA

    底层调用腾讯云 API 3.0：DescribeCaptchaResult
    实现位置：security.tencent_captcha_sdk.TencentCloudCaptchaClient

    配置：
        CAPTCHA_TENCENT_SECRET_ID / SECRET_KEY
        CAPTCHA_TENCENT_CAPTCHA_APP_ID

    使用：
        # 方式 A：传 ticket + randstr（原始腾讯云字段）
        provider.verify(
            token="ignored",
            ip="1.2.3.4",
            ticket="t_xxx",
            randstr="@xxx",
        )

        # 方式 B：传 JSON 字符串 {"ticket": "...", "randstr": "..."}
        provider.verify(token=json.dumps({...}), ip="1.2.3.4")

        # 方式 C：传 t:R 格式（仅供调试）
        provider.verify(token="t_xxx:@xxx", ip="1.2.3.4")
    """

    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        captcha_app_id: str,
        captcha_type: int = 9,
        client: Optional[Any] = None,
    ):
        self._secret_id = secret_id
        self._secret_key = secret_key
        self._captcha_app_id = captcha_app_id
        self._captcha_type = captcha_type
        # 可注入自定义 client（用于测试）
        self._client = client
        self._client_lock = None
        self._init_client_lock()

    def _init_client_lock(self) -> None:
        import threading

        if self._client_lock is None:
            self._client_lock = threading.Lock()

    @property
    def client(self):
        """懒加载 SDK client"""
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    from security.tencent_captcha_sdk import (
                        TencentCloudCaptchaClient,
                    )

                    self._client = TencentCloudCaptchaClient(
                        secret_id=self._secret_id,
                        secret_key=self._secret_key,
                        captcha_app_id=self._captcha_app_id,
                    )
        return self._client

    def get_provider_name(self) -> str:
        return "tencent"

    def get_site_key(self) -> Optional[str]:
        """腾讯云验证码不需要前端 site_key（widget 端初始化在不同层面）"""
        return self._captcha_app_id

    def verify(self, token: str, ip: str = "", **kwargs) -> CaptchaVerifyResult:
        """
        验证腾讯云 CAPTCHA 票据

        Args:
            token: 票据传递（三种方式见类 docstring）
            ip: 用户 IP
            **kwargs: 支持 ticket / randstr / captcha_type
        """
        from security.tencent_captcha_sdk import TencentCloudAPIError

        ticket, randstr = self._extract_ticket_randstr(token, kwargs)
        if not ticket or not randstr:
            return CaptchaVerifyResult(
                success=False,
                provider="tencent",
                error_codes=["missing-ticket-or-randstr"],
            )

        captcha_type = int(
            kwargs.get("captcha_type", self._captcha_type)
        )
        try:
            response = self.client.describe_captcha_result(
                ticket=ticket,
                randstr=randstr,
                user_ip=ip or "0.0.0.0",
                captcha_type=captcha_type,
            )
        except TencentCloudAPIError as e:
            logger.warning(f"Tencent CAPTCHA 调用失败: {e}")
            return CaptchaVerifyResult(
                success=False,
                provider="tencent",
                error_codes=[e.code or "api-error"],
                raw={"error": e.message, "code": e.code},
            )
        except Exception as e:
            logger.exception(f"Tencent CAPTCHA 异常: {e}")
            return CaptchaVerifyResult(
                success=False,
                provider="tencent",
                error_codes=["internal-error"],
                raw={"error": str(e)},
            )

        if "Response" not in response:
            return CaptchaVerifyResult(
                success=False,
                provider="tencent",
                error_codes=["malformed-response"],
                raw=response,
            )

        response_data = response["Response"]
        if "Error" in response_data:
            err = response_data["Error"]
            return CaptchaVerifyResult(
                success=False,
                provider="tencent",
                error_codes=[err.get("Code", "unknown-error")],
                raw=response,
            )

        captcha_code = response_data.get("CaptchaCode", -1)
        success = captcha_code == 1
        error_codes = (
            [] if success
            else [self.client._map_captcha_code_to_error(captcha_code)]
        )
        return CaptchaVerifyResult(
            success=success,
            provider="tencent",
            error_codes=error_codes,
            challenge_ts=time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
            ),
            raw=response,
        )

    @staticmethod
    def _extract_ticket_randstr(
        token: str, kwargs: Dict[str, Any]
    ) -> tuple:
        """从 token/kwargs 提取 (ticket, randstr)"""
        # 优先 kwargs
        if "ticket" in kwargs and "randstr" in kwargs:
            return kwargs["ticket"], kwargs["randstr"]

        # 尝试 JSON
        if token and token.strip().startswith("{"):
            try:
                obj = json.loads(token)
                if "ticket" in obj and "randstr" in obj:
                    return obj["ticket"], obj["randstr"]
            except (json.JSONDecodeError, KeyError):
                pass

        # 尝试 t:R 分隔格式
        if token and ":" in token:
            parts = token.split(":", 1)
            if len(parts) == 2:
                return parts[0], parts[1]

        return "", ""


# ==================== Token Store（防重放）====================


class CaptchaTokenStore:
    """
    一次性 CAPTCHA Token 存储（防重放）

    流程：
    1. 前端调用 /api/v1/captcha/challenge 获取 challenge_id
    2. 用户在 CAPTCHA widget 中完成验证，获得 token
    3. 前端发起原始请求（带 token）
    4. 后端调用 verify_captcha_token(token) 检查 token 是否已使用

    可选存储：
    - 内存 dict（默认，单进程）
    - Redis（跨进程，防伪更强）
    """

    def __init__(self, ttl_seconds: int = 300):
        """token TTL 默认 5 分钟"""
        self._used_tokens: Dict[str, float] = {}
        self._ttl_seconds = ttl_seconds

    def is_used(self, token: str) -> bool:
        """检查 token 是否已被使用 / 已过期"""
        if not token:
            return True  # 空 token 视为"无效"
        used_at = self._used_tokens.get(token)
        if used_at is None:
            return False
        if time.time() - used_at > self._ttl_seconds:
            # 过期 token 可以复用（实际上应该再次被 CAPTCHA 拦截）
            self._used_tokens.pop(token, None)
            return False
        return True

    def mark_used(self, token: str) -> None:
        """标记 token 已被使用"""
        self._used_tokens[token] = time.time()

    def cleanup_expired(self) -> int:
        """清理过期 token"""
        now = time.time()
        expired = [
            t for t, ts in self._used_tokens.items()
            if now - ts > self._ttl_seconds
        ]
        for t in expired:
            self._used_tokens.pop(t, None)
        return len(expired)

    def generate_challenge_id(self) -> str:
        """生成挑战 ID（前端 widget）"""
        return f"challenge-{uuid.uuid4().hex[:16]}"


_token_store: Optional[CaptchaTokenStore] = None


def get_token_store() -> CaptchaTokenStore:
    """获取全局 token store"""
    global _token_store
    if _token_store is None:
        _token_store = CaptchaTokenStore()
    return _token_store


def reset_token_store_for_testing() -> None:
    global _token_store
    _token_store = None


# ==================== Provider 工厂 ====================


_provider: Optional[CaptchaProvider] = None
_provider_type: CaptchaProviderType = CaptchaProviderType.NOOP


def configure_captcha(
    provider_type: CaptchaProviderType,
    **kwargs,
) -> CaptchaProvider:
    """
    配置全局 CAPTCHA provider

    Args:
        provider_type: NOOP / HCAPTCHA / TENCENT / RECAPTCHA
        **kwargs: provider 所需参数
            - NOOP: noop_prefix
            - HCAPTCHA / RECAPTCHA: secret, site_key
            - TENCENT: secret_id, secret_key, captcha_app_id
    """
    global _provider, _provider_type
    _provider_type = provider_type

    if provider_type == CaptchaProviderType.NOOP:
        _provider = NoopCaptchaProvider()
    elif provider_type == CaptchaProviderType.HCAPTCHA:
        _provider = HCaptchaProvider(
            secret=kwargs["secret"],
            site_key=kwargs.get("site_key"),
        )
    elif provider_type == CaptchaProviderType.RECAPTCHA:
        _provider = ReCaptchaProvider(
            secret=kwargs["secret"],
            site_key=kwargs.get("site_key"),
        )
    elif provider_type == CaptchaProviderType.TENCENT:
        _provider = TencentCaptchaProvider(
            secret_id=kwargs["secret_id"],
            secret_key=kwargs["secret_key"],
            captcha_app_id=kwargs["captcha_app_id"],
        )
    else:
        raise ValueError(f"未知 CAPTCHA provider 类型: {provider_type}")

    logger.info(f"CAPTCHA provider configured: {provider_type.value}")
    return _provider


def get_captcha_provider() -> CaptchaProvider:
    """获取全局 CAPTCHA provider（默认 Noop）"""
    global _provider
    if _provider is None:
        _provider = NoopCaptchaProvider()
    return _provider


def get_provider_type() -> CaptchaProviderType:
    """获取当前 provider 类型"""
    return _provider_type


def verify_captcha_token(
    token: str,
    ip: str = "",
    provider: Optional[CaptchaProvider] = None,
) -> CaptchaVerifyResult:
    """
    验证 CAPTCHA token（走全局 provider + token store 防重放）

    统计会在 stats() 中体现。
    """
    from security.captcha_stats import record_attempt, record_success, record_failure  # noqa: E501

    token_store = get_token_store()
    if token_store.is_used(token):
        record_attempt(provider=provider or get_captcha_provider(), success=False, ip=ip)
        return CaptchaVerifyResult(
            success=False,
            provider=(provider or get_captcha_provider()).__class__.__name__,
            error_codes=["token-already-used-or-expired"],
        )

    actual_provider = provider or get_captcha_provider()
    result = actual_provider.verify(token=token, ip=ip)
    if result.success:
        token_store.mark_used(token)
        record_success(provider=actual_provider, ip=ip)
    else:
        record_failure(provider=actual_provider, ip=ip)
    return result


__all__ = [
    "CaptchaProviderType",
    "CaptchaVerifyResult",
    "CaptchaProvider",
    "NoopCaptchaProvider",
    "HCaptchaProvider",
    "ReCaptchaProvider",
    "TencentCaptchaProvider",
    "CaptchaTokenStore",
    "get_token_store",
    "reset_token_store_for_testing",
    "configure_captcha",
    "get_captcha_provider",
    "get_provider_type",
    "verify_captcha_token",
]
