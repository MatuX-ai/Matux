"""
AI-Edu 成就系统单元测试
测试覆盖：成就解锁逻辑、CRUD 操作、用户成就关联
"""

from datetime import datetime, timedelta
import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import Base
from models.achievement import (
    Achievement,
    AchievementCategory,
    AchievementType,
    UserAchievement,
)
from services.achievement_service import AchievementService, get_achievement_service

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
def achievement_service(test_db):
    """创建成就服务实例"""
    return get_achievement_service(test_db)


@pytest.fixture
def sample_user():
    """示例用户数据"""
    return {"id": 1, "username": "test_user", "email": "test@example.com"}


@pytest.fixture
def sample_achievements():
    """示例成就数据"""
    return [
        {
            "name": "勤奋学习者",
            "category": "learning",
            "achievement_type": "cumulative",
            "unlock_condition": {"study_time_minutes": 60},
            "points_reward": 50,
            "is_hidden": False,
        },
        {
            "name": "代码新手",
            "category": "coding",
            "achievement_type": "cumulative",
            "unlock_condition": {"code_executions": 10},
            "points_reward": 30,
            "is_hidden": False,
        },
        {
            "name": "测验满分",
            "category": "quiz",
            "achievement_type": "single",
            "unlock_condition": {"quiz_score": 100},
            "points_reward": 40,
            "is_hidden": False,
        },
    ]


# ==================== 成就 CRUD 测试 ====================


class TestAchievementCRUD:
    """成就 CRUD 操作测试"""

    def test_create_achievement(self, achievement_service, sample_achievements):
        """测试创建成就"""
        achievement_data = sample_achievements[0]

        achievement = achievement_service.create_achievement(**achievement_data)

        assert achievement is not None
        assert achievement.name == achievement_data["name"]
        assert achievement.category.value == achievement_data["category"]
        assert achievement.points_reward == achievement_data["points_reward"]
        assert achievement.is_hidden == achievement_data["is_hidden"]

    def test_get_achievement(self, achievement_service, sample_achievements, test_db):
        """测试获取成就"""
        # 先创建
        achievement_data = sample_achievements[0]
        achievement = achievement_service.create_achievement(**achievement_data)

        # 再获取
        retrieved = achievement_service.get_achievement(achievement.id)

        assert retrieved is not None
        assert retrieved.id == achievement.id
        assert retrieved.name == achievement.name

    def test_get_all_achievements(self, achievement_service, sample_achievements):
        """测试获取所有成就"""
        # 创建多个成就
        for data in sample_achievements:
            achievement_service.create_achievement(**data)

        # 获取列表
        achievements = achievement_service.get_all_achievements()

        assert len(achievements) == len(sample_achievements)

    def test_update_achievement(
        self, achievement_service, sample_achievements, test_db
    ):
        """测试更新成就"""
        # 创建
        achievement_data = sample_achievements[0]
        achievement = achievement_service.create_achievement(**achievement_data)

        # 更新
        updated = achievement_service.update_achievement(
            achievement_id=achievement.id, name="更新的成就名称", points_reward=100
        )

        assert updated.name == "更新的成就名称"
        assert updated.points_reward == 100

    def test_delete_achievement(
        self, achievement_service, sample_achievements, test_db
    ):
        """测试删除成就"""
        # 创建
        achievement_data = sample_achievements[0]
        achievement = achievement_service.create_achievement(**achievement_data)
        achievement_id = achievement.id

        # 删除
        deleted = achievement_service.delete_achievement(achievement_id)

        assert deleted is True

        # 验证已删除
        retrieved = achievement_service.get_achievement(achievement_id)
        assert retrieved is None


# ==================== 成就解锁逻辑测试 ====================


class TestAchievementUnlock:
    """成就解锁逻辑测试"""

    def test_check_unlock_cumulative_achievement(
        self, achievement_service, sample_achievements, sample_user, test_db
    ):
        """测试累计型成就解锁"""
        # 创建成就
        achievement_data = sample_achievements[0]  # 勤奋学习者
        achievement = achievement_service.create_achievement(**achievement_data)

        # 用户行为数据（满足条件）
        behavior_stats = {
            "study_time_minutes": 90,  # > 60 分钟
            "courses_completed": 5,
            "code_executions": 5,
        }

        # 检查解锁
        unlocked = achievement_service.check_single_achievement_unlock(
            user_id=sample_user["id"],
            achievement=achievement,
            behavior_stats=behavior_stats,
        )

        assert unlocked is True

    def test_check_not_unlocked(
        self, achievement_service, sample_achievements, sample_user, test_db
    ):
        """测试未达成解锁条件"""
        # 创建成就
        achievement_data = sample_achievements[0]
        achievement = achievement_service.create_achievement(**achievement_data)

        # 用户行为数据（不满足条件）
        behavior_stats = {
            "study_time_minutes": 30,  # < 60 分钟
            "courses_completed": 2,
            "code_executions": 3,
        }

        # 检查解锁
        unlocked = achievement_service.check_single_achievement_unlock(
            user_id=sample_user["id"],
            achievement=achievement,
            behavior_stats=behavior_stats,
        )

        assert unlocked is False

    def test_check_unlock_single_achievement(
        self, achievement_service, sample_achievements, sample_user, test_db
    ):
        """测试单次型成就解锁"""
        # 创建成就
        achievement_data = sample_achievements[2]  # 测验满分
        achievement = achievement_service.create_achievement(**achievement_data)

        # 用户行为数据（满足条件）
        behavior_stats = {"quiz_score": 100, "quizzes_taken": 5}  # 满分

        # 检查解锁
        unlocked = achievement_service.check_single_achievement_unlock(
            user_id=sample_user["id"],
            achievement=achievement,
            behavior_stats=behavior_stats,
        )

        assert unlocked is True

    def test_check_unlock_coding_achievement(
        self, achievement_service, sample_achievements, sample_user, test_db
    ):
        """测试代码执行成就解锁"""
        # 创建成就
        achievement_data = sample_achievements[1]  # 代码新手
        achievement = achievement_service.create_achievement(**achievement_data)

        # 用户行为数据（满足条件）
        behavior_stats = {"code_executions": 15, "study_time_minutes": 30}  # > 10 次

        # 检查解锁
        unlocked = achievement_service.check_single_achievement_unlock(
            user_id=sample_user["id"],
            achievement=achievement,
            behavior_stats=behavior_stats,
        )

        assert unlocked is True


