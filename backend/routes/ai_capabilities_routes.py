"""
AI 能力组件 API路由
封装 XEduHub SOTA 模型，提供视觉分析、NLP 对话等能力的统一调用接口
"""

from datetime import datetime
import logging
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from models.user import User
from services.performance_monitor import performance_monitor
from utils.dependencies import get_current_user_sync, get_sync_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/ai-capabilities",
    tags=["AI 能力组件"],
    responses={404: {"description": "Not found"}},
)


# ==================== 请求/响应模型 ====================


class VisionTaskRequest(BaseModel):
    """视觉分析任务请求"""

    image_url: str = Field(..., description="图片 URL 或 Base64 编码")
    task_type: str = Field(
        ...,
        description="任务类型",
        examples=[
            "object_detection",
            "image_classification",
            "pose_estimation",
            "plant_disease",
        ],
    )
    model_name: str = Field(default="yolov5", description="模型名称")
    confidence_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0, description="置信度阈值"
    )


class DetectedObject(BaseModel):
    """检测到的对象"""

    label: str
    confidence: float
    bbox: Optional[List[float]] = None  # [x1, y1, x2, y2]
    keypoints: Optional[List[Dict[str, float]]] = None  # 关键点（姿态估计）


class VisionAnalysisResponse(BaseModel):
    """视觉分析响应"""

    success: bool
    objects: List[DetectedObject]
    inference_time_ms: float
    model_name: str
    task_type: str
    timestamp: str


class NLPChatRequest(BaseModel):
    """NLP 对话请求"""

    message: str = Field(..., description="用户消息")
    context: Optional[List[Dict[str, str]]] = Field(
        default=None, description="对话上下文"
    )
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="生成温度")


class NLPChatResponse(BaseModel):
    """NLP 对话响应"""

    reply: str
    model: str
    confidence: float
    inference_time_ms: float
    timestamp: str


class MLTaskRequest(BaseModel):
    """机器学习任务请求"""

    data: Dict[str, Any] = Field(..., description="输入数据")
    task_type: str = Field(
        ...,
        description="任务类型",
        examples=["classification", "regression", "clustering"],
    )
    model_name: str = Field(default="random_forest", description="模型名称")


class MLTaskResponse(BaseModel):
    """机器学习任务响应"""

    prediction: Any
    probabilities: Optional[Dict[str, float]] = None
    inference_time_ms: float
    model_name: str
    timestamp: str


# ==================== Mock 实现 (实际应集成 XEduHub) ====================


