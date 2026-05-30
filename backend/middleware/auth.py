"""
认证中间件模块
提供用户认证相关的依赖注入函数
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.user import User
from utils.auth_utils import get_current_user_sync
from utils.database import get_db


def get_current_user(
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前登录用户

    Args:
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 认证失败时抛出
    """
    # 使用同步版本（适用于同步路由）
    # 对于异步路由，应该使用异步版本的依赖注入
    try:
        # 这里暂时返回一个模拟用户，实际应该从 token 中解析
        # TODO: 需要从 OAuth2 token 中解析用户信息
        return get_current_user_sync.__annotations__.get('return', User)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"认证失败：{str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# 为了兼容性，也提供一个简化的版本
def get_current_user_optional() -> Optional[User]:
    """
    获取当前用户（可选）
    如果未认证，返回 None 而不是抛出异常
    """
    try:
        return get_current_user()
    except HTTPException:
        return None
