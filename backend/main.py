"""
MatuX STEM 学习平台 API 服务主入口
提供AI代码生成、个性化学习、STEM实验等功能的FastAPI服务

注意：课件管理模块已解耦至 OpenMTSciEd 项目，机构管理模块已解耦至 OpenMTEduInst 项目。
本项目保留的路由存根仅用于兼容性，新功能请在对应项目中开发。
"""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
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
from routes import (  # noqa: E501
    ai_recommend_routes,
    ai_routes,
    ar_lab_routes,
    ar_rewards,
    ar_vr_mock_routes,
    ar_vr_routes,
    auth_routes,
    blockchain_gateway_routes,
    collaborative_editor_routes,
    course_routes,
    course_version_routes,
    creativity_routes,
    digital_twin_routes,
    dynamic_course_routes,
    educational_institution_routes,
    hardware_certification_routes,
    learning_behavior_routes,
    learning_source_routes,
    local_knowledge_graph_routes,  # 本地知识图谱
    material_routes,  # 统一课件库
    model_benchmark_routes,
    model_update_routes,
    multimedia_routes,
    payment_routes,
    permission_routes,
    sponsorship_routes,
    subscription_routes,
    tenant_config_routes,
    unified_learning_record_routes,
    ai_edu_progress_routes,  # AI教育学习进度
    ai_teacher_routes,  # AI 个性化教师
    vector_knowledge_routes,  # 向量知识库 (RAG)
)
from routes import ai_capabilities_routes  # XEduHub AI 能力组件
from routes import achievement_routes  # 成就系统
from routes import openhydra_routes  # OpenHydra AI 沙箱环境
from routes import admin_settings_routes  # Admin 后台全局设置
from routes import finance_routes  # 财务管理
from routes import sensor_data_routes  # 传感器数据
from routes import oauth_routes  # OAuth 第三方登录
from routes import exam_routes  # 防作弊测验系统
from ai_service.model_routes import router as model_router  # AI 模型热更新管理
from modules.auth.auth_routes import router as unified_auth_router
from modules.learning.aggregation_routes import (  # noqa: E501
    router as aggregation_router,
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

# 配置许可证验证中间件
# app.add_middleware(LicenseMiddleware)  # 临时禁用用于测试

# 配置熔断器中间件
if settings.CIRCUIT_BREAKER_ENABLED:
    circuit_config = CircuitBreakerConfig(
        failure_threshold=getattr(
            settings, "CIRCUIT_BREAKER_FAILURE_THRESHOLD", 5
        ),
        timeout=getattr(settings, "CIRCUIT_BREAKER_TIMEOUT", 60),
        half_open_max_calls=getattr(
            settings, "CIRCUIT_BREAKER_HALF_OPEN_ATTEMPTS", 3
        ),
    )
    app.add_middleware(  # noqa: E501
        CircuitBreakerMiddleware, config=circuit_config
    )

# 配置权限验证中间件
app.add_middleware(PermissionMiddleware)

# 配置日志
logger = setup_logger(settings.LOG_LEVEL, settings.LOG_FILE)

# 包含路由
app.include_router(  # noqa: E501
    ai_routes.router, prefix="/api/v1", tags=["AI服务"]
)
app.include_router(  # noqa: E501
    ai_recommend_routes.router,
    prefix="/api/v1",
    tags=["AI 推荐服务"],
)
app.include_router(  # noqa: E501
    auth_routes.router, prefix="/api/v1/auth", tags=["认证"]
)
app.include_router(  # noqa: E501
    payment_routes.router, prefix="/api/v1", tags=["支付系统"]
)
app.include_router(subscription_routes.router, prefix="/api/v1", tags=["订阅系统"])
app.include_router(  # noqa: E501
    hardware_certification_routes.router,
    prefix="/api/v1/hardware",
    tags=["硬件认证"],
)
app.include_router(course_routes.router, tags=["课程管理"])
# [已解耦] 租户配置管理路由 - 功能已迁移至 OpenMTEduInst 项目
# 此路由保留作为兼容性存根，新功能请在 OpenMTEduInst 中开发
app.include_router(tenant_config_routes.router, tags=["租户配置管理(已解耦)"])
# [已解耦] 教育机构管理路由 - 功能已迁移至 OpenMTEduInst 项目
# 此路由保留作为兼容性存根，新功能请在 OpenMTEduInst 中开发
app.include_router(educational_institution_routes.router, tags=["教育机构管理(已解耦)"])

# [已解耦] 权限管理路由 - 多租户权限功能已迁移至 OpenMTEduInst 项目
# 此路由保留作为兼容性存根
app.include_router(permission_routes.router, tags=["权限管理(已解耦)"])
app.include_router(course_version_routes.router, tags=["课程版本控制"])
app.include_router(collaborative_editor_routes.router, tags=["协作编辑"])
app.include_router(multimedia_routes.router, tags=["多媒体资源"])
app.include_router(creativity_routes.router, tags=["创意引擎"])
app.include_router(  # noqa: E501
    dynamic_course_routes.router, prefix="/api/v1", tags=["动态课程生成"]
)
app.include_router(ar_lab_routes.router)
app.include_router(sponsorship_routes.router, tags=["企业赞助管理"])
app.include_router(model_benchmark_routes.router, tags=["模型基准测试"])
app.include_router(
    blockchain_gateway_routes.router,
    prefix="/api/v1",
    tags=["区块链网关"],
)
app.include_router(
    learning_behavior_routes.router, prefix="/api/v1", tags=["学习行为特征"]
)

# 多来源学习关联管理路由
app.include_router(  # noqa: E501
    learning_source_routes.router,
    prefix="/api/v1",
    tags=["学习来源管理"],
)
app.include_router(  # noqa: E501
    unified_learning_record_routes.router,
    prefix="/api/v1",
    tags=["统一学习记录"],
)

app.include_router(ar_rewards.router, prefix="/api/v1", tags=["AR 奖励系统"])
# OpenHydra AI 沙箱环境 API 路由
# 提供容器生命周期管理、Jupyter 环境访问等功能
app.include_router(openhydra_routes.router, tags=["AI 实验室"])
# XEduHub AI 能力组件 API 路由
# 封装视觉分析、NLP 对话、ML 预测等 SOTA 模型能力
app.include_router(ai_capabilities_routes.router, tags=["AI 能力组件"])

# 成就系统 API 路由
# 提供成就创建、查询、进度追踪、徽章展示等功能
app.include_router(achievement_routes.router)

# 财务管理 API 路由
# 提供学费、薪酬、定价、消课等财务相关接口
app.include_router(finance_routes.router, tags=["财务管理"])
# Admin 后台全局设置 API 路由
# 提供全局配置的增删改查和测试连接功能
app.include_router(admin_settings_routes.router, tags=["Admin 设置管理"])

# 传感器数据 API 路由（提供 AR 实验室模拟传感器数据）
app.include_router(sensor_data_routes.router)

# 统一认证 API 路由（手机号注册/登录、家长绑定学生、Token刷新）
app.include_router(unified_auth_router)

# OAuth 第三方登录 API 路由
# 提供 GitHub/Google/WeChat/QQ 的 OAuth 2.0 授权码流程
app.include_router(oauth_routes.router)

# 防作弊测验系统 API 路由
# 提供测验 CRUD、考试流程、防作弊检测等功能
app.include_router(exam_routes.router)

# AI 模型热更新管理 API 路由
# 提供模型的注册、加载、卸载、推理、A/B测试等功能
app.include_router(model_router)

# 课程聚合 API 路由（子项目回调、学生课程查询）
app.include_router(aggregation_router)

# [已解耦] 统一课件库 API 路由 - 功能已迁移至 OpenMTSciEd 项目 (localhost:3000/api/v1)
# 此路由保留作为兼容性存根，新功能请在 OpenMTSciEd 中开发
# 支持24种课件类型的完整CRUD操作、统计分析、批量操作等功能
app.include_router(material_routes.router, tags=["统一课件库(已解耦)"])

# AI教育学习进度 API 路由
# 提供学习进度的上报、查询和统计分析功能
app.include_router(ai_edu_progress_routes.router, tags=["AI教育学习进度"])

# AI 个性化教师 API 路由
# 提供学生学习画像、上下文记忆、AI教师对话、成长轨迹、智能教学建议等功能
app.include_router(ai_teacher_routes.router, tags=["AI 个性化教师"])

# 向量知识库 API 路由 (RAG)
# 提供分层知识库检索、RAG上下文生成、知识库管理
app.include_router(vector_knowledge_routes.router, tags=["向量知识库"])

# 本地知识图谱 API 路由
# 提供本地知识图谱管理、学习路径推荐、个性化学习画像
app.include_router(local_knowledge_graph_routes.router, tags=["本地知识图谱"])

# AR 奖励系统API路由
# 处理 AR 场景完成、元件验证等奖励事件
# 集成成就徽章和积分奖励系统
# 手势识别系统API路由
# 处理 MediaPipe 手势识别和复杂手势序列检测
# 支持隐藏任务触发和奖励发放

# 可选路由注册 (根据配置启用)
if settings.ENABLE_AR_VR_ROUTES:
    app.include_router(ar_vr_routes.router, tags=["AR/VR 课程"])
    logger.info("✅ AR/VR 课程内容管理路由已启用")

if settings.ENABLE_AR_VR_MOCK_ROUTES:
    app.include_router(ar_vr_mock_routes.mock_router, tags=["AR/VR Mock服务"])
    logger.info("✅ AR/VR Mock服务路由已启用")

if settings.ENABLE_DIGITAL_TWIN_ROUTES:
    app.include_router(digital_twin_routes.router, tags=["数字孪生实验室"])
    logger.info("✅ 数字孪生实验室路由已启用")

if settings.ENABLE_FEDERATED_ROUTES:
    logger.info("✅ 联邦学习 API 路由已启用（暂未实现）")

if settings.ENABLE_MODEL_UPDATE_ROUTES:
    app.include_router(model_update_routes.router, tags=["模型更新"])
    logger.info("✅ AI 模型热更新路由已启用")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

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

    # 创建数据库表
    await create_db_and_tables()
    logger.info("Database tables created successfully")

    # 初始化测试数据（仅开发环境）
    if settings.DEBUG:
        try:
            from utils.init_test_data import initialize_test_data
            await initialize_test_data()
        except Exception as e:
            logger.error(f"测试数据初始化失败：{e}")
            import traceback
            traceback.print_exc()

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
        logger.error(f"数据库模块注册表初始化失败: {str(e)}")
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
        logger.info("数据库模块注册表资源已清理")
    except Exception as e:
        logger.error(f"清理注册表资源失败: {str(e)}")


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

    # 获取注册表信息
    registry_info = {}
    try:
        from database import get_registry_manager
        registry_manager = get_registry_manager()
        registry_info = registry_manager.get_registry_config()
    except Exception as e:
        registry_info = {"error": str(e)}

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
    """健康检查端点"""
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
            "total_categories": len(categorized)
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/registry/modules")
async def list_registry_modules(category: str | None = None):
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
                    "name": m.name,  # noqa: F821
                    "table_name": m.table_name,
                    "category": m.category,
                    "version": m.version,
                    "is_active": m.is_active,
                    "description": m.description,
                }
                for m in modules
            ],
            "filter_category": category,
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/test/faulty")
async def faulty_endpoint():
    """故障测试端点 - 用于熔断器测试"""
    import random

    if random.random() < 0.7:  # 70%概率失败
        raise ConnectionError("Simulated connection failure")
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
        # Fallback: 返回简单的文本响应
        fallback_text = (
            "# Prometheus metrics not available\n"
            "# Install prometheus_client for metrics support\n"
            "metrics_placeholder_info: Database registry system active\n"
        )
        return PlainTextResponse(fallback_text, status_code=200)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
