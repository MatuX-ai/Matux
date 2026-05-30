"""
教育局数据对接联邦学习服务
提供教育数据联邦学习的核心业务逻辑和服务接口
"""

import asyncio
from datetime import datetime
import hashlib
from io import StringIO
import json
import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from ..ai_service.federated_learning import (
    CoordinatorService,
    FLMonitor,
    PrivacyEngine,
    SecureAggregator,
)
from ..ai_service.fl_models import (
    EduFLTrainingConfig,
    FLParticipantInfo,
    FLTrainingProgress,
    FLTrainingStatus,
)
from ..config.edu_data_config import edu_config
from ..models.edu_data_models import (
    EduAcademicPerformance,
    EduDataBatch,
    EduDataPrivacyLevel,
    EduGradeLevel,
    EduNodeRegistration,
    EduReportMetadata,
    EduReportRequest,
    EduStudentDemographics,
    EduSubject,
    EduTrainingConfig,
)
from ..utils.data_masking import DataMaskingService
from ..utils.data_quality import DataQualityChecker

logger = logging.getLogger(__name__)


class EduFederatedLearningService:
    """教育联邦学习核心服务类"""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> "EduFederatedLearningService":
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
            self.privacy_engine = PrivacyEngine(
                total_epsilon=edu_config.fl_privacy_epsilon, delta=1e-5
            )

            # 初始化安全聚合器
            self.aggregator = SecureAggregator(self.privacy_engine)

            # 初始化协调服务
            self.coordinator = CoordinatorService(
                secure_aggregator=self.aggregator, privacy_engine=self.privacy_engine
            )

            # 初始化监控服务
            self.monitor = FLMonitor()

            # 初始化数据脱敏服务
            self.data_masking_service = DataMaskingService()

            # 初始化数据质量检查器
            self.data_quality_checker = DataQualityChecker()

            # 存储活动训练
            self.active_trainings: Dict[str, FLTrainingProgress] = {}

            # 存储注册节点
            self.registered_nodes: Dict[str, EduNodeRegistration] = {}

            # 启动健康检查任务
            asyncio.create_task(self._health_check_task())

            logger.info("教育联邦学习服务初始化完成")

        except Exception as e:
            logger.error(f"教育联邦学习服务初始化失败: {e}")
            raise

    async def start_training(self, config: EduTrainingConfig) -> str:
        """启动教育数据联邦学习训练"""
        try:
            # 转换为联邦学习配置
            fl_config = EduFLTrainingConfig(
                model_name=config.model_name,
                rounds=config.rounds,
                participants=config.participants,
                privacy_budget=config.privacy_budget,
                noise_multiplier=config.noise_multiplier,
                clipping_threshold=config.clipping_threshold,
                learning_rate=config.learning_rate,
                batch_size=config.batch_size,
                timeout=config.timeout,
                edu_subjects=[s.value for s in config.subjects],
                edu_grade_levels=[g.value for g in config.grade_levels],
                edu_region_analysis=config.enable_region_comparison,
                edu_trend_prediction=config.enable_trend_analysis,
            )

            # 验证参与方
            valid_participants = await self._validate_participants(config.participants)
            if not valid_participants:
                raise ValueError("没有有效的参与方")

            # 启动协调服务中的训练
            training_id = await self.coordinator.start_training(fl_config)

            # 创建训练进度跟踪
            progress = FLTrainingProgress(
                training_id=training_id,
                current_round=0,
                total_rounds=config.rounds,
                status=FLTrainingStatus.INITIALIZING,
                progress_percentage=0.0,
                participants_status={p: "pending" for p in valid_participants},
            )

            self.active_trainings[training_id] = progress

            logger.info(f"教育数据联邦学习训练已启动: {training_id}")
            return training_id

        except Exception as e:
            logger.error(f"启动训练失败: {e}")
            raise

    async def get_training_status(
        self, training_id: str
    ) -> Optional[FLTrainingProgress]:
        """获取训练状态"""
        try:
            # 首先检查本地缓存
            if training_id in self.active_trainings:
                return self.active_trainings[training_id]

            # 从协调器获取状态
            coordinator_progress = await self.coordinator.get_training_status(
                training_id
            )
            if coordinator_progress:
                # 转换为教育扩展的进度对象
                edu_progress = FLTrainingProgress(
                    training_id=coordinator_progress.training_id,
                    current_round=coordinator_progress.current_round,
                    total_rounds=coordinator_progress.total_rounds,
                    status=coordinator_progress.status,
                    progress_percentage=coordinator_progress.progress_percentage,
                    metrics_history=coordinator_progress.metrics_history,
                    participants_status=coordinator_progress.participants_status,
                    estimated_completion_time=coordinator_progress.estimated_completion_time,
                )
                return edu_progress

            return None

        except Exception as e:
            logger.error(f"获取训练状态失败: {e}")
            return None

    async def monitor_training_progress(self, training_id: str):
        """监控训练进度"""
        try:
            while True:
                if training_id not in self.active_trainings:
                    break

                progress = await self.get_training_status(training_id)
                if progress:
                    self.active_trainings[training_id] = progress

                    # 检查是否完成
                    if progress.status in [
                        FLTrainingStatus.COMPLETED,
                        FLTrainingStatus.FAILED,
                    ]:
                        break

                await asyncio.sleep(30)  # 每30秒检查一次

        except Exception as e:
            logger.error(f"监控训练进度失败: {e}")

    async def generate_report(
        self, report_request: EduReportRequest
    ) -> EduReportMetadata:
        """生成教育数据分析报告"""
        try:
            # 这里应该调用报告生成服务
            # 暂时返回模拟数据
            report_metadata = EduReportMetadata(
                training_id=report_request.training_id,
                report_type=report_request.report_type,
                format=report_request.format,
                generated_by="system",
                file_path=f"./reports/output/report_{report_request.training_id}.{report_request.format}",
                file_size=1024000,  # 1MB模拟大小
                page_count=25 if report_request.format == "pdf" else None,
                data_sources=["federated_training_results"],
                privacy_level=EduDataPrivacyLevel.HIGH,
            )

            logger.info(f"教育报告生成完成: {report_metadata.report_id}")
            return report_metadata

        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            raise

    async def get_report_file(self, report_id: str) -> Optional[Dict[str, Any]]:
        """获取报告文件"""
        try:
            # 这里应该实现实际的文件检索逻辑
            # 暂时返回模拟响应
            return {
                "filename": f"report_{report_id}.pdf",
                "content_type": "application/pdf",
                "size": 1024000,
            }

        except Exception as e:
            logger.error(f"获取报告文件失败: {e}")
            return None

    async def register_node(self, node_info: EduNodeRegistration) -> bool:
        """注册教育数据节点"""
        try:
            # 验证节点信息
            if not node_info.node_id or not node_info.public_key:
                raise ValueError("节点ID和公钥不能为空")

            # 检查节点是否已注册
            if node_info.node_id in self.registered_nodes:
                logger.warning(f"节点已注册: {node_info.node_id}")
                return True

            # 验证公钥格式
            if not self._validate_public_key(node_info.public_key):
                raise ValueError("无效的公钥格式")

            # 存储节点信息
            self.registered_nodes[node_info.node_id] = node_info

            # 注册到协调器
            participant_info = FLParticipantInfo(
                participant_id=node_info.node_id,
                role="participant",
                status="online",
                capabilities=["education_data", "secure_computation"],
                resource_limits={"cpu": "4", "memory": "8Gi"},
            )

            success = await self.coordinator.register_participant(participant_info)

            if success:
                logger.info(
                    f"教育节点注册成功: {node_info.node_name} ({node_info.node_id})"
                )
                return True
            else:
                # 回滚节点注册
                self.registered_nodes.pop(node_info.node_id, None)
                return False

        except Exception as e:
            logger.error(f"注册节点失败: {e}")
            return False

    async def process_uploaded_data(
        self, file, metadata: Dict[str, Any]
    ) -> EduDataBatch:
        """处理上传的教育数据"""
        try:
            # 读取文件内容
            content = await file.read()

            # 根据文件类型解析数据
            if file.filename.endswith(".csv"):
                df = pd.read_csv(StringIO(content.decode("utf-8")))
            elif file.filename.endswith(".xlsx"):
                df = pd.read_excel(content)
            elif file.filename.endswith(".json"):
                data = json.loads(content.decode("utf-8"))
                df = pd.DataFrame(data)
            else:
                raise ValueError(f"不支持的文件格式: {file.filename}")

            # 数据质量检查
            if edu_config.data_quality_checks_enabled:
                quality_report = self.data_quality_checker.check_dataframe_quality(df)
                if not quality_report.is_valid:
                    raise ValueError(f"数据质量检查失败: {quality_report.issues}")

            # 数据脱敏处理
            if edu_config.data_masking_enabled:
                df = self.data_masking_service.mask_dataframe(
                    df, edu_config.pii_fields, edu_config.data_masking_level
                )

            # 转换为教育数据记录
            records = self._convert_to_edu_records(df, metadata)

            # 创建数据批次
            data_batch = EduDataBatch(
                source_id=metadata.get("source_id", "unknown"),
                data_type=metadata.get("data_type", "academic_performance"),
                records=records,
                checksum=hashlib.sha256(content).hexdigest(),
                encrypted=False,  # 暂时不加密
            )

            logger.info(f"教育数据处理完成: {len(records)} 条记录")
            return data_batch

        except Exception as e:
            logger.error(f"处理上传数据失败: {e}")
            raise

    async def get_system_statistics(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            # 获取协调器状态
            cluster_status = await self.coordinator.get_cluster_status()

            # 统计活跃训练
            active_trainings = len(
                [
                    t
                    for t in self.active_trainings.values()
                    if t.status == FLTrainingStatus.TRAINING
                ]
            )

            # 统计注册节点
            total_nodes = len(self.registered_nodes)
            online_nodes = len(
                [
                    n
                    for n in self.registered_nodes.values()
                    if self._is_node_online(n.node_id)
                ]
            )

            return {
                "total_trainings": len(self.active_trainings),
                "active_trainings": active_trainings,
                "completed_trainings": len(
                    [
                        t
                        for t in self.active_trainings.values()
                        if t.status == FLTrainingStatus.COMPLETED
                    ]
                ),
                "registered_nodes": total_nodes,
                "online_nodes": online_nodes,
                "cluster_status": cluster_status,
                "privacy_budget_used": self.privacy_engine.get_consumed_budget(),
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            # 检查各组件状态
            coordinator_healthy = await self._check_coordinator_health()
            privacy_engine_healthy = self._check_privacy_engine_health()
            data_services_healthy = self._check_data_services_health()

            overall_status = all(
                [coordinator_healthy, privacy_engine_healthy, data_services_healthy]
            )

            return {
                "overall_status": overall_status,
                "components": {
                    "coordinator": coordinator_healthy,
                    "privacy_engine": privacy_engine_healthy,
                    "data_services": data_services_healthy,
                },
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "overall_status": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def _validate_public_key(self, public_key: str) -> bool:
        """验证公钥格式"""
        try:
            # 简单的公钥格式验证
            return len(public_key) > 30 and public_key.startswith("-----BEGIN")
        except (AttributeError, TypeError):
            return False

    def _is_node_online(self, node_id: str) -> bool:
        """检查节点是否在线"""
        try:
            # 这里应该实现实际的心跳检查逻辑
            return node_id in self.registered_nodes
        except (KeyError, TypeError, AttributeError):
            return False

    async def _validate_participants(self, participants: List[str]) -> List[str]:
        """验证参与方有效性"""
        valid_participants = []
        for participant in participants:
            if participant in self.registered_nodes:
                valid_participants.append(participant)
        return valid_participants

    def _convert_to_edu_records(
        self, df: pd.DataFrame, metadata: Dict[str, Any]
    ) -> List[Any]:
        """将DataFrame转换为教育数据记录"""
        records = []
        data_type = metadata.get("data_type", "academic_performance")

        for _, row in df.iterrows():
            try:
                if data_type == "academic_performance":
                    record = EduAcademicPerformance(
                        student_id=str(row.get("student_id", "")),
                        subject=EduSubject(row.get("subject", "math")),
                        assessment_type="standardized_test",  # 默认值
                        score=float(row.get("score", 0)),
                        date_taken=datetime.now(),  # 默认当前时间
                        academic_year=str(row.get("academic_year", "2023-2024")),
                    )
                elif data_type == "student_demographics":
                    record = EduStudentDemographics(
                        student_id=str(row.get("student_id", "")),
                        age=(
                            int(row.get("age", 0)) if pd.notna(row.get("age")) else None
                        ),
                        gender=(
                            str(row.get("gender", ""))
                            if pd.notna(row.get("gender"))
                            else None
                        ),
                        grade_level=EduGradeLevel(row.get("grade_level", "elementary")),
                        school_id=str(row.get("school_id", "")),
                        region_id=str(row.get("region_id", "")),
                    )
                else:
                    # 默认处理为学术表现数据
                    record = EduAcademicPerformance(
                        student_id=str(row.get("student_id", "")),
                        subject=EduSubject.MATH,
                        assessment_type="standardized_test",
                        score=float(row.get("score", 0)),
                        date_taken=datetime.now(),
                        academic_year="2023-2024",
                    )

                records.append(record)
            except Exception as e:
                logger.warning(f"转换数据记录失败: {e}")
                continue

        return records

    async def _check_coordinator_health(self) -> bool:
        """检查协调器健康状态"""
        try:
            status = await self.coordinator.get_cluster_status()
            return status is not None
        except (Exception, asyncio.TimeoutError, ConnectionError):
            return False

    def _check_privacy_engine_health(self) -> bool:
        """检查隐私引擎健康状态"""
        try:
            # 检查隐私预算是否充足
            consumed_budget = self.privacy_engine.get_consumed_budget()
            return consumed_budget < edu_config.fl_privacy_epsilon
        except (AttributeError, ValueError, RuntimeError):
            return False

    def _check_data_services_health(self) -> bool:
        """检查数据服务健康状态"""
        try:
            return (
                self.data_masking_service is not None
                and self.data_quality_checker is not None
            )
        except:
            return False

    async def _health_check_task(self):
        """定期健康检查任务"""
        while True:
            try:
                health_status = await self.health_check()
                if not health_status.get("overall_status"):
                    logger.warning(f"教育联邦学习服务健康检查发现问题: {health_status}")

                await asyncio.sleep(300)  # 每5分钟检查一次

            except Exception as e:
                logger.error(f"健康检查任务出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再重试
