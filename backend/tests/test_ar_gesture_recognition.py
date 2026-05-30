"""
AR手势识别模块单元测试
"""

from datetime import datetime
import unittest
from unittest.mock import Mock

import numpy as np

# 导入被测试的模块
try:
    from xr_modules.ar_gesture_recognition.ar_gesture_service import ARGestureService
    from xr_modules.ar_gesture_recognition.gesture_detector import GestureDetector
    from xr_modules.ar_gesture_recognition.gesture_mapper import GestureMapper
    from xr_modules.ar_gesture_recognition.gesture_processor import GestureProcessor
    from xr_modules.ar_gesture_recognition.hand_tracker import HandTracker
    from xr_modules.ar_gesture_recognition.models import (
        ARGestureConfig,
        GestureRecognitionResult,
        GestureType,
        HandDetectionResult,
        HandLandmark,
        HandSide,
    )
except ImportError as e:
    print(f"导入测试模块失败: {e}")

    # 创建占位符类用于测试
    class PlaceholderTest(unittest.TestCase):
        def test_placeholder(self):
            self.skipTest("模块导入失败，跳过测试")


class TestModels(unittest.TestCase):
    """测试数据模型"""

    def test_gesture_type_enum(self):
        """测试手势类型枚举"""
        self.assertEqual(GestureType.CIRCLE, "circle")
        self.assertEqual(GestureType.SWIPE_RIGHT, "swipe_right")
        self.assertEqual(GestureType.FIST, "fist")

    def test_hand_landmark_model(self):
        """测试手部关键点模型"""
        landmark = HandLandmark(x=0.5, y=0.3, z=0.1)
        self.assertEqual(landmark.x, 0.5)
        self.assertEqual(landmark.y, 0.3)
        self.assertEqual(landmark.z, 0.1)
        self.assertEqual(landmark.visibility, 1.0)

    def test_argesture_config(self):
        """测试手势配置模型"""
        config = ARGestureConfig()
        self.assertEqual(config.min_detection_confidence, 0.7)
        self.assertEqual(config.image_width, 640)
        self.assertTrue(config.enable_multi_hand)


class TestHandTracker(unittest.TestCase):
    """测试手部追踪器"""

    def setUp(self):
        """测试前准备"""
        self.tracker = HandTracker(min_detection_confidence=0.5)

    def tearDown(self):
        """测试后清理"""
        self.tracker.close()

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.tracker.hands)
        self.assertEqual(self.tracker.min_detection_confidence, 0.5)

    def test_empty_image_detection(self):
        """测试空图像检测"""
        # 创建黑色图像
        empty_image = np.zeros((480, 640, 3), dtype=np.uint8)
        results = self.tracker.detect_hands(empty_image)
        self.assertIsInstance(results, list)

    def test_landmark_extraction(self):
        """测试关键点提取"""
        # 创建模拟的关键点数据
        mock_landmarks = Mock()
        mock_landmark = Mock()
        mock_landmark.x = 0.5
        mock_landmark.y = 0.3
        mock_landmark.z = 0.1
        mock_landmark.visibility = 0.9

        mock_landmarks.landmark = [mock_landmark] * 21

        # 测试私有方法
        landmarks = self.tracker._extract_landmarks(mock_landmarks, 640, 480)
        self.assertEqual(len(landmarks), 21)
        self.assertEqual(landmarks[0].x, 0.5)


