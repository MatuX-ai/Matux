"""
数据库基础模块
提供Base类和其他数据库基础设施
"""

from .registry_manager import (
    RegistryManager,
    ModelBasedModule,
    get_registry_manager,
    init_registry_manager
)
from .module_registry import (
    DatabaseModuleRegistry,
    DatabaseModule,
    ModuleMetadata,
    AutoDiscovery,
    get_database_registry
)
import logging
from pathlib import Path

from sqlalchemy.ext.declarative import declarative_base

logger = logging.getLogger(__name__)

# 创建基类
Base = declarative_base()

# 导入注册表功能


def _ensure_examples_directory() -> None:
    """
    安全创建 examples 目录（延迟初始化，避免模块导入时的副作用）

    只有在需要时才创建目录，且不会因权限问题阻塞应用启动
    """
    try:
        examples_dir = Path(__file__).parent / "examples"
        if not examples_dir.exists():
            examples_dir.mkdir(exist_ok=True)
            logger.debug(f"创建 examples 目录: {examples_dir}")
    except PermissionError as e:
        logger.warning(f"无法创建 examples 目录（权限不足）: {e}")
    except Exception as e:
        logger.warning(f"创建 examples 目录失败: {e}")


# 延迟初始化：不在模块导入时创建目录
# 如需使用 examples 目录，调用 ensure_examples_directory()
def ensure_examples_directory() -> Path:
    """获取 examples 目录（不存在则创建）"""
    _ensure_examples_directory()
    return Path(__file__).parent / "examples"


__all__ = [
    # 基础类
    "Base",
    # 注册表核心
    "DatabaseModuleRegistry",
    "DatabaseModule",
    "ModuleMetadata",
    "AutoDiscovery",
    "get_database_registry",
    # 管理器
    "RegistryManager",
    "ModelBasedModule",
    "get_registry_manager",
    "init_registry_manager",
    # 工具函数
    "ensure_examples_directory",
]
