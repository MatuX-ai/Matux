"""
数据库表延迟创建管理器

核心职责：
1. 管理模块与数据库表的映射关系
2. 支持模块激活时按需创建表
3. 支持表结构版本升级
4. 启动时仅创建核心表
"""

import asyncio
import importlib
import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class LazyTableManager:
    """
    数据库表延迟创建管理器

    将 create_db_and_tables() 的全量建表拆分为：
    - 启动时：仅创建核心模块的表
    - 模块激活时：按需创建该模块依赖的表
    - 升级时：按需执行表结构迁移
    """

    def __init__(self):
        # 模块名 → 需要创建的 ORM Model 类全路径列表
        self._module_tables: Dict[str, List[str]] = {}

        # 已创建的表名集合
        self._created_tables: Set[str] = set()

        # 建表锁（防止并发重复创建）
        self._table_locks: Dict[str, asyncio.Lock] = {}

        # 全局建表锁
        self._global_lock = asyncio.Lock()

    def register_module_tables(
        self, module_name: str, model_class_paths: List[str]
    ) -> None:
        """
        注册模块的数据库表映射

        Args:
            module_name: 模块名称
            model_class_paths: ORM Model 类全路径列表
                例如: ["models.course.Course", "models.course.Material"]
        """
        self._module_tables[module_name] = model_class_paths
        logger.debug(
            f"📋 注册表映射: {module_name} → {len(model_class_paths)} 个模型"
        )

    def register_many(
        self, mappings: Dict[str, List[str]]
    ) -> None:
        """批量注册模块表映射"""
        for module_name, model_paths in mappings.items():
            self.register_module_tables(module_name, model_paths)

    async def create_tables_for_module(self, module_name: str) -> bool:
        """
        为指定模块创建数据库表

        Args:
            module_name: 模块名称

        Returns:
            True 表示创建成功，False 表示跳过（已创建或无注册）
        """
        model_paths = self._module_tables.get(module_name)
        if not model_paths:
            logger.debug(f"模块 {module_name} 无注册的数据库表")
            return False

        # 过滤已创建的表
        pending_paths = [
            p for p in model_paths if p not in self._created_tables
        ]
        if not pending_paths:
            logger.debug(f"模块 {module_name} 的表已全部创建")
            return True

        # 获取或创建模块锁
        if module_name not in self._table_locks:
            self._table_locks[module_name] = asyncio.Lock()

        async with self._table_locks[module_name]:
            # 双重检查
            pending_paths = [
                p for p in model_paths if p not in self._created_tables
            ]
            if not pending_paths:
                return True

            try:
                await self._do_create_tables(module_name, pending_paths)
                return True
            except Exception as e:
                logger.error(f"❌ 模块 {module_name} 表创建失败: {e}")
                raise

    async def _do_create_tables(
        self, module_name: str, model_paths: List[str]
    ) -> None:
        """
        实际执行表创建

        导入 model 类并调用其 metadata.create_all()
        """
        from utils.database import get_engine, Base

        engine = await get_engine()
        created_count = 0

        for path in model_paths:
            if path in self._created_tables:
                continue

            try:
                # 动态导入 model 类
                model_class = self._import_model_class(path)

                if model_class is not None:
                    # 获取该 model 的 metadata 并创建表
                    table_name = getattr(
                        model_class, "__tablename__", path.split(".")[-1]
                    )
                    async with engine.begin() as conn:
                        await conn.run_sync(
                            model_class.__table__.create,
                            checkfirst=True,
                        )
                    self._created_tables.add(path)
                    created_count += 1
                    logger.debug(f"✅ 表创建成功: {table_name} ({path})")

            except Exception as e:
                logger.warning(
                    f"⚠️  表创建跳过: {path} - "
                    f"{type(e).__name__}: {e}"
                )

        if created_count > 0:
            logger.info(
                f"📦 模块 {module_name} 创建了 {created_count} 个表"
            )

    def _import_model_class(self, class_path: str) -> Any:
        """
        动态导入 ORM Model 类

        Args:
            class_path: 类全路径，例如 "models.course.Course"

        Returns:
            导入的类，失败返回 None
        """
        try:
            parts = class_path.rsplit(".", 1)
            if len(parts) != 2:
                logger.warning(f"无效的 model 路径: {class_path}")
                return None

            module_path, class_name = parts
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name, None)

            if cls is None:
                logger.warning(
                    f"类 {class_name} 在模块 {module_path} 中不存在"
                )
                return None

            return cls

        except ImportError as e:
            logger.warning(f"导入失败 {class_path}: {e}")
            return None
        except Exception as e:
            logger.warning(f"导入异常 {class_path}: {e}")
            return None

    async def create_core_tables(self, core_module_names: List[str]) -> None:
        """
        启动时仅创建核心模块的表

        Args:
            core_module_names: 核心模块名列表
        """
        logger.info(
            f"🔧 创建核心数据库表: {len(core_module_names)} 个模块"
        )

        for name in core_module_names:
            try:
                await self.create_tables_for_module(name)
            except Exception as e:
                logger.warning(f"核心表创建跳过: {name} - {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取表管理统计信息"""
        total_registered = sum(
            len(tables) for tables in self._module_tables.values()
        )
        return {
            "modules_registered": len(self._module_tables),
            "tables_registered": total_registered,
            "tables_created": len(self._created_tables),
            "tables_pending": total_registered - len(self._created_tables),
            "created_table_paths": sorted(self._created_tables),
        }

    @property
    def module_table_map(self) -> Dict[str, List[str]]:
        """获取模块→表映射（只读）"""
        return dict(self._module_tables)


# ==================== 全局实例 ====================

_manager_instance: Optional[LazyTableManager] = None


def get_lazy_table_manager() -> LazyTableManager:
    """获取全局 LazyTableManager 实例"""
    if _manager_instance is None:
        raise RuntimeError(
            "LazyTableManager 尚未初始化，请先调用 init_lazy_table_manager()"
        )
    return _manager_instance


def init_lazy_table_manager() -> LazyTableManager:
    """初始化全局 LazyTableManager 实例"""
    global _manager_instance
    _manager_instance = LazyTableManager()
    logger.info("🔧 LazyTableManager 已初始化")
    return _manager_instance
