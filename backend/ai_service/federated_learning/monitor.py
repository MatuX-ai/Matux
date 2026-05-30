"""
联邦学习监控系统
实时监控训练进度、性能指标和系统健康状态
"""

import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
import logging
from typing import Any, Dict, List, Optional

from ..fl_models import FLAggregationResult, FLTrainingConfig, FLTrainingProgress

logger = logging.getLogger(__name__)


class MetricsCollector:
    """指标收集器"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = defaultdict(lambda: deque(maxlen=max_history))
        self.alert_thresholds = {
            "aggregation_success_rate": 0.8,
            "privacy_epsilon": 10.0,
            "training_latency": 300.0,  # 5分钟
            "participant_drop_rate": 0.3,
        }

    def record_metric(
        self, metric_name: str, value: float, tags: Dict[str, str] = None
    ):
        """记录指标"""
        timestamp = datetime.now()
        record = {"timestamp": timestamp, "value": value, "tags": tags or {}}
        self.metrics_history[metric_name].append(record)
        self._check_alerts(metric_name, value)

    def _check_alerts(self, metric_name: str, value: float):
        """检查告警条件"""
        threshold = self.alert_thresholds.get(metric_name)
        if threshold and value > threshold:
            logger.warning(f"告警: {metric_name} 超过阈值 {threshold}, 当前值: {value}")

    def get_recent_metrics(self, metric_name: str, minutes: int = 60) -> List[Dict]:
        """获取最近的指标数据"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        history = self.metrics_history[metric_name]
        return [record for record in history if record["timestamp"] >= cutoff_time]

    def calculate_statistics(
        self, metric_name: str, minutes: int = 60
    ) -> Dict[str, float]:
        """计算指标统计信息"""
        recent_data = self.get_recent_metrics(metric_name, minutes)
        if not recent_data:
            return {}

        values = [record["value"] for record in recent_data]
        return {
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1] if values else None,
        }


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.active_alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.notification_callbacks = []

    def add_notification_callback(self, callback):
        """添加通知回调"""
        self.notification_callbacks.append(callback)

    def trigger_alert(self, alert_type: str, message: str, severity: str = "warning"):
        """触发告警"""
        alert_id = f"{alert_type}_{datetime.now().timestamp()}"
        alert = {
            "id": alert_id,
            "type": alert_type,
            "message": message,
            "severity": severity,
            "timestamp": datetime.now(),
            "status": "active",
        }

        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)

        # 触发通知
        for callback in self.notification_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"通知回调执行失败: {e}")

        logger.warning(f"告警触发 [{severity}]: {message}")
        return alert_id

    def resolve_alert(self, alert_id: str):
        """解决告警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id]["status"] = "resolved"
            self.active_alerts[alert_id]["resolved_at"] = datetime.now()
            logger.info(f"告警已解决: {alert_id}")


class PerformanceTracker:
    """性能跟踪器"""

    def __init__(self):
        self.training_sessions = {}
        self.performance_metrics = defaultdict(list)

    def start_session(self, session_id: str, config: FLTrainingConfig):
        """开始训练会话跟踪"""
        self.training_sessions[session_id] = {
            "config": config,
            "start_time": datetime.now(),
            "round_metrics": [],
            "status": "running",
        }

    def record_round_performance(
        self, session_id: str, round_num: int, metrics: Dict[str, Any]
    ):
        """记录轮次性能"""
        if session_id not in self.training_sessions:
            return

        round_data = {
            "round": round_num,
            "timestamp": datetime.now(),
            "metrics": metrics,
        }
        self.training_sessions[session_id]["round_metrics"].append(round_data)

    def complete_session(self, session_id: str):
        """完成训练会话"""
        if session_id in self.training_sessions:
            self.training_sessions[session_id]["status"] = "completed"
            self.training_sessions[session_id]["end_time"] = datetime.now()

    def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话摘要"""
        if session_id not in self.training_sessions:
            return None

        session = self.training_sessions[session_id]
        round_metrics = session["round_metrics"]

        if not round_metrics:
            return None

        # 计算汇总统计
        total_time = (
            session.get("end_time", datetime.now()) - session["start_time"]
        ).total_seconds()

        # 收敛分析
        losses = [m["metrics"].get("loss", 0) for m in round_metrics]
        convergence_rate = self._calculate_convergence_rate(losses)

        return {
            "session_id": session_id,
            "total_rounds": len(round_metrics),
            "total_time_seconds": total_time,
            "average_round_time": (
                total_time / len(round_metrics) if round_metrics else 0
            ),
            "final_loss": losses[-1] if losses else 0,
            "best_loss": min(losses) if losses else 0,
            "convergence_rate": convergence_rate,
            "participant_retention": self._calculate_participant_retention(
                round_metrics
            ),
        }

    def _calculate_convergence_rate(self, losses: List[float]) -> float:
        """计算收敛率"""
        if len(losses) < 2:
            return 0.0
        return (losses[0] - losses[-1]) / losses[0] if losses[0] > 0 else 0.0

    def _calculate_participant_retention(self, round_metrics: List[Dict]) -> float:
        """计算参与者留存率"""
        if not round_metrics:
            return 0.0

        initial_count = round_metrics[0]["metrics"].get("participant_count", 0)
        final_count = round_metrics[-1]["metrics"].get("participant_count", 0)

        return final_count / initial_count if initial_count > 0 else 0.0


