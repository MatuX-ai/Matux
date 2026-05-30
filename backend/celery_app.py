"""
Celery配置文件
用于异步任务处理，特别是视频转码任务
"""

import logging
import os

from celery import Celery
from celery.schedules import crontab

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Celery实例
celery_app = Celery("imato_multimedia")

# 配置Celery
celery_app.conf.update(
    # Broker配置 (使用Redis)
    broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    # 结果后端配置
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
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
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_pool="prefork",
    # 任务结果过期时间 (24小时)
    result_expires=86400,
    # 任务重试配置
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # 任务超时配置 (全局默认)
    task_soft_time_limit=30,  # 软超时30秒
    task_time_limit=60,  # 硬超时60秒
    # 监控配置
    worker_send_task_events=True,
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
    worker_max_memory_per_child=100000,  # KB
    worker_disable_rate_limits=False,
)

# 自动发现任务
celery_app.autodiscover_tasks(["tasks"])

# 定期任务配置
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


# 添加任务失败和超时回调
@celery_app.task(base=celery_app.Task)
def on_task_failure(
    sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwargs
):
    """任务失败回调"""
    logger.error(f"Task {sender.name} failed: {exception}")
    # 可以在这里添加额外的失败处理逻辑


@celery_app.task(base=celery_app.Task)
def on_task_timeout(sender=None, task_id=None, **kwargs):
    """任务超时回调"""
    logger.warning(f"Task {sender.name} timed out: {task_id}")
    # 可以在这里添加超时处理逻辑


# 注册事件监听器
celery_app.events.state_handlers["task-failed"] = on_task_failure

celery_app.conf.update(
    # 添加自定义任务基类
    task_cls="middleware.celery_circuit_breaker:CircuitBreakerTask"
)

if __name__ == "__main__":
    celery_app.start()
