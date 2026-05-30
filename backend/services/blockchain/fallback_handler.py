"""
区块链网关降级处理
提供各种异常情况下的降级策略
"""

from datetime import datetime
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FallbackStrategy:
    """降级策略类"""

    @staticmethod
    async def fallback_issue_integral(
        service, student_id: str, amount: int, issuer_id: int, description: str = None
    ) -> Dict[str, Any]:
        """
        积分发行降级处理

        Args:
            service: 服务实例
            student_id: 学生ID
            amount: 积分数量
            issuer_id: 发行人ID
            description: 描述信息

        Returns:
            降级响应
        """
        logger.warning(f"积分发行服务降级 - 学生: {student_id}, 数量: {amount}")

        # 返回模拟的成功响应
        return {
            "tx_id": f"fallback_tx_{int(datetime.now().timestamp())}",
            "student_id": student_id,
            "amount": amount,
            "issuer_id": issuer_id,
            "timestamp": datetime.now().isoformat(),
            "status": "fallback_success",
            "message": "服务暂时不可用，已记录请求将在服务恢复后处理",
        }

    @staticmethod
    async def fallback_get_student_balance(service, student_id: str) -> Dict[str, Any]:
        """
        查询学生余额降级处理

        Args:
            service: 服务实例
            student_id: 学生ID

        Returns:
            降级响应
        """
        logger.warning(f"查询学生余额服务降级 - 学生: {student_id}")

        # 返回缓存数据或默认值
        cached_balance = service._get_cached_balance(student_id)
        if cached_balance is not None:
            return cached_balance

        # 返回默认值
        return {
            "student_id": student_id,
            "total_amount": 0,
            "updated_at": int(datetime.now().timestamp()),
            "source": "fallback_default",
        }

    @staticmethod
    async def fallback_get_transaction_history(
        service, student_id: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """
        查询交易历史降级处理

        Args:
            service: 服务实例
            student_id: 学生ID
            limit: 限制数量
            offset: 偏移量

        Returns:
            降级响应
        """
        logger.warning(f"查询交易历史服务降级 - 学生: {student_id}")

        # 返回空结果集
        return {
            "transactions": [],
            "total_count": 0,
            "source": "fallback_empty",
            "message": "服务暂时不可用，无法获取交易历史",
        }

    @staticmethod
    async def fallback_health_check(service) -> Dict[str, Any]:
        """
        健康检查降级处理

        Args:
            service: 服务实例

        Returns:
            降级响应
        """
        logger.warning("健康检查服务降级")

        return {
            "status": "degraded",
            "service": "Blockchain Gateway",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "blockchain_connected": False,
            "message": "服务处于降级状态",
            "fallback_reason": "primary_service_unavailable",
        }


class CacheManager:
    """缓存管理器"""

    def __init__(self):
        self.balance_cache = {}
        self.transaction_cache = {}
        self.cache_ttl = 300  # 5分钟缓存

    def cache_student_balance(self, student_id: str, balance_data: Dict[str, Any]):
        """缓存学生余额"""
        self.balance_cache[student_id] = {
            "data": balance_data,
            "timestamp": datetime.now().timestamp(),
        }
        logger.debug(f"缓存学生余额: {student_id}")

    def get_cached_balance(self, student_id: str) -> Optional[Dict[str, Any]]:
        """获取缓存的学生余额"""
        cache_entry = self.balance_cache.get(student_id)
        if not cache_entry:
            return None

        # 检查缓存是否过期
        if datetime.now().timestamp() - cache_entry["timestamp"] > self.cache_ttl:
            del self.balance_cache[student_id]
            return None

        return cache_entry["data"]

    def cache_transaction_history(self, student_id: str, history_data: Dict[str, Any]):
        """缓存交易历史"""
        cache_key = student_id or "all"
        self.transaction_cache[cache_key] = {
            "data": history_data,
            "timestamp": datetime.now().timestamp(),
        }
        logger.debug(f"缓存交易历史: {cache_key}")

    def get_cached_transaction_history(
        self, student_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """获取缓存的交易历史"""
        cache_key = student_id or "all"
        cache_entry = self.transaction_cache.get(cache_key)
        if not cache_entry:
            return None

        # 检查缓存是否过期
        if datetime.now().timestamp() - cache_entry["timestamp"] > self.cache_ttl:
            del self.transaction_cache[cache_key]
            return None

        return cache_entry["data"]

    def clear_expired_cache(self):
        """清理过期缓存"""
        current_time = datetime.now().timestamp()

        # 清理余额缓存
        expired_balances = [
            student_id
            for student_id, entry in self.balance_cache.items()
            if current_time - entry["timestamp"] > self.cache_ttl
        ]
        for student_id in expired_balances:
            del self.balance_cache[student_id]

        # 清理交易缓存
        expired_transactions = [
            key
            for key, entry in self.transaction_cache.items()
            if current_time - entry["timestamp"] > self.cache_ttl
        ]
        for key in expired_transactions:
            del self.transaction_cache[key]

        if expired_balances or expired_transactions:
            logger.debug(
                f"清理过期缓存 - 余额: {len(expired_balances)}, 交易: {len(expired_transactions)}"
            )


class CircuitBreakerFallback:
    """熔断器降级处理"""

    def __init__(self):
        self.cache_manager = CacheManager()
        self.fallback_strategy = FallbackStrategy()

    async def handle_issue_integral_fallback(
        self,
        service,
        student_id: str,
        amount: int,
        issuer_id: int,
        description: str = None,
    ) -> Dict[str, Any]:
        """处理积分发行降级"""
        try:
            # 记录降级事件
            self._log_fallback_event(
                "issue_integral",
                {"student_id": student_id, "amount": amount, "issuer_id": issuer_id},
            )

            # 执行降级策略
            result = await self.fallback_strategy.fallback_issue_integral(
                service, student_id, amount, issuer_id, description
            )

            # 缓存请求以便后续处理
            self._queue_fallback_request(
                "issue_integral",
                {
                    "student_id": student_id,
                    "amount": amount,
                    "issuer_id": issuer_id,
                    "description": description,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            return result

        except Exception as e:
            logger.error(f"降级处理失败: {e}")
            raise

    async def handle_get_balance_fallback(
        self, service, student_id: str
    ) -> Dict[str, Any]:
        """处理余额查询降级"""
        try:
            # 记录降级事件
            self._log_fallback_event("get_balance", {"student_id": student_id})

            # 尝试从缓存获取
            cached_result = self.cache_manager.get_cached_balance(student_id)
            if cached_result:
                return cached_result

            # 执行降级策略
            result = await self.fallback_strategy.fallback_get_student_balance(
                service, student_id
            )

            return result

        except Exception as e:
            logger.error(f"余额查询降级处理失败: {e}")
            raise

    async def handle_get_history_fallback(
        self,
        service,
        student_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """处理交易历史查询降级"""
        try:
            # 记录降级事件
            self._log_fallback_event(
                "get_history",
                {"student_id": student_id, "limit": limit, "offset": offset},
            )

            # 尝试从缓存获取
            cached_result = self.cache_manager.get_cached_transaction_history(
                student_id
            )
            if cached_result:
                return cached_result

            # 执行降级策略
            result = await self.fallback_strategy.fallback_get_transaction_history(
                service, student_id, limit, offset
            )

            return result

        except Exception as e:
            logger.error(f"交易历史查询降级处理失败: {e}")
            raise

    def _log_fallback_event(self, operation: str, params: Dict[str, Any]):
        """记录降级事件"""
        logger.warning(
            f"服务降级 - 操作: {operation}, 参数: {json.dumps(params, ensure_ascii=False)}"
        )

    def _queue_fallback_request(self, operation: str, request_data: Dict[str, Any]):
        """排队降级请求以便后续处理"""
        try:
            # 在实际应用中，这里应该将请求存储到队列或数据库中
            # 以便服务恢复后重新处理
            logger.info(f"排队降级请求 - 操作: {operation}, 数据: {request_data}")

            # 简单的内存队列实现（生产环境应使用Redis或其他队列系统）
            if not hasattr(self, "_fallback_queue"):
                self._fallback_queue = []

            self._fallback_queue.append(
                {
                    "operation": operation,
                    "data": request_data,
                    "queued_at": datetime.now().isoformat(),
                }
            )

        except Exception as e:
            logger.error(f"排队降级请求失败: {e}")


# 全局实例
circuit_breaker_fallback = CircuitBreakerFallback()
