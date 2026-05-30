"""
AI-Edu 代码沙箱服务 - Docker 容器隔离实现
提供安全的代码执行环境
"""

from dataclasses import dataclass
from datetime import datetime
import io
import json
import logging
import tarfile
import time
from typing import Any, Dict, Optional

import docker

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """代码执行结果"""

    success: bool
    output: str
    error: str
    execution_time_ms: float
    memory_used_kb: int
    exit_code: int
    container_id: Optional[str]


class CodeSandboxService:
    """代码沙箱服务类"""

    def __init__(self):
        """初始化 Docker 客户端"""
        try:
            self.client = docker.from_env()
            logger.info("✅ Docker 客户端初始化成功")
        except Exception as e:
            logger.error(f"❌ Docker 客户端初始化失败：{e}")
            raise

        # 沙箱配置
        self.sandbox_config = {
            "image": "ai-edu-sandbox:latest",
            "cpu_quota": 50000,  # CPU 配额 (微秒), 50% = 50000/100000
            "cpu_period": 100000,
            "mem_limit": "128m",  # 内存限制 128MB
            "network_mode": "none",  # 禁用网络
            "read_only": True,  # 只读文件系统
            "tmpfs": {"/tmp": "rw,noexec,nosuid,size=32m"},  # 临时目录 32MB
            "ulimits": [
                docker.types.Ulimit(name="cpu", soft=5, hard=5),  # CPU 时间 5 秒
                docker.types.Ulimit(name="nofile", soft=64, hard=64),  # 文件描述符 64
                docker.types.Ulimit(name="nproc", soft=50, hard=50),  # 进程数 50
            ],
            "security_opt": [
                "no-new-privileges:true",  # 禁止提权
                "apparmor:docker-default",  # AppArmor 配置文件
            ],
            "cap_drop": [
                "ALL",  # 删除所有 Linux capabilities
            ],
            "user": "sandbox",  # 使用非 root 用户
            "working_dir": "/sandbox",
            "environment": {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONUNBUFFERED": "1",
                "PYTHONFAULTHANDLER": "1",
            },
        }

        # 容器池（可选优化）
        self.container_pool = []
        self.pool_size = 3

    def build_sandbox_image(self) -> bool:
        """构建沙箱基础镜像"""
        try:
            logger.info("🔨 开始构建沙箱镜像...")

            # 从 Dockerfile 构建
            image, logs = self.client.images.build(
                path="./backend/docker/sandbox-base",
                tag="ai-edu-sandbox:latest",
                rm=True,
                forcerm=True,
            )

            # 打印构建日志
            for log in logs:
                if "stream" in log:
                    logger.debug(log["stream"].strip())

            logger.info(f"✅ 镜像构建成功：{image.short_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 镜像构建失败：{e}")
            return False

    def execute_code(
        self,
        code: str,
        language: str = "python",
        timeout_seconds: int = 5,
        stdin_input: Optional[str] = None,
    ) -> ExecutionResult:
        """
        在沙箱中执行代码

        Args:
            code: 要执行的代码
            language: 编程语言 (目前仅支持 python)
            timeout_seconds: 超时时间（秒）
            stdin_input: 标准输入内容

        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()
        container_id = None

        try:
            # 验证代码安全性
            if not self._validate_code(code):
                return ExecutionResult(
                    success=False,
                    output="",
                    error="代码包含不安全的内容",
                    execution_time_ms=0,
                    memory_used_kb=0,
                    exit_code=-1,
                    container_id=None,
                )

            # 创建并运行容器
            logger.info(f"🚀 创建沙箱容器执行代码 (timeout={timeout_seconds}s)")

            container = self.client.containers.run(
                image=self.sandbox_config["image"],
                command=self._build_command(code, language),
                detach=True,
                **self._get_runtime_config(timeout_seconds),
            )
            container_id = container.short_id
            logger.debug(f"容器已创建：{container_id}")

            # 等待执行完成
            try:
                result = container.wait(timeout=timeout_seconds + 2)
                exit_code = result.get("StatusCode", 0)

            except Exception as e:
                # 超时或其他错误，强制停止容器
                logger.warning(f"⚠️ 执行异常，终止容器：{e}")
                container.stop(timeout=1)
                exit_code = -1

            # 获取输出
            output_log = container.logs(stdout=True, stderr=False).decode(
                "utf-8", errors="replace"
            )
            error_log = container.logs(stdout=False, stderr=True).decode(
                "utf-8", errors="replace"
            )

            # 获取资源使用情况
            stats = self._get_container_stats(container)

            # 清理容器
            container.remove(force=True)
            logger.debug(f"容器已清理：{container_id}")

            execution_time_ms = (time.time() - start_time) * 1000

            return ExecutionResult(
                success=(exit_code == 0),
                output=output_log,
                error=error_log if exit_code != 0 else "",
                execution_time_ms=execution_time_ms,
                memory_used_kb=stats["memory_kb"],
                exit_code=exit_code,
                container_id=container_id,
            )

        except Exception as e:
            logger.error(f"❌ 代码执行失败：{e}")

            # 尝试清理残留容器
            if container_id:
                try:
                    container = self.client.containers.get(container_id)
                    container.remove(force=True)
                except Exception:
                    pass

            return ExecutionResult(
                success=False,
                output="",
                error=f"执行失败：{str(e)}",
                execution_time_ms=(time.time() - start_time) * 1000,
                memory_used_kb=0,
                exit_code=-1,
                container_id=container_id,
            )

    def _validate_code(self, code: str) -> bool:
        """
        验证代码安全性（基础实现）

        TODO: 实现更完善的 AST 分析
        """
        dangerous_patterns = [
            "__import__",
            "eval(",
            "exec(",
            "compile(",
            "open(",
            "os.system",
            "os.popen",
            "subprocess",
            "socket.",
            "requests.",
            "urllib.",
        ]

        for pattern in dangerous_patterns:
            if pattern in code:
                logger.warning(f"检测到危险模式：{pattern}")
                return False

        return True

    def _build_command(self, code: str, language: str) -> list:
        """构建容器执行命令"""
        if language == "python":
            # 将代码写入临时文件并执行
            return ["python", "-c", code]
        else:
            raise ValueError(f"不支持的编程语言：{language}")

    def _get_runtime_config(self, timeout_seconds: int) -> dict:
        """获取运行时配置"""
        config = self.sandbox_config.copy()

        # 更新超时配置
        config["ulimits"] = [
            docker.types.Ulimit(
                name="cpu", soft=timeout_seconds, hard=timeout_seconds + 2
            ),
            docker.types.Ulimit(name="nofile", soft=64, hard=64),
            docker.types.Ulimit(name="nproc", soft=50, hard=50),
        ]

        return config

    def _get_container_stats(self, container) -> dict:
        """获取容器资源使用统计"""
        try:
            stats = container.stats(stream=False)

            # 内存使用 (KB)
            memory_usage = stats.get("memory_stats", {}).get("usage", 0)
            memory_kb = int(memory_usage / 1024) if memory_usage else 0

            return {
                "memory_kb": memory_kb,
                "cpu_percent": stats.get("cpu_stats", {}).get("cpu_percent", 0),
            }
        except Exception as e:
            logger.debug(f"获取容器统计失败：{e}")
            return {"memory_kb": 0, "cpu_percent": 0}

    def health_check(self) -> dict:
        """健康检查"""
        try:
            # 检查 Docker 连接
            self.client.ping()

            # 检查镜像是否存在
            images = self.client.images.list()
            sandbox_image_exists = any("ai-edu-sandbox" in img.tags for img in images)

            return {
                "status": "healthy",
                "docker_connected": True,
                "sandbox_image_available": sandbox_image_exists,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def cleanup_all_containers(self):
        """清理所有沙箱容器"""
        try:
            containers = self.client.containers.list(
                filters={"label": "ai-edu=sandbox"}, all=True
            )

            for container in containers:
                try:
                    container.remove(force=True)
                    logger.debug(f"清理容器：{container.short_id}")
                except Exception as e:
                    logger.debug(f"清理容器失败：{e}")

            logger.info(f"✅ 已清理 {len(containers)} 个容器")

        except Exception as e:
            logger.error(f"清理容器失败：{e}")


# 全局单例
_sandbox_service: Optional[CodeSandboxService] = None


def get_sandbox_service() -> CodeSandboxService:
    """获取沙箱服务单例"""
    global _sandbox_service
    if _sandbox_service is None:
        _sandbox_service = CodeSandboxService()
    return _sandbox_service


async def init_sandbox_environment():
    """初始化沙箱环境"""
    service = get_sandbox_service()

    # 检查镜像是否存在
    health = service.health_check()

    if not health.get("sandbox_image_available"):
        logger.info("沙箱镜像不存在，开始构建...")
        success = service.build_sandbox_image()

        if not success:
            raise RuntimeError("沙箱镜像构建失败")

    logger.info("✅ 沙箱环境初始化完成")
    return service
