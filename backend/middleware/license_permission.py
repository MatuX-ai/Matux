"""
基于许可证的权限控制系统
提供细粒度的功能访问控制和灵活的商业模式支持
"""

from functools import wraps
from datetime import datetime
from typing import List, Callable, Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from backend.models.license import LicenseType, License, LicenseStatus
from backend.database import get_db
from backend.core.security import get_current_user
from backend.models.user import User


# ============================================
# 权限矩阵定义
# ============================================

PERMISSION_MATRIX: Dict[str, Dict[LicenseType, bool]] = {
    # 基础功能（所有版本都可用）
    "course_management": {
        LicenseType.OPEN_SOURCE: True,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.TRIAL: True,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },
    "user_management": {
        LicenseType.OPEN_SOURCE: True,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.TRIAL: True,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },

    # AI 功能（仅付费版可用）
    "ai_course_generation": {
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },
    "ai_chat_assistant": {
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },
    "ai_code_completion": {
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },

    # 部署模式相关功能
    "offline_mode": {
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: False,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },
    "cloud_sync": {
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },
    "multi_tenant": {
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: False,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },

    # Token 计费功能
    "token_billing": {
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: True,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },
    "monthly_bonus_tokens": {
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },

    # 高级功能
    "advanced_analytics": {
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: True,
        LicenseType.EDUCATION: True,
        LicenseType.ENTERPRISE: True,
    },
    "priority_support": {
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: True,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },
    "custom_branding": {
        LicenseType.OPEN_SOURCE: False,
        LicenseType.WINDOWS_LOCAL: False,
        LicenseType.CLOUD_HOSTED: False,
        LicenseType.TRIAL: False,
        LicenseType.COMMERCIAL: False,
        LicenseType.EDUCATION: False,
        LicenseType.ENTERPRISE: True,
    },
}

# 升级建议映射
UPGRADE_SUGGESTIONS: Dict[LicenseType, str] = {
    LicenseType.OPEN_SOURCE: "升级到 Windows 本地版或云托管版以解锁 AI 功能和高级特性",
    LicenseType.TRIAL: "购买正式版以解锁完整功能（Windows 本地版/云托管版/企业版）",
    LicenseType.WINDOWS_LOCAL: "升级到云托管版以支持云端同步和多租户管理",
    LicenseType.CLOUD_HOSTED: "升级到企业定制版以获得离线模式和自定义品牌功能",
}


# ============================================
# 许可证服务类
# ============================================

class LicensePermissionService:
    """许可证权限管理服务"""

    def __init__(self, db: Session):
        self.db = db

    async def get_user_license(self, user_id: str) -> Optional[License]:
        """获取用户的有效许可证"""
        license_obj = self.db.query(License).filter(
            License.status == LicenseStatus.ACTIVE,
            License.is_active == True,
            # 这里假设 License 表有 user_id 字段，如果没有需要调整
            # 实际项目中可能需要通过 User.license_id 或其他方式关联
        ).first()

        return license_obj

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
        if license_obj.status != LicenseStatus.ACTIVE:
            return {
                "allowed": False,
                "reason": f"许可证状态异常：{license_obj.status.value}",
                "upgrade_suggestion": "请联系管理员激活许可证"
            }

        # 检查是否过期
        if license_obj.is_expired:
            return {
                "allowed": False,
                "reason": "许可证已过期",
                "upgrade_suggestion": "请续费或重新购买许可证"
            }

        # 检查功能权限
        permission_result = self.check_feature_permission(
            feature,
            license_obj.license_type
        )

        # 添加许可证类型信息
        permission_result["license_type"] = license_obj.license_type.value

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
            if license_obj.status != LicenseStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "inactive_license",
                        "message": f"许可证状态异常：{license_obj.status.value}",
                        "upgrade_suggestion": "请联系管理员激活许可证"
                    }
                )

            # 检查是否过期
            if license_obj.is_expired:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "expired_license",
                        "message": "许可证已过期",
                        "upgrade_suggestion": "请续费或重新购买许可证"
                    }
                )

            # 检查许可证类型是否在允许列表中
            if license_obj.license_type not in allowed_types:
                allowed_names = [t.value for t in allowed_types]
                current_type = license_obj.license_type.value

                upgrade_suggestion = UPGRADE_SUGGESTIONS.get(
                    license_obj.license_type,
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
                license_obj.license_type
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
