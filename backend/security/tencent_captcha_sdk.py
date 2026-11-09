"""
【P3 后台】腾讯云 SDK TC3-HMAC-SHA256 签名 + 验证码 API 调用

API 3.0 签名规范：
https://cloud.tencent.com/document/api/1119/53807

请求示例（DescribeCaptchaResult）：
    POST https://captcha.tencentcloudapi.com/
    Headers:
        Authorization: TC3-HMAC-SHA256 Credential=...
        X-TC-Action: DescribeCaptchaResult
        X-TC-Timestamp: 1700000000
        X-TC-Version: 2019-07-22
        Content-Type: application/json; charset=utf-8
    Body:
        {
            "CaptchaType": 9,
            "Ticket": "xxx",
            "UserIp": "1.2.3.4",
            "Randstr": "xxx",
            "CaptchaAppId": 12345
        }

签名步骤：
1. 拼 CanonicalRequest = HTTPRequestMethod + "\n" + CanonicalURI + "\n" + CanonicalQueryString + "\n" + CanonicalHeaders + "\n" + SignedHeaders + "\n" + HashedRequestPayload
2. 拼 StringToSign = Algorithm + "\n" + RequestTimestamp + "\n" + CredentialScope + "\n" + HashedCanonicalRequest
3. 计算 SecretSigning = HMAC-SHA256(SecretKey, Date)
4. 计算 SecretService = HMAC-SHA256(SecretSigning, Service)
5. 计算 SecretSigningKey = HMAC-SHA256(SecretService, "tc3_request")
6. 计算 Signature = HMAC-SHA256(SecretSigningKey, StringToSign)（hex）
7. 拼 Authorization 头

返回字段：
- Response.CaptchaCode: 1=成功, 0=失败
- Response.CaptchaMsg: 错误描述
- Response.RequestId: 请求 ID
"""

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ==================== 异常 ====================


class TencentCloudAPIError(Exception):
    """腾讯云 API 调用异常"""

    def __init__(self, message: str, code: str = "", request_id: str = ""):
        super().__init__(message)
        self.message = message
        self.code = code
        self.request_id = request_id


# ==================== 签名核心 ====================


