"""一次性脚本：创建测试管理员账号"""
import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

import bcrypt  # noqa: E402
from models.user import User, UserRole  # noqa: E402
from sqlalchemy import select  # noqa: E402
from utils.database import AsyncSessionLocal  # noqa: E402


async def main():
    hashed = bcrypt.hashpw(b"TestAdmin123!"[:72], bcrypt.gensalt()).decode("utf-8")

    async with AsyncSessionLocal() as db:
        stmt = select(User).where(User.username == "test_admin")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            user.hashed_password = hashed
            user.is_active = True
            await db.commit()
            print(f"OK: user exists, password reset  | id={user.id} email={user.email}")
        else:
            user = User(
                email="admin@testorg.com",
                username="test_admin",
                hashed_password=hashed,
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"OK: user created  | id={user.id} email={user.email}")


if __name__ == "__main__":
    asyncio.run(main())
