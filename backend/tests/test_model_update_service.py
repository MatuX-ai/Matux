"""
AI模型热更新服务测试用例
"""

from datetime import datetime
import os
import tempfile
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from ..services.model_update_service import (
    ModelUpdateService,
    calculate_file_hash,
    compress_file,
)


class TestModelUpdateService:
    """模型更新服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """创建模型更新服务实例"""
        return ModelUpdateService(mock_db)

    @pytest.fixture
    def sample_model_file(self):
        """创建示例模型文件"""
        with tempfile.NamedTemporaryFile(suffix=".tflite", delete=False) as f:
            # 写入一些测试数据
            test_data = b"This is a test model file content for testing purposes." * 100
            f.write(test_data)
            f.flush()
            yield f.name
        # 清理文件
        os.unlink(f.name)

    def test_calculate_file_hash(self, sample_model_file):
        """测试文件哈希计算"""
        hash_value = calculate_file_hash(sample_model_file)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256哈希长度
        assert hash_value.isalnum()

    def test_compress_file(self, sample_model_file):
        """测试文件压缩"""
        with tempfile.NamedTemporaryFile(
            suffix=".lz4", delete=False
        ) as compressed_file:
            result = compress_file(sample_model_file, compressed_file.name, "lz4")

            assert "original_size" in result
            assert "compressed_size" in result
            assert "compression_ratio" in result
            assert "algorithm" in result

            # 压缩比应该小于等于1
            assert result["compression_ratio"] <= 1.0

            # 压缩文件应该存在
            assert os.path.exists(compressed_file.name)

        os.unlink(compressed_file.name)

    @pytest.mark.asyncio
    async def test_upload_model_version_success(
        self, service, sample_model_file, mock_db
    ):
        """测试成功上传模型版本"""
        # 模拟查询返回None（版本不存在）
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.upload_model_version(
            model_name="test_model",
            version="1.0.0",
            model_file_path=sample_model_file,
            description="Test model version",
        )

        # 验证返回结果
        assert result["model_name"] == "test_model"
        assert result["version"] == "1.0.0"
        assert "file_hash" in result
        assert "storage_path" in result

        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_model_version_duplicate(
        self, service, sample_model_file, mock_db
    ):
        """测试重复版本上传"""
        # 模拟查询返回已存在的版本
        mock_version = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_version

        with pytest.raises(Exception) as exc_info:
            await service.upload_model_version(
                model_name="test_model",
                version="1.0.0",
                model_file_path=sample_model_file,
            )

        assert "该版本已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_upload_model_version_file_not_found(self, service, mock_db):
        """测试文件不存在的情况"""
        with pytest.raises(Exception) as exc_info:
            await service.upload_model_version(
                model_name="test_model",
                version="1.0.0",
                model_file_path="/nonexistent/file.tflite",
            )

        assert "模型文件不存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_model_versions(self, service, mock_db):
        """测试获取模型版本列表"""
        # 创建模拟版本数据
        mock_versions = [
            Mock(
                id=1,
                model_name="test_model",
                version="1.0.0",
                file_size=1024,
                compressed_size=512,
                compression_ratio=0.5,
                file_hash="abc123",
                description="First version",
                created_at=datetime.utcnow(),
                is_active=True,
            ),
            Mock(
                id=2,
                model_name="test_model",
                version="1.1.0",
                file_size=2048,
                compressed_size=1024,
                compression_ratio=0.5,
                file_hash="def456",
                description="Second version",
                created_at=datetime.utcnow(),
                is_active=True,
            ),
        ]

        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_versions
        )

        versions = await service.get_model_versions("test_model")

        assert len(versions) == 2
        assert versions[0]["version"] == "1.0.0"
        assert versions[1]["version"] == "1.1.0"
        assert all("id" in version for version in versions)
        assert all("file_size" in version for version in versions)

    @pytest.mark.asyncio
    async def test_get_latest_model_version(self, service, mock_db):
        """测试获取最新模型版本"""
        mock_version = Mock(
            id=1,
            model_name="test_model",
            version="2.0.0",
            file_size=1024,
            compressed_size=512,
            compression_ratio=0.5,
            file_hash="xyz789",
            description="Latest version",
            created_at=datetime.utcnow(),
            file_path="/path/to/model.tflite",
        )

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            mock_version
        )

        latest_version = await service.get_latest_model_version("test_model")

        assert latest_version is not None
        assert latest_version["version"] == "2.0.0"
        assert latest_version["model_name"] == "test_model"
        assert "storage_path" in latest_version

    @pytest.mark.asyncio
    async def test_get_latest_model_version_not_found(self, service, mock_db):
        """测试获取不存在的最新版本"""
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )

        latest_version = await service.get_latest_model_version("nonexistent_model")

        assert latest_version is None

    @pytest.mark.asyncio
    async def test_prepare_model_for_transfer(
        self, service, sample_model_file, mock_db
    ):
        """测试准备模型传输"""
        # 创建模拟模型版本
        mock_version = Mock()
        mock_version.id = 1
        mock_version.model_name = "test_model"
        mock_version.version = "1.0.0"
        mock_version.file_path = sample_model_file
        mock_version.file_hash = "test_hash"
        mock_version.compression_ratio = 0.5

        mock_db.query.return_value.filter.return_value.first.return_value = mock_version

        transfer_info = await service.prepare_model_for_transfer(1, chunk_size=256)

        assert transfer_info["model_id"] == 1
        assert transfer_info["model_name"] == "test_model"
        assert transfer_info["version"] == "1.0.0"
        assert "chunks" in transfer_info
        assert "total_chunks" in transfer_info
        assert transfer_info["chunk_size"] == 256
        assert len(transfer_info["chunks"]) > 0

    @pytest.mark.asyncio
    async def test_get_chunk_data(self, service, sample_model_file, mock_db):
        """测试获取数据块"""
        # 创建模拟模型版本
        mock_version = Mock()
        mock_version.file_path = sample_model_file

        mock_db.query.return_value.filter.return_value.first.return_value = mock_version

        # 获取第一个数据块
        chunk_data = await service.get_chunk_data(1, 0, chunk_size=128)

        assert isinstance(chunk_data, bytes)
        assert len(chunk_data) <= 128

    @pytest.mark.asyncio
    async def test_validate_model_update(self, service, mock_db):
        """测试模型更新验证"""
        # 创建模拟模型版本
        mock_version = Mock()
        mock_version.id = 1
        mock_version.model_name = "test_model"
        mock_version.version = "1.0.0"
        mock_version.file_hash = "expected_hash_value"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_version

        # 测试验证通过的情况
        result = await service.validate_model_update(1, "expected_hash_value")
        assert result["is_valid"] == True
        assert result["expected_hash"] == "expected_hash_value"
        assert result["received_hash"] == "expected_hash_value"

        # 测试验证失败的情况
        result = await service.validate_model_update(1, "different_hash_value")
        assert result["is_valid"] == False
        assert result["received_hash"] == "different_hash_value"


# 集成测试
class TestModelUpdateIntegration:
    """模型更新集成测试"""

    @pytest.mark.asyncio
    async def test_complete_update_flow(self, mock_db, sample_model_file):
        """测试完整的更新流程"""
        service = ModelUpdateService(mock_db)

        # 1. 上传模型版本
        with patch.object(service, "db", mock_db):
            mock_db.query.return_value.filter.return_value.first.return_value = None

            upload_result = await service.upload_model_version(
                model_name="integration_test_model",
                version="1.0.0",
                model_file_path=sample_model_file,
                description="Integration test model",
            )

            model_id = upload_result["model_id"]

            # 2. 准备传输
            mock_db.query.return_value.filter.return_value.first.return_value = Mock(
                id=model_id,
                model_name="integration_test_model",
                version="1.0.0",
                file_path=sample_model_file,
                file_hash=upload_result["file_hash"],
            )

            transfer_info = await service.prepare_model_for_transfer(
                model_id, chunk_size=256
            )

            # 3. 验证传输数据
            validation_result = await service.validate_model_update(
                model_id, upload_result["file_hash"]
            )

            assert validation_result["is_valid"] == True
            assert len(transfer_info["chunks"]) > 0
            assert transfer_info["total_size"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
