"""
数据库模块注册表管理器

提供高级的注册表管理功能，包括配置驱动注册、健康检查、迁移管理等
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加backend目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from .module_registry import (
    DatabaseModuleRegistry, 
    DatabaseModule, 
    ModuleMetadata,
    get_database_registry
)

# 现在可以安全导入settings
from config.settings import settings

logger = logging.getLogger(__name__)


class ModelBasedModule(DatabaseModule):
    """基于SQLAlchemy模型的数据库模块实现"""
    
    def __init__(self, model_class):
        super().__init__()
        self._model_class = model_class
        self._table_name = getattr(model_class, '__tablename__', model_class.__name__.lower())
    
    @property
    def module_name(self) -> str:
        return self._table_name
    
    @property
    def table_name(self) -> str:
        return self._table_name
    
    def get_metadata(self) -> ModuleMetadata:
        registry = get_database_registry()
        return registry.get_module(self.module_name)
    
    async def initialize(self) -> None:
        """初始化模型模块"""
        # 这里可以添加模型特定的初始化逻辑
        # 例如：创建索引、验证表结构等
        logger.info(f"初始化模型模块: {self.module_name}")
        await super().initialize()
    
    def get_model_class(self):
        """获取模型类"""
        return self._model_class


class RegistryManager:
    """注册表管理器"""
    
    def __init__(self):
        self.registry = get_database_registry()
        self._health_check_enabled = True
        self._auto_discovery_enabled = True
    
    async def initialize_registry(self, auto_discover: bool = True) -> None:
        """初始化注册表"""
        logger.info("开始初始化数据库模块注册表...")
        
        if auto_discover:
            # 自动发现并注册所有模型
            from .module_registry import initialize_registry_from_models
            initialize_registry_from_models()
        
        # 注册模型实例
        await self._register_model_instances()
        
        # 初始化所有模块
        await self.registry.initialize_all()
        
        logger.info("数据库模块注册表初始化完成")
    
    async def _register_model_instances(self) -> None:
        """为每个模型注册对应的模块实例"""
        modules = self.registry.list_modules()
        
        for metadata in modules:
            if metadata.name not in self.registry._module_instances:
                model_instance = ModelBasedModule(metadata.module_class)
                self.registry.register_module_instance(model_instance)
    
    async def health_check(self) -> Dict[str, Any]:
        """执行注册表健康检查"""
        if not self._health_check_enabled:
            return {"status": "disabled"}
        
        health_status = {
            "registry_status": "healthy" if self.registry._initialized else "uninitialized",
            "stats": self.registry.get_registry_stats(),
            "modules_status": [],
            "issues": []
        }
        
        # 检查每个模块的状态
        for module_name in self.registry._modules:
            module_status = {
                "name": module_name,
                "registered": True,
                "instance_created": module_name in self.registry._module_instances,
                "initialized": False,
                "active": self.registry._modules[module_name].is_active
            }
            
            if module_name in self.registry._module_instances:
                instance = self.registry._module_instances[module_name]
                module_status["initialized"] = instance.is_initialized
            
            health_status["modules_status"].append(module_status)
            
            # 收集问题
            if not module_status["instance_created"]:
                health_status["issues"].append(f"模块 {module_name} 未创建实例")
            elif not module_status["initialized"]:
                health_status["issues"].append(f"模块 {module_name} 未初始化")
        
        # 确定整体状态
        if health_status["issues"]:
            health_status["registry_status"] = "degraded"
        
        return health_status
    
    def get_module_info(self, module_name: str) -> Optional[Dict[str, Any]]:
        """获取模块详细信息"""
        metadata = self.registry.get_module(module_name)
        if not metadata:
            return None
        
        instance = self.registry.get_module_instance(module_name)
        
        return {
            "name": metadata.name,
            "table_name": metadata.table_name,
            "category": metadata.category,
            "version": metadata.version,
            "description": metadata.description,
            "dependencies": metadata.dependencies,
            "is_active": metadata.is_active,
            "has_instance": instance is not None,
            "is_initialized": instance.is_initialized if instance else False,
            "class_name": metadata.module_class.__name__
        }
    
    def list_modules_by_category(self) -> Dict[str, List[Dict[str, Any]]]:
        """按分类列出所有模块信息"""
        result = {}
        categories = self.registry.list_categories()
        
        for category in categories:
            modules = self.registry.get_modules_by_category(category)
            result[category] = []
            
            for metadata in modules:
                info = self.get_module_info(metadata.name)
                if info:
                    result[category].append(info)
        
        return result
    
    async def reload_registry(self) -> None:
        """重新加载注册表"""
        logger.info("开始重新加载注册表...")
        
        # 清理现有注册表
        await self.registry.cleanup_all()
        
        # 重新初始化
        await self.initialize_registry(auto_discover=self._auto_discovery_enabled)
        
        logger.info("注册表重新加载完成")
    
    def enable_auto_discovery(self, enabled: bool = True) -> None:
        """启用/禁用自动发现"""
        self._auto_discovery_enabled = enabled
        logger.info(f"自动发现已{'启用' if enabled else '禁用'}")
    
    def enable_health_check(self, enabled: bool = True) -> None:
        """启用/禁用健康检查"""
        self._health_check_enabled = enabled
        logger.info(f"健康检查已{'启用' if enabled else '禁用'}")
    
    def get_registry_config(self) -> Dict[str, Any]:
        """获取注册表配置"""
        return {
            "auto_discovery_enabled": self._auto_discovery_enabled,
            "health_check_enabled": self._health_check_enabled,
            "initialized": self.registry._initialized,
            "stats": self.registry.get_registry_stats()
        }


# 全局管理器实例
_manager: Optional[RegistryManager] = None

def get_registry_manager() -> RegistryManager:
    """获取全局注册表管理器实例"""
    global _manager
    if _manager is None:
        _manager = RegistryManager()
    return _manager


def init_registry_manager() -> RegistryManager:
    """初始化注册表管理器"""
    manager = get_registry_manager()
    return manager