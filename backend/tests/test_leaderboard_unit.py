"""
AI-Edu 积分排行榜系统单元测试
测试覆盖：积分计算、交易流水、排行榜排序
"""

from datetime import datetime, timedelta
import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from database.db import Base
from models.leaderboard import PointsTransaction, UserPoints, UserStatistics
from services.leaderboard_service import LeaderboardService, get_leaderboard_service

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
def leaderboard_service(test_db):
    """创建排行榜服务实例"""
    return get_leaderboard_service(test_db)


@pytest.fixture
def sample_users():
    """示例用户数据"""
    return [
        {"id": 1, "username": "user1"},
        {"id": 2, "username": "user2"},
        {"id": 3, "username": "user3"},
    ]


# ==================== 积分管理测试 ====================


class TestPointsManagement:
    """积分管理测试"""

    def test_add_points(self, leaderboard_service, sample_users):
        """测试添加积分"""
        user_id = sample_users[0]["id"]

        points = leaderboard_service.add_points(
            user_id=user_id, amount=100, reason="course_completion"
        )

        assert points is not None
        assert points.total_points == 100
        assert points.available_points == 100
        assert points.consumed_points == 0

    def test_spend_points(self, leaderboard_service, sample_users):
        """测试消费积分"""
        user_id = sample_users[0]["id"]

        # 先添加积分
        leaderboard_service.add_points(user_id=user_id, amount=100, reason="initial")

        # 消费积分
        points = leaderboard_service.spend_points(
            user_id=user_id, amount=50, reason="redeem_gift"
        )

        assert points.total_points == 100
        assert points.available_points == 50
        assert points.consumed_points == 50

    def test_spend_insufficient_points(self, leaderboard_service, sample_users):
        """测试积分不足"""
        user_id = sample_users[0]["id"]

        # 尝试消费不存在的积分
        with pytest.raises(ValueError) as exc_info:
            leaderboard_service.spend_points(user_id=user_id, amount=100, reason="test")

        assert "积分不足" in str(exc_info.value)

    def test_points_transaction_record(
        self, leaderboard_service, sample_users, test_db
    ):
        """测试积分交易记录"""
        user_id = sample_users[0]["id"]

        # 添加积分
        leaderboard_service.add_points(
            user_id=user_id,
            amount=100,
            reason="course_completion",
            reference_type="course",
            reference_id=1,
        )

        # 查询交易记录
        transactions = leaderboard_service.get_points_history(user_id=user_id, limit=10)

        assert len(transactions) == 1
        assert transactions[0].transaction_type == "earn"
        assert transactions[0].points_amount == 100
        assert transactions[0].reason == "course_completion"
        assert transactions[0].reference_type == "course"
        assert transactions[0].reference_id == 1

    def test_points_breakdown(self, leaderboard_service, sample_users):
        """测试积分来源明细"""
        user_id = sample_users[0]["id"]

        # 多次添加积分
        leaderboard_service.add_points(
            user_id=user_id, amount=50, reason="course_completion"
        )
        leaderboard_service.add_points(
            user_id=user_id, amount=30, reason="achievement_unlock"
        )
        leaderboard_service.add_points(
            user_id=user_id, amount=20, reason="quiz_perfect"
        )

        points = leaderboard_service.get_user_points(user_id=user_id)

        assert points.points_breakdown["course_completion"] == 50
        assert points.points_breakdown["achievement_unlock"] == 30
        assert points.points_breakdown["quiz_perfect"] == 20
        assert points.total_points == 100


# ==================== 用户统计测试 ====================


class TestUserStatistics:
    """用户统计测试"""

    def test_create_user_statistics(self, leaderboard_service, sample_users):
        """测试创建用户统计"""
        user_id = sample_users[0]["id"]

        stats = leaderboard_service.get_user_statistics(user_id=user_id)

        assert stats is not None
        assert stats.user_id == user_id
        assert stats.total_study_time_minutes == 0
        assert stats.courses_completed == 0

    def test_update_user_statistics(self, leaderboard_service, sample_users, test_db):
        """测试更新用户统计"""
        user_id = sample_users[0]["id"]

        # 手动更新一些数据（实际应该从其他表聚合）
        stats = leaderboard_service.get_user_statistics(user_id=user_id)
        stats.total_study_time_minutes = 120
        stats.courses_completed = 5
        stats.achievements_unlocked = 3
        test_db.commit()

        # 重新获取
        updated_stats = leaderboard_service.update_user_statistics(user_id=user_id)

        assert updated_stats.total_study_time_minutes >= 120
        assert updated_stats.courses_completed >= 5
        assert updated_stats.achievements_unlocked >= 3


# ==================== 排行榜排序测试 ====================


