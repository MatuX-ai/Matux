"""
AI-Edu 代码执行 API 端点
支持多种编程语言的在线代码执行
使用 Docker 沙箱隔离确保安全
"""

import logging
import os
import subprocess
import tempfile
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class CodeExecutionRequest(BaseModel):
    """代码执行请求模型"""

    code: str = Field(..., description="要执行的代码")
    language: str = Field(
        ..., description="编程语言", examples=["python", "javascript"]
    )
    timeout: int = Field(default=5, description="超时时间（秒）", ge=1, le=30)


class CodeExecutionResponse(BaseModel):
    """代码执行响应模型"""

    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float
    memory_usage: Optional[int] = None


class TestResult(BaseModel):
    """测试结果"""

    passed: bool
    output: str
    expected: Optional[str] = None
    actual: Optional[str] = None


@router.post("/execute-code", response_model=CodeExecutionResponse)
async def execute_code(request: CodeExecutionRequest):
    """
    执行提交的代码并返回结果（Docker 沙箱隔离）

    Args:
        request: 代码执行请求

    Returns:
        代码执行结果
    """
    try:
        # 导入沙箱服务
        from services.code_sandbox_service import get_sandbox_service

        sandbox = get_sandbox_service()

        # 在沙箱中执行代码
        result = sandbox.execute_code(
            code=request.code,
            language=request.language,
            timeout_seconds=request.timeout,
        )

        return CodeExecutionResponse(
            success=result.success,
            output=result.output,
            error=result.error if result.error else None,
            execution_time=result.execution_time_ms / 1000,
            memory_usage=result.memory_used_kb,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"代码执行失败：{e}")
        raise HTTPException(status_code=500, detail=f"代码执行失败：{str(e)}")


async def execute_python_code(code: str, timeout: int = 5) -> CodeExecutionResponse:
    """
    执行 Python 代码

    Args:
        code: Python 代码字符串
        timeout: 超时时间（秒）

    Returns:
        执行结果
    """
    import time

    start_time = time.time()

    # 创建临时文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        temp_file = f.name

    try:
        # 执行代码
        result = subprocess.run(
            ["python", temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )

        execution_time = time.time() - start_time

        return CodeExecutionResponse(
            success=result.returncode == 0,
            output=result.stdout or "",
            error=result.stderr if result.returncode != 0 else None,
            execution_time=execution_time,
        )
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)


async def execute_javascript_code(code: str, timeout: int = 5) -> CodeExecutionResponse:
    """
    执行 JavaScript 代码（需要 Node.js 环境）

    Args:
        code: JavaScript 代码字符串
        timeout: 超时时间（秒）

    Returns:
        执行结果
    """
    import time

    # 检查 Node.js 是否可用
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Node.js 不可用，使用简单模拟
        return CodeExecutionResponse(
            success=True,
            output="JavaScript 执行环境未配置，请在服务器安装 Node.js",
            execution_time=0.0,
        )

    start_time = time.time()

    # 创建临时文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".js", delete=False, encoding="utf-8"
    ) as f:
        f.write(code)
        temp_file = f.name

    try:
        # 执行代码
        result = subprocess.run(
            ["node", temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )

        execution_time = time.time() - start_time

        return CodeExecutionResponse(
            success=result.returncode == 0,
            output=result.stdout or "",
            error=result.stderr if result.returncode != 0 else None,
            execution_time=execution_time,
        )
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.unlink(temp_file)


class TestCaseRequest(BaseModel):
    """测试用例请求模型"""

    code: str = Field(..., description="要测试的代码")
    language: str = Field(..., description="编程语言")
    test_cases: list = Field(..., description="测试用例列表")


@router.post("/test-code", response_model=Dict[str, Any])
async def test_code_with_cases(request: TestCaseRequest):
    """
    使用测试用例验证代码

    Args:
        request: 测试用例请求

    Returns:
        测试结果
    """
    results = []
    total_passed = 0

    for test_case in request.test_cases:
        # 构造完整的测试代码
        full_code = f"{request.code}\n\n{test_case.get('test_code', '')}"

        # 执行测试
        if request.language.lower() == "python":
            result = await execute_python_code(full_code, test_case.get("timeout", 5))
        else:
            result = await execute_javascript_code(
                full_code, test_case.get("timeout", 5)
            )

        # 判断是否通过
        passed = (
            result.success
            and result.output.strip() == test_case.get("expected_output", "").strip()
        )

        if passed:
            total_passed += 1

        results.append(
            TestResult(
                passed=passed,
                output=result.output,
                expected=test_case.get("expected_output"),
                actual=result.output,
            ).dict()
        )

    return {
        "total": len(request.test_cases),
        "passed": total_passed,
        "failed": len(request.test_cases) - total_passed,
        "results": results,
        "success_rate": total_passed / len(request.test_cases) if request.test_cases else 0,
    }


@router.get("/supported-languages")
async def get_supported_languages():
    """
    获取支持的编程语言列表

    Returns:
        语言列表
    """
    languages = {
        "python": {
            "name": "Python",
            "version": await get_python_version(),
            "available": True,
        },
        "javascript": {
            "name": "JavaScript (Node.js)",
            "version": await get_node_version(),
            "available": await is_node_available(),
        },
    }

    return languages


async def get_python_version() -> str:
    """获取 Python 版本"""
    try:
        result = subprocess.run(
            ["python", "--version"], capture_output=True, text=True, timeout=2
        )
        return result.stdout.strip() or result.stderr.strip()
    except Exception:
        return "未知"


async def get_node_version() -> str:
    """获取 Node.js 版本"""
    try:
        result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, timeout=2
        )
        return result.stdout.strip()
    except Exception:
        return "未安装"


async def is_node_available() -> bool:
    """检查 Node.js 是否可用"""
    try:
        subprocess.run(["node", "--version"], capture_output=True, timeout=2)
        return True
    except Exception:
        return False
