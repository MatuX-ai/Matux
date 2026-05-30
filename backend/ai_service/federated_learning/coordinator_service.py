"""
Kubernetes协调器服务
管理联邦学习节点的动态发现、负载均衡和资源调度
"""

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from ..fl_models import (
    FLParticipantInfo,
    FLTrainingConfig,
    FLTrainingProgress,
    FLTrainingStatus,
)
from .monitor import FLMonitor
from .secure_aggregator import SecureAggregator

logger = logging.getLogger(__name__)


class KubernetesManager:
    """Kubernetes资源管理器"""

    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self.v1 = None
        self.apps_v1 = None
        self._initialize_k8s_client()

    def _initialize_k8s_client(self):
        """初始化Kubernetes客户端"""
        try:
            # 尝试加载集群内配置
            config.load_incluster_config()
        except config.ConfigException:
            try:
                # 尝试加载kubeconfig
                config.load_kube_config()
            except config.ConfigException:
                logger.warning("无法加载Kubernetes配置，使用模拟模式")
                self.v1 = None
                self.apps_v1 = None
                return

        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        logger.info("Kubernetes客户端初始化成功")

    async def discover_federated_nodes(self) -> List[FLParticipantInfo]:
        """发现联邦学习节点"""
        if not self.v1:
            return self._mock_discover_nodes()

        try:
            # 查找带有联邦学习标签的Pod
            label_selector = "app=federated-learning"
            pods = self.v1.list_namespaced_pod(
                namespace=self.namespace, label_selector=label_selector
            )

            participants = []
            for pod in pods.items:
                participant = FLParticipantInfo(
                    participant_id=pod.metadata.name,
                    role="participant",  # 简化处理，实际应根据标签确定
                    status="online" if pod.status.phase == "Running" else "offline",
                    last_heartbeat=datetime.now(),
                    capabilities=["training"],
                    resource_limits={
                        "cpu": pod.spec.containers[0].resources.limits.get("cpu", "1"),
                        "memory": pod.spec.containers[0].resources.limits.get(
                            "memory", "1Gi"
                        ),
                    },
                )
                participants.append(participant)

            logger.info(f"发现 {len(participants)} 个联邦学习节点")
            return participants

        except ApiException as e:
            logger.error(f"发现节点失败: {e}")
            return self._mock_discover_nodes()

    def _mock_discover_nodes(self) -> List[FLParticipantInfo]:
        """模拟节点发现（用于开发测试）"""
        mock_nodes = [
            FLParticipantInfo(
                participant_id=f"client-{i}",
                role="participant",
                status="online",
                last_heartbeat=datetime.now(),
                capabilities=["training", "encryption"],
                resource_limits={"cpu": "2", "memory": "4Gi"},
            )
            for i in range(3)  # 模拟3个客户端
        ]
        return mock_nodes

    async def scale_deployment(self, deployment_name: str, replicas: int) -> bool:
        """扩缩容部署"""
        if not self.apps_v1:
            logger.warning("Kubernetes客户端未初始化，跳过扩缩容")
            return True

        try:
            body = {"spec": {"replicas": replicas}}
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name, namespace=self.namespace, body=body
            )
            logger.info(f"部署 {deployment_name} 扩缩容至 {replicas} 个副本")
            return True
        except ApiException as e:
            logger.error(f"扩缩容失败: {e}")
            return False

    def get_node_resources(self) -> Dict[str, Any]:
        """获取节点资源信息"""
        if not self.v1:
            return {"nodes": 3, "total_cpu": "6", "total_memory": "12Gi"}

        try:
            nodes = self.v1.list_node()
            total_cpu = 0
            total_memory = 0

            for node in nodes.items:
                capacity = node.status.capacity
                cpu = int(capacity.get("cpu", 0))
                memory = self._parse_memory(capacity.get("memory", "0"))
                total_cpu += cpu
                total_memory += memory

            return {
                "nodes": len(nodes.items),
                "total_cpu": str(total_cpu),
                "total_memory": f"{total_memory}Gi",
            }
        except ApiException as e:
            logger.error(f"获取资源信息失败: {e}")
            return {"nodes": 0, "total_cpu": "0", "total_memory": "0Gi"}

    def _parse_memory(self, memory_str: str) -> float:
        """解析内存字符串为GiB"""
        if memory_str.endswith("Ki"):
            return int(memory_str[:-2]) / (1024 * 1024)
        elif memory_str.endswith("Mi"):
            return int(memory_str[:-2]) / 1024
        elif memory_str.endswith("Gi"):
            return int(memory_str[:-2])
        else:
            return int(memory_str) / (1024 * 1024 * 1024)