class TestLeaderboardRanking:
    """排行榜排序测试"""

    def test_get_points_leaderboard(self, leaderboard_service, sample_users):
        """测试积分排行榜排序"""
        # 为不同用户添加不同积分
        leaderboard_service.add_points(user_id=1, amount=100, reason="test")
        leaderboard_service.add_points(user_id=2, amount=300, reason="test")
        leaderboard_service.add_points(user_id=3, amount=200, reason="test")

        # 获取排行榜（应该按积分降序）
        from models.leaderboard import LeaderboardPeriod, LeaderboardType

        leaderboard = leaderboard_service.get_leaderboard(
            leaderboard_type=LeaderboardType.TOTAL_POINTS,
            period=LeaderboardPeriod.ALL_TIME,
            limit=10,
        )

        assert len(leaderboard) == 3
        assert leaderboard[0]["rank"] == 1
        assert leaderboard[0]["score"] == 300  # user2
        assert leaderboard[1]["score"] == 200  # user3
        assert leaderboard[2]["score"] == 100  # user1

    def test_get_study_time_leaderboard(
        self, leaderboard_service, sample_users, test_db
    ):
        """测试学习时长排行榜"""
        # 创建不同的学习时长
        for i, user in enumerate(sample_users):
            stats = leaderboard_service.get_user_statistics(user_id=user["id"])
            stats.total_study_time_minutes = (i + 1) * 60  # 60, 120, 180
            test_db.commit()

        from models.leaderboard import LeaderboardPeriod, LeaderboardType

        leaderboard = leaderboard_service.get_leaderboard(
            leaderboard_type=LeaderboardType.STUDY_TIME,
            period=LeaderboardPeriod.ALL_TIME,
            limit=10,
        )

        assert len(leaderboard) == 3
        assert leaderboard[0]["score"] == 180  # user3
        assert leaderboard[1]["score"] == 120  # user2
        assert leaderboard[2]["score"] == 60  # user1

    def test_limit_leaderboard_results(self, leaderboard_service, sample_users):
        """测试限制返回数量"""
        # 创建数据
        for user in sample_users:
            leaderboard_service.add_points(
                user_id=user["id"], amount=100, reason="test"
            )

        from models.leaderboard import LeaderboardPeriod, LeaderboardType

        # 只返回前 2 名
        leaderboard = leaderboard_service.get_leaderboard(
            leaderboard_type=LeaderboardType.TOTAL_POINTS,
            period=LeaderboardPeriod.ALL_TIME,
            limit=2,
        )

        assert len(leaderboard) == 2

    def test_get_user_rank(self, leaderboard_service, sample_users):
        """测试获取用户排名"""
        # 创建数据
        leaderboard_service.add_points(user_id=1, amount=100, reason="test")
        leaderboard_service.add_points(user_id=2, amount=300, reason="test")
        leaderboard_service.add_points(user_id=3, amount=200, reason="test")

        from models.leaderboard import LeaderboardPeriod, LeaderboardType

        # 获取 user1 的排名
        rank_info = leaderboard_service.get_user_rank(
            user_id=1,
            leaderboard_type=LeaderboardType.TOTAL_POINTS,
            period=LeaderboardPeriod.ALL_TIME,
        )

        assert rank_info["rank"] == 3  # user1 排第 3


# ==================== 排名变化测试 ====================


