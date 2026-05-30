"""
硬件模块租赁系统API路由
提供硬件模块管理和租赁相关API端点
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from middleware.auth import get_current_user
from models.hardware_module import (
    DamageLevel,
    HardwareModule,
    HardwareModuleCreate,
    HardwareModuleResponse,
    HardwareModuleStatus,
    HardwareModuleUpdate,
    ModuleRentalRecord,
    ModuleRentalRecordResponse,
    ModuleRentalStatus,
    RentModuleRequest,
    ReturnModuleRequest,
)
from models.user import User
from models.user_license import HardwareRentalSummary, UserLicense
from services.hardware_inventory_service import hardware_inventory_service
from utils.database import get_db
from utils.logger import setup_logger

router = APIRouter(tags=["硬件模块"])
logger = setup_logger("INFO")


@router.get("/api/v1/hardware/modules", response_model=List[HardwareModuleResponse])
async def list_hardware_modules(
    module_type: Optional[str] = Query(None, description="模块类型筛选"),
    status: Optional[HardwareModuleStatus] = Query(None, description="状态筛选"),
    available_only: bool = Query(False, description="只显示可租赁的模块"),
    db: AsyncSession = Depends(get_db),
):
    """
    列出硬件模块

    Args:
        module_type: 模块类型筛选
        status: 状态筛选
        available_only: 只显示可租赁的模块
        db: 数据库会话

    Returns:
        List[HardwareModuleResponse]: 硬件模块列表
    """
    try:
        logger.info("获取硬件模块列表")

        query = select(HardwareModule)

        # 应用筛选条件
        if module_type:
            query = query.filter(HardwareModule.module_type == module_type)

        if status:
            query = query.filter(HardwareModule.status == status)

        if available_only:
            query = query.filter(
                HardwareModule.status == HardwareModuleStatus.AVAILABLE,
                HardwareModule.quantity_available > 0,
                HardwareModule.is_active == True,
            )

        # 预加载关联数据
        query = query.options(selectinload(HardwareModule.rental_records))

        result = await db.execute(query)
        modules = result.scalars().all()

        logger.info(f"找到 {len(modules)} 个硬件模块")
        return [HardwareModuleResponse.from_orm(module) for module in modules]

    except Exception as e:
        logger.error(f"获取硬件模块列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模块列表失败: {str(e)}")


@router.get(
    "/api/v1/hardware/modules/{module_id}", response_model=HardwareModuleResponse
)
async def get_hardware_module(
    module_id: int = Path(..., description="硬件模块ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取单个硬件模块详情

    Args:
        module_id: 硬件模块ID
        db: 数据库会话

    Returns:
        HardwareModuleResponse: 硬件模块详情
    """
    try:
        logger.info(f"获取硬件模块详情: {module_id}")

        query = select(HardwareModule).filter(HardwareModule.id == module_id)
        query = query.options(selectinload(HardwareModule.rental_records))

        result = await db.execute(query)
        module = result.scalar_one_or_none()

        if not module:
            raise HTTPException(status_code=404, detail="硬件模块不存在")

        return HardwareModuleResponse.from_orm(module)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取硬件模块详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取模块详情失败: {str(e)}")


