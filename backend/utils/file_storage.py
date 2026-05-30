"""
文件存储管理工具
处理文件上传、存储和访问的通用服务
"""

from datetime import datetime
import os
from typing import Any, Dict, Optional
import uuid


class FileStorageManager:
    """文件存储管理器"""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or os.path.join(os.getcwd(), "uploads")
        self.ensure_storage_directory()

    def ensure_storage_directory(self):
        """确保存储目录存在"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path, exist_ok=True)

    def save_file(
        self, file_content: bytes, filename: str, subdirectory: str = ""
    ) -> str:
        """
        保存文件到存储目录

        Args:
            file_content: 文件内容
            filename: 原始文件名
            subdirectory: 子目录路径

        Returns:
            str: 文件存储路径
        """
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4()}_{filename}"

        # 构建完整路径
        if subdirectory:
            full_path = os.path.join(self.storage_path, subdirectory, unique_filename)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
        else:
            full_path = os.path.join(self.storage_path, unique_filename)

        # 保存文件
        with open(full_path, "wb") as f:
            f.write(file_content)

        return full_path

    def get_file_url(self, file_path: str) -> str:
        """
        获取文件访问URL

        Args:
            file_path: 文件路径

        Returns:
            str: 文件URL
        """
        # 从完整路径中提取相对路径
        relative_path = os.path.relpath(file_path, self.storage_path)
        return f"/uploads/{relative_path.replace(os.sep, '/')}"

    def delete_file(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 删除是否成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False

    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            Optional[Dict]: 文件信息字典
        """
        try:
            if not os.path.exists(file_path):
                return None

            stat = os.stat(file_path)
            return {
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "name": os.path.basename(file_path),
            }
        except Exception as e:
            print(f"获取文件信息失败: {e}")
            return None


# S3存储管理器（可选）
class S3StorageManager:
    """AWS S3存储管理器"""

    def __init__(
        self,
        aws_access_key: str,
        aws_secret_key: str,
        bucket_name: str,
        region: str = "us-east-1",
    ):
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = None
        self._initialize_s3_client()

    def _initialize_s3_client(self):
        """初始化S3客户端"""
        try:
            import boto3

            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.region,
            )
        except ImportError:
            print("警告: boto3未安装，S3存储不可用")
        except Exception as e:
            print(f"S3客户端初始化失败: {e}")

    def save_file(
        self, file_content: bytes, filename: str, folder: str = ""
    ) -> Optional[str]:
        """
        保存文件到S3

        Args:
            file_content: 文件内容
            filename: 文件名
            folder: S3文件夹路径

        Returns:
            Optional[str]: S3文件URL
        """
        if not self.s3_client:
            return None

        try:
            # 构建S3键名
            key = (
                f"{folder}/{uuid.uuid4()}_{filename}"
                if folder
                else f"{uuid.uuid4()}_{filename}"
            )

            # 上传文件
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType=self._get_content_type(filename),
            )

            # 返回公共URL
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"

        except Exception as e:
            print(f"S3文件上传失败: {e}")
            return None

    def _get_content_type(self, filename: str) -> str:
        """根据文件扩展名获取内容类型"""
        extension = filename.lower().split(".")[-1] if "." in filename else ""

        content_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "pdf": "application/pdf",
            "txt": "text/plain",
            "html": "text/html",
            "css": "text/css",
            "js": "application/javascript",
            "json": "application/json",
            "zip": "application/zip",
            "mp4": "video/mp4",
            "avi": "video/x-msvideo",
            "mov": "video/quicktime",
        }

        return content_types.get(extension, "application/octet-stream")

    def delete_file(self, s3_key: str) -> bool:
        """删除S3文件"""
        if not self.s3_client:
            return False

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except Exception as e:
            print(f"S3文件删除失败: {e}")
            return False


# 存储配置类
class StorageConfig:
    """存储配置管理"""

    def __init__(self):
        self.storage_type = os.getenv("STORAGE_TYPE", "local")  # local 或 s3
        self.local_storage_path = os.getenv("UPLOAD_PATH", "./uploads")

        # S3配置
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_bucket = os.getenv("AWS_BUCKET_NAME")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")

    def get_storage_manager(self):
        """获取适当的存储管理器"""
        if self.storage_type == "s3" and self.aws_access_key and self.aws_bucket:
            return S3StorageManager(
                self.aws_access_key,
                self.aws_secret_key,
                self.aws_bucket,
                self.aws_region,
            )
        else:
            return FileStorageManager(self.local_storage_path)

    def get_s3_client(self):
        """获取S3客户端（如果配置了S3）"""
        if self.storage_type == "s3":
            manager = self.get_storage_manager()
            return manager.s3_client if hasattr(manager, "s3_client") else None
        return None
