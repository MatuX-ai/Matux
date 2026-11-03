"""
企业网关路由模块初始化

导出的是路由“模块”而非 router 实例，
以匹配 main.py 中 `xxx_routes.router` 的使用方式。
"""

from . import device_management_routes, enterprise_auth_routes, monitoring_routes

__all__ = ["enterprise_auth_routes", "device_management_routes", "monitoring_routes"]
