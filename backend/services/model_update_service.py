"""
AI模型热更新服务
实现通过BLE推送新权重的模型更新功能
"""

from datetime import datetime
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from config.settings import settings
from models.model_version import ModelVersion
from utils.database import get_db

logger = logging.getLogger(__name__)


class ModelUpdateService:
    """模型更新服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.model_storage_path = Path(settings.MODEL_STORAGE_PATH)
        self.model_storage_path.mkdir(parents=True, exist_ok=True)

    async def upload_model_version(
        self,
        model_name: str,
        version: str,
        model_file_path: str,
        description: str = "",
        compression_enabled: bool = True,
    ) -> Dict[str, any]:
        """
        上传新模型版本

        Args:
            model_name: 模型名称
            version: 版本号 (语义化版本)
            model_file_path: 模型文件路径
            description: 版本描述
            compression_enabled: 是否启用压缩

        Returns:
            上传结果信息
        """
        try:
            # 验证模型文件是否存在
            if not os.path.exists(model_file_path):
                raise HTTPException(status_code=404, detail="模型文件不存在")

            # 检查版本是否已存在
            existing_version = (
                self.db.query(ModelVersion)
                .filter(
                    ModelVersion.model_name == model_name,
                    ModelVersion.version == version,
                )
                .first()
            )

            if existing_version:
                raise HTTPException(status_code=409, detail="该版本已存在")

            # 计算文件哈希
            file_hash = calculate_file_hash(model_file_path)

            # 获取文件大小
            file_size = os.path.getsize(model_file_path)

            # 压缩文件（如果启用）
            compressed_path = model_file_path
            compressed_size = file_size
            compression_ratio = 1.0

            if compression_enabled and file_size > 102400:  # 大于100KB才压缩
                compressed_path = f"{model_file_path}.lz4"
                compression_result = compress_file(
                    model_file_path, compressed_path, algorithm="lz4"
                )
                compressed_size = compression_result["compressed_size"]
                compression_ratio = compression_result["compression_ratio"]
                logger.info(
                    f"模型压缩完成: 原始{file_size}bytes -> 压缩{compressed_size}bytes "
                    f"(压缩比: {compression_ratio:.2f})"
                )

            # 保存到存储目录
            storage_filename = f"{model_name}_v{version}_{file_hash[:16]}"
            if compression_enabled:
                storage_filename += ".lz4"

            storage_path = self.model_storage_path / storage_filename
            os.rename(compressed_path, storage_path)

            # 创建数据库记录
            model_version = ModelVersion(
                model_name=model_name,
                version=version,
                file_path=str(storage_path),
                file_size=file_size,
                compressed_size=compressed_size,
                file_hash=file_hash,
                compression_ratio=compression_ratio,
                description=description,
                created_at=datetime.utcnow(),
                is_active=True,
            )

            self.db.add(model_version)
            self.db.commit()
            self.db.refresh(model_version)

            logger.info(f"模型版本上传成功: {model_name} v{version}")

            return {
                "model_id": model_version.id,
                "model_name": model_name,
                "version": version,
                "file_size": file_size,
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio,
                "file_hash": file_hash,
                "storage_path": str(storage_path),
                "created_at": model_version.created_at.isoformat(),
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"模型版本上传失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

    async def get_model_versions(self, model_name: str) -> List[Dict[str, any]]:
        """
        获取指定模型的所有版本

        Args:
            model_name: 模型名称

        Returns:
            版本列表
        """
        try:
            versions = (
                self.db.query(ModelVersion)
                .filter(ModelVersion.model_name == model_name)
                .order_by(ModelVersion.created_at.desc())
                .all()
            )

            return [
                {
                    "id": version.id,
                    "version": version.version,
                    "file_size": version.file_size,
                    "compressed_size": version.compressed_size,
                    "compression_ratio": version.compression_ratio,
                    "file_hash": version.file_hash,
                    "description": version.description,
                    "created_at": version.created_at.isoformat(),
                    "is_active": version.is_active,
                }
                for version in versions
            ]

        except Exception as e:
            logger.error(f"获取模型版本失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

    async def get_latest_model_version(
        self, model_name: str
    ) -> Optional[Dict[str, any]]:
        """
        获取指定模型的最新版本

        Args:
            model_name: 模型名称

        Returns:
            最新版本信息
        """
        try:
            latest_version = (
                self.db.query(ModelVersion)
                .filter(
                    ModelVersion.model_name == model_name,
                    ModelVersion.is_active == True,
                )
                .order_by(ModelVersion.created_at.desc())
                .first()
            )

            if not latest_version:
                return None

            return {
                "id": latest_version.id,
                "model_name": latest_version.model_name,
                "version": latest_version.version,
                "file_size": latest_version.file_size,
                "compressed_size": latest_version.compressed_size,
                "compression_ratio": latest_version.compression_ratio,
                "file_hash": latest_version.file_hash,
                "description": latest_version.description,
                "created_at": latest_version.created_at.isoformat(),
                "storage_path": latest_version.file_path,
            }

        except Exception as e:
            logger.error(f"获取最新模型版本失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

    async def prepare_model_for_transfer(
        self, model_id: int, chunk_size: int = 512
    ) -> Dict[str, any]:
        """
        为传输准备模型数据

        Args:
            model_id: 模型ID
            chunk_size: 数据块大小

        Returns:
            传输准备信息
        """
        try:
            model_version = (
                self.db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
            )

            if not model_version:
                raise HTTPException(status_code=404, detail="模型不存在")

            if not os.path.exists(model_version.file_path):
                raise HTTPException(status_code=404, detail="模型文件丢失")

            # 读取文件内容
            with open(model_version.file_path, "rb") as f:
                model_data = f.read()

            # 分割为数据块
            chunks = []
            for i in range(0, len(model_data), chunk_size):
                chunk = model_data[i : i + chunk_size]
                chunks.append(chunk)

            # 生成传输信息
            transfer_info = {
                "model_id": model_version.id,
                "model_name": model_version.model_name,
                "version": model_version.version,
                "total_size": len(model_data),
                "chunk_size": chunk_size,
                "total_chunks": len(chunks),
                "file_hash": model_version.file_hash,
                "compression_ratio": model_version.compression_ratio,
                "chunks": chunks,
                "prepared_at": datetime.utcnow().isoformat(),
            }

            logger.info(
                f"模型传输准备完成: {model_version.model_name} v{model_version.version}, "
                f"{len(chunks)}个数据块"
            )

            return transfer_info

        except Exception as e:
            logger.error(f"模型传输准备失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"准备失败: {str(e)}")

    async def get_chunk_data(
        self, model_id: int, chunk_index: int, chunk_size: int = 512
    ) -> bytes:
        """
        获取指定数据块

        Args:
            model_id: 模型ID
            chunk_index: 数据块索引
            chunk_size: 数据块大小

        Returns:
            数据块内容
        """
        try:
            model_version = (
                self.db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
            )

            if not model_version:
                raise HTTPException(status_code=404, detail="模型不存在")

            if not os.path.exists(model_version.file_path):
                raise HTTPException(status_code=404, detail="模型文件丢失")

            # 读取指定数据块
            with open(model_version.file_path, "rb") as f:
                f.seek(chunk_index * chunk_size)
                chunk_data = f.read(chunk_size)

            return chunk_data

        except Exception as e:
            logger.error(f"获取数据块失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

    async def validate_model_update(
        self, model_id: int, received_hash: str
    ) -> Dict[str, any]:
        """
        验证模型更新结果

        Args:
            model_id: 模型ID
            received_hash: 接收到的文件哈希

        Returns:
            验证结果
        """
        try:
            model_version = (
                self.db.query(ModelVersion).filter(ModelVersion.id == model_id).first()
            )

            if not model_version:
                raise HTTPException(status_code=404, detail="模型不存在")

            # 比较哈希值
            is_valid = model_version.file_hash.lower() == received_hash.lower()

            result = {
                "model_id": model_version.id,
                "model_name": model_version.model_name,
                "version": model_version.version,
                "expected_hash": model_version.file_hash,
                "received_hash": received_hash,
                "is_valid": is_valid,
                "validated_at": datetime.utcnow().isoformat(),
            }

            if is_valid:
                logger.info(
                    f"模型更新验证通过: {model_version.model_name} v{model_version.version}"
                )
            else:
                logger.warning(f"模型更新验证失败: 哈希不匹配")

            return result

        except Exception as e:
            logger.error(f"模型更新验证失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"验证失败: {str(e)}")


# 工具函数
def calculate_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """计算文件哈希值"""
    hash_obj = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()


def compress_file(
    input_path: str, output_path: str, algorithm: str = "lz4"
) -> Dict[str, any]:
    """压缩文件"""
    try:
        if algorithm == "lz4":
            import lz4.frame

            with (
                open(input_path, "rb") as infile,
                lz4.frame.open(output_path, "wb") as outfile,
            ):
                outfile.write(infile.read())
        else:
            raise ValueError(f"不支持的压缩算法: {algorithm}")

        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(output_path)
        compression_ratio = compressed_size / original_size if original_size > 0 else 0

        return {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
            "algorithm": algorithm,
        }

    except ImportError:
        # 如果没有安装lz4，使用gzip作为备选
        import gzip

        with open(input_path, "rb") as infile, gzip.open(output_path, "wb") as outfile:
            outfile.write(infile.read())

        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(output_path)
        compression_ratio = compressed_size / original_size if original_size > 0 else 0

        return {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "compression_ratio": compression_ratio,
            "algorithm": "gzip",
        }


# 依赖注入函数
def get_model_update_service(db: Session = Depends(get_db)) -> ModelUpdateService:
    """获取模型更新服务实例"""
    return ModelUpdateService(db)
