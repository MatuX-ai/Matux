"""
数据库基础模块
提供Base类和其他数据库基础设施
"""

from sqlalchemy.ext.declarative import declarative_base

# 创建基类
Base = declarative_base()

# 导入注册表功能
from .module_registry import (
    DatabaseModuleRegistry, 
    DatabaseModule, 
    ModuleMetadata,
    AutoDiscovery,
    get_database_registry
)

from .registry_manager import (
    RegistryManager,
    ModelBasedModule,
    get_registry_manager,
    init_registry_manager
)

from pathlib import Path

# 自动创建examples目录
examples_dir = Path(__file__).parent / "examples"
examples_dir.mkdir(exist_ok=True)

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
]