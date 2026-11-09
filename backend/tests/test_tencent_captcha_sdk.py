"""
【P3 后台】腾讯云天御 CAPTCHA SDK 测试

覆盖：
1. TC3-HMAC-SHA256 签名算法（独立单元测试，不发真实请求）
2. TencentCloudCaptchaClient（注入 mock HTTP session）
3. TencentCaptchaProvider 适配器（注入 stub client）
4. 错误码映射
5. ticket/randstr 多种提取方式
"""

import hashlib
import hmac
import json
import os
import sys
from typing import Any, Dict

import pytest

_BACKEND_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from security.captcha import (  # noqa: E501, E402
    TencentCaptchaProvider,
)
from security.tencent_captcha_sdk import (  # noqa: E501, E402
    TencentCloudAPIError,
    TencentCloudCaptchaClient,
    sign_tencent_cloud_tc3,
)


# ==================== 1. 签名算法单元测试 ====================


class TestTC3Signing:
    """TC3-HMAC-SHA256 签名计算"""

    SECRET_KEY = "Gu5t9xGARNpq86cd98joQYCN3CmkEj8x"
    SERVICE = "cvm"
    ACTION = "DescribeInstances"
    HOST = "cvm.tencentcloudapi.com"
    TIMESTAMP = 1700000000
    DATE = "2023-11-14"

    def test_signature_format(self):
        sig = sign_tencent_cloud_tc3(
            secret_key=self.SECRET_KEY,
            service=self.SERVICE,
            action=self.ACTION,
            payload='{"Limit": 1}',
            timestamp=self.TIMESTAMP,
            date=self.DATE,
            host=self.HOST,
        )
        # Authorization 头应符合 TC3 格式
        auth = sig["authorization"]
        assert auth.startswith("TC3-HMAC-SHA256 Credential=")
        assert f"/{self.DATE}/{self.SERVICE}/tc3_request" in auth
        assert "SignedHeaders=content-type;host;x-tc-action" in auth
        assert "Signature=" in auth

    def test_signature_length(self):
        """Signature 应是 64 字符 hex（小写）"""
        sig = sign_tencent_cloud_tc3(
            secret_key=self.SECRET_KEY,
            service=self.SERVICE,
            action=self.ACTION,
            payload="{}",
            timestamp=self.TIMESTAMP,
            date=self.DATE,
            host=self.HOST,
        )
        auth = sig["authorization"]
        signature_part = auth.split("Signature=")[1]
        assert len(signature_part) == 64
        # 应该是 hex
        int(signature_part, 16)

    def test_signature_changes_with_payload(self):
        sig1 = sign_tencent_cloud_tc3(
            secret_key=self.SECRET_KEY, service=self.SERVICE,
            action=self.ACTION, payload='{"a": 1}',
            timestamp=self.TIMESTAMP, date=self.DATE, host=self.HOST,
        )
        sig2 = sign_tencent_cloud_tc3(
            secret_key=self.SECRET_KEY, service=self.SERVICE,
            action=self.ACTION, payload='{"a": 2}',
            timestamp=self.TIMESTAMP, date=self.DATE, host=self.HOST,
        )
        assert sig1["authorization"] != sig2["authorization"]

    def test_signature_changes_with_secret(self):
        sig1 = sign_tencent_cloud_tc3(
            secret_key="secret1", service=self.SERVICE,
            action=self.ACTION, payload='{}',
            timestamp=self.TIMESTAMP, date=self.DATE, host=self.HOST,
        )
        sig2 = sign_tencent_cloud_tc3(
            secret_key="secret2", service=self.SERVICE,
            action=self.ACTION, payload='{}',
            timestamp=self.TIMESTAMP, date=self.DATE, host=self.HOST,
        )
        assert sig1["authorization"] != sig2["authorization"]

    def test_signature_manual_compute(self):
        """
        手动复现签名算法，验证与函数输出一致

        这是签名正确性的金标准测试
        """
        payload = '{"Limit": 1, "Offset": 0}'
        action = self.ACTION
        service = self.SERVICE
        host = self.HOST
        date = self.DATE
        ts = self.TIMESTAMP
        content_type = "application/json; charset=utf-8"

        # Step 1
        canonical_headers = (
            f"content-type:{content_type}\n"
            f"host:{host}\n"
            f"x-tc-action:{action.lower()}\n"
        )
        signed_headers = "content-type;host;x-tc-action"
        hashed_payload = hashlib.sha256(payload.encode()).hexdigest()
        canonical_request = (
            f"POST\n"
            f"/\n"
            f"\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{hashed_payload}"
        )
        credential_scope = f"{date}/{service}/tc3_request"
        hashed_cr = hashlib.sha256(canonical_request.encode()).hexdigest()
        string_to_sign = (
            f"TC3-HMAC-SHA256\n"
            f"{ts}\n"
            f"{credential_scope}\n"
            f"{hashed_cr}"
        )

        # Step 2: SecretDate / SecretService / SecretSigning
        secret_date = hmac.new(
            self.SECRET_KEY.encode(), date.encode(), hashlib.sha256
        ).digest()
        secret_service = hmac.new(
            secret_date, service.encode(), hashlib.sha256
        ).digest()
        secret_signing = hmac.new(
            secret_service, b"tc3_request", hashlib.sha256
        ).digest()
        expected_sig = hmac.new(
            secret_signing, string_to_sign.encode(), hashlib.sha256
        ).hexdigest()

        # 调用函数
        sig = sign_tencent_cloud_tc3(
            secret_key=self.SECRET_KEY,
            service=service, action=action, payload=payload,
            timestamp=ts, date=date, host=host,
        )
        actual_sig = sig["authorization"].split("Signature=")[1]
        assert actual_sig == expected_sig


