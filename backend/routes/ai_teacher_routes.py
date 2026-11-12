"""
AI 个性化教师 API 路由

基于 PRD F-08-AI 设计，提供：
- 学生学习画像 CRUD
- 上下文记忆管理（长期 + 会话）
- AI 教师对话（画像注入 + 记忆检索 + 人格配置）
- 成长轨迹查询
- 智能教学建议
- AI 教师人格配置
- 知识状态查询
"""

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from datetime import datetime
import logging
import os
from typing import Any, Dict, List, Optional

from cache.ai_teacher_persistence import (
    get_memories_repo,
    get_personas_repo,
    get_profiles_repo,
    get_sessions_repo,
)
from config.settings import settings
from fastapi import APIRouter, Depends, HTTPException, Query
from middleware.auth import get_current_user
from models.user import User
from pydantic import BaseModel, Field
from services.ai_teacher_event_bus import ai_teacher_live_bus  # 【P3-B】
from services.ai_teacher_live_settings import ai_teacher_live_settings  # 【P3-B】

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai-teacher", tags=["AI 个性化教师"])

# 【P0-3 合规】当前 /chat 仍是规则模板回复（尚未接入 LLM），
# 因此回复来源标记为 mock —— 前端据此显示「离线模式」角标。
CHAT_MODEL_NAME = "mock-ai-teacher"


def _build_session_entries(user_message: str, assistant_reply: str) -> List[Dict[str, Any]]:
    """构造会话条目（【P0-3 合规】默认不落盘对话原文）。

    ``AI_LLM_STORE_CONVERSATION`` 默认 False —— 会话文件只保留
    角色 / 长度 / 时间戳等元数据，不写学生提问与 AI 回复原文
    （1.0.2-release-criteria G1-d / G1-e）。
    """
    now = datetime.now().isoformat()
    if settings.AI_LLM_STORE_CONVERSATION:
        return [
            {"role": "user", "content": user_message, "timestamp": now},
            {"role": "assistant", "content": assistant_reply, "timestamp": now},
        ]
    return [
        {"role": "user", "content_length": len(user_message), "timestamp": now},
        {
            "role": "assistant",
            "content_length": len(assistant_reply),
            "timestamp": now,
        },
    ]


# ==================== 【P0-B 修复】RAG 检索超时保护 ====================
# 背景：/chat 里的 RAG 检索会懒加载 sentence-transformers / text2vec 模型，
#   首次调用会去 huggingface.co 下载权重。桌面端/离线环境下外网不可达，
#   下载每个文件重试 5 × 10s，导致 POST /chat 卡 60s+ 最终超时（前端只看到永远 loading）。
# 策略：单 worker 线程池 + 3s 超时；一旦超时/异常就置 disabled，
#   后续请求直接跳过 RAG（回到纯占位回复），不再阻塞对话。
_RAG_TIMEOUT_SEC = float(os.getenv("AI_TEACHER_RAG_TIMEOUT_SEC", "3"))
_RAG_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ai-teacher-rag")
_RAG_STATE: Dict[str, bool] = {"disabled": False}


def _rag_worker(message: str, user_id: str, profile_seed: str):
    """在工作线程中完成懒加载 + 检索（get_* 本身也可能触发模型加载）。"""
    from services.vector_knowledge_service import get_vector_knowledge_service

    service = get_vector_knowledge_service()
    return service.rag_retrieve(
        query=message,
        user_id=user_id,
        profile_seed=profile_seed,
    )


def _try_rag_context(message: str, user_id: str, profile_seed: str):
    """尝试 RAG 检索；超时或不可用时返回空上下文，不影响对话主流程。

    注意：get_vector_knowledge_service() 会在首次调用时懒加载 embedding 模型
    （离线环境会去 huggingface 下载并长时间阻塞），因此必须把它一起放进
    工作线程，否则超时机制形同虚设。
    """
    if _RAG_STATE["disabled"]:
        return "", False
    try:
        future = _RAG_EXECUTOR.submit(_rag_worker, message, user_id, profile_seed)
        result = future.result(timeout=_RAG_TIMEOUT_SEC)
        return result.context, result.total_score > 0
    except FuturesTimeoutError:
        _RAG_STATE["disabled"] = True
        logger.warning(
            "RAG 检索超时（>%ss，模型可能正在下载），已禁用后续检索",
            _RAG_TIMEOUT_SEC,
        )
        return "", False
    except Exception as exc:  # noqa: BLE001 - RAG 任何异常都不应阻断对话
        _RAG_STATE["disabled"] = True
        logger.warning("RAG 检索不可用，已禁用后续检索: %s", exc)
        return "", False


