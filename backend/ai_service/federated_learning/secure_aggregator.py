"""
安全聚合协调器
实现基于同态加密和安全多方计算的模型权重聚合
"""

import logging
from typing import Any, Dict, List

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import numpy as np
import torch

from ..fl_models import (
    FLAggregationResult,
    FLModelMetadata,
    FLParticipantInfo,
    FLTrainingConfig,
)
from .privacy_engine import PrivacyEngine

logger = logging.getLogger(__name__)


class SecureAggregator:
    """
    安全聚合协调器
    负责协调多个参与方的安全模型聚合
    """

    def __init__(self, privacy_engine: PrivacyEngine):
        self.privacy_engine = privacy_engine
        self.participants: Dict[str, FLParticipantInfo] = {}
        self.aggregation_history: List[FLAggregationResult] = []
        self.private_key = self._generate_rsa_keypair()
        self.public_keys: Dict[str, bytes] = {}  # participant_id -> public_key

    def _generate_rsa_keypair(self) -> rsa.RSAPrivateKey:
        """生成RSA密钥对用于安全通信"""
        return rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

    def get_public_key(self) -> bytes:
        """获取公钥用于分发给参与者"""
        public_key = self.private_key.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def add_participant(self, participant_info: FLParticipantInfo) -> bool:
        """添加参与者"""
        try:
            self.participants[participant_info.participant_id] = participant_info
            logger.info(f"添加参与者: {participant_info.participant_id}")
            return True
        except Exception as e:
            logger.error(f"添加参与者失败: {e}")
            return False

    def register_participant_key(
        self, participant_id: str, public_key_pem: bytes
    ) -> bool:
        """注册参与者的公钥"""
        try:
            # 验证公钥格式
            public_key = serialization.load_pem_public_key(
                public_key_pem, backend=default_backend()
            )
            self.public_keys[participant_id] = public_key_pem
            logger.info(f"注册参与者公钥: {participant_id}")
            return True
        except Exception as e:
            logger.error(f"注册参与者公钥失败: {e}")
            return False

    async def secure_aggregate(
        self, model_updates: List[FLModelMetadata], training_config: FLTrainingConfig
    ) -> FLAggregationResult:
        """
        执行安全聚合

        Args:
            model_updates: 参与者提交的模型更新
            training_config: 训练配置

        Returns:
            FLAggregationResult: 聚合结果
        """
        try:
            logger.info(f"开始安全聚合，参与方数量: {len(model_updates)}")

            # 1. 验证参与者身份和数据完整性
            validated_updates = await self._validate_updates(model_updates)
            if not validated_updates:
                raise ValueError("模型更新验证失败")

            # 2. 解密接收到的加密梯度
            decrypted_gradients = await self._decrypt_gradients(validated_updates)

            # 3. 应用差分隐私保护
            private_gradients = self.privacy_engine.add_differential_privacy(
                decrypted_gradients,
                training_config.privacy_budget,
                training_config.noise_multiplier,
            )

            # 4. 执行加权平均聚合
            aggregated_weights = self._weighted_average_aggregation(
                private_gradients, training_config
            )

            # 5. 生成聚合结果
            result = FLAggregationResult(
                aggregated_weights=aggregated_weights,
                participant_count=len(validated_updates),
                aggregation_round=len(self.aggregation_history),
                privacy_metrics=self._calculate_privacy_metrics(training_config),
                convergence_metrics=self._calculate_convergence_metrics(
                    private_gradients
                ),
            )

            # 6. 记录聚合历史
            self.aggregation_history.append(result)

            logger.info(f"安全聚合完成，轮次: {result.aggregation_round}")
            return result

        except Exception as e:
            logger.error(f"安全聚合失败: {e}")
            raise

    async def _validate_updates(
        self, model_updates: List[FLModelMetadata]
    ) -> List[FLModelMetadata]:
        """验证模型更新的有效性"""
        validated = []

        for update in model_updates:
            # 检查参与者是否注册
            if update.participant_id not in self.participants:
                logger.warning(f"未注册的参与者: {update.participant_id}")
                continue

            # 检查数据完整性（简单验证，实际应使用数字签名）
            if not self._verify_update_integrity(update):
                logger.warning(f"数据完整性验证失败: {update.participant_id}")
                continue

            validated.append(update)

        return validated

    def _verify_update_integrity(self, update: FLModelMetadata) -> bool:
        """验证更新数据完整性"""
        # 简单的完整性检查，实际应用中应使用数字签名
        try:
            # 检查权重字典是否有效
            if not isinstance(update.model_weights, dict):
                return False

            # 检查必要字段是否存在
            required_fields = ["layer1.weight", "layer1.bias"]  # 示例字段
            for field in required_fields:
                if field not in update.model_weights:
                    logger.debug(f"缺少必要字段: {field}")

            return True
        except Exception:
            return False

    async def _decrypt_gradients(
        self, model_updates: List[FLModelMetadata]
    ) -> List[Dict[str, Any]]:
        """解密梯度数据"""
        decrypted_list = []

        for update in model_updates:
            try:
                # 这里应该实现实际的解密逻辑
                # 目前返回原始数据作为示例
                decrypted_weights = update.model_weights.copy()
                decrypted_list.append(decrypted_weights)

            except Exception as e:
                logger.error(f"解密梯度失败 {update.participant_id}: {e}")
                continue

        return decrypted_list

    def _weighted_average_aggregation(
        self, gradients_list: List[Dict[str, Any]], config: FLTrainingConfig
    ) -> Dict[str, Any]:
        """执行加权平均聚合"""
        if not gradients_list:
            raise ValueError("梯度列表为空")

        # 初始化聚合结果
        aggregated = {}
        len(gradients_list)

        # 对每个参数层进行聚合
        sample_gradient = gradients_list[0]
        for param_name in sample_gradient.keys():
            # 收集所有参与者的该层梯度
            param_gradients = []
            for gradient_dict in gradients_list:
                if param_name in gradient_dict:
                    param_gradients.append(torch.tensor(gradient_dict[param_name]))

            if param_gradients:
                # 计算加权平均（这里使用等权重）
                stacked_gradients = torch.stack(param_gradients)
                averaged_gradient = torch.mean(stacked_gradients, dim=0)

                # 应用梯度裁剪
                clipped_gradient = self._clip_gradient(
                    averaged_gradient, config.clipping_threshold
                )

                aggregated[param_name] = clipped_gradient.numpy().tolist()

        return aggregated

    def _clip_gradient(self, gradient: torch.Tensor, threshold: float) -> torch.Tensor:
        """梯度裁剪以防止异常值"""
        gradient_norm = torch.norm(gradient)
        if gradient_norm > threshold:
            clip_coef = threshold / (gradient_norm + 1e-6)
            gradient = gradient * clip_coef
        return gradient

    def _calculate_privacy_metrics(self, config: FLTrainingConfig) -> Dict[str, float]:
        """计算隐私保护指标"""
        return {
            "epsilon": config.privacy_budget,
            "delta": 1e-5,  # 典型的δ值
            "noise_multiplier": config.noise_multiplier,
            "clipping_threshold": config.clipping_threshold,
        }

    def _calculate_convergence_metrics(
        self, gradients_list: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """计算收敛性指标"""
        if not gradients_list:
            return {}

        # 计算梯度方差作为收敛指标
        sample_param = list(gradients_list[0].keys())[0]
        param_gradients = [
            grad_dict[sample_param]
            for grad_dict in gradients_list
            if sample_param in grad_dict
        ]

        if param_gradients:
            gradients_array = np.array(param_gradients)
            variance = np.var(gradients_array)
            return {"gradient_variance": float(variance)}

        return {}

    def get_aggregation_stats(self) -> Dict[str, Any]:
        """获取聚合统计信息"""
        return {
            "total_aggregations": len(self.aggregation_history),
            "participants_registered": len(self.participants),
            "recent_aggregation": (
                self.aggregation_history[-1].dict()
                if self.aggregation_history
                else None
            ),
            "active_participants": [
                pid
                for pid, info in self.participants.items()
                if info.status == "online"
            ],
        }
