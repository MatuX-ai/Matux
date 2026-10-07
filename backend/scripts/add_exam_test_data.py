"""
添加测验测试数据脚本

运行方式:
    cd g:\iMato\backend
    python scripts/add_exam_test_data.py
"""

from models.user import User
from models.exam import Exam, Question, ExamStatus, QuestionType, ExamDifficulty
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, update
import asyncio
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")


DATABASE_URL = "sqlite+aiosqlite:///./ai_service.db"


async def main():
    print("🔧 开始添加测验测试数据...")

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # 查找测试用户
        result = await session.execute(select(User).where(User.email == "test_m2_001@test.com"))
        user = result.scalar_one_or_none()

        if not user:
            print("❌ 未找到测试用户 test_m2_001@test.com，请先创建用户")
            return

        print(f"✅ 找到测试用户: {user.email} (ID: {user.id})")

        # 检查是否已有测验数据
        result = await session.execute(
            select(Exam).where(Exam.creator_id == user.id,
                               Exam.status == ExamStatus.PUBLISHED)
        )
        existing_exams = result.scalars().all()
        if existing_exams:
            print(f"ℹ️  已存在 {len(existing_exams)} 个已发布的测验，跳过创建")
            return

        # 创建测验数据
        now = datetime.utcnow()

        exams_data = [
            {
                "title": "Python 基础测验",
                "description": "测试 Python 编程语言基础知识，包括变量、数据类型、控制流程等",
                "difficulty": ExamDifficulty.EASY,
                "duration_minutes": 30,
                "total_questions": 5,
                "total_score": 100.0,
                "passing_score": 60.0,
                "max_attempts": 2,
                "start_time": now - timedelta(days=1),
                "end_time": now + timedelta(days=30),
            },
            {
                "title": "算法与数据结构测验",
                "description": "测试常见算法和数据结构的理解和应用能力",
                "difficulty": ExamDifficulty.MEDIUM,
                "duration_minutes": 60,
                "total_questions": 10,
                "total_score": 100.0,
                "passing_score": 70.0,
                "max_attempts": 1,
                "start_time": now + timedelta(days=7),
                "end_time": now + timedelta(days=37),
            },
            {
                "title": "Web 开发综合测验",
                "description": "测试 HTML、CSS、JavaScript 及前端框架知识",
                "difficulty": ExamDifficulty.HARD,
                "duration_minutes": 45,
                "total_questions": 8,
                "total_score": 100.0,
                "passing_score": 75.0,
                "max_attempts": 2,
                "start_time": None,
                "end_time": None,
            },
        ]

        created_exams = []
        for exam_data in exams_data:
            exam = Exam(
                title=exam_data["title"],
                description=exam_data["description"],
                course_id=None,
                creator_id=user.id,
                difficulty=exam_data["difficulty"],
                status=ExamStatus.PUBLISHED,
                duration_minutes=exam_data["duration_minutes"],
                start_time=exam_data["start_time"],
                end_time=exam_data["end_time"],
                passing_score=exam_data["passing_score"],
                max_attempts=exam_data["max_attempts"],
                total_questions=exam_data["total_questions"],
                total_score=exam_data["total_score"],
                shuffle_questions=True,
                shuffle_options=True,
                show_result_immediately=True,
                anti_cheat_enabled=True,
            )
            session.add(exam)
            created_exams.append(exam_data)
            print(f"📝 创建测验: {exam_data['title']}")

        await session.flush()

        # 为第一个测验添加题目
        result = await session.execute(
            select(Exam).where(Exam.title == "Python 基础测验",
                               Exam.creator_id == user.id)
        )
        python_exam = result.scalar_one_or_none()

        if python_exam:
            questions = [
                {
                    "question_type": QuestionType.SINGLE_CHOICE,
                    "title": "Python 中，以下哪个是正确的变量命名方式？",
                    "options": ["1var", "_var", "my-var", "class"],
                    "correct_answer": "B",
                    "explanation": "Python 变量名必须以字母或下划线开头，不能使用数字开头或特殊字符。",
                    "score": 20.0,
                    "tags": ["python", "基础", "变量"],
                },
                {
                    "question_type": QuestionType.MULTIPLE_CHOICE,
                    "title": "以下哪些是 Python 的内置数据类型？",
                    "options": ["int", "string", "list", "array"],
                    "correct_answer": "A,C",
                    "explanation": "int、list 是内置类型，string 应为 str，array 不是内置类型。",
                    "score": 20.0,
                    "tags": ["python", "数据类型"],
                },
                {
                    "question_type": QuestionType.TRUE_FALSE,
                    "title": "Python 列表可以存储不同类型的元素。",
                    "options": ["正确", "错误"],
                    "correct_answer": "A",
                    "explanation": "Python 列表是动态类型，可以存储任意类型的对象。",
                    "score": 20.0,
                    "tags": ["python", "列表"],
                },
                {
                    "question_type": QuestionType.SINGLE_CHOICE,
                    "title": "for 循环用于遍历以下哪种对象？",
                    "options": ["字典", "集合", "字符串", "以上全部"],
                    "correct_answer": "D",
                    "explanation": "Python 的 for 循环可以遍历所有可迭代对象。",
                    "score": 20.0,
                    "tags": ["python", "循环"],
                },
                {
                    "question_type": QuestionType.SHORT_ANSWER,
                    "title": "请写出使用 list comprehension 创建 1-10 平方列表的表达式",
                    "options": None,
                    "correct_answer": "[x**2 for x in range(1, 11)]",
                    "explanation": "列表推导式语法: [表达式 for 变量 in 可迭代对象]",
                    "score": 20.0,
                    "tags": ["python", "列表推导式"],
                },
            ]

            for i, q_data in enumerate(questions):
                question = Question(
                    exam_id=python_exam.id,
                    question_type=q_data["question_type"],
                    title=q_data["title"],
                    options=q_data["options"],
                    correct_answer=q_data["correct_answer"],
                    score=q_data["score"],
                    order_index=i,
                    explanation=q_data["explanation"],
                    tags=q_data["tags"],
                    difficulty=ExamDifficulty.EASY,
                    is_active=True,
                )
                session.add(question)
                print(f"   📋 添加题目: {q_data['title'][:30]}...")

        await session.commit()
        print("\n✅ 测验测试数据创建完成！")
        print(f"   - 创建了 {len(created_exams)} 个已发布的测验")
        print("   - 为 Python 基础测验添加了 5 道题目")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
