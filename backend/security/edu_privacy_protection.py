"""
教育数据隐私保护机制
实现差分隐私、梯度裁剪、隐私预算管理等隐私保护功能
"""

from dataclasses import dataclass
from datetime import datetime
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

from ..config.edu_data_config import edu_config

logger = logging.getLogger(__name__)


@dataclass
class PrivacyBudget:
    """隐私预算跟踪"""

    epsilon: float  # 隐私损失参数
    delta: float  # 失败概率
    consumed: float = 0.0  # 已消耗的预算
    allocated: float = 0.0  # 已分配的预算
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def consume(self, amount: float) -> bool:
        """消耗隐私预算"""
        if self.consumed + amount <= self.epsilon:
            self.consumed += amount
            self.allocated += amount
            return True
        return False

    def remaining(self) -> float:
        """剩余隐私预算"""
        return max(0.0, self.epsilon - self.consumed)

    def is_exhausted(self) -> bool:
        """检查预算是否耗尽"""
        return self.consumed >= self.epsilon


class DifferentialPrivacyEngine:
    """差分隐私引擎"""

    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        self.epsilon = epsilon
        self.delta = delta
        self.budget = PrivacyBudget(epsilon, delta)
        self.noise_multiplier = edu_config.fl_noise_multiplier
        self.clipping_threshold = edu_config.fl_clipping_threshold
        self.privacy_accountant = PrivacyAccountant()

    def add_noise_to_gradients(
        self, gradients: Dict[str, torch.Tensor], sensitivity: float = 1.0
    ) -> Dict[str, torch.Tensor]:
        """
        向梯度添加差分隐私噪声

        Args:
            gradients: 模型梯度字典
            sensitivity: 敏感度（默认为1.0）

        Returns:
            添加噪声后的梯度
        """
        try:
            noisy_gradients = {}

            # 计算噪声标准差
            noise_std = self._calculate_noise_std(sensitivity)

            # 为每个梯度张量添加噪声
            for param_name, grad_tensor in gradients.items():
                if grad_tensor is not None:
                    # 梯度裁剪
                    clipped_grad = self._clip_gradient(
                        grad_tensor, self.clipping_threshold
                    )

                    # 添加高斯噪声
                    noise = torch.normal(
                        mean=0.0,
                        std=noise_std,
                        size=grad_tensor.shape,
                        device=grad_tensor.device,
                    )

                    noisy_gradients[param_name] = clipped_grad + noise

                    # 记录隐私消耗
                    self.privacy_accountant.record_composition(noise_std, sensitivity)

            logger.debug(f"向 {len(gradients)} 个参数添加了差分隐私噪声")
            return noisy_gradients

        except Exception as e:
            logger.error(f"添加差分隐私噪声失败: {e}")
            raise

    def _calculate_noise_std(self, sensitivity: float) -> float:
        """计算噪声标准差"""
        # σ = sensitivity * noise_multiplier / epsilon
        return sensitivity * self.noise_multiplier / self.epsilon

    def _clip_gradient(self, gradient: torch.Tensor, threshold: float) -> torch.Tensor:
        """梯度裁剪"""
        # 计算梯度范数
        grad_norm = torch.norm(gradient)

        # 如果范数超过阈值，则进行裁剪
        if grad_norm > threshold:
            clip_factor = threshold / grad_norm
            return gradient * clip_factor
        return gradient

    def get_privacy_loss(self) -> Dict[str, float]:
        """获取隐私损失统计"""
        return {
            "epsilon": self.epsilon,
            "delta": self.delta,
            "consumed_budget": self.budget.consumed,
            "remaining_budget": self.budget.remaining(),
            "budget_utilization": (
                self.budget.consumed / self.epsilon if self.epsilon > 0 else 0
            ),
        }


