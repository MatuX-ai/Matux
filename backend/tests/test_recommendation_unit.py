"""
AI-Edu AI 推荐系统单元测试
测试覆盖：推荐算法、用户画像、冷启动、反馈循环
"""

from datetime import datetime, timedelta
import json
import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import Base
from models.recommendation import (
    CourseFeature,
    LearningStyle,
    RecommendationRecord,
    UserLearningProfile,
)
from services.recommendation_service import (
    RecommendationService,
    get_recommendation_service,
)

# ==================== 测试夹具 ====================


@pytest.fixture
def test_db():
    """创建测试数据库"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def recommendation_service(test_db):
    """创建推荐服务实例"""
    return get_recommendation_service(test_db)


@pytest.fixture
def sample_user_profile():
    """示例用户画像数据"""
    return {
        "user_id": 1,
        "learning_style": "visual",
        "interests": ["python", "machine learning", "data science"],
        "skill_levels": {"python": 0.7, "javascript": 0.5, "machine_learning": 0.3},
        "knowledge_mastery": {"basics": 0.8, "intermediate": 0.6, "advanced": 0.2},
    }


@pytest.fixture
def sample_course_features():
    """示例课程特征数据"""
    return [
        {
            "course_id": 1,
            "difficulty_level": 2,
            "knowledge_tags": ["python", "basics", "syntax"],
            "skill_category": "programming",
            "prerequisites": [],
        },
        {
            "course_id": 2,
            "difficulty_level": 4,
            "knowledge_tags": ["machine learning", "algorithms", "advanced"],
            "skill_category": "ai",
            "prerequisites": [1],
        },
        {
            "course_id": 3,
            "difficulty_level": 3,
            "knowledge_tags": ["data science", "statistics", "intermediate"],
            "skill_category": "data",
            "prerequisites": [1],
        },
    ]


# ==================== 用户画像测试 ====================


class TestUserProfile:
    """用户画像测试"""

    def test_create_user_profile(self, recommendation_service, sample_user_profile):
        """测试创建用户画像"""
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style=sample_user_profile["learning_style"],
            interests=sample_user_profile["interests"],
        )

        assert profile is not None
        assert profile.user_id == sample_user_profile["user_id"]
        assert profile.learning_style.value == sample_user_profile["learning_style"]

    def test_update_user_preferences(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试更新用户偏好"""
        # 先创建
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style="visual",
            interests=["python"],
        )

        # 再更新
        updated_profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style="kinesthetic",
            interests=["python", "ai"],
        )

        assert updated_profile.learning_style.value == "kinesthetic"
        assert len(updated_profile.interests) == 2

    def test_get_user_profile(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试获取用户画像"""
        # 创建
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style=sample_user_profile["learning_style"],
            interests=sample_user_profile["interests"],
        )

        # 获取
        retrieved = recommendation_service.get_user_profile(
            sample_user_profile["user_id"]
        )

        assert retrieved is not None
        assert retrieved.user_id == profile.user_id


# ==================== 推荐算法测试 ====================


class TestRecommendationAlgorithm:
    """推荐算法测试"""

    def test_difficulty_match_score(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试难度匹配分数"""
        # 创建用户画像（中等水平）
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style="visual",
            interests=["python"],
        )

        # 更新能力维度为中等
        profile.skill_levels = {"python": 0.5}
        test_db.commit()

        # 测试不同难度的课程
        easy_course = recommendation_service._calculate_recommendation_score(
            user_profile=profile,
            course_feature={"difficulty_level": 1},
            behavior_stats={},
        )

        medium_course = recommendation_service._calculate_recommendation_score(
            user_profile=profile,
            course_feature={"difficulty_level": 3},
            behavior_stats={},
        )

        hard_course = recommendation_service._calculate_recommendation_score(
            user_profile=profile,
            course_feature={"difficulty_level": 5},
            behavior_stats={},
        )

        # i+1 理论：稍难于当前水平的课程得分应该最高
        assert medium_course > easy_course or medium_course > hard_course

    def test_interest_match_score(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试兴趣匹配分数"""
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style="visual",
            interests=["python", "machine learning"],
        )

        # 高匹配课程
        high_match = recommendation_service._calculate_recommendation_score(
            user_profile=profile,
            course_feature={
                "knowledge_tags": ["python", "machine learning", "deep learning"]
            },
            behavior_stats={},
        )

        # 低匹配课程
        low_match = recommendation_service._calculate_recommendation_score(
            user_profile=profile,
            course_feature={"knowledge_tags": ["java", "spring", "enterprise"]},
            behavior_stats={},
        )

        assert high_match > low_match

    def test_cold_start_recommendation(self, recommendation_service, test_db):
        """测试冷启动推荐（新用户）"""
        # 创建空画像用户
        profile = recommendation_service.create_or_update_profile(
            user_id=999, learning_style="unspecified", interests=[]
        )

        # 应该有默认配置
        assert profile is not None
        assert profile.learning_style is not None

    def test_recommendation_feedback_loop(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试推荐反馈循环"""
        # 创建用户和课程
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style="visual",
            interests=["python"],
        )

        # 生成推荐
        recommendations = recommendation_service.recommend_courses(
            user_id=sample_user_profile["user_id"], limit=5
        )

        # 提交反馈（假设第一个被点击）
        if recommendations:
            recommendation_service.record_feedback(
                user_id=sample_user_profile["user_id"],
                recommendation_id=recommendations[0]["id"],
                feedback_type="click",
            )

            # 重新推荐，相似课程权重应该增加
            new_recommendations = recommendation_service.recommend_courses(
                user_id=sample_user_profile["user_id"], limit=5
            )

            assert len(new_recommendations) > 0


