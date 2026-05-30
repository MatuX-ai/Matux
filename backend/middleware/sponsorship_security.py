"""
企业赞助管理系统安全中间件
提供输入验证、权限控制、速率限制等安全功能
"""

from collections import defaultdict
from datetime import datetime
import json
import re
import time
from typing import Any, Dict

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.sponsorship_config import get_sponsorship_config

security_config = get_sponsorship_config().security


class RateLimiter:
    """速率限制器"""

    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.limits: Dict[str, tuple] = {
            "default": (100, 60),  # 100次/分钟
            "analytics": (50, 60),  # 50次/分钟
            "conversion": (20, 60),  # 20次/分钟
        }

    def is_allowed(self, client_id: str, endpoint: str = "default") -> bool:
        """检查是否允许请求"""
        now = time.time()
        limit, window = self.limits.get(endpoint, self.limits["default"])

        # 清理过期请求记录
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id] if now - req_time < window
        ]

        # 检查是否超过限制
        if len(self.requests[client_id]) >= limit:
            return False

        # 记录本次请求
        self.requests[client_id].append(now)
        return True

    def get_retry_after(self, client_id: str) -> int:
        """获取重试等待时间"""
        if not self.requests[client_id]:
            return 0
        oldest_request = min(self.requests[client_id])
        return int(60 - (time.time() - oldest_request))


class InputValidator:
    """输入验证器"""

    def __init__(self):
        self.config = get_sponsorship_config()

    def validate_sponsorship_data(self, data: Dict[str, Any]) -> bool:
        """验证赞助活动数据"""
        required_fields = ["name", "sponsor_amount", "start_date", "end_date"]

        # 检查必需字段
        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")

        # 验证字段类型和值
        if not isinstance(data["name"], str) or len(data["name"]) > 255:
            raise HTTPException(status_code=400, detail="活动名称格式不正确")

        if (
            not isinstance(data["sponsor_amount"], (int, float))
            or data["sponsor_amount"] <= 0
        ):
            raise HTTPException(status_code=400, detail="赞助金额必须为正数")

        # 验证日期逻辑
        if data["start_date"] >= data["end_date"]:
            raise HTTPException(status_code=400, detail="结束日期必须晚于开始日期")

        # 验证曝光类型
        if "exposure_types" in data:
            valid_types = [
                "banner",
                "sidebar",
                "popup",
                "email",
                "social_media",
                "content_integration",
            ]
            for exp_type in data["exposure_types"]:
                if exp_type not in valid_types:
                    raise HTTPException(
                        status_code=400, detail=f"无效的曝光类型: {exp_type}"
                    )

        return True

    def validate_exposure_data(self, data: Dict[str, Any]) -> bool:
        """验证曝光数据"""
        required_fields = ["exposure_type", "view_count"]

        for field in required_fields:
            if field not in data:
                raise HTTPException(status_code=400, detail=f"缺少必需字段: {field}")

        # 验证数值范围
        if data["view_count"] < 0:
            raise HTTPException(status_code=400, detail="展示次数不能为负数")

        if "click_count" in data and data["click_count"] > data["view_count"]:
            raise HTTPException(status_code=400, detail="点击次数不能超过展示次数")

        return True

    def sanitize_input(self, input_data: Any) -> Any:
        """输入清理和消毒"""
        if isinstance(input_data, str):
            # 移除潜在危险字符
            dangerous_patterns = [
                (r"['\";<>]", ""),  # SQL注入相关字符
                (
                    r"(union|select|insert|delete|drop|create|alter)",
                    "",
                    re.IGNORECASE,
                ),  # SQL关键字
                (
                    r"<script[^>]*>.*?</script>",
                    "",
                    re.IGNORECASE | re.DOTALL,
                ),  # XSS脚本
                (r"javascript:", "", re.IGNORECASE),  # JavaScript协议
            ]

            cleaned = input_data
            for pattern, replacement, *flags in dangerous_patterns:
                flag = flags[0] if flags else 0
                cleaned = re.sub(pattern, replacement, cleaned, flags=flag)

            # 限制字符串长度
            max_length = self.config.security.MAX_STRING_LENGTH
            if len(cleaned) > max_length:
                cleaned = cleaned[:max_length]

            return cleaned

        elif isinstance(input_data, dict):
            return {k: self.sanitize_input(v) for k, v in input_data.items()}
        elif isinstance(input_data, list):
            return [self.sanitize_input(item) for item in input_data]
        else:
            return input_data