# ==================== Pydantic 模型 ====================

class WeakPointModel(BaseModel):
    knowledge_point: str
    mastery: float = Field(ge=0, le=1)
    error_rate: float = Field(ge=0, le=1)
    suggestion: str
    last_detected: str


class AttentionProfileModel(BaseModel):
    average_focus_duration_minutes: float
    tab_switch_frequency: float
    hesitation_time_ms: float
    trend: str = "stable"


class EmotionLogModel(BaseModel):
    timestamp: str
    emotion: str
    source: str
    confidence: float = Field(ge=0, le=1)


class LearningMilestoneModel(BaseModel):
    id: str
    type: str
    title: str
    description: str
    achieved_at: str
    metadata: Optional[Dict[str, Any]] = None


class SkillTreeNodeModel(BaseModel):
    id: str
    name: str
    category: str
    progress: float = Field(ge=0, le=1)
    status: str
    children: Optional[List["SkillTreeNodeModel"]] = None
    parent: Optional[str] = None
    unlock_requirement: Optional[str] = None


class AbilityDimensionsModel(BaseModel):
    programming_thinking: int = Field(ge=0, le=100)
    algorithm_ability: int = Field(ge=0, le=100)
    debugging_skill: int = Field(ge=0, le=100)
    project_practice: int = Field(ge=0, le=100)
    stem_experiment: int = Field(ge=0, le=100)
    code_quality: int = Field(ge=0, le=100)
    independent_completion: int = Field(ge=0, le=100)
    question_quality: int = Field(ge=0, le=100)


class LearningProfileResponse(BaseModel):
    user_id: str
    display_name: str
    grade_level: str
    age_group: str
    learning_style: str
    preferred_content_type: str
    ability_dimensions: AbilityDimensionsModel
    interest_preferences: List[str]
    knowledge_mastery: Dict[str, float]
    total_study_time_minutes: int
    completed_courses_count: int
    average_quiz_score: float
    current_streak_days: int
    longest_streak_days: int
    weak_points: List[WeakPointModel]
    error_patterns: Dict[str, int]
    attention_profile: AttentionProfileModel
    emotional_states: List[EmotionLogModel]
    learning_milestones: List[LearningMilestoneModel]
    skill_tree: List[SkillTreeNodeModel]
    persona_seed: str
    learning_goals: List[str]
    created_at: str
    updated_at: str


class LearningProfileUpdateRequest(BaseModel):
    weak_points: Optional[List[WeakPointModel]] = None
    error_patterns: Optional[Dict[str, int]] = None
    attention_profile: Optional[AttentionProfileModel] = None
    emotional_states: Optional[List[EmotionLogModel]] = None
    learning_milestones: Optional[List[LearningMilestoneModel]] = None
    skill_tree: Optional[List[SkillTreeNodeModel]] = None
    ability_dimensions: Optional[AbilityDimensionsModel] = None
    knowledge_mastery: Optional[Dict[str, float]] = None


class TeacherPersonaModel(BaseModel):
    user_id: str
    address_mode: str = "name"
    nickname: str = ""
    language_style: str = "lively"
    hint_level: str = "guided_thinking"
    encouragement_frequency: str = "moderate"
    strictness: str = "standard"
    emoji_usage: str = "moderate"


class ChatRequest(BaseModel):
    user_id: str
    message: str
    session_id: str
    profile_seed: Optional[str] = None
    persona: Optional[Dict[str, str]] = None
    context: Optional[Dict[str, str]] = None
    knowledge_context: Optional[str] = None  # RAG 检索上下文
    knowledge_sources: Optional[List[str]] = None  # RAG 知识来源


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    emotion_detected: str
    memories_referenced: List[str]
    knowledge_used: bool
    suggestions: List[Dict[str, Any]]
    model: str
    confidence: float
    inference_time_ms: int


