"""
Token 计费系统数据库迁移脚本
创建 Token 套餐、余额、充值记录和使用记录相关数据表

Revision ID: pricing_001
Revises:
Create Date: 2026-03-14 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = 'pricing_001'
down_revision = None  # 需要根据实际前一个迁移文件调整
branch_labels = None
depends_on = None


def upgrade():
    """升级：创建所有 Token 计费相关表"""

    # 获取数据库连接以检查表是否存在
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = inspector.get_table_names()

    print("开始创建 Token 计费系统数据表...")

    # ==================== 1. 创建 token_packages 表 ====================
    if 'token_packages' not in existing_tables:
        op.create_table('token_packages',
                        sa.Column('id', sa.Integer(), nullable=False),
                        sa.Column('name', sa.String(
                            length=100), nullable=False),
                        sa.Column('package_type', sa.Enum('FREE', 'STANDARD', 'PREMIUM',
                                                          'ENTERPRISE', name='tokenpackagetype'), nullable=True),
                        sa.Column('token_count', sa.Integer(), nullable=False),
                        sa.Column('price', sa.Float(), nullable=False),
                        sa.Column('valid_days', sa.Integer(), nullable=True),
                        sa.Column('bonus_features', sa.JSON(), nullable=True),
                        sa.Column('is_active', sa.Boolean(), nullable=True),
                        sa.Column('created_at', sa.DateTime(), nullable=True),
                        sa.Column('updated_at', sa.DateTime(), nullable=True),
                        sa.PrimaryKeyConstraint('id')
                        )

        # 创建索引
        op.create_index(op.f('ix_token_packages_id'),
                        'token_packages', ['id'], unique=False)
        op.create_index(op.f('ix_token_packages_package_type'),
                        'token_packages', ['package_type'], unique=False)
        op.create_index(op.f('ix_token_packages_is_active'),
                        'token_packages', ['is_active'], unique=False)

        print("✓ 创建 token_packages 表成功")
    else:
        print("- token_packages 表已存在，跳过")

    # ==================== 2. 创建 user_token_balances 表 ====================
    if 'user_token_balances' not in existing_tables:
        op.create_table('user_token_balances',
                        sa.Column('id', sa.Integer(), nullable=False),
                        sa.Column('user_id', sa.Integer(), nullable=False),
                        sa.Column('total_tokens', sa.Integer(), nullable=True),
                        sa.Column('used_tokens', sa.Integer(), nullable=True),
                        sa.Column('remaining_tokens',
                                  sa.Integer(), nullable=True),
                        sa.Column('monthly_bonus_tokens',
                                  sa.Integer(), nullable=True),
                        sa.Column('last_bonus_date',
                                  sa.DateTime(), nullable=True),
                        sa.Column('created_at', sa.DateTime(), nullable=True),
                        sa.Column('updated_at', sa.DateTime(), nullable=True),
                        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
                        sa.PrimaryKeyConstraint('id'),
                        sa.UniqueConstraint('user_id')
                        )

        # 创建索引
        op.create_index(op.f('ix_user_token_balances_id'),
                        'user_token_balances', ['id'], unique=False)
        op.create_index(op.f('ix_user_token_balances_user_id'),
                        'user_token_balances', ['user_id'], unique=False)

        print("✓ 创建 user_token_balances 表成功")
    else:
        print("- user_token_balances 表已存在，跳过")

    # ==================== 3. 创建 token_recharge_records 表 ====================
    if 'token_recharge_records' not in existing_tables:
        op.create_table('token_recharge_records',
                        sa.Column('id', sa.Integer(), nullable=False),
                        sa.Column('user_balance_id',
                                  sa.Integer(), nullable=False),
                        sa.Column('package_id', sa.Integer(), nullable=True),
                        sa.Column('token_amount', sa.Integer(),
                                  nullable=False),
                        sa.Column('payment_amount',
                                  sa.Float(), nullable=False),
                        sa.Column('payment_method', sa.String(
                            length=50), nullable=True),
                        sa.Column('payment_status', sa.String(
                            length=20), nullable=True),
                        sa.Column('payment_time',
                                  sa.DateTime(), nullable=True),
                        sa.Column('order_no', sa.String(
                            length=100), nullable=False),
                        sa.Column('created_at', sa.DateTime(), nullable=True),
                        sa.ForeignKeyConstraint(
                            ['package_id'], ['token_packages.id'], ),
                        sa.ForeignKeyConstraint(['user_balance_id'], [
                            'user_token_balances.id'], ),
                        sa.PrimaryKeyConstraint('id'),
                        sa.UniqueConstraint('order_no')
                        )

        # 创建索引
        op.create_index(op.f('ix_token_recharge_records_id'),
                        'token_recharge_records', ['id'], unique=False)
        op.create_index(op.f('ix_token_recharge_records_user_balance_id'),
                        'token_recharge_records', ['user_balance_id'], unique=False)
        op.create_index(op.f('ix_token_recharge_records_order_no'),
                        'token_recharge_records', ['order_no'], unique=False)

        print("✓ 创建 token_recharge_records 表成功")
    else:
        print("- token_recharge_records 表已存在，跳过")

    # ==================== 4. 创建 token_usage_records 表 ====================
    if 'token_usage_records' not in existing_tables:
        op.create_table('token_usage_records',
                        sa.Column('id', sa.Integer(), nullable=False),
                        sa.Column('user_balance_id',
                                  sa.Integer(), nullable=False),
                        sa.Column('token_amount', sa.Integer(),
                                  nullable=False),
                        sa.Column('usage_type', sa.String(
                            length=50), nullable=False),
                        sa.Column('usage_description',
                                  sa.Text(), nullable=True),
                        sa.Column('resource_id', sa.Integer(), nullable=True),
                        sa.Column('resource_type', sa.String(
                            length=50), nullable=True),
                        sa.Column('created_at', sa.DateTime(), nullable=True),
                        sa.ForeignKeyConstraint(['user_balance_id'], [
                            'user_token_balances.id'], ),
                        sa.PrimaryKeyConstraint('id')
                        )

        # 创建索引
        op.create_index(op.f('ix_token_usage_records_id'),
                        'token_usage_records', ['id'], unique=False)
        op.create_index(op.f('ix_token_usage_records_user_balance_id'),
                        'token_usage_records', ['user_balance_id'], unique=False)
        op.create_index(op.f('ix_token_usage_records_usage_type'),
                        'token_usage_records', ['usage_type'], unique=False)

        print("✓ 创建 token_usage_records 表成功")
    else:
        print("- token_usage_records 表已存在，跳过")

    # ==================== 5. 创建复合索引（提高查询性能） ====================
    print("正在创建复合索引...")

    # 为充值记录创建复合索引
    try:
        op.create_index('idx_recharge_user_created', 'token_recharge_records',
                        ['user_balance_id', 'created_at'], unique=False)
        print("✓ 创建 idx_recharge_user_created 索引成功")
    except Exception as e:
        print(f"- idx_recharge_user_created 索引可能已存在：{e}")

    # 为使用记录创建复合索引
    try:
        op.create_index('idx_usage_user_type', 'token_usage_records',
                        ['user_balance_id', 'usage_type'], unique=False)
        print("✓ 创建 idx_usage_user_type 索引成功")
    except Exception as e:
        print(f"- idx_usage_user_type 索引可能已存在：{e}")

    # 为使用记录创建时间索引
    try:
        op.create_index('idx_usage_created', 'token_usage_records',
                        ['created_at'], unique=False)
        print("✓ 创建 idx_usage_created 索引成功")
    except Exception as e:
        print(f"- idx_usage_created 索引可能已存在：{e}")

    print("\n✅ Token 计费系统数据表创建完成！")
    print("\n创建的表:")
    print("  - token_packages (Token 套餐包)")
    print("  - user_token_balances (用户 Token 余额)")
    print("  - token_recharge_records (充值记录)")
    print("  - token_usage_records (使用记录)")


def downgrade():
    """降级：删除所有 Token 计费相关表"""

    print("开始删除 Token 计费系统数据表...")

    # 按相反顺序删除表
    try:
        op.drop_index('idx_usage_created', table_name='token_usage_records')
        op.drop_index('idx_usage_user_type', table_name='token_usage_records')
        op.drop_index('idx_recharge_user_created',
                      table_name='token_recharge_records')

        op.drop_table('token_usage_records')
        print("✓ 删除 token_usage_records 表成功")

        op.drop_table('token_recharge_records')
        print("✓ 删除 token_recharge_records 表成功")

        op.drop_table('user_token_balances')
        print("✓ 删除 user_token_balances 表成功")

        op.drop_table('token_packages')
        print("✓ 删除 token_packages 表成功")

        print("\n✅ Token 计费系统数据表删除完成！")
    except Exception as e:
        print(f"❌ 删除表时出错：{e}")
        raise
