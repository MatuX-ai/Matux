"""
基于许可证的权限控制系统
提供细粒度的功能访问控制和灵活的商业模式支持
"""

from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

from fastapi import Depends, HTTPException, status
from middleware.auth import get_current_user
from models.license import LicenseStatus, LicenseType
from models.user import User
from models.user_license import UserLicense
from sqlalchemy.orm import Session
from utils.database import get_db

# ============================================
# 权限矩阵定义
# ============================================
# 档位对应关系：BASIC 与 OPEN_SOURCE 同为免费基础档，
# PREMIUM 与 CLOUD_HOSTED 同为付费档。

PERMISSION_MATRIX: Dict[str, Dict[LicenseType, bool]] = {
    # 基础功能（所有版本都可用）
    "course_management": {
        LicenseType.BASIC: True,
        LicenseType.OPEN_SOURCE: True,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.PREMIUM: True,
        LicenseType.TRIAL: True,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },
    "user_management": {
        LicenseType.BASIC: True,
        LicenseType.OPEN_SOURCE: True,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.PREMIUM: True,
        LicenseType.TRIAL: True,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },

    # AI 功能（仅付费版可用）
    "ai_course_generation": {
        LicenseType.BASIC: False,
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.PREMIUM: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },
    "ai_chat_assistant": {
        LicenseType.BASIC: False,
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.PREMIUM: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },
    "ai_code_completion": {
        LicenseType.BASIC: False,
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.PREMIUM: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },

    # 部署模式相关功能
    "offline_mode": {
        LicenseType.BASIC: False,
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: False,
        LicenseType.PREMIUM: False,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },
    "cloud_sync": {
        LicenseType.BASIC: False,
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.PREMIUM: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },
    "multi_tenant": {
        LicenseType.BASIC: False,
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: False,
        LicenseType.PREMIUM: False,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },

    # Token 计费功能
    "token_billing": {
        LicenseType.BASIC: False,
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.PREMIUM: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },
    "monthly_bonus_tokens": {
        LicenseType.BASIC: False,
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.PREMIUM: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },

    # 高级功能
    "advanced_analytics": {
        LicenseType.BASIC: False,
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.PREMIUM: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },
    "priority_support": {
        LicenseType.BASIC: False,
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.PREMIUM: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },
    "custom_branding": {
        LicenseType.BASIC: False,
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: False,
        LicenseType.PREMIUM: False,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },
}

# 升级建议映射
UPGRADE_SUGGESTIONS: Dict[LicenseType, str] = {
    LicenseType.BASIC: "升级到 Windows 本地版或云托管版以解锁 AI 功能和高级特性",
    LicenseType.OPEN_SOURCE: "升级到 Windows 本地版或云托管版以解锁 AI 功能和高级特性",
    LicenseType.TRIAL: "购买正式版以解锁完整功能（Windows 本地版/云托管版/企业版）",
    LicenseType.WINDOWS_LOCAL: "升级到云托管版以支持云端同步和多租户管理",
    LicenseType.CLOUD_HOSTED: "升级到企业定制版以获得离线模式和自定义品牌功能",
    LicenseType.PREMIUM: "升级到企业定制版以获得离线模式和自定义品牌功能",
}


# ============================================
# 许可证服务类
# ============================================

class LicensePermissionService:
    """许可证权限管理服务"""

    def __init__(self, db: Session):
        self.db = db

    async def get_user_license(self, user_id: str) -> Optional[Any]:
        """获取用户的有效许可证

        注意：models/license.py 中的 License 是 Pydantic 模型（不是 SQLAlchemy 映射类），
        不能作为 db.query() 的查询目标（类级字段访问会直接抛 AttributeError），
        因此这里查询用户许可证关联表 user_licenses。
        状态/类型/有效期等字段统一由下方 _extract_* 辅助方法从记录中安全提取。
        """
        license_row = self.db.query(UserLicense).filter(
            UserLicense.user_id == user_id,
            UserLicense.is_active.is_(True),
        ).first()

        return license_row

    @staticmethod
    def _extract_status(license_obj: Any) -> LicenseStatus:
        """从许可证记录中提取状态（无法识别时视为 ACTIVE）"""
        raw_status = getattr(license_obj, "status", None)
        status_value = getattr(raw_status, "value", raw_status)
        try:
            return LicenseStatus(status_value)
        except (ValueError, TypeError):
            return LicenseStatus.ACTIVE

    @staticmethod
    def _extract_license_type(license_obj: Any) -> LicenseType:
        """从许可证记录中提取许可证类型（无法识别时缺省为 BASIC）"""
        raw_type = getattr(license_obj, "license_type", None)
        type_value = getattr(raw_type, "value", raw_type)
        try:
            return LicenseType(type_value)
        except (ValueError, TypeError):
            return LicenseType.BASIC

    @staticmethod
    def _is_expired(license_obj: Any) -> bool:
        """判断许可证是否已过期"""
        expired_flag = getattr(license_obj, "is_expired", None)
        if isinstance(expired_flag, bool):
            return expired_flag

        expires_at = getattr(license_obj, "expires_at", None)
        if expires_at is None:
            return False

        return expires_at < datetime.utcnow()

    def check_feature_permission(
        self,
        feature: str,
        license_type: LicenseType
    ) -> Dict[str, Any]:
        """
        检查特定许可证类型对某个功能的访问权限

        Args:
            feature: 功能名称
            license_type: 许可证类型

        Returns:
            {
                "allowed": bool,
                "reason": str,
                "upgrade_suggestion": str
            }
        """
        # 获取权限矩阵中的配置
        feature_permissions = PERMISSION_MATRIX.get(feature)

        if not feature_permissions:
            # 功能未在矩阵中定义，默认允许
            return {
                "allowed": True,
                "reason": f"功能 '{feature}' 未设置权限限制",
                "upgrade_suggestion": ""
            }

        # 检查该许可证类型是否有权限
        allowed = feature_permissions.get(license_type, False)

        if allowed:
            return {
                "allowed": True,
                "reason": "权限验证通过",
                "upgrade_suggestion": ""
            }
        else:
            upgrade_suggestion = UPGRADE_SUGGESTIONS.get(
                license_type,
                "请联系客服了解如何升级许可证"
            )

            return {
                "allowed": False,
                "reason": f"当前许可证类型 ({license_type.value}) 不支持 '{feature}' 功能",
                "upgrade_suggestion": upgrade_suggestion
            }

    async def verify_feature_access(
        self,
        user_id: str,
        feature: str
    ) -> Dict[str, Any]:
        """
        验证用户对特定功能的访问权限

        Args:
            user_id: 用户 ID
            feature: 功能名称

        Returns:
            {
                "allowed": bool,
                "reason": str,
                "upgrade_suggestion": str,
                "license_type": str (optional)
            }
        """
        # 获取用户许可证
        license_obj = await self.get_user_license(user_id)

        if not license_obj:
            return {
                "allowed": False,
                "reason": "未找到有效许可证，请先激活许可证",
                "upgrade_suggestion": "请购买或激活许可证以使用该功能"
            }

        # 检查许可证状态
        license_status = self._extract_status(license_obj)
        if license_status != LicenseStatus.ACTIVE:
            return {
                "allowed": False,
                "reason": f"许可证状态异常：{license_status.value}",
                "upgrade_suggestion": "请联系管理员激活许可证"
            }

        # 检查是否过期
        if self._is_expired(license_obj):
            return {
                "allowed": False,
                "reason": "许可证已过期",
                "upgrade_suggestion": "请续费或重新购买许可证"
            }

        # 检查功能权限
        license_type = self._extract_license_type(license_obj)
        permission_result = self.check_feature_permission(
            feature,
            license_type
        )

        # 添加许可证类型信息
        permission_result["license_type"] = license_type.value

        return permission_result