# ==================== 2. TencentCloudCaptchaClient (mock) ====================


class MockHTTPSession:
    """用于测试的 HTTP session 桩"""

    def __init__(self, response_data: Dict[str, Any], raise_exc: bool = False):
        self.response_data = response_data
        self.raise_exc = raise_exc
        self.last_payload = None
        self.last_headers = None
        self.last_host = None

    def post(self, host, payload, headers):
        self.last_host = host
        self.last_payload = payload
        self.last_headers = headers
        if self.raise_exc:
            raise TencentCloudAPIError("mock network error", code="mock-error")
        return self.response_data


class TestClientDescribeCaptchaResult:
    def setup_method(self):
        self.client = TencentCloudCaptchaClient(
            secret_id="AKIDxxx",
            secret_key="SECRETxxx",
            captcha_app_id="12345",
        )

    def test_init_validates_required(self):
        with pytest.raises(ValueError):
            TencentCloudCaptchaClient(secret_id="", secret_key="k", captcha_app_id="1")
        with pytest.raises(ValueError):
            TencentCloudCaptchaClient(secret_id="x", secret_key="", captcha_app_id="1")
        with pytest.raises(ValueError):
            TencentCloudCaptchaClient(secret_id="x", secret_key="k", captcha_app_id="")

    def test_describe_success(self):
        session = MockHTTPSession(
            response_data={
                "Response": {
                    "CaptchaCode": 1,
                    "CaptchaMsg": "OK",
                    "RequestId": "req-12345",
                }
            }
        )
        client = TencentCloudCaptchaClient(
            secret_id="AKIDxxx",
            secret_key="SECRETxxx",
            captcha_app_id="12345",
            http_session=session,
        )
        resp = client.describe_captcha_result(
            ticket="t_abc",
            randstr="@xyz",
            user_ip="1.2.3.4",
        )
        assert resp["Response"]["CaptchaCode"] == 1

    def test_describe_sends_correct_headers(self):
        session = MockHTTPSession(
            response_data={"Response": {"CaptchaCode": 1}}
        )
        client = TencentCloudCaptchaClient(
            secret_id="AKIDxxx",
            secret_key="SECRETxxx",
            captcha_app_id="12345",
            http_session=session,
        )
        client.describe_captcha_result(
            ticket="t_abc", randstr="@xyz", user_ip="1.2.3.4"
        )
        headers = session.last_headers
        # 必须包含这些头
        assert headers["Host"] == "captcha.tencentcloudapi.com"
        assert headers["X-TC-Action"] == "DescribeCaptchaResult"
        assert headers["X-TC-Version"] == "2019-07-22"
        assert headers["Content-Type"] == "application/json; charset=utf-8"
        assert headers["Authorization"].startswith("TC3-HMAC-SHA256 ")

    def test_describe_sends_correct_payload(self):
        session = MockHTTPSession(
            response_data={"Response": {"CaptchaCode": 1}}
        )
        client = TencentCloudCaptchaClient(
            secret_id="AKIDxxx",
            secret_key="SECRETxxx",
            captcha_app_id="12345",
            http_session=session,
        )
        client.describe_captcha_result(
            ticket="t_abc", randstr="@xyz", user_ip="1.2.3.4"
        )
        payload = json.loads(session.last_payload)
        assert payload["Ticket"] == "t_abc"
        assert payload["Randstr"] == "@xyz"
        assert payload["UserIp"] == "1.2.3.4"
        assert payload["CaptchaType"] == 9
        assert payload["CaptchaAppId"] == 12345

    def test_describe_with_captcha_type(self):
        session = MockHTTPSession(
            response_data={"Response": {"CaptchaCode": 1}}
        )
        client = TencentCloudCaptchaClient(
            secret_id="AKIDxxx",
            secret_key="SECRETxxx",
            captcha_app_id="12345",
            http_session=session,
        )
        client.describe_captcha_result(
            ticket="t", randstr="r", user_ip="1.1.1.1", captcha_type=7
        )
        payload = json.loads(session.last_payload)
        assert payload["CaptchaType"] == 7

    def test_describe_with_business_id(self):
        session = MockHTTPSession(
            response_data={"Response": {"CaptchaCode": 1}}
        )
        client = TencentCloudCaptchaClient(
            secret_id="AKIDxxx",
            secret_key="SECRETxxx",
            captcha_app_id="12345",
            http_session=session,
        )
        client.describe_captcha_result(
            ticket="t", randstr="r", user_ip="1.1.1.1",
            business_id="biz-001",
        )
        payload = json.loads(session.last_payload)
        assert payload["BusinessId"] == "biz-001"

    def test_describe_network_error(self):
        session = MockHTTPSession(response_data={}, raise_exc=True)
        client = TencentCloudCaptchaClient(
            secret_id="AKIDxxx",
            secret_key="SECRETxxx",
            captcha_app_id="12345",
            http_session=session,
        )
        with pytest.raises(TencentCloudAPIError):
            client.describe_captcha_result(
                ticket="t", randstr="r", user_ip="1.1.1.1"
            )


