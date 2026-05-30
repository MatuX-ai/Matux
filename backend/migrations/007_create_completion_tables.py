"""创建用户代码历史记录和补全缓存表"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class UserCodeHistory(Base):
    """用户代码历史记录表"""

    __tablename__ = "user_code_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    code_snippet = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    language = Column(String(50), nullable=False, index=True)
    usage_count = Column(Integer, default=1, nullable=False)
    last_used = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 索引优化查询性能
    __table_args__ = (
        Index("idx_user_language", "user_id", "language"),
        Index("idx_last_used", "last_used"),
        Index("idx_usage_count", "usage_count"),
    )


class CompletionCache(Base):
    """代码补全缓存表"""

    __tablename__ = "completion_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prefix_hash = Column(String(64), nullable=False, unique=True, index=True)
    completions_json = Column(Text, nullable=False)  # JSON格式存储补全结果
    confidence_scores_json = Column(Text, nullable=False)  # JSON格式存储置信度分数
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    hit_count = Column(Integer, default=0, nullable=False)
    language = Column(String(50), nullable=True, index=True)

    # 索引优化缓存查找
    __table_args__ = (
        Index("idx_expires_at", "expires_at"),
        Index("idx_language_prefix", "language", "prefix_hash"),
    )


def upgrade(migrate_engine):
    """应用迁移"""
    Base.metadata.create_all(migrate_engine)


def downgrade(migrate_engine):
    """回滚迁移"""
    # 删除表
    UserCodeHistory.__table__.drop(migrate_engine)
    CompletionCache.__table__.drop(migrate_engine)
