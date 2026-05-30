"""
迁移学习引擎
实现基于传统机器学习的知识迁移和模型优化
支持教师-学生模型范式和渐进式学习
"""

from datetime import datetime
import logging
import os
from typing import Any, Callable, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import cross_val_score, train_test_split

from ai_service.traditional_ml_transfer import TraditionalTransferLearning
from config.transfer_learning_config import settings
from services.dataset_processor import AssistmentsDatasetProcessor

logger = logging.getLogger(__name__)


class TransferLearningEngine:
    """迁移学习引擎主类"""

    def __init__(self, config=None):
        self.config = config or settings
        self.teacher_models = {}
        self.student_models = {}
        self.knowledge_transfer_history = []
        self.evaluation_metrics = {}

    def initialize_source_domain(self, source_data: pd.DataFrame) -> Dict[str, Any]:
        """
        初始化源域（ASSISTments数据）
        训练教师模型并提取知识
        """
        logger.info("初始化源域知识迁移...")

        # 使用传统ML方法训练教师模型
        traditional_ml = TraditionalTransferLearning(self.config)

        # 预处理数据
        processed_data = traditional_ml.preprocess_data(source_data)

        # 训练教师模型
        teacher_result = traditional_ml.train_teacher_model(processed_data)

        # 保存教师模型
        self.teacher_models["source_domain"] = {
            "model": teacher_result["model"],
            "features": processed_data["features"],
            "performance": teacher_result["performance"],
            "feature_importance": teacher_result["feature_importance"],
        }

        logger.info(
            f"源域教师模型训练完成，最佳准确率: {max(score['accuracy'] for score in teacher_result['performance'].values()):.4f}"
        )

        return {
            "teacher_model": teacher_result["model"],
            "knowledge_base": processed_data["features"],
            "source_performance": teacher_result["performance"],
        }

    def adapt_to_target_domain(
        self, target_data: pd.DataFrame, adaptation_strategy: str = "fine_tune"
    ) -> Dict[str, Any]:
        """
        适配目标域（推荐系统场景）
        实现知识迁移和模型适配
        """
        logger.info(f"开始目标域适配，策略: {adaptation_strategy}")

        if "source_domain" not in self.teacher_models:
            raise ValueError("请先初始化源域知识")

        # 根据适配策略选择不同的方法
        if adaptation_strategy == "fine_tune":
            return self._fine_tune_approach(target_data)
        elif adaptation_strategy == "feature_mapping":
            return self._feature_mapping_approach(target_data)
        elif adaptation_strategy == "ensemble_transfer":
            return self._ensemble_transfer_approach(target_data)
        else:
            raise ValueError(f"未知的适配策略: {adaptation_strategy}")

    def _fine_tune_approach(self, target_data: pd.DataFrame) -> Dict[str, Any]:
        """微调适配方法"""
        logger.info("使用微调适配方法...")

        # 获取源域教师模型
        source_teacher = self.teacher_models["source_domain"]["model"]
        source_features = self.teacher_models["source_domain"]["features"]

        # 目标域数据预处理（保持特征一致性）
        target_processor = AssistmentsDatasetProcessor(self.config.dataset)
        target_features = target_processor.extract_features(target_data)
        target_modeling_data = target_processor.prepare_for_modeling(
            target_data, target_features
        )

        # 特征对齐 - 使用源域的特征提取器
        aligned_features = self._align_features(
            target_modeling_data["processed_dataframe"], source_features
        )

        # 微调模型
        fine_tuned_model = self._perform_fine_tuning(
            source_teacher,
            aligned_features,
            target_modeling_data["processed_dataframe"]["correct"],
        )

        # 评估微调效果
        evaluation = self._evaluate_model_performance(
            fine_tuned_model,
            aligned_features,
            target_modeling_data["processed_dataframe"]["correct"],
        )

        self.student_models["fine_tuned"] = {
            "model": fine_tuned_model,
            "adaptation_method": "fine_tune",
            "evaluation": evaluation,
        }

        return {
            "adapted_model": fine_tuned_model,
            "evaluation": evaluation,
            "adaptation_type": "fine_tuning",
        }

    def _feature_mapping_approach(self, target_data: pd.DataFrame) -> Dict[str, Any]:
        """特征映射适配方法"""
        logger.info("使用特征映射适配方法...")

        # 分析源域和目标域的特征空间差异
        source_features_info = self._analyze_feature_space(
            self.teacher_models["source_domain"]["features"]
        )

        target_processor = AssistmentsDatasetProcessor(self.config.dataset)
        target_features = target_processor.extract_features(target_data)
        target_features_info = self._analyze_feature_space(target_features)

        # 构建特征映射函数
        feature_mapper = self._build_feature_mapper(
            source_features_info, target_features_info
        )

        # 训练新的学生模型
        student_model = self._train_student_model_with_mapping(
            target_data, feature_mapper
        )

        # 评估映射效果
        evaluation = self._evaluate_mapping_performance(student_model, target_data)

        self.student_models["feature_mapped"] = {
            "model": student_model,
            "mapper": feature_mapper,
            "adaptation_method": "feature_mapping",
            "evaluation": evaluation,
        }

        return {
            "adapted_model": student_model,
            "feature_mapper": feature_mapper,
            "evaluation": evaluation,
            "adaptation_type": "feature_mapping",
        }

    def _ensemble_transfer_approach(self, target_data: pd.DataFrame) -> Dict[str, Any]:
        """集成迁移方法"""
        logger.info("使用集成迁移方法...")

        # 训练多个不同的学生模型
        ensemble_models = []

        # 方法1: 直接迁移
        direct_model = self._direct_transfer_model(target_data)
        ensemble_models.append(("direct_transfer", direct_model))

        # 方法2: 特征增强
        enhanced_model = self._feature_enhanced_model(target_data)
        ensemble_models.append(("feature_enhanced", enhanced_model))

        # 方法3: 知识蒸馏
        distilled_model = self._knowledge_distillation_model(target_data)
        ensemble_models.append(("knowledge_distilled", distilled_model))

        # 集成预测
        ensemble_predictor = self._create_ensemble_predictor(ensemble_models)

        # 评估集成效果
        evaluation = self._evaluate_ensemble_performance(
            ensemble_predictor, target_data
        )

        self.student_models["ensemble"] = {
            "models": ensemble_models,
            "ensemble_predictor": ensemble_predictor,
            "adaptation_method": "ensemble_transfer",
            "evaluation": evaluation,
        }

        return {
            "adapted_model": ensemble_predictor,
            "component_models": ensemble_models,
            "evaluation": evaluation,
            "adaptation_type": "ensemble_transfer",
        }

    def _align_features(
        self, target_df: pd.DataFrame, source_features: Dict
    ) -> np.ndarray:
        """特征对齐：将目标域特征转换为源域特征格式"""
        # 这里实现具体的特征对齐逻辑
        # 简化实现：使用通用特征提取
        feature_columns = [
            col
            for col in target_df.columns
            if col not in ["student_id", "problem_id", "correct", "timestamp"]
        ]

        return target_df[feature_columns].fillna(0).values

    def _perform_fine_tuning(
        self, base_model, features: np.ndarray, targets: np.ndarray
    ) -> Any:
        """执行模型微调"""
        # 简化实现：重新训练相似架构的模型
        from sklearn.ensemble import RandomForestClassifier

        # 划分训练验证集
        X_train, X_val, y_train, y_val = train_test_split(
            features,
            targets,
            test_size=0.2,
            random_state=self.config.dataset.random_seed,
        )

        # 微调模型
        fine_tuned = RandomForestClassifier(
            n_estimators=50,  # 减少树的数量以加快训练
            max_depth=8,
            random_state=self.config.dataset.random_seed,
        )

        fine_tuned.fit(X_train, y_train)
        return fine_tuned

    def _evaluate_model_performance(
        self, model, features: np.ndarray, targets: np.ndarray
    ) -> Dict[str, float]:
        """评估模型性能"""
        predictions = model.predict(features)

        metrics = {
            "accuracy": np.mean(predictions == targets),
            "mse": mean_squared_error(targets, predictions),
            "mae": mean_absolute_error(targets, predictions),
        }

        # 交叉验证
        try:
            cv_scores = cross_val_score(model, features, targets, cv=3)
            metrics["cv_mean"] = cv_scores.mean()
            metrics["cv_std"] = cv_scores.std()
        except (ValueError, TypeError, RuntimeError):
            metrics["cv_mean"] = metrics["accuracy"]
            metrics["cv_std"] = 0.0

        return metrics

    def _analyze_feature_space(self, features: Dict) -> Dict[str, Any]:
        """分析特征空间结构"""
        analysis = {
            "feature_types": {},
            "dimensionality": {},
            "statistical_properties": {},
        }

        for feature_group, feature_data in features.items():
            if hasattr(feature_data, "shape"):
                analysis["dimensionality"][feature_group] = feature_data.shape
            elif isinstance(feature_data, list):
                analysis["dimensionality"][feature_group] = len(feature_data)

            # 简化的统计分析
            analysis["statistical_properties"][feature_group] = {
                "mean": 0.5,  # 简化假设
                "std": 0.3,
                "sparsity": 0.1,
            }

        return analysis

    def _build_feature_mapper(self, source_info: Dict, target_info: Dict) -> Callable:
        """构建特征映射函数"""

        def feature_mapper(target_features):
            # 简化的线性映射
            # 实际应用中需要更复杂的映射逻辑
            return target_features * 0.8 + 0.1  # 归一化映射

        return feature_mapper

    def _train_student_model_with_mapping(
        self, target_data: pd.DataFrame, feature_mapper: Callable
    ) -> Any:
        """使用特征映射训练学生模型"""
        # 简化实现
        from sklearn.linear_model import LogisticRegression

        # 提取和映射特征
        processor = AssistmentsDatasetProcessor(self.config.dataset)
        features = processor.extract_features(target_data)
        modeling_data = processor.prepare_for_modeling(target_data, features)

        X = (
            modeling_data["processed_dataframe"]
            .select_dtypes(include=[np.number])
            .fillna(0)
            .values
        )
        y = modeling_data["processed_dataframe"]["correct"].values

        # 应用特征映射
        X_mapped = feature_mapper(X)

        # 训练学生模型
        student_model = LogisticRegression(random_state=self.config.dataset.random_seed)
        student_model.fit(X_mapped, y)

        return student_model

    def _evaluate_mapping_performance(
        self, model, target_data: pd.DataFrame
    ) -> Dict[str, float]:
        """评估特征映射性能"""
        processor = AssistmentsDatasetProcessor(self.config.dataset)
        features = processor.extract_features(target_data)
        modeling_data = processor.prepare_for_modeling(target_data, features)

        X = (
            modeling_data["processed_dataframe"]
            .select_dtypes(include=[np.number])
            .fillna(0)
            .values
        )
        y = modeling_data["processed_dataframe"]["correct"].values

        return self._evaluate_model_performance(model, X, y)

    def _direct_transfer_model(self, target_data: pd.DataFrame) -> Any:
        """直接迁移模型"""
        # 使用源域模型直接在目标域上预测
        source_model = self.teacher_models["source_domain"]["model"]
        return source_model

    def _feature_enhanced_model(self, target_data: pd.DataFrame) -> Any:
        """特征增强模型"""
        from sklearn.ensemble import GradientBoostingClassifier

        processor = AssistmentsDatasetProcessor(self.config.dataset)
        features = processor.extract_features(target_data)
        modeling_data = processor.prepare_for_modeling(target_data, features)

        X = (
            modeling_data["processed_dataframe"]
            .select_dtypes(include=[np.number])
            .fillna(0)
            .values
        )
        y = modeling_data["processed_dataframe"]["correct"].values

        # 增强模型
        enhanced_model = GradientBoostingClassifier(
            n_estimators=100, max_depth=6, random_state=self.config.dataset.random_seed
        )
        enhanced_model.fit(X, y)

        return enhanced_model

    def _knowledge_distillation_model(self, target_data: pd.DataFrame) -> Any:
        """知识蒸馏模型"""
        # 使用软标签进行训练
        source_model = self.teacher_models["source_domain"]["model"]

        processor = AssistmentsDatasetProcessor(self.config.dataset)
        features = processor.extract_features(target_data)
        modeling_data = processor.prepare_for_modeling(target_data, features)

        X = (
            modeling_data["processed_dataframe"]
            .select_dtypes(include=[np.number])
            .fillna(0)
            .values
        )
        y = modeling_data["processed_dataframe"]["correct"].values

        # 获取教师模型的软预测
        soft_labels = source_model.predict_proba(X)[:, 1]  # 正类概率

        # 结合硬标签和软标签训练学生模型
        from sklearn.ensemble import RandomForestClassifier

        student_model = RandomForestClassifier(
            n_estimators=100, random_state=self.config.dataset.random_seed
        )

        # 使用加权组合进行训练
        combined_targets = 0.7 * y + 0.3 * (soft_labels > 0.5).astype(int)
        student_model.fit(X, combined_targets)

        return student_model

    def _create_ensemble_predictor(self, models: List[Tuple[str, Any]]) -> Callable:
        """创建集成预测器"""

        def ensemble_predict(X):
            predictions = []
            for model_name, model in models:
                if hasattr(model, "predict_proba"):
                    pred_proba = model.predict_proba(X)[:, 1]
                    predictions.append(pred_proba)
                else:
                    pred = model.predict(X)
                    predictions.append(pred)

            # 简单平均集成
            ensemble_pred = np.mean(predictions, axis=0)
            return (ensemble_pred > 0.5).astype(int)

        return ensemble_predict

    def _evaluate_ensemble_performance(
        self, ensemble_predictor: Callable, target_data: pd.DataFrame
    ) -> Dict[str, float]:
        """评估集成模型性能"""
        processor = AssistmentsDatasetProcessor(self.config.dataset)
        features = processor.extract_features(target_data)
        modeling_data = processor.prepare_for_modeling(target_data, features)

        X = (
            modeling_data["processed_dataframe"]
            .select_dtypes(include=[np.number])
            .fillna(0)
            .values
        )
        y = modeling_data["processed_dataframe"]["correct"].values

        predictions = ensemble_predictor(X)

        return {
            "accuracy": np.mean(predictions == y),
            "ensemble_diversity": len(
                self.student_models.get("ensemble", {}).get("models", [])
            ),
        }

    def generate_recommendations(
        self, user_features: np.ndarray, model_name: str = "ensemble"
    ) -> List[Dict[str, Any]]:
        """
        基于迁移学习模型生成推荐
        """
        if model_name not in self.student_models:
            raise ValueError(f"模型 {model_name} 不存在")

        model_info = self.student_models[model_name]
        adapted_model = model_info["model"]

        # 生成预测
        if callable(adapted_model):
            # 集成模型情况
            predictions = adapted_model(user_features)
        else:
            # 普通模型情况
            predictions = adapted_model.predict(user_features)

        # 转换为推荐格式
        recommendations = []
        for i, pred in enumerate(predictions):
            recommendations.append(
                {
                    "item_id": f"course_{i}",
                    "confidence": (
                        float(pred) if isinstance(pred, (int, float)) else 0.5
                    ),
                    "reasoning": f'基于迁移学习模型预测，适配方法: {model_info["adaptation_method"]}',
                }
            )

        return recommendations

    def get_transfer_performance_report(self) -> Dict[str, Any]:
        """获取迁移学习性能报告"""
        report = {
            "transfer_history": self.knowledge_transfer_history,
            "model_evaluations": {},
            "best_performing_approach": None,
        }

        # 收集各模型评估结果
        best_accuracy = 0
        best_approach = None

        for model_name, model_info in self.student_models.items():
            report["model_evaluations"][model_name] = model_info.get("evaluation", {})

            if "evaluation" in model_info and "accuracy" in model_info["evaluation"]:
                accuracy = model_info["evaluation"]["accuracy"]
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_approach = model_name

        report["best_performing_approach"] = best_approach
        report["timestamp"] = datetime.now().isoformat()

        return report

    def save_transfer_knowledge(self, save_path: str = None) -> str:
        """保存迁移学习知识"""
        if save_path is None:
            save_path = os.path.join(
                self.config.model.model_save_path,
                f"transfer_knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl",
            )

        knowledge_package = {
            "teacher_models": self.teacher_models,
            "student_models": self.student_models,
            "transfer_history": self.knowledge_transfer_history,
            "config": self.config.__dict__,
            "timestamp": datetime.now().isoformat(),
        }

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        joblib.dump(knowledge_package, save_path)
        logger.info(f"迁移学习知识已保存到: {save_path}")

        return save_path

    def load_transfer_knowledge(self, load_path: str) -> bool:
        """加载迁移学习知识"""
        try:
            knowledge_package = joblib.load(load_path)

            self.teacher_models = knowledge_package.get("teacher_models", {})
            self.student_models = knowledge_package.get("student_models", {})
            self.knowledge_transfer_history = knowledge_package.get(
                "transfer_history", []
            )

            logger.info(f"迁移学习知识已从 {load_path} 加载")
            return True
        except Exception as e:
            logger.error(f"加载迁移学习知识失败: {e}")
            return False


