"""
Exam Routes - 测验系统 API 端点

提供完整的在线测验功能：
- 测验 CRUD（创建/读取/更新/删除）
- 题目管理
- 考试流程（开始/提交/评分）
- 防作弊事件上报
- 成绩查询与统计
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from middleware.auth import get_current_user
from models.exam import ExamStatus, AttemptStatus
from models.user import User
from services.anti_cheat_service import anti_cheat_service
from services.exam_service import exam_service
from utils.database import get_db

router = APIRouter(prefix="/api/v1/exams", tags=["测验系统"])


# ============ Request/Response Models ============


class ExamCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    course_id: int | None = None
    difficulty: str = "medium"
    duration_minutes: int = 30
    start_time: str | None = None
    end_time: str | None = None
    passing_score: float = 60.0
    max_attempts: int = 1
    shuffle_questions: bool = True
    shuffle_options: bool = True
    show_result_immediately: bool = False
    anti_cheat_enabled: bool = True
    max_screen_switches: int = 3
    min_answer_seconds: int = 3
    restrict_paste: bool = True
    restrict_copy: bool = True
    fullscreen_required: bool = True


class ExamUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    difficulty: str | None = None
    status: str | None = None
    duration_minutes: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    passing_score: float | None = None
    shuffle_questions: bool | None = None
    anti_cheat_enabled: bool | None = None


class QuestionCreate(BaseModel):
    question_type: str = Field(..., pattern=r"^(single_choice|multiple_choice|true_false|short_answer|coding)$")
    title: str = Field(..., min_length=1)
    description: str | None = None
    options: list | None = None
    correct_answer: str | None = None
    score: float = 10.0
    explanation: str | None = None
    tags: list[str] | None = None
    difficulty: str = "medium"


class CheatEventReport(BaseModel):
    cheat_type: str
    details: dict | None = None
    severity: int = 1


class SubmitAnswers(BaseModel):
    answers: dict


class GradeRequest(BaseModel):
    scores: dict[str, float]
    notes: str | None = None


# ============ 测验 CRUD ============


@router.post("", summary="创建测验")
async def create_exam(
    exam_data: ExamCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新测验"""
    exam = await exam_service.create_exam(
        db=db, exam_data=exam_data.model_dump(), creator_id=current_user.id
    )
    return exam.to_dict()


