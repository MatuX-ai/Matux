"""
AI-Edu-for-Kids 完整版后端服务

集成完整的学习进度 API 路由，支持实际的数据库操作
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
import uvicorn

# 导入独立的 AI-Edu 模型
from models.ai_edu_models import (
    AIEduDatabaseManager,
    AIEduLearningProgress,
    AIEduLesson,
    AIEduModule,
    AIEduPointsTransaction,
    get_ai_edu_db,
)

# 创建数据库引擎
db_path = Path(__file__).parent.parent / "data" / "ai_edu_standalone.db"
database_url = f"sqlite:///{db_path}"
engine = create_engine(database_url)


def get_db():
    """获取 AI-Edu 数据库管理器"""
    return get_ai_edu_db()


# 创建 FastAPI 应用
app = FastAPI(
    title="AI-Edu-for-Kids API",
    description="AI 教育课程学习平台 API - 完整版",
    version="2.0.0",
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
    return {"service": "AI-Edu-for-Kids API", "version": "2.0.0", "status": "running"}


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# ==================== 课程模块相关 API ====================


@app.get("/api/v1/org/{org_id}/ai-edu/modules")
async def get_modules(org_id: int, db: AIEduDatabaseManager = Depends(get_db)):
    """获取所有可用的课程模块"""
    try:
        modules = db.get_all_modules(active_only=True)

        return {"success": True, "data": modules, "count": len(modules)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/org/{org_id}/ai-edu/modules/{module_id}/lessons")
async def get_module_lessons(
    org_id: int, module_id: int, db: AIEduDatabaseManager = Depends(get_db)
):
    """获取指定模块的所有课时"""
    try:
        # 检查模块是否存在
        module = db.get_module_by_id(module_id)
        if not module:
            raise HTTPException(status_code=404, detail="Module not found")

        lessons = db.get_lessons_by_module(module_id, active_only=True)

        return {"success": True, "data": lessons, "count": len(lessons)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 学习进度相关 API ====================


@app.get("/api/v1/org/{org_id}/ai-edu/progress")
async def get_user_progress(
    org_id: int,
    lesson_id: Optional[int] = Query(None, description="指定课时 ID"),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(1, description="用户 ID (临时)"),
):
    """获取用户的学习进度"""
    try:
        # 构建查询条件
        stmt = select(AIEduLearningProgress).where(
            AIEduLearningProgress.user_id == user_id
        )

        if lesson_id:
            stmt = stmt.where(AIEduLearningProgress.lesson_id == lesson_id)

        result = db.execute(stmt)
        progresses = result.scalars().all()

        return {
            "success": True,
            "data": [
                {
                    "progress_id": progress.id,
                    "lesson_id": progress.lesson_id,
                    "progress_percentage": progress.progress_percentage,
                    "status": progress.status,
                    "time_spent_seconds": progress.time_spent_seconds,
                    "quiz_score": progress.quiz_score,
                    "code_quality_score": progress.code_quality_score,
                    "last_accessed_time": (
                        progress.last_accessed_time.isoformat()
                        if progress.last_accessed_time
                        else None
                    ),
                }
                for progress in progresses
            ],
            "count": len(progresses),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/org/{org_id}/ai-edu/progress")
async def update_learning_progress(
    org_id: int,
    request_data: Dict[str, Any],
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(1, description="用户 ID (临时)"),
):
    """更新学习进度"""
    try:
        lesson_id = request_data.get("lesson_id")
        progress_data = {
            "progress_percentage": request_data.get("progress_percentage", 0),
            "time_spent_seconds": request_data.get("time_spent_seconds", 0),
            "quiz_score": request_data.get("quiz_score"),
            "code_quality_score": request_data.get("code_quality_score"),
            "status": request_data.get("status", "in_progress"),
        }

        # 查找或创建进度记录
        stmt = select(AIEduLearningProgress).where(
            AIEduLearningProgress.user_id == user_id,
            AIEduLearningProgress.lesson_id == lesson_id,
        )
        result = db.execute(stmt)
        progress = result.scalar_one_or_none()

        if not progress:
            # 创建新进度记录
            from datetime import datetime

            progress = AIEduLearningProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                progress_percentage=progress_data["progress_percentage"],
                status=progress_data["status"],
                time_spent_seconds=progress_data["time_spent_seconds"],
                quiz_score=progress_data["quiz_score"],
                code_quality_score=progress_data["code_quality_score"],
                start_time=datetime.utcnow(),
                last_accessed_time=datetime.utcnow(),
            )
            db.add(progress)
        else:
            # 更新现有进度
            for key, value in progress_data.items():
                if value is not None:
                    setattr(progress, key, value)
            progress.last_accessed_time = __import__("datetime").datetime.utcnow()

        db.commit()
        db.refresh(progress)

        return {
            "success": True,
            "data": {
                "progress_id": progress.id,
                "lesson_id": progress.lesson_id,
                "progress_percentage": progress.progress_percentage,
                "status": progress.status,
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/org/{org_id}/ai-edu/progress/statistics")
async def get_progress_statistics(
    org_id: int,
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(1, description="用户 ID (临时)"),
):
    """获取学习进度统计信息"""
    try:
        # 查询用户的所有进度
        stmt = select(AIEduLearningProgress).where(
            AIEduLearningProgress.user_id == user_id
        )
        result = db.execute(stmt)
        progresses = result.scalars().all()

        # 计算统计数据
        total_courses = len(progresses)
        completed_courses = sum(1 for p in progresses if p.status == "completed")
        in_progress_courses = sum(1 for p in progresses if p.status == "in_progress")
        not_started_courses = sum(1 for p in progresses if p.status == "not_started")

        total_time_seconds = sum(p.time_spent_seconds or 0 for p in progresses)
        total_time_hours = round(total_time_seconds / 3600, 2)

        # 计算平均分数
        quiz_scores = [p.quiz_score for p in progresses if p.quiz_score is not None]
        code_scores = [
            p.code_quality_score for p in progresses if p.code_quality_score is not None
        ]

        average_quiz_score = (
            round(sum(quiz_scores) / len(quiz_scores), 2) if quiz_scores else 0
        )
        average_code_score = (
            round(sum(code_scores) / len(code_scores), 2) if code_scores else 0
        )

        # 计算总积分
        points_stmt = select(AIEduPointsTransaction).where(
            AIEduPointsTransaction.user_id == user_id
        )
        points_result = db.execute(points_stmt)
        transactions = points_result.scalars().all()
        total_points = sum(
            t.final_points for t in transactions if t.transaction_type == "earn"
        )

        # 计算完成率
        completion_rate = (
            round((completed_courses / total_courses * 100), 2)
            if total_courses > 0
            else 0
        )

        return {
            "success": True,
            "data": {
                "total_courses": total_courses,
                "completed_courses": completed_courses,
                "in_progress_courses": in_progress_courses,
                "not_started_courses": not_started_courses,
                "total_time_hours": total_time_hours,
                "average_quiz_score": average_quiz_score,
                "average_code_score": average_code_score,
                "total_points": total_points,
                "completion_rate": completion_rate,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 课程完成相关 API ====================


@app.post("/api/v1/org/{org_id}/ai-edu/progress/complete")
async def complete_lesson(
    org_id: int,
    request_data: Dict[str, Any],
    db: Session = Depends(get_db),
    user_id: Optional[int] = Query(1, description="用户 ID (临时)"),
):
    """完成课程并获得积分奖励"""
    try:
        from datetime import datetime

        lesson_id = request_data.get("lesson_id")
        quiz_score = request_data.get("quiz_score", 0)
        code_quality_score = request_data.get("code_quality_score", 0)
        time_spent_seconds = request_data.get("time_spent_seconds", 0)

        # 获取课时信息
        stmt = select(AIEduLesson).where(AIEduLesson.id == lesson_id)
        result = db.execute(stmt)
        lesson = result.scalar_one_or_none()

        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        # 计算积分奖励
        base_points = lesson.base_points or 20

        # 质量系数
        quality_score = max(quiz_score, code_quality_score)
        if quality_score >= 90:
            quality_multiplier = 1.2
        elif quality_score >= 80:
            quality_multiplier = 1.1
        else:
            quality_multiplier = 1.0

        quality_bonus = int(base_points * (quality_multiplier - 1))

        # 时间奖励
        time_bonus = 0
        if lesson.estimated_duration_minutes:
            standard_seconds = lesson.estimated_duration_minutes * 60
            if time_spent_seconds < standard_seconds:
                time_saved = standard_seconds - time_spent_seconds
                time_bonus = int(time_saved / 60 * 0.5)

        # 总积分
        total_points = int(base_points * quality_multiplier) + time_bonus

        # 更新学习进度为完成状态
        stmt = select(AIEduLearningProgress).where(
            AIEduLearningProgress.user_id == user_id,
            AIEduLearningProgress.lesson_id == lesson_id,
        )
        result = db.execute(stmt)
        progress = result.scalar_one_or_none()

        if progress:
            progress.status = "completed"
            progress.progress_percentage = 100
            progress.completion_time = datetime.utcnow()
            if quiz_score:
                progress.quiz_score = quiz_score
            if code_quality_score:
                progress.code_quality_score = code_quality_score
        else:
            progress = AIEduLearningProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                status="completed",
                progress_percentage=100,
                quiz_score=quiz_score,
                code_quality_score=code_quality_score,
                time_spent_seconds=time_spent_seconds,
                completion_time=datetime.utcnow(),
                start_time=datetime.utcnow(),
                last_accessed_time=datetime.utcnow(),
            )
            db.add(progress)

        # 创建积分交易记录
        transaction = AIEduPointsTransaction(
            user_id=user_id,
            transaction_type="earn",
            points_amount=total_points,
            source_type="course_completion",
            source_id=lesson_id,
            base_points=base_points,
            quality_bonus=quality_bonus,
            streak_bonus=time_bonus,
            final_points=total_points,
            status="completed",
            transaction_time=datetime.utcnow(),
        )
        db.add(transaction)

        db.commit()

        return {
            "success": True,
            "points_earned": total_points,
            "message": f"恭喜完成课程！获得{total_points}积分奖励",
            "breakdown": {
                "base_points": base_points,
                "quality_bonus": quality_bonus,
                "time_bonus": time_bonus,
                "total": total_points,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("=" * 80)
    print("AI-Edu-for-Kids 完整版后端服务启动中...")
    print("=" * 80)
    print("\n📌 访问以下地址查看 API 文档:")
    print("   http://localhost:8000/docs")
    print("\n💡 可用端点:")
    print("   GET  /api/v1/org/{org_id}/ai-edu/modules          # 获取模块列表")
    print("   GET  /api/v1/org/{org_id}/ai-edu/modules/{id}/lessons  # 获取课时列表")
    print("   GET  /api/v1/org/{org_id}/ai-edu/progress         # 获取学习进度")
    print("   POST /api/v1/org/{org_id}/ai-edu/progress         # 更新学习进度")
    print("   GET  /api/v1/org/{org_id}/ai-edu/progress/statistics # 获取统计")
    print("   POST /api/v1/org/{org_id}/ai-edu/progress/complete # 完成课程")
    print("\n🔧 提示:")
    print("   - 按 Ctrl+C 停止服务")
    print("   - 默认端口：8000")
    print("   - 使用 SQLite 数据库：data/ai_edu_standalone.db")
    print("=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=8000)
