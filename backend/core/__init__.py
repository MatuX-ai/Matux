"""
MatuX 核心引擎

提供模块化懒加载架构的核心组件：
- ModuleSpec / ModuleState / ModuleTier: 模块数据结构
- ModuleLazyLoader: 懒加载引擎
- ActivationMiddleware: 路由激活中间件
- LazyTableManager: 数据库表延迟创建
- ModuleCircuitBreaker: 模块级熔断器
- ServiceDependencyManager: 依赖降级管理
"""

from .activation_middleware import ModuleActivationMiddleware
from .lazy_loader import (
    ModuleActivationError,
    ModuleLazyLoader,
    get_lazy_loader,
    init_lazy_loader,
)
from .lazy_tables import (
    LazyTableManager,
    get_lazy_table_manager,
    init_lazy_table_manager,
)
from .module_circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    ModuleCircuitBreaker,
    ModuleCircuitBreakerRegistry,
    get_breaker_registry,
    init_breaker_registry,
)
from .module_spec import ModuleSpec, ModuleState, ModuleTier
from .service_dependencies import (
    DisabledService,
    LocalTemplateResponder,
    MemoryCacheBackend,
    ReadOnlyMode,
    ServiceDependencyManager,
    get_service_manager,
    init_service_manager,
)

__all__ = [
    "ModuleSpec",
    "ModuleState",
    "ModuleTier",
    "ModuleLazyLoader",
    "ModuleActivationError",
    "get_lazy_loader",
    "init_lazy_loader",
    "ModuleActivationMiddleware",
    "LazyTableManager",
    "get_lazy_table_manager",
    "init_lazy_table_manager",
    "ServiceDependencyManager",
    "MemoryCacheBackend",
    "LocalTemplateResponder",
    "ReadOnlyMode",
    "DisabledService",
    "get_service_manager",
    "init_service_manager",
    "ModuleCircuitBreaker",
    "ModuleCircuitBreakerRegistry",
    "CircuitBreakerConfig",
    "CircuitBreakerOpenError",
    "CircuitState",
    "get_breaker_registry",
    "init_breaker_registry",
]
