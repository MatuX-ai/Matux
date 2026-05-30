"""验证硬件模块数据库迁移结果"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 加载环境变量
load_dotenv()


def main():
    # 获取数据库URL
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # 创建引擎
    engine = create_engine(database_url)

    print("🔍 验证硬件模块数据库迁移结果...")

    # 检查表是否存在
    with engine.connect() as conn:
        # 检查hardware_modules表
        result = conn.execute(text("SELECT COUNT(*) FROM hardware_modules"))
        module_count = result.fetchone()[0]
        print(f"✅ hardware_modules表: {module_count} 条记录")

        # 检查module_rental_records表
        result = conn.execute(text("SELECT COUNT(*) FROM module_rental_records"))
        rental_count = result.fetchone()[0]
        print(f"✅ module_rental_records表: {rental_count} 条记录")

        # 显示硬件模块数据
        if module_count > 0:
            print("\n📋 硬件模块列表:")
            result = conn.execute(
                text(
                    "SELECT id, name, module_type, quantity_available, total_quantity FROM hardware_modules"
                )
            )
            for row in result:
                print(
                    f"  - ID:{row.id} {row.name} ({row.module_type}): {row.quantity_available}/{row.total_quantity} 可用"
                )

        # 显示索引信息
        print("\n📊 数据库索引:")
        result = conn.execute(
            text(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='hardware_modules'"
            )
        )
        indexes = [row[0] for row in result]
        for idx in indexes:
            print(f"  - {idx}")


if __name__ == "__main__":
    main()
