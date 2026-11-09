"""
【P3 监控】Prometheus 指标导出端点

GET /metrics
- 文本格式输出（Prometheus 标准）
- 无需鉴权（生产建议内网访问或加 basic auth）
"""

import logging

from fastapi import APIRouter, Response

from security.metrics import get_content_type, get_metrics_output

logger = logging.getLogger(__name__)

router = APIRouter(tags=["monitoring"])


@router.get("/metrics", summary="Prometheus 指标导出")
async def metrics_endpoint() -> Response:
    """
    Prometheus 抓取端点

    返回 text/plain; version=0.0.4 格式
    """
    try:
        output = get_metrics_output()
        return Response(
            content=output,
            media_type=get_content_type(),
        )
    except Exception as e:
        logger.error(f"生成 metrics 失败: {e}")
        return Response(
            content=f"# error generating metrics: {e}\n",
            media_type="text/plain; charset=utf-8",
            status_code=500,
        )


__all__ = ["router"]
