"""
联邦学习客户端
负责本地模型训练和与协调器的安全通信
"""

from datetime import datetime
import logging
from typing import Any, Callable, Dict, Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import torch
import torch.nn as nn
import torch.optim as optim

from ..fl_models import (
    FLModelMetadata,
    FLParticipantInfo,
    FLParticipantRole,
    FLTrainingConfig,
)
from .privacy_engine import PrivacyEngine

logger = logging.getLogger(__name__)


class SimpleFedModel(nn.Module):
    """简单的联邦学习模型示例"""

    def __init__(
        self, input_dim: int = 784, hidden_dim: int = 128, output_dim: int = 10
    ):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x


class FederatedClient:
    """
    联邦学习客户端
    负责本地训练、隐私保护和安全通信
    """

    def __init__(
        self, participant_id: str, coordinator_url: str, privacy_engine: PrivacyEngine
    ):
        self.participant_id = participant_id
        self.coordinator_url = coordinator_url
        self.privacy_engine = privacy_engine
        self.model: Optional[nn.Module] = None
        self.optimizer: Optional[optim.Optimizer] = None
        self.private_key = self._generate_rsa_keypair()
        self.coordinator_public_key: Optional[bytes] = None
        self.training_config: Optional[FLTrainingConfig] = None
        self.local_data = None
        self.is_registered = False

        # 客户端信息
        self.participant_info = FLParticipantInfo(
            participant_id=participant_id,
            role=FLParticipantRole.PARTICIPANT,
            status="offline",
        )

    def _generate_rsa_keypair(self) -> rsa.RSAPrivateKey:
        """生成RSA密钥对"""
        return rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

    def get_public_key(self) -> bytes:
        """获取客户端公钥"""
        public_key = self.private_key.public_key()
        return public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    async def register_with_coordinator(self) -> bool:
        """向协调器注册"""
        try:
            # 这里应该实现与协调器的实际注册逻辑
            # 包括发送公钥、接收协调器公钥等

            logger.info(f"客户端 {self.participant_id} 向协调器注册")
            self.participant_info.status = "online"
            self.is_registered = True
            return True

        except Exception as e:
            logger.error(f"注册失败: {e}")
            return False

    def initialize_model(
        self, model_class: type = SimpleFedModel, **model_kwargs
    ) -> bool:
        """初始化本地模型"""
        try:
            self.model = model_class(**model_kwargs)
            self.optimizer = optim.SGD(self.model.parameters(), lr=0.01, momentum=0.9)
            logger.info(f"模型初始化完成: {model_class.__name__}")
            return True
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            return False

    def load_local_data(self, data_loader: Any) -> bool:
        """加载本地训练数据"""
        try:
            self.local_data = data_loader
            logger.info("本地数据加载完成")
            return True
        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            return False

    async def participate_in_training(
        self,
        training_config: FLTrainingConfig,
        receive_global_model: Callable,
        send_model_update: Callable,
    ) -> bool:
        """
        参与联邦学习训练

        Args:
            training_config: 训练配置
            receive_global_model: 接收全局模型的回调函数
            send_model_update: 发送模型更新的回调函数

        Returns:
            bool: 训练是否成功
        """
        try:
            self.training_config = training_config
            logger.info(f"开始参与训练: {training_config.training_id}")

            for round_num in range(training_config.rounds):
                logger.info(f"开始训练轮次 {round_num + 1}/{training_config.rounds}")

                # 1. 接收全局模型
                global_weights = await receive_global_model()
                if global_weights:
                    self._load_model_weights(global_weights)

                # 2. 本地训练
                await self._local_training(round_num)

                # 3. 提取并处理模型更新
                model_update = self._extract_model_update()

                # 4. 应用隐私保护
                private_update = self.privacy_engine.add_differential_privacy(
                    [model_update.model_weights],
                    training_config.privacy_budget,
                    training_config.noise_multiplier,
                    training_config.clipping_threshold,
                )[0]

                model_update.model_weights = private_update
                model_update.privacy_noise_added = True

                # 5. 发送更新给协调器
                await send_model_update(model_update)

                logger.info(f"轮次 {round_num + 1} 完成")

            self.participant_info.status = "completed"
            return True

        except Exception as e:
            logger.error(f"训练过程中出错: {e}")
            self.participant_info.status = "failed"
            return False

    async def _local_training(self, round_num: int) -> Dict[str, float]:
        """执行本地训练"""
        if not self.model or not self.local_data:
            raise ValueError("模型或数据未初始化")

        self.model.train()
        total_loss = 0.0
        total_samples = 0

        # 简化的训练循环
        for batch_idx, (data, target) in enumerate(self.local_data):
            if batch_idx >= 10:  # 限制训练批次以加快演示
                break

            self.optimizer.zero_grad()

            # 前向传播
            output = self.model(data.flatten(1))  # 简单展平处理
            loss = nn.CrossEntropyLoss()(output, target)

            # 反向传播
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item() * data.size(0)
            total_samples += data.size(0)

            if batch_idx % 5 == 0:
                logger.debug(
                    f"轮次 {round_num}, 批次 {batch_idx}, 损失: {loss.item():.6f}"
                )

        avg_loss = total_loss / total_samples if total_samples > 0 else 0.0

        metrics = {
            "loss": avg_loss,
            "samples_processed": total_samples,
            "round": round_num,
        }

        logger.info(f"本地训练完成 - 轮次: {round_num}, 平均损失: {avg_loss:.4f}")
        return metrics

    def _extract_model_update(self) -> FLModelMetadata:
        """提取模型更新"""
        if not self.model:
            raise ValueError("模型未初始化")

        # 提取模型权重
        weights_dict = {}
        for name, param in self.model.named_parameters():
            weights_dict[name] = param.data.cpu().numpy().tolist()

        return FLModelMetadata(
            training_id=(
                self.training_config.training_id if self.training_config else ""
            ),
            model_weights=weights_dict,
            participant_id=self.participant_id,
            round_number=self.training_config.rounds if self.training_config else 0,
        )

    def _load_model_weights(self, weights_dict: Dict[str, Any]):
        """加载模型权重"""
        if not self.model:
            raise ValueError("模型未初始化")

        model_dict = self.model.state_dict()
        for name, weights in weights_dict.items():
            if name in model_dict:
                if isinstance(weights, list):
                    model_dict[name] = torch.tensor(weights)
                else:
                    model_dict[name] = torch.tensor(weights)

        self.model.load_state_dict(model_dict)
        logger.debug("模型权重加载完成")

    def encrypt_update(self, model_update: FLModelMetadata) -> bytes:
        """加密模型更新"""
        try:
            if not self.coordinator_public_key:
                raise ValueError("协调器公钥未设置")

            # 将模型更新序列化为JSON
            import json

            update_json = json.dumps(model_update.dict(), default=str)
            update_bytes = update_json.encode("utf-8")

            # 使用协调器公钥加密
            coordinator_key = serialization.load_pem_public_key(
                self.coordinator_public_key, backend=default_backend()
            )

            encrypted_data = coordinator_key.encrypt(
                update_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            return encrypted_data

        except Exception as e:
            logger.error(f"加密更新失败: {e}")
            raise

    def decrypt_message(self, encrypted_data: bytes) -> Dict[str, Any]:
        """解密来自协调器的消息"""
        try:
            decrypted_data = self.private_key.decrypt(
                encrypted_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            import json

            return json.loads(decrypted_data.decode("utf-8"))

        except Exception as e:
            logger.error(f"解密消息失败: {e}")
            raise

    def get_client_stats(self) -> Dict[str, Any]:
        """获取客户端统计信息"""
        return {
            "participant_id": self.participant_id,
            "status": self.participant_info.status,
            "is_registered": self.is_registered,
            "model_initialized": self.model is not None,
            "data_loaded": self.local_data is not None,
            "privacy_stats": (
                self.privacy_engine.get_privacy_stats() if self.privacy_engine else {}
            ),
            "last_heartbeat": self.participant_info.last_heartbeat.isoformat(),
        }

    async def send_heartbeat(self):
        """发送心跳信号"""
        try:
            self.participant_info.last_heartbeat = datetime.now()
            # 这里应该实现实际的心跳发送逻辑
            logger.debug(f"发送心跳: {self.participant_id}")
        except Exception as e:
            logger.error(f"发送心跳失败: {e}")