class CoordinatorService:
    """
    联邦学习协调器服务
    基于Kubernetes管理联邦学习训练流程
    """

    def __init__(
        self, kubernetes_manager: KubernetesManager, secure_aggregator: SecureAggregator
    ):
        self.k8s_manager = kubernetes_manager
        self.secure_aggregator = secure_aggregator
        self.monitor = FLMonitor()
        self.active_trainings: Dict[str, FLTrainingProgress] = {}
        self.participants: Dict[str, FLParticipantInfo] = {}
        self.health_check_interval = 30  # 秒

    async def initialize_coordinator(self) -> bool:
        """初始化协调器"""
        try:
            # 发现可用的联邦学习节点
            discovered_nodes = await self.k8s_manager.discover_federated_nodes()

            # 注册节点到安全聚合器
            for node in discovered_nodes:
                self.secure_aggregator.add_participant(node)
                self.participants[node.participant_id] = node

            logger.info(f"协调器初始化完成，发现 {len(discovered_nodes)} 个节点")
            return True

        except Exception as e:
            logger.error(f"协调器初始化失败: {e}")
            return False

    async def start_federated_training(self, config: FLTrainingConfig) -> str:
        """启动联邦学习训练"""
        try:
            training_id = config.training_id

            # 更新参与者列表
            available_participants = [
                pid
                for pid, info in self.participants.items()
                if info.status == "online"
            ]

            if len(available_participants) < 2:
                raise ValueError("可用参与者不足，至少需要2个")

            # 设置训练进度
            progress = FLTrainingProgress(
                training_id=training_id,
                current_round=0,
                total_rounds=config.rounds,
                status=FLTrainingStatus.INITIALIZING,
                progress_percentage=0.0,
                participants_status={pid: "ready" for pid in available_participants},
            )

            self.active_trainings[training_id] = progress
            self.monitor.start_training_session(training_id, config)

            # 启动训练循环
            asyncio.create_task(self._training_loop(training_id, config))

            logger.info(f"联邦学习训练启动: {training_id}")
            return training_id

        except Exception as e:
            logger.error(f"启动训练失败: {e}")
            raise

    async def _training_loop(self, training_id: str, config: FLTrainingConfig):
        """训练主循环"""
        try:
            progress = self.active_trainings[training_id]
            progress.status = FLTrainingStatus.TRAINING

            for round_num in range(config.rounds):
                progress.current_round = round_num
                progress.progress_percentage = (round_num / config.rounds) * 100

                logger.info(f"训练轮次 {round_num + 1}/{config.rounds}")

                # 1. 广播全局模型给所有参与者
                await self._broadcast_global_model(training_id, round_num)

                # 2. 等待参与者上传更新
                model_updates = await self._collect_model_updates(
                    training_id,
                    list(progress.participants_status.keys()),
                    timeout=config.timeout,
                )

                if not model_updates:
                    logger.warning(f"轮次 {round_num + 1} 未收到足够的模型更新")
                    continue

                # 3. 执行安全聚合
                progress.status = FLTrainingStatus.AGGREGATING
                aggregation_result = await self.secure_aggregator.secure_aggregate(
                    model_updates, config
                )

                # 4. 记录聚合结果
                self.monitor.record_aggregation_result(training_id, aggregation_result)

                # 5. 更新进度
                progress.metrics_history.append(
                    {
                        "round": round_num,
                        "participant_count": aggregation_result.participant_count,
                        "timestamp": datetime.now().isoformat(),
                        "privacy_epsilon": aggregation_result.privacy_metrics.get(
                            "epsilon", 0
                        ),
                    }
                )

                progress.status = FLTrainingStatus.TRAINING
                await asyncio.sleep(1)  # 模拟处理延迟

            # 训练完成
            progress.status = FLTrainingStatus.COMPLETED
            progress.progress_percentage = 100.0
            self.monitor.complete_training_session(training_id)

            logger.info(f"训练完成: {training_id}")

        except Exception as e:
            logger.error(f"训练循环出错: {e}")
            if training_id in self.active_trainings:
                self.active_trainings[training_id].status = FLTrainingStatus.FAILED

    async def _broadcast_global_model(self, training_id: str, round_num: int):
        """广播全局模型"""
        # 这里应该实现实际的模型广播逻辑
        logger.debug(f"广播全局模型 - 训练: {training_id}, 轮次: {round_num}")
        await asyncio.sleep(0.1)  # 模拟网络延迟

    async def _collect_model_updates(
        self, training_id: str, participant_ids: List[str], timeout: int
    ) -> List[Any]:
        """收集模型更新"""
        # 这里应该实现实际的更新收集逻辑
        logger.debug(
            f"收集模型更新 - 训练: {training_id}, 参与者: {len(participant_ids)}"
        )
        await asyncio.sleep(0.2)  # 模拟收集延迟
        return []  # 返回空列表作为示例

    async def get_training_status(
        self, training_id: str
    ) -> Optional[FLTrainingProgress]:
        """获取训练状态"""
        return self.active_trainings.get(training_id)

    async def get_cluster_status(self) -> Dict[str, Any]:
        """获取集群状态"""
        resources = self.k8s_manager.get_node_resources()
        participants_online = len(
            [p for p in self.participants.values() if p.status == "online"]
        )

        return {
            "total_nodes": resources["nodes"],
            "available_cpu": resources["total_cpu"],
            "available_memory": resources["total_memory"],
            "participants_online": participants_online,
            "participants_total": len(self.participants),
            "active_trainings": len(self.active_trainings),
            "aggregator_stats": self.secure_aggregator.get_aggregation_stats(),
        }

    async def health_check(self):
        """健康检查"""
        while True:
            try:
                # 更新参与者状态
                for participant_id, participant in self.participants.items():
                    # 检查心跳超时
                    if datetime.now() - participant.last_heartbeat > timedelta(
                        minutes=5
                    ):
                        participant.status = "offline"

                # 清理超时的训练
                expired_trainings = []
                for training_id, progress in self.active_trainings.items():
                    if (
                        progress.status == FLTrainingStatus.FAILED
                        and datetime.now()
                        - getattr(progress, "last_update", datetime.now())
                        > timedelta(hours=1)
                    ):
                        expired_trainings.append(training_id)

                for training_id in expired_trainings:
                    del self.active_trainings[training_id]
                    logger.info(f"清理超时训练: {training_id}")

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"健康检查出错: {e}")
                await asyncio.sleep(self.health_check_interval)

    def get_monitoring_data(self) -> Dict[str, Any]:
        """获取监控数据"""
        return self.monitor.get_monitoring_summary()
