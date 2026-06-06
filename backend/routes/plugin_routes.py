"""
后端插件管理 API

提供插件管理的 RESTful API 端点:
- 获取插件列表
- 获取插件详情
- 安装/卸载插件
- 启用/禁用插件
- 更新插件
- 搜索插件
- 检查兼容性

路由前缀: /api/v1/plugins
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import os
import json
import logging

from core.plugin_manager import (
    PluginManager,
    PluginInfo,
    PluginLoadResult,
    get_plugin_manager,
)

# ==================== 配置 ====================

router = APIRouter()
logger = logging.getLogger(__name__)

# ==================== 请求/响应模型 ====================


class PluginListItem(BaseModel):
    """插件列表项"""
    id: str
    name: str
    version: str
    description: str
    author: str
    icon: Optional[str] = None
    categories: List[str] = []
    state: str
    enabled: bool
    compatible: Optional[bool] = None


class PluginDetail(BaseModel):
    """插件详情"""
    id: str
    name: str
    version: str
    description: str
    author: Dict[str, str]
    license: str
    categories: List[str] = []
    keywords: List[str] = []
    icon: Optional[str] = None
    state: str
    enabled: bool
    installed_at: Optional[str] = None
    loaded_at: Optional[str] = None
    device_compatibility: Dict[str, Any] = {}
    permissions: List[str] = []
    settings: Dict[str, Any] = {}
    error: Optional[str] = None


class InstallPluginRequest(BaseModel):
    """安装插件请求"""
    plugin_id: str = Field(..., description="插件 ID")
    version: Optional[str] = Field(None, description="插件版本（默认最新版本）")
    force: bool = Field(False, description="强制安装（覆盖已安装）")
    skip_compatibility_check: bool = Field(False, description="跳过兼容性检查")


class UninstallPluginRequest(BaseModel):
    """卸载插件请求"""
    plugin_id: str = Field(..., description="插件 ID")
    keep_data: bool = Field(True, description="保留插件数据")


class TogglePluginRequest(BaseModel):
    """启用/禁用插件请求"""
    plugin_id: str = Field(..., description="插件 ID")
    enabled: bool = Field(..., description="是否启用")


class UpdatePluginRequest(BaseModel):
    """更新插件请求"""
    plugin_id: str = Field(..., description="插件 ID")
    version: Optional[str] = Field(None, description="目标版本（默认最新版本）")


class CompatibilityCheckResult(BaseModel):
    """兼容性检查结果"""
    compatible: bool
    device_class: str
    device_score: int
    required_tiers: List[str]
    compatible_tiers: List[str]
    warnings: List[str] = []
    errors: List[str] = []


class PluginSearchResult(BaseModel):
    """插件搜索结果"""
    total: int
    plugins: List[PluginListItem]
    query: str
    filters: Dict[str, Any] = {}


class PluginStats(BaseModel):
    """插件统计信息"""
    total_installed: int
    total_enabled: int
    total_disabled: int
    total_loaded: int
    total_errors: int
    categories: Dict[str, int] = {}


# ==================== 辅助函数 ====================


async def get_plugin_manager_dep() -> PluginManager:
    """获取插件管理器（依赖注入）"""
    return get_plugin_manager()


def _load_device_profile() -> Optional[Dict[str, Any]]:
    """加载设备评估报告"""
    import platform

    # Electron 应用路径
    if platform.system() == "Windows":
        app_data = os.environ.get("APPDATA", "")
        profile_path = os.path.join(app_data, "iMato", "device-profile.json")
    elif platform.system() == "Darwin":
        app_data = os.path.expanduser("~/Library/Application Support")
        profile_path = os.path.join(app_data, "iMato", "device-profile.json")
    else:
        app_data = os.path.expanduser("~/.config")
        profile_path = os.path.join(app_data, "iMato", "device-profile.json")

    if not os.path.exists(profile_path):
        return None

    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as err:
        logger.error(f"读取设备评估报告失败: {err}")
        return None


def _check_plugin_compatibility(plugin_info: PluginInfo, device_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    检查插件与设备的兼容性

    Returns:
        兼容性检查结果
    """
    if not device_profile:
        return {
            "compatible": True,
            "warnings": ["设备评估报告不存在，跳过兼容性检查"],
        }

    manifest = plugin_info.manifest
    compat = manifest.get("deviceCompatibility", {})

    if not compat:
        return {
            "compatible": True,
            "warnings": ["插件未声明设备兼容性要求"],
        }

    device_class = device_profile.get(
        "assessment", {}).get("deviceClass", "basic")
    device_score = device_profile.get("assessment", {}).get("score", 0)

    # 设备等级到 Tier 的映射
    device_tier_map = {
        "basic": ["tier-a"],
        "standard": ["tier-a", "tier-b"],
        "advanced": ["tier-a", "tier-b", "tier-c"],
        "professional": ["tier-a", "tier-b", "tier-c", "tier-d"],
    }

    compatible_tiers = device_tier_map.get(device_class, [])
    required_tiers = compat.get("compatibleTiers", [])

    # 检查 Tier 兼容性
    has_compatible_tier = any(
        tier in compatible_tiers for tier in required_tiers)

    warnings = []
    errors = []

    if not has_compatible_tier:
        errors.append(
            f"插件不兼容当前设备等级 ({device_class})\n"
            f"插件要求: {', '.join(required_tiers)}\n"
            f"设备支持: {', '.join(compatible_tiers)}"
        )

    # 检查最低评分
    min_score = compat.get("minDeviceScore", 0)
    if device_score < min_score:
        errors.append(f"设备评分不足: 当前 {device_score} 分，插件要求最低 {min_score} 分")

    # 检查硬件要求
    required_hardware = compat.get("requiredHardware", {})
    hardware = device_profile.get("hardware", {})

    if required_hardware.get("minMemoryMB"):
        actual_memory = hardware.get("memory", {}).get("totalMB", 0)
        if actual_memory < required_hardware["minMemoryMB"]:
            errors.append(
                f"内存不足: 当前 {actual_memory} MB，插件要求最低 {required_hardware['minMemoryMB']} MB"
            )

    if required_hardware.get("requireGPU"):
        has_gpu = hardware.get("gpu", {}).get("hasDedicatedGPU", False)
        if not has_gpu:
            errors.append("插件需要独立 GPU，但当前设备未检测到")

    if required_hardware.get("requireCUDA"):
        has_cuda = hardware.get("gpu", {}).get("supportsCUDA", False)
        if not has_cuda:
            errors.append("插件需要 CUDA 支持，但当前设备未检测到")

    if required_hardware.get("requireDocker"):
        has_docker = device_profile.get("software", {}).get(
            "containers", {}).get("hasDocker", False)
        if not has_docker:
            errors.append("插件需要 Docker，但当前设备未安装或不可用")

    compatible = len(errors) == 0

    return {
        "compatible": compatible,
        "device_class": device_class,
        "device_score": device_score,
        "required_tiers": required_tiers,
        "compatible_tiers": compatible_tiers,
        "warnings": warnings,
        "errors": errors,
    }


