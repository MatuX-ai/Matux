"""
AR/VR Mock服务测试套件
包含单元测试、集成测试和性能测试
"""

import os
import sys
import unittest
from unittest.mock import Mock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.ar_vr_mock_service import (
    ARVRMockOrchestrator,
    InteractionMockHandler,
    MockScenario,
    PhysicsMockEngine,
    SensorMockGenerator,
)


class TestSensorMockGenerator(unittest.TestCase):
    """测试传感器Mock数据生成器"""

    def setUp(self):
        """测试前准备"""
        self.generator = SensorMockGenerator(MockScenario.SUCCESSFUL_INTERACTION)

    def test_accelerometer_generation(self):
        """测试加速度计数据生成"""
        data = self.generator.generate_accelerometer_data()

        # 验证基本结构
        self.assertIn("sensor_type", data)
        self.assertIn("payload", data)
        self.assertIn("timestamp", data)
        self.assertEqual(data["sensor_type"], "accelerometer")

        # 验证数据有效性
        payload = data["payload"]
        self.assertIn("x", payload)
        self.assertIn("y", payload)
        self.assertIn("z", payload)

        # 验证数值合理性（地球重力约为9.8m/s²）
        self.assertGreater(payload["y"], 8.0)
        self.assertLess(payload["y"], 12.0)

    def test_gyroscope_generation(self):
        """测试陀螺仪数据生成"""
        data = self.generator.generate_gyroscope_data()

        self.assertEqual(data["sensor_type"], "gyroscope")
        payload = data["payload"]

        # 验证角度数据
        self.assertIn("alpha", payload)
        self.assertIn("beta", payload)
        self.assertIn("gamma", payload)

        # 验证角度范围
        self.assertGreaterEqual(payload["alpha"], 0)
        self.assertLessEqual(payload["alpha"], 360)

    def test_gps_generation(self):
        """测试GPS数据生成"""
        data = self.generator.generate_gps_data()

        self.assertEqual(data["sensor_type"], "gps")
        payload = data["payload"]

        # 验证GPS数据结构
        required_fields = ["latitude", "longitude", "altitude", "accuracy", "speed"]
        for field in required_fields:
            self.assertIn(field, payload)

        # 验证北京附近坐标
        self.assertGreater(payload["latitude"], 39.0)
        self.assertLess(payload["latitude"], 41.0)
        self.assertGreater(payload["longitude"], 115.0)
        self.assertLess(payload["longitude"], 117.0)

    def test_camera_generation(self):
        """测试摄像头数据生成"""
        data = self.generator.generate_camera_data()

        self.assertEqual(data["sensor_type"], "camera")
        payload = data["payload"]

        # 验证图像数据
        self.assertIn("image", payload)
        self.assertIn("width", payload)
        self.assertIn("height", payload)
        self.assertIn("detection_objects", payload)

        # 验证Base64格式
        self.assertTrue(payload["image"].startswith("data:image/"))

    def test_different_scenarios(self):
        """测试不同场景下的数据生成"""
        # 正常场景
        normal_gen = SensorMockGenerator(MockScenario.SUCCESSFUL_INTERACTION)
        normal_data = normal_gen.generate_accelerometer_data()
        self.assertEqual(normal_data["quality"], "high")

        # 传感器错误场景
        error_gen = SensorMockGenerator(MockScenario.SENSOR_ERROR)
        error_data = error_gen.generate_accelerometer_data()
        # 可能产生低质量数据或异常值
        self.assertIn(error_data["quality"], ["low", "medium", "high", "invalid"])


class TestInteractionMockHandler(unittest.TestCase):
    """测试交互Mock处理器"""

    def setUp(self):
        """测试前准备"""
        self.handler = InteractionMockHandler(MockScenario.SUCCESSFUL_INTERACTION)

    def test_gesture_handling(self):
        """测试手势处理"""
        gesture_data = {"type": "tap", "position": [1, 2, 3]}

        result = self.handler.handle_gesture(gesture_data)

        # 验证返回结构
        self.assertIn("success", result)
        self.assertIn("gesture_type", result)
        self.assertIn("response_time", result)
        self.assertIn("simulated_effects", result)

        self.assertEqual(result["gesture_type"], "tap")
        self.assertTrue(isinstance(result["response_time"], float))

    def test_voice_command_handling(self):
        """测试语音命令处理"""
        commands = ["开始实验", "停止实验", "重置", "增加重力"]

        for command in commands:
            result = self.handler.handle_voice_command(command)

            self.assertIn("success", result)
            self.assertIn("command", result)
            self.assertIn("response", result)
            self.assertEqual(result["command"], command)

    def test_scenario_variations(self):
        """测试不同场景的行为差异"""
        # 高成功率场景
        high_success_handler = InteractionMockHandler(
            MockScenario.SUCCESSFUL_INTERACTION
        )
        success_count = 0
        for _ in range(100):
            result = high_success_handler.handle_gesture({"type": "tap"})
            if result["success"]:
                success_count += 1
        self.assertGreater(success_count, 80)  # 期望80%以上成功率

        # 低成功率场景
        low_success_handler = InteractionMockHandler(MockScenario.SENSOR_ERROR)
        success_count = 0
        for _ in range(100):
            result = low_success_handler.handle_gesture({"type": "tap"})
            if result["success"]:
                success_count += 1
        self.assertLess(success_count, 50)  # 期望50%以下成功率


