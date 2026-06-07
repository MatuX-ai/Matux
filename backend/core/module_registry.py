"""
模块注册表

定义所有功能模块的规格，按 4 层分级架构注册：
- Tier 0 (核心层): auth, course, user → 启动即加载
- Tier 1 (高优先级): AI, payment, exam → 后台预加载
- Tier 2 (按需激活): AR/VR, blockchain, digital twin → 请求时激活
- Tier 3 (延迟激活): 高级 AI 沙箱, 硬件认证 → 用户主动触发

注意：
- /health 端点直接定义在 main.py 中，始终可用
- 部分路由使用非标准 router 变量名（如 ar_rewards.router）
- 存根路由（已解耦）归入 Tier 0 以保持兼容
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


def _factory(module_path: str, attr_name: str = "router"):
    """
    创建路由工厂函数的延迟加载包装器

    返回一个 callable，调用时才真正 import 模块并获取 router。
    包含错误处理和循环导入检测。
    """
    _cached_router = None
    _load_attempts = 0
    _max_attempts = 3

    def _create_router():
        nonlocal _cached_router, _load_attempts
        
        # 返回缓存的 router
        if _cached_router is not None:
            return _cached_router
        
        import importlib
        import logging
        logger = logging.getLogger(__name__)
        
        while _load_attempts < _max_attempts:
            try:
                mod = importlib.import_module(module_path)
                router = getattr(mod, attr_name)
                _cached_router = router
                return router
            except (ImportError, AttributeError) as e:
                _load_attempts += 1
                if _load_attempts >= _max_attempts:
                    logger.error(
                        f"Failed to load router {module_path}.{attr_name} "
                        f"after {_max_attempts} attempts: {e}"
                    )
                    raise ModuleNotFoundError(
                        f"Router '{attr_name}' not found in module '{module_path}'"
                    ) from e
                logger.warning(
                    f"Attempt {_load_attempts}/{_max_attempts} failed for "
                    f"{module_path}.{attr_name}: {e}. Retrying..."
                )
    
    return _create_router


class ModuleRegistryError(Exception):
    """模块注册表错误"""
    pass


def get_all_module_specs() -> List[dict]:
    """
    获取所有模块规格定义

    返回字典列表，每个字典描述一个模块的完整规格。
    由 core.lazy_loader 的 register 方法注册到懒加载引擎。
    """
    modules = []

    # ==================== Tier 0: 核心层 ====================
    # 用户认证、课程、基础数据 → 启动必须，< 3 秒

    modules.append({
        "name": "auth",
        "tier": 0,
        "prefix": "/api/v1/auth",
        "tags": ["认证"],
        "router_factory": _factory("routes.auth_routes", "router"),
        "dependencies": [],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.user.User",
            "models.oauth_account.OAuthAccount",
            "models.token_schemas.TokenBlacklist",
        ],
    })

    # 统一认证路由（手机号注册/登录、家长绑定学生、Token 刷新）
    modules.append({
        "name": "unified_auth",
        "tier": 0,
        "prefix": "",
        "tags": ["统一认证"],
        "router_factory": _factory("modules.auth.auth_routes", "router"),
        "dependencies": [],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    # 设备评估 API（插件化架构 Phase 1）
    modules.append({
        "name": "device_profile",
        "tier": 0,
        "prefix": "",
        "tags": ["设备评估"],
        "router_factory": _factory("routes.device_profile_routes", "router"),
        "dependencies": [],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    # 插件管理 API（插件化架构 Phase 2）
    modules.append({
        "name": "plugin_management",
        "tier": 0,
        "prefix": "",
        "tags": ["插件管理"],
        "router_factory": _factory("routes.plugin_routes", "router"),
        "dependencies": [],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "course",
        "tier": 0,
        "prefix": "",
        "tags": ["课程管理"],
        "router_factory": _factory("routes.course_routes", "router"),
        "dependencies": [],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.course.Course",
            "models.course.CourseLesson",
            "models.course.CourseAssignment",
        ],
    })

    # 课程版本控制
    modules.append({
        "name": "course_version",
        "tier": 0,
        "prefix": "",
        "tags": ["课程版本控制"],
        "router_factory": _factory("routes.course_version_routes", "router"),
        "dependencies": ["course"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    # 课程聚合（子项目回调、学生课程查询）
    modules.append({
        "name": "aggregation",
        "tier": 0,
        "prefix": "",
        "tags": ["课程聚合"],
        "router_factory": _factory(
            "modules.learning.aggregation_routes", "router"
        ),
        "dependencies": ["course"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    # 订阅系统
    modules.append({
        "name": "subscription",
        "tier": 0,
        "prefix": "/api/v1",
        "tags": ["订阅系统"],
        "router_factory": _factory("routes.subscription_routes", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.subscription.SubscriptionPlan",
            "models.subscription_fsm.SubscriptionFSM",
            "models.user_license.UserLicense",
        ],
    })

    # [已解耦] 存根路由 → Tier 0 保持兼容
    modules.append({
        "name": "tenant_config",
        "tier": 0,
        "prefix": "",
        "tags": ["租户配置管理(已解耦)"],
        "router_factory": _factory("routes.tenant_config_routes", "router"),
        "dependencies": [],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "edu_institution",
        "tier": 0,
        "prefix": "",
        "tags": ["教育机构管理(已解耦)"],
        "router_factory": _factory(
            "routes.educational_institution_routes", "router"
        ),
        "dependencies": [],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "permission",
        "tier": 0,
        "prefix": "",
        "tags": ["权限管理(已解耦)"],
        "router_factory": _factory("routes.permission_routes", "router"),
        "dependencies": [],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.permission.Permission",
            "models.user_organization.UserOrganization",
        ],
    })

    # [已解耦] 统一课件库
    modules.append({
        "name": "material",
        "tier": 0,
        "prefix": "",
        "tags": ["统一课件库(已解耦)"],
        "router_factory": _factory("routes.material_routes", "router"),
        "dependencies": [],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    # ==================== Tier 1: 高优先级 ====================
    # AI 服务、支付、考试 → 后台预加载，< 10 秒

    modules.append({
        "name": "ai_service",
        "tier": 1,
        "prefix": "/api/v1",
        "tags": ["AI服务"],
        "router_factory": _factory("routes.ai_routes", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.ai_request.AIRequest",
            "models.ai_completion.AICompletion",
        ],
    })

    modules.append({
        "name": "ai_recommend",
        "tier": 1,
        "prefix": "/api/v1",
        "tags": ["AI 推荐服务"],
        "router_factory": _factory("routes.ai_recommend_routes", "router"),
        "dependencies": ["ai_service"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.recommendation.Recommendation",
        ],
    })

    modules.append({
        "name": "ai_capabilities",
        "tier": 1,
        "prefix": "",
        "tags": ["AI 能力组件"],
        "router_factory": _factory(
            "routes.ai_capabilities_routes", "router"
        ),
        "dependencies": ["auth"],
        "required_services": ["openai"],
        "fallback_services": {"openai": "local_template"},
        "model_classes": [],
    })

    modules.append({
        "name": "ai_teacher",
        "tier": 1,
        "prefix": "",
        "tags": ["AI 个性化教师"],
        "router_factory": _factory("routes.ai_teacher_routes", "router"),
        "dependencies": ["ai_capabilities"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "ai_edu_progress",
        "tier": 1,
        "prefix": "",
        "tags": ["AI教育学习进度"],
        "router_factory": _factory(
            "routes.ai_edu_progress_routes", "router"
        ),
        "dependencies": ["auth", "course"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "payment",
        "tier": 1,
        "prefix": "/api/v1",
        "tags": ["支付系统"],
        "router_factory": _factory("routes.payment_routes", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.payment.Payment",
        ],
    })

    modules.append({
        "name": "exam",
        "tier": 1,
        "prefix": "",
        "tags": ["考试"],
        "router_factory": _factory("routes.exam_routes", "router"),
        "dependencies": ["auth", "course"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.exam.Exam",
            "models.exam.Question",
            "models.exam.ExamAttempt",
            "models.exam.CheatEvent",
        ],
    })

    modules.append({
        "name": "achievement",
        "tier": 1,
        "prefix": "",
        "tags": ["成就"],
        "router_factory": _factory("routes.achievement_routes", "router"),
        "dependencies": ["auth", "course"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.achievement.Achievement",
            "models.achievement.UserAchievement",
        ],
    })

    modules.append({
        "name": "multimedia",
        "tier": 1,
        "prefix": "",
        "tags": ["多媒体资源"],
        "router_factory": _factory("routes.multimedia_routes", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.multimedia.MediaResource",
            "models.multimedia.MediaCategory",
        ],
    })

    modules.append({
        "name": "learning_source",
        "tier": 1,
        "prefix": "/api/v1",
        "tags": ["学习来源管理"],
        "router_factory": _factory(
            "routes.learning_source_routes", "router"
        ),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "unified_learning_record",
        "tier": 1,
        "prefix": "/api/v1",
        "tags": ["统一学习记录"],
        "router_factory": _factory(
            "routes.unified_learning_record_routes", "router"
        ),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "dynamic_course",
        "tier": 1,
        "prefix": "/api/v1",
        "tags": ["动态课程生成"],
        "router_factory": _factory(
            "routes.dynamic_course_routes", "router"
        ),
        "dependencies": ["course"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    # ==================== Tier 2: 按需激活 ====================
    # AR/VR、区块链、数字孪生 → 请求时激活，< 2 秒

    modules.append({
        "name": "ar_vr",
        "tier": 2,
        "prefix": "",
        "tags": ["AR/VR"],
        "router_factory": _factory("routes.ar_vr_routes", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {"vircadia": "2d_simulation"},
        "model_classes": [
            "models.ar_vr_content.ARVRContent",
        ],
    })

    modules.append({
        "name": "ar_vr_mock",
        "tier": 2,
        "prefix": "",
        "tags": ["AR/VR Mock"],
        "router_factory": _factory("routes.ar_vr_mock_routes", "mock_router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "ar_lab",
        "tier": 2,
        "prefix": "",
        "tags": ["AR 实验室"],
        "router_factory": _factory("routes.ar_lab_routes", "router"),
        "dependencies": ["auth", "course"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "ar_rewards",
        "tier": 2,
        "prefix": "/api/v1",
        "tags": ["AR 奖励系统"],
        "router_factory": _factory("routes.ar_rewards", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "blockchain_gateway",
        "tier": 2,
        "prefix": "/api/v1",
        "tags": ["区块链网关"],
        "router_factory": _factory(
            "routes.blockchain_gateway_routes", "router"
        ),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {"hyperledger": "cache_mode"},
        "model_classes": [
            "models.verifiable_credential.VerifiableCredential",
        ],
    })

    modules.append({
        "name": "digital_twin",
        "tier": 2,
        "prefix": "",
        "tags": ["数字孪生"],
        "router_factory": _factory("routes.digital_twin_routes", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {"docker": "read_only"},
        "model_classes": [],
    })

    modules.append({
        "name": "collaborative_editor",
        "tier": 2,
        "prefix": "",
        "tags": ["协作编辑"],
        "router_factory": _factory(
            "routes.collaborative_editor_routes", "router"
        ),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.collaborative_editor.CollaborativeSession",
            "models.collaborative_editor.DocumentVersion",
        ],
    })

    modules.append({
        "name": "learning_behavior",
        "tier": 2,
        "prefix": "/api/v1",
        "tags": ["学习行为特征"],
        "router_factory": _factory(
            "routes.learning_behavior_routes", "router"
        ),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.learning_behavior.LearningBehavior",
        ],
    })

    modules.append({
        "name": "finance",
        "tier": 2,
        "prefix": "",
        "tags": ["财务管理"],
        "router_factory": _factory("routes.finance_routes", "router"),
        "dependencies": ["auth", "payment"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.finance.Transaction",
            "models.finance.Invoice",
        ],
    })

    modules.append({
        "name": "sponsorship",
        "tier": 2,
        "prefix": "",
        "tags": ["企业赞助管理"],
        "router_factory": _factory("routes.sponsorship_routes", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.sponsorship.Sponsorship",
        ],
    })

    modules.append({
        "name": "admin_settings",
        "tier": 2,
        "prefix": "",
        "tags": ["Admin 设置管理"],
        "router_factory": _factory("routes.admin_settings_routes", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "oauth",
        "tier": 2,
        "prefix": "",
        "tags": ["OAuth"],
        "router_factory": _factory("routes.oauth_routes", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.oauth_account.OAuthAccount",
        ],
    })

    modules.append({
        "name": "local_knowledge_graph",
        "tier": 2,
        "prefix": "",
        "tags": ["本地知识图谱"],
        "router_factory": _factory(
            "routes.local_knowledge_graph_routes", "router"
        ),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "content_store",
        "tier": 2,
        "prefix": "",
        "tags": ["内容商店"],
        "router_factory": _factory("routes.content_store_routes", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [
            "models.content_store.ContentItem",
            "models.content_store.ContentCategory",
        ],
    })

    # ==================== Tier 3: 延迟激活 ====================
    # AI 沙箱、硬件认证、OpenHydra → 用户主动触发

    modules.append({
        "name": "openhydra",
        "tier": 3,
        "prefix": "",
        "tags": ["AI 实验室"],
        "router_factory": _factory("routes.openhydra_routes", "router"),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {"openhydra": "disabled"},
        "model_classes": [],
    })

    modules.append({
        "name": "hardware",
        "tier": 3,
        "prefix": "/api/v1/hardware",
        "tags": ["硬件认证"],
        "router_factory": _factory(
            "routes.hardware_certification_routes", "router"
        ),
        "dependencies": ["auth"],
        "required_services": [],
        "fallback_services": {"hardware_auth": "offline_sim"},
        "model_classes": [
            "models.hardware_certification.HardwareCertificationDB",
            "models.hardware_module.HardwareModule",
        ],
    })

    modules.append({
        "name": "sensor_data",
        "tier": 3,
        "prefix": "",
        "tags": ["传感器"],
        "router_factory": _factory("routes.sensor_data_routes", "router"),
        "dependencies": ["hardware"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "vector_knowledge",
        "tier": 3,
        "prefix": "",
        "tags": ["向量知识库"],
        "router_factory": _factory(
            "routes.vector_knowledge_routes", "router"
        ),
        "dependencies": ["ai_capabilities"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "model_benchmark",
        "tier": 3,
        "prefix": "",
        "tags": ["模型基准测试"],
        "router_factory": _factory(
            "routes.model_benchmark_routes", "router"
        ),
        "dependencies": ["ai_capabilities"],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    modules.append({
        "name": "creativity",
        "tier": 3,
        "prefix": "",
        "tags": ["创意引擎"],
        "router_factory": _factory("routes.creativity_routes", "router"),
        "dependencies": ["ai_capabilities"],
        "required_services": ["openai"],
        "fallback_services": {"openai": "local_template"},
        "model_classes": [
            "models.creativity_models.CreativeProject",
        ],
    })

    # AI 模型热更新管理（来自 ai_service 子包）
    modules.append({
        "name": "model_update",
        "tier": 3,
        "prefix": "",
        "tags": ["AI 模型热更新"],
        "router_factory": _factory("ai_service.model_routes", "router"),
        "dependencies": [],
        "required_services": [],
        "fallback_services": {},
        "model_classes": [],
    })

    return modules


def get_core_modules() -> List[str]:
    """获取核心模块名列表（Tier 0）"""
    return [
        "auth",
        "unified_auth",
        "course",
        "course_version",
        "aggregation",
        "subscription",
        "tenant_config",
        "edu_institution",
        "permission",
        "material",
    ]


def get_preload_modules(tier_limit: int = 1) -> List[str]:
    """获取需要预加载的模块名列表"""
    specs = get_all_module_specs()
    return [s["name"] for s in specs if s["tier"] <= tier_limit]


# =============================================================================
# 插件机制：替代硬编码的动态模块注册
# =============================================================================

# 全局插件注册表
_PLUGIN_REGISTRY: List[dict] = []


def register_module(
    name: str,
    tier: int,
    prefix: str = "",
    tags: List[str] = None,
    dependencies: List[str] = None,
    required_services: List[str] = None,
    fallback_services: dict = None,
    model_classes: List[str] = None,
):
    """
    模块注册装饰器

    用法:
        @register_module("my_module", tier=1, prefix="/api/v1")
        def create_my_router():
            from routes import my_routes
            return my_routes.router
    """
    def decorator(router_factory):
        spec = {
            "name": name,
            "tier": tier,
            "prefix": prefix,
            "tags": tags or [],
            "router_factory": router_factory,
            "dependencies": dependencies or [],
            "required_services": required_services or [],
            "fallback_services": fallback_services or {},
            "model_classes": model_classes or [],
        }
        # 检查是否重复注册
        if not any(p["name"] == name for p in _PLUGIN_REGISTRY):
            _PLUGIN_REGISTRY.append(spec)
            logger.info(f"📦 插件模块已注册: {name} (Tier {tier})")
        return router_factory
    return decorator


def get_plugin_modules() -> List[dict]:
    """获取所有通过装饰器注册的插件模块"""
    return _PLUGIN_REGISTRY.copy()


def discover_plugins(base_path: str = "routes") -> List[dict]:
    """
    自动发现插件模块

    扫描指定目录下的所有 Python 文件，查找 @register_module 装饰的模块。
    """
    import os
    import sys
    from pathlib import Path

    discovered = []
    backend_path = Path(__file__).parent.parent
    scan_path = backend_path / base_path

    if not scan_path.exists():
        logger.warning(f"插件扫描路径不存在: {scan_path}")
        return discovered

    # 动态导入routes包以触发装饰器执行
    try:
        import importlib
        import pkgutil

        # 确保路径在 sys.path 中
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))

        # 遍历 routes 包下的所有模块
        for importer, modname, ispkg in pkgutil.iter_modules([str(scan_path)]):
            if modname.endswith("_routes"):
                try:
                    full_module_name = f"routes.{modname}"
                    mod = importlib.import_module(full_module_name)
                    logger.debug(f"扫描模块: {full_module_name}")
                except ImportError as e:
                    logger.warning(f"无法导入模块 {full_module_name}: {e}")

    except Exception as e:
        logger.warning(f"插件自动发现失败: {e}")

    # 从插件注册表获取已注册的模块
    discovered = get_plugin_modules()
    logger.info(f"🔍 发现 {len(discovered)} 个插件模块")
    return discovered


def get_all_module_specs_with_plugins() -> List[dict]:
    """
    获取所有模块规格（包含插件）

    合并硬编码模块和插件注册的模块。
    插件优先级高于硬编码（允许覆盖）。
    """
    # 获取硬编码模块
    hardcoded = get_all_module_specs()

    # 获取插件模块
    plugins = get_plugin_modules()

    # 合并：以插件覆盖硬编码
    merged = {m["name"]: m for m in hardcoded}
    for plugin in plugins:
        merged[plugin["name"]] = plugin

    return list(merged.values())
