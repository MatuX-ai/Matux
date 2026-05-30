"""
硬件认证服务层
负责认证验证逻辑、测试结果分析和认证决策
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid

from models.hardware_certification import (
    CertificationRequest,
    CertificationResponse,
    CertificationStatus,
    TestCategory,
    TestResult,
)
from utils.logger import setup_logger

logger = setup_logger("INFO")


class HardwareCertificationService:
    """硬件认证服务类"""

    def __init__(self):
        # 简化的内存存储（实际项目中应使用数据库）
        self._certifications = {}
        self._min_pass_rate = 0.8  # 最低通过率要求 (80%)
        self._required_categories = [
            TestCategory.FUNCTIONALITY,
            TestCategory.PERFORMANCE,
            TestCategory.COMPATIBILITY,
        ]

    def verify_certification(
        self, request: CertificationRequest
    ) -> CertificationResponse:
        """
        验证硬件认证

        Args:
            request: 认证请求

        Returns:
            CertificationResponse: 认证响应
        """
        try:
            logger.info(f"开始验证硬件认证: {request.hw_id}")

            # 分析测试结果
            analysis_result = self._analyze_test_results(request.test_results)

            # 判断认证状态
            certification_status = self._determine_certification_status(
                analysis_result, request.test_results
            )

            # 生成证书ID（如果是通过认证）
            certificate_id = None
            certified_at = None
            expires_at = None
            badge_url = None

            if certification_status == CertificationStatus.CERTIFIED:
                certificate_id = str(uuid.uuid4())
                certified_at = datetime.utcnow()
                expires_at = certified_at + timedelta(days=365)  # 一年有效期
                badge_url = f"https://badges.imatuproject.org/cert/{request.hw_id}.svg"

                # 保存认证记录
                self._save_certification_record(
                    request,
                    certification_status,
                    certificate_id,
                    certified_at,
                    expires_at,
                )

            response = CertificationResponse(
                hw_id=request.hw_id,
                status=certification_status,
                badge_url=badge_url,
                certified_at=certified_at,
                expires_at=expires_at,
                test_summary=analysis_result["summary"],
                failed_tests=analysis_result["failed_tests"],
                certificate_id=certificate_id,
            )

            logger.info(f"硬件认证完成: {request.hw_id}, 状态: {certification_status}")
            return response

        except Exception as e:
            logger.error(f"硬件认证验证失败: {str(e)}")
            raise

    def _analyze_test_results(self, test_results: List[TestResult]) -> Dict:
        """
        分析测试结果

        Args:
            test_results: 测试结果列表

        Returns:
            Dict: 分析结果
        """
        summary = {
            "total": len(test_results),
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "by_category": {},
        }

        failed_tests = []
        category_stats = {}

        # 统计各类别测试结果
        for result in test_results:
            # 更新总体统计
            if result.status == "pass":
                summary["passed"] += 1
            elif result.status == "fail":
                summary["failed"] += 1
                failed_tests.append(result)
            else:
                summary["skipped"] += 1

            # 按类别统计
            category = result.category.value
            if category not in category_stats:
                category_stats[category] = {"total": 0, "passed": 0, "failed": 0}

            category_stats[category]["total"] += 1
            if result.status == "pass":
                category_stats[category]["passed"] += 1
            elif result.status == "fail":
                category_stats[category]["failed"] += 1

        summary["by_category"] = category_stats
        summary["pass_rate"] = (
            summary["passed"] / summary["total"] if summary["total"] > 0 else 0
        )

        return {"summary": summary, "failed_tests": failed_tests}

    def _determine_certification_status(
        self, analysis_result: Dict, test_results: List[TestResult]
    ) -> CertificationStatus:
        """
        确定认证状态

        Args:
            analysis_result: 分析结果
            test_results: 测试结果列表

        Returns:
            CertificationStatus: 认证状态
        """
        summary = analysis_result["summary"]
        failed_tests = analysis_result["failed_tests"]

        # 检查基本要求
        if summary["total"] == 0:
            return CertificationStatus.FAILED

        # 检查通过率
        if summary["pass_rate"] < self._min_pass_rate:
            return CertificationStatus.FAILED

        # 检查必需类别是否都有测试
        tested_categories = set(result.category.value for result in test_results)
        required_categories_set = set(cat.value for cat in self._required_categories)

        if not required_categories_set.issubset(tested_categories):
            missing_categories = required_categories_set - tested_categories
            logger.warning(f"缺少必需测试类别: {missing_categories}")
            return CertificationStatus.FAILED

        # 检查关键测试是否通过（这里可以根据需要自定义关键测试）
        critical_failures = [
            test for test in failed_tests if self._is_critical_test(test)
        ]

        if critical_failures:
            logger.warning(f"关键测试失败: {[test.name for test in critical_failures]}")
            return CertificationStatus.FAILED

        return CertificationStatus.CERTIFIED

    def _is_critical_test(self, test_result: TestResult) -> bool:
        """
        判断是否为关键测试

        Args:
            test_result: 测试结果

        Returns:
            bool: 是否为关键测试
        """
        # 关键测试判断逻辑（可根据业务需求调整）
        critical_keywords = ["boot", "connection", "basic", "core"]
        test_name_lower = test_result.name.lower()

        return any(keyword in test_name_lower for keyword in critical_keywords)

    def _save_certification_record(
        self,
        request: CertificationRequest,
        status: CertificationStatus,
        certificate_id: str,
        certified_at: datetime,
        expires_at: datetime,
    ):
        """
        保存认证记录

        Args:
            request: 认证请求
            status: 认证状态
            certificate_id: 证书ID
            certified_at: 认证时间
            expires_at: 过期时间
        """
        record = {
            "hw_id": request.hw_id,
            "status": status.value,
            "device_info": request.device_info,
            "test_results": [result.dict() for result in request.test_results],
            "firmware_version": request.firmware_version,
            "hardware_version": request.hardware_version,
            "submitted_by": request.submitted_by,
            "certificate_id": certificate_id,
            "certified_at": certified_at,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
        }

        self._certifications[request.hw_id] = record
        logger.info(f"认证记录已保存: {request.hw_id}")

    def get_certification_history(self, hw_id: str) -> Optional[Dict]:
        """
        获取硬件认证历史

        Args:
            hw_id: 硬件ID

        Returns:
            Optional[Dict]: 认证历史记录
        """
        return self._certifications.get(hw_id)

    def get_all_certifications(self) -> Dict:
        """
        获取所有认证记录

        Returns:
            Dict: 所有认证记录
        """
        return self._certifications.copy()

    def is_certified(self, hw_id: str) -> bool:
        """
        检查硬件是否已认证且未过期

        Args:
            hw_id: 硬件ID

        Returns:
            bool: 是否已认证且有效
        """
        record = self.get_certification_history(hw_id)
        if not record:
            return False

        if record["status"] != CertificationStatus.CERTIFIED.value:
            return False

        expires_at = record.get("expires_at")
        if not expires_at:
            return True

        return datetime.fromisoformat(expires_at) > datetime.utcnow()


# 单例实例
hardware_certification_service = HardwareCertificationService()