def _sha256_hex(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _hmac_sha256(key: bytes, content: str) -> bytes:
    return hmac.new(key, content.encode("utf-8"), hashlib.sha256).digest()


def sign_tencent_cloud_tc3(
    secret_key: str,
    service: str,
    action: str,
    payload: str,
    timestamp: int,
    date: str,
    host: str = "captcha.tencentcloudapi.com",
    method: str = "POST",
    canonical_uri: str = "/",
    canonical_query: str = "",
) -> Dict[str, str]:
    """
    计算 TC3-HMAC-SHA256 签名

    Returns:
        dict with:
        - authorization: 完整 Authorization 头
        - timestamp: X-TC-Timestamp 头值
        - date: 请求日期（用于调试）
    """
    # 1. CanonicalRequest
    content_type = "application/json; charset=utf-8"
    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-tc-action:{action.lower()}\n"
    )
    signed_headers = "content-type;host;x-tc-action"
    hashed_request_payload = _sha256_hex(payload)
    canonical_request = (
        f"{method}\n"
        f"{canonical_uri}\n"
        f"{canonical_query}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{hashed_request_payload}"
    )

    # 2. StringToSign
    credential_scope = f"{date}/{service}/tc3_request"
    hashed_canonical_request = _sha256_hex(canonical_request)
    string_to_sign = (
        f"TC3-HMAC-SHA256\n"
        f"{timestamp}\n"
        f"{credential_scope}\n"
        f"{hashed_canonical_request}"
    )

    # 3. 计算 Signature
    secret_date = _hmac_sha256(secret_key.encode("utf-8"), date)
    secret_service = _hmac_sha256(secret_date, service)
    secret_signing = _hmac_sha256(secret_service, "tc3_request")
    signature = hmac.new(
        secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()

    # 4. Authorization 头
    authorization = (
        f"TC3-HMAC-SHA256 "
        f"Credential={secret_key}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )

    return {
        "authorization": authorization,
        "timestamp": str(timestamp),
        "date": date,
    }


# ==================== 客户端 ====================


class TencentCloudCaptchaClient:
    """
    腾讯云天御 CAPTCHA API 3.0 客户端

    仅实现 DescribeCaptchaResult（验证用户票据）
    文档：https://cloud.tencent.com/document/api/1119/53807
    """

    HOST = "captcha.tencentcloudapi.com"
    SERVICE = "captcha"
    VERSION = "2019-07-22"
    ACTION = "DescribeCaptchaResult"
    DEFAULT_TIMEOUT = 5

    def __init__(
        self,
        secret_id: str,
        secret_key: str,
        captcha_app_id: str,
        host: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        http_session: Optional[Any] = None,
    ):
        """
        Args:
            secret_id: 腾讯云 API 密钥 ID
            secret_key: 腾讯云 API 密钥 Key
            captcha_app_id: 验证码应用 ID
            host: 覆盖 host（用于测试桩）
            timeout: HTTP 超时（秒）
            http_session: 可注入的 HTTP session（用于测试）
        """
        if not secret_id or not secret_key or not captcha_app_id:
            raise ValueError(
                "secret_id / secret_key / captcha_app_id 都不能为空"
            )
        self._secret_id = secret_id
        self._secret_key = secret_key
        self._captcha_app_id = captcha_app_id
        self._host = host or self.HOST
        self._timeout = timeout
        self._http_session = http_session

    # ---------- 公共方法 ----------

    def describe_captcha_result(
        self,
        ticket: str,
        randstr: str,
        user_ip: str,
        captcha_type: int = 9,
        business_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        验证用户 CAPTCHA 票据

        Args:
            ticket: 用户完成验证后获得的票据
            randstr: 随机串（与 ticket 配对）
            user_ip: 用户 IP
            captcha_type: 验证码类型（9=滑块, 7=图形）
            business_id: 业务 ID（可选）

        Returns:
            原始响应 dict（含 Response.CaptchaCode 等字段）

        Raises:
            TencentCloudAPIError: API 错误
        """
        payload_dict: Dict[str, Any] = {
            "CaptchaType": captcha_type,
            "Ticket": ticket,
            "UserIp": user_ip,
            "Randstr": randstr,
            "CaptchaAppId": int(self._captcha_app_id),
        }
        if business_id:
            payload_dict["BusinessId"] = business_id

        payload = json.dumps(payload_dict, separators=(",", ":"))

        # 签名
        now_ts = int(time.time())
        date = datetime.fromtimestamp(now_ts, tz=timezone.utc).strftime("%Y-%m-%d")
        sig = sign_tencent_cloud_tc3(
            secret_key=self._secret_key,
            service=self.SERVICE,
            action=self.ACTION,
            payload=payload,
            timestamp=now_ts,
            date=date,
            host=self._host,
        )

        headers = {
            "Authorization": sig["authorization"],
            "Content-Type": "application/json; charset=utf-8",
            "Host": self._host,
            "X-TC-Action": self.ACTION,
            "X-TC-Timestamp": sig["timestamp"],
            "X-TC-Version": self.VERSION,
        }

        # HTTP 请求
        response = self._do_post(payload=payload, headers=headers)
        return response

    # ---------- 便捷方法 ----------

    def verify_ticket(
        self,
        ticket: str,
        randstr: str,
        user_ip: str,
        captcha_type: int = 9,
    ) -> bool:
        """
        验证 ticket 是否通过（简化的布尔返回）

        Returns:
            True: CaptchaCode == 1（验证通过）
            False: 其他（验证失败 / 错误码）

        Raises:
            TencentCloudAPIError: 协议级错误（如签名错）
        """
        resp = self.describe_captcha_result(
            ticket=ticket,
            randstr=randstr,
            user_ip=user_ip,
            captcha_type=captcha_type,
        )

        if "Response" not in resp:
            raise TencentCloudAPIError(
                f"腾讯云返回格式异常：缺少 Response 字段。raw={resp}",
                code="malformed-response",
            )

        response_data = resp["Response"]
        # 网络/服务级错误（Response.Error）
        if "Error" in response_data:
            err = response_data["Error"]
            raise TencentCloudAPIError(
                err.get("Message", "未知错误"),
                code=err.get("Code", ""),
                request_id=resp.get("Response", {}).get("RequestId", ""),
            )

        captcha_code = response_data.get("CaptchaCode", -1)
        return captcha_code == 1

    def get_error_codes_from_response(self, response: Dict[str, Any]) -> list:
        """从 API 响应提取 error_codes（兼容 CaptchaVerifyResult）"""
        if "Response" not in response:
            return ["malformed-response"]
        resp = response["Response"]
        if "Error" in resp:
            err = resp["Error"]
            return [err.get("Code", "unknown-error")]
        # 业务码 → 错误码映射
        code = resp.get("CaptchaCode", -1)
        if code == 1:
            return []
        # 6=票据过期 7=票据无效 8=已使用 9=不存在 ...
        return [self._map_captcha_code_to_error(code)]

    @staticmethod
    def _map_captcha_code_to_error(code: int) -> str:
        mapping = {
            0: "captcha-failed",
            6: "ticket-expired",
            7: "ticket-invalid",
            8: "ticket-already-used",
            9: "ticket-not-exist",
            10: "ticket-ip-mismatch",
            11: "ticket-rate-limited",
            12: "ticket-app-id-invalid",
        }
        return mapping.get(code, f"captcha-code-{code}")

    # ---------- HTTP ----------

    def _do_post(
        self, payload: str, headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """执行 POST 请求"""
        if self._http_session is not None:
            return self._http_session.post(
                self._host, payload=payload, headers=headers
            )
        # 默认使用 urllib
        try:
            import ssl
            import urllib.request

            url = f"https://{self._host}/"
            req = urllib.request.Request(
                url,
                data=payload.encode("utf-8"),
                headers=headers,
                method="POST",
            )
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(
                req, timeout=self._timeout, context=ctx
            ) as resp:
                body = resp.read().decode("utf-8")
            return json.loads(body)
        except Exception as e:
            logger.warning(f"腾讯云 CAPTCHA API 调用失败: {e}")
            raise TencentCloudAPIError(
                f"HTTP 请求失败: {e}", code="network-error"
            ) from e


__all__ = [
    "TencentCloudAPIError",
    "TencentCloudCaptchaClient",
    "sign_tencent_cloud_tc3",
]
