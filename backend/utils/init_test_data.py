"""
数据库初始化工具
用于创建测试账号和预置数据
"""

import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.user import User, UserRole
from models.license import Organization, License, LicenseType, LicenseStatus

logger = logging.getLogger(__name__)

# 测试账号配置
TEST_ADMIN_EMAIL = "admin@testorg.com"
TEST_ADMIN_PASSWORD = "TestAdmin123!"  # 实际应该使用哈希密码
TEST_ADMIN_USERNAME = "test_admin"
TEST_ORG_NAME = "Test Organization"


def hash_password(password: str) -> str:
    """密码哈希处理"""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(password)


async def create_test_organization_async(db: AsyncSession) -> Organization:
    """创建测试组织（异步版本）"""
    try:
        # 检查是否已存在
        stmt = select(Organization).where(Organization.name == TEST_ORG_NAME)
        result = await db.execute(stmt)
        org = result.scalar_one_or_none()
        
        if org:
            logger.info(f"测试组织已存在：{org.name}")
            return org
        
        # 创建测试组织
        org = Organization(
            name=TEST_ORG_NAME,
            contact_email=TEST_ADMIN_EMAIL,
            phone="+86-138-0000-0000",
            address="测试地址",
            website="https://test.example.com",
            max_users=100,
            current_users=0,
            license_count=0,
            is_active=True
        )
        
        db.add(org)
        await db.commit()
        await db.refresh(org)
        
        logger.info(f"✓ 测试组织创建成功：{org.name} (ID: {org.id})")
        return org
        
    except Exception as e:
        await db.rollback()
        logger.error(f"创建测试组织失败：{e}")
        raise


async def create_test_admin_user_async(db: AsyncSession, organization: Organization) -> User:
    """创建测试管理员账号（异步版本）"""
    try:
        # 检查是否已存在
        stmt = select(User).where(User.email == TEST_ADMIN_EMAIL)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            logger.info(f"测试账号已存在：{user.email}")
            return user
        
        # 创建测试管理员账号
        hashed_pw = hash_password(TEST_ADMIN_PASSWORD)
        
        user = User(
            email=TEST_ADMIN_EMAIL,
            username=TEST_ADMIN_USERNAME,
            password_hash=hashed_pw,
            full_name="测试管理员",
            role=UserRole.ADMIN,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        logger.info(f"✓ 测试管理员账号创建成功：{user.email} (ID: {user.id})")
        return user
        
    except Exception as e:
        await db.rollback()
        logger.error(f"创建测试管理员账号失败：{e}")
        raise


async def create_test_license_async(db: AsyncSession, organization: Organization) -> License:
    """为测试组织创建许可证（异步版本）"""
    try:
        # 检查是否已存在
        stmt = select(License).where(
            License.organization_id == organization.id,
            License.license_type == LicenseType.CLOUD_HOSTED
        )
        result = await db.execute(stmt)
        license_obj = result.scalar_one_or_none()
        
        if license_obj:
            logger.info(f"测试许可证已存在：{license_obj.license_key}")
            return license_obj
        
        from secrets import token_urlsafe
        
        # 创建云托管版许可证
        license_obj = License(
            organization_id=organization.id,
            license_type=LicenseType.CLOUD_HOSTED,
            status=LicenseStatus.ACTIVE,
            license_key=f"TEST-{token_urlsafe(16).upper()}",
            max_users=organization.max_users,
            max_devices=10,
            features=["full_access", "api_access", "priority_support"],
            issued_at=datetime.utcnow(),
            expires_at=datetime(2099, 12, 31),  # 长期有效
            is_active=True
        )
        
        db.add(license_obj)
        
        # 更新组织的许可证计数
        organization.license_count = 1
        await db.commit()
        await db.refresh(license_obj)
        
        logger.info(f"✓ 测试许可证创建成功：{license_obj.license_key}")
        return license_obj
        
    except Exception as e:
        await db.rollback()
        logger.error(f"创建测试许可证失败：{e}")
        raise


def initialize_test_data():
    """初始化所有测试数据"""
    import asyncio
    from utils.database import AsyncSessionLocal
    
    logger.info("=" * 60)
    logger.info("开始初始化测试数据...")
    logger.info("=" * 60)
    
    async def _init():
        async with AsyncSessionLocal() as db:
            try:
                # 先导入所有模型以确保它们被注册到 Base.metadata
                # 这样可以避免关系初始化错误
                from models.course import Course
                
                # 1. 创建测试组织
                org = await create_test_organization_async(db)
                
                # 2. 创建测试管理员账号
                admin_user = await create_test_admin_user_async(db, org)
                
                # 3. 创建测试许可证
                test_license = await create_test_license_async(db, org)
                
                logger.info("=" * 60)
                logger.info("✓ 测试数据初始化完成！")
                logger.info("=" * 60)
                logger.info("")
                logger.info("📋 测试账号信息:")
                logger.info(f"   邮箱/用户名：{TEST_ADMIN_EMAIL}")
                logger.info(f"   密码：{TEST_ADMIN_PASSWORD}")
                logger.info(f"   角色：机构管理员 (ADMIN)")
                logger.info("")
                logger.info(f"🏢 测试组织信息:")
                logger.info(f"   名称：{org.name}")
                logger.info(f"   ID: {org.id}")
                logger.info("")
                logger.info(f"🎫 测试许可证信息:")
                logger.info(f"   类型：云托管版 (CLOUD_HOSTED)")
                logger.info(f"   密钥：{test_license.license_key}")
                logger.info(f"   有效期至：2099-12-31")
                logger.info("")
                logger.info("⚠️ 警告：测试账号仅用于开发环境，生产环境请禁用！")
                logger.info("=" * 60)
                
            except Exception as e:
                await db.rollback()
                logger.error(f"❌ 测试数据初始化失败：{e}")
                import traceback
                traceback.print_exc()
                raise
    
    asyncio.run(_init())
