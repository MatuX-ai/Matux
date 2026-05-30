"""
Celery任务监控API路由
提供任务熔断器状态查询和管理接口
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query

from services.celery_monitoring import (
    CeleryMonitoringService,
    get_celery_monitoring_service,
)

router = APIRouter(prefix="/api/v1/celery-monitoring", tags=["Celery Monitoring"])


@router.get("/states")
async def get_all_circuit_breaker_states(
    service: CeleryMonitoringService = Depends(get_celery_monitoring_service),
):
    """
    获取所有任务熔断器状态
    """
    return service.get_all_circuit_breaker_states()


@router.get("/states/{task_name}")
async def get_task_circuit_breaker_state(
    task_name: str,
    service: CeleryMonitoringService = Depends(get_celery_monitoring_service),
):
    """
    获取特定任务的熔断器状态

    Args:
        task_name: 任务名称
    """
    return service.get_task_circuit_breaker_state(task_name)


@router.post("/reset/{task_name}")
async def reset_task_circuit_breaker(
    task_name: str,
    service: CeleryMonitoringService = Depends(get_celery_monitoring_service),
):
    """
    重置特定任务的熔断器

    Args:
        task_name: 任务名称
    """
    return service.reset_task_circuit_breaker(task_name)


@router.put("/configure/{task_name}")
async def configure_task_circuit_breaker(
    task_name: str,
    failure_threshold: Optional[int] = Query(None, description="失败阈值"),
    timeout: Optional[int] = Query(None, description="熔断超时时间(秒)"),
    soft_time_limit: Optional[int] = Query(None, description="软超时时间(秒)"),
    time_limit: Optional[int] = Query(None, description="硬超时时间(秒)"),
    half_open_attempts: Optional[int] = Query(None, description="半开状态尝试次数"),
    service: CeleryMonitoringService = Depends(get_celery_monitoring_service),
):
    """
    配置任务熔断器参数

    Args:
        task_name: 任务名称
        failure_threshold: 失败阈值
        timeout: 熔断超时时间(秒)
        soft_time_limit: 软超时时间(秒)
        time_limit: 硬超时时间(秒)
        half_open_attempts: 半开状态尝试次数
    """
    return service.configure_task_circuit_breaker(
        task_name=task_name,
        failure_threshold=failure_threshold,
        timeout=timeout,
        soft_time_limit=soft_time_limit,
        time_limit=time_limit,
        half_open_attempts=half_open_attempts,
    )


@router.get("/statistics")
async def get_global_statistics(
    service: CeleryMonitoringService = Depends(get_celery_monitoring_service),
):
    """
    获取全局统计信息
    """
    return service.get_global_statistics()


# 健康检查端点
@router.get("/health")
async def health_check():
    """
    Celery监控服务健康检查
    """
    return {
        "status": "healthy",
        "service": "Celery Monitoring Service",
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }


# 版本信息
@router.get("/version")
async def get_version():
    """
    获取服务版本信息
    """
    return {
        "service": "Celery Monitoring Service",
        "version": "1.0.0",
        "features": [
            "Task circuit breaker monitoring",
            "Real-time status tracking",
            "Dynamic configuration",
            "Health monitoring",
        ],
    }
