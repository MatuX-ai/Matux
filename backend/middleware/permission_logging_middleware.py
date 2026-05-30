"""
权限变更日志记录系统
自动记录权限相关的操作日志
"""

import json
import logging
from typing import Any, Dict, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from services.permission_service import permission_service

logger = logging.getLogger(__name__)


class PermissionLoggingMiddleware(BaseHTTPMiddleware):
    """权限日志中间件"""

    # 需要记录日志的敏感操作路径模式
    SENSITIVE_PATHS = {
        # 用户管理
        "/api/v1/users": ["POST", "PUT", "DELETE"],
        "/api/v1/users/*": ["PUT", "DELETE"],
        # 角色管理
        "/api/v1/roles": ["POST", "PUT", "DELETE"],
        "/api/v1/roles/*": ["PUT", "DELETE"],
        # 权限管理
        "/api/v1/permissions": ["POST", "PUT", "DELETE"],
        "/api/v1/permissions/*": ["PUT", "DELETE"],
        # 许可证管理
        "/api/v1/licenses": ["POST", "PUT", "DELETE"],
        "/api/v1/licenses/*": ["PUT", "DELETE"],
        # 系统配置
        "/api/v1/config": ["POST", "PUT", "DELETE"],
        "/api/v1/config/*": ["PUT", "DELETE"],
    }

    # 路径到资源类型的映射
    PATH_RESOURCE_MAPPING = {
        "/api/v1/users": "user",
        "/api/v1/roles": "role",
        "/api/v1/permissions": "permission",
        "/api/v1/licenses": "license",
        "/api/v1/config": "config",
    }

    async def dispatch(self, request: Request, call_next):
        """中间件主逻辑"""
        # 检查是否需要记录日志
        if not self._should_log_request(request):
            return await call_next(request)

        # 获取请求信息
        user_id = self._get_user_id_from_request(request)
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # 记录请求前的状态
        request_body = await self._get_request_body(request)
        old_state = await self._get_resource_state_before_change(request)

        try:
            # 执行请求
            response = await call_next(request)

            # 记录成功的操作
            if response.status_code < 400:
                await self._log_successful_operation(
                    request=request,
                    user_id=user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    old_state=old_state,
                    request_body=request_body,
                )

            return response

        except Exception as e:
            # 记录失败的操作
            await self._log_failed_operation(
                request=request,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                error=str(e),
                old_state=old_state,
            )
            raise

    def _should_log_request(self, request: Request) -> bool:
        """判断是否需要记录该请求的日志"""
        path = request.url.path
        method = request.method

        # 检查精确路径匹配
        if path in self.SENSITIVE_PATHS:
            return method in self.SENSITIVE_PATHS[path]

        # 检查通配符路径匹配
        for pattern_path, methods in self.SENSITIVE_PATHS.items():
            if pattern_path.endswith("/*") and path.startswith(pattern_path[:-2]):
                return method in methods

        return False

    def _get_user_id_from_request(self, request: Request) -> Optional[int]:
        """从请求中提取用户ID"""
        # 从请求状态中获取用户信息（如果已认证）
        if hasattr(request.state, "user") and request.state.user:
            return request.state.user.id

        # 从JWT token中解析用户ID
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from jose import jwt

                from config.settings import Settings

                settings = Settings()
                token = auth_header[7:]  # 移除 'Bearer ' 前缀
                payload = jwt.decode(
                    token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
                )
                return payload.get("sub")  # 假设用户ID存储在sub字段中
            except Exception:
                pass

        return None

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查X-Forwarded-For头（负载均衡场景）
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        # 检查X-Real-IP头
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # 使用客户端IP
        return request.client.host if request.client else "unknown"

    async def _get_request_body(self, request: Request) -> Optional[str]:
        """获取请求体内容"""
        try:
            body = await request.body()
            if body:
                return body.decode("utf-8")[:1000]  # 限制长度
        except Exception:
            pass
        return None

    async def _get_resource_state_before_change(
        self, request: Request
    ) -> Optional[str]:
        """获取变更前的资源状态"""
        try:
            # 对于PUT和DELETE请求，尝试获取原始资源信息
            if request.method in ["PUT", "DELETE"]:
                # 这里可以根据具体业务逻辑实现
                # 例如查询数据库获取修改前的数据
                pass
        except Exception:
            pass
        return None

    async def _log_successful_operation(
        self,
        request: Request,
        user_id: Optional[int],
        ip_address: str,
        user_agent: str,
        old_state: Optional[str],
        request_body: Optional[str],
    ):
        """记录成功的操作日志"""
        try:
            action_type = self._map_method_to_action(request.method)
            resource_type = self._get_resource_type(request.url.path)
            resource_id = self._extract_resource_id(request.url.path)

            # 构造描述信息
            description = f"{request.method} {request.url.path}"
            if request_body:
                description += f" - 请求体: {request_body[:200]}..."

            await permission_service.log_permission_change(
                user_id=user_id,
                target_user_id=None,  # 根据具体业务确定目标用户
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                old_value=old_state,
                new_value=request_body,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        except Exception as e:
            logger.error(f"记录成功操作日志失败: {e}")

    async def _log_failed_operation(
        self,
        request: Request,
        user_id: Optional[int],
        ip_address: str,
        user_agent: str,
        error: str,
        old_state: Optional[str],
    ):
        """记录失败的操作日志"""
        try:
            action_type = self._map_method_to_action(request.method) + "_failed"
            resource_type = self._get_resource_type(request.url.path)
            resource_id = self._extract_resource_id(request.url.path)

            description = f"{request.method} {request.url.path} - 失败: {error}"

            await permission_service.log_permission_change(
                user_id=user_id,
                target_user_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                old_value=old_state,
                new_value=error,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
            )

        except Exception as e:
            logger.error(f"记录失败操作日志失败: {e}")

    def _map_method_to_action(self, method: str) -> str:
        """将HTTP方法映射到操作类型"""
        mapping = {
            "POST": "create",
            "GET": "read",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }
        return mapping.get(method.upper(), "unknown")

    def _get_resource_type(self, path: str) -> str:
        """根据路径确定资源类型"""
        # 移除API前缀和版本号
        clean_path = path.replace("/api/v1/", "/")

        # 查找最匹配的路径
        for pattern, resource_type in self.PATH_RESOURCE_MAPPING.items():
            if clean_path.startswith(pattern):
                return resource_type

        # 默认返回路径的最后一部分作为资源类型
        parts = clean_path.strip("/").split("/")
        return parts[-1] if parts else "unknown"

    def _extract_resource_id(self, path: str) -> Optional[int]:
        """从路径中提取资源ID"""
        try:
            # 匹配类似 /api/v1/users/123 的模式
            parts = path.strip("/").split("/")
            if len(parts) >= 4 and parts[-1].isdigit():
                return int(parts[-1])
        except Exception:
            pass
        return None


# 便捷的日志记录函数
async def log_user_role_assignment(
    operator_id: int,
    target_user_id: int,
    role_code: str,
    action: str,  # 'assign' or 'revoke'
    reason: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """记录用户角色分配/撤销操作"""
    try:
        action_type = f"role_{action}"
        description = f"{'分配' if action == 'assign' else '撤销'}角色 {role_code}"
        if reason:
            description += f" - 原因: {reason}"

        await permission_service.log_permission_change(
            user_id=operator_id,
            target_user_id=target_user_id,
            action_type=action_type,
            resource_type="role",
            role_code=role_code,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        logger.error(f"记录角色操作日志失败: {e}")


async def log_permission_change(
    operator_id: int,
    target_user_id: Optional[int],
    permission_code: str,
    action: str,  # 'grant' or 'revoke'
    reason: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """记录权限变更操作"""
    try:
        action_type = f"permission_{action}"
        description = f"{'授予' if action == 'grant' else '撤销'}权限 {permission_code}"
        if reason:
            description += f" - 原因: {reason}"

        await permission_service.log_permission_change(
            user_id=operator_id,
            target_user_id=target_user_id,
            action_type=action_type,
            resource_type="permission",
            permission_code=permission_code,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        logger.error(f"记录权限变更日志失败: {e}")


async def log_sensitive_operation(
    user_id: int,
    operation: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """记录敏感操作日志"""
    try:
        description = f"敏感操作: {operation}"
        if details:
            description += f" - 详情: {json.dumps(details, ensure_ascii=False)}"

        await permission_service.log_permission_change(
            user_id=user_id,
            target_user_id=None,
            action_type="sensitive_operation",
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception as e:
        logger.error(f"记录敏感操作日志失败: {e}")
