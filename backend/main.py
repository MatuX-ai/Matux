"""
MatuX STEM 学习平台 API 服务主入口
提供AI代码生成、个性化学习、STEM实验等功能的FastAPI服务

注意：课件管理模块已解耦至 OpenMTSciEd 项目，机构管理模块已解耦至 OpenMTEduInst 项目。
本项目保留的路由存根仅用于兼容性，新功能请在对应项目中开发。
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response  # PlainTextResponse 保留备用
from starlette.exceptions import HTTPException as StarletteHTTPException

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
from database import (
    init_registry_manager,
)
from utils.database import create_db_and_tables
from utils.logger import setup_logger

# 加载环境变量
settings = Settings()

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="MatuX STEM 学习平台 API 服务 - AI编程、个性化学习、STEM实验、游戏化激励",
    docs_url="/docs",
    redoc_url="/redoc",
)

# =============================================================================
# 中间件配置顺序说明（FastAPI按逆序执行，先添加的后执行）
# 1. ModuleActivationMiddleware - 模块懒加载拦截（最先添加，最后执行）
# 2. PermissionMiddleware - 权限校验（最后添加，最先执行）
# 3. CircuitBreakerMiddleware - 熔断保护
# 4. APMMiddleware - APM性能监控
# 5. CORSMiddleware - 跨域资源共享（最后添加的中间件最先执行响应）
# =============================================================================

# 配置 CORS 中间件
allowed_origins = settings.ALLOWED_ORIGINS

app.add_middleware(  # noqa: E501
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置APM监控中间件
app.add_middleware(  # noqa: E501
    APMMiddleware, service_name=settings.APP_NAME
)

# 配置许可证验证中间件（通过环境变量控制，DEBUG模式下可禁用）
if getattr(settings, 'ENABLE_LICENSE_CHECK', True) and not settings.DEBUG:
    app.add_middleware(LicenseMiddleware)

# 配置熔断器中间件
if settings.CIRCUIT_BREAKER_ENABLED:
    circuit_config = CircuitBreakerConfig(
        failure_threshold=int(getattr(settings, "CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5)),
        success_threshold=2,  # 半开→关闭所需成功次数
        timeout=float(getattr(settings, "CIRCUIT_BREAKER_TIMEOUT", 60)),
        half_open_max_calls=int(getattr(settings, "CIRCUIT_BREAKER_HALF_OPEN_ATTEMPTS", 3)),
    )
    app.add_middleware(
        CircuitBreakerMiddleware, config=circuit_config
    )

# 配置权限验证中间件
app.add_middleware(PermissionMiddleware)

# 配置模块激活中间件（懒加载架构）
if settings.ENABLE_LAZY_LOADING:
    from core.activation_middleware import ModuleActivationMiddleware
    app.add_middleware(ModuleActivationMiddleware)

# 配置日志
logger = setup_logger(settings.LOG_LEVEL, settings.LOG_FILE)

# 路由注册
# 懒加载模式：路由由 LazyLoader 引擎自动管理
# 传统模式：一次性注册所有路由
if not settings.ENABLE_LAZY_LOADING:
    from legacy_routes import register_all_routes
    register_all_routes(app)
else:
    # 仅注册系统管理 API（始终可用）
    from routes.system_status_routes import router as system_status_router
    app.include_router(system_status_router)
    logger.info("📦 懒加载模式：路由由 LazyLoader 引擎管理")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    import time
    _start_time = time.time()

    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(
        f"Lazy Loading: {'ON' if settings.ENABLE_LAZY_LOADING else 'OFF'}"
    )

    # 导入所有模型以确保它们被注册到 Base.metadata
    # 按依赖顺序导入：先导入基础模型，再导入依赖模型
    # [已废弃] models/license.py 中的 Organization/License 是 Pydantic 模型，不是 SQLAlchemy 模型
    # 在正式迁移完成前，移除这里的 ORM 注册导入
    # from models.license import Organization, License  # noqa: F401
    from models.sponsorship import Sponsorship  # noqa: F401
    from models.user import User  # noqa: F401
    from models.ar_vr_content import ARVRContent  # noqa: F401
    from models.content_store import ContentItem  # noqa: F401
    from models.course_version import CourseVersion  # noqa: F401
    from models.dynamic_course import GeneratedCourse  # noqa: F401
    from models.hardware_certification import (  # noqa: F401
        HardwareCertificationDB,
    )
    from models.hardware_module import HardwareModule  # noqa: F401
    from models.learning_source import LearningSource  # noqa: F401
    from models.payment import Payment  # noqa: F401
    from models.permission import Permission  # noqa: F401
    from models.subscription import SubscriptionPlan  # noqa: F401
    from models.subscription_fsm import SubscriptionFSM  # noqa: F401
    from models.unified_learning_record import (  # noqa: F401
        UnifiedLearningRecord,
    )
    from models.user_license import UserLicense  # noqa: F401
    from models.user_organization import (  # noqa: F401
        UserOrganization,
    )
    from models.ai_request import AIRequest  # noqa: F401
    from models.unified_material import UnifiedMaterial  # noqa: F401
    from models.user_guardian import UserGuardian  # noqa: F401
    from models.oauth_account import OAuthAccount  # noqa: F401
    from models.exam import Exam, Question, ExamAttempt, CheatEvent  # noqa: F401
    from modules.learning.models import (  # noqa: F401
        StudentCourseAggregation,
    )

    # 初始化 APM 监控
    init_apm()

    # === 统一数据库初始化 ===
    async def _init_database():
        """统一数据库初始化函数（懒加载和非懒加载模式共用）"""
        await create_db_and_tables()
        logger.info("✅ 数据库表创建成功")
    
    # === 懒加载架构：初始化核心模块 ===
    if settings.ENABLE_LAZY_LOADING:
        await _init_lazy_architecture(app, _start_time)
    else:
        # 旧模式：全量创建所有表
        await _init_database()

    # 初始化测试数据（仅开发环境且未启用懒加载）
    if settings.DEBUG and not settings.ENABLE_LAZY_LOADING:
        try:
            from utils.init_test_data import initialize_test_data
            await initialize_test_data()
        except Exception as e:
            logger.exception("测试数据初始化失败：%s", str(e))
            raise

    # 初始化数据库模块注册表
    try:
        logger.info("正在初始化数据库模块注册表...")
        registry_manager = init_registry_manager()
        await registry_manager.initialize_registry(auto_discover=True)

        # 输出注册表统计信息
        stats = registry_manager.get_registry_config()
        logger.info(
            f"数据库模块注册表初始化完成: {stats}"
        )

        # 执行健康检查
        health = await registry_manager.health_check()
        logger.info(f"注册表健康检查: {health['registry_status']}")

        if health['issues']:
            for issue in health['issues']:
                logger.warning(f"注册表警告: {issue}")

    except Exception as e:
        logger.exception("数据库模块注册表初始化失败: %s", str(e))
        raise


async def _init_lazy_architecture(app_instance, start_time: float):
    """
    初始化懒加载架构

    流程：
    1. 初始化核心引擎组件
    2. 注册所有模块规格
    3. 创建核心数据库表（Tier 0）
    4. 激活 Tier 0 核心模块路由
    5. 注册激活中间件
    6. 后台预加载 Tier 1 模块
    """
    import asyncio
    import time
    from core import (
        init_lazy_loader,
        init_lazy_table_manager,
        init_service_manager,
        ModuleSpec,
        ModuleTier,
    )
    from core.module_registry import get_all_module_specs
    from core.lazy_tables import get_lazy_table_manager

    logger.info("\n" + "=" * 60)
    logger.info("🚀 启动懒加载架构")
    logger.info("=" * 60)

    # Step 1: 初始化核心组件
    loader = init_lazy_loader(app_instance)
    table_manager = init_lazy_table_manager()
    service_manager = init_service_manager()

    # 注册外部服务降级方案
    service_manager.register_many({
        "redis": "in_memory",
        "neo4j": "disabled",
        "openai": "local_template",
        "rabbitmq": "sync_mode",
        "smtp": "log_only",
        "hardware_auth": "offline_sim",
        "docker": "read_only",
        "vircadia": "2d_simulation",
        "openhydra": "disabled",
        "hyperledger": "cache_mode",
    })

    logger.info("✅ 核心组件初始化完成")

    # Step 2: 注册所有模块（支持插件机制）
    from core.module_registry import get_all_module_specs_with_plugins, discover_plugins
    
    # 自动发现插件
    discover_plugins(base_path="routes")
    
    # 获取所有模块规格（包含插件）
    all_specs = get_all_module_specs_with_plugins()
    logger.info(f"✅ 模块注册完成: {len(all_specs)} 个模块 (含插件)")
    
    for spec_data in all_specs:
        spec = ModuleSpec(
            name=spec_data["name"],
            tier=ModuleTier(spec_data["tier"]),
            router_factory=spec_data["router_factory"],
            prefix=spec_data.get("prefix", ""),
            tags=spec_data.get("tags", []),
            dependencies=spec_data.get("dependencies", []),
            required_services=spec_data.get("required_services", []),
            fallback_services=spec_data.get("fallback_services", {}),
            model_classes=spec_data.get("model_classes", []),
        )
        try:
            loader.register(spec)
        except ValueError:
            pass  # 重复注册跳过

    # 注册表映射
    for spec_data in all_specs:
        if spec_data.get("model_classes"):
            table_manager.register_module_tables(
                spec_data["name"],
                spec_data["model_classes"],
            )

    # Step 3: 创建核心数据库表
    await create_db_and_tables()
    logger.info("✅ 数据库表创建成功")

    # Step 4: 激活 Tier 0 核心模块
    core_results = await loader.activate_tier(ModuleTier.TIER_0_CORE)
    core_elapsed = (time.time() - start_time) * 1000
    logger.info(
        f"✅ Tier 0 核心模块激活完成: "
        f"{sum(1 for v in core_results.values() if v)}/{len(core_results)} "
        f"成功 (总耗时: {core_elapsed:.0f}ms)"
    )

    # Step 5: 后台预加载 Tier 1
    async def _preload_tier1():
        try:
            await asyncio.sleep(settings.PRELOAD_DELAY_SECONDS)
            logger.info("📋 开始后台预加载 Tier 1 模块...")
            t1_results = await loader.activate_tier(ModuleTier.TIER_1_HIGH)
            success = sum(1 for v in t1_results.values() if v)
            logger.info(
                f"✅ Tier 1 预加载完成: "
                f"{success}/{len(t1_results)} 成功"
            )
        except asyncio.CancelledError:
            logger.info("Tier 1 预加载任务被取消")
            raise
        except Exception as e:
            logger.exception("Tier 1 预加载失败: %s", str(e))
        
    # 保存到模块级别变量（通过闭包访问）
    app.state._preload_task = asyncio.create_task(_preload_tier1())
        
    # 将任务存储在懒加载器中以便shutdown时访问
    if hasattr(loader, 'set_background_task'):
        loader.set_background_task(app.state._preload_task)
        
    elapsed = (time.time() - start_time) * 1000
    logger.info(
        f"\n🎯 懒加载架构启动完成 (Tier 0 就绪: {elapsed:.0f}ms)"
    )
    logger.info("=" * 60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件 - 包含超时保护"""
    logger.info(f"Shutting down {settings.APP_NAME}")
    
    # 取消后台预加载任务
    preload_task = getattr(app.state, '_preload_task', None)
    if preload_task and not preload_task.done():
        preload_task.cancel()
        try:
            await asyncio.wait_for(preload_task, timeout=5.0)
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            logger.warning("预加载任务取消超时")

    # 清理注册表资源（带超时保护）
    try:
        from database import get_registry_manager
        registry_manager = get_registry_manager()
        await asyncio.wait_for(
            registry_manager.registry.cleanup_all(),
            timeout=10.0
        )
        logger.info("数据库模块注册表资源已清理")
    except asyncio.TimeoutError:
        logger.warning("注册表清理超时，强制关闭")
    except Exception as e:
        logger.exception("清理注册表资源失败: %s", str(e))


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """请求验证异常处理器"""
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


