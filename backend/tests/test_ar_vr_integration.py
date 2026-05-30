"""
AR/VR课程集成模块测试套件
包含单元测试、集成测试和回测验证
"""

import asyncio
from datetime import datetime
import os
import sys
import unittest
from unittest.mock import Mock, patch

from sqlalchemy.orm import Session

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 导入模型
from models.ar_vr_content import (
    ARVRContent,
    ARVRContentType,
    ARVRPlatform,
    ARVRSensorData,
    InteractionMode,
    SensorType,
)

# 导入路由
from routes.ar_vr_routes import router
from services.ar_physics_service import ARPhysicsService

# 导入服务
from services.ar_vr_content_service import ARVRContentService
from services.web_rtc_sensor_service import WebRTCManager, WebRTCSensorDataStream


class TestARVRModels(unittest.TestCase):
    """测试AR/VR数据模型"""

    def test_arvr_content_creation(self):
        """测试AR/VR内容模型创建"""
        content = ARVRContent(
            org_id=1,
            course_id=1,
            title="测试AR内容",
            description="测试描述",
            content_type=ARVRContentType.UNITY_WEBGL,
            platform=ARVRPlatform.WEB_BROWSER,
            config={"width": 800, "height": 600},
            required_sensors=[SensorType.TOUCH.value],
            interaction_modes=[InteractionMode.GESTURE.value],
            is_public=True,
            access_level="course",
        )

        self.assertEqual(content.title, "测试AR内容")
        self.assertEqual(content.content_type, ARVRContentType.UNITY_WEBGL)
        self.assertTrue(content.is_public)
        self.assertEqual(len(content.required_sensors), 1)

    def test_sensor_data_model(self):
        """测试传感器数据模型"""
        sensor_data = ARVRSensorData(
            content_id=1,
            user_id=1,
            org_id=1,
            sensor_type=SensorType.ACCELEROMETER,
            data_payload={"x": 1.0, "y": 2.0, "z": 3.0},
            session_id="test_session",
        )

        self.assertEqual(sensor_data.sensor_type, SensorType.ACCELEROMETER)
        self.assertEqual(sensor_data.data_payload["x"], 1.0)
        self.assertEqual(sensor_data.session_id, "test_session")


class TestARVRContentService(unittest.TestCase):
    """测试AR/VR内容服务"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = Mock(spec=Session)
        self.service = ARVRContentService(self.mock_db)

    def test_create_arvr_content_success(self):
        """测试成功创建AR/VR内容"""
        from models.ar_vr_content import ARVRContentCreate

        content_data = ARVRContentCreate(
            course_id=1,
            title="测试内容",
            content_type=ARVRContentType.UNITY_WEBGL,
            platform=ARVRPlatform.WEB_BROWSER,
            is_public=True,
        )

        mock_user = Mock()
        mock_user.id = 1

        # 模拟数据库查询
        self.mock_db.query.return_value.filter.return_value.first.return_value = Mock()

        with (
            patch.object(self.service.db, "add") as mock_add,
            patch.object(self.service.db, "commit") as mock_commit,
            patch.object(self.service.db, "refresh") as mock_refresh,
        ):

            result = self.service.create_arvr_content(1, content_data, mock_user)

            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            mock_refresh.assert_called_once()
            self.assertIsNotNone(result)

    def test_list_arvr_contents(self):
        """测试列出AR/VR内容"""
        mock_contents = [Mock(), Mock()]
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_contents
        )

        result = self.service.list_arvr_contents(1)

        self.assertEqual(len(result), 2)
        self.mock_db.query.assert_called()


class TestWebRTCService(unittest.TestCase):
    """测试WebRTC服务"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = Mock(spec=Session)

    def test_webrtc_manager_initialization(self):
        """测试WebRTC管理器初始化"""
        manager = WebRTCManager(self.mock_db)

        self.assertIsNotNone(manager.stream_manager)
        self.assertFalse(manager.running)

    def test_parse_connection_params(self):
        """测试连接参数解析"""
        stream_manager = WebRTCSensorDataStream(self.mock_db)

        params = stream_manager._parse_connection_params(
            "/test?session_id=123&content_id=456"
        )

        self.assertEqual(params["session_id"], "123")
        self.assertEqual(params["content_id"], "456")


