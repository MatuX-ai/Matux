"""
AI-Edu-for-Kids 简化版后端服务

只包含 AI-Edu 相关的功能，避免其他模块的依赖问题
"""

import os

from core.router_registry import register_all_routers
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from utils.database import Base, sync_engine
import uvicorn

# 创建 FastAPI 应用
app = FastAPI(
    title="AI-Edu-for-Kids API", description="AI 教育课程学习平台 API", version="1.0.0"
)

# 【4a】路由注册收敛到 core.router_registry（单一事实源，issue #21）。
#
#   * mode="lazy"：本入口只注册「懒加载归属」与「两侧共用」的条目，
#     共 19 项 —— 18 项 active 实际注册，1 项 pending_integration 被跳过。
#   * pending_integration 条目在**导入前**即被判定并跳过，因此入口不再于
#     模块导入期硬引用路由模块。这修复了 origin/main 上
#     `ModuleNotFoundError: No module named 'services.ai_teacher_live_settings'`
#     导致的入口起不来（issue #26）。
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