# 添加许可证异常处理器
app.add_exception_handler(StarletteHTTPException, license_exception_handler)


@app.get("/")
async def root():
    """根路径健康检查"""
    # 构建已激活的可选功能列表
    optional_features = []
    if settings.ENABLE_AR_VR_ROUTES:
        optional_features.append("AR/VR 课程 (已启用)")
    if settings.ENABLE_AR_VR_MOCK_ROUTES:
        optional_features.append("AR/VR Mock服务 (已启用)")
    if settings.ENABLE_DIGITAL_TWIN_ROUTES:
        optional_features.append("数字孪生实验室 (已启用)")
    if settings.ENABLE_FEDERATED_ROUTES:
        optional_features.append("联邦学习 API (已启用)")
    if settings.ENABLE_MODEL_UPDATE_ROUTES:
        optional_features.append("AI 模型热更新 (已启用)")
    if settings.ENABLE_XR_GESTURE_ROUTES:
        optional_features.append(
            "XR 手势识别 (已启用，注意：与 gesture_recognition 重复)"
        )

    # 获取注册表信息（仅返回摘要，不泄露内部配置）
    registry_info = {}
    try:
        from database import get_registry_manager
        registry_manager = get_registry_manager()
        stats = registry_manager.get_registry_config()
        registry_info = {
            "initialized": stats.get("initialized", False),
            "total_modules": stats.get("stats", {}).get("total", 0),
            "active_modules": stats.get("stats", {}).get("active", 0),
        }
    except Exception as e:
        registry_info = {"error": "unavailable"}

    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "status": "healthy",
        "database_registry": registry_info,
        "core_features": [
            "AI 服务",
            "认证系统",
            "推荐系统",
            "支付系统",
            "订阅系统",
            "硬件认证",
            "课程管理",
            "课程版本控制",
            "协作编辑",
            "多媒体资源",
            "创意引擎",
            "AR 实验室",
            "模型基准测试",
            "区块链网关",
            "学习行为特征",
            "AI 教育学习进度",
            "AI 个性化教师",
            "向量知识库 (RAG)",
            "本地知识图谱",
        ],
        "decoupled_modules": {
            "课件管理": "已解耦至 OpenMTSciEd (localhost:3000/api/v1)",
            "机构管理": "已解耦至 OpenMTEduInst (独立部署)",
            "多租户配置": "已解耦至 OpenMTEduInst (保留兼容存根)",
            "许可证管理": "已解耦至 OpenMTEduInst (保留兼容存根)",
        },
        "optional_features": optional_features if optional_features else ["无"],
        "configuration_note": "可选功能通过环境变量控制，详见.env.example",
    }


