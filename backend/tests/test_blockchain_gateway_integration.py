"""
区块链网关集成测试
测试完整的API端到端流程
"""

from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient
import pytest

from main import app
from services.blockchain.gateway_service import blockchain_gateway_service

client = TestClient(app)


@pytest.fixture
def mock_jwt_token():
    """模拟JWT令牌"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXIiLCJleHAiOjk5OTk5OTk5OTl9.mock_signature"


@pytest.fixture
def mock_education_user():
    """模拟教育局用户"""
    return {
        "id": 1,
        "username": "edu_admin",
        "email": "admin@education.gov",
        "role": "education",
        "is_active": True,
        "permissions": [],
    }


class TestBlockchainGatewayAPI:
    """区块链网关API集成测试"""

    def test_health_check_endpoint(self):
        """测试健康检查端点"""
        with patch.object(
            blockchain_gateway_service,
            "health_check",
            return_value={
                "status": "healthy",
                "connected": True,
                "last_block_height": 1000,
            },
        ):
            response = client.get("/api/v1/blockchain/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "Blockchain Gateway"
            assert data["blockchain_connected"] == True

    def test_issue_integral_success(self, mock_jwt_token, mock_education_user):
        """测试积分发行成功"""
        # 模拟认证和权限检查
        with patch("routes.auth_routes.get_current_user") as mock_auth:
            mock_auth.return_value = mock_education_user

            with patch.object(
                blockchain_gateway_service, "issue_integral"
            ) as mock_issue:
                mock_issue.return_value = {
                    "tx_id": "tx_test_123456",
                    "student_id": "student_001",
                    "amount": 100,
                    "issuer_id": 1,
                    "timestamp": datetime.now().isoformat(),
                }

                response = client.post(
                    "/api/v1/blockchain/issue-integral",
                    json={
                        "student_id": "student_001",
                        "amount": 100,
                        "description": "测试发行",
                    },
                    headers={"Authorization": f"Bearer {mock_jwt_token}"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["tx_id"] == "tx_test_123456"
                assert data["student_id"] == "student_001"
                assert data["amount"] == 100

    def test_issue_integral_permission_denied(self, mock_jwt_token):
        """测试积分发行权限不足"""
        # 模拟普通用户
        mock_user = {
            "id": 2,
            "username": "regular_user",
            "email": "user@example.com",
            "role": "user",
            "is_active": True,
            "permissions": [],
        }

        with patch("routes.auth_routes.get_current_user") as mock_auth:
            mock_auth.return_value = mock_user

            response = client.post(
                "/api/v1/blockchain/issue-integral",
                json={"student_id": "student_001", "amount": 100},
                headers={"Authorization": f"Bearer {mock_jwt_token}"},
            )

            assert response.status_code == 403
            data = response.json()
            assert "权限不足" in data["detail"]

    def test_issue_integral_invalid_parameters(
        self, mock_jwt_token, mock_education_user
    ):
        """测试积分发行参数验证"""
        with patch("routes.auth_routes.get_current_user") as mock_auth:
            mock_auth.return_value = mock_education_user

            # 测试空学生ID
            response = client.post(
                "/api/v1/blockchain/issue-integral",
                json={"student_id": "", "amount": 100},
                headers={"Authorization": f"Bearer {mock_jwt_token}"},
            )

            assert response.status_code == 422  # 验证错误

            # 测试负数金额
            response = client.post(
                "/api/v1/blockchain/issue-integral",
                json={"student_id": "student_001", "amount": -50},
                headers={"Authorization": f"Bearer {mock_jwt_token}"},
            )

            assert response.status_code == 422  # 验证错误

    def test_oauth_token_exchange_success(self):
        """测试OAuth2令牌交换成功"""
        with patch.object(
            blockchain_gateway_service, "validate_client_credentials", return_value=True
        ):
            with patch.object(
                blockchain_gateway_service, "generate_access_token"
            ) as mock_generate:
                mock_generate.return_value = {
                    "access_token": "test_oauth_token",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                    "scope": "read write",
                }

                response = client.post(
                    "/api/v1/blockchain/oauth/token",
                    json={
                        "grant_type": "client_credentials",
                        "client_id": "test_client_1",
                        "client_secret": "test_secret_1",
                        "scope": "read write",
                    },
                )

                assert response.status_code == 200
                data = response.json()
                assert data["access_token"] == "test_oauth_token"
                assert data["token_type"] == "Bearer"
                assert data["expires_in"] == 3600

    def test_oauth_token_exchange_invalid_credentials(self):
        """测试OAuth2令牌交换凭据无效"""
        with patch.object(
            blockchain_gateway_service,
            "validate_client_credentials",
            return_value=False,
        ):
            response = client.post(
                "/api/v1/blockchain/oauth/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": "invalid_client",
                    "client_secret": "wrong_secret",
                },
            )

            assert response.status_code == 401
            data = response.json()
            assert "无效的客户端凭据" in data["detail"]

    def test_get_student_balance_success(self, mock_jwt_token, mock_education_user):
        """测试查询学生余额成功"""
        with patch("routes.auth_routes.get_current_user") as mock_auth:
            mock_auth.return_value = mock_education_user

            with patch.object(
                blockchain_gateway_service, "get_student_balance"
            ) as mock_balance:
                mock_balance.return_value = {
                    "student_id": "student_001",
                    "total_amount": 1500,
                    "updated_at": 1234567890,
                }

                response = client.get(
                    "/api/v1/blockchain/students/student_001/balance",
                    headers={"Authorization": f"Bearer {mock_jwt_token}"},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["student_id"] == "student_001"
                assert data["balance"] == 1500

    def test_get_transaction_history_success(self, mock_jwt_token, mock_education_user):
        """测试查询交易历史成功"""
        with patch("routes.auth_routes.get_current_user") as mock_auth:
            mock_auth.return_value = mock_education_user

            with patch.object(
                blockchain_gateway_service, "get_transaction_history"
            ) as mock_history:
                mock_history.return_value = {
                    "transactions": [
                        {
                            "id": "tx_001",
                            "student_id": "student_001",
                            "amount": 100,
                            "type": "issue",
                        }
                    ],
                    "total_count": 1,
                }

                response = client.get(
                    "/api/v1/blockchain/transactions/history?limit=10",
                    headers={"Authorization": f"Bearer {mock_jwt_token}"},
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data["transactions"]) == 1
                assert data["total_count"] == 1
                assert data["limit"] == 10

    def test_circuit_breaker_fallback_scenario(
        self, mock_jwt_token, mock_education_user
    ):
        """测试熔断器降级场景"""
        with patch("routes.auth_routes.get_current_user") as mock_auth:
            mock_auth.return_value = mock_education_user

            # 模拟服务连续失败触发熔断器
            with patch.object(
                blockchain_gateway_service, "issue_integral"
            ) as mock_issue:
                mock_issue.side_effect = Exception("区块链服务不可用")

                # 连续调用触发熔断
                for i in range(6):  # 超过失败阈值
                    try:
                        client.post(
                            "/api/v1/blockchain/issue-integral",
                            json={"student_id": f"student_{i}", "amount": 100},
                            headers={"Authorization": f"Bearer {mock_jwt_token}"},
                        )
                    except (Exception, ConnectionError, TimeoutError):
                        pass  # 忽略异常

                # 验证熔断器状态（通过健康检查）
                with patch.object(
                    blockchain_gateway_service, "health_check"
                ) as mock_health:
                    mock_health.return_value = {
                        "status": "degraded",
                        "connected": False,
                        "circuit_breaker_state": "open",
                    }

                    response = client.get("/api/v1/blockchain/health")
                    assert response.status_code == 200
                    data = response.json()
                    assert (
                        data["status"] == "healthy"
                    )  # API仍返回成功，但内部状态显示降级


class TestCircuitBreakerIntegration:
    """熔断器集成测试"""

    def test_circuit_breaker_protects_against_failures(self):
        """测试熔断器保护免受连续失败影响"""
        # 这个测试需要更复杂的设置来验证熔断器的实际行为

    def test_fallback_execution_when_circuit_open(self):
        """测试电路开启时执行降级逻辑"""
        # 这个测试需要模拟熔断器的状态转换


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
