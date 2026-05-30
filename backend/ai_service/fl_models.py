"""
联邦学习模型和配置定义
包含基础联邦学习模型和教育数据扩展模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field

# 教育数据模型导入
try:
    from ..models.edu_data_models import (
        EduAcademicPerformance,
        EduModelWeights,
        EduSchoolInfo,
        EduStudentDemographics,
        EduTrainingConfig,
        EduTrainingMetrics,
    )

    EDU_MODELS_AVAILABLE = True
except ImportError:
    EDU_MODELS_AVAILABLE = False
    EduTrainingConfig = None
    EduModelWeights = None
    EduTrainingMetrics = None
    EduStudentDemographics = None
    EduAcademicPerformance = None
    EduSchoolInfo = None


class FLTrainingStatus(str, Enum):
    """联邦学习训练状态"""

    INITIALIZING = "initializing"
    TRAINING = "training"
    AGGREGATING = "aggregating"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class FLParticipantRole(str, Enum):
    """参与者角色"""

    COORDINATOR = "coordinator"
    PARTICIPANT = "participant"
    AGGREGATOR = "aggregator"


class FLTrainingConfig(BaseModel):
    """联邦学习训练配置"""

    training_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str = Field(..., description="模型名称")
    rounds: int = Field(..., ge=1, le=1000, description="训练轮数")
    participants: List[str] = Field(..., description="参与方列表")
    aggregation_method: str = Field(default="fedavg", description="聚合方法")
    privacy_budget: float = Field(default=1.0, gt=0, description="隐私预算ε")
    noise_multiplier: float = Field(default=1.0, gt=0, description="噪声乘数")
    clipping_threshold: float = Field(default=1.0, gt=0, description="梯度裁剪阈值")
    learning_rate: float = Field(default=0.01, gt=0, description="学习率")
    batch_size: int = Field(default=32, ge=1, description="批次大小")
    created_at: datetime = Field(default_factory=datetime.now)
    timeout: int = Field(default=3600, description="超时时间(秒)")


class FLModelMetadata(BaseModel):
    """联邦学习模型元数据"""

    model_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    training_id: str = Field(..., description="关联的训练ID")
    model_weights: Dict[str, Any] = Field(..., description="模型权重")
    metrics: Dict[str, float] = Field(default={}, description="模型指标")
    participant_id: str = Field(..., description="参与者ID")
    round_number: int = Field(..., ge=0, description="训练轮次")
    timestamp: datetime = Field(default_factory=datetime.now)
    privacy_noise_added: bool = Field(default=False, description="是否添加隐私噪声")


class FLParticipantInfo(BaseModel):
    """联邦学习参与者信息"""

    participant_id: str = Field(..., description="参与者ID")
    role: FLParticipantRole = Field(..., description="参与者角色")
    status: str = Field(default="online", description="参与者状态")
    last_heartbeat: datetime = Field(default_factory=datetime.now)
    capabilities: List[str] = Field(default=[], description="支持的能力")
    resource_limits: Dict[str, Any] = Field(default={}, description="资源限制")


class FLAggregationResult(BaseModel):
    """聚合结果"""

    aggregated_weights: Dict[str, Any] = Field(..., description="聚合后的权重")
    participant_count: int = Field(..., ge=0, description="参与聚合的节点数")
    aggregation_round: int = Field(..., ge=0, description="聚合轮次")
    privacy_metrics: Dict[str, float] = Field(default={}, description="隐私指标")
    convergence_metrics: Dict[str, float] = Field(default={}, description="收敛指标")


class FLTrainingProgress(BaseModel):
    """训练进度"""

    training_id: str = Field(..., description="训练ID")
    current_round: int = Field(..., ge=0, description="当前轮次")
    total_rounds: int = Field(..., ge=1, description="总轮次")
    status: FLTrainingStatus = Field(..., description="训练状态")
    progress_percentage: float = Field(..., ge=0, le=100, description="进度百分比")
    metrics_history: List[Dict[str, Any]] = Field(default=[], description="指标历史")
    participants_status: Dict[str, str] = Field(default={}, description="参与者状态")
    estimated_completion_time: Optional[datetime] = Field(
        None, description="预计完成时间"
    )


# 教育数据联邦学习扩展
if EDU_MODELS_AVAILABLE:

    class EduFLTrainingConfig(FLTrainingConfig):
        """教育数据联邦学习训练配置扩展"""

        edu_subjects: List[str] = Field(
            default=["math", "science", "technology", "engineering"],
            description="教育学科",
        )
        edu_grade_levels: List[str] = Field(
            default=["elementary", "middle", "high"], description="年级级别"
        )
        edu_region_analysis: bool = Field(default=True, description="区域分析")
        edu_trend_prediction: bool = Field(default=True, description="趋势预测")

        class Config:
            # 允许额外字段
            extra = "allow"

    class EduFLModelMetadata(FLModelMetadata):
        """教育联邦学习模型元数据扩展"""

        edu_metrics: Optional[EduTrainingMetrics] = Field(None, description="教育指标")
        stem_scores: Optional[Dict[str, float]] = Field(None, description="STEM得分")
        regional_analysis: Optional[Dict[str, Any]] = Field(
            None, description="区域分析结果"
        )