# ==================== API 端点 ====================


@router.get("/api/v1/plugins", response_model=List[PluginListItem])
async def list_plugins(
    state: Optional[str] = Query(
        None, description="过滤状态 (loaded, enabled, disabled, error)"),
    category: Optional[str] = Query(None, description="过滤分类"),
    compatible_only: bool = Query(False, description="仅显示兼容的插件"),
    plugin_manager: PluginManager = Depends(get_plugin_manager_dep),
):
    """
    获取插件列表

    - **state**: 可选，过滤插件状态
    - **category**: 可选，过滤插件分类
    - **compatible_only**: 可选，仅显示与当前设备兼容的插件
    """
    try:
        # 获取所有插件
        plugins = plugin_manager.get_all_plugins()

        # 加载设备评估报告
        device_profile = _load_device_profile()

        result = []

        for plugin in plugins:
            # 状态过滤
            if state:
                if state == "enabled" and not plugin.enabled:
                    continue
                elif state == "disabled" and plugin.enabled:
                    continue
                elif state != plugin.state:
                    continue

            # 分类过滤
            if category:
                categories = plugin.manifest.get("categories", [])
                if category not in categories:
                    continue

            # 兼容性检查
            compatible = None
            if compatible_only or device_profile:
                compat_result = _check_plugin_compatibility(
                    plugin, device_profile)
                compatible = compat_result["compatible"]

                if compatible_only and not compatible:
                    continue

            # 构建列表项
            manifest = plugin.manifest
            author = manifest.get("author", {})

            result.append(PluginListItem(
                id=plugin.id,
                name=plugin.name,
                version=plugin.version,
                description=plugin.description,
                author=author.get("name", "Unknown"),
                icon=manifest.get("icon"),
                categories=manifest.get("categories", []),
                state=plugin.state,
                enabled=plugin.enabled,
                compatible=compatible,
            ))

        return result

    except Exception as err:
        logger.error(f"获取插件列表失败: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取插件列表失败: {str(err)}")


