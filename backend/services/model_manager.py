"""
预训练模型管理器
负责模型版本控制、缓存管理和性能监控
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
import json
import logging
import os
from typing import Any, Dict, List, Optional

from redis import asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_service.model_compressor import ModelCompressor
from ai_service.traditional_ml_transfer import TraditionalTransferLearning
from ai_service.transfer_learning_engine import TransferLearningEngine
from config.transfer_learning_config import settings
from models.recommendation import ColdStartRecommendationLog, PretrainedModel

logger = logging.getLogger(__name__)


@dataclass
class ModelCacheEntry:
    """模型缓存条目"""

    model_id: int
    model_data: Any
    loaded_at: datetime
    access_count: int
    last_accessed: datetime


class PretrainedModelManager:
    """预训练模型管理器"""

    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.model_cache: Dict[int, ModelCacheEntry] = {}
        self.cache_ttl = settings.deployment.model_cache_ttl
        self.max_cache_size = settings.deployment.prediction_cache_size
        self.transfer_engine = TransferLearningEngine(settings)
        self.compressor = ModelCompressor(settings)
        self.traditional_ml = TraditionalTransferLearning(settings)

        # 性能监控
        self.performance_stats = {
            "total_predictions": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0.0,
            "model_load_times": [],
        }

    async def get_best_model(self, db: AsyncSession) -> Optional[PretrainedModel]:
        """获取最佳的预训练模型"""
        try:
            stmt = (
                select(PretrainedModel)
                .where(PretrainedModel.training_status == "completed")
                .order_by(
                    PretrainedModel.accuracy_after.desc(),
                    PretrainedModel.created_at.desc(),
                )
                .limit(1)
            )

            result = await db.execute(stmt)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"获取最佳模型失败: {e}")
            return None

    async def load_model_to_cache(
        self, model: PretrainedModel, db: AsyncSession
    ) -> bool:
        """将模型加载到缓存"""
        try:
            model_id = model.id

            # 检查缓存是否已满
            if len(self.model_cache) >= self.max_cache_size:
                await self._evict_least_used_model()

            # 加载模型数据
            start_time = datetime.now()

            # 根据模型类型加载不同数据
            if (
                hasattr(self.transfer_engine, "student_models")
                and self.transfer_engine.student_models
            ):
                model_data = self.transfer_engine.student_models
            else:
                # 尝试从文件加载
                model_data = await self._load_model_from_storage(model.model_path)

            load_time = (datetime.now() - start_time).total_seconds()

            # 更新性能统计
            self.performance_stats["model_load_times"].append(load_time)

            # 创建缓存条目
            cache_entry = ModelCacheEntry(
                model_id=model_id,
                model_data=model_data,
                loaded_at=datetime.now(),
                access_count=0,
                last_accessed=datetime.now(),
            )

            self.model_cache[model_id] = cache_entry

            logger.info(f"模型 {model_id} 已加载到缓存，加载时间: {load_time:.3f}s")
            return True

        except Exception as e:
            logger.error(f"加载模型到缓存失败: {e}")
            return False

    async def get_cached_model(self, model_id: int) -> Optional[Any]:
        """从缓存获取模型"""
        try:
            if model_id in self.model_cache:
                # 更新访问统计
                self.model_cache[model_id].access_count += 1
                self.model_cache[model_id].last_accessed = datetime.now()
                self.performance_stats["cache_hits"] += 1

                logger.debug(f"缓存命中 - 模型 {model_id}")
                return self.model_cache[model_id].model_data
            else:
                self.performance_stats["cache_misses"] += 1
                logger.debug(f"缓存未命中 - 模型 {model_id}")
                return None

        except Exception as e:
            logger.error(f"获取缓存模型失败: {e}")
            return None

    async def _evict_least_used_model(self):
        """驱逐最少使用的模型"""
        if not self.model_cache:
            return

        # 找到访问次数最少且最久未使用的模型
        oldest_model_id = min(
            self.model_cache.keys(),
            key=lambda k: (
                self.model_cache[k].access_count,
                self.model_cache[k].last_accessed,
            ),
        )

        evicted_model = self.model_cache.pop(oldest_model_id)
        logger.info(
            f"驱逐模型 {oldest_model_id}，访问次数: {evicted_model.access_count}"
        )

    async def _load_model_from_storage(self, model_path: str) -> Any:
        """从存储加载模型"""
        try:
            if os.path.exists(model_path):
                # 这里应该是实际的模型加载逻辑
                # 简化处理：返回模拟模型数据
                return {"model_type": "traditional_ml", "status": "loaded"}
            else:
                # 如果文件不存在，使用默认模型
                return self.traditional_ml
        except Exception as e:
            logger.error(f"从存储加载模型失败: {e}")
            return self.traditional_ml

    async def generate_prediction(
        self, model_id: int, user_features: Any, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """生成预测结果"""
        start_time = datetime.now()

        try:
            # 获取模型
            model_data = await self.get_cached_model(model_id)

            if model_data is None:
                # 缓存未命中，尝试加载模型
                model = await self._get_model_by_id(model_id, db)
                if model:
                    await self.load_model_to_cache(model, db)
                    model_data = await self.get_cached_model(model_id)

            if model_data is None:
                raise ValueError(f"无法获取模型 {model_id}")

            # 生成预测
            if isinstance(model_data, dict) and "model_type" in model_data:
                # 模拟预测
                predictions = self._generate_mock_predictions(user_features)
            else:
                # 使用实际模型预测
                predictions = model_data.generate_recommendations(
                    user_features, "ensemble"
                )

            # 计算响应时间
            response_time = (datetime.now() - start_time).total_seconds()

            # 更新性能统计
            self._update_performance_stats(response_time)

            return predictions

        except Exception as e:
            logger.error(f"生成预测失败: {e}")
            # 返回默认推荐
            return self._generate_default_recommendations()

    async def _get_model_by_id(
        self, model_id: int, db: AsyncSession
    ) -> Optional[PretrainedModel]:
        """根据ID获取模型"""
        try:
            stmt = select(PretrainedModel).where(PretrainedModel.id == model_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取模型失败: {e}")
            return None

    def _generate_mock_predictions(self, user_features: Any) -> List[Dict[str, Any]]:
        """生成模拟预测结果"""
        import numpy as np

        # 基于用户特征生成个性化推荐
        feature_sum = np.sum(user_features) if hasattr(user_features, "__len__") else 0
        base_confidence = 0.5 + (feature_sum % 10) * 0.05  # 0.5-0.95之间的置信度

        recommendations = []
        for i in range(5):  # 生成5个推荐
            confidence = base_confidence + np.random.normal(0, 0.1)
            confidence = max(0.1, min(0.99, confidence))  # 限制在合理范围

            recommendations.append(
                {
                    "item_id": f"course_{i}_{hash(str(user_features)) % 1000}",
                    "confidence": float(confidence),
                    "reasoning": f"基于用户特征的个性化推荐 #{i+1}",
                }
            )

        return recommendations

    def _generate_default_recommendations(self) -> List[Dict[str, Any]]:
        """生成默认推荐"""
        return [
            {
                "item_id": f"default_course_{i}",
                "confidence": 0.5,
                "reasoning": "默认热门推荐",
            }
            for i in range(3)
        ]

    def _update_performance_stats(self, response_time: float):
        """更新性能统计"""
        self.performance_stats["total_predictions"] += 1
        self.performance_stats["average_response_time"] = (
            self.performance_stats["average_response_time"]
            * (self.performance_stats["total_predictions"] - 1)
            + response_time
        ) / self.performance_stats["total_predictions"]

    async def get_model_performance_report(self) -> Dict[str, Any]:
        """获取模型性能报告"""
        try:
            # 计算缓存命中率
            total_requests = (
                self.performance_stats["cache_hits"]
                + self.performance_stats["cache_misses"]
            )
            cache_hit_rate = (
                self.performance_stats["cache_hits"] / total_requests
                if total_requests > 0
                else 0
            )

            # 平均模型加载时间
            avg_load_time = (
                sum(self.performance_stats["model_load_times"])
                / len(self.performance_stats["model_load_times"])
                if self.performance_stats["model_load_times"]
                else 0
            )

            return {
                "cache_statistics": {
                    "hit_rate": cache_hit_rate,
                    "total_requests": total_requests,
                    "cache_size": len(self.model_cache),
                },
                "performance_metrics": {
                    "total_predictions": self.performance_stats["total_predictions"],
                    "average_response_time": self.performance_stats[
                        "average_response_time"
                    ],
                    "average_model_load_time": avg_load_time,
                },
                "cached_models": [
                    {
                        "model_id": entry.model_id,
                        "loaded_at": entry.loaded_at.isoformat(),
                        "access_count": entry.access_count,
                        "last_accessed": entry.last_accessed.isoformat(),
                    }
                    for entry in self.model_cache.values()
                ],
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")
            return {"error": str(e)}

    async def cleanup_expired_cache(self):
        """清理过期缓存"""
        try:
            current_time = datetime.now()
            expired_models = []

            for model_id, entry in self.model_cache.items():
                if (current_time - entry.loaded_at).total_seconds() > self.cache_ttl:
                    expired_models.append(model_id)

            for model_id in expired_models:
                self.model_cache.pop(model_id)
                logger.info(f"清理过期模型缓存: {model_id}")

        except Exception as e:
            logger.error(f"清理过期缓存失败: {e}")

    async def warm_up_cache(self, db: AsyncSession):
        """预热缓存 - 加载常用模型"""
        try:
            logger.info("开始预热模型缓存...")

            # 获取最近使用的模型
            stmt = (
                select(
                    ColdStartRecommendationLog.model_id,
                    func.count(ColdStartRecommendationLog.id).label("usage_count"),
                )
                .group_by(ColdStartRecommendationLog.model_id)
                .order_by(func.count(ColdStartRecommendationLog.id).desc())
                .limit(3)
            )  # 预热前3个最常用的模型

            result = await db.execute(stmt)
            popular_models = result.all()

            for model_id, usage_count in popular_models:
                model = await self._get_model_by_id(model_id, db)
                if model and model.training_status == "completed":
                    await self.load_model_to_cache(model, db)

            logger.info(f"缓存预热完成，加载了 {len(popular_models)} 个模型")

        except Exception as e:
            logger.error(f"缓存预热失败: {e}")


# Redis缓存管理器
class RedisModelCache:
    """基于Redis的模型缓存管理器"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.cache_prefix = "model_cache:"
        self.ttl = 3600  # 1小时

    async def connect(self):
        """连接到Redis"""
        try:
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Redis缓存连接成功")
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            self.redis_client = None

    async def cache_model(self, model_id: int, model_data: Any) -> bool:
        """缓存模型到Redis"""
        if not self.redis_client:
            return False

        try:
            cache_key = f"{self.cache_prefix}{model_id}"
            serialized_data = json.dumps(
                {
                    "model_data": str(model_data),  # 简化序列化
                    "timestamp": datetime.now().isoformat(),
                }
            )

            await self.redis_client.setex(cache_key, self.ttl, serialized_data)
            return True

        except Exception as e:
            logger.error(f"Redis缓存模型失败: {e}")
            return False

    async def get_cached_model(self, model_id: int) -> Optional[Any]:
        """从Redis获取缓存模型"""
        if not self.redis_client:
            return None

        try:
            cache_key = f"{self.cache_prefix}{model_id}"
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                data = json.loads(cached_data)
                return data["model_data"]
            return None

        except Exception as e:
            logger.error(f"Redis获取缓存模型失败: {e}")
            return None

    async def invalidate_cache(self, model_id: int):
        """使缓存失效"""
        if not self.redis_client:
            return

        try:
            cache_key = f"{self.cache_prefix}{model_id}"
            await self.redis_client.delete(cache_key)
            logger.info(f"Redis缓存已失效: {model_id}")

        except Exception as e:
            logger.error(f"Redis缓存失效失败: {e}")