class TestClientVerifyTicket:
    def setup_method(self):
        self.client = TencentCloudCaptchaClient(
            secret_id="AKIDxxx",
            secret_key="SECRETxxx",
            captcha_app_id="12345",
        )

    def test_verify_ticket_success(self):
        session = MockHTTPSession(
            response_data={"Response": {"CaptchaCode": 1, "RequestId": "r1"}}
        )
        client = TencentCloudCaptchaClient(
            secret_id="x", secret_key="y", captcha_app_id="1",
            http_session=session,
        )
        ok = client.verify_ticket("t", "r", "1.2.3.4")
        assert ok is True

    def test_verify_ticket_failure(self):
        session = MockHTTPSession(
            response_data={"Response": {"CaptchaCode": 0, "RequestId": "r2"}}
        )
        client = TencentCloudCaptchaClient(
            secret_id="x", secret_key="y", captcha_app_id="1",
            http_session=session,
        )
        ok = client.verify_ticket("t", "r", "1.2.3.4")
        assert ok is False

    def test_verify_ticket_api_error(self):
        session = MockHTTPSession(
            response_data={
                "Response": {
                    "Error": {"Code": "AuthFailure", "Message": "Invalid credentials"},
                    "RequestId": "r3",
                }
            }
        )
        client = TencentCloudCaptchaClient(
            secret_id="x", secret_key="y", captcha_app_id="1",
            http_session=session,
        )
        with pytest.raises(TencentCloudAPIError) as exc_info:
            client.verify_ticket("t", "r", "1.2.3.4")
        assert exc_info.value.code == "AuthFailure"

    def test_verify_ticket_malformed(self):
        session = MockHTTPSession(response_data={"foo": "bar"})
        client = TencentCloudCaptchaClient(
            secret_id="x", secret_key="y", captcha_app_id="1",
            http_session=session,
        )
        with pytest.raises(TencentCloudAPIError) as exc_info:
            client.verify_ticket("t", "r", "1.2.3.4")
        assert "缺少 Response" in str(exc_info.value)


# ==================== 3. 错误码映射 ====================


class TestErrorCodeMapping:
    def test_captcha_code_to_error(self):
        client = TencentCloudCaptchaClient(
            secret_id="x", secret_key="y", captcha_app_id="1"
        )
        assert client._map_captcha_code_to_error(1) == "captcha-code-1"
        # 但 1 应该是 success（在使用层面）
        assert client._map_captcha_code_to_error(6) == "ticket-expired"
        assert client._map_captcha_code_to_error(7) == "ticket-invalid"
        assert client._map_captcha_code_to_error(8) == "ticket-already-used"
        assert client._map_captcha_code_to_error(999) == "captcha-code-999"

    def test_get_error_codes_success(self):
        client = TencentCloudCaptchaClient(
            secret_id="x", secret_key="y", captcha_app_id="1"
        )
        resp = {"Response": {"CaptchaCode": 1, "RequestId": "x"}}
        assert client.get_error_codes_from_response(resp) == []

    def test_get_error_codes_failed(self):
        client = TencentCloudCaptchaClient(
            secret_id="x", secret_key="y", captcha_app_id="1"
        )
        resp = {"Response": {"CaptchaCode": 6, "RequestId": "x"}}
        codes = client.get_error_codes_from_response(resp)
        assert "ticket-expired" in codes

    def test_get_error_codes_api_error(self):
        client = TencentCloudCaptchaClient(
            secret_id="x", secret_key="y", captcha_app_id="1"
        )
        resp = {
            "Response": {
                "Error": {"Code": "AuthFailure", "Message": "x"},
                "RequestId": "r",
            }
        }
        assert "AuthFailure" in client.get_error_codes_from_response(resp)

    def test_get_error_codes_malformed(self):
        client = TencentCloudCaptchaClient(
            secret_id="x", secret_key="y", captcha_app_id="1"
        )
        assert "malformed-response" in client.get_error_codes_from_response({})


# ==================== 4. TencentCaptchaProvider ====================


class StubClient:
    """测试用的 stub client"""

    def __init__(self, captcha_code: int = 1, raise_exc: bool = False):
        self.captcha_code = captcha_code
        self.raise_exc = raise_exc
        self.last_kwargs = None

    def describe_captcha_result(self, **kwargs):
        self.last_kwargs = kwargs
        if self.raise_exc:
            raise TencentCloudAPIError("stub", code="stub-error")
        return {"Response": {"CaptchaCode": self.captcha_code, "RequestId": "stub"}}

    def _map_captcha_code_to_error(self, code):
        mapping = {0: "captcha-failed", 6: "ticket-expired"}
        return mapping.get(code, f"captcha-code-{code}")


