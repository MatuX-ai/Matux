"""P3-C 社交化分享数据库迁移

Revision ID: 20261009_p3c_share
Revises: 20261009_p3d1_ai_teacher_persistence  # 接续 P3-D-1
Create Date: 2026-10-09

P3-C 阶段：创建社交化分享相关表
- share_cards: 分享卡片（短链、二维码、统计）
- invite_codes: 邀请码（生成、限制、奖励）
- invite_records: 邀请记录（使用留痕、奖励发放）
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20261009_p3c_share"
down_revision = "20261009_p3d1_ai_teacher_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构 - 创建社交化分享相关表"""

    # ==================== share_cards（分享卡片）====================
    op.create_table(
        "share_cards",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("card_type", sa.String(50), nullable=False, index=True,
                  comment="卡片类型：achievement/course/user_profile/learning_record"),
        sa.Column("target_id", sa.Integer(), nullable=False, index=True,
                  comment="目标对象 ID"),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False,
                  comment="创建者用户 ID"),
        sa.Column("title", sa.String(200), nullable=False, comment="卡片标题"),
        sa.Column("subtitle", sa.String(500), nullable=True, comment="卡片副标题"),
        sa.Column("cover_image", sa.String(500), nullable=True, comment="封面图 URL"),
        sa.Column("description", sa.Text(), nullable=True, comment="描述文案"),
        sa.Column("metadata", sa.JSON(), nullable=True, comment="扩展元数据"),
        sa.Column("short_code", sa.String(16), nullable=False, unique=True, index=True,
                  comment="短链代码（8 字符 base62）"),
        sa.Column("qr_code_path", sa.String(500), nullable=True,
                  comment="二维码图片存储路径"),
        sa.Column("view_count", sa.Integer(), nullable=True, server_default="0",
                  comment="浏览次数"),
        sa.Column("share_count", sa.Integer(), nullable=True, server_default="0",
                  comment="分享次数"),
        sa.Column("status", sa.String(20), nullable=True, server_default="active",
                  comment="状态：active/expired/disabled"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True,
                  comment="过期时间（None 永不过期）"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), onupdate=sa.func.now(),
                  comment="更新时间"),
    )
    op.create_index("idx_share_cards_type_target", "share_cards",
                    ["card_type", "target_id"])
    op.create_index("idx_share_cards_creator_status", "share_cards",
                    ["creator_id", "status"])

    # ==================== invite_codes（邀请码）====================
    op.create_table(
        "invite_codes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(16), nullable=False, unique=True, index=True,
                  comment="邀请码（8 字符 base62）"),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False,
                  comment="生成者用户 ID"),
        sa.Column("usage_limit", sa.Integer(), nullable=True,
                  comment="使用次数上限（NULL 无限）"),
        sa.Column("used_count", sa.Integer(), nullable=True, server_default="0",
                  comment="已使用次数"),
        sa.Column("reward_type", sa.String(20), nullable=True, server_default="points",
                  comment="奖励类型：points/discount/gift"),
        sa.Column("reward_value", sa.Integer(), nullable=True, server_default="100",
                  comment="奖励值"),
        sa.Column("channel", sa.String(50), nullable=True,
                  comment="推广渠道：wechat/weibo/x/link"),
        sa.Column("status", sa.String(20), nullable=True, server_default="active",
                  comment="状态：active/exhausted/expired/disabled"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True,
                  comment="过期时间"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), comment="创建时间"),
    )
    op.create_index("idx_invite_codes_creator_status", "invite_codes",
                    ["creator_id", "status"])

    # ==================== invite_records（邀请记录）====================
    op.create_table(
        "invite_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code_id", sa.Integer(), sa.ForeignKey("invite_codes.id"), nullable=False,
                  comment="邀请码 ID"),
        sa.Column("inviter_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False,
                  comment="邀请人用户 ID"),
        sa.Column("invitee_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True,
                  comment="被邀请人用户 ID（NULL 直到注册）"),
        sa.Column("status", sa.String(20), nullable=True, server_default="pending",
                  comment="状态：pending/registered/rewarded"),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True,
                  comment="注册时间"),
        sa.Column("rewarded_at", sa.DateTime(timezone=True), nullable=True,
                  comment="奖励发放时间"),
        sa.Column("extra_metadata", sa.JSON(), nullable=True, comment="扩展元数据（IP、设备等）"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), comment="创建时间"),
    )
    op.create_index("idx_invite_records_inviter", "invite_records", ["inviter_id"])
    op.create_index("idx_invite_records_code_status", "invite_records",
                    ["code_id", "status"])


def downgrade() -> None:
    """回滚数据库结构"""
    op.drop_index("idx_invite_records_code_status", table_name="invite_records")
    op.drop_index("idx_invite_records_inviter", table_name="invite_records")
    op.drop_table("invite_records")

    op.drop_index("idx_invite_codes_creator_status", table_name="invite_codes")
    op.drop_table("invite_codes")

    op.drop_index("idx_share_cards_creator_status", table_name="share_cards")
    op.drop_index("idx_share_cards_type_target", table_name="share_cards")
    op.drop_table("share_cards")