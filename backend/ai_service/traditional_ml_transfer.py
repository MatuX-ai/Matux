"""
传统机器学习迁移学习框架
基于Scikit-learn实现的知识迁移和模型压缩
适用于Python 3.14环境下的冷启动数据增强
"""

from datetime import datetime
import logging
import os
from typing import Any, Dict, List

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from config.transfer_learning_config import settings

logger = logging.getLogger(__name__)


class TraditionalTransferLearning:
    """基于传统机器学习的迁移学习框架"""

    def __init__(self, config=None):
        self.config = config or settings
        self.models = {}  # 存储不同阶段的模型
        self.vectorizers = {}  # 特征向量化器
        self.performance_history = []  # 性能历史记录

    def load_assistments_data(self, data_path: str = None) -> pd.DataFrame:
        """
        加载ASSISTments数据集
        由于HF datasets可能存在兼容性问题，优先使用本地CSV文件
        """
        if data_path is None:
            data_path = self.config.dataset.processed_data_path

        try:
            # 尝试从本地文件加载
            if os.path.exists(data_path):
                logger.info(f"从本地文件加载数据: {data_path}")
                df = pd.read_csv(data_path)
                logger.info(f"成功加载 {len(df)} 条记录")
                return df
            else:
                # 如果没有本地文件，生成模拟数据用于演示
                logger.warning("本地数据文件不存在，生成模拟数据")
                return self._generate_mock_assistments_data()

        except Exception as e:
            logger.error(f"数据加载失败: {e}")
            # 返回模拟数据作为后备方案
            return self._generate_mock_assistments_data()

    def _generate_mock_assistments_data(self) -> pd.DataFrame:
        """生成模拟的ASSISTments数据用于演示"""
        np.random.seed(self.config.dataset.random_seed)

        n_samples = 10000
        n_skills = 100
        n_problems = 500

        # 生成模拟数据
        data = {
            "student_id": np.random.randint(1, 1000, n_samples),
            "problem_id": np.random.randint(1, n_problems, n_samples),
            "skill_ids": [
                np.random.choice(range(n_skills), size=np.random.randint(1, 5)).tolist()
                for _ in range(n_samples)
            ],
            "correct": np.random.binomial(1, 0.7, n_samples),  # 70%正确率
            "attempt_count": np.random.randint(1, 4, n_samples),
            "time_spent": np.random.exponential(30, n_samples),  # 平均30秒
            "timestamp": pd.date_range("2023-01-01", periods=n_samples, freq="1min"),
        }

        df = pd.DataFrame(data)

        # 添加技能描述文本
        skill_descriptions = [f"数学技能_{i}" for i in range(n_skills)]
        df["skill_text"] = df["skill_ids"].apply(
            lambda skills: " ".join([skill_descriptions[s] for s in skills])
        )

        # 添加问题文本
        problem_templates = [
            "解方程题",
            "几何证明",
            "函数图像",
            "概率统计",
            "代数运算",
            "微积分",
            "线性代数",
            "离散数学",
        ]
        df["problem_text"] = df["problem_id"].apply(
            lambda pid: f"{problem_templates[pid % len(problem_templates)]} 题目{pid}"
        )

        logger.info(f"生成模拟数据: {len(df)} 条记录")
        return df

    def preprocess_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        数据预处理和特征工程
        """
        logger.info("开始数据预处理...")

        # 特征提取
        features = {}

        # 1. 文本特征 - 技能描述TF-IDF
        if "skill_text" in df.columns:
            tfidf_vectorizer = TfidfVectorizer(
                max_features=1000, ngram_range=(1, 2), min_df=2
            )
            skill_features = tfidf_vectorizer.fit_transform(df["skill_text"])
            features["skill_tfidf"] = skill_features.toarray()
            self.vectorizers["skill_tfidf"] = tfidf_vectorizer

        # 2. 数值特征
        numerical_features = []
        if "attempt_count" in df.columns:
            numerical_features.append("attempt_count")
        if "time_spent" in df.columns:
            numerical_features.append("time_spent")

        if numerical_features:
            scaler = StandardScaler()
            scaled_numerical = scaler.fit_transform(df[numerical_features])
            features["numerical"] = scaled_numerical
            self.vectorizers["numerical_scaler"] = scaler

        # 3. 统计特征
        # 学生历史表现统计
        student_stats = (
            df.groupby("student_id")
            .agg(
                {
                    "correct": ["mean", "count"],
                    "time_spent": "mean",
                    "attempt_count": "mean",
                }
            )
            .reset_index()
        )

        student_stats.columns = [
            "student_id",
            "accuracy_rate",
            "total_attempts",
            "avg_time_spent",
            "avg_attempt_count",
        ]
        features["student_stats"] = student_stats

        # 4. 目标变量
        y = (
            df["correct"].values
            if "correct" in df.columns
            else np.random.binomial(1, 0.7, len(df))
        )

        logger.info(
            f"特征工程完成，特征维度: {sum(len(v) if hasattr(v, '__len__') else v.shape[1] for v in features.values())}"
        )
        return {"features": features, "target": y, "raw_data": df}

    def train_teacher_model(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        训练教师模型（传统ML模型）
        """
        logger.info("训练教师模型...")

        features = processed_data["features"]
        y = processed_data["target"]

        # 合并特征
        X_combined = self._combine_features(features)

        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X_combined,
            y,
            test_size=self.config.dataset.test_size,
            random_state=self.config.dataset.random_seed,
        )

        # 训练多个候选模型
        models = {
            "random_forest": RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=self.config.dataset.random_seed,
            ),
            "logistic_regression": LogisticRegression(
                random_state=self.config.dataset.random_seed, max_iter=1000
            ),
        }

        best_model = None
        best_score = 0
        model_scores = {}

        for name, model in models.items():
            logger.info(f"训练 {name} 模型...")
            model.fit(X_train, y_train)

            # 评估模型
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            precision, recall, f1, _ = precision_recall_fscore_support(
                y_test, y_pred, average="binary"
            )

            model_scores[name] = {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }

            logger.info(f"{name} - 准确率: {accuracy:.4f}, F1: {f1:.4f}")

            if accuracy > best_score:
                best_score = accuracy
                best_model = model
                self.models["teacher"] = model

        # 保存性能记录
        performance_record = {
            "model_type": "teacher",
            "timestamp": datetime.now().isoformat(),
            "scores": model_scores,
            "best_model": type(best_model).__name__,
            "feature_dimension": X_combined.shape[1],
        }
        self.performance_history.append(performance_record)

        logger.info(f"教师模型训练完成，最佳准确率: {best_score:.4f}")
        return {
            "model": best_model,
            "performance": model_scores,
            "feature_importance": self._get_feature_importance(
                best_model, X_combined.shape[1]
            ),
        }

    def _combine_features(self, features: Dict[str, Any]) -> np.ndarray:
        """合并不同类型特征"""
        feature_arrays = []

        # 处理稠密特征
        dense_features = ["skill_tfidf", "numerical"]
        for feat_name in dense_features:
            if feat_name in features:
                feature_arrays.append(features[feat_name])

        # 处理学生统计特征
        if "student_stats" in features:
            stats_df = features["student_stats"]
            stat_features = stats_df[
                [
                    "accuracy_rate",
                    "total_attempts",
                    "avg_time_spent",
                    "avg_attempt_count",
                ]
            ].fillna(0)
            feature_arrays.append(stat_features.values)

        # 合并所有特征
        if feature_arrays:
            return np.hstack(feature_arrays)
        else:
            # 如果没有特征，返回默认特征
            return np.random.rand(len(next(iter(features.values()))), 10)

    def _get_feature_importance(self, model, n_features: int) -> List[float]:
        """获取特征重要性"""
        if hasattr(model, "feature_importances_"):
            return model.feature_importances_.tolist()
        elif hasattr(model, "coef_"):
            return np.abs(model.coef_[0]).tolist()
        else:
            return [1.0 / n_features] * n_features

    def compress_model(self, teacher_model, method: str = "pruning") -> Dict[str, Any]:
        """
        模型压缩实现
        """
        logger.info(f"开始模型压缩: {method}")

        compressed_model = None
        compression_info = {}

        if method == "pruning":
            # 特征剪枝 - 移除低重要性的特征
            feature_importance = self._get_feature_importance(
                teacher_model, 1000
            )  # 假设1000维特征
            importance_threshold = np.percentile(
                feature_importance, 70
            )  # 保留前30%重要特征

            pruned_indices = [
                i
                for i, imp in enumerate(feature_importance)
                if imp >= importance_threshold
            ]
            compression_ratio = len(pruned_indices) / len(feature_importance)

            compressed_model = {
                "model": teacher_model,
                "pruned_indices": pruned_indices,
                "compression_ratio": compression_ratio,
            }

            compression_info = {
                "method": "feature_pruning",
                "original_features": len(feature_importance),
                "retained_features": len(pruned_indices),
                "compression_ratio": compression_ratio,
            }

        elif method == "quantization":
            # 简单量化 - 将浮点数转换为整数
            if hasattr(teacher_model, "coef_"):
                # 对线性模型进行量化
                coef_quantized = np.round(teacher_model.coef_ * 1000).astype(np.int32)
                intercept_quantized = np.round(teacher_model.intercept_ * 1000).astype(
                    np.int32
                )

                compressed_model = {
                    "coef": coef_quantized,
                    "intercept": intercept_quantized,
                    "scale_factor": 1000,
                }

                compression_info = {
                    "method": "coefficient_quantization",
                    "scale_factor": 1000,
                    "original_size": teacher_model.coef_.nbytes
                    + teacher_model.intercept_.nbytes,
                    "compressed_size": coef_quantized.nbytes
                    + intercept_quantized.nbytes,
                }

        # 保存压缩模型
        self.models[f"compressed_{method}"] = compressed_model

        logger.info(f"模型压缩完成: {compression_info}")
        return {"model": compressed_model, "info": compression_info}

    def predict_with_compressed_model(
        self, X: np.ndarray, method: str = "pruning"
    ) -> np.ndarray:
        """使用压缩模型进行预测"""
        compressed_model = self.models.get(f"compressed_{method}")

        if not compressed_model:
            raise ValueError(f"未找到压缩模型: {method}")

        if method == "pruning":
            # 使用剪枝后的特征索引
            pruned_X = X[:, compressed_model["pruned_indices"]]
            return compressed_model["model"].predict(pruned_X)
        elif method == "quantization":
            # 使用量化系数进行预测
            scaled_X = X * compressed_model["scale_factor"]
            logits = (
                np.dot(scaled_X, compressed_model["coef"].T)
                + compressed_model["intercept"]
            )
            return (logits > 0).astype(int)

        return np.zeros(len(X))  # 默认返回

    def save_model(self, model_name: str, model_path: str = None) -> str:
        """保存模型到磁盘"""
        if model_path is None:
            model_path = self.config.get_model_path(model_name)

        model_data = {
            "model": self.models.get(model_name),
            "vectorizers": self.vectorizers,
            "config": self.config.__dict__,
            "performance_history": self.performance_history,
            "timestamp": datetime.now().isoformat(),
        }

        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(model_data, model_path)
        logger.info(f"模型已保存到: {model_path}")
        return model_path

    def load_model(self, model_path: str) -> bool:
        """从磁盘加载模型"""
        try:
            model_data = joblib.load(model_path)
            self.models.update(model_data.get("model", {}))
            self.vectorizers.update(model_data.get("vectorizers", {}))
            self.performance_history = model_data.get("performance_history", [])
            logger.info(f"模型已从 {model_path} 加载")
            return True
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            "performance_history": self.performance_history,
            "current_models": list(self.models.keys()),
            "vectorizers": list(self.vectorizers.keys()),
            "latest_performance": (
                self.performance_history[-1] if self.performance_history else None
            ),
        }


