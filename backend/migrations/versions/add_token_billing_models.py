"""add_token_billing_models

Revision ID: add_token_billing
Revises: ai_edu_001_create_ai_edu_tables
Create Date: 2026-03-14 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_token_billing'
down_revision = 'ai_edu_001_create_ai_edu_tables'
branch_labels = None
depends_on = None


def upgrade():
    """升级：创建 Token 计费相关表"""
    
    # 1. 创建 token_packages 表（Token 套餐包）
    op.create_table(
        'token_packages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('package_type', sa.Enum('FREE', 'STANDARD', 'PREMIUM', 'ENTERPRISE', name='tokenpackagetype'), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('valid_days', sa.Integer(), nullable=True),
        sa.Column('bonus_features', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_token_packages_id'), 'token_packages', ['id'], unique=False)
    
    # 2. 创建 user_token_balances 表（用户 Token 余额）
    op.create_table(
        'user_token_balances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('used_tokens', sa.Integer(), nullable=True),
        sa.Column('remaining_tokens', sa.Integer(), nullable=True),
        sa.Column('monthly_bonus_tokens', sa.Integer(), nullable=True),
        sa.Column('last_bonus_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_token_balances_id'), 'user_token_balances', ['id'], unique=False)
    op.create_index(op.f('ix_user_token_balances_user_id'), 'user_token_balances', ['user_id'], unique=False)
    
    # 3. 创建 token_recharge_records 表（Token 充值记录）
    op.create_table(
        'token_recharge_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_balance_id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.Integer(), nullable=True),
        sa.Column('token_amount', sa.Integer(), nullable=False),
        sa.Column('payment_amount', sa.Float(), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_status', sa.String(length=20), nullable=True),
        sa.Column('payment_time', sa.DateTime(), nullable=True),
        sa.Column('order_no', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['package_id'], ['token_packages.id'], ),
        sa.ForeignKeyConstraint(['user_balance_id'], ['user_token_balances.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_no')
    )
    op.create_index(op.f('ix_token_recharge_records_id'), 'token_recharge_records', ['id'], unique=False)
    op.create_index(op.f('ix_token_recharge_records_user_balance_id'), 'token_recharge_records', ['user_balance_id'], unique=False)
    
    # 4. 创建 token_usage_records 表（Token 使用记录）
    op.create_table(
        'token_usage_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_balance_id', sa.Integer(), nullable=False),
        sa.Column('token_amount', sa.Integer(), nullable=False),
        sa.Column('usage_type', sa.String(length=50), nullable=False),
        sa.Column('usage_description', sa.Text(), nullable=True),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_balance_id'], ['user_token_balances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_token_usage_records_id'), 'token_usage_records', ['id'], unique=False)
    op.create_index(op.f('ix_token_usage_records_user_balance_id'), 'token_usage_records', ['user_balance_id'], unique=False)


def downgrade():
    """降级：删除 Token 计费相关表"""
    op.drop_index(op.f('ix_token_usage_records_user_balance_id'), table_name='token_usage_records')
    op.drop_index(op.f('ix_token_usage_records_id'), table_name='token_usage_records')
    op.drop_table('token_usage_records')
    
    op.drop_index(op.f('ix_token_recharge_records_user_balance_id'), table_name='token_recharge_records')
    op.drop_index(op.f('ix_token_recharge_records_id'), table_name='token_recharge_records')
    op.drop_table('token_recharge_records')
    
    op.drop_index(op.f('ix_user_token_balances_user_id'), table_name='user_token_balances')
    op.drop_index(op.f('ix_user_token_balances_id'), table_name='user_token_balances')
    op.drop_table('user_token_balances')
    
    op.drop_index(op.f('ix_token_packages_id'), table_name='token_packages')
    op.drop_table('token_packages')
