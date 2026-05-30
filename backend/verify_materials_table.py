"""
验证课件库数据库表是否创建成功
"""

import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, inspect
from config.settings import settings

def verify_materials_table():
    """验证unified_materials表是否存在"""

    print("=" * 60)
    print("课件库数据库表验证")
    print("=" * 60)

    # 将异步URL转换为同步URL
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite+aiosqlite://"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite:///")
    elif db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    # 创建同步数据库引擎
    engine = create_engine(db_url)

    # 检查表是否存在
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    if "unified_materials" in tables:
        print("\n✅ unified_materials 表存在！")

        # 显示表结构
        columns = inspector.get_columns("unified_materials")
        print(f"\n📊 表结构 ({len(columns)} 列):")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")

        # 显示索引
        indexes = inspector.get_indexes("unified_materials")
        print(f"\n📑 索引 ({len(indexes)} 个):")
        for idx in indexes:
            print(f"  - {idx['name']}: {idx['column_names']}")

        print("\n✅ 验证通过！课件库系统已就绪。")
        return True
    else:
        print("\n❌ unified_materials 表不存在！")
        print("\n可用的表:")
        for table in tables:
            print(f"  - {table}")
        return False

if __name__ == "__main__":
    try:
        verify_materials_table()
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
