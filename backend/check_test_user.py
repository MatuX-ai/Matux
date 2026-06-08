#!/usr/bin/env python3
"""检查测试账号是否存在"""
import asyncio
from sqlalchemy import select
from utils.database import AsyncSessionLocal
from models.user import User


async def check():
    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.username == 'test_admin')
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            print(f'✓ 测试账号存在')
            print(f'  - 用户名: {user.username}')
            print(f'  - 邮箱: {user.email}')
            print(f'  - 是否激活: {user.is_active}')
            print(f'  - 角色: {user.role}')
        else:
            print('✗ 测试账号不存在')

if __name__ == "__main__":
    asyncio.run(check())