# 测试和演示函数
def demo_transfer_learning_engine():
    """演示迁移学习引擎"""
    print("=== 迁移学习引擎演示 ===")

    # 初始化引擎
    engine = TransferLearningEngine()

    # 1. 模拟源域数据（ASSISTments）
    print("1. 初始化源域知识...")
    source_processor = AssistmentsDatasetProcessor()
    source_data = source_processor.load_raw_data()
    source_result = engine.initialize_source_domain(source_data)
    print(
        f"   源域教师模型准确率: {max(score['accuracy'] for score in source_result['source_performance'].values()):.4f}"
    )

    # 2. 模拟目标域数据（推荐系统）
    print("2. 适配目标域...")
    target_data = source_data.sample(n=1000, random_state=42)  # 使用部分数据作为目标域
    adaptation_result = engine.adapt_to_target_domain(target_data, "ensemble_transfer")
    print(f"   目标域适配准确率: {adaptation_result['evaluation']['accuracy']:.4f}")

    # 3. 生成推荐示例
    print("3. 生成推荐...")
    sample_features = np.random.rand(5, 20)  # 模拟用户特征
    recommendations = engine.generate_recommendations(sample_features)
    print(f"   生成 {len(recommendations)} 条推荐")

    # 4. 性能报告
    print("4. 生成性能报告...")
    performance_report = engine.get_transfer_performance_report()
    print(f"   最佳适配方法: {performance_report['best_performing_approach']}")

    # 5. 保存知识
    print("5. 保存迁移知识...")
    save_path = engine.save_transfer_knowledge()
    print(f"   知识保存路径: {save_path}")

    print("\n=== 演示完成 ===")
    return engine


if __name__ == "__main__":
    demo_transfer_learning_engine()
