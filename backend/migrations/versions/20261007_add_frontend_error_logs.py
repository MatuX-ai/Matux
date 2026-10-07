"""
add frontend error logs table

Revision ID: 20261007_add_frontend_error_logs
Revises: add_token_billing
Create Date: 2026-10-07 12:00:00.000000

将前端错误日志从内存列表替换为数据库持久化存储。
原 backend/routes/error_log_routes.py 与 backend/routes/org_error_log_routes.py
中的 `error_logs` / `_frontend_error_logs` 全部切换为写入 frontend_error_logs 表。
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20261007_add_frontend_error_logs"
down_revision = "add_token_billing"
branch_labels = None
depends_on = None


def upgrade():
    """升级 - 创建前端错误日志表"""
    op.create_table(
        "frontend_error_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("log_type", sa.String(length=64), nullable=False, server_default="UNKNOWN"),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="warning"),
        sa.Column("log_format", sa.String(length=32), nullable=False, server_default="legacy"),
        sa.Column("source", sa.String(length=64), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("url", sa.String(length=2048), nullable=True),
        sa.Column("stack", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.String(length=1024), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # 常用查询索引
    op.create_index(
        "ix_frontend_error_logs_id",
        "frontend_error_logs",
        ["id"],
    )
    op.create_index(
        "ix_frontend_error_logs_org_id",
        "frontend_error_logs",
        ["org_id"],
    )
    op.create_index(
        "ix_frontend_error_logs_user_id",
        "frontend_error_logs",
        ["user_id"],
    )
    op.create_index(
        "ix_frontend_error_logs_log_type",
        "frontend_error_logs",
        ["log_type"],
    )
    op.create_index(
        "ix_frontend_error_logs_occurred_at",
        "frontend_error_logs",
        ["occurred_at"],
    )
    op.create_index(
        "ix_frontend_error_logs_org_received",
        "frontend_error_logs",
        ["org_id", "received_at"],
    )
    op.create_index(
        "ix_frontend_error_logs_org_type",
        "frontend_error_logs",
        ["org_id", "log_type", "received_at"],
    )


def downgrade():
    """降级 - 删除前端错误日志表"""
    op.drop_index(
        "ix_frontend_error_logs_org_type",
        table_name="frontend_error_logs",
    )
    op.drop_index(
        "ix_frontend_error_logs_org_received",
        table_name="frontend_error_logs",
    )
    op.drop_index(
        "ix_frontend_error_logs_occurred_at",
        table_name="frontend_error_logs",
    )
    op.drop_index(
        "ix_frontend_error_logs_log_type",
        table_name="frontend_error_logs",
    )
    op.drop_index(
        "ix_frontend_error_logs_user_id",
        table_name="frontend_error_logs",
    )
    op.drop_index(
        "ix_frontend_error_logs_org_id",
        table_name="frontend_error_logs",
    )
    op.drop_index(
        "ix_frontend_error_logs_id",
        table_name="frontend_error_logs",
    )
    op.drop_table("frontend_error_logs")
