"""
教育局数据对接模型定义
包含教育数据特有的数据结构和配置模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import uuid

from pydantic import BaseModel, Field, validator


class EduSubject(str, Enum):
    """教育学科枚举"""

    MATH = "math"
    SCIENCE = "science"
    TECHNOLOGY = "technology"
    ENGINEERING = "engineering"
    LANGUAGE = "language"
    ARTS = "arts"
    SOCIAL_STUDIES = "social_studies"
    PHYSICAL_EDUCATION = "physical_education"


class EduGradeLevel(str, Enum):
    """年级级别枚举"""

    ELEMENTARY = "elementary"  # 小学
    MIDDLE = "middle"  # 初中
    HIGH = "high"  # 高中
    UNIVERSITY = "university"  # 大学


class EduRegionType(str, Enum):
    """区域类型枚举"""

    DISTRICT = "district"
    CITY = "city"
    PROVINCE = "province"
    NATIONAL = "national"


class EduDataPrivacyLevel(str, Enum):
    """数据隐私级别"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EduDataSourceType(str, Enum):
    """数据来源类型"""

    SCHOOL = "school"
    DISTRICT = "district"
    REGIONAL = "regional"
    NATIONAL = "national"


class EduAssessmentType(str, Enum):
    """评估类型"""

    STANDARDIZED_TEST = "standardized_test"
    FORMATIVE_ASSESSMENT = "formative_assessment"
    SUMMATIVE_ASSESSMENT = "summative_assessment"
    PERFORMANCE_TASK = "performance_task"


class EduStudentDemographics(BaseModel):
    """学生人口统计信息"""

    student_id: str = Field(..., description="学生ID")
    age: Optional[int] = Field(None, description="年龄")
    gender: Optional[str] = Field(None, description="性别")
    grade_level: EduGradeLevel = Field(..., description="年级")
    school_id: str = Field(..., description="学校ID")
    region_id: str = Field(..., description="区域ID")
    socioeconomic_status: Optional[str] = Field(None, description="社会经济地位")
    special_needs: Optional[List[str]] = Field(default=[], description="特殊需求")


class EduAcademicPerformance(BaseModel):
    """学术表现数据"""

    student_id: str = Field(..., description="学生ID")
    subject: EduSubject = Field(..., description="学科")
    assessment_type: EduAssessmentType = Field(..., description="评估类型")
    score: float = Field(..., ge=0, le=100, description="分数")
    percentile_rank: Optional[float] = Field(
        None, ge=0, le=100, description="百分位排名"
    )
    date_taken: datetime = Field(..., description="考试日期")
    academic_year: str = Field(..., description="学年")


class EduSchoolInfo(BaseModel):
    """学校信息"""

    school_id: str = Field(..., description="学校ID")
    school_name: str = Field(..., description="学校名称")
    school_type: str = Field(..., description="学校类型")
    district_id: str = Field(..., description="学区ID")
    region_id: str = Field(..., description="区域ID")
    enrollment: int = Field(..., ge=0, description="在校学生数")
    teachers_count: int = Field(..., ge=0, description="教师数量")
    established_year: Optional[int] = Field(None, description="建校年份")


class EduRegionalData(BaseModel):
    """区域教育数据"""

    region_id: str = Field(..., description="区域ID")
    region_name: str = Field(..., description="区域名称")
    region_type: EduRegionType = Field(..., description="区域类型")
    population: int = Field(..., ge=0, description="人口数")
    schools_count: int = Field(..., ge=0, description="学校数量")
    students_count: int = Field(..., ge=0, description="学生总数")
    teachers_count: int = Field(..., ge=0, description="教师总数")
    budget_allocation: Optional[float] = Field(None, description="教育预算")


