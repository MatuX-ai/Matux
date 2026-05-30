"""
预训练模型API路由
提供迁移学习模型的训练、压缩、部署和推荐服务
"""

from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_service.model_compressor import ModelCompressor
from ai_service.transfer_learning_engine import TransferLearningEngine
from config.transfer_learning_config import settings
from models.recommendation import PretrainedModel
from services.dataset_processor import AssistmentsDatasetProcessor
from utils.database import get_db

logger = logging.getLogger(__name__)

# 创建路由实例
router = APIRouter(prefix=settings.deployment.api_prefix, tags=["pretrain-model"])

# 全局服务实例
transfer_learning_service = TransferLearningEngine(settings)
model_compressor = ModelCompressor(settings)
dataset_processor = AssistmentsDatasetProcessor(settings.dataset)


# Pydantic模型定义
class TrainRequest(BaseModel):
    """训练请求模型"""

    dataset_source: str = "assistments2012"
    adaptation_strategy: str = "ensemble_transfer"
    model_name: str = "default_transfer_model"
    compression_required: bool = True


class TrainResponse(BaseModel):
    """训练响应模型"""

    task_id: str
    status: str
    message: str
    model_id: Optional[int] = None


class CompressionRequest(BaseModel):
    """压缩请求模型"""

    model_id: int
    compression_methods: List[str] = ["quantization", "pruning"]
    target_compression_ratio: float = 0.5


class CompressionResponse(BaseModel):
    """压缩响应模型"""

    model_id: int
    compressed_model_paths: List[str]
    compression_ratios: List[float]
    best_method: str


class RecommendationRequest(BaseModel):
    """推荐请求模型"""

    user_id: str
    model_id: Optional[int] = None
    num_recommendations: int = 10
    user_features: Optional[Dict[str, Any]] = None


class RecommendationResponse(BaseModel):
    """推荐响应模型"""

    recommendations: List[Dict[str, Any]]
    model_used: str
    response_time_ms: float
    coverage_score: float


class ModelStatusResponse(BaseModel):
    """模型状态响应模型"""

    model_id: int
    model_name: str
    status: str
    accuracy: Optional[float]
    compression_ratio: Optional[float]
    created_at: str
    last_updated: str


# 全局任务存储
training_tasks = {}