@router.get("/api/v1/plugins/{plugin_id}", response_model=PluginDetail)
async def get_plugin_detail(
    plugin_id: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager_dep),
):
    """
    获取插件详情

    - **plugin_id**: 插件 ID
    """
    try:
        plugin = plugin_manager.get_plugin(plugin_id)

        if not plugin:
            raise HTTPException(status_code=404, detail=f"插件不存在: {plugin_id}")

        manifest = plugin.manifest

        return PluginDetail(
            id=plugin.id,
            name=plugin.name,
            version=plugin.version,
            description=plugin.description,
            author=manifest.get("author", {}),
            license=plugin.license,
            categories=manifest.get("categories", []),
            keywords=manifest.get("keywords", []),
            icon=manifest.get("icon"),
            state=plugin.state,
            enabled=plugin.enabled,
            installed_at=plugin.installed_at,
            loaded_at=plugin.loaded_at,
            device_compatibility=manifest.get("deviceCompatibility", {}),
            permissions=manifest.get("permissions", []),
            settings=manifest.get("settings", {}),
            error=plugin.error,
        )

    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"获取插件详情失败: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取插件详情失败: {str(err)}")


@router.post("/api/v1/plugins/install")
async def install_plugin(
    request: InstallPluginRequest,
    background_tasks: BackgroundTasks,
    plugin_manager: PluginManager = Depends(get_plugin_manager_dep),
):
    """
    安装插件

    注意: 此 API 仅触发安装流程，实际安装由 Electron 主进程执行。
    前端应通过 Electron IPC 调用 plugin:install。
    """
    try:
        # 检查插件是否已安装
        existing_plugin = plugin_manager.get_plugin(request.plugin_id)

        if existing_plugin and not request.force:
            raise HTTPException(
                status_code=409,
                detail=f"插件已安装: {request.plugin_id} v{existing_plugin.version}"
            )

        # 返回安装指令（前端通过 Electron IPC 执行）
        return {
            "success": True,
            "message": "安装请求已接收，请通过 Electron IPC 执行安装",
            "plugin_id": request.plugin_id,
            "version": request.version,
            "action": "electron:plugin:install",
        }

    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"安装插件失败: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"安装插件失败: {str(err)}")


