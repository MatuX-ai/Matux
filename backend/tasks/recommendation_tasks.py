"""
推荐系统任务管道
处理异步推荐计算、模型训练和缓存预热等任务
"""

import asyncio
from datetime import datetime, timedelta
import json
import logging
from typing import Any, Dict, List

from redis.redis_client import get_redis_client
from sqlalchemy.ext.asyncio import AsyncSession

from ai_service.recommendation_service import RecommendationEngine
from models.recommendation import RecommendationFeedback
from models.user import User
from utils.database import get_db

logger = logging.getLogger(__name__)


class RecommendationTaskPipeline:
    """推荐任务管道管理器"""

    def __init__(self):
        self.engine = RecommendationEngine()
        self.redis_client = get_redis_client()
        self.task_registry = {}

    async def register_task(
        self, task_name: str, task_func, schedule_interval: int = 3600
    ):
        """注册定时任务"""
        self.task_registry[task_name] = {
            "func": task_func,
            "interval": schedule_interval,
            "last_run": None,
        }
        logger.info(f"任务已注册: {task_name} (间隔: {schedule_interval}s)")

    async def start_pipeline(self):
        """启动任务管道"""
        logger.info("启动推荐任务管道...")

        # 注册默认任务
        await self.register_task(
            "model_training", self.train_recommendation_model, 86400
        )  # 每24小时
        await self.register_task(
            "cache_warming", self.warm_recommendation_cache, 3600
        )  # 每小时
        await self.register_task(
            "data_collection", self.collect_user_behavior_data, 1800
        )  # 每30分钟
        await self.register_task(
            "model_update", self.update_model_with_feedback, 900
        )  # 每15分钟

        # 启动定时任务循环
        await self._run_scheduled_tasks()

    async def _run_scheduled_tasks(self):
        """运行定时任务"""
        while True:
            try:
                current_time = datetime.utcnow()

                for task_name, task_info in self.task_registry.items():
                    if (
                        task_info["last_run"] is None
                        or (current_time - task_info["last_run"]).seconds
                        >= task_info["interval"]
                    ):

                        logger.info(f"执行任务: {task_name}")
                        try:
                            await task_info["func"]()
                            task_info["last_run"] = current_time
                            logger.info(f"任务完成: {task_name}")
                        except Exception as e:
                            logger.error(f"任务执行失败 {task_name}: {e}")

                # 每分钟检查一次
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"任务管道错误: {e}")
                await asyncio.sleep(60)

    async def train_recommendation_model(self):
        """训练推荐模型"""
        try:
            logger.info("开始训练推荐模型...")

            async with get_db() as db:
                # 初始化并训练模型
                await self.engine.initialize(db)

                # 保存模型
                self.engine.save_model()

                # 更新Redis中的模型版本信息
                model_info = {
                    "version": datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
                    "trained_at": datetime.utcnow().isoformat(),
                    "user_count": len(self.engine.user_profiles),
                    "course_count": len(self.engine.course_features),
                }

                await self.redis_client.setex(
                    "recommendation:model_info",
                    86400,  # 24小时过期
                    json.dumps(model_info),
                )

                logger.info("推荐模型训练完成")

        except Exception as e:
            logger.error(f"模型训练失败: {e}")

    async def warm_recommendation_cache(self):
        """预热推荐缓存"""
        try:
            logger.info("开始预热推荐缓存...")

            async with get_db() as db:
                # 获取活跃用户
                active_users = await self._get_active_users(db, hours=24)
                logger.info(f"找到 {len(active_users)} 个活跃用户")

                # 为每个活跃用户生成推荐并缓存
                cache_count = 0
                for user in active_users[:100]:  # 限制预热用户数量
                    try:
                        recommendations = await self.engine.get_recommendations(
                            user.id, db, num_recommendations=10
                        )

                        # 缓存推荐结果
                        cache_key = f"recommendations:user:{user.id}"
                        await self.redis_client.setex(
                            cache_key,
                            3600,  # 1小时过期
                            json.dumps(
                                {
                                    "recommendations": recommendations,
                                    "generated_at": datetime.utcnow().isoformat(),
                                    "user_id": user.id,
                                }
                            ),
                        )

                        cache_count += 1

                    except Exception as e:
                        logger.warning(f"为用户 {user.id} 预热缓存失败: {e}")
                        continue

                logger.info(f"推荐缓存预热完成，共缓存 {cache_count} 个用户")

        except Exception as e:
            logger.error(f"缓存预热失败: {e}")

    async def collect_user_behavior_data(self):
        """收集用户行为数据"""
        try:
            logger.info("开始收集用户行为数据...")

            async with get_db() as db:
                # 收集最近的行为数据
                behavior_data = await self._collect_recent_behaviors(db, hours=24)

                # 存储到Redis用于实时分析
                behavior_key = f"user_behaviors:{datetime.utcnow().strftime('%Y%m%d')}"
                await self.redis_client.lpush(
                    behavior_key, *[json.dumps(behavior) for behavior in behavior_data]
                )

                # 设置过期时间（保留7天）
                await self.redis_client.expire(behavior_key, 604800)

                # 更新用户画像统计
                await self._update_user_profile_stats(db, behavior_data)

                logger.info(f"收集了 {len(behavior_data)} 条用户行为数据")

        except Exception as e:
            logger.error(f"行为数据收集失败: {e}")

    async def update_model_with_feedback(self):
        """根据反馈更新模型"""
        try:
            logger.info("开始处理用户反馈...")

            async with get_db() as db:
                # 获取最近的反馈数据
                recent_feedback = await self._get_recent_feedback(db, hours=24)

                if not recent_feedback:
                    logger.info("没有新的反馈数据")
                    return

                # 批量处理反馈
                for feedback in recent_feedback:
                    try:
                        await self.engine.update_model_with_feedback(
                            feedback.user_id,
                            feedback.recommended_course_id,
                            feedback.feedback_type,
                            db,
                        )
                    except Exception as e:
                        logger.warning(f"处理反馈失败 {feedback.id}: {e}")
                        continue

                logger.info(f"处理了 {len(recent_feedback)} 条用户反馈")

        except Exception as e:
            logger.error(f"反馈处理失败: {e}")

    async def generate_personalized_recommendations(
        self, user_id: str, force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """生成个性化推荐"""
        try:
            # 检查缓存
            cache_key = f"recommendations:user:{user_id}"

            if not force_refresh:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    cached_result = json.loads(cached_data)
                    # 检查缓存是否过期（1小时内）
                    cache_time = datetime.fromisoformat(cached_result["generated_at"])
                    if datetime.utcnow() - cache_time < timedelta(hours=1):
                        logger.info(f"使用缓存推荐: {user_id}")
                        return cached_result["recommendations"]

            # 生成新的推荐
            async with get_db() as db:
                recommendations = await self.engine.get_recommendations(
                    user_id, db, num_recommendations=10
                )

                # 更新缓存
                await self.redis_client.setex(
                    cache_key,
                    3600,
                    json.dumps(
                        {
                            "recommendations": recommendations,
                            "generated_at": datetime.utcnow().isoformat(),
                            "user_id": user_id,
                        }
                    ),
                )

                return recommendations

        except Exception as e:
            logger.error(f"生成个性化推荐失败: {e}")
            return []

    async def batch_generate_recommendations(
        self, user_ids: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """批量生成推荐"""
        try:
            results = {}

            # 并发生成推荐
            tasks = [
                self.generate_personalized_recommendations(user_id)
                for user_id in user_ids
            ]

            recommendations_list = await asyncio.gather(*tasks, return_exceptions=True)

            for user_id, recommendations in zip(user_ids, recommendations_list):
                if isinstance(recommendations, Exception):
                    logger.error(f"为用户 {user_id} 生成推荐失败: {recommendations}")
                    results[user_id] = []
                else:
                    results[user_id] = recommendations

            return results

        except Exception as e:
            logger.error(f"批量生成推荐失败: {e}")
            return {}

    # 辅助方法
    async def _get_active_users(self, db: AsyncSession, hours: int = 24) -> List[User]:
        """获取活跃用户"""
        try:
            from datetime import datetime, timedelta

            from sqlalchemy import select

            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # 这里应该查询最近有活动的用户
            # 由于缺少具体的行为表，暂时返回所有用户
            result = await db.execute(select(User))
            return result.scalars().all()

        except Exception as e:
            logger.error(f"获取活跃用户失败: {e}")
            return []

    async def _collect_recent_behaviors(
        self, db: AsyncSession, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """收集最近的用户行为"""
        try:
            behaviors = []

            # 这里应该从各种行为表收集数据
            # 包括课程学习记录、内容访问记录、搜索记录等
            from models.recommendation import LearningRecord

            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            result = await db.execute(
                select(LearningRecord).where(LearningRecord.timestamp >= cutoff_time)
            )
            learning_records = result.scalars().all()

            for record in learning_records:
                behaviors.append(
                    {
                        "user_id": record.user_id,
                        "course_id": record.course_id,
                        "action": "learning_progress",
                        "progress": record.progress,
                        "timestamp": record.timestamp.isoformat(),
                    }
                )

            return behaviors

        except Exception as e:
            logger.error(f"收集行为数据失败: {e}")
            return []

    async def _update_user_profile_stats(
        self, db: AsyncSession, behaviors: List[Dict[str, Any]]
    ):
        """更新用户画像统计"""
        try:
            # 按用户分组行为数据
            user_stats = {}
            for behavior in behaviors:
                user_id = behavior["user_id"]
                if user_id not in user_stats:
                    user_stats[user_id] = {
                        "total_actions": 0,
                        "course_interactions": set(),
                        "last_activity": behavior["timestamp"],
                    }

                user_stats[user_id]["total_actions"] += 1
                if "course_id" in behavior:
                    user_stats[user_id]["course_interactions"].add(
                        behavior["course_id"]
                    )

                # 更新最后活动时间
                if behavior["timestamp"] > user_stats[user_id]["last_activity"]:
                    user_stats[user_id]["last_activity"] = behavior["timestamp"]

            # 存储统计信息到Redis
            for user_id, stats in user_stats.items():
                stats_key = f"user_stats:{user_id}"
                stats_data = {
                    "total_actions": stats["total_actions"],
                    "unique_courses": len(stats["course_interactions"]),
                    "last_activity": stats["last_activity"],
                }

                await self.redis_client.setex(
                    stats_key, 86400, json.dumps(stats_data)  # 24小时过期
                )

        except Exception as e:
            logger.error(f"更新用户画像统计失败: {e}")

    async def _get_recent_feedback(
        self, db: AsyncSession, hours: int = 24
    ) -> List[RecommendationFeedback]:
        """获取最近的反馈数据"""
        try:
            from datetime import datetime, timedelta

            from sqlalchemy import select

            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            result = await db.execute(
                select(RecommendationFeedback).where(
                    RecommendationFeedback.timestamp >= cutoff_time
                )
            )

            return result.scalars().all()

        except Exception as e:
            logger.error(f"获取反馈数据失败: {e}")
            return []


# 全局任务管道实例
recommendation_pipeline = RecommendationTaskPipeline()


def get_recommendation_pipeline() -> RecommendationTaskPipeline:
    """获取推荐任务管道实例"""
    return recommendation_pipeline


# Celery任务定义（如果使用Celery）
try:
    from celery_app import celery

    @celery.task
    def train_model_task():
        """Celery训练模型任务"""

        async def _train():
            pipeline = get_recommendation_pipeline()
            await pipeline.train_recommendation_model()

        asyncio.run(_train())

    @celery.task
    def warm_cache_task():
        """Celery缓存预热任务"""

        async def _warm():
            pipeline = get_recommendation_pipeline()
            await pipeline.warm_recommendation_cache()

        asyncio.run(_warm())

except ImportError:
    logger.info("Celery未安装，跳过Celery任务定义")