@router.post("/train", response_model=TrainResponse)
async def train_pretrained_model(
    request: TrainRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    触发迁移学习训练任务
    """
    task_id = str(uuid.uuid4())

    try:
        # 创建数据库记录
        db_model = PretrainedModel(
            model_name=request.model_name,
            model_version=f"v1_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            base_model="traditional_ml_ensemble",
            dataset_source=request.dataset_source,
            training_status="pending",
            training_progress=0.0,
        )

        db.add(db_model)
        await db.commit()
        await db.refresh(db_model)

        # 启动后台训练任务
        background_tasks.add_task(
            _background_training_task, task_id, db_model.id, request, db
        )

        training_tasks[task_id] = {
            "model_id": db_model.id,
            "status": "started",
            "start_time": datetime.now(),
        }

        logger.info(f"启动训练任务 {task_id}，模型ID: {db_model.id}")

        return TrainResponse(
            task_id=task_id,
            status="started",
            message=f"训练任务已启动，模型ID: {db_model.id}",
            model_id=db_model.id,
        )

    except Exception as e:
        logger.error(f"训练任务启动失败: {e}")
        raise HTTPException(status_code=500, detail=f"训练启动失败: {str(e)}")


async def _background_training_task(
    task_id: str, model_id: int, request: TrainRequest, db: AsyncSession
):
    """后台训练任务"""
    try:
        # 更新状态为训练中
        stmt = select(PretrainedModel).where(PretrainedModel.id == model_id)
        result = await db.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model:
            db_model.training_status = "training"
            db_model.training_progress = 10.0
            await db.commit()

        training_tasks[task_id]["status"] = "training"

        # 1. 加载和处理数据
        logger.info("步骤1: 加载ASSISTments数据...")
        raw_data = dataset_processor.load_raw_data()
        db_model.training_progress = 20.0
        await db.commit()

        # 2. 初始化源域知识
        logger.info("步骤2: 初始化源域知识...")
        transfer_learning_service.initialize_source_domain(raw_data)
        db_model.training_progress = 40.0
        await db.commit()

        # 3. 适配目标域
        logger.info("步骤3: 适配目标域...")
        # 使用部分数据作为目标域示例
        target_data = raw_data.sample(n=min(1000, len(raw_data)), random_state=42)
        adaptation_result = transfer_learning_service.adapt_to_target_domain(
            target_data, request.adaptation_strategy
        )
        db_model.training_progress = 70.0
        await db.commit()

        # 4. 模型压缩（如果需要）
        if request.compression_required:
            logger.info("步骤4: 模型压缩...")
            best_model = adaptation_result["adapted_model"]
            compression_result = model_compressor.compress_model(best_model, "auto")

            # 保存压缩模型
            compressed_path = model_compressor.save_compressed_model(
                f"model_{model_id}", compression_result["compression_info"]["method"]
            )

            db_model.compression_method = compression_result["compression_info"][
                "method"
            ]
            db_model.model_path = compressed_path
            db_model.compression_ratio = model_compressor._calculate_compression_ratio(
                best_model, compression_result["model"]
            )
            db_model.model_size = model_compressor._get_model_size(
                compression_result["model"]
            )
            db_model.training_progress = 90.0
            await db.commit()
        else:
            # 保存未压缩模型
            model_path = transfer_learning_service.save_transfer_knowledge()
            db_model.model_path = model_path
            db_model.model_size = 1000000  # 估算大小

        # 5. 完成训练
        db_model.training_status = "completed"
        db_model.training_progress = 100.0
        db_model.accuracy_after = adaptation_result["evaluation"].get("accuracy", 0.8)

        await db.commit()

        training_tasks[task_id]["status"] = "completed"
        training_tasks[task_id]["completion_time"] = datetime.now()

        logger.info(f"训练任务 {task_id} 完成")

    except Exception as e:
        logger.error(f"训练任务 {task_id} 失败: {e}")

        # 更新数据库状态
        stmt = select(PretrainedModel).where(PretrainedModel.id == model_id)
        result = await db.execute(stmt)
        db_model = result.scalar_one_or_none()

        if db_model:
            db_model.training_status = "failed"
            db_model.metadata_info = {"error": str(e)}
            await db.commit()

        training_tasks[task_id]["status"] = "failed"
        training_tasks[task_id]["error"] = str(e)


@router.post("/compress/{model_id}", response_model=CompressionResponse)
async def compress_model(
    model_id: int, request: CompressionRequest, db: AsyncSession = Depends(get_db)
):
    """
    对指定模型进行压缩
    """
    try:
        # 获取模型信息
        stmt = select(PretrainedModel).where(PretrainedModel.id == model_id)
        result = await db.execute(stmt)
        db_model = result.scalar_one_or_none()

        if not db_model:
            raise HTTPException(status_code=404, detail="模型不存在")

        if db_model.training_status != "completed":
            raise HTTPException(status_code=400, detail="模型尚未训练完成")

        # 加载模型
        # 这里需要根据实际的模型保存方式来加载
        # 简化处理：使用迁移学习引擎的现有模型
        if not transfer_learning_service.student_models:
            raise HTTPException(status_code=400, detail="无可用模型进行压缩")

        # 获取最佳模型
        best_model_key = max(
            transfer_learning_service.student_models.keys(),
            key=lambda k: transfer_learning_service.student_models[k]
            .get("evaluation", {})
            .get("accuracy", 0),
        )
        model_to_compress = transfer_learning_service.student_models[best_model_key][
            "model"
        ]

        # 批量压缩
        compression_results = model_compressor.batch_compress_models(
            {f"model_{model_id}": model_to_compress}, request.compression_methods
        )

        compressed_paths = []
        compression_ratios = []
        best_ratio = float("inf")
        best_method = ""

        for method, result in compression_results[f"model_{model_id}"].items():
            if "error" not in result:
                # 保存压缩模型
                save_path = model_compressor.save_compressed_model(
                    f"model_{model_id}", method
                )
                ratio = result["compression_info"].get("compression_ratio", 1.0)

                compressed_paths.append(save_path)
                compression_ratios.append(ratio)

                if ratio < best_ratio:
                    best_ratio = ratio
                    best_method = method

        # 更新数据库
        db_model.compression_method = best_method
        db_model.compression_ratio = best_ratio
        await db.commit()

        return CompressionResponse(
            model_id=model_id,
            compressed_model_paths=compressed_paths,
            compression_ratios=compression_ratios,
            best_method=best_method,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"模型压缩失败: {e}")
        raise HTTPException(status_code=500, detail=f"压缩失败: {str(e)}")


@router.post("/recommend", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest, db: AsyncSession = Depends(get_db)
):
    """
    基于预训练模型生成推荐
    """
    start_time = datetime.now()

    try:
        # 选择模型
        if request.model_id:
            # 使用指定模型
            stmt = select(PretrainedModel).where(PretrainedModel.id == request.model_id)
            result = await db.execute(stmt)
            db_model = result.scalar_one_or_none()

            if not db_model or db_model.training_status != "completed":
                raise HTTPException(status_code=400, detail="指定模型不可用")
        else:
            # 使用最新的完成模型
            stmt = (
                select(PretrainedModel)
                .where(PretrainedModel.training_status == "completed")
                .order_by(PretrainedModel.created_at.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            db_model = result.scalar_one_or_none()

            if not db_model:
                raise HTTPException(status_code=404, detail="无可用的预训练模型")

        # 生成用户特征（简化处理）
        if request.user_features:
            user_features = _convert_user_features(request.user_features)
        else:
            # 生成默认用户特征
            user_features = _generate_default_user_features(request.user_id)

        # 获取推荐
        recommendations = transfer_learning_service.generate_recommendations(
            user_features, "ensemble"
        )

        # 截取指定数量
        recommendations = recommendations[: request.num_recommendations]

        # 计算响应时间
        response_time = (datetime.now() - start_time).total_seconds() * 1000

        # 计算覆盖率得分（简化）
        coverage_score = min(1.0, len(recommendations) / request.num_recommendations)

        # 记录推荐日志
        log_entry = ColdStartRecommendationLog(
            user_id=request.user_id,
            model_id=db_model.id,
            recommended_courses=recommendations,
            coverage_score=coverage_score,
            recommendation_timestamp=datetime.now(),
            response_time_ms=int(response_time),
            is_cold_start=1,
        )

        db.add(log_entry)
        await db.commit()

        return RecommendationResponse(
            recommendations=recommendations,
            model_used=db_model.model_name,
            response_time_ms=response_time,
            coverage_score=coverage_score,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"推荐生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")


def _convert_user_features(user_features: Dict[str, Any]) -> Any:
    """转换用户特征为模型可处理的格式"""
    # 简化实现：将字典转换为数值数组
    import numpy as np

    # 提取数值特征
    numeric_features = []
    for key, value in user_features.items():
        if isinstance(value, (int, float)):
            numeric_features.append(float(value))
        elif isinstance(value, bool):
            numeric_features.append(1.0 if value else 0.0)
        else:
            # 对于非数值特征，使用简单的编码
            numeric_features.append(hash(str(value)) % 1000 / 1000.0)

    # 确保特征维度一致
    target_dim = 20  # 假设模型期望20维特征
    if len(numeric_features) < target_dim:
        numeric_features.extend([0.0] * (target_dim - len(numeric_features)))
    elif len(numeric_features) > target_dim:
        numeric_features = numeric_features[:target_dim]

    return np.array([numeric_features])


def _generate_default_user_features(user_id: str) -> Any:
    """生成默认用户特征"""
    import hashlib

    import numpy as np

    # 基于用户ID生成确定性的特征向量
    hash_val = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)

    # 生成20维特征向量
    features = []
    for i in range(20):
        # 使用不同的种子生成不同的特征值
        feature_val = (hash_val >> (i * 4)) & 0xF
        features.append(feature_val / 15.0)  # 归一化到[0,1]

    return np.array([features])


@router.get("/status/{task_id}", response_model=TrainResponse)
async def get_training_status(task_id: str):
    """
    查询训练任务状态
    """
    if task_id not in training_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task_info = training_tasks[task_id]

    return TrainResponse(
        task_id=task_id,
        status=task_info["status"],
        message=f"任务状态: {task_info['status']}",
        model_id=task_info.get("model_id"),
    )


@router.get("/models", response_model=List[ModelStatusResponse])
async def list_models(
    status: Optional[str] = Query(None, description="过滤模型状态"),
    db: AsyncSession = Depends(get_db),
):
    """
    列出所有预训练模型
    """
    try:
        stmt = select(PretrainedModel)
        if status:
            stmt = stmt.where(PretrainedModel.training_status == status)
        stmt = stmt.order_by(PretrainedModel.created_at.desc())

        result = await db.execute(stmt)
        models = result.scalars().all()

        return [
            ModelStatusResponse(
                model_id=model.id,
                model_name=model.model_name,
                status=model.training_status,
                accuracy=model.accuracy_after,
                compression_ratio=model.compression_ratio,
                created_at=model.created_at.isoformat(),
                last_updated=model.updated_at.isoformat(),
            )
            for model in models
        ]

    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {
        "status": "healthy",
        "service": "pretrain-model-api",
        "timestamp": datetime.now().isoformat(),
        "active_models": len(transfer_learning_service.student_models),
        "available_compression_methods": [
            "quantization",
            "pruning",
            "feature_selection",
        ],
    }


# 注册事件处理器
@router.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    logger.info("预训练模型服务启动")
    # 可以在这里添加初始化逻辑


@router.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    logger.info("预训练模型服务关闭")
    # 可以在这里添加清理逻辑
