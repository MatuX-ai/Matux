import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from ..utils.blockchain_client import BlockchainClient
from .integral_decay_calculator import decay_calculator
from .reward_event_bus import RewardEvent, reward_event_bus

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型"""

    DAILY_DECAY = "daily_decay"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_REPORT = "monthly_report"
    ACTIVITY_CHECK = "activity_check"
    CUSTOM = "custom"


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """定时任务"""

    task_id: str
    name: str
    task_type: TaskType
    cron_expression: str  # cron表达式
    function: Callable
    params: Dict[str, Any]
    enabled: bool
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    failure_count: int


class IntegralDecayScheduler:
    """积分衰减定时调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.tasks: Dict[str, ScheduledTask] = {}
        self.blockchain_client = BlockchainClient()
        self._initialize_scheduled_tasks()

    def _initialize_scheduled_tasks(self):
        """初始化预定任务"""
        # 每日凌晨2点执行积分衰减
        self.register_task(
            task_id="daily_integral_decay",
            name="每日积分衰减计算",
            task_type=TaskType.DAILY_DECAY,
            cron_expression="0 2 * * *",  # 每天凌晨2点
            function=self._execute_daily_decay,
            params={"batch_size": 1000},
            enabled=True,
        )

        # 每周一上午9点发送周报
        self.register_task(
            task_id="weekly_decay_summary",
            name="每周衰减汇总报告",
            task_type=TaskType.WEEKLY_SUMMARY,
            cron_expression="0 9 * * 1",  # 每周一9点
            function=self._send_weekly_summary,
            params={},
            enabled=True,
        )

        # 每月1号上午10点发送月报
        self.register_task(
            task_id="monthly_decay_report",
            name="每月衰减详细报告",
            task_type=TaskType.MONTHLY_REPORT,
            cron_expression="0 10 1 * *",  # 每月1号10点
            function=self._send_monthly_report,
            params={},
            enabled=True,
        )

        # 每小时检查用户活动状态
        self.register_task(
            task_id="hourly_activity_check",
            name="小时级用户活动检查",
            task_type=TaskType.ACTIVITY_CHECK,
            cron_expression="0 * * * *",  # 每小时整点
            function=self._check_user_activity,
            params={"threshold_hours": 24},
            enabled=True,
        )

    def register_task(
        self,
        task_id: str,
        name: str,
        task_type: TaskType,
        cron_expression: str,
        function: Callable,
        params: Dict[str, Any],
        enabled: bool = True,
    ):
        """注册定时任务"""
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            task_type=task_type,
            cron_expression=cron_expression,
            function=function,
            params=params,
            enabled=enabled,
            last_run=None,
            next_run=None,
            run_count=0,
            failure_count=0,
        )

        self.tasks[task_id] = task
        logger.info(f"定时任务已注册: {name} ({task_id})")

    def start_scheduler(self):
        """启动调度器"""
        try:
            # 添加所有启用的任务到调度器
            for task in self.tasks.values():
                if task.enabled:
                    self._add_job_to_scheduler(task)

            self.scheduler.start()
            logger.info("积分衰减调度器已启动")

        except Exception as e:
            logger.error(f"启动调度器失败: {e}")
            raise

    def stop_scheduler(self):
        """停止调度器"""
        try:
            self.scheduler.shutdown()
            logger.info("积分衰减调度器已停止")
        except Exception as e:
            logger.error(f"停止调度器失败: {e}")

    def _add_job_to_scheduler(self, task: ScheduledTask):
        """将任务添加到调度器"""
        try:
            trigger = CronTrigger.from_crontab(task.cron_expression)

            self.scheduler.add_job(
                func=self._execute_task_wrapper,
                trigger=trigger,
                id=task.task_id,
                name=task.name,
                args=[task],
                misfire_grace_time=300,  # 5分钟宽限期
            )

            logger.debug(f"任务已添加到调度器: {task.name}")

        except Exception as e:
            logger.error(f"添加任务到调度器失败 {task.name}: {e}")

    async def _execute_task_wrapper(self, task: ScheduledTask):
        """任务执行包装器"""
        try:
            task.last_run = datetime.now()
            task.run_count += 1

            logger.info(f"开始执行任务: {task.name}")

            # 执行具体任务
            if asyncio.iscoroutinefunction(task.function):
                await task.function(**task.params)
            else:
                task.function(**task.params)

            task.next_run = self._calculate_next_run(task)
            logger.info(f"任务执行完成: {task.name}")

        except Exception as e:
            task.failure_count += 1
            logger.error(f"任务执行失败 {task.name}: {e}")
            # 可以在这里添加失败重试逻辑

    async def _execute_daily_decay(self, batch_size: int = 1000):
        """执行每日积分衰减"""
        try:
            logger.info("开始执行每日积分衰减计算")

            # 获取所有用户积分数据（分批处理）
            user_points = await self._get_user_points_batch(batch_size)
            user_levels = await self._get_user_levels()

            # 批量计算衰减
            decay_results = decay_calculator.bulk_calculate_decay(
                user_points, user_levels
            )

            # 应用衰减到区块链
            applied_count = 0
            failed_count = 0

            for user_id, decay_amount in decay_results.items():
                if decay_amount > 0:
                    success = await self._apply_decay_to_blockchain(
                        user_id, decay_amount
                    )
                    if success:
                        applied_count += 1
                        # 更新用户活动状态
                        decay_calculator.update_user_activity(user_id)
                    else:
                        failed_count += 1

            # 发送衰减完成事件
            event = RewardEvent(
                event_type="daily_decay_completed",
                user_id=0,  # 系统事件
                data={
                    "total_users": len(decay_results),
                    "users_with_decay": sum(1 for d in decay_results.values() if d > 0),
                    "applied_count": applied_count,
                    "failed_count": failed_count,
                    "total_decay_points": sum(decay_results.values()),
                },
                timestamp=datetime.now(),
            )

            await reward_event_bus.publish(event)

            logger.info(
                f"每日积分衰减执行完成: "
                f"总计{len(decay_results)}用户, "
                f"{sum(1 for d in decay_results.values() if d > 0)}个用户产生衰减, "
                f"成功应用{applied_count}个"
            )

        except Exception as e:
            logger.error(f"每日积分衰减执行失败: {e}")
            raise

    async def _send_weekly_summary(self):
        """发送每周衰减汇总"""
        try:
            logger.info("生成每周衰减汇总报告")

            # 获取本周衰减统计数据
            weekly_stats = await self._get_weekly_decay_statistics()

            # 发送报告到管理员或相关服务
            await self._send_report_email("weekly_decay_summary", weekly_stats)

            logger.info("每周衰减汇总报告已发送")

        except Exception as e:
            logger.error(f"发送每周汇总失败: {e}")

    async def _send_monthly_report(self):
        """发送每月详细报告"""
        try:
            logger.info("生成每月衰减详细报告")

            # 获取本月详细衰减数据
            monthly_data = await self._get_monthly_decay_details()

            # 生成详细报告
            report = {
                "period": "monthly",
                "generated_at": datetime.now().isoformat(),
                "statistics": monthly_data,
                "top_decay_users": await self._get_top_decay_users(100),
                "recommendations": self._generate_decay_recommendations(monthly_data),
            }

            # 保存报告
            await self._save_monthly_report(report)

            logger.info("每月衰减详细报告已生成")

        except Exception as e:
            logger.error(f"生成每月报告失败: {e}")

    async def _check_user_activity(self, threshold_hours: int = 24):
        """检查用户活动状态"""
        try:
            inactive_users = await self._find_inactive_users(threshold_hours)

            if inactive_users:
                logger.info(f"发现{len(inactive_users)}个不活跃用户")

                # 发送提醒通知
                for user_id in inactive_users:
                    await self._send_activity_reminder(user_id)

        except Exception as e:
            logger.error(f"检查用户活动状态失败: {e}")

    async def _get_user_points_batch(self, batch_size: int) -> Dict[int, int]:
        """获取用户积分批次数据"""
        # 这里应该调用用户服务或数据库获取用户积分
        # 模拟实现
        return {i: 1000 + (i % 1000) for i in range(1, min(batch_size + 1, 10000))}

    async def _get_user_levels(self) -> Dict[int, str]:
        """获取用户等级信息"""
        # 模拟实现
        return {i: "standard" if i % 3 != 0 else "vip" for i in range(1, 10000)}

    async def _apply_decay_to_blockchain(self, user_id: int, decay_amount: int) -> bool:
        """应用衰减到区块链"""
        try:
            result = await self.blockchain_client.invoke_integral_chaincode(
                function="applyDecay",
                args=[str(user_id), str(decay_amount), "Daily automatic decay"],
            )

            return result.get("success", False)

        except Exception as e:
            logger.error(f"应用衰减到区块链失败 用户{user_id}: {e}")
            return False

    async def _get_weekly_decay_statistics(self) -> Dict[str, Any]:
        """获取每周衰减统计"""
        # 实现统计逻辑
        return {
            "week_start": (datetime.now() - timedelta(days=7)).date().isoformat(),
            "week_end": datetime.now().date().isoformat(),
            "total_decay_points": 15000,
            "affected_users": 1250,
            "average_decay_per_user": 12.0,
        }

    async def _get_monthly_decay_details(self) -> Dict[str, Any]:
        """获取每月衰减详情"""
        return {
            "month": datetime.now().strftime("%Y-%m"),
            "daily_averages": [100, 120, 95, 110, 130, 85, 90],  # 示例数据
            "user_category_breakdown": {
                "vip": {"count": 200, "avg_decay": 8.5},
                "standard": {"count": 1000, "avg_decay": 15.2},
                "beginner": {"count": 500, "avg_decay": 5.1},
            },
        }

    async def _get_top_decay_users(self, limit: int) -> List[Dict[str, Any]]:
        """获取衰减最多的用户"""
        # 模拟实现
        return [
            {"user_id": i, "decay_points": 1000 - i * 2, "rank": i + 1}
            for i in range(limit)
        ]

    async def _find_inactive_users(self, threshold_hours: int) -> List[int]:
        """查找不活跃用户"""
        # 模拟实现
        return [1001, 1002, 1003]  # 示例用户ID

    async def _send_activity_reminder(self, user_id: int):
        """发送活动提醒"""
        logger.info(f"向用户{user_id}发送活动提醒")
        # 实现提醒发送逻辑

    async def _send_report_email(self, report_type: str, data: Dict[str, Any]):
        """发送报告邮件"""
        logger.info(f"发送{report_type}报告邮件")
        # 实现邮件发送逻辑

    def _generate_decay_recommendations(self, data: Dict[str, Any]) -> List[str]:
        """生成衰减建议"""
        recommendations = []

        avg_decay = data.get("average_decay_per_user", 0)
        if avg_decay > 20:
            recommendations.append("建议降低衰减率以提高用户留存")
        elif avg_decay < 5:
            recommendations.append("可以适当提高衰减率以增加用户活跃度")

        return recommendations

    async def _save_monthly_report(self, report: Dict[str, Any]):
        """保存月度报告"""
        filename = f"decay_report_{datetime.now().strftime('%Y%m')}.json"
        # 实现报告保存逻辑
        logger.info(f"月度报告已保存: {filename}")

    def _calculate_next_run(self, task: ScheduledTask) -> Optional[datetime]:
        """计算下次运行时间"""
        try:
            trigger = CronTrigger.from_crontab(task.cron_expression)
            return trigger.get_next_fire_time(None, datetime.now())
        except Exception:
            return None

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        job = self.scheduler.get_job(task_id)

        return {
            "task_id": task.task_id,
            "name": task.name,
            "enabled": task.enabled,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "next_run": task.next_run.isoformat() if task.next_run else None,
            "run_count": task.run_count,
            "failure_count": task.failure_count,
            "scheduled": job is not None,
        }

    def get_all_task_statuses(self) -> List[Dict[str, Any]]:
        """获取所有任务状态"""
        return [self.get_task_status(task_id) for task_id in self.tasks.keys()]

    def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        try:
            if task_id in self.tasks:
                self.scheduler.pause_job(task_id)
                self.tasks[task_id].enabled = False
                logger.info(f"任务已暂停: {task_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"暂停任务失败 {task_id}: {e}")
            return False

    def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        try:
            if task_id in self.tasks:
                self.scheduler.resume_job(task_id)
                self.tasks[task_id].enabled = True
                logger.info(f"任务已恢复: {task_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"恢复任务失败 {task_id}: {e}")
            return False

    def run_task_immediately(self, task_id: str) -> bool:
        """立即运行任务"""
        try:
            if task_id in self.tasks:
                self.scheduler.modify_job(task_id, next_run_time=datetime.now())
                logger.info(f"任务将立即执行: {task_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"立即运行任务失败 {task_id}: {e}")
            return False


# 全局实例
decay_scheduler = IntegralDecayScheduler()