class TestPhysicsMockEngine(unittest.TestCase):
    """测试物理引擎Mock"""

    def setUp(self):
        """测试前准备"""
        self.engine = PhysicsMockEngine(MockScenario.SUCCESSFUL_INTERACTION)

    def test_object_initialization(self):
        """测试对象初始化"""
        self.engine.initialize_objects("virtual_lab")

        # 验证对象创建
        self.assertIn("ground", self.engine.objects)
        self.assertIn("ball_1", self.engine.objects)
        self.assertIn("ball_2", self.engine.objects)

        # 验证静态对象
        self.assertTrue(self.engine.objects["ground"]["static"])
        self.assertFalse(self.engine.objects["ball_1"]["static"])

    def test_physics_update(self):
        """测试物理更新"""
        self.engine.initialize_objects("virtual_lab")

        # 记录初始位置
        initial_y = self.engine.objects["ball_1"]["position"][1]

        # 执行几次物理更新
        for _ in range(60):  # 1秒的更新（60帧）
            self.engine.update_physics()

        # 验证重力作用效果
        final_y = self.engine.objects["ball_1"]["position"][1]
        self.assertLess(final_y, initial_y)  # 物体应该下降

    def test_collision_detection(self):
        """测试碰撞检测"""
        self.engine.initialize_objects("virtual_lab")

        # 将球放在地面下方
        self.engine.objects["ball_1"]["position"][1] = -1.0

        # 执行物理更新
        self.engine.update_physics()

        # 验证碰撞反弹（球应该回到地面上）
        self.assertGreaterEqual(self.engine.objects["ball_1"]["position"][1], 0)


class TestARVRMockOrchestrator(unittest.IsolatedAsyncioTestCase):
    """测试Mock服务编排器"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = Mock()
        self.orchestrator = ARVRMockOrchestrator(self.mock_db)

    async def test_session_lifecycle(self):
        """测试会话生命周期"""
        # 启动会话
        session_id = await self.orchestrator.start_mock_session(
            1, 123, MockScenario.SUCCESSFUL_INTERACTION
        )
        self.assertIsNotNone(session_id)
        self.assertIn(session_id, self.orchestrator.active_sessions)

        # 验证会话数据
        session_data = self.orchestrator.active_sessions[session_id]
        self.assertEqual(session_data["content_id"], 1)
        self.assertEqual(session_data["user_id"], 123)
        self.assertEqual(session_data["scenario"], MockScenario.SUCCESSFUL_INTERACTION)

        # 停止会话
        success = await self.orchestrator.stop_mock_session(session_id)
        self.assertTrue(success)
        self.assertNotIn(session_id, self.orchestrator.active_sessions)

    async def test_sensor_data_stream(self):
        """测试传感器数据流"""
        session_id = await self.orchestrator.start_mock_session(1, 123)

        # 获取传感器数据
        sensor_types = ["accelerometer", "gyroscope"]
        data_stream = await self.orchestrator.get_sensor_data_stream(
            session_id, sensor_types
        )

        self.assertEqual(len(data_stream), 2)
        self.assertEqual(data_stream[0]["sensor_type"], "accelerometer")
        self.assertEqual(data_stream[1]["sensor_type"], "gyroscope")

        await self.orchestrator.stop_mock_session(session_id)

    async def test_interaction_handling(self):
        """测试交互处理"""
        session_id = await self.orchestrator.start_mock_session(1, 123)

        # 处理手势交互
        gesture_result = await self.orchestrator.handle_interaction(
            session_id, "gesture", {"type": "tap", "position": [0, 0, 0]}
        )

        self.assertIn("success", gesture_result)
        self.assertIn("gesture_type", gesture_result)

        # 处理语音命令
        voice_result = await self.orchestrator.handle_interaction(
            session_id, "voice", {"command": "开始实验"}
        )

        self.assertIn("success", voice_result)
        self.assertIn("command", voice_result)

        await self.orchestrator.stop_mock_session(session_id)

    async def test_physics_state(self):
        """测试物理状态获取"""
        session_id = await self.orchestrator.start_mock_session(1, 123)

        physics_state = await self.orchestrator.get_physics_state(session_id)

        self.assertIn("objects", physics_state)
        self.assertIn("gravity", physics_state)
        self.assertIn("simulation_time", physics_state)

        await self.orchestrator.stop_mock_session(session_id)


class TestIntegration(unittest.IsolatedAsyncioTestCase):
    """集成测试"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = Mock()

    async def test_complete_workflow(self):
        """测试完整工作流程"""
        orchestrator = ARVRMockOrchestrator(self.mock_db)

        # 1. 启动会话
        session_id = await orchestrator.start_mock_session(
            1, 123, MockScenario.SUCCESSFUL_INTERACTION
        )

        # 2. 获取传感器数据
        sensor_data = await orchestrator.get_sensor_data_stream(
            session_id, ["accelerometer", "gyroscope"]
        )
        self.assertEqual(len(sensor_data), 2)

        # 3. 处理交互
        gesture_result = await orchestrator.handle_interaction(
            session_id, "gesture", {"type": "tap"}
        )
        self.assertTrue(gesture_result["success"])

        # 4. 获取物理状态
        physics_state = await orchestrator.get_physics_state(session_id)
        self.assertIn("objects", physics_state)

        # 5. 停止会话
        await orchestrator.stop_mock_session(session_id)

    async def test_multiple_sessions(self):
        """测试多会话并发"""
        orchestrator = ARVRMockOrchestrator(self.mock_db)

        # 创建多个会话
        session_ids = []
        for i in range(3):
            session_id = await orchestrator.start_mock_session(i + 1, 100 + i)
            session_ids.append(session_id)

        # 验证所有会话都存在
        self.assertEqual(len(orchestrator.active_sessions), 3)

        # 为每个会话获取数据
        for session_id in session_ids:
            data = await orchestrator.get_sensor_data_stream(
                session_id, ["accelerometer"]
            )
            self.assertEqual(len(data), 1)

        # 清理会话
        for session_id in session_ids:
            await orchestrator.stop_mock_session(session_id)

        self.assertEqual(len(orchestrator.active_sessions), 0)


class TestPerformance(unittest.IsolatedAsyncioTestCase):
    """性能测试"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = Mock()

    async def test_high_frequency_operations(self):
        """测试高频操作性能"""
        orchestrator = ARVRMockOrchestrator(self.mock_db)
        session_id = await orchestrator.start_mock_session(1, 123)

        import time

        start_time = time.time()

        # 执行100次高频操作
        for i in range(100):
            await orchestrator.get_sensor_data_stream(session_id, ["accelerometer"])
            await orchestrator.handle_interaction(
                session_id, "gesture", {"type": "tap"}
            )

        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 100

        print(f"平均操作时间: {avg_time*1000:.2f}ms")
        print(f"吞吐量: {100/total_time:.2f} ops/sec")

        # 性能断言（应该在合理范围内）
        self.assertLess(avg_time, 0.1)  # 平均每次操作应该小于100ms

        await orchestrator.stop_mock_session(session_id)


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestSensorMockGenerator))
    test_suite.addTest(unittest.makeSuite(TestInteractionMockHandler))
    test_suite.addTest(unittest.makeSuite(TestPhysicsMockEngine))
    test_suite.addTest(unittest.makeSuite(TestARVRMockOrchestrator))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    test_suite.addTest(unittest.makeSuite(TestPerformance))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return result


if __name__ == "__main__":
    # 运行测试
    test_result = run_all_tests()

    # 输出测试摘要
    print("\n" + "=" * 50)
    print("测试结果摘要:")
    print(f"运行测试数: {test_result.testsRun}")
    print(f"失败数: {len(test_result.failures)}")
    print(f"错误数: {len(test_result.errors)}")
    print(
        f"成功率: {((test_result.testsRun - len(test_result.failures) - len(test_result.errors)) / test_result.testsRun * 100):.1f}%"
    )

    # 如果有失败或错误，输出详细信息
    if test_result.failures:
        print("\n失败的测试:")
        for test, traceback in test_result.failures:
            print(f"- {test}: {traceback}")

    if test_result.errors:
        print("\n错误的测试:")
        for test, traceback in test_result.errors:
            print(f"- {test}: {traceback}")
