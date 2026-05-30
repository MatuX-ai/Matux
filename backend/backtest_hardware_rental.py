"""
模块化硬件租赁系统完整回测验证脚本
验证所有功能模块的完整性和正确性
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config.settings import Settings
from models.hardware_module import (
    Base,
    DamageLevel,
    HardwareModule,
    HardwareModuleStatus,
    ModuleRentalRecord,
    ModuleRentalStatus,
)
from models.user_license import UserLicense
from services.hardware_inventory_service import hardware_inventory_service


class HardwareRentalBacktest:
    """硬件租赁系统回测验证类"""

    def __init__(self):
        self.settings = Settings()
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0

    async def setup_test_environment(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")

        # 创建测试数据库引擎
        self.engine = create_async_engine(
            getattr(self.settings, "TEST_DATABASE_URL", None)
            or self.settings.DATABASE_URL,
            echo=False,
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # 创建表结构
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        print("✅ 测试环境设置完成")

    async def cleanup_test_environment(self):
        """清理测试环境"""
        print("🧹 清理测试环境...")
        if hasattr(self, "engine"):
            await self.engine.dispose()
        print("✅ 测试环境清理完成")

    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results.append(
            {
                "test_name": test_name,
                "passed": passed,
                "details": details,
                "timestamp": datetime.now(),
            }
        )

        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

        print(f"{status} {test_name}: {details}")

    async def test_data_model_integrity(self):
        """测试数据模型完整性"""
        print("\n📋 测试1: 数据模型完整性验证")

        async with self.async_session() as session:
            try:
                # 创建测试数据
                module = HardwareModule(
                    name="Backtest Arduino",
                    module_type="microcontroller",
                    serial_number="BT-ARD-001",
                    price_per_day=Decimal("1.00"),
                    deposit_amount=Decimal("50.00"),
                    total_quantity=10,
                    quantity_available=10,
                    description="回测专用Arduino模块",
                    status=HardwareModuleStatus.AVAILABLE,
                    is_active=True,
                )

                license = UserLicense(
                    license_key="BT-LICENSE-001",
                    user_id=999,
                    tenant_id=1,
                    hardware_rental_limit=5,
                    hardware_rented_count=0,
                )

                session.add_all([module, license])
                await session.commit()
                await session.refresh(module)
                await session.refresh(license)

                # 验证数据创建
                assert module.id is not None, "模块ID未生成"
                assert license.id is not None, "许可证ID未生成"
                assert module.quantity_available == 10, "初始库存不正确"

                self.log_test_result("数据模型创建", True, "模块和许可证创建成功")

                # 测试关联关系
                rental = ModuleRentalRecord(
                    module_id=module.id,
                    user_license_id=license.id,
                    rental_start_date=datetime.utcnow(),
                    rental_end_date=datetime.utcnow() + timedelta(days=7),
                    daily_rate=Decimal("1.00"),
                    total_amount=Decimal("7.00"),
                    deposit_paid=Decimal("50.00"),
                    status=ModuleRentalStatus.ACTIVE,
                )

                session.add(rental)
                await session.commit()
                await session.refresh(rental)

                assert rental.id is not None, "租赁记录ID未生成"
                self.log_test_result("关联关系验证", True, "租赁记录创建成功")

                # 清理测试数据
                await session.delete(rental)
                await session.delete(module)
                await session.delete(license)
                await session.commit()

            except Exception as e:
                self.log_test_result("数据模型完整性", False, f"异常: {str(e)}")
                await session.rollback()

    async def test_inventory_management(self):
        """测试库存管理功能"""
        print("\n📦 测试2: 库存管理功能验证")

        async with self.async_session() as session:
            try:
                # 创建测试模块
                module = HardwareModule(
                    name="Inventory Test Module",
                    module_type="sensor",
                    serial_number="INV-TEST-001",
                    price_per_day=Decimal("1.00"),
                    deposit_amount=Decimal("30.00"),
                    total_quantity=5,
                    quantity_available=5,
                    status=HardwareModuleStatus.AVAILABLE,
                    is_active=True,
                )
                session.add(module)
                await session.commit()
                await session.refresh(module)

                module_id = module.id

                # 测试库存检查
                is_available = await hardware_inventory_service.check_availability(
                    module_id, 3, session
                )
                assert is_available is True, "库存检查失败"
                self.log_test_result("库存可用性检查", True, "3个库存可用")

                # 测试超出库存检查
                is_available = await hardware_inventory_service.check_availability(
                    module_id, 10, session
                )
                assert is_available is False, "应该检测到库存不足"
                self.log_test_result("库存不足检测", True, "正确识别库存不足")

                # 测试预留功能
                reserved = await hardware_inventory_service.reserve_module(
                    module_id, 2, session
                )
                assert reserved is True, "预留功能失败"

                await session.refresh(module)
                assert module.quantity_available == 3, "预留后库存未更新"
                self.log_test_result("模块预留功能", True, "成功预留2个模块")

                # 测试释放功能
                released = await hardware_inventory_service.release_reservation(
                    module_id, 1, session
                )
                assert released is True, "释放功能失败"

                await session.refresh(module)
                assert module.quantity_available == 4, "释放后库存未更新"
                self.log_test_result("模块释放功能", True, "成功释放1个模块")

                # 清理
                await session.delete(module)
                await session.commit()

            except Exception as e:
                self.log_test_result("库存管理", False, f"异常: {str(e)}")
                await session.rollback()

    async def test_rental_lifecycle(self):
        """测试租赁生命周期"""
        print("\n🔄 测试3: 租赁生命周期验证")

        async with self.async_session() as session:
            try:
                # 创建测试数据
                module = HardwareModule(
                    name="Lifecycle Test Module",
                    module_type="actuator",
                    serial_number="LIFECYCLE-001",
                    price_per_day=Decimal("1.00"),
                    deposit_amount=Decimal("40.00"),
                    total_quantity=3,
                    quantity_available=3,
                    status=HardwareModuleStatus.AVAILABLE,
                    is_active=True,
                )

                license = UserLicense(
                    license_key="LIFECYCLE-LIC-001",
                    user_id=888,
                    tenant_id=1,
                    hardware_rental_limit=3,
                    hardware_rented_count=0,
                )

                session.add_all([module, license])
                await session.commit()
                await session.refresh(module)
                await session.refresh(license)

                # 1. 租赁模块
                reserved = await hardware_inventory_service.reserve_module(
                    module.id, 1, session
                )
                assert reserved is True, "租赁预留失败"

                rental = ModuleRentalRecord(
                    module_id=module.id,
                    user_license_id=license.id,
                    rental_start_date=datetime.utcnow(),
                    rental_end_date=datetime.utcnow() + timedelta(days=5),
                    daily_rate=Decimal("1.00"),
                    total_amount=Decimal("5.00"),
                    deposit_paid=Decimal("40.00"),
                    status=ModuleRentalStatus.ACTIVE,
                )

                session.add(rental)
                await session.commit()
                await session.refresh(rental)

                await session.refresh(module)
                assert module.quantity_available == 2, "租赁后库存未减少"
                self.log_test_result("租赁开始", True, "模块成功租赁")

                # 2. 归还模块
                rental.actual_return_date = datetime.utcnow()
                rental.status = ModuleRentalStatus.RETURNED
                module.quantity_available += 1
                if (
                    module.quantity_available > 0
                    and module.status == HardwareModuleStatus.RENTED
                ):
                    module.status = HardwareModuleStatus.AVAILABLE

                await session.commit()
                await session.refresh(rental)
                await session.refresh(module)

                assert rental.status == ModuleRentalStatus.RETURNED, "归还状态未更新"
                assert module.quantity_available == 3, "归还后库存未恢复"
                self.log_test_result("租赁归还", True, "模块成功归还")

                # 3. 验证租赁历史
                history_query = await session.execute(
                    select(ModuleRentalRecord).filter(
                        ModuleRentalRecord.user_license_id == license.id
                    )
                )
                history = history_query.scalars().all()
                assert len(history) == 1, "租赁历史记录不正确"
                self.log_test_result("租赁历史", True, "历史记录正确")

                # 清理
                await session.delete(rental)
                await session.delete(module)
                await session.delete(license)
                await session.commit()

            except Exception as e:
                self.log_test_result("租赁生命周期", False, f"异常: {str(e)}")
                await session.rollback()

    async def test_damage_compensation(self):
        """测试损坏赔付功能"""
        print("\n💰 测试4: 损坏赔付功能验证")

        async with self.async_session() as session:
            try:
                # 创建测试数据
                module = HardwareModule(
                    name="Damage Test Module",
                    module_type="display",
                    serial_number="DAMAGE-001",
                    price_per_day=Decimal("1.00"),
                    deposit_amount=Decimal("60.00"),
                    total_quantity=2,
                    quantity_available=2,
                    status=HardwareModuleStatus.AVAILABLE,
                    is_active=True,
                )

                license = UserLicense(
                    license_key="DAMAGE-LIC-001",
                    user_id=777,
                    tenant_id=1,
                    hardware_rental_limit=2,
                    hardware_rented_count=0,
                )

                session.add_all([module, license])
                await session.commit()
                await session.refresh(module)
                await session.refresh(license)

                # 测试不同损坏等级的赔付
                test_cases = [
                    (DamageLevel.LIGHT, Decimal("12.00")),  # 60 * 0.2
                    (DamageLevel.MODERATE, Decimal("30.00")),  # 60 * 0.5
                    (DamageLevel.SEVERE, Decimal("60.00")),  # 60 * 1.0
                ]

                for damage_level, expected_compensation in test_cases:
                    rental = ModuleRentalRecord(
                        module_id=module.id,
                        user_license_id=license.id,
                        rental_start_date=datetime.utcnow() - timedelta(days=3),
                        rental_end_date=datetime.utcnow(),
                        daily_rate=Decimal("1.00"),
                        total_amount=Decimal("3.00"),
                        deposit_paid=Decimal("60.00"),
                        status=ModuleRentalStatus.RETURNED,
                        is_damaged=True,
                        damage_level=damage_level,
                        damage_description=f"{damage_level.value} damage test",
                    )

                    compensation = rental.calculate_compensation()
                    assert (
                        compensation == expected_compensation
                    ), f"{damage_level.value}赔付计算错误"

                    session.add(rental)

                await session.commit()
                self.log_test_result("损坏赔付计算", True, "所有损坏等级赔付计算正确")

                # 清理
                cleanup_query = await session.execute(
                    select(ModuleRentalRecord).filter(
                        ModuleRentalRecord.user_license_id == license.id
                    )
                )
                rentals = cleanup_query.scalars().all()
                for rental in rentals:
                    await session.delete(rental)

                await session.delete(module)
                await session.delete(license)
                await session.commit()

            except Exception as e:
                self.log_test_result("损坏赔付", False, f"异常: {str(e)}")
                await session.rollback()

    async def test_concurrent_scenarios(self):
        """测试并发场景"""
        print("\n⚡ 测试5: 并发场景验证")

        async with self.async_session() as session:
            try:
                # 创建高需求模块
                module = HardwareModule(
                    name="Concurrent Test Module",
                    module_type="processor",
                    serial_number="CONCURRENT-001",
                    price_per_day=Decimal("1.00"),
                    deposit_amount=Decimal("25.00"),
                    total_quantity=3,  # 限量3个
                    quantity_available=3,
                    status=HardwareModuleStatus.AVAILABLE,
                    is_active=True,
                )

                session.add(module)
                await session.commit()
                await session.refresh(module)

                # 模拟多个用户同时租赁
                async def simulate_rental_attempt(attempt_id):
                    try:
                        is_available = (
                            await hardware_inventory_service.check_availability(
                                module.id, 1, session
                            )
                        )

                        if is_available:
                            await asyncio.sleep(0.01)  # 模拟网络延迟
                            reserved = await hardware_inventory_service.reserve_module(
                                module.id, 1, session
                            )
                            return reserved
                    except Exception:
                        return False
                    return False

                # 启动5个并发请求（超过库存量）
                tasks = [simulate_rental_attempt(i) for i in range(5)]
                results = await asyncio.gather(*tasks)

                successful_reservations = sum(1 for result in results if result)

                # 验证没有超卖
                await session.refresh(module)
                assert successful_reservations <= 3, "发生超卖现象"
                assert module.quantity_available >= 0, "库存变为负数"

                expected_available = 3 - successful_reservations
                assert module.quantity_available == expected_available, "库存计算错误"

                self.log_test_result(
                    "并发库存控制",
                    True,
                    f"成功处理{successful_reservations}个并发请求，无超卖",
                )

                # 清理并恢复库存
                await session.delete(module)
                await session.commit()

            except Exception as e:
                self.log_test_result("并发场景", False, f"异常: {str(e)}")
                await session.rollback()

    async def run_complete_backtest(self):
        """运行完整回测"""
        print("=" * 60)
        print("🚀 开始模块化硬件租赁系统完整回测")
        print("=" * 60)

        start_time = datetime.now()

        try:
            # 设置测试环境
            await self.setup_test_environment()

            # 执行各项测试
            await self.test_data_model_integrity()
            await self.test_inventory_management()
            await self.test_rental_lifecycle()
            await self.test_damage_compensation()
            await self.test_concurrent_scenarios()

            # 输出测试总结
            end_time = datetime.now()
            duration = end_time - start_time

            print("\n" + "=" * 60)
            print("📊 回测结果总结")
            print("=" * 60)
            print(f"测试开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"测试结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"总耗时: {duration.total_seconds():.2f}秒")
            print(f"总测试数: {self.passed_tests + self.failed_tests}")
            print(f"✅ 通过测试: {self.passed_tests}")
            print(f"❌ 失败测试: {self.failed_tests}")
            print(
                f"成功率: {(self.passed_tests / (self.passed_tests + self.failed_tests) * 100):.1f}%"
            )

            if self.failed_tests == 0:
                print("\n🎉 所有测试通过！系统功能验证成功！")
                return True
            else:
                print(f"\n⚠️  存在 {self.failed_tests} 个失败测试，请检查相关功能")
                return False

        except Exception as e:
            print(f"\n💥 回测执行异常: {str(e)}")
            return False
        finally:
            # 清理测试环境
            await self.cleanup_test_environment()


async def main():
    """主函数"""
    backtest = HardwareRentalBacktest()
    success = await backtest.run_complete_backtest()

    # 返回适当的退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
