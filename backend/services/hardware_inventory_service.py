"""
硬件库存管理服务
处理硬件模块的库存检查、预留、释放等操作
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from models.hardware_module import HardwareModule, HardwareModuleStatus
from utils.logger import setup_logger

logger = setup_logger("INFO")


class HardwareInventoryService:
    """硬件库存管理服务类"""

    async def check_availability(
        self, module_id: int, quantity: int, db: AsyncSession
    ) -> bool:
        """
        检查模块库存是否充足

        Args:
            module_id: 硬件模块ID
            quantity: 需要的数量
            db: 数据库会话

        Returns:
            bool: 是否有足够库存
        """
        try:
            query = select(HardwareModule).filter(
                HardwareModule.id == module_id,
                HardwareModule.status == HardwareModuleStatus.AVAILABLE,
                HardwareModule.quantity_available >= quantity,
                HardwareModule.is_active == True,
            )

            result = await db.execute(query)
            module = result.scalar_one_or_none()

            return module is not None

        except Exception as e:
            logger.error(f"检查库存可用性失败: {str(e)}")
            return False

    async def reserve_module(
        self, module_id: int, quantity: int, db: AsyncSession
    ) -> bool:
        """
        预留指定数量的模块

        Args:
            module_id: 硬件模块ID
            quantity: 预留数量
            db: 数据库会话

        Returns:
            bool: 预留是否成功
        """
        try:
            query = select(HardwareModule).filter(HardwareModule.id == module_id)
            result = await db.execute(query)
            module = result.scalar_one_or_none()

            if not module:
                return False

            # 检查是否有足够库存
            if module.quantity_available < quantity:
                return False

            # 更新库存
            module.quantity_available -= quantity
            if module.quantity_available == 0:
                module.status = HardwareModuleStatus.RENTED

            await db.commit()
            logger.info(f"成功预留模块 {module_id} 数量 {quantity}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"预留模块失败: {str(e)}")
            return False

    async def release_reservation(
        self, module_id: int, quantity: int, db: AsyncSession
    ) -> bool:
        """
        释放预留的模块

        Args:
            module_id: 硬件模块ID
            quantity: 释放数量
            db: 数据库会话

        Returns:
            bool: 释放是否成功
        """
        try:
            query = select(HardwareModule).filter(HardwareModule.id == module_id)
            result = await db.execute(query)
            module = result.scalar_one_or_none()

            if not module:
                return False

            # 更新库存
            module.quantity_available += quantity
            if (
                module.quantity_available > 0
                and module.status == HardwareModuleStatus.RENTED
            ):
                module.status = HardwareModuleStatus.AVAILABLE

            await db.commit()
            logger.info(f"成功释放模块 {module_id} 数量 {quantity}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"释放模块失败: {str(e)}")
            return False

    async def get_module_stock_info(
        self, module_id: int, db: AsyncSession
    ) -> Optional[dict]:
        """
        获取模块库存信息

        Args:
            module_id: 硬件模块ID
            db: 数据库会话

        Returns:
            dict: 库存信息字典
        """
        try:
            query = select(HardwareModule).filter(HardwareModule.id == module_id)
            query = query.options(selectinload(HardwareModule.rental_records))
            result = await db.execute(query)
            module = result.scalar_one_or_none()

            if not module:
                return None

            # 计算各种状态的数量
            total_rented = len(
                [r for r in module.rental_records if r.status == "ACTIVE"]
            )
            total_returned = len(
                [
                    r
                    for r in module.rental_records
                    if r.status in ["RETURNED", "COMPLETED"]
                ]
            )
            total_damaged = len([r for r in module.rental_records if r.is_damaged])

            return {
                "module_id": module.id,
                "name": module.name,
                "total_quantity": module.total_quantity,
                "available_quantity": module.quantity_available,
                "reserved_quantity": total_rented,
                "returned_quantity": total_returned,
                "damaged_quantity": total_damaged,
                "status": module.status.value,
                "is_active": module.is_active,
            }

        except Exception as e:
            logger.error(f"获取库存信息失败: {str(e)}")
            return None

    async def batch_check_availability(
        self, module_quantities: dict, db: AsyncSession
    ) -> dict:
        """
        批量检查多个模块的库存

        Args:
            module_quantities: {module_id: quantity} 字典
            db: 数据库会话

        Returns:
            dict: {module_id: bool} 可用性检查结果
        """
        try:
            results = {}

            for module_id, quantity in module_quantities.items():
                is_available = await self.check_availability(module_id, quantity, db)
                results[module_id] = is_available

            return results

        except Exception as e:
            logger.error(f"批量检查库存失败: {str(e)}")
            return {}


# 创建全局实例
hardware_inventory_service = HardwareInventoryService()
