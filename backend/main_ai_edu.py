"""
AI-Edu-for-Kids 简化版后端服务

只包含 AI-Edu 相关的功能，避免其他模块的依赖问题
"""

from routes.vircadia_avatar_routes import router as vircadia_avatar_router
from routes.token_routes import router as token_router
from routes.recommendation_routes import router as recommendation_router
from routes.micro_course_routes import router as micro_course_router
from routes.llm_assistant_routes import router as llm_assistant_router
from routes.leaderboard_routes import router as leaderboard_router
from routes.error_log_routes import router as error_log_router
from routes.creativity_routes import router as creativity_router
# 【P1-Backend 修复 #1】补齐 arvr_course_routes：前端 ARVRCoursePlayerComponent 调用
#   /api/v1/arvr-courses/{id}，原 routes/ar_vr_routes.py 提供的路径是 /api/v1/org/{org_id}/arvr/*，
#   前端调用 404 → ARVR 课程 502。补齐后 ARVR 课程可正常加载。
from routes.arvr_course_routes import router as arvr_course_router
# 【P1-Backend 修复 #2】补齐 org_error_log_routes：前端 ErrorLoggerService 调用
#   /api/v1/org/{org_id}/logs/error，原 routes/error_log_routes.py 提供的路径是 /logs/error（无 org_id 前缀），
#   前端调用 404 → ErrorLoggerService 上报失败。补齐后前端错误可正常上报。
from routes.org_error_log_routes import router as org_error_log_router
# 【P1-Admin 补齐】注册 Admin AR/VR 课程管理路由
#   提供后台课程 CRUD / 上传 / 编辑 / 删除能力，路径 /api/v1/admin/arvr/*，
#   需要 Bearer JWT + admin 角色才能访问。
from routes.admin_arvr_routes import router as admin_arvr_router
# 协作文档模块因编码问题暂未修复，后续处理
# from routes.collaboration_routes import (
#     discussion_router,
#     document_router,
#     group_router,
#     project_router,
# )
from routes.ai_edu_websocket_routes import router as ai_edu_websocket_router
from routes.ai_edu_quiz_routes import router as ai_edu_quiz_router
from routes.ai_edu_progress_routes import router as ai_edu_progress_router
from routes.ai_edu_code_execution import router as ai_edu_code_router
from routes.achievement_routes import router as achievement_router
# 【P1 修复 #P1-2】补充 exam_router 注册：在线测验模块
#   main_ai_edu.py 原版未注册 exam_routes，导致 /api/v1/exams 返回 404
#   前端 ExamListComponent 会显示“服务器错误”，UX 完整度测试中标记为 P1。
from routes.exam_routes import router as exam_router
# 【修复 #10】补充 auth_router 注册：main_ai_edu.py 原版未包含认证路由，
#   导致 /api/v1/auth/signin 返回 404，前端登录失败。
#   auth_routes 依赖为 iMato 标准库（bcrypt、jose、sqlalchemy 等），与现有后端环境兼容。
from routes.auth_routes import router as auth_router
# 【修复 #11】补充 system_status_router 注册：底部状态栏轮询
#   /api/v1/system/health-detail 和 /api/v1/system/modules 依赖此 router。
#   缺失则 404 → catchError → healthy$.next(false) → 状态栏显示"后端未启动"。
from routes.system_status_routes import router as system_status_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn

from utils.database import Base, sync_engine

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


if __name__ == "__main__":
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

    # 启动时创建数据库表（在 __main__ 中执行，避免阻塞模块导入）
    Base.metadata.create_all(bind=sync_engine)

    uvicorn.run(app, host="0.0.0.0", port=backend_port)
