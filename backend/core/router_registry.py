"""双入口路由注册单一事实源（方案 C / PR-B commit 1）。

设计依据：tmp/router-c-design.md（方案 C 落地设计）
落地范围：PR-B commit 1 —— **仅新增本文件，零行为变更**
    main.py / main_ai_edu.py / legacy_routes.py 均未改动，
    本模块当前不被任何入口调用；后续 commit 3/4 才接入。

ROUTER_TABLE 的 61 条口径（必须写进注释，否则下一个人又会数成 59 或 62）::

    legacy 侧      : 53 处 include_router 调用 -> 52 个不同模块
                     （share_routes 贡献 2 处：api_router + page_router）
    main_ai_edu 侧 : 19 处 include_router 调用 -> 19 个不同模块
    交集           : 10 个模块
    并集           : 52 + 19 - 10 = 61 个模块   <- issue #21 的「并集 61」口径

    注：61 条按**模块**建表，share_routes 一条携带两个 router 对象，
        因此展开后的 include_router 调用数为 62。

生成方式（设计文档 §4.1 方案 C）：一次性脚本 AST 解析 legacy_routes.py +
main_ai_edu.py 产出候选 -> 人工核对 -> 固化为静态表 -> CI 反向校验。
本文件中的 module_path / router_attr / prefix / tags 全部来自 AST 实测值，
不手写。

白名单（issue #26 拍板）::

    routes.ai_teacher_routes        依赖 backend/cache/ 未入库
    routes.ai_edu_websocket_routes  依赖 services/ai_teacher_live_settings.py 未入库

    二者标记 status="pending_integration"：register_all_routers 遇到时
    logger.warning + 跳过 + 记录到 logs/router_registration_report.json。
    对应 WIP 提交后把 status 改回 active，白名单即自动清空。

三级失败策略（设计文档 §5.3）::

    L0 致命：strict=True 且任一失败 -> 收集全部失败后抛
             RouterRegistrationError（含完整失败清单），进程启动失败
    L1 降级（默认）：任一失败 -> logger.error + 落盘报告，应用继续启动，
             其余条目正常服务
    L2 熔断：同一模块连续失败 2 次（跨进程计数，写入 logs/）-> 跳过该模块
             并置 MODULE_DISABLED 标记，启动横幅显著告警
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import importlib
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# ==================== 常量 ====================

#: 正常参与注册的路由
STATUS_ACTIVE = "active"
#: 白名单：依赖尚未入库的模块，跳过注册（issue #26）
STATUS_PENDING_INTEGRATION = "pending_integration"
STATUS_VALUES = (STATUS_ACTIVE, STATUS_PENDING_INTEGRATION)

#: 归属 legacy 入口（legacy_routes.py）
MODE_LEGACY = "legacy"
#: 归属 main.py 懒加载分支（main_ai_edu 侧独有的 AI-Edu 路由）
MODE_LAZY = "lazy"
#: 两侧共用
MODE_BOTH = "both"
MODE_VALUES = (MODE_LEGACY, MODE_LAZY, MODE_BOTH)

#: 报告与失败计数落盘目录（backend/logs/，已被 .gitignore 忽略）
LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
REPORT_FILENAME = "router_registration_report.json"
FAILURE_COUNTER_FILENAME = "router_registration_failures.json"

#: L2 熔断阈值：同一模块连续失败达到该次数即跳过
CIRCUIT_BREAKER_THRESHOLD = 2


# ==================== 规格定义 ====================


@dataclass(frozen=True)
class RouterSpec:
    """单条路由注册规格（不可变、声明式）。

    字段说明：

    - name          稳定标识，ROUTER_TABLE 内唯一，用于 only/exclude 过滤
    - module_path   导入路径，例："routes.ai_edu_progress_routes"
    - router_attr   模块内的 router 属性名，例："router" / "api_router"；
                    同一模块含多个 router 对象时用元组（当前仅 share_routes）
    - prefix        include_router(prefix=...)
    - tags          include_router(tags=...)，对所有 attr 生效
    - attr_tags     可选的逐 attr 标签覆盖，长度须与 router_attr 一致
    - status        "active" | "pending_integration"
    - mode          "legacy" | "lazy" | "both"，归属入口
    - condition_key settings 中的开关键名，为空表示无条件启用
    - note          备注（依赖、已知问题等）
    """

    name: str
    module_path: str
    router_attr: Tuple[str, ...] = ("router",)
    prefix: str = ""
    tags: Tuple[str, ...] = ()
    attr_tags: Tuple[Tuple[str, ...], ...] = ()
    status: str = STATUS_ACTIVE
    mode: str = MODE_BOTH
    condition_key: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if isinstance(self.router_attr, str):
            object.__setattr__(self, "router_attr", (self.router_attr,))
        if isinstance(self.tags, str):
            object.__setattr__(self, "tags", (self.tags,))
        if not self.router_attr:
            raise ValueError(f"RouterSpec({self.name}): router_attr 不能为空")
        if self.attr_tags and len(self.attr_tags) != len(self.router_attr):
            raise ValueError(
                f"RouterSpec({self.name}): attr_tags 长度 "
                f"{len(self.attr_tags)} 与 router_attr 长度 "
                f"{len(self.router_attr)} 不一致"
            )
        if self.status not in STATUS_VALUES:
            raise ValueError(
                f"RouterSpec({self.name}): status 非法 -> {self.status!r}"
                f"（可选：{', '.join(STATUS_VALUES)}）"
            )
        if self.mode not in MODE_VALUES:
            raise ValueError(
                f"RouterSpec({self.name}): mode 非法 -> {self.mode!r}"
                f"（可选：{', '.join(MODE_VALUES)}）"
            )

    @property
    def key(self) -> str:
        """唯一键：模块 + 属性。"""
        return f"{self.module_path}:{'/'.join(self.router_attr)}"

    @property
    def is_pending_integration(self) -> bool:
        """是否属于白名单（pending_integration）。"""
        return self.status == STATUS_PENDING_INTEGRATION

    def tags_for(self, index: int) -> Tuple[str, ...]:
        """返回第 index 个 router 属性对应的标签。"""
        if self.attr_tags:
            if index < len(self.attr_tags):
                return self.attr_tags[index]
            return ()
        return self.tags

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典（便于报告输出与调试）。"""
        return {
            "name": self.name,
            "module": self.module_path,
            "attr": list(self.router_attr),
            "prefix": self.prefix,
            "tags": list(self.tags),
            "attr_tags": [list(t) for t in self.attr_tags],
            "status": self.status,
            "mode": self.mode,
            "condition_key": self.condition_key,
            "note": self.note,
        }


