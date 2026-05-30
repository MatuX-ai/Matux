"""
区块链服务单元测试
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from models.verifiable_credential import CredentialSubject, VerifiableCredential
from services.blockchain.service import BlockchainService


@pytest.fixture
def blockchain_service():
    """创建区块链服务实例"""
    return BlockchainService()


@pytest.fixture
def sample_certificate():
    """创建示例证书数据"""
    return {
        "id": "cert_001",
        "holderDID": "did:example:user123",
        "issuerDID": "did:example:org456",
        "skillName": "区块链开发",
        "skillLevel": "专家级",
        "evidence": ["项目经验", "认证考试"],
        "issuanceDate": "2026-01-01T00:00:00Z",
        "expirationDate": "2028-01-01T00:00:00Z",
    }


class TestBlockchainService:

    @pytest.mark.asyncio
    async def test_initialize_success(self, blockchain_service):
        """测试服务初始化成功"""
        with patch("services.blockchain.service.Client") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            await blockchain_service.initialize()

            assert blockchain_service.initialized == True
            assert blockchain_service.client == mock_client_instance

    @pytest.mark.asyncio
    async def test_initialize_failure_fallback(self, blockchain_service):
        """测试初始化失败时的降级处理"""
        with patch(
            "services.blockchain.service.Client",
            side_effect=Exception("Connection failed"),
        ):
            await blockchain_service.initialize()
            assert blockchain_service.initialized == True  # 应该降级到mock模式

    @pytest.mark.asyncio
    async def test_issue_certificate_success(
        self, blockchain_service, sample_certificate
    ):
        """测试成功颁发证书"""
        await blockchain_service.initialize()

        # Mock链码调用
        with patch.object(blockchain_service, "_invoke_chaincode") as mock_invoke:
            mock_invoke.return_value = "tx_123456"

            tx_id = await blockchain_service.issue_certificate(sample_certificate)

            assert tx_id == "tx_123456"
            mock_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_issue_certificate_missing_fields(self, blockchain_service):
        """测试证书数据缺失必要字段"""
        await blockchain_service.initialize()

        incomplete_cert = {"holderDID": "did:example:user123"}  # 缺少issuerDID等字段

        with pytest.raises(Exception, match="区块链调用失败"):
            await blockchain_service.issue_certificate(incomplete_cert)

    @pytest.mark.asyncio
    async def test_verify_certificate_success(self, blockchain_service):
        """测试成功验证证书"""
        await blockchain_service.initialize()

        mock_cert_data = {
            "id": "cert_001",
            "holderDID": "did:example:user123",
            "issuerDID": "did:example:org456",
            "skillName": "区块链开发",
            "skillLevel": "专家级",
            "status": "active",
            "issueDate": "2026-01-01T00:00:00Z",
            "expiryDate": "2028-01-01T00:00:00Z",
            "proof": {
                "type": "Ed25519Signature2020",
                "created": "2026-01-01T00:00:00Z",
                "verificationMethod": "did:example:org456#keys-1",
                "proofPurpose": "assertionMethod",
                "jws": "mock_signature",
            },
        }

        with patch.object(blockchain_service, "_query_chaincode") as mock_query:
            mock_query.return_value = json.dumps(mock_cert_data)
            with patch.object(
                blockchain_service, "_verify_vc_signature", return_value=True
            ):
                result = await blockchain_service.verify_certificate("cert_001")

                assert result["id"] == "cert_001"
                assert result["status"] == "active"

    @pytest.mark.asyncio
    async def test_verify_certificate_revoked(self, blockchain_service):
        """测试验证已撤销的证书"""
        await blockchain_service.initialize()

        revoked_cert = {
            "id": "cert_001",
            "status": "revoked",
            "holderDID": "did:example:user123",
        }

        with patch.object(blockchain_service, "_query_chaincode") as mock_query:
            mock_query.return_value = json.dumps(revoked_cert)

            with pytest.raises(Exception, match="证书已被撤销"):
                await blockchain_service.verify_certificate("cert_001")

    @pytest.mark.asyncio
    async def test_verify_certificate_expired(self, blockchain_service):
        """测试验证已过期的证书"""
        await blockchain_service.initialize()

        expired_cert = {
            "id": "cert_001",
            "status": "active",
            "holderDID": "did:example:user123",
            "expiryDate": "2020-01-01T00:00:00Z",  # 已过期
        }

        with patch.object(blockchain_service, "_query_chaincode") as mock_query:
            mock_query.return_value = json.dumps(expired_cert)
            with patch.object(
                blockchain_service, "_verify_vc_signature", return_value=True
            ):

                with pytest.raises(Exception, match="证书已过期"):
                    await blockchain_service.verify_certificate("cert_001")

    @pytest.mark.asyncio
    async def test_revoke_certificate_success(self, blockchain_service):
        """测试成功撤销证书"""
        await blockchain_service.initialize()

        with patch.object(blockchain_service, "_invoke_chaincode") as mock_invoke:
            mock_invoke.return_value = "tx_789012"

            tx_id = await blockchain_service.revoke_certificate("cert_001", "违反规定")

            assert tx_id == "tx_789012"
            mock_invoke.assert_called_once_with("RevokeCert", ["cert_001", "违反规定"])

    @pytest.mark.asyncio
    async def test_get_certificates_by_holder(self, blockchain_service):
        """测试根据持有者查询证书"""
        await blockchain_service.initialize()

        mock_certs = [
            {
                "id": "cert_001",
                "skillName": "区块链开发",
                "skillLevel": "专家级",
                "status": "active",
            }
        ]

        with patch.object(blockchain_service, "_query_chaincode") as mock_query:
            mock_query.return_value = json.dumps(mock_certs)

            certs = await blockchain_service.get_certificates_by_holder(
                "did:example:user123"
            )

            assert len(certs) == 1
            assert certs[0]["id"] == "cert_001"

    @pytest.mark.asyncio
    async def test_create_certification_request(self, blockchain_service):
        """测试创建认证请求"""
        await blockchain_service.initialize()

        request_data = {
            "holderDID": "did:example:user123",
            "skillName": "Python编程",
            "skillLevel": "高级",
            "evidence": ["项目作品"],
        }

        with patch.object(blockchain_service, "_invoke_chaincode") as mock_invoke:
            mock_invoke.return_value = "req_345678"

            req_id = await blockchain_service.create_certification_request(request_data)

            assert req_id == "req_345678"
            mock_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, blockchain_service):
        """测试健康检查（已初始化）"""
        await blockchain_service.initialize()

        health = await blockchain_service.health_check()

        assert health["status"] == "healthy"
        assert health["initialized"] == True

    @pytest.mark.asyncio
    async def test_health_check_uninitialized(self, blockchain_service):
        """测试健康检查（未初始化）"""
        # 不调用initialize

        with patch.object(blockchain_service, "initialize") as mock_init:
            mock_init.side_effect = Exception("Network error")

            health = await blockchain_service.health_check()

            assert health["status"] == "unhealthy"
            assert "Network error" in health["error"]


# VC服务测试
class TestVCService:

    @pytest.fixture
    def vc_service(self):
        from services.blockchain.vc_service import vc_service

        # 重新初始化以确保干净状态
        vc_service.__init__()
        return vc_service

    def test_generate_ed25519_keypair(self, vc_service):
        """测试生成Ed25519密钥对"""
        from services.blockchain.vc_service import VCCryptoService

        crypto_service = VCCryptoService()

        private_key, public_key = crypto_service.generate_ed25519_keypair()

        assert len(private_key) == 32  # Ed25519私钥长度
        assert len(public_key) == 32  # Ed25519公钥长度
        assert private_key != public_key

    @pytest.mark.asyncio
    async def test_initialize_issuer_keys(self, vc_service):
        """测试初始化颁发者密钥"""
        private_key_hex = vc_service.initialize_issuer_keys()

        assert len(private_key_hex) == 64  # 32字节的十六进制表示
        assert vc_service._issuer_private_key is not None
        assert vc_service._issuer_public_key is not None

    @pytest.mark.asyncio
    async def test_create_skill_certificate(self, vc_service):
        """测试创建技能证书"""
        vc_service.initialize_issuer_keys()

        vc = vc_service.create_skill_certificate(
            holder_did="did:example:user123",
            issuer_did="did:example:org456",
            skill_name="区块链开发",
            skill_level="专家级",
            evidence=["项目经验", "认证考试"],
        )

        assert vc.id.startswith("urn:uuid:")
        assert vc.holderDID == "did:example:user123"
        assert vc.issuer == "did:example:org456"
        assert vc.skill_name == "区块链开发"
        assert vc.skill_level == "专家级"
        assert len(vc.evidence) == 2
        assert vc.proof is not None
        assert vc.status == "active"

    @pytest.mark.asyncio
    async def test_verify_valid_credential(self, vc_service):
        """测试验证有效凭证"""
        vc_service.initialize_issuer_keys()

        # 创建证书
        vc = vc_service.create_skill_certificate(
            holder_did="did:example:user123",
            issuer_did="did:example:org456",
            skill_name="区块链开发",
            skill_level="专家级",
        )

        # 验证证书
        result = vc_service.verify_credential(vc)

        assert result["valid"] == True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_verify_expired_credential(self, vc_service):
        """测试验证过期凭证"""
        vc_service.initialize_issuer_keys()

        # 创建已过期的证书
        from datetime import datetime, timedelta

        expired_date = datetime.now() - timedelta(days=1)

        vc = VerifiableCredential(
            id="test_cert",
            issuer="did:example:org456",
            issuanceDate="2020-01-01T00:00:00Z",
            expirationDate=expired_date.isoformat() + "Z",
            credentialSubject=CredentialSubject(id="did:example:user123"),
            status="active",
        )

        result = vc_service.verify_credential(vc)

        assert result["valid"] == False
        assert any("过期" in error for error in result["errors"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