# ============================================
# 权限装饰器
# ============================================

def require_license_type(*allowed_types: LicenseType):
    """
    许可证类型权限装饰器

    用法:
        @router.get("/ai/generate")
        @require_license_type(LicenseType.WINDOWS_LOCAL, LicenseType.CLOUD_HOSTED)
        async def generate_course(...):
            ...

    Args:
        *allowed_types: 允许的许可证类型列表
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db),
            **kwargs
        ):
            # 获取用户许可证
            license_service = LicensePermissionService(db)
            license_obj = await license_service.get_user_license(current_user.id)

            # 检查许可证是否存在
            if not license_obj:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "no_license",
                        "message": "未找到有效许可证，请先激活许可证",
                        "upgrade_suggestion": "请购买或激活许可证以使用该功能"
                    }
                )

            # 检查许可证状态
            license_status = LicensePermissionService._extract_status(license_obj)
            if license_status != LicenseStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "inactive_license",
                        "message": f"许可证状态异常：{license_status.value}",
                        "upgrade_suggestion": "请联系管理员激活许可证"
                    }
                )

            # 检查是否过期
            if LicensePermissionService._is_expired(license_obj):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "expired_license",
                        "message": "许可证已过期",
                        "upgrade_suggestion": "请续费或重新购买许可证"
                    }
                )

            # 检查许可证类型是否在允许列表中
            license_type = LicensePermissionService._extract_license_type(license_obj)
            if license_type not in allowed_types:
                allowed_names = [t.value for t in allowed_types]
                current_type = license_type.value

                upgrade_suggestion = UPGRADE_SUGGESTIONS.get(
                    license_type,
                    f"当前功能需要以下许可证类型之一：{', '.join(allowed_names)}"
                )

                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "insufficient_license",
                        "message": f"当前许可证类型 ({current_type}) 不支持此功能",
                        "required_types": allowed_names,
                        "current_type": current_type,
                        "upgrade_suggestion": upgrade_suggestion
                    }
                )

            # 权限验证通过，执行业务逻辑
            return await func(*args, current_user=current_user, db=db, **kwargs)

        return wrapper
    return decorator


def require_feature(feature_name: str):
    """
    功能权限装饰器（基于权限矩阵）

    用法:
        @router.get("/ai/chat")
        @require_feature("ai_chat_assistant")
        async def ai_chat(...):
            ...

    Args:
        feature_name: 功能名称（需在 PERMISSION_MATRIX 中定义）
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db),
            **kwargs
        ):
            # 获取用户许可证
            license_service = LicensePermissionService(db)
            license_obj = await license_service.get_user_license(current_user.id)

            if not license_obj:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "no_license",
                        "message": "未找到有效许可证"
                    }
                )

            # 检查功能权限
            permission = license_service.check_feature_permission(
                feature_name,
                LicensePermissionService._extract_license_type(license_obj)
            )

            if not permission["allowed"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "feature_not_allowed",
                        "message": permission["reason"],
                        "upgrade_suggestion": permission["upgrade_suggestion"]
                    }
                )

            # 权限验证通过
            return await func(*args, current_user=current_user, db=db, **kwargs)

        return wrapper
    return decorator


# ============================================
# 依赖注入函数
# ============================================

async def check_license_permission(
    feature: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    依赖注入函数：检查功能权限

    用法:
        @router.get("/check-permission")
        async def check_my_permission(
            result: dict = Depends(check_license_permission("ai_chat"))
        ):
            return result
    """
    license_service = LicensePermissionService(db)
    return await license_service.verify_feature_access(current_user.id, feature)
