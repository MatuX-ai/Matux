"""
任务编排服务单元测试 - 积分发放功能
测试覆盖：积分发放、错误处理、日志记录
"""

import os
import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.task_orchestration_service import TaskOrchestrationService

# ==================== 测试夹具 ====================


@pytest.fixture
def mock_db_session():
    """模拟数据库会话"""
    db = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def task_orchestration_service(mock_db_session):
    """创建任务编排服务实例（带 mock 数据库）"""
    return TaskOrchestrationService(db_session=mock_db_session)


# ==================== 积分发放测试 ====================


class TestPointsAward:
    """积分发放测试"""

    @pytest.mark.asyncio
    async def test_award_points_success(
        self, task_orchestration_service, mock_db_session
    ):
        """测试成功发放积分"""
        # Mock 积分服务
        mock_points_record = Mock()
        mock_points_record.total_points = 500

        with patch(
            "services.leaderboard_service.leaderboard_service.get_leaderboard_service"
        ) as mock_get_service:
            mock_points_service = Mock()
            mock_points_service.add_points = Mock(return_value=mock_points_record)
            mock_get_service.return_value = mock_points_service

            # 调用方法
            result = await task_orchestration_service._award_points_to_user(
                user_id=123, points=300, reason="阶段 1 完成"
            )

            # 验证结果
            assert result is True

            # 验证调用了 add_points
            mock_points_service.add_points.assert_called_once_with(
                user_id=123,
                amount=300,
                reason="task_completion",
                reference_type="linked_task",
                reference_description="阶段 1 完成",
            )

    @pytest.mark.asyncio
    async def test_award_points_no_db_session(self, task_orchestration_service):
        """测试无数据库会话时返回 False"""
        # 移除数据库会话
        task_orchestration_service.db = None

        # 调用方法
        result = await task_orchestration_service._award_points_to_user(
            user_id=123, points=300, reason="测试"
        )

        # 应该返回 False
        assert result is False

    @pytest.mark.asyncio
    async def test_award_points_exception_handling(
        self, task_orchestration_service, mock_db_session
    ):
        """测试异常处理"""
        with patch(
            "services.leaderboard_service.leaderboard_service.get_leaderboard_service"
        ) as mock_get_service:
            # 模拟异常
            mock_get_service.side_effect = Exception("数据库错误")

            # 调用方法
            result = await task_orchestration_service._award_points_to_user(
                user_id=123, points=300, reason="测试"
            )

            # 应该返回 False
            assert result is False

    @pytest.mark.asyncio
    async def test_award_points_different_amounts(
        self, task_orchestration_service, mock_db_session
    ):
        """测试不同积分数额"""
        mock_points_record = Mock()
        mock_points_record.total_points = 1000

        test_cases = [
            (100, "小奖励"),
            (500, "中奖励"),
            (1000, "大奖励"),
            (0, "零积分"),
        ]

        for points, reason in test_cases:
            with patch(
                "services.leaderboard_service.leaderboard_service.get_leaderboard_service"
            ) as mock_get_service:
                mock_points_service = Mock()
                mock_points_service.add_points = Mock(return_value=mock_points_record)
                mock_get_service.return_value = mock_points_service

                result = await task_orchestration_service._award_points_to_user(
                    user_id=123, points=points, reason=reason
                )

                assert result is True
                mock_points_service.add_points.assert_called_with(
                    user_id=123,
                    amount=points,
                    reason="task_completion",
                    reference_type="linked_task",
                    reference_description=reason,
                )


# ==================== XP 奖励计算测试 ====================