class FLMonitor:
    """
    联邦学习监控系统主类
    """

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.performance_tracker = PerformanceTracker()
        self.system_health = {
            "last_check": datetime.now(),
            "status": "healthy",
            "components": {},
        }

    def start_training_session(self, training_id: str, config: FLTrainingConfig):
        """开始训练会话监控"""
        self.performance_tracker.start_session(training_id, config)
        self.metrics_collector.record_metric(
            "training_started", 1.0, {"training_id": training_id}
        )
        logger.info(f"开始监控训练会话: {training_id}")

    def record_aggregation_result(self, training_id: str, result: FLAggregationResult):
        """记录聚合结果"""
        # 记录聚合指标
        self.metrics_collector.record_metric(
            "aggregation_participants",
            float(result.participant_count),
            {"training_id": training_id, "round": result.aggregation_round},
        )

        # 记录隐私指标
        privacy_eps = result.privacy_metrics.get("epsilon", 0)
        self.metrics_collector.record_metric(
            "privacy_epsilon",
            privacy_eps,
            {"training_id": training_id, "round": result.aggregation_round},
        )

        # 记录收敛指标
        grad_variance = result.convergence_metrics.get("gradient_variance", 0)
        self.metrics_collector.record_metric(
            "gradient_variance",
            grad_variance,
            {"training_id": training_id, "round": result.aggregation_round},
        )

        logger.debug(
            f"记录聚合结果 - 训练: {training_id}, 轮次: {result.aggregation_round}"
        )

    def record_training_progress(self, progress: FLTrainingProgress):
        """记录训练进度"""
        self.metrics_collector.record_metric(
            "training_progress",
            progress.progress_percentage,
            {
                "training_id": progress.training_id,
                "round": progress.current_round,
                "status": progress.status.value,
            },
        )

        # 检查进度异常
        if progress.progress_percentage < 10 and progress.current_round > 5:
            self.alert_manager.trigger_alert(
                "slow_progress",
                f"训练 {progress.training_id} 进度缓慢: {progress.progress_percentage:.1f}%",
                "warning",
            )

    def complete_training_session(self, training_id: str):
        """完成训练会话"""
        self.performance_tracker.complete_session(training_id)
        self.metrics_collector.record_metric(
            "training_completed", 1.0, {"training_id": training_id}
        )
        logger.info(f"训练会话完成: {training_id}")

    def update_system_health(
        self, component: str, status: str, details: Dict[str, Any] = None
    ):
        """更新系统健康状态"""
        self.system_health["components"][component] = {
            "status": status,
            "details": details or {},
            "last_update": datetime.now(),
        }
        self.system_health["last_check"] = datetime.now()

        # 检查整体健康状态
        unhealthy_components = [
            comp
            for comp, info in self.system_health["components"].items()
            if info["status"] != "healthy"
        ]

        if unhealthy_components:
            self.system_health["status"] = "degraded"
            self.alert_manager.trigger_alert(
                "system_unhealthy",
                f"系统组件不健康: {', '.join(unhealthy_components)}",
                "critical",
            )
        else:
            self.system_health["status"] = "healthy"

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """获取监控摘要"""
        return {
            "system_health": self.system_health,
            "active_alerts": list(self.alert_manager.active_alerts.values()),
            "recent_metrics": {
                "aggregation_participants": self.metrics_collector.calculate_statistics(
                    "aggregation_participants"
                ),
                "privacy_epsilon": self.metrics_collector.calculate_statistics(
                    "privacy_epsilon"
                ),
                "training_progress": self.metrics_collector.calculate_statistics(
                    "training_progress"
                ),
            },
            "performance_summaries": {
                session_id: self.performance_tracker.get_session_summary(session_id)
                for session_id in list(
                    self.performance_tracker.training_sessions.keys()
                )[
                    -5:
                ]  # 最近5个会话
            },
        }

    def get_detailed_metrics(
        self, training_id: str = None, hours: int = 24
    ) -> Dict[str, Any]:
        """获取详细指标数据"""
        metrics_data = {}

        metric_names = [
            "aggregation_participants",
            "privacy_epsilon",
            "gradient_variance",
            "training_progress",
        ]

        for metric_name in metric_names:
            if training_id:
                # 过滤特定训练的数据
                recent_data = self.metrics_collector.get_recent_metrics(
                    metric_name, hours * 60
                )
                filtered_data = [
                    record
                    for record in recent_data
                    if record["tags"].get("training_id") == training_id
                ]
                metrics_data[metric_name] = filtered_data
            else:
                metrics_data[metric_name] = self.metrics_collector.get_recent_metrics(
                    metric_name, hours * 60
                )

        return metrics_data

    def export_monitoring_data(self, format: str = "json") -> str:
        """导出监控数据"""
        summary = self.get_monitoring_summary()

        if format.lower() == "json":
            return json.dumps(summary, default=str, indent=2)
        else:
            # 可以添加其他格式支持
            return json.dumps(summary, default=str)

    async def periodic_health_check(self, interval: int = 60):
        """周期性健康检查"""
        while True:
            try:
                # 这里可以添加具体的健康检查逻辑
                self.update_system_health("monitoring_system", "healthy")
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"健康检查失败: {e}")
                await asyncio.sleep(interval)