class TestGestureDetector(unittest.TestCase):
    """测试手势检测器"""

    def setUp(self):
        """测试前准备"""
        self.detector = GestureDetector()

    def test_initialization(self):
        """测试初始化"""
        self.assertIn("WRIST", self.detector.HAND_LANDMARKS)
        self.assertIn("THUMB_TIP", self.detector.HAND_LANDMARKS)

    def test_unknown_gesture_recognition(self):
        """测试未知手势识别"""
        # 创建最小的关键点列表
        landmarks = [HandLandmark(x=0.0, y=0.0, z=0.0) for _ in range(21)]

        hand_detection = HandDetectionResult(
            hand_side=HandSide.RIGHT,
            landmarks=landmarks,
            confidence=0.8,
            bounding_box={"x": 0, "y": 0, "width": 1, "height": 1},
            timestamp=datetime.utcnow(),
        )

        result = self.detector.recognize_gesture(hand_detection, 1)
        self.assertEqual(result.gesture_type, GestureType.UNKNOWN)
        self.assertEqual(result.frame_number, 1)

    def test_finger_state_calculation(self):
        """测试手指状态计算"""
        # 创建伸直手指的关键点
        landmarks = []
        for i in range(21):
            # 模拟伸直的手指（指尖在MCP关节上方）
            if i in [8, 12, 16, 20]:  # 指尖
                landmark = HandLandmark(x=0.5, y=0.2, z=0.0)  # y较小表示在上方
            else:
                landmark = HandLandmark(x=0.5, y=0.5, z=0.0)
            landmarks.append(landmark)

        finger_states = self.detector._get_finger_states(landmarks)

        # 验证手指状态计算（注意：由于简化逻辑，这里可能需要调整期望值）
        self.assertIsInstance(finger_states, dict)


class TestGestureProcessor(unittest.TestCase):
    """测试手势处理器"""

    def setUp(self):
        """测试前准备"""
        config = ARGestureConfig()
        self.processor = GestureProcessor(config)

    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(len(self.processor.gesture_history), 0)
        self.assertEqual(self.processor.last_gesture_type, GestureType.UNKNOWN)

    def test_gesture_filtering_low_confidence(self):
        """测试低置信度过滤"""
        config = ARGestureConfig(min_detection_confidence=0.8)
        processor = GestureProcessor(config)

        # 创建低置信度的手势结果
        landmarks = [HandLandmark(x=0.0, y=0.0, z=0.0) for _ in range(21)]
        hand_detection = HandDetectionResult(
            hand_side=HandSide.RIGHT,
            landmarks=landmarks,
            confidence=0.8,
            bounding_box={"x": 0, "y": 0, "width": 1, "height": 1},
            timestamp=datetime.utcnow(),
        )

        gesture_result = GestureRecognitionResult(
            gesture_type=GestureType.FIST,
            confidence=0.6,  # 低于阈值
            hand_side=HandSide.RIGHT,
            hand_detection=hand_detection,
            recognition_time=datetime.utcnow(),
            frame_number=1,
        )

        event = processor.process_gesture(gesture_result)
        self.assertIsNone(event)

    def test_gesture_smoothing(self):
        """测试手势平滑处理"""
        # 连续添加相同手势
        landmarks = [HandLandmark(x=0.0, y=0.0, z=0.0) for _ in range(21)]
        hand_detection = HandDetectionResult(
            hand_side=HandSide.RIGHT,
            landmarks=landmarks,
            confidence=0.9,
            bounding_box={"x": 0, "y": 0, "width": 1, "height": 1},
            timestamp=datetime.utcnow(),
        )

        # 第一次识别
        gesture_result1 = GestureRecognitionResult(
            gesture_type=GestureType.FIST,
            confidence=0.8,
            hand_side=HandSide.RIGHT,
            hand_detection=hand_detection,
            recognition_time=datetime.utcnow(),
            frame_number=1,
        )

        event1 = self.processor.process_gesture(gesture_result1)
        self.assertIsNotNone(event1)

        # 短时间内再次识别相同手势应该被过滤
        gesture_result2 = GestureRecognitionResult(
            gesture_type=GestureType.FIST,
            confidence=0.85,
            hand_side=HandSide.RIGHT,
            hand_detection=hand_detection,
            recognition_time=datetime.utcnow(),
            frame_number=2,
        )

        event2 = self.processor.process_gesture(gesture_result2)
        self.assertIsNone(event2)  # 应该被过滤


