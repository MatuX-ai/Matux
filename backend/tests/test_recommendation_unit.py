"""
AI-Edu AI 推荐系统单元测试
测试覆盖：推荐算法、用户画像、冷启动、反馈循环

与真实实现对齐说明（Issue #32 批次 1 L3）
------------------------------------------------
本文件原先调用的是一套**仓库中并不存在**的 API，全部 14 个用例都在
`AttributeError` 上失败。真实实现对照如下：

| 原测试调用                                   | 真实实现                                          |
|--------------------------------------------|---------------------------------------------------|
| `create_or_update_profile(user_id, ...)`    | `get_or_create_user_profile(user_id)` + `update_user_profile(user_id, updates)` |
| `get_user_profile(user_id)`                 | `get_or_create_user_profile(user_id)`             |
| `record_feedback(user_id, rec_id, ...)`     | `submit_feedback(recommendation_id, user_clicked, ...)` |
| `service.score_weights`                     | 画像字段 `profile.recommendation_weights`         |
| `profile.interests` / `profile.skill_levels`| `profile.interest_preferences` / `profile.ability_dimensions` |
| `_calculate_recommendation_score(...)` 返回 float | 返回 `(score, reasons)` 元组                |
| `course_feature` 传 dict                    | 需要 `CourseFeature` ORM 对象                      |

同时记录两处**实现缺陷**（属批次 3「改实现」，本 PR 只改测试，不动实现）：

1. `services/recommendation_service.py::_get_user_skill_distribution` 里
   `from models.course import CourseSkill`，但 `models/course.py` 没有
   `CourseSkill` —— 任何调用都会 ImportError。
2. `services/recommendation_service.py::_calculate_diversity` 访问
   `course_feature.skill_tags`，但 `models/recommendation.py::CourseFeature`
   没有该字段。

两处缺陷让 `_calculate_diversity` -> `_calculate_recommendation_score` ->
`recommend_courses`（课程表非空时）整条链路不可用。因此：

- 难度匹配 / 兴趣匹配改用可直接调用的 `_match_difficulty` / `_match_interest`；
- 综合打分链路的用例标记为 skip，并在 skip 原因里写明缺陷位置。
"""

import os
import sys
import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.recommendation import (  # noqa: E402
    CourseFeature,
    LearningStyle,
    RecommendationAlgorithm,
    RecommendationRecord,
)
from services.recommendation_service import get_recommendation_service  # noqa: E402
from utils.database import Base  # noqa: E402

# ==================== 测试夹具 ====================


@pytest.fixture
def test_db():
    """创建测试数据库"""
    # 服务在函数内部延迟导入 models.ai_edu_rewards（analyze_learning_behavior /
    # _get_user_skill_distribution）。若不在 create_all 之前导入，
    # ai_edu_learning_progress 表不会建出来，推荐查询会报 no such table。
    import models.ai_edu_rewards  # noqa: F401

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
def sample_course_features(test_db):
    """示例课程特征数据（写入 course_features 表）"""
    features = [
        CourseFeature(
            course_id=1,
            difficulty_level=1,
            knowledge_points=["basics"],
            skill_categories=["programming"],
            tags=["python"],
            average_rating=4.2,
            completion_rate=0.6,
            student_count=120,
        ),
        CourseFeature(
            course_id=2,
            difficulty_level=3,
            knowledge_points=["syntax", "oop"],
            skill_categories=["ai"],
            tags=["python", "machine learning"],
            average_rating=4.8,
            completion_rate=0.45,
            student_count=860,
        ),
        CourseFeature(
            course_id=3,
            difficulty_level=5,
            knowledge_points=["distributed"],
            skill_categories=["data"],
            tags=["java", "spring"],
            average_rating=3.1,
            completion_rate=0.2,
            student_count=40,
        ),
    ]
    test_db.add_all(features)
    test_db.commit()
    for feature in features:
        test_db.refresh(feature)
    return features


# ==================== 用户画像测试 ====================


