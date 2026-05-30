"""
数据库数据模块注册表

提供统一的数据库模块注册、发现、生命周期管理机制
支持热插拔式模块扩展和多租户场景下的模块隔离
"""

import importlib
import inspect
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from sqlalchemy.ext.declarative import DeclarativeMeta

logger = logging.getLogger(__name__)


@dataclass
class ModuleMetadata:
    """模块元数据"""
    name: str
    module_class: Type[DeclarativeMeta]
    table_name: str
    category: str = "default"
    version: str = "1.0.0"
    dependencies: List[str] = field(default_factory=list)
    description: str = ""
    is_active: bool = True
    created_at: str = field(default_factory=lambda: "")


class DatabaseModule(ABC):
    """数据库模块抽象基类"""
    
    def __init__(self):
        self._initialized = False
    
    @property
    @abstractmethod
    def module_name(self) -> str:
        """模块名称"""
        pass
    
    @property
    @abstractmethod
    def table_name(self) -> str:
        """数据库表名"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> ModuleMetadata:
        """获取模块元数据"""
        pass
    
    async def initialize(self) -> None:
        """初始化模块"""
        self._initialized = True
        logger.info(f"模块 {self.module_name} 初始化完成")
    
    async def cleanup(self) -> None:
        """清理模块资源"""
        self._initialized = False
        logger.info(f"模块 {self.module_name} 清理完成")
    
    @property
    def is_initialized(self) -> bool:
        """模块是否已初始化"""
        return self._initialized


class DatabaseModuleRegistry:
    """数据库数据模块注册表"""
    
    def __init__(self):
        self._modules: Dict[str, ModuleMetadata] = {}
        self._module_instances: Dict[str, DatabaseModule] = {}
        self._categories: Dict[str, List[str]] = defaultdict(list)
        self._table_index: Dict[str, str] = {}  # table_name -> module_name
        self._initialized = False
    
    def register_module(self, 
                       module_class: Type[DeclarativeMeta], 
                       category: str = "default",
                       version: str = "1.0.0",
                       dependencies: List[str] = None,
                       description: str = "") -> None:
        """注册数据库模块"""
        try:
            # 提取表名和模块信息
            table_name = getattr(module_class, '__tablename__', str(module_class.__name__).lower())
            module_name = table_name
            
            # 检查是否已注册
            if module_name in self._modules:
                logger.warning(f"模块 {module_name} 已存在，跳过注册")
                return
            
            # 创建元数据
            metadata = ModuleMetadata(
                name=module_name,
                module_class=module_class,
                table_name=table_name,
                category=category,
                version=version,
                dependencies=dependencies or [],
                description=description,
                is_active=True
            )
            
            # 注册到各个索引
            self._modules[module_name] = metadata
            self._categories[category].append(module_name)
            self._table_index[table_name] = module_name
            
            logger.info(f"成功注册模块: {module_name} (表: {table_name}, 分类: {category})")
            
        except Exception as e:
            logger.error(f"注册模块失败 {module_class}: {str(e)}")
            raise
    
    def register_module_instance(self, module_instance: DatabaseModule) -> None:
        """注册模块实例"""
        module_name = module_instance.module_name
        
        if module_name in self._module_instances:
            logger.warning(f"模块实例 {module_name} 已存在，将被覆盖")
        
        self._module_instances[module_name] = module_instance
        logger.info(f"成功注册模块实例: {module_name}")
    
    def unregister_module(self, module_name: str) -> bool:
        """注销模块"""
        if module_name not in self._modules:
            logger.warning(f"模块 {module_name} 未找到")
            return False
        
        metadata = self._modules[module_name]
        
        # 从所有索引中移除
        del self._modules[module_name]
        self._categories[metadata.category].remove(module_name)
        del self._table_index[metadata.table_name]
        
        # 清理实例
        if module_name in self._module_instances:
            del self._module_instances[module_name]
        
        logger.info(f"成功注销模块: {module_name}")
        return True
    
    def get_module(self, module_name: str) -> Optional[ModuleMetadata]:
        """获取模块元数据"""
        return self._modules.get(module_name)
    
    def get_module_class(self, module_name: str) -> Optional[Type[DeclarativeMeta]]:
        """获取模块类"""
        metadata = self.get_module(module_name)
        return metadata.module_class if metadata else None
    
    def get_module_instance(self, module_name: str) -> Optional[DatabaseModule]:
        """获取模块实例"""
        return self._module_instances.get(module_name)
    
    def get_module_by_table(self, table_name: str) -> Optional[ModuleMetadata]:
        """通过表名获取模块"""
        module_name = self._table_index.get(table_name)
        return self.get_module(module_name) if module_name else None
    
    def list_modules(self, category: str = None) -> List[ModuleMetadata]:
        """列出所有模块"""
        if category:
            module_names = self._categories.get(category, [])
            return [self._modules[name] for name in module_names]
        return list(self._modules.values())
    
    def list_categories(self) -> List[str]:
        """列出所有分类"""
        return list(self._categories.keys())
    
    def get_modules_by_category(self, category: str) -> List[ModuleMetadata]:
        """获取指定分类的模块"""
        return self.list_modules(category)
    
    def activate_module(self, module_name: str) -> bool:
        """激活模块"""
        if module_name in self._modules:
            self._modules[module_name].is_active = True
            logger.info(f"模块 {module_name} 已激活")
            return True
        return False
    
    def deactivate_module(self, module_name: str) -> bool:
        """停用模块"""
        if module_name in self._modules:
            self._modules[module_name].is_active = False
            logger.info(f"模块 {module_name} 已停用")
            return True
        return False
    
    async def initialize_all(self) -> None:
        """初始化所有注册的模块实例"""
        initialization_order = self._calculate_init_order()
        
        for module_name in initialization_order:
            if module_name in self._module_instances:
                try:
                    await self._module_instances[module_name].initialize()
                except Exception as e:
                    logger.error(f"初始化模块 {module_name} 失败: {str(e)}")
        
        self._initialized = True
        logger.info("所有模块初始化完成")
    
    async def cleanup_all(self) -> None:
        """清理所有模块实例"""
        for module_name, instance in self._module_instances.items():
            try:
                await instance.cleanup()
            except Exception as e:
                logger.error(f"清理模块 {module_name} 失败: {str(e)}")
        
        self._initialized = False
        logger.info("所有模块清理完成")
    
    def _calculate_init_order(self) -> List[str]:
        """计算模块初始化顺序（拓扑排序）"""
        # 简化的依赖解析，实际项目中可使用更复杂的拓扑排序算法
        order = []
        visited = set()
        
        def visit(module_name):
            if module_name in visited:
                return
            visited.add(module_name)
            
            metadata = self._modules.get(module_name)
            if metadata:
                for dep in metadata.dependencies:
                    if dep in self._modules:
                        visit(dep)
            
            order.append(module_name)
        
        for module_name in self._modules:
            if module_name not in visited:
                visit(module_name)
        
        return order
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        active_modules = sum(1 for m in self._modules.values() if m.is_active)
        
        return {
            "total_modules": len(self._modules),
            "active_modules": active_modules,
            "inactive_modules": len(self._modules) - active_modules,
            "total_instances": len(self._module_instances),
            "categories": len(self._categories),
            "tables": len(self._table_index),
            "initialized": self._initialized
        }


class AutoDiscovery:
    """自动发现模块工具"""
    
    @staticmethod
    def discover_models_from_package(package_path: Union[str, Path]) -> List[Type[DeclarativeMeta]]:
        """从包路径自动发现模型类"""
        models = []
        
        try:
            if isinstance(package_path, str):
                package_path = Path(package_path)
            
            # 遍历Python文件
            for py_file in package_path.rglob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                
                # 动态导入模块
                module_path = str(py_file.relative_to(package_path.parent)).replace("/", ".").replace("\\", ".").replace(".py", "")
                
                try:
                    module = importlib.import_module(module_path)
                    
                    # 查找DeclarativeMeta子类
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, DeclarativeMeta) and 
                            obj != DeclarativeMeta and
                            hasattr(obj, '__tablename__')):
                            models.append(obj)
                            
                except Exception as e:
                    logger.debug(f"导入模块 {module_path} 失败: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"自动发现模型失败: {str(e)}")
        
        return models


# 全局注册表实例
_registry: Optional[DatabaseModuleRegistry] = None

def get_database_registry() -> DatabaseModuleRegistry:
    """获取全局数据库注册表实例"""
    global _registry
    if _registry is None:
        _registry = DatabaseModuleRegistry()
    return _registry


def initialize_registry_from_models() -> DatabaseModuleRegistry:
    """从现有models包初始化注册表"""
    registry = get_database_registry()
    
    # 清空现有注册
    registry._modules.clear()
    registry._categories.clear()
    registry._table_index.clear()
    registry._module_instances.clear()
    
    # 自动发现并注册所有模型
    models_package = Path(__file__).parent.parent / "models"
    discovered_models = AutoDiscovery.discover_models_from_package(models_package)
    
    for model_class in discovered_models:
        registry.register_module(model_class)
    
    logger.info(f"从models包自动注册了 {len(discovered_models)} 个模块")
    return registry