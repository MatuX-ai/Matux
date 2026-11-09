"""时区归一化回归测试（批次 3 / PR-3b）。

覆盖 naive / aware datetime 混用导致的
``TypeError: can't compare offset-naive and offset-aware datetimes``：
带 ``Z`` 的 ISO 8601 字符串解析后是 aware，而 ``datetime.now()`` 是 naive；
不带时区的字符串解析后又是 naive。实现统一按 UTC aware 比较。
"""

from datetime import datetime, timedelta, timezone
import json
from unittest.mock import patch

from models.verifiable_credential import CredentialSubject, VerifiableCredential
import pytest
from services.blockchain.service import BlockchainService

PROOF = {
    "type": "Ed25519Signature2020",
    "created": "2026-01-01T00:00:00Z",
    "verificationMethod": "did:example:org456#keys-1",
    "proofPurpose": "assertionMethod",
    "jws": "mock_signature",
}


def _cert_data(expiry_date):
    """最小可验证证书数据（proof 结构可通过 _verify_vc_signature）。"""
    return {
        "id": "cert_tz",
        "status": "active",
        "expiryDate": expiry_date,
        "proof": dict(PROOF),
    }


def _credential(expiration_date, issuance_date="2026-01-01T00:00:00Z"):
    """构造 VerifiableCredential（issuance 默认带 Z）。"""
    return VerifiableCredential(
        id="test_cert_tz",
        issuer="did:example:org456",
        issuanceDate=issuance_date,
        expirationDate=expiration_date,
        credentialSubject=CredentialSubject(id="did:example:user123"),
        status="active",
    )


@pytest.fixture
def blockchain_service():
    return BlockchainService()


async def _verify(service, expiry_date):
    with patch.object(service, "_query_chaincode") as mock_query:
        mock_query.return_value = json.dumps(_cert_data(expiry_date))
        return await service.verify_certificate("cert_tz")


class TestVerifyCertificateTimezone:
    """service.verify_certificate 的 expiryDate 解析与比较"""

    @pytest.mark.asyncio
    async def test_accepts_z_suffix(self, blockchain_service):
        """带 Z 的 expiryDate（aware）不应抛 TypeError"""
        result = await _verify(blockchain_service, "2028-01-01T00:00:00Z")
        assert result["id"] == "cert_tz"

    @pytest.mark.asyncio
    async def test_accepts_naive_expiry_date(self, blockchain_service):
        """不带时区的 expiryDate（naive）按 UTC 处理，不应抛 TypeError"""
        result = await _verify(blockchain_service, "2028-01-01T00:00:00")
        assert result["id"] == "cert_tz"

    @pytest.mark.asyncio
    async def test_rejects_expired_with_z_suffix(self, blockchain_service):
        """带 Z 的已过期时间应命中「证书已过期」"""
        with pytest.raises(Exception, match="证书已过期"):
            await _verify(blockchain_service, "2020-01-01T00:00:00Z")

    @pytest.mark.asyncio
    async def test_rejects_expired_naive_expiry_date(self, blockchain_service):
        """不带时区的已过期时间同样应命中「证书已过期」"""
        with pytest.raises(Exception, match="证书已过期"):
            await _verify(blockchain_service, "2020-01-01T00:00:00")

    @pytest.mark.asyncio
    async def test_expiry_boundary_against_utc_now(self, blockchain_service):
        """以 UTC now 为基准的边界：过期 1 小时 vs 未来 1 小时"""
        now = datetime.now(timezone.utc)
        with pytest.raises(Exception, match="证书已过期"):
            await _verify(blockchain_service, (now - timedelta(hours=1)).isoformat())

        result = await _verify(
            blockchain_service, (now + timedelta(hours=1)).isoformat()
        )
        assert result["id"] == "cert_tz"


class TestCredentialExpiryTimezone:
    """VerifiableCredential.is_expired 的时区归一"""

    def test_naive_expiration_not_expired(self):
        """naive 未来时间不应判为过期，也不应抛异常"""
        future = datetime.now(timezone.utc) + timedelta(days=30)
        vc = _credential(future.replace(tzinfo=None).isoformat())
        assert vc.is_expired() is False

    def test_naive_expiration_expired(self):
        """naive 过去时间应判为过期"""
        past = datetime.now(timezone.utc) - timedelta(days=30)
        vc = _credential(past.replace(tzinfo=None).isoformat())
        assert vc.is_expired() is True

    def test_z_suffix_expiration_expired(self):
        """带 Z 的过去时间应判为过期"""
        vc = _credential(
            expiration_date="2020-01-01T00:00:00Z",
            issuance_date="2019-01-01T00:00:00Z",
        )
        assert vc.is_expired() is True

    def test_z_suffix_expiration_not_expired(self):
        """带 Z 的未来时间不应判为过期"""
        vc = _credential("2028-01-01T00:00:00Z")
        assert vc.is_expired() is False

    def test_mixed_naive_and_aware_dates_do_not_raise(self):
        """issuanceDate 带 Z、expirationDate 不带时区 → 构造与比较均不抛异常"""
        vc = _credential(
            expiration_date="2028-01-01T00:00:00", issuance_date="2026-01-01T00:00:00Z"
        )
        assert vc.is_expired() is False

    def test_mixed_dates_still_enforce_expiration_after_issuance(self):
        """归一化后「过期日期必须晚于颁发日期」仍然生效"""
        with pytest.raises(ValueError, match="过期日期必须晚于颁发日期"):
            _credential(
                expiration_date="2025-01-01T00:00:00",
                issuance_date="2026-01-01T00:00:00Z",
            )

    def test_missing_expiration_is_not_expired(self):
        """无 expirationDate 时不算过期"""
        vc = VerifiableCredential(
            id="test_cert_no_exp",
            issuer="did:example:org456",
            issuanceDate="2026-01-01T00:00:00Z",
            credentialSubject=CredentialSubject(id="did:example:user123"),
        )
        assert vc.is_expired() is False
