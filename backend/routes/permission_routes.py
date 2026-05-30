"""
权限管理API接口
提供权限、角色管理及相关操作的RESTful API
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from models.permission import Permission, Role, UserRoleAssignment
from models.user import User, UserRole
from routes.auth_routes import get_current_user
from services.permission_service import permission_service
from utils.database import get_db
from utils.decorators import admin_required, require_permission

router = APIRouter(prefix="/api/v1/permissions", tags=["权限管理"])


# Pydantic模型定义
class PermissionCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    category: str
    action: str
    resource: Optional[str] = None


class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    action: Optional[str] = None
    resource: Optional[str] = None
    is_active: Optional[bool] = None


class RoleCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    is_system: bool = False
    priority: int = 0
    permission_codes: List[str] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    permission_codes: Optional[List[str]] = None


class UserRoleAssignmentCreate(BaseModel):
    user_id: int
    role_code: str
    expires_at: Optional[datetime] = None
    reason: Optional[str] = None


class PermissionCheckRequest(BaseModel):
    user_id: int
    permission_codes: List[str]


class BatchPermissionCheckRequest(BaseModel):
    checks: List[PermissionCheckRequest]


# 权限管理API
@router.get("/permissions", summary="获取权限列表")
@require_permission("system.config")
async def list_permissions(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取权限列表"""
    from sqlalchemy import select

    stmt = select(Permission)

    # 添加过滤条件
    filters = []
    if category:
        filters.append(Permission.category == category)
    if is_active is not None:
        filters.append(Permission.is_active == is_active)

    if filters:
        stmt = stmt.filter(*filters)

    # 分页和排序
    stmt = stmt.offset(offset).limit(limit).order_by(Permission.created_at.desc())

    result = await db.execute(stmt)
    permissions = result.scalars().all()

    return {
        "permissions": [perm.to_dict() for perm in permissions],
        "total": len(permissions),
    }


@router.post("/permissions", summary="创建权限")
@require_permission("system.config")
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新权限"""
    from sqlalchemy import select

    # 检查权限代码是否已存在
    stmt = select(Permission).filter(Permission.code == permission_data.code)
    result = await db.execute(stmt)
    existing_permission = result.scalar_one_or_none()

    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"权限代码 {permission_data.code} 已存在",
        )

    # 创建权限
    permission = Permission(
        name=permission_data.name,
        code=permission_data.code,
        description=permission_data.description,
        category=permission_data.category,
        action=permission_data.action,
        resource=permission_data.resource,
    )

    db.add(permission)
    await db.flush()

    # 记录日志
    await permission_service.log_permission_change(
        user_id=current_user.id,
        target_user_id=None,
        action_type="create_permission",
        resource_type="permission",
        resource_id=permission.id,
        permission_code=permission.code,
        description=f"创建权限: {permission.name}",
        db=db,
    )

    await db.commit()

    return {"message": "权限创建成功", "permission": permission.to_dict()}


@router.put("/permissions/{permission_id}", summary="更新权限")
@require_permission("system.config")
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新权限信息"""
    from sqlalchemy import select

    # 获取权限
    stmt = select(Permission).filter(Permission.id == permission_id)
    result = await db.execute(stmt)
    permission = result.scalar_one_or_none()

    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="权限不存在")

    # 记录原始状态
    old_values = permission.to_dict()

    # 更新字段
    update_data = permission_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(permission, field, value)

    await db.flush()

    # 记录日志
    await permission_service.log_permission_change(
        user_id=current_user.id,
        target_user_id=None,
        action_type="update_permission",
        resource_type="permission",
        resource_id=permission.id,
        permission_code=permission.code,
        old_value=str(old_values),
        new_value=str(permission.to_dict()),
        description=f"更新权限: {permission.name}",
        db=db,
    )

    await db.commit()

    return {"message": "权限更新成功", "permission": permission.to_dict()}


