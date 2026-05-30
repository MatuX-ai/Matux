"""
AI教学推荐服务
基于协同过滤和内容推荐的混合推荐系统
"""

from datetime import datetime
from functools import wraps
import logging
import os
import pickle
from typing import Any, Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors


# 临时占位符，避免 NameError
def monitor_ai_operation(operation_name: str):
    """AI 操作监控装饰器 (临时占位)"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.transfer_learning_config import settings as tl_settings
from models.content_store import ContentItem, ContentRating
from models.recommendation import (
    CourseFeature,
)
from models.subscription import SubscriptionStatus, UserSubscription
from .difficulty_calculator import DifficultyCalculator
from .knowledge_graph_manager import KnowledgeGraphManager

# 导入新增的自适应学习功能
from .markov_analyzer import MarkovChainAnalyzer
from .model_compressor import ModelCompressor

# 导入预训练模型相关组件
from .transfer_learning_engine import TransferLearningEngine

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """推荐引擎核心类"""

    def __init__(self, model_path: str = "./models/recommendation_model.pkl"):
        self.model = NearestNeighbors(n_neighbors=10, metric="cosine")
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words="english")
        self.model_path = model_path
        self.is_trained = False
        self.user_profiles = {}
        self.course_features = {}
        self.content_store_features = {}
        self.interaction_matrix = None

        # 内容商店推荐相关
        self.content_access_weights = {
            ContentRating.FREE: 1.0,
            ContentRating.BASIC: 1.2,
            ContentRating.PROFESSIONAL: 1.5,
            ContentRating.ENTERPRISE: 2.0,
        }

        # 订阅等级权重
        self.subscription_weights = {
            "basic": 1.0,
            "professional": 1.3,
            "enterprise": 1.6,
        }

        # 初始化自适应学习组件
        self.markov_analyzer = MarkovChainAnalyzer(window_size=30, min_events=5)
        self.knowledge_graph = KnowledgeGraphManager()
        self.difficulty_calculator = DifficultyCalculator(
            smoothing_factor=0.3, min_samples=5
        )

        # 初始化预训练模型组件
        self.transfer_learning_engine = TransferLearningEngine(tl_settings)
        self.model_compressor = ModelCompressor(tl_settings)
        self.pretrained_models_available = False

    async def initialize(self, db: AsyncSession):
        """初始化推荐引擎，加载训练数据"""
        try:
            await self._load_training_data(db)
            if len(self.user_profiles) > 0 and len(self.course_features) > 0:
                self._train_model()
                self.is_trained = True
                logger.info("推荐引擎初始化完成")
            else:
                logger.warning("训练数据不足，推荐引擎未完全初始化")
        except Exception as e:
            logger.error(f"推荐引擎初始化失败: {e}")

    async def _load_training_data(self, db: AsyncSession):
        """加载训练数据"""
        # 加载用户学习记录
        result = await db.execute(select(LearningRecord))
        learning_records = result.scalars().all()

        # 加载用户画像
        result = await db.execute(select(UserLearningProfile))
        user_profiles = result.scalars().all()

        # 加载课程特征
        result = await db.execute(select(CourseFeature))
        course_features = result.scalars().all()

        # 构建用户画像字典
        for profile in user_profiles:
            self.user_profiles[profile.user_id] = {
                "learning_preferences": profile.learning_preferences or {},
                "skill_levels": profile.skill_levels or {},
                "interests": profile.interests or [],
                "learning_history_vector": profile.learning_history_vector or [],
            }

        # 构建课程特征字典
        for course in course_features:
            self.course_features[course.course_id] = {
                "title": course.title,
                "description": course.description or "",
                "category": course.category or "",
                "difficulty_level": course.difficulty_level or "beginner",
                "tags": course.tags or [],
                "feature_vector": course.feature_vector or [],
                "popularity_score": course.popularity_score or 0.0,
            }

        # 构建用户-课程交互矩阵
        self._build_interaction_matrix(learning_records)

    def _build_interaction_matrix(self, learning_records: list):
        """构建用户-课程交互矩阵"""
        if not learning_records:
            return

        # 创建用户和课程索引映射
        unique_users = list(set(record.user_id for record in learning_records))
        unique_courses = list(set(record.course_id for record in learning_records))

        self.user_index_map = {user_id: idx for idx, user_id in enumerate(unique_users)}
        self.course_index_map = {
            course_id: idx for idx, course_id in enumerate(unique_courses)
        }

        # 初始化交互矩阵
        num_users = len(unique_users)
        num_courses = len(unique_courses)
        self.interaction_matrix = np.zeros((num_users, num_courses))

        # 填充交互矩阵
        for record in learning_records:
            user_idx = self.user_index_map.get(record.user_id)
            course_idx = self.course_index_map.get(record.course_id)
            if user_idx is not None and course_idx is not None:
                # 使用进度和时长作为交互强度
                interaction_strength = record.progress * (
                    record.time_spent / 60.0
                )  # 标准化时长
                self.interaction_matrix[user_idx, course_idx] = interaction_strength

    def _train_model(self):
        """训练推荐模型"""
        if self.interaction_matrix is None or len(self.interaction_matrix) == 0:
            return

        # 训练协同过滤模型
        self.model.fit(self.interaction_matrix)

        # 准备内容推荐的文本特征
        course_descriptions = []
        course_ids = []
        for course_id, features in self.course_features.items():
            text = f"{features['title']} {features['description']} {' '.join(features['tags'])}"
            course_descriptions.append(text)
            course_ids.append(course_id)

        if course_descriptions:
            self.content_features = self.tfidf_vectorizer.fit_transform(
                course_descriptions
            )
            self.course_ids_for_content = course_ids

    @monitor_ai_operation("recommendation_engine")
    async def get_adaptive_recommendations(
        self, user_id: str, db: AsyncSession, num_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """获取自适应学习路径推荐

        Args:
            user_id: 用户ID
            db: 数据库会话
            num_recommendations: 推荐数量

        Returns:
            List[Dict]: 自适应推荐结果
        """
        recommendations = []

        try:
            # 1. 分析用户行为模式
            behavior_analysis = self.markov_analyzer.analyze_user_behavior(user_id)

            # 2. 获取用户画像
            user_profile = await self._get_enhanced_user_profile(user_id, db)

            # 3. 基于知识图谱的路径推荐
            if (
                hasattr(self.knowledge_graph, "_mock_mode")
                and not self.knowledge_graph._mock_mode
            ):
                learning_path = self.knowledge_graph.recommend_learning_path(
                    user_profile,
                    target_expertise=user_profile.get("primary_interest", "general"),
                    max_path_length=num_recommendations * 2,
                )

                if learning_path:
                    # 将路径转换为推荐格式
                    path_recommendations = []
                    for i, node_id in enumerate(
                        learning_path.nodes[:num_recommendations]
                    ):
                        path_recommendations.append(
                            {
                                "course_id": node_id,
                                "score": learning_path.confidence_score
                                * (1 - i * 0.1),  # 递减权重
                                "type": "knowledge_graph_path",
                                "estimated_hours": learning_path.total_estimated_hours
                                / len(learning_path.nodes),
                                "reasoning": f"基于知识图谱的第{i+1}步推荐",
                            }
                        )
                    recommendations.extend(path_recommendations)

            # 4. 结合传统推荐
            traditional_recs = await self.get_recommendations(
                user_id, db, num_recommendations
            )

            # 5. 融合推荐结果
            fused_recommendations = self._fuse_adaptive_recommendations(
                recommendations, traditional_recs, behavior_analysis
            )

            # 6. 应用难度调整
            adjusted_recommendations = await self._apply_difficulty_adjustment(
                user_id, fused_recommendations, db
            )

            return adjusted_recommendations[:num_recommendations]

        except Exception as e:
            logger.error(f"获取自适应推荐失败: {e}")
            # 回退到传统推荐
            return await self.get_recommendations(user_id, db, num_recommendations)

    async def _get_enhanced_user_profile(
        self, user_id: str, db: AsyncSession
    ) -> Dict[str, Any]:
        """获取增强版用户画像"""
        # 获取基础用户画像
        profile = self.user_profiles.get(user_id, {})

        # 添加行为分析结果
        behavior_analysis = self.markov_analyzer.analyze_user_behavior(user_id)

        enhanced_profile = {
            "user_id": user_id,
            "base_profile": profile,
            "behavior_insights": {
                "failure_rate": behavior_analysis.failure_rate,
                "skip_rate": behavior_analysis.skip_rate,
                "patterns": [
                    p.pattern_id for p in [behavior_analysis.most_common_pattern] if p
                ],
                "anomaly_detected": behavior_analysis.anomaly_detected,
            },
            "skills": profile.get("skill_levels", {}),
            "interests": profile.get("interests", []),
            "primary_interest": (
                profile.get("interests", ["general"])[0]
                if profile.get("interests")
                else "general"
            ),
        }

        return enhanced_profile

    def _fuse_adaptive_recommendations(
        self, adaptive_recs: List[Dict], traditional_recs: List[Dict], behavior_analysis
    ) -> List[Dict]:
        """融合自适应推荐和传统推荐结果"""
        # 合并所有推荐
        all_recs = {}

        # 处理自适应推荐 (权重0.6)
        for rec in adaptive_recs:
            course_id = rec["course_id"]
            if course_id not in all_recs:
                all_recs[course_id] = {"score": 0, "sources": [], "details": {}}
            all_recs[course_id]["score"] += rec["score"] * 0.6
            all_recs[course_id]["sources"].append("adaptive")
            all_recs[course_id]["details"].update(rec)

        # 处理传统推荐 (权重0.4)
        for rec in traditional_recs:
            course_id = rec["course_id"]
            if course_id not in all_recs:
                all_recs[course_id] = {"score": 0, "sources": [], "details": {}}
            all_recs[course_id]["score"] += rec["score"] * 0.4
            all_recs[course_id]["sources"].append("traditional")
            all_recs[course_id]["details"].update(rec)

        # 转换为列表并排序
        fused_list = [
            {
                "course_id": course_id,
                "score": data["score"],
                "recommendation_sources": data["sources"],
                **data["details"],
            }
            for course_id, data in all_recs.items()
        ]

        return sorted(fused_list, key=lambda x: x["score"], reverse=True)

    async def _apply_difficulty_adjustment(
        self, user_id: str, recommendations: List[Dict], db: AsyncSession
    ) -> List[Dict]:
        """应用难度调整到推荐结果"""
        adjusted_recommendations = []

        for rec in recommendations:
            course_id = rec["course_id"]

            # 获取个性化难度
            personalized_difficulty = (
                self.difficulty_calculator.get_personalized_difficulty(
                    user_id, course_id
                )
            )

            # 应用难度调整
            adjustment = self.difficulty_calculator.adjust_difficulty_for_user(
                user_id, course_id
            )

            # 更新推荐项
            adjusted_rec = rec.copy()
            adjusted_rec["difficulty_score"] = personalized_difficulty
            adjusted_rec["difficulty_adjustment"] = {
                "current": adjustment.current_difficulty,
                "adjusted": adjustment.adjusted_difficulty,
                "reason": adjustment.adjustment_reason,
                "confidence": adjustment.confidence_score,
            }

            # 根据难度调整最终得分
            difficulty_factor = 1.0 / (
                1.0 + personalized_difficulty * 0.1
            )  # 难度越高，得分越低
            adjusted_rec["final_score"] = rec["score"] * difficulty_factor

            adjusted_recommendations.append(adjusted_rec)

        # 按最终得分重新排序
        return sorted(
            adjusted_recommendations, key=lambda x: x["final_score"], reverse=True
        )

    async def _get_user_subscription_level(self, user_id: str, db: AsyncSession) -> str:
        """获取用户订阅等级"""
        try:
            subscription_query = select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.status.in_(
                    [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
                ),
            )
            subscription_result = await db.execute(subscription_query)
            subscription = subscription_result.scalar_one_or_none()

            if subscription and subscription.plan:
                return subscription.plan.plan_type.value
            return "free"  # 默认免费等级
        except Exception as e:
            logger.error(f"获取用户订阅等级失败: {e}")
            return "free"

    async def _content_store_recommendations(
        self,
        user_id: str,
        subscription_level: str,
        db: AsyncSession,
        num_recommendations: int,
    ) -> List[Dict[str, Any]]:
        """内容商店推荐"""
        try:
            # 获取用户画像偏好
            user_profile = self.user_profiles.get(user_id, {})
            user_interests = user_profile.get("interests", [])
            user_profile.get("learning_preferences", {})

            # 查询符合条件的内容商品
            content_query = (
                select(ContentItem)
                .where(
                    ContentItem.status == "published", ContentItem.is_featured == True
                )
                .order_by(
                    ContentItem.purchase_count.desc(), ContentItem.rating_score.desc()
                )
            )

            content_result = await db.execute(content_query)
            contents = content_result.scalars().all()

            # 计算推荐分数
            recommendations = []
            subscription_weight = self.subscription_weights.get(subscription_level, 1.0)

            for content in contents[: num_recommendations * 3]:  # 获取更多候选内容
                # 基础分数
                base_score = (
                    content.rating_score * 0.4
                    + (content.purchase_count / 1000) * 0.3
                    + (content.view_count / 10000) * 0.3
                )

                # 订阅等级权重
                access_weight = self.content_access_weights.get(content.rating, 1.0)
                subscription_adjustment = min(
                    subscription_weight / access_weight, 2.0
                )  # 最大2倍调整

                # 兴趣匹配度
                interest_match = self._calculate_interest_match(content, user_interests)

                # 最终分数
                final_score = (
                    base_score * subscription_adjustment * (1 + interest_match * 0.5)
                )

                recommendations.append(
                    {
                        "content_id": content.content_id,
                        "title": content.title,
                        "type": "content_store",
                        "content_type": content.content_type.value,
                        "rating_required": content.rating.value,
                        "score": final_score,
                        "base_score": base_score,
                        "subscription_adjustment": subscription_adjustment,
                        "interest_match": interest_match,
                    }
                )

            # 按分数排序并返回前N个
            return sorted(recommendations, key=lambda x: x["score"], reverse=True)[
                :num_recommendations
            ]

        except Exception as e:
            logger.error(f"内容商店推荐失败: {e}")
            return []

    def _calculate_interest_match(
        self, content: ContentItem, user_interests: List[str]
    ) -> float:
        """计算内容与用户兴趣的匹配度"""
        try:
            # 基于标签计算匹配度
            content_tags = (
                [tag_assoc.tag.name.lower() for tag_assoc in content.tags]
                if content.tags
                else []
            )
            user_interests_lower = [interest.lower() for interest in user_interests]

            if not content_tags or not user_interests_lower:
                return 0.0

            # 计算交集比例
            intersection = set(content_tags) & set(user_interests_lower)
            match_score = len(intersection) / len(
                set(content_tags) | set(user_interests_lower)
            )

            return match_score
        except Exception:
            return 0.0

    @monitor_ai_operation("recommendation_engine")
    async def get_recommendations(
        self, user_id: str, db: AsyncSession, num_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """获取用户推荐课程 - 增强版，支持预训练模型"""
        if not self.is_trained:
            await self.initialize(db)

        recommendations = []

        try:
            # 检查是否可以使用预训练模型
            use_pretrained_model = await self._should_use_pretrained_model(user_id, db)

            if use_pretrained_model:
                # 使用预训练模型生成推荐
                pretrained_recs = await self._get_pretrained_model_recommendations(
                    user_id, db, num_recommendations
                )
                if pretrained_recs:
                    recommendations = pretrained_recs
                    logger.info(f"使用预训练模型为用户 {user_id} 生成推荐")
                else:
                    # 预训练模型推荐失败，回退到传统方法
                    recommendations = await self._get_traditional_recommendations(
                        user_id, db, num_recommendations
                    )
            else:
                # 使用传统推荐方法
                recommendations = await self._get_traditional_recommendations(
                    user_id, db, num_recommendations
                )

        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            # 返回热门课程作为后备方案
            recommendations = await self._get_popular_courses(num_recommendations, db)

        return recommendations[:num_recommendations]

    async def _should_use_pretrained_model(
        self, user_id: str, db: AsyncSession
    ) -> bool:
        """判断是否应该使用预训练模型"""
        try:
            # 检查是否有可用的预训练模型
            from sqlalchemy import select

            from models.recommendation import PretrainedModel

            stmt = (
                select(PretrainedModel)
                .where(PretrainedModel.training_status == "completed")
                .order_by(PretrainedModel.created_at.desc())
                .limit(1)
            )

            result = await db.execute(stmt)
            latest_model = result.scalar_one_or_none()

            if not latest_model:
                return False

            # 检查用户是否为冷启动用户
            # 冷启动用户或模型性能足够好时使用预训练模型
            # TODO: LearningRecord 模型暂时缺失，返回 True 使用预训练模型
            return True

        except Exception as e:
            logger.error(f"检查预训练模型使用条件失败: {e}")
            return False

    async def _get_pretrained_model_recommendations(
        self, user_id: str, db: AsyncSession, num_recommendations: int
    ) -> List[Dict[str, Any]]:
        """使用预训练模型生成推荐"""
        try:
            # 获取用户特征
            user_features = await self._extract_user_features_for_model(user_id, db)

            # 生成推荐
            model_recommendations = (
                self.transfer_learning_engine.generate_recommendations(
                    user_features, "ensemble"
                )
            )

            # 转换为标准推荐格式
            formatted_recommendations = []
            for i, rec in enumerate(model_recommendations[:num_recommendations]):
                formatted_recommendations.append(
                    {
                        "course_id": rec.get("item_id", f"course_{i}"),
                        "score": rec.get("confidence", 0.5),
                        "recommendation_types": ["pretrained_model"],
                        "reasoning": rec.get("reasoning", "基于预训练模型推荐"),
                        "source_model": "transfer_learning_ensemble",
                    }
                )

            return formatted_recommendations

        except Exception as e:
            logger.error(f"预训练模型推荐失败: {e}")
            return []

    async def _get_traditional_recommendations(
        self, user_id: str, db: AsyncSession, num_recommendations: int
    ) -> List[Dict[str, Any]]:
        """传统的推荐方法"""
        # 获取用户订阅信息
        user_subscription_level = await self._get_user_subscription_level(user_id, db)

        # 协同过滤推荐
        cf_recs = await self._collaborative_filtering_recommendations(
            user_id, num_recommendations * 2
        )

        # 内容推荐
        content_recs = await self._content_based_recommendations(
            user_id, num_recommendations * 2
        )

        # 内容商店推荐
        store_recs = await self._content_store_recommendations(
            user_id, user_subscription_level, db, num_recommendations
        )

        # 混合推荐结果
        recommendations = self._hybrid_recommendations(
            cf_recs,
            content_recs,
            num_recommendations,
            store_recs=store_recs,
            subscription_level=user_subscription_level,
        )

        # 过滤已学过的课程
        recommendations = await self._filter_completed_courses(
            user_id, recommendations, db
        )

        # 添加多样性
        recommendations = self._add_diversity(recommendations)

        return recommendations

    async def _extract_user_features_for_model(
        self, user_id: str, db: AsyncSession
    ) -> Any:
        """为预训练模型提取用户特征"""
        try:
            import numpy as np

            # 获取用户基本信息
            from models.recommendation import LearningRecord, UserLearningProfile

            # 获取用户画像
            stmt = select(UserLearningProfile).where(
                UserLearningProfile.user_id == user_id
            )
            result = await db.execute(stmt)
            user_profile = result.scalar_one_or_none()

            # 获取学习记录
            # TODO: LearningRecord 模型暂时缺失，使用空列表
            learning_records = []

            # 构建特征向量
            features = []

            # 基础特征
            features.extend(
                [
                    len(learning_records),  # 学习记录数量
                    (
                        np.mean([rec.progress for rec in learning_records])
                        if learning_records
                        else 0
                    ),  # 平均进度
                    (
                        np.mean([rec.time_spent for rec in learning_records])
                        if learning_records
                        else 0
                    ),  # 平均时长
                ]
            )

            # 技能水平特征
            if user_profile and user_profile.skill_levels:
                skill_avg = np.mean(list(user_profile.skill_levels.values()))
                features.append(skill_avg)
            else:
                features.append(0.5)  # 默认中等水平

            # 兴趣特征
            if user_profile and user_profile.interests:
                interest_count = len(user_profile.interests)
                features.append(min(interest_count / 10.0, 1.0))  # 归一化兴趣数量
            else:
                features.append(0.3)  # 默认兴趣水平

            # 确保特征维度一致
            target_dim = 20
            if len(features) < target_dim:
                features.extend([0.0] * (target_dim - len(features)))
            elif len(features) > target_dim:
                features = features[:target_dim]

            return np.array([features])

        except Exception as e:
            logger.error(f"提取用户特征失败: {e}")
            # 返回默认特征
            import numpy as np

            return np.random.rand(1, 20)

        recommendations = []

        try:
            # 协同过滤推荐
            cf_recs = await self._collaborative_filtering_recommendations(
                user_id, num_recommendations * 2
            )

            # 内容推荐
            content_recs = await self._content_based_recommendations(
                user_id, num_recommendations * 2
            )

            # 混合推荐结果
            recommendations = self._hybrid_recommendations(
                cf_recs, content_recs, num_recommendations
            )

            # 过滤已学过的课程
            recommendations = await self._filter_completed_courses(
                user_id, recommendations, db
            )

            # 添加多样性
            recommendations = self._add_diversity(recommendations)

        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            # 返回热门课程作为后备方案
            recommendations = await self._get_popular_courses(num_recommendations, db)

        return recommendations[:num_recommendations]

    async def _collaborative_filtering_recommendations(
        self, user_id: str, num_candidates: int
    ) -> List[Dict[str, Any]]:
        """协同过滤推荐"""
        if user_id not in self.user_index_map:
            return []

        user_idx = self.user_index_map[user_id]
        user_vector = self.interaction_matrix[user_idx].reshape(1, -1)

        # 找到相似用户
        distances, indices = self.model.kneighbors(
            user_vector, n_neighbors=min(10, len(self.interaction_matrix))
        )

        # 收集候选课程
        candidate_scores = {}
        for idx in indices[0]:
            if idx != user_idx:  # 排除自己
                similarity = 1 / (1 + distances[0][np.where(indices[0] == idx)[0][0]])
                neighbor_interactions = self.interaction_matrix[idx]

                for course_idx, score in enumerate(neighbor_interactions):
                    if (
                        score > 0 and self.interaction_matrix[user_idx][course_idx] == 0
                    ):  # 用户未学过的课程
                        course_id = list(self.course_index_map.keys())[course_idx]
                        if course_id not in candidate_scores:
                            candidate_scores[course_id] = 0
                        candidate_scores[course_id] += score * similarity

        # 排序并返回前N个
        sorted_candidates = sorted(
            candidate_scores.items(), key=lambda x: x[1], reverse=True
        )
        return [
            {"course_id": course_id, "score": score, "type": "collaborative"}
            for course_id, score in sorted_candidates[:num_candidates]
        ]

    async def _content_based_recommendations(
        self, user_id: str, num_candidates: int
    ) -> List[Dict[str, Any]]:
        """基于内容的推荐"""
        if user_id not in self.user_profiles:
            return []

        user_profile = self.user_profiles[user_id]
        user_interests = " ".join(user_profile.get("interests", []))

        if not user_interests or self.content_features is None:
            return []

        # 计算用户兴趣与课程的相似度
        user_vector = self.tfidf_vectorizer.transform([user_interests])
        similarities = cosine_similarity(user_vector, self.content_features).flatten()

        # 获取推荐课程
        candidate_scores = []
        for idx, similarity in enumerate(similarities):
            if similarity > 0:
                course_id = self.course_ids_for_content[idx]
                if course_id in self.course_features:
                    base_score = (
                        similarity * self.course_features[course_id]["popularity_score"]
                    )
                    candidate_scores.append(
                        {"course_id": course_id, "score": base_score, "type": "content"}
                    )

        return sorted(candidate_scores, key=lambda x: x["score"], reverse=True)[
            :num_candidates
        ]

    def _hybrid_recommendations(
        self,
        cf_recs: List[Dict],
        content_recs: List[Dict],
        num_final: int,
        store_recs=None,
        subscription_level=None,
    ) -> List[Dict[str, Any]]:
        """混合推荐结果"""
        # 合并多种推荐结果
        all_recs = {}

        # 处理协同过滤推荐 (40%权重)
        for rec in cf_recs:
            course_id = rec["course_id"]
            if course_id not in all_recs:
                all_recs[course_id] = {"score": 0, "types": [], "details": {}}
            all_recs[course_id]["score"] += rec["score"] * 0.4
            all_recs[course_id]["types"].append("collaborative")
            all_recs[course_id]["details"].update(rec)

        # 处理内容推荐 (30%权重)
        for rec in content_recs:
            course_id = rec["course_id"]
            if course_id not in all_recs:
                all_recs[course_id] = {"score": 0, "types": [], "details": {}}
            all_recs[course_id]["score"] += rec["score"] * 0.3
            all_recs[course_id]["types"].append("content")
            all_recs[course_id]["details"].update(rec)

        # 处理内容商店推荐 (30%权重)
        if store_recs:
            for rec in store_recs:
                content_id = f"store_{rec['content_id']}"  # 使用不同ID空间
                if content_id not in all_recs:
                    all_recs[content_id] = {"score": 0, "types": [], "details": {}}
                all_recs[content_id]["score"] += rec["score"] * 0.3
                all_recs[content_id]["types"].append("content_store")
                all_recs[content_id]["details"].update(rec)

        # 根据订阅等级调整分数
        if subscription_level:
            subscription_boost = self.subscription_weights.get(subscription_level, 1.0)
            for item_id, item_data in all_recs.items():
                # 对内容商店推荐给予订阅等级加成
                if "content_store" in item_data["types"]:
                    item_data["score"] *= subscription_boost

        # 转换为列表并排序
        final_recs = [
            {
                "item_id": item_id,
                "score": data["score"],
                "recommendation_types": data["types"],
                "details": data["details"],
            }
            for course_id, data in all_recs.items()
        ]

        return sorted(final_recs, key=lambda x: x["score"], reverse=True)[:num_final]

    async def _filter_completed_courses(
        self, user_id: str, recommendations: List[Dict], db: AsyncSession
    ) -> List[Dict]:
        """过滤掉用户已完成的课程"""
        # 查询用户已完成的课程
        result = await db.execute(
            select(LearningRecord.course_id)
            .where(LearningRecord.user_id == user_id)
            .where(LearningRecord.completion_status == "completed")
        )
        completed_courses = set(result.scalars().all())

        # 过滤推荐结果
        filtered_recs = [
            rec for rec in recommendations if rec["course_id"] not in completed_courses
        ]

        return filtered_recs

    def _add_diversity(self, recommendations: List[Dict]) -> List[Dict]:
        """增加推荐结果的多样性"""
        if len(recommendations) <= 1:
            return recommendations

        diverse_recs = []
        seen_categories = set()

        for rec in recommendations:
            course_id = rec["course_id"]
            if course_id in self.course_features:
                category = self.course_features[course_id].get("category", "")
                if (
                    category not in seen_categories
                    or len(diverse_recs) < len(recommendations) // 2
                ):
                    diverse_recs.append(rec)
                    seen_categories.add(category)

        # 补充剩余推荐
        remaining_recs = [rec for rec in recommendations if rec not in diverse_recs]
        diverse_recs.extend(remaining_recs)

        return diverse_recs[: len(recommendations)]

    async def _get_popular_courses(
        self, num_recommendations: int, db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """获取热门课程（后备推荐策略）"""
        result = await db.execute(
            select(CourseFeature)
            .order_by(CourseFeature.popularity_score.desc())
            .limit(num_recommendations * 2)
        )
        popular_courses = result.scalars().all()

        return [
            {
                "course_id": course.course_id,
                "score": course.popularity_score,
                "recommendation_types": ["popular"],
            }
            for course in popular_courses
        ][:num_recommendations]

    async def update_user_profile(
        self, user_id: str, learning_record: any, db: AsyncSession
    ):
        """更新用户画像"""
        try:
            # 获取或创建用户画像
            result = await db.execute(
                select(UserLearningProfile).where(
                    UserLearningProfile.user_id == user_id
                )
            )
            profile = result.scalar_one_or_none()

            if not profile:
                profile = UserLearningProfile(user_id=user_id)
                db.add(profile)

            # 更新学习历史向量
            await self._update_learning_history_vector(profile, learning_record, db)

            # 更新技能水平
            await self._update_skill_levels(profile, learning_record)

            profile.last_updated = datetime.utcnow()
            await db.commit()

        except Exception as e:
            await db.rollback()
            logger.error(f"更新用户画像失败: {e}")

    async def _update_learning_history_vector(
        self, profile, learning_record: any, db: AsyncSession
    ):
        """更新学习历史向量"""
        # 获取用户最近的学习记录
        result = await db.execute(
            select(LearningRecord)
            .where(LearningRecord.user_id == profile.user_id)
            .order_by(LearningRecord.created_at.desc())
            .limit(50)  # 最近50条记录
        )
        recent_records = result.scalars().all()

        # 构建学习历史向量
        history_vector = []
        for record in recent_records:
            # 将学习行为编码为向量特征
            features = [
                record.progress,  # 学习进度
                record.time_spent / 60.0,  # 学习时长（小时）
                record.difficulty_rating or 3,  # 难度评分
                record.interest_rating or 3,  # 兴趣评分
            ]
            history_vector.extend(features)

        # 保持向量长度一致
        target_length = 200  # 固定长度
        if len(history_vector) < target_length:
            history_vector.extend([0] * (target_length - len(history_vector)))
        else:
            history_vector = history_vector[:target_length]

        profile.learning_history_vector = history_vector

    async def _update_skill_levels(self, profile, learning_record: any):
        """更新技能水平"""
        # 从课程特征推断涉及的技能
        course_id = learning_record.course_id
        if course_id in self.course_features:
            course_tags = self.course_features[course_id].get("tags", [])

            if not profile.skill_levels:
                profile.skill_levels = {}

            # 根据学习进度更新相关技能水平
            progress_factor = learning_record.progress
            for tag in course_tags:
                current_level = profile.skill_levels.get(tag, 0)
                # 基于学习进度提升技能水平
                new_level = min(10, current_level + (progress_factor * 2))  # 最大10级
                profile.skill_levels[tag] = new_level

    def save_model(self):
        """保存模型到磁盘"""
        try:
            model_data = {
                "model": self.model,
                "tfidf_vectorizer": self.tfidf_vectorizer,
                "user_profiles": self.user_profiles,
                "course_features": self.course_features,
                "interaction_matrix": self.interaction_matrix,
                "user_index_map": getattr(self, "user_index_map", {}),
                "course_index_map": getattr(self, "course_index_map", {}),
                "content_features": getattr(self, "content_features", None),
                "course_ids_for_content": getattr(self, "course_ids_for_content", []),
                "is_trained": self.is_trained,
            }

            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, "wb") as f:
                pickle.dump(model_data, f)
            logger.info(f"推荐模型已保存到 {self.model_path}")

        except Exception as e:
            logger.error(f"保存模型失败: {e}")

    def load_model(self):
        """从磁盘加载模型"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, "rb") as f:
                    model_data = pickle.load(f)

                self.model = model_data["model"]
                self.tfidf_vectorizer = model_data["tfidf_vectorizer"]
                self.user_profiles = model_data["user_profiles"]
                self.course_features = model_data["course_features"]
                self.interaction_matrix = model_data["interaction_matrix"]
                self.user_index_map = model_data["user_index_map"]
                self.course_index_map = model_data["course_index_map"]
                self.content_features = model_data["content_features"]
                self.course_ids_for_content = model_data["course_ids_for_content"]
                self.is_trained = model_data["is_trained"]

                logger.info(f"推荐模型已从 {self.model_path} 加载")
                return True
            else:
                logger.warning(f"模型文件不存在: {self.model_path}")
                return False

        except Exception as e:
            logger.error(f"加载模型失败: {e}")
            return False

    async def _load_content_store_data(self, db: AsyncSession):
        """加载内容商店数据"""
        try:
            # 查询内容商品数据
            from sqlalchemy import select

            result = await db.execute(
                select(ContentItem).where(ContentItem.status == "published")
            )
            contents = result.scalars().all()

            self.content_store_features = {
                content.content_id: {
                    "title": content.title,
                    "description": content.description,
                    "content_type": content.content_type.value,
                    "category_id": content.category_id,
                    "rating_required": content.rating.value,
                    "price": content.price,
                    "is_free": content.is_free,
                    "tags": (
                        [tag_assoc.tag.name for tag_assoc in content.tags]
                        if content.tags
                        else []
                    ),
                    "view_count": content.view_count,
                    "purchase_count": content.purchase_count,
                    "rating_score": content.rating_score,
                }
                for content in contents
            }

            logger.info(f"加载了 {len(self.content_store_features)} 个内容商品特征")

        except Exception as e:
            logger.error(f"加载内容商店数据失败: {e}")

    async def get_cold_start_recommendations(
        self,
        user_profile: Dict[str, Any],
        db: AsyncSession,
        num_recommendations: int = 5,
    ) -> List[Dict[str, Any]]:
        """冷启动用户推荐"""
        try:
            recommendations = []

            # 基于用户画像的兴趣推荐
            user_interests = user_profile.get("interests", [])
            learning_goals = user_profile.get("learning_goals", [])
            user_profile.get("skill_level", "beginner")

            # 推荐热门免费内容
            popular_free_query = (
                select(ContentItem)
                .where(ContentItem.is_free == True, ContentItem.status == "published")
                .order_by(
                    ContentItem.view_count.desc(), ContentItem.rating_score.desc()
                )
                .limit(num_recommendations * 2)
            )

            popular_result = await db.execute(popular_free_query)
            popular_contents = popular_result.scalars().all()

            # 计算匹配分数
            for content in popular_contents:
                interest_match = self._calculate_interest_match(content, user_interests)
                goal_match = self._calculate_goal_match(content, learning_goals)

                # 综合分数
                final_score = (
                    content.rating_score * 0.4 + interest_match * 0.3 + goal_match * 0.3
                )

                recommendations.append(
                    {
                        "item_id": f"store_{content.content_id}",
                        "title": content.title,
                        "type": "content_store",
                        "content_type": content.content_type.value,
                        "score": final_score,
                        "interest_match": interest_match,
                        "goal_match": goal_match,
                    }
                )

            # 按分数排序
            return sorted(recommendations, key=lambda x: x["score"], reverse=True)[
                :num_recommendations
            ]

        except Exception as e:
            logger.error(f"冷启动推荐失败: {e}")
            return []

    def _calculate_goal_match(
        self, content: ContentItem, learning_goals: List[str]
    ) -> float:
        """计算内容与学习目标的匹配度"""
        try:
            content_text = f"{content.title} {content.description}".lower()
            goal_matches = 0

            for goal in learning_goals:
                if goal.lower() in content_text:
                    goal_matches += 1

            return goal_matches / len(learning_goals) if learning_goals else 0.0
        except Exception:
            return 0.0

    async def update_model_with_feedback(
        self, user_id: str, item_id: str, feedback_type: str, db: AsyncSession
    ):
        """根据用户反馈更新推荐模型"""
        try:
            # 记录反馈
            feedback = RecommendationFeedback(
                user_id=user_id,
                recommended_course_id=item_id,  # 兼容字段名
                feedback_type=feedback_type,
                context={"source": "real_time"},
            )

            db.add(feedback)
            await db.commit()

            # 更新用户画像
            if user_id in self.user_profiles:
                profile = self.user_profiles[user_id]
                if "feedback_history" not in profile:
                    profile["feedback_history"] = []

                profile["feedback_history"].append(
                    {
                        "item_id": item_id,
                        "feedback_type": feedback_type,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                # 限制反馈历史长度
                if len(profile["feedback_history"]) > 100:
                    profile["feedback_history"] = profile["feedback_history"][-50:]

            logger.info(f"用户反馈已记录: {user_id} -> {item_id} ({feedback_type})")

        except Exception as e:
            logger.error(f"更新反馈模型失败: {e}")
