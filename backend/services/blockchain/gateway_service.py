"""
区块链网关服务
提供统一的区块链接口访问，包括权限验证、熔断器、降级等功能
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

import jwt

from config.settings import settings
from services.blockchain.fallback_handler import circuit_breaker_fallback
from utils.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""

    failure_threshold: int = 5
    timeout: int = 60
    half_open_attempts: int = 3


class BlockchainGatewayService:
    """区块链网关服务类"""

    def __init__(self):
        self.initialized = False
        self.circuit_breaker = None
        self.client_registry = {}
        self.token_cache = {}
        self._setup_circuit_breaker()

    def _setup_circuit_breaker(self):
        """设置熔断器"""
        config = CircuitBreakerConfig(
            failure_threshold=getattr(
                settings, "BLOCKCHAIN_CIRCUIT_BREAKER_THRESHOLD", 5
            ),
            timeout=getattr(settings, "BLOCKCHAIN_CIRCUIT_BREAKER_TIMEOUT", 60),
            half_open_attempts=getattr(
                settings, "BLOCKCHAIN_CIRCUIT_BREAKER_HALF_OPEN", 3
            ),
        )

        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.failure_threshold,
            timeout=config.timeout,
            half_open_attempts=config.half_open_attempts,
        )

    async def initialize(self):
        """初始化区块链网关服务"""
        try:
            # 初始化客户端注册表
            self._load_client_registry()

            # 初始化熔断器
            await self.circuit_breaker.initialize()

            self.initialized = True
            logger.info("区块链网关服务初始化完成")

        except Exception as e:
            logger.error(f"区块链网关服务初始化失败: {e}")
            raise

    def _load_client_registry(self):
        """加载客户端注册表"""
        # 在实际应用中，这应该从数据库或配置文件加载
        self.client_registry = {
            "test_client_1": {
                "client_secret": "test_secret_1",
                "allowed_scopes": ["read", "write"],
                "is_active": True,
            },
            "mobile_app": {
                "client_secret": "mobile_app_secret",
                "allowed_scopes": ["read"],
                "is_active": True,
            },
            "education_portal": {
                "client_secret": "edu_portal_secret",
                "allowed_scopes": ["blockchain:read", "blockchain:write"],
                "is_active": True,
            },
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        try:
            # 检查区块链连接状态
            connected = await self._check_blockchain_connection()

            return {
                "status": "healthy" if connected else "degraded",
                "connected": connected,
                "last_block_height": (
                    await self._get_last_block_height() if connected else None
                ),
                "circuit_breaker_state": self.circuit_breaker.get_state(),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    @CircuitBreaker.protected(
        fallback=circuit_breaker_fallback.handle_issue_integral_fallback
    )
    async def issue_integral(
        self, student_id: str, amount: int, issuer_id: int, description: str = None
    ) -> Dict[str, Any]:
        """
        发行积分给学生

        Args:
            student_id: 学生ID
            amount: 积分数量
            issuer_id: 发行人ID
            description: 描述信息

        Returns:
            交易结果，包含交易哈希

        Raises:
            Exception: 区块链调用失败
        """
        if not self.initialized:
            await self.initialize()

        try:
            # 验证参数
            if not student_id:
                raise ValueError("学生ID不能为空")
            if amount <= 0:
                raise ValueError("积分数量必须大于0")

            # 构造链码调用参数
            chaincode_args = [
                student_id,
                str(amount),
                str(issuer_id),
                description or "积分发行_" + datetime.now().strftime("%Y%m%d_%H%M%S"),
            ]

            # 调用链码（模拟实现）
            tx_id = await self._invoke_chaincode(
                channel_name="imatu-channel",
                chaincode_name="integral",
                function_name="IssueIntegral",
                args=chaincode_args,
                endorsing_peers=["peer0.education.org"],
            )

            logger.info(f"成功为学生 {student_id} 发行 {amount} 积分，交易ID: {tx_id}")

            return {
                "tx_id": tx_id,
                "student_id": student_id,
                "amount": amount,
                "issuer_id": issuer_id,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"积分发行失败: {e}")
            raise Exception(f"区块链调用失败: {str(e)}")

    @CircuitBreaker.protected(
        fallback=circuit_breaker_fallback.handle_get_balance_fallback
    )
    async def get_student_balance(self, student_id: str) -> Dict[str, Any]:
        """
        查询学生积分余额

        Args:
            student_id: 学生ID

        Returns:
            学生余额信息
        """
        if not self.initialized:
            await self.initialize()

        try:
            # 查询链码
            result = await self._query_chaincode(
                channel_name="imatu-channel",
                chaincode_name="integral",
                function_name="GetStudentBalance",
                args=[student_id],
            )

            balance_data = (
                json.loads(result)
                if result
                else {
                    "student_id": student_id,
                    "total_amount": 0,
                    "updated_at": int(datetime.now().timestamp()),
                }
            )

            return balance_data

        except Exception as e:
            logger.error(f"查询学生余额失败: {e}")
            # 降级处理：返回默认值
            return {
                "student_id": student_id,
                "total_amount": 0,
                "updated_at": int(datetime.now().timestamp()),
            }

    @CircuitBreaker.protected(
        fallback=circuit_breaker_fallback.handle_get_history_fallback
    )
    async def get_transaction_history(
        self, student_id: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """
        查询交易历史

        Args:
            student_id: 学生ID（可选）
            limit: 返回记录数限制
            offset: 偏移量

        Returns:
            交易历史记录
        """
        if not self.initialized:
            await self.initialize()

        try:
            # 构造查询参数
            query_args = []
            if student_id:
                query_args.append(student_id)
            query_args.extend([str(limit), str(offset)])

            # 查询链码
            result = await self._query_chaincode(
                channel_name="imatu-channel",
                chaincode_name="integral",
                function_name="GetTransactionHistory",
                args=query_args,
            )

            history_data = (
                json.loads(result) if result else {"transactions": [], "total_count": 0}
            )

            return history_data

        except Exception as e:
            logger.error(f"查询交易历史失败: {e}")
            # 降级处理：返回空结果
            return {"transactions": [], "total_count": 0}

    async def validate_client_credentials(
        self, client_id: str, client_secret: str
    ) -> bool:
        """
        验证客户端凭据

        Args:
            client_id: 客户端ID
            client_secret: 客户端密钥

        Returns:
            验证结果
        """
        try:
            client_info = self.client_registry.get(client_id)
            if not client_info or not client_info.get("is_active"):
                return False

            return client_info.get("client_secret") == client_secret

        except Exception as e:
            logger.error(f"客户端凭据验证失败: {e}")
            return False

    async def generate_access_token(
        self, client_id: str, grant_type: str, scope: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成访问令牌

        Args:
            client_id: 客户端ID
            grant_type: 授权类型
            scope: 权限范围

        Returns:
            令牌信息
        """
        try:
            # 验证授权类型
            if grant_type != "client_credentials":
                raise ValueError("不支持的授权类型")

            # 生成JWT令牌
            payload = {
                "iss": "blockchain-gateway",
                "sub": client_id,
                "aud": "blockchain-api",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iat": datetime.utcnow(),
                "scope": scope or "read",
            }

            token = jwt.encode(
                payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
            )

            return {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": scope or "read",
            }

        except Exception as e:
            logger.error(f"令牌生成失败: {e}")
            raise Exception(f"令牌生成失败: {str(e)}")

    async def reset_circuit_breaker(self) -> Dict[str, Any]:
        """
        重置熔断器

        Returns:
            重置结果
        """
        try:
            await self.circuit_breaker.reset()
            return {
                "status": "success",
                "message": "熔断器已重置",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"重置熔断器失败: {e}")
            raise Exception(f"重置熔断器失败: {str(e)}")

    async def _check_blockchain_connection(self) -> bool:
        """检查区块链连接状态"""
        try:
            # 模拟连接检查
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False

    async def _get_last_block_height(self) -> Optional[int]:
        """获取最新区块高度"""
        try:
            # 模拟获取区块高度
            return 1000
        except Exception:
            return None

    async def _invoke_chaincode(
        self,
        channel_name: str,
        chaincode_name: str,
        function_name: str,
        args: List[str],
        endorsing_peers: List[str],
    ) -> str:
        """
        调用链码（写操作）

        Args:
            channel_name: 通道名称
            chaincode_name: 链码名称
            function_name: 函数名称
            args: 参数列表
            endorsing_peers: 背书节点列表

        Returns:
            交易ID
        """
        # 模拟链码调用
        await asyncio.sleep(0.2)  # 模拟网络延迟

        # 生成模拟交易ID
        tx_data = f"{channel_name}:{chaincode_name}:{function_name}:{':'.join(args)}"
        tx_id = f"tx_{int(datetime.now().timestamp())}_{hashlib.md5(tx_data.encode()).hexdigest()[:12]}"

        logger.debug(f"链码调用成功: {tx_id}")
        return tx_id

    async def _query_chaincode(
        self,
        channel_name: str,
        chaincode_name: str,
        function_name: str,
        args: List[str],
    ) -> str:
        """
        查询链码（读操作）

        Args:
            channel_name: 通道名称
            chaincode_name: 链码名称
            function_name: 函数名称
            args: 参数列表

        Returns:
            查询结果
        """
        # 模拟查询结果
        await asyncio.sleep(0.1)  # 模拟网络延迟

        # 根据函数名返回不同的模拟数据
        if function_name == "GetStudentBalance":
            return json.dumps(
                {
                    "student_id": args[0] if args else "default_student",
                    "total_amount": 1500,
                    "updated_at": int(datetime.now().timestamp()),
                }
            )
        elif function_name == "GetTransactionHistory":
            return json.dumps(
                {
                    "transactions": [
                        {
                            "id": "tx_001",
                            "student_id": args[0] if args else "default_student",
                            "amount": 100,
                            "type": "issue",
                            "timestamp": int(datetime.now().timestamp()) - 3600,
                        }
                    ],
                    "total_count": 1,
                }
            )
        else:
            return "{}"

    def _get_cached_balance(self, student_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的余额数据"""
        return circuit_breaker_fallback.cache_manager.get_cached_balance(student_id)


# 单例实例
blockchain_gateway_service = BlockchainGatewayService()
