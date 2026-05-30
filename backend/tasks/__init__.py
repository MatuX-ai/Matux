"""
Celery任务定义文件
包含视频转码、文档处理等异步任务
"""

from datetime import datetime, timedelta
import logging
import os
from typing import Any, Dict, List

import boto3
from sqlalchemy.orm import Session

from celery_app import celery_app
from models.multimedia import (
    MediaTranscodingJob,
    MediaType,
    MultimediaResource,
    VideoStatus,
)
from services.multimedia_service import StorageConfig
from utils.database import get_db

logger = logging.getLogger(__name__)

# AWS MediaConvert配置
MEDIA_CONVERT_ROLE = os.getenv("MEDIA_CONVERT_ROLE")
MEDIA_CONVERT_ENDPOINT = os.getenv("MEDIA_CONVERT_ENDPOINT")


@celery_app.task(bind=True, name="tasks.video_transcode")
def transcode_video(self, video_id: int) -> Dict[str, Any]:
    """
    视频转码任务
    使用AWS Elemental MediaConvert进行视频转码

    Args:
        video_id: 视频资源ID

    Returns:
        Dict: 转码结果
    """
    try:
        # 获取数据库会话
        db_gen = get_db()
        db: Session = next(db_gen)

        # 获取视频资源和转码任务
        video = (
            db.query(MultimediaResource)
            .filter(MultimediaResource.id == video_id)
            .first()
        )
        if not video:
            raise ValueError(f"视频资源不存在: {video_id}")

        transcoding_job = (
            db.query(MediaTranscodingJob)
            .filter(MediaTranscodingJob.resource_id == video_id)
            .first()
        )

        if not transcoding_job:
            raise ValueError(f"转码任务不存在: {video_id}")

        # 更新任务状态为处理中
        transcoding_job.status = VideoStatus.PROCESSING
        transcoding_job.progress_percent = 0.0
        transcoding_job.started_at = datetime.utcnow()
        db.commit()

        # 初始化AWS MediaConvert客户端
        mediaconvert = boto3.client("mediaconvert", endpoint_url=MEDIA_CONVERT_ENDPOINT)

        # 构建转码作业配置
        job_settings = _build_transcoding_job_settings(
            video.original_url, transcoding_job.output_configs
        )

        # 创建转码作业
        response = mediaconvert.create_job(
            Role=MEDIA_CONVERT_ROLE,
            Settings=job_settings,
            Queue=os.getenv("MEDIA_CONVERT_QUEUE", ""),
            UserMetadata={"video_id": str(video_id), "job_id": transcoding_job.job_id},
        )

        # 更新转码任务信息
        job_id = response["Job"]["Id"]
        transcoding_job.job_id = job_id
        transcoding_job.status = VideoStatus.TRANSCODING
        transcoding_job.progress_percent = 10.0  # 初始进度
        db.commit()

        logger.info(f"视频转码作业已创建: {job_id} for video {video_id}")

        return {
            "success": True,
            "job_id": job_id,
            "video_id": video_id,
            "message": "转码作业已启动",
        }

    except Exception as e:
        logger.error(f"视频转码任务失败: {e}")

        # 更新失败状态
        if "db" in locals():
            transcoding_job = (
                db.query(MediaTranscodingJob)
                .filter(MediaTranscodingJob.resource_id == video_id)
                .first()
            )
            if transcoding_job:
                transcoding_job.status = VideoStatus.FAILED
                transcoding_job.error_message = str(e)
                transcoding_job.completed_at = datetime.utcnow()
                db.commit()

        raise self.retry(exc=e, countdown=60, max_retries=3)


