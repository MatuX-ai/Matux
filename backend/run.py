#!/usr/bin/env python3
"""
iMato AI Service 启动脚本
包含 Redis 和 Neo4j 自动检测与启动
"""

import logging
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

# =============================================================================
# Windows 编码设置（必须在其他导入之前）
# =============================================================================
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =============================================================================
# 配置：支持环境变量覆盖硬编码路径
# =============================================================================
def _get_redis_path() -> Path:
    """获取 Redis 路径（环境变量优先）"""
    redis_home = os.getenv("REDIS_HOME", "")
    if redis_home:
        return Path(redis_home) / "redis-server.exe"
    # Windows 默认安装位置
    if sys.platform == 'win32':
        for default_path in ["G:/Redis", "C:/Program Files/Redis", "C:/Redis"]:
            p = Path(default_path)
            if p.exists():
                return p / "redis-server.exe"
    return Path("redis-server")  # Unix 系统


def _get_redis_cli_path() -> Path:
    """获取 redis-cli 路径"""
    redis_home = os.getenv("REDIS_HOME", "")
    if redis_home:
        return Path(redis_home) / "redis-cli.exe"
    if sys.platform == 'win32':
        for default_path in ["G:/Redis", "C:/Program Files/Redis", "C:/Redis"]:
            p = Path(default_path)
            if p.exists():
                return p / "redis-cli.exe"
    return Path("redis-cli")  # Unix 系统