class TestRankChange:
    """排名变化计算测试"""

    def test_rank_change_calculation(self, leaderboard_service, sample_users, test_db):
        """测试排名变化计算逻辑"""
        from models.leaderboard import (
            LeaderboardPeriod,
            LeaderboardRecord,
            LeaderboardType,
        )

        # 创建上一期的排名记录
        # user1: 第 3 名，user2: 第 1 名，user3: 第 2 名
        prev_period_start = datetime.now() - timedelta(days=2)
        prev_period_end = datetime.now() - timedelta(days=1)

        for i, user in enumerate(sample_users):
            record = LeaderboardRecord(
                user_id=user["id"],
                period="all_time",  # 使用 all_time 作为测试
                period_start=prev_period_start,
                period_end=prev_period_end,
                rank=i + 1,  # user1=1, user2=2, user3=3
                score=(3 - i) * 100,  # 300, 200, 100
                score_type="total_points",
                created_at=prev_period_start,
            )
            test_db.add(record)
        test_db.commit()

        # 创建本期数据（排名反转）
        # user1: 300 分（应该第 1），user2: 200 分（应该第 2），user3: 100 分（应该第 3）
        leaderboard_service.add_points(user_id=1, amount=300, reason="current")
        leaderboard_service.add_points(user_id=2, amount=200, reason="current")
        leaderboard_service.add_points(user_id=3, amount=100, reason="current")

        # 获取排行榜
        leaderboard = leaderboard_service.get_leaderboard(
            leaderboard_type=LeaderboardType.TOTAL_POINTS,
            period=LeaderboardPeriod.ALL_TIME,
            limit=10,
        )

        assert len(leaderboard) == 3

        # user1: 从上期第 1 -> 本期第 1，rank_change = 0
        assert leaderboard[0]["user_id"] == 1
        assert leaderboard[0]["rank"] == 1
        assert leaderboard[0]["score"] == 300
        # 由于上期记录使用的是"all_time"周期，而_get_previous_period_records 对 ALL_TIME 返回空字典
        # 所以这里 rank_change 应该是 0
        assert leaderboard[0]["rank_change"] == 0

        # user2: 从上期第 2 -> 本期第 2，rank_change = 0
        assert leaderboard[1]["user_id"] == 2
        assert leaderboard[1]["rank"] == 2
        assert leaderboard[1]["score"] == 200
        assert leaderboard[1]["rank_change"] == 0

        # user3: 从上期第 3 -> 本期第 3，rank_change = 0
        assert leaderboard[2]["user_id"] == 3
        assert leaderboard[2]["rank"] == 3
        assert leaderboard[2]["score"] == 100
        assert leaderboard[2]["rank_change"] == 0

    def test_rank_change_rising(self, leaderboard_service, sample_users, test_db):
        """测试排名上升场景"""
        from models.leaderboard import (
            LeaderboardPeriod,
            LeaderboardRecord,
            LeaderboardType,
        )

        # 模拟日榜的上期数据
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        prev_period_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        prev_period_end = yesterday.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # 上期：user1 第 5 名，user2 第 3 名，user3 第 1 名
        test_db.add(
            LeaderboardRecord(
                user_id=1,
                period="daily",
                period_start=prev_period_start,
                period_end=prev_period_end,
                rank=5,
                score=50,
                score_type="total_points",
                created_at=prev_period_start,
            )
        )
        test_db.add(
            LeaderboardRecord(
                user_id=2,
                period="daily",
                period_start=prev_period_start,
                period_end=prev_period_end,
                rank=3,
                score=150,
                score_type="total_points",
                created_at=prev_period_start,
            )
        )
        test_db.add(
            LeaderboardRecord(
                user_id=3,
                period="daily",
                period_start=prev_period_start,
                period_end=prev_period_end,
                rank=1,
                score=250,
                score_type="total_points",
                created_at=prev_period_start,
            )
        )
        test_db.commit()

        # 本期：user1 表现好，应该排第 1
        leaderboard_service.add_points(user_id=1, amount=300, reason="today")
        leaderboard_service.add_points(user_id=2, amount=200, reason="today")
        leaderboard_service.add_points(user_id=3, amount=100, reason="today")

        # 获取日榜
        leaderboard = leaderboard_service.get_leaderboard(
            leaderboard_type=LeaderboardType.TOTAL_POINTS,
            period=LeaderboardPeriod.DAILY,
            limit=10,
        )

        # user1 从第 5 上升到第 1，rank_change = 5 - 1 = 4（正数表示上升）
        user1_entry = next(entry for entry in leaderboard if entry["user_id"] == 1)
        assert user1_entry["rank"] == 1
        assert user1_entry["rank_change"] == 4  # 上升 4 名

    def test_rank_change_falling(self, leaderboard_service, sample_users, test_db):
        """测试排名下降场景"""
        from models.leaderboard import (
            LeaderboardPeriod,
            LeaderboardRecord,
            LeaderboardType,
        )

        # 上期：user1 第 1 名
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        prev_period_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        prev_period_end = yesterday.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        test_db.add(
            LeaderboardRecord(
                user_id=1,
                period="daily",
                period_start=prev_period_start,
                period_end=prev_period_end,
                rank=1,
                score=300,
                score_type="total_points",
                created_at=prev_period_start,
            )
        )
        test_db.commit()

        # 本期：user1 表现差，排第 3
        leaderboard_service.add_points(user_id=1, amount=100, reason="today")
        leaderboard_service.add_points(user_id=2, amount=200, reason="today")
        leaderboard_service.add_points(user_id=3, amount=300, reason="today")

        leaderboard = leaderboard_service.get_leaderboard(
            leaderboard_type=LeaderboardType.TOTAL_POINTS,
            period=LeaderboardPeriod.DAILY,
            limit=10,
        )

        # user1 从第 1 下降到第 3，rank_change = 1 - 3 = -2（负数表示下降）
        user1_entry = next(entry for entry in leaderboard if entry["user_id"] == 1)
        assert user1_entry["rank"] == 3
        assert user1_entry["rank_change"] == -2  # 下降 2 名

    def test_rank_change_new_user(self, leaderboard_service, sample_users, test_db):
        """测试新用户（上期无记录）"""
        from models.leaderboard import LeaderboardPeriod, LeaderboardType

        # 只有本期数据，没有上期记录
        leaderboard_service.add_points(user_id=1, amount=100, reason="today")
        leaderboard_service.add_points(user_id=2, amount=200, reason="today")

        leaderboard = leaderboard_service.get_leaderboard(
            leaderboard_type=LeaderboardType.TOTAL_POINTS,
            period=LeaderboardPeriod.DAILY,
            limit=10,
        )

        # 新用户 rank_change 应该为 0
        for entry in leaderboard:
            assert entry["rank_change"] == 0

    def test_rank_change_no_previous_period(self, leaderboard_service, sample_users):
        """测试无上期数据的周期（如 ALL_TIME）"""
        from models.leaderboard import LeaderboardPeriod, LeaderboardType

        # ALL_TIME 没有"上一期"的概念
        leaderboard_service.add_points(user_id=1, amount=100, reason="test")
        leaderboard_service.add_points(user_id=2, amount=200, reason="test")

        leaderboard = leaderboard_service.get_leaderboard(
            leaderboard_type=LeaderboardType.TOTAL_POINTS,
            period=LeaderboardPeriod.ALL_TIME,
            limit=10,
        )

        # ALL_TIME 周期 rank_change 应该为 0
        for entry in leaderboard:
            assert entry["rank_change"] == 0


