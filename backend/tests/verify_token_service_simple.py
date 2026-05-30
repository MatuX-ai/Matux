"""
Token 服务简单功能验证（简化版）
"""

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, event, text
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


# 使用 SQLite 内存数据库
engine = create_engine("sqlite:///:memory:")

# 禁用外键检查


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=OFF")
    cursor.close()


Session = sessionmaker(bind=engine)
db = Session()

print("=" * 60)
print("Token 服务功能验证")
print("=" * 60)

try:
    # 1. 创建表
    print("\n[1/5] 创建数据表...")
    db.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username VARCHAR(50), email VARCHAR(120), password_hash VARCHAR(200))"))
    db.execute(text("CREATE TABLE token_packages (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(100), package_type VARCHAR(50), token_count INTEGER, price FLOAT, valid_days INTEGER, is_active BOOLEAN DEFAULT 1)"))
    db.execute(text("CREATE TABLE user_token_balances (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE, total_tokens INTEGER DEFAULT 0, used_tokens INTEGER DEFAULT 0, remaining_tokens INTEGER DEFAULT 0, monthly_bonus_tokens INTEGER DEFAULT 0)"))
    db.execute(text("CREATE TABLE token_recharge_records (id INTEGER PRIMARY KEY AUTOINCREMENT, user_balance_id INTEGER, package_id INTEGER, token_amount INTEGER, payment_amount FLOAT, payment_method VARCHAR(50), order_no VARCHAR(100) UNIQUE)"))
    db.execute(text("CREATE TABLE token_usage_records (id INTEGER PRIMARY KEY AUTOINCREMENT, user_balance_id INTEGER, token_amount INTEGER, usage_type VARCHAR(50), usage_description TEXT)"))
    db.commit()
    print("✓ 表创建成功")

    # 2. 插入套餐
    print("\n[2/5] 插入测试套餐...")
    db.execute(text("INSERT INTO token_packages (name, package_type, token_count, price, valid_days, is_active) VALUES ('免费包', 'FREE', 100, 0.0, 30, 1), ('标准包', 'STANDARD', 1000, 99.0, 365, 1), ('高级包', 'PREMIUM', 3000, 249.0, 365, 1)"))
    db.commit()
    print("✓ 套餐插入成功")

    # 3. 创建用户
    print("\n[3/5] 创建测试用户...")
    db.execute(text(
        "INSERT INTO users (username, email, password_hash) VALUES ('testuser', 'test@example.com', 'hashed')"))
    db.commit()
    test_user_id = 1
    print(f"✓ 用户创建成功 (ID={test_user_id})")

    # 4. 测试服务
    print("\n[4/5] 测试 Token 服务核心功能...")
    from services.token_service import TokenService

    token_service = TokenService(db)

    # 4.1 获取或创建余额
    balance = token_service.get_or_create_user_balance(test_user_id)
    print(f"  ✓ get_or_create_user_balance: 余额 ID={balance.id}")

    # 4.2 购买套餐
    from datetime import datetime
    recharge = token_service.purchase_token_package(
        user_id=test_user_id,
        package_id=2,  # 标准包
        payment_method="wechat",
        order_no=f"TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    print(f"  ✓ purchase_token_package: 充值 {recharge.token_amount} tokens")

    # 4.3 消费 Token
    success, message = token_service.consume_tokens(
        user_id=test_user_id,
        token_amount=100,
        usage_type="ai_teacher",
        usage_description="AI 对话测试"
    )
    print(f"  ✓ consume_tokens: {success}, {message}")

    # 4.4 获取统计
    stats = token_service.get_token_stats(test_user_id)
    print(
        f"  ✓ get_token_stats: 总={stats['total_tokens']}, 剩余={stats['remaining_tokens']}")

    # 4.5 成本预估
    course_cost = token_service.estimate_course_cost("medium")
    chat_cost = token_service.estimate_ai_chat_cost(500)
    print(f"  ✓ estimate_course_cost: {course_cost} tokens")
    print(f"  ✓ estimate_ai_chat_cost: {chat_cost} tokens")

    # 5. 验证
    print("\n[5/5] 验证数据一致性...")
    final_balance = token_service.get_or_create_user_balance(test_user_id)
    assert final_balance.total_tokens == 1000
    assert final_balance.used_tokens == 100
    assert final_balance.remaining_tokens == 900
    print("✓ 所有数据验证通过")

    print("\n🎉 Token 服务所有核心功能验证通过！")

except Exception as e:
    print(f"\n❌ 验证失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    db.close()
