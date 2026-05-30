"""
AI-Edu 在线测验 API 端点
支持测验启动、提交、批改等功能
"""

from datetime import datetime
import random
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


# ==================== 数据模型 ====================


class QuizQuestion(BaseModel):
    """测验题目"""

    id: int
    type: str = Field(..., description="题目类型", examples=["choice", "fill", "code"])
    content: str = Field(..., description="题目内容")
    options: Optional[List[str]] = Field(None, description="选择题选项")
    correct_answer: Any = Field(..., description="正确答案")
    points: int = Field(..., description="分值")
    difficulty: int = Field(default=1, description="难度系数 (1-5)")
    explanation: Optional[str] = Field(None, description="答案解析")


class QuizAnswer(BaseModel):
    """用户答案"""

    question_id: int
    answer: Any


class QuizStartRequest(BaseModel):
    """启动测验请求"""

    lesson_id: int
    user_id: int


class QuizSubmitRequest(BaseModel):
    """提交测验请求"""

    quiz_id: str
    answers: List[QuizAnswer]


class QuizState(BaseModel):
    """测验状态"""

    quiz_id: str
    lesson_id: int
    questions: List[QuizQuestion]
    current_question_index: int = 0
    started_at: datetime
    time_limit_minutes: Optional[int] = None


class QuizResult(BaseModel):
    """测验结果"""

    quiz_id: str
    score: int
    total_score: int
    accuracy: float
    time_spent_seconds: int
    points_earned: int
    passed: bool


# ==================== 内存存储（生产环境应使用数据库） ====================

# 临时存储测验状态
active_quizzes: Dict[str, QuizState] = {}

# 临时存储测验结果
quiz_results: Dict[str, QuizResult] = {}


# ==================== 示例题库（实际应从数据库加载） ====================

SAMPLE_QUESTIONS = {
    1: [  # Lesson ID 1 的题目
        QuizQuestion(
            id=1,
            type="choice",
            content="Python 中用于定义函数的关键字是？",
            options=["def", "function", "func", "define"],
            correct_answer=0,  # 选项 A 的索引
            points=10,
            difficulty=1,
            explanation="在 Python 中，使用 def 关键字来定义函数。函数定义的语法是：def function_name(parameters): 然后是函数体。",
        ),
        QuizQuestion(
            id=2,
            type="choice",
            content="以下哪个是 Python 的注释符号？",
            options=["//", "#", "/*", "--"],
            correct_answer=1,
            points=10,
            difficulty=1,
            explanation="Python 使用 # 作为单行注释符号。多行注释可以使用三个引号（'''或\"\"\"）包裹。",
        ),
        QuizQuestion(
            id=3,
            type="fill",
            content="Python 中用于输出内容的函数是______()",
            correct_answer="print",
            points=15,
            difficulty=2,
            explanation="print() 是 Python 中最基本的输出函数，用于将内容打印到控制台。它可以输出字符串、数字、列表等各种数据类型。",
        ),
        QuizQuestion(
            id=4,
            type="code",
            content="编写一个函数，计算两个数的和",
            correct_answer="def add(a, b):\n    return a + b",
            points=25,
            difficulty=3,
            explanation="这是一个简单的函数定义示例。需要掌握：1) 使用 def 定义函数 2) 参数传递 3) return 返回结果。注意 Python 的缩进规则。",
        ),
        QuizQuestion(
            id=5,
            type="choice",
            content="Python 列表的索引从几开始？",
            options=["1", "0", "-1", "任意值"],
            correct_answer=1,
            points=10,
            difficulty=1,
            explanation="Python 列表的索引从 0 开始计数。第一个元素的索引是 0，第二个是 1，以此类推。也可以使用负数索引，-1 表示最后一个元素。",
        ),
    ],
    2: [  # Lesson ID 2 的题目
        QuizQuestion(
            id=6,
            type="choice",
            content="物联网的英文缩写是？",
            options=["IoT", "IOI", "III", "IOT"],
            correct_answer=0,
            points=10,
            difficulty=1,
            explanation="物联网的英文是 Internet of Things，缩写为 IoT。它指的是通过各种信息传感器设备连接万物形成的网络。",
        ),
        QuizQuestion(
            id=7,
            type="fill",
            content="ESP8266 是一款常用的______模块",
            correct_answer="WiFi",
            points=15,
            difficulty=2,
            explanation="ESP8266 是一款低成本、低功耗的 WiFi 微控制器模块，广泛用于物联网项目中，支持 Arduino 和 MicroPython 编程。",
        ),
    ],
}


