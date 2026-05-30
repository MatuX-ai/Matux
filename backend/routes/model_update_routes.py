"""
AI模型热更新API路由
"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile

from models.model_version import ModelVersion
from services.model_update_service import ModelUpdateService, get_model_update_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/model-update", tags=["模型更新"])


@router.post("/upload", summary="上传新模型版本")
async def upload_model_version(
    model_name: str = Form(..., description="模型名称"),
    version: str = Form(..., description="版本号"),
    description: str = Form("", description="版本描述"),
    compression_enabled: bool = Form(True, description="是否启用压缩"),
    model_file: UploadFile = File(..., description="模型文件"),
    service: ModelUpdateService = Depends(get_model_update_service),
):
    """
    上传新的模型版本文件
    """
    try:
        # 保存上传的文件
        import shutil
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(model_file.file, tmp_file)
            tmp_file_path = tmp_file.name

        # 上传模型版本
        result = await service.upload_model_version(
            model_name=model_name,
            version=version,
            model_file_path=tmp_file_path,
            description=description,
            compression_enabled=compression_enabled,
        )

        # 清理临时文件
        os.unlink(tmp_file_path)

        return {"success": True, "message": "模型版本上传成功", "data": result}

    except Exception as e:
        logger.error(f"模型上传失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_name}/versions", summary="获取模型版本列表")
async def get_model_versions(
    model_name: str, service: ModelUpdateService = Depends(get_model_update_service)
):
    """
    获取指定模型的所有版本信息
    """
    try:
        versions = await service.get_model_versions(model_name)
        return {"success": True, "data": versions}
    except Exception as e:
        logger.error(f"获取模型版本失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_name}/latest", summary="获取最新模型版本")
async def get_latest_model_version(
    model_name: str, service: ModelUpdateService = Depends(get_model_update_service)
):
    """
    获取指定模型的最新版本信息
    """
    try:
        latest_version = await service.get_latest_model_version(model_name)
        if not latest_version:
            raise HTTPException(status_code=404, detail="未找到该模型的版本")

        return {"success": True, "data": latest_version}
    except Exception as e:
        logger.error(f"获取最新模型版本失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}/prepare-transfer", summary="准备模型传输")
async def prepare_model_for_transfer(
    model_id: int,
    chunk_size: int = Query(512, ge=128, le=1024, description="数据块大小"),
    service: ModelUpdateService = Depends(get_model_update_service),
):
    """
    为BLE传输准备模型数据，返回传输元信息
    """
    try:
        transfer_info = await service.prepare_model_for_transfer(model_id, chunk_size)
        return {"success": True, "data": transfer_info}
    except Exception as e:
        logger.error(f"准备模型传输失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{model_id}/chunks/{chunk_index}", summary="获取模型数据块")
async def get_model_chunk(
    model_id: int,
    chunk_index: int,
    chunk_size: int = Query(512, description="数据块大小"),
    service: ModelUpdateService = Depends(get_model_update_service),
):
    """
    获取指定索引的模型数据块，用于分块传输
    """
    try:
        chunk_data = await service.get_chunk_data(model_id, chunk_index, chunk_size)
        return chunk_data
    except Exception as e:
        logger.error(f"获取模型数据块失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/{model_id}/validate", summary="验证模型更新")
async def validate_model_update(
    model_id: int,
    received_hash: str = Form(..., description="接收到的文件哈希值"),
    service: ModelUpdateService = Depends(get_model_update_service),
):
    """
    验证设备端接收到的模型文件完整性
    """
    try:
        validation_result = await service.validate_model_update(model_id, received_hash)
        return {"success": True, "data": validation_result}
    except Exception as e:
        logger.error(f"模型更新验证失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", summary="获取模型更新服务状态")
async def get_service_status(
    service: ModelUpdateService = Depends(get_model_update_service),
):
    """
    获取模型更新服务的运行状态信息
    """
    try:
        import psutil

        # 获取磁盘使用情况
        disk_usage = psutil.disk_usage(service.model_storage_path)

        # 获取模型统计信息
        total_models = service.db.query(ModelVersion).count()
        active_models = (
            service.db.query(ModelVersion)
            .filter(ModelVersion.is_active == True)
            .count()
        )

        return {
            "success": True,
            "data": {
                "service_status": "running",
                "storage_path": str(service.model_storage_path),
                "disk_total": disk_usage.total,
                "disk_used": disk_usage.used,
                "disk_free": disk_usage.free,
                "disk_usage_percent": round(disk_usage.percent, 2),
                "total_models": total_models,
                "active_models": active_models,
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
    except Exception as e:
        logger.error(f"获取服务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
