"""
教育数据联邦学习协调器服务
扩展基础协调器以支持教育领域的特殊需求
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional, Set

from ...config.edu_data_config import edu_config
from ...models.edu_data_models import EduNodeRegistration, EduRegionalData, EduSubject
from ...security.edu_privacy_protection import audit_logger, dp_engine
from ..fl_models import EduFLTrainingConfig, FLParticipantInfo
from .coordinator_service import CoordinatorService

logger = logging.getLogger(__name__)


@dataclass
class EduTrainingSession:
    """教育训练会话"""

    training_id: str
    config: EduFLTrainingConfig
    participants: Set[str]
    current_round: int
    regional_data: Dict[str, EduRegionalData]
    subject_scores: Dict[EduSubject, List[float]]
    started_at: datetime
    last_activity: datetime
    privacy_budget_consumed: float = 0.0


class EducationCoordinatorService(CoordinatorService):
    """教育数据联邦学习协调器"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edu_training_sessions: Dict[str, EduTrainingSession] = {}
        self.edu_nodes: Dict[str, EduNodeRegistration] = {}
        self.regional_analytics_cache: Dict[str, Dict] = {}

    async def start_edu_training(self, config: EduFLTrainingConfig) -> str:
        """
        启动教育数据联邦学习训练

        Args:
            config: 教育训练配置

        Returns:
            训练ID
        """
        try:
            # 验证教育特定配置
            await self._validate_edu_config(config)

            # 检查参与节点可用性
            available_nodes = await self._get_available_edu_nodes(config.participants)
            if len(available_nodes) < edu_config.fl_min_participants:
                raise ValueError(
                    f"可用教育节点不足，需要至少{edu_config.fl_min_participants}个，当前只有{len(available_nodes)}个"
                )

            # 启动基础训练
            training_id = await self.start_training(config)

            # 创建教育训练会话
            edu_session = EduTrainingSession(
                training_id=training_id,
                config=config,
                participants=set(available_nodes),
                current_round=0,
                regional_data={},
                subject_scores={subject: [] for subject in config.edu_subjects},
                started_at=datetime.now(),
                last_activity=datetime.now(),
            )

            self.edu_training_sessions[training_id] = edu_session

            # 记录审计日志
            audit_logger.log_privacy_operation(
                "edu_training_start",
                {
                    "training_id": training_id,
                    "participants": list(available_nodes),
                    "subjects": config.edu_subjects,
                    "regions": len(
                        set(node.region_id for node in self.edu_nodes.values())
                    ),
                    "privacy_budget": config.privacy_budget,
                },
            )

            logger.info(f"教育数据联邦学习训练已启动: {training_id}")
            logger.info(
                f"参与节点: {len(available_nodes)}, 学科: {len(config.edu_subjects)}"
            )

            return training_id

        except Exception as e:
            logger.error(f"启动教育训练失败: {e}")
            raise

    async def register_edu_node(self, node_info: EduNodeRegistration) -> bool:
        """
        注册教育数据节点

        Args:
            node_info: 节点注册信息

        Returns:
            注册是否成功
        """
        try:
            # 验证节点信息
            if not await self._validate_edu_node(node_info):
                return False

            # 检查区域配额
            region_nodes = [
                n for n in self.edu_nodes.values() if n.region_id == node_info.region_id
            ]

            if len(region_nodes) >= edu_config.edu_max_nodes_per_region:
                logger.warning(
                    f"区域 {node_info.region_id} 的节点数量已达上限 "
                    f"({edu_config.edu_max_nodes_per_region})"
                )
                return False

            # 注册为基础联邦学习参与者
            fl_participant = FLParticipantInfo(
                participant_id=node_info.node_id,
                role="participant",
                status="online",
                capabilities=[
                    "education_data",
                    "secure_computation",
                    "differential_privacy",
                ]
                + node_info.capabilities,
                resource_limits={"cpu": "4", "memory": "8Gi"},
            )

            success = await self.register_participant(fl_participant)

            if success:
                self.edu_nodes[node_info.node_id] = node_info
                logger.info(
                    f"教育节点注册成功: {node_info.node_name} ({node_info.node_id})"
                )

                # 记录审计日志
                audit_logger.log_privacy_operation(
                    "node_registration",
                    {
                        "node_id": node_info.node_id,
                        "node_name": node_info.node_name,
                        "region_id": node_info.region_id,
                        "node_type": node_info.node_type.value,
                    },
                )

                return True
            else:
                logger.error(f"基础参与者注册失败: {node_info.node_id}")
                return False

        except Exception as e:
            logger.error(f"注册教育节点失败: {e}")
            return False

    async def collect_edu_model_updates(
        self, training_id: str, round_number: int
    ) -> List[Dict[str, Any]]:
        """
        收集教育模型更新

        Args:
            training_id: 训练ID
            round_number: 轮次编号

        Returns:
            模型更新列表
        """
        try:
            # 获取基础模型更新
            model_updates = await self.collect_model_updates(training_id, round_number)

            # 处理教育特定的更新
            edu_updates = []
            for update in model_updates:
                edu_update = await self._process_edu_model_update(update, training_id)
                if edu_update:
                    edu_updates.append(edu_update)

            logger.debug(f"收集到 {len(edu_updates)} 个教育模型更新")
            return edu_updates

        except Exception as e:
            logger.error(f"收集教育模型更新失败: {e}")
            return []

    async def aggregate_edu_models(
        self, training_id: str, model_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        聚合教育模型

        Args:
            training_id: 训练ID
            model_updates: 模型更新列表

        Returns:
            聚合后的模型参数
        """
        try:
            if training_id not in self.edu_training_sessions:
                raise ValueError(f"教育训练会话不存在: {training_id}")

            session = self.edu_training_sessions[training_id]

            # 执行基础聚合
            aggregated_params = await self.aggregate_models(training_id, model_updates)

            # 添加教育特定的聚合处理
            if session.config.edu_region_analysis:
                aggregated_params = await self._enhance_with_regional_analysis(
                    aggregated_params, training_id
                )

            # 更新隐私预算消耗
            privacy_cost = self._calculate_privacy_cost(len(model_updates))
            session.privacy_budget_consumed += privacy_cost

            # 记录审计日志
            audit_logger.log_privacy_operation(
                "model_aggregation",
                {
                    "training_id": training_id,
                    "round": session.current_round,
                    "participants": len(model_updates),
                    "privacy_cost": privacy_cost,
                    "total_privacy_consumed": session.privacy_budget_consumed,
                },
            )

            logger.info(
                f"教育模型聚合完成: {training_id}, 轮次 {session.current_round}"
            )
            return aggregated_params

        except Exception as e:
            logger.error(f"聚合教育模型失败: {e}")
            raise

    async def get_edu_training_progress(
        self, training_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取教育训练进度

        Args:
            training_id: 训练ID

        Returns:
            教育训练进度信息
        """
        try:
            # 获取基础进度
            base_progress = await self.get_training_status(training_id)
            if not base_progress:
                return None

            # 获取教育特定信息
            edu_info = {}
            if training_id in self.edu_training_sessions:
                session = self.edu_training_sessions[training_id]

                # 计算STEM得分
                stem_scores = self._calculate_stem_scores(session.subject_scores)

                # 获取区域分析
                regional_analysis = await self._get_regional_analysis(training_id)

                edu_info = {
                    "stem_scores": stem_scores,
                    "regional_analysis": regional_analysis,
                    "subject_progress": {
                        subject: len(scores)
                        for subject, scores in session.subject_scores.items()
                    },
                    "privacy_consumption": {
                        "consumed": session.privacy_budget_consumed,
                        "remaining": session.config.privacy_budget
                        - session.privacy_budget_consumed,
                        "utilization": session.privacy_budget_consumed
                        / session.config.privacy_budget,
                    },
                }

            # 合并进度信息
            progress_info = base_progress.dict()
            progress_info.update(edu_info)

            return progress_info

        except Exception as e:
            logger.error(f"获取教育训练进度失败: {e}")
            return None

    async def get_regional_education_insights(
        self, region_ids: List[str]
    ) -> Dict[str, Any]:
        """
        获取区域教育洞察

        Args:
            region_ids: 区域ID列表

        Returns:
            区域教育分析结果
        """
        try:
            insights = {}

            for region_id in region_ids:
                if region_id in self.regional_analytics_cache:
                    # 使用缓存数据
                    insights[region_id] = self.regional_analytics_cache[region_id]
                else:
                    # 计算新的分析结果
                    analysis = await self._compute_regional_analysis(region_id)
                    insights[region_id] = analysis
                    self.regional_analytics_cache[region_id] = analysis

            return insights

        except Exception as e:
            logger.error(f"获取区域教育洞察失败: {e}")
            return {}

    async def _validate_edu_config(self, config: EduFLTrainingConfig):
        """验证教育配置"""
        # 检查必需的教育配置
        if not config.edu_subjects:
            raise ValueError("必须指定至少一个学科")

        if not config.edu_grade_levels:
            raise ValueError("必须指定至少一个年级级别")

        # 验证隐私预算
        if config.privacy_budget > edu_config.fl_privacy_epsilon:
            raise ValueError(
                f"隐私预算不能超过系统限制 {edu_config.fl_privacy_epsilon}"
            )

        # 检查参与方
        if len(config.participants) < edu_config.fl_min_participants:
            raise ValueError(f"参与方数量不能少于 {edu_config.fl_min_participants}")

    async def _get_available_edu_nodes(self, node_ids: List[str]) -> List[str]:
        """获取可用的教育节点"""
        available_nodes = []

        for node_id in node_ids:
            if node_id in self.edu_nodes:
                # 检查节点是否在线
                participant_info = await self.get_participant_info(node_id)
                if participant_info and participant_info.status == "online":
                    available_nodes.append(node_id)

        return available_nodes

    async def _validate_edu_node(self, node_info: EduNodeRegistration) -> bool:
        """验证教育节点信息"""
        # 基本验证
        if not node_info.node_id or not node_info.node_name:
            logger.error("节点ID和名称不能为空")
            return False

        # 检查重复注册
        if node_info.node_id in self.edu_nodes:
            logger.warning(f"节点已注册: {node_info.node_id}")
            return True

        # 验证公钥格式
        if not node_info.public_key or len(node_info.public_key) < 50:
            logger.error("无效的公钥")
            return False

        # 验证区域ID
        if not node_info.region_id:
            logger.error("区域ID不能为空")
            return False

        return True

    async def _process_edu_model_update(
        self, update: Dict[str, Any], training_id: str
    ) -> Optional[Dict[str, Any]]:
        """处理教育模型更新"""
        try:
            # 添加教育特定的元数据
            edu_update = update.copy()

            if training_id in self.edu_training_sessions:
                session = self.edu_training_sessions[training_id]

                # 添加学科权重信息
                edu_update["subject_weights"] = {
                    subject: edu_config.get_subject_weight(subject)
                    for subject in session.config.edu_subjects
                }

                # 添加区域信息
                participant_id = update.get("participant_id")
                if participant_id and participant_id in self.edu_nodes:
                    node_info = self.edu_nodes[participant_id]
                    edu_update["region_id"] = node_info.region_id
                    edu_update["node_type"] = node_info.node_type.value

            return edu_update

        except Exception as e:
            logger.error(f"处理教育模型更新失败: {e}")
            return None

    async def _enhance_with_regional_analysis(
        self, params: Dict[str, Any], training_id: str
    ) -> Dict[str, Any]:
        """使用区域分析增强模型参数"""
        try:
            enhanced_params = params.copy()

            if training_id in self.edu_training_sessions:
                session = self.edu_training_sessions[training_id]

                # 收集区域数据
                regional_data = await self._collect_regional_data(
                    list(session.participants)
                )

                # 应用区域调整因子
                for param_name, param_value in params.items():
                    if isinstance(param_value, (int, float)):
                        # 基于区域特征调整参数
                        regional_factor = self._calculate_regional_factor(
                            param_name, regional_data
                        )
                        enhanced_params[param_name] = param_value * regional_factor

            return enhanced_params

        except Exception as e:
            logger.error(f"区域分析增强失败: {e}")
            return params

    async def _collect_regional_data(
        self, participant_ids: List[str]
    ) -> Dict[str, Any]:
        """收集区域数据"""
        regional_data = {}

        for participant_id in participant_ids:
            if participant_id in self.edu_nodes:
                node_info = self.edu_nodes[participant_id]
                region_id = node_info.region_id

                if region_id not in regional_data:
                    regional_data[region_id] = {
                        "nodes": [],
                        "total_students": 0,
                        "schools_count": 0,
                    }

                regional_data[region_id]["nodes"].append(participant_id)

        return regional_data

    def _calculate_regional_factor(
        self, param_name: str, regional_data: Dict[str, Any]
    ) -> float:
        """计算区域调整因子"""
        # 简化的区域因子计算
        base_factor = 1.0

        # 根据参与节点数量调整
        total_nodes = sum(len(data["nodes"]) for data in regional_data.values())
        if total_nodes > 0:
            avg_nodes_per_region = total_nodes / len(regional_data)
            base_factor *= 1.0 + avg_nodes_per_region * 0.01

        return base_factor

    def _calculate_stem_scores(
        self, subject_scores: Dict[EduSubject, List[float]]
    ) -> Dict[str, float]:
        """计算STEM综合得分"""
        stem_scores = {}

        for subject, scores in subject_scores.items():
            if scores:
                stem_scores[subject.value] = sum(scores) / len(scores)
            else:
                stem_scores[subject.value] = 0.0

        # 计算综合STEM得分
        if subject_scores:
            weighted_sum = sum(
                stem_scores.get(subject.value, 0)
                * edu_config.get_subject_weight(subject.value)
                for subject in [
                    EduSubject.MATH,
                    EduSubject.SCIENCE,
                    EduSubject.TECHNOLOGY,
                    EduSubject.ENGINEERING,
                ]
                if subject in subject_scores
            )
            stem_scores["overall"] = weighted_sum

        return stem_scores

    async def _get_regional_analysis(self, training_id: str) -> Dict[str, Any]:
        """获取区域分析结果"""
        try:
            if training_id not in self.edu_training_sessions:
                return {}

            session = self.edu_training_sessions[training_id]
            participating_regions = set(
                self.edu_nodes[node_id].region_id
                for node_id in session.participants
                if node_id in self.edu_nodes
            )

            regional_insights = await self.get_regional_education_insights(
                list(participating_regions)
            )

            return {
                "participating_regions": list(participating_regions),
                "region_count": len(participating_regions),
                "regional_insights": regional_insights,
            }

        except Exception as e:
            logger.error(f"获取区域分析失败: {e}")
            return {}

    async def _compute_regional_analysis(self, region_id: str) -> Dict[str, Any]:
        """计算区域分析"""
        try:
            # 收集该区域的所有节点
            region_nodes = [
                node for node in self.edu_nodes.values() if node.region_id == region_id
            ]

            analysis = {
                "region_id": region_id,
                "node_count": len(region_nodes),
                "schools_coverage": len(set(node.node_name for node in region_nodes)),
                "student_population_estimate": len(region_nodes) * 1000,  # 估算
                "last_updated": datetime.now().isoformat(),
            }

            return analysis

        except Exception as e:
            logger.error(f"计算区域分析失败: {e}")
            return {"region_id": region_id, "error": str(e)}

    def _calculate_privacy_cost(self, participant_count: int) -> float:
        """计算隐私成本"""
        # 简化的隐私成本计算
        base_cost = 0.05
        scale_factor = math.log(participant_count + 1)
        return base_cost * scale_factor

    async def cleanup_expired_sessions(self):
        """清理过期的训练会话"""
        try:
            current_time = datetime.now()
            expired_sessions = []

            for training_id, session in self.edu_training_sessions.items():
                # 检查会话是否超时
                if (current_time - session.last_activity) > timedelta(hours=24):
                    expired_sessions.append(training_id)

            # 清理过期会话
            for training_id in expired_sessions:
                del self.edu_training_sessions[training_id]
                logger.info(f"清理过期教育训练会话: {training_id}")

        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")


# 全局教育协调器实例
edu_coordinator = EducationCoordinatorService(
    secure_aggregator=None, privacy_engine=dp_engine  # 将在运行时注入
)
