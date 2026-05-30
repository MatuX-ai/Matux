"""
Celery任务监控和熔断器管理服务
提供任务状态监控、熔断器状态查询和管理功能
"""

from datetime import datetime
import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException

from config.settings import settings
from middleware.celery_circuit_breaker import (
    CeleryTaskCircuitBreakerConfig,
    TaskCircuitState,
    task_circuit_manager,
)

logger = logging.getLogger(__name__)


class CeleryMonitoringService:
    """Celery任务监控服务"""

    def __init__(self):
        self.service_name = "CeleryMonitoringService"

    def get_all_circuit_breaker_states(self) -> Dict[str, Any]:
        """获取所有任务熔断器状态"""
        try:
            states = task_circuit_manager.get_all_states()
            return {
                "timestamp": datetime.now().isoformat(),
                "service": self.service_name,
                "total_tasks": len(states),
                "states": states,
            }
        except Exception as e:
            logger.error(f"Failed to get circuit breaker states: {e}")
            raise HTTPException(
                status_code=500, detail=f"Monitor service error: {str(e)}"
            )

    def get_task_circuit_breaker_state(self, task_name: str) -> Dict[str, Any]:
        """获取特定任务的熔断器状态"""
        try:
            breaker = task_circuit_manager.get_or_create_breaker(task_name)
            return {
                "timestamp": datetime.now().isoformat(),
                "task_name": task_name,
                "state": breaker.get_state_info(),
            }
        except Exception as e:
            logger.error(f"Failed to get circuit breaker state for {task_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Task monitor error: {str(e)}")

    def reset_task_circuit_breaker(self, task_name: str) -> Dict[str, Any]:
        """重置特定任务的熔断器"""
        try:
            breaker = task_circuit_manager.get_or_create_breaker(task_name)
            # 强制转换到CLOSED状态
            breaker._transition_state(TaskCircuitState.CLOSED)

            logger.info(f"Reset circuit breaker for task: {task_name}")

            return {
                "timestamp": datetime.now().isoformat(),
                "task_name": task_name,
                "message": "Circuit breaker reset successfully",
                "new_state": breaker.get_state_info(),
            }
        except Exception as e:
            logger.error(f"Failed to reset circuit breaker for {task_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

    def configure_task_circuit_breaker(
        self,
        task_name: str,
        failure_threshold: Optional[int] = None,
        timeout: Optional[int] = None,
        soft_time_limit: Optional[int] = None,
        time_limit: Optional[int] = None,
        half_open_attempts: Optional[int] = None,
    ) -> Dict[str, Any]:
        """配置任务熔断器参数"""
        try:
            # 创建新的配置
            config = CeleryTaskCircuitBreakerConfig(
                task_name=task_name,
                failure_threshold=failure_threshold
                or settings.CELERY_TASK_FAILURE_THRESHOLD,
                timeout=timeout or settings.CELERY_TASK_CIRCUIT_TIMEOUT,
                soft_time_limit=soft_time_limit or settings.CELERY_TASK_SOFT_TIMEOUT,
                time_limit=time_limit or settings.CELERY_TASK_HARD_TIMEOUT,
                half_open_attempts=half_open_attempts
                or settings.CELERY_TASK_HALF_OPEN_ATTEMPTS,
                enable_timeout_protection=settings.CELERY_ENABLE_TIMEOUT_PROTECTION,
                enable_failure_protection=settings.CELERY_ENABLE_FAILURE_PROTECTION,
            )

            # 更新配置
            task_circuit_manager.register_task_config(task_name, config)

            logger.info(f"Updated circuit breaker config for task: {task_name}")

            return {
                "timestamp": datetime.now().isoformat(),
                "task_name": task_name,
                "message": "Configuration updated successfully",
                "new_config": {
                    "failure_threshold": config.failure_threshold,
                    "timeout": config.timeout,
                    "soft_time_limit": config.soft_time_limit,
                    "time_limit": config.time_limit,
                    "half_open_attempts": config.half_open_attempts,
                },
            }
        except Exception as e:
            logger.error(f"Failed to configure circuit breaker for {task_name}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Configuration failed: {str(e)}"
            )

    def get_global_statistics(self) -> Dict[str, Any]:
        """获取全局统计信息"""
        try:
            states = task_circuit_manager.get_all_states()

            # 统计各状态的任务数量
            state_counts = {}
            total_failures = 0
            total_successes = 0
            total_timeouts = 0

            for task_info in states.values():
                state = task_info["state"]
                state_counts[state] = state_counts.get(state, 0) + 1
                total_failures += task_info["failure_count"]
                total_successes += task_info["success_count"]
                total_timeouts += task_info["timeout_count"]

            total_requests = total_failures + total_successes

            return {
                "timestamp": datetime.now().isoformat(),
                "service": self.service_name,
                "summary": {
                    "total_tasks": len(states),
                    "total_requests": total_requests,
                    "total_failures": total_failures,
                    "total_successes": total_successes,
                    "total_timeouts": total_timeouts,
                    "overall_failure_rate": (
                        round((total_failures / total_requests * 100), 2)
                        if total_requests > 0
                        else 0
                    ),
                },
                "state_distribution": state_counts,
                "configuration": {
                    "default_timeout": settings.CELERY_TASK_DEFAULT_TIMEOUT,
                    "failure_threshold": settings.CELERY_TASK_FAILURE_THRESHOLD,
                    "circuit_timeout": settings.CELERY_TASK_CIRCUIT_TIMEOUT,
                },
            }
        except Exception as e:
            logger.error(f"Failed to get global statistics: {e}")
            raise HTTPException(
                status_code=500, detail=f"Statistics service error: {str(e)}"
            )


# 创建全局服务实例
celery_monitoring_service = CeleryMonitoringService()


# API路由辅助函数
def get_celery_monitoring_service() -> CeleryMonitoringService:
    """获取Celery监控服务实例"""
    return celery_monitoring_service


# 导出主要类和服务
__all__ = [
    "CeleryMonitoringService",
    "celery_monitoring_service",
    "get_celery_monitoring_service",
]