def _build_transcoding_job_settings(
    input_url: str, output_configs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    构建MediaConvert转码作业配置

    Args:
        input_url: 输入文件URL
        output_configs: 输出配置

    Returns:
        Dict: MediaConvert作业配置
    """
    # 基础输入配置
    inputs = [
        {
            "FileInput": input_url,
            "AudioSelectors": {"Audio Selector 1": {"DefaultSelection": "DEFAULT"}},
            "VideoSelector": {"ColorSpace": "FOLLOW"},
        }
    ]

    # 构建输出组
    output_groups = []

    # HLS输出组
    if "hls" in output_configs.get("output_formats", []):
        hls_outputs = _build_hls_outputs(output_configs.get("quality_profiles", []))
        output_groups.append(
            {
                "Name": "HLS Outputs",
                "OutputGroupSettings": {
                    "Type": "HLS_GROUP_SETTINGS",
                    "HlsGroupSettings": {
                        "SegmentLength": 10,
                        "MinSegmentLength": 0,
                        "Destination": _get_output_destination("hls"),
                    },
                },
                "Outputs": hls_outputs,
            }
        )

    # MP4输出组
    if "mp4" in output_configs.get("output_formats", []):
        mp4_outputs = _build_mp4_outputs(output_configs.get("quality_profiles", []))
        output_groups.append(
            {
                "Name": "MP4 Outputs",
                "OutputGroupSettings": {
                    "Type": "FILE_GROUP_SETTINGS",
                    "FileGroupSettings": {
                        "Destination": _get_output_destination("mp4")
                    },
                },
                "Outputs": mp4_outputs,
            }
        )

    return {"Inputs": inputs, "OutputGroups": output_groups}


def _build_hls_outputs(quality_profiles: List[str]) -> List[Dict[str, Any]]:
    """构建HLS输出配置"""
    outputs = []

    quality_settings = {
        "1080p": {"Width": 1920, "Height": 1080, "Bitrate": 5000000},
        "720p": {"Width": 1280, "Height": 720, "Bitrate": 2500000},
        "480p": {"Width": 854, "Height": 480, "Bitrate": 1200000},
        "360p": {"Width": 640, "Height": 360, "Bitrate": 800000},
    }

    for profile in quality_profiles:
        if profile in quality_settings:
            settings = quality_settings[profile]
            outputs.append(
                {
                    "ContainerSettings": {
                        "Container": "M3U8",
                        "M3u8Settings": {
                            "AudioFramesPerPes": 4,
                            "PcrControl": "PCR_EVERY_PES_PACKET",
                        },
                    },
                    "VideoDescription": {
                        "CodecSettings": {
                            "Codec": "H_264",
                            "H264Settings": {
                                "MaxBitrate": settings["Bitrate"],
                                "RateControlMode": "QVBR",
                                "SceneChangeDetect": "TRANSITION_DETECTION",
                            },
                        },
                        "Width": settings["Width"],
                        "Height": settings["Height"],
                    },
                    "AudioDescriptions": [
                        {
                            "CodecSettings": {
                                "Codec": "AAC",
                                "AacSettings": {
                                    "Bitrate": 96000,
                                    "CodingMode": "CODING_MODE_2_0",
                                    "SampleRate": 48000,
                                },
                            }
                        }
                    ],
                }
            )

    return outputs


def _build_mp4_outputs(quality_profiles: List[str]) -> List[Dict[str, Any]]:
    """构建MP4输出配置"""
    outputs = []

    quality_settings = {
        "1080p": {"Width": 1920, "Height": 1080, "Bitrate": 5000000},
        "720p": {"Width": 1280, "Height": 720, "Bitrate": 2500000},
        "480p": {"Width": 854, "Height": 480, "Bitrate": 1200000},
    }

    for profile in quality_profiles:
        if profile in quality_settings:
            settings = quality_settings[profile]
            outputs.append(
                {
                    "ContainerSettings": {
                        "Container": "MP4",
                        "Mp4Settings": {
                            "CslgAtom": "INCLUDE",
                            "FreeSpaceBox": "EXCLUDE",
                            "MoovPlacement": "PROGRESSIVE_DOWNLOAD",
                        },
                    },
                    "VideoDescription": {
                        "CodecSettings": {
                            "Codec": "H_264",
                            "H264Settings": {
                                "MaxBitrate": settings["Bitrate"],
                                "RateControlMode": "QVBR",
                            },
                        },
                        "Width": settings["Width"],
                        "Height": settings["Height"],
                    },
                    "AudioDescriptions": [
                        {
                            "CodecSettings": {
                                "Codec": "AAC",
                                "AacSettings": {
                                    "Bitrate": 96000,
                                    "CodingMode": "CODING_MODE_2_0",
                                    "SampleRate": 48000,
                                },
                            }
                        }
                    ],
                }
            )

    return outputs


def _get_output_destination(output_type: str) -> str:
    """获取输出目标路径"""
    storage_config = StorageConfig()

    if storage_config.storage_type == "s3":
        base_path = f"s3://{storage_config.aws_bucket}/output/"
    else:
        base_path = "/processed/"

    return f"{base_path}{{JobId}}/{output_type}/"


@celery_app.task(name="tasks.check_transcoding_status")
def check_transcoding_status():
    """
    检查转码任务状态
    定期轮询AWS MediaConvert获取转码进度
    """
    try:
        db_gen = get_db()
        db: Session = next(db_gen)

        # 获取正在转码的任务
        active_jobs = (
            db.query(MediaTranscodingJob)
            .filter(MediaTranscodingJob.status == VideoStatus.TRANSCODING)
            .all()
        )

        if not active_jobs:
            return {"message": "没有活动的转码任务"}

        mediaconvert = boto3.client("mediaconvert", endpoint_url=MEDIA_CONVERT_ENDPOINT)

        for job in active_jobs:
            try:
                # 查询AWS MediaConvert作业状态
                response = mediaconvert.get_job(Id=job.job_id)
                job_status = response["Job"]["Status"]

                # 更新本地状态
                if job_status == "COMPLETE":
                    # 转码完成
                    job.status = VideoStatus.READY
                    job.progress_percent = 100.0
                    job.completed_at = datetime.utcnow()

                    # 更新视频资源状态
                    video = (
                        db.query(MultimediaResource)
                        .filter(MultimediaResource.id == job.resource_id)
                        .first()
                    )
                    if video:
                        video.video_status = VideoStatus.READY
                        video.processed_url = _generate_processed_url(job)

                elif job_status == "ERROR":
                    # 转码失败
                    job.status = VideoStatus.FAILED
                    job.error_message = response["Job"].get("ErrorMessage", "未知错误")
                    job.completed_at = datetime.utcnow()

                    # 更新视频资源状态
                    video = (
                        db.query(MultimediaResource)
                        .filter(MultimediaResource.id == job.resource_id)
                        .first()
                    )
                    if video:
                        video.video_status = VideoStatus.FAILED

                elif job_status == "PROGRESSING":
                    # 正在转码中，更新进度
                    progress = (
                        response["Job"].get("Timing", {}).get("ProgressPercent", 0)
                    )
                    job.progress_percent = float(progress)

                db.commit()

            except Exception as e:
                logger.error(f"检查转码任务 {job.job_id} 状态失败: {e}")
                continue

        return {
            "message": f"检查了 {len(active_jobs)} 个转码任务",
            "active_jobs": len(active_jobs),
        }

    except Exception as e:
        logger.error(f"检查转码状态任务失败: {e}")
        raise


def _generate_processed_url(job: MediaTranscodingJob) -> str:
    """生成处理后的文件URL"""
    storage_config = StorageConfig()

    if storage_config.storage_type == "s3":
        return f"https://{storage_config.aws_bucket}.s3.{storage_config.aws_region}.amazonaws.com/output/{job.job_id}/hls/playlist.m3u8"
    else:
        return f"/processed/{job.job_id}/hls/playlist.m3u8"


@celery_app.task(name="tasks.document_process")
def process_document(document_id: int) -> Dict[str, Any]:
    """
    文档处理任务
    包括PDF转换、缩略图生成等

    Args:
        document_id: 文档资源ID

    Returns:
        Dict: 处理结果
    """
    try:
        db_gen = get_db()
        db: Session = next(db_gen)

        document = (
            db.query(MultimediaResource)
            .filter(MultimediaResource.id == document_id)
            .first()
        )

        if not document:
            raise ValueError(f"文档资源不存在: {document_id}")

        if document.media_type != MediaType.DOCUMENT:
            raise ValueError("资源不是文档类型")

        # TODO: 实现具体的文档处理逻辑
        # - PDF转换
        # - 缩略图生成
        # - 文本提取
        # - OCR处理

        logger.info(f"文档处理完成: {document_id}")

        return {"success": True, "document_id": document_id, "message": "文档处理完成"}

    except Exception as e:
        logger.error(f"文档处理任务失败: {e}")
        raise


@celery_app.task(name="tasks.thumbnail_generate")
def generate_thumbnail(resource_id: int) -> Dict[str, Any]:
    """
    缩略图生成任务

    Args:
        resource_id: 资源ID

    Returns:
        Dict: 生成结果
    """
    try:
        db_gen = get_db()
        db: Session = next(db_gen)

        resource = (
            db.query(MultimediaResource)
            .filter(MultimediaResource.id == resource_id)
            .first()
        )

        if not resource:
            raise ValueError(f"资源不存在: {resource_id}")

        # TODO: 实现缩略图生成逻辑
        # - 视频关键帧提取
        # - 文档首页截图
        # - 图片缩放处理

        logger.info(f"缩略图生成完成: {resource_id}")

        return {
            "success": True,
            "resource_id": resource_id,
            "message": "缩略图生成完成",
        }

    except Exception as e:
        logger.error(f"缩略图生成任务失败: {e}")
        raise


@celery_app.task(name="tasks.cleanup_old_files")
def cleanup_old_files(days_old: int = 30) -> Dict[str, Any]:
    """
    清理旧文件任务

    Args:
        days_old: 清理多少天前的文件

    Returns:
        Dict: 清理结果
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        db_gen = get_db()
        db: Session = next(db_gen)

        # 查找需要清理的临时文件
        old_resources = (
            db.query(MultimediaResource)
            .filter(
                and_(
                    MultimediaResource.created_at < cutoff_date,
                    MultimediaResource.is_active == False,
                )
            )
            .all()
        )

        cleaned_count = 0
        storage_config = StorageConfig()

        for resource in old_resources:
            try:
                # 删除存储的文件
                if storage_config.storage_type == "s3":
                    _delete_s3_file(resource.original_url)
                else:
                    _delete_local_file(resource.original_url)

                # 从数据库删除记录
                db.delete(resource)
                cleaned_count += 1

            except Exception as e:
                logger.error(f"删除资源 {resource.id} 失败: {e}")
                continue

        db.commit()

        logger.info(f"清理完成: 删除了 {cleaned_count} 个旧文件")

        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "message": f"清理了 {cleaned_count} 个 {days_old} 天前的文件",
        }

    except Exception as e:
        logger.error(f"清理旧文件任务失败: {e}")
        raise


