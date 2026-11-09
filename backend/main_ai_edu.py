"""
AI-Edu-for-Kids 简化版后端服务

只包含 AI-Edu 相关的功能，避免其他模块的依赖问题
"""

import asyncio
import logging
import os
from pathlib import Path
import sys


def _run_user_code_if_requested() -> None:
    """隐藏模式：用随包 Python 运行时执行用户代码（本地代码执行降级用）。

    【§8.1-6】桌面端不随包分发 Docker，代码执行降级为本地受限进程：
    由 services/local_code_runner.py 调起 `main_ai_edu.exe --run-user-code <file>`。

    必须放在导入 FastAPI / 路由之前：子进程只需要解释器本身，
    否则每次执行用户代码都要多付上千个模块的导入时间（数秒）。
    """
    argv = sys.argv[1:]
    if not argv or argv[0] != "--run-user-code":
        return
    if len(argv) < 2:
        sys.stderr.write("usage: main_ai_edu --run-user-code <script>\n")
        sys.exit(2)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover - 非 TextIOWrapper
            pass

    script_path = argv[1]
    try:
        source = Path(script_path).read_text(encoding="utf-8")
        # 本进程就是「代码执行器」，执行用户的 python 脚本是设计行为；
        # 隔离由 local_code_runner 的独立子进程 + 超时强杀 + 静态黑名单保证，
        # 容器级隔离在 Phase 1.5 接 Docker 沙箱。
        namespace = {"__name__": "__main__", "__file__": script_path}
        exec(compile(source, script_path, "exec"), namespace)  # noqa: S102
    except SystemExit:
        raise
    except BaseException:
        import traceback

        traceback.print_exc()
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    _run_user_code_if_requested()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 【Phase1 修复】扁平化成就 / 课程查询路由：桌面端此前只有组织级成就路由，
#   /api/v1/achievements 与 /api/v1/courses 均 404，前端只能显示示例数据。
from routes.achievement_catalog_routes import router as achievement_catalog_router
from routes.achievement_routes import router as achievement_router

# 【P1-Admin 补齐】注册 Admin AR/VR 课程管理路由
#   提供后台课程 CRUD / 上传 / 编辑 / 删除能力，路径 /api/v1/admin/arvr/*，
#   需要 Bearer JWT + admin 角色才能访问。
from routes.admin_arvr_routes import router as admin_arvr_router
from routes.ai_edu_code_execution import router as ai_edu_code_router
from routes.ai_edu_progress_routes import router as ai_edu_progress_router
from routes.ai_edu_quiz_routes import router as ai_edu_quiz_router

# 协作文档模块因编码问题暂未修复，后续处理
# from routes.collaboration_routes import (
#     discussion_router,
#     document_router,
#     group_router,
#     project_router,
# )
from routes.ai_edu_websocket_routes import router as ai_edu_websocket_router

# 【P0 修复】补齐 AI 个性化教师路由：桌面端（main_ai_edu 入口）原先未注册，
#   导致 /api/v1/ai-teacher/* 全部 404，前端 AI 教师页面不可用。
#   依赖 backend/cache/ 已在 feat/desktop-p3-batch1 分支入库，可直接注册。
#   路由内 prefix 已含 /api/v1/ai-teacher，共 17 条路由，不需再传 prefix。
from routes.ai_teacher_routes import router as ai_teacher_router

# 【P1-Backend 修复 #1】补齐 arvr_course_routes：前端 ARVRCoursePlayerComponent 调用
#   /api/v1/arvr-courses/{id}，原 routes/ar_vr_routes.py 提供的路径是 /api/v1/org/{org_id}/arvr/*，
#   前端调用 404 → ARVR 课程 502。补齐后 ARVR 课程可正常加载。
from routes.arvr_course_routes import router as arvr_course_router

# 【修复 #10】补充 auth_router 注册：main_ai_edu.py 原版未包含认证路由，
#   导致 /api/v1/auth/signin 返回 404，前端登录失败。
#   auth_routes 依赖为 iMato 标准库（bcrypt、jose、sqlalchemy 等），与现有后端环境兼容。
from routes.auth_routes import router as auth_router
from routes.course_catalog_routes import router as course_catalog_router
from routes.creativity_routes import router as creativity_router

# 【P0-A 修复】注册数字孪生实验室路由：桌面端入口（main_ai_edu）此前从未 include，
#   且 legacy_routes 受 ENABLE_DIGITAL_TWIN_ROUTES=False 关闭，
#   导致 /api/v1/digital-twin/sessions 与 /ws/session/{id} 全部 404。
#   前端 digital-twin-lab 因此显示“会话 ID 缺失 / 实时同步已停用”。
#   路由内部 prefix 已含 /digital-twin。
from routes.digital_twin_routes import router as digital_twin_router
from routes.error_log_routes import router as error_log_router