class EduTrainingConfig(BaseModel):
    """教育数据联邦学习训练配置"""

    training_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str = Field(default="edu_stem_analyzer", description="模型名称")
    rounds: int = Field(default=20, ge=1, le=100, description="训练轮数")
    participants: List[str] = Field(..., description="参与学校/区域列表")
    subjects: List[EduSubject] = Field(
        default=[
            EduSubject.MATH,
            EduSubject.SCIENCE,
            EduSubject.TECHNOLOGY,
            EduSubject.ENGINEERING,
        ],
        description="分析学科",
    )
    grade_levels: List[EduGradeLevel] = Field(
        default=[EduGradeLevel.ELEMENTARY, EduGradeLevel.MIDDLE, EduGradeLevel.HIGH],
        description="年级范围",
    )
    privacy_level: EduDataPrivacyLevel = Field(
        default=EduDataPrivacyLevel.HIGH, description="隐私保护级别"
    )
    aggregation_method: str = Field(default="fedavg_secure", description="安全聚合方法")
    privacy_budget: float = Field(default=1.0, gt=0, description="差分隐私预算ε")
    noise_multiplier: float = Field(default=1.1, gt=0, description="噪声乘数")
    clipping_threshold: float = Field(default=1.0, gt=0, description="梯度裁剪阈值")
    learning_rate: float = Field(default=0.01, gt=0, description="学习率")
    batch_size: int = Field(default=64, ge=1, description="批次大小")
    enable_trend_analysis: bool = Field(default=True, description="启用趋势分析")
    enable_region_comparison: bool = Field(default=True, description="启用区域对比")
    created_at: datetime = Field(default_factory=datetime.now)
    timeout: int = Field(default=7200, description="超时时间(秒)")

    @validator("subjects")
    def validate_subjects(cls, v):
        if not v:
            raise ValueError("至少需要选择一个学科")
        return v

    @validator("grade_levels")
    def validate_grade_levels(cls, v):
        if not v:
            raise ValueError("至少需要选择一个年级级别")
        return v


class EduModelWeights(BaseModel):
    """教育模型权重"""

    subject_weights: Dict[EduSubject, float] = Field(..., description="各学科权重")
    grade_level_weights: Dict[EduGradeLevel, float] = Field(
        ..., description="各年级权重"
    )
    regional_factors: Dict[str, float] = Field(default={}, description="区域因素权重")
    temporal_trends: Dict[str, float] = Field(default={}, description="时间趋势系数")
    demographic_adjustments: Dict[str, float] = Field(
        default={}, description="人口统计调整因子"
    )


class EduTrainingMetrics(BaseModel):
    """教育训练指标"""

    training_id: str = Field(..., description="训练ID")
    round_number: int = Field(..., ge=0, description="轮次")
    subject_scores: Dict[EduSubject, float] = Field(..., description="各学科平均分")
    participation_rate: float = Field(..., ge=0, le=100, description="参与率")
    data_quality_score: float = Field(..., ge=0, le=100, description="数据质量评分")
    privacy_consumption: float = Field(..., ge=0, description="隐私预算消耗")
    convergence_metric: float = Field(..., ge=0, description="收敛指标")
    timestamp: datetime = Field(default_factory=datetime.now)


class EduReportRequest(BaseModel):
    """教育报告生成请求"""

    training_id: str = Field(..., description="训练ID")
    report_type: str = Field(default="stem_analysis", description="报告类型")
    format: str = Field(default="pdf", description="报告格式(pdf/excel)")
    include_charts: bool = Field(default=True, description="是否包含图表")
    include_detailed_stats: bool = Field(default=True, description="是否包含详细统计")
    comparison_regions: Optional[List[str]] = Field(default=[], description="对比区域")
    time_range: Optional[tuple[datetime, datetime]] = Field(
        None, description="时间范围"
    )
    grade_filter: Optional[List[EduGradeLevel]] = Field(None, description="年级过滤器")


