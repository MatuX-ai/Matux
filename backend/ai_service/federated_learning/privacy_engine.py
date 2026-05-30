"""
差分隐私引擎
实现高斯噪声添加和隐私预算管理
"""

import logging
import math
from typing import Any, Dict, List, Tuple

import numpy as np
import torch

logger = logging.getLogger(__name__)


class PrivacyBudgetManager:
    """隐私预算管理器"""

    def __init__(self, total_epsilon: float, delta: float = 1e-5):
        self.total_epsilon = total_epsilon
        self.delta = delta
        self.consumed_epsilon = 0.0
        self.consumed_delta = 0.0

    def consume_budget(self, epsilon: float, delta: float = 0.0) -> bool:
        """消费隐私预算"""
        if self.consumed_epsilon + epsilon <= self.total_epsilon:
            self.consumed_epsilon += epsilon
            self.consumed_delta += delta
            return True
        return False

    def get_remaining_budget(self) -> Tuple[float, float]:
        """获取剩余隐私预算"""
        remaining_epsilon = self.total_epsilon - self.consumed_epsilon
        remaining_delta = self.delta - self.consumed_delta
        return max(0.0, remaining_epsilon), max(0.0, remaining_delta)

    def reset_budget(self):
        """重置隐私预算"""
        self.consumed_epsilon = 0.0
        self.consumed_delta = 0.0


