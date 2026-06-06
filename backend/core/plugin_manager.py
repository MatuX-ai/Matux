"""
后端插件管理器

功能:
1. 动态加载已安装插件的路由和服务
2. 管理插件生命周期（启用/禁用/卸载）
3. 插件依赖解析和加载顺序
4. 插件热重载（开发模式）
5. 插件状态监控
6. 插件配置管理
7. 插件间通信

用法:
    from core.plugin_manager import PluginManager
    
    plugin_manager = PluginManager()
    await plugin_manager.initialize()
    await plugin_manager.load_all_plugins()
"""

import os
import sys
import json
import importlib
import importlib.util
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from fastapi import FastAPI, APIRouter
from pydantic import BaseModel

# ==================== 配置 ====================

logger = logging.getLogger(__name__)

# 插件安装目录（由 Electron 主进程设置）
PLUGIN_BASE_DIR = os.path.expanduser("~/.imato/plugins")
PLUGIN_DATA_DIR = os.path.expanduser("~/.imato/plugin-data")

# ==================== 数据模型 ====================


class PluginState:
    """插件状态枚举"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


class PluginInfo(BaseModel):
    """插件信息"""
    id: str
    name: str
    version: str
    description: str = ""
    author: Dict[str, str] = {}
    license: str = ""
    install_path: str
    data_dir: str
    state: str = PluginState.UNLOADED
    enabled: bool = True
    installed_at: str = ""
    loaded_at: Optional[str] = None
    error: Optional[str] = None
    manifest: Dict[str, Any] = {}
    dependencies: List[str] = []
    routes: List[Dict[str, Any]] = []
    services: List[Dict[str, Any]] = []


class PluginLoadResult(BaseModel):
    """插件加载结果"""
    success: bool
    plugin_id: str
    error: Optional[str] = None
    warnings: List[str] = []
    loaded_routes: int = 0
    loaded_services: int = 0


# ==================== 插件管理器 ====================


class PluginManager:
    """
    插件管理器

    负责:
    - 扫描已安装插件
    - 动态加载插件模块
    - 注册路由和服务
    - 管理插件生命周期
    - 处理插件依赖
    """

    def __init__(self, app: FastAPI = None):
        """
        初始化插件管理器

        Args:
            app: FastAPI 应用实例（用于注册路由）
        """
        self.app = app
        self.plugins: Dict[str, PluginInfo] = {}
        self.loaded_modules: Dict[str, Any] = {}
        self.service_instances: Dict[str, Any] = {}
        self.route_routers: Dict[str, APIRouter] = {}

        # 钩子回调
        self._on_plugin_loaded: List[Callable] = []
        self._on_plugin_unloaded: List[Callable] = []
        self._on_plugin_enabled: List[Callable] = []
        self._on_plugin_disabled: List[Callable] = []

        # 确保目录存在
        os.makedirs(PLUGIN_BASE_DIR, exist_ok=True)
        os.makedirs(PLUGIN_DATA_DIR, exist_ok=True)

    async def initialize(self):
        """初始化插件管理器"""
        logger.info("初始化插件管理器...")

        # 1. 扫描已安装插件
        await self.scan_installed_plugins()

        # 2. 解析依赖关系
        self._resolve_dependencies()

        # 3. 加载所有启用的插件
        await self.load_all_plugins()

        logger.info(f"插件管理器初始化完成，已加载 {len(self.loaded_modules)} 个插件")

    async def scan_installed_plugins(self):
        """扫描已安装的插件"""
        logger.info(f"扫描插件目录: {PLUGIN_BASE_DIR}")

        plugin_info_files = []

        for item in os.listdir(PLUGIN_BASE_DIR):
            if item.endswith(".json"):
                plugin_info_files.append(os.path.join(PLUGIN_BASE_DIR, item))

        logger.info(f"找到 {len(plugin_info_files)} 个插件信息文件")

        for info_file in plugin_info_files:
            try:
                with open(info_file, "r", encoding="utf-8") as f:
                    info_data = json.load(f)

                plugin_id = info_data.get("id")

                if not plugin_id:
                    logger.warning(f"插件信息文件缺少 id 字段: {info_file}")
                    continue

                # 创建 PluginInfo 对象
                plugin_info = PluginInfo(
                    id=plugin_id,
                    name=info_data.get("name", plugin_id),
                    version=info_data.get("version", "0.0.0"),
                    description=info_data.get("description", ""),
                    author=info_data.get("author", {}),
                    license=info_data.get("license", ""),
                    install_path=info_data.get("installPath", ""),
                    data_dir=info_data.get("dataDir", ""),
                    state=PluginState.UNLOADED,
                    enabled=info_data.get("enabled", True),
                    installed_at=info_data.get("installedAt", ""),
                    manifest=info_data.get("manifest", {}),
                )

                # 提取依赖
                deps = plugin_info.manifest.get("dependencies", {})
                plugin_deps = deps.get("plugins", [])
                plugin_info.dependencies = [
                    dep["id"] for dep in plugin_deps if not dep.get("optional", False)]

                # 提取路由和服务信息
                entry_points = plugin_info.manifest.get("entryPoints", {})
                backend = entry_points.get("backend", {})

                plugin_info.routes = backend.get("routes", [])
                plugin_info.services = backend.get("services", [])

                self.plugins[plugin_id] = plugin_info

                logger.info(
                    f"扫描到插件: {plugin_info.name} v{plugin_info.version} ({plugin_id})")

            except Exception as err:
                logger.error(f"读取插件信息失败 {info_file}: {err}")

    def _resolve_dependencies(self):
        """解析插件依赖关系，确定加载顺序"""
        logger.info("解析插件依赖关系...")

        # 拓扑排序
        visited = set()
        loading_order = []

        def visit(plugin_id: str, path: List[str] = None):
            if path is None:
                path = []

            if plugin_id in path:
                logger.error(f"检测到循环依赖: {' -> '.join(path + [plugin_id])}")
                return

            if plugin_id in visited:
                return

            path = path + [plugin_id]
            plugin = self.plugins.get(plugin_id)

            if not plugin:
                logger.warning(f"依赖插件不存在: {plugin_id}")
                return

            # 递归访问依赖
            for dep_id in plugin.dependencies:
                visit(dep_id, path)

            visited.add(plugin_id)
            loading_order.append(plugin_id)

        # 访问所有插件
        for plugin_id in self.plugins:
            visit(plugin_id)

        # 更新加载顺序
        self._loading_order = loading_order

        logger.info(f"加载顺序: {' -> '.join(loading_order)}")

    async def load_all_plugins(self):
        """加载所有启用的插件"""
        logger.info("开始加载所有启用的插件...")

        loaded_count = 0
        failed_count = 0

        for plugin_id in self._loading_order:
            plugin = self.plugins.get(plugin_id)

            if not plugin or not plugin.enabled:
                continue

            result = await self.load_plugin(plugin_id)

            if result.success:
                loaded_count += 1
            else:
                failed_count += 1
                logger.error(f"插件加载失败: {plugin_id} - {result.error}")

        logger.info(f"插件加载完成: 成功 {loaded_count} 个，失败 {failed_count} 个")

    async def load_plugin(self, plugin_id: str) -> PluginLoadResult:
        """
        加载单个插件

        Args:
            plugin_id: 插件 ID

        Returns:
            PluginLoadResult: 加载结果
        """
        plugin = self.plugins.get(plugin_id)

        if not plugin:
            return PluginLoadResult(
                success=False,
                plugin_id=plugin_id,
                error=f"插件不存在: {plugin_id}"
            )

        if not plugin.enabled:
            return PluginLoadResult(
                success=False,
                plugin_id=plugin_id,
                error=f"插件已禁用: {plugin_id}"
            )

        if plugin.state == PluginState.LOADED or plugin.state == PluginState.ENABLED:
            return PluginLoadResult(
                success=True,
                plugin_id=plugin_id,
                warnings=["插件已加载"]
            )

        logger.info(f"正在加载插件: {plugin.name} ({plugin_id})")
        plugin.state = PluginState.LOADING

        warnings = []

        try:
            # 1. 检查依赖是否已加载
            for dep_id in plugin.dependencies:
                dep_plugin = self.plugins.get(dep_id)

                if not dep_plugin:
                    warnings.append(f"依赖插件不存在: {dep_id}")
                    continue

                if dep_plugin.state not in [PluginState.LOADED, PluginState.ENABLED]:
                    warnings.append(f"依赖插件未加载: {dep_id}")

            # 2. 加载 Python 模块
            loaded_routes = 0
            loaded_services = 0

            if plugin.routes or plugin.services:
                # 将插件目录添加到 sys.path
                plugin_path = Path(plugin.install_path)
                backend_path = plugin_path / "backend"

                if backend_path.exists():
                    sys.path.insert(0, str(backend_path))

                # 加载路由
                for route_config in plugin.routes:
                    route_file = route_config.get("file")

                    if route_file:
                        try:
                            router = await self._load_route_module(plugin, route_config)
                            if router:
                                self.route_routers[plugin_id] = router
                                loaded_routes += 1
                        except Exception as err:
                            warnings.append(f"路由加载失败 {route_file}: {err}")

                # 加载服务
                for service_config in plugin.services:
                    service_file = service_config.get("file")
                    service_name = service_config.get("name")

                    if service_file and service_name:
                        try:
                            service_instance = await self._load_service_module(plugin, service_config)
                            if service_instance:
                                self.service_instances[service_name] = service_instance
                                loaded_services += 1
                        except Exception as err:
                            warnings.append(f"服务加载失败 {service_file}: {err}")

            # 3. 更新状态
            plugin.state = PluginState.ENABLED if plugin.enabled else PluginState.LOADED
            plugin.loaded_at = datetime.now().isoformat()

            self.loaded_modules[plugin_id] = plugin

            # 4. 触发回调
            await self._trigger_callbacks(self._on_plugin_loaded, plugin)

            logger.info(
                f"✓ 插件加载成功: {plugin.name} ({loaded_routes} 路由, {loaded_services} 服务)")

            return PluginLoadResult(
                success=True,
                plugin_id=plugin_id,
                warnings=warnings,
                loaded_routes=loaded_routes,
                loaded_services=loaded_services
            )

        except Exception as err:
            plugin.state = PluginState.ERROR
            plugin.error = str(err)

            logger.error(f"✗ 插件加载失败: {plugin.name} - {err}", exc_info=True)

            return PluginLoadResult(
                success=False,
                plugin_id=plugin_id,
                error=str(err),
                warnings=warnings
            )

    async def unload_plugin(self, plugin_id: str) -> PluginLoadResult:
        """
        卸载插件

        Args:
            plugin_id: 插件 ID

        Returns:
            PluginLoadResult: 卸载结果
        """
        plugin = self.plugins.get(plugin_id)

        if not plugin:
            return PluginLoadResult(
                success=False,
                plugin_id=plugin_id,
                error=f"插件不存在: {plugin_id}"
            )

        if plugin.state == PluginState.UNLOADED:
            return PluginLoadResult(
                success=True,
                plugin_id=plugin_id,
                warnings=["插件已卸载"]
            )

        logger.info(f"正在卸载插件: {plugin.name} ({plugin_id})")

        try:
            # 1. 检查是否有其他插件依赖此插件
            dependents = []
            for pid, p in self.plugins.items():
                if plugin_id in p.dependencies and p.state in [PluginState.LOADED, PluginState.ENABLED]:
                    dependents.append(pid)

            if dependents:
                return PluginLoadResult(
                    success=False,
                    plugin_id=plugin_id,
                    error=f"以下插件依赖此插件，无法卸载: {', '.join(dependents)}"
                )

            # 2. 移除路由
            if plugin_id in self.route_routers:
                router = self.route_routers.pop(plugin_id)

                # 从 FastAPI 应用移除路由
                if self.app:
                    # FastAPI 不支持动态移除路由，需要重建应用
                    logger.warning("FastAPI 不支持动态移除路由，建议重启服务")

            # 3. 移除服务实例
            for service_config in plugin.services:
                service_name = service_config.get("name")
                if service_name in self.service_instances:
                    del self.service_instances[service_name]

            # 4. 从 sys.path 移除
            plugin_path = Path(plugin.install_path)
            backend_path = str(plugin_path / "backend")

            if backend_path in sys.path:
                sys.path.remove(backend_path)

            # 5. 卸载模块（从 sys.modules 移除）
            modules_to_remove = []
            for module_name in sys.modules:
                if module_name.startswith(plugin_id.replace("-", "_")):
                    modules_to_remove.append(module_name)

            for module_name in modules_to_remove:
                del sys.modules[module_name]

            # 6. 更新状态
            plugin.state = PluginState.UNLOADED
            plugin.loaded_at = None

            if plugin_id in self.loaded_modules:
                del self.loaded_modules[plugin_id]

            # 7. 触发回调
            await self._trigger_callbacks(self._on_plugin_unloaded, plugin)

            logger.info(f"✓ 插件卸载成功: {plugin.name}")

            return PluginLoadResult(
                success=True,
                plugin_id=plugin_id
            )

        except Exception as err:
            plugin.state = PluginState.ERROR
            plugin.error = str(err)

            logger.error(f"✗ 插件卸载失败: {plugin.name} - {err}", exc_info=True)

            return PluginLoadResult(
                success=False,
                plugin_id=plugin_id,
                error=str(err)
            )

    async def enable_plugin(self, plugin_id: str) -> PluginLoadResult:
        """启用插件"""
        plugin = self.plugins.get(plugin_id)

        if not plugin:
            return PluginLoadResult(
                success=False,
                plugin_id=plugin_id,
                error=f"插件不存在: {plugin_id}"
            )

        plugin.enabled = True

        # 更新插件信息文件
        self._update_plugin_info(plugin)

        # 加载插件
        result = await self.load_plugin(plugin_id)

        if result.success:
            await self._trigger_callbacks(self._on_plugin_enabled, plugin)

        return result

    async def disable_plugin(self, plugin_id: str) -> PluginLoadResult:
        """禁用插件"""
        plugin = self.plugins.get(plugin_id)

        if not plugin:
            return PluginLoadResult(
                success=False,
                plugin_id=plugin_id,
                error=f"插件不存在: {plugin_id}"
            )

        # 先卸载
        result = await self.unload_plugin(plugin_id)

        if result.success:
            plugin.enabled = False

            # 更新插件信息文件
            self._update_plugin_info(plugin)

            await self._trigger_callbacks(self._on_plugin_disabled, plugin)

        return result

    def get_plugin(self, plugin_id: str) -> Optional[PluginInfo]:
        """获取插件信息"""
        return self.plugins.get(plugin_id)

    def get_all_plugins(self) -> List[PluginInfo]:
        """获取所有插件信息"""
        return list(self.plugins.values())

    def get_enabled_plugins(self) -> List[PluginInfo]:
        """获取所有启用的插件"""
        return [p for p in self.plugins.values() if p.enabled]

    def get_loaded_plugins(self) -> List[PluginInfo]:
        """获取所有已加载的插件"""
        return [p for p in self.plugins.values() if p.state in [PluginState.LOADED, PluginState.ENABLED]]

    def get_service(self, service_name: str) -> Optional[Any]:
        """获取服务实例"""
        return self.service_instances.get(service_name)

    def register_callback(self, event: str, callback: Callable):
        """
        注册事件回调

        Args:
            event: 事件名称 ('loaded', 'unloaded', 'enabled', 'disabled')
            callback: 回调函数
        """
        if event == "loaded":
            self._on_plugin_loaded.append(callback)
        elif event == "unloaded":
            self._on_plugin_unloaded.append(callback)
        elif event == "enabled":
            self._on_plugin_enabled.append(callback)
        elif event == "disabled":
            self._on_plugin_disabled.append(callback)
        else:
            logger.warning(f"未知的事件类型: {event}")

    # ==================== 私有方法 ====================

    async def _load_route_module(self, plugin: PluginInfo, route_config: Dict) -> Optional[APIRouter]:
        """
        加载路由模块

        Args:
            plugin: 插件信息
            route_config: 路由配置

        Returns:
            APIRouter 实例
        """
        route_file = route_config.get("file")
        prefix = route_config.get("prefix", f"/api/v1/{plugin.id}")
        tags = route_config.get("tags", [plugin.name])

        if not route_file:
            return None

        # 构建模块路径
        plugin_path = Path(plugin.install_path)
        route_path = plugin_path / route_file

        if not route_path.exists():
            raise FileNotFoundError(f"路由文件不存在: {route_path}")

        # 动态加载模块
        module_name = f"plugin_{plugin.id.replace('-', '_')}_routes"
        spec = importlib.util.spec_from_file_location(module_name, route_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # 获取 router 对象
        router = getattr(module, "router", None)

        if not router or not isinstance(router, APIRouter):
            raise ValueError(f"路由模块未导出 router 对象: {route_file}")

        # 注册到 FastAPI 应用
        if self.app:
            self.app.include_router(router, prefix=prefix, tags=tags)
            logger.info(f"  ✓ 注册路由: {prefix} ({tags})")

        return router

    async def _load_service_module(self, plugin: PluginInfo, service_config: Dict) -> Optional[Any]:
        """
        加载服务模块

        Args:
            plugin: 插件信息
            service_config: 服务配置

        Returns:
            服务实例
        """
        service_file = service_config.get("file")
        service_name = service_config.get("name")
        auto_start = service_config.get("autoStart", False)

        if not service_file or not service_name:
            return None

        # 构建模块路径
        plugin_path = Path(plugin.install_path)
        service_path = plugin_path / service_file

        if not service_path.exists():
            raise FileNotFoundError(f"服务文件不存在: {service_path}")

        # 动态加载模块
        module_name = f"plugin_{plugin.id.replace('-', '_')}_{service_name.lower()}"
        spec = importlib.util.spec_from_file_location(
            module_name, service_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # 获取服务类
        service_class = getattr(module, service_name, None)

        if not service_class:
            raise ValueError(f"服务模块未导出类 {service_name}: {service_file}")

        # 实例化服务
        # TODO: 实现依赖注入（数据库 Session 等）
        service_instance = service_class()

        # 自动启动服务
        if auto_start and hasattr(service_instance, "start"):
            if asyncio.iscoroutinefunction(service_instance.start):
                await service_instance.start()
            else:
                service_instance.start()

            logger.info(f"  ✓ 服务已启动: {service_name}")

        return service_instance

    def _update_plugin_info(self, plugin: PluginInfo):
        """更新插件信息文件"""
        info_path = os.path.join(PLUGIN_BASE_DIR, f"{plugin.id}.json")

        try:
            with open(info_path, "r", encoding="utf-8") as f:
                info_data = json.load(f)

            info_data["enabled"] = plugin.enabled

            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(info_data, f, indent=2, ensure_ascii=False)

        except Exception as err:
            logger.error(f"更新插件信息失败: {err}")

    async def _trigger_callbacks(self, callbacks: List[Callable], plugin: PluginInfo):
        """触发回调函数"""
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(plugin)
                else:
                    callback(plugin)
            except Exception as err:
                logger.error(f"回调执行失败: {err}")


# ==================== 全局实例 ====================

# 全局插件管理器实例
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager(app: FastAPI = None) -> PluginManager:
    """
    获取全局插件管理器实例

    Args:
        app: FastAPI 应用实例

    Returns:
        PluginManager 实例
    """
    global _plugin_manager

    if _plugin_manager is None:
        _plugin_manager = PluginManager(app)

    return _plugin_manager


async def initialize_plugin_manager(app: FastAPI):
    """
    初始化全局插件管理器

    Args:
        app: FastAPI 应用实例
    """
    global _plugin_manager

    _plugin_manager = PluginManager(app)
    await _plugin_manager.initialize()

    logger.info(f"插件管理器已初始化，共 {len(_plugin_manager.plugins)} 个插件")
