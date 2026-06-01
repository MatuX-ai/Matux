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

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai-teacher", tags=["AI 个性化教师"])


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

_mock_profiles: Dict[str, Dict[str, Any]] = {}
_mock_sessions: Dict[str, Dict[str, Any]] = {}
_mock_memories: Dict[str, List[Dict[str, Any]]] = {}
_mock_personas: Dict[str, Dict[str, str]] = {}


def _get_mock_profile(user_id: str) -> Dict[str, Any]:
    """获取或创建 mock 画像"""
    if user_id not in _mock_profiles:
        _mock_profiles[user_id] = {
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
    return _mock_profiles[user_id]


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
    _mock_profiles[user_id] = profile
    return profile


@router.get("/memory/{user_id}/long-term", response_model=List[LongTermMemoryModel])
async def get_long_term_memories(user_id: str, query: Optional[str] = None):
    """获取长期记忆"""
    if user_id not in _mock_memories:
        _mock_memories[user_id] = [
            {
                "id": "mem_1", "user_id": user_id, "category": "learning_summary",
                "content": "学生完成循环入门测验，for/while 正确率 60%",
                "tags": ["循环", "测验"], "importance": 0.8,
                "created_at": datetime.now().isoformat(),
                "access_count": 2, "last_accessed_at": datetime.now().isoformat(),
            }
        ]
    return _mock_memories[user_id]


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
    if user_id not in _mock_memories:
        _mock_memories[user_id] = []
    _mock_memories[user_id].append(memory)
    return memory


@router.get("/session/{user_id}")
async def get_session(user_id: str):
    """获取或创建会话"""
    if user_id not in _mock_sessions:
        _mock_sessions[user_id] = {
            "sessionId": f"session_{datetime.now().timestamp()}",
            "userId": user_id,
            "recentMessages": [],
            "currentTask": None,
            "startedAt": datetime.now().isoformat(),
            "lastActivityAt": datetime.now().isoformat(),
        }
    return _mock_sessions[user_id]


@router.post("/chat", response_model=ChatResponse)
async def chat_with_teacher(request: ChatRequest):
    """AI 教师对话（集成 RAG 知识检索）"""
    start_time = datetime.now()

    # 构建个性化回复
    persona = request.persona or {}
    profile_seed = request.profile_seed or ""
    address_mode = persona.get("address_mode", "name")

    # RAG 上下文注入
    knowledge_context = request.knowledge_context or ""
    knowledge_used = bool(knowledge_context)

    # 如果没有前端传入的 RAG 上下文，后端自行检索
    if not knowledge_context:
        try:
            from services.vector_knowledge_service import get_vector_knowledge_service
            rag_service = get_vector_knowledge_service()
            rag_result = rag_service.rag_retrieve(
                query=request.message,
                user_id=request.user_id,
                profile_seed=profile_seed,
            )
            knowledge_context = rag_result.context
            knowledge_used = rag_result.total_score > 0
        except Exception:
            pass  # RAG 不可用时降级

    # 基于学生画像 + RAG 上下文生成个性化回复
    reply = _generate_personalized_reply(
        request.message, profile_seed, address_mode, persona,
        knowledge_context=knowledge_context,
    )

    # 更新会话
    if request.user_id in _mock_sessions:
        session = _mock_sessions[request.user_id]
        session["recentMessages"].extend([
            {"role": "user", "content": request.message, "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": reply, "timestamp": datetime.now().isoformat()},
        ])
        session["recentMessages"] = session["recentMessages"][-20:]
        session["lastActivityAt"] = datetime.now().isoformat()

    elapsed = (datetime.now() - start_time).total_seconds() * 1000

    return ChatResponse(
        reply=reply,
        session_id=request.session_id,
        emotion_detected="neutral",
        memories_referenced=request.knowledge_sources or [],
        knowledge_used=knowledge_used,
        suggestions=[],
        model="mock-ai-teacher",
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
    if user_id not in _mock_personas:
        _mock_personas[user_id] = {
            "user_id": user_id, "address_mode": "name", "nickname": "",
            "language_style": "lively", "hint_level": "guided_thinking",
            "encouragement_frequency": "moderate", "strictness": "standard",
            "emoji_usage": "moderate",
        }
    return _mock_personas[user_id]


@router.patch("/persona/{user_id}", response_model=TeacherPersonaModel)
async def update_persona(user_id: str, persona: TeacherPersonaModel):
    """更新 AI 教师人格配置"""
    _mock_personas[user_id] = persona.model_dump()
    return persona


@router.delete("/memory/{user_id}")
async def reset_memory(user_id: str):
    """重置 AI 教师记忆"""
    _mock_memories.pop(user_id, None)
    _mock_sessions.pop(user_id, None)
    return {"success": True}


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
