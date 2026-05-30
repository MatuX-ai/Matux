"""
路由包初始化
使用延迟导入避免循环引用
"""

import importlib

# 使用 __getattr__ 延迟加载模块，避免循环导入
_module_registry = {}

def __getattr__(name):
    if name not in _module_registry:
        _module_registry[name] = importlib.import_module(f".{name}", __package__)
    return _module_registry[name]

__all__ = ["ai_routes", "auth_routes", "user_license_routes", "ai_edu_progress_routes", "ai_teacher_routes"]
