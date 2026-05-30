"""
任务编排服务单元测试 - 模型文件大小计算
测试覆盖：文件大小计算、边界情况、异常处理
"""

import asyncio
import os
from pathlib import Path

# 添加项目路径
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.task_orchestration_service import TaskOrchestrationService

# ==================== 测试夹具 ====================


@pytest.fixture
def temp_model_file():
    """创建临时模型文件用于测试"""
    # 创建一个 1MB 的临时文件
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pth") as f:
        # 写入 1MB 数据 (1024 * 1024 bytes)
        f.write(b"\x00" * (1024 * 1024))
        temp_path = f.name

    try:
        yield temp_path
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.fixture
def small_model_file():
    """创建小型临时模型文件（1KB）"""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pth") as f:
        f.write(b"\x00" * 1024)
        temp_path = f.name

    try:
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.fixture
def large_model_file():
    """创建大型临时模型文件（10MB）"""
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pth") as f:
        f.write(b"\x00" * (10 * 1024 * 1024))
        temp_path = f.name

    try:
        yield temp_path
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


@pytest.fixture
def task_orchestration_service():
    """创建任务编排服务实例"""
    return TaskOrchestrationService(db_session=None)


# ==================== 文件大小计算测试 ====================


class TestModelFileSizeCalculation:
    """模型文件大小计算测试"""

    @pytest.mark.asyncio
    async def test_1mb_file_size(self, task_orchestration_service, temp_model_file):
        """测试 1MB 文件计算"""
        result = await task_orchestration_service._calculate_model_file_size(
            temp_model_file
        )

        assert result == 1.0, f"期望 1.0 MB，实际 {result} MB"

    @pytest.mark.asyncio
    async def test_1kb_file_size(self, task_orchestration_service, small_model_file):
        """测试 1KB 文件计算（小于 1MB）"""
        result = await task_orchestration_service._calculate_model_file_size(
            small_model_file
        )

        # 1KB = 0.0009765625 MB，四舍五入到 2 位小数应该是 0.0
        assert 0.0 <= result < 0.01, f"小文件应该接近 0 MB，实际 {result} MB"

    @pytest.mark.asyncio
    async def test_10mb_file_size(self, task_orchestration_service, large_model_file):
        """测试 10MB 文件计算"""
        result = await task_orchestration_service._calculate_model_file_size(
            large_model_file
        )

        assert result == 10.0, f"期望 10.0 MB，实际 {result} MB"

    @pytest.mark.asyncio
    async def test_nonexistent_file(self, task_orchestration_service):
        """测试不存在的文件"""
        fake_path = "/fake/path/model.pth"
        result = await task_orchestration_service._calculate_model_file_size(fake_path)

        assert result == 0.0, "不存在的文件应该返回 0.0 MB"

    @pytest.mark.asyncio
    async def test_empty_string_path(self, task_orchestration_service):
        """测试空字符串路径"""
        result = await task_orchestration_service._calculate_model_file_size("")

        # 空字符串可能会被解释为当前目录，所以不强制要求返回 0.0
        # 主要验证方法不会崩溃
        assert isinstance(result, float), "应该返回浮点数"

    @pytest.mark.asyncio
    async def test_exact_mb_boundary(self, task_orchestration_service):
        """测试精确 MB 边界（2MB）"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pth") as f:
            # 创建恰好 2MB 的文件
            f.write(b"\x00" * (2 * 1024 * 1024))
            temp_path = f.name

        try:
            result = await task_orchestration_service._calculate_model_file_size(
                temp_path
            )
            assert result == 2.0, f"期望 2.0 MB，实际 {result} MB"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_decimal_precision(self, task_orchestration_service):
        """测试小数精度（保留 2 位小数）"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pth") as f:
            # 创建 1.5MB 的文件
            size_bytes = int(1.5 * 1024 * 1024)
            f.write(b"\x00" * size_bytes)
            temp_path = f.name

        try:
            result = await task_orchestration_service._calculate_model_file_size(
                temp_path
            )
            assert result == 1.5, f"期望 1.5 MB，实际 {result} MB"
            # 验证小数位数
            assert len(str(result).split(".")[-1]) <= 2, "应该最多保留 2 位小数"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


# ==================== 评估方法集成测试 ====================


