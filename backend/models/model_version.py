"""
AI模型版本管理数据模型
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ModelVersion(Base):
    """模型版本信息表"""

    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_name = Column(String(100), nullable=False, index=True, comment="模型名称")
    version = Column(String(20), nullable=False, comment="版本号")
    file_path = Column(String(500), nullable=False, comment="模型文件存储路径")
    file_size = Column(Integer, nullable=False, comment="原始文件大小(bytes)")
    compressed_size = Column(Integer, nullable=False, comment="压缩后文件大小(bytes)")
    file_hash = Column(String(64), nullable=False, comment="文件SHA256哈希值")
    compression_ratio = Column(Float, default=1.0, comment="压缩比")
    description = Column(Text, nullable=True, comment="版本描述")
    created_at = Column(DateTime, nullable=False, comment="创建时间")
    is_active = Column(Boolean, default=True, comment="是否为活跃版本")
    metadata_json = Column(Text, nullable=True, comment="额外元数据(JSON格式)")

    def __repr__(self):
        return f"<ModelVersion(id={self.id}, model='{self.model_name}', version='{self.version}')>"
