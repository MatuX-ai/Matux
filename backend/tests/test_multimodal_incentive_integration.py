import asyncio
from datetime import datetime, timedelta
import json
import unittest
from unittest.mock import AsyncMock, Mock, patch

from backend.services.achievement_badge_system import achievement_system
from backend.services.ar_reward_service import ar_reward_service
from backend.services.complex_gesture_recognizer import complex_gesture_recognizer
from backend.services.hidden_task_reward_system import hidden_task_system
from backend.services.integral_decay_calculator import decay_calculator

# 导入被测试的模块
from backend.services.reward_event_bus import RewardEvent, reward_event_bus
from backend.services.voice_correction_detector import VoiceCorrectionDetector
from backend.services.voice_reward_service import voice_reward_service


class TestMultimodalIncentiveIntegration(unittest.TestCase):
    """多模态激励联动功能集成测试"""

    def setUp(self):
        """测试初始化"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # 模拟用户数据
        self.test_user_id = 1001
        self.test_voice_command = "正确连接D9引脚到LED正极"
        self.test_ar_scene_data = {
            "accuracy": 92.5,
            "components_placed": 4,
            "total_components": 4,
            "completion_time": 156.0,
        }

    def tearDown(self):
        """测试清理"""
        self.loop.close()

    def test_voice_correction_reward_flow(self):
        """测试语音纠错奖励完整流程"""

        async def test_flow():
            # 1. 语音纠错检测
            detector = VoiceCorrectionDetector()
            correction_result = detector.detect_corrections(self.test_voice_command)

            self.assertIsNotNone(correction_result)
            self.assertTrue(correction_result.is_correction)
            self.assertGreater(correction_result.confidence, 0.5)

            # 2. 发送奖励事件
            event = RewardEvent(
                event_type="voice_correction",
                user_id=self.test_user_id,
                data={
                    "correction_type": correction_result.correction_type,
                    "confidence": correction_result.confidence,
                    "accuracy": correction_result.accuracy,
                    "command": self.test_voice_command,
                },
                timestamp=datetime.now(),
            )

            # 3. 验证奖励服务处理
            # 这里应该mock区块链调用
            with patch(
                "backend.utils.blockchain_client.BlockchainClient.invoke_integral_chaincode"
            ) as mock_invoke:
                mock_invoke.return_value = {"success": True, "message": "积分发放成功"}

                # 模拟事件总线发布
                await reward_event_bus.publish(event)

                # 验证积分发放调用
                mock_invoke.assert_called()

        self.loop.run_until_complete(test_flow())

    def test_ar_scene_completion_flow(self):
        """测试AR场景完成奖励流程"""

        async def test_flow():
            # 1. 构造场景完成数据
            scene_data = {
                "accuracy": self.test_ar_scene_data["accuracy"],
                "completion_time": self.test_ar_scene_data["completion_time"],
                "components_placed": self.test_ar_scene_data["components_placed"],
                "total_components": self.test_ar_scene_data["total_components"],
                "bonus_points": 50,
                "scene_id": "test_circuit_001",
            }

            # 2. 发送场景完成事件
            event = RewardEvent(
                event_type="ar_scene_completed",
                user_id=self.test_user_id,
                data=scene_data,
                timestamp=datetime.now(),
            )

            # 3. 验证AR奖励服务处理
            with patch(
                "backend.utils.blockchain_client.BlockchainClient.invoke_integral_chaincode"
            ) as mock_invoke:
                mock_invoke.return_value = {"success": True, "message": "积分发放成功"}

                await reward_event_bus.publish(event)

                # 验证积分发放和成就检查
                mock_invoke.assert_called()

                # 检查成就解锁
                achievements = achievement_system.get_user_achievements(
                    self.test_user_id
                )
                self.assertIsInstance(achievements, list)

        self.loop.run_until_complete(test_flow())

    def test_gesture_sequence_detection(self):
        """测试手势序列检测"""

        async def test_flow():
            # 1. 模拟手势点数据
            from backend.services.complex_gesture_recognizer import GesturePoint

            gesture_points = [
                GesturePoint(x=0.1, y=0.2, z=0.0, timestamp=100.0, confidence=0.9),
                GesturePoint(x=0.2, y=0.3, z=0.0, timestamp=100.1, confidence=0.85),
                GesturePoint(x=0.3, y=0.4, z=0.0, timestamp=100.2, confidence=0.92),
            ]

            # 2. 添加到复杂手势识别器
            complex_gesture_recognizer.add_gesture_points(gesture_points)

            # 3. 检测复杂序列
            sequences = complex_gesture_recognizer.detect_complex_sequences()

            # 4. 验证序列检测结果
            self.assertIsInstance(sequences, list)

            # 5. 如果检测到序列，验证隐藏任务触发
            for sequence_name, confidence in sequences:
                if confidence > 0.8:
                    # 触发隐藏任务事件
                    event = RewardEvent(
                        event_type="complex_gesture_sequence",
                        user_id=self.test_user_id,
                        data={"sequence_name": sequence_name, "confidence": confidence},
                        timestamp=datetime.now(),
                    )

                    with patch(
                        "backend.utils.blockchain_client.BlockchainClient.invoke_integral_chaincode"
                    ) as mock_invoke:
                        mock_invoke.return_value = {"success": True}
                        await reward_event_bus.publish(event)
                        mock_invoke.assert_called()

        self.loop.run_until_complete(test_flow())

    def test_integral_decay_calculation(self):
        """测试积分衰减计算"""

        async def test_flow():
            # 1. 设置测试用户积分
            initial_points = 1000
            user_level = "standard"

            # 2. 计算衰减
            decay_amount = decay_calculator.calculate_daily_decay(
                self.test_user_id, initial_points, user_level
            )

            # 3. 验证衰减计算
            self.assertIsInstance(decay_amount, int)
            self.assertGreaterEqual(decay_amount, 0)
            self.assertLess(decay_amount, initial_points)

            # 4. 验证衰减历史记录
            summary = decay_calculator.get_user_decay_summary(self.test_user_id)
            self.assertIn("current_points", summary)
            self.assertIn("decayed_points", summary)

            # 5. 测试衰减预测
            projection = decay_calculator.get_decay_projection(self.test_user_id, 7)
            self.assertIsInstance(projection, list)
            self.assertEqual(len(projection), 7)

        self.loop.run_until_complete(test_flow())

    def test_hidden_task_completion(self):
        """测试隐藏任务完成流程"""

        async def test_flow():
            # 1. 模拟完成隐藏任务
            task_completion_data = {
                "task_name": "ht_gesture_master",
                "points": 200,
                "completion_time": datetime.now().isoformat(),
            }

            # 2. 发送隐藏任务完成事件
            event = RewardEvent(
                event_type="hidden_task_completed",
                user_id=self.test_user_id,
                data=task_completion_data,
                timestamp=datetime.now(),
            )

            # 3. 验证隐藏任务系统处理
            with patch(
                "backend.utils.blockchain_client.BlockchainClient.invoke_integral_chaincode"
            ) as mock_invoke:
                mock_invoke.return_value = {"success": True, "message": "奖励发放成功"}

                await reward_event_bus.publish(event)

                # 验证奖励发放
                mock_invoke.assert_called()

                # 检查任务进度更新
                task_status = await hidden_task_system.get_user_hidden_tasks(
                    self.test_user_id
                )
                self.assertIn("completed_tasks", task_status)

        self.loop.run_until_complete(test_flow())

    def test_cross_module_event_coordination(self):
        """测试跨模块事件协调"""

        async def test_flow():
            events_received = []

            # 1. 设置多个事件监听器
            def voice_listener(event):
                events_received.append(("voice", event.event_type))

            def ar_listener(event):
                events_received.append(("ar", event.event_type))

            def gesture_listener(event):
                events_received.append(("gesture", event.event_type))

            reward_event_bus.subscribe("voice_correction", voice_listener)
            reward_event_bus.subscribe("ar_scene_completed", ar_listener)
            reward_event_bus.subscribe("complex_gesture_sequence", gesture_listener)

            # 2. 并发发送不同类型事件
            events = [
                RewardEvent(
                    "voice_correction",
                    self.test_user_id,
                    {"test": "voice"},
                    datetime.now(),
                ),
                RewardEvent(
                    "ar_scene_completed",
                    self.test_user_id,
                    {"test": "ar"},
                    datetime.now(),
                ),
                RewardEvent(
                    "complex_gesture_sequence",
                    self.test_user_id,
                    {"test": "gesture"},
                    datetime.now(),
                ),
            ]

            # 3. 异步发布所有事件
            tasks = [reward_event_bus.publish(event) for event in events]
            await asyncio.gather(*tasks)

            # 4. 验证所有事件都被正确处理
            self.assertEqual(len(events_received), 3)
            event_types = [etype for _, etype in events_received]
            self.assertIn("voice_correction", event_types)
            self.assertIn("ar_scene_completed", event_types)
            self.assertIn("complex_gesture_sequence", event_types)

            # 5. 清理监听器
            reward_event_bus.unsubscribe("voice_correction", voice_listener)
            reward_event_bus.unsubscribe("ar_scene_completed", ar_listener)
            reward_event_bus.unsubscribe("complex_gesture_sequence", gesture_listener)

        self.loop.run_until_complete(test_flow())

    def test_system_resilience(self):
        """测试系统韧性"""

        async def test_flow():
            # 1. 测试错误处理
            invalid_event = RewardEvent(
                event_type="invalid_event_type",
                user_id=self.test_user_id,
                data={"invalid": "data"},
                timestamp=datetime.now(),
            )

            # 2. 验证系统能处理无效事件而不崩溃
            try:
                await reward_event_bus.publish(invalid_event)
                # 系统应该优雅地处理无效事件
            except Exception as e:
                self.fail(f"系统不应该因无效事件而崩溃: {e}")

            # 3. 测试网络异常情况
            with patch(
                "backend.utils.blockchain_client.BlockchainClient.invoke_integral_chaincode"
            ) as mock_invoke:
                mock_invoke.side_effect = Exception("网络连接失败")

                event = RewardEvent(
                    event_type="voice_correction",
                    user_id=self.test_user_id,
                    data={"test": "data"},
                    timestamp=datetime.now(),
                )

                # 系统应该处理异常而不崩溃
                try:
                    await reward_event_bus.publish(event)
                except Exception as e:
                    self.fail(f"系统应该优雅处理网络异常: {e}")

        self.loop.run_until_complete(test_flow())


class TestPerformanceIntegration(unittest.TestCase):
    """性能集成测试"""

    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_concurrent_event_processing(self):
        """测试并发事件处理性能"""

        async def test_performance():
            user_count = 100
            events_per_user = 10

            # 1. 准备大量并发事件
            events = []
            for user_id in range(1, user_count + 1):
                for i in range(events_per_user):
                    event = RewardEvent(
                        event_type="voice_correction",
                        user_id=user_id,
                        data={"iteration": i, "user_id": user_id},
                        timestamp=datetime.now(),
                    )
                    events.append(event)

            # 2. 记录开始时间
            start_time = datetime.now()

            # 3. 并发处理所有事件
            with patch(
                "backend.utils.blockchain_client.BlockchainClient.invoke_integral_chaincode"
            ) as mock_invoke:
                mock_invoke.return_value = {"success": True}

                tasks = [reward_event_bus.publish(event) for event in events]
                await asyncio.gather(*tasks, return_exceptions=True)

            # 4. 计算处理时间
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            # 5. 验证性能指标
            total_events = user_count * events_per_user
            events_per_second = (
                total_events / processing_time if processing_time > 0 else 0
            )

            print(f"处理{total_events}个事件耗时: {processing_time:.2f}秒")
            print(f"平均每秒处理: {events_per_second:.2f}个事件")

            # 基本性能要求：1000个事件应在5秒内处理完
            self.assertLess(processing_time, 5.0)
            self.assertGreater(events_per_second, 200.0)

        self.loop.run_until_complete(test_performance())


if __name__ == "__main__":
    # 运行集成测试
    unittest.main(verbosity=2)
