"""
认证相关的依赖项和工具函数
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from config.settings import settings
from models.user import User
from utils.database import get_db

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user_sync(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    同步版本的获取当前用户函数
    供多租户中间件等同步场景使用

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

        # 添加租户ID到payload中（如果存在）
        org_id: Optional[int] = payload.get("org_id")

    except JWTError:
        raise credentials_exception

    try:
        # 查询用户
        stmt = select(User).filter(User.username == username, User.is_active == True)
        result = db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        # 将租户ID附加到用户对象上（如果存在）
        if org_id:
            user.org_id = org_id

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"用户查询失败: {str(e)}",
        )


def create_access_token_sync(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    同步版本的创建访问令牌函数

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token_sync(token: str) -> Optional[dict]:
    """
    验证JWT token并返回payload

    Args:
        token: JWT token

    Returns:
        Optional[dict]: payload字典，如果验证失败返回None
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


# 便捷别名
get_current_user = get_current_user_sync
