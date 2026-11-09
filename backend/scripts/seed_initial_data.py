#!/usr/bin/env python3
"""桌面端首启种子数据：默认演示账号 + 最小可用课程内容。

背景（上线硬伤之二）：
    安装包不再随包分发 backend/ai_service.db —— 那是开发库，含开发期个人学习记录。
    首次启动由 create_all 建空库后，本模块负责补齐「能登录、有课可上」的最小数据集。

安全边界（幂等 + 不覆盖用户数据）：
    1. 演示账号仅在建库后的空库（users 表为空）时创建，密码只在创建时写入一次；
       已存在的账号绝不重置密码，避免把用户自设密码改回默认值。
    2. 课程内容仅在 courses 表为空时导入；已有数据的库直接跳过。
    3. 任何失败都不阻断后端启动（返回报告中标记 skipped/err），用户仍可注册后使用。

命令行用法（开发/运维手动初始化）：
    cd backend && python -m scripts.seed_initial_data --report
"""

import argparse
import asyncio
from typing import Any, Dict

import bcrypt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# 显式导入种子链条需要的 ORM 模型，保证 Base.metadata 覆盖到这些表
# （冻结态下 main_ai_edu 会先导入本模块再 create_all）
import models.achievement as _achievement  # noqa: F401
import models.course as _course  # noqa: F401
import models.leaderboard as _leaderboard  # noqa: F401
import models.learning_source as _learning_source  # noqa: F401
import models.organization as _organization  # noqa: F401
import models.recommendation as _recommendation  # noqa: F401
import models.unified_learning_record as _learning_record  # noqa: F401
import models.user as _user  # noqa: F401
import models.user_organization as _user_org  # noqa: F401

# 默认演示账号（与 create_test_accounts.py 保持同一套口令约定）
DEFAULT_ACCOUNTS = [
    {
        "username": "test_admin",
        "email": "admin@testorg.com",
        "password": "TestAdmin123!",
        "role": "admin",
    },
    {
        "username": "test_teacher",
        "email": "teacher@testorg.com",
        "password": "TestTeacher123!",
        "role": "teacher",
    },
    {
        "username": "test_student",
        "email": "student@testorg.com",
        "password": "TestStudent123!",
        "role": "student",
    },
]


def hash_password(raw: str) -> str:
    """与 auth_routes 一致：bcrypt 直接哈希（截断到 72 字节）。"""
    return bcrypt.hashpw(raw.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode("utf-8")[:72], (hashed or "").encode("utf-8"))
    except (ValueError, TypeError):
        return False


async def _count(db: AsyncSession, model: Any) -> int:
    result = await db.execute(select(func.count()).select_from(model))
    return int(result.scalar() or 0)


async def ensure_default_accounts(db: AsyncSession) -> int:
    """空库时创建 3 个演示账号（已存在则跳过，不修改密码）。"""
    from models.user import User, UserRole

    created = 0
    for acc in DEFAULT_ACCOUNTS:
        stmt = select(User).where(User.username == acc["username"])
        if (await db.execute(stmt)).scalar_one_or_none() is not None:
            continue
        db.add(
            User(
                username=acc["username"],
                email=acc["email"],
                hashed_password=hash_password(acc["password"]),
                role=UserRole(acc["role"]),
                is_active=True,
                is_superuser=False,
            )
        )
        created += 1
    if created:
        await db.commit()
    return created


async def seed_initial_data(force_content: bool = False) -> Dict[str, Any]:
    """补齐首启数据，返回执行报告（永不抛异常给调用方处理之外的路径）。"""
    from models.course import Course
    from models.user import User
    from scripts.seed_demo_data import seed_test_student_data
    from utils.database import AsyncSessionLocal

    report: Dict[str, Any] = {
        "users_before": 0,
        "accounts_created": 0,
        "courses_before": 0,
        "content_seeded": False,
    }

    async with AsyncSessionLocal() as db:
        report["users_before"] = await _count(db, User)
        report["courses_before"] = await _count(db, Course)
        # 仅全新空库才注入演示账号，避免污染用户已在使用中的库
        if report["users_before"] == 0:
            report["accounts_created"] = await ensure_default_accounts(db)

    if report["courses_before"] == 0 or force_content:
        report["content_seeded"] = bool(await seed_test_student_data())

    return report


def seed_initial_data_sync(force_content: bool = False) -> Dict[str, Any]:
    """同步入口（供 main_ai_edu 等非 async 启动路径调用）。"""
    return asyncio.run(seed_initial_data(force_content=force_content))


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化 iMato 首启种子数据")
    parser.add_argument(
        "--force-content",
        action="store_true",
        help="即使课程已存在也重新导入演示内容（幂等逻辑会跳过重复记录）",
    )
    parser.add_argument("--report", action="store_true", help="仅打印执行报告")
    args = parser.parse_args()

    report = seed_initial_data_sync(force_content=args.force_content)
    print(f"[seed] 执行报告: {report}")

    if args.report:
        print(
            "[seed] 账号: test_admin/TestAdmin123!, "
            "test_teacher/TestTeacher123!, test_student/TestStudent123!"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
