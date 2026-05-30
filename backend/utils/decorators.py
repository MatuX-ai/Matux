"""
权限校验装饰器
实现基于角色和权限的访问控制装饰器
"""

import functools
import logging
from typing import Callable, List, Optional, Union, Dict, Any, Tuple
from functools import wraps
from sqlalchemy.orm import Session

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserRole
from services.permission_service import permission_service
from utils.database import get_async_db

# 循环导入问题：不在这里导入get_current_user，改为在函数内部导入

logger = logging.getLogger(__name__)


def require_role(roles: Union[UserRole, List[UserRole]], require_all: bool = False):
    """
    角色权限校验装饰器

    Args:
        roles: 需要的角色（单个或列表）
        require_all: 是否需要满足所有角色（默认False，满足任一即可）

    Example:
        @require_role(UserRole.ADMIN)
        @require_role([UserRole.ADMIN, UserRole.ORG_ADMIN])
        @require_role([UserRole.ADMIN, UserRole.ORG_ADMIN], require_all=True)
    """
    if isinstance(roles, UserRole):
        roles = [roles]

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户
            current_user = kwargs.get("current_user")
            if not current_user:
                # 尝试从参数中获取用户
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未提供身份认证信息",
                )

            # 检查角色权限
            user_role_enum = current_user.role
            if require_all:
                # 需要满足所有角色
                if not all(role == user_role_enum for role in roles):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"需要所有角色: {[role.value for role in roles]}",
                    )
            else:
                # 满足任一角色即可
                if not any(role == user_role_enum for role in roles):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"需要以下任一角色: {[role.value for role in roles]}",
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_permission(permissions: Union[str, List[str]], require_all: bool = True):
    """
    权限校验装饰器

    Args:
        permissions: 需要的权限代码（单个或列表）
        require_all: 是否需要满足所有权限（默认True）

    Example:
        @require_permission("user.read")
        @require_permission(["user.read", "user.write"])
        @require_permission(["user.read", "user.write"], require_all=False)
    """
    if isinstance(permissions, str):
        permissions = [permissions]

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户和数据库会话
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")

            # 如果没有传入db参数，创建新的数据库会话
            if not db:
                async for db_session in get_async_db():
                    db = db_session
                    break

            if not current_user:
                # 尝试从参数中获取用户
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未提供身份认证信息",
                )

            # 检查权限
            if require_all:
                # 需要满足所有权限
                has_all = await permission_service.check_user_has_all_permissions(
                    current_user.id, permissions, db
                )
                if not has_all:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少必要权限: {permissions}",
                    )
            else:
                # 满足任一权限即可
                has_any = await permission_service.check_user_has_any_permission(
                    current_user.id, permissions, db
                )
                if not has_any:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"需要以下任一权限: {permissions}",
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_role_or_permission(
    roles: Optional[List[UserRole]] = None, permissions: Optional[List[str]] = None
):
    """
    角色或权限任一满足即可的装饰器

    Args:
        roles: 可接受的角色列表
        permissions: 可接受的权限列表

    Example:
        @require_any_role_or_permission(
            roles=[UserRole.ADMIN, UserRole.ORG_ADMIN],
            permissions=["user.manage", "user.read"]
        )
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取当前用户和数据库会话
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")

            # 如果没有传入db参数，创建新的数据库会话
            if not db:
                async for db_session in get_async_db():
                    db = db_session
                    break

            if not current_user:
                # 尝试从参数中获取用户
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未提供身份认证信息",
                )

            # 检查角色
            if roles:
                user_role_enum = current_user.role
                if any(role == user_role_enum for role in roles):
                    return await func(*args, **kwargs)

            # 检查权限
            if permissions:
                has_any_permission = (
                    await permission_service.check_user_has_any_permission(
                        current_user.id, permissions, db
                    )
                )
                if has_any_permission:
                    return await func(*args, **kwargs)

            # 两者都不满足
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足：需要指定角色或权限",
            )

        return wrapper

    return decorator


def require_superuser():
    """
    超级管理员权限校验装饰器

    Example:
        @require_superuser()
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")

            if not current_user:
                # 尝试从参数中获取用户
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未提供身份认证信息",
                )

            if not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限"
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def conditional_require_permission(
    condition_field: str,
    permission_mapping: dict,
    default_permission: Optional[str] = None,
):
    """
    根据条件动态要求权限的装饰器

    Args:
        condition_field: 条件字段名（在kwargs中的键名）
        permission_mapping: 条件值到权限的映射
        default_permission: 默认权限（当条件不匹配时使用）

    Example:
        @conditional_require_permission(
            condition_field="action",
            permission_mapping={
                "create": "user.create",
                "update": "user.update",
                "delete": "user.delete"
            },
            default_permission="user.read"
        )
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 获取条件值
            condition_value = kwargs.get(condition_field)

            # 确定需要的权限
            required_permission = permission_mapping.get(
                condition_value, default_permission
            )

            if not required_permission:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无法确定所需权限: {condition_field}={condition_value}",
                )

            # 获取当前用户和数据库会话
            current_user = kwargs.get("current_user")
            db = kwargs.get("db")

            # 如果没有传入db参数，创建新的数据库会话
            if not db:
                async for db_session in get_async_db():
                    db = db_session
                    break

            if not current_user:
                # 尝试从参数中获取用户
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未提供身份认证信息",
                )

            # 检查权限
            has_permission = await permission_service.check_user_permission(
                current_user.id, required_permission, db
            )

            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少必要权限: {required_permission}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# 便捷的组合装饰器
def admin_required():
    """管理员权限要求（兼容旧版本）"""
    return require_role([UserRole.ADMIN, UserRole.ORG_ADMIN])


def org_admin_required():
    """企业管理员权限要求"""
    return require_role(UserRole.ORG_ADMIN)


def premium_user_required():
    """高级用户权限要求"""
    return require_role([UserRole.PREMIUM, UserRole.ADMIN, UserRole.ORG_ADMIN])


# 依赖注入版本的权限校验（适用于FastAPI路由）
async def get_current_user_with_permission(
    permission: str, db: AsyncSession = Depends(get_async_db)
) -> User:
    # 延迟导入避免循环依赖
    from routes.auth_routes import get_current_user

    current_user: User = await get_current_user()
    """
    获取具有指定权限的当前用户（依赖注入版本）

    Args:
        permission: 所需权限代码
        current_user: 当前用户（由get_current_user提供）
        db: 数据库会话

    Returns:
        User: 通过权限校验的用户
    """
    has_permission = await permission_service.check_user_permission(
        current_user.id, permission, db
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"缺少必要权限: {permission}"
        )

    return current_user


async def get_current_user_with_role(role: UserRole) -> User:
    # 延迟导入避免循环依赖
    from routes.auth_routes import get_current_user

    current_user: User = await get_current_user()
    """
    获取具有指定角色的当前用户（依赖注入版本）

    Args:
        role: 所需角色
        current_user: 当前用户（由 get_current_user 提供）

    Returns:
        User: 通过角色校验的用户
    """
    if current_user.role != role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=f"需要角色：{role.value}"
        )


class TokenBillingDecorator:
    """Token 计费装饰器类"""

    def __init__(self, token_service):
        """
        初始化装饰器

        Args:
            token_service: TokenService 实例
        """
        self.token_service = token_service
        self.billing_enabled = True  # 降级开关

    def disable_billing(self):
        """禁用计费（降级模式）"""
        self.billing_enabled = False
        logger.warning("Token 计费已禁用 - 降级模式")

    def enable_billing(self):
        """启用计费（正常模式）"""
        self.billing_enabled = True
        logger.info("Token 计费已启用 - 正常模式")

    def consume_tokens(
        self,
        usage_type: str,
        estimate_func: Optional[Callable[..., int]] = None,
        fixed_amount: Optional[int] = None,
        usage_description: Optional[str] = None,
        resource_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        allow_insufficient_balance: bool = False
    ):
        """
        Token 消费装饰器

        Args:
            usage_type: 使用类型 (ai_teacher, course_generation, etc.)
            estimate_func: 预估 Token 数量的函数 (接收被装饰函数的参数)
            fixed_amount: 固定 Token 数量 (与 estimate_func 二选一)
            usage_description: 使用描述
            resource_id: 资源 ID
            resource_type: 资源类型
            allow_insufficient_balance: 余额不足时是否允许继续执行

        Returns:
            装饰器函数
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 获取 user_id (假设第一个参数或关键字参数包含 user_id)
                user_id = kwargs.get('user_id') or (
                    args[1] if len(args) > 1 else None)

                if not user_id:
                    logger.warning(
                        f"{func.__name__}: 无法获取 user_id，跳过 Token 检查")
                    return await func(*args, **kwargs)

                # 计算 Token 消耗量
                if fixed_amount is not None:
                    token_amount = fixed_amount
                elif estimate_func:
                    try:
                        token_amount = estimate_func(*args, **kwargs)
                    except Exception as e:
                        logger.error(f"{func.__name__}: Token 预估失败：{e}")
                        token_amount = 10  # 默认最小值
                else:
                    token_amount = 10  # 默认值

                # 检查计费是否启用
                if not self.billing_enabled:
                    logger.debug(f"{func.__name__}: 计费已禁用，跳过 Token 检查")
                    return await func(*args, **kwargs)

                # 检查 Token 余额
                balance = self.token_service.get_or_create_user_balance(
                    user_id)

                if balance.remaining_tokens < token_amount:
                    logger.warning(
                        f"用户 {user_id} Token 余额不足："
                        f"剩余 {balance.remaining_tokens}, 需要 {token_amount}"
                    )

                    if not allow_insufficient_balance:
                        # 抛出异常或返回错误
                        raise HTTPException(
                            status_code=402,
                            detail={
                                "code": "INSUFFICIENT_TOKENS",
                                "message": f"Token 余额不足，当前剩余：{balance.remaining_tokens}，需要：{token_amount}",
                                "required": token_amount,
                                "available": balance.remaining_tokens,
                                "usage_type": usage_type
                            }
                        )
                    else:
                        # 允许执行但不扣费（记录警告）
                        logger.warning(
                            f"用户 {user_id} Token 不足但仍允许执行：{func.__name__}")

                # 执行原函数
                try:
                    result = await func(*args, **kwargs)

                    # 成功后扣费
                    success, message = self.token_service.consume_tokens(
                        user_id=user_id,
                        token_amount=token_amount,
                        usage_type=usage_type,
                        usage_description=usage_description or func.__name__,
                        resource_id=resource_id,
                        resource_type=resource_type
                    )

                    if not success:
                        logger.error(f"{func.__name__}: Token 扣费失败：{message}")

                    # 将扣费信息添加到结果中
                    if isinstance(result, dict):
                        result['billing'] = {
                            'tokens_consumed': token_amount,
                            'remaining_balance': balance.remaining_tokens - token_amount,
                            'usage_type': usage_type
                        }

                    return result

                except Exception as e:
                    logger.error(f"{func.__name__}: 执行失败，不扣费：{e}")
                    raise

            return wrapper
        return decorator

    def check_balance_only(self, min_balance: int = 0):
        """
        仅检查余额的装饰器（不扣费）

        Args:
            min_balance: 最低余额要求
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                user_id = kwargs.get('user_id') or (
                    args[1] if len(args) > 1 else None)

                if not user_id:
                    return await func(*args, **kwargs)

                if not self.billing_enabled:
                    return await func(*args, **kwargs)

                balance = self.token_service.get_or_create_user_balance(
                    user_id)

                if balance.remaining_tokens < min_balance:
                    raise HTTPException(
                        status_code=402,
                        detail={
                            "code": "INSUFFICIENT_TOKENS",
                            "message": f"Token 余额不足，当前剩余：{balance.remaining_tokens}，最低要求：{min_balance}",
                            "required": min_balance,
                            "available": balance.remaining_tokens
                        }
                    )

                return await func(*args, **kwargs)

            return wrapper
        return decorator


def create_token_billing_decorator(db_session_getter: Callable[[], Session]):
    """
    创建 Token 计费装饰器的工厂函数

    Args:
        db_session_getter: 获取数据库会话的函数

    Returns:
        TokenBillingDecorator 实例
    """
    from services.token_service import TokenService

    def get_decorator() -> TokenBillingDecorator:
        db = db_session_getter()
        token_service = TokenService(db)
        return TokenBillingDecorator(token_service)

    return get_decorator

    return current_user
