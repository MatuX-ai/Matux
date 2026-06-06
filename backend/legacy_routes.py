"""
传统路由注册（非懒加载模式）

当 ENABLE_LAZY_LOADING=False 时，main.py 调用此函数注册所有路由。
当 ENABLE_LAZY_LOADING=True 时，由 LazyLoader 引擎自动管理路由注册。

这样 main.py 可以在两种模式间切换，而不需要大量条件判断。
"""

import logging

logger = logging.getLogger(__name__)


def register_all_routes(app):
    """
    注册所有传统路由到 FastAPI 应用

    仅在 ENABLE_LAZY_LOADING=False 时调用。
    当懒加载启用时，路由由 core.lazy_loader 自动管理。
    """
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
        local_knowledge_graph_routes,
        material_routes,
        model_benchmark_routes,
        model_update_routes,
        multimedia_routes,
        payment_routes,
        permission_routes,
        sponsorship_routes,
        subscription_routes,
        tenant_config_routes,
        unified_learning_record_routes,
        ai_edu_progress_routes,
        ai_teacher_routes,
        vector_knowledge_routes,
    )
    from routes import ai_capabilities_routes
    from routes import achievement_routes
    from routes import openhydra_routes
    from routes import admin_settings_routes
    from routes import finance_routes
    from routes import sensor_data_routes
    from routes import oauth_routes
    from routes import exam_routes
    from ai_service.model_routes import router as model_router
    from modules.auth.auth_routes import router as unified_auth_router
    from modules.learning.aggregation_routes import router as aggregation_router

    from config.settings import Settings
    settings = Settings()

    logger.info("📦 注册所有路由（传统模式）...")

    # === 核心路由 ===
    app.include_router(ai_routes.router, prefix="/api/v1", tags=["AI服务"])
    app.include_router(ai_recommend_routes.router,
                       prefix="/api/v1", tags=["AI 推荐服务"])
    app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["认证"])
    app.include_router(payment_routes.router, prefix="/api/v1", tags=["支付系统"])
    app.include_router(subscription_routes.router,
                       prefix="/api/v1", tags=["订阅系统"])
    app.include_router(hardware_certification_routes.router,
                       prefix="/api/v1/hardware", tags=["硬件认证"])
    app.include_router(course_routes.router, tags=["课程管理"])
    app.include_router(tenant_config_routes.router, tags=["租户配置管理(已解耦)"])
    app.include_router(educational_institution_routes.router,
                       tags=["教育机构管理(已解耦)"])
    app.include_router(permission_routes.router, tags=["权限管理(已解耦)"])
    app.include_router(course_version_routes.router, tags=["课程版本控制"])
    app.include_router(collaborative_editor_routes.router, tags=["协作编辑"])
    app.include_router(multimedia_routes.router, tags=["多媒体资源"])
    app.include_router(creativity_routes.router, tags=["创意引擎"])
    app.include_router(dynamic_course_routes.router,
                       prefix="/api/v1", tags=["动态课程生成"])
    app.include_router(ar_lab_routes.router)
    app.include_router(sponsorship_routes.router, tags=["企业赞助管理"])
    app.include_router(model_benchmark_routes.router, tags=["模型基准测试"])
    app.include_router(blockchain_gateway_routes.router,
                       prefix="/api/v1", tags=["区块链网关"])
    app.include_router(learning_behavior_routes.router,
                       prefix="/api/v1", tags=["学习行为特征"])
    app.include_router(learning_source_routes.router,
                       prefix="/api/v1", tags=["学习来源管理"])
    app.include_router(unified_learning_record_routes.router,
                       prefix="/api/v1", tags=["统一学习记录"])
    app.include_router(ar_rewards.router, prefix="/api/v1", tags=["AR 奖励系统"])
    app.include_router(openhydra_routes.router, tags=["AI 实验室"])
    app.include_router(ai_capabilities_routes.router, tags=["AI 能力组件"])
    app.include_router(achievement_routes.router)
    app.include_router(finance_routes.router, tags=["财务管理"])
    app.include_router(admin_settings_routes.router, tags=["Admin 设置管理"])
    app.include_router(sensor_data_routes.router)
    app.include_router(unified_auth_router)
    app.include_router(oauth_routes.router)
    app.include_router(exam_routes.router)
    app.include_router(model_router)
    app.include_router(aggregation_router)
    app.include_router(material_routes.router, tags=["统一课件库(已解耦)"])
    app.include_router(ai_edu_progress_routes.router, tags=["AI教育学习进度"])
    app.include_router(ai_teacher_routes.router, tags=["AI 个性化教师"])
    app.include_router(vector_knowledge_routes.router, tags=["向量知识库"])
    app.include_router(local_knowledge_graph_routes.router, tags=["本地知识图谱"])

    # === 可选路由 ===
    if settings.ENABLE_AR_VR_ROUTES:
        app.include_router(ar_vr_routes.router, tags=["AR/VR 课程"])
        logger.info("✅ AR/VR 课程内容管理路由已启用")

    if settings.ENABLE_AR_VR_MOCK_ROUTES:
        app.include_router(ar_vr_mock_routes.mock_router,
                           tags=["AR/VR Mock服务"])
        logger.info("✅ AR/VR Mock服务路由已启用")

    if settings.ENABLE_DIGITAL_TWIN_ROUTES:
        app.include_router(digital_twin_routes.router, tags=["数字孪生实验室"])
        logger.info("✅ 数字孪生实验室路由已启用")

    if settings.ENABLE_MODEL_UPDATE_ROUTES:
        app.include_router(model_update_routes.router, tags=["模型更新"])
        logger.info("✅ AI 模型热更新路由已启用")

    logger.info(f"📦 路由注册完成（传统模式）")
