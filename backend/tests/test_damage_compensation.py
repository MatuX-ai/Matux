"""
配件损坏赔付流程验证测试
验证不同损坏等级的赔付计算和处理流程
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from models.hardware_module import (
    DamageLevel,
    HardwareModule,
    ModuleRentalRecord,
    ModuleRentalStatus,
)
from models.user_license import UserLicense


class TestDamageCompensationProcess:
    """损坏赔付流程测试"""

    @pytest.fixture
    def sample_module(self):
        """创建测试硬件模块"""
        return HardwareModule(
            name="Test Module",
            module_type="sensor",
            serial_number="TEST-MOD-001",
            price_per_day=1.0,
            deposit_amount=Decimal("50.00"),
            total_quantity=10,
            quantity_available=10,
            description="测试模块用于损坏赔付测试",
            status="available",
            is_active=True,
        )

    @pytest.fixture
    def sample_user_license(self):
        """创建测试用户许可证"""
        return UserLicense(
            license_key="TEST-LICENSE-001",
            user_id=1,
            tenant_id=1,
            hardware_rental_limit=5,
            hardware_rented_count=0,
        )

    def test_light_damage_compensation(self, sample_module, sample_user_license):
        """测试轻微损坏赔付"""
        # 创建轻微损坏的租赁记录
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=5),
            rental_end_date=datetime.utcnow(),
            daily_rate=sample_module.price_per_day,
            total_amount=Decimal("5.00"),  # 5天租金
            deposit_paid=sample_module.deposit_amount,
            status=ModuleRentalStatus.RETURNED,
            is_damaged=True,
            damage_level=DamageLevel.LIGHT,
            damage_description="外壳轻微刮痕，不影响功能",
        )

        # 计算赔付金额
        compensation = rental.calculate_compensation()

        # 轻微损坏应该赔付押金的20%
        expected_compensation = sample_module.deposit_amount * Decimal("0.2")
        assert compensation == expected_compensation
        assert compensation == Decimal("10.00")  # 50 * 0.2 = 10

    def test_moderate_damage_compensation(self, sample_module, sample_user_license):
        """测试中等损坏赔付"""
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=3),
            rental_end_date=datetime.utcnow(),
            daily_rate=sample_module.price_per_day,
            total_amount=Decimal("3.00"),
            deposit_paid=sample_module.deposit_amount,
            status=ModuleRentalStatus.RETURNED,
            is_damaged=True,
            damage_level=DamageLevel.MODERATE,
            damage_description="部分功能受限，需要维修",
        )

        compensation = rental.calculate_compensation()

        # 中等损坏应该赔付押金的50%
        expected_compensation = sample_module.deposit_amount * Decimal("0.5")
        assert compensation == expected_compensation
        assert compensation == Decimal("25.00")  # 50 * 0.5 = 25

    def test_severe_damage_compensation(self, sample_module, sample_user_license):
        """测试严重损坏赔付"""
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=7),
            rental_end_date=datetime.utcnow(),
            daily_rate=sample_module.price_per_day,
            total_amount=Decimal("7.00"),
            deposit_paid=sample_module.deposit_amount,
            status=ModuleRentalStatus.RETURNED,
            is_damaged=True,
            damage_level=DamageLevel.SEVERE,
            damage_description="完全损坏，无法修复",
        )

        compensation = rental.calculate_compensation()

        # 严重损坏应该赔付全部押金
        expected_compensation = sample_module.deposit_amount
        assert compensation == expected_compensation
        assert compensation == Decimal("50.00")

    def test_no_damage_no_compensation(self, sample_module, sample_user_license):
        """测试无损坏情况不产生赔付"""
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=2),
            rental_end_date=datetime.utcnow(),
            daily_rate=sample_module.price_per_day,
            total_amount=Decimal("2.00"),
            deposit_paid=sample_module.deposit_amount,
            status=ModuleRentalStatus.RETURNED,
            is_damaged=False,  # 无损坏
            damage_level=None,
            damage_description="",
        )

        compensation = rental.calculate_compensation()

        # 无损坏应该不产生赔付
        assert compensation == Decimal("0.00")

    def test_partial_deposit_refund_with_damage(
        self, sample_module, sample_user_license
    ):
        """测试有损坏时的部分押金退还"""
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=4),
            rental_end_date=datetime.utcnow(),
            daily_rate=sample_module.price_per_day,
            total_amount=Decimal("4.00"),
            deposit_paid=sample_module.deposit_amount,
            deposit_refunded=Decimal("0.00"),  # 初始未退款
            status=ModuleRentalStatus.RETURNED,
            is_damaged=True,
            damage_level=DamageLevel.MODERATE,
            damage_description="需要维修",
        )

        compensation = rental.calculate_compensation()
        refund_amount = rental.deposit_paid - compensation

        # 验证计算逻辑
        assert compensation == Decimal("25.00")  # 50 * 0.5
        assert refund_amount == Decimal("25.00")  # 50 - 25

    def test_multiple_damage_scenarios(self, sample_module, sample_user_license):
        """测试多种损坏场景"""
        test_cases = [
            {
                "damage_level": DamageLevel.LIGHT,
                "expected_multiplier": Decimal("0.2"),
                "description": "轻微损坏",
            },
            {
                "damage_level": DamageLevel.MODERATE,
                "expected_multiplier": Decimal("0.5"),
                "description": "中等损坏",
            },
            {
                "damage_level": DamageLevel.SEVERE,
                "expected_multiplier": Decimal("1.0"),
                "description": "严重损坏",
            },
        ]

        for case in test_cases:
            rental = ModuleRentalRecord(
                module_id=sample_module.id,
                user_license_id=sample_user_license.id,
                rental_start_date=datetime.utcnow() - timedelta(days=3),
                rental_end_date=datetime.utcnow(),
                daily_rate=sample_module.price_per_day,
                total_amount=Decimal("3.00"),
                deposit_paid=sample_module.deposit_amount,
                status=ModuleRentalStatus.RETURNED,
                is_damaged=True,
                damage_level=case["damage_level"],
                damage_description=case["description"],
            )

            compensation = rental.calculate_compensation()
            expected = sample_module.deposit_amount * case["expected_multiplier"]

            assert compensation == expected, f"{case['description']}赔付计算错误"

    def test_damage_level_validation(self, sample_module, sample_user_license):
        """测试损坏等级验证"""
        # 测试有损坏标记但无损坏等级的情况
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=2),
            rental_end_date=datetime.utcnow(),
            daily_rate=sample_module.price_per_day,
            total_amount=Decimal("2.00"),
            deposit_paid=sample_module.deposit_amount,
            status=ModuleRentalStatus.RETURNED,
            is_damaged=True,
            damage_level=None,  # 有损坏标记但无等级
            damage_description="损坏描述",
        )

        # 应该返回0赔付（无效的损坏等级）
        compensation = rental.calculate_compensation()
        assert compensation == Decimal("0.00")

    def test_compensation_with_additional_fees(
        self, sample_module, sample_user_license
    ):
        """测试包含额外费用的赔付"""
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=6),
            rental_end_date=datetime.utcnow(),
            daily_rate=sample_module.price_per_day,
            total_amount=Decimal("6.00"),
            deposit_paid=sample_module.deposit_amount,
            status=ModuleRentalStatus.RETURNED,
            is_damaged=True,
            damage_level=DamageLevel.SEVERE,
            damage_description="需要更换核心组件",
            additional_fees=Decimal("15.00"),  # 额外维修费用
        )

        base_compensation = rental.calculate_compensation()
        total_compensation = base_compensation + (
            rental.additional_fees or Decimal("0.00")
        )

        # 基础赔付 + 额外费用
        assert base_compensation == Decimal("50.00")  # 全额押金
        assert total_compensation == Decimal("65.00")  # 50 + 15

    def test_compensation_rounding_precision(self, sample_module, sample_user_license):
        """测试赔付金额精度"""
        # 测试涉及小数的计算精度
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=1),
            rental_end_date=datetime.utcnow(),
            daily_rate=sample_module.price_per_day,
            total_amount=Decimal("1.00"),
            deposit_paid=Decimal("33.33"),  # 特殊押金金额
            status=ModuleRentalStatus.RETURNED,
            is_damaged=True,
            damage_level=DamageLevel.MODERATE,
            damage_description="精度测试",
        )

        compensation = rental.calculate_compensation()
        expected = Decimal("33.33") * Decimal("0.5")

        # 验证精度处理
        assert compensation == expected
        assert len(str(compensation).split(".")[-1]) <= 2  # 最多两位小数

    def test_compensation_business_rules(self, sample_module, sample_user_license):
        """测试业务规则约束"""
        # 测试赔付金额不超过押金总额
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=10),
            rental_end_date=datetime.utcnow(),
            daily_rate=sample_module.price_per_day,
            total_amount=Decimal("10.00"),
            deposit_paid=sample_module.deposit_amount,
            status=ModuleRentalStatus.RETURNED,
            is_damaged=True,
            damage_level=DamageLevel.SEVERE,
            damage_description="业务规则测试",
        )

        compensation = rental.calculate_compensation()

        # 赔付不应超过押金
        assert compensation <= rental.deposit_paid
        # 对于严重损坏，应该是全额押金
        assert compensation == rental.deposit_paid


class TestDamageProcessingWorkflow:
    """损坏处理工作流测试"""

    def test_damage_reporting_workflow(self, sample_module, sample_user_license):
        """测试损坏报告工作流"""
        # 1. 创建正常租赁
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=5),
            rental_end_date=datetime.utcnow(),
            daily_rate=Decimal("1.00"),
            total_amount=Decimal("5.00"),
            deposit_paid=Decimal("50.00"),
            status=ModuleRentalStatus.ACTIVE,
        )

        # 2. 报告损坏
        rental.report_damage(
            damage_level=DamageLevel.MODERATE,
            description="使用过程中意外跌落导致外壳破损",
            reported_by="user",
        )

        # 3. 验证状态更新
        assert rental.is_damaged is True
        assert rental.damage_level == DamageLevel.MODERATE
        assert rental.damage_description is not None
        assert rental.status == ModuleRentalStatus.RETURNED  # 损坏后自动标记为已归还

    def test_damage_assessment_process(self, sample_module, sample_user_license):
        """测试损坏评估流程"""
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=3),
            rental_end_date=datetime.utcnow(),
            daily_rate=Decimal("1.00"),
            total_amount=Decimal("3.00"),
            deposit_paid=Decimal("50.00"),
            status=ModuleRentalStatus.RETURNED,
            is_damaged=True,
            damage_level=DamageLevel.LIGHT,
        )

        # 模拟管理员评估
        assessment_result = rental.assess_damage(
            assessed_level=DamageLevel.MODERATE,  # 管理员认定为中等损坏
            assessment_notes="经检测，内部电路有轻微影响",
            assessed_by="admin",
        )

        # 验证评估结果
        assert assessment_result["compensation_adjusted"] is True
        assert rental.damage_level == DamageLevel.MODERATE
        assert rental.calculate_compensation() == Decimal("25.00")  # 中等损坏赔付

    def test_compensation_payment_tracking(self, sample_module, sample_user_license):
        """测试赔付支付跟踪"""
        rental = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=7),
            rental_end_date=datetime.utcnow(),
            daily_rate=Decimal("1.00"),
            total_amount=Decimal("7.00"),
            deposit_paid=Decimal("50.00"),
            status=ModuleRentalStatus.RETURNED,
            is_damaged=True,
            damage_level=DamageLevel.SEVERE,
        )

        compensation = rental.calculate_compensation()

        # 模拟赔付支付流程
        payment_status = rental.process_compensation_payment(
            amount=compensation,
            payment_method="deposit_deduction",
            processed_by="system",
        )

        # 验证支付状态
        assert payment_status["success"] is True
        assert rental.compensation_paid is True
        assert rental.compensation_amount == compensation
        assert rental.deposit_refunded == Decimal("0.00")  # 严重损坏不退款


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
