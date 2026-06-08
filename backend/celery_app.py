"""
Celery配置文件
用于异步任务处理，特别是视频转码任务
"""

import logging
import os
import platform

from celery import Celery
from celery.schedules import crontab
from celery.signals import task_failure

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Windows 兼容性处理
# Windows 不支持 fork()，prefork 模式会失败
# =============================================================================
IS_WINDOWS = platform.system() == "Windows"
if IS_WINDOWS:
    logger.warning(
        "Windows 环境检测到，Celery worker_pool 将使用 'solo' 模式\n"
        "注意：'solo' 模式是单进程，队列优先级将不起作用\n"
        "如需生产级并发，请使用 Linux/macOS 或 Docker 容器"
    )

# Worker pool 选择（Windows 不支持 prefork）


def _get_worker_pool() -> str:
    """获取适合当前平台的 worker pool"""
    if IS_WINDOWS:
        return "solo"
    # 优先使用 prefork (多进程)，回退到 threads 或 solo
    return os.getenv("CELERY_WORKER_POOL", "prefork")


# =============================================================================
# 创建 Celery 实例
# =============================================================================
celery_app = Celery("imato_multimedia")

# 确定 worker pool
_worker_pool = _get_worker_pool()
logger.info(f"Celery worker pool: {_worker_pool}")

# =============================================================================
# 配置 Celery
# =============================================================================
celery_app.conf.update(
    # Broker配置 (使用Redis)
    broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    # 结果后端配置
    result_backend=os.getenv("CELERY_RESULT_BACKEND",
                             "redis://localhost:6379/0"),
    # 任务序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # 时区配置
    timezone="Asia/Shanghai",
    enable_utc=True,
    # 任务路由
    task_routes={
        "tasks.video_transcode": {"queue": "video_processing"},
        "tasks.document_process": {"queue": "document_processing"},
        "tasks.thumbnail_generate": {"queue": "image_processing"},
        "tasks.cleanup_old_files": {"queue": "maintenance"},
    },
    # Worker配置
    worker_prefetch_multiplier=int(
        os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1")),
    worker_max_tasks_per_child=int(
        os.getenv("CELERY_WORKER_MAX_TASKS_PER_CHILD", "1000")),
    worker_pool=_worker_pool,  # Windows 兼容性
    # 任务结果过期时间 (24小时)
    result_expires=int(os.getenv("CELERY_RESULT_EXPIRES", "86400")),
    # 任务重试配置
    task_acks_late=os.getenv("CELERY_TASK_ACKS_LATE",
                             "true").lower() in ("true", "1", "yes"),
    task_reject_on_worker_lost=os.getenv(
        "CELERY_TASK_REJECT_ON_WORKER_LOST", "true").lower() in ("true", "1", "yes"),
    # 任务超时配置 (全局默认)
    task_soft_time_limit=int(
        os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "30")),  # 软超时30秒
    task_time_limit=int(os.getenv("CELERY_TASK_TIME_LIMIT", "60")),  # 硬超时60秒
    # 监控配置
    worker_send_task_events=os.getenv(
        "CELERY_WORKER_SEND_TASK_EVENTS", "true").lower() in ("true", "1", "yes"),
    task_send_sent_event=True,
    # 任务监控和追踪
    task_track_started=True,
    task_publish_retry=True,
    task_publish_retry_policy={
        "max_retries": 3,
        "interval_start": 0,
        "interval_step": 0.2,
        "interval_max": 0.5,
    },
    # 内存和性能优化
    worker_max_memory_per_child=int(
        os.getenv("CELERY_WORKER_MAX_MEMORY_PER_CHILD", "100000")),  # KB
    worker_disable_rate_limits=False,
)

# =============================================================================
# 自动发现任务（带错误处理）
# =============================================================================


def _discover_tasks():
    """安全发现任务模块"""
    try:
        celery_app.autodiscover_tasks(["tasks"])
        logger.info("任务自动发现完成")
    except ModuleNotFoundError as e:
        logger.error(f"tasks 模块未找到: {e}")
        logger.warning("请确保 tasks 目录存在且包含 __init__.py")
    except Exception as e:
        logger.error(f"任务自动发现失败: {e}")
        raise


_discover_tasks()

# =============================================================================
# 定期任务配置
# =============================================================================
celery_app.conf.beat_schedule = {
    # 清理旧的临时文件 (每天凌晨2点)
    "cleanup-old-files": {
        "task": "tasks.cleanup_old_files",
        "schedule": crontab(hour=2, minute=0),
        "args": (),
    },
    # 检查转码任务状态 (每5分钟)
    "check-transcoding-status": {
        "task": "tasks.check_transcoding_status",
        "schedule": 300.0,  # 5分钟
        "args": (),
    },
    # 清理失败的转码任务 (每小时)
    "cleanup-failed-transcodes": {
        "task": "tasks.cleanup_failed_transcodes",
        "schedule": 3600.0,  # 1小时
        "args": (),
    },
}


# 任务失败回调（通过 Celery 信号机制）
@task_failure.connect
def on_task_failure_handler(
    sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs
):
    """任务失败回调"""
    logger.error(f"Task {sender.name} failed: {exception}")


@celery_app.task(base=celery_app.Task)
def on_task_timeout(sender=None, task_id=None, **kwargs):
    """任务超时回调"""
    logger.warning(f"Task {sender.name} timed out: {task_id}")


# =============================================================================
# 尝试注册自定义任务基类（circuit_breaker 模块为可选，不存在时不阻塞）
# =============================================================================
try:
    # type: ignore[import-untyped]
    from middleware.celery_circuit_breaker import CircuitBreakerTask
    celery_app.conf.update(
        task_cls="middleware.celery_circuit_breaker:CircuitBreakerTask"
    )
    logger.info("CircuitBreakerTask 已注册")
except (ImportError, ModuleNotFoundError) as e:
    logger.info(f"celery_circuit_breaker 模块未安装，使用默认任务基类: {e}")
except Exception as e:
    logger.error(f"CircuitBreakerTask 注册失败: {e}")
    logger.info("回退到默认任务基类")

if __name__ == "__main__":
    celery_app.start()
