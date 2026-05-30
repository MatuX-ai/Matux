"""
BACKEND-P1-001 任务验证脚本
测试排行榜排名变化计算功能
"""

import sys
import os
# 添加 backend 目录到 Python 路径
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# 导入模型和服务
from models.leaderboard import UserPoints, LeaderboardRecord, LeaderboardPeriod, LeaderboardType
from models.user import User
from services.leaderboard_service import LeaderboardService
from database.db import Base


def test_rank_change_calculation():
    """测试排名变化计算功能"""
    print("=" * 60)
    print("🧪 BACKEND-P1-001: 排行榜排名变化计算测试")
    print("=" * 60)

    # 创建内存数据库
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 创建测试用户
        users = [
            User(id=1, username='user1', email='user1@test.com'),
            User(id=2, username='user2', email='user2@test.com'),
            User(id=3, username='user3', email='user3@test.com'),
        ]
        for user in users:
            db.add(user)

        # 创建用户积分
        user_points = [
            UserPoints(user_id=1, total_points=300),
            UserPoints(user_id=2, total_points=200),
            UserPoints(user_id=3, total_points=100),
        ]
        for points in user_points:
            db.add(points)

        # 创建上一期的排行榜记录（模拟上期数据）
        now = datetime.now()
        prev_day = now - timedelta(days=1)
        period_start = prev_day.replace(hour=0, minute=0, second=0, microsecond=0)
        period_end = prev_day.replace(hour=23, minute=59, second=59, microsecond=999999)

        # 上期的排名：user1 第 1，user2 第 2，user3 第 3
        prev_records = [
            LeaderboardRecord(
                user_id=1,
                leaderboard_type=LeaderboardType.TOTAL_POINTS.value,
                period=LeaderboardPeriod.DAILY.value,
                period_start=period_start,
                period_end=period_end,
                rank=1,
                score=280,  # 上期分数
                rank_change=0
            ),
            LeaderboardRecord(
                user_id=2,
                leaderboard_type=LeaderboardType.TOTAL_POINTS.value,
                period=LeaderboardPeriod.DAILY.value,
                period_start=period_start,
                period_end=period_end,
                rank=2,
                score=210,
                rank_change=0
            ),
            LeaderboardRecord(
                user_id=3,
                leaderboard_type=LeaderboardType.TOTAL_POINTS.value,
                period=LeaderboardPeriod.DAILY.value,
                period_start=period_start,
                period_end=period_end,
                rank=3,
                score=150,
                rank_change=0
            ),
        ]
        for record in prev_records:
            db.add(record)

        db.commit()

        # 创建服务实例
        service = LeaderboardService(db)

        # 获取今日排行榜
        print("\n📊 今日排行榜:")
        leaderboard = service.get_leaderboard(
            leaderboard_type=LeaderboardType.TOTAL_POINTS,
            period=LeaderboardPeriod.DAILY,
            limit=10
        )

        for entry in leaderboard:
            print(f"  第{entry['rank']}名：{entry['username']} - {entry['score']}分 "
                  f"(排名变化：{entry['rank_change']:+d})")

        # 验证结果
        print("\n✅ 验证结果:")

        # user1: 从第 1 → 第 1，rank_change = 0
        user1 = leaderboard[0]
        assert user1['user_id'] == 1, "user1 应该是第 1 名"
        assert user1['rank_change'] == 0, "user1 排名无变化"
        print(f"  ✓ user1: 排名 {user1['rank']}, 变化 {user1['rank_change']:+d} ✅")

        # user2: 从第 2 → 第 2，rank_change = 0
        user2 = leaderboard[1]
        assert user2['user_id'] == 2, "user2 应该是第 2 名"
        assert user2['rank_change'] == 0, "user2 排名无变化"
        print(f"  ✓ user2: 排名 {user2['rank']}, 变化 {user2['rank_change']:+d} ✅")

        # user3: 从第 3 → 第 3，rank_change = 0
        user3 = leaderboard[2]
        assert user3['user_id'] == 3, "user3 应该是第 3 名"
        assert user3['rank_change'] == 0, "user3 排名无变化"
        print(f"  ✓ user3: 排名 {user3['rank']}, 变化 {user3['rank_change']:+d} ✅")

        # 测试场景 2: 排名发生变化
        print("\n\n📊 测试场景 2: 排名变化")

        # 更新 user3 的积分，使其超过 user2
        user3_points = db.query(UserPoints).filter(UserPoints.user_id == 3).first()
        user3_points.total_points = 350  # 超过 user1 和 user2
        db.commit()

        # 重新获取排行榜
        leaderboard2 = service.get_leaderboard(
            leaderboard_type=LeaderboardType.TOTAL_POINTS,
            period=LeaderboardPeriod.DAILY,
            limit=10
        )

        print("\n更新后的排行榜:")
        for entry in leaderboard2:
            print(f"  第{entry['rank']}名：{entry['username']} - {entry['score']}分 "
                  f"(排名变化：{entry['rank_change']:+d})")

        # user3: 从第 3 → 第 1，rank_change = 3 - 1 = 2 (上升 2 名)
        user3_new = leaderboard2[0]
        assert user3_new['user_id'] == 3, "user3 应该是第 1 名"
        assert user3_new['rank_change'] == 2, "user3 排名上升 2 名"
        print(f"\n  ✓ user3: 从第 3 → 第 1，排名变化 {user3_new['rank_change']:+d} ✅")

        # user1: 从第 1 → 第 2，rank_change = 1 - 2 = -1 (下降 1 名)
        user1_new = leaderboard2[1]
        assert user1_new['user_id'] == 1, "user1 应该是第 2 名"
        assert user1_new['rank_change'] == -1, "user1 排名下降 1 名"
        print(f"  ✓ user1: 从第 1 → 第 2，排名变化 {user1_new['rank_change']:+d} ✅")

        # user2: 从第 2 → 第 3，rank_change = 2 - 3 = -1 (下降 1 名)
        user2_new = leaderboard2[2]
        assert user2_new['user_id'] == 2, "user2 应该是第 3 名"
        assert user2_new['rank_change'] == -1, "user2 排名下降 1 名"
        print(f"  ✓ user2: 从第 2 → 第 3，排名变化 {user2_new['rank_change']:+d} ✅")

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！排名变化计算功能正常！")
        print("=" * 60)

        return True

    except AssertionError as e:
        print(f"\n❌ 测试失败：{e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试出错：{e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = test_rank_change_calculation()
    sys.exit(0 if success else 1)
