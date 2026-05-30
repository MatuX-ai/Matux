"""
迁移学习配置文件
包含ASSISTments数据集处理和模型训练的相关配置
"""

from dataclasses import dataclass
import os


@dataclass
class DatasetConfig:
    """数据集配置"""

    # ASSISTments数据集配置
    assistments_dataset_name: str = "cais/assistments2012"
    cache_dir: str = "./data/cache"
    processed_data_path: str = "./data/processed/assistments_dataset.csv"

    # 数据预处理参数
    test_size: float = 0.2
    validation_size: float = 0.1
    random_seed: int = 42

    # 特征工程参数
    max_sequence_length: int = 512
    min_skill_frequency: int = 5
    max_skills_per_problem: int = 10


@dataclass
class ModelConfig:
    """模型配置"""

    # 基础模型配置
    teacher_model_name: str = "bert-base-uncased"
    student_model_name: str = "distilbert-base-uncased"

    # 训练参数
    batch_size: int = 32
    learning_rate: float = 2e-5
    num_epochs: int = 3
    warmup_steps: int = 500
    weight_decay: float = 0.01

    # 知识蒸馏参数
    temperature: float = 3.0
    alpha_ce: float = 0.5
    alpha_mse: float = 0.5

    # 模型保存配置
    model_save_path: str = "./models/distilled"
    checkpoint_interval: int = 1000  # 每N步保存检查点


@dataclass
class CompressionConfig:
    """模型压缩配置"""

    # 量化配置
    quantization_bits: int = 8  # 8-bit量化
    use_fp16: bool = True  # 使用FP16

    # 剪枝配置
    pruning_ratio: float = 0.3  # 剪枝比例
    pruning_method: str = "magnitude"  # 剪枝方法

    # 结构化稀疏化
    structured_sparsity: bool = True
    block_size: int = 4


@dataclass
class DeploymentConfig:
    """部署配置"""

    # 模型服务配置
    api_prefix: str = "/api/v1/pretrain-model"
    max_concurrent_requests: int = 10
    timeout_seconds: int = 30

    # 缓存配置
    model_cache_ttl: int = 3600  # 1小时
    prediction_cache_size: int = 1000

    # 监控配置
    enable_monitoring: bool = True
    log_predictions: bool = True


class TransferLearningSettings:
    """迁移学习全局设置"""

    def __init__(self):
        self.dataset = DatasetConfig()
        self.model = ModelConfig()
        self.compression = CompressionConfig()
        self.deployment = DeploymentConfig()

        # 确保目录存在
        self._ensure_directories()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.dataset.cache_dir,
            os.path.dirname(self.dataset.processed_data_path),
            self.model.model_save_path,
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def get_model_path(self, model_name: str, version: str = "latest") -> str:
        """获取模型文件路径"""
        return os.path.join(self.model.model_save_path, f"{model_name}_{version}.pth")

    def get_compressed_model_path(self, model_name: str, compression_type: str) -> str:
        """获取压缩模型文件路径"""
        return os.path.join(
            self.model.model_save_path,
            f"{model_name}_compressed_{compression_type}.pth",
        )


# 全局配置实例
settings = TransferLearningSettings()

# 导出配置类
__all__ = [
    "DatasetConfig",
    "ModelConfig",
    "CompressionConfig",
    "DeploymentConfig",
    "TransferLearningSettings",
    "settings",
]
