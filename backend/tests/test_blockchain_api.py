"""
区块链API路由测试
"""

from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from main import app
from services.blockchain.service import blockchain_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def mock_blockchain_service():
    """为每个测试准备mock的区块链服务"""
    with patch("routes.blockchain_routes.blockchain_service", blockchain_service):
        yield


class TestBlockchainAPI:

    def test_health_check(self):
        """测试健康检查端点"""
        with patch.object(blockchain_service, "health_check") as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "initialized": True,
                "timestamp": "2026-01-01T00:00:00Z",
            }

            response = client.get("/blockchain/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["initialized"] == True

    def test_issue_certificate_success(self):
        """测试成功颁发证书"""
        certificate_data = {
            "holderDID": "did:example:user123",
            "issuerDID": "did:example:org456",
            "skillName": "区块链开发",
            "skillLevel": "专家级",
            "evidence": ["项目经验"],
        }

        with patch.object(blockchain_service, "issue_certificate") as mock_issue:
            mock_issue.return_value = "tx_123456"

            response = client.post("/blockchain/certificates", json=certificate_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["transactionId"] == "tx_123456"
            assert "certificateId" in data["data"]

    def test_issue_certificate_invalid_data(self):
        """测试颁发证书时数据验证失败"""
        invalid_data = {
            "holderDID": "did:example:user123"
            # 缺少必需字段
        }

        response = client.post("/blockchain/certificates", json=invalid_data)

        assert response.status_code == 422  # 验证错误

    def test_get_certificate_success(self):
        """测试成功获取证书"""
        mock_cert = {
            "id": "cert_001",
            "holderDID": "did:example:user123",
            "issuerDID": "did:example:org456",
            "skillName": "区块链开发",
            "skillLevel": "专家级",
            "issueDate": "2026-01-01T00:00:00Z",
            "expiryDate": "2028-01-01T00:00:00Z",
            "status": "active",
            "evidence": ["项目经验"],
        }

        with patch.object(blockchain_service, "verify_certificate") as mock_verify:
            mock_verify.return_value = mock_cert

            response = client.get("/blockchain/certificates/cert_001")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "cert_001"
            assert data["skillName"] == "区块链开发"

    def test_get_certificate_not_found(self):
        """测试获取不存在的证书"""
        with patch.object(blockchain_service, "verify_certificate") as mock_verify:
            mock_verify.side_effect = Exception("证书不存在")

            response = client.get("/blockchain/certificates/nonexistent")

            assert response.status_code == 404

    def test_revoke_certificate_success(self):
        """测试成功撤销证书"""
        revoke_data = {"reason": "违反使用条款"}

        with patch.object(blockchain_service, "revoke_certificate") as mock_revoke:
            mock_revoke.return_value = "tx_789012"

            response = client.delete(
                "/blockchain/certificates/cert_001", json=revoke_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["transactionId"] == "tx_789012"

    def test_get_certificates_by_holder(self):
        """测试根据持有者查询证书"""
        mock_certs = [
            {
                "id": "cert_001",
                "holderDID": "did:example:user123",
                "issuerDID": "did:example:org456",
                "skillName": "区块链开发",
                "skillLevel": "专家级",
                "issueDate": "2026-01-01T00:00:00Z",
                "expiryDate": "2028-01-01T00:00:00Z",
                "status": "active",
                "evidence": ["项目经验"],
            }
        ]

        with patch.object(blockchain_service, "get_certificates_by_holder") as mock_get:
            mock_get.return_value = mock_certs

            response = client.get("/blockchain/certificates/holder/did:example:user123")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == "cert_001"

    def test_create_certification_request(self):
        """测试创建认证请求"""
        request_data = {
            "holderDID": "did:example:user123",
            "skillName": "Python编程",
            "skillLevel": "高级",
            "evidence": ["项目作品"],
        }

        with patch.object(
            blockchain_service, "create_certification_request"
        ) as mock_create:
            mock_create.return_value = "req_345678"

            response = client.post("/blockchain/requests", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["requestId"] == "req_345678"

    def test_approve_request(self):
        """测试批准认证请求"""
        review_data = {"issuerDID": "did:example:org456"}

        with patch.object(blockchain_service, "approve_request") as mock_approve:
            mock_approve.return_value = "tx_999999"

            response = client.post(
                "/blockchain/requests/req_123/approve", json=review_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["transactionId"] == "tx_999999"

    def test_reject_request(self):
        """测试拒绝认证请求"""
        review_data = {"comments": "不符合要求"}

        with patch.object(blockchain_service, "reject_request") as mock_reject:
            mock_reject.return_value = "tx_888888"

            response = client.post(
                "/blockchain/requests/req_123/reject", json=review_data
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["transactionId"] == "tx_888888"

    def test_get_pending_requests(self):
        """测试获取待处理请求"""
        mock_requests = [
            {
                "requestId": "req_123",
                "holderDID": "did:example:user123",
                "skillName": "区块链开发",
                "status": "pending",
            }
        ]

        with patch.object(blockchain_service, "get_pending_requests") as mock_get:
            mock_get.return_value = mock_requests

            response = client.get("/blockchain/requests/pending")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["requestId"] == "req_123"

    def test_verify_certificate_endpoint_valid(self):
        """测试证书验证端点（有效证书）"""
        mock_cert = {
            "id": "cert_001",
            "holderDID": "did:example:user123",
            "status": "active",
        }

        with patch.object(blockchain_service, "verify_certificate") as mock_verify:
            mock_verify.return_value = mock_cert

            response = client.get("/blockchain/verify/cert_001")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert data["data"]["valid"] == True

    def test_verify_certificate_endpoint_invalid(self):
        """测试证书验证端点（无效证书）"""
        with patch.object(blockchain_service, "verify_certificate") as mock_verify:
            mock_verify.side_effect = Exception("证书已撤销")

            response = client.get("/blockchain/verify/invalid_cert")

            assert response.status_code == 200  # 注意：验证端点总是返回200
            data = response.json()
            assert data["success"] == False
            assert data["data"]["valid"] == False
            assert "已撤销" in data["message"]


# 集成测试
class TestBlockchainIntegration:

    @pytest.mark.asyncio
    async def test_full_certificate_lifecycle(self):
        """测试完整的证书生命周期"""
        # 1. 颁发证书
        cert_data = {
            "holderDID": "did:example:newuser",
            "issuerDID": "did:example:issuer",
            "skillName": "测试技能",
            "skillLevel": "中级",
            "evidence": ["测试证据"],
        }

        with (
            patch.object(blockchain_service, "issue_certificate") as mock_issue,
            patch.object(blockchain_service, "verify_certificate") as mock_verify,
            patch.object(blockchain_service, "revoke_certificate") as mock_revoke,
        ):

            # 颁发
            mock_issue.return_value = "tx_issue_123"
            issue_response = client.post("/blockchain/certificates", json=cert_data)
            assert issue_response.status_code == 200

            cert_id = issue_response.json()["data"]["certificateId"]

            # 验证
            mock_verify.return_value = {**cert_data, "id": cert_id, "status": "active"}
            verify_response = client.get(f"/blockchain/certificates/{cert_id}")
            assert verify_response.status_code == 200

            # 撤销
            mock_revoke.return_value = "tx_revoke_456"
            revoke_response = client.delete(
                f"/blockchain/certificates/{cert_id}", json={"reason": "测试撤销"}
            )
            assert revoke_response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