# 【P1 修复 #P1-2】补充 exam_router 注册：在线测验模块
#   main_ai_edu.py 原版未注册 exam_routes，导致 /api/v1/exams 返回 404
#   前端 ExamListComponent 会显示“服务器错误”，UX 完整度测试中标记为 P1。
from routes.exam_routes import router as exam_router
# 【P0-C 修复】注册游戏化 WebSocket 路由（/ws/gamification）
#   成就中心 / 签到页依赖实时推送（achievement_unlocked / node_status_updated / set_completed）。
#   此前桌面端入口（main_ai_edu）只挂了 AI 教育 WS，从未 include 本 router，
#   因此 /ws/gamification 返回 404，前端无论怎么改 URL 都连不上。
#   注：commit 28890ff 恢复的是 legacy_routes.py 的注册，桌面端不走该入口。
from routes.gamification_websocket_routes import router as gamification_ws_router
from routes.leaderboard_routes import router as leaderboard_router
from routes.llm_assistant_routes import router as llm_assistant_router
from routes.micro_course_routes import router as micro_course_router

# 【P0-B 修复】注册 OpenSciEDU 公共课程路由：桌面端入口此前未 include，
#   前端 /api/v1/opensciedu/* 全部 404 → 只能走 mock 兜底。
#   路由内部 prefix 已含 /api/v1/opensciedu。
from routes.opensciedu_routes import router as opensciedu_router

# 【P1-Backend 修复 #2】补齐 org_error_log_routes：前端 ErrorLoggerService 调用
#   /api/v1/org/{org_id}/logs/error，原 routes/error_log_routes.py 提供的路径是 /logs/error（无 org_id 前缀），
#   前端调用 404 → ErrorLoggerService 上报失败。补齐后前端错误可正常上报。
from routes.org_error_log_routes import router as org_error_log_router
from routes.recommendation_routes import router as recommendation_router

# 【修复 #11】补充 system_status_router 注册：底部状态栏轮询
#   /api/v1/system/health-detail 和 /api/v1/system/modules 依赖此 router。
#   缺失则 404 → catchError → healthy$.next(false) → 状态栏显示"后端未启动"。
from routes.system_status_routes import router as system_status_router
from routes.token_routes import router as token_router
from routes.vircadia_avatar_routes import router as vircadia_avatar_router
from utils.database import Base, sync_engine
import uvicorn

logger = logging.getLogger("main_ai_edu")


