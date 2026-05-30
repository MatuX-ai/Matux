"""
统一课件库数据库迁移脚本
创建unified_materials表及相关索引
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from models.unified_material import UnifiedMaterial, Base

# 导入所有相关模型以确保外键关系正确
from models.license import Organization, License
from models.user import User
from models.course import Course, CourseLesson
from models.payment import Product


def create_unified_materials_table():
    """创建统一课件库数据表"""

    # 将异步 URL 转换为同步 URL
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite+aiosqlite://"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite:///")
    elif db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    # 创建数据库引擎
    engine = create_engine(db_url)

    # 创建所有表（包括unified_materials）
    Base.metadata.create_all(bind=engine)

    print("✅ 统一课件库数据表创建成功!")

    # 创建额外的索引以提高查询性能
    with engine.connect() as conn:
        # 为文件哈希创建唯一索引（用于去重）
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_materials_file_hash
            ON unified_materials (file_hash)
        """))

        # 为组合查询创建复合索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_materials_org_type
            ON unified_materials (org_id, type)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_materials_org_category
            ON unified_materials (org_id, category)
        """))

        # 为统计查询创建索引
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_materials_stats
            ON unified_materials (org_id, created_at, visibility)
        """))

        conn.commit()
        print("✅ 索引创建成功!")

    # 验证表创建
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "unified_materials" in tables:
        print("✅ 表验证通过")
        # 显示表结构
        columns = inspector.get_columns("unified_materials")
        print(f"📊 表结构 ({len(columns)} 列):")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")

        # 显示索引
        indexes = inspector.get_indexes("unified_materials")
        print(f"\n📑 索引 ({len(indexes)} 个):")
        for idx in indexes:
            print(f"  - {idx['name']}: {idx['column_names']}")
    else:
        print("❌ 表创建失败")


if __name__ == "__main__":
    try:
        create_unified_materials_table()
        print("\n🎉 统一课件库数据库迁移完成!")
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
