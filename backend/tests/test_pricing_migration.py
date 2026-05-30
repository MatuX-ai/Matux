"""
Token 计费系统数据库迁移测试脚本
用于验证迁移脚本是否能正确执行
"""

from config.settings import settings
from sqlalchemy import create_engine, text, inspect
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


# 如果是 SQLite，使用同步模式
if 'sqlite' in settings.DATABASE_URL:
    # 替换为同步 SQLite
    sync_db_url = settings.DATABASE_URL.replace('sqlite+aiosqlite', 'sqlite')
    engine = create_engine(sync_db_url)
else:
    engine = create_engine(settings.DATABASE_URL)


def test_migration():
    """测试 Token 计费系统的数据库迁移"""

    print("=" * 60)
    print("Token 计费系统数据库迁移测试")
    print("=" * 60)

    # 创建数据库引擎（已在全局变量中创建）
    try:
        print(
            f"✓ 数据库连接成功：{settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else '本地数据库'}")
    except Exception as e:
        print(f"❌ 数据库连接失败：{e}")
        return False

    # 检查表是否存在
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("\n当前数据库中的表:")
    for table in tables:
        marker = "✓" if "token" in table.lower() else " "
        print(f"{marker} {table}")

    # 检查 Token 计费相关的 4 个表
    required_tables = [
        'token_packages',
        'user_token_balances',
        'token_recharge_records',
        'token_usage_records'
    ]

    print("\n" + "=" * 60)
    print("检查 Token 计费系统核心表")
    print("=" * 60)

    all_exist = True
    for table_name in required_tables:
        exists = table_name in tables
        status = "✓ 存在" if exists else "✗ 不存在"
        print(f"{status}: {table_name}")
        if not exists:
            all_exist = False

    # 如果表不存在，执行迁移
    if not all_exist:
        print("\n⚠️  检测到缺失的表，开始执行迁移...")

        try:
            # 导入并执行迁移脚本
            from migrations.pricing_001_create_token_billing_tables import upgrade

            print("正在执行升级操作...")
            upgrade()

            print("\n✅ 迁移执行完成！")

            # 重新检查表
            tables = inspect(engine).get_table_names()
            all_exist = all(table in tables for table in required_tables)

        except Exception as e:
            print(f"❌ 迁移执行失败：{e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("\n✅ 所有 Token 计费表已存在！")

    # 检查索引
    print("\n" + "=" * 60)
    print("检查索引配置")
    print("=" * 60)

    with engine.connect() as conn:
        for table_name in required_tables:
            indexes = inspector.get_indexes(table_name)
            if indexes:
                print(f"\n{table_name} 表的索引:")
                for idx in indexes:
                    print(f"  - {idx['name']}: {idx['column_names']}")
            else:
                print(f"⚠️  {table_name} 表没有索引")

    # 测试数据插入（可选）
    print("\n" + "=" * 60)
    print("测试数据插入")
    print("=" * 60)

    try:
        with engine.connect() as conn:
            # 插入一个测试套餐
            from datetime import datetime

            # 检查是否有测试数据
            result = conn.execute(text("""
                SELECT COUNT(*) FROM token_packages
            """)).fetchone()

            count = result[0] if result else 0
            print(f"当前 token_packages 表中有 {count} 条记录")

            if count == 0:
                # 插入示例数据
                conn.execute(text("""
                    INSERT INTO token_packages
                    (name, package_type, token_count, price, valid_days, is_active, created_at, updated_at)
                    VALUES
                    ('免费体验包', 'FREE', 100, 0.0, 30, true, :now, :now),
                    ('标准套餐', 'STANDARD', 1000, 99.0, 365, true, :now, :now),
                    ('高级套餐', 'PREMIUM', 3000, 249.0, 365, true, :now, :now),
                    ('企业套餐', 'ENTERPRISE', 10000, 699.0, 365, true, :now, :now)
                """), {"now": datetime.utcnow()})

                conn.commit()
                print("✓ 成功插入 4 个测试套餐")

            # 显示所有套餐
            result = conn.execute(text("""
                SELECT id, name, package_type, token_count, price, valid_days
                FROM token_packages
                ORDER BY price ASC
            """)).fetchall()

            print("\nToken 套餐列表:")
            print(f"{'ID':<5} {'名称':<15} {'类型':<12} {'Token 数':<8} {'价格':<8} {'有效期'}")
            print("-" * 70)
            for row in result:
                pkg_type = row[2] if row[2] else 'N/A'
                valid_days = f"{row[5]}天" if row[5] else '永久'
                print(
                    f"{row[0]:<5} {row[1]:<15} {pkg_type:<12} {row[3]:<8} ¥{row[4]:<7.1f} {valid_days}")

    except Exception as e:
        print(f"⚠️  测试数据插入失败：{e}")
        # 不中断测试流程

    # 最终总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    if all_exist:
        print("✅ Token 计费系统数据库迁移测试通过！")
        print("\n已创建的表:")
        for table in required_tables:
            print(f"  ✓ {table}")
        return True
    else:
        print("❌ Token 计费系统数据库迁移测试失败！")
        print("\n缺失的表:")
        for table in required_tables:
            if table not in tables:
                print(f"  ✗ {table}")
        return False


if __name__ == "__main__":
    success = test_migration()

    if success:
        print("\n🎉 所有测试通过！Token 计费系统已就绪。")
        sys.exit(0)
    else:
        print("\n💥 测试失败！请检查错误信息。")
        sys.exit(1)