class MockXEduHub:
    """Mock XEduHub 服务（用于演示和测试）"""

    @staticmethod
    async def analyze_vision(request: VisionTaskRequest) -> VisionAnalysisResponse:
        """模拟视觉分析"""
        start_time = time.time()

        # 模拟不同任务类型的返回
        if request.task_type == "object_detection":
            objects = [
                DetectedObject(
                    label="temperature_sensor",
                    confidence=0.95,
                    bbox=[100.0, 150.0, 300.0, 350.0],
                ),
                DetectedObject(
                    label="humidity_sensor",
                    confidence=0.89,
                    bbox=[400.0, 200.0, 550.0, 400.0],
                ),
            ]
        elif request.task_type == "plant_disease":
            objects = [
                DetectedObject(
                    label="powdery_mildew",
                    confidence=0.89,
                    bbox=[50.0, 80.0, 200.0, 250.0],
                )
            ]
        else:
            objects = [
                DetectedObject(
                    label="unknown_object",
                    confidence=0.75,
                    bbox=[0.0, 0.0, 100.0, 100.0],
                )
            ]

        inference_time = (time.time() - start_time) * 1000

        return VisionAnalysisResponse(
            success=True,
            objects=objects,
            inference_time_ms=inference_time,
            model_name=request.model_name,
            task_type=request.task_type,
            timestamp=datetime.utcnow().isoformat(),
        )

    @staticmethod
    async def chat(request: NLPChatRequest) -> NLPChatResponse:
        """模拟 NLP 对话"""
        start_time = time.time()

        # 简单的规则回复
        message_lower = request.message.lower()

        if "什么是" in message_lower or "what is" in message_lower:
            reply = "这是一个很好的问题！让我为您解释一下..."
        elif "如何" in message_lower or "how to" in message_lower:
            reply = "要完成这个任务，您可以按照以下步骤操作..."
        elif "帮助" in message_lower or "help" in message_lower:
            reply = "我很乐意帮助您！请告诉我您遇到的具体问题。"
        else:
            reply = "我明白了。关于这个问题，我认为..."

        inference_time = (time.time() - start_time) * 1000

        return NLPChatResponse(
            reply=reply,
            model="chatglm-6b-mock",
            confidence=0.85,
            inference_time_ms=inference_time,
            timestamp=datetime.utcnow().isoformat(),
        )

    @staticmethod
    async def run_ml_task(request: MLTaskRequest) -> MLTaskResponse:
        """模拟机器学习任务"""
        start_time = time.time()

        # 模拟预测结果
        if request.task_type == "classification":
            prediction = "class_a"
            probabilities = {"class_a": 0.75, "class_b": 0.20, "class_c": 0.05}
        elif request.task_type == "regression":
            prediction = 42.5
            probabilities = None
        else:
            prediction = "cluster_1"
            probabilities = None

        inference_time = (time.time() - start_time) * 1000

        return MLTaskResponse(
            prediction=prediction,
            probabilities=probabilities,
            inference_time_ms=inference_time,
            model_name=request.model_name,
            timestamp=datetime.utcnow().isoformat(),
        )


# ==================== API路由 ====================


