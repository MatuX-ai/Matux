#!/usr/bin/env python3
"""
iMato AI Service 启动脚本
包含 Redis 和 Neo4j 自动检测与启动
"""

import subprocess
import sys
import os
import time
from pathlib import Path

# Windows 编码设置
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 检查并启动 Redis
def check_and_start_redis():
    """检查并启动 Redis 服务"""
    print("🔍 检查 Redis 服务...")

    # 检查是否可以通过 redis-cli 连接
    try:
        result = subprocess.run(
            ["G:\\Redis\\redis-cli.exe", "ping"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0 and "PONG" in result.stdout:
            print("✅ Redis 已在运行")
            return True
    except Exception:
        pass

    # 尝试启动 Redis
    print("⚙️  正在启动 Redis 服务器...")
    redis_path = Path("G:/Redis/redis-server.exe")

    if redis_path.exists():
        try:
            # 后台启动 Redis
            subprocess.Popen(
                [str(redis_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.DETACHED_PROCESS
            )
            time.sleep(2)  # 等待启动

            # 验证是否启动成功
            result = subprocess.run(
                ["G:\\Redis\\redis-cli.exe", "ping"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if "PONG" in result.stdout:
                print("✅ Redis 启动成功")
                return True
        except Exception as e:
            print(f"⚠️  Redis 启动失败：{e}")
    else:
        print("⚠️  Redis 未安装，将使用降级模式")

    return False

# 检查 Neo4j 状态
def check_neo4j_status():
    """检查 Neo4j 服务状态"""
    print("🔍 检查 Neo4j 服务...")

    # 检查 Neo4j Desktop 是否正在运行
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Process | Where-Object {$_.ProcessName -like '*neo4j*'}"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.stdout.strip():
            print("✅ Neo4j Desktop 正在运行")
            print("   请确保已在 Neo4j Desktop 中启动数据库实例")
            print("   连接地址：neo4j://127.0.0.1:7687")
            return True
    except Exception:
        pass

    # 检查其他安装方式
    neo4j_paths = [
        "C:/Program Files/Neo4j",
        "C:/Program Files/Neo4j Desktop 2",
        "G:/Neo4j",
        os.path.expanduser("~/AppData/Local/Neo4j"),
    ]

    for path in neo4j_paths:
        if Path(path).exists():
            print(f"ℹ️   Neo4j 已安装在：{path}")
            print("⚠️   请手动启动 Neo4j Desktop 并创建数据库实例")
            print("   或使用 Docker: docker run -d -p 7474:7474 -p 7687:7687 neo4j:latest")
            return True

    print("⚠️   Neo4j 未安装，将使用降级模式")
    print("💡   如需安装 Neo4j，请访问：https://neo4j.com/download/")
    return False

if __name__ == "__main__":
    from config.settings import settings

    print("=" * 60)
    print("🚀 iMato AI Service 启动程序")
    print("=" * 60)
    print()

    # 检查并启动依赖服务
    redis_available = check_and_start_redis()
    neo4j_available = check_neo4j_status()

    print()
    print("-" * 60)
    print("📊 服务状态:")
    print(f"  • Redis: {'✅ 已就绪' if redis_available else '⚠️ 降级模式'}")
    print(f"  • Neo4j: {'ℹ️  已安装 (需手动启动)' if neo4j_available else '⚠️ 降级模式'}")
    print("-" * 60)
    print()

    # 启动主应用
    import uvicorn

    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📡 Listening on {settings.HOST}:{settings.PORT}")
    print(f"🔧 Debug mode: {settings.DEBUG}")
    print("-" * 50)

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
