"""
联邦学习核心服务
协调各个组件提供统一的服务接口
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from ..ai_service.federated_learning import (
    CoordinatorService,
    FLMonitor,
    KubernetesManager,
    PrivacyEngine,
    SecureAggregator,
)
from ..ai_service.fl_models import (
    FLParticipantInfo,
    FLTrainingConfig,
    FLTrainingProgress,
    FLTrainingStatus,
)

logger = logging.getLogger(__name__)


class FederatedLearningService:
    """联邦学习核心服务类"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "FederatedLearningService":
        """获取服务实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._initialize_components()
            self._initialized = True

    def _initialize_components(self):
        """初始化核心组件"""
        try:
            # 初始化隐私引擎
            self.privacy_engine = PrivacyEngine(total_epsilon=1.0)

            # 初始化安全聚合器
            self.secure_aggregator = SecureAggregator(self.privacy_engine)

            # 初始化Kubernetes管理器
            self.k8s_manager = KubernetesManager()

            # 初始化协调器服务
            self.coordinator_service = CoordinatorService(
                self.k8s_manager, self.secure_aggregator
            )

            # 初始化监控系统
            self.monitor = FLMonitor()

            # 启动后台任务
            self._start_background_tasks()

            logger.info("联邦学习服务初始化完成")

        except Exception as e:
            logger.error(f"服务初始化失败: {e}")
            raise

    def _start_background_tasks(self):
        """启动后台任务"""
        # 启动健康检查
        asyncio.create_task(self._periodic_health_check())

        # 启动协调器初始化
        asyncio.create_task(self._initialize_coordinator())

    async def _initialize_coordinator(self):
        """初始化协调器"""
        await asyncio.sleep(1)  # 等待系统启动
        success = await self.coordinator_service.initialize_coordinator()
        if success:
            logger.info("协调器初始化成功")
        else:
            logger.warning("协调器初始化失败")

    async def _periodic_health_check(self):
        """周期性健康检查"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                await self.coordinator_service.health_check()
            except Exception as e:
                logger.error(f"健康检查失败: {e}")

    async def start_training(self, config: FLTrainingConfig) -> str:
        """启动联邦学习训练"""
        try:
            # 验证配置
            validation_result = await self.validate_training_config(config)
            if not validation_result.get("valid", False):
                raise ValueError(f"配置验证失败: {validation_result.get('errors', [])}")

            # 启动训练
            training_id = await self.coordinator_service.start_federated_training(
                config
            )

            logger.info(f"训练启动成功: {training_id}")
            return training_id

        except Exception as e:
            logger.error(f"启动训练失败: {e}")
            raise

    async def get_training_status(
        self, training_id: str
    ) -> Optional[FLTrainingProgress]:
        """获取训练状态"""
        try:
            return await self.coordinator_service.get_training_status(training_id)
        except Exception as e:
            logger.error(f"获取训练状态失败: {e}")
            return None

    async def list_trainings(
        self, status: Optional[str] = None, limit: int = 10
    ) -> List[FLTrainingProgress]:
        """列出训练任务"""
        try:
            # 这里应该查询持久化存储，目前返回内存中的数据
            all_trainings = list(self.coordinator_service.active_trainings.values())

            if status:
                filtered_trainings = [
                    t for t in all_trainings if t.status.value == status
                ]
            else:
                filtered_trainings = all_trainings

            # 按时间排序并限制数量
            sorted_trainings = sorted(
                filtered_trainings, key=lambda x: x.current_round, reverse=True
            )

            return sorted_trainings[:limit]

        except Exception as e:
            logger.error(f"列出训练失败: {e}")
            return []

    async def pause_training(self, training_id: str) -> bool:
        """暂停训练"""
        try:
            # 这里应该实现实际的暂停逻辑
            if training_id in self.coordinator_service.active_trainings:
                progress = self.coordinator_service.active_trainings[training_id]
                if progress.status == FLTrainingStatus.TRAINING:
                    progress.status = FLTrainingStatus.PAUSED
                    logger.info(f"训练已暂停: {training_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"暂停训练失败: {e}")
            return False

    async def resume_training(self, training_id: str) -> bool:
        """恢复训练"""
        try:
            # 这里应该实现实际的恢复逻辑
            if training_id in self.coordinator_service.active_trainings:
                progress = self.coordinator_service.active_trainings[training_id]
                if progress.status == FLTrainingStatus.PAUSED:
                    progress.status = FLTrainingStatus.TRAINING
                    # 重新启动训练循环
                    config = FLTrainingConfig(
                        training_id=training_id,
                        model_name="resumed",
                        rounds=1,
                        participants=[],
                    )
                    asyncio.create_task(
                        self.coordinator_service._training_loop(training_id, config)
                    )
                    logger.info(f"训练已恢复: {training_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"恢复训练失败: {e}")
            return False

    async def stop_training(self, training_id: str) -> bool:
        """停止训练"""
        try:
            if training_id in self.coordinator_service.active_trainings:
                progress = self.coordinator_service.active_trainings[training_id]
                progress.status = FLTrainingStatus.FAILED
                logger.info(f"训练已停止: {training_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"停止训练失败: {e}")
            return False

    async def list_participants(self) -> List[FLParticipantInfo]:
        """列出所有参与者"""
        try:
            return list(self.coordinator_service.participants.values())
        except Exception as e:
            logger.error(f"列出参与者失败: {e}")
            return []

    async def get_participant_info(
        self, participant_id: str
    ) -> Optional[FLParticipantInfo]:
        """获取参与者信息"""
        try:
            return self.coordinator_service.participants.get(participant_id)
        except Exception as e:
            logger.error(f"获取参与者信息失败: {e}")
            return None

    async def get_cluster_status(self) -> Dict[str, Any]:
        """获取集群状态"""
        try:
            return await self.coordinator_service.get_cluster_status()
        except Exception as e:
            logger.error(f"获取集群状态失败: {e}")
            return {}

    async def get_monitoring_metrics(
        self, training_id: Optional[str] = None, hours: int = 24
    ) -> Dict[str, Any]:
        """获取监控指标"""
        try:
            if training_id:
                return self.monitor.get_detailed_metrics(training_id, hours)
            else:
                return self.monitor.get_monitoring_summary()
        except Exception as e:
            logger.error(f"获取监控指标失败: {e}")
            return {}

    async def get_active_alerts(self) -> Dict[str, Any]:
        """获取活跃告警"""
        try:
            monitoring_data = self.monitor.get_monitoring_summary()
            return {
                "active_alerts": monitoring_data.get("active_alerts", []),
                "alert_count": len(monitoring_data.get("active_alerts", [])),
            }
        except Exception as e:
            logger.error(f"获取告警失败: {e}")
            return {}

    async def register_participant(self, participant_info: FLParticipantInfo) -> bool:
        """注册参与者"""
        try:
            success = self.secure_aggregator.add_participant(participant_info)
            if success:
                self.coordinator_service.participants[
                    participant_info.participant_id
                ] = participant_info
                logger.info(f"参与者注册成功: {participant_info.participant_id}")
            return success
        except Exception as e:
            logger.error(f"注册参与者失败: {e}")
            return False

    async def validate_training_config(
        self, config: FLTrainingConfig
    ) -> Dict[str, Any]:
        """验证训练配置"""
        try:
            errors = []

            # 验证基本参数
            if config.rounds <= 0:
                errors.append("训练轮数必须大于0")

            if config.privacy_budget <= 0:
                errors.append("隐私预算必须大于0")

            if config.noise_multiplier <= 0:
                errors.append("噪声乘数必须大于0")

            if config.learning_rate <= 0:
                errors.append("学习率必须大于0")

            if len(config.participants) < 2:
                errors.append("至少需要2个参与者")

            # 验证参与者存在性
            available_participants = list(self.coordinator_service.participants.keys())
            invalid_participants = [
                p for p in config.participants if p not in available_participants
            ]
            if invalid_participants:
                errors.append(f"无效的参与者: {invalid_participants}")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": [],  # 可以添加警告信息
            }

        except Exception as e:
            logger.error(f"验证配置失败: {e}")
            return {"valid": False, "errors": [str(e)], "warnings": []}

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            cluster_status = await self.get_cluster_status()
            monitoring_data = self.monitor.get_monitoring_summary()

            # 检查各组件状态
            components_healthy = (
                cluster_status.get("participants_online", 0) > 0
                and monitoring_data["system_health"]["status"] == "healthy"
            )

            return {
                "status": "healthy" if components_healthy else "degraded",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "coordinator": "healthy",
                    "aggregator": "healthy",
                    "privacy_engine": "healthy",
                    "monitoring": monitoring_data["system_health"]["status"],
                    "cluster": (
                        "healthy"
                        if cluster_status.get("participants_online", 0) > 0
                        else "unhealthy"
                    ),
                },
                "metrics": {
                    "participants_online": cluster_status.get("participants_online", 0),
                    "active_trainings": cluster_status.get("active_trainings", 0),
                    "alerts_count": len(monitoring_data.get("active_alerts", [])),
                },
            }

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    async def monitor_training_progress(self, training_id: str):
        """监控训练进度（后台任务）"""
        try:
            while True:
                progress = await self.get_training_status(training_id)
                if not progress or progress.status in [
                    FLTrainingStatus.COMPLETED,
                    FLTrainingStatus.FAILED,
                ]:
                    break

                # 记录进度到监控系统
                self.monitor.record_training_progress(progress)

                # 检查是否需要告警
                if progress.progress_percentage < 10 and progress.current_round > 5:
                    self.monitor.alert_manager.trigger_alert(
                        "slow_training",
                        f"训练 {training_id} 进度缓慢: {progress.progress_percentage:.1f}%",
                        "warning",
                    )

                await asyncio.sleep(30)  # 每30秒检查一次

        except Exception as e:
            logger.error(f"监控训练进度失败: {e}")