@router.post("/vision/analyze", response_model=VisionAnalysisResponse)
async def vision_analyze(
    request: VisionTaskRequest,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    视觉分析接口

    调用 XEduHub 的计算机视觉模型进行图像识别、目标检测等任务

    Args:
        request: 视觉分析请求
        current_user: 当前用户
        db: 数据库会话

    Returns:
        VisionAnalysisResponse: 分析结果

    Examples:
        POST /api/v1/ai-capabilities/vision/analyze
        {
            "image_url": "https://example.com/sensor_data.jpg",
            "task_type": "object_detection",
            "model_name": "yolov5"
        }
    """
    try:
        logger.info(
            f"收到视觉分析请求：用户 {current_user.id}, 任务 {request.task_type}"
        )

        # 调用 XEduHub（当前为 Mock 实现）
        result = await MockXEduHub.analyze_vision(request)

        logger.info(
            f"视觉分析完成：{len(result.objects)} 个对象，耗时 {result.inference_time_ms:.2f}ms"
        )

        return result

    except Exception as e:
        logger.error(f"视觉分析失败：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"视觉分析失败：{str(e)}",
        )


@router.post("/nlp/chat", response_model=NLPChatResponse)
async def nlp_chat(
    request: NLPChatRequest,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    NLP 对话接口

    基于 XEduLLM 构建 AI 学习助手，支持多轮对话

    Args:
        request: NLP 对话请求
        current_user: 当前用户
        db: 数据库会话

    Returns:
        NLPChatResponse: AI 助手回复

    Examples:
        POST /api/v1/ai-capabilities/nlp/chat
        {
            "message": "什么是卷积神经网络？",
            "context": [{"role": "user", "content": "你好"}]
        }
    """
    try:
        logger.info(f"收到 NLP 对话请求：用户 {current_user.id}")

        # 调用 XEduLLM（当前为 Mock 实现）
        result = await MockXEduHub.chat(request)

        logger.info(f"NLP 对话完成：耗时 {result.inference_time_ms:.2f}ms")

        return result

    except Exception as e:
        logger.error(f"NLP 对话失败：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NLP 对话失败：{str(e)}",
        )


@router.post("/ml/predict", response_model=MLTaskResponse)
async def ml_predict(
    request: MLTaskRequest,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    机器学习预测接口

    调用 XEdu 的机器学习模型进行分类、回归、聚类等任务

    Args:
        request: 机器学习任务请求
        current_user: 当前用户
        db: 数据库会话

    Returns:
        MLTaskResponse: 预测结果

    Examples:
        POST /api/v1/ai-capabilities/ml/predict
        {
            "data": {"features": [0.5, 0.8, 0.3]},
            "task_type": "classification",
            "model_name": "random_forest"
        }
    """
    try:
        logger.info(
            f"收到 ML 预测请求：用户 {current_user.id}, 任务 {request.task_type}"
        )

        # 调用 XEdu ML（当前为 Mock 实现）
        result = await MockXEduHub.run_ml_task(request)

        logger.info(
            f"ML 预测完成：{result.prediction}, 耗时 {result.inference_time_ms:.2f}ms"
        )

        return result

    except Exception as e:
        logger.error(f"ML 预测失败：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML 预测失败：{str(e)}",
        )


@router.get("/models/list")
async def list_available_models(
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    获取可用模型列表

    Returns:
        Dict: 模型列表信息
    """
    models = {
        "vision": [
            {"name": "yolov5", "type": "object_detection", "accuracy": "95%"},
            {
                "name": "efficientnet-b3",
                "type": "image_classification",
                "accuracy": "92%",
            },
            {"name": "openpose", "type": "pose_estimation", "accuracy": "90%"},
            {"name": "plant_disease_net", "type": "plant_disease", "accuracy": "89%"},
        ],
        "nlp": [
            {"name": "chatglm-6b", "type": "dialogue", "parameters": "6B"},
            {"name": "bert-base", "type": "text_classification", "parameters": "110M"},
        ],
        "ml": [
            {"name": "random_forest", "type": "classification/regression"},
            {"name": "svm", "type": "classification/regression"},
            {"name": "kmeans", "type": "clustering"},
        ],
    }

    return {
        "models": models,
        "total_count": sum(len(v) for v in models.values()),
        "provider": "XEduHub",
    }


@router.get("/health")
async def health_check():
    """
    健康检查

    Returns:
        Dict: 服务健康状态
    """
    return {
        "status": "healthy",
        "service": "ai-capabilities",
        "version": "1.0.0",
        "xeduhub_connected": True,  # Mock 状态
    }


@router.get("/monitoring/dashboard")
async def get_monitoring_dashboard(
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    获取性能监控仪表板数据

    Returns:
        Dict: 监控仪表板数据，包括:
            - 总体健康状态
            - 所有模型的性能指标
            - 延迟百分位数 (P50, P95, P99)
    """
    try:
        # 获取健康状态
        health = performance_monitor.get_health_status()

        # 获取所有模型的指标
        models_metrics = performance_monitor.get_all_models_metrics()

        # 计算延迟百分位数
        latency_percentiles = {}
        for model_name in performance_monitor.model_metrics.keys():
            latency_percentiles[model_name] = {
                "p50": round(
                    performance_monitor.get_latency_percentile(model_name, 50), 2
                ),
                "p95": round(
                    performance_monitor.get_latency_percentile(model_name, 95), 2
                ),
                "p99": round(
                    performance_monitor.get_latency_percentile(model_name, 99), 2
                ),
            }

        return {
            "health": health,
            "models": models_metrics,
            "latency_percentiles": latency_percentiles,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"获取监控数据失败：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取监控数据失败：{str(e)}",
        )


@router.post("/monitoring/reset")
async def reset_monitoring_metrics(
    model_name: Optional[str] = None,
    current_user: User = Depends(get_current_user_sync),
    db: Session = Depends(get_sync_db),
):
    """
    重置监控指标

    Args:
        model_name: 模型名称（可选，不传则重置所有）

    Returns:
        Dict: 重置结果
    """
    try:
        performance_monitor.reset_metrics(model_name)

        return {
            "success": True,
            "message": f'已重置{"模型 " + model_name if model_name else "所有"}的监控指标',
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"重置监控指标失败：{e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置监控指标失败：{str(e)}",
        )