@router.post("/api/v1/hardware/modules", response_model=HardwareModuleResponse)
async def create_hardware_module(
    module_data: HardwareModuleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的硬件模块

    Args:
        module_data: 硬件模块创建数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        HardwareModuleResponse: 创建的硬件模块
    """
    try:
        logger.info(f"创建硬件模块: {module_data.name}")

        # 检查序列号是否已存在
        existing_query = select(HardwareModule).filter(
            HardwareModule.serial_number == module_data.serial_number
        )
        result = await db.execute(existing_query)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="序列号已存在")

        # 创建新模块
        new_module = HardwareModule(**module_data.dict())
        db.add(new_module)
        await db.commit()
        await db.refresh(new_module)

        logger.info(f"硬件模块创建成功: {new_module.id}")
        return HardwareModuleResponse.from_orm(new_module)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建硬件模块失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建模块失败: {str(e)}")


@router.put(
    "/api/v1/hardware/modules/{module_id}", response_model=HardwareModuleResponse
)
async def update_hardware_module(
    module_data: HardwareModuleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    module_id: int = Path(..., description="硬件模块ID"),
):
    """
    更新硬件模块信息

    Args:
        module_id: 硬件模块ID
        module_data: 硬件模块更新数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        HardwareModuleResponse: 更新后的硬件模块
    """
    try:
        logger.info(f"更新硬件模块: {module_id}")

        # 获取模块
        query = select(HardwareModule).filter(HardwareModule.id == module_id)
        result = await db.execute(query)
        module = result.scalar_one_or_none()

        if not module:
            raise HTTPException(status_code=404, detail="硬件模块不存在")

        # 更新字段
        update_data = module_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(module, field, value)

        await db.commit()
        await db.refresh(module)

        logger.info(f"硬件模块更新成功: {module_id}")
        return HardwareModuleResponse.from_orm(module)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新硬件模块失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新模块失败: {str(e)}")


@router.delete("/api/v1/hardware/modules/{module_id}")
async def delete_hardware_module(
    module_id: int = Path(..., description="硬件模块ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    删除硬件模块

    Args:
        module_id: 硬件模块ID
        current_user: 当前用户
        db: 数据库会话

    Returns:
        dict: 删除结果
    """
    try:
        logger.info(f"删除硬件模块: {module_id}")

        # 获取模块
        query = select(HardwareModule).filter(HardwareModule.id == module_id)
        result = await db.execute(query)
        module = result.scalar_one_or_none()

        if not module:
            raise HTTPException(status_code=404, detail="硬件模块不存在")

        # 检查是否有活跃的租赁记录
        active_rentals = [
            r for r in module.rental_records if r.status == ModuleRentalStatus.ACTIVE
        ]
        if active_rentals:
            raise HTTPException(status_code=400, detail="存在活跃租赁记录，无法删除")

        # 删除模块
        await db.delete(module)
        await db.commit()

        logger.info(f"硬件模块删除成功: {module_id}")
        return {"message": "硬件模块删除成功"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除硬件模块失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除模块失败: {str(e)}")


@router.post(
    "/api/v1/hardware/modules/{module_id}/rent",
    response_model=ModuleRentalRecordResponse,
)
async def rent_hardware_module(
    request: RentModuleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    module_id: int = Path(..., description="硬件模块ID"),
):
    """
    租赁硬件模块

    Args:
        module_id: 硬件模块ID
        request: 租赁请求数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ModuleRentalRecordResponse: 租赁记录
    """
    try:
        logger.info(f"用户 {current_user.id} 请求租赁模块 {module_id}")

        # 获取模块和用户许可证
        module_query = select(HardwareModule).filter(HardwareModule.id == module_id)
        license_query = select(UserLicense).filter(
            UserLicense.id == request.user_license_id
        )

        module_result = await db.execute(module_query)
        license_result = await db.execute(license_query)

        module = module_result.scalar_one_or_none()
        user_license = license_result.scalar_one_or_none()

        if not module:
            raise HTTPException(status_code=404, detail="硬件模块不存在")
        if not user_license:
            raise HTTPException(status_code=404, detail="用户许可证不存在")

        # 检查模块是否可租赁
        if not module.is_available:
            raise HTTPException(status_code=400, detail="模块不可租赁")

        # 检查用户是否还能租赁更多硬件
        if not user_license.can_rent_more_hardware:
            raise HTTPException(status_code=400, detail="已达租赁限额")

        # 检查库存
        if not await hardware_inventory_service.check_availability(module_id, 1, db):
            raise HTTPException(status_code=400, detail="库存不足")

        # 预留模块
        if not await hardware_inventory_service.reserve_module(module_id, 1, db):
            raise HTTPException(status_code=400, detail="模块预留失败")

        # 创建租赁记录
        rental_record = ModuleRentalRecord(
            module_id=module_id,
            user_license_id=request.user_license_id,
            rental_start_date=datetime.utcnow(),
            rental_end_date=datetime.utcnow() + timedelta(days=request.rental_days),
            daily_rate=module.price_per_day,
            total_amount=module.price_per_day * request.rental_days,
            deposit_paid=module.deposit_amount,
            status=ModuleRentalStatus.ACTIVE,
        )

        db.add(rental_record)
        await db.commit()
        await db.refresh(rental_record)

        # 更新模块状态
        module.quantity_available -= 1
        if module.quantity_available == 0:
            module.status = HardwareModuleStatus.RENTED
        await db.commit()

        logger.info(f"模块租赁成功: 记录ID {rental_record.id}")
        return ModuleRentalRecordResponse.from_orm(rental_record)

    except HTTPException:
        # 发生错误时释放预留
        await hardware_inventory_service.release_reservation(module_id, 1, db)
        raise
    except Exception as e:
        await db.rollback()
        await hardware_inventory_service.release_reservation(module_id, 1, db)
        logger.error(f"模块租赁失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"租赁失败: {str(e)}")


@router.post(
    "/api/v1/hardware/modules/{module_id}/return",
    response_model=ModuleRentalRecordResponse,
)
async def return_hardware_module(
    module_id: int = Path(..., description="硬件模块 ID"),
    request: ReturnModuleRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    归还硬件模块

    Args:
        module_id: 硬件模块ID
        request: 归还请求数据
        current_user: 当前用户
        db: 数据库会话

    Returns:
        ModuleRentalRecordResponse: 更新后的租赁记录
    """
    try:
        logger.info(f"用户 {current_user.id} 归还模块 {module_id}")

        # 查找活跃的租赁记录
        query = select(ModuleRentalRecord).filter(
            ModuleRentalRecord.module_id == module_id,
            ModuleRentalRecord.status == ModuleRentalStatus.ACTIVE,
        )
        query = query.options(selectinload(ModuleRentalRecord.module))

        result = await db.execute(query)
        rental_record = result.scalar_one_or_none()

        if not rental_record:
            raise HTTPException(status_code=404, detail="未找到活跃的租赁记录")

        # 更新归还信息
        rental_record.actual_return_date = (
            request.actual_return_date or datetime.utcnow()
        )
        rental_record.is_damaged = request.is_damaged
        rental_record.damage_level = request.damage_level
        rental_record.damage_description = request.damage_description

        # 计算赔偿金额
        if request.is_damaged and request.damage_level:
            rental_record.compensation_amount = rental_record.calculate_compensation()

        # 更新状态
        rental_record.status = ModuleRentalStatus.RETURNED

        # 更新模块库存
        rental_record.module.quantity_available += 1
        if rental_record.module.quantity_available > 0:
            rental_record.module.status = HardwareModuleStatus.AVAILABLE

        await db.commit()
        await db.refresh(rental_record)

        logger.info(f"模块归还处理完成: 记录ID {rental_record.id}")
        return ModuleRentalRecordResponse.from_orm(rental_record)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"模块归还失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"归还失败: {str(e)}")


@router.get(
    "/api/v1/hardware/modules/user/{user_license_id}/rentals",
    response_model=List[ModuleRentalRecordResponse],
)
async def get_user_rental_history(
    user_license_id: int = Path(..., description="用户许可证ID"),
    status: Optional[ModuleRentalStatus] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户租赁历史

    Args:
        user_license_id: 用户许可证ID
        status: 状态筛选
        db: 数据库会话

    Returns:
        List[ModuleRentalRecordResponse]: 租赁记录列表
    """
    try:
        logger.info(f"获取用户 {user_license_id} 的租赁历史")

        query = select(ModuleRentalRecord).filter(
            ModuleRentalRecord.user_license_id == user_license_id
        )

        if status:
            query = query.filter(ModuleRentalRecord.status == status)

        query = query.options(selectinload(ModuleRentalRecord.module)).order_by(
            ModuleRentalRecord.created_at.desc()
        )

        result = await db.execute(query)
        rentals = result.scalars().all()

        return [ModuleRentalRecordResponse.from_orm(rental) for rent in rentals]

    except Exception as e:
        logger.error(f"获取租赁历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取租赁历史失败: {str(e)}")


@router.get(
    "/api/v1/hardware/modules/user/{user_license_id}/summary",
    response_model=HardwareRentalSummary,
)
async def get_user_rental_summary(
    user_license_id: int = Path(..., description="用户许可证ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取用户租赁摘要信息

    Args:
        user_license_id: 用户许可证ID
        db: 数据库会话

    Returns:
        HardwareRentalSummary: 租赁摘要
    """
    try:
        logger.info(f"获取用户 {user_license_id} 的租赁摘要")

        # 获取用户许可证
        license_query = select(UserLicense).filter(UserLicense.id == user_license_id)
        license_query = license_query.options(
            selectinload(UserLicense.hardware_rentals)
        )

        result = await db.execute(license_query)
        user_license = result.scalar_one_or_none()

        if not user_license:
            raise HTTPException(status_code=404, detail="用户许可证不存在")

        # 计算摘要信息
        total_rentals = len(user_license.hardware_rentals)
        active_rentals = len(user_license.active_hardware_rentals)

        # 计算逾期租赁
        overdue_rentals = sum(
            1 for record in user_license.hardware_rentals if record.is_overdue
        )

        # 计算总花费和待退押金
        total_spent = sum(
            record.total_amount
            for record in user_license.hardware_rentals
            if record.status
            in [ModuleRentalStatus.COMPLETED, ModuleRentalStatus.RETURNED]
        )
        pending_deposit = sum(
            record.deposit_paid - record.deposit_refunded
            for record in user_license.hardware_rentals
            if record.status == ModuleRentalStatus.ACTIVE
        )

        summary = HardwareRentalSummary(
            total_rentals=total_rentals,
            active_rentals=active_rentals,
            overdue_rentals=overdue_rentals,
            total_spent=total_spent,
            pending_deposit=pending_deposit,
            rental_limit=user_license.hardware_rental_limit,
            can_rent_more=user_license.can_rent_more_hardware,
        )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取租赁摘要失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取租赁摘要失败: {str(e)}")
