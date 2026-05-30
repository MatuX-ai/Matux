"""create AI Edu course tables

Revision ID: ai_edu_001
Revises: previous_revision
Create Date: 2026-03-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'ai_edu_001'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """升级数据库结构"""

    # 创建 AI 课程模块表
    op.create_table('ai_edu_modules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('grade_ranges', sa.JSON(), nullable=True),
        sa.Column('expected_lessons', sa.Integer(), nullable=True),
        sa.Column('expected_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('prerequisites', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('display_order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('module_code')
    )
    op.create_index(op.f('ix_ai_edu_modules_module_code'), 'ai_edu_modules', ['module_code'], unique=True)

    # 创建 AI 课程课时表
    op.create_table('ai_edu_lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=False),
        sa.Column('lesson_code', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('subtitle', sa.String(length=200), nullable=True),
        sa.Column('content_type', sa.String(length=50), nullable=True),
        sa.Column('content_url', sa.String(length=500), nullable=True),
        sa.Column('resources', sa.JSON(), nullable=True),
        sa.Column('learning_objectives', sa.JSON(), nullable=True),
        sa.Column('knowledge_points', sa.JSON(), nullable=True),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('has_quiz', sa.Boolean(), nullable=True, default=False),
        sa.Column('quiz_passing_score', sa.Float(), nullable=True, default=80.0),
        sa.Column('has_practice', sa.Boolean(), nullable=True, default=False),
        sa.Column('practice_type', sa.String(length=50), nullable=True),
        sa.Column('base_points', sa.Integer(), nullable=True, default=20),
        sa.Column('bonus_conditions', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('display_order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['module_id'], ['ai_edu_modules.id'], )
    )
    op.create_index(op.f('ix_ai_edu_lessons_lesson_code'), 'ai_edu_lessons', ['lesson_code'], unique=True)

    # 创建 AI 课程奖励规则表
    op.create_table('ai_edu_reward_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_code', sa.String(length=50), nullable=False),
        sa.Column('rule_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.Enum('theory', 'practice', 'project', 'achievement', 'streak', 'special'), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=True),
        sa.Column('base_points', sa.Integer(), nullable=True, default=20),
        sa.Column('grade_multipliers', sa.JSON(), nullable=True),
        sa.Column('quality_coefficients', sa.JSON(), nullable=True),
        sa.Column('time_bonus_enabled', sa.Boolean(), nullable=True, default=False),
        sa.Column('standard_time_minutes', sa.Integer(), nullable=True),
        sa.Column('time_bonus_rate', sa.Float(), nullable=True, default=0.5),
        sa.Column('streak_bonus_enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('streak_multipliers', sa.JSON(), nullable=True),
        sa.Column('achievement_id', sa.Integer(), nullable=True),
        sa.Column('trigger_conditions', sa.JSON(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, default=100),
        sa.Column('cooldown_seconds', sa.Integer(), nullable=True, default=0),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['module_id'], ['ai_edu_modules.id'], ),
        sa.UniqueConstraint('rule_code')
    )
    op.create_index(op.f('ix_ai_edu_reward_rules_rule_code'), 'ai_edu_reward_rules', ['rule_code'], unique=True)

    # 创建 AI 课程成就徽章表
    op.create_table('ai_edu_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('achievement_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon_url', sa.String(length=255), nullable=True),
        sa.Column('rarity', sa.Enum('common', 'rare', 'epic', 'legendary', 'mythic'), nullable=True, default='common'),
        sa.Column('unlock_conditions', sa.JSON(), nullable=True),
        sa.Column('points_reward', sa.Integer(), nullable=True, default=100),
        sa.Column('integral_reward', sa.Integer(), nullable=True, default=0),
        sa.Column('special_rewards', sa.JSON(), nullable=True),
        sa.Column('unlocked_count', sa.Integer(), nullable=True, default=0),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('display_order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('achievement_code')
    )
    op.create_index(op.f('ix_ai_edu_achievements_achievement_code'), 'ai_edu_achievements', ['achievement_code'], unique=True)

    # 创建用户 AI 课程成就记录表
    op.create_table('user_ai_edu_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), nullable=True),
        sa.Column('progress_data', sa.JSON(), nullable=True),
        sa.Column('points_claimed', sa.Boolean(), nullable=True, default=False),
        sa.Column('claimed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['achievement_id'], ['ai_edu_achievements.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_index(op.f('ix_user_ai_edu_achievements_user_id'), 'user_ai_edu_achievements', ['user_id'])

    # 创建 AI 课程学习进度表
    op.create_table('ai_edu_learning_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('progress_percentage', sa.Integer(), nullable=True, default=0),
        sa.Column('status', sa.String(length=20), nullable=True, default='not_started'),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True, default=0),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('completion_time', sa.DateTime(), nullable=True),
        sa.Column('last_accessed_time', sa.DateTime(), nullable=True),
        sa.Column('quiz_score', sa.Float(), nullable=True),
        sa.Column('code_quality_score', sa.Float(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=True, default=1),
        sa.Column('points_earned', sa.Integer(), nullable=True, default=0),
        sa.Column('achievements_unlocked', sa.JSON(), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['lesson_id'], ['ai_edu_lessons.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_index(op.f('ix_ai_edu_learning_progress_user_id'), 'ai_edu_learning_progress', ['user_id'])

    # 创建 AI 课程积分交易记录表
    op.create_table('ai_edu_points_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=True),
        sa.Column('points_amount', sa.Integer(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('source_description', sa.String(length=255), nullable=True),
        sa.Column('base_points', sa.Integer(), nullable=True, default=0),
        sa.Column('grade_multiplier', sa.Float(), nullable=True, default=1.0),
        sa.Column('quality_bonus', sa.Integer(), nullable=True, default=0),
        sa.Column('streak_bonus', sa.Integer(), nullable=True, default=0),
        sa.Column('final_points', sa.Integer(), nullable=True),
        sa.Column('blockchain_tx_hash', sa.String(length=100), nullable=True),
        sa.Column('block_number', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_index(op.f('ix_ai_edu_points_transactions_user_id'), 'ai_edu_points_transactions', ['user_id'])

    # 创建 AI 课程连胜计数器表
    op.create_table('ai_edu_streak_counters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('streak_type', sa.String(length=50), nullable=True),
        sa.Column('current_streak', sa.Integer(), nullable=True, default=0),
        sa.Column('best_streak', sa.Integer(), nullable=True, default=0),
        sa.Column('last_activity_date', sa.DateTime(), nullable=True),
        sa.Column('total_bonus_earned', sa.Integer(), nullable=True, default=0),
        sa.Column('last_reward_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], )
    )
    op.create_index(op.f('ix_ai_edu_streak_counters_user_id'), 'ai_edu_streak_counters', ['user_id'])


def downgrade() -> None:
    """降级数据库结构"""
    op.drop_index(op.f('ix_ai_edu_streak_counters_user_id'), table_name='ai_edu_streak_counters')
    op.drop_table('ai_edu_streak_counters')
    op.drop_index(op.f('ix_ai_edu_points_transactions_user_id'), table_name='ai_edu_points_transactions')
    op.drop_table('ai_edu_points_transactions')
    op.drop_index(op.f('ix_ai_edu_learning_progress_user_id'), table_name='ai_edu_learning_progress')
    op.drop_table('ai_edu_learning_progress')
    op.drop_index(op.f('ix_user_ai_edu_achievements_user_id'), table_name='user_ai_edu_achievements')
    op.drop_table('user_ai_edu_achievements')
    op.drop_index(op.f('ix_ai_edu_achievements_achievement_code'), table_name='ai_edu_achievements')
    op.drop_table('ai_edu_achievements')
    op.drop_index(op.f('ix_ai_edu_reward_rules_rule_code'), table_name='ai_edu_reward_rules')
    op.drop_table('ai_edu_reward_rules')
    op.drop_index(op.f('ix_ai_edu_lessons_lesson_code'), table_name='ai_edu_lessons')
    op.drop_table('ai_edu_lessons')
    op.drop_index(op.f('ix_ai_edu_modules_module_code'), table_name='ai_edu_modules')
    op.drop_table('ai_edu_modules')