class PermissionChecker:
    """权限检查器"""

    def __init__(self):
        self.role_permissions = {
            "admin": ["create", "read", "update", "delete", "analytics", "conversion"],
            "manager": ["create", "read", "update", "analytics"],
            "user": ["read", "analytics"],
        }

    def check_permission(
        self, user_role: str, action: str, resource_org_id: int, user_org_id: int
    ) -> bool:
        """检查用户权限"""
        # 组织隔离检查
        if resource_org_id != user_org_id:
            return False

        # 权限等级检查
        if user_role not in self.role_permissions:
            return False

        return action in self.role_permissions[user_role]

    def check_sponsorship_access(
        self, user_role: str, sponsorship_id: int, action: str, user_org_id: int
    ) -> bool:
        """检查赞助活动访问权限"""
        # 这里应该查询数据库验证赞助活动归属
        # 简化实现，假设验证通过
        return self.check_permission(user_role, action, user_org_id, user_org_id)


class AuditLogger:
    """审计日志记录器"""

    def __init__(self):
        self.audit_enabled = get_sponsorship_config().security.AUDIT_LOG_ENABLED

    def log_action(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: int,
        details: Dict[str, Any] = None,
    ):
        """记录操作日志"""
        if not self.audit_enabled:
            return

        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": None,  # 应该从请求中获取
            "user_agent": None,  # 应该从请求中获取
        }

        # 这里应该将日志写入专门的审计日志表
        print(f"AUDIT LOG: {json.dumps(log_entry)}")


# 全局实例
rate_limiter = RateLimiter()
input_validator = InputValidator()
permission_checker = PermissionChecker()
audit_logger = AuditLogger()

# 安全中间件依赖
security = HTTPBearer()


async def get_current_user_security(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """获取当前用户安全信息"""
    # 这里应该实现JWT解码和用户验证
    # 简化实现返回模拟用户信息
    return {"user_id": 1, "username": "test_user", "role": "admin", "org_id": 1}


async def sponsorship_security_middleware(
    request: Request, current_user: dict = Depends(get_current_user_security)
):
    """赞助系统安全中间件"""

    # 1. 速率限制检查
    client_id = f"{current_user['user_id']}_{request.client.host if request.client else 'unknown'}"
    endpoint_type = "analytics" if "analytics" in request.url.path else "default"

    if not rate_limiter.is_allowed(client_id, endpoint_type):
        retry_after = rate_limiter.get_retry_after(client_id)
        raise HTTPException(
            status_code=429, detail=f"请求过于频繁，请在 {retry_after} 秒后重试"
        )

    # 2. 输入数据验证和清理
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                # 解析JSON数据
                try:
                    json_data = json.loads(body.decode())
                    # 清理输入数据
                    cleaned_data = input_validator.sanitize_input(json_data)
                    # 验证业务逻辑
                    if "sponsorships" in request.url.path and request.method == "POST":
                        input_validator.validate_sponsorship_data(cleaned_data)
                    elif "exposures" in request.url.path and request.method == "POST":
                        input_validator.validate_exposure_data(cleaned_data)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="无效的JSON格式")
        except Exception as e:
            if "Request body exhausted" not in str(e):
                raise HTTPException(status_code=400, detail=str(e))

    # 3. 权限检查
    required_action = {
        "POST": "create",
        "GET": "read",
        "PUT": "update",
        "DELETE": "delete",
    }.get(request.method, "read")

    # 从URL中提取资源ID进行权限验证
    path_parts = request.url.path.split("/")
    if "sponsorships" in path_parts:
        sponsorship_index = path_parts.index("sponsorships")
        if len(path_parts) > sponsorship_index + 1:
            try:
                sponsorship_id = int(path_parts[sponsorship_index + 1])
                if not permission_checker.check_sponsorship_access(
                    current_user["role"],
                    sponsorship_id,
                    required_action,
                    current_user["org_id"],
                ):
                    raise HTTPException(status_code=403, detail="权限不足")
            except ValueError:
                pass  # 不是数字ID，跳过权限检查

    # 4. 记录审计日志
    audit_logger.log_action(
        user_id=current_user["user_id"],
        action=required_action,
        resource_type="sponsorship_api",
        resource_id=0,  # 可以从URL中提取具体资源ID
        details={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )

    # 5. 添加安全响应头
    request.state.user = current_user
    request.state.security_checked = True

    return request


# 异常处理器
async def sponsorship_security_exception_handler(request: Request, exc: Exception):
    """安全异常处理器"""
    if isinstance(exc, HTTPException):
        return exc

    # 记录安全违规事件
    audit_logger.log_action(
        user_id=getattr(request.state, "user", {}).get("user_id", 0),
        action="security_violation",
        resource_type="system",
        resource_id=0,
        details={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": request.url.path,
            "method": request.method,
        },
    )

    return HTTPException(status_code=500, detail="内部安全错误")
