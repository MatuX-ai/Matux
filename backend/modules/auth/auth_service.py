"""
统一认证服务
支持手机号注册/登录、JWT签发/验证、家长绑定学生
作为 iMato 统一身份认证中心的核心服务
"""

import re
from datetime import datetime, timedelta
from typing import Optional, List

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from models.user import User, UserRole
from models.user_guardian import UserGuardian


def hash_password(password: str) -> str:
    """密码哈希"""
    return bcrypt.hashpw(
        password.encode("utf-8")[:72], bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(
        plain_password.encode("utf-8")[:72],
        hashed_password.encode("utf-8") if isinstance(hashed_password, str) else hashed_password,
    )


def validate_phone(phone: str) -> bool:
    """验证手机号格式（中国大陆）"""
    pattern = r"^1[3-9]\d{9}$"
    return bool(re.match(pattern, phone))


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """创建JWT访问令牌"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """创建刷新令牌（7天有效期）"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """解码JWT令牌"""
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError:
        return None


class UnifiedAuthService:
    """统一认证服务"""

    # ============ 注册 ============

    async def register_by_phone(
        self,
        db: AsyncSession,
        phone: str,
        password: str,
        username: Optional[str] = None,
        role: str = "student",
    ) -> User:
        """手机号注册"""
        if not validate_phone(phone):
            raise ValueError("手机号格式不正确")

        # 检查手机号是否已注册
        stmt = select(User).filter(User.phone == phone)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("该手机号已注册")

        # 生成用户名（如果未提供）
        if not username:
            username = f"user_{phone[-6:]}"
            # 确保用户名唯一
            counter = 0
            while True:
                check_stmt = select(User).filter(User.username == username)
                check_result = await db.execute(check_stmt)
                if not check_result.scalar_one_or_none():
                    break
                counter += 1
                username = f"user_{phone[-6:]}_{counter}"

        # 验证角色
        try:
            user_role = UserRole(role)
        except ValueError:
            user_role = UserRole.STUDENT

        # 创建用户
        user = User(
            username=username,
            phone=phone,
            email=None,
            hashed_password=hash_password(password),
            role=user_role,
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def register_by_email(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        username: str,
        role: str = "student",
    ) -> User:
        """邮箱注册（兼容旧接口）"""
        # 检查邮箱
        stmt = select(User).filter(User.email == email)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("该邮箱已注册")

        # 检查用户名
        stmt = select(User).filter(User.username == username)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("该用户名已存在")

        try:
            user_role = UserRole(role)
        except ValueError:
            user_role = UserRole.STUDENT

        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=user_role,
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    # ============ 登录 ============

    async def login_by_phone(
        self, db: AsyncSession, phone: str, password: str
    ) -> Optional[dict]:
        """手机号+密码登录，返回令牌"""
        stmt = select(User).filter(User.phone == phone)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            raise ValueError("账户已被禁用")

        return await self._generate_token_pair(db, user)

    async def login_by_username(
        self, db: AsyncSession, username: str, password: str
    ) -> Optional[dict]:
        """用户名+密码登录（兼容旧接口），返回令牌"""
        stmt = select(User).filter(
            or_(User.username == username, User.email == username)
        )
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            raise ValueError("账户已被禁用")

        return await self._generate_token_pair(db, user)

    async def _generate_token_pair(
        self, db: AsyncSession, user: User
    ) -> dict:
        """生成令牌对"""
        # 获取用户组织关联
        org_ids = await self._get_user_org_ids(db, user.id)

        payload = {
            "sub": str(user.id),
            "username": user.username,
            "phone": user.phone,
            "role": user.role.value if user.role else "user",
            "org_ids": org_ids,
        }

        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user.to_dict(),
        }

    async def _get_user_org_ids(
        self, db: AsyncSession, user_id: int
    ) -> List[int]:
        """获取用户所属组织ID列表"""
        try:
            from models.user_organization import UserOrganization

            stmt = select(UserOrganization.org_id).filter(
                UserOrganization.user_id == user_id,
                UserOrganization.is_active == True,
            )
            result = await db.execute(stmt)
            return [row[0] for row in result.fetchall() if row[0] is not None]
        except Exception:
            return []

    # ============ Token刷新 ============

    async def refresh_access_token(
        self, db: AsyncSession, refresh_token: str
    ) -> Optional[dict]:
        """刷新访问令牌"""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        stmt = select(User).filter(User.id == int(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            return None

        return await self._generate_token_pair(db, user)

    # ============ 家长绑定学生 ============

    async def bind_child(
        self,
        db: AsyncSession,
        parent_id: int,
        student_phone: str,
        relationship: Optional[str] = None,
        is_primary: bool = False,
    ) -> UserGuardian:
        """家长绑定学生"""
        # 查找学生
        stmt = select(User).filter(
            User.phone == student_phone, User.role == UserRole.STUDENT
        )
        result = await db.execute(stmt)
        student = result.scalar_one_or_none()

        if not student:
            raise ValueError("未找到该学生账号，请确认手机号正确且已注册为学生角色")

        # 检查是否已绑定
        stmt = select(UserGuardian).filter(
            UserGuardian.guardian_id == parent_id,
            UserGuardian.student_id == student.id,
            UserGuardian.is_active == True,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError("该学生已绑定，请勿重复操作")

        # 创建绑定
        guardian_link = UserGuardian(
            student_id=student.id,
            guardian_id=parent_id,
            relation_type=relationship,
            is_primary=is_primary,
        )
        db.add(guardian_link)
        await db.commit()
        await db.refresh(guardian_link)
        return guardian_link

    async def get_bound_children(
        self, db: AsyncSession, parent_id: int
    ) -> List[dict]:
        """获取家长绑定的所有学生"""
        stmt = (
            select(UserGuardian, User)
            .join(User, UserGuardian.student_id == User.id)
            .filter(
                UserGuardian.guardian_id == parent_id,
                UserGuardian.is_active == True,
            )
        )
        result = await db.execute(stmt)
        rows = result.all()

        return [
            {
                "guardian_link_id": link.id,
                "student_id": student.id,
                "student_name": student.username,
                "student_phone": student.phone,
                "relationship": link.relation_type,
                "is_primary": link.is_primary,
            }
            for link, student in rows
        ]

    async def get_guardians(
        self, db: AsyncSession, student_id: int
    ) -> List[dict]:
        """获取学生的所有监护人"""
        stmt = (
            select(UserGuardian, User)
            .join(User, UserGuardian.guardian_id == User.id)
            .filter(
                UserGuardian.student_id == student_id,
                UserGuardian.is_active == True,
            )
        )
        result = await db.execute(stmt)
        rows = result.all()

        return [
            {
                "guardian_link_id": link.id,
                "guardian_id": guardian.id,
                "guardian_name": guardian.username,
                "guardian_phone": guardian.phone,
                "relationship": link.relation_type,
                "is_primary": link.is_primary,
            }
            for link, guardian in rows
        ]

    async def unbind_child(
        self, db: AsyncSession, parent_id: int, student_id: int
    ) -> bool:
        """解绑学生"""
        stmt = select(UserGuardian).filter(
            UserGuardian.guardian_id == parent_id,
            UserGuardian.student_id == student_id,
            UserGuardian.is_active == True,
        )
        result = await db.execute(stmt)
        link = result.scalar_one_or_none()

        if not link:
            return False

        link.is_active = False
        await db.commit()
        return True


# 全局服务实例
unified_auth_service = UnifiedAuthService()
