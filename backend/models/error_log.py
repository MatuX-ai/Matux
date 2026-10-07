"""
前端错误日志数据库模型

用于生产环境持久化存储前端上报的错误日志，替代原有的内存列表实现。

设计要点:
1. 兼容两种前端上报格式：
   - 旧版 error_log_routes.py: type/code/status/url/message/timestamp/details
   - 新版 org_error_log_routes.py: source/userAgent/stack/userId
2. 通过 `log_format` 字段区分两条上报路径，便于运维溯源
3. `extra` (JSON) 字段保留原始 payload，确保细节不丢失
4. 索引: org_id、user_id、log_type、occurred_at、log_format
"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from utils.database import Base


# ==================== SQLAlchemy ORM 模型 ====================


class FrontendErrorLog(Base):
    """
    前端错误日志表

    存储前端 ErrorLoggerService / 上报代理提交的运行时错误。
    原 error_log_routes.py / org_error_log_routes.py 中的内存 List[Dict]
    全部切换为写入本表，避免后端重启后日志丢失以及多 Worker 共享问题。
    """

    __tablename__ = "frontend_error_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # 多租户隔离
    org_id = Column(
        Integer, nullable=False, index=True,
        default=1, server_default="1",
    )

    # 用户关联（前端可能未登录，使用 nullable）
    user_id = Column(String(64), nullable=True, index=True)

    # 错误分类与级别
    log_type = Column(
        String(64), nullable=False, index=True,
        default="UNKNOWN", server_default="UNKNOWN",
        comment="错误类型: NETWORK/HTTP/AUTH/VALIDATION/JS_ERROR/PROMISE_REJECTION/...",
    )
    severity = Column(
        String(16), nullable=False,
        default="warning", server_default="warning",
        comment="严重等级: info/warning/error/critical",
    )

    # 错误来源（区分两条上报路径）
    log_format = Column(
        String(32), nullable=False,
        default="legacy", server_default="legacy",
        comment="上报格式: legacy(error_log_routes) / frontend(org_error_log_routes)",
    )
    source = Column(
        String(64), nullable=True,
        comment="前端 source 字段: window.error / unhandledrejection / manual",
    )

    # 主要描述
    message = Column(Text, nullable=False)
    code = Column(String(64), nullable=True, comment="应用层错误码")
    http_status = Column(Integer, nullable=True, comment="HTTP 状态码")

    # 上下文信息
    url = Column(String(2048), nullable=True, comment="错误发生页面 URL")
    stack = Column(Text, nullable=True, comment="JS 堆栈（仅新格式有）")
    user_agent = Column(String(1024), nullable=True, comment="浏览器 UA")

    # 时间信息
    occurred_at = Column(
        DateTime(timezone=True), nullable=False, index=True,
        comment="前端事件时间戳",
    )
    received_at = Column(
        DateTime(timezone=True), server_default=func.now(),
        nullable=False, comment="后端接收时间",
    )

    # 原始数据兜底，避免字段遗漏导致信息丢失
    extra = Column(
        JSON, nullable=True,
        comment="原始 payload 完整快照，便于事后扩展字段",
    )

    # 复合索引：按 org_id + 时间窗口查询最常用
    __table_args__ = (
        Index(
            "ix_frontend_error_logs_org_received",
            "org_id", "received_at",
        ),
        Index(
            "ix_frontend_error_logs_org_type",
            "org_id", "log_type", "received_at",
        ),
    )

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（兼容前端 / 历史内存结构）"""
        return {
            "id": self.id,
            "org_id": self.org_id,
            "user_id": self.user_id,
            "type": self.log_type,
            "severity": self.severity,
            "log_format": self.log_format,
            "source": self.source,
            "message": self.message,
            "code": self.code,
            "status": self.http_status,
            "url": self.url,
            "stack": self.stack,
            "user_agent": self.user_agent,
            "timestamp": (
                self.occurred_at.isoformat() if self.occurred_at else None
            ),
            "received_at": (
                self.received_at.isoformat() if self.received_at else None
            ),
            "details": self.extra,
        }


# ==================== Pydantic API 模型 ====================


class FrontendErrorLogResponse(BaseModel):
    """错误日志响应模型"""

    id: int
    org_id: int
    user_id: Optional[str] = None
    type: str
    severity: str
    log_format: str
    source: Optional[str] = None
    message: str
    code: Optional[str] = None
    status: Optional[int] = None
    url: Optional[str] = None
    stack: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: str
    received_at: Optional[str] = None
    details: Optional[Any] = None

    class Config:
        from_attributes = True


class FrontendErrorLogStats(BaseModel):
    """错误日志统计响应"""

    org_id: int
    total_count: int = Field(0, description="该组织累计条数")
    today_count: int = Field(0, description="今日条数")
    type_distribution: Dict[str, int] = Field(
        default_factory=dict, description="按错误类型分布",
    )
    source_distribution: Dict[str, int] = Field(
        default_factory=dict, description="按前端 source 分布",
    )
