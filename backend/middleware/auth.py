"""
认证中间件模块
提供用户认证相关的依赖注入函数
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from models.user import User
from utils.database import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/signin")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前登录用户（异步版本）

    Args:
        token: JWT token
        db: 数据库会话

    Returns:
        User: 当前用户对象

    Raises:
        HTTPException: 认证失败时抛出
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    try:
        # 查询用户
        from sqlalchemy import select
        stmt = select(User).filter(User.username ==
                                   username, User.is_active == True)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"认证失败：{str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# 为了兼容性，也提供一个简化的版本
async def get_current_user_optional() -> Optional[User]:
    """
    获取当前用户（可选）
    如果未认证，返回 None 而不是抛出异常
    """
    try:
        return await get_current_user()
    except HTTPException:
        return None