@router.post("/api/v1/plugins/uninstall")
async def uninstall_plugin(
    request: UninstallPluginRequest,
    plugin_manager: PluginManager = Depends(get_plugin_manager_dep),
):
    """
    卸载插件

    注意: 此 API 仅触发卸载流程，实际卸载由 Electron 主进程执行。
    """
    try:
        plugin = plugin_manager.get_plugin(request.plugin_id)

        if not plugin:
            raise HTTPException(
                status_code=404, detail=f"插件不存在: {request.plugin_id}")

        # 先卸载（从内存中移除）
        result = await plugin_manager.unload_plugin(request.plugin_id)

        if not result.success:
            raise HTTPException(
                status_code=500, detail=f"卸载插件失败: {result.error}")

        # 返回卸载指令（前端通过 Electron IPC 执行文件删除）
        return {
            "success": True,
            "message": "插件已从内存中卸载，请通过 Electron IPC 删除文件",
            "plugin_id": request.plugin_id,
            "keep_data": request.keep_data,
            "action": "electron:plugin:uninstall",
        }

    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"卸载插件失败: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"卸载插件失败: {str(err)}")


@router.post("/api/v1/plugins/toggle")
async def toggle_plugin(
    request: TogglePluginRequest,
    plugin_manager: PluginManager = Depends(get_plugin_manager_dep),
):
    """
    启用/禁用插件
    """
    try:
        plugin = plugin_manager.get_plugin(request.plugin_id)

        if not plugin:
            raise HTTPException(
                status_code=404, detail=f"插件不存在: {request.plugin_id}")

        if request.enabled:
            result = await plugin_manager.enable_plugin(request.plugin_id)
        else:
            result = await plugin_manager.disable_plugin(request.plugin_id)

        if not result.success:
            raise HTTPException(
                status_code=500, detail=f"操作失败: {result.error}")

        return {
            "success": True,
            "plugin_id": request.plugin_id,
            "enabled": request.enabled,
            "message": f"插件已{'启用' if request.enabled else '禁用'}",
        }

    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"切换插件状态失败: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"操作失败: {str(err)}")


@router.post("/api/v1/plugins/update")
async def update_plugin(
    request: UpdatePluginRequest,
    plugin_manager: PluginManager = Depends(get_plugin_manager_dep),
):
    """
    更新插件

    注意: 实际更新由 Electron 主进程执行。
    """
    try:
        plugin = plugin_manager.get_plugin(request.plugin_id)

        if not plugin:
            raise HTTPException(
                status_code=404, detail=f"插件不存在: {request.plugin_id}")

        # 返回更新指令
        return {
            "success": True,
            "message": "更新请求已接收，请通过 Electron IPC 执行更新",
            "plugin_id": request.plugin_id,
            "current_version": plugin.version,
            "target_version": request.version,
            "action": "electron:plugin:update",
        }

    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"更新插件失败: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新插件失败: {str(err)}")


