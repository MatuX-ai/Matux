"""
组织级错误日志收集路由（前端兼容路径，数据库持久化）

提供前端 ErrorLoggerService 调用的路径:
- POST /api/v1/org/{org_id}/logs/error - 批量上报前端错误日志

与 backend/routes/error_log_routes.py 的区别:
- 原 error_log_routes.py 的端点位于 /logs/error（无 org_id 前缀），与前端期望路径不匹配
- 本文件使用与前端一致的 /api/v1/org/{org_id}/logs/error 路径
- payload 格式兼容前端: { logs: [...] }

[重构说明]
原实现使用 _frontend_error_logs 内存列表，重启即丢失。
现统一写入 frontend_error_logs 表（log_format='frontend' 字段标记）。

Author: P1-Backend 修复
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.error_log import FrontendErrorLog
from utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/org/{org_id}/logs",
    tags=["错误日志（前端兼容路径）"],
)


# ==================== Pydantic 模型 ====================


class FrontendErrorLogEntry(BaseModel):
    """单条前端错误日志（前端 ErrorLoggerService 直接发送格式）

    前端兼容契约 (org 级别上报格式):
    字段集 {message, stack, url, userAgent, userId, timestamp, source}
    是前端 ErrorLoggerService 当前版本发送的格式。
    url/userAgent 必填, 其它字段可选。
    不可破坏现有字段; 新增字段一律 Optional 并提供默认值。
    """

    message: str = Field(..., description="错误消息")
    stack: Optional[str] = Field(None, description="错误堆栈")
    url: str = Field(..., description="错误发生的 URL")
    userAgent: str = Field(..., description="浏览器 userAgent")
    userId: Optional[str] = Field(None, description="用户 ID（前端使用 string）")
    timestamp: str = Field(..., description="ISO 时间戳")
    source: str = Field(
        ..., description="错误来源: window.error / unhandledrejection / manual",
    )


class FrontendErrorLogBatchRequest(BaseModel):
    """前端批量错误日志上报请求"""

    logs: List[FrontendErrorLogEntry] = Field(..., description="错误日志列表")


class FrontendErrorLogResponse(BaseModel):
    """前端错误日志上报响应"""

    success: bool
    message: str
    logged_count: int
    failed_count: int = 0


# ==================== 辅助函数 ====================


def _truncate(value: Optional[str], max_len: int = 2000) -> Optional[str]:
    """截断过长的字符串字段，避免日志存储被异常值撑爆"""
    if value is None:
        return None
    if len(value) <= max_len:
        return value
    return value[:max_len] + f"...[截断, 原始长度 {len(value)}]"


def _parse_iso(timestamp: str) -> Optional[datetime]:
    """兼容前端多种 ISO 时间格式解析"""
    if not timestamp:
        return None
    try:
        ts = timestamp.strip()
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (ValueError, AttributeError):
        return None


def _severity_for_source(source: str) -> str:
    """根据错误来源推导严重等级"""
    mapping = {
        "window.error": "error",
        "unhandledrejection": "error",
        "manual": "warning",
    }
    return mapping.get(source, "warning")


# ==================== API 端点 ====================


@router.post("/error", response_model=FrontendErrorLogResponse)
async def collect_frontend_error_logs(
    org_id: int,
    request: FrontendErrorLogBatchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    收集前端错误日志（前端 ErrorLoggerService 调用入口）

    前端调用路径:
        POST /api/v1/org/{org_id}/logs/error
        Body: { logs: [...] }

    说明:
        - 此端点不需要鉴权（前端匿名上报）
        - 日志持久化到 frontend_error_logs 表，重启后端不丢失
        - 单条字段长度超过限制自动截断，避免日志爆炸
    """
    rows: List[FrontendErrorLog] = []
    logged = 0
    failed = 0

    for entry in request.logs:
        try:
            occurred_at = _parse_iso(entry.timestamp) or datetime.utcnow()
            row = FrontendErrorLog(
                org_id=org_id,
                user_id=entry.userId or "anonymous",
                log_type="JS_ERROR",
                severity=_severity_for_source(entry.source),
                log_format="frontend",
                source=entry.source,
                message=_truncate(entry.message, 2000) or "",
                stack=_truncate(entry.stack, 8000),
                url=_truncate(entry.url, 500),
                user_agent=_truncate(entry.userAgent, 500),
                extra={
                    "original_timestamp": entry.timestamp,
                },
                occurred_at=occurred_at,
            )
            rows.append(row)
            logged += 1
        except Exception as e:
            logger.error(f"Failed to process one error entry: {e}")
            failed += 1

    if rows:
        try:
            db.add_all(rows)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed to persist frontend error logs: {e}", exc_info=True,
            )
            # 即便出错也返回 200，避免阻塞前端主流程
            return FrontendErrorLogResponse(
                success=False,
                message=f"后端收集失败: {str(e)}",
                logged_count=0,
                failed_count=len(request.logs),
            )

    # 写一条后端日志（用于运维观察）
    for entry in request.logs:
        logger.warning(
            f"[前端错误][org={org_id}] {entry.source}: {entry.message[:200]}"
        )

    return FrontendErrorLogResponse(
        success=True,
        message=f"成功收集 {logged} 条错误日志" + (
            f"，{failed} 条失败" if failed else ""
        ),
        logged_count=logged,
        failed_count=failed,
    )


@router.get("/error", response_model=List[Dict[str, Any]])
async def get_frontend_error_logs(
    org_id: int,
    limit: int = 100,
    source: Optional[str] = None,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    查询前端错误日志（运维/调试使用）

    前端不会调用，但方便后端排查问题。
    """
    try:
        conditions = [
            FrontendErrorLog.org_id == org_id,
            FrontendErrorLog.log_format == "frontend",
        ]
        if source:
            conditions.append(FrontendErrorLog.source == source)
        if user_id:
            conditions.append(FrontendErrorLog.user_id == user_id)

        stmt = (
            select(FrontendErrorLog)
            .where(and_(*conditions))
            .order_by(FrontendErrorLog.received_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()
        return [row.to_dict() for row in rows]
    except Exception as e:
        logger.error(f"Failed to query frontend error logs: {e}", exc_info=True)
        return []


@router.get("/stats", response_model=Dict[str, Any])
async def get_frontend_error_stats(
    org_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取前端错误统计信息"""
    try:
        base = and_(
            FrontendErrorLog.org_id == org_id,
            FrontendErrorLog.log_format == "frontend",
        )

        # 总条数
        total_stmt = select(func.count(FrontendErrorLog.id)).where(base)
        total = (await db.execute(total_stmt)).scalar() or 0

        # 今日条数（UTC 日切分）
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        today_stmt = (
            select(func.count(FrontendErrorLog.id))
            .where(base, FrontendErrorLog.received_at >= today_start)
        )
        today_count = (await db.execute(today_stmt)).scalar() or 0

        # 按 source 统计
        source_stmt = (
            select(FrontendErrorLog.source, func.count(FrontendErrorLog.id))
            .where(base)
            .group_by(FrontendErrorLog.source)
        )
        source_rows = (await db.execute(source_stmt)).all()
        source_counts = {
            (row[0] or "unknown"): row[1] for row in source_rows
        }

        return {
            "org_id": org_id,
            "total_count": total,
            "today_count": today_count,
            "source_distribution": source_counts,
        }
    except Exception as e:
        logger.error(f"Failed to get frontend error stats: {e}", exc_info=True)
        return {
            "org_id": org_id,
            "total_count": 0,
            "today_count": 0,
            "source_distribution": {},
            "error": str(e),
        }