# ==================== API 端点 ====================


@router.post("/quiz/start", response_model=QuizState)
async def start_quiz(request: QuizStartRequest):
    """
    启动测验

    Args:
        request: 启动测验请求

    Returns:
        测验状态（包含题目列表）
    """
    # 生成唯一的 quiz_id
    quiz_id = str(uuid.uuid4())

    # 根据 lesson_id 获取题目
    questions = SAMPLE_QUESTIONS.get(request.lesson_id, [])

    if not questions:
        raise HTTPException(
            status_code=404, detail=f"未找到课程 {request.lesson_id} 的测验题目"
        )

    # 随机打乱题目顺序
    shuffled_questions = random.sample(questions, len(questions))

    # 创建测验状态
    quiz_state = QuizState(
        quiz_id=quiz_id,
        lesson_id=request.lesson_id,
        questions=shuffled_questions,
        started_at=datetime.now(),
        time_limit_minutes=len(shuffled_questions) * 2,  # 每题 2 分钟
    )

    # 保存到内存存储
    active_quizzes[quiz_id] = quiz_state

    return quiz_state


@router.post("/quiz/submit", response_model=QuizResult)
async def submit_quiz(request: QuizSubmitRequest):
    """
    提交测验答案

    Args:
        request: 提交测验请求

    Returns:
        测验结果
    """
    # 查找活跃的测验
    if request.quiz_id not in active_quizzes:
        raise HTTPException(status_code=404, detail="未找到活跃的测验")

    quiz_state = active_quizzes[request.quiz_id]

    # 计算得分
    total_score = 0
    earned_score = 0

    for answer in request.answers:
        # 查找对应的题目
        question = next(
            (q for q in quiz_state.questions if q.id == answer.question_id), None
        )

        if question:
            total_score += question.points

            # 判分
            if is_correct(question, answer.answer):
                earned_score += question.points

    # 计算正确率
    accuracy = earned_score / total_score if total_score > 0 else 0

    # 计算用时
    time_spent = int((datetime.now() - quiz_state.started_at).total_seconds())

    # 计算获得的积分（基于正确率）
    points_earned = int(accuracy * 100)  # 基础 100 积分 * 正确率

    # 判断是否通过（60% 正确率）
    passed = accuracy >= 0.6

    # 创建测验结果
    result = QuizResult(
        quiz_id=request.quiz_id,
        score=earned_score,
        total_score=total_score,
        accuracy=accuracy,
        time_spent_seconds=time_spent,
        points_earned=points_earned,
        passed=passed,
    )

    # 保存结果
    quiz_results[request.quiz_id] = result

    # 从活跃列表中移除
    del active_quizzes[request.quiz_id]

    return result


@router.get("/quiz/{quiz_id}/review", response_model=Dict[str, Any])
async def review_quiz(quiz_id: str):
    """
    查看测验答案解析

    Args:
        quiz_id: 测验 ID

    Returns:
        答案解析，包含每道题的详细解析
    """
    # 先尝试在结果中查找
    if quiz_id in quiz_results:
        result = quiz_results[quiz_id]

        # 获取详细的题目解析
        detailed_explanations = get_detailed_question_explanations(quiz_id)

        # 返回带解析的结果
        return {
            "result": result.dict(),
            "explanations": detailed_explanations,
        }

    # 如果还在活跃状态
    if quiz_id in active_quizzes:
        raise HTTPException(status_code=400, detail="测验尚未提交，无法查看解析")

    raise HTTPException(status_code=404, detail="未找到测验记录")


