"""
硬件模块API测试脚本
用于验证硬件模块功能是否正常工作
"""

import asyncio
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config.settings import Settings
from models.hardware_module import Base, HardwareModule, HardwareModuleStatus
from services.hardware_inventory_service import hardware_inventory_service


async def test_hardware_module_creation():
    """测试硬件模块创建功能"""
    print("=== 测试硬件模块创建功能 ===")

    # 创建测试数据库引擎
    settings = Settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        # 创建表
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        try:
            # 创建测试硬件模块
            test_module = HardwareModule(
                name="Arduino Uno R3",
                module_type="microcontroller",
                serial_number="ARD-UNO-001",
                price_per_day=1.0,  # 1元/天
                deposit_amount=50.0,
                total_quantity=10,
                quantity_available=10,
                description="标准Arduino Uno开发板",
                status=HardwareModuleStatus.AVAILABLE,
                is_active=True,
            )

            session.add(test_module)
            await session.commit()
            await session.refresh(test_module)

            print(f"✓ 成功创建硬件模块: {test_module.name} (ID: {test_module.id})")

            # 测试库存检查
            is_available = await hardware_inventory_service.check_availability(
                test_module.id, 1, session
            )
            print(f"✓ 库存检查结果: {'可用' if is_available else '不可用'}")

            # 测试预留功能
            reserved = await hardware_inventory_service.reserve_module(
                test_module.id, 1, session
            )
            print(f"✓ 模块预留结果: {'成功' if reserved else '失败'}")

            if reserved:
                # 检查预留后的库存
                stock_info = await hardware_inventory_service.get_module_stock_info(
                    test_module.id, session
                )
                print(
                    f"✓ 预留后库存信息: 可用 {stock_info['available_quantity']}, 总数 {stock_info['total_quantity']}"
                )

                # 测试释放功能
                released = await hardware_inventory_service.release_reservation(
                    test_module.id, 1, session
                )
                print(f"✓ 模块释放结果: {'成功' if released else '失败'}")

            # 清理测试数据
            await session.delete(test_module)
            await session.commit()
            print("✓ 测试数据清理完成")

        except Exception as e:
            print(f"✗ 测试失败: {str(e)}")
            await session.rollback()
        finally:
            await engine.dispose()


async def main():
    """主测试函数"""
    print("开始硬件模块API测试...")
    await test_hardware_module_creation()
    print("硬件模块API测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