class PrivacyAccountant:
    """隐私会计器 - 跟踪复合隐私损失"""

    def __init__(self):
        self.compositions = []  # 记录每次组合
        self.total_epsilon = 0.0
        self.total_delta = 0.0

    def record_composition(self, noise_std: float, sensitivity: float):
        """记录一次隐私组合"""
        composition = {
            "noise_std": noise_std,
            "sensitivity": sensitivity,
            "timestamp": datetime.now(),
        }
        self.compositions.append(composition)

    def calculate_advanced_composition(
        self, delta: float = 1e-5
    ) -> Tuple[float, float]:
        """
        使用高级组合定理计算总的隐私损失
        """
        if not self.compositions:
            return 0.0, 0.0

        k = len(self.compositions)  # 组合次数
        epsilons = []

        for comp in self.compositions:
            # 对于每个高斯机制，计算ε
            sigma = comp["noise_std"]
            sensitivity = comp["sensitivity"]
            epsilon_i = sensitivity / sigma * math.sqrt(2 * math.log(1.25 / delta))
            epsilons.append(epsilon_i)

        # 高级组合定理
        total_epsilon = (
            math.sqrt(2 * k * math.log(1 / delta)) * max(epsilons)
            + k * max(epsilons) ** 2
        )
        total_delta = k * delta

        self.total_epsilon = total_epsilon
        self.total_delta = total_delta

        return total_epsilon, total_delta


class SecureAggregation:
    """安全聚合机制"""

    def __init__(self, privacy_engine: DifferentialPrivacyEngine):
        self.privacy_engine = privacy_engine
        self.participants_weights = {}  # 存储各参与方的权重
        self.aggregation_count = 0

    def aggregate_with_dp(
        self, model_updates: List[Dict[str, Any]], weights: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        使用差分隐私的安全聚合

        Args:
            model_updates: 各参与方的模型更新
            weights: 参与方权重（可选）

        Returns:
            聚合后的模型参数
        """
        try:
            if not model_updates:
                raise ValueError("没有模型更新可供聚合")

            # 设置默认权重
            if weights is None:
                weights = [1.0 / len(model_updates)] * len(model_updates)

            # 验证权重
            if len(weights) != len(model_updates):
                raise ValueError("权重数量与模型更新数量不匹配")

            # 获取模型参数键
            param_keys = model_updates[0].keys()

            # 初始化聚合结果
            aggregated_params = {}

            # 对每个参数进行加权聚合
            for param_key in param_keys:
                weighted_sum = None

                for i, (update, weight) in enumerate(zip(model_updates, weights)):
                    param_value = update.get(param_key)

                    if param_value is not None:
                        if weighted_sum is None:
                            weighted_sum = param_value * weight
                        else:
                            weighted_sum += param_value * weight

                if weighted_sum is not None:
                    aggregated_params[param_key] = weighted_sum

            # 添加聚合级别的差分隐私噪声
            if edu_config.edu_data_privacy_level == "high":
                aggregated_params = self._add_aggregation_noise(aggregated_params)

            self.aggregation_count += 1
            logger.info(f"完成第 {self.aggregation_count} 次安全聚合")

            return aggregated_params

        except Exception as e:
            logger.error(f"安全聚合失败: {e}")
            raise

    def _add_aggregation_noise(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """向聚合结果添加额外的隐私噪声"""
        noisy_params = {}

        for param_key, param_value in params.items():
            if isinstance(param_value, (torch.Tensor, np.ndarray)):
                # 计算参数的敏感度
                sensitivity = self._estimate_sensitivity(param_value)

                # 添加噪声
                if isinstance(param_value, torch.Tensor):
                    noise = torch.normal(
                        mean=0.0,
                        std=sensitivity * 0.1,  # 聚合层噪声较小
                        size=param_value.shape,
                        device=param_value.device,
                    )
                    noisy_params[param_key] = param_value + noise
                else:
                    noise = np.random.normal(0, sensitivity * 0.1, param_value.shape)
                    noisy_params[param_key] = param_value + noise
            else:
                # 对标量值添加噪声
                sensitivity = abs(param_value) * 0.01 if param_value != 0 else 0.01
                noise = np.random.normal(0, sensitivity)
                noisy_params[param_key] = param_value + noise

        return noisy_params

    def _estimate_sensitivity(self, param_value) -> float:
        """估计参数敏感度"""
        if isinstance(param_value, (torch.Tensor, np.ndarray)):
            return (
                float(torch.std(param_value).item())
                if torch.numel(param_value) > 1
                else abs(float(param_value))
            )
        else:
            return abs(float(param_value)) * 0.1


class DataAnonymization:
    """数据匿名化工具"""

    @staticmethod
    def k_anonymize(
        data: List[Dict], quasi_identifiers: List[str], k: int = 5
    ) -> List[Dict]:
        """
        K-匿名化处理

        Args:
            data: 原始数据列表
            quasi_identifiers: 准标识符列表
            k: K值

        Returns:
            匿名化后的数据
        """
        try:
            if not data or not quasi_identifiers:
                return data

            # 按准标识符分组
            groups = {}
            for record in data:
                key = tuple(record.get(qi, "") for qi in quasi_identifiers)
                if key not in groups:
                    groups[key] = []
                groups[key].append(record)

            # 对小组进行泛化处理
            anonymized_data = []
            for group_records in groups.values():
                if len(group_records) >= k:
                    # 直接保留
                    anonymized_data.extend(group_records)
                else:
                    # 需要泛化处理
                    generalized_records = DataAnonymization._generalize_records(
                        group_records, quasi_identifiers
                    )
                    anonymized_data.extend(generalized_records)

            logger.info(
                f"K-匿名化处理完成: 原始记录 {len(data)}, 匿名化后 {len(anonymized_data)}"
            )
            return anonymized_data

        except Exception as e:
            logger.error(f"K-匿名化处理失败: {e}")
            return data

    @staticmethod
    def _generalize_records(
        records: List[Dict], quasi_identifiers: List[str]
    ) -> List[Dict]:
        """对记录进行泛化处理"""
        if not records:
            return []

        generalized = []
        for record in records:
            gen_record = record.copy()
            for qi in quasi_identifiers:
                if qi in gen_record:
                    gen_record[qi] = DataAnonymization._generalize_value(gen_record[qi])
            generalized.append(gen_record)

        return generalized

    @staticmethod
    def _generalize_value(value) -> str:
        """泛化单个值"""
        if isinstance(value, (int, float)):
            # 数值泛化
            val = float(value)
            if val < 10:
                return "<10"
            elif val < 20:
                return "10-19"
            elif val < 30:
                return "20-29"
            elif val < 50:
                return "30-49"
            else:
                return "50+"
        elif isinstance(value, str):
            # 字符串泛化
            if len(value) > 3:
                return value[:2] + "*" * (len(value) - 2)
            else:
                return "*" * len(value)
        else:
            return str(value)


class AuditLogger:
    """隐私审计日志"""

    def __init__(self):
        self.audit_trail = []

    def log_privacy_operation(self, operation: str, details: Dict[str, Any]):
        """记录隐私相关操作"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details,
            "user_agent": details.get("user_agent", "unknown"),
            "ip_address": details.get("ip_address", "unknown"),
        }

        self.audit_trail.append(log_entry)
        logger.info(f"隐私操作已记录: {operation}")

    def get_audit_report(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> List[Dict]:
        """获取审计报告"""
        filtered_logs = self.audit_trail

        if start_time:
            filtered_logs = [
                log
                for log in filtered_logs
                if datetime.fromisoformat(log["timestamp"]) >= start_time
            ]

        if end_time:
            filtered_logs = [
                log
                for log in filtered_logs
                if datetime.fromisoformat(log["timestamp"]) <= end_time
            ]

        return filtered_logs

    def export_audit_log(self, filename: str):
        """导出审计日志"""
        import json

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.audit_trail, f, indent=2, ensure_ascii=False)


