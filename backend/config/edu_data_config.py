"""
教育局数据对接联邦学习系统配置
包含教育数据特有的配置参数和设置
"""

from typing import Dict, List

from pydantic import Field
from pydantic_settings import BaseSettings


class EduDataConfig(BaseSettings):
    """教育数据对接配置类"""

    # 基础联邦学习配置
    fl_privacy_epsilon: float = Field(default=1.0, description="差分隐私预算ε")
    fl_noise_multiplier: float = Field(default=1.1, description="噪声乘数")
    fl_clipping_threshold: float = Field(default=1.0, description="梯度裁剪阈值")
    fl_max_rounds: int = Field(default=50, description="最大训练轮数")
    fl_timeout_seconds: int = Field(default=7200, description="训练超时时间(秒)")
    fl_min_participants: int = Field(default=3, description="最小参与方数量")
    fl_convergence_threshold: float = Field(default=0.01, description="收敛阈值")

    # 教育数据特定配置
    edu_data_privacy_level: str = Field(
        default="high", description="数据隐私级别(low/medium/high)"
    )
    edu_subjects: List[str] = Field(
        default=["math", "science", "technology", "engineering"],
        description="支持的学科",
    )
    edu_grade_levels: List[str] = Field(
        default=["elementary", "middle", "high"], description="年级级别"
    )
    edu_region_analysis: bool = Field(default=True, description="是否启用区域分析")
    edu_trend_prediction: bool = Field(default=True, description="是否启用趋势预测")

    # STEM能力评估配置
    stem_assessment_weights: Dict[str, float] = Field(
        default={
            "math": 0.25,
            "science": 0.25,
            "technology": 0.25,
            "engineering": 0.25,
        },
        description="STEM各学科权重配置",
    )

    # 报告生成配置
    report_formats: List[str] = Field(
        default=["pdf", "excel"], description="支持的报告格式"
    )
    report_template_dir: str = Field(
        default="./templates/reports", description="报告模板目录"
    )
    report_output_dir: str = Field(
        default="./reports/output", description="报告输出目录"
    )
    report_retention_days: int = Field(default=30, description="报告保留天数")

    # 数据脱敏配置
    data_masking_enabled: bool = Field(default=True, description="是否启用数据脱敏")
    data_masking_level: str = Field(
        default="strict", description="脱敏级别(basic/strict/comprehensive)"
    )
    pii_fields: List[str] = Field(
        default=["student_name", "parent_name", "phone", "address"],
        description="个人身份信息字段",
    )
    sensitive_aggregation_threshold: int = Field(
        default=10, description="敏感数据聚合阈值"
    )

    # 教育局节点配置
    edu_node_discovery_enabled: bool = Field(
        default=True, description="是否启用节点发现"
    )
    edu_node_heartbeat_interval: int = Field(default=300, description="心跳间隔(秒)")
    edu_node_timeout: int = Field(default=1800, description="节点超时时间(秒)")
    edu_max_nodes_per_region: int = Field(default=50, description="每个区域最大节点数")

    # 监控和日志配置
    edu_monitoring_enabled: bool = Field(default=True, description="是否启用监控")
    edu_log_level: str = Field(default="INFO", description="日志级别")
    edu_audit_log_enabled: bool = Field(default=True, description="是否启用审计日志")
    edu_metrics_collection: bool = Field(default=True, description="是否收集指标")

    # 安全配置
    edu_tls_required: bool = Field(default=True, description="是否要求TLS")
    edu_jwt_expiration_hours: int = Field(default=24, description="JWT过期时间(小时)")
    edu_api_rate_limit: str = Field(default="100/hour", description="API速率限制")
    edu_data_encryption_enabled: bool = Field(
        default=True, description="是否启用数据加密"
    )

    # 数据质量配置
    data_quality_checks_enabled: bool = Field(
        default=True, description="是否启用数据质量检查"
    )
    min_data_points_per_subject: int = Field(
        default=100, description="每学科最小数据点数"
    )
    max_missing_values_ratio: float = Field(default=0.1, description="最大缺失值比例")
    outlier_detection_enabled: bool = Field(
        default=True, description="是否启用异常值检测"
    )

    class Config:
        env_file = ".env.edu_data"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_subject_weight(self, subject: str) -> float:
        """获取指定学科的权重"""
        return self.stem_assessment_weights.get(subject.lower(), 0.0)

    def is_valid_privacy_level(self) -> bool:
        """验证隐私级别是否有效"""
        return self.edu_data_privacy_level in ["low", "medium", "high"]

    def get_supported_formats(self) -> List[str]:
        """获取支持的报告格式"""
        return [fmt.lower() for fmt in self.report_formats]

    def is_pii_field(self, field_name: str) -> bool:
        """判断字段是否为PII字段"""
        return field_name.lower() in [field.lower() for field in self.pii_fields]


# 全局配置实例
edu_config = EduDataConfig()

if __name__ == "__main__":
    # 测试配置加载
    print("教育数据对接配置:")
    print(f"隐私级别: {edu_config.edu_data_privacy_level}")
    print(f"支持学科: {edu_config.edu_subjects}")
    print(f"报告格式: {edu_config.report_formats}")
    print(f"PII字段: {edu_config.pii_fields}")