# ==================== 用户成就管理测试 ====================


class TestUserAchievement:
    """用户成就管理测试"""

    def test_unlock_achievement(
        self, achievement_service, sample_achievements, sample_user, test_db
    ):
        """测试解锁成就"""
        # 创建成就
        achievement_data = sample_achievements[0]
        achievement = achievement_service.create_achievement(**achievement_data)

        # 解锁
        user_achievement = achievement_service.unlock_achievement(
            user_id=sample_user["id"], achievement_id=achievement.id
        )

        assert user_achievement is not None
        assert user_achievement.user_id == sample_user["id"]
        assert user_achievement.achievement_id == achievement.id
        assert user_achievement.is_unlocked is True
        assert user_achievement.points_earned == achievement.points_reward

    def test_prevent_duplicate_unlock(
        self, achievement_service, sample_achievements, sample_user, test_db
    ):
        """测试防止重复解锁"""
        # 创建成就
        achievement_data = sample_achievements[0]
        achievement = achievement_service.create_achievement(**achievement_data)

        # 第一次解锁
        achievement_service.unlock_achievement(
            user_id=sample_user["id"], achievement_id=achievement.id
        )

        # 第二次解锁（应该失败或返回已存在的记录）
        with pytest.raises(Exception):
            achievement_service.unlock_achievement(
                user_id=sample_user["id"], achievement_id=achievement.id
            )

    def test_get_user_achievements(
        self, achievement_service, sample_achievements, sample_user, test_db
    ):
        """测试获取用户成就"""
        # 创建并解锁多个成就
        for i, data in enumerate(sample_achievements[:2]):
            achievement = achievement_service.create_achievement(**data)
            if i == 0:  # 只解锁第一个
                achievement_service.unlock_achievement(
                    user_id=sample_user["id"], achievement_id=achievement.id
                )

        # 获取用户成就
        user_achievements = achievement_service.get_user_achievements(
            user_id=sample_user["id"]
        )

        assert len(user_achievements) == 1
        assert user_achievements[0].is_unlocked is True

    def test_get_achievements_by_category(
        self, achievement_service, sample_achievements, sample_user, test_db
    ):
        """测试按分类获取成就"""
        # 创建成就
        for data in sample_achievements:
            achievement_service.create_achievement(**data)

        # 按分类获取
        learning_achievements = achievement_service.get_achievements_by_category(
            category="learning"
        )

        assert len(learning_achievements) == 1
        assert learning_achievements[0].category.value == "learning"


# ==================== 边界条件测试 ====================


class TestEdgeCases:
    """边界条件测试"""

    def test_zero_points_reward(self, achievement_service, sample_user, test_db):
        """测试零积分奖励"""
        achievement = achievement_service.create_achievement(
            name="零积分成就",
            category="special",
            achievement_type="single",
            unlock_condition={"special_condition": True},
            points_reward=0,
            is_hidden=True,
        )

        assert achievement.points_reward == 0
        assert achievement.is_hidden is True

    def test_empty_unlock_condition(self, achievement_service, test_db):
        """测试空解锁条件"""
        achievement = achievement_service.create_achievement(
            name="空条件成就",
            category="special",
            achievement_type="single",
            unlock_condition={},
            points_reward=10,
            is_hidden=False,
        )

        # 空条件应该无法解锁（除非特殊处理）
        behavior_stats = {}
        unlocked = achievement_service.check_single_achievement_unlock(
            user_id=1, achievement=achievement, behavior_stats=behavior_stats
        )

        assert unlocked is False

    def test_invalid_category(self, achievement_service, test_db):
        """测试无效分类"""
        with pytest.raises(ValueError):
            achievement_service.create_achievement(
                name="无效分类成就",
                category="invalid_category",
                achievement_type="cumulative",
                unlock_condition={},
                points_reward=10,
                is_hidden=False,
            )

    def test_negative_points_reward(self, achievement_service, test_db):
        """测试负数积分奖励"""
        with pytest.raises(Exception):
            achievement_service.create_achievement(
                name="负积分成就",
                category="special",
                achievement_type="single",
                unlock_condition={},
                points_reward=-10,
                is_hidden=False,
            )


# ==================== 性能测试 ====================


class TestPerformance:
    """性能测试"""

    def test_bulk_unlock_performance(self, achievement_service, sample_user, test_db):
        """测试批量解锁性能"""
        import time

        # 创建 10 个成就
        for i in range(10):
            achievement_service.create_achievement(
                name=f"成就{i}",
                category="learning",
                achievement_type="cumulative",
                unlock_condition={"study_time_minutes": (i + 1) * 10},
                points_reward=i * 10,
                is_hidden=False,
            )

        # 批量解锁
        start_time = time.time()

        achievements = achievement_service.get_all_achievements()
        for achievement in achievements:
            try:
                achievement_service.unlock_achievement(
                    user_id=sample_user["id"], achievement_id=achievement.id
                )
            except:
                pass  # 忽略重复解锁错误

        end_time = time.time()
        duration = end_time - start_time

        # 应该在 1 秒内完成
        assert duration < 1.0


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
