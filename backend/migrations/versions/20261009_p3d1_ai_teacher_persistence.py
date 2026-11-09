"""create ai teacher persistence tables

Revision ID: 20261009_p3d1_ai_teacher_persistence
Revises: 20261009_p3a1_global_stats
Create Date: 2026-10-09

P3-D-1 阶段：为 AI 教师持久化层创建 7 张表

5 张 KV 模型（user_id 主键 + JSON value）：
- ai_teacher_profiles       - 学习画像
- ai_teacher_sessions       - 会话上下文
- ai_teacher_memories       - 长期记忆
- ai_teacher_personas       - AI 教师人格配置
- ai_teacher_live_settings  - 实时推送设置

2 张列表模型（id 自增 + 时间索引）：
- ai_teacher_event_history  - 全局事件历史（200 条上限）
- ai_teacher_user_history   - 按用户事件历史（每用户 50 条上限）

承接 P3-B 的 FileJsonRepository（JSON 文件持久化）。
默认 backend 仍是 file，本迁移只在 backend=sql 时启用。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20261009_p3d1_ai_teacher_persistence"
down_revision = "20261009_p3a1_global_stats"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构 - 创建 7 张 AI 教师持久化表"""

    # ==================== 5 张 KV 模型 ====================

    # ai_teacher_profiles - 学习画像
    op.create_table(
        "ai_teacher_profiles",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        comment="AI 教师学生学习画像",
    )
    op.create_index(
        "ix_ai_teacher_profiles_user_id", "ai_teacher_profiles", ["user_id"]
    )

    # ai_teacher_sessions - 会话上下文
    op.create_table(
        "ai_teacher_sessions",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        comment="AI 教师会话上下文",
    )
    op.create_index(
        "ix_ai_teacher_sessions_user_id", "ai_teacher_sessions", ["user_id"]
    )

    # ai_teacher_memories - 长期记忆
    op.create_table(
        "ai_teacher_memories",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        comment="AI 教师长期记忆",
    )
    op.create_index(
        "ix_ai_teacher_memories_user_id", "ai_teacher_memories", ["user_id"]
    )

    # ai_teacher_personas - AI 教师人格配置
    op.create_table(
        "ai_teacher_personas",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        comment="AI 教师人格配置",
    )
    op.create_index(
        "ix_ai_teacher_personas_user_id", "ai_teacher_personas", ["user_id"]
    )

    # ai_teacher_live_settings - 实时推送设置
    op.create_table(
        "ai_teacher_live_settings",
        sa.Column("user_id", sa.String(length=64), primary_key=True),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        comment="AI 教师实时推送设置",
    )
    op.create_index(
        "ix_ai_teacher_live_settings_user_id",
        "ai_teacher_live_settings",
        ["user_id"],
    )

    # ==================== 2 张列表模型 ====================

    # ai_teacher_event_history - 全局事件历史（200 条上限）
    op.create_table(
        "ai_teacher_event_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=64), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
        comment="AI 教师全局事件历史（200 条上限）",
    )
    op.create_index(
        "idx_event_history_user_time",
        "ai_teacher_event_history",
        ["user_id", "created_at"],
    )
    op.create_index(
        "idx_event_history_type_time",
        "ai_teacher_event_history",
        ["event_type", "created_at"],
    )

    # ai_teacher_user_history - 按用户事件历史（每用户 50 条上限）
    op.create_table(
        "ai_teacher_user_history",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
        comment="AI 教师按用户事件历史（每用户 50 条上限）",
    )
    op.create_index(
        "idx_user_history_user_time",
        "ai_teacher_user_history",
        ["user_id", "created_at"],
    )
    op.create_index(
        "idx_user_history_user_type",
        "ai_teacher_user_history",
        ["user_id", "event_type"],
    )


def downgrade() -> None:
    """回滚数据库结构 - 删除 7 张 AI 教师持久化表"""

    # 列表模型（先删除有外键依赖的）
    op.drop_index("idx_user_history_user_type", table_name="ai_teacher_user_history")
    op.drop_index("idx_user_history_user_time", table_name="ai_teacher_user_history")
    op.drop_table("ai_teacher_user_history")

    op.drop_index("idx_event_history_type_time", table_name="ai_teacher_event_history")
    op.drop_index("idx_event_history_user_time", table_name="ai_teacher_event_history")
    op.drop_table("ai_teacher_event_history")

    # KV 模型
    op.drop_index("ix_ai_teacher_live_settings_user_id", table_name="ai_teacher_live_settings")
    op.drop_table("ai_teacher_live_settings")

    op.drop_index("ix_ai_teacher_personas_user_id", table_name="ai_teacher_personas")
    op.drop_table("ai_teacher_personas")

    op.drop_index("ix_ai_teacher_memories_user_id", table_name="ai_teacher_memories")
    op.drop_table("ai_teacher_memories")

    op.drop_index("ix_ai_teacher_sessions_user_id", table_name="ai_teacher_sessions")
    op.drop_table("ai_teacher_sessions")

    op.drop_index("ix_ai_teacher_profiles_user_id", table_name="ai_teacher_profiles")
    op.drop_table("ai_teacher_profiles")