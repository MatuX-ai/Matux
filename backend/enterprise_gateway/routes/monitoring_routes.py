"""
监控路由
提供企业API使用情况监控和统计功能
"""

from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from models.enterprise_models import EnterpriseAPILog
from services.enterprise_auth_service import enterprise_auth_service
from utils.database import get_db

router = APIRouter()


@router.get("/monitoring/stats/{client_id}", response_model=dict)
async def get_client_statistics(
    client_id: str,
    days: int = Query(30, description="统计天数", ge=1, le=365),
    db: Session = Depends(get_db),
):
    """
    获取客户端使用统计

    Args:
        client_id: 企业客户端ID
        days: 统计天数
        db: 数据库会话

    Returns:
        客户端使用统计信息
    """
    try:
        stats = enterprise_auth_service.get_client_statistics(client_id, days, db)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found or no data available",
            )

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client statistics: {str(e)}",
        )


@router.get("/monitoring/logs/{client_id}", response_model=List[dict])
async def get_client_logs(
    client_id: str,
    limit: int = Query(100, description="返回记录数", ge=1, le=1000),
    offset: int = Query(0, description="偏移量", ge=0),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    status_code: Optional[int] = Query(None, description="HTTP状态码"),
    db: Session = Depends(get_db),
):
    """
    获取客户端API访问日志

    Args:
        client_id: 企业客户端ID
        limit: 返回记录数限制
        offset: 偏移量
        start_date: 开始日期
        end_date: 结束日期
        status_code: HTTP状态码筛选
        db: 数据库会话

    Returns:
        API访问日志列表
    """
    try:
        from sqlalchemy import desc

        from models.enterprise_models import EnterpriseClient

        # 获取客户端内部ID
        client = (
            db.query(EnterpriseClient)
            .filter(EnterpriseClient.client_id == client_id)
            .first()
        )

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )

        # 构建查询
        query = db.query(EnterpriseAPILog).filter(
            EnterpriseAPILog.enterprise_client_id == client.id
        )

        # 添加筛选条件
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(EnterpriseAPILog.timestamp >= start_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD",
                )

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                query = query.filter(EnterpriseAPILog.timestamp < end_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD",
                )

        if status_code:
            query = query.filter(EnterpriseAPILog.status_code == status_code)

        # 执行查询
        logs = (
            query.order_by(desc(EnterpriseAPILog.timestamp))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return [log.to_dict() for log in logs]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client logs: {str(e)}",
        )


@router.get("/monitoring/realtime/{client_id}", response_model=dict)
async def get_realtime_metrics(
    client_id: str,
    minutes: int = Query(5, description="统计分钟数", ge=1, le=60),
    db: Session = Depends(get_db),
):
    """
    获取客户端实时指标

    Args:
        client_id: 企业客户端ID
        minutes: 统计分钟数
        db: 数据库会话

    Returns:
        实时指标数据
    """
    try:
        from models.enterprise_models import EnterpriseClient

        # 获取客户端内部ID
        client = (
            db.query(EnterpriseClient)
            .filter(EnterpriseClient.client_id == client_id)
            .first()
        )

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )

        # 计算时间范围
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)

        # 查询实时数据
        recent_logs = (
            db.query(EnterpriseAPILog)
            .filter(
                EnterpriseAPILog.enterprise_client_id == client.id,
                EnterpriseAPILog.timestamp >= start_time,
                EnterpriseAPILog.timestamp <= end_time,
            )
            .all()
        )

        # 计算指标
        total_requests = len(recent_logs)
        successful_requests = len(
            [
                log
                for log in recent_logs
                if log.status_code and 200 <= log.status_code < 300
            ]
        )
        failed_requests = total_requests - successful_requests

        avg_response_time = (
            sum(log.response_time for log in recent_logs if log.response_time)
            / len([log for log in recent_logs if log.response_time])
            if any(log.response_time for log in recent_logs)
            else 0
        )

        # 按分钟统计请求量
        requests_by_minute = {}
        for i in range(minutes):
            minute_start = start_time + timedelta(minutes=i)
            minute_end = minute_start + timedelta(minutes=1)
            count = len(
                [
                    log
                    for log in recent_logs
                    if minute_start <= log.timestamp < minute_end
                ]
            )
            requests_by_minute[minute_start.strftime("%H:%M")] = count

        return {
            "period_minutes": minutes,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": (
                (successful_requests / total_requests * 100)
                if total_requests > 0
                else 0
            ),
            "average_response_time_ms": round(avg_response_time, 2),
            "requests_by_minute": requests_by_minute,
            "current_quota_usage": client.current_usage,
            "quota_limit": client.api_quota_limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get realtime metrics: {str(e)}",
        )


@router.get("/monitoring/alerts/{client_id}", response_model=dict)
async def get_client_alerts(client_id: str, db: Session = Depends(get_db)):
    """
    获取客户端告警信息

    Args:
        client_id: 企业客户端ID
        db: 数据库会话

    Returns:
        告警信息
    """
    try:
        from models.enterprise_models import EnterpriseClient

        # 获取客户端信息
        client = (
            db.query(EnterpriseClient)
            .filter(EnterpriseClient.client_id == client_id)
            .first()
        )

        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Client not found"
            )

        alerts = []

        # 检查配额使用情况
        usage_percentage = (
            (client.current_usage / client.api_quota_limit * 100)
            if client.api_quota_limit
            else 0
        )
        if usage_percentage >= 90:
            alerts.append(
                {
                    "type": "QUOTA_WARNING",
                    "level": "WARNING",
                    "message": f"API quota usage is at {usage_percentage:.1f}% of limit",
                    "threshold": "90%",
                }
            )
        elif usage_percentage >= 95:
            alerts.append(
                {
                    "type": "QUOTA_CRITICAL",
                    "level": "CRITICAL",
                    "message": f"API quota usage is at {usage_percentage:.1f}% of limit",
                    "threshold": "95%",
                }
            )

        # 检查近期错误率
        from datetime import timedelta

        recent_period = datetime.utcnow() - timedelta(hours=1)
        recent_logs = (
            db.query(EnterpriseAPILog)
            .filter(
                EnterpriseAPILog.enterprise_client_id == client.id,
                EnterpriseAPILog.timestamp >= recent_period,
            )
            .all()
        )

        if recent_logs:
            error_rate = (
                len(
                    [
                        log
                        for log in recent_logs
                        if log.status_code and log.status_code >= 400
                    ]
                )
                / len(recent_logs)
                * 100
            )
            if error_rate >= 5:
                alerts.append(
                    {
                        "type": "HIGH_ERROR_RATE",
                        "level": "WARNING",
                        "message": f"Error rate is {error_rate:.1f}% in the last hour",
                        "threshold": "5%",
                    }
                )

        return {
            "client_id": client_id,
            "alerts": alerts,
            "total_alerts": len(alerts),
            "has_critical_alerts": any(
                alert["level"] == "CRITICAL" for alert in alerts
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client alerts: {str(e)}",
        )