class TestXPCalculation:
    """XP 奖励计算测试"""

    @pytest.mark.asyncio
    async def test_award_stage1_xp_base_only(
        self, task_orchestration_service, mock_db_session
    ):
        """测试只有基础 XP（准确率低）"""
        metrics = {"accuracy": 0.75}

        with patch.object(
            task_orchestration_service, "_award_points_to_user", return_value=True
        ):
            result = await task_orchestration_service._award_stage1_xp(
                user_id=123, metrics=metrics
            )

            # 基础 300 XP，无奖金
            assert result == 300

    @pytest.mark.asyncio
    async def test_award_stage1_xp_85_accuracy(
        self, task_orchestration_service, mock_db_session
    ):
        """测试准确率 85%"""
        metrics = {"accuracy": 0.85}

        with patch.object(
            task_orchestration_service, "_award_points_to_user", return_value=True
        ):
            result = await task_orchestration_service._award_stage1_xp(
                user_id=123, metrics=metrics
            )

            # 基础 300 + 奖金 100 = 400 XP
            assert result == 400

    @pytest.mark.asyncio
    async def test_award_stage1_xp_90_accuracy(
        self, task_orchestration_service, mock_db_session
    ):
        """测试准确率 90%"""
        metrics = {"accuracy": 0.90}

        with patch.object(
            task_orchestration_service, "_award_points_to_user", return_value=True
        ):
            result = await task_orchestration_service._award_stage1_xp(
                user_id=123, metrics=metrics
            )

            # 基础 300 + 奖金 200 = 500 XP
            assert result == 500

    @pytest.mark.asyncio
    async def test_award_stage1_xp_95_accuracy(
        self, task_orchestration_service, mock_db_session
    ):
        """测试准确率 95%+"""
        metrics = {"accuracy": 0.96}

        with patch.object(
            task_orchestration_service, "_award_points_to_user", return_value=True
        ):
            result = await task_orchestration_service._award_stage1_xp(
                user_id=123, metrics=metrics
            )

            # 基础 300 + 奖金 300 = 600 XP
            assert result == 600

    @pytest.mark.asyncio
    async def test_award_stage1_xp_with_points_award(
        self, task_orchestration_service, mock_db_session
    ):
        """测试 XP 发放并调用积分服务"""
        metrics = {"accuracy": 0.95}

        with patch.object(
            task_orchestration_service, "_award_points_to_user"
        ) as mock_award:
            mock_award.return_value = True

            result = await task_orchestration_service._award_stage1_xp(
                user_id=123, metrics=metrics
            )

            assert result == 600

            # 验证调用了积分发放
            mock_award.assert_called_once_with(123, 600, "阶段 1 完成")


# ==================== 边界条件测试 ====================


class TestEdgeCases:
    """边界条件测试"""

    @pytest.mark.asyncio
    async def test_award_points_zero(self, task_orchestration_service, mock_db_session):
        """测试零积分发放"""
        mock_points_record = Mock()
        mock_points_record.total_points = 0

        with patch(
            "services.leaderboard_service.leaderboard_service.get_leaderboard_service"
        ) as mock_get_service:
            mock_points_service = Mock()
            mock_points_service.add_points = Mock(return_value=mock_points_record)
            mock_get_service.return_value = mock_points_service

            result = await task_orchestration_service._award_points_to_user(
                user_id=123, points=0, reason="参与奖"
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_award_points_special_characters_in_reason(
        self, task_orchestration_service, mock_db_session
    ):
        """测试特殊字符的原因描述"""
        mock_points_record = Mock()
        mock_points_record.total_points = 300

        with patch(
            "services.leaderboard_service.leaderboard_service.get_leaderboard_service"
        ) as mock_get_service:
            mock_points_service = Mock()
            mock_points_service.add_points = Mock(return_value=mock_points_record)
            mock_get_service.return_value = mock_points_service

            result = await task_orchestration_service._award_points_to_user(
                user_id=123, points=300, reason="特殊原因！@#$%^&*()"
            )

            assert result is True


# ==================== 集成测试 ====================


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_submission_flow(
        self, task_orchestration_service, mock_db_session
    ):
        """测试完整的提交流程"""
        # Mock 所有依赖
        mock_points_record = Mock()
        mock_points_record.total_points = 800

        with patch.object(
            task_orchestration_service, "_award_points_to_user"
        ) as mock_award:
            mock_award.return_value = True

            # 模拟高准确率
            metrics = {"accuracy": 0.95}

            # 调用 XP 发放
            xp_earned = await task_orchestration_service._award_stage1_xp(
                user_id=123, metrics=metrics
            )

            # 验证
            assert xp_earned == 600
            mock_award.assert_called_once_with(123, 600, "阶段 1 完成")


# ==================== 运行测试 ====================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