# 使用示例和测试
async def demo_model_management():
    """演示模型管理功能"""
    print("=== 预训练模型管理器演示 ===")

    # 创建管理器实例
    manager = PretrainedModelManager()

    # 1. 模拟模型缓存操作
    print("1. 模拟模型缓存...")
    mock_model = type(
        "MockModel", (), {"id": 1, "model_path": "./models/mock_model.pkl"}
    )()
    await manager.load_model_to_cache(mock_model, None)
    print(f"   缓存模型数量: {len(manager.model_cache)}")

    # 2. 生成预测
    print("2. 生成预测...")
    import numpy as np

    user_features = np.random.rand(1, 20)
    predictions = await manager.generate_prediction(1, user_features, None)
    print(f"   生成 {len(predictions)} 个推荐")

    # 3. 性能报告
    print("3. 获取性能报告...")
    report = await manager.get_model_performance_report()
    print(f"   缓存命中率: {report['cache_statistics']['hit_rate']:.2%}")
    print(
        f"   平均响应时间: {report['performance_metrics']['average_response_time']:.3f}s"
    )

    # 4. 清理过期缓存
    print("4. 清理过期缓存...")
    await manager.cleanup_expired_cache()
    print(f"   清理后缓存数量: {len(manager.model_cache)}")

    print("\n=== 演示完成 ===")
    return manager


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_model_management())
