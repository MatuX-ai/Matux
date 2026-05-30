"""
AI-Edu 智能推荐服务（精简版）
实现基于规则、相似度和用户画像的个性化推荐
"""

from collections import defaultdict
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models.ai_edu_rewards import AIEduLesson, AIEduModule
from models.recommendation import (
    CourseFeature,
    LearningStyle,
    RecommendationAlgorithm,
    RecommendationRecord,
    UserLearningProfile,
)

logger = logging.getLogger(__name__)


class RecommendationService:
    """智能推荐服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 用户画像管理 ====================

    def get_or_create_user_profile(self, user_id: int) -> UserLearningProfile:
        """获取或创建用户学习画像"""
        profile = (
            self.db.query(UserLearningProfile)
            .filter(UserLearningProfile.user_id == user_id)
            .first()
        )

        if not profile:
            # 创建默认画像
            profile = UserLearningProfile(
                user_id=user_id,
                learning_style=LearningStyle.VISUAL,
                preferred_content_type="video",
                ability_dimensions={},
                interest_preferences=[],
                knowledge_mastery={},
                recommendation_weights={
                    "difficulty_match": 0.3,
                    "interest_match": 0.3,
                    "skill_improvement": 0.2,
                    "popularity": 0.1,
                    "diversity": 0.1,
                },
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)

        return profile

    def update_user_profile(
        self, user_id: int, updates: Dict[str, Any]
    ) -> UserLearningProfile:
        """更新用户画像"""
        profile = self.get_or_create_user_profile(user_id)

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        self.db.commit()
        self.db.refresh(profile)

        logger.info(f"✅ 用户 {user_id} 的学习画像已更新")
        return profile

    def analyze_learning_behavior(self, user_id: int) -> Dict[str, Any]:
        """分析用户学习行为（简化版）"""
        from models.ai_edu_rewards import AIEduLearningProgress

        # 统计学习数据
        progress_records = (
            self.db.query(AIEduLearningProgress)
            .filter(AIEduLearningProgress.user_id == user_id)
            .all()
        )

        total_time = (
            sum(r.time_spent_seconds or 0 for r in progress_records) / 60
        )  # 转换为分钟
        completed_count = sum(1 for r in progress_records if r.status == "completed")
        avg_score = sum(
            r.quiz_score or 0 for r in progress_records if r.quiz_score
        ) / max(len([r for r in progress_records if r.quiz_score]), 1)

        return {
            "total_study_time_minutes": total_time,
            "completed_courses_count": completed_count,
            "average_quiz_score": round(avg_score, 2),
            "engagement_level": (
                "high"
                if completed_count > 5
                else "medium" if completed_count > 2 else "low"
            ),
        }

    def _get_user_skill_distribution(self, user_id: int) -> Dict[str, float]:
        """
        获取用户技能分布

        Args:
            user_id: 用户 ID

        Returns:
            技能分布字典 {skill_name: weight}
        """
        from sqlalchemy import func

        from models.ai_edu_rewards import AIEduLearningProgress
        from models.course import CourseSkill

        # 1. 查询用户已完成的课程
        completed_courses = (
            self.db.query(AIEduLearningProgress)
            .filter(
                and_(
                    AIEduLearningProgress.user_id == user_id,
                    AIEduLearningProgress.status == "completed",
                )
            )
            .all()
        )

        if not completed_courses:
            return {}

        # 2. 提取技能标签并加权统计
        skill_weights = defaultdict(float)

        for progress in completed_courses:
            # 查询课程的技能标签
            course_skills = (
                self.db.query(CourseSkill)
                .filter(CourseSkill.course_id == progress.lesson_id)
                .all()
            )

            # 获取课程信息用于加权
            course_rating = progress.quiz_score or 70.0  # 默认评分
            learning_duration_hours = (progress.time_spent_seconds or 0) / 3600

            # 根据课程评分和学习时间加权
            weight = (course_rating / 100.0) * max(learning_duration_hours, 0.5)

            for course_skill in course_skills:
                if hasattr(course_skill, "skill") and course_skill.skill:
                    skill_name = course_skill.skill.name
                    skill_weights[skill_name] += weight

        # 3. 归一化处理
        total_weight = sum(skill_weights.values())
        if total_weight > 0:
            return {
                skill: weight / total_weight for skill, weight in skill_weights.items()
            }

        return {}

    # ==================== 推荐算法 ====================

    def recommend_courses(
        self, user_id: int, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        为用户推荐课程（混合推荐策略）

        Args:
            user_id: 用户 ID
            limit: 推荐数量
            filters: 过滤条件 {difficulty_min, difficulty_max, skill_category}

        Returns:
            推荐课程列表（含推荐理由和分数）
        """
        # 1. 获取用户画像
        profile = self.get_or_create_user_profile(user_id)

        # 2. 分析学习行为
        behavior_stats = self.analyze_learning_behavior(user_id)

        # 3. 获取所有课程特征
        query = self.db.query(CourseFeature)

        # 应用过滤条件
        if filters:
            if "difficulty_min" in filters:
                query = query.filter(
                    CourseFeature.difficulty_level >= filters["difficulty_min"]
                )
            if "difficulty_max" in filters:
                query = query.filter(
                    CourseFeature.difficulty_level <= filters["difficulty_max"]
                )
            if "skill_category" in filters:
                query = query.filter(
                    CourseFeature.skill_categories.contains([filters["skill_category"]])
                )

        all_courses = query.all()

        # 4. 为每个课程计算推荐分数
        scored_courses = []

        for course in all_courses:
            score, reasons = self._calculate_recommendation_score(
                user_profile=profile,
                course_feature=course,
                behavior_stats=behavior_stats,
            )

            scored_courses.append(
                {
                    "course": course.to_dict(),
                    "score": score,
                    "reasons": reasons,
                    "algorithm": "hybrid",
                }
            )

        # 5. 按分数排序并返回 Top N
        scored_courses.sort(key=lambda x: x["score"], reverse=True)

        recommendations = scored_courses[:limit]

        # 6. 记录推荐（用于后续优化）
        self._log_recommendations(user_id, recommendations)

        return recommendations

    def _calculate_recommendation_score(
        self,
        user_profile: UserLearningProfile,
        course_feature: CourseFeature,
        behavior_stats: Dict[str, Any],
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """
        计算课程推荐分数

        Returns:
            (总分， 理由列表)
        """
        weights = user_profile.recommendation_weights or {
            "difficulty_match": 0.3,
            "interest_match": 0.3,
            "skill_improvement": 0.2,
            "popularity": 0.1,
            "diversity": 0.1,
        }

        scores = {}
        reasons = []

        # 1. 难度匹配分数
        difficulty_score, diff_reason = self._match_difficulty(
            user_profile, course_feature, behavior_stats
        )
        scores["difficulty_match"] = difficulty_score
        if diff_reason:
            reasons.append(diff_reason)

        # 2. 兴趣匹配分数
        interest_score, int_reason = self._match_interest(user_profile, course_feature)
        scores["interest_match"] = interest_score
        if int_reason:
            reasons.append(int_reason)

        # 3. 技能提升分数
        skill_score, skill_reason = self._match_skill_improvement(
            user_profile, course_feature
        )
        scores["skill_improvement"] = skill_score
        if skill_reason:
            reasons.append(skill_reason)

        # 4. 热门程度分数
        popularity_score = self._calculate_popularity(course_feature)
        scores["popularity"] = popularity_score

        # 5. 多样性分数（避免推荐过于单一）
        diversity_score = self._calculate_diversity(user_profile, course_feature)
        scores["diversity"] = diversity_score

        # 计算加权总分
        total_score = sum(
            scores.get(key, 0) * weight for key, weight in weights.items()
        )

        return total_score, reasons

    def _match_difficulty(
        self,
        user_profile: UserLearningProfile,
        course_feature: CourseFeature,
        behavior_stats: Dict[str, Any],
    ) -> Tuple[float, Optional[Dict[str, Any]]]:
        """难度匹配（i+1 理论：略高于当前水平）"""
        # 根据平均成绩推断当前水平
        avg_score = behavior_stats.get("average_quiz_score", 0)

        # 理想难度：比当前水平稍高
        if avg_score >= 90:
            ideal_difficulty = 4  # 学霸推荐高难度
        elif avg_score >= 70:
            ideal_difficulty = 3  # 中等难度
        elif avg_score >= 50:
            ideal_difficulty = 2  # 中低难度
        else:
            ideal_difficulty = 1  # 初学者从简单开始

        # 计算匹配度
        difficulty_diff = abs(course_feature.difficulty_level - ideal_difficulty)
        score = max(0, 1 - difficulty_diff * 0.2)  # 每差 1 级扣 20%

        reason = None
        if score >= 0.8:
            reason = {
                "type": "difficulty_perfect",
                "description": f"难度非常适合你当前的水平",
                "confidence": score,
            }
        elif score >= 0.6:
            reason = {
                "type": "difficulty_good",
                "description": f"难度较为合适",
                "confidence": score,
            }

        return score, reason

    def _match_interest(
        self, user_profile: UserLearningProfile, course_feature: CourseFeature
    ) -> Tuple[float, Optional[Dict[str, Any]]]:
        """兴趣匹配"""
        user_interests = set(
            i.get("category") for i in user_profile.interest_preferences or []
        )
        course_tags = set(course_feature.tags or [])
        course_skills = set(course_feature.skill_categories or [])

        # 计算交集
        all_course_features = user_interests & (course_tags | course_skills)

        if all_course_features:
            score = min(1.0, len(all_course_features) / max(len(user_interests), 1))
            return score, {
                "type": "interest_match",
                "description": f'这门课程符合你的兴趣：{", ".join(all_course_features)}',
                "matched_features": list(all_course_features),
                "confidence": score,
            }

        return 0.3, None  # 默认基础分

    def _match_skill_improvement(
        self, user_profile: UserLearningProfile, course_feature: CourseFeature
    ) -> Tuple[float, Optional[Dict[str, Any]]]:
        """技能提升匹配（补短板）"""
        knowledge_mastery = user_profile.knowledge_mastery or {}
        course_knowledge = set(course_feature.knowledge_points or [])

        if not knowledge_mastery or not course_knowledge:
            return 0.5, None

        # 找出课程能帮助提升的薄弱知识点
        weak_points = [
            kp
            for kp in course_knowledge
            if kp in knowledge_mastery and knowledge_mastery[kp] < 0.7
        ]

        if weak_points:
            score = min(1.0, len(weak_points) / len(course_knowledge))
            return score, {
                "type": "skill_improvement",
                "description": f'可以帮助你加强：{", ".join(weak_points)}',
                "weak_points": weak_points,
                "confidence": score,
            }

        return 0.4, None

    def _calculate_popularity(self, course_feature: CourseFeature) -> float:
        """计算热门程度分数"""
        # 综合考虑学习人数、评分、完成率
        student_score = min(1.0, (course_feature.student_count or 0) / 1000)
        rating_score = (course_feature.average_rating or 0) / 5.0
        completion_score = course_feature.completion_rate or 0

        return 0.4 * student_score + 0.4 * rating_score + 0.2 * completion_score

    def _calculate_diversity(
        self, user_profile: UserLearningProfile, course_feature: CourseFeature
    ) -> float:
        """计算多样性分数（鼓励探索不同领域）"""
        # ✅ 查询用户已学课程的技能分布
        skill_distribution = self._get_user_skill_distribution(user_profile.user_id)

        # 获取课程的主要技能分类
        course_skills = set()
        if course_feature.skill_tags:
            course_skills = set(tag.name for tag in course_feature.skill_tags)

        # 计算技能重叠度
        user_skills = set(skill_distribution.keys())
        overlap = len(course_skills & user_skills)
        total_user_skills = len(user_skills)

        # 如果没有已学技能，返回默认值
        if total_user_skills == 0:
            return 0.5

        # 重叠度越低，多样性分数越高
        overlap_ratio = overlap / total_user_skills
        diversity_score = 1.0 - overlap_ratio

        logger.info(
            f"用户{user_profile.user_id}多样性评分：{diversity_score:.2f} "
            f"(重叠技能：{overlap}, 总技能：{total_user_skills})"
        )

        return diversity_score

    def _log_recommendations(self, user_id: int, recommendations: List[Dict]):
        """记录推荐结果（用于后续分析和优化）"""
        try:
            for rec in recommendations[:5]:  # 只记录前 5 个
                record = RecommendationRecord(
                    user_id=user_id,
                    course_id=rec["course"]["course_id"],
                    algorithm_type=RecommendationAlgorithm.HYBRID,
                    recommendation_score=rec["score"],
                    reason={"reasons": rec["reasons"]},
                    context={"timestamp": datetime.utcnow().isoformat()},
                )
                self.db.add(record)

            self.db.commit()
        except Exception as e:
            logger.error(f"记录推荐失败：{e}")
            self.db.rollback()

    # ==================== 学习路径规划 ====================

    def generate_learning_path(
        self, user_id: int, target_skills: List[str], time_commitment_minutes: int = 60
    ) -> Dict[str, Any]:
        """
        生成个性化学习路径

        Args:
            user_id: 用户 ID
            target_skills: 目标技能列表
            time_commitment_minutes: 可用时间（分钟）

        Returns:
            学习路径规划
        """
        profile = self.get_or_create_user_profile(user_id)

        # 1. 找到相关的课程
        relevant_courses = (
            self.db.query(CourseFeature)
            .filter(
                or_(
                    CourseFeature.skill_categories.contains(target_skills),
                    CourseFeature.knowledge_points.contains(target_skills),
                )
            )
            .all()
        )

        # 2. 按先修关系排序（简化版：按难度排序）
        relevant_courses.sort(key=lambda c: c.difficulty_level)

        # 3. 生成学习序列
        learning_sequence = []
        total_time = 0

        for course in relevant_courses:
            if total_time >= time_commitment_minutes:
                break

            learning_sequence.append(
                {
                    "course_id": course.course_id,
                    "estimated_duration": course.estimated_duration_minutes,
                    "difficulty": course.difficulty_level,
                    "skills_covered": course.skill_categories[:3],  # 只显示前 3 个技能
                }
            )
            total_time += course.estimated_duration_minutes

        return {
            "user_id": user_id,
            "target_skills": target_skills,
            "time_commitment": time_commitment_minutes,
            "recommended_sequence": learning_sequence,
            "total_estimated_time": total_time,
            "difficulty_progression": "循序渐进" if relevant_courses else "无合适课程",
        }

    # ==================== 反馈收集 ====================

    def submit_feedback(
        self,
        recommendation_id: int,
        user_clicked: bool,
        user_completed: bool = False,
        user_rating: Optional[int] = None,
        feedback_text: Optional[str] = None,
    ):
        """提交用户对推荐的反馈"""
        record = (
            self.db.query(RecommendationRecord)
            .filter(RecommendationRecord.id == recommendation_id)
            .first()
        )

        if not record:
            raise ValueError(f"推荐记录 {recommendation_id} 不存在")

        record.user_clicked = user_clicked
        record.user_completed = user_completed
        record.user_rating = user_rating
        record.feedback_text = feedback_text

        if user_clicked:
            record.clicked_at = datetime.utcnow()
        if user_completed:
            record.completed_at = datetime.utcnow()

        self.db.commit()

        logger.info(
            f"✅ 推荐反馈已记录：rec_id={recommendation_id}, clicked={user_clicked}"
        )


def get_recommendation_service(db: Session) -> RecommendationService:
    """获取推荐服务实例"""
    return RecommendationService(db)
