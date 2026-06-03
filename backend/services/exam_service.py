"""
Exam Service - 测验业务逻辑服务

提供测验的 CRUD 操作、随机抽题、自动评分、成绩分析等功能
"""

import random
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.exam import (
    AttemptStatus,
    Exam,
    ExamAttempt,
    ExamDifficulty,
    ExamStatus,
    Question,
    QuestionType,
)
from models.user import User


class ExamService:
    """测验服务"""

    # ============ 测验管理 ============

    async def create_exam(
        self, db: AsyncSession, exam_data: dict, creator_id: int
    ) -> Exam:
        """创建测验"""
        exam = Exam(
            title=exam_data["title"],
            description=exam_data.get("description"),
            course_id=exam_data.get("course_id"),
            creator_id=creator_id,
            difficulty=ExamDifficulty(exam_data.get("difficulty", "medium")),
            duration_minutes=exam_data.get("duration_minutes", 30),
            start_time=(
                datetime.fromisoformat(exam_data["start_time"])
                if exam_data.get("start_time")
                else None
            ),
            end_time=(
                datetime.fromisoformat(exam_data["end_time"])
                if exam_data.get("end_time")
                else None
            ),
            passing_score=exam_data.get("passing_score", 60.0),
            max_attempts=exam_data.get("max_attempts", 1),
            shuffle_questions=exam_data.get("shuffle_questions", True),
            shuffle_options=exam_data.get("shuffle_options", True),
            show_result_immediately=exam_data.get("show_result_immediately", False),
            anti_cheat_enabled=exam_data.get("anti_cheat_enabled", True),
            max_screen_switches=exam_data.get("max_screen_switches", 3),
            min_answer_seconds=exam_data.get("min_answer_seconds", 3),
            restrict_paste=exam_data.get("restrict_paste", True),
            restrict_copy=exam_data.get("restrict_copy", True),
            fullscreen_required=exam_data.get("fullscreen_required", True),
        )
        db.add(exam)
        await db.commit()
        await db.refresh(exam)
        return exam

    async def update_exam(self, db: AsyncSession, exam_id: int, exam_data: dict) -> Optional[Exam]:
        """更新测验"""
        stmt = select(Exam).filter(Exam.id == exam_id)
        result = await db.execute(stmt)
        exam = result.scalar_one_or_none()

        if not exam:
            return None

        for key, value in exam_data.items():
            if hasattr(exam, key) and key not in ("id", "created_at", "attempt_count"):
                setattr(exam, key, value)

        await db.commit()
        await db.refresh(exam)
        return exam

    async def delete_exam(self, db: AsyncSession, exam_id: int) -> bool:
        """删除测验"""
        stmt = select(Exam).filter(Exam.id == exam_id)
        result = await db.execute(stmt)
        exam = result.scalar_one_or_none()

        if not exam:
            return False

        await db.delete(exam)
        await db.commit()
        return True

    async def get_exam(self, db: AsyncSession, exam_id: int) -> Optional[Exam]:
        """获取测验详情"""
        stmt = select(Exam).filter(Exam.id == exam_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_exams(
        self,
        db: AsyncSession,
        status: Optional[str] = None,
        course_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Exam], int]:
        """获取测验列表"""
        query = select(Exam)

        if status:
            query = query.filter(Exam.status == ExamStatus(status))
        if course_id:
            query = query.filter(Exam.course_id == course_id)

        # 总数
        count_query = select(func.count()).select_from(query.subquery())
        total = await db.execute(count_query)
        total_count = total.scalar() or 0

        # 分页
        query = query.order_by(Exam.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(query)
        exams = result.scalars().all()

        return list(exams), total_count

    # ============ 题目管理 ============

    async def add_question(self, db: AsyncSession, exam_id: int, question_data: dict) -> Question:
        """添加题目"""
        # 计算排序序号
        stmt = (
            select(func.count()).select_from(Question).filter(Question.exam_id == exam_id)
        )
        result = await db.execute(stmt)
        count = result.scalar() or 0

        question = Question(
            exam_id=exam_id,
            question_type=QuestionType(question_data["question_type"]),
            title=question_data["title"],
            description=question_data.get("description"),
            options=question_data.get("options"),
            correct_answer=question_data.get("correct_answer"),
            score=question_data.get("score", 10.0),
            order_index=count,
            explanation=question_data.get("explanation"),
            tags=question_data.get("tags"),
            difficulty=ExamDifficulty(question_data.get("difficulty", "medium")),
        )
        db.add(question)

        # 更新测验的总题数和总分
        exam = await self.get_exam(db, exam_id)
        if exam:
            exam.total_questions = (exam.total_questions or 0) + 1
            exam.total_score = (exam.total_score or 0) + question.score

        await db.commit()
        await db.refresh(question)
        return question

    async def get_questions(
        self, db: AsyncSession, exam_id: int, include_answers: bool = False
    ) -> list[Question]:
        """获取测验的所有题目"""
        stmt = (
            select(Question)
            .filter(Question.exam_id == exam_id, Question.is_active == True)
            .order_by(Question.order_index)
        )
        result = await db.execute(stmt)
        questions = result.scalars().all()

        # 如果不包含答案，移除正确答案字段
        if not include_answers:
            for q in questions:
                q.correct_answer = None

        return list(questions)

    async def update_question(
        self, db: AsyncSession, question_id: int, question_data: dict
    ) -> Optional[Question]:
        """更新题目"""
        stmt = select(Question).filter(Question.id == question_id)
        result = await db.execute(stmt)
        question = result.scalar_one_or_none()

        if not question:
            return None

        for key, value in question_data.items():
            if hasattr(question, key) and key not in ("id", "exam_id", "created_at"):
                setattr(question, key, value)

        await db.commit()
        await db.refresh(question)
        return question

    async def delete_question(self, db: AsyncSession, question_id: int) -> bool:
        """删除题目"""
        stmt = select(Question).filter(Question.id == question_id)
        result = await db.execute(stmt)
        question = result.scalar_one_or_none()

        if not question:
            return False

        exam = await self.get_exam(db, question.exam_id)
        if exam:
            exam.total_questions = max(0, (exam.total_questions or 1) - 1)
            exam.total_score = max(0, (exam.total_score or question.score) - question.score)

        await db.delete(question)
        await db.commit()
        return True

    # ============ 考试流程 ============

    async def start_exam(
        self,
        db: AsyncSession,
        exam_id: int,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
    ) -> Optional[ExamAttempt]:
        """开始考试"""
        exam = await self.get_exam(db, exam_id)
        if not exam:
            return None

        if exam.status != ExamStatus.PUBLISHED:
            raise ValueError("测验未发布")

        # 检查时间窗口
        now = datetime.utcnow()
        if exam.start_time and now < exam.start_time.replace(tzinfo=None):
            raise ValueError("考试尚未开始")
        if exam.end_time and now > exam.end_time.replace(tzinfo=None):
            raise ValueError("考试已结束")

        # 检查尝试次数
        stmt = select(func.count()).select_from(ExamAttempt).filter(
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.user_id == user_id,
            ExamAttempt.status != AttemptStatus.VOIDED,
        )
        result = await db.execute(stmt)
        attempt_count = result.scalar() or 0

        if attempt_count >= exam.max_attempts:
            raise ValueError("已达到最大尝试次数")

        # 创建答题记录
        attempt = ExamAttempt(
            exam_id=exam_id,
            user_id=user_id,
            status=AttemptStatus.IN_PROGRESS,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
        )
        db.add(attempt)

        # 更新测验统计
        exam.attempt_count = (exam.attempt_count or 0) + 1

        await db.commit()
        await db.refresh(attempt)
        return attempt

    async def submit_exam(
        self,
        db: AsyncSession,
        attempt_id: int,
        answers: dict,
        user_id: int,
    ) -> Optional[ExamAttempt]:
        """提交考试答案"""
        stmt = select(ExamAttempt).filter(
            ExamAttempt.id == attempt_id,
            ExamAttempt.user_id == user_id,
        )
        result = await db.execute(stmt)
        attempt = result.scalar_one_or_none()

        if not attempt:
            return None

        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ValueError("该答题记录已提交")

        # 计算耗时
        time_spent = int((datetime.utcnow() - attempt.started_at.replace(tzinfo=None)).total_seconds())
        attempt.time_spent_seconds = time_spent
        attempt.answers = answers

        # 自动评分（客观题）
        exam = await self.get_exam(db, attempt.exam_id)
        questions = await self.get_questions(db, attempt.exam_id, include_answers=True)

        total_score = 0.0
        earned_score = 0.0
        graded_answers = {}

        for question in questions:
            total_score += question.score
            user_answer = answers.get(str(question.id))

            if question.question_type in (
                QuestionType.SINGLE_CHOICE,
                QuestionType.MULTIPLE_CHOICE,
                QuestionType.TRUE_FALSE,
            ):
                # 客观题自动评分
                is_correct = self._check_answer(question, user_answer)
                if is_correct:
                    earned_score += question.score

                graded_answers[str(question.id)] = {
                    "user_answer": user_answer,
                    "correct_answer": question.correct_answer,
                    "score": question.score if is_correct else 0,
                    "is_correct": is_correct,
                }
            else:
                # 主观题需要人工评分
                graded_answers[str(question.id)] = {
                    "user_answer": user_answer,
                    "correct_answer": question.correct_answer,
                    "score": 0,
                    "is_correct": None,  # 待人工评分
                }

        attempt.answers = graded_answers
        attempt.total_score = total_score
        attempt.score = earned_score
        attempt.percentage = round((earned_score / total_score * 100), 2) if total_score > 0 else 0
        attempt.submitted_at = func.now()
        attempt.auto_graded = True

        # 检查是否有主观题
        has_subjective = any(
            q.question_type in (QuestionType.SHORT_ANSWER, QuestionType.CODING)
            for q in questions
        )

        if has_subjective:
            attempt.status = AttemptStatus.SUBMITTED
        else:
            attempt.status = AttemptStatus.GRADED

        await db.commit()
        await db.refresh(attempt)
        return attempt

    def _check_answer(self, question: Question, user_answer) -> bool:
        """检查答案是否正确"""
        if not user_answer:
            return False

        correct = question.correct_answer

        if question.question_type == QuestionType.SINGLE_CHOICE:
            return str(user_answer).strip() == str(correct).strip()

        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            # 多选题：比较排序后的列表
            if isinstance(user_answer, list) and isinstance(correct, list):
                return sorted(user_answer) == sorted(correct)
            return str(user_answer).strip() == str(correct).strip()

        elif question.question_type == QuestionType.TRUE_FALSE:
            return str(user_answer).strip().lower() == str(correct).strip().lower()

        return False

    async def grade_subjective(
        self,
        db: AsyncSession,
        attempt_id: int,
        grader_id: int,
        scores: dict[str, float],
        notes: Optional[str] = None,
    ) -> Optional[ExamAttempt]:
        """人工评分（主观题）"""
        stmt = select(ExamAttempt).filter(ExamAttempt.id == attempt_id)
        result = await db.execute(stmt)
        attempt = result.scalar_one_or_none()

        if not attempt:
            return None

        # 更新主观题分数
        graded_answers = attempt.answers or {}
        total_subjective_score = 0.0

        for q_id, manual_score in scores.items():
            if q_id in graded_answers:
                graded_answers[q_id]["score"] = manual_score
                graded_answers[q_id]["is_correct"] = manual_score > 0
                total_subjective_score += manual_score

        # 计算客观题得分
        objective_score = sum(
            item["score"]
            for item in graded_answers.values()
            if item.get("is_correct") is not None and item["is_correct"] is not False
        )

        attempt.answers = graded_answers
        attempt.score = objective_score + total_subjective_score
        attempt.percentage = (
            round((attempt.score / attempt.total_score * 100), 2)
            if attempt.total_score
            else 0
        )
        attempt.status = AttemptStatus.GRADED
        attempt.graded_by = grader_id
        attempt.graded_at = func.now()
        attempt.grader_notes = notes

        await db.commit()
        await db.refresh(attempt)
        return attempt

    async def get_user_attempts(
        self, db: AsyncSession, exam_id: int, user_id: int
    ) -> list[ExamAttempt]:
        """获取用户在某个测验的答题记录"""
        stmt = (
            select(ExamAttempt)
            .filter(
                ExamAttempt.exam_id == exam_id,
                ExamAttempt.user_id == user_id,
            )
            .order_by(ExamAttempt.started_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_attempt(self, db: AsyncSession, attempt_id: int) -> Optional[ExamAttempt]:
        """获取答题记录"""
        stmt = select(ExamAttempt).filter(ExamAttempt.id == attempt_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def void_attempt(
        self, db: AsyncSession, attempt_id: int, reason: str = "作弊判定"
    ) -> bool:
        """作废答题记录"""
        stmt = select(ExamAttempt).filter(ExamAttempt.id == attempt_id)
        result = await db.execute(stmt)
        attempt = result.scalar_one_or_none()

        if not attempt:
            return False

        attempt.status = AttemptStatus.VOIDED
        attempt.grader_notes = reason
        await db.commit()
        return True

    async def get_exam_statistics(self, db: AsyncSession, exam_id: int) -> dict:
        """获取测验统计数据"""
        stmt = select(ExamAttempt).filter(
            ExamAttempt.exam_id == exam_id,
            ExamAttempt.status.in_([AttemptStatus.GRADED, AttemptStatus.SUBMITTED]),
        )
        result = await db.execute(stmt)
        attempts = result.scalars().all()

        if not attempts:
            return {
                "total_attempts": 0,
                "average_score": 0,
                "highest_score": 0,
                "lowest_score": 0,
                "pass_rate": 0,
                "average_time_spent": 0,
            }

        exam = await self.get_exam(db, exam_id)
        scores = [a.score or 0 for a in attempts]
        passing_score = exam.passing_score if exam else 60

        return {
            "total_attempts": len(attempts),
            "average_score": round(sum(scores) / len(scores), 2),
            "highest_score": max(scores),
            "lowest_score": min(scores),
            "pass_rate": round(
                sum(1 for s in scores if s >= passing_score) / len(scores) * 100, 2
            ),
            "average_time_spent": round(
                sum(a.time_spent_seconds or 0 for a in attempts) / len(attempts)
            ),
        }


# 全局服务实例
exam_service = ExamService()
