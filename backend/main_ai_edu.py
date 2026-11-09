"""
AI-Edu-for-Kids 简化版后端服务

只包含 AI-Edu 相关的功能，避免其他模块的依赖问题

【PR #68 合并目标版本 · 草案】以 origin/main 的注册表骨架为准，保留分支全部非路由改动：
  * 路由注册：统一走 core.router_registry.register_all_routers(mode="lazy")，
    丢弃分支手写的 25 个 include_router。
  * digital_twin（决策 2）与 share（决策 3）保持 Phase 2 启用，本入口不注册。
  * 非路由：保留分支的 --run-user-code 隐藏模式、UTF-8 stdio、副 Base 建表、
    首启种子初始化等全部桌面端修复。
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

from core.router_registry import register_all_routers
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# 【PR #68】路由注册收敛到 core.router_registry（单一事实源，issue #21）。
#
#   * mode="lazy"：本入口只注册「懒加载归属」与「两侧共用」的条目，共 24 项 ——
#     23 项 active 实际注册，1 项 pending_integration（ai_edu_websocket）被跳过。
#   * 桌面端此前手写 include 的路由（AI 教师 / 成就目录 / 课程目录 /
#     游戏化 WebSocket / OpenSciEDU）已全部登记入 ROUTER_TABLE，由本调用统一注册，
#     入口不再手写 include_router。
#   * digital_twin（决策 2）与 share（决策 3）保持 pending / 条件关闭，
#     Phase 2 再启用，本入口不注册。
#   * strict=False：注册失败按 L1 降级处理（写日志与报告，不阻断启动）；
#     连续失败达阈值的条目按 L2 熔断跳过。
register_all_routers(app, mode="lazy", strict=False)

# CORS 配置
# 【P1 修复 #13】环境变量驱动 + 合理默认值
# - 默认允许 4200 (Angular dev server) / 3000 (Webpack dev server) / 8080 (本地 UX 测试静态服务器)
# - 生产环境可通过环境变量 CORS_ALLOWED_ORIGINS 覆盖，逗号分隔，例如：
#   CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com
# - 开发环境允许本地任意 http://localhost:* 端口，方便不同端口调试
_default_dev_origins = [
    "http://localhost:4200",
    "http://localhost:3000",
    "http://localhost:8080",
]
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