@app.get("/health")
async def health_check():
    """健康检查端点 - 注册表异常时返回503"""
    health_info: dict = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

    # 添加注册表健康信息
    try:
        from database import get_registry_manager
        registry_manager = get_registry_manager()
        registry_health = await registry_manager.health_check()
        health_info["database_registry"] = registry_health

        # 如果注册表有问题，调整整体状态
        if registry_health['registry_status'] != 'healthy':
            health_info['status'] = registry_health['registry_status']

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": settings.APP_NAME,
                "error": "Registry unavailable"
            }
        )

    return health_info


@app.get("/registry/stats")
async def registry_stats():
    """注册表统计信息端点 - 仅返回公开摘要"""
    try:
        from database import get_registry_manager
        registry_manager = get_registry_manager()
        stats = registry_manager.get_registry_config()
        # 只返回公开的统计信息，隐藏内部配置细节
        return {
            "total_modules": stats.get("stats", {}).get("total", 0),
            "active_modules": stats.get("stats", {}).get("active", 0),
            "initialized": stats.get("initialized", False),
            "health_check_enabled": stats.get("health_check_enabled", False),
        }
    except Exception as e:
        return {"error": "Registry unavailable"}


@app.get("/registry/modules")
async def list_registry_modules(category: str | None = None):
    """列出注册表中的模块 - 仅返回公开信息"""
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
                    "is_active": m.is_active,
                }
                for m in modules
            ],
            "filter_category": category,
        }
    except Exception as e:
        return {"error": "Registry unavailable"}


