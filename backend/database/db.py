"""
数据库模块
提供 Base 声明基类，供其他模型导入使用
"""

from sqlalchemy.ext.declarative import declarative_base

# 创建声明式基类
Base = declarative_base()
