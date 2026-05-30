"""
Token 计费系统数据库初始化脚本
直接使用 SQLAlchemy 创建表（不使用 Alembic）
"""

from config.settings import settings
from sqlalchemy import create_engine, text
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


# 如果是 SQLite，使用同步模式
if 'sqlite' in settings.DATABASE_URL:
    sync_db_url = settings.DATABASE_URL.replace('sqlite+aiosqlite', 'sqlite')
    engine = create_engine(sync_db_url)
else:
    engine = create_engine(settings.DATABASE_URL)


def create_tables():
    """直接创建 Token 计费系统表"""

    print("=" * 60)
    print("Token 计费系统数据库表创建")
    print("=" * 60)

    with engine.connect() as conn:
        # 1. 创建 token_packages 表
        print("\n正在创建 token_packages 表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS token_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                package_type VARCHAR(50),
                token_count INTEGER NOT NULL,
                price FLOAT NOT NULL,
                valid_days INTEGER DEFAULT 365,
                bonus_features JSON,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✓ token_packages 表创建成功")

        # 2. 创建 user_token_balances 表
        print("\n正在创建 user_token_balances 表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_token_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                total_tokens INTEGER DEFAULT 0,
                used_tokens INTEGER DEFAULT 0,
                remaining_tokens INTEGER DEFAULT 0,
                monthly_bonus_tokens INTEGER DEFAULT 0,
                last_bonus_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        print("✓ user_token_balances 表创建成功")

        # 3. 创建 token_recharge_records 表
        print("\n正在创建 token_recharge_records 表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS token_recharge_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_balance_id INTEGER NOT NULL,
                package_id INTEGER,
                token_amount INTEGER NOT NULL,
                payment_amount FLOAT NOT NULL,
                payment_method VARCHAR(50),
                payment_status VARCHAR(20) DEFAULT 'pending',
                payment_time DATETIME,
                order_no VARCHAR(100) NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (package_id) REFERENCES token_packages(id),
                FOREIGN KEY (user_balance_id) REFERENCES user_token_balances(id)
            )
        """))
        print("✓ token_recharge_records 表创建成功")

        # 4. 创建 token_usage_records 表
        print("\n正在创建 token_usage_records 表...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS token_usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_balance_id INTEGER NOT NULL,
                token_amount INTEGER NOT NULL,
                usage_type VARCHAR(50) NOT NULL,
                usage_description TEXT,
                resource_id INTEGER,
                resource_type VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_balance_id) REFERENCES user_token_balances(id)
            )
        """))
        print("✓ token_usage_records 表创建成功")

        # 5. 创建索引
        print("\n正在创建索引...")

        # token_packages 索引
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_token_packages_type ON token_packages(package_type)"))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_token_packages_active ON token_packages(is_active)"))

        # user_token_balances 索引
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_user_balances_user ON user_token_balances(user_id)"))

        # token_recharge_records 索引
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_recharge_balance ON token_recharge_records(user_balance_id)"))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_recharge_order ON token_recharge_records(order_no)"))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_recharge_created ON token_recharge_records(created_at)"))

        # token_usage_records 索引
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_usage_balance ON token_usage_records(user_balance_id)"))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_usage_type ON token_usage_records(usage_type)"))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_usage_created ON token_usage_records(created_at)"))

        print("✓ 所有索引创建成功")

        # 6. 插入示例数据
        print("\n正在插入示例数据...")
        from datetime import datetime

        # 检查是否已有数据
        result = conn.execute(
            text("SELECT COUNT(*) FROM token_packages")).fetchone()

        if result[0] == 0:
            # 插入 4 个套餐
            conn.execute(text("""
                INSERT INTO token_packages (name, package_type, token_count, price, valid_days, is_active)
                VALUES
                    ('免费体验包', 'FREE', 100, 0.0, 30, 1),
                    ('标准套餐', 'STANDARD', 1000, 99.0, 365, 1),
                    ('高级套餐', 'PREMIUM', 3000, 249.0, 365, 1),
                    ('企业套餐', 'ENTERPRISE', 10000, 699.0, 365, 1)
            """))
            print("✓ 成功插入 4 个示例套餐")
        else:
            print("- 套餐数据已存在，跳过插入")

        conn.commit()

        # 7. 显示结果
        print("\n" + "=" * 60)
        print("Token 套餐列表")
        print("=" * 60)

        result = conn.execute(text("""
            SELECT id, name, package_type, token_count, price, valid_days
            FROM token_packages
            ORDER BY price ASC
        """)).fetchall()

        print(f"\n{'ID':<5} {'名称':<15} {'类型':<12} {'Token 数':<8} {'价格':<8} {'有效期'}")
        print("-" * 70)
        for row in result:
            pkg_type = row[2] if row[2] else 'N/A'
            valid_days = f"{row[5]}天" if row[5] else '永久'
            print(
                f"{row[0]:<5} {row[1]:<15} {pkg_type:<12} {row[3]:<8} ¥{row[4]:<7.1f} {valid_days}")

    print("\n" + "=" * 60)
    print("✅ Token 计费系统数据库初始化完成！")
    print("=" * 60)
    print("\n已创建的表:")
    print("  ✓ token_packages (Token 套餐包)")
    print("  ✓ user_token_balances (用户 Token 余额)")
    print("  ✓ token_recharge_records (充值记录)")
    print("  ✓ token_usage_records (使用记录)")
    print("\n已创建的索引:")
    print("  ✓ 各表主键索引")
    print("  ✓ 外键索引")
    print("  ✓ 查询优化索引")
    print("\n🎉 数据库已就绪，可以开始开发 Week 1 后续任务！")


if __name__ == "__main__":
    try:
        create_tables()
    except Exception as e:
        print(f"\n❌ 数据库初始化失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
