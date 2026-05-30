"""
推荐服务单元测试
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_service.recommendation_service import RecommendationEngine
from models.recommendation import CourseFeature, LearningRecord, UserLearningProfile


@pytest.fixture
def sample_learning_records():
    """创建示例学习记录"""
    return [
        LearningRecord(
            id=1,
            user_id="user1",
            course_id="course1",
            lesson_id="lesson1",
            progress=0.8,
            time_spent=60,
            completion_status="completed",
            difficulty_rating=4,
            interest_rating=5,
        ),
        LearningRecord(
            id=2,
            user_id="user1",
            course_id="course2",
            lesson_id="lesson2",
            progress=0.6,
            time_spent=45,
            completion_status="in_progress",
            difficulty_rating=3,
            interest_rating=4,
        ),
        LearningRecord(
            id=3,
            user_id="user2",
            course_id="course1",
            lesson_id="lesson1",
            progress=0.9,
            time_spent=90,
            completion_status="completed",
            difficulty_rating=5,
            interest_rating=5,
        ),
    ]


@pytest.fixture
def sample_user_profiles():
    """创建示例用户画像"""
    return [
        UserLearningProfile(
            id=1,
            user_id="user1",
            learning_preferences={"preferred_difficulty": "intermediate"},
            skill_levels={"python": 7, "javascript": 5},
            interests=["web开发", "数据分析"],
            learning_history_vector=[0.8, 0.6, 0.9, 0.7] * 50,  # 扩展到200维
        ),
        UserLearningProfile(
            id=2,
            user_id="user2",
            learning_preferences={"preferred_difficulty": "advanced"},
            skill_levels={"python": 9, "machine_learning": 8},
            interests=["机器学习", "深度学习"],
            learning_history_vector=[0.9, 0.8, 0.95, 0.85] * 50,
        ),
    ]


@pytest.fixture
def sample_course_features():
    """创建示例课程特征"""
    return [
        CourseFeature(
            id=1,
            course_id="course1",
            title="Python基础教程",
            description="Python编程入门课程",
            category="编程基础",
            difficulty_level="beginner",
            estimated_duration=20,
            tags=["python", "编程", "入门"],
            feature_vector=[0.8, 0.2, 0.1, 0.9] * 25,
            popularity_score=0.8,
        ),
        CourseFeature(
            id=2,
            course_id="course2",
            title="机器学习实战",
            description="机器学习算法与实践",
            category="人工智能",
            difficulty_level="intermediate",
            estimated_duration=40,
            tags=["机器学习", "python", "数据分析"],
            feature_vector=[0.9, 0.8, 0.7, 0.6] * 25,
            popularity_score=0.9,
        ),
        CourseFeature(
            id=3,
            course_id="course3",
            title="Web前端开发",
            description="现代Web前端技术栈",
            category="前端开发",
            difficulty_level="intermediate",
            estimated_duration=30,
            tags=["javascript", "react", "前端"],
            feature_vector=[0.7, 0.8, 0.6, 0.5] * 25,
            popularity_score=0.7,
        ),
    ]


@pytest.mark.asyncio
class TestRecommendationEngine:
    """推荐引擎测试类"""

    @pytest.fixture
    def recommendation_engine(self):
        """创建推荐引擎实例"""
        return RecommendationEngine(
            model_path="./test_models/test_recommendation_model.pkl"
        )

    async def test_initialize_with_empty_data(self, recommendation_engine):
        """测试空数据初始化"""
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalars().all.return_value = []

        await recommendation_engine.initialize(mock_db)

        assert not recommendation_engine.is_trained
        assert len(recommendation_engine.user_profiles) == 0
        assert len(recommendation_engine.course_features) == 0

    async def test_initialize_with_sample_data(
        self,
        recommendation_engine,
        sample_learning_records,
        sample_user_profiles,
        sample_course_features,
    ):
        """测试带样本数据的初始化"""
        mock_db = AsyncMock()

        # 设置mock返回值
        mock_db.execute.side_effect = [
            AsyncMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        all=MagicMock(return_value=sample_learning_records)
                    )
                )
            ),
            AsyncMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        all=MagicMock(return_value=sample_user_profiles)
                    )
                )
            ),
            AsyncMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        all=MagicMock(return_value=sample_course_features)
                    )
                )
            ),
        ]

        await recommendation_engine.initialize(mock_db)

        assert len(recommendation_engine.user_profiles) == 2
        assert len(recommendation_engine.course_features) == 3
        assert recommendation_engine.interaction_matrix is not None
        assert recommendation_engine.interaction_matrix.shape == (2, 2)  # 2用户 x 2课程

    async def test_get_recommendations_untrained(self, recommendation_engine):
        """测试未训练状态下获取推荐"""
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalars().all.return_value = []

        recommendations = await recommendation_engine.get_recommendations(
            "user1", mock_db, 3
        )

        # 应该返回空列表或热门推荐
        assert isinstance(recommendations, list)

    async def test_collaborative_filtering_recommendations(
        self,
        recommendation_engine,
        sample_learning_records,
        sample_user_profiles,
        sample_course_features,
    ):
        """测试协同过滤推荐"""
        mock_db = AsyncMock()
        mock_db.execute.side_effect = [
            AsyncMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        all=MagicMock(return_value=sample_learning_records)
                    )
                )
            ),
            AsyncMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        all=MagicMock(return_value=sample_user_profiles)
                    )
                )
            ),
            AsyncMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        all=MagicMock(return_value=sample_course_features)
                    )
                )
            ),
        ]

        await recommendation_engine.initialize(mock_db)

        # 测试为user1推荐
        recommendations = (
            await recommendation_engine._collaborative_filtering_recommendations(
                "user1", 5
            )
        )

        assert isinstance(recommendations, list)
        # 验证返回格式
        for rec in recommendations:
            assert "course_id" in rec
            assert "score" in rec
            assert "type" in rec
            assert rec["type"] == "collaborative"

    async def test_content_based_recommendations(
        self, recommendation_engine, sample_user_profiles, sample_course_features
    ):
        """测试基于内容的推荐"""
        mock_db = AsyncMock()
        mock_db.execute.side_effect = [
            AsyncMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        all=MagicMock(return_value=sample_user_profiles)
                    )
                )
            ),
            AsyncMock(
                scalars=MagicMock(
                    return_value=MagicMock(
                        all=MagicMock(return_value=sample_course_features)
                    )
                )
            ),
        ]

        # 手动设置数据以便测试
        recommendation_engine.user_profiles = {
            profile.user_id: {
                "learning_preferences": profile.learning_preferences,
                "skill_levels": profile.skill_levels,
                "interests": profile.interests,
                "learning_history_vector": profile.learning_history_vector,
            }
            for profile in sample_user_profiles
        }

        recommendation_engine.course_features = {
            course.course_id: {
                "title": course.title,
                "description": course.description,
                "category": course.category,
                "difficulty_level": course.difficulty_level,
                "tags": course.tags,
                "feature_vector": course.feature_vector,
                "popularity_score": course.popularity_score,
            }
            for course in sample_course_features
        }

        # 准备内容特征
        course_descriptions = []
        course_ids = []
        for course_id, features in recommendation_engine.course_features.items():
            text = f"{features['title']} {features['description']} {' '.join(features['tags'])}"
            course_descriptions.append(text)
            course_ids.append(course_id)

        if course_descriptions:
            recommendation_engine.content_features = (
                recommendation_engine.tfidf_vectorizer.fit_transform(
                    course_descriptions
                )
            )
            recommendation_engine.course_ids_for_content = course_ids

        # 测试为user1推荐
        recommendations = await recommendation_engine._content_based_recommendations(
            "user1", 5
        )

        assert isinstance(recommendations, list)
        # 验证返回格式
        for rec in recommendations:
            assert "course_id" in rec
            assert "score" in rec
            assert "type" in rec
            assert rec["type"] == "content"

    async def test_update_user_profile(
        self, recommendation_engine, sample_learning_records
    ):
        """测试更新用户画像"""
        mock_db = AsyncMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        learning_record = sample_learning_records[0]

        await recommendation_engine.update_user_profile(
            "user1", learning_record, mock_db
        )

        # 验证数据库操作
        assert mock_db.add.called
        assert mock_db.commit.called

    async def test_save_and_load_model(self, recommendation_engine):
        """测试模型保存和加载"""
        # 设置一些测试数据
        recommendation_engine.user_profiles = {"user1": {"test": "data"}}
        recommendation_engine.course_features = {"course1": {"test": "data"}}
        recommendation_engine.is_trained = True

        # 保存模型
        with patch("os.makedirs"), patch("builtins.open", MagicMock()):
            recommendation_engine.save_model()

        # 加载模型
        with (
            patch("os.path.exists", return_value=True),
            patch("builtins.open", MagicMock()),
        ):
            result = recommendation_engine.load_model()
            assert result == True


@pytest.mark.asyncio
class TestRecommendationRoutes:
    """推荐路由测试类"""

    def test_recommendation_endpoints_exist(self):
        """测试推荐相关的API端点是否存在"""
        from routes.recommendation_routes import router

        routes = [route.path for route in router.routes]

        expected_routes = [
            "/courses",
            "/feedback",
            "/learning-record",
            "/user-profile",
            "/user-profile/preferences",
            "/stats",
            "/refresh-model",
        ]

        for route in expected_routes:
            full_route = f"/recommendations{route}"
            assert any(full_route in r for r in routes), f"路由 {full_route} 不存在"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