@app.get("/test/faulty")
async def faulty_endpoint():
    """故障测试端点 - 用于熔断器测试"""
    import random
    from fastapi import HTTPException

    if random.random() < 0.7:  # 70%概率失败
        raise HTTPException(
            status_code=503,
            detail="Simulated connection failure for testing"
        )
    return {
        "message": "success",
        "timestamp": __import__(
            "datetime"
        ).datetime.utcnow().isoformat(),
    }


@app.get("/test/success")
async def success_endpoint():
    """成功测试端点"""
    return {
        "message": "success",
        "timestamp": __import__(
            "datetime"
        ).datetime.utcnow().isoformat(),
    }


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus指标端点 - 支持fallback模式"""
    try:
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
        from starlette.responses import Response

        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    except ImportError:
        # Fallback: 返回符合Prometheus文本格式的响应
        fallback_text = (
            "# HELP app_info Application info\n"
            "# TYPE app_info gauge\n"
            f'app_info{{version="{settings.APP_VERSION}",service="{settings.APP_NAME}"}} 1\n'
            "# HELP app_registry_status Registry status (1=healthy, 0=unhealthy)\n"
            "# TYPE app_registry_status gauge\n"
            "app_registry_status 1\n"
        )
        return Response(fallback_text, media_type="text/plain; charset=utf-8")


if __name__ == "__main__":
    import uvicorn
    import os

    # 生产环境使用多进程
    workers = 1 if settings.DEBUG else (os.cpu_count() or 1) * 2
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=workers,
        access_log=not settings.DEBUG,
    )
