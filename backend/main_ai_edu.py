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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from utils.database import Base, sync_engine

# 创建 FastAPI 应用
app = FastAPI(
    title="AI-Edu-for-Kids API", description="AI 教育课程学习平台 API", version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
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
    print("=" * 80)
    print("AI-Edu-for-Kids Backend Starting...")
    print("=" * 80)
    print("\n  API Docs: http://localhost:8000/docs")
    print("\n  Tips:")
    print("   - Press Ctrl+C to stop")
    print("   - Default port: 8000")
    print("=" * 80)

    # 启动时创建数据库表（在 __main__ 中执行，避免阻塞模块导入）
    Base.metadata.create_all(bind=sync_engine)

    uvicorn.run(app, host="0.0.0.0", port=8000)