class EduReportMetadata(BaseModel):
    """教育报告元数据"""

    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    training_id: str = Field(..., description="关联训练ID")
    report_type: str = Field(..., description="报告类型")
    format: str = Field(..., description="报告格式")
    generated_at: datetime = Field(default_factory=datetime.now)
    generated_by: str = Field(..., description="生成者")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., ge=0, description="文件大小(字节)")
    page_count: Optional[int] = Field(None, description="页数(仅PDF)")
    data_sources: List[str] = Field(default=[], description="数据来源")
    privacy_level: EduDataPrivacyLevel = Field(..., description="隐私级别")


class EduDataSharingProtocol(BaseModel):
    """教育数据共享协议"""

    protocol_version: str = Field(default="1.0", description="协议版本")
    data_types: List[str] = Field(..., description="共享数据类型")
    privacy_guarantees: List[str] = Field(..., description="隐私保证措施")
    usage_restrictions: List[str] = Field(..., description="使用限制")
    retention_period: int = Field(..., description="数据保留期限(天)")
    audit_requirements: List[str] = Field(..., description="审计要求")
    compliance_standards: List[str] = Field(..., description="合规标准")
    created_at: datetime = Field(default_factory=datetime.now)


# 数据传输对象
class EduDataBatch(BaseModel):
    """教育数据批次"""

    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = Field(..., description="数据源ID")
    data_type: str = Field(..., description="数据类型")
    records: List[
        Union[EduStudentDemographics, EduAcademicPerformance, EduSchoolInfo]
    ] = Field(..., description="数据记录")
    timestamp: datetime = Field(default_factory=datetime.now)
    checksum: str = Field(..., description="数据校验和")
    encrypted: bool = Field(default=False, description="是否加密")


class EduNodeRegistration(BaseModel):
    """教育节点注册信息"""

    node_id: str = Field(..., description="节点ID")
    node_name: str = Field(..., description="节点名称")
    node_type: EduDataSourceType = Field(..., description="节点类型")
    region_id: str = Field(..., description="所属区域")
    contact_info: Dict[str, str] = Field(..., description="联系方式")
    public_key: str = Field(..., description="公钥")
    capabilities: List[str] = Field(default=[], description="支持的功能")
    registered_at: datetime = Field(default_factory=datetime.now)


# 验证和辅助函数
def validate_edu_data_structure(data: Dict[str, Any]) -> bool:
    """验证教育数据结构"""
    required_fields = ["student_id", "subject", "score"]
    return all(field in data for field in required_fields)


def calculate_stem_score(
    subject_scores: Dict[EduSubject, float], weights: Dict[EduSubject, float]
) -> float:
    """计算STEM综合得分"""
    weighted_sum = sum(
        subject_scores.get(subject, 0) * weights.get(subject, 0)
        for subject in [
            EduSubject.MATH,
            EduSubject.SCIENCE,
            EduSubject.TECHNOLOGY,
            EduSubject.ENGINEERING,
        ]
    )
    weight_sum = sum(
        weights.get(subject, 0)
        for subject in [
            EduSubject.MATH,
            EduSubject.SCIENCE,
            EduSubject.TECHNOLOGY,
            EduSubject.ENGINEERING,
        ]
    )

    return weighted_sum / weight_sum if weight_sum > 0 else 0.0


if __name__ == "__main__":
    # 测试模型
    config = EduTrainingConfig(
        participants=["school_001", "school_002", "school_003"],
        subjects=[EduSubject.MATH, EduSubject.SCIENCE],
        grade_levels=[EduGradeLevel.MIDDLE, EduGradeLevel.HIGH],
    )
    print(f"训练配置: {config}")

    # 测试STEM得分计算
    scores = {
        EduSubject.MATH: 85.5,
        EduSubject.SCIENCE: 82.0,
        EduSubject.TECHNOLOGY: 78.5,
        EduSubject.ENGINEERING: 80.0,
    }
    weights = {
        EduSubject.MATH: 0.3,
        EduSubject.SCIENCE: 0.3,
        EduSubject.TECHNOLOGY: 0.2,
        EduSubject.ENGINEERING: 0.2,
    }
    stem_score = calculate_stem_score(scores, weights)
    print(f"STEM综合得分: {stem_score:.2f}")