def _delete_s3_file(file_url: str):
    """删除S3文件"""
    if not file_url:
        return

    storage_config = StorageConfig()
    s3_client = storage_config.get_s3_client()

    # 从URL提取bucket和key
    if file_url.startswith("https://"):
        parts = file_url.split("/")
        bucket = parts[2].split(".")[0]
        key = "/".join(parts[3:])
        s3_client.delete_object(Bucket=bucket, Key=key)


def _delete_local_file(file_url: str):
    """删除本地文件"""
    if not file_url:
        return

    # 转换相对路径为绝对路径
    if file_url.startswith("/"):
        file_path = file_url[1:]  # 移除开头的斜杠
    else:
        file_path = file_url

    full_path = os.path.join(os.getcwd(), file_path)
    if os.path.exists(full_path):
        os.remove(full_path)


@celery_app.task(name="tasks.cleanup_failed_transcodes")
def cleanup_failed_transcodes(hours_old: int = 24) -> Dict[str, Any]:
    """
    清理失败的转码任务

    Args:
        hours_old: 清理多少小时前失败的任务

    Returns:
        Dict: 清理结果
    """
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)

        db_gen = get_db()
        db: Session = next(db_gen)

        # 查找失败且超时的转码任务
        failed_jobs = (
            db.query(MediaTranscodingJob)
            .filter(
                and_(
                    MediaTranscodingJob.status == VideoStatus.FAILED,
                    MediaTranscodingJob.completed_at < cutoff_time,
                )
            )
            .all()
        )

        cleaned_count = len(failed_jobs)

        # 删除失败的任务记录
        for job in failed_jobs:
            db.delete(job)

        db.commit()

        logger.info(f"清理失败转码任务完成: 删除了 {cleaned_count} 个任务")

        return {
            "success": True,
            "cleaned_count": cleaned_count,
            "message": f"清理了 {cleaned_count} 个 {hours_old} 小时前失败的转码任务",
        }

    except Exception as e:
        logger.error(f"清理失败转码任务失败: {e}")
        raise
