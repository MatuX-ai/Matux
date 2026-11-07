"""
数据库 Session 基类（education 模型专用）

背景
----
``backend/education/models/{student,teacher,schedule}.py`` 都执行
``from database.session_base import Base``，但该模块在 origin/main 上从未存在，
导致这 3 个 education 模型 import 时直接抛 ``ModuleNotFoundError``。

本文件补齐这个缺失模块，使 education 模型可以正常 import。

设计约束
--------
* 只补「缺失的模块」，不改任何业务实现；
* 使用**独立**的 declarative Base，不并入 ``database/__init__.py`` 的 Base ——
  统一 Base 属于 L1（MetaData 共享）范畴，不在本次修复范围内；
* 因此 education 模型里指向 ``users`` / ``courses`` 等其它 Base 的外键与
  relationship，在 ``configure_mappers()`` 阶段仍无法解析 —— 这同样是 L1
  范畴的已知边界，本模块只保证 import 期不再失败。
"""

from sqlalchemy.ext.declarative import declarative_base

# 创建基类
Base = declarative_base()
