"""
多媒体资源管理API路由
提供视频上传、3D模型预览、文档处理等功能的RESTful API
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse

from models.multimedia import (
    DocumentFormat,
    DocumentProcessingRequest,
    MediaType,
    MultimediaResource,
    MultimediaResourceCreate,
    MultimediaResourceResponse,
    MultimediaResourceUpdate,
    ThreeDModelPreviewConfig,
    TranscodingJobResponse,
    VideoStatus,
    VideoTranscodingRequest,
    VideoUploadResponse,
)
from models.user import User
from services.document_service import DocumentProcessingService
from services.multimedia_service import MultimediaService
from services.three_d_service import ThreeDModelService
from utils.dependencies import get_current_user_sync, get_sync_db
from utils.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/org/{org_id}/multimedia", tags=["多媒体资源"])


# 依赖注入函数
def get_multimedia_service(db: Session = Depends(get_sync_db)) -> MultimediaService:
    return MultimediaService(db)


def get_3d_service(db: Session = Depends(get_sync_db)) -> ThreeDModelService:
    return ThreeDModelService(db)


def get_document_service(
    db: Session = Depends(get_sync_db),
) -> DocumentProcessingService:
    return DocumentProcessingService(db)


@router.post("/", response_model=MultimediaResourceResponse, summary="创建多媒体资源")
def create_multimedia_resource(
    org_id: int = get_current_tenant(),
    resource_data: MultimediaResourceCreate = Form(...),
    current_user: User = Depends(get_current_user_sync),
    service: MultimediaService = Depends(get_multimedia_service),
):
    """
    创建新的多媒体资源记录
    """
    try:
        resource = service.create_multimedia_resource(
            org_id, resource_data, current_user
        )
        return resource
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建多媒体资源失败 {e}")
        raise HTTPException(status_code=500, detail="创建资源失败")


@router.get(
    "/", response_model=List[MultimediaResourceResponse], summary="获取多媒体资源列表"
)
def list_multimedia_resources(
    org_id: int = get_current_tenant(),
    course_id: Optional[int] = Query(None, description="课程 ID 筛选"),
    media_type: Optional[MediaType] = Query(None, description="媒体类型筛选"),
    current_user: User = Depends(get_current_user_sync),
    service: MultimediaService = Depends(get_multimedia_service),
):
    """
    获取多媒体资源列表，支持按课程和媒体类型筛选
    """
    try:
        if course_id:
            resources = service.get_course_multimedia(org_id, course_id, media_type)
        else:
            # 如果没有指定课程，则获取该组织的所有资源
            resources = (
                service.db.query(MultimediaResource)
                .filter(MultimediaResource.org_id == org_id)
                .all()
            )

            if media_type:
                resources = [r for r in resources if r.media_type == media_type]

        return resources
    except Exception as e:
        logger.error(f"获取多媒体资源列表失败：{e}")
        raise HTTPException(status_code=500, detail="获取资源列表失败")


@router.get(
    "/{resource_id}",
    response_model=MultimediaResourceResponse,
    summary="获取多媒体资源详情",
)
def get_multimedia_resource(
    org_id: int = get_current_tenant(),
    resource_id: int = ...,
    current_user: User = Depends(get_current_user_sync),
    service: MultimediaService = Depends(get_multimedia_service),
):
    """
    获取指定多媒体资源的详细信息
    """
    try:
        resource = (
            service.db.query(MultimediaResource)
            .filter(
                MultimediaResource.id == resource_id,
                MultimediaResource.org_id == org_id,
            )
            .first()
        )

        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")

        return resource
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取多媒体资源详情失败 {e}")
        raise HTTPException(status_code=500, detail="获取资源详情失败")


@router.put(
    "/{resource_id}",
    response_model=MultimediaResourceResponse,
    summary="更新多媒体资源",
)
def update_multimedia_resource(
    org_id: int = get_current_tenant(),
    resource_id: int = ...,
    update_data: MultimediaResourceUpdate = ...,
    current_user: User = Depends(get_current_user_sync),
    service: MultimediaService = Depends(get_multimedia_service),
):
    """
    更新多媒体资源信息
    """
    try:
        resource = (
            service.db.query(MultimediaResource)
            .filter(
                MultimediaResource.id == resource_id,
                MultimediaResource.org_id == org_id,
            )
            .first()
        )

        if not resource:
            raise HTTPException(status_code=404, detail="资源不存在")

        # 检查权限
        if not service._can_manage_resource(current_user, resource):
            raise HTTPException(status_code=403, detail="无权修改此资源")

        # 更新字段
        update_fields = update_data.dict(exclude_unset=True)
        for field, value in update_fields.items():
            setattr(resource, field, value)

        service.db.commit()
        service.db.refresh(resource)

        return resource
    except HTTPException:
        raise
    except Exception as e:
        service.db.rollback()
        logger.error(f"更新多媒体资源失败 {e}")
        raise HTTPException(status_code=500, detail="更新资源失败")


@router.delete("/{resource_id}", summary="删除多媒体资源")
def delete_multimedia_resource(
    org_id: int = get_current_tenant(),
    resource_id: int = ...,
    current_user: User = Depends(get_current_user_sync),
    service: MultimediaService = Depends(get_multimedia_service),
):
    """
    删除多媒体资源（逻辑删除）
    """
    try:
        success = service.delete_multimedia_resource(org_id, resource_id, current_user)
        if success:
            return {"message": "资源删除成功"}
        else:
            raise HTTPException(status_code=500, detail="删除资源失败")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除多媒体资源失败 {e}")
        raise HTTPException(status_code=500, detail="删除资源失败")


# 视频上传相关API
@router.post(
    "/{resource_id}/upload-url",
    response_model=VideoUploadResponse,
    summary="获取视频上传URL",
)
def get_video_upload_url(
    org_id: int = get_current_tenant(),
    resource_id: int = ...,
    current_user: User = Depends(get_current_user_sync),
    service: MultimediaService = Depends(get_multimedia_service),
):
    """
    获取视频文件上传的预签名URL
    """
    try:
        upload_info = service.get_upload_presigned_url(
            org_id, resource_id, current_user
        )
        return VideoUploadResponse(**upload_info)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取上传URL失败: {e}")
        raise HTTPException(status_code=500, detail="获取上传URL失败")


@router.post(
    "/{resource_id}/complete-upload",
    response_model=MultimediaResourceResponse,
    summary="完成文件上传",
)
def complete_file_upload(
    org_id: int = get_current_tenant(),
    resource_id: int = ...,
    file_size: int = Form(...),
    mime_type: str = Form(...),
    current_user: User = Depends(get_current_user_sync),
    service: MultimediaService = Depends(get_multimedia_service),
):
    """
    完成文件上传，更新资源信息
    """
    try:
        file_info = {"file_size": file_size, "mime_type": mime_type}
        resource = service.complete_upload(org_id, resource_id, file_info, current_user)
        return resource
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"完成上传失败: {e}")
        raise HTTPException(status_code=500, detail="完成上传失败")


@router.post(
    "/{resource_id}/transcode",
    response_model=TranscodingJobResponse,
    summary="启动视频转码",
)
def start_video_transcoding(
    org_id: int = get_current_tenant(),
    resource_id: int = ...,
    transcoding_request: VideoTranscodingRequest = ...,
    current_user: User = Depends(get_current_user_sync),
    service: MultimediaService = Depends(get_multimedia_service),
):
    """
    启动视频转码任务
    """
    try:
        job = service.initiate_video_transcoding(
            org_id, resource_id, transcoding_request.quality_profiles, current_user
        )
        return TranscodingJobResponse(
            job_id=job.job_id,
            resource_id=job.resource_id,
            status=job.status,
            progress_percent=job.progress_percent,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启动视频转码失败: {e}")
        raise HTTPException(status_code=500, detail="启动转码失败")


@router.get(
    "/transcoding-jobs/{job_id}",
    response_model=TranscodingJobResponse,
    summary="获取转码任务状态",
)
def get_transcoding_job_status(
    org_id: int = get_current_tenant(),
    job_id: str = ...,
    current_user: User = Depends(get_current_user_sync),
    service: MultimediaService = Depends(get_multimedia_service),
):
    """
    获取视频转码任务的当前状态
    """
    try:
        job = (
            service.db.query(MediaTranscodingJob)
            .filter(
                MediaTranscodingJob.job_id == job_id,
                MediaTranscodingJob.org_id == org_id,
            )
            .first()
        )

        if not job:
            raise HTTPException(status_code=404, detail="转码任务不存在")

        return TranscodingJobResponse(
            job_id=job.job_id,
            resource_id=job.resource_id,
            status=job.status,
            progress_percent=job.progress_percent,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取转码任务失败：{e}")
        raise HTTPException(status_code=500, detail="获取任务状态失败")


# 3D模型相关API
@router.post("/{resource_id}/process-3d", summary="处理3D模型")
def process_3d_model(
    org_id: int = get_current_tenant(),
    resource_id: int = ...,
    current_user: User = Depends(get_current_user_sync),
    service: ThreeDModelService = Depends(get_3d_service),
):
    """
    处理3D模型文件，生成预览数据
    """
    try:
        result = service.process_3d_model(resource_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"处理3D模型失败: {e}")
        raise HTTPException(status_code=500, detail="处理3D模型失败")


@router.get(
    "/{resource_id}/preview-3d", response_class=HTMLResponse, summary="获取3D模型预览"
)
def get_3d_model_preview(
    org_id: int = get_current_tenant(),
    resource_id: int = ...,
    container_id: Optional[str] = Query(None, description="预览容器ID"),
    current_user: User = Depends(get_current_user_sync),
    service: ThreeDModelService = Depends(get_3d_service),
):
    """
    获取3D模型的交互式预览HTML页面
    """
    try:
        html_content = service.get_model_preview_html(resource_id, container_id)
        return HTMLResponse(content=html_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取3D模型预览失败: {e}")
        raise HTTPException(status_code=500, detail="获取预览失败")


@router.get("/3d-formats", summary="获取支持的3D模型格式")
def get_supported_3d_formats(service: ThreeDModelService = Depends(get_3d_service)):
    """
    获取系统支持的3D模型格式列表
    """
    try:
        formats = service.get_supported_formats()
        return {"supported_formats": formats}
    except Exception as e:
        logger.error(f"获取3D格式列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取格式列表失败")


# 文档处理相关API
@router.post("/{resource_id}/process-document", summary="处理文档")
def process_document(
    org_id: int = get_current_tenant(),
    resource_id: int = ...,
    processing_request: DocumentProcessingRequest = ...,
    current_user: User = Depends(get_current_user_sync),
    service: DocumentProcessingService = Depends(get_document_service),
):
    """
    处理文档文件，包括文本提取、PDF转换、缩略图生成等
    """
    try:
        result = service.process_document(
            resource_id,
            processing_request.convert_to_pdf,
            processing_request.generate_thumbnails,
            processing_request.extract_text,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"处理文档失败: {e}")
        raise HTTPException(status_code=500, detail="处理文档失败")


@router.get("/document-formats", summary="获取支持的文档格式")
def get_supported_document_formats(
    service: DocumentProcessingService = Depends(get_document_service),
):
    """
    获取系统支持的文档格式列表
    """
    try:
        formats = service.get_supported_formats()
        return {"supported_formats": [f.value for f in formats]}
    except Exception as e:
        logger.error(f"获取文档格式列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取格式列表失败")


# 统计和搜索API
@router.get("/statistics", summary="获取多媒体资源统计信息")
def get_multimedia_statistics(
    org_id: int = get_current_tenant(),
    current_user: User = Depends(get_current_user_sync),
    service: MultimediaService = Depends(get_multimedia_service),
):
    """
    获取组织的多媒体资源统计信息
    """
    try:
        # 统计各类资源数量
        stats = {}

        for media_type in MediaType:
            count = (
                service.db.query(MultimediaResource)
                .filter(
                    MultimediaResource.org_id == org_id,
                    MultimediaResource.media_type == media_type,
                    MultimediaResource.is_active == True,
                )
                .count()
            )
            stats[media_type.value] = count

        # 统计视频转码状态
        transcoding_stats = {}
        for status in VideoStatus:
            count = (
                service.db.query(MediaTranscodingJob)
                .filter(
                    MediaTranscodingJob.org_id == org_id,
                    MediaTranscodingJob.status == status,
                )
                .count()
            )
            transcoding_stats[status.value] = count

        return {
            "resource_counts": stats,
            "transcoding_stats": transcoding_stats,
            "total_resources": sum(stats.values()),
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")


@router.get(
    "/search", response_model=List[MultimediaResourceResponse], summary="搜索多媒体资源"
)
def search_multimedia_resources(
    org_id: int = get_current_tenant(),
    query: str = Query(..., description="搜索关键词"),
    media_type: Optional[MediaType] = Query(None, description="媒体类型筛选"),
    current_user: User = Depends(get_current_user_sync),
    service: MultimediaService = Depends(get_multimedia_service),
):
    """
    搜索多媒体资源（按标题、描述、标签搜索）
    """
    try:
        from sqlalchemy import or_

        search_query = service.db.query(MultimediaResource).filter(
            MultimediaResource.org_id == org_id, MultimediaResource.is_active == True
        )

        # 添加搜索条件
        search_conditions = [
            MultimediaResource.title.contains(query),
            MultimediaResource.description.contains(query),
        ]

        # 搜索标签（如果存储为 JSON）
        try:
            search_conditions.append(MultimediaResource.tags.contains(query))
        except (AttributeError, TypeError):
            pass  # 如果 tags 不是 JSON 格式则跳过

        search_query = search_query.filter(or_(*search_conditions))

        # 添加媒体类型筛选
        if media_type:
            search_query = search_query.filter(
                MultimediaResource.media_type == media_type
            )

        results = search_query.order_by(MultimediaResource.created_at.desc()).all()
        return results

    except Exception as e:
        logger.error(f"搜索多媒体资源失败 {e}")
        raise HTTPException(status_code=500, detail="搜索失败")


# 文件上传端点（直接上传）
@router.post(
    "/upload", response_model=MultimediaResourceResponse, summary="直接上传文件"
)
async def direct_file_upload(
    org_id: int = get_current_tenant(),
    course_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    media_type: MediaType = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_sync),
    multimedia_service: MultimediaService = Depends(get_multimedia_service),
    document_service: DocumentProcessingService = Depends(get_document_service),
):
    """
    直接上传文件并自动处理
    """
    try:
        # 创建资源记录
        resource_data = MultimediaResourceCreate(
            course_id=course_id,
            title=title,
            description=description,
            media_type=media_type,
            file_name=file.filename,
            mime_type=file.content_type,
        )

        resource = multimedia_service.create_multimedia_resource(
            org_id, resource_data, current_user
        )

        # 保存文件
        file_content = await file.read()

        # 根据存储类型保存文件
        if multimedia_service.storage_config.storage_type == "s3":
            # 保存到S3
            s3_client = multimedia_service.storage_config.get_s3_client()
            file_key = f"multimedia/{org_id}/{course_id}/{resource.id}_{file.filename}"

            s3_client.put_object(
                Bucket=multimedia_service.storage_config.aws_bucket,
                Key=file_key,
                Body=file_content,
                ContentType=file.content_type,
            )

            resource.original_url = f"https://{multimedia_service.storage_config.aws_bucket}.s3.{multimedia_service.storage_config.aws_region}.amazonaws.com/{file_key}"
        else:
            # 保存到本地
            import os

            upload_dir = os.path.join(
                multimedia_service.storage_config.local_storage_path,
                str(org_id),
                str(course_id),
            )
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, f"{resource.id}_{file.filename}")
            with open(file_path, "wb") as f:
                f.write(file_content)

            resource.original_url = (
                f"/uploads/{org_id}/{course_id}/{resource.id}_{file.filename}"
            )

        # 更新文件大小
        resource.file_size = len(file_content)

        # 根据媒体类型进行相应处理
        if media_type == MediaType.DOCUMENT:
            # 处理文档
            await document_service.process_document(resource.id)
        elif media_type == MediaType.THREE_D_MODEL:
            # 处理3D模型
            from services.three_d_service import ThreeDModelService

            threed_service = ThreeDModelService(multimedia_service.db)
            await threed_service.process_3d_model(resource.id)
        elif media_type == MediaType.VIDEO:
            # 设置视频状态
            resource.video_status = VideoStatus.UPLOADED

        multimedia_service.db.commit()
        multimedia_service.db.refresh(resource)

        return resource

    except Exception as e:
        multimedia_service.db.rollback()
        logger.error(f"直接文件上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
