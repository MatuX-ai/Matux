"""
ASSISTments数据集处理器
专门处理教育领域的行为数据，用于冷启动推荐系统
"""

import logging
import os
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder

from config.transfer_learning_config import settings

logger = logging.getLogger(__name__)


class AssistmentsDatasetProcessor:
    """ASSISTments数据集处理器"""

    def __init__(self, config=None):
        self.config = config or settings.dataset
        self.label_encoders = {}
        self.feature_extractors = {}

    def load_raw_data(self, source_path: str = None) -> pd.DataFrame:
        """
        加载原始ASSISTments数据
        支持多种数据源格式
        """
        if source_path is None:
            # 尝试多种可能的数据源路径
            possible_paths = [
                "./data/raw/assistments2012.csv",
                "./data/assistments_original.csv",
                self.config.processed_data_path.replace("processed", "raw").replace(
                    ".csv", "_raw.csv"
                ),
            ]

            for path in possible_paths:
                if os.path.exists(path):
                    source_path = path
                    break

        if source_path and os.path.exists(source_path):
            logger.info(f"从 {source_path} 加载原始数据")
            try:
                # 尝试不同的编码格式
                encodings = ["utf-8", "gbk", "latin-1"]
                df = None

                for encoding in encodings:
                    try:
                        df = pd.read_csv(source_path, encoding=encoding)
                        logger.info(f"使用 {encoding} 编码成功加载数据")
                        break
                    except UnicodeDecodeError:
                        continue

                if df is not None:
                    return self._validate_and_clean_raw_data(df)

            except Exception as e:
                logger.error(f"加载原始数据失败: {e}")

        # 如果无法加载真实数据，生成高质量的模拟数据
        logger.warning("无法加载真实数据，生成高质量模拟数据")
        return self._generate_high_quality_mock_data()

    def _validate_and_clean_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """验证和清理原始数据"""
        logger.info("开始数据验证和清理...")

        original_rows = len(df)

        # 1. 基本数据清洗
        # 删除完全空的行
        df = df.dropna(how="all")

        # 处理列名标准化
        df.columns = [col.lower().strip().replace(" ", "_") for col in df.columns]

        # 2. 必需字段检查和处理

        # 尝试映射可能的不同字段名
        field_mapping = {
            "student_id": ["user_id", "student", "user"],
            "problem_id": ["item_id", "question_id", "problem"],
            "correct": ["outcome", "is_correct", "result", "answer"],
        }

        for standard_field, alternatives in field_mapping.items():
            if standard_field not in df.columns:
                for alt_field in alternatives:
                    if alt_field in df.columns:
                        df[standard_field] = df[alt_field]
                        logger.info(f"字段映射: {alt_field} -> {standard_field}")
                        break

        # 3. 数据类型转换和验证
        if "student_id" in df.columns:
            df["student_id"] = pd.to_numeric(df["student_id"], errors="coerce")

        if "problem_id" in df.columns:
            df["problem_id"] = pd.to_numeric(df["problem_id"], errors="coerce")

        if "correct" in df.columns:
            # 处理不同的正确性表示方式
            if df["correct"].dtype == "object":
                # 处理字符串类型的正确性标记
                correct_mapping = {
                    "correct": 1,
                    "incorrect": 0,
                    "true": 1,
                    "false": 0,
                    "1": 1,
                    "0": 0,
                    "t": 1,
                    "f": 0,
                    "yes": 1,
                    "no": 0,
                }
                df["correct"] = df["correct"].str.lower().map(correct_mapping).fillna(0)
            else:
                df["correct"] = pd.to_numeric(df["correct"], errors="coerce").fillna(0)

            # 确保正确性值在[0,1]范围内
            df["correct"] = df["correct"].clip(0, 1)

        # 4. 时间戳处理
        timestamp_cols = [
            col for col in df.columns if "time" in col.lower() or "date" in col.lower()
        ]
        if timestamp_cols:
            df["timestamp"] = pd.to_datetime(df[timestamp_cols[0]], errors="coerce")
        else:
            # 如果没有时间戳，生成模拟时间序列
            df["timestamp"] = pd.date_range(
                start="2023-01-01", periods=len(df), freq="1min"
            )

        # 5. 删除无效记录
        df = df.dropna(subset=["student_id", "problem_id", "correct"])

        cleaned_rows = len(df)
        logger.info(
            f"数据清理完成: {original_rows} -> {cleaned_rows} 行 ({cleaned_rows/original_rows:.1%})"
        )

        return df

    def _generate_high_quality_mock_data(self) -> pd.DataFrame:
        """生成高质量的模拟ASSISTments数据"""
        logger.info("生成高质量模拟数据...")

        np.random.seed(42)  # 确保可重现性

        # 教育领域的典型参数
        n_students = 2000
        n_problems = 1000
        n_skills = 150
        avg_attempts_per_student = 50

        # 生成学生能力水平 (正态分布)
        student_ability = np.random.normal(0, 1, n_students)

        # 生成题目难度 (正态分布)
        problem_difficulty = np.random.normal(0, 1, n_problems)

        # 生成技能掌握度
        skill_proficiency = np.random.beta(2, 2, (n_students, n_skills))

        # 生成数据记录
        records = []

        for _ in range(n_students * avg_attempts_per_student):
            student_id = np.random.randint(0, n_students)
            problem_id = np.random.randint(0, n_problems)

            # 题目涉及的技能 (1-5个)
            n_problem_skills = np.random.randint(1, 6)
            problem_skills = np.random.choice(n_skills, n_problem_skills, replace=False)

            # 计算正确概率
            # 基础概率基于学生能力和题目难度
            base_prob = 1 / (
                1
                + np.exp(
                    -(student_ability[student_id] - problem_difficulty[problem_id])
                )
            )

            # 技能匹配加成
            skill_match_bonus = np.mean(skill_proficiency[student_id, problem_skills])

            # 综合正确概率
            correct_prob = np.clip(
                base_prob * (0.5 + 0.5 * skill_match_bonus), 0.1, 0.95
            )

            # 生成结果
            correct = int(np.random.random() < correct_prob)

            # 其他特征
            attempt_count = np.random.poisson(1.5) + 1
            time_spent = np.random.gamma(
                2, 15 * (2 - correct_prob)
            )  # 正确时花费更少时间

            records.append(
                {
                    "student_id": student_id,
                    "problem_id": problem_id,
                    "skill_ids": problem_skills.tolist(),
                    "correct": correct,
                    "attempt_count": attempt_count,
                    "time_spent": round(time_spent, 1),
                    "timestamp": pd.Timestamp("2023-01-01")
                    + pd.Timedelta(minutes=np.random.randint(0, 365 * 24 * 60)),
                    "hint_used": int(np.random.random() < 0.3),  # 30%使用提示
                    "review_mode": int(np.random.random() < 0.2),  # 20%复习模式
                }
            )

        df = pd.DataFrame(records)

        # 添加丰富的文本描述
        df = self._add_educational_descriptions(df, n_skills, n_problems)

        logger.info(f"生成 {len(df)} 条高质量模拟记录")
        return df

    def _add_educational_descriptions(
        self, df: pd.DataFrame, n_skills: int, n_problems: int
    ) -> pd.DataFrame:
        """为数据添加教育领域相关的文本描述"""

        # 生成技能描述
        math_topics = [
            "代数基础",
            "几何学",
            "三角函数",
            "微积分",
            "概率统计",
            "线性代数",
            "离散数学",
            "数论",
            "组合数学",
            "图论",
            "复数",
            "向量",
            "矩阵",
            "函数",
            "极限",
        ]

        skill_descriptions = []
        for i in range(n_skills):
            topic = math_topics[i % len(math_topics)]
            subtopic = f"知识点_{i//len(math_topics) + 1}"
            skill_descriptions.append(f"{topic}{subtopic}")

        # 为每条记录添加技能文本
        df["skill_text"] = df["skill_ids"].apply(
            lambda skills: " ".join([skill_descriptions[s] for s in skills])
        )

        # 生成题目类型描述
        problem_types = [
            "选择题",
            "填空题",
            "计算题",
            "证明题",
            "应用题",
            "概念理解",
            "公式推导",
            "图形分析",
            "数据分析",
            "综合题",
        ]

        # 为每个题目分配类型
        problem_type_mapping = {
            i: np.random.choice(problem_types) for i in range(n_problems)
        }

        df["problem_text"] = df["problem_id"].apply(
            lambda pid: f"{problem_type_mapping[pid]} - 题目编号{pid}"
        )

        # 添加学科领域
        subjects = ["数学", "物理", "化学", "生物", "计算机"]
        df["subject"] = df["problem_id"].apply(lambda pid: np.random.choice(subjects))

        return df

    def extract_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        特征工程：从原始数据中提取有用的特征
        """
        logger.info("开始特征工程...")

        features = {}

        # 1. 学生行为特征
        student_features = self._extract_student_features(df)
        features["student_behavior"] = student_features

        # 2. 题目特征
        problem_features = self._extract_problem_features(df)
        features["problem_characteristics"] = problem_features

        # 3. 交互特征
        interaction_features = self._extract_interaction_features(df)
        features["interaction_patterns"] = interaction_features

        # 4. 文本特征
        if "skill_text" in df.columns:
            text_features = self._extract_text_features(df)
            features["textual_features"] = text_features

        # 5. 时间特征
        temporal_features = self._extract_temporal_features(df)
        features["temporal_patterns"] = temporal_features

        logger.info(
            f"特征工程完成，共提取 {sum(len(v) for v in features.values())} 个特征"
        )
        return features

    def _extract_student_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取学生行为特征"""
        student_agg = (
            df.groupby("student_id")
            .agg(
                {
                    "correct": ["mean", "count", "std"],
                    "time_spent": ["mean", "std"],
                    "attempt_count": ["mean", "max"],
                    "hint_used": "sum",
                    "review_mode": "sum",
                }
            )
            .reset_index()
        )

        # 展平列名
        student_agg.columns = [
            "student_id",
            "accuracy_rate",
            "total_attempts",
            "accuracy_std",
            "avg_time_spent",
            "time_std",
            "avg_attempts",
            "max_attempts",
            "hints_used",
            "reviews_done",
        ]

        # 计算派生特征
        student_agg["learning_efficiency"] = (
            student_agg["accuracy_rate"]
            * student_agg["total_attempts"]
            / (student_agg["avg_time_spent"] + 1)
        )

        student_agg["hint_dependency"] = student_agg["hints_used"] / (
            student_agg["total_attempts"] + 1
        )

        return student_agg.fillna(0)

    def _extract_problem_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取题目特征"""
        problem_agg = (
            df.groupby("problem_id")
            .agg(
                {
                    "correct": ["mean", "count"],
                    "time_spent": "mean",
                    "attempt_count": "mean",
                    "student_id": "nunique",
                }
            )
            .reset_index()
        )

        problem_agg.columns = [
            "problem_id",
            "problem_difficulty",
            "attempts_count",
            "avg_solve_time",
            "avg_attempts_per_student",
            "unique_students",
        ]

        # 计算题目区分度
        problem_agg["discrimination_index"] = (
            1 - abs(problem_agg["problem_difficulty"] - 0.5) * 2
        )

        return problem_agg.fillna(0)

    def _extract_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取交互模式特征"""
        # 计算连续正确/错误序列
        df_sorted = df.sort_values(["student_id", "timestamp"])
        df_sorted["prev_correct"] = df_sorted.groupby("student_id")["correct"].shift(1)
        df_sorted["streak"] = (
            df_sorted["correct"] == df_sorted["prev_correct"]
        ).astype(int)

        interaction_features = (
            df_sorted.groupby(["student_id", "problem_id"])
            .agg({"streak": "sum", "hint_used": "any", "review_mode": "any"})
            .reset_index()
        )

        interaction_features.columns = [
            "student_id",
            "problem_id",
            "performance_streak",
            "used_hint",
            "in_review_mode",
        ]

        return interaction_features

    def _extract_text_features(self, df: pd.DataFrame) -> np.ndarray:
        """提取文本特征"""
        if "skill_text" not in df.columns:
            return np.random.rand(len(df), 100)  # 返回默认特征

        # TF-IDF向量化
        tfidf = TfidfVectorizer(
            max_features=500, ngram_range=(1, 2), min_df=2, stop_words=None
        )

        text_features = tfidf.fit_transform(df["skill_text"].fillna(""))
        self.feature_extractors["skill_tfidf"] = tfidf

        return text_features.toarray()

    def _extract_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """提取时间特征"""
        if "timestamp" not in df.columns:
            return pd.DataFrame({"hour": np.random.randint(0, 24, len(df))})

        temporal_df = pd.DataFrame(
            {
                "student_id": df["student_id"],
                "hour": df["timestamp"].dt.hour,
                "day_of_week": df["timestamp"].dt.dayofweek,
                "month": df["timestamp"].dt.month,
                "is_weekend": df["timestamp"].dt.dayofweek.isin([5, 6]).astype(int),
            }
        )

        # 聚合时间特征
        temporal_agg = (
            temporal_df.groupby("student_id")
            .agg(
                {
                    "hour": ["mean", "std"],
                    "day_of_week": "nunique",
                    "is_weekend": "mean",
                }
            )
            .reset_index()
        )

        temporal_agg.columns = [
            "student_id",
            "avg_study_hour",
            "hour_variability",
            "active_days",
            "weekend_ratio",
        ]

        return temporal_agg.fillna(0)

    def prepare_for_modeling(
        self, df: pd.DataFrame, features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        准备建模所需的数据格式
        """
        logger.info("准备建模数据...")

        # 合并所有特征
        modeling_data = df.copy()

        # 合并学生特征
        if "student_behavior" in features:
            modeling_data = modeling_data.merge(
                features["student_behavior"], on="student_id", how="left"
            )

        # 合并题目特征
        if "problem_characteristics" in features:
            modeling_data = modeling_data.merge(
                features["problem_characteristics"], on="problem_id", how="left"
            )

        # 合并交互特征
        if "interaction_patterns" in features:
            modeling_data = modeling_data.merge(
                features["interaction_patterns"],
                on=["student_id", "problem_id"],
                how="left",
            )

        # 处理缺失值
        numeric_columns = modeling_data.select_dtypes(include=[np.number]).columns
        modeling_data[numeric_columns] = modeling_data[numeric_columns].fillna(0)

        # 编码分类变量
        categorical_columns = ["subject"] if "subject" in modeling_data.columns else []
        for col in categorical_columns:
            if col in modeling_data.columns:
                le = LabelEncoder()
                modeling_data[col] = le.fit_transform(modeling_data[col].astype(str))
                self.label_encoders[col] = le

        logger.info(f"建模数据准备完成，形状: {modeling_data.shape}")
        return {
            "processed_dataframe": modeling_data,
            "feature_names": modeling_data.columns.tolist(),
            "target_column": "correct",
        }

    def save_processed_data(self, data: pd.DataFrame, filepath: str = None) -> str:
        """保存处理后的数据"""
        if filepath is None:
            filepath = self.config.processed_data_path

        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        data.to_csv(filepath, index=False, encoding="utf-8")
        logger.info(f"处理后的数据已保存到: {filepath}")
        return filepath

    def load_processed_data(self, filepath: str = None) -> pd.DataFrame:
        """加载已处理的数据"""
        if filepath is None:
            filepath = self.config.processed_data_path

        if os.path.exists(filepath):
            return pd.read_csv(filepath)
        else:
            raise FileNotFoundError(f"处理后的数据文件不存在: {filepath}")


# 测试函数
def test_assistments_processor():
    """测试ASSISTments数据处理器"""
    print("=== ASSISTments数据处理器测试 ===")

    processor = AssistmentsDatasetProcessor()

    # 1. 加载数据
    print("1. 加载数据...")
    raw_data = processor.load_raw_data()
    print(f"   原始数据形状: {raw_data.shape}")

    # 2. 特征工程
    print("2. 特征工程...")
    features = processor.extract_features(raw_data)
    print(f"   提取特征组数: {len(features)}")

    # 3. 准备建模数据
    print("3. 准备建模数据...")
    modeling_ready = processor.prepare_for_modeling(raw_data, features)
    print(f"   建模数据形状: {modeling_ready['processed_dataframe'].shape}")

    # 4. 保存数据
    print("4. 保存处理后数据...")
    save_path = processor.save_processed_data(modeling_ready["processed_dataframe"])
    print(f"   保存路径: {save_path}")

    print("\n=== 测试完成 ===")
    return processor


if __name__ == "__main__":
    test_assistments_processor()
