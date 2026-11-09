"""add global unlock rate and holders fields to achievements

Revision ID: 20261009_p3a1_global_stats
Revises: 20261007_add_frontend_error_logs
Create Date: 2026-10-09

P3-A-1 阶段：为 achievements 表添加全局解锁率统计字段
- global_unlock_rate: 全局解锁率（基于全平台用户，0-1）
- total_holders: 累计解锁用户数（去重）
- stats_updated_at: 统计更新时间
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20261009_p3a1_global_stats"
down_revision = "20261007_add_frontend_error_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构 - 添加全局统计字段"""
    op.add_column(
        "achievements",
        sa.Column(
            "global_unlock_rate",
            sa.Float(),
            nullable=True,
            server_default="0.0",
            comment="全局解锁率（基于全平台用户，0-1）",
        ),
    )
    op.add_column(
        "achievements",
        sa.Column(
            "total_holders",
            sa.Integer(),
            nullable=True,
            server_default="0",
            comment="累计解锁用户数（去重）",
        ),
    )
    op.add_column(
        "achievements",
        sa.Column(
            "stats_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="统计更新时间",
        ),
    )


def downgrade() -> None:
    """回滚数据库结构"""
    op.drop_column("achievements", "stats_updated_at")
    op.drop_column("achievements", "total_holders")
    op.drop_column("achievements", "global_unlock_rate")
