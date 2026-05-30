"""
依赖注入工具模块
提供常用的依赖项注入函数
"""

from sqlalchemy.orm import Session

from models.user import User


def get_current_user_sync() -> User:
    """
    获取当前用户（同步版本）
    用于非异步上下文
    """
    # 这里需要实现同步版本的用户获取逻辑
    # 暂时抛出异常，因为大多数情况下应该使用异步版本
    raise NotImplementedError("请使用异步版本的get_current_user")


def get_sync_db() -> Session:
    """
    获取同步数据库会话
    """
    # 这里需要实现同步数据库会话获取逻辑
    # 暂时抛出异常
    raise NotImplementedError("请使用异步版本的get_db")
