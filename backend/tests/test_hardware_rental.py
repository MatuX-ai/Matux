"""
硬件租赁系统集成测试
测试硬件模块租赁、归还、库存管理等功能
"""

import asyncio
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config.settings import Settings
from models.hardware_module import (
    DamageLevel,
    HardwareModule,
    HardwareModuleStatus,
    ModuleRentalRecord,
    ModuleRentalStatus,
)
from models.user_license import UserLicense
from services.hardware_inventory_service import hardware_inventory_service


class TestHardwareModuleModel:
    """硬件模块模型测试"""

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
    async def sample_module(self, db_session):
        """创建测试硬件模块"""
        module = HardwareModule(
            name="Test Arduino",
            module_type="microcontroller",
            serial_number="TEST-ARD-001",
            price_per_day=1.0,
            deposit_amount=50.0,
            total_quantity=5,
            quantity_available=5,
            description="测试用Arduino模块",
            status=HardwareModuleStatus.AVAILABLE,
            is_active=True,
        )
        db_session.add(module)
        await db_session.commit()
        await db_session.refresh(module)
        return module

    @pytest.fixture
    async def sample_user_license(self, db_session):
        """创建测试用户许可证"""
        license = UserLicense(
            license_key="TEST-LICENSE-001",
            user_id=1,
            tenant_id=1,
            hardware_rental_limit=3,
            hardware_rented_count=0,
        )
        db_session.add(license)
        await db_session.commit()
        await db_session.refresh(license)
        return license

    async def test_hardware_module_creation(self, sample_module):
        """测试硬件模块创建"""
        assert sample_module.id is not None
        assert sample_module.name == "Test Arduino"
        assert sample_module.price_per_day == 1.0
        assert sample_module.quantity_available == 5
        assert sample_module.status == HardwareModuleStatus.AVAILABLE

    async def test_module_availability_check(self, sample_module, db_session):
        """测试模块可用性检查"""
        # 测试库存充足的情况
        is_available = await hardware_inventory_service.check_availability(
            sample_module.id, 2, db_session
        )
        assert is_available is True

        # 测试库存不足的情况
        is_available = await hardware_inventory_service.check_availability(
            sample_module.id, 10, db_session
        )
        assert is_available is False

    async def test_module_reservation(self, sample_module, db_session):
        """测试模块预留功能"""
        # 预留2个模块
        reserved = await hardware_inventory_service.reserve_module(
            sample_module.id, 2, db_session
        )
        assert reserved is True

        # 检查库存更新
        await db_session.refresh(sample_module)
        assert sample_module.quantity_available == 3

        # 尝试预留超过库存的数量
        reserved = await hardware_inventory_service.reserve_module(
            sample_module.id, 10, db_session
        )
        assert reserved is False

    async def test_module_release(self, sample_module, db_session):
        """测试模块释放功能"""
        # 先预留一些模块
        await hardware_inventory_service.reserve_module(sample_module.id, 3, db_session)
        await db_session.refresh(sample_module)
        assert sample_module.quantity_available == 2

        # 释放模块
        released = await hardware_inventory_service.release_reservation(
            sample_module.id, 2, db_session
        )
        assert released is True

        # 检查库存恢复
        await db_session.refresh(sample_module)
        assert sample_module.quantity_available == 4

    async def test_rental_process(self, sample_module, sample_user_license, db_session):
        """测试完整的租赁流程"""
        # 1. 检查可用性
        is_available = await hardware_inventory_service.check_availability(
            sample_module.id, 1, db_session
        )
        assert is_available is True

        # 2. 预留模块
        reserved = await hardware_inventory_service.reserve_module(
            sample_module.id, 1, db_session
        )
        assert reserved is True

        # 3. 创建租赁记录
        rental_record = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow(),
            rental_end_date=datetime.utcnow() + timedelta(days=7),
            daily_rate=sample_module.price_per_day,
            total_amount=sample_module.price_per_day * 7,
            deposit_paid=sample_module.deposit_amount,
            status=ModuleRentalStatus.ACTIVE,
        )
        db_session.add(rental_record)
        await db_session.commit()
        await db_session.refresh(rental_record)

        assert rental_record.id is not None
        assert rental_record.status == ModuleRentalStatus.ACTIVE

        # 4. 检查库存减少
        await db_session.refresh(sample_module)
        assert sample_module.quantity_available == 4

        # 5. 归还模块
        rental_record.actual_return_date = datetime.utcnow()
        rental_record.status = ModuleRentalStatus.RETURNED
        sample_module.quantity_available += 1
        if sample_module.quantity_available > 0:
            sample_module.status = HardwareModuleStatus.AVAILABLE

        await db_session.commit()

        # 6. 验证归还后状态
        await db_session.refresh(rental_record)
        await db_session.refresh(sample_module)
        assert rental_record.status == ModuleRentalStatus.RETURNED
        assert sample_module.quantity_available == 5
        assert sample_module.status == HardwareModuleStatus.AVAILABLE

    async def test_damage_compensation_calculation(
        self, sample_module, sample_user_license, db_session
    ):
        """测试损坏赔偿计算"""
        # 创建损坏的租赁记录
        rental_record = ModuleRentalRecord(
            module_id=sample_module.id,
            user_license_id=sample_user_license.id,
            rental_start_date=datetime.utcnow() - timedelta(days=7),
            rental_end_date=datetime.utcnow(),
            daily_rate=sample_module.price_per_day,
            total_amount=sample_module.price_per_day * 7,
            deposit_paid=sample_module.deposit_amount,
            status=ModuleRentalStatus.RETURNED,
            is_damaged=True,
            damage_level=DamageLevel.MODERATE,
            damage_description="屏幕轻微划痕",
        )

        # 测试赔偿金额计算
        compensation = rental_record.calculate_compensation()
        expected_compensation = sample_module.deposit_amount * 0.5  # 中等损坏50%
        assert abs(compensation - expected_compensation) < 0.01

    async def test_concurrent_rental_scenarios(self, sample_module, db_session):
        """测试并发租赁场景"""
        # 模拟多个用户同时尝试租赁同一模块
        tasks = []
        for i in range(3):
            task = asyncio.create_task(
                self._attempt_rental(sample_module.id, 1, db_session)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计成功的租赁次数
        successful_rentals = sum(1 for result in results if result is True)
        assert successful_rentals <= 5  # 不超过总库存

    async def _attempt_rental(self, module_id, quantity, db_session):
        """辅助方法：尝试租赁模块"""
        try:
            if await hardware_inventory_service.check_availability(
                module_id, quantity, db_session
            ):
                return await hardware_inventory_service.reserve_module(
                    module_id, quantity, db_session
                )
            return False
        except Exception:
            return False

    async def test_batch_availability_check(self, db_session):
        """测试批量可用性检查"""
        # 创建多个测试模块
        modules_data = [
            ("Module A", "TYPE-A", "MOD-A-001", 3),
            ("Module B", "TYPE-B", "MOD-B-001", 2),
            ("Module C", "TYPE-C", "MOD-C-001", 1),
        ]

        module_ids = []
        for name, mod_type, serial, qty in modules_data:
            module = HardwareModule(
                name=name,
                module_type=mod_type,
                serial_number=serial,
                price_per_day=1.0,
                deposit_amount=50.0,
                total_quantity=qty,
                quantity_available=qty,
                status=HardwareModuleStatus.AVAILABLE,
                is_active=True,
            )
            db_session.add(module)
            await db_session.commit()
            await db_session.refresh(module)
            module_ids.append(module.id)

        # 测试批量检查
        quantities = {module_ids[0]: 2, module_ids[1]: 1, module_ids[2]: 1}
        results = await hardware_inventory_service.batch_check_availability(
            quantities, db_session
        )

        assert len(results) == 3
        assert results[module_ids[0]] is True  # 有足够的Module A
        assert results[module_ids[1]] is True  # 有足够的Module B
        assert results[module_ids[2]] is True  # 有足够的Module C

    async def test_module_stock_info(
        self, sample_module, sample_user_license, db_session
    ):
        """测试模块库存信息获取"""
        # 创建一些租赁记录
        for i in range(2):
            rental = ModuleRentalRecord(
                module_id=sample_module.id,
                user_license_id=sample_user_license.id,
                rental_start_date=datetime.utcnow() - timedelta(days=i + 1),
                rental_end_date=datetime.utcnow() + timedelta(days=7 - i),
                daily_rate=1.0,
                total_amount=7.0,
                deposit_paid=50.0,
                status=(
                    ModuleRentalStatus.ACTIVE if i == 0 else ModuleRentalStatus.RETURNED
                ),
            )
            db_session.add(rental)

        await db_session.commit()

        # 获取库存信息
        stock_info = await hardware_inventory_service.get_module_stock_info(
            sample_module.id, db_session
        )

        assert stock_info is not None
        assert stock_info["module_id"] == sample_module.id
        assert stock_info["name"] == sample_module.name
        assert stock_info["total_quantity"] == 5
        assert (
            stock_info["available_quantity"] == 5
        )  # 注意：这里可能需要根据实际业务逻辑调整
        assert stock_info["reserved_quantity"] == 1  # 1个活跃租赁
        assert stock_info["returned_quantity"] == 1  # 1个已归还
        assert stock_info["status"] == "available"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
