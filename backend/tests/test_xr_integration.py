"""
XR远程教学系统集成测试
验证所有模块的协同工作能力和性能表现
"""

import logging
import threading
import time
import unittest

# 设置测试日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # 导入XR模块
    # 导入API路由
    from routes.xr_gesture_routes import router as gesture_router
    from routes.xr_vr_editor_routes import router as editor_router
    from routes.xr_whiteboard_routes import router as whiteboard_router
    from xr_modules.ar_gesture_recognition.ar_gesture_service import (
        create_default_gesture_service,
    )
    from xr_modules.ar_gesture_recognition.models import ARGestureConfig, GestureEvent
    from xr_modules.vr_3d_editor.models import CodeLanguage, VREditorConfig
    from xr_modules.vr_3d_editor.vr_editor_core import VREditorCore
    from xr_modules.whiteboard_collab.models import WhiteboardConfig
    from xr_modules.whiteboard_collab.whiteboard_core import WhiteboardCore

except ImportError as e:
    logger.error(f"模块导入失败: {e}")

    # 创建占位符测试类
    class IntegrationTestPlaceholder(unittest.TestCase):
        def test_placeholder(self):
            self.skipTest("模块导入失败，跳过集成测试")


class TestModuleIntegration(unittest.TestCase):
    """模块集成测试"""

    def setUp(self):
        """测试前准备"""
        logger.info("开始集成测试准备")

    def tearDown(self):
        """测试后清理"""
        logger.info("集成测试清理完成")

    def test_gesture_to_editor_integration(self):
        """测试手势识别与VR编辑器集成"""
        logger.info("测试手势识别与VR编辑器集成")

        # 初始化手势服务
        gesture_config = ARGestureConfig(
            min_detection_confidence=0.7,
            gesture_timeout=1.0,
            continuous_gesture_threshold=2,
        )
        gesture_service = create_default_gesture_service()
        gesture_service.config = gesture_config

        # 初始化VR编辑器
        editor_config = VREditorConfig(
            theme="dark", language=CodeLanguage.PYTHON, interaction_mode="hand_tracking"
        )
        editor = VREditorCore(editor_config)
        session_id = editor.initialize_session(user_id=1, device_id="test_device")

        # 设置集成回调
        def gesture_callback(event: GestureEvent, command: str):
            logger.info(f"手势事件: {event.gesture_result.gesture_type} -> {command}")
            # 根据手势命令执行编辑器操作
            if command == "save_project":
                editor.save_session()
            elif command == "next_step":
                # 模拟下一步操作
                pass

            elif command == "zoom_in":
                editor.set_zoom_level(editor.session.state.zoom_level * 1.2)

        gesture_service.set_gesture_callback(gesture_callback)

        # 启动会话
        gesture_session = gesture_service.start_session(
            user_id=1, device_id="test_device"
        )

        # 模拟手势识别过程
        gesture_service.process_frame(None)  # 处理空帧进行初始化

        # 验证集成状态
        self.assertIsNotNone(gesture_service.current_session)
        self.assertIsNotNone(editor.session)
        self.assertEqual(
            gesture_service.current_session.user_id, editor.session.user_id
        )

        # 清理
        gesture_service.stop_session()
        editor.close_session()

        logger.info("手势与编辑器集成测试完成")

    def test_editor_to_whiteboard_integration(self):
        """测试VR编辑器与白板协作集成"""
        logger.info("测试VR编辑器与白板协作集成")

        # 初始化VR编辑器
        editor = VREditorCore()
        editor_session = editor.initialize_session(user_id=1, device_id="test_device")

        # 初始化白板
        whiteboard_config = WhiteboardConfig(
            canvas_width=1920, canvas_height=1080, real_time_sync=True
        )
        whiteboard = WhiteboardCore(whiteboard_config)
        whiteboard_session = whiteboard.create_session(
            owner_id=1, board_name="测试白板"
        )

        # 创建测试文件
        test_file_id = editor.open_file(
            "test.py", "print('Hello XR World!')", CodeLanguage.PYTHON
        )

        # 模拟代码拖拽到白板的操作
        active_file = editor.get_active_file()
        if active_file:
            # 将代码内容添加到白板作为文本元素
            text_id = whiteboard.add_text(
                x=100, y=100, content=active_file.content, user_id=1
            )

            # 验证文本已添加
            elements = whiteboard.get_elements()
            text_elements = [e for e in elements if e.element_type == "text"]
            self.assertGreater(len(text_elements), 0)

            logger.info(f"代码已从编辑器传输到白板: {text_id}")

        # 清理
        editor.close_session()
        whiteboard.close_session()

        logger.info("编辑器与白板集成测试完成")

    def test_full_system_workflow(self):
        """测试完整系统工作流程"""
        logger.info("测试完整XR系统工作流程")

        # 1. 初始化所有组件
        gesture_service = create_default_gesture_service()
        editor = VREditorCore()
        whiteboard = WhiteboardCore()

        # 2. 启动会话
        user_id = 1
        device_id = "xr_device_001"

        gesture_service.start_session(user_id, device_id)
        editor.initialize_session(user_id, device_id)
        whiteboard.create_session(user_id, "XR协作空间")

        # 3. 验证会话同步
        self.assertEqual(
            gesture_service.current_session.session_id, editor.session.session_id
        )

        # 4. 模拟协作场景
        # 在编辑器中创建代码
        code_file_id = editor.open_file(
            "main.py", "def hello():\n    print('XR Hello')\n", CodeLanguage.PYTHON
        )

        # 通过手势保存代码
        gesture_service.process_frame(None)  # 触发处理

        # 将代码分享到白板
        active_file = editor.get_active_file()
        if active_file:
            whiteboard.add_text(
                200,
                200,
                f"代码文件: {active_file.name}\n{active_file.content}",
                user_id,
            )

        # 5. 验证数据一致性
        editor_elements = editor.session.opened_files
        whiteboard_elements = whiteboard.get_elements()

        self.assertGreater(len(editor_elements), 0)
        self.assertGreater(len(whiteboard_elements), 0)

        # 6. 清理资源
        gesture_service.stop_session()
        editor.close_session()
        whiteboard.close_session()

        logger.info("完整系统工作流程测试完成")

    def test_concurrent_access(self):
        """测试并发访问和协作功能"""
        logger.info("测试并发访问和协作功能")

        # 初始化共享白板
        whiteboard = WhiteboardCore()
        session_id = whiteboard.create_session(owner_id=1, board_name="协作白板")

        # 模拟多个用户的并发操作
        def user_operation(user_id: int, operation_type: str):
            """模拟用户操作"""
            if operation_type == "add_stroke":
                stroke_id = whiteboard.start_stroke(
                    100 + user_id * 50, 100 + user_id * 30, 1.0, user_id=user_id
                )
                whiteboard.add_stroke_point(150 + user_id * 50, 150 + user_id * 30, 1.0)
                whiteboard.end_stroke()
                logger.info(f"用户{user_id}添加笔画: {stroke_id}")

            elif operation_type == "add_text":
                text_id = whiteboard.add_text(
                    300 + user_id * 100,
                    100 + user_id * 50,
                    f"用户{user_id}的文本",
                    user_id,
                )
                logger.info(f"用户{user_id}添加文本: {text_id}")

        # 创建多个线程模拟并发用户
        threads = []
        for i in range(3):  # 3个并发用户
            thread = threading.Thread(target=user_operation, args=(i + 1, "add_stroke"))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join(timeout=5.0)

        # 验证所有操作都成功执行
        elements = whiteboard.get_elements()
        strokes = [e for e in elements if e.element_type == "stroke"]

        # 应该有3个用户的笔画
        self.assertEqual(len(strokes), 3)

        # 验证每个用户都有自己的元素
        user_ids = set(e.user_id for e in strokes if e.user_id)
        self.assertEqual(len(user_ids), 3)

        whiteboard.close_session()
        logger.info("并发访问测试完成")

    def test_error_handling(self):
        """测试错误处理和异常恢复"""
        logger.info("测试错误处理和异常恢复")

        # 测试无效会话处理
        editor = VREditorCore()

        # 尝试在未初始化的会话上操作
        with self.assertRaises(RuntimeError):
            editor.open_file("test.py", "print('test')")

        # 测试文件操作错误处理
        session_id = editor.initialize_session(user_id=1)
        invalid_file_id = "invalid_file_id"

        # 尝试更新不存在的文件
        result = editor.update_file_content(invalid_file_id, "new content")
        self.assertFalse(result)

        # 测试资源清理
        editor.close_session()
        self.assertIsNone(editor.session)

        logger.info("错误处理测试完成")


class TestPerformanceIntegration(unittest.TestCase):
    """性能集成测试"""

    def test_response_time(self):
        """测试系统响应时间"""
        logger.info("测试系统响应时间")

        # 初始化组件
        gesture_service = create_default_gesture_service()
        editor = VREditorCore()

        gesture_service.start_session(user_id=1)
        editor.initialize_session(user_id=1)

        # 测试手势处理响应时间
        start_time = time.time()
        gesture_service.process_frame(None)
        gesture_time = time.time() - start_time

        # 测试编辑器操作响应时间
        start_time = time.time()
        editor.open_file("test.py", "print('test')")
        editor_time = time.time() - start_time

        # 验证响应时间在合理范围内
        self.assertLess(gesture_time, 0.1)  # 手势处理应在100ms内
        self.assertLess(editor_time, 0.05)  # 编辑器操作应在50ms内

        logger.info(f"手势处理时间: {gesture_time:.4f}s")
        logger.info(f"编辑器操作时间: {editor_time:.4f}s")

        # 清理
        gesture_service.stop_session()
        editor.close_session()

    def test_memory_usage(self):
        """测试内存使用情况"""
        logger.info("测试内存使用情况")

        import os

        import psutil

        # 获取初始内存使用
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 创建多个会话实例
        editors = []
        for i in range(10):
            editor = VREditorCore()
            editor.initialize_session(user_id=i)
            editors.append(editor)

        # 测量内存增长
        current_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = current_memory - initial_memory

        logger.info(f"初始内存: {initial_memory:.2f}MB")
        logger.info(f"当前内存: {current_memory:.2f}MB")
        logger.info(f"内存增长: {memory_growth:.2f}MB")

        # 验证内存增长在合理范围内（每个实例不超过10MB）
        self.assertLess(memory_growth, 100)  # 10个实例不超过100MB

        # 清理
        for editor in editors:
            editor.close_session()

        final_memory = process.memory_info().rss / 1024 / 1024
        logger.info(f"清理后内存: {final_memory:.2f}MB")


