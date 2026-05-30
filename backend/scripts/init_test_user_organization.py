"""
初始化测试账号的组织关联
为 admin@testorg.com 用户创建与 Test Organization 的关联
"""

import asyncio
import logging
from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.license import Organization
from models.user_organization import (
    UserOrganization,
    UserOrganizationRole,
    UserOrganizationStatus,
)
from utils.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_test_user_organization():
    """初始化测试用户的组织关联"""

    db = AsyncSessionLocal()

    try:
        # 1. 查找测试用户
        stmt = select(User).where(User.email == "admin@testorg.com")
        result = await db.execute(stmt)
        test_user = result.scalar_one_or_none()

        if not test_user:
            logger.error("❌ 测试用户不存在：admin@testorg.com")
            return False

        logger.info(f"✓ 找到测试用户：{test_user.username} (ID: {test_user.id})")

        # 2. 查找测试组织
        stmt = select(Organization).where(Organization.contact_email == "admin@testorg.com")
        result = await db.execute(stmt)
        test_org = result.scalar_one_or_none()

        if not test_org:
            logger.error("❌ 测试组织不存在")
            return False

        logger.info(f"✓ 找到测试组织：{test_org.name} (ID: {test_org.id})")

        # 3. 检查是否已存在关联
        stmt = select(UserOrganization).where(
            UserOrganization.user_id == test_user.id,
            UserOrganization.org_id == test_org.id
        )
        result = await db.execute(stmt)
        existing_assoc = result.scalar_one_or_none()

        if existing_assoc:
            logger.info(f"⚠️  用户 - 组织关联已存在")
            # 更新为主组织
            if not existing_assoc.is_primary:
                existing_assoc.is_primary = True
                existing_assoc.role = UserOrganizationRole.ADMIN
                existing_assoc.status = UserOrganizationStatus.ACTIVE
                await db.commit()
                logger.info("✓ 已更新为主组织关联")
            else:
                logger.info("✓ 已是主组织关联")
            return True

        # 4. 创建新的关联
        user_org = UserOrganization(
            user_id=test_user.id,
            org_id=test_org.id,
            role=UserOrganizationRole.ADMIN,
            is_primary=True,
            status=UserOrganizationStatus.ACTIVE,
            member_id=f"ADMIN-{test_user.id:03d}",
            start_date=date.today(),
            extra_data={
                "initialized_by": "init_test_user_organization.py",
                "purpose": "测试账号自动初始化"
            }
        )

        db.add(user_org)
        await db.commit()
        await db.refresh(user_org)

        logger.info(f"✓ 用户 - 组织关联创建成功!")
        logger.info(f"   用户 ID: {test_user.id}")
        logger.info(f"   组织 ID: {test_org.id}")
        logger.info(f"   角色：{user_org.role.value}")
        logger.info(f"   主组织：{user_org.is_primary}")
        logger.info(f"   成员 ID: {user_org.member_id}")

        return True

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ 初始化失败：{e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await db.close()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("开始初始化测试用户的组织关联...")
    logger.info("=" * 60)

    success = asyncio.run(init_test_user_organization())

    if success:
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ 初始化完成!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("📋 测试账号信息:")
        logger.info("   邮箱：admin@testorg.com")
        logger.info("   密码：TestAdmin123!")
        logger.info("   角色：机构管理员 (ORG_ADMIN)")
        logger.info("   组织 ID: 1 (Test Organization)")
        logger.info("")
        logger.info("🔐 登录后可访问:")
        logger.info("   http://localhost:4200/management/organization/1/dashboard")
        logger.info("=" * 60)
    else:
        logger.error("")
        logger.error("=" * 60)
        logger.error("❌ 初始化失败!")
        logger.error("=" * 60)
