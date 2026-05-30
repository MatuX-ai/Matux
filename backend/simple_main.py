"""
简化版主应用入口 - 用于测试数据库注册表系统
避开复杂的路由依赖问题
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import Settings
from middleware import (
    APMMiddleware, 
    init_apm, 
    PermissionMiddleware,
    LicenseMiddleware, 
    license_exception_handler,
    CircuitBreakerConfig, 
    CircuitBreakerMiddleware
)
from database import init_registry_manager
from utils.database import create_db_and_tables
from utils.logger import setup_logger

# 加载环境变量
settings = Settings()

# 创建FastAPI应用实例
app = FastAPI(
    title=f"{settings.APP_NAME} - 注册表测试版",
    version=settings.APP_VERSION,
    description="简化版应用，专门用于测试数据库模块注册表系统",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS中间件 - 处理字符串或列表格式
if isinstance(settings.ALLOWED_ORIGINS, str):
    allow_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]
else:
    allow_origins = settings.ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置基础中间件
app.add_middleware(APMMiddleware, service_name=settings.APP_NAME)
app.add_middleware(LicenseMiddleware)
app.add_middleware(PermissionMiddleware)

# 配置熔断器中间件（如果可用且启用）
if getattr(settings, 'CIRCUIT_BREAKER_ENABLED', False):
    circuit_config = CircuitBreakerConfig(
        failure_threshold=getattr(settings, "CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5),
        timeout=getattr(settings, "CIRCUIT_BREAKER_TIMEOUT", 60),
        half_open_attempts=getattr(settings, "CIRCUIT_BREAKER_HALF_OPEN_ATTEMPTS", 3),
    )
    app.add_middleware(CircuitBreakerMiddleware, config=circuit_config)

# 配置日志
logger = setup_logger(settings.LOG_LEVEL, settings.LOG_FILE)
logger.info("启动简化版应用以测试数据库注册表系统")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} (Registry Test Mode)")
    
    # 初始化APM监控
    try:
        init_apm()
        logger.info("[OK] APM监控初始化完成")
    except Exception as e:
        logger.warning(f"[WARN] APM监控初始化失败: {str(e)}")
    
    # 创建数据库表
    try:
        await create_db_and_tables()
        logger.info("[OK] 数据库表创建完成")
    except Exception as e:
        logger.error(f"[ERROR] 数据库表创建失败: {str(e)}")
    
    # 初始化数据库模块注册表
    try:
        logger.info("正在初始化数据库模块注册表...")
        registry_manager = init_registry_manager()
        await registry_manager.initialize_registry(auto_discover=True)
        
        # 输出注册表统计信息
        stats = registry_manager.get_registry_config()
        logger.info(f"[SUCCESS] 数据库模块注册表初始化完成: {stats}")
        
        # 执行健康检查
        health = await registry_manager.health_check()
        logger.info(f"[HEALTH] 注册表健康检查: {health['registry_status']}")
        
        if health['issues']:
            for issue in health['issues']:
                logger.warning(f"[WARN] 注册表警告: {issue}")
        else:
            logger.info("[OK] 注册表健康检查通过，无发现问题")
        
    except Exception as e:
        logger.error(f"[ERROR] 数据库模块注册表初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info(f"Shutting down {settings.APP_NAME}")
    
    # 清理注册表资源
    try:
        from database import get_registry_manager
        registry_manager = get_registry_manager()
        await registry_manager.registry.cleanup_all()
        logger.info("[OK] 数据库模块注册表资源已清理")
    except Exception as e:
        logger.error(f"[ERROR] 清理注册表资源失败: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"全局异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )


# 添加许可证异常处理器
try:
    app.add_exception_handler(401, license_exception_handler)
    app.add_exception_handler(403, license_exception_handler)
except:
    logger.warning("[WARN] 许可证异常处理器注册失败")


@app.get("/")
async def root():
    """根路径健康检查"""
    registry_info = {}
    try:
        from database import get_registry_manager
        registry_manager = get_registry_manager()
        registry_info = registry_manager.get_registry_config()
    except Exception as e:
        registry_info = {"error": str(e)}
    
    return {
        "message": f"Welcome to {settings.APP_NAME} - Registry Test Mode",
        "version": settings.APP_VERSION,
        "status": "healthy",
        "mode": "registry_test",
        "database_registry": registry_info,
        "features": [
            "数据库模块注册表",
            "自动模型发现", 
            "模块生命周期管理",
            "健康检查监控"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    health_info = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "mode": "registry_test"
    }
    
    # 添加注册表健康信息
    try:
        from database import get_registry_manager
        registry_manager = get_registry_manager()
        registry_health = await registry_manager.health_check()
        health_info["database_registry"] = registry_health
        
        if registry_health['registry_status'] != 'healthy':
            health_info['status'] = registry_health['registry_status']
            
    except Exception as e:
        health_info["database_registry_error"] = str(e)
        health_info["status"] = "degraded"
    
    return health_info


@app.get("/registry/stats")
async def registry_stats():
    """注册表统计信息端点"""
    try:
        from database import get_registry_manager
        registry_manager = get_registry_manager()
        stats = registry_manager.get_registry_config()
        categorized = registry_manager.list_modules_by_category()
        
        return {
            "registry_stats": stats,
            "modules_by_category": categorized,
            "total_categories": len(categorized),
            "mode": "registry_test"
        }
    except Exception as e:
        return {"error": str(e), "mode": "registry_test"}


@app.get("/registry/modules")
async def list_registry_modules(category: str = None):
    """列出注册表中的模块"""
    try:
        from database import get_database_registry
        registry = get_database_registry()
        
        if category:
            modules = registry.get_modules_by_category(category)
        else:
            modules = registry.list_modules()
        
        return {
            "modules": [
                {
                    "name": m.name,
                    "table_name": m.table_name,
                    "category": m.category,
                    "version": m.version,
                    "is_active": m.is_active,
                    "description": m.description
                }
                for m in modules
            ],
            "filter_category": category,
            "mode": "registry_test"
        }
    except Exception as e:
        return {"error": str(e), "mode": "registry_test"}


@app.get("/test/success")
async def success_endpoint():
    """成功测试端点"""
    return {
        "message": "success",
        "mode": "registry_test",
        "timestamp": "ok"
    }


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus指标端点 - 支持fallback模式"""
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        from starlette.responses import Response
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            "# Prometheus metrics not available\n# Database registry system active\n",
            status_code=200
        )


class ServerState:
    def __init__(self):
        self.should_exit = False


async def shutdown_handler(signum, frame, server_state):
    """优雅关闭处理器"""
    logger.info(f"收到信号 {signum}，开始优雅关闭...")
    server_state.should_exit = True


if __name__ == "__main__":
    import uvicorn
    
    # 设置信号处理
    server_state = ServerState()
    
    def signal_handler(signum, frame):
        asyncio.create_task(shutdown_handler(signum, frame, server_state))
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("="*60)
    logger.info(f"启动 {settings.APP_NAME} 注册表测试模式")
    logger.info(f"服务地址: http://{settings.HOST}:{settings.PORT}")
    logger.info(f"API文档: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"健康检查: http://{settings.HOST}:{settings.PORT}/health")
    logger.info(f"注册表统计: http://{settings.HOST}:{settings.PORT}/registry/stats")
    logger.info("="*60)
    
    try:
        uvicorn.run(
            "simple_main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=False,  # 测试模式下禁用reload
            log_level="info",  # 使用固定日志级别避免配置问题
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("用户中断，正在关闭服务...")
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        sys.exit(1)
    finally:
        logger.info("服务已关闭")