class TestAPIIntegration(unittest.TestCase):
    """API集成测试"""

    def test_route_registration(self):
        """测试API路由注册"""
        logger.info("测试API路由注册")

        # 验证所有XR路由都已正确导入
        self.assertIsNotNone(gesture_router)
        self.assertIsNotNone(editor_router)
        self.assertIsNotNone(whiteboard_router)

        # 检查路由前缀
        self.assertTrue(gesture_router.prefix.startswith("/api/v1/xr"))
        self.assertTrue(editor_router.prefix.startswith("/api/v1/xr"))
        self.assertTrue(whiteboard_router.prefix.startswith("/api/v1/xr"))

        logger.info("API路由注册测试完成")

    def test_cross_module_communication(self):
        """测试跨模块通信"""
        logger.info("测试跨模块通信")

        # 模拟通过API进行模块间通信的场景
        # 这里可以测试WebSocket连接、事件广播等功能

        logger.info("跨模块通信测试完成")


if __name__ == "__main__":
    # 创建测试套件
    suite = unittest.TestSuite()

    # 添加测试用例
    suite.addTest(unittest.makeSuite(TestModuleIntegration))
    suite.addTest(unittest.makeSuite(TestPerformanceIntegration))
    suite.addTest(unittest.makeSuite(TestAPIIntegration))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 输出测试摘要
    logger.info("=" * 50)
    logger.info("集成测试摘要:")
    logger.info(f"测试总数: {result.testsRun}")
    logger.info(f"失败数量: {len(result.failures)}")
    logger.info(f"错误数量: {len(result.errors)}")
    logger.info(f"跳过数量: {len(result.skipped)}")
    logger.info("=" * 50)

    if result.wasSuccessful():
        logger.info("🎉 所有集成测试通过!")
    else:
        logger.error("❌ 部分集成测试失败!")
