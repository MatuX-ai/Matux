"""
权限系统数据库迁移脚本
创建权限管理相关表结构
"""

import logging

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)


# 表结构定义
def create_permission_tables(metadata: MetaData) -> list:
    """创建权限系统相关表"""

    tables = []

    # 权限表
    permissions_table = Table(
        "permissions",
        metadata,
        Column("id", Integer, primary_key=True, index=True),
        Column("name", String(100), unique=True, index=True, nullable=False),
        Column("code", String(100), unique=True, index=True, nullable=False),
        Column("description", Text),
        Column("category", String(50), nullable=False),
        Column("action", String(50), nullable=False),
        Column("resource", String(100)),
        Column("is_active", Boolean, default=True),
        Column("created_at", DateTime(timezone=True), server_default=func.now()),
        Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
    )
    tables.append(permissions_table)

    # 角色表
    roles_table = Table(
        "roles",
        metadata,
        Column("id", Integer, primary_key=True, index=True),
        Column("name", String(50), unique=True, index=True, nullable=False),
        Column("code", String(50), unique=True, index=True, nullable=False),
        Column("description", Text),
        Column("is_system", Boolean, default=False),
        Column("is_active", Boolean, default=True),
        Column("priority", Integer, default=0),
        Column("created_at", DateTime(timezone=True), server_default=func.now()),
        Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
    )
    tables.append(roles_table)

    # 角色权限关联表
    role_permissions_table = Table(
        "role_permissions",
        metadata,
        Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
        Column(
            "permission_id", Integer, ForeignKey("permissions.id"), primary_key=True
        ),
        Column("created_at", DateTime(timezone=True), server_default=func.now()),
    )
    tables.append(role_permissions_table)

    # 用户角色关联表
    user_roles_table = Table(
        "user_roles",
        metadata,
        Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
        Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
        Column("assigned_by", Integer, ForeignKey("users.id")),
        Column("assigned_at", DateTime(timezone=True), server_default=func.now()),
        Column("expires_at", DateTime(timezone=True)),
        Column("is_active", Boolean, default=True),
    )
    tables.append(user_roles_table)

    # 用户角色分配详情表
    user_role_assignments_table = Table(
        "user_role_assignments",
        metadata,
        Column("id", Integer, primary_key=True, index=True),
        Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
        Column("role_id", Integer, ForeignKey("roles.id"), nullable=False),
        Column("assigned_by", Integer, ForeignKey("users.id")),
        Column("assigned_at", DateTime(timezone=True), server_default=func.now()),
        Column("expires_at", DateTime(timezone=True)),
        Column("revoked_at", DateTime(timezone=True)),
        Column("revoked_by", Integer, ForeignKey("users.id")),
        Column("is_active", Boolean, default=True),
        Column("reason", Text),
    )
    tables.append(user_role_assignments_table)

    # 权限变更日志表
    permission_logs_table = Table(
        "permission_logs",
        metadata,
        Column("id", Integer, primary_key=True, index=True),
        Column("user_id", Integer, ForeignKey("users.id")),
        Column("target_user_id", Integer, ForeignKey("users.id")),
        Column("action_type", String(50), nullable=False),
        Column("resource_type", String(50), nullable=False),
        Column("resource_id", Integer),
        Column("permission_code", String(100)),
        Column("role_code", String(50)),
        Column("old_value", Text),
        Column("new_value", Text),
        Column("ip_address", String(45)),
        Column("user_agent", Text),
        Column("description", Text),
        Column("created_at", DateTime(timezone=True), server_default=func.now()),
    )
    tables.append(permission_logs_table)

    return tables


def upgrade():
    """升级到最新版本"""
    from models.permission import Permission, Role
    from utils.database import engine

    logger.info("开始创建权限系统表...")

    # 创建权限相关表
    Permission.__table__.create(bind=engine, checkfirst=True)
    Role.__table__.create(bind=engine, checkfirst=True)
    tables_to_create = [
        "role_permissions",
        "user_roles",
        "user_role_assignments",
        "permission_logs",
    ]

    # 创建关联表
    metadata = MetaData()
    permission_tables = create_permission_tables(metadata)

    for table in permission_tables:
        if table.name in tables_to_create:
            table.create(bind=engine, checkfirst=True)
            logger.info(f"创建表: {table.name}")

    logger.info("权限系统表创建完成")


def downgrade():
    """降级到上一版本"""
    from utils.database import engine

    logger.info("开始删除权限系统表...")

    # 删除顺序很重要，先删除外键依赖的表
    tables_to_drop = [
        "permission_logs",
        "user_role_assignments",
        "user_roles",
        "role_permissions",
    ]

    metadata = MetaData()
    permission_tables = create_permission_tables(metadata)

    for table_name in tables_to_drop:
        table = next((t for t in permission_tables if t.name == table_name), None)
        if table:
            table.drop(bind=engine, checkfirst=True)
            logger.info(f"删除表: {table_name}")

    # 最后删除主表
    from models.permission import Permission, Role

    Permission.__table__.drop(bind=engine, checkfirst=True)
    Role.__table__.drop(bind=engine, checkfirst=True)

    logger.info("权限系统表删除完成")


def seed_initial_data():
    """填充初始数据"""
    from services.permission_service import permission_service
    from utils.database import get_async_db

    logger.info("开始填充权限系统初始数据...")

    async def _seed():
        async for db in get_async_db():
            try:
                # 初始化系统权限
                permission_map = await permission_service.initialize_system_permissions(
                    db
                )
                logger.info(f"初始化权限完成: {len(permission_map)} 个权限")

                # 初始化系统角色
                role_map = await permission_service.initialize_system_roles(db)
                logger.info(f"初始化角色完成: {len(role_map)} 个角色")

                break
            except Exception as e:
                logger.error(f"填充初始数据失败: {e}")
                raise

    import asyncio

    asyncio.run(_seed())

    logger.info("权限系统初始数据填充完成")


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="权限系统数据库迁移工具")
    parser.add_argument(
        "action", choices=["upgrade", "downgrade", "seed"], help="执行的操作"
    )
    parser.add_argument("--sync", action="store_true", help="使用同步方式执行")

    args = parser.parse_args()

    if args.action == "upgrade":
        if args.sync:
            upgrade()
        else:
            asyncio.run(asyncio.to_thread(upgrade))
    elif args.action == "downgrade":
        if args.sync:
            downgrade()
        else:
            asyncio.run(asyncio.to_thread(downgrade))
    elif args.action == "seed":
        seed_initial_data()