# 全局隐私保护实例
dp_engine = DifferentialPrivacyEngine(epsilon=edu_config.fl_privacy_epsilon, delta=1e-5)

audit_logger = AuditLogger()


if __name__ == "__main__":
    # 测试差分隐私引擎
    print("测试差分隐私引擎...")

    # 创建测试梯度
    test_gradients = {
        "layer1.weight": torch.randn(10, 5),
        "layer2.bias": torch.randn(10),
    }

    # 添加噪声
    noisy_gradients = dp_engine.add_noise_to_gradients(test_gradients)
    print(f"原始梯度数量: {len(test_gradients)}")
    print(f"加噪后梯度数量: {len(noisy_gradients)}")

    # 检查隐私损失
    privacy_loss = dp_engine.get_privacy_loss()
    print(f"隐私损失: {privacy_loss}")

    # 测试数据匿名化
    test_data = [
        {"name": "张三", "age": 25, "city": "北京"},
        {"name": "李四", "age": 26, "city": "北京"},
        {"name": "王五", "age": 24, "city": "上海"},
    ]

    anonymized_data = DataAnonymization.k_anonymize(
        test_data, quasi_identifiers=["age", "city"], k=2
    )
    print(f"匿名化前: {test_data}")
    print(f"匿名化后: {anonymized_data}")
