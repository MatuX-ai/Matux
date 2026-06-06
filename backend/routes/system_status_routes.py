"""
系统模块状态 API

Provide module lazy loading architecture management interfaces:
- GET  /api/v1/system/modules       get all module status
- GET  /api/v1/system/modules/{name} get single module status
- POST /api/v1/system/modules/{name}/activate manual activate module
- POST /api/v1/system/modules/{name}/deactivate manual deactivate module
- GET  /api/v1/system/health-detail  enhanced health check (with module status)
- GET  /api/v1/system/circuit-breakers  get all circuit breaker status
- POST /api/v1/system/circuit-breakers/{name}/reset  reset circuit breaker
- GET  /api/v1/system/dependencies  get dependency service status
"""

import logging

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["系统模块管理"])


@router.get("/api/v1/system/modules")
async def get_all_modules():
    """获取所有模块状态"""
    try:
        from core.lazy_loader import get_lazy_loader

        loader = get_lazy_loader()
        return loader.get_status()
    except RuntimeError as e:
        return {
            "status": "not_initialized",
            "message": "模块管理系统尚未初始化",
            "modules": [],
            "summary": {
                "total": 0,
                "active": 0,
                "degraded": 0,
                "loading": 0,
                "failed": 0,
                "unloaded": 0,
                "disabled": 0,
            },
        }


@router.get("/api/v1/system/modules/{module_name}")
async def get_module_status(module_name: str):
    """获取单个模块状态"""
    try:
        from core.lazy_loader import get_lazy_loader

        loader = get_lazy_loader()
        spec = loader.get_module(module_name)

        if spec is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": f"模块 '{module_name}' 未注册",
                    "available_modules": list(loader.modules.keys()),
                },
            )

        return spec.to_dict()

    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="模块管理系统尚未初始化",
        )


@router.post("/api/v1/system/modules/{module_name}/activate")
async def activate_module(module_name: str):
    """手动激活指定模块"""
    try:
        from core.lazy_loader import get_lazy_loader, ModuleActivationError

        loader = get_lazy_loader()

        if module_name not in loader.modules:
            raise HTTPException(
                status_code=404,
                detail=f"模块 '{module_name}' 未注册",
            )

        success = await loader.activate(module_name)
        spec = loader.get_module(module_name)

        return {
            "module": module_name,
            "state": spec.state.value,
            "success": success,
            "message": "激活成功"
            if success
            else f"降级运行: {spec.error_message}",
            "load_time_ms": round(spec.load_time_ms, 2),
        }

    except ModuleActivationError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "message": f"模块激活失败",
                "module": e.module_name,
                "reason": e.reason,
            },
        )
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="模块管理系统尚未初始化",
        )


@router.post("/api/v1/system/modules/{module_name}/deactivate")
async def deactivate_module(module_name: str):
    """手动去激活指定模块（仅限非核心模块）"""
    try:
        from core.lazy_loader import get_lazy_loader

        loader = get_lazy_loader()

        if module_name not in loader.modules:
            raise HTTPException(
                status_code=404,
                detail=f"模块 '{module_name}' 未注册",
            )

        success = await loader.deactivate(module_name)
        spec = loader.get_module(module_name)

        if not success:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "不允许去激活该模块",
                    "module": module_name,
                    "tier": spec.tier.value if spec else None,
                },
            )

        return {
            "module": module_name,
            "state": spec.state.value,
            "success": True,
            "message": "去激活成功",
        }

    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="模块管理系统尚未初始化",
        )


