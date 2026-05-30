"""
模型压缩器
实现多种模型压缩技术，包括量化、剪枝和知识蒸馏
专为推荐系统场景优化
"""

from datetime import datetime
import hashlib
import logging
import os
from typing import Any, Dict, List, Union

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier

from config.transfer_learning_config import settings

logger = logging.getLogger(__name__)


class ModelCompressor:
    """模型压缩器主类"""

    def __init__(self, config=None):
        self.config = config or settings.compression
        self.compression_history = []
        self.compressed_models = {}

    def compress_model(self, model: Any, method: str = "auto") -> Dict[str, Any]:
        """
        压缩给定模型
        支持自动选择最优压缩方法
        """
        logger.info(f"开始模型压缩，方法: {method}")

        if method == "auto":
            method = self._select_optimal_compression_method(model)

        # 根据方法选择压缩策略
        compression_strategies = {
            "quantization": self._quantize_model,
            "pruning": self._prune_model,
            "knowledge_distillation": self._distill_model,
            "feature_selection": self._select_features,
            "ensemble_reduction": self._reduce_ensemble,
        }

        if method not in compression_strategies:
            raise ValueError(f"不支持的压缩方法: {method}")

        # 执行压缩
        compressed_result = compression_strategies[method](model)

        # 记录压缩历史
        compression_record = {
            "method": method,
            "original_size": self._get_model_size(model),
            "compressed_size": self._get_model_size(compressed_result["model"]),
            "compression_ratio": self._calculate_compression_ratio(
                model, compressed_result["model"]
            ),
            "timestamp": datetime.now().isoformat(),
            "model_hash": self._hash_model(model),
        }

        self.compression_history.append(compression_record)
        self.compressed_models[method] = compressed_result

        logger.info(
            f"模型压缩完成，压缩比: {compression_record['compression_ratio']:.2f}"
        )
        return compressed_result

    def _select_optimal_compression_method(self, model: Any) -> str:
        """自动选择最优压缩方法"""
        model_type = type(model).__name__

        # 基于模型类型的选择策略
        if "Forest" in model_type or "Tree" in model_type:
            return "pruning"  # 树模型适合剪枝
        elif "Regression" in model_type or "Linear" in model_type:
            return "quantization"  # 线性模型适合量化
        elif hasattr(model, "estimators_"):  # 集成模型
            return "ensemble_reduction"
        else:
            return "feature_selection"  # 默认特征选择

    def _quantize_model(self, model: Any) -> Dict[str, Any]:
        """模型量化压缩"""
        logger.info("执行模型量化...")

        quantized_params = {}

        # 量化不同类型的参数
        if hasattr(model, "coef_"):
            # 线性模型系数量化
            quantized_params["coef_"] = self._quantize_array(
                model.coef_, self.config.quantization_bits
            )
            if hasattr(model, "intercept_"):
                quantized_params["intercept_"] = self._quantize_array(
                    model.intercept_, self.config.quantization_bits
                )

        if hasattr(model, "feature_importances_"):
            # 特征重要性量化
            quantized_params["feature_importances_"] = self._quantize_array(
                model.feature_importances_, self.config.quantization_bits
            )

        # 创建量化后的模型副本
        quantized_model = self._create_quantized_model_copy(model, quantized_params)

        return {
            "model": quantized_model,
            "compression_info": {
                "method": "quantization",
                "bits": self.config.quantization_bits,
                "original_params": self._extract_model_params(model),
                "quantized_params": quantized_params,
            },
        }

    def _prune_model(self, model: Any) -> Dict[str, Any]:
        """模型剪枝压缩"""
        logger.info("执行模型剪枝...")

        if isinstance(model, (RandomForestClassifier, RandomForestRegressor)):
            # 随机森林剪枝
            pruned_model = self._prune_random_forest(model)
        elif isinstance(model, DecisionTreeClassifier):
            # 决策树剪枝
            pruned_model = self._prune_decision_tree(model)
        else:
            # 通用剪枝方法
            pruned_model = self._general_pruning(model)

        return {
            "model": pruned_model,
            "compression_info": {
                "method": "pruning",
                "pruning_ratio": self.config.pruning_ratio,
                "pruned_components": self._identify_prunable_components(model),
            },
        }

    def _distill_model(self, model: Any) -> Dict[str, Any]:
        """知识蒸馏压缩"""
        logger.info("执行知识蒸馏...")

        # 简化版知识蒸馏：训练更小的学生模型
        distilled_model = self._train_distilled_student(model)

        return {
            "model": distilled_model,
            "compression_info": {
                "method": "knowledge_distillation",
                "distillation_config": {"temperature": 3.0, "alpha": 0.7},
            },
        }

    def _select_features(self, model: Any) -> Dict[str, Any]:
        """特征选择压缩"""
        logger.info("执行特征选择...")

        # 基于特征重要性的特征选择
        if hasattr(model, "feature_importances_"):
            selected_features = self._select_important_features(
                model.feature_importances_
            )
        else:
            # 默认选择前80%的特征
            n_features = getattr(model, "n_features_", 100)
            selected_features = list(range(int(n_features * 0.8)))

        # 创建特征选择后的模型
        feature_selected_model = self._create_feature_selected_model(
            model, selected_features
        )

        return {
            "model": feature_selected_model,
            "compression_info": {
                "method": "feature_selection",
                "selected_features": selected_features,
                "selection_ratio": len(selected_features)
                / getattr(model, "n_features_", 100),
            },
        }

    def _reduce_ensemble(self, model: Any) -> Dict[str, Any]:
        """集成模型约简"""
        logger.info("执行集成模型约简...")

        if hasattr(model, "estimators_"):
            # 减少基学习器数量
            reduced_model = self._reduce_ensemble_size(model)
        else:
            reduced_model = model  # 如果不是集成模型，返回原模型

        return {
            "model": reduced_model,
            "compression_info": {
                "method": "ensemble_reduction",
                "original_estimators": len(getattr(model, "estimators_", [])),
                "reduced_estimators": len(getattr(reduced_model, "estimators_", [])),
            },
        }

    def _quantize_array(self, arr: np.ndarray, bits: int) -> np.ndarray:
        """数组量化"""
        if bits == 8:
            # 8位量化
            scale = np.max(np.abs(arr)) / 127.0
            quantized = np.round(arr / scale).astype(np.int8)
            return quantized
        elif bits == 16:
            # 16位量化
            return arr.astype(np.float16)
        else:
            # 其他位宽，简单缩放
            scale = 2 ** (bits - 1) - 1
            normalized = np.clip(arr / np.max(np.abs(arr)), -1, 1)
            quantized = np.round(normalized * scale).astype(np.int32)
            return quantized

    def _create_quantized_model_copy(
        self, original_model: Any, quantized_params: Dict
    ) -> Any:
        """创建量化后的模型副本"""
        import copy

        quantized_model = copy.deepcopy(original_model)

        # 更新量化参数
        for param_name, quantized_value in quantized_params.items():
            if hasattr(quantized_model, param_name):
                setattr(quantized_model, param_name, quantized_value)

        return quantized_model

    def _extract_model_params(self, model: Any) -> Dict[str, Any]:
        """提取模型参数用于比较"""
        params = {}
        param_names = ["coef_", "intercept_", "feature_importances_"]

        for param_name in param_names:
            if hasattr(model, param_name):
                params[param_name] = getattr(model, param_name)

        return params

    def _prune_random_forest(
        self, rf_model: Union[RandomForestClassifier, RandomForestRegressor]
    ) -> Any:
        """随机森林剪枝"""
        import copy

        pruned_rf = copy.deepcopy(rf_model)

        # 剪枝策略：移除最不重要的树
        n_estimators_to_keep = int(
            len(rf_model.estimators_) * (1 - self.config.pruning_ratio)
        )

        if hasattr(rf_model, "feature_importances_"):
            # 基于特征重要性重新训练较小的森林
            pruned_rf.n_estimators = n_estimators_to_keep
            # 这里简化处理，实际应该重新训练
        else:
            # 简单地减少树的数量
            pruned_rf.estimators_ = rf_model.estimators_[:n_estimators_to_keep]

        return pruned_rf

    def _prune_decision_tree(self, tree_model: DecisionTreeClassifier) -> Any:
        """决策树剪枝"""
        import copy

        pruned_tree = copy.deepcopy(tree_model)

        # 设置剪枝参数
        if hasattr(pruned_tree, "min_samples_leaf"):
            pruned_tree.min_samples_leaf = max(
                2, int(pruned_tree.min_samples_leaf * (1 + self.config.pruning_ratio))
            )

        return pruned_tree

    def _general_pruning(self, model: Any) -> Any:
        """通用剪枝方法"""
        # 对于不支持特定剪枝的模型，返回原模型
        return model

    def _identify_prunable_components(self, model: Any) -> List[str]:
        """识别可剪枝的组件"""
        prunable = []

        if hasattr(model, "estimators_"):
            prunable.append("estimators")
        if hasattr(model, "feature_importances_"):
            prunable.append("features")
        if hasattr(model, "coef_"):
            prunable.append("coefficients")

        return prunable

    def _train_distilled_student(self, teacher_model: Any) -> Any:
        """训练蒸馏学生模型"""
        # 简化实现：训练一个更小的模型
        from sklearn.ensemble import RandomForestClassifier

        student_model = RandomForestClassifier(
            n_estimators=20, max_depth=5, random_state=42  # 减少树的数量  # 降低深度
        )

        # 注意：实际应用中需要真实的训练数据
        # 这里只是返回结构，实际训练需要在具体使用时进行
        return student_model

    def _select_important_features(self, feature_importances: np.ndarray) -> List[int]:
        """选择重要特征"""
        # 选择前k个最重要的特征
        k = int(len(feature_importances) * (1 - self.config.pruning_ratio))
        important_indices = np.argsort(feature_importances)[-k:]
        return important_indices.tolist()

    def _create_feature_selected_model(
        self, original_model: Any, selected_features: List[int]
    ) -> Any:
        """创建特征选择后的模型"""
        import copy

        selected_model = copy.deepcopy(original_model)

        # 存储特征选择信息
        if not hasattr(selected_model, "_selected_features"):
            selected_model._selected_features = selected_features

        return selected_model

    def _reduce_ensemble_size(self, ensemble_model: Any) -> Any:
        """减少集成模型大小"""
        import copy

        reduced_model = copy.deepcopy(ensemble_model)

        if hasattr(ensemble_model, "estimators_"):
            n_estimators = len(ensemble_model.estimators_)
            n_to_keep = max(1, int(n_estimators * (1 - self.config.pruning_ratio)))
            reduced_model.estimators_ = ensemble_model.estimators_[:n_to_keep]

        return reduced_model

    def _get_model_size(self, model: Any) -> int:
        """获取模型大小（字节）"""
        try:
            # 使用 joblib 估算模型大小
            temp_path = f"temp_model_{hash(str(model))}.pkl"
            joblib.dump(model, temp_path)
            size = os.path.getsize(temp_path)
            os.remove(temp_path)
            return size
        except (OSError, IOError, AttributeError, TypeError):
            # 估算大小
            if hasattr(model, "coef_"):
                return (
                    model.coef_.nbytes
                    + getattr(model, "intercept_", np.array([])).nbytes
                )
            elif hasattr(model, "estimators_"):
                return len(model.estimators_) * 10000  # 估算每棵树 10KB
            else:
                return 10000  # 默认大小

    def _calculate_compression_ratio(
        self, original_model: Any, compressed_model: Any
    ) -> float:
        """计算压缩比"""
        original_size = self._get_model_size(original_model)
        compressed_size = self._get_model_size(compressed_model)
        return compressed_size / original_size if original_size > 0 else 1.0

    def _hash_model(self, model: Any) -> str:
        """计算模型哈希值"""
        try:
            model_str = str(model)
            return hashlib.md5(model_str.encode()).hexdigest()[:16]
        except:
            return "unknown_hash"

    def batch_compress_models(
        self, models: Dict[str, Any], methods: List[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """批量压缩多个模型"""
        if methods is None:
            methods = ["quantization", "pruning", "feature_selection"]

        results = {}

        for model_name, model in models.items():
            results[model_name] = {}
            for method in methods:
                try:
                    compressed_result = self.compress_model(model, method)
                    results[model_name][method] = compressed_result
                    logger.info(f"模型 {model_name} 使用 {method} 压缩完成")
                except Exception as e:
                    logger.error(f"模型 {model_name} 使用 {method} 压缩失败: {e}")
                    results[model_name][method] = {"error": str(e)}

        return results

    def compare_compression_methods(
        self, model: Any, methods: List[str] = None
    ) -> Dict[str, Any]:
        """比较不同压缩方法的效果"""
        if methods is None:
            methods = ["quantization", "pruning", "feature_selection"]

        comparison_results = {}

        original_size = self._get_model_size(model)
        original_performance = self._evaluate_model(model)  # 需要实现

        for method in methods:
            try:
                compressed_result = self.compress_model(model, method)
                compressed_model = compressed_result["model"]

                compressed_size = self._get_model_size(compressed_model)
                compressed_performance = self._evaluate_model(compressed_model)

                comparison_results[method] = {
                    "compression_ratio": compressed_size / original_size,
                    "size_reduction": (original_size - compressed_size) / original_size,
                    "performance_preservation": self._compare_performance(
                        original_performance, compressed_performance
                    ),
                    "compression_info": compressed_result["compression_info"],
                }

            except Exception as e:
                comparison_results[method] = {"error": str(e)}

        return comparison_results

    def _evaluate_model(self, model: Any) -> Dict[str, float]:
        """评估模型性能（简化版）"""
        # 实际应用中需要真实的测试数据
        return {
            "accuracy": 0.85,  # 模拟值
            "inference_time": 0.01,  # 秒
            "memory_usage": 1000000,  # 字节
        }

    def _compare_performance(
        self, original_perf: Dict[str, float], compressed_perf: Dict[str, float]
    ) -> Dict[str, float]:
        """比较性能变化"""
        comparison = {}
        for metric in original_perf:
            if metric in compressed_perf:
                original_val = original_perf[metric]
                compressed_val = compressed_perf[metric]

                if metric == "accuracy":
                    comparison[metric] = compressed_val / original_val
                elif metric in ["inference_time", "memory_usage"]:
                    comparison[metric] = original_val / compressed_val  # 越大越好

        return comparison

    def get_compression_report(self) -> Dict[str, Any]:
        """获取压缩报告"""
        report = {
            "compression_history": self.compression_history,
            "compressed_models": list(self.compressed_models.keys()),
            "average_compression_ratio": 0.0,
            "best_method": None,
        }

        if self.compression_history:
            ratios = [
                record["compression_ratio"] for record in self.compression_history
            ]
            report["average_compression_ratio"] = np.mean(ratios)

            # 找到最佳压缩方法
            best_record = min(
                self.compression_history, key=lambda x: x["compression_ratio"]
            )
            report["best_method"] = best_record["method"]

        report["timestamp"] = datetime.now().isoformat()
        return report

    def save_compressed_model(
        self, model_name: str, method: str, save_path: str = None
    ) -> str:
        """保存压缩模型"""
        if method not in self.compressed_models:
            raise ValueError(f"未找到压缩方法 {method} 的模型")

        if save_path is None:
            save_path = os.path.join(
                self.config.model_save_path,
                f"compressed_{model_name}_{method}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl",
            )

        compressed_result = self.compressed_models[method]
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        joblib.dump(compressed_result, save_path)

        logger.info(f"压缩模型已保存到: {save_path}")
        return save_path


# 测试和演示函数
def demo_model_compressor():
    """演示模型压缩器"""
    print("=== 模型压缩器演示 ===")

    # 创建压缩器
    compressor = ModelCompressor()

    # 1. 创建测试模型
    print("1. 创建测试模型...")
    from sklearn.datasets import make_classification
    from sklearn.ensemble import RandomForestClassifier

    X, y = make_classification(n_samples=1000, n_features=20, random_state=42)
    test_model = RandomForestClassifier(n_estimators=50, random_state=42)
    test_model.fit(X, y)

    print(f"   原始模型大小估计: {compressor._get_model_size(test_model)} 字节")

    # 2. 压缩模型
    print("2. 执行模型压缩...")
    compressed_result = compressor.compress_model(test_model, "auto")
    print(
        f"   压缩后模型大小: {compressor._get_model_size(compressed_result['model'])} 字节"
    )
    print(f"   压缩比: {compressed_result['compression_info']['method']}")

    # 3. 比较不同压缩方法
    print("3. 比较压缩方法...")
    comparison = compressor.compare_compression_methods(test_model)
    for method, result in comparison.items():
        if "error" not in result:
            print(
                f"   {method}: 压缩比 {result['compression_ratio']:.3f}, "
                f"性能保持 {result['performance_preservation'].get('accuracy', 0):.3f}"
            )

    # 4. 生成报告
    print("4. 生成压缩报告...")
    report = compressor.get_compression_report()
    print(f"   平均压缩比: {report['average_compression_ratio']:.3f}")
    print(f"   最佳方法: {report['best_method']}")

    print("\n=== 演示完成 ===")
    return compressor


if __name__ == "__main__":
    demo_model_compressor()
