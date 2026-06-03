"""
AI 模型管理 API 路由

提供模型的注册、加载、卸载、推理等 RESTful API。
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

from .model_manager import (
    ModelManager,
    ModelType,
    ModelStatus,
)

router = APIRouter(prefix="/api/v1/models", tags=["models"])

# 全局模型管理器实例
model_manager = ModelManager(cache_dir="./data/model_cache")


class RegisterModelRequest(BaseModel):
    """注册模型请求"""
    name: str = Field(..., description="模型名称")
    version: str = Field(..., description="版本号")
    model_type: str = Field(...,
                            description="模型类型 (tensorflow/onnx/pytorch/custom)")
    source_path: str = Field("", description="本地文件路径")
    source_url: str = Field("", description="远程 URL")
    description: str = Field("", description="描述信息")
    tags: List[str] = Field(default_factory=list, description="标签")
    config: Dict[str, Any] = Field(default_factory=dict, description="配置")


class PredictRequest(BaseModel):
    """推理请求"""
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="推理参数")


class ABTestRequest(BaseModel):
    """A/B 测试请求"""
    model_a_id: str = Field(..., description="模型 A ID")
    model_b_id: str = Field(..., description="模型 B ID")
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    ratio: float = Field(0.5, ge=0.0, le=1.0, description="模型 A 流量比例")


@router.post("/register")
async def register_model(req: RegisterModelRequest):
    """注册新模型"""
    try:
        model_type = ModelType(req.model_type)
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"不支持的模型类型: {req.model_type}")

    metadata = await model_manager.register_model(
        name=req.name,
        version=req.version,
        model_type=model_type,
        source_path=req.source_path,
        source_url=req.source_url,
        description=req.description,
        tags=req.tags,
        config=req.config,
    )

    return {
        "success": True,
        "data": {
            "model_id": metadata.model_id,
            "name": metadata.name,
            "version": metadata.version,
            "status": metadata.status.value,
            "created_at": metadata.created_at.isoformat(),
        },
    }


@router.post("/{model_id}/load")
async def load_model(model_id: str):
    """加载模型"""
    try:
        success = await model_manager.load_model(model_id)
        if success:
            return {"success": True, "message": "模型加载已启动"}
        raise HTTPException(status_code=409, detail="模型正在加载中")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{model_id}/unload")
async def unload_model(model_id: str):
    """卸载模型"""
    success = await model_manager.unload_model(model_id)
    if success:
        return {"success": True, "message": "模型已卸载"}
    raise HTTPException(status_code=404, detail="模型不存在")


@router.get("")
async def list_models(
    status: Optional[str] = Query(None, description="按状态筛选"),
):
    """列出所有模型"""
    model_status = None
    if status:
        try:
            model_status = ModelStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {status}")

    models = model_manager.list_models(status=model_status)
    return {
        "success": True,
        "data": [
            {
                "model_id": m.model_id,
                "name": m.name,
                "version": m.version,
                "model_type": m.model_type.value,
                "status": m.status.value,
                "description": m.description,
                "tags": m.tags,
                "use_count": m.use_count,
                "avg_inference_time_ms": m.avg_inference_time_ms,
                "memory_usage_mb": m.memory_usage_mb,
                "created_at": m.created_at.isoformat(),
                "loaded_at": m.loaded_at.isoformat() if m.loaded_at else None,
                "last_used_at": m.last_used_at.isoformat() if m.last_used_at else None,
            }
            for m in models
        ],
        "total": len(models),
    }


@router.get("/{model_id}")
async def get_model(model_id: str):
    """获取模型详情"""
    metadata = model_manager.get_model(model_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="模型不存在")

    return {
        "success": True,
        "data": {
            "model_id": metadata.model_id,
            "name": metadata.name,
            "version": metadata.version,
            "model_type": metadata.model_type.value,
            "status": metadata.status.value,
            "source_path": metadata.source_path,
            "source_url": metadata.source_url,
            "checksum": metadata.checksum,
            "file_size": metadata.file_size,
            "description": metadata.description,
            "tags": metadata.tags,
            "use_count": metadata.use_count,
            "avg_inference_time_ms": metadata.avg_inference_time_ms,
            "memory_usage_mb": metadata.memory_usage_mb,
            "gpu_memory_usage_mb": metadata.gpu_memory_usage_mb,
            "created_at": metadata.created_at.isoformat(),
            "loaded_at": metadata.loaded_at.isoformat() if metadata.loaded_at else None,
            "last_used_at": metadata.last_used_at.isoformat() if metadata.last_used_at else None,
            "config": metadata.config,
            "error_message": metadata.error_message,
        },
    }


@router.post("/{model_id}/predict")
async def predict(model_id: str, req: PredictRequest):
    """使用模型推理"""
    result = await model_manager.predict(
        model_id=model_id,
        input_data=req.input_data,
        parameters=req.parameters,
    )

    return {
        "success": result.success,
        "data": {
            "request_id": result.request_id,
            "output": result.output_data,
            "inference_time_ms": result.inference_time_ms,
        },
        "error": result.error_message if not result.success else None,
    }


@router.post("/ab-test")
async def ab_test(req: ABTestRequest):
    """A/B 测试"""
    result = await model_manager.ab_test(
        model_a_id=req.model_a_id,
        model_b_id=req.model_b_id,
        input_data=req.input_data,
        ratio=req.ratio,
    )

    return {
        "success": result.success,
        "data": {
            "request_id": result.request_id,
            "model_id": result.model_id,
            "output": result.output_data,
            "inference_time_ms": result.inference_time_ms,
        },
    }


@router.get("/stats/inference")
async def get_inference_stats():
    """获取推理统计"""
    return {"success": True, "data": model_manager.get_inference_stats()}


@router.get("/stats/resources")
async def get_resource_usage():
    """获取资源使用情况"""
    return {"success": True, "data": model_manager.get_resource_usage()}


@router.post("/cleanup")
async def cleanup_idle_models(
    max_idle_seconds: int = Query(3600, description="最大闲置时间(秒)"),
):
    """清理闲置模型"""
    unloaded = await model_manager.unload_idle_models(max_idle_seconds)
    return {"success": True, "message": f"已卸载 {unloaded} 个闲置模型", "unloaded": unloaded}
