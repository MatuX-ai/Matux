"""
模块规格定义

定义模块懒加载架构所需的核心数据结构：
- ModuleState: 模块生命周期状态
- ModuleTier: 模块优先级层级
- ModuleSpec: 模块规格描述
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ModuleState(str, Enum):
    """模块生命周期状态"""

    UNLOADED = "unloaded"       # 未加载（仅注册）
    LOADING = "loading"         # 加载中
    ACTIVE = "active"           # 运行中
    DEGRADED = "degraded"       # 降级运行
    FAILED = "failed"           # 加载失败
    DISABLED = "disabled"       # 已禁用

    def is_available(self) -> bool:
        """模块是否可用（active 或 degraded）"""
        return self in (ModuleState.ACTIVE, ModuleState.DEGRADED)


class ModuleTier(int, Enum):
    """模块优先级层级"""

    TIER_0_CORE = 0        # 核心层：启动必须，< 3 秒
    TIER_1_HIGH = 1        # 高优先级：后台预加载，< 10 秒
    TIER_2_ON_DEMAND = 2   # 按需激活：首次请求时，< 2 秒
    TIER_3_DELAYED = 3     # 延迟激活：用户主动触发

    @property
    def description(self) -> str:
        descriptions = {
            0: "核心层（启动即加载）",
            1: "高优先级（后台预加载）",
            2: "按需激活（首次请求时）",
            3: "延迟激活（用户主动触发）",
        }
        return descriptions.get(self.value, "未知")


@dataclass
class ModuleSpec:
    """
    模块规格描述

    描述一个可懒加载的功能模块的所有元信息，包括：
    - 基本信息（名称、路由前缀、标签）
    - 层级和优先级
    - 依赖关系（其他模块、外部服务）
    - 降级方案
    - 运行时状态
    """

    # === 基本信息 ===
    name: str                                              # 模块唯一标识
    tier: ModuleTier                                       # 优先级层级
    router_factory: Callable                               # () -> APIRouter
    prefix: str = ""                                       # 路由前缀
    tags: List[str] = field(default_factory=list)          # API 标签

    # === 依赖关系 ===
    dependencies: List[str] = field(default_factory=list)      # 依赖的其他模块名
    required_services: List[str] = field(default_factory=list)  # 依赖的外部服务

    # === 降级配置 ===
    fallback_services: Dict[str, str] = field(default_factory=dict)  # 服务降级映射

    # === 数据库模型 ===
    model_classes: List[str] = field(
        default_factory=list)  # 该模块的 ORM model 类全路径

    # === 运行时状态（内部使用，不序列化） ===
    state: ModuleState = field(default=ModuleState.UNLOADED)
    error_message: Optional[str] = None
    load_time_ms: float = 0.0
    activation_count: int = 0
    last_activated_at: Optional[float] = None
    circuit_breaker: Any = field(default=None, repr=False)

    def mark_loading(self) -> None:
        """标记为加载中"""
        self.state = ModuleState.LOADING
        self.error_message = None

    def mark_active(self, load_time_ms: float) -> None:
        """标记为已激活"""
        self.state = ModuleState.ACTIVE
        self.load_time_ms = load_time_ms
        self.activation_count += 1
        self.last_activated_at = time.time()
        self.error_message = None

    def mark_degraded(self, reason: str) -> None:
        """标记为降级运行"""
        self.state = ModuleState.DEGRADED
        self.error_message = reason

    def mark_failed(self, error: str) -> None:
        """标记为加载失败"""
        self.state = ModuleState.FAILED
        self.error_message = error

    def mark_disabled(self) -> None:
        """标记为已禁用"""
        self.state = ModuleState.DISABLED
        self.error_message = "模块已被管理员禁用"

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（用于 API 响应）"""
        return {
            "name": self.name,
            "tier": self.tier.value,
            "tier_description": self.tier.description,
            "prefix": self.prefix,
            "tags": self.tags,
            "state": self.state.value,
            "dependencies": self.dependencies,
            "required_services": self.required_services,
            "fallback_services": self.fallback_services,
            "error_message": self.error_message,
            "load_time_ms": round(self.load_time_ms, 2),
            "activation_count": self.activation_count,
            "last_activated_at": self.last_activated_at,
        }

    @staticmethod
    def validate_dependencies(
        modules: Dict[str, "ModuleSpec"], max_depth: int = 2
    ) -> List[str]:
        """
        验证模块依赖关系

        检查：
        1. 所有依赖的模块是否已注册
        2. 依赖深度是否超过限制（最多 max_depth 级）
        3. 是否存在循环依赖

        Returns:
            发现的问题列表，空列表表示无问题
        """
        issues = []

        def _check_depth(name: str, depth: int, visited: set) -> None:
            if depth > max_depth:
                issues.append(f"模块 '{name}' 依赖深度超过 {max_depth} 级")
                return
            if name in visited:
                issues.append(f"检测到循环依赖: {name}")
                return

            visited.add(name)
            spec = modules.get(name)
            if spec is None:
                issues.append(f"模块 '{name}' 未注册")
                return

            for dep in spec.dependencies:
                _check_depth(dep, depth + 1, visited.copy())

        for name in modules:
            _check_depth(name, 0, set())

        return issues
