"""
错误日志收集路由（持久化存储）

提供前端错误日志的收集、存储和分析功能。

[重构说明]
原实现使用进程内 List[Dict] 存储，重启即丢失，且多 Worker 场景下无法共享。
现统一写入 frontend_error_logs 表，符合生产环境的可观测性要求。

Author: P1-Backend 修复
"""

from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.error_log import FrontendErrorLog
from utils.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logs", tags=["错误日志管理"])


# ==================== 数据模型 ====================


class ErrorLogEntry(BaseModel):
    """单条错误日志

    前端兼容契约 v1 (legacy 错误日志格式):
    字段集 {type, message, code, status, url, timestamp, details}
    是前端 ErrorLoggerService 早期版本发送的格式，**不可破坏**。
    如需新增必填字段, 请新增到 ErrorLogBatchRequest 而非 Entry,
    以保持向后兼容。新增可选字段统一使用 Optional + 默认值 None。
    """

    type: str = Field(..., description="错误类型 (NETWORK/HTTP/VALIDATION/AUTH 等)")
    message: str = Field(..., description="错误消息")
    code: Optional[str] = Field(None, description="错误代码")
    status: Optional[int] = Field(None, description="HTTP 状态码")
    url: Optional[str] = Field(None, description="请求 URL")
    timestamp: str = Field(..., description="时间戳 (ISO 格式)")
    details: Optional[Any] = Field(None, description="详细错误信息")


class ErrorLogBatchRequest(BaseModel):
    """批量错误日志提交"""

    errors: List[ErrorLogEntry] = Field(..., description="错误日志列表")
    user_id: int = Field(..., description="用户 ID")
    org_id: int = Field(..., description="组织 ID")


class ErrorLogResponse(BaseModel):
    """响应模型"""

    success: bool
    message: str
    logged_count: int


class ErrorLogClearResponse(BaseModel):
    """清理响应模型"""

    success: bool
    message: str
    deleted_count: int


# ==================== 辅助函数 ====================


def _severity_for(error_type: str) -> str:
    """根据错误类型推导严重等级"""
    mapping = {
        "NETWORK": "error",
        "SERVER": "error",
        "HTTP": "warning",
        "AUTH": "warning",
        "PERMISSION": "info",
        "VALIDATION": "info",
        "NOT_FOUND": "info",
        "UNKNOWN": "warning",
    }
    return mapping.get(error_type, "warning")


def _parse_iso(timestamp: str) -> Optional[datetime]:
    """兼容前端多种 ISO 时间格式解析"""
    if not timestamp:
        return None
    try:
        # 支持带 Z 与不带时区的格式
        ts = timestamp.strip()
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except (ValueError, AttributeError):
        return None


def _truncate(value: Optional[str], max_len: int) -> Optional[str]:
    """截断过长的字符串字段，避免日志存储被异常值撑爆"""
    if value is None:
        return None
    if len(value) <= max_len:
        return value
    return value[:max_len] + f"...[截断, 原始长度 {len(value)}]"


# ==================== API 端点 ====================