# =============================================================================
# Redis 检测与启动
# =============================================================================
def _check_redis_connection(cli_path: Path, timeout: int = 2) -> bool:
    """
    检查 Redis 连接（内部函数）

    Args:
        cli_path: redis-cli 路径
        timeout: 超时时间（秒）

    Returns:
        True if Redis is responding
    """
    try:
        result = subprocess.run(
            [str(cli_path), "ping"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0 and "PONG" in result.stdout
    except subprocess.TimeoutExpired:
        logger.warning(f"Redis 连接检查超时 ({timeout}s)")
        return False
    except FileNotFoundError:
        logger.error(f"redis-cli 未找到: {cli_path}")
        return False
    except Exception as e:
        logger.error(f"Redis 连接检查失败: {e}")
        return False


def check_and_start_redis() -> bool:
    """
    检查并启动 Redis 服务
    - 支持环境变量配置路径
    - 使用循环重试代替固定等待
    - 明确的日志记录
    """
    logger.info("检查 Redis 服务...")

    cli_path = _get_redis_cli_path()
    server_path = _get_redis_path()

    # 1. 检查是否已运行
    if _check_redis_connection(cli_path):
        logger.info("Redis 已在运行")
        return True

    # 2. 尝试启动 Redis
    logger.info(f"正在启动 Redis 服务器: {server_path}")

    if not server_path.exists():
        if sys.platform == 'win32':
            logger.warning(
                f"Redis 未安装: {server_path}\n"
                f"请设置 REDIS_HOME 环境变量或安装 Redis\n"
                f"下载: https://github.com/tporadowski/redis/releases"
            )
        else:
            logger.warning("Redis 未安装，将使用降级模式")
        return False

    try:
        # 后台启动 Redis
        if sys.platform == 'win32':
            subprocess.Popen(
                [str(server_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS
            )
        else:
            subprocess.Popen(
                [str(server_path), "--daemonize", "yes"],
                start_new_session=True
            )
    except PermissionError:
        logger.error(f"权限不足，无法启动 Redis: {server_path}")
        return False
    except Exception as e:
        logger.error(f"Redis 启动失败: {e}")
        return False

    # 3. 循环重试验证启动成功
    max_retries = 10
    retry_interval = 1.0  # 秒

    for attempt in range(1, max_retries + 1):
        time.sleep(retry_interval)
        if _check_redis_connection(cli_path):
            logger.info(f"Redis 启动成功 (尝试 {attempt}/{max_retries})")
            return True
        logger.debug(f"Redis 启动中... ({attempt}/{max_retries})")

    logger.error(f"Redis 启动验证失败，已重试 {max_retries} 次")
    return False


# =============================================================================
# Neo4j 检测
# =============================================================================
def check_neo4j_status() -> bool:
    """
    检查 Neo4j 服务状态
    - 跨平台检测
    - 明确的日志输出
    """
    logger.info("检查 Neo4j 服务...")

    # Neo4j 连接配置
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")

    if sys.platform == 'win32':
        # Windows: 检测进程
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-Process | Where-Object {$_.ProcessName -like '*neo4j*'}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                logger.info("Neo4j Desktop 正在运行")
                logger.info(f"请确保已在 Neo4j Desktop 中启动数据库实例")
                logger.info(f"连接地址：{neo4j_uri}")
                return True
        except subprocess.TimeoutExpired:
            logger.warning("Neo4j 进程检测超时")
        except FileNotFoundError:
            logger.warning("PowerShell 未找到")
        except Exception as e:
            logger.warning(f"Neo4j 进程检测失败: {e}")
    else:
        # Unix: 检测端口
        try:
            result = subprocess.run(
                ["nc", "-z", "localhost", "7687"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"Neo4j 正在运行: {neo4j_uri}")
                return True
        except FileNotFoundError:
            pass  # nc 不可用
        except Exception as e:
            logger.warning(f"Neo4j 端口检测失败: {e}")

    # 检查安装位置
    neo4j_paths = [
        Path("C:/Program Files/Neo4j"),
        Path("C:/Program Files/Neo4j Desktop 2"),
        Path("G:/Neo4j"),
        Path("/usr/local/share/neo4j"),
        Path("/opt/neo4j"),
        Path(os.path.expanduser("~/AppData/Local/Neo4j")),
    ]

    # 添加环境变量中的路径
    neo4j_home = os.getenv("NEO4J_HOME", "")
    if neo4j_home:
        neo4j_paths.insert(0, Path(neo4j_home))

    for path in neo4j_paths:
        if path.exists():
            logger.info(f"Neo4j 已安装在: {path}")
            logger.warning("请手动启动 Neo4j Desktop 并创建数据库实例")
            if sys.platform != 'win32':
                logger.info(
                    "或使用 Docker: docker run -d -p 7474:7474 -p 7687:7687 neo4j:latest")
            return True

    logger.warning(
        f"Neo4j 未安装，将使用降级模式\n"
        f"如需安装 Neo4j，请访问：https://neo4j.com/download/"
    )
    return False

# =============================================================================
# 暴露给模块导入的函数（安全）
# =============================================================================


def get_redis_status():
    """获取 Redis 状态（不自动启动）"""
    cli_path = _get_redis_cli_path()
    return _check_redis_connection(cli_path)


def get_neo4j_status():
    """获取 Neo4j 状态（不自动启动）"""
    # 简化检测
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-Process | Where-Object {$_.ProcessName -like '*neo4j*'}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


# =============================================================================
# 主入口
# =============================================================================
def main():
    """主启动函数"""
    print("=" * 60)
    print("iMato AI Service 启动程序")
    print("=" * 60)
    print()

    # 检查并启动依赖服务
    redis_available = check_and_start_redis()
    neo4j_available = check_neo4j_status()

    print()
    print("-" * 60)
    print("服务状态:")
    print(f"  Redis: {'已就绪' if redis_available else '降级模式 (无缓存)'}")
    print(f"  Neo4j: {'已安装 (需手动启动)' if neo4j_available else '降级模式 (无图数据库)'}")
    print("-" * 60)
    print()

    # 启动主应用
    import uvicorn

    # 延迟导入 settings，避免 Redis 未就绪时过早加载配置
    from config.settings import settings

    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Listening on {settings.HOST}:{settings.PORT}")
    print(f"Debug mode: {settings.DEBUG}")
    print("-" * 50)

    # Workers 配置：Windows 不支持多进程，DEBUG 模式单进程
    if settings.DEBUG or settings.FORCE_SINGLE_WORKER or sys.platform == "win32":
        workers = 1
    else:
        cpu_count = os.cpu_count() or 1
        max_workers = settings.MAX_WORKERS
        workers = min(cpu_count * 2, max_workers)
        print(f"Workers: CPU={cpu_count}, 上限={max_workers}, 实际={workers}")

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=workers,
    )


if __name__ == "__main__":
    main()
