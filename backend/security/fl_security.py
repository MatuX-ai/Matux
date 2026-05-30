"""
联邦学习安全和认证模块
提供专门的权限控制和安全验证功能
"""

from datetime import datetime, timedelta
import hashlib
import logging
from typing import Any, Dict, List

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from ..config.settings import settings
from ..models.user import User

logger = logging.getLogger(__name__)

security = HTTPBearer()


class FLPermissionManager:
    """联邦学习权限管理器"""

    # 联邦学习相关权限定义
    FL_PERMISSIONS = {
        "fl_start_training": "启动联邦学习训练",
        "fl_manage_participants": "管理联邦学习参与者",
        "fl_view_monitoring": "查看联邦学习监控数据",
        "fl_manage_configurations": "管理联邦学习配置",
        "fl_access_models": "访问联邦学习模型",
        "fl_export_data": "导出联邦学习数据",
    }

    def __init__(self):
        self.required_permissions = {
            "/federated/trainings/": ["fl_start_training"],
            "/federated/participants/": ["fl_manage_participants"],
            "/federated/monitoring/": ["fl_view_monitoring"],
            "/federated/configurations/": ["fl_manage_configurations"],
        }

    def check_permission(self, user: User, endpoint: str, method: str) -> bool:
        """检查用户权限"""
        # 管理员拥有所有权限
        if user.is_admin:
            return True

        # 获取所需权限
        required_perms = self._get_required_permissions(endpoint, method)

        # 检查用户是否拥有任一所需权限
        user_permissions = self._get_user_permissions(user)
        return any(perm in user_permissions for perm in required_perms)

    def _get_required_permissions(self, endpoint: str, method: str) -> List[str]:
        """获取端点所需权限"""
        # 简化的权限映射逻辑
        for path_prefix, permissions in self.required_permissions.items():
            if endpoint.startswith(path_prefix):
                return permissions
        return []

    def _get_user_permissions(self, user: User) -> List[str]:
        """获取用户拥有的权限"""
        permissions = []

        # 基于用户角色分配权限
        if hasattr(user, "role"):
            role_permissions = self._get_role_permissions(user.role)
            permissions.extend(role_permissions)

        # 添加用户特定权限
        if hasattr(user, "permissions") and user.permissions:
            permissions.extend(user.permissions)

        return list(set(permissions))  # 去重

    def _get_role_permissions(self, role: str) -> List[str]:
        """根据角色获取权限"""
        role_mapping = {
            "admin": list(self.FL_PERMISSIONS.keys()),
            "researcher": [
                "fl_start_training",
                "fl_view_monitoring",
                "fl_access_models",
            ],
            "participant": ["fl_view_monitoring"],
            "viewer": ["fl_view_monitoring"],
        }
        return role_mapping.get(role, [])


class FLSecurityToken:
    """联邦学习安全令牌"""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY or "fl_default_secret_key"
        self.algorithm = "HS256"
        self.token_expiry = timedelta(hours=24)

    def generate_token(self, user_id: str, participant_id: str = None) -> str:
        """生成安全令牌"""
        payload = {
            "user_id": user_id,
            "participant_id": participant_id,
            "exp": datetime.utcnow() + self.token_expiry,
            "iat": datetime.utcnow(),
            "scope": "federated_learning",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # 验证作用域
            if payload.get("scope") != "federated_learning":
                raise HTTPException(status_code=401, detail="Invalid token scope")

            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def generate_participant_token(self, participant_id: str) -> str:
        """为参与者生成专用令牌"""
        return self.generate_token("participant", participant_id)


class FLDataEncryption:
    """联邦学习数据加密"""

    def __init__(self):
        self.encryption_key = (
            settings.ENCRYPTION_KEY or "default_encryption_key_32bytes!"
        )

    def encrypt_model_weights(self, weights: Dict[str, Any]) -> bytes:
        """加密模型权重"""
        import json
        import pickle

        from cryptography.fernet import Fernet

        # 生成加密密钥
        key = Fernet.generate_key()
        cipher_suite = Fernet(key)

        # 序列化权重
        weights_str = json.dumps(weights, default=str)

        # 加密
        encrypted_data = cipher_suite.encrypt(weights_str.encode())

        # 返回密钥和加密数据
        return pickle.dumps((key, encrypted_data))

    def decrypt_model_weights(self, encrypted_data: bytes) -> Dict[str, Any]:
        """解密模型权重"""
        import json
        import pickle

        from cryptography.fernet import Fernet

        # 解析密钥和数据
        key, encrypted_weights = pickle.loads(encrypted_data)
        cipher_suite = Fernet(key)

        # 解密
        decrypted_data = cipher_suite.decrypt(encrypted_weights)
        weights = json.loads(decrypted_data.decode())

        return weights

    def calculate_checksum(self, data: bytes) -> str:
        """计算数据校验和"""
        return hashlib.sha256(data).hexdigest()


async def get_current_fl_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> User:
    """获取当前联邦学习用户"""
    try:
        token_manager = FLSecurityToken()
        payload = token_manager.verify_token(credentials.credentials)

        # 这里应该从数据库获取用户信息
        # 简化实现，创建一个模拟用户
        user = User(
            id=payload["user_id"],
            username=f"user_{payload['user_id']}",
            email=f"user_{payload['user_id']}@example.com",
            is_active=True,
            is_admin=payload["user_id"] == "admin",
        )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"认证失败: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


def require_fl_permission(permission: str):
    """联邦学习权限装饰器"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取当前用户（假设通过依赖注入）
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401, detail="User not authenticated")

            # 检查权限
            permission_manager = FLPermissionManager()
            endpoint = kwargs.get("request", {}).get("url", {}).get("path", "")
            if not permission_manager.check_permission(current_user, endpoint, "POST"):
                raise HTTPException(status_code=403, detail="Insufficient permissions")

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class FLAuditLogger:
    """联邦学习审计日志"""

    def __init__(self):
        self.logger = logging.getLogger("fl_audit")

    def log_training_action(
        self,
        user_id: str,
        action: str,
        training_id: str,
        details: Dict[str, Any] = None,
    ):
        """记录训练相关操作"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "training_id": training_id,
            "details": details or {},
            "event_type": "training_action",
        }
        self.logger.info(f"AUDIT: {log_entry}")

    def log_participant_action(
        self, participant_id: str, action: str, details: Dict[str, Any] = None
    ):
        """记录参与者操作"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "participant_id": participant_id,
            "action": action,
            "details": details or {},
            "event_type": "participant_action",
        }
        self.logger.info(f"AUDIT: {log_entry}")

    def log_security_event(
        self, event_type: str, description: str, severity: str = "info"
    ):
        """记录安全事件"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "description": description,
            "severity": severity,
        }
        if severity == "critical":
            self.logger.critical(f"SECURITY: {log_entry}")
        elif severity == "warning":
            self.logger.warning(f"SECURITY: {log_entry}")
        else:
            self.logger.info(f"SECURITY: {log_entry}")


# 全局实例
fl_permission_manager = FLPermissionManager()
fl_security_token = FLSecurityToken()
fl_data_encryption = FLDataEncryption()
fl_audit_logger = FLAuditLogger()
