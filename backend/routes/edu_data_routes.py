"""
教育局数据对接API路由
提供教育数据联邦学习和报告生成的RESTful API接口
"""

from datetime import datetime
import json
import logging

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from ai_service.fl_models import FLTrainingProgress
from config.edu_data_config import edu_config
from middleware.auth import get_current_active_user
from models.edu_data_models import (
    EduDataSharingProtocol,
    EduNodeRegistration,
    EduReportMetadata,
    EduReportRequest,
    EduTrainingConfig,
)
from ..models.user import User
from ..services.edu_federated_service import EduFederatedLearningService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/edu-data", tags=["教育数据联邦学习"])


# 依赖注入
async def get_edu_fl_service() -> EduFederatedLearningService:
    """获取教育联邦学习服务实例"""
    return EduFederatedLearningService.get_instance()


@router.post("/trainings/", response_model=dict)
async def start_edu_federated_training(
    config: EduTrainingConfig,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    edu_service: EduFederatedLearningService = Depends(get_edu_fl_service),
):
    """
    启动教育数据联邦学习训练
    """
    try:
        logger.info(f"用户 {current_user.username} 请求启动教育数据联邦学习训练")

        # 权限检查 - 需要教育数据或AI权限
        if (
            not current_user.has_permission("education_data")
            and not current_user.has_permission("ai")
            and not current_user.is_admin
        ):
            raise HTTPException(status_code=403, detail="权限不足")

        # 验证配置
        if not config.participants:
            raise HTTPException(status_code=400, detail="至少需要一个参与方")

        if edu_config.data_quality_checks_enabled:
            # 验证数据质量要求
            if len(config.subjects) < 1:
                raise HTTPException(status_code=400, detail="至少需要选择一个学科")

        # 启动训练
        training_id = await edu_service.start_training(config)

        # 在后台启动监控任务
        background_tasks.add_task(edu_service.monitor_training_progress, training_id)

        return {
            "training_id": training_id,
            "message": "教育数据联邦学习训练已启动",
            "model_name": config.model_name,
            "subjects": [s.value for s in config.subjects],
            "grade_levels": [g.value for g in config.grade_levels],
            "privacy_level": config.privacy_level.value,
            "created_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动教育数据联邦学习训练失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trainings/{training_id}", response_model=FLTrainingProgress)