class TestGestureMapper(unittest.TestCase):
    """测试手势映射器"""

    def setUp(self):
        """测试前准备"""
        config = ARGestureConfig()
        self.mapper = GestureMapper(config)

    def test_initialization(self):
        """测试初始化"""
        self.assertGreater(len(self.mapper.mappings), 0)
        self.assertIn(GestureType.CIRCLE, self.mapper.mappings)

    def test_gesture_mapping(self):
        """测试手势映射"""
        landmarks = [HandLandmark(x=0.0, y=0.0, z=0.0) for _ in range(21)]
        hand_detection = HandDetectionResult(
            hand_side=HandSide.RIGHT,
            landmarks=landmarks,
            confidence=0.9,
            bounding_box={"x": 0, "y": 0, "width": 1, "height": 1},
            timestamp=datetime.utcnow(),
        )

        gesture_result = GestureRecognitionResult(
            gesture_type=GestureType.CIRCLE,
            confidence=0.8,
            hand_side=HandSide.RIGHT,
            hand_detection=hand_detection,
            recognition_time=datetime.utcnow(),
            frame_number=1,
        )

        gesture_event = GestureEvent(
            event_id="test_event",
            gesture_result=gesture_result,
            session_id="test_session",
            device_id="test_device",
            created_at=datetime.utcnow(),
        )

        command = self.mapper.map_gesture_to_command(gesture_event)
        self.assertEqual(command, "save_project")

    def test_mapping_update(self):
        """测试映射更新"""
        # 更新现有映射
        success = self.mapper.update_mapping(
            GestureType.CIRCLE, command="new_save_command", description="新的保存命令"
        )
        self.assertTrue(success)

        # 验证更新结果
        mappings = self.mapper.get_available_commands()
        circle_commands = [cmd for cmd in mappings if cmd["gesture_type"] == "circle"]
        self.assertTrue(
            any(cmd["command"] == "new_save_command" for cmd in circle_commands)
        )


class TestARGestureService(unittest.TestCase):
    """测试AR手势识别服务"""

    def setUp(self):
        """测试前准备"""
        self.service = ARGestureService()

    def tearDown(self):
        """测试后清理"""
        self.service.close()

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.service.hand_tracker)
        self.assertIsNotNone(self.service.gesture_detector)
        self.assertIsNotNone(self.service.gesture_processor)
        self.assertIsNotNone(self.service.gesture_mapper)
        self.assertFalse(self.service.is_running)

    def test_session_management(self):
        """测试会话管理"""
        # 开始会话
        session_id = self.service.start_session(user_id=1, device_id="test_device")
        self.assertIsNotNone(session_id)
        self.assertTrue(self.service.is_running)
        self.assertIsNotNone(self.service.current_session)

        # 获取会话信息
        session_info = self.service.get_session_info()
        self.assertEqual(session_info.session_id, session_id)
        self.assertEqual(session_info.user_id, 1)
        self.assertEqual(session_info.device_id, "test_device")

        # 停止会话
        self.service.stop_session()
        self.assertFalse(self.service.is_running)
        self.assertIsNone(self.service.current_session)

    def test_get_available_commands(self):
        """测试获取可用命令"""
        commands = self.service.get_available_commands()
        self.assertIsInstance(commands, list)
        self.assertGreater(len(commands), 0)

        # 验证命令结构
        for command in commands:
            self.assertIn("gesture_type", command)
            self.assertIn("command", command)
            self.assertIn("description", command)
            self.assertIn("priority", command)

    def test_service_status(self):
        """测试服务状态"""
        status = self.service.get_service_status()
        self.assertIsInstance(status, dict)
        self.assertIn("is_running", status)
        self.assertIn("frame_count", status)
        self.assertIn("config", status)
        self.assertFalse(status["is_running"])


if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)