class LongTermMemoryModel(BaseModel):
    id: str
    user_id: str
    category: str
    content: str
    tags: List[str]
    importance: float = Field(ge=0, le=1)
    created_at: str
    access_count: int
    last_accessed_at: str


class SaveMemoryRequest(BaseModel):
    category: str
    content: str
    tags: List[str]
    importance: float = Field(ge=0, le=1)


class KnowledgeStateItemModel(BaseModel):
    knowledge_point: str
    mastery: float = Field(ge=0, le=1)
    status: str
    prerequisites: List[str]
    next_topics: List[str]
    last_practiced: Optional[str]
    practice_count: int


class TeachingSuggestionModel(BaseModel):
    id: str
    diagnosis_type: str
    severity: str
    title: str
    description: str
    suggested_action: str
    related_knowledge_points: List[str]
    recommended_courses: List[str]
    created_at: str
    is_read: bool


class DailySuggestionModel(BaseModel):
    date: str
    greeting: str
    yesterday_review: str
    today_goals: List[str]
    weak_point_reminder: List[WeakPointModel]
    suggested_courses: List[Dict[str, str]]
    ai_message: str


class AbilityTrendPointModel(BaseModel):
    date: str
    programming_thinking: int
    algorithm_ability: int
    debugging_skill: int
    project_practice: int
    stem_experiment: int
    independent_completion: int


class GrowthTrajectoryResponse(BaseModel):
    user_id: str
    ability_trend: List[AbilityTrendPointModel]
    milestones: List[LearningMilestoneModel]
    ai_monthly_message: str
    statistics: Dict[str, Any]
    interest_evolution: List[Dict[str, Any]]


# ==================== Mock 数据 ====================
# 【P3-B 修复】从进程内 dict 迁移到持久化仓储（cache.ai_teacher_persistence）
# - 重启后画像 / 会话 / 记忆 / 人格 数据可恢复
# - 多进程部署时可共享（写竞争由仓储 RLock 保护）
# - P3-D 计划：迁移到 SQLAlchemy 模型

_profiles_repo = get_profiles_repo()
_sessions_repo = get_sessions_repo()
_memories_repo = get_memories_repo()
_personas_repo = get_personas_repo()


def _get_mock_profile(user_id: str) -> Dict[str, Any]:
    """获取或创建 mock 画像（持久化）"""
    existing = _profiles_repo.get(user_id)
    if existing is not None:
        return existing
    profile = {
        "user_id": user_id,
        "display_name": "小明",
        "grade_level": "G7",
        "age_group": "12-14",
        "learning_style": "visual",
        "preferred_content_type": "interactive",
        "ability_dimensions": {
            "programming_thinking": 68, "algorithm_ability": 45,
            "debugging_skill": 52, "project_practice": 60,
            "stem_experiment": 55, "code_quality": 40,
            "independent_completion": 65, "question_quality": 58,
        },
        "interest_preferences": ["game_development", "robotics", "3d_modeling"],
        "knowledge_mastery": {
            "python_basics": 0.85, "conditions": 0.90, "loops": 0.45,
            "functions": 0.0, "led_control": 1.0, "sensors": 0.45,
        },
        "total_study_time_minutes": 11220,
        "completed_courses_count": 23,
        "average_quiz_score": 72.5,
        "current_streak_days": 15,
        "longest_streak_days": 30,
        "weak_points": [
            {"knowledge_point": "range() 参数理解", "mastery": 0.55, "error_rate": 0.45,
             "suggestion": "Blockly 对照练习", "last_detected": datetime.now().isoformat()},
            {"knowledge_point": "缩进规范", "mastery": 0.70, "error_rate": 0.30,
             "suggestion": "代码格式化插件", "last_detected": datetime.now().isoformat()},
        ],
        "error_patterns": {"indentation_error": 12, "range_parameter": 8},
        "attention_profile": {
            "average_focus_duration_minutes": 25,
            "tab_switch_frequency": 2.3,
            "hesitation_time_ms": 4500,
            "trend": "stable",
        },
        "emotional_states": [
            {"timestamp": datetime.now().isoformat(), "emotion": "excited",
             "source": "dialogue", "confidence": 0.8},
        ],
        "learning_milestones": [
            {"id": "m1", "type": "first_blockly", "title": "初入编程",
             "description": "完成第一个 Blockly 关卡", "achieved_at": "2026-01-15T10:00:00Z"},
            {"id": "m2", "type": "python_intro", "title": "Python 入门",
             "description": "完成 Python 基础课程", "achieved_at": "2026-02-20T14:00:00Z"},
        ],
        "skill_tree": [
            {"id": "python_basics", "name": "Python 基础", "category": "python",
             "progress": 0.6, "status": "learning", "children": [
                {"id": "variables", "name": "变量与数据类型", "category": "python",
                 "progress": 1.0, "status": "mastered", "parent": "python_basics"},
                {"id": "loops", "name": "循环", "category": "python",
                 "progress": 0.6, "status": "learning", "parent": "python_basics"},
            ]},
        ],
        "persona_seed": "小明，G7，视觉型学习者，编程思维68/100",
        "learning_goals": ["掌握 Python 函数", "完成机器人项目"],
        "created_at": "2026-01-10T08:00:00Z",
        "updated_at": datetime.now().isoformat(),
    }
    # 【P3-B 修复】持久化
    _profiles_repo.set(user_id, profile)
    return profile