@router.delete("/permissions/{permission_id}", summary="删除权限")
@require_permission("system.config")
async def delete_permission(
    permission_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除权限"""
    from sqlalchemy import select

    # 获取权限
    stmt = select(Permission).filter(Permission.id == permission_id)
    result = await db.execute(stmt)
    permission = result.scalar_one_or_none()

    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="权限不存在")

    permission_code = permission.code
    permission_name = permission.name

    # 删除权限
    await db.delete(permission)
    await db.flush()

    # 记录日志
    await permission_service.log_permission_change(
        user_id=current_user.id,
        target_user_id=None,
        action_type="delete_permission",
        resource_type="permission",
        resource_id=permission_id,
        permission_code=permission_code,
        description=f"删除权限: {permission_name}",
        db=db,
    )

    await db.commit()

    return {"message": "权限删除成功"}


# 角色管理API
@router.get("/roles", summary="获取角色列表")
@require_permission("system.config")
async def list_roles(
    is_system: Optional[bool] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取角色列表"""
    from sqlalchemy import select

    stmt = select(Role)

    # 添加过滤条件
    filters = []
    if is_system is not None:
        filters.append(Role.is_system == is_system)
    if is_active is not None:
        filters.append(Role.is_active == is_active)

    if filters:
        stmt = stmt.filter(*filters)

    # 分页和排序
    stmt = (
        stmt.offset(offset)
        .limit(limit)
        .order_by(Role.priority.desc(), Role.created_at.desc())
    )

    result = await db.execute(stmt)
    roles = result.scalars().all()

    # 获取每个角色的权限数量
    role_details = []
    for role in roles:
        role_dict = role.to_dict()
        # 获取权限数量
        from models.permission import role_permissions

        perm_count_stmt = select(role_permissions).filter(
            role_permissions.c.role_id == role.id
        )
        perm_count_result = await db.execute(perm_count_stmt)
        role_dict["permission_count"] = len(perm_count_result.fetchall())
        role_details.append(role_dict)

    return {"roles": role_details, "total": len(role_details)}


@router.post("/roles", summary="创建角色")
@require_permission("system.config")
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新角色"""
    from sqlalchemy import select

    # 检查角色代码是否已存在
    stmt = select(Role).filter(Role.code == role_data.code)
    result = await db.execute(stmt)
    existing_role = result.scalar_one_or_none()

    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"角色代码 {role_data.code} 已存在",
        )

    # 创建角色
    role = Role(
        name=role_data.name,
        code=role_data.code,
        description=role_data.description,
        is_system=role_data.is_system,
        priority=role_data.priority,
    )

    db.add(role)
    await db.flush()

    # 分配权限
    if role_data.permission_codes:
        # 获取权限ID
        perm_stmt = select(Permission).filter(
            Permission.code.in_(role_data.permission_codes)
        )
        perm_result = await db.execute(perm_stmt)
        permissions = perm_result.scalars().all()

        # 创建角色权限关联
        from models.permission import role_permissions

        role_perm_values = [
            {"role_id": role.id, "permission_id": perm.id} for perm in permissions
        ]
        if role_perm_values:
            await db.execute(role_permissions.insert(), role_perm_values)

    # 记录日志
    await permission_service.log_permission_change(
        user_id=current_user.id,
        target_user_id=None,
        action_type="create_role",
        resource_type="role",
        resource_id=role.id,
        role_code=role.code,
        description=f"创建角色: {role.name}",
        db=db,
    )

    await db.commit()

    return {"message": "角色创建成功", "role": role.to_dict()}


@router.get("/roles/{role_id}/permissions", summary="获取角色权限")
@require_permission("system.config")
async def get_role_permissions(
    role_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取角色的所有权限"""
    from sqlalchemy import select

    # 获取角色
    role_stmt = select(Role).filter(Role.id == role_id)
    role_result = await db.execute(role_stmt)
    role = role_result.scalar_one_or_none()

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    # 获取角色权限
    from models.permission import role_permissions

    perm_stmt = (
        select(Permission)
        .join(role_permissions)
        .filter(role_permissions.c.role_id == role_id)
    )
    perm_result = await db.execute(perm_stmt)
    permissions = perm_result.scalars().all()

    return {
        "role_id": role_id,
        "role_name": role.name,
        "permissions": [perm.to_dict() for perm in permissions],
    }


@router.put("/roles/{role_id}/permissions", summary="更新角色权限")
@require_permission("system.config")
async def update_role_permissions(
    role_id: int,
    permission_codes: List[str],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新角色的权限分配"""
    from sqlalchemy import select

    # 获取角色
    role_stmt = select(Role).filter(Role.id == role_id)
    role_result = await db.execute(role_stmt)
    role = role_result.scalar_one_or_none()

    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    # 获取权限ID
    perm_stmt = select(Permission).filter(Permission.code.in_(permission_codes))
    perm_result = await db.execute(perm_stmt)
    permissions = perm_result.scalars().all()
    permission_ids = [perm.id for perm in permissions]

    # 更新角色权限关联
    from models.permission import role_permissions

    # 先删除现有权限关联
    delete_stmt = role_permissions.delete().where(role_permissions.c.role_id == role_id)
    await db.execute(delete_stmt)

    # 添加新的权限关联
    if permission_ids:
        role_perm_values = [
            {"role_id": role_id, "permission_id": perm_id} for perm_id in permission_ids
        ]
        await db.execute(role_permissions.insert(), role_perm_values)

    # 记录日志
    await permission_service.log_permission_change(
        user_id=current_user.id,
        target_user_id=None,
        action_type="update_role_permissions",
        resource_type="role",
        resource_id=role_id,
        role_code=role.code,
        description=f"更新角色 {role.name} 的权限分配",
        db=db,
    )

    await db.commit()

    return {
        "message": "角色权限更新成功",
        "role_id": role_id,
        "permission_count": len(permission_ids),
    }


# 用户角色管理API
@router.get("/users/{user_id}/roles", summary="获取用户角色")
@require_permission("user.read")
async def get_user_roles(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的所有角色分配"""
    from sqlalchemy import select

    # 检查用户是否存在
    user_stmt = select(User).filter(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 获取用户角色分配
    assignment_stmt = (
        select(UserRoleAssignment)
        .filter(UserRoleAssignment.user_id == user_id)
        .order_by(UserRoleAssignment.assigned_at.desc())
    )

    assignment_result = await db.execute(assignment_stmt)
    assignments = assignment_result.scalars().all()

    # 获取角色详细信息
    role_details = []
    for assignment in assignments:
        role_stmt = select(Role).filter(Role.id == assignment.role_id)
        role_result = await db.execute(role_stmt)
        role = role_result.scalar_one_or_none()
        if role:
            assignment_dict = assignment.to_dict()
            assignment_dict["role"] = role.to_dict()
            role_details.append(assignment_dict)

    return {"user_id": user_id, "username": user.username, "roles": role_details}


@router.post("/user-roles", summary="为用户分配角色")
@require_permission("user.manage_roles")
async def assign_user_role(
    assignment_data: UserRoleAssignmentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """为用户分配角色"""
    try:
        assignment = await permission_service.assign_role_to_user(
            user_id=assignment_data.user_id,
            role_code=assignment_data.role_code,
            assigned_by=current_user.id,
            expires_at=assignment_data.expires_at,
            reason=assignment_data.reason,
            db=db,
        )

        return {"message": "角色分配成功", "assignment": assignment.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"角色分配失败: {str(e)}",
        )


@router.delete("/user-roles/{assignment_id}", summary="撤销用户角色分配")
@require_permission("user.manage_roles")
async def revoke_user_role(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """撤销用户角色分配"""
    from sqlalchemy import select

    # 获取分配记录
    stmt = select(UserRoleAssignment).filter(UserRoleAssignment.id == assignment_id)
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="角色分配记录不存在"
        )

    # 撤销分配
    assignment.is_active = False
    assignment.revoked_at = datetime.utcnow()
    assignment.revoked_by = current_user.id

    # 记录日志
    await permission_service.log_permission_change(
        user_id=current_user.id,
        target_user_id=assignment.user_id,
        action_type="revoke_role_assignment",
        resource_type="role_assignment",
        resource_id=assignment_id,
        role_code=assignment.role.code if hasattr(assignment, "role") else None,
        description=f"撤销用户角色分配 #{assignment_id}",
        db=db,
    )

    await db.commit()

    return {"message": "角色分配撤销成功"}


# 权限检查API
@router.post("/check", summary="批量检查用户权限")
async def batch_check_permissions(
    check_request: BatchPermissionCheckRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量检查多个用户的权限"""
    results = []

    for check in check_request.checks:
        # 非管理员只能检查自己的权限
        if check.user_id != current_user.id and current_user.role != UserRole.ADMIN:
            results.append(
                {
                    "user_id": check.user_id,
                    "permission_codes": check.permission_codes,
                    "results": {code: False for code in check.permission_codes},
                    "error": "只能检查自己的权限",
                }
            )
            continue

        # 检查权限
        user_results = {}
        for perm_code in check.permission_codes:
            has_permission = await permission_service.check_user_permission(
                check.user_id, perm_code, db
            )
            user_results[perm_code] = has_permission

        results.append(
            {
                "user_id": check.user_id,
                "permission_codes": check.permission_codes,
                "results": user_results,
            }
        )

    return {"checks": results}


@router.get("/logs", summary="获取权限变更日志")
@admin_required()
async def get_permission_logs(
    user_id: Optional[int] = None,
    action_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    limit: int = Query(100, le=1000),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取权限变更日志"""
    logs = await permission_service.get_permission_logs(
        user_id=user_id,
        action_type=action_type,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
        db=db,
    )

    return {"logs": [log.to_dict() for log in logs], "total": len(logs)}


# 系统初始化API
@router.post("/initialize", summary="初始化权限系统")
@admin_required()
async def initialize_permission_system(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """初始化系统预定义权限和角色"""
    try:
        # 初始化权限
        permission_map = await permission_service.initialize_system_permissions(db)

        # 初始化角色
        role_map = await permission_service.initialize_system_roles(db)

        return {
            "message": "权限系统初始化成功",
            "permissions_created": len(permission_map),
            "roles_created": len(role_map),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化失败: {str(e)}",
        )