class PrivacyEngine:
    """
    差分隐私引擎
    提供梯度噪声添加和隐私保护功能
    """

    def __init__(self, total_epsilon: float = 1.0, delta: float = 1e-5):
        self.budget_manager = PrivacyBudgetManager(total_epsilon, delta)
        self.noise_history = []

    def add_differential_privacy(
        self,
        gradients: List[Dict[str, Any]],
        epsilon: float,
        noise_multiplier: float,
        clipping_threshold: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """
        为梯度添加差分隐私保护

        Args:
            gradients: 梯度列表
            epsilon: 隐私预算
            noise_multiplier: 噪声乘数
            clipping_threshold: 梯度裁剪阈值

        Returns:
            添加噪声后的梯度列表
        """
        try:
            logger.info(
                f"添加差分隐私保护: ε={epsilon}, noise_multiplier={noise_multiplier}"
            )

            # 消费隐私预算
            if not self.budget_manager.consume_budget(epsilon):
                raise ValueError("隐私预算不足")

            # 对每个梯度添加噪声
            noisy_gradients = []
            for gradient_dict in gradients:
                noisy_grad = self._add_noise_to_gradient(
                    gradient_dict, epsilon, noise_multiplier, clipping_threshold
                )
                noisy_gradients.append(noisy_grad)

                # 记录噪声添加历史
                self.noise_history.append(
                    {
                        "timestamp": np.datetime64("now"),
                        "epsilon": epsilon,
                        "noise_multiplier": noise_multiplier,
                        "parameters_count": len(gradient_dict),
                    }
                )

            logger.info(f"差分隐私保护完成，处理{len(gradients)}个梯度")
            return noisy_gradients

        except Exception as e:
            logger.error(f"添加差分隐私失败: {e}")
            raise

    def _add_noise_to_gradient(
        self,
        gradient_dict: Dict[str, Any],
        epsilon: float,
        noise_multiplier: float,
        clipping_threshold: float,
    ) -> Dict[str, Any]:
        """为单个梯度字典添加噪声"""
        noisy_gradient = {}

        for param_name, param_gradient in gradient_dict.items():
            try:
                # 转换为tensor
                if isinstance(param_gradient, list):
                    tensor_grad = torch.tensor(param_gradient, dtype=torch.float32)
                elif isinstance(param_gradient, np.ndarray):
                    tensor_grad = torch.from_numpy(param_gradient).float()
                else:
                    tensor_grad = torch.tensor(param_gradient, dtype=torch.float32)

                # 梯度裁剪
                clipped_grad = self._clip_tensor(tensor_grad, clipping_threshold)

                # 计算噪声标准差
                sigma = noise_multiplier * clipping_threshold

                # 添加高斯噪声
                noise = torch.normal(mean=0.0, std=sigma, size=clipped_grad.shape)

                # 应用噪声
                noisy_param = clipped_grad + noise

                # 转换回原始格式
                if isinstance(param_gradient, list):
                    noisy_gradient[param_name] = noisy_param.tolist()
                elif isinstance(param_gradient, np.ndarray):
                    noisy_gradient[param_name] = noisy_param.numpy()
                else:
                    noisy_gradient[param_name] = noisy_param.tolist()

            except Exception as e:
                logger.warning(f"处理参数 {param_name} 时出错: {e}")
                # 如果处理失败，保留原始梯度
                noisy_gradient[param_name] = param_gradient

        return noisy_gradient

    def _clip_tensor(self, tensor: torch.Tensor, threshold: float) -> torch.Tensor:
        """梯度裁剪"""
        l2_norm = torch.norm(tensor)
        if l2_norm > threshold:
            clip_coef = threshold / (l2_norm + 1e-6)
            return tensor * clip_coef
        return tensor

    def calculate_privacy_loss(
        self, noise_multiplier: float, steps: int, sampling_probability: float
    ) -> Tuple[float, float]:
        """
        计算隐私损失 (ε, δ)

        Args:
            noise_multiplier: 噪声乘数
            steps: 训练步数
            sampling_probability: 采样概率

        Returns:
            Tuple[ε, δ]: 隐私损失
        """
        try:
            # 使用RDP (Rényi Differential Privacy) 计算
            rdp_epsilon = self._compute_rdp_epsilon(
                noise_multiplier, steps, sampling_probability
            )

            # 转换为(ε, δ)-DP
            delta = self.budget_manager.delta
            epsilon = rdp_epsilon + math.log(1 / delta) / (steps * sampling_probability)

            return max(0.0, epsilon), delta

        except Exception as e:
            logger.error(f"计算隐私损失失败: {e}")
            return float("inf"), float("inf")

    def _compute_rdp_epsilon(
        self, noise_multiplier: float, steps: int, sampling_probability: float
    ) -> float:
        """计算RDP下的隐私损失"""
        # RDP计算公式
        alpha = 1 + noise_multiplier**2  # RDP阶数
        rdp = alpha * sampling_probability**2 / (2 * noise_multiplier**2)
        return rdp * steps

    def add_laplace_noise(
        self, value: float, sensitivity: float, epsilon: float
    ) -> float:
        """
        添加拉普拉斯噪声（用于标量值）

        Args:
            value: 原始值
            sensitivity: 敏感度
            epsilon: 隐私预算

        Returns:
            添加噪声后的值
        """
        scale = sensitivity / epsilon
        noise = np.random.laplace(0, scale)
        return value + noise

    def add_gaussian_noise(self, tensor: torch.Tensor, std: float) -> torch.Tensor:
        """添加高斯噪声到张量"""
        noise = torch.normal(mean=0.0, std=std, size=tensor.shape)
        return tensor + noise

    def adaptive_noise_addition(
        self,
        gradients: List[Dict[str, Any]],
        target_epsilon: float,
        max_noise: float = 10.0,
    ) -> List[Dict[str, Any]]:
        """
        自适应噪声添加
        根据梯度幅度动态调整噪声水平
        """
        try:
            noisy_gradients = []

            for gradient_dict in gradients:
                adaptive_grad = {}

                for param_name, param_gradient in gradient_dict.items():
                    # 计算梯度幅度
                    if isinstance(param_gradient, (list, np.ndarray)):
                        grad_magnitude = np.linalg.norm(np.array(param_gradient))
                    else:
                        grad_magnitude = abs(float(param_gradient))

                    # 自适应噪声标准差
                    adaptive_std = min(grad_magnitude * 0.1, max_noise)

                    # 添加噪声
                    if isinstance(param_gradient, list):
                        tensor_grad = torch.tensor(param_gradient, dtype=torch.float32)
                        noisy_tensor = self.add_gaussian_noise(
                            tensor_grad, adaptive_std
                        )
                        adaptive_grad[param_name] = noisy_tensor.tolist()
                    else:
                        noisy_value = self.add_gaussian_noise(
                            torch.tensor(float(param_gradient)), adaptive_std
                        )
                        adaptive_grad[param_name] = noisy_value.item()

                noisy_gradients.append(adaptive_grad)

            # 消费相应的隐私预算
            self.budget_manager.consume_budget(target_epsilon)

            return noisy_gradients

        except Exception as e:
            logger.error(f"自适应噪声添加失败: {e}")
            raise

    def get_privacy_stats(self) -> Dict[str, Any]:
        """获取隐私保护统计信息"""
        remaining_epsilon, remaining_delta = self.budget_manager.get_remaining_budget()

        return {
            "total_epsilon": self.budget_manager.total_epsilon,
            "consumed_epsilon": self.budget_manager.consumed_epsilon,
            "remaining_epsilon": remaining_epsilon,
            "delta": self.budget_manager.delta,
            "noise_operations_count": len(self.noise_history),
            "average_noise_multiplier": (
                np.mean([op["noise_multiplier"] for op in self.noise_history])
                if self.noise_history
                else 0.0
            ),
            "budget_utilization": (
                self.budget_manager.consumed_epsilon / self.budget_manager.total_epsilon
                if self.budget_manager.total_epsilon > 0
                else 0.0
            ),
        }

    def reset_privacy_budget(self):
        """重置隐私预算"""
        self.budget_manager.reset_budget()
        self.noise_history.clear()
        logger.info("隐私预算已重置")