# ==================== 路由端点 ====================

@router.get("/profile/{user_id}", response_model=LearningProfileResponse)
async def get_learning_profile(user_id: str):
    """获取学生学习画像"""
    profile = _get_mock_profile(user_id)
    return profile


@router.patch("/profile/{user_id}", response_model=LearningProfileResponse)
async def update_learning_profile(user_id: str, update: LearningProfileUpdateRequest):
    """更新学习画像"""
    profile = _get_mock_profile(user_id)
    update_data = update.model_dump(exclude_none=True)
    profile.update(update_data)
    profile["updated_at"] = datetime.now().isoformat()
    # 【P3-B 修复】持久化
    _profiles_repo.set(user_id, profile)
    return profile


@router.get("/memory/{user_id}/long-term", response_model=List[LongTermMemoryModel])
async def get_long_term_memories(user_id: str, query: Optional[str] = None):
    """获取长期记忆"""
    existing = _memories_repo.get(user_id)
    if existing is None:
        existing = [
            {
                "id": "mem_1", "user_id": user_id, "category": "learning_summary",
                "content": "学生完成循环入门测验，for/while 正确率 60%",
                "tags": ["循环", "测验"], "importance": 0.8,
                "created_at": datetime.now().isoformat(),
                "access_count": 2, "last_accessed_at": datetime.now().isoformat(),
            }
        ]
        _memories_repo.set(user_id, existing)
    return existing


@router.post("/memory/{user_id}/long-term", response_model=LongTermMemoryModel)
async def save_long_term_memory(user_id: str, request: SaveMemoryRequest):
    """保存长期记忆"""
    memory = {
        "id": f"mem_{datetime.now().timestamp()}",
        "user_id": user_id,
        **request.model_dump(),
        "created_at": datetime.now().isoformat(),
        "access_count": 0,
        "last_accessed_at": datetime.now().isoformat(),
    }
    memories = _memories_repo.get(user_id, [])
    memories.append(memory)
    # 【P3-B 修复】持久化
    _memories_repo.set(user_id, memories)
    return memory


@router.get("/session/{user_id}")
async def get_session(user_id: str):
    """获取或创建会话"""
    existing = _sessions_repo.get(user_id)
    if existing is None:
        existing = {
            "sessionId": f"session_{datetime.now().timestamp()}",
            "userId": user_id,
            "recentMessages": [],
            "currentTask": None,
            "startedAt": datetime.now().isoformat(),
            "lastActivityAt": datetime.now().isoformat(),
        }
        _sessions_repo.set(user_id, existing)
    return existing


