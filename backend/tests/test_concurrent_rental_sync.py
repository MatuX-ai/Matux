"""
并发租赁库存同步测试
测试多用户同时租赁时的库存同步和竞态条件处理
"""

import asyncio
from datetime import datetime, timedelta
import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config.settings import Settings
from models.hardware_module import (
    HardwareModule,
    HardwareModuleStatus,
    ModuleRentalRecord,
    ModuleRentalStatus,
)
from models.user_license import UserLicense
from services.hardware_inventory_service import hardware_inventory_service


class TestConcurrentRentalSync:
    """并发租赁同步测试"""

    @pytest.fixture
    async def db_session(self):
        """创建测试数据库会话"""
        settings = Settings()
        engine = create_async_engine(
            settings.TEST_DATABASE_URL or settings.DATABASE_URL
        )
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with async_session() as session:
            yield session

        await engine.dispose()

    @pytest.fixture
    async def high_demand_module(self, db_session):
        """创建高需求测试模块（少量库存）"""
        module = HardwareModule(
            name="Popular Sensor",
            module_type="sensor",
            serial_number="POP-SEN-001",
            price_per_day=1.0,
            deposit_amount=30.0,
            total_quantity=3,  # 只有3个库存
            quantity_available=3,
            description="高需求传感器模块",
            status=HardwareModuleStatus.AVAILABLE,
            is_active=True,
        )
        db_session.add(module)
        await db_session.commit()
        await db_session.refresh(module)
        return module

    @pytest.fixture
    async def multiple_user_licenses(self, db_session):
        """创建多个用户许可证"""
        licenses = []
        for i in range(10):  # 创建10个用户许可证
            license = UserLicense(
                license_key=f"USER-LICENSE-{i:03d}",
                user_id=i + 1,
                tenant_id=1,
                hardware_rental_limit=2,
                hardware_rented_count=0,
            )
            db_session.add(license)
            licenses.append(license)

        await db_session.commit()
        for license in licenses:
            await db_session.refresh(license)
        return licenses

    async def test_race_condition_prevention(self, high_demand_module, db_session):
        """测试竞态条件防护"""
        print("开始竞态条件测试...")

        # 模拟多个用户同时尝试租赁最后一个库存
        concurrent_requests = 5
        results = []

        async def attempt_rental(request_id):
            """模拟租赁尝试"""
            try:
                # 每个请求都检查可用性然后预留
                is_available = await hardware_inventory_service.check_availability(
                    high_demand_module.id, 1, db_session
                )

                if is_available:
                    # 添加小延迟模拟网络延迟
                    await asyncio.sleep(0.1)
                    reserved = await hardware_inventory_service.reserve_module(
                        high_demand_module.id, 1, db_session
                    )
                    results.append((request_id, reserved, "success"))
                else:
                    results.append((request_id, False, "not_available"))

            except Exception as e:
                results.append((request_id, False, f"error: {str(e)}"))

        # 同时启动多个租赁请求
        tasks = [attempt_rental(i) for i in range(concurrent_requests)]
        await asyncio.gather(*tasks)

        # 分析结果
        successful_reservations = [r for r in results if r[1]]
        failed_reservations = [r for r in results if not r[1]]

        print(f"总请求数: {concurrent_requests}")
        print(f"成功预订: {len(successful_reservations)}")
        print(f"失败预订: {len(failed_reservations)}")
        print("详细结果:", results)

        # 验证库存没有超卖
        await db_session.refresh(high_demand_module)
        expected_available = max(0, 3 - len(successful_reservations))
        assert high_demand_module.quantity_available == expected_available
        assert len(successful_reservations) <= 3  # 不超过总库存

    async def test_inventory_consistency_under_load(
        self, high_demand_module, multiple_user_licenses, db_session
    ):
        """测试负载下的库存一致性"""
        print("开始负载测试...")

        # 创建大量并发租赁请求
        rental_requests = []
        for i, license in enumerate(multiple_user_licenses[:8]):  # 使用前8个许可证
            request = {
                "user_license_id": license.id,
                "module_id": high_demand_module.id,
                "quantity": 1,
                "request_time": time.time(),
            }
            rental_requests.append(request)

        # 存储结果
        successful_rentals = []
        failed_rentals = []

        async def process_rental_request(request):
            """处理单个租赁请求"""
            try:
                # 检查并预留模块
                is_available = await hardware_inventory_service.check_availability(
                    request["module_id"], request["quantity"], db_session
                )

                if is_available:
                    reserved = await hardware_inventory_service.reserve_module(
                        request["module_id"], request["quantity"], db_session
                    )

                    if reserved:
                        # 创建租赁记录
                        rental_record = ModuleRentalRecord(
                            module_id=request["module_id"],
                            user_license_id=request["user_license_id"],
                            rental_start_date=datetime.utcnow(),
                            rental_end_date=datetime.utcnow() + timedelta(days=7),
                            daily_rate=1.0,
                            total_amount=7.0,
                            deposit_paid=30.0,
                            status=ModuleRentalStatus.ACTIVE,
                        )
                        db_session.add(rental_record)
                        await db_session.commit()
                        await db_session.refresh(rental_record)

                        successful_rentals.append(
                            {
                                "request": request,
                                "rental_id": rental_record.id,
                                "timestamp": time.time(),
                            }
                        )
                        return True

                failed_rentals.append(
                    {
                        "request": request,
                        "reason": "库存不足" if not is_available else "预留失败",
                        "timestamp": time.time(),
                    }
                )
                return False

            except Exception as e:
                failed_rentals.append(
                    {
                        "request": request,
                        "reason": f"异常: {str(e)}",
                        "timestamp": time.time(),
                    }
                )
                return False

        # 并发处理所有请求
        tasks = [process_rental_request(req) for req in rental_requests]
        await asyncio.gather(*tasks)

        # 验证最终状态
        await db_session.refresh(high_demand_module)

        total_attempts = len(rental_requests)
        successful_count = len(successful_rentals)
        failed_count = len(failed_rentals)

        print(f"总尝试次数: {total_attempts}")
        print(f"成功租赁: {successful_count}")
        print(f"失败租赁: {failed_count}")
        print(f"最终可用库存: {high_demand_module.quantity_available}")

        # 验证数据一致性
        assert successful_count + failed_count == total_attempts
        assert high_demand_module.quantity_available >= 0
        assert high_demand_module.quantity_available == 3 - successful_count

        # 验证没有重复预订
        unique_successful_licenses = set(
            r["request"]["user_license_id"] for r in successful_rentals
        )
        assert len(unique_successful_licenses) == len(successful_rentals)

    async def test_concurrent_return_processing(
        self, high_demand_module, multiple_user_licenses, db_session
    ):
        """测试并发归还处理"""
        print("开始并发归还测试...")

        # 首先创建一些租赁记录
        active_rentals = []
        for i in range(3):  # 创建3个活跃租赁
            rental = ModuleRentalRecord(
                module_id=high_demand_module.id,
                user_license_id=multiple_user_licenses[i].id,
                rental_start_date=datetime.utcnow() - timedelta(days=3),
                rental_end_date=datetime.utcnow() + timedelta(days=4),
                daily_rate=1.0,
                total_amount=7.0,
                deposit_paid=30.0,
                status=ModuleRentalStatus.ACTIVE,
            )
            db_session.add(rental)
            active_rentals.append(rental)

        await db_session.commit()
        for rental in active_rentals:
            await db_session.refresh(rental)

        # 更新模块库存（模拟已出租状态）
        high_demand_module.quantity_available = 0
        high_demand_module.status = HardwareModuleStatus.RENTED
        await db_session.commit()

        # 模拟并发归还
        return_results = []

        async def process_return(rental_record):
            """处理归还"""
            try:
                # 模拟归还处理时间
                await asyncio.sleep(0.05)

                # 更新租赁记录
                rental_record.actual_return_date = datetime.utcnow()
                rental_record.status = ModuleRentalStatus.RETURNED

                # 更新模块库存
                high_demand_module.quantity_available += 1
                if high_demand_module.quantity_available > 0:
                    high_demand_module.status = HardwareModuleStatus.AVAILABLE

                await db_session.commit()

                return_results.append(
                    {
                        "rental_id": rental_record.id,
                        "status": "success",
                        "timestamp": time.time(),
                    }
                )

            except Exception as e:
                return_results.append(
                    {
                        "rental_id": rental_record.id,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": time.time(),
                    }
                )

        # 并发处理归还
        tasks = [process_return(rental) for rental in active_rentals]
        await asyncio.gather(*tasks)

        # 验证最终状态
        await db_session.refresh(high_demand_module)

        successful_returns = [r for r in return_results if r["status"] == "success"]

        print(f"总归还尝试: {len(active_rentals)}")
        print(f"成功归还: {len(successful_returns)}")
        print(f"最终库存: {high_demand_module.quantity_available}")
        print(f"模块状态: {high_demand_module.status}")

        # 验证库存正确恢复
        assert len(successful_returns) == 3
        assert high_demand_module.quantity_available == 3
        assert high_demand_module.status == HardwareModuleStatus.AVAILABLE

    async def test_deadlock_prevention(self, db_session):
        """测试死锁预防"""
        print("开始死锁预防测试...")

        # 创建多个模块用于交叉租赁测试
        modules = []
        for i in range(3):
            module = HardwareModule(
                name=f"Module-{i}",
                module_type="test",
                serial_number=f"MOD-{i:03d}",
                price_per_day=1.0,
                deposit_amount=20.0,
                total_quantity=2,
                quantity_available=2,
                status=HardwareModuleStatus.AVAILABLE,
                is_active=True,
            )
            db_session.add(module)
            modules.append(module)

        await db_session.commit()
        for module in modules:
            await db_session.refresh(module)

        # 创建复杂的交叉租赁场景
        async def complex_rental_scenario():
            """复杂租赁场景测试"""
            try:
                # 场景：用户A租Module-0，用户B租Module-1，然后交换需求
                # 这种场景容易产生死锁

                # 第一阶段：各自租赁
                res1 = await hardware_inventory_service.reserve_module(
                    modules[0].id, 1, db_session
                )
                res2 = await hardware_inventory_service.reserve_module(
                    modules[1].id, 1, db_session
                )

                if res1 and res2:
                    # 第二阶段：尝试交叉租赁
                    await asyncio.sleep(0.01)  # 模拟延迟

                    # 用户A想要Module-1，用户B想要Module-0
                    res3 = await hardware_inventory_service.reserve_module(
                        modules[1].id, 1, db_session
                    )
                    res4 = await hardware_inventory_service.reserve_module(
                        modules[0].id, 1, db_session
                    )

                    # 清理：释放所有预留
                    if res1:
                        await hardware_inventory_service.release_reservation(
                            modules[0].id, 1, db_session
                        )
                    if res2:
                        await hardware_inventory_service.release_reservation(
                            modules[1].id, 1, db_session
                        )
                    if res3:
                        await hardware_inventory_service.release_reservation(
                            modules[1].id, 1, db_session
                        )
                    if res4:
                        await hardware_inventory_service.release_reservation(
                            modules[0].id, 1, db_session
                        )

                return True

            except Exception as e:
                print(f"死锁测试异常: {e}")
                return False

        # 运行多个并发的复杂场景
        tasks = [complex_rental_scenario() for _ in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证没有死锁发生
        successful_scenarios = [r for r in results if r is True]
        print(f"成功完成的复杂场景: {len(successful_scenarios)}/{len(results)}")

        # 验证所有模块库存正常
        for module in modules:
            await db_session.refresh(module)
            assert module.quantity_available == 2
            assert module.status == HardwareModuleStatus.AVAILABLE


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