@router.get("/api/v1/plugins/{plugin_id}/compatibility", response_model=CompatibilityCheckResult)
async def check_plugin_compatibility(
    plugin_id: str,
    plugin_manager: PluginManager = Depends(get_plugin_manager_dep),
):
    """
    检查插件与当前设备的兼容性
    """
    try:
        plugin = plugin_manager.get_plugin(plugin_id)

        if not plugin:
            raise HTTPException(status_code=404, detail=f"插件不存在: {plugin_id}")

        # 加载设备评估报告
        device_profile = _load_device_profile()

        if not device_profile:
            return CompatibilityCheckResult(
                compatible=True,
                device_class="unknown",
                device_score=0,
                required_tiers=[],
                compatible_tiers=[],
                warnings=["设备评估报告不存在，跳过兼容性检查"],
            )

        # 执行兼容性检查
        result = _check_plugin_compatibility(plugin, device_profile)

        return CompatibilityCheckResult(**result)

    except HTTPException:
        raise
    except Exception as err:
        logger.error(f"兼容性检查失败: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"兼容性检查失败: {str(err)}")


@router.get("/api/v1/plugins/search", response_model=PluginSearchResult)
async def search_plugins(
    q: str = Query(..., description="搜索关键词"),
    category: Optional[str] = Query(None, description="过滤分类"),
    tier: Optional[str] = Query(None, description="过滤设备等级"),
    plugin_manager: PluginManager = Depends(get_plugin_manager_dep),
):
    """
    搜索插件

    - **q**: 搜索关键词（匹配名称、描述、关键词）
    - **category**: 可选，过滤分类
    - **tier**: 可选，过滤设备等级
    """
    try:
        plugins = plugin_manager.get_all_plugins()
        device_profile = _load_device_profile()

        # 搜索关键词（小写）
        query_lower = q.lower()

        result = []

        for plugin in plugins:
            manifest = plugin.manifest

            # 关键词匹配
            match = False

            # 匹配名称
            if query_lower in plugin.name.lower():
                match = True

            # 匹配描述
            if not match and query_lower in plugin.description.lower():
                match = True

            # 匹配关键词
            if not match:
                keywords = manifest.get("keywords", [])
                if any(query_lower in kw.lower() for kw in keywords):
                    match = True

            if not match:
                continue

            # 分类过滤
            if category:
                categories = manifest.get("categories", [])
                if category not in categories:
                    continue

            # Tier 过滤
            if tier:
                compat = manifest.get("deviceCompatibility", {})
                tiers = compat.get("compatibleTiers", [])
                if tier not in tiers:
                    continue

            # 兼容性检查
            compatible = None
            if device_profile:
                compat_result = _check_plugin_compatibility(
                    plugin, device_profile)
                compatible = compat_result["compatible"]

            author = manifest.get("author", {})

            result.append(PluginListItem(
                id=plugin.id,
                name=plugin.name,
                version=plugin.version,
                description=plugin.description,
                author=author.get("name", "Unknown"),
                icon=manifest.get("icon"),
                categories=manifest.get("categories", []),
                state=plugin.state,
                enabled=plugin.enabled,
                compatible=compatible,
            ))

        return PluginSearchResult(
            total=len(result),
            plugins=result,
            query=q,
            filters={
                "category": category,
                "tier": tier,
            },
        )

    except Exception as err:
        logger.error(f"搜索插件失败: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索插件失败: {str(err)}")


@router.get("/api/v1/plugins/stats", response_model=PluginStats)
async def get_plugin_stats(
    plugin_manager: PluginManager = Depends(get_plugin_manager_dep),
):
    """
    获取插件统计信息
    """
    try:
        plugins = plugin_manager.get_all_plugins()

        stats = PluginStats(
            total_installed=len(plugins),
            total_enabled=len([p for p in plugins if p.enabled]),
            total_disabled=len([p for p in plugins if not p.enabled]),
            total_loaded=len(
                [p for p in plugins if p.state in ["loaded", "enabled"]]),
            total_errors=len([p for p in plugins if p.state == "error"]),
        )

        # 分类统计
        categories = {}
        for plugin in plugins:
            for cat in plugin.manifest.get("categories", []):
                categories[cat] = categories.get(cat, 0) + 1

        stats.categories = categories

        return stats

    except Exception as err:
        logger.error(f"获取插件统计失败: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取插件统计失败: {str(err)}")


@router.post("/api/v1/plugins/reload")
async def reload_plugins(
    plugin_manager: PluginManager = Depends(get_plugin_manager_dep),
):
    """
    重新加载所有插件（开发模式）

    注意: 此操作会卸载并重新加载所有插件，可能导致服务短暂不可用。
    """
    try:
        logger.info("重新加载所有插件...")

        # 卸载所有插件
        for plugin_id in list(plugin_manager.plugins.keys()):
            await plugin_manager.unload_plugin(plugin_id)

        # 重新扫描
        await plugin_manager.scan_installed_plugins()
        plugin_manager._resolve_dependencies()

        # 重新加载
        await plugin_manager.load_all_plugins()

        return {
            "success": True,
            "message": "插件已重新加载",
            "total_loaded": len(plugin_manager.get_loaded_plugins()),
        }

    except Exception as err:
        logger.error(f"重新加载插件失败: {err}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重新加载插件失败: {str(err)}")