@router.get("", summary="获取测验列表")
async def list_exams(
    status: str | None = Query(None),
    course_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """获取测验列表（支持筛选和分页）"""
    exams, total = await exam_service.get_exams(
        db=db, status=status, course_id=course_id, page=page, page_size=page_size
    )
    return {
        "exams": [e.to_dict() for e in exams],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{exam_id}", summary="获取测验详情")
async def get_exam(
    exam_id: int,
    include_answers: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """获取测验详情（包含题目列表）"""
    exam = await exam_service.get_exam(db=db, exam_id=exam_id)
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测验不存在")

    questions = await exam_service.get_questions(
        db=db, exam_id=exam_id, include_answers=include_answers
    )

    return {
        **exam.to_dict(),
        "questions": [q.to_dict(include_answer=include_answers) for q in questions],
    }


@router.put("/{exam_id}", summary="更新测验")
async def update_exam(
    exam_id: int,
    exam_data: ExamUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新测验信息"""
    exam = await exam_service.update_exam(
        db=db, exam_id=exam_id, exam_data=exam_data.model_dump(exclude_none=True)
    )
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测验不存在")
    return exam.to_dict()


@router.delete("/{exam_id}", summary="删除测验")
async def delete_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除测验及其所有关联数据"""
    success = await exam_service.delete_exam(db=db, exam_id=exam_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测验不存在")
    return {"message": "删除成功"}


@router.post("/{exam_id}/publish", summary="发布测验")
async def publish_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """发布测验（学生可见并可开始考试）"""
    exam = await exam_service.update_exam(
        db=db, exam_id=exam_id, exam_data={"status": ExamStatus.PUBLISHED.value}
    )
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测验不存在")
    return {"message": "发布成功", "exam": exam.to_dict()}


# ============ 题目管理 ============


@router.post("/{exam_id}/questions", summary="添加题目")
async def add_question(
    exam_id: int,
    question_data: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """向测验添加题目"""
    question = await exam_service.add_question(
        db=db, exam_id=exam_id, question_data=question_data.model_dump()
    )
    return question.to_dict(include_answer=True)


@router.put("/questions/{question_id}", summary="更新题目")
async def update_question(
    question_id: int,
    question_data: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新题目"""
    question = await exam_service.update_question(
        db=db, question_id=question_id, question_data=question_data.model_dump()
    )
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
    return question.to_dict(include_answer=True)


@router.delete("/questions/{question_id}", summary="删除题目")
async def delete_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除题目"""
    success = await exam_service.delete_question(db=db, question_id=question_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
    return {"message": "删除成功"}


# ============ 考试流程 ============


@router.post("/{exam_id}/start", summary="开始考试")
async def start_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    request=None,
    db: AsyncSession = Depends(get_db),
):
    """开始考试，返回答题记录"""
    try:
        ip_address = request.client.host if request else None if hasattr(request, 'client') else None
    except Exception:
        ip_address = None

    attempt = await exam_service.start_exam(
        db=db,
        exam_id=exam_id,
        user_id=current_user.id,
        ip_address=ip_address,
    )
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="测验不存在")

    # 获取题目（不含答案）
    questions = await exam_service.get_questions(db=db, exam_id=exam_id, include_answers=False)

    return {
        "attempt_id": attempt.id,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "questions": [q.to_dict(include_answer=False) for q in questions],
    }


@router.post("/attempts/{attempt_id}/submit", summary="提交答案")
async def submit_exam(
    attempt_id: int,
    submit_data: SubmitAnswers,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交考试答案"""
    try:
        attempt = await exam_service.submit_exam(
            db=db, attempt_id=attempt_id, answers=submit_data.answers, user_id=current_user.id
        )
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="答题记录不存在")
        return attempt.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/attempts/{attempt_id}/grade", summary="人工评分")
async def grade_exam(
    attempt_id: int,
    grade_data: GradeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """人工评分（主观题评分）"""
    attempt = await exam_service.grade_subjective(
        db=db,
        attempt_id=attempt_id,
        grader_id=current_user.id,
        scores=grade_data.scores,
        notes=grade_data.notes,
    )
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="答题记录不存在")
    return attempt.to_dict()


# ============ 防作弊 ============


@router.post("/attempts/{attempt_id}/heartbeat", summary="防作弊心跳上报")
async def cheat_heartbeat(
    attempt_id: int,
    event_data: CheatEventReport,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """防作弊心跳上报，前端定期发送"""
    event = await anti_cheat_service.report_cheat_event(
        db=db,
        attempt_id=attempt_id,
        cheat_type=event_data.cheat_type,
        details=event_data.details,
        severity=event_data.severity,
    )
    return {"event_id": event.id, "severity": event.severity, "timestamp": event.timestamp.isoformat() if event.timestamp else None}


@router.get("/{exam_id}/cheat-summary", summary="防作弊统计摘要")
async def exam_cheat_summary(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取测验防作弊统计"""
    summary = await anti_cheat_service.get_exam_cheat_summary(db=db, exam_id=exam_id)
    return summary


# ============ 成绩查询 ============


@router.get("/attempts/{attempt_id}", summary="获取答题记录详情")
async def get_attempt(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取答题记录详情"""
    attempt = await exam_service.get_attempt(db=db, attempt_id=attempt_id)
    if not attempt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="答题记录不存在")

    result = attempt.to_dict()
    # 包含答案详情
    result["answers"] = attempt.answers
    result["cheat_events"] = [e.to_dict() for e in (attempt.cheat_events or [])]
    return result


@router.get("/{exam_id}/my-attempts", summary="获取我的答题记录")
async def my_attempts(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户在某个测验的答题记录列表"""
    attempts = await exam_service.get_user_attempts(
        db=db, exam_id=exam_id, user_id=current_user.id
    )
    return {"attempts": [a.to_dict() for a in attempts]}


@router.get("/{exam_id}/statistics", summary="测验统计数据")
async def exam_statistics(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取测验统计数据（平均分、通过率等）"""
    stats = await exam_service.get_exam_statistics(db=db, exam_id=exam_id)
    return stats
