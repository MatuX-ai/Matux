"""
错误日志收集路由

提供前端错误日志的收集、存储和分析功能
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logs", tags=["错误日志管理"])


# ==================== 数据模型 ====================


class ErrorLogEntry(BaseModel):
    """单条错误日志"""

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


# ==================== 内存存储（生产环境应使用数据库） ====================


error_logs: List[Dict[str, Any]] = []
MAX_LOGS = 10000  # 最多保留 10000 条日志


# ==================== API 端点 ====================


@router.post("/error", response_model=ErrorLogResponse)
async def collect_error_logs(request: ErrorLogBatchRequest):
    """
    收集前端错误日志

    Args:
        request: 批量错误日志请求

    Returns:
        处理结果
    """
    try:
        # 转换并存储日志
        for error in request.errors:
            log_entry = {
                "id": len(error_logs) + 1,
                "org_id": request.org_id,
                "user_id": request.user_id,
                "type": error.type,
                "message": error.message,
                "code": error.code,
                "status": error.status,
                "url": error.url,
                "timestamp": error.timestamp,
                "details": error.details,
                "created_at": datetime.now().isoformat(),
            }

            error_logs.append(log_entry)

            # 记录到后端日志
            log_level = _get_log_level(error.type)
            logger.log(
                log_level,
                f"[前端错误] 用户{request.user_id}: {error.message} "
                f"(类型:{error.type}, URL:{error.url})",
            )

        # 清理过期日志
        if len(error_logs) > MAX_LOGS:
            error_logs[:] = error_logs[-MAX_LOGS:]

        return ErrorLogResponse(
            success=True,
            message=f"成功收集 {len(request.errors)} 条错误日志",
            logged_count=len(request.errors),
        )

    except Exception as e:
        logger.error(f"收集错误日志失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="收集错误日志失败")


@router.get("/error", response_model=List[Dict[str, Any]])
async def get_error_logs(
    org_id: int = 1,
    user_id: Optional[int] = None,
    error_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
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
        filtered_logs = error_logs.copy()

        # 按组织过滤
        filtered_logs = [log for log in filtered_logs if log["org_id"] == org_id]

        # 按用户过滤
        if user_id:
            filtered_logs = [log for log in filtered_logs if log["user_id"] == user_id]

        # 按错误类型过滤
        if error_type:
            filtered_logs = [log for log in filtered_logs if log["type"] == error_type]

        # 按日期范围过滤
        if start_date:
            filtered_logs = [
                log for log in filtered_logs if log["timestamp"] >= start_date
            ]
        if end_date:
            filtered_logs = [
                log for log in filtered_logs if log["timestamp"] <= end_date
            ]

        # 按时间倒序排序
        filtered_logs.sort(key=lambda x: x["timestamp"], reverse=True)

        # 限制返回数量
        return filtered_logs[:limit]

    except Exception as e:
        logger.error(f"查询错误日志失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="查询错误日志失败")


@router.get("/stats", response_model=Dict[str, Any])
async def get_error_statistics(org_id: int = 1):
    """
    获取错误统计信息

    Args:
        org_id: 组织 ID

    Returns:
        统计数据
    """
    try:
        org_logs = [log for log in error_logs if log["org_id"] == org_id]

        # 按类型统计
        type_counts: Dict[str, int] = {}
        for log in org_logs:
            error_type = log["type"]
            type_counts[error_type] = type_counts.get(error_type, 0) + 1

        # 计算总数和今日数量
        total_count = len(org_logs)
        today = datetime.now().date().isoformat()
        today_count = sum(1 for log in org_logs if log["timestamp"].startswith(today))

        # 最常见的错误
        top_errors = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_count": total_count,
            "today_count": today_count,
            "type_distribution": type_counts,
            "top_error_types": [{"type": t, "count": c} for t, c in top_errors],
        }

    except Exception as e:
        logger.error(f"获取错误统计失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取统计数据失败")


@router.delete("/error", response_model=Dict[str, Any])
async def clear_error_logs(org_id: int = 1, older_than_days: int = 30):
    """
    清理旧日志

    Args:
        org_id: 组织 ID
        older_than_days: 清理多少天前的日志

    Returns:
        清理结果
    """
    try:
        from datetime import timedelta

        cutoff_date = (datetime.now() - timedelta(days=older_than_days)).isoformat()

        original_count = len(error_logs)
        error_logs[:] = [
            log
            for log in error_logs
            if log["org_id"] != org_id or log["timestamp"] > cutoff_date
        ]
        deleted_count = original_count - len(error_logs)

        return {
            "success": True,
            "message": f"清理了 {deleted_count} 条旧日志",
            "deleted_count": deleted_count,
        }

    except Exception as e:
        logger.error(f"清理错误日志失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail="清理日志失败")


# ==================== 辅助函数 ====================


def _get_log_level(error_type: str) -> int:
    """
    根据错误类型获取日志级别

    Args:
        error_type: 错误类型

    Returns:
        logging 级别常量
    """
    level_mapping = {
        "NETWORK": logging.ERROR,
        "SERVER": logging.ERROR,
        "HTTP": logging.WARNING,
        "AUTH": logging.WARNING,
        "PERMISSION": logging.INFO,
        "VALIDATION": logging.INFO,
        "NOT_FOUND": logging.INFO,
        "UNKNOWN": logging.WARNING,
    }

    return level_mapping.get(error_type, logging.WARNING)