class TestTencentProvider:
    def setup_method(self):
        self.stub = StubClient(captcha_code=1)
        self.provider = TencentCaptchaProvider(
            secret_id="AKIDxxx",
            secret_key="SECRETxxx",
            captcha_app_id="12345",
            client=self.stub,
        )

    def test_provider_name(self):
        assert self.provider.get_provider_name() == "tencent"

    def test_get_site_key(self):
        assert self.provider.get_site_key() == "12345"

    def test_verify_with_kwargs(self):
        result = self.provider.verify(
            token="ignored",
            ip="1.2.3.4",
            ticket="t_abc",
            randstr="@xyz",
        )
        assert result.success is True
        assert result.provider == "tencent"

    def test_verify_with_json_token(self):
        token = json.dumps({"ticket": "t_json", "randstr": "@json"})
        result = self.provider.verify(token=token, ip="1.2.3.4")
        assert result.success is True

    def test_verify_with_separator_token(self):
        result = self.provider.verify(
            token="t_sep:@sep", ip="1.2.3.4"
        )
        assert result.success is True

    def test_verify_missing_ticket(self):
        result = self.provider.verify(token="", ip="1.2.3.4")
        assert result.success is False
        assert "missing-ticket-or-randstr" in result.error_codes

    def test_verify_only_ticket_no_randstr(self):
        result = self.provider.verify(
            token="just_a_string", ip="1.2.3.4", ticket="t"
        )
        assert result.success is False

    def test_verify_captcha_code_zero(self):
        stub = StubClient(captcha_code=0)
        provider = TencentCaptchaProvider(
            secret_id="x", secret_key="y", captcha_app_id="1", client=stub
        )
        result = provider.verify(
            token="ignored", ip="1.2.3.4",
            ticket="t", randstr="r",
        )
        assert result.success is False
        assert "captcha-failed" in result.error_codes

    def test_verify_api_error(self):
        stub = StubClient(raise_exc=True)
        provider = TencentCaptchaProvider(
            secret_id="x", secret_key="y", captcha_app_id="1", client=stub
        )
        result = provider.verify(
            token="ignored", ip="1.2.3.4",
            ticket="t", randstr="r",
        )
        assert result.success is False
        assert "stub-error" in result.error_codes

    def test_verify_malformed_response(self):
        class BadStub:
            def describe_captcha_result(self, **kwargs):
                return {"foo": "bar"}  # 缺 Response

        provider = TencentCaptchaProvider(
            secret_id="x", secret_key="y", captcha_app_id="1",
            client=BadStub(),
        )
        result = provider.verify(
            token="ignored", ip="1.2.3.4",
            ticket="t", randstr="r",
        )
        assert result.success is False
        assert "malformed-response" in result.error_codes

    def test_verify_response_with_error(self):
        class ErrorStub:
            def describe_captcha_result(self, **kwargs):
                return {
                    "Response": {
                        "Error": {"Code": "AuthFailure", "Message": "x"},
                        "RequestId": "r",
                    }
                }

        provider = TencentCaptchaProvider(
            secret_id="x", secret_key="y", captcha_app_id="1",
            client=ErrorStub(),
        )
        result = provider.verify(
            token="ignored", ip="1.2.3.4",
            ticket="t", randstr="r",
        )
        assert result.success is False
        assert "AuthFailure" in result.error_codes

    def test_passes_ip_to_client(self):
        self.provider.verify(
            token="ignored", ip="5.5.5.5",
            ticket="t", randstr="r",
        )
        assert self.stub.last_kwargs["user_ip"] == "5.5.5.5"

    def test_default_ip(self):
        self.provider.verify(
            token="ignored", ip="",
            ticket="t", randstr="r",
        )
        assert self.stub.last_kwargs["user_ip"] == "0.0.0.0"


# ==================== 5. lazy client init ====================


class TestLazyClientInit:
    def test_client_lazily_initialized(self):
        provider = TencentCaptchaProvider(
            secret_id="AKIDxxx",
            secret_key="SECRETxxx",
            captcha_app_id="12345",
        )
        # 初始未创建
        assert provider._client is None
        # 触发后创建
        _ = provider.client
        assert provider._client is not None

    def test_injected_client_used(self):
        stub = StubClient()
        provider = TencentCaptchaProvider(
            secret_id="x", secret_key="y", captcha_app_id="1",
            client=stub,
        )
        # 注入后不会重新创建
        assert provider.client is stub
        assert provider.client is stub
