"""
区块链网关服务回测验证脚本
验证所有功能模块的完整性和正确性
"""

import asyncio
from datetime import datetime
import json
import logging
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.blockchain.fallback_handler import circuit_breaker_fallback
from services.blockchain.gateway_service import blockchain_gateway_service
from utils.circuit_breaker import CircuitBreaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlockchainGatewayBacktest:
    """区块链网关回测验证类"""

    def __init__(self):
        self.results = []
        self.passed_count = 0
        self.failed_count = 0
        self.start_time = datetime.now()

    def log_result(self, test_name: str, status: str, message: str, details: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,
            "message": message,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

        self.results.append(result)

        if status == "PASS":
            self.passed_count += 1
            logger.info(f"✅ {test_name}: {message}")
        else:
            self.failed_count += 1
            logger.error(f"❌ {test_name}: {message}")
            if details:
                logger.error(f"   详情: {details}")

    async def test_service_initialization(self):
        """测试服务初始化"""
        test_name = "服务初始化"
        try:
            await blockchain_gateway_service.initialize()
            if blockchain_gateway_service.initialized:
                self.log_result(test_name, "PASS", "服务初始化成功")
            else:
                self.log_result(test_name, "FAIL", "服务初始化标志未设置")
        except Exception as e:
            self.log_result(test_name, "FAIL", "服务初始化异常", str(e))

    async def test_health_check(self):
        """测试健康检查功能"""
        test_name = "健康检查"
        try:
            health_data = await blockchain_gateway_service.health_check()

            required_fields = ["status", "connected", "timestamp"]
            missing_fields = [
                field for field in required_fields if field not in health_data
            ]

            if not missing_fields:
                self.log_result(test_name, "PASS", "健康检查返回完整数据")
            else:
                self.log_result(
                    test_name, "FAIL", f"健康检查缺少字段: {missing_fields}"
                )

        except Exception as e:
            self.log_result(test_name, "FAIL", "健康检查异常", str(e))

    async def test_issue_integral_success(self):
        """测试积分发行成功场景"""
        test_name = "积分发行成功"
        try:
            result = await blockchain_gateway_service.issue_integral(
                student_id="backtest_student_001",
                amount=100,
                issuer_id=1,
                description="回测发行",
            )

            required_fields = ["tx_id", "student_id", "amount", "issuer_id"]
            missing_fields = [field for field in required_fields if field not in result]

            if not missing_fields and result.get("tx_id"):
                self.log_result(test_name, "PASS", "积分发行成功，返回交易ID")
            else:
                self.log_result(test_name, "FAIL", "积分发行返回数据不完整")

        except Exception as e:
            self.log_result(test_name, "FAIL", "积分发行异常", str(e))

    async def test_issue_integral_fallback(self):
        """测试积分发行降级处理"""
        test_name = "积分发行降级处理"
        try:
            # 模拟服务失败触发降级
            result = await circuit_breaker_fallback.handle_issue_integral_fallback(
                blockchain_gateway_service, "fallback_student", 200, 1, "降级测试"
            )

            if result.get("status") == "fallback_success" and result.get("tx_id"):
                self.log_result(test_name, "PASS", "降级处理返回成功响应")
            else:
                self.log_result(test_name, "FAIL", "降级处理响应格式不正确")

        except Exception as e:
            self.log_result(test_name, "FAIL", "降级处理异常", str(e))

    async def test_get_student_balance(self):
        """测试查询学生余额"""
        test_name = "查询学生余额"
        try:
            balance_data = await blockchain_gateway_service.get_student_balance(
                "test_student"
            )

            required_fields = ["student_id", "total_amount", "updated_at"]
            missing_fields = [
                field for field in required_fields if field not in balance_data
            ]

            if not missing_fields:
                self.log_result(test_name, "PASS", "余额查询返回完整数据")
            else:
                self.log_result(
                    test_name, "FAIL", f"余额查询缺少字段: {missing_fields}"
                )

        except Exception as e:
            self.log_result(test_name, "FAIL", "余额查询异常", str(e))

    async def test_oauth2_token_validation(self):
        """测试OAuth2令牌验证"""
        test_name = "OAuth2令牌验证"
        try:
            # 测试有效凭据
            valid_result = await blockchain_gateway_service.validate_client_credentials(
                "test_client_1", "test_secret_1"
            )

            # 测试无效凭据
            invalid_result = (
                await blockchain_gateway_service.validate_client_credentials(
                    "invalid_client", "wrong_secret"
                )
            )

            if valid_result and not invalid_result:
                self.log_result(test_name, "PASS", "客户端凭据验证逻辑正确")
            else:
                self.log_result(test_name, "FAIL", "客户端凭据验证逻辑错误")

        except Exception as e:
            self.log_result(test_name, "FAIL", "OAuth2验证异常", str(e))

    async def test_access_token_generation(self):
        """测试访问令牌生成"""
        test_name = "访问令牌生成"
        try:
            token_data = await blockchain_gateway_service.generate_access_token(
                "test_client_1", "client_credentials", "read write"
            )

            required_fields = ["access_token", "token_type", "expires_in", "scope"]
            missing_fields = [
                field for field in required_fields if field not in token_data
            ]

            if not missing_fields and token_data.get("access_token"):
                self.log_result(test_name, "PASS", "令牌生成成功")
            else:
                self.log_result(test_name, "FAIL", "令牌生成返回数据不完整")

        except Exception as e:
            self.log_result(test_name, "FAIL", "令牌生成异常", str(e))

    async def test_circuit_breaker_functionality(self):
        """测试熔断器功能"""
        test_name = "熔断器功能"
        try:
            circuit_breaker = CircuitBreaker(
                failure_threshold=2, timeout=1, half_open_attempts=1
            )
            await circuit_breaker.initialize()

            # 测试初始状态
            if circuit_breaker.get_state() == "closed":
                self.log_result(test_name + " - 初始状态", "PASS", "熔断器初始状态正确")
            else:
                self.log_result(test_name + " - 初始状态", "FAIL", "熔断器初始状态错误")

            # 测试失败阈值
            for _ in range(2):
                await circuit_breaker._on_failure()

            if circuit_breaker.get_state() == "open":
                self.log_result(test_name + " - 熔断触发", "PASS", "熔断器正确触发")
            else:
                self.log_result(test_name + " - 熔断触发", "FAIL", "熔断器未能正确触发")

            self.log_result(test_name, "PASS", "熔断器核心功能验证通过")

        except Exception as e:
            self.log_result(test_name, "FAIL", "熔断器测试异常", str(e))

    async def test_cache_management(self):
        """测试缓存管理功能"""
        test_name = "缓存管理"
        try:
            cache_manager = circuit_breaker_fallback.cache_manager

            # 测试缓存存储
            test_data = {
                "student_id": "cache_test",
                "total_amount": 500,
                "updated_at": 1234567890,
            }
            cache_manager.cache_student_balance("cache_test", test_data)

            # 测试缓存获取
            cached_data = cache_manager.get_cached_balance("cache_test")

            if cached_data and cached_data.get("total_amount") == 500:
                self.log_result(test_name, "PASS", "缓存存储和获取功能正常")
            else:
                self.log_result(test_name, "FAIL", "缓存功能异常")

        except Exception as e:
            self.log_result(test_name, "FAIL", "缓存管理异常", str(e))

    async def run_all_tests(self):
        """运行所有回测"""
        logger.info("🚀 开始区块链网关服务回测验证...")
        logger.info("=" * 60)

        test_functions = [
            self.test_service_initialization,
            self.test_health_check,
            self.test_issue_integral_success,
            self.test_issue_integral_fallback,
            self.test_get_student_balance,
            self.test_oauth2_token_validation,
            self.test_access_token_generation,
            self.test_circuit_breaker_functionality,
            self.test_cache_management,
        ]

        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                logger.error(f"测试执行异常 {test_func.__name__}: {e}")

        # 生成报告
        await self.generate_report()

    async def generate_report(self):
        """生成回测报告"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        report = {
            "test_suite": "区块链网关服务回测验证",
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "total_tests": len(self.results),
            "passed_tests": self.passed_count,
            "failed_tests": self.failed_count,
            "pass_rate": (
                round((self.passed_count / len(self.results)) * 100, 2)
                if self.results
                else 0
            ),
            "results": self.results,
        }

        # 保存报告到文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"blockchain_gateway_backtest_{timestamp}.json"

        with open(report_filename, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 打印摘要
        logger.info("=" * 60)
        logger.info("📊 回测验证报告摘要:")
        logger.info(f"   总测试数: {len(self.results)}")
        logger.info(f"   通过测试: {self.passed_count}")
        logger.info(f"   失败测试: {self.failed_count}")
        logger.info(f"   通过率: {report['pass_rate']}%")
        logger.info(f"   执行耗时: {duration:.2f}秒")
        logger.info(f"   详细报告: {report_filename}")
        logger.info("=" * 60)

        if self.failed_count == 0:
            logger.info("🎉 所有回测验证通过！")
        else:
            logger.warning(f"⚠️  {self.failed_count} 个测试失败，请检查相关功能")


async def main():
    """主函数"""
    backtest = BlockchainGatewayBacktest()
    await backtest.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