async def get_edu_training_status(
    training_id: str,
    current_user: User = Depends(get_current_active_user),
    edu_service: EduFederatedLearningService = Depends(get_edu_fl_service),
):
    """
    获取教育数据训练状态
    """
    try:
        # 权限检查
        if (
            not current_user.has_permission("education_data")
            and not current_user.has_permission("ai")
            and not current_user.is_admin
        ):
            raise HTTPException(status_code=403, detail="权限不足")

        progress = await edu_service.get_training_status(training_id)
        if not progress:
            raise HTTPException(status_code=404, detail="训练不存在")
        return progress
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取训练状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reports/generate", response_model=EduReportMetadata)
async def generate_edu_report(
    report_request: EduReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    edu_service: EduFederatedLearningService = Depends(get_edu_fl_service),
):
    """
    生成教育数据分析报告
    """
    try:
        logger.info(f"用户 {current_user.username} 请求生成教育报告")

        # 权限检查
        if (
            not current_user.has_permission("education_data")
            and not current_user.has_permission("ai")
            and not current_user.is_admin
        ):
            raise HTTPException(status_code=403, detail="权限不足")

        # 验证报告格式
        if report_request.format.lower() not in edu_config.get_supported_formats():
            raise HTTPException(
                status_code=400, detail=f"不支持的报告格式: {report_request.format}"
            )

        # 生成报告
        report_metadata = await edu_service.generate_report(report_request)

        return report_metadata

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成教育报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reports/{report_id}/download")
async def download_edu_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user),
    edu_service: EduFederatedLearningService = Depends(get_edu_fl_service),
):
    """
    下载教育报告
    """
    try:
        # 权限检查
        if (
            not current_user.has_permission("education_data")
            and not current_user.has_permission("ai")
            and not current_user.is_admin
        ):
            raise HTTPException(status_code=403, detail="权限不足")

        report_file = await edu_service.get_report_file(report_id)
        if not report_file:
            raise HTTPException(status_code=404, detail="报告不存在")

        return report_file

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nodes/register", response_model=dict)
async def register_edu_node(
    node_info: EduNodeRegistration,
    current_user: User = Depends(get_current_active_user),
    edu_service: EduFederatedLearningService = Depends(get_edu_fl_service),
):
    """
    注册教育数据节点
    """
    try:
        logger.info(f"注册教育节点: {node_info.node_name}")

        # 权限检查
        if (
            not current_user.has_permission("education_data")
            and not current_user.is_admin
        ):
            raise HTTPException(status_code=403, detail="权限不足")

        success = await edu_service.register_node(node_info)
        if not success:
            raise HTTPException(status_code=400, detail="节点注册失败")

        return {
            "message": "节点注册成功",
            "node_id": node_info.node_id,
            "registered_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"注册节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data/upload")
async def upload_edu_data(
    file: UploadFile = File(...),
    metadata: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    edu_service: EduFederatedLearningService = Depends(get_edu_fl_service),
):
    """
    上传教育数据
    """
    try:
        logger.info(f"用户 {current_user.username} 上传教育数据文件: {file.filename}")

        # 权限检查
        if (
            not current_user.has_permission("education_data")
            and not current_user.is_admin
        ):
            raise HTTPException(status_code=403, detail="权限不足")

        # 解析元数据
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="元数据格式无效")

        # 验证文件类型
        allowed_extensions = [".csv", ".xlsx", ".json"]
        if not any(file.filename.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持的格式: {', '.join(allowed_extensions)}",
            )

        # 处理上传的数据
        data_batch = await edu_service.process_uploaded_data(file, metadata_dict)

        return {
            "message": "数据上传成功",
            "batch_id": data_batch.batch_id,
            "record_count": len(data_batch.records),
            "processed_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传教育数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/protocol", response_model=EduDataSharingProtocol)
async def get_data_sharing_protocol(
    current_user: User = Depends(get_current_active_user),
):
    """
    获取数据共享协议
    """
    try:
        protocol = EduDataSharingProtocol(
            protocol_version="1.0",
            data_types=[
                "student_demographics",
                "academic_performance",
                "school_information",
                "regional_statistics",
            ],
            privacy_guarantees=[
                "differential_privacy",
                "homomorphic_encryption",
                "secure_multi_party_computation",
            ],
            usage_restrictions=[
                "research_only",
                "aggregate_analysis_only",
                "no_individual_identification",
            ],
            retention_period=edu_config.report_retention_days,
            audit_requirements=[
                "data_access_logging",
                "privacy_budget_tracking",
                "compliance_monitoring",
            ],
            compliance_standards=["GDPR", "FERPA", "教育数据安全规范"],
        )

        return protocol

    except Exception as e:
        logger.error(f"获取数据共享协议失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=dict)
async def edu_data_health_check(
    edu_service: EduFederatedLearningService = Depends(get_edu_fl_service),
):
    """
    教育数据系统健康检查
    """
    try:
        health_status = await edu_service.health_check()
        return {
            "status": "healthy" if health_status.get("overall_status") else "unhealthy",
            "service": "Education Data Federated Learning",
            "timestamp": datetime.now().isoformat(),
            "details": health_status,
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=dict)
async def get_edu_data_statistics(
    current_user: User = Depends(get_current_active_user),
    edu_service: EduFederatedLearningService = Depends(get_edu_fl_service),
):
    """
    获取教育数据统计信息
    """
    try:
        # 权限检查
        if (
            not current_user.has_permission("education_data")
            and not current_user.is_admin
        ):
            raise HTTPException(status_code=403, detail="权限不足")

        stats = await edu_service.get_system_statistics()
        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
