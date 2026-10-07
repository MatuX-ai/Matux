"""检查数据库表结构"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
import asyncio
import sys
sys.path.insert(0, '.')


DATABASE_URL = "sqlite+aiosqlite:///./ai_service.db"


async def check():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # 检查 test_student 用户
        result = await session.execute(text("SELECT id, email FROM users WHERE email LIKE '%test%' OR email LIKE '%student%'"))
        users = result.fetchall()
        print("Test users:")
        for u in users:
            print(f"  - {u[0]}: {u[1]}")

        # 检查 exams 表
        result = await session.execute(text("SELECT id, title, status FROM exams"))
        exams = result.fetchall()
        print("\nExams:")
        for e in exams:
            print(f"  - {e[0]}: {e[1]} ({e[2]})")

        # 检查 exam_attempts 表
        result = await session.execute(text("SELECT id, exam_id, user_id, status FROM exam_attempts"))
        attempts = result.fetchall()
        print("\nExam attempts:")
        if attempts:
            for a in attempts:
                print(
                    f"  - {a[0]}: exam_id={a[1]}, user_id={a[2]}, status={a[3]}")
        else:
            print("  (none)")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check())
