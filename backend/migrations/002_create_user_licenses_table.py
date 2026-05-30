"""
用户许可证关联表迁移脚本
创建user_licenses表用于用户与许可证的关联管理
"""

import enum
import os

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    Table,
    create_engine,
)
from sqlalchemy.sql import func

# 加载环境变量
load_dotenv()


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    ORG_ADMIN = "org_admin"
    PREMIUM = "premium"


class UserLicenseStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    REVOKED = "revoked"


def create_user_licenses_table():
    """创建用户许可证关联表"""

    # 获取数据库URL
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # 创建引擎
    engine = create_engine(database_url)
    metadata = MetaData()

    # 定义user_licenses表
    user_licenses = Table(
        "user_licenses",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("users.id"), nullable=False, index=True),
        Column(
            "license_id", Integer, ForeignKey("licenses.id"), nullable=False, index=True
        ),
        Column("role", Enum(UserRole), default=UserRole.USER, nullable=False),
        Column("status", Enum(UserLicenseStatus), default=UserLicenseStatus.INACTIVE),
        Column("can_manage", Boolean, default=False),
        Column("can_view", Boolean, default=True),
        Column("can_use", Boolean, default=True),
        Column("assigned_by", Integer, ForeignKey("users.id")),
        Column("assigned_at", DateTime, default=func.now()),
        Column("expires_at", DateTime),
        Column("created_at", DateTime, default=func.now()),
        Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
        # 复合主键
        # sqlite不支持复合主键的ALTER TABLE，所以这里注释掉
        # PrimaryKeyConstraint('user_id', 'license_id')
    )

    # 创建表
    metadata.create_all(engine)
    print("✅ user_licenses 表创建成功")

    # 验证表创建
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "user_licenses" in tables:
        print("✅ 表验证通过")
        # 显示表结构
        columns = inspector.get_columns("user_licenses")
        print(f"📊 表结构 ({len(columns)} 列):")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
    else:
        print("❌ 表创建失败")


def add_user_role_column():
    """为users表添加role字段"""
    from sqlalchemy import inspect

    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    engine = create_engine(database_url)
    inspector = inspect(engine)

    # 检查users表是否存在role字段
    columns = [col["name"] for col in inspector.get_columns("users")]

    if "role" not in columns:
        # 添加role字段
        with engine.connect() as conn:
            try:
                conn.execute(
                    "ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"
                )
                conn.commit()
                print("✅ users表role字段添加成功")
            except Exception as e:
                print(f"⚠️  role字段可能已存在或添加失败: {e}")
    else:
        print("✅ users表role字段已存在")


if __name__ == "__main__":
    print("🚀 开始数据库迁移...")

    try:
        # 导入inspect
        from sqlalchemy import inspect

        # 添加用户role字段
        add_user_role_column()

        # 创建用户许可证表
        create_user_licenses_table()

        print("\n🎉 数据库迁移完成!")
        print("\n📋 创建的表:")
        print("  - user_licenses: 用户与许可证关联表")
        print("\n🔧 修改的表:")
        print("  - users: 添加了role字段")

    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback

        traceback.print_exc()
