"""
教育局数据接口协议和标准化处理
定义教育数据的标准格式、转换规则和验证机制
"""

from enum import Enum
import logging
from typing import Any, Dict, List, Union

import pandas as pd

from ..models.edu_data_models import EduAssessmentType, EduSubject
from ..utils.data_quality import DataQualityChecker

logger = logging.getLogger(__name__)


class DataFormat(Enum):
    """支持的数据格式"""

    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"
    XML = "xml"


class EduDataStandardizer:
    """教育数据标准化处理器"""

    def __init__(self):
        self.quality_checker = DataQualityChecker()
        self.standard_fields = {
            "student": [
                "student_id",
                "name",
                "age",
                "gender",
                "grade_level",
                "school_id",
                "region_id",
                "enrollment_date",
            ],
            "academic": [
                "student_id",
                "subject",
                "assessment_type",
                "score",
                "date_taken",
                "academic_year",
                "percentile_rank",
            ],
            "school": [
                "school_id",
                "school_name",
                "school_type",
                "district_id",
                "region_id",
                "enrollment",
                "teachers_count",
                "established_year",
            ],
        }

    def standardize_data(
        self, raw_data: Union[pd.DataFrame, List[Dict]], data_type: str
    ) -> pd.DataFrame:
        """
        标准化教育数据

        Args:
            raw_data: 原始数据
            data_type: 数据类型 ('student', 'academic', 'school')

        Returns:
            标准化后的DataFrame
        """
        try:
            # 转换为DataFrame
            if isinstance(raw_data, list):
                df = pd.DataFrame(raw_data)
            else:
                df = raw_data.copy()

            # 应用标准化转换
            standardized_df = self._apply_standardization(df, data_type)

            # 验证数据质量
            quality_report = self.quality_checker.check_dataframe_quality(
                standardized_df
            )
            if not quality_report.is_valid:
                logger.warning(f"数据质量检查发现问题: {quality_report.issues}")

            logger.info(
                f"数据标准化完成 - 类型: {data_type}, 记录数: {len(standardized_df)}"
            )
            return standardized_df

        except Exception as e:
            logger.error(f"数据标准化失败: {e}")
            raise

    def _apply_standardization(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """应用具体的标准化规则"""
        if data_type == "student":
            return self._standardize_student_data(df)
        elif data_type == "academic":
            return self._standardize_academic_data(df)
        elif data_type == "school":
            return self._standardize_school_data(df)
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")

    def _standardize_student_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化学生数据"""
        # 字段映射
        field_mapping = {
            "学号": "student_id",
            "学生ID": "student_id",
            "姓名": "name",
            "学生姓名": "name",
            "年龄": "age",
            "性别": "gender",
            "年级": "grade_level",
            "年级级别": "grade_level",
            "学校ID": "school_id",
            "学校编码": "school_id",
            "区域ID": "region_id",
            "入学日期": "enrollment_date",
        }

        # 应用字段映射
        df = df.rename(columns=field_mapping)

        # 标准化年级级别
        if "grade_level" in df.columns:
            df["grade_level"] = df["grade_level"].apply(self._normalize_grade_level)

        # 标准化性别
        if "gender" in df.columns:
            df["gender"] = df["gender"].apply(self._normalize_gender)

        # 验证必填字段
        required_fields = ["student_id", "name"]
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            raise ValueError(f"缺少必填字段: {missing_fields}")

        return df

    def _standardize_academic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化学术数据"""
        # 字段映射
        field_mapping = {
            "学号": "student_id",
            "学生ID": "student_id",
            "学科": "subject",
            "科目": "subject",
            "评估类型": "assessment_type",
            "考试类型": "assessment_type",
            "分数": "score",
            "成绩": "score",
            "考试日期": "date_taken",
            "学年": "academic_year",
            "百分位排名": "percentile_rank",
        }

        # 应用字段映射
        df = df.rename(columns=field_mapping)

        # 标准化学科名称
        if "subject" in df.columns:
            df["subject"] = df["subject"].apply(self._normalize_subject)

        # 标准化评估类型
        if "assessment_type" in df.columns:
            df["assessment_type"] = df["assessment_type"].apply(
                self._normalize_assessment_type
            )

        # 验证分数范围
        if "score" in df.columns:
            df["score"] = pd.to_numeric(df["score"], errors="coerce")
            invalid_scores = df[(df["score"] < 0) | (df["score"] > 100)]
            if len(invalid_scores) > 0:
                logger.warning(f"发现 {len(invalid_scores)} 个无效分数")
                df.loc[(df["score"] < 0) | (df["score"] > 100), "score"] = None

        # 验证必填字段
        required_fields = ["student_id", "subject", "score"]
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            raise ValueError(f"缺少必填字段: {missing_fields}")

        return df

    def _standardize_school_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化学校数据"""
        # 字段映射
        field_mapping = {
            "学校ID": "school_id",
            "学校编码": "school_id",
            "学校名称": "school_name",
            "学校类型": "school_type",
            "学区ID": "district_id",
            "区域ID": "region_id",
            "在校生数": "enrollment",
            "学生人数": "enrollment",
            "教师数": "teachers_count",
            "建校年份": "established_year",
        }

        # 应用字段映射
        df = df.rename(columns=field_mapping)

        # 验证数值字段
        numeric_fields = ["enrollment", "teachers_count", "established_year"]
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors="coerce")

        # 验证必填字段
        required_fields = ["school_id", "school_name"]
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            raise ValueError(f"缺少必填字段: {missing_fields}")

        return df

    def _normalize_grade_level(self, grade_level: Any) -> str:
        """标准化年级级别"""
        if pd.isna(grade_level):
            return "unknown"

        grade_str = str(grade_level).lower().strip()

        # 映射各种年级表示法
        grade_mappings = {
            "小学": "elementary",
            "初中": "middle",
            "高中": "high",
            "大学": "university",
            "1-6年级": "elementary",
            "7-9年级": "middle",
            "10-12年级": "high",
            "primary": "elementary",
            "junior_high": "middle",
            "senior_high": "high",
        }

        for key, value in grade_mappings.items():
            if key in grade_str:
                return value

        return grade_str

    def _normalize_subject(self, subject: Any) -> str:
        """标准化学科名称"""
        if pd.isna(subject):
            return "unknown"

        subject_str = str(subject).lower().strip()

        subject_mappings = {
            "数学": "math",
            "语文": "language",
            "英语": "language",
            "物理": "science",
            "化学": "science",
            "生物": "science",
            "科学": "science",
            "技术": "technology",
            "工程": "engineering",
            "艺术": "arts",
            "体育": "physical_education",
            "社会": "social_studies",
        }

        for key, value in subject_mappings.items():
            if key in subject_str:
                return value

        return subject_str

    def _normalize_gender(self, gender: Any) -> str:
        """标准化性别"""
        if pd.isna(gender):
            return "unknown"

        gender_str = str(gender).lower().strip()

        if gender_str in ["男", "male", "m", "boy"]:
            return "male"
        elif gender_str in ["女", "female", "f", "girl"]:
            return "female"
        else:
            return "other"

    def _normalize_assessment_type(self, assessment_type: Any) -> str:
        """标准化评估类型"""
        if pd.isna(assessment_type):
            return "standardized_test"

        type_str = str(assessment_type).lower().strip()

        type_mappings = {
            "期末考试": "summative_assessment",
            "期中考试": "formative_assessment",
            "月考": "formative_assessment",
            "单元测试": "formative_assessment",
            "标准化测试": "standardized_test",
            "performance": "performance_task",
        }

        for key, value in type_mappings.items():
            if key in type_str:
                return value

        return "standardized_test"


class EduDataProtocol:
    """教育数据接口协议"""

    @staticmethod
    def validate_data_structure(data: Dict[str, Any], data_type: str) -> bool:
        """
        验证数据结构是否符合协议要求

        Args:
            data: 待验证的数据
            data_type: 数据类型

        Returns:
            是否符合协议
        """
        try:
            if data_type == "student":
                return EduDataProtocol._validate_student_structure(data)
            elif data_type == "academic":
                return EduDataProtocol._validate_academic_structure(data)
            elif data_type == "school":
                return EduDataProtocol._validate_school_structure(data)
            else:
                return False

        except Exception as e:
            logger.error(f"数据结构验证失败: {e}")
            return False

    @staticmethod
    def _validate_student_structure(data: Dict[str, Any]) -> bool:
        """验证学生数据结构"""
        required_fields = ["student_id", "name"]

        # 检查必填字段
        for field in required_fields:
            if field not in data or pd.isna(data[field]):
                return False

        # 验证字段类型和范围
        if "age" in data and not pd.isna(data["age"]):
            try:
                age = int(data["age"])
                if age < 0 or age > 100:
                    return False
            except (ValueError, TypeError):
                return False

        if "grade_level" in data and not pd.isna(data["grade_level"]):
            if str(data["grade_level"]).lower() not in [
                "elementary",
                "middle",
                "high",
                "university",
            ]:
                return False

        return True

    @staticmethod
    def _validate_academic_structure(data: Dict[str, Any]) -> bool:
        """验证学术数据结构"""
        required_fields = ["student_id", "subject", "score"]

        # 检查必填字段
        for field in required_fields:
            if field not in data or pd.isna(data[field]):
                return False

        # 验证分数范围
        try:
            score = float(data["score"])
            if score < 0 or score > 100:
                return False
        except (ValueError, TypeError):
            return False

        # 验证学科
        if str(data["subject"]).lower() not in [s.value for s in EduSubject]:
            return False

        return True

    @staticmethod
    def _validate_school_structure(data: Dict[str, Any]) -> bool:
        """验证学校数据结构"""
        required_fields = ["school_id", "school_name"]

        # 检查必填字段
        for field in required_fields:
            if field not in data or pd.isna(data[field]):
                return False

        # 验证数值字段
        numeric_fields = ["enrollment", "teachers_count"]
        for field in numeric_fields:
            if field in data and not pd.isna(data[field]):
                try:
                    value = int(data[field])
                    if value < 0:
                        return False
                except (ValueError, TypeError):
                    return False

        return True

    @staticmethod
    def generate_data_schema(data_type: str) -> Dict[str, Any]:
        """生成数据模式定义"""
        schemas = {
            "student": {
                "type": "object",
                "required": ["student_id", "name"],
                "properties": {
                    "student_id": {"type": "string"},
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0, "maximum": 100},
                    "gender": {"type": "string", "enum": ["male", "female", "other"]},
                    "grade_level": {
                        "type": "string",
                        "enum": ["elementary", "middle", "high", "university"],
                    },
                    "school_id": {"type": "string"},
                    "region_id": {"type": "string"},
                },
            },
            "academic": {
                "type": "object",
                "required": ["student_id", "subject", "score"],
                "properties": {
                    "student_id": {"type": "string"},
                    "subject": {
                        "type": "string",
                        "enum": [s.value for s in EduSubject],
                    },
                    "score": {"type": "number", "minimum": 0, "maximum": 100},
                    "assessment_type": {
                        "type": "string",
                        "enum": [t.value for t in EduAssessmentType],
                    },
                    "date_taken": {"type": "string", "format": "date-time"},
                },
            },
            "school": {
                "type": "object",
                "required": ["school_id", "school_name"],
                "properties": {
                    "school_id": {"type": "string"},
                    "school_name": {"type": "string"},
                    "school_type": {"type": "string"},
                    "district_id": {"type": "string"},
                    "region_id": {"type": "string"},
                    "enrollment": {"type": "integer", "minimum": 0},
                    "teachers_count": {"type": "integer", "minimum": 0},
                },
            },
        }

        return schemas.get(data_type, {})


class EduDataConverter:
    """教育数据格式转换器"""

    @staticmethod
    def convert_to_json(data: pd.DataFrame, output_path: str = None) -> str:
        """转换为JSON格式"""
        json_data = data.to_json(orient="records", date_format="iso", force_ascii=False)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_data)

        return json_data

    @staticmethod
    def convert_to_csv(data: pd.DataFrame, output_path: str = None) -> str:
        """转换为CSV格式"""
        csv_data = data.to_csv(index=False, encoding="utf-8")

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(csv_data)

        return csv_data

    @staticmethod
    def convert_to_excel(data: pd.DataFrame, output_path: str) -> str:
        """转换为Excel格式"""
        data.to_excel(output_path, index=False, engine="openpyxl")
        return output_path


# 全局实例
data_standardizer = EduDataStandardizer()
data_protocol = EduDataProtocol()
data_converter = EduDataConverter()


if __name__ == "__main__":
    # 测试数据标准化
    test_data = pd.DataFrame(
        {
            "学号": ["S001", "S002", "S003"],
            "姓名": ["张三", "李四", "王五"],
            "年级": ["小学", "初中", "高中"],
            "数学": [85, 92, 78],
            "语文": [88, 85, 90],
        }
    )

    print("原始数据:")
    print(test_data.head())

    # 标准化数据
    try:
        standardized_data = data_standardizer.standardize_data(test_data, "student")
        print("\n标准化后数据:")
        print(standardized_data.head())

        # 验证数据结构
        sample_record = standardized_data.iloc[0].to_dict()
        is_valid = data_protocol.validate_data_structure(sample_record, "student")
        print(f"\n数据结构验证: {'通过' if is_valid else '失败'}")

    except Exception as e:
        print(f"测试失败: {e}")