@router.post("/error", response_model=ErrorLogResponse)
async def collect_error_logs(
    request: ErrorLogBatchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    收集前端错误日志

    Args:
        request: 批量错误日志请求
        db: 异步数据库会话

    Returns:
        处理结果
    """
    try:
        rows: List[FrontendErrorLog] = []
        for error in request.errors:
            occurred_at = _parse_iso(error.timestamp) or datetime.utcnow()
            row = FrontendErrorLog(
                org_id=request.org_id,
                user_id=str(request.user_id),
                log_type=error.type or "UNKNOWN",
                severity=_severity_for(error.type),
                log_format="legacy",
                message=_truncate(error.message, 4000) or "",
                code=error.code,
                http_status=error.status,
                url=_truncate(error.url, 2000),
                extra={
                    "details": error.details,
                    "original_timestamp": error.timestamp,
                },
                occurred_at=occurred_at,
            )
            rows.append(row)

        if rows:
            db.add_all(rows)
            await db.commit()

        # 同步记录到后端日志（便于运维观察）
        for error in request.errors:
            level = _severity_for(error.type)
            log_fn = {
                "error": logger.error,
                "warning": logger.warning,
                "info": logger.info,
            }.get(level, logger.warning)
            log_fn(
                f"[前端错误] 用户{request.user_id}: {error.message} "
                f"(类型:{error.type}, URL:{error.url})"
            )

        return ErrorLogResponse(
            success=True,
            message=f"成功收集 {len(request.errors)} 条错误日志",
            logged_count=len(request.errors),
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"收集错误日志失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="收集错误日志失败")


@router.get("/error", response_model=List[Dict[str, Any]])
async def get_error_logs(
    org_id: int = Query(1, description="组织 ID"),
    user_id: Optional[int] = Query(None, description="用户 ID（可选）"),
    error_type: Optional[str] = Query(None, description="错误类型（可选）"),
    start_date: Optional[str] = Query(None, description="开始日期 (ISO 格式)"),
    end_date: Optional[str] = Query(None, description="结束日期 (ISO 格式)"),
    limit: int = Query(100, description="返回数量限制", le=1000),
    db: AsyncSession = Depends(get_db),
):
    """
    查询错误日志

    Args:
        org_id: 组织 ID
        user_id: 用户 ID（可选）
        error_type: 错误类型（可选）
        start_date: 开始日期（ISO 格式）
        end_date: 结束日期（ISO 格式）
        limit: 返回数量限制

    Returns:
        错误日志列表
    """
    try:
        conditions = [FrontendErrorLog.org_id == org_id]

        if user_id is not None:
            conditions.append(FrontendErrorLog.user_id == str(user_id))

        if error_type:
            conditions.append(FrontendErrorLog.log_type == error_type)

        start_dt = _parse_iso(start_date) if start_date else None
        end_dt = _parse_iso(end_date) if end_date else None
        if start_dt:
            conditions.append(FrontendErrorLog.occurred_at >= start_dt)
        if end_dt:
            conditions.append(FrontendErrorLog.occurred_at <= end_dt)

        stmt = (
            select(FrontendErrorLog)
            .where(and_(*conditions))
            .order_by(FrontendErrorLog.occurred_at.desc())
            .limit(int(limit))
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()
        return [row.to_dict() for row in rows]

    except Exception as e:
        logger.error(f"查询错误日志失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="查询错误日志失败")


@router.get("/stats", response_model=Dict[str, Any])
async def get_error_statistics(
    org_id: int = Query(1, description="组织 ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取错误统计信息

    Args:
        org_id: 组织 ID

    Returns:
        统计数据
    """
    try:
        # 总条数
        total_stmt = (
            select(func.count(FrontendErrorLog.id))
            .where(FrontendErrorLog.org_id == org_id)
        )
        total_count = (await db.execute(total_stmt)).scalar() or 0

        # 今日条数（按 UTC 日切分）
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        today_stmt = (
            select(func.count(FrontendErrorLog.id))
            .where(
                FrontendErrorLog.org_id == org_id,
                FrontendErrorLog.received_at >= today_start,
            )
        )
        today_count = (await db.execute(today_stmt)).scalar() or 0

        # 按类型分布
        type_stmt = (
            select(FrontendErrorLog.log_type, func.count(FrontendErrorLog.id))
            .where(FrontendErrorLog.org_id == org_id)
            .group_by(FrontendErrorLog.log_type)
        )
        type_rows = (await db.execute(type_stmt)).all()
        type_counts = {row[0]: row[1] for row in type_rows}

        # 排序取前 5
        top_errors = sorted(
            type_counts.items(), key=lambda x: x[1], reverse=True,
        )[:5]

        return {
            "total_count": total_count,
            "today_count": today_count,
            "type_distribution": type_counts,
            "top_error_types": [{"type": t, "count": c} for t, c in top_errors],
        }

    except Exception as e:
        logger.error(f"获取错误统计失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取统计数据失败")


@router.delete("/error", response_model=ErrorLogClearResponse)
async def clear_error_logs(
    org_id: int = Query(1, description="组织 ID"),
    older_than_days: int = Query(
        30, description="清理多少天前的日志",
        ge=1, le=365,
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    清理旧日志

    Args:
        org_id: 组织 ID
        older_than_days: 清理多少天前的日志（1-365）

    Returns:
        清理结果
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        # 先统计再删除，返回真实影响条数
        count_stmt = (
            select(func.count(FrontendErrorLog.id))
            .where(
                FrontendErrorLog.org_id == org_id,
                FrontendErrorLog.occurred_at < cutoff_date,
            )
        )
        deleted_count = (await db.execute(count_stmt)).scalar() or 0

        if deleted_count > 0:
            stmt = (
                delete(FrontendErrorLog)
                .where(
                    FrontendErrorLog.org_id == org_id,
                    FrontendErrorLog.occurred_at < cutoff_date,
                )
            )
            await db.execute(stmt)
            await db.commit()

        return ErrorLogClearResponse(
            success=True,
            message=f"清理了 {deleted_count} 条旧日志",
            deleted_count=deleted_count,
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"清理错误日志失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="清理日志失败")
