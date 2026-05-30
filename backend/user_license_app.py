"""
用户许可证功能专用应用
简化版FastAPI应用，专注于用户许可证对接功能
"""

import os

# 添加项目根目录到Python路径
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from middleware.permission_middleware import PermissionMiddleware
from routes.auth_routes import router as auth_router
from routes.user_license_routes import router as user_license_router
from utils.database import create_db_and_tables
from utils.logger import setup_logger

# 加载环境变量
settings = Settings()

# 创建FastAPI应用实例
app = FastAPI(
    title="用户许可证对接服务",
    version="1.0.0",
    description="提供用户与许可证关联管理的API服务",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置权限验证中间件
app.add_middleware(PermissionMiddleware)

# 配置日志
logger = setup_logger("INFO", "user_license_app.log")

# 包含路由
app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(user_license_router, prefix="/api/v1", tags=["用户许可证"])


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("Starting User License Integration Service v1.0.0")
    # 创建数据库表
    await create_db_and_tables()
    logger.info("Database tables created successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Shutting down User License Integration Service")


@app.get("/")
async def root():
    """根路径健康检查"""
    return {
        "message": "User License Integration Service",
        "version": "1.0.0",
        "status": "healthy",
        "features": ["用户认证", "许可证关联", "权限管理", "租户同步"],
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "User License Integration Service",
        "version": "1.0.0",
    }


@app.get("/api/info")
async def api_info():
    """API信息端点"""
    return {
        "service": "用户许可证对接服务",
        "version": "1.0.0",
        "endpoints": {
            "认证": "/api/v1/auth/*",
            "用户许可证": "/api/v1/users/*",
            "文档": "/docs",
            "健康检查": "/health",
        },
        "authentication": "JWT Token",
        "database": "SQLite (test.db)",
    }


if __name__ == "__main__":
    print("🚀 启动用户许可证对接服务...")
    print("📝 文档地址: http://localhost:8000/docs")
    print("🏥 健康检查: http://localhost:8000/health")
    print("ℹ️  API信息: http://localhost:8000/api/info")
    print("🔐 默认测试账户:")
    print("   - 管理员: admin / password123")
    print("   - 企业管理员: orgadmin / password123")
    print("   - 普通用户: user1 / password123")

    uvicorn.run(
        "user_license_app:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
