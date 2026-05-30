"""
企业网关路由模块初始化
"""

from .device_management_routes import router as device_management_routes
from .enterprise_auth_routes import router as enterprise_auth_routes
from .monitoring_routes import router as monitoring_routes

__all__ = ["enterprise_auth_routes", "device_management_routes", "monitoring_routes"]
