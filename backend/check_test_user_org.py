"""检查测试账号的组织关联"""
import asyncio
import sys
sys.path.insert(0, 'G:\\iMato\\backend')

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from utils.database import get_db_session
from models.user import User
from models.user_organization import UserOrganization

async def check_user_org():
    async with get_db_session() as db:
        # 查找 admin@testorg.com 用户
        stmt = select(User).where(User.username == "admin@testorg.com")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            print("❌ 用户 admin@testorg.com 不存在")
            return

        print(f"✅ 找到用户:")
        print(f"  ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Role: {user.role}")

        # 检查 user_organizations 关联
        stmt = select(UserOrganization).where(UserOrganization.user_id == user.id)
        result = await db.execute(stmt)
        orgs = result.scalars().all()

        if not orgs:
            print(f"\n❌ 用户 {user.id} 没有任何组织关联!")
            print("\n需要运行初始化脚本创建组织关联...")
        else:
            print(f"\n✅ 找到 {len(orgs)} 个组织关联:")
            for org in orgs:
                print(f"  - Org ID: {org.org_id}, Is Primary: {org.is_primary}, Status: {org.status}")

if __name__ == "__main__":
    asyncio.run(check_user_org())