# ==================== 路由总表（61 条） ====================
#
# 顺序 = 设计文档 §4.3 的 A/B/C 分组：
#   A 组 main_ai_edu 独有 9 条 -> B 组 交集 10 条 -> C 组 legacy 独有 42 条
#
# 该表由一次性脚本 AST 实测生成并人工核对后固化（设计文档 §4.1）。
# 禁止手改：任何增删都必须同步更新 tmp/ 下的生成脚本，
# 否则 test_router_registry.py 的断言会红。

ROUTER_TABLE: Tuple[RouterSpec, ...] = (
    RouterSpec(
        name="ai_edu_code_execution",
        module_path="routes.ai_edu_code_execution",
        router_attr=("router",),
        prefix="/api/v1/org/{org_id}/ai-edu",
        tags=("AI 教育代码执行",),
        status="active",
        mode="lazy",
    ),
    RouterSpec(
        name="ai_edu_quiz",
        module_path="routes.ai_edu_quiz_routes",
        router_attr=("router",),
        prefix="/api/v1/org/{org_id}/ai-edu",
        tags=("AI 教育测验",),
        status="active",
        mode="lazy",
    ),
    RouterSpec(
        name="recommendation",
        module_path="routes.recommendation_routes",
        router_attr=("router",),
        prefix="",
        tags=("AI 智能推荐",),
        status="active",
        mode="lazy",
    ),
    RouterSpec(
        name="leaderboard",
        module_path="routes.leaderboard_routes",
        router_attr=("router",),
        prefix="",
        tags=("积分排行榜",),
        status="active",
        mode="lazy",
    ),
    RouterSpec(
        name="micro_course",
        module_path="routes.micro_course_routes",
        router_attr=("router",),
        prefix="",
        tags=("微课程转化",),
        status="active",
        mode="lazy",
    ),
    RouterSpec(
        name="llm_assistant",
        module_path="routes.llm_assistant_routes",
        router_attr=("router",),
        prefix="",
        tags=("AI 学习助手",),
        status="active",
        mode="lazy",
    ),
    RouterSpec(
        name="token",
        module_path="routes.token_routes",
        router_attr=("router",),
        prefix="",
        tags=("Token 管理",),
        status="active",
        mode="lazy",
    ),
    RouterSpec(
        name="vircadia_avatar",
        module_path="routes.vircadia_avatar_routes",
        router_attr=("router",),
        prefix="",
        tags=("Vircadia Avatar",),
        status="active",
        mode="lazy",
    ),
    RouterSpec(
        name="arvr_course",
        module_path="routes.arvr_course_routes",
        router_attr=("router",),
        prefix="",
        tags=(),
        status="active",
        mode="lazy",
    ),
    RouterSpec(
        name="ai_edu_progress",
        module_path="routes.ai_edu_progress_routes",
        router_attr=("router",),
        prefix="",
        tags=("AI教育学习进度",),
        status="active",
        mode="both",
    ),
    RouterSpec(
        name="ai_edu_websocket",
        module_path="routes.ai_edu_websocket_routes",
        router_attr=("router",),
        prefix="",
        tags=("AI 教育 WebSocket",),
        status="pending_integration",
        mode="both",
        note="依赖 services/ai_teacher_live_settings.py 未入库（issue #26）",
    ),
    RouterSpec(
        name="achievement",
        module_path="routes.achievement_routes",
        router_attr=("router",),
        prefix="",
        tags=("成就系统",),
        status="active",
        mode="both",
    ),
    RouterSpec(
        name="exam",
        module_path="routes.exam_routes",
        router_attr=("router",),
        prefix="",
        tags=("在线测验",),
        status="active",
        mode="both",
    ),
    RouterSpec(
        name="creativity",
        module_path="routes.creativity_routes",
        router_attr=("router",),
        prefix="",
        tags=("创意引擎",),
        status="active",
        mode="both",
    ),
    RouterSpec(
        name="auth",
        module_path="routes.auth_routes",
        router_attr=("router",),
        prefix="/api/v1/auth",
        tags=("认证",),
        status="active",
        mode="both",
    ),
    RouterSpec(
        name="system_status",
        module_path="routes.system_status_routes",
        router_attr=("router",),
        prefix="",
        tags=("系统管理",),
        status="active",
        mode="both",
    ),
    RouterSpec(
        name="error_log",
        module_path="routes.error_log_routes",
        router_attr=("router",),
        prefix="",
        tags=("错误日志管理",),
        status="active",
        mode="both",
    ),
    RouterSpec(
        name="org_error_log",
        module_path="routes.org_error_log_routes",
        router_attr=("router",),
        prefix="",
        tags=("错误日志（前端兼容路径）",),
        status="active",
        mode="both",
    ),
    RouterSpec(
        name="admin_arvr",
        module_path="routes.admin_arvr_routes",
        router_attr=("router",),
        prefix="",
        tags=("Admin - AR/VR 课程管理",),
        status="active",
        mode="both",
    ),
    RouterSpec(
        name="ai",
        module_path="routes.ai_routes",
        router_attr=("router",),
        prefix="/api/v1",
        tags=("AI服务",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="ai_recommend",
        module_path="routes.ai_recommend_routes",
        router_attr=("router",),
        prefix="/api/v1",
        tags=("AI 推荐服务",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="payment",
        module_path="routes.payment_routes",
        router_attr=("router",),
        prefix="/api/v1",
        tags=("支付系统",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="subscription",
        module_path="routes.subscription_routes",
        router_attr=("router",),
        prefix="/api/v1",
        tags=("订阅系统",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="hardware_certification",
        module_path="routes.hardware_certification_routes",
        router_attr=("router",),
        prefix="/api/v1/hardware",
        tags=("硬件认证",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="course",
        module_path="routes.course_routes",
        router_attr=("router",),
        prefix="",
        tags=("课程管理",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="tenant_config",
        module_path="routes.tenant_config_routes",
        router_attr=("router",),
        prefix="",
        tags=("租户配置管理(已解耦)",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="edu_institution",
        module_path="routes.educational_institution_routes",
        router_attr=("router",),
        prefix="",
        tags=("教育机构管理(已解耦)",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="permission",
        module_path="routes.permission_routes",
        router_attr=("router",),
        prefix="",
        tags=("权限管理(已解耦)",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="course_version",
        module_path="routes.course_version_routes",
        router_attr=("router",),
        prefix="",
        tags=("课程版本控制",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="collaborative_editor",
        module_path="routes.collaborative_editor_routes",
        router_attr=("router",),
        prefix="",
        tags=("协作编辑",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="multimedia",
        module_path="routes.multimedia_routes",
        router_attr=("router",),
        prefix="",
        tags=("多媒体资源",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="dynamic_course",
        module_path="routes.dynamic_course_routes",
        router_attr=("router",),
        prefix="/api/v1",
        tags=("动态课程生成",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="ar_lab",
        module_path="routes.ar_lab_routes",
        router_attr=("router",),
        prefix="",
        tags=(),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="sponsorship",
        module_path="routes.sponsorship_routes",
        router_attr=("router",),
        prefix="",
        tags=("企业赞助管理",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="model_benchmark",
        module_path="routes.model_benchmark_routes",
        router_attr=("router",),
        prefix="",
        tags=("模型基准测试",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="blockchain_gateway",
        module_path="routes.blockchain_gateway_routes",
        router_attr=("router",),
        prefix="/api/v1",
        tags=("区块链网关",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="learning_behavior",
        module_path="routes.learning_behavior_routes",
        router_attr=("router",),
        prefix="/api/v1",
        tags=("学习行为特征",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="learning_source",
        module_path="routes.learning_source_routes",
        router_attr=("router",),
        prefix="",
        tags=("学习来源管理",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="unified_learning_record",
        module_path="routes.unified_learning_record_routes",
        router_attr=("router",),
        prefix="",
        tags=("统一学习记录",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="ar_rewards",
        module_path="routes.ar_rewards",
        router_attr=("router",),
        prefix="/api/v1",
        tags=("AR 奖励系统",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="openhydra",
        module_path="routes.openhydra_routes",
        router_attr=("router",),
        prefix="",
        tags=("AI 实验室",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="ai_capabilities",
        module_path="routes.ai_capabilities_routes",
        router_attr=("router",),
        prefix="",
        tags=("AI 能力组件",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="finance",
        module_path="routes.finance_routes",
        router_attr=("router",),
        prefix="",
        tags=("财务管理",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="admin_settings",
        module_path="routes.admin_settings_routes",
        router_attr=("router",),
        prefix="",
        tags=("Admin 设置管理",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="sensor_data",
        module_path="routes.sensor_data_routes",
        router_attr=("router",),
        prefix="",
        tags=(),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="unified_auth",
        module_path="modules.auth.auth_routes",
        router_attr=("router",),
        prefix="",
        tags=(),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="oauth",
        module_path="routes.oauth_routes",
        router_attr=("router",),
        prefix="",
        tags=(),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="model",
        module_path="ai_service.model_routes",
        router_attr=("router",),
        prefix="",
        tags=(),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="aggregation",
        module_path="modules.learning.aggregation_routes",
        router_attr=("router",),
        prefix="",
        tags=(),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="material",
        module_path="routes.material_routes",
        router_attr=("router",),
        prefix="",
        tags=("统一课件库(已解耦)",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="ai_tutor",
        module_path="routes.ai_tutor_routes",
        router_attr=("router",),
        prefix="",
        tags=("AI编程导师",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="gamification_websocket",
        module_path="routes.gamification_websocket_routes",
        router_attr=("router",),
        prefix="",
        tags=("P3-A 游戏化 WebSocket",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="share",
        module_path="routes.share_routes",
        router_attr=(
            "api_router",
            "page_router",
        ),
        prefix="",
        tags=(),
        attr_tags=(
            ("P3-C 社交分享 API",),
            ("P3-C 社交分享 落地页",),
        ),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="ai_teacher",
        module_path="routes.ai_teacher_routes",
        router_attr=("router",),
        prefix="",
        tags=("AI 个性化教师",),
        status="pending_integration",
        mode="legacy",
        note="依赖 backend/cache/ 未入库（issue #26）",
    ),
    RouterSpec(
        name="vector_knowledge",
        module_path="routes.vector_knowledge_routes",
        router_attr=("router",),
        prefix="",
        tags=("向量知识库",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="local_knowledge_graph",
        module_path="routes.local_knowledge_graph_routes",
        router_attr=("router",),
        prefix="",
        tags=("本地知识图谱",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="opensciedu",
        module_path="routes.opensciedu_routes",
        router_attr=("router",),
        prefix="",
        tags=("OpenSciEDU 公共课程",),
        status="active",
        mode="legacy",
    ),
    RouterSpec(
        name="ar_vr",
        module_path="routes.ar_vr_routes",
        router_attr=("router",),
        prefix="",
        tags=("AR/VR 课程",),
        status="active",
        mode="legacy",
        condition_key="ENABLE_AR_VR_ROUTES",
    ),
    RouterSpec(
        name="ar_vr_mock",
        module_path="routes.ar_vr_mock_routes",
        router_attr=("mock_router",),
        prefix="",
        tags=("AR/VR Mock服务",),
        status="active",
        mode="legacy",
        condition_key="ENABLE_AR_VR_MOCK_ROUTES",
    ),
    RouterSpec(
        name="digital_twin",
        module_path="routes.digital_twin_routes",
        router_attr=("router",),
        prefix="",
        tags=("数字孪生实验室",),
        status="active",
        mode="legacy",
        condition_key="ENABLE_DIGITAL_TWIN_ROUTES",
    ),
    RouterSpec(
        name="model_update",
        module_path="routes.model_update_routes",
        router_attr=("router",),
        prefix="",
        tags=("模型更新",),
        status="active",
        mode="legacy",
        condition_key="ENABLE_MODEL_UPDATE_ROUTES",
    ),
)


# ==================== 结果清单 ====================


@dataclass
class RouterRegistrationReport:
    """注册结果清单（设计文档 §5.2 隔离契约 / §5.4 落盘格式）。"""

    mode: str = MODE_LEGACY
    total: int = 0
    succeeded: List[str] = field(default_factory=list)
    failed: List[Dict[str, str]] = field(default_factory=list)
    skipped: List[Dict[str, str]] = field(default_factory=list)
    disabled: List[Dict[str, str]] = field(default_factory=list)
    duration_ms: Dict[str, float] = field(default_factory=dict)

    @property
    def failed_count(self) -> int:
        return len(self.failed)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为落盘格式。"""
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "mode": self.mode,
            "total": self.total,
            "succeeded": len(self.succeeded),
            "succeeded_modules": list(self.succeeded),
            "failed": list(self.failed),
            "skipped": list(self.skipped),
            "disabled": list(self.disabled),
            "duration_ms": {
                key: round(value, 2) for key, value in self.duration_ms.items()
            },
        }


class RouterRegistrationError(RuntimeError):
    """L0 致命错误：strict=True 时抛出，携带完整失败清单。"""

    def __init__(
        self,
        failures: Sequence[Dict[str, str]],
        mode: str = MODE_LEGACY,
    ):
        self.failures = list(failures)
        self.mode = mode
        detail = "; ".join(
            f"{item.get('module')}: {item.get('error')}" for item in self.failures
        )
        super().__init__(f"路由注册失败（mode={mode}，共 {len(self.failures)} 项）：{detail}")


# ==================== 内部工具 ====================


def _import_router(spec: RouterSpec, attr: str) -> Any:
    """导入模块并取出 router 对象。

    直接 importlib.import_module + getattr，绕开 routes/__init__.py 的惰性
    __getattr__（该代理只在 ``from routes import x`` 形态下触发），
    因此拿到的是真实 router 对象而不是惰性代理。
    """
    module = importlib.import_module(spec.module_path)
    try:
        return getattr(module, attr)
    except AttributeError as exc:
        raise AttributeError(f"模块 {spec.module_path} 中不存在 router 属性 {attr!r}") from exc


def _condition_enabled(condition_key: str) -> bool:
    """读取 settings 中的开关键。

    settings 不可用时按「未启用」处理 —— 条件路由默认关闭，
    宁可少注册也不要因为配置读取异常导致启动失败。
    """
    try:
        from config.settings import get_settings
    except Exception as exc:  # noqa: BLE001 - 配置不可读不应阻断启动
        logger.warning(
            "无法读取 config.settings（%s），条件路由 %s 按未启用处理",
            exc,
            condition_key,
        )
        return False
    try:
        return bool(getattr(get_settings(), condition_key, False))
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "读取 settings.%s 失败（%s），按未启用处理",
            condition_key,
            exc,
        )
        return False


def _select_specs(
    mode: str,
    only: Optional[Sequence[str]],
    exclude: Optional[Sequence[str]],
) -> List[RouterSpec]:
    """按 mode / only / exclude 筛选待注册条目。"""
    specs: List[RouterSpec] = list(ROUTER_TABLE)
    if mode == MODE_LAZY:
        # 懒加载分支只显式注册「懒加载归属」与「两侧共用」的条目；
        # 其余条目交由 core/lazy_loader 按 Tier 激活。
        # 精确集合在 PR-B commit 4 随 main.py 双分支收敛一并定稿。
        specs = [s for s in specs if s.mode in (MODE_LAZY, MODE_BOTH)]

    only_set = set(only) if only else None
    exclude_set = set(exclude) if exclude else set()

    selected: List[RouterSpec] = []
    for spec in specs:
        if only_set is not None and spec.name not in only_set:
            continue
        if spec.name in exclude_set:
            continue
        selected.append(spec)
    return selected


def _load_failure_counters() -> Dict[str, int]:
    """读取跨进程失败计数（L2 熔断用）。"""
    path = LOG_DIR / FAILURE_COUNTER_FILENAME
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        logger.warning("路由失败计数文件不可用（%s），按空计数处理", exc)
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        str(key): int(value) for key, value in data.items() if isinstance(value, int)
    }


def _save_failure_counters(counters: Dict[str, int]) -> None:
    """落盘跨进程失败计数。落盘失败不影响启动。"""
    path = LOG_DIR / FAILURE_COUNTER_FILENAME
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(counters, handle, ensure_ascii=False, indent=2, sort_keys=True)
    except OSError as exc:
        logger.warning("路由失败计数落盘失败（不影响启动）: %s", exc)


def _write_report(report: RouterRegistrationReport) -> None:
    """落盘注册报告。落盘失败不影响启动。"""
    path = LOG_DIR / REPORT_FILENAME
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(report.to_dict(), handle, ensure_ascii=False, indent=2)
    except OSError as exc:
        logger.warning("路由注册报告落盘失败（不影响启动）: %s", exc)


# ==================== 对外接口 ====================


def _register_spec(
    app: Any,
    spec: RouterSpec,
    report: RouterRegistrationReport,
    counters: Dict[str, int],
    updated: Dict[str, int],
) -> None:
    """处理单条 spec：白名单 -> 条件开关 -> L2 熔断 -> 实际注册。

    失败一律隔离（L1 降级）：记录到 report.failed 并累加失败计数，
    不向上抛，由调用方在 strict=True 时统一抛 RouterRegistrationError。
    """
    # --- 1. 白名单：pending_integration 直接跳过 ---
    if spec.is_pending_integration:
        reason = spec.note or f"status={STATUS_PENDING_INTEGRATION}"
        logger.warning("跳过待集成路由 %s（%s）", spec.name, reason)
        report.skipped.append(
            {
                "module": spec.module_path,
                "attr": "/".join(spec.router_attr),
                "reason": reason,
            }
        )
        return

    # --- 2. 条件开关 ---
    if spec.condition_key and not _condition_enabled(spec.condition_key):
        logger.info("跳过未启用路由 %s（%s=False）", spec.name, spec.condition_key)
        report.skipped.append(
            {
                "module": spec.module_path,
                "attr": "/".join(spec.router_attr),
                "reason": f"{spec.condition_key}=False",
            }
        )
        return

    # --- 3. L2 熔断：连续失败达阈值则跳过 ---
    previous = counters.get(spec.key, 0)
    if previous >= CIRCUIT_BREAKER_THRESHOLD:
        logger.error(
            "路由 %s 连续失败 %d 次，已熔断跳过（MODULE_DISABLED）",
            spec.key,
            previous,
        )
        report.disabled.append(
            {
                "module": spec.module_path,
                "attr": "/".join(spec.router_attr),
                "reason": f"连续失败 {previous} 次，已熔断",
            }
        )
        return

    # --- 4. 实际注册 ---
    started = time.perf_counter()
    try:
        for index, attr in enumerate(spec.router_attr):
            router = _import_router(spec, attr)
            app.include_router(
                router,
                prefix=spec.prefix,
                tags=list(spec.tags_for(index)),
            )
    except Exception as exc:  # noqa: BLE001 - 注册失败必须隔离
        report.duration_ms[spec.key] = (time.perf_counter() - started) * 1000
        error = f"{type(exc).__name__}: {exc}"
        logger.error("路由注册失败 %s：%s", spec.key, error)
        report.failed.append(
            {
                "module": spec.module_path,
                "attr": "/".join(spec.router_attr),
                "error": error,
            }
        )
        updated[spec.key] = previous + 1
        return

    report.duration_ms[spec.key] = (time.perf_counter() - started) * 1000
    report.succeeded.append(spec.key)
    updated[spec.key] = 0


def register_all_routers(
    app: Any,
    *,
    mode: str = MODE_LEGACY,
    strict: bool = False,
    only: Optional[Sequence[str]] = None,
    exclude: Optional[Sequence[str]] = None,
) -> RouterRegistrationReport:
    """按 ROUTER_TABLE 注册路由，返回注册结果清单。

    Args:
        app: FastAPI 应用实例（或任何提供 include_router 的对象）
        mode: "legacy" 注册全量条目（legacy 模式提供完整路由集）；
              "lazy" 只注册归属懒加载与两侧共用的条目
        strict: True -> L0 致命，收集完全部失败后抛 RouterRegistrationError
        only: 只注册指定 name 的条目（调试用）
        exclude: 排除指定 name 的条目（调试用）

    Returns:
        RouterRegistrationReport —— 成功 / 失败 / 跳过 / 熔断四类清单
    """
    if mode not in (MODE_LEGACY, MODE_LAZY):
        raise ValueError(f"mode 非法 -> {mode!r}（可选：{MODE_LEGACY}, {MODE_LAZY}）")

    specs = _select_specs(mode, only, exclude)
    report = RouterRegistrationReport(mode=mode, total=len(specs))

    counters = _load_failure_counters()
    updated: Dict[str, int] = {}

    for spec in specs:
        _register_spec(app, spec, report, counters, updated)

    # 未参与本次注册的条目保留原有计数
    merged = {k: v for k, v in counters.items() if k not in updated}
    merged.update(updated)
    _save_failure_counters(merged)
    _write_report(report)

    # --- L0 致命：收集完全部失败后再抛，保证错误信息含完整清单 ---
    if strict and report.failed:
        raise RouterRegistrationError(report.failed, mode=mode)

    if report.failed or report.disabled:
        logger.warning(
            "路由注册完成（降级启动）：成功 %d / 失败 %d / 跳过 %d / 熔断 %d",
            len(report.succeeded),
            len(report.failed),
            len(report.skipped),
            len(report.disabled),
        )
    else:
        logger.info(
            "路由注册完成：成功 %d / 跳过 %d（共 %d 条）",
            len(report.succeeded),
            len(report.skipped),
            report.total,
        )
    return report


def pending_integration_modules() -> List[str]:
    """返回白名单模块路径（status="pending_integration"，issue #26）。

    test_router_parity.py 用它构造 exclude 集合：白名单内的模块不参与
    parity 判定，但也不能被误判为「漏注册」。
    """
    return [spec.module_path for spec in ROUTER_TABLE if spec.is_pending_integration]


def active_specs() -> List[RouterSpec]:
    """返回所有 status="active" 的规格。"""
    return [spec for spec in ROUTER_TABLE if spec.status == STATUS_ACTIVE]


def specs_by_name() -> Dict[str, RouterSpec]:
    """返回 name -> RouterSpec 的映射。"""
    return {spec.name: spec for spec in ROUTER_TABLE}