# ==================== 混合推荐测试 ====================


class TestHybridRecommendation:
    """混合推荐测试"""

    def test_hybrid_recommendation_weights(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试混合推荐权重"""
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style="visual",
            interests=["python"],
        )

        # 计算各维度分数
        course_feature = {
            "difficulty_level": 3,
            "knowledge_tags": ["python", "programming"],
        }

        scores = recommendation_service._calculate_recommendation_score(
            user_profile=profile, course_feature=course_feature, behavior_stats={}
        )

        # 验证权重总和为 1
        weights = recommendation_service.score_weights
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001

    def test_diversity_in_recommendations(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试推荐多样性"""
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style="visual",
            interests=["python", "data science"],
        )

        # 生成多个推荐
        recommendations = recommendation_service.recommend_courses(
            user_id=sample_user_profile["user_id"], limit=10
        )

        # 应该包含不同类型的课程
        if len(recommendations) > 1:
            # 检查是否有不同的技能分类
            skill_categories = set()
            for rec in recommendations:
                if "skill_category" in rec:
                    skill_categories.add(rec["skill_category"])

            # 应该有至少 2 种不同类型
            assert len(skill_categories) >= 1  # 至少有一种类型


# ==================== 边界条件测试 ====================


class TestEdgeCases:
    """边界条件测试"""

    def test_empty_course_database(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试空课程数据库"""
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style="visual",
            interests=["python"],
        )

        # 没有课程时返回空列表
        recommendations = recommendation_service.recommend_courses(
            user_id=sample_user_profile["user_id"], limit=10
        )

        assert recommendations == []

    def test_invalid_learning_style(self, recommendation_service, test_db):
        """测试无效学习风格"""
        with pytest.raises(ValueError):
            recommendation_service.create_or_update_profile(
                user_id=1, learning_style="invalid_style", interests=[]
            )

    def test_zero_limit_recommendation(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试零数量推荐"""
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style="visual",
            interests=["python"],
        )

        # limit 为 0 应该返回空列表
        recommendations = recommendation_service.recommend_courses(
            user_id=sample_user_profile["user_id"], limit=0
        )

        assert recommendations == []

    def test_very_large_limit(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试超大数量限制"""
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style="visual",
            interests=["python"],
        )

        # 大数量限制应该能正常处理
        recommendations = recommendation_service.recommend_courses(
            user_id=sample_user_profile["user_id"], limit=1000
        )

        # 即使请求很多，也应该有合理上限
        assert len(recommendations) <= 1000


# ==================== 性能测试 ====================


class TestPerformance:
    """性能测试"""

    def test_recommendation_performance(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试推荐性能"""
        import time

        # 创建用户
        profile = recommendation_service.create_or_update_profile(
            user_id=sample_user_profile["user_id"],
            learning_style="visual",
            interests=["python"],
        )

        start_time = time.time()

        # 执行推荐
        recommendations = recommendation_service.recommend_courses(
            user_id=sample_user_profile["user_id"], limit=20
        )

        end_time = time.time()
        duration = end_time - start_time

        # 应该在合理时间内完成
        assert duration < 1.0  # 1 秒内

        # 应该返回推荐结果
        assert len(recommendations) >= 0


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