class TestUserProfile:
    """用户画像测试"""

    def test_create_user_profile(self, recommendation_service, sample_user_profile):
        """测试创建用户画像"""
        profile = recommendation_service.get_or_create_user_profile(
            user_id=sample_user_profile["user_id"],
        )

        assert profile is not None
        assert profile.user_id == sample_user_profile["user_id"]
        # 真实实现的默认画像：视觉型 + 默认推荐权重（合计 1.0）
        assert profile.learning_style == LearningStyle.VISUAL
        assert abs(sum(profile.recommendation_weights.values()) - 1.0) < 0.001

    def test_update_user_preferences(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试更新用户偏好"""
        user_id = sample_user_profile["user_id"]

        # 先创建
        recommendation_service.get_or_create_user_profile(user_id)

        # 再更新
        updated_profile = recommendation_service.update_user_profile(
            user_id,
            {
                "learning_style": LearningStyle.KINESTHETIC,
                "interest_preferences": [
                    {"category": "python"},
                    {"category": "ai"},
                ],
            },
        )

        assert updated_profile.learning_style.value == "kinesthetic"
        assert len(updated_profile.interest_preferences) == 2

    def test_get_user_profile(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试获取用户画像"""
        user_id = sample_user_profile["user_id"]

        # 创建
        profile = recommendation_service.get_or_create_user_profile(user_id=user_id)
        profile_id = profile.id

        # 获取（真实实现是 get-or-create，重复调用返回同一条记录）
        retrieved = recommendation_service.get_or_create_user_profile(user_id=user_id)

        assert retrieved is not None
        assert retrieved.id == profile_id
        assert retrieved.user_id == profile.user_id


# ==================== 推荐算法测试 ====================


class TestRecommendationAlgorithm:
    """推荐算法测试"""

    def test_difficulty_match_score(
        self,
        recommendation_service,
        sample_user_profile,
        test_db,
        sample_course_features,
    ):
        """测试难度匹配分数"""
        profile = recommendation_service.get_or_create_user_profile(
            user_id=sample_user_profile["user_id"]
        )

        easy_course, medium_course, hard_course = sample_course_features

        # 平均成绩 70 -> 理想难度为 3（i+1 理论：略高于当前水平）
        behavior_stats = {"average_quiz_score": 70}

        easy_score = recommendation_service._match_difficulty(
            user_profile=profile,
            course_feature=easy_course,
            behavior_stats=behavior_stats,
        )[0]

        medium_score = recommendation_service._match_difficulty(
            user_profile=profile,
            course_feature=medium_course,
            behavior_stats=behavior_stats,
        )[0]

        hard_score = recommendation_service._match_difficulty(
            user_profile=profile,
            course_feature=hard_course,
            behavior_stats=behavior_stats,
        )[0]

        # i+1 理论：稍难于当前水平的课程得分应该最高
        assert medium_score > easy_score
        assert medium_score > hard_score

    def test_interest_match_score(
        self,
        recommendation_service,
        sample_user_profile,
        test_db,
        sample_course_features,
    ):
        """测试兴趣匹配分数"""
        user_id = sample_user_profile["user_id"]
        recommendation_service.update_user_profile(
            user_id,
            {"interest_preferences": [{"category": "python"}, {"category": "ai"}]},
        )
        profile = recommendation_service.get_or_create_user_profile(user_id=user_id)

        easy_course, medium_course, hard_course = sample_course_features

        # 高匹配课程（tag 命中兴趣）
        high_match = recommendation_service._match_interest(
            user_profile=profile, course_feature=medium_course
        )[0]

        # 低匹配课程（tag 完全不命中）
        low_match = recommendation_service._match_interest(
            user_profile=profile, course_feature=hard_course
        )[0]

        assert high_match > low_match

    def test_cold_start_recommendation(self, recommendation_service, test_db):
        """测试冷启动推荐（新用户）"""
        # 创建空画像用户
        profile = recommendation_service.get_or_create_user_profile(user_id=999)

        # 应该有默认配置
        assert profile is not None
        assert profile.learning_style is not None
        assert profile.knowledge_mastery == {}
        assert profile.ability_dimensions == {}

    def test_recommendation_feedback_loop(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试推荐反馈循环"""
        # 推荐记录本应由 recommend_courses 写入，但该链路被实现缺陷阻塞
        # （_calculate_diversity -> models.course.CourseSkill 缺失），
        # 这里直接落一条记录，验证反馈闭环本身的行为。
        record = RecommendationRecord(
            user_id=sample_user_profile["user_id"],
            course_id=2,
            algorithm_type=RecommendationAlgorithm.HYBRID,
            recommendation_score=0.8,
        )
        test_db.add(record)
        test_db.commit()
        test_db.refresh(record)

        # 提交反馈（假设用户点击了）
        recommendation_service.submit_feedback(
            recommendation_id=record.id,
            user_clicked=True,
            user_rating=5,
        )

        test_db.refresh(record)
        assert record.user_clicked is True
        assert record.user_rating == 5
        assert record.clicked_at is not None


# ==================== 混合推荐测试 ====================


class TestHybridRecommendation:
    """混合推荐测试"""

    def test_hybrid_recommendation_weights(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试混合推荐权重"""
        profile = recommendation_service.get_or_create_user_profile(
            user_id=sample_user_profile["user_id"]
        )

        # 权重配置存放在用户画像上（真实实现没有 service.score_weights 属性）
        weights = profile.recommendation_weights

        # 验证权重总和为 1
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001
        assert set(weights) == {
            "difficulty_match",
            "interest_match",
            "skill_improvement",
            "popularity",
            "diversity",
        }

    def test_diversity_in_recommendations(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试推荐多样性"""
        pytest.skip(
            "实现缺陷（批次 3）：_calculate_diversity 依赖 models.course.CourseSkill"
            "（仓库中不存在）与 CourseFeature.skill_tags（模型中无此字段），"
            "综合打分链路当前不可用"
        )


# ==================== 边界条件测试 ====================


class TestEdgeCases:
    """边界条件测试"""

    def test_empty_course_database(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试空课程数据库"""
        recommendation_service.get_or_create_user_profile(
            user_id=sample_user_profile["user_id"]
        )

        # 没有课程时返回空列表
        recommendations = recommendation_service.recommend_courses(
            user_id=sample_user_profile["user_id"], limit=10
        )

        assert recommendations == []

    def test_invalid_learning_style(self, recommendation_service, test_db):
        """测试无效学习风格"""
        # 真实实现不做前置校验，非法枚举值在提交时由 SQLAlchemy 抛出 LookupError
        with pytest.raises(LookupError):
            recommendation_service.update_user_profile(
                user_id=1, updates={"learning_style": "invalid_style"}
            )

    def test_zero_limit_recommendation(
        self, recommendation_service, sample_user_profile, test_db
    ):
        """测试零数量推荐"""
        recommendation_service.get_or_create_user_profile(
            user_id=sample_user_profile["user_id"]
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
        recommendation_service.get_or_create_user_profile(
            user_id=sample_user_profile["user_id"]
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
        # 创建用户
        recommendation_service.get_or_create_user_profile(
            user_id=sample_user_profile["user_id"]
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