def _force_utf8_stdio() -> None:
    """统一 stdout/stderr 为 UTF-8。

    Electron 用 utf8 解析子进程输出；Windows 默认 cp936 会让中文日志乱码，
    且种子/启动日志里的 emoji 会抛 UnicodeEncodeError 直接中断流程。
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover - 非 TextIOWrapper
            pass


# 创建 FastAPI 应用
app = FastAPI(
    title="AI-Edu-for-Kids API", description="AI 教育课程学习平台 API", version="1.0.0"
)

# CORS 配置
# 【P1 修复 #13】环境变量驱动 + 合理默认值
# - 默认允许 4200 (Angular dev server) / 3000 (Webpack dev server) / 8080 (本地 UX 测试静态服务器)
# - 生产环境可通过环境变量 CORS_ALLOWED_ORIGINS 覆盖，逗号分隔，例如：
#   CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
# - 开发环境允许本地任意 http://localhost:* 端口，方便不同端口调试
_default_dev_origins = ["http://localhost:4200", "http://localhost:3000", "http://localhost:8080"]
_env_origins = os.getenv("CORS_ALLOWED_ORIGINS")
if _env_origins:
    allow_origins = [o.strip() for o in _env_origins.split(",") if o.strip()]
elif os.getenv("APP_ENV") == "production":
    # 生产环境默认为保守白名单，需通过环境变量显式指定
    allow_origins = ["http://localhost:4200"]
else:
    # 开发环境：同时覆盖常见调试端口
    allow_origins = _default_dev_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查端点
@app.get("/")
async def root():
    return {"service": "AI-Edu-for-Kids API", "version": "1.0.0", "status": "running"}


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# 导入 AI-Edu 路由

# 错误日志收集路由

# O2.4 AI 学习助手路由

# O2.3 微课程转化路由

# Vircadia Avatar 路由

# 注册路由
app.include_router(
    ai_edu_progress_router, tags=["AI 教育"]
)
app.include_router(
    ai_edu_code_router, prefix="/api/v1/org/{org_id}/ai-edu", tags=["AI 教育代码执行"]
)
app.include_router(
    ai_edu_quiz_router, prefix="/api/v1/org/{org_id}/ai-edu", tags=["AI 教育测验"]
)
app.include_router(ai_edu_websocket_router, tags=["AI 教育 WebSocket"])
app.include_router(achievement_router, tags=["成就系统"])
# 【Phase1 修复】扁平化成就 / 课程查询（真实数据库）
#   GET /api/v1/achievements?userId=  → 成就定义 + 解锁状态
#   GET /api/v1/courses             → 课程列表（含我的选课）
app.include_router(achievement_catalog_router)
app.include_router(course_catalog_router)
# 【P1 修复 #P1-2】注册测验路由。路由内部已包含完整 prefix /api/v1/exams，
#   ExamListComponent 调用 /api/v1/exams?status=published&page=1&page_size=20
#   不需要再传 prefix。
app.include_router(exam_router, tags=["在线测验"])
app.include_router(recommendation_router, tags=["AI 智能推荐"])
app.include_router(leaderboard_router, tags=["积分排行榜"])
# 协作文档路由因编码问题暂未启用
# app.include_router(discussion_router, tags=["协作学习 - 讨论区"])
# app.include_router(document_router, tags=["协作学习 - 协作文档"])
# app.include_router(group_router, tags=["协作学习 - 学习小组"])
# app.include_router(project_router, tags=["协作学习 - 项目管理"])
# O2.3 微课程转化
app.include_router(micro_course_router, tags=["微课程转化"])
# O2.4 AI 学习助手
app.include_router(llm_assistant_router, tags=["AI 学习助手"])

# 创意激发引擎
app.include_router(creativity_router, tags=["创意引擎"])
# 【修复 #10】认证路由（signin/signup/me/token/refresh/logout 等）
app.include_router(auth_router, prefix="/api/v1/auth", tags=["认证"])
# 【修复 #11】系统状态路由（health-detail/modules/circuit-breakers 等）
#   路由装饰器中已含完整路径 /api/v1/system/*，不需要再传 prefix
app.include_router(system_status_router)
# Token 管理
app.include_router(token_router, tags=["Token 管理"])
# 错误日志收集
app.include_router(
    error_log_router, tags=["错误日志管理"]
)
# Vircadia Avatar
app.include_router(
    vircadia_avatar_router, tags=["Vircadia Avatar"]
)
# 【P1-Backend 修复 #1】注册 ARVR 课程路由（前端简化路径）
#   前端 ARVRCoursePlayerComponent 调用 GET /api/v1/arvr-courses/{id}
#   路由内部 prefix 已包含 /api/v1/arvr-courses
app.include_router(arvr_course_router)
# 【P1-Backend 修复 #2】注册组织级错误日志路由（前端兼容路径）
#   前端 ErrorLoggerService 调用 POST /api/v1/org/{org_id}/logs/error
#   路由内部 prefix 已包含 /api/v1/org/{org_id}/logs
app.include_router(org_error_log_router)
# 【P1-Admin 补齐】注册 Admin AR/VR 课程管理后台
#   路径 /api/v1/admin/arvr/*，要求 JWT + admin 角色
app.include_router(admin_arvr_router)
# 【P0 修复】注册 AI 个性化教师路由（17 条，/api/v1/ai-teacher/*）
#   本入口手写 include_router，不经过 core.router_registry.register_all_routers，
#   因此不会与 ROUTER_TABLE 重复注册。
app.include_router(ai_teacher_router, tags=["AI 个性化教师"])
# 【P0-C 修复】注册游戏化 WebSocket：router 内 prefix 已含 /ws/gamification，
#   端点本身是 @router.websocket("")，最终路径 /ws/gamification?token=<JWT>。
app.include_router(gamification_ws_router)
# 【P0-A 修复】数字孪生实验室（HTTP + WebSocket）
app.include_router(digital_twin_router, tags=["数字孪生实验室"])
# 【P0-B 修复】OpenSciEDU 公共课程（真实 API，命不中时前端自动回退 mock）
app.include_router(opensciedu_router, tags=["OpenSciEDU 公共课程"])


# 临时测试路由
@app.get("/api/v1/org/{org_id}/ai-edu/modules")
async def get_modules(org_id: int):
    return {
        "success": True,
        "data": [
            {
                "id": 1,
                "module_code": "basic_concepts_01",
                "name": "AI 基本概念入门",
                "description": "人工智能基础概念介绍，适合小学 1-6 年级学生",
                "category": "basic_concepts",
                "expected_lessons": 3,
                "expected_duration_minutes": 60,
            }
        ],
    }


@app.get("/api/v1/org/{org_id}/ai-edu/progress")
async def get_progress(org_id: int):
    return {"success": True, "data": [], "count": 0}


@app.get("/api/v1/org/{org_id}/ai-edu/progress/statistics")
async def get_statistics(org_id: int):
    return {
        "success": True,
        "data": {
            "total_courses": 3,
            "completed_courses": 0,
            "in_progress_courses": 0,
            "not_started_courses": 3,
            "total_time_hours": 1.0,
            "average_quiz_score": 0,
            "average_code_score": 0,
            "total_points": 0,
            "completion_rate": 0,
        },
    }


_SECONDARY_MODULES = (
    "models.achievement",
    "models.leaderboard",
    "models.content_store",
    "models.finance",
    "models.hardware_module",
)


def _import_secondary_models() -> None:
    """逐个导入副 Base 模型（单个失败不影响其他表）。"""
    for module in _SECONDARY_MODULES:
        try:
            __import__(module)
        except Exception:
            logger.warning("导入 %s 失败（跳该表）", module, exc_info=True)


def _register_users_shadow(legacy_base) -> None:
    """在副 Base 的 metadata 里注册 users 影子表供 FK 解析。

    副 Base 的 user_achievements 等表有 FK 指向 users（主 Base 的表）。
    不同 metadata 互不可见，缺少目标定义时 create_all 会报 NoReferencedTableError。
    create_all 默认 checkfirst，已存在的真实 users 表不会被重建。
    """
    try:
        from sqlalchemy import Column, Integer, Table

        if "users" not in legacy_base.metadata.tables:
            Table("users", legacy_base.metadata, Column("id", Integer, primary_key=True))
    except Exception:  # pragma: no cover - 影子表仅用于 FK 解析
        logger.warning("注册 users 影子表失败", exc_info=True)


def _create_secondary_tables() -> None:
    """补建「第二套 declarative Base」（database.db.Base）注册的表。

    历史原因项目里存在两个 declarative_base：
      - utils.database.Base：users / courses 等主业务表
      - database.db.Base：achievements / leaderboard / content_store 等
    首启空库时必须两套都 create_all，否则安装包不再携带 ai_service.db 后，
    成就 / 排行榜等页面会因表缺失直接 500。
    """
    try:
        from database.db import Base as LegacyBase
    except Exception:
        logger.warning("导入 database.db.Base 失败，跳过副表创建", exc_info=True)
        return

    _import_secondary_models()
    _register_users_shadow(LegacyBase)

    try:
        LegacyBase.metadata.create_all(bind=sync_engine)
    except Exception:
        # 副表建不出来不应阻断主流程（主业务表与种子数据更重要）
        logger.warning("副表创建失败（不阻断启动）", exc_info=True)


async def _bootstrap_database_async() -> dict:
    """建表 + 首启种子（同一事件循环内完成，避免 async engine 跨 loop）。"""
    from scripts.seed_initial_data import seed_initial_data
    from utils.database import close_db, create_db_and_tables

    try:
        await create_db_and_tables()
    except Exception:
        # 完整模型清单导入失败时回退到「已注册模型」建表，保证库文件与核心表存在
        logger.warning(
            "create_db_and_tables 失败，回退 Base.metadata.create_all", exc_info=True
        )
        Base.metadata.create_all(bind=sync_engine)

    _create_secondary_tables()

    report = await seed_initial_data()
    # 释放本 loop 内建立的连接，交给 uvicorn 自己的事件循环重新建连
    await close_db()
    return report


def _init_database() -> None:
    """应用启动前的数据库初始化（幂等；失败不阻断启动）。"""
    try:
        # 先导入种子模块：它显式 import 了内容相关 ORM 模型，
        # 保证 create_all 能覆盖 courses / course_lessons 等表。
        import scripts.seed_initial_data  # noqa: F401
    except Exception:
        logger.warning("导入种子模块失败（继续建表）", exc_info=True)

    try:
        report = asyncio.run(_bootstrap_database_async())
        logger.info("数据库初始化完成，首启种子报告：%s", report)
    except Exception:
        # 空库也可用（用户可自行注册），因此不阻断启动
        logger.warning("数据库初始化失败（不阻断启动）", exc_info=True)


if __name__ == "__main__":
    _force_utf8_stdio()

    # 【修复】端口可由环境变量 PORT 覆盖（Electron 启动后端时会设置）
    backend_port = int(os.getenv("PORT", "8000"))
    print("=" * 80)
    print("AI-Edu-for-Kids Backend Starting...")
    print("=" * 80)
    print(f"\n  API Docs: http://localhost:{backend_port}/docs")
    print("\n  Tips:")
    print("   - Press Ctrl+C to stop")
    print(f"   - Port: {backend_port} (from PORT env var or default 8000)")
    print("=" * 80)

    # 启动时创建数据库表 + 首启种子数据（在 __main__ 中执行，避免阻塞模块导入）
    _init_database()

    uvicorn.run(app, host="0.0.0.0", port=backend_port)
