"""
区块链服务核心实现
提供与Hyperledger Fabric网络交互的功能
"""

import asyncio
from datetime import datetime
import hashlib
import json
import logging
from typing import Any, Dict, List

# 注意：实际部署时需要安装hfc库
# pip install hfc
try:
    from hfc.fabric import Client
except ImportError:
    # Mock实现用于开发环境
    class MockClient:
        def __init__(self, net_profile=None):
            pass

        def new_channel(self, channel_name):
            return MockChannel()

        def get_user(self, org, name):
            return MockUser()

    class MockChannel:
        pass

    class MockUser:
        pass

    Client = MockClient

logger = logging.getLogger(__name__)


class BlockchainService:
    """区块链服务类"""

    def __init__(self, network_config_path: str = "blockchain/config/network.json"):
        """
        初始化区块链服务

        Args:
            network_config_path: 网络配置文件路径
        """
        self.network_config_path = network_config_path
        self.client = None
        self.channel = None
        self.initialized = False

    async def initialize(self):
        """初始化区块链客户端连接"""
        try:
            # 在实际环境中加载网络配置
            self.client = Client(net_profile=self.network_config_path)
            self.channel = self.client.new_channel("mychannel")
            self.initialized = True
            logger.info("区块链服务初始化成功")
        except Exception as e:
            logger.error(f"区块链服务初始化失败: {e}")
            # 开发环境下使用mock
            self.client = MockClient()
            self.channel = MockChannel()
            self.initialized = True

    async def issue_certificate(self, cert_data: Dict[str, Any]) -> str:
        """
        颁发技能证书

        Args:
            cert_data: 证书数据

        Returns:
            交易ID
        """
        if not self.initialized:
            await self.initialize()

        try:
            # 添加时间戳和ID
            if "id" not in cert_data:
                cert_data["id"] = f"cert_{int(datetime.now().timestamp())}"

            if "issueDate" not in cert_data:
                cert_data["issueDate"] = datetime.now().isoformat()

            if "status" not in cert_data:
                cert_data["status"] = "active"

            # 构造链码调用参数
            cert_json = json.dumps(cert_data, ensure_ascii=False)

            # 模拟链码调用（实际环境中替换为真实调用）
            response = await self._invoke_chaincode("IssueCert", [cert_json])

            logger.info(f"证书颁发成功: {cert_data['id']}")
            return response

        except Exception as e:
            logger.error(f"证书颁发失败: {e}")
            raise Exception(f"区块链调用失败: {str(e)}")

    async def verify_certificate(self, cert_id: str) -> Dict[str, Any]:
        """
        验证证书有效性

        Args:
            cert_id: 证书ID

        Returns:
            证书数据
        """
        if not self.initialized:
            await self.initialize()

        try:
            # 查询链码
            response = await self._query_chaincode("GetCert", [cert_id])
            cert_data = json.loads(response)

            # 验证证书状态
            if cert_data.get("status") == "revoked":
                raise Exception("证书已被撤销")

            # 验证过期时间
            expiry_date = cert_data.get("expiryDate")
            if expiry_date:
                expiry_dt = datetime.fromisoformat(expiry_date.replace("Z", "+00:00"))
                if datetime.now() > expiry_dt:
                    raise Exception("证书已过期")

            # 验证W3C VC签名（简化版）
            if not self._verify_vc_signature(cert_data):
                raise Exception("证书签名验证失败")

            logger.info(f"证书验证成功: {cert_id}")
            return cert_data

        except json.JSONDecodeError:
            raise Exception("证书数据格式错误")
        except Exception as e:
            logger.error(f"证书验证失败: {e}")
            raise Exception(f"证书验证失败: {str(e)}")

    async def revoke_certificate(self, cert_id: str, reason: str) -> str:
        """
        撤销证书

        Args:
            cert_id: 证书ID
            reason: 撤销原因

        Returns:
            交易ID
        """
        if not self.initialized:
            await self.initialize()

        try:
            response = await self._invoke_chaincode("RevokeCert", [cert_id, reason])
            logger.info(f"证书撤销成功: {cert_id}")
            return response

        except Exception as e:
            logger.error(f"证书撤销失败: {e}")
            raise Exception(f"证书撤销失败: {str(e)}")

    async def create_certification_request(self, request_data: Dict[str, Any]) -> str:
        """
        创建认证请求

        Args:
            request_data: 请求数据

        Returns:
            请求ID
        """
        if not self.initialized:
            await self.initialize()

        try:
            # 添加必要字段
            request_data["requestDate"] = datetime.now().isoformat()
            request_data["status"] = "pending"

            request_json = json.dumps(request_data, ensure_ascii=False)
            response = await self._invoke_chaincode(
                "CreateCertificationRequest", [request_json]
            )

            logger.info(f"认证请求创建成功: {response}")
            return response

        except Exception as e:
            logger.error(f"认证请求创建失败: {e}")
            raise Exception(f"认证请求创建失败: {str(e)}")

    async def approve_request(self, request_id: str, issuer_did: str) -> str:
        """
        批准认证请求

        Args:
            request_id: 请求ID
            issuer_did: 颁发者DID

        Returns:
            交易ID
        """
        if not self.initialized:
            await self.initialize()

        try:
            response = await self._invoke_chaincode(
                "ApproveCertificationRequest", [request_id, issuer_did]
            )
            logger.info(f"认证请求批准成功: {request_id}")
            return response

        except Exception as e:
            logger.error(f"认证请求批准失败: {e}")
            raise Exception(f"认证请求批准失败: {str(e)}")

    async def reject_request(self, request_id: str, comments: str) -> str:
        """
        拒绝认证请求

        Args:
            request_id: 请求ID
            comments: 拒绝理由

        Returns:
            交易ID
        """
        if not self.initialized:
            await self.initialize()

        try:
            response = await self._invoke_chaincode(
                "RejectCertificationRequest", [request_id, comments]
            )
            logger.info(f"认证请求拒绝成功: {request_id}")
            return response

        except Exception as e:
            logger.error(f"认证请求拒绝失败: {e}")
            raise Exception(f"认证请求拒绝失败: {str(e)}")

    async def get_certificates_by_holder(self, holder_did: str) -> List[Dict[str, Any]]:
        """
        根据持有者查询证书

        Args:
            holder_did: 持有者DID

        Returns:
            证书列表
        """
        if not self.initialized:
            await self.initialize()

        try:
            response = await self._query_chaincode("GetCertsByHolder", [holder_did])
            return json.loads(response)

        except Exception as e:
            logger.error(f"查询持有者证书失败: {e}")
            return []

    async def get_pending_requests(self) -> List[Dict[str, Any]]:
        """
        获取待处理的认证请求

        Returns:
            请求列表
        """
        if not self.initialized:
            await self.initialize()

        try:
            response = await self._query_chaincode("GetPendingRequests", [])
            return json.loads(response)

        except Exception as e:
            logger.error(f"获取待处理请求失败: {e}")
            return []

    def _verify_vc_signature(self, cert_data: Dict[str, Any]) -> bool:
        """
        验证W3C VC签名（简化实现）

        Args:
            cert_data: 证书数据

        Returns:
            验证结果
        """
        try:
            # 简化的签名验证逻辑
            # 实际环境中应该使用适当的加密库进行完整验证
            proof = cert_data.get("proof", {})
            if not proof.get("jws"):
                return False

            # 验证基本结构
            required_fields = ["type", "created", "verificationMethod", "proofPurpose"]
            for field in required_fields:
                if not proof.get(field):
                    return False

            return True

        except Exception:
            return False

    async def _invoke_chaincode(self, function: str, args: List[str]) -> str:
        """
        调用链码（写操作）

        Args:
            function: 函数名
            args: 参数列表

        Returns:
            交易ID
        """
        # 模拟链码调用
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return f"tx_{int(datetime.now().timestamp())}_{hashlib.md5(function.encode()).hexdigest()[:8]}"

    async def _query_chaincode(self, function: str, args: List[str]) -> str:
        """
        查询链码（读操作）

        Args:
            function: 函数名
            args: 参数列表

        Returns:
            查询结果
        """
        # 模拟查询结果
        await asyncio.sleep(0.05)  # 模拟网络延迟

        # 根据函数名返回不同的模拟数据
        if function == "GetCert":
            return json.dumps(
                {
                    "id": args[0],
                    "holderDid": "did:example:user123",
                    "issuerDid": "did:example:org456",
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
            )
        elif function == "GetCertsByHolder":
            return json.dumps(
                [
                    {
                        "id": "cert_001",
                        "skillName": "区块链开发",
                        "skillLevel": "专家级",
                        "status": "active",
                    }
                ]
            )
        elif function == "GetPendingRequests":
            return json.dumps([])
        else:
            return "{}"

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        try:
            if not self.initialized:
                await self.initialize()

            return {
                "status": "healthy",
                "initialized": self.initialized,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# 单例实例
blockchain_service = BlockchainService()
