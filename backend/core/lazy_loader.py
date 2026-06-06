"""
模块懒加载引擎

核心职责：
1. 管理所有功能模块的注册与生命周期
2. 提供模块激活/去激活接口
3. 实现模块级容错与故障隔离
4. 支持按层级批量激活
"""

import asyncio
import importlib
import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import FastAPI

from .module_spec import ModuleSpec, ModuleState, ModuleTier

logger = logging.getLogger(__name__)

# 熔断器默认配置
DEFAULT_BREAKER_CONFIG = None  # 延迟导入避免循环依赖


class ModuleActivationError(Exception):
    """模块激活失败异常"""

    def __init__(self, module_name: str, reason: str):
        self.module_name = module_name
        self.reason = reason
        super().__init__(f"模块 '{module_name}' 激活失败: {reason}")


class ModuleLazyLoader:
    """
    模块懒加载引擎

    管理 FastAPI 应用中功能模块的注册、激活、去激活和状态查询。
    支持按 Tier 层级批量激活，单个模块失败不影响其他模块。
    """

    def __init__(self, app: FastAPI):
        self.app = app
        self.modules: Dict[str, ModuleSpec] = {}
        self._loading_locks: Dict[str,
                                  asyncio.Lock] = defaultdict(asyncio.Lock)
        self._global_lock = asyncio.Lock()
        self._activated_routers: set = set()
        # URL prefix → module_name 映射（中间件使用）
        self._prefix_map: Dict[str, str] = {}
        # 熔断器注册表
        self._breaker_registry = None

    # ==================== 注册 ====================

    def register(self, spec: ModuleSpec) -> None:
        """
        注册模块到注册表（不立即加载路由）

        Args:
            spec: 模块规格描述

        Raises:
            ValueError: 模块名重复
        """
        if spec.name in self.modules:
            raise ValueError(f"模块 '{spec.name}' 已注册，不能重复注册")

        self.modules[spec.name] = spec

        # 建立 prefix → module 映射
        if spec.prefix:
            self._prefix_map[spec.prefix] = spec.name

        logger.info(
            f"📦 模块已注册: {spec.name} "
            f"(Tier {spec.tier.value} - {spec.tier.description})"
        )

    def register_many(self, specs: List[ModuleSpec]) -> None:
        """批量注册模块"""
        for spec in specs:
            try:
                self.register(spec)
            except ValueError as e:
                logger.warning(f"跳过重复模块: {e}")

    # ==================== 激活 ====================

    async def activate(self, module_name: str) -> bool:
        """
        激活指定模块

        流程：
        1. 检查模块状态（已激活则跳过）
        2. 递归激活依赖模块（最多 2 级）
        3. 检查外部服务依赖（可降级）
        4. 调用 router_factory() 创建路由
        5. 注册路由到 FastAPI 应用
        6. 创建该模块的数据库表
        7. 更新状态

        Args:
            module_name: 模块名称

        Returns:
            True 表示激活成功，False 表示降级运行

        Raises:
            ModuleActivationError: 激活失败且无降级方案
        """
        spec = self.modules.get(module_name)
        if spec is None:
            raise ModuleActivationError(module_name, "模块未注册")

        # 已激活或已禁用 → 跳过
        if spec.state in (ModuleState.ACTIVE, ModuleState.DISABLED):
            return spec.state == ModuleState.ACTIVE

        # 使用锁防止并发激活
        lock = self._loading_locks[module_name]
        async with lock:
            # 双重检查
            if spec.state == ModuleState.ACTIVE:
                return True

            start_time = time.time()
            spec.mark_loading()
            logger.info(f"🚀 模块激活开始: {module_name} (Tier {spec.tier.value})")

            try:
                # Step 1: 递归激活依赖模块
                await self._activate_dependencies(module_name, depth=0)

                # Step 2: 检查外部服务依赖
                degraded_services = await self._check_services(spec)
                if degraded_services:
                    logger.warning(
                        f"⚠️  模块 {module_name} 服务降级: {degraded_services}"
                    )

                # Step 3: 创建路由
                router = spec.router_factory()
                self.app.include_router(
                    router,
                    prefix=spec.prefix,
                    tags=spec.tags,
                )
                self._activated_routers.add(module_name)
                logger.info(f"📡 路由注册完成: {module_name} → {spec.prefix}")

                # Step 4: 创建数据库表（如果有）
                await self._create_module_tables(spec)

                # Step 5: 更新状态
                elapsed_ms = (time.time() - start_time) * 1000
                if degraded_services:
                    spec.mark_degraded(
                        f"以下服务不可用: {', '.join(degraded_services)}"
                    )
                    logger.info(
                        f"⚠️  模块降级运行: {module_name} "
                        f"(耗时: {elapsed_ms:.0f}ms)"
                    )
                    return False
                else:
                    spec.mark_active(elapsed_ms)
                    logger.info(
                        f"✅ 模块激活完成: {module_name} "
                        f"(耗时: {elapsed_ms:.0f}ms)"
                    )
                    return True

            except Exception as e:
                elapsed_ms = (time.time() - start_time) * 1000
                error_msg = f"{type(e).__name__}: {str(e)}"
                spec.mark_failed(error_msg)
                logger.error(
                    f"❌ 模块激活失败: {module_name} "
                    f"(耗时: {elapsed_ms:.0f}ms) - {error_msg}"
                )
                raise ModuleActivationError(module_name, error_msg) from e

    async def _activate_dependencies(
        self, module_name: str, depth: int, max_depth: int = 2
    ) -> None:
        """递归激活依赖模块"""
        if depth > max_depth:
            raise ModuleActivationError(
                module_name,
                f"依赖链深度超过 {max_depth} 级",
            )

        spec = self.modules.get(module_name)
        if spec is None:
            return

        for dep_name in spec.dependencies:
            dep_spec = self.modules.get(dep_name)
            if dep_spec is None:
                logger.warning(
                    f"⚠️  模块 {module_name} 依赖 '{dep_name}' 未注册，跳过"
                )
                continue

            if dep_spec.state not in (
                ModuleState.ACTIVE,
                ModuleState.DEGRADED,
            ):
                logger.info(
                    f"📎 激活依赖: {dep_name} "
                    f"(被 {module_name} 依赖, depth={depth})"
                )
                await self.activate(dep_name)

    async def _check_services(self, spec: ModuleSpec) -> List[str]:
        """
        检查外部服务依赖可用性

        Returns:
            不可用的服务列表
        """
        if not spec.required_services:
            return []

        # 导入服务依赖管理器（延迟导入避免循环依赖）
        try:
            from core.service_dependencies import get_service_manager

            manager = get_service_manager()
            degraded = []
            for service_name in spec.required_services:
                available = await manager.check_service(service_name)
                if not available:
                    # 检查是否有降级方案
                    fallback = spec.fallback_services.get(service_name)
                    if fallback:
                        logger.info(
                            f"🔄 服务 {service_name} 不可用，"
                            f"降级为: {fallback}"
                        )
                        degraded.append(service_name)
                    else:
                        logger.warning(
                            f"❌ 服务 {service_name} 不可用且无降级方案"
                        )
                        degraded.append(service_name)
            return degraded

        except ImportError:
            # 服务依赖管理器未实现，跳过检查
            return []

    async def _create_module_tables(self, spec: ModuleSpec) -> None:
        """为模块创建所需的数据库表"""
        if not spec.model_classes:
            return

        try:
            from core.lazy_tables import get_lazy_table_manager

            manager = get_lazy_table_manager()
            await manager.create_tables_for_module(spec.name)
        except ImportError:
            # 延迟表管理器未实现，跳过
            logger.debug(f"跳过表创建（lazy_tables 未就绪）: {spec.name}")
        except Exception as e:
            logger.warning(f"表创建失败（不影响模块激活）: {spec.name} - {e}")

    # ==================== 批量激活 ====================

    async def activate_tier(self, tier: ModuleTier) -> Dict[str, bool]:
        """
        批量激活指定层级的所有模块

        Args:
            tier: 目标层级

        Returns:
            {module_name: success} 字典
        """
        results = {}
        tier_modules = [
            name
            for name, spec in self.modules.items()
            if spec.tier == tier
            and spec.state
            in (ModuleState.UNLOADED, ModuleState.FAILED)
        ]

        if not tier_modules:
            logger.info(f"ℹ️  Tier {tier.value} 无待激活模块")
            return results

        logger.info(
            f"📋 批量激活 Tier {tier.value}: "
            f"{len(tier_modules)} 个模块"
        )

        for name in tier_modules:
            try:
                success = await self.activate(name)
                results[name] = success
            except ModuleActivationError:
                results[name] = False

        success_count = sum(1 for v in results.values() if v)
        logger.info(
            f"📋 Tier {tier.value} 批量激活完成: "
            f"{success_count}/{len(tier_modules)} 成功"
        )
        return results

    # ==================== 状态查询 ====================

    def get_status(self) -> Dict[str, Any]:
        """
        获取所有模块状态摘要

        Returns:
            包含所有模块状态和统计信息的字典
        """
        modules_list = [spec.to_dict() for spec in self.modules.values()]

        # 按状态统计
        state_counts = defaultdict(int)
        for spec in self.modules.values():
            state_counts[spec.state.value] += 1

        # 按层级统计
        tier_stats = {}
        for tier in ModuleTier:
            tier_modules = [
                s for s in self.modules.values() if s.tier == tier
            ]
            active = sum(
                1 for s in tier_modules if s.state.is_available()
            )
            tier_stats[tier.value] = {
                "total": len(tier_modules),
                "active": active,
                "description": tier.description,
            }

        return {
            "modules": modules_list,
            "summary": {
                "total": len(self.modules),
                "active": state_counts.get("active", 0),
                "degraded": state_counts.get("degraded", 0),
                "loading": state_counts.get("loading", 0),
                "failed": state_counts.get("failed", 0),
                "unloaded": state_counts.get("unloaded", 0),
                "disabled": state_counts.get("disabled", 0),
            },
            "tier_stats": tier_stats,
        }

    def get_module(self, name: str) -> Optional[ModuleSpec]:
        """获取单个模块规格"""
        return self.modules.get(name)

    def _get_breaker_registry(self):
        """获取熔断器注册表（延迟初始化）"""
        if self._breaker_registry is None:
            try:
                from .module_circuit_breaker import (
                    get_breaker_registry,
                    CircuitBreakerConfig,
                    init_breaker_registry,
                )
                try:
                    self._breaker_registry = get_breaker_registry()
                except RuntimeError:
                    self._breaker_registry = init_breaker_registry(
                        CircuitBreakerConfig(
                            failure_threshold=3,
                            timeout=60.0,
                        )
                    )
            except ImportError:
                return None
        return self._breaker_registry

    def find_module_by_path(self, request_path: str) -> Optional[str]:
        """
        根据请求路径查找对应模块名

        Args:
            request_path: HTTP 请求路径

        Returns:
            模块名，未找到返回 None
        """
        # 精确匹配前缀
        for prefix, module_name in self._prefix_map.items():
            if request_path.startswith(prefix):
                return module_name

        # 尝试匹配带 /api/v1 前缀
        for prefix, module_name in self._prefix_map.items():
            if prefix.startswith("/api/v1"):
                if request_path.startswith(prefix):
                    return module_name

        return None

    def get_breaker_status(self, module_name: str) -> Optional[Dict]:
        """获取模块熔断器状态"""
        registry = self._get_breaker_registry()
        if registry is None:
            return None
        breaker = registry.get(module_name)
        return breaker.get_status() if breaker else None

    def get_all_breaker_status(self) -> Dict[str, Any]:
        """获取所有模块熔断器状态"""
        registry = self._get_breaker_registry()
        if registry is None:
            return {}
        return registry.get_all_status()

    def is_module_active(self, name: str) -> bool:
        """检查模块是否已激活"""
        spec = self.modules.get(name)
        return spec is not None and spec.state.is_available()

    # ==================== 去激活 ====================

    async def deactivate(self, module_name: str) -> bool:
        """
        去激活指定模块

        注意：FastAPI 不支持直接移除路由，因此去激活实际上是
        将模块状态标记为 UNLOADED，由中间件拦截后续请求。

        Args:
            module_name: 模块名称

        Returns:
            True 表示成功
        """
        spec = self.modules.get(module_name)
        if spec is None:
            return False

        if spec.tier == ModuleTier.TIER_0_CORE:
            logger.warning(f"⚠️  不允许去激活核心模块: {module_name}")
            return False

        spec.state = ModuleState.UNLOADED
        spec.error_message = None
        logger.info(f"🔻 模块已去激活: {module_name}")
        return True


# ==================== 全局实例 ====================

_loader_instance: Optional[ModuleLazyLoader] = None


def get_lazy_loader() -> ModuleLazyLoader:
    """获取全局 ModuleLazyLoader 实例"""
    if _loader_instance is None:
        raise RuntimeError(
            "ModuleLazyLoader 尚未初始化，请先调用 init_lazy_loader()"
        )
    return _loader_instance


def init_lazy_loader(app: FastAPI) -> ModuleLazyLoader:
    """初始化全局 ModuleLazyLoader 实例"""
    global _loader_instance
    _loader_instance = ModuleLazyLoader(app)
    logger.info("🔧 ModuleLazyLoader 已初始化")
    return _loader_instance