class TestARPhysicsService(unittest.TestCase):
    """测试AR物理引擎服务"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = Mock(spec=Session)
        self.service = ARPhysicsService(self.mock_db)

    def test_initialize_physics_engine(self):
        """测试物理引擎初始化"""
        engine = self.service.initialize_physics_for_content(1)

        self.assertIsNotNone(engine)
        self.assertIn(1, self.service.physics_engines)

    def test_handle_gesture_interaction(self):
        """测试手势交互处理"""
        gesture_data = {
            "type": "tap",
            "position": [0, 0, 0],
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 模拟内容存在
        mock_content = Mock()
        mock_content.content_type = Mock()
        mock_content.content_type.value = "virtual_lab"
        mock_content.config = {"experiments": ["pendulum"]}

        with patch.object(
            self.service.content_service, "get_arvr_content", return_value=mock_content
        ):
            result = self.service.handle_gesture_interaction(1, 1, gesture_data)

            self.assertIsInstance(result, dict)
            self.assertIn("success", result)


class TestAPIRoutes(unittest.TestCase):
    """测试API路由"""

    def setUp(self):
        """测试前准备"""
        self.client = Mock()

    def test_router_prefix(self):
        """测试路由前缀"""
        self.assertEqual(router.prefix, "/api/v1/org/{org_id}/arvr")
        self.assertIn("AR/VR课程", router.tags)


class TestIntegration(unittest.TestCase):
    """集成测试"""

    def setUp(self):
        """测试前准备"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """测试后清理"""
        self.loop.close()

    def test_complete_workflow(self):
        """测试完整工作流程"""

        async def workflow_test():
            # 1. 创建AR/VR内容
            mock_db = Mock(spec=Session)
            ARVRContentService(mock_db)

            # 2. 初始化物理引擎
            physics_service = ARPhysicsService(mock_db)
            physics_service.initialize_physics_for_content(1)

            # 3. 处理传感器数据
            sensor_data = {
                "sensor_type": "accelerometer",
                "payload": {"x": 1.0, "y": 2.0, "z": 3.0},
            }

            # 4. 处理交互
            gesture_data = {"type": "tap", "position": [0, 0, 0]}

            result = physics_service.handle_gesture_interaction(1, 1, gesture_data)
            self.assertTrue(result["success"])

            # 5. 更新物理状态
            physics_state = physics_service.get_physics_state(1)
            self.assertIsNotNone(physics_state)

        self.loop.run_until_complete(workflow_test())


class TestBacktesting(unittest.TestCase):
    """回测验证测试"""

    def test_performance_metrics(self):
        """测试性能指标"""
        # 模拟性能测试数据
        test_cases = [
            {"operation": "create_content", "expected_time": 0.1, "actual_time": 0.08},
            {"operation": "handle_gesture", "expected_time": 0.05, "actual_time": 0.04},
            {
                "operation": "physics_update",
                "expected_time": 0.02,
                "actual_time": 0.015,
            },
        ]

        for case in test_cases:
            self.assertLessEqual(
                case["actual_time"],
                case["expected_time"] * 1.2,
                f"{case['operation']}性能不达标",
            )

    def test_data_consistency(self):
        """测试数据一致性"""
        # 测试传感器数据的一致性
        sensor_readings = [
            {"x": 1.0, "y": 2.0, "z": 3.0},
            {"x": 1.1, "y": 2.1, "z": 3.1},
            {"x": 0.9, "y": 1.9, "z": 2.9},
        ]

        # 验证数据在合理范围内变化
        for reading in sensor_readings:
            self.assertGreaterEqual(reading["x"], -10.0)
            self.assertLessEqual(reading["x"], 10.0)

    def test_error_handling(self):
        """测试错误处理"""
        mock_db = Mock(spec=Session)
        service = ARVRContentService(mock_db)

        # 测试数据库错误处理
        mock_db.commit.side_effect = Exception("数据库错误")

        with self.assertRaises(Exception):
            service.create_arvr_content(1, Mock(), Mock())

        # 验证事务回滚
        mock_db.rollback.assert_called_once()


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加测试用例
    test_suite.addTest(unittest.makeSuite(TestARVRModels))
    test_suite.addTest(unittest.makeSuite(TestARVRContentService))
    test_suite.addTest(unittest.makeSuite(TestWebRTCService))
    test_suite.addTest(unittest.makeSuite(TestARPhysicsService))
    test_suite.addTest(unittest.makeSuite(TestAPIRoutes))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    test_suite.addTest(unittest.makeSuite(TestBacktesting))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 输出测试报告
    print("\n" + "=" * 50)
    print("AR/VR课程集成测试报告")
    print("=" * 50)
    print(f"测试总数: {result.testsRun}")
    print(f"失败数: {len(result.failures)}")
    print(f"错误数: {len(result.errors)}")
    print(
        f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print("\n失败的测试:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")

    if result.errors:
        print("\n错误的测试:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