@router.get("/quiz/{quiz_id}/status")
async def get_quiz_status(quiz_id: str):
    """
    获取测验状态

    Args:
        quiz_id: 测验 ID

    Returns:
        测验状态
    """
    if quiz_id in active_quizzes:
        return active_quizzes[quiz_id]

    if quiz_id in quiz_results:
        return {"status": "completed", "result": quiz_results[quiz_id]}

    raise HTTPException(status_code=404, detail="未找到测验")


# ==================== 辅助函数 ====================


def is_correct(question: QuizQuestion, user_answer: Any) -> bool:
    """
    判断答案是否正确

    Args:
        question: 题目
        user_answer: 用户答案

    Returns:
        是否正确
    """
    if question.type == "choice":
        return user_answer == question.correct_answer
    elif question.type == "fill":
        # 填空题：去除空格后比较，忽略大小写
        return (
            str(user_answer).strip().lower()
            == str(question.correct_answer).strip().lower()
        )
    elif question.type == "code":
        # 编程题：简单文本比较（实际应该运行测试用例）
        return str(user_answer).strip() == str(question.correct_answer).strip()
    else:
        return False


def get_detailed_question_explanations(quiz_id: str) -> List[Dict[str, Any]]:
    """
    获取每道题目的详细解析

    Args:
        quiz_id: 测验 ID

    Returns:
        详细解析列表，包含每题的题目、答案、解析等
    """
    detailed_explanations = []

    if quiz_id in quiz_results:
        result = quiz_results[quiz_id]

        # 从活跃测验或历史数据中获取题目
        questions = []
        # 这里简化处理，实际应该从数据库获取
        for lesson_id, lesson_questions in SAMPLE_QUESTIONS.items():
            questions.extend(lesson_questions)

        # 生成每题的解析
        for i, question in enumerate(questions[:5]):  # 假设最多 5 题
            explanation = {
                "question_id": question.id,
                "question_number": i + 1,
                "question_type": question.type,
                "question_content": question.content,
                "options": question.options,
                "correct_answer": question.correct_answer,
                "explanation": question.explanation or "暂无解析",
                "difficulty": question.difficulty,
                "points": question.points,
                "knowledge_points": get_knowledge_points(question),
            }
            detailed_explanations.append(explanation)

    return detailed_explanations


def get_knowledge_points(question: QuizQuestion) -> List[str]:
    """
    获取题目涉及的知识点

    Args:
        question: 题目对象

    Returns:
        知识点列表
    """
    # 根据题目类型和内容提取知识点
    knowledge_map = {
        1: ["Python 基础", "函数定义"],
        2: ["Python 基础", "注释语法"],
        3: ["Python 基础", "输入输出"],
        4: ["Python 基础", "函数编程"],
        5: ["Python 基础", "数据结构"],
        6: ["物联网基础", "专业术语"],
        7: ["硬件知识", "通信模块"],
    }
    return knowledge_map.get(question.id, ["通用知识"])


def get_question_explanations(quiz_id: str) -> List[Dict[str, Any]]:
    """
    获取题目解析

    Args:
        quiz_id: 测验 ID

    Returns:
        解析列表
    """
    # 这里返回示例解析，实际应从数据库或配置中加载
    explanations = []

    if quiz_id in quiz_results:
        result = quiz_results[quiz_id]

        # 根据分数生成简单的解析
        if result.accuracy >= 0.9:
            feedback = "太棒了！你对这个知识点掌握得很好！🎉"
        elif result.accuracy >= 0.6:
            feedback = "不错！还有一些细节需要注意。👍"
        else:
            feedback = "建议复习一下课程内容，然后再次尝试。📚"

        explanations.append(
            {
                "general_feedback": feedback,
                "tips": [
                    "多动手实践是学习编程的最好方法",
                    "遇到不懂的地方可以回看课程视频",
                    "可以在讨论区向其他同学请教",
                ],
            }
        )

    return explanations


@router.get("/quiz-history/{user_id}")
async def get_quiz_history(user_id: int):
    """
    获取用户的测验历史

    Args:
        user_id: 用户 ID

    Returns:
        历史记录列表
    """
    # TODO: 实际应从数据库查询
    return {
        "user_id": user_id,
        "history": [],
        "total_count": 0,
        "average_accuracy": 0,
        "total_points": 0,
    }