# 使用示例和测试函数
def demo_traditional_transfer_learning():
    """演示传统迁移学习流程"""
    print("=== 传统迁移学习演示 ===")

    # 初始化迁移学习框架
    transfer_learn = TraditionalTransferLearning()

    # 1. 加载数据
    print("1. 加载数据...")
    data = transfer_learn.load_assistments_data()
    print(f"   数据形状: {data.shape}")

    # 2. 数据预处理
    print("2. 数据预处理...")
    processed_data = transfer_learn.preprocess_data(data)

    # 3. 训练教师模型
    print("3. 训练教师模型...")
    teacher_result = transfer_learn.train_teacher_model(processed_data)
    print(
        f"   最佳模型准确率: {max(score['accuracy'] for score in teacher_result['performance'].values()):.4f}"
    )

    # 4. 模型压缩
    print("4. 模型压缩...")
    compressed_result = transfer_learn.compress_model(
        teacher_result["model"], "pruning"
    )
    print(f"   压缩比率: {compressed_result['info']['compression_ratio']:.2f}")

    # 5. 保存模型
    print("5. 保存模型...")
    model_path = transfer_learn.save_model("teacher_demo")
    print(f"   模型保存路径: {model_path}")

    # 6. 性能报告
    print("6. 生成性能报告...")
    report = transfer_learn.get_performance_report()
    print(f"   当前模型数量: {len(report['current_models'])}")

    print("\n=== 演示完成 ===")
    return transfer_learn


if __name__ == "__main__":
    demo_traditional_transfer_learning()
