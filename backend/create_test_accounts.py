#!/usr/bin/env python3
"""
创建多种角色的测试账号
- 管理员: test_admin / TestAdmin123!
- 教师: test_teacher / TestTeacher123!
- 学生: test_student / TestStudent123!
"""
import asyncio
import bcrypt
from sqlalchemy import select
from utils.database import AsyncSessionLocal
from models.user import User, UserRole


async def create_test_accounts():
    """创建多种角色的测试账号"""

    accounts = [
        {
            "username": "test_admin",
            "email": "admin@testorg.com",
            "password": "TestAdmin123!",
            "role": UserRole.ADMIN,
            "full_name": "测试管理员",
        },
        {
            "username": "test_teacher",
            "email": "teacher@testorg.com",
            "password": "TestTeacher123!",
            "role": UserRole.TEACHER,
            "full_name": "测试教师",
        },
        {
            "username": "test_student",
            "email": "student@testorg.com",
            "password": "TestStudent123!",
            "role": UserRole.STUDENT,
            "full_name": "测试学生",
        },
    ]

    async with AsyncSessionLocal() as db:
        for account in accounts:
            stmt = select(User).where(User.username == account["username"])
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()

            # 哈希密码
            hashed = bcrypt.hashpw(
                account["password"].encode('utf-8')[:72],
                bcrypt.gensalt()
            ).decode("utf-8")

            if user:
                # 更新现有账号
                user.hashed_password = hashed
                user.email = account["email"]
                user.role = account["role"]
                user.is_active = True
                print(
                    f"✓ 更新账号: {account['username']} ({account['role'].value})")
            else:
                # 创建新账号
                user = User(
                    username=account["username"],
                    email=account["email"],
                    hashed_password=hashed,
                    role=account["role"],
                    is_active=True,
                )
                db.add(user)
                print(
                    f"✓ 创建账号: {account['username']} ({account['role'].value})")

            await db.commit()

    print("\n所有测试账号创建完成！")
    print("\n可用的测试账号：")
    for account in accounts:
        print(
            f"  - {account['username']} / {account['password']} ({account['role'].value})")

if __name__ == "__main__":
    asyncio.run(create_test_accounts())
