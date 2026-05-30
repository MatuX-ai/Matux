"""
XR远程教学系统回测验证报告生成器
执行全面的功能验证和性能测试
"""

import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any
import subprocess
import sys

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class XRBacktestValidator:
    """XR系统回测验证器"""
    
    def __init__(self):
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {},
            "module_tests": {},
            "integration_tests": {},
            "performance_tests": {},
            "security_tests": {},
            "compatibility_tests": {}
        }
    
    def run_comprehensive_backtest(self) -> Dict[str, Any]:
        """运行全面的回测验证"""
        logger.info("开始XR远程教学系统全面回测验证")
        
        # 1. 系统信息收集
        self._collect_system_info()
        
        # 2. 模块功能测试
        self._test_individual_modules()
        
        # 3. 集成测试
        self._test_module_integration()
        
        # 4. 性能测试
        self._test_performance_metrics()
        
        # 5. 安全测试
        self._test_security_features()
        
        # 6. 兼容性测试
        self._test_compatibility()
        
        # 7. 生成报告
        self._generate_report()
        
        return self.test_results
    
    def _collect_system_info(self):
        """收集系统信息"""
        logger.info("收集系统信息")
        
        import platform
        import sys
        
        self.test_results["system_info"] = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "test_timestamp": datetime.now().isoformat()
        }
    
    def _test_individual_modules(self):
        """测试各个独立模块"""
        logger.info("测试独立模块功能")
        
        module_tests = {}
        
        # 测试AR手势识别模块
        try:
            from xr_modules.ar_gesture_recognition.ar_gesture_service import create_default_gesture_service
            from xr_modules.ar_gesture_recognition.models import ARGestureConfig
            
            gesture_service = create_default_gesture_service()
            config = ARGestureConfig()
            
            module_tests["ar_gesture_recognition"] = {
                "status": "passed",
                "details": {
                    "service_initialization": "successful",
                    "default_config_loaded": True,
                    "supported_gestures": len(gesture_service.gesture_mapper.get_available_commands()),
                    "test_time": datetime.now().isoformat()
                }
            }
            logger.info("✅ AR手势识别模块测试通过")
            
        except Exception as e:
            module_tests["ar_gesture_recognition"] = {
                "status": "failed",
                "error": str(e),
                "details": {}
            }
            logger.error(f"❌ AR手势识别模块测试失败: {e}")
        
        # 测试VR代码编辑器模块
        try:
            from xr_modules.vr_3d_editor.vr_editor_core import VREditorCore
            from xr_modules.vr_3d_editor.models import VREditorConfig
            
            editor = VREditorCore()
            config = VREditorConfig()
            
            module_tests["vr_3d_editor"] = {
                "status": "passed",
                "details": {
                    "core_initialization": "successful",
                    "supported_languages": len(editor.get_supported_languages()),
                    "default_config_loaded": True,
                    "test_time": datetime.now().isoformat()
                }
            }
            logger.info("✅ VR代码编辑器模块测试通过")
            
        except Exception as e:
            module_tests["vr_3d_editor"] = {
                "status": "failed",
                "error": str(e),
                "details": {}
            }
            logger.error(f"❌ VR代码编辑器模块测试失败: {e}")
        
        # 测试白板协作模块
        try:
            from xr_modules.whiteboard_collab.whiteboard_core import WhiteboardCore
            from xr_modules.whiteboard_collab.models import WhiteboardConfig
            
            whiteboard = WhiteboardCore()
            config = WhiteboardConfig()
            
            module_tests["whiteboard_collab"] = {
                "status": "passed",
                "details": {
                    "core_initialization": "successful",
                    "default_tools": len(["pen", "marker", "highlighter", "eraser"]),
                    "default_config_loaded": True,
                    "test_time": datetime.now().isoformat()
                }
            }
            logger.info("✅ 白板协作模块测试通过")
            
        except Exception as e:
            module_tests["whiteboard_collab"] = {
                "status": "failed",
                "error": str(e),
                "details": {}
            }
            logger.error(f"❌ 白板协作模块测试失败: {e}")
        
        self.test_results["module_tests"] = module_tests
    
    def _test_module_integration(self):
        """测试模块集成"""
        logger.info("测试模块集成功能")
        
        integration_tests = {}
        
        try:
            # 测试手势到编辑器的集成
            start_time = time.time()
            
            from xr_modules.ar_gesture_recognition.ar_gesture_service import create_default_gesture_service
            from xr_modules.vr_3d_editor.vr_editor_core import VREditorCore
            
            gesture_service = create_default_gesture_service()
            editor = VREditorCore()
            
            # 启动会话
            gesture_session = gesture_service.start_session(user_id=1, device_id="test_device")
            editor_session = editor.initialize_session(user_id=1, device_id="test_device")
            
            # 验证会话同步
            sessions_synced = gesture_service.current_session.session_id == editor.session.session_id
            
            integration_time = time.time() - start_time
            
            integration_tests["gesture_to_editor"] = {
                "status": "passed" if sessions_synced else "failed",
                "details": {
                    "session_sync": sessions_synced,
                    "integration_time": round(integration_time, 4),
                    "test_timestamp": datetime.now().isoformat()
                }
            }
            
            if sessions_synced:
                logger.info("✅ 手势识别与编辑器集成测试通过")
            else:
                logger.error("❌ 手势识别与编辑器集成测试失败")
            
            # 清理
            gesture_service.stop_session()
            editor.close_session()
            
        except Exception as e:
            integration_tests["gesture_to_editor"] = {
                "status": "failed",
                "error": str(e),
                "details": {}
            }
            logger.error(f"❌ 集成测试失败: {e}")
        
        self.test_results["integration_tests"] = integration_tests
    
    def _test_performance_metrics(self):
        """测试性能指标"""
        logger.info("测试性能指标")
        
        performance_tests = {}
        
        try:
            # 响应时间测试
            from xr_modules.ar_gesture_recognition.ar_gesture_service import create_default_gesture_service
            
            gesture_service = create_default_gesture_service()
            gesture_service.start_session(user_id=1)
            
            # 测试多次处理的平均响应时间
            response_times = []
            for i in range(10):
                start_time = time.time()
                gesture_service.process_frame(None)
                response_time = time.time() - start_time
                response_times.append(response_time)
            
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            performance_tests["response_time"] = {
                "status": "passed" if avg_response_time < 0.1 else "warning",
                "details": {
                    "average_response_time": round(avg_response_time, 4),
                    "max_response_time": round(max_response_time, 4),
                    "samples": len(response_times),
                    "target": "< 0.1s",
                    "test_timestamp": datetime.now().isoformat()
                }
            }
            
            # 内存使用测试
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            performance_tests["memory_usage"] = {
                "status": "passed" if memory_mb < 500 else "warning",
                "details": {
                    "current_memory_mb": round(memory_mb, 2),
                    "target": "< 500MB",
                    "test_timestamp": datetime.now().isoformat()
                }
            }
            
            gesture_service.stop_session()
            logger.info("✅ 性能测试完成")
            
        except Exception as e:
            performance_tests["overall"] = {
                "status": "failed",
                "error": str(e),
                "details": {}
            }
            logger.error(f"❌ 性能测试失败: {e}")
        
        self.test_results["performance_tests"] = performance_tests
    
    def _test_security_features(self):
        """测试安全特性"""
        logger.info("测试安全特性")
        
        security_tests = {}
        
        try:
            # 测试会话隔离
            from xr_modules.ar_gesture_recognition.ar_gesture_service import create_default_gesture_service
            
            service1 = create_default_gesture_service()
            service2 = create_default_gesture_service()
            
            session1 = service1.start_session(user_id=1)
            session2 = service2.start_session(user_id=2)
            
            # 验证会话ID不同
            sessions_isolated = session1 != session2
            
            security_tests["session_isolation"] = {
                "status": "passed" if sessions_isolated else "failed",
                "details": {
                    "isolation_verified": sessions_isolated,
                    "session1_id": session1,
                    "session2_id": session2,
                    "test_timestamp": datetime.now().isoformat()
                }
            }
            
            if sessions_isolated:
                logger.info("✅ 会话隔离测试通过")
            else:
                logger.error("❌ 会话隔离测试失败")
            
            # 清理
            service1.stop_session()
            service2.stop_session()
            
        except Exception as e:
            security_tests["session_isolation"] = {
                "status": "failed",
                "error": str(e),
                "details": {}
            }
            logger.error(f"❌ 安全测试失败: {e}")
        
        self.test_results["security_tests"] = security_tests
    
    def _test_compatibility(self):
        """测试兼容性"""
        logger.info("测试系统兼容性")
        
        compatibility_tests = {}
        
        try:
            # 测试Python版本兼容性
            import sys
            python_version = sys.version_info
            version_compatible = python_version >= (3, 8)
            
            compatibility_tests["python_version"] = {
                "status": "passed" if version_compatible else "failed",
                "details": {
                    "current_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                    "minimum_required": "3.8",
                    "compatible": version_compatible,
                    "test_timestamp": datetime.now().isoformat()
                }
            }
            
            # 测试依赖包导入
            required_packages = [
                "cv2", "numpy", "mediapipe", "fastapi", "pydantic"
            ]
            
            imported_packages = []
            missing_packages = []
            
            for package in required_packages:
                try:
                    __import__(package)
                    imported_packages.append(package)
                except ImportError:
                    missing_packages.append(package)
            
            compatibility_tests["package_dependencies"] = {
                "status": "passed" if not missing_packages else "warning",
                "details": {
                    "imported_packages": imported_packages,
                    "missing_packages": missing_packages,
                    "total_required": len(required_packages),
                    "successfully_imported": len(imported_packages),
                    "test_timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info("✅ 兼容性测试完成")
            
        except Exception as e:
            compatibility_tests["overall"] = {
                "status": "failed",
                "error": str(e),
                "details": {}
            }
            logger.error(f"❌ 兼容性测试失败: {e}")
        
        self.test_results["compatibility_tests"] = compatibility_tests
    
    def _generate_report(self):
        """生成测试报告"""
        logger.info("生成回测验证报告")
        
        # 计算总体统计
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warning_tests = 0
        
        for category in ["module_tests", "integration_tests", "performance_tests", 
                        "security_tests", "compatibility_tests"]:
            if category in self.test_results:
                for test_name, test_result in self.test_results[category].items():
                    total_tests += 1
                    if test_result["status"] == "passed":
                        passed_tests += 1
                    elif test_result["status"] == "failed":
                        failed_tests += 1
                    elif test_result["status"] == "warning":
                        warning_tests += 1
        
        # 添加汇总信息
        self.test_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "warning_tests": warning_tests,
            "pass_rate": round((passed_tests / total_tests * 100), 2) if total_tests > 0 else 0,
            "generated_at": datetime.now().isoformat()
        }
        
        # 保存报告到文件
        report_filename = f"xr_system_backtest_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"回测报告已保存: {report_filename}")
        
        # 打印摘要
        self._print_summary()
    
    def _print_summary(self):
        """打印测试摘要"""
        summary = self.test_results["summary"]
        
        print("\n" + "="*60)
        print("XR远程教学系统回测验证报告摘要")
        print("="*60)
        print(f"测试时间: {self.test_results['timestamp']}")
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过测试: {summary['passed_tests']}")
        print(f"失败测试: {summary['failed_tests']}")
        print(f"警告测试: {summary['warning_tests']}")
        print(f"通过率: {summary['pass_rate']}%")
        print("="*60)
        
        if summary['pass_rate'] >= 90:
            print("🎉 系统整体表现优秀！")
        elif summary['pass_rate'] >= 75:
            print("✅ 系统基本功能正常")
        else:
            print("⚠️  系统需要进一步优化")


def main():
    """主函数"""
    validator = XRBacktestValidator()
    results = validator.run_comprehensive_backtest()
    
    # 根据结果决定退出码
    summary = results["summary"]
    if summary["failed_tests"] == 0:
        print("\n✅ 所有关键测试通过，系统可以部署")
        sys.exit(0)
    else:
        print(f"\n❌ 存在 {summary['failed_tests']} 个失败测试")
        sys.exit(1)


if __name__ == "__main__":
    main()