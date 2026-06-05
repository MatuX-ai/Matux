#!/usr/bin/env python3
"""
最小化启动脚本 - 用于快速测试
"""
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting minimal FastAPI server...")
    print("📡 Listening on http://localhost:8000")
    print("-" * 50)

    # 直接运行，不加载配置
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