@router.get("/api/v1/system/health-detail")
async def get_health_detail():
    """
    增强的健康检查

    返回系统整体健康状态，包括：
    - 后端基本信息
    - 模块加载统计
    - 数据库表状态
    - 核心服务可用性
    """
    try:
        from core.lazy_loader import get_lazy_loader

        loader = get_lazy_loader()
        module_status = loader.get_status()
    except RuntimeError:
        module_status = None

    # 数据库表统计
    table_stats = {}
    try:
        from core.lazy_tables import get_lazy_table_manager

        manager = get_lazy_table_manager()
        table_stats = manager.get_stats()
    except (RuntimeError, ImportError):
        pass

    # 熔断器状态
    circuit_breaker_stats = {}
    try:
        from core.lazy_loader import get_lazy_loader

        loader = get_lazy_loader()
        circuit_breaker_stats = loader.get_all_breaker_status()
    except (RuntimeError, ImportError):
        pass

    # 依赖服务状态
    dependency_status = {}
    try:
        from core.service_dependencies import get_service_manager

        svc_manager = get_service_manager()
        dependency_status = svc_manager.get_all_status()
    except (RuntimeError, ImportError):
        pass

    # 综合健康状态
    overall_status = "healthy"
    if module_status:
        summary = module_status.get("summary", {})
        if summary.get("failed", 0) > 0:
            overall_status = "degraded"
        if summary.get("active", 0) == 0 and summary.get("total", 0) > 0:
            overall_status = "unhealthy"
    if circuit_breaker_stats:
        open_breakers = sum(
            1 for b in circuit_breaker_stats.values()
            if b.get("state") == "open"
        )
        if open_breakers > 0:
            overall_status = "degraded"

    return {
        "status": overall_status,
        "service": "iMato AI Service",
        "version": "1.0.0",
        "modules": module_status,
        "database_tables": table_stats,
        "circuit_breakers": {
            "total": len(circuit_breaker_stats),
            "modules": circuit_breaker_stats,
        },
        "dependencies": dependency_status,
    }


@router.get("/api/v1/system/tiers")
async def get_tier_info():
    """获取模块层级分类信息"""
    from core.module_spec import ModuleTier

    return {
        "tiers": [
            {
                "tier": tier.value,
                "name": tier.name,
                "description": tier.description,
            }
            for tier in ModuleTier
        ]
    }


@router.get("/api/v1/system/circuit-breakers")
async def get_circuit_breaker_status():
    """获取所有模块熔断器状态"""
    try:
        from core.lazy_loader import get_lazy_loader

        loader = get_lazy_loader()
        return {
            "circuit_breakers": loader.get_all_breaker_status(),
            "total": len(loader.get_all_breaker_status()),
        }
    except (RuntimeError, ImportError):
        return {
            "circuit_breakers": {},
            "total": 0,
            "message": "熔断器系统尚未初始化",
        }


@router.post("/api/v1/system/circuit-breakers/{module_name}/reset")
async def reset_circuit_breaker(module_name: str):
    """重置指定模块的熔断器"""
    try:
        from core.lazy_loader import get_lazy_loader

        loader = get_lazy_loader()
        registry = loader._get_breaker_registry()
        if registry is None:
            raise HTTPException(
                status_code=503,
                detail="熔断器系统尚未初始化",
            )

        breaker = registry.get(module_name)
        if breaker is None:
            raise HTTPException(
                status_code=404,
                detail=f"模块 '{module_name}' 没有熔断器记录",
            )

        breaker.reset()
        return {
            "module": module_name,
            "state": "closed",
            "message": "熔断器已重置",
        }
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="熔断器系统尚未初始化",
        )


@router.get("/api/v1/system/dependencies")
async def get_dependency_status():
    """获取依赖服务状态"""
    try:
        from core.service_dependencies import get_service_manager

        manager = get_service_manager()
        return {
            "dependencies": manager.get_all_status(),
            "total": len(manager.get_all_status()),
        }
    except RuntimeError:
        return {
            "dependencies": {},
            "total": 0,
            "message": "服务依赖管理器尚未初始化",
        }


@router.post("/api/v1/system/dependencies/recheck")
async def recheck_dependencies():
    """重新检测所有依赖服务状态"""
    try:
        from core.service_dependencies import get_service_manager

        manager = get_service_manager()
        manager.invalidate_cache()

        # 触发所有服务的重新检测
        results = {}
        for name in manager._services:
            results[name] = await manager.check_service(name)

        return {
            "message": "依赖服务重新检测完成",
            "results": results,
        }
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="服务依赖管理器尚未初始化",
        )
