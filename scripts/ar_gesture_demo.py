"""
AR手势识别系统测试和演示脚本
验证手势识别功能的完整性和性能
"""

import cv2
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, List

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from xr_modules.ar_gesture_recognition.ar_gesture_service import create_default_gesture_service
    from xr_modules.ar_gesture_recognition.models import GestureEvent, ARGestureConfig
except ImportError as e:
    logger.error(f"导入模块失败: {e}")
    logger.info("请确保在正确的环境中运行此脚本")
    exit(1)


class ARGesturDemo:
    """AR手势识别演示类"""
    
    def __init__(self):
        self.service = None
        self.cap = None
        self.running = False
        
    def initialize_camera(self, camera_index: int = 0) -> bool:
        """初始化摄像头"""
        try:
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                logger.error("无法打开摄像头")
                return False
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            logger.info("摄像头初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"摄像头初始化失败: {e}")
            return False
    
    def initialize_service(self, config: ARGestureConfig = None) -> bool:
        """初始化手势识别服务"""
        try:
            self.service = create_default_gesture_service()
            if config:
                self.service.config = config
            
            # 设置回调函数
            self.service.set_gesture_callback(self.gesture_callback)
            self.service.set_frame_callback(self.frame_callback)
            
            logger.info("手势识别服务初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"服务初始化失败: {e}")
            return False
    
    def gesture_callback(self, event: GestureEvent, command: str):
        """手势识别回调函数"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 手势识别: {event.gesture_result.gesture_type} "
              f"(置信度: {event.gesture_result.confidence:.2f}) -> {command}")
        
        if command:
            self.execute_command(command)
    
    def frame_callback(self, frame):
        """帧处理回调函数"""
        # 这里可以添加额外的帧处理逻辑
        pass
    
    def execute_command(self, command: str):
        """执行识别到的命令"""
        command_actions = {
            "save_project": lambda: print("💾 执行保存项目操作"),
            "next_step": lambda: print("⏭️  执行下一步操作"),
            "zoom_in": lambda: print("🔍 执行放大操作"),
            "confirm_action": lambda: print("✅ 执行确认操作"),
            "cancel_action": lambda: print("❌ 执行取消操作"),
            "continue_process": lambda: print("▶️  执行继续操作"),
            "complete_task": lambda: print("🎉 执行完成任务操作")
        }
        
        if command in command_actions:
            command_actions[command]()
        else:
            print(f"❓ 未知命令: {command}")
    
    def run_demo(self, duration: int = None):
        """运行演示"""
        if not self.service or not self.cap:
            logger.error("服务或摄像头未初始化")
            return
        
        try:
            # 开始会话
            session_id = self.service.start_session(device_id="demo_camera")
            logger.info(f"演示会话开始: {session_id}")
            
            self.running = True
            start_time = time.time()
            
            print("\n=== AR手势识别演示开始 ===")
            print("可用手势:")
            print("✋ 手掌 - 取消操作")
            print("✊ 握拳 - 确认操作")
            print("👌 OK手势 - 确认操作")
            print("✌️  胜利手势 - 完成任务")
            print("👍 竖拇指 - 继续执行")
            print("👉 食指指向 - 选择对象")
            print("🤏 捏合 - 放大视图")
            print("🔄 画圆 - 保存项目")
            print("\n按 'q' 键退出演示\n")
            
            while self.running:
                # 检查运行时间
                if duration and (time.time() - start_time) > duration:
                    break
                
                # 读取帧
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("无法读取摄像头帧")
                    break
                
                # 处理帧
                processed_frame = self.service.process_frame(frame)
                
                # 显示帧
                if processed_frame is not None:
                    cv2.imshow('AR手势识别演示', processed_frame)
                
                # 检查按键
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    # 重置统计信息
                    print("统计信息已重置")
                elif key == ord('s'):
                    # 显示当前状态
                    status = self.service.get_service_status()
                    print(f"当前状态: {status}")
            
        except KeyboardInterrupt:
            logger.info("用户中断演示")
        except Exception as e:
            logger.error(f"演示运行失败: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        self.running = False
        
        if self.service:
            self.service.close()
            logger.info("手势识别服务已关闭")
        
        if self.cap:
            self.cap.release()
            logger.info("摄像头已释放")
        
        cv2.destroyAllWindows()
        logger.info("演示结束")


def run_performance_test(duration: int = 30) -> Dict:
    """运行性能测试"""
    logger.info("开始性能测试...")
    
    demo = ARGesturDemo()
    
    # 初始化
    if not demo.initialize_camera() or not demo.initialize_service():
        return {"error": "初始化失败"}
    
    try:
        # 开始会话
        session_id = demo.service.start_session(device_id="performance_test")
        
        frame_count = 0
        gesture_count = 0
        start_time = time.time()
        
        # 性能测试循环
        while time.time() - start_time < duration:
            ret, frame = demo.cap.read()
            if not ret:
                break
            
            # 处理帧
            demo.service.process_frame(frame)
            frame_count += 1
            
            # 获取统计信息
            session_info = demo.service.get_session_info()
            if session_info:
                gesture_count = session_info.statistics.total_gestures
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        # 计算性能指标
        fps = frame_count / test_duration
        gestures_per_minute = (gesture_count / test_duration) * 60
        
        results = {
            "test_duration": test_duration,
            "total_frames": frame_count,
            "total_gestures": gesture_count,
            "fps": round(fps, 2),
            "gestures_per_minute": round(gestures_per_minute, 2),
            "avg_processing_time": round((test_duration / frame_count) * 1000, 2) if frame_count > 0 else 0
        }
        
        logger.info(f"性能测试完成: {results}")
        return results
        
    except Exception as e:
        logger.error(f"性能测试失败: {e}")
        return {"error": str(e)}
    finally:
        demo.cleanup()


def run_accuracy_test():
    """运行准确性测试"""
    logger.info("开始准确性测试...")
    
    # 这里可以实现更复杂的准确性测试逻辑
    # 包括预定义的手势序列和期望结果的比较
    
    print("准确性测试功能待实现...")
    return {"status": "not_implemented"}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AR手势识别系统演示和测试')
    parser.add_argument('--demo', action='store_true', help='运行演示模式')
    parser.add_argument('--test', choices=['performance', 'accuracy'], help='运行测试模式')
    parser.add_argument('--duration', type=int, default=60, help='测试持续时间(秒)')
    parser.add_argument('--camera', type=int, default=0, help='摄像头索引')
    
    args = parser.parse_args()
    
    if args.demo:
        # 运行演示
        demo = ARGesturDemo()
        if demo.initialize_camera(args.camera) and demo.initialize_service():
            demo.run_demo()
        else:
            logger.error("演示初始化失败")
    
    elif args.test == 'performance':
        # 运行性能测试
        results = run_performance_test(args.duration)
        print("\n=== 性能测试结果 ===")
        for key, value in results.items():
            print(f"{key}: {value}")
    
    elif args.test == 'accuracy':
        # 运行准确性测试
        results = run_accuracy_test()
        print("\n=== 准确性测试结果 ===")
        print(results)
    
    else:
        # 显示帮助信息
        parser.print_help()


if __name__ == "__main__":
    main()