class TestEvaluateModelIntegration:
    """模型评估集成测试"""

    @pytest.mark.asyncio
    async def test_evaluate_model_includes_file_size(
        self, task_orchestration_service, temp_model_file
    ):
        """测试评估结果包含文件大小"""
        training_report = {"accuracy": 0.95, "loss": 0.05, "training_time_minutes": 30}

        result = await task_orchestration_service._evaluate_model(
            temp_model_file, training_report
        )

        assert "model_size_mb" in result, "评估结果应包含 model_size_mb"
        assert (
            result["model_size_mb"] == 1.0
        ), f"期望 1.0 MB，实际 {result['model_size_mb']} MB"
        assert result["accuracy"] == 0.95
        assert result["loss"] == 0.05
        assert result["training_time_minutes"] == 30

    @pytest.mark.asyncio
    async def test_evaluate_model_with_missing_file(self, task_orchestration_service):
        """测试文件缺失时的评估"""
        training_report = {"accuracy": 0.90, "loss": 0.10, "training_time_minutes": 20}

        fake_path = "/nonexistent/model.pth"
        result = await task_orchestration_service._evaluate_model(
            fake_path, training_report
        )

        assert "model_size_mb" in result
        assert result["model_size_mb"] == 0.0, "文件缺失时大小应为 0.0 MB"
        assert result["accuracy"] == 0.90

    @pytest.mark.asyncio
    async def test_evaluate_model_all_fields(
        self, task_orchestration_service, temp_model_file
    ):
        """测试评估结果所有字段完整"""
        training_report = {"accuracy": 0.88, "loss": 0.12, "training_time_minutes": 45}

        result = await task_orchestration_service._evaluate_model(
            temp_model_file, training_report
        )

        # 验证所有必需字段
        required_fields = [
            "accuracy",
            "loss",
            "training_time_minutes",
            "model_size_mb",
            "evaluated_at",
        ]
        for field in required_fields:
            assert field in result, f"缺少必需字段：{field}"

        # 验证字段值
        assert result["accuracy"] == 0.88
        assert result["loss"] == 0.12
        assert result["training_time_minutes"] == 45
        assert result["model_size_mb"] == 1.0
        assert "evaluated_at" in result  # ISO 格式时间戳


# ==================== 边界条件测试 ====================


class TestEdgeCases:
    """边界条件测试"""

    @pytest.mark.asyncio
    async def test_very_small_file(self, task_orchestration_service):
        """测试非常小的文件（1 字节）"""
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pth") as f:
            f.write(b"\x00")  # 1 字节
            temp_path = f.name

        try:
            result = await task_orchestration_service._calculate_model_file_size(
                temp_path
            )
            assert result == 0.0, "1 字节文件应该显示为 0.0 MB（四舍五入）"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_directory_instead_file(self, task_orchestration_service):
        """测试传入目录而非文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = await task_orchestration_service._calculate_model_file_size(
                temp_dir
            )
            # 应该返回 0.0 或抛出异常被捕获
            assert result == 0.0, "目录应该返回 0.0 MB"

    @pytest.mark.asyncio
    async def test_permission_denied_simulation(self, task_orchestration_service):
        """测试权限拒绝场景（模拟）"""
        # 在某些系统上可能无法直接测试权限问题
        # 这里主要验证异常处理逻辑
        import stat

        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pth") as f:
            f.write(b"\x00" * 1024)
            temp_path = f.name

        try:
            # 尝试设置文件不可读（在某些系统上可能无效）
            try:
                os.chmod(temp_path, stat.S_IRUSR)  # 只读
            except (OSError, PermissionError):
                pass  # 忽略权限设置失败

            # 即使权限设置失败，方法也应该优雅处理
            result = await task_orchestration_service._calculate_model_file_size(
                temp_path
            )
            assert isinstance(result, float), "应该返回浮点数"
        finally:
            try:
                if os.path.exists(temp_path):
                    os.chmod(temp_path, stat.S_IWUSR | stat.S_IRUSR)  # 恢复写权限
                    os.unlink(temp_path)
            except (OSError, IOError, PermissionError):
                pass


# ==================== 性能测试 ====================


class TestPerformance:
    """性能测试"""

    @pytest.mark.asyncio
    async def test_large_file_performance(self, task_orchestration_service):
        """测试大文件计算性能（100MB）"""
        import time

        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pth") as f:
            # 创建 100MB 文件
            f.write(b"\x00" * (100 * 1024 * 1024))
            temp_path = f.name

        try:
            start_time = time.time()
            result = await task_orchestration_service._calculate_model_file_size(
                temp_path
            )
            duration = time.time() - start_time

            assert result == 100.0, f"期望 100.0 MB，实际 {result} MB"
            assert duration < 1.0, f"应该在 1 秒内完成，实际 {duration:.2f} 秒"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


# ==================== 运行测试 ====================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