# ==================== 边界条件测试 ====================


class TestEdgeCases:
    """边界条件测试"""

    def test_zero_points(self, leaderboard_service, sample_users):
        """测试零积分"""
        user_id = sample_users[0]["id"]

        points = leaderboard_service.get_user_points(user_id=user_id)

        assert points.total_points == 0
        assert points.available_points == 0

    def test_large_points_amount(self, leaderboard_service, sample_users):
        """测试大数额积分"""
        user_id = sample_users[0]["id"]

        # 添加大额积分
        points = leaderboard_service.add_points(
            user_id=user_id, amount=1000000, reason="large_bonus"
        )

        assert points.total_points == 1000000
        assert points.available_points == 1000000

    def test_exact_points_balance(self, leaderboard_service, sample_users):
        """测试精确余额（消费全部积分）"""
        user_id = sample_users[0]["id"]

        # 添加积分
        leaderboard_service.add_points(user_id=user_id, amount=100, reason="test")

        # 消费全部
        points = leaderboard_service.spend_points(
            user_id=user_id, amount=100, reason="spend_all"
        )

        assert points.available_points == 0
        assert points.consumed_points == 100

    def test_empty_leaderboard(self, leaderboard_service):
        """测试空排行榜"""
        from models.leaderboard import LeaderboardPeriod, LeaderboardType

        leaderboard = leaderboard_service.get_leaderboard(
            leaderboard_type=LeaderboardType.TOTAL_POINTS,
            period=LeaderboardPeriod.ALL_TIME,
            limit=10,
        )

        assert len(leaderboard) == 0


# ==================== 并发测试 ====================


class TestConcurrency:
    """并发测试"""

    def test_concurrent_points_operations(self, leaderboard_service, sample_users):
        """测试并发积分操作"""
        import threading

        user_id = sample_users[0]["id"]
        errors = []

        def add_points_thread():
            try:
                for _ in range(10):
                    leaderboard_service.add_points(
                        user_id=user_id, amount=10, reason="concurrent"
                    )
            except Exception as e:
                errors.append(e)

        # 创建多个线程
        threads = [threading.Thread(target=add_points_thread) for _ in range(5)]

        # 启动线程
        for t in threads:
            t.start()

        # 等待完成
        for t in threads:
            t.join()

        # 验证结果
        assert len(errors) == 0

        points = leaderboard_service.get_user_points(user_id=user_id)
        expected = 5 * 10 * 10  # 5 个线程，每个 10 次，每次 10 积分
        assert points.total_points == expected


# ==================== 性能测试 ====================


class TestPerformance:
    """性能测试"""

    def test_bulk_points_operations(self, leaderboard_service, sample_users):
        """测试批量积分操作性能"""
        import time

        user_id = sample_users[0]["id"]

        start_time = time.time()

        # 执行 100 次积分操作
        for i in range(100):
            leaderboard_service.add_points(
                user_id=user_id, amount=1, reason=f"operation_{i}"
            )

        end_time = time.time()
        duration = end_time - start_time

        # 应该在合理时间内完成
        assert duration < 5.0  # 5 秒内

        # 验证积分正确
        points = leaderboard_service.get_user_points(user_id=user_id)
        assert points.total_points == 100


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