@router.post("/chat", response_model=ChatResponse)
async def chat_with_teacher(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """AI 教师对话（集成 RAG 知识检索）

    【P0-1 合规】端点强制 JWT 鉴权：未携带 / 携带无效 token 一律 401，
    不再允许本机任意进程匿名调用（1.0.2-release-criteria G1-b）。

    【P0-2 合规】``user_id`` 一律以 token 主体为准：客户端传入的 ``user_id``
    不参与任何授权判断，只用于归属校验（不一致 → 403），
    避免任何人冒用他人身份读写会话（1.0.2-release-criteria G1-c）。
    """
    start_time = datetime.now()

    # 【P0-2】user_id 从 token 主体取；客户端声明的 user_id 只做归属校验
    effective_user_id = str(current_user.id)
    claimed_user_id = (request.user_id or "").strip()
    if claimed_user_id and claimed_user_id != effective_user_id:
        raise HTTPException(
            status_code=403,
            detail="user_id 与当前登录用户不一致",
        )

    # 构建个性化回复
    persona = request.persona or {}
    profile_seed = request.profile_seed or ""
    address_mode = persona.get("address_mode", "name")

    # RAG 上下文注入
    knowledge_context = request.knowledge_context or ""
    knowledge_used = bool(knowledge_context)

    # 如果没有前端传入的 RAG 上下文，后端自行检索
    if not knowledge_context:
        knowledge_context, knowledge_used = _try_rag_context(
            request.message, effective_user_id, profile_seed
        )

    # 基于学生画像 + RAG 上下文生成个性化回复
    reply = _generate_personalized_reply(
        request.message, profile_seed, address_mode, persona,
        knowledge_context=knowledge_context,
    )

    # 更新会话（【P3-B 修复】持久化；【P0-3 合规】默认只落元数据）
    session = _sessions_repo.get(effective_user_id)
    if session is not None:
        session["recentMessages"].extend(
            _build_session_entries(request.message, reply)
        )
        session["recentMessages"] = session["recentMessages"][-20:]
        session["lastActivityAt"] = datetime.now().isoformat()
        _sessions_repo.set(effective_user_id, session)

    elapsed = (datetime.now() - start_time).total_seconds() * 1000

    # 【P0-3 合规】审计日志只记元数据，不记对话原文
    logger.info(
        "AI 教师对话完成：user_id=%s model=%s message_len=%d reply_len=%d "
        "elapsed_ms=%d knowledge_used=%s",
        effective_user_id,
        CHAT_MODEL_NAME,
        len(request.message),
        len(reply),
        int(elapsed),
        knowledge_used,
    )

    return ChatResponse(
        reply=reply,
        session_id=request.session_id,
        emotion_detected="neutral",
        memories_referenced=request.knowledge_sources or [],
        knowledge_used=knowledge_used,
        suggestions=[],
        model=CHAT_MODEL_NAME,
        confidence=0.85,
        inference_time_ms=int(elapsed),
    )


@router.get("/growth/{user_id}", response_model=GrowthTrajectoryResponse)
async def get_growth_trajectory(user_id: str, months: int = Query(default=6, ge=1, le=24)):
    """获取成长轨迹"""
    profile = _get_mock_profile(user_id)
    trend = []
    now = datetime.now()
    for i in range(months - 1, -1, -1):
        date = datetime(now.year, now.month - i, 1)
        factor = (months - i) / months
        trend.append({
            "date": date.strftime("%Y-%m"),
            "programming_thinking": int(30 + factor * 40),
            "algorithm_ability": int(15 + factor * 30),
            "debugging_skill": int(20 + factor * 35),
            "project_practice": int(25 + factor * 35),
            "stem_experiment": int(20 + factor * 35),
            "independent_completion": int(30 + factor * 35),
        })

    return GrowthTrajectoryResponse(
        user_id=user_id,
        ability_trend=trend,
        milestones=profile["learning_milestones"],
        ai_monthly_message="这个月你进步非常大！继续加油！💪",
        statistics={
            "totalStudyHours": 187,
            "completedCourses": 23,
            "completedProjects": 8,
            "totalQuestions": 156,
            "questionQualityTrend": "improving",
        },
        interest_evolution=[
            {"period": "2026-01", "interests": [{"name": "游戏开发", "percentage": 60}]},
            {"period": "2026-03", "interests": [
                {"name": "机器人", "percentage": 30},
                {"name": "游戏开发", "percentage": 50},
            ]},
            {"period": "2026-05", "interests": [
                {"name": "机器人", "percentage": 45},
                {"name": "游戏开发", "percentage": 35},
            ]},
        ],
    )


@router.get("/suggestions/{user_id}", response_model=List[TeachingSuggestionModel])
async def get_teaching_suggestions(user_id: str):
    """获取教学建议"""
    return [
        TeachingSuggestionModel(
            id="sug_1", diagnosis_type="prerequisite_missing", severity="warning",
            title="前置知识缺失", description="你正在学函数，但变量作用域还没掌握",
            suggested_action="先回顾变量作用域的概念",
            related_knowledge_points=["变量作用域", "函数"],
            recommended_courses=["python_scope_basics"],
            created_at=datetime.now().isoformat(), is_read=False,
        ),
        TeachingSuggestionModel(
            id="sug_2", diagnosis_type="concept_confusion", severity="info",
            title="概念混淆", description="你好像把 list 和 tuple 搞混了",
            suggested_action="对比练习：创建 list 和 tuple",
            related_knowledge_points=["list", "tuple"],
            recommended_courses=["python_data_structures"],
            created_at=datetime.now().isoformat(), is_read=False,
        ),
    ]


@router.patch("/suggestions/{suggestion_id}/read")
async def mark_suggestion_read(suggestion_id: str):
    """标记建议已读"""
    return {"success": True}


@router.get("/daily-suggestion/{user_id}", response_model=DailySuggestionModel)
async def get_daily_suggestion(user_id: str):
    """获取每日学习建议"""
    profile = _get_mock_profile(user_id)
    return DailySuggestionModel(
        date=datetime.now().strftime("%Y-%m-%d"),
        greeting=f"{profile['display_name']}，下午好！☀️",
        yesterday_review="昨天你完成了 Python 循环练习，正确率 75%！",
        today_goals=["完成循环进阶练习", "尝试用 for 循环写一个小程序", "复习 range() 的三种用法"],
        weak_point_reminder=profile["weak_points"],
        suggested_courses=[{"courseId": "python_loops_advanced", "reason": "刚学完循环基础，进阶课程是自然延伸"}],
        ai_message="💡 今日建议：先用 Blockly 搭 3 个循环积木，再翻译成 Python！",
    )


@router.get("/knowledge-state/{user_id}", response_model=List[KnowledgeStateItemModel])
async def get_knowledge_state(user_id: str):
    """获取知识状态"""
    return [
        KnowledgeStateItemModel(
            knowledge_point="python_basics", mastery=0.85, status="mastered",
            prerequisites=[], next_topics=["conditions", "loops"],
            last_practiced=datetime.now().isoformat(), practice_count=45,
        ),
        KnowledgeStateItemModel(
            knowledge_point="conditions", mastery=0.90, status="mastered",
            prerequisites=["python_basics"], next_topics=["loops"],
            last_practiced=datetime.now().isoformat(), practice_count=30,
        ),
        KnowledgeStateItemModel(
            knowledge_point="loops", mastery=0.45, status="learning",
            prerequisites=["conditions"], next_topics=["functions"],
            last_practiced=datetime.now().isoformat(), practice_count=18,
        ),
        KnowledgeStateItemModel(
            knowledge_point="functions", mastery=0.0, status="not_started",
            prerequisites=["loops"], next_topics=["oop"],
            last_practiced=None, practice_count=0,
        ),
    ]


@router.get("/persona/{user_id}", response_model=TeacherPersonaModel)
async def get_persona(user_id: str):
    """获取 AI 教师人格配置"""
    existing = _personas_repo.get(user_id)
    if existing is None:
        existing = {
            "user_id": user_id, "address_mode": "name", "nickname": "",
            "language_style": "lively", "hint_level": "guided_thinking",
            "encouragement_frequency": "moderate", "strictness": "standard",
            "emoji_usage": "moderate",
        }
        _personas_repo.set(user_id, existing)
    return existing


@router.patch("/persona/{user_id}", response_model=TeacherPersonaModel)
async def update_persona(user_id: str, persona: TeacherPersonaModel):
    """更新 AI 教师人格配置"""
    # 【P3-B 修复】持久化
    _personas_repo.set(user_id, persona.model_dump())
    return persona


@router.delete("/memory/{user_id}")
async def reset_memory(user_id: str):
    """重置 AI 教师记忆"""
    # 【P3-B 修复】持久化仓储支持按 key 删除
    _memories_repo.delete(user_id)
    _sessions_repo.delete(user_id)
    return {"success": True}


# ==================== 【P3-B】实时推送设置 + 事件历史 ====================


@router.get("/live-settings/{user_id}")
async def get_live_settings(user_id: str):
    """【P3-B】获取用户 AI 教师实时推送设置"""
    try:
        uid = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id 必须是整数")
    settings = ai_teacher_live_settings.get_settings(uid)
    return settings.to_dict()


@router.put("/live-settings/{user_id}")
async def update_live_settings(user_id: str, payload: Dict[str, Any]):
    """【P3-B】更新用户 AI 教师实时推送设置"""
    try:
        uid = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id 必须是整数")
    updated = ai_teacher_live_settings.update_settings(uid, payload or {})
    return updated.to_dict()


@router.get("/live-events/history/{user_id}")
async def get_live_events_history(
    user_id: str, limit: int = Query(default=20, ge=1, le=100)
):
    """【P3-B】获取最近 AI 教师实时事件历史（供前端断线后回放）"""
    try:
        uid = int(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="user_id 必须是整数")
    history = ai_teacher_live_bus.get_history(uid, limit=limit)
    return {"success": True, "data": history, "count": len(history)}


# ==================== 辅助函数 ====================

def _generate_personalized_reply(
    message: str, profile_seed: str, address_mode: str, persona: Dict[str, str],
    knowledge_context: str = "",
) -> str:
    """生成个性化回复（集成 RAG 知识上下文）"""
    language_style = persona.get("language_style", "lively")
    hint_level = persona.get("hint_level", "guided_thinking")
    emoji_usage = persona.get("emoji_usage", "moderate")

    emoji = "💡" if emoji_usage != "none" else ""
    address = "同学" if address_mode == "classmate" else "你"

    # 如果有 RAG 知识上下文，融入回复
    if knowledge_context:
        if "循环" in message or "loop" in message.lower():
            return (
                f"{address}，关于循环，我帮你找到了一些知识：{emoji}\n\n"
                f"{knowledge_context}\n\n"
                f"还记得你上次用动画学懂了条件判断吗？循环其实很像条件判断的重复版。"
                f"要不要先在 Blockly 里试试循环积木？"
            )
        return (
            f"{address}，这是个好问题！{emoji} 让我结合知识库帮你理清思路：\n\n"
            f"{knowledge_context}\n\n"
            f"你觉得从哪个角度来思考比较好呢？"
        )

    if "循环" in message or "loop" in message.lower():
        if hint_level == "direct_answer":
            return f"for 循环语法：for i in range(n): 其中 range(n) 生成 0 到 n-1 的序列。{emoji}"
        elif hint_level == "direction_only":
            return f"试试在 Blockly 里拖几个循环积木，然后看看生成的 Python 代码。{emoji}"
        else:
            return (
                f"{address}，循环是一个很重要的概念！{emoji} "
                f"还记得你上次用动画学懂了条件判断吗？循环其实很像条件判断的重复版。"
                f"要不要先在 Blockly 里试试循环积木，看看它和 Python 代码怎么对应？"
            )

    if "函数" in message or "function" in message.lower():
        if hint_level == "direct_answer":
            return f"函数定义语法：def function_name(parameters): 然后缩进写函数体。{emoji}"
        return f"{address}，函数就像一个打包好的工具箱，定义一次可以反复使用。{emoji} 你已经掌握了循环，函数是下一个自然步骤！"

    if "难" in message or "不会" in message:
        return (
            f"编程有时候确实让人头大，连我写了几百万行代码也会有这种感觉。{emoji} "
            f"咱们先把这个大问题拆成几个小步骤，一步步来？"
        )

    return f"{address}，这是个好问题！{emoji} 让我帮你理清思路，你觉得可以从哪个角度来思考呢？"
