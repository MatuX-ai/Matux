"""直接测试 start_exam 方法"""
import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select
from datetime import datetime

# 模拟配置
DATABASE_URL = "sqlite+aiosqlite:///./ai_service.db"

async def test_start_exam():
    from models.exam import Exam, ExamAttempt, ExamStatus, AttemptStatus
    from models.user import User
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. 先获取一个用户
        stmt = select(User).limit(1)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            print("No user found!")
            return
        print(f"Found user: id={user.id}, username={user.username}")
        
        # 2. 获取一个已发布的测验
        stmt = select(Exam).filter(Exam.status == ExamStatus.PUBLISHED).limit(1)
        result = await session.execute(stmt)
        exam = result.scalar_one_or_none()
        if not exam:
            print("No published exam found!")
            return
        print(f"Found exam: id={exam.id}, title={exam.title}, status={exam.status}")
        
        # 3. 调用 start_exam 逻辑
        print("\n=== Starting exam ===")
        
        # 检查尝试次数
        from sqlalchemy import func
        stmt = select(func.count()).select_from(ExamAttempt).filter(
            ExamAttempt.exam_id == exam.id,
            ExamAttempt.user_id == user.id,
            ExamAttempt.status != AttemptStatus.VOIDED,
        )
        result = await session.execute(stmt)
        attempt_count = result.scalar() or 0
        print(f"Current attempt count: {attempt_count}, max: {exam.max_attempts}")
        
        if attempt_count >= exam.max_attempts:
            print("Max attempts reached!")
            return
        
        # 创建答题记录
        print("Creating ExamAttempt...")
        attempt = ExamAttempt(
            exam_id=exam.id,
            user_id=user.id,
            status=AttemptStatus.IN_PROGRESS,
            ip_address="127.0.0.1",
        )
        session.add(attempt)
        
        # 更新测验统计
        exam.attempt_count = (exam.attempt_count or 0) + 1
        print(f"Updated exam.attempt_count to {exam.attempt_count}")
        
        print("Committing...")
        await session.commit()
        
        print("Refreshing attempt...")
        try:
            await session.refresh(attempt)
            print(f"Success! attempt_id={attempt.id}")
            print(f"attempt.started_at={attempt.started_at}")
        except Exception as e:
            print(f"ERROR during refresh: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n=== Test completed ===")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_start_exam())
