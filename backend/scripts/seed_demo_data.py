#!/usr/bin/env python3
"""
test_student 冷启动数据脚本

为 test_student 填充完整的业务数据，覆盖以下 14+ 张表：
1. organizations         - 测试组织（复用）
2. users                 - 测试账号（复用 test_admin/teacher/student）
3. user_organizations    - 用户-组织关联
4. learning_sources      - 3 个学习来源（校本部/创新机器人/兴趣班）
5. courses               - 8 门课程（4 学科 × 3 难度）
6. course_lessons        - ~36 个课时
7. course_enrollments    - 3 门报名
8. course_assignments    - ~18 个作业
9. unified_learning_records - 78 条 30 天学习记录
10. achievements         - 20 个成就定义（可选，try/except）
11. user_achievements    - 8 个已解锁
12. user_points          - 1250 总积分
13. points_transactions  - 30 条流水
14. leaderboard_records  - 20 条周榜 + 20 条总榜
15. user_learning_profiles - 用户画像
16. recommendation_records - 3 条推荐

幂等性：每次插入前 select 检查，已存在则跳过。
执行结果输出统计报告。
"""

import asyncio
import logging
import random
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from utils.database import AsyncSessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("seed_demo")


# =============================================================================
# 常量配置
# =============================================================================

TEST_ORG_NAME = "Test Organization"
TEST_STUDENT_USERNAME = "test_student"
TEST_TEACHER_USERNAME = "test_teacher"
TEST_ADMIN_USERNAME = "test_admin"

# 8 门课程定义（4 学科 × 3 难度）
COURSES_DATA: List[Dict[str, Any]] = [
    {
        "title": "机器人基础入门：让积木动起来",
        "description": "通过乐高 WeDo 2.0 套装，学习电机、传感器和简单编程，让你的积木作品真正动起来。",
        "category": "robotics",
        "difficulty": "beginner",
        "duration_minutes": 360,
        "tags": ["机器人", "积木", "入门"],
        "source_idx": 0,  # 校本部
    },
    {
        "title": "Python 编程入门：和计算机会话",
        "description": "从 print() 到 for 循环，用 Python 与计算机交朋友，适合零基础的同学。",
        "category": "programming",
        "difficulty": "beginner",
        "duration_minutes": 480,
        "tags": ["Python", "编程", "入门"],
        "source_idx": 0,
    },
    {
        "title": "AI 编程与机器学习初探",
        "description": "用 scikit-learn 训练你的第一个分类模型，理解 AI 是怎么'学习'的。",
        "category": "ai",
        "difficulty": "intermediate",
        "duration_minutes": 600,
        "tags": ["AI", "机器学习", "Python"],
        "source_idx": 0,
    },
    {
        "title": "ROS 机器人操作系统实战",
        "description": "学习工业级机器人开发框架 ROS，掌握节点、话题、服务三大核心概念。",
        "category": "robotics",
        "difficulty": "advanced",
        "duration_minutes": 720,
        "tags": ["ROS", "机器人", "高级"],
        "source_idx": 1,  # 创新机器人
    },
    {
        "title": "3D 建模与打印：从创意到实物",
        "description": "用 Tinkercad 设计你的第一个 3D 模型，并发送到 3D 打印机把它变出来。",
        "category": "engineering",
        "difficulty": "intermediate",
        "duration_minutes": 480,
        "tags": ["3D打印", "建模", "工程"],
        "source_idx": 2,  # 兴趣班
    },
    {
        "title": "数学建模基础：用方程解决真实问题",
        "description": "从鸡兔同笼到疫情防控，学习如何把生活问题翻译成数学方程。",
        "category": "math",
        "difficulty": "intermediate",
        "duration_minutes": 420,
        "tags": ["数学", "建模", "方程"],
        "source_idx": 0,
    },
    {
        "title": "创意艺术编程：用代码画画",
        "description": "用 Processing / p5.js 创作生成艺术，让代码成为画笔。",
        "category": "arts",
        "difficulty": "beginner",
        "duration_minutes": 360,
        "tags": ["艺术", "Processing", "创意"],
        "source_idx": 2,
    },
    {
        "title": "智能硬件与物联网：让物品联网",
        "description": "用 Arduino + ESP8266，把温湿度传感器数据上传到云端仪表板。",
        "category": "electronics",
        "difficulty": "advanced",
        "duration_minutes": 600,
        "tags": ["物联网", "Arduino", "硬件"],
        "source_idx": 1,
    },
]

# 课时模板（按课程类型生成）
LESSON_TEMPLATES = {
    "robotics": [
        "第 1 课：认识电机和齿轮",
        "第 2 课：搭建第一个小车",
        "第 3 课：让小车动起来",
        "第 4 课：超声波避障",
        "第 5 课：巡线小车项目",
        "第 6 课：综合挑战赛",
    ],
    "programming": [
        "第 1 课：print() 与变量",
        "第 2 课：if 条件语句",
        "第 3 课：for 循环与 while 循环",
        "第 4 课：列表与字典",
        "第 5 课：函数与模块",
        "第 6 课：综合项目 - 猜数字游戏",
    ],
    "ai": [
        "第 1 课：什么是机器学习",
        "第 2 课：准备你的第一个数据集",
        "第 3 课：训练一个分类器",
        "第 4 课：评估模型表现",
        "第 5 课：调参与优化",
    ],
    "math": [
        "第 1 课：从问题到方程",
        "第 2 课：鸡兔同笼问题",
        "第 3 课：函数与图像",
        "第 4 课：概率初步",
    ],
    "engineering": [
        "第 1 课：Tinkercad 入门",
        "第 2 课：基本几何体建模",
        "第 3 课：组合与布尔运算",
        "第 4 课：从模型到切片",
        "第 5 课：打印与后处理",
    ],
    "arts": [
        "第 1 课：Processing 开发环境",
        "第 2 课：基本图形与颜色",
        "第 3 课：动画与运动",
        "第 4 课：交互与鼠标事件",
        "第 5 课：创作你的生成艺术",
    ],
    "electronics": [
        "第 1 课：Arduino 基础",
        "第 2 课：数字与模拟信号",
        "第 3 课：传感器读取",
        "第 4 课：ESP8266 联网",
        "第 5 课：MQTT 协议",
        "第 6 课：云端仪表板",
    ],
}

# 3 个学习来源
LEARNING_SOURCES_DATA: List[Dict[str, Any]] = [
    {
        "source_type": "school_curriculum",
        "name": "示范实验学校 - STEM 课程",
        "is_primary": True,
        "notes": "校本 STEM 课程（主来源）",
    },
    {
        "source_type": "institution",
        "name": "创新机器人培训中心",
        "is_primary": False,
        "notes": "校外机器人培训",
    },
    {
        "source_type": "school_interest",
        "name": "校内 STEAM 兴趣班",
        "is_primary": False,
        "notes": "每周四下午的兴趣班",
    },
]

# 20 个成就定义（5 分类 × 4 难度）
ACHIEVEMENTS_DATA: List[Dict[str, Any]] = [
    # learning 分类
    {
        "name": "初入编程",
        "description": "完成第一行代码",
        "category": "learning",
        "achievement_type": "single",
        "badge_icon": "/badges/first_step.png",
        "badge_color": "#10b981",
        "badge_rarity": "common",
        "unlock_condition": {"type": "single", "event": "first_code_run"},
        "points_reward": 50,
    },
    {
        "name": "Python 入门",
        "description": "完成 Python 入门课程",
        "category": "learning",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/python_beginner.png",
        "badge_color": "#0ea5e9",
        "badge_rarity": "rare",
        "unlock_condition": {"type": "cumulative", "metric": "python_lessons_completed", "threshold": 6},
        "points_reward": 150,
    },
    {
        "name": "7 天坚持",
        "description": "连续 7 天学习打卡",
        "category": "learning",
        "achievement_type": "sequence",
        "badge_icon": "/badges/streak_7.png",
        "badge_color": "#f59e0b",
        "badge_rarity": "rare",
        "unlock_condition": {"type": "sequence", "metric": "consecutive_days", "threshold": 7},
        "points_reward": 200,
    },
    {
        "name": "30 天传说",
        "description": "连续 30 天学习打卡",
        "category": "learning",
        "achievement_type": "sequence",
        "badge_icon": "/badges/streak_30.png",
        "badge_color": "#b45309",
        "badge_rarity": "legendary",
        "unlock_condition": {"type": "sequence", "metric": "consecutive_days", "threshold": 30},
        "points_reward": 1000,
    },
    # coding 分类
    {
        "name": "代码新手",
        "description": "成功运行第一个程序",
        "category": "coding",
        "achievement_type": "single",
        "badge_icon": "/badges/code_newbie.png",
        "badge_color": "#94a3b8",
        "badge_rarity": "common",
        "unlock_condition": {"type": "single", "event": "code_executed", "count": 1},
        "points_reward": 50,
    },
    {
        "name": "积木高手",
        "description": "完成 5 个机器人项目",
        "category": "coding",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/lego_master.png",
        "badge_color": "#3b82f6",
        "badge_rarity": "rare",
        "unlock_condition": {"type": "cumulative", "metric": "robotics_projects", "threshold": 5},
        "points_reward": 200,
    },
    {
        "name": "Bug 猎手",
        "description": "解决 20 个代码 bug",
        "category": "coding",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/bug_hunter.png",
        "badge_color": "#7c3aed",
        "badge_rarity": "epic",
        "unlock_condition": {"type": "cumulative", "metric": "bugs_fixed", "threshold": 20},
        "points_reward": 300,
    },
    {
        "name": "项目达人",
        "description": "完成 3 个完整实战项目",
        "category": "coding",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/project_pro.png",
        "badge_color": "#b45309",
        "badge_rarity": "legendary",
        "unlock_condition": {"type": "cumulative", "metric": "projects_completed", "threshold": 3},
        "points_reward": 500,
    },
    # quiz 分类
    {
        "name": "测验达人",
        "description": "完成 10 次小测验",
        "category": "quiz",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/quiz_pro.png",
        "badge_color": "#94a3b8",
        "badge_rarity": "common",
        "unlock_condition": {"type": "cumulative", "metric": "quizzes_taken", "threshold": 10},
        "points_reward": 80,
    },
    {
        "name": "满分 5 次",
        "description": "5 次测验拿到满分",
        "category": "quiz",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/perfect_5.png",
        "badge_color": "#3b82f6",
        "badge_rarity": "rare",
        "unlock_condition": {"type": "cumulative", "metric": "perfect_quizzes", "threshold": 5},
        "points_reward": 250,
    },
    {
        "name": "挑战者",
        "description": "挑战 1 道高难度题",
        "category": "quiz",
        "achievement_type": "single",
        "badge_icon": "/badges/challenger.png",
        "badge_color": "#7c3aed",
        "badge_rarity": "epic",
        "unlock_condition": {"type": "single", "event": "hard_question_solved"},
        "points_reward": 200,
    },
    {
        "name": "冠军",
        "description": "单周排行榜第一名",
        "category": "quiz",
        "achievement_type": "single",
        "badge_icon": "/badges/champion.png",
        "badge_color": "#b45309",
        "badge_rarity": "legendary",
        "unlock_condition": {"type": "single", "event": "weekly_first_place"},
        "points_reward": 800,
    },
    # social 分类
    {
        "name": "分享达人",
        "description": "分享作品 5 次",
        "category": "social",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/sharer.png",
        "badge_color": "#94a3b8",
        "badge_rarity": "common",
        "unlock_condition": {"type": "cumulative", "metric": "shares_count", "threshold": 5},
        "points_reward": 60,
    },
    {
        "name": "小组长",
        "description": "创建 1 个学习小组",
        "category": "social",
        "achievement_type": "single",
        "badge_icon": "/badges/leader.png",
        "badge_color": "#3b82f6",
        "badge_rarity": "rare",
        "unlock_condition": {"type": "single", "event": "group_created"},
        "points_reward": 150,
    },
    {
        "name": "导师",
        "description": "帮助 10 位同学解答问题",
        "category": "social",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/mentor.png",
        "badge_color": "#7c3aed",
        "badge_rarity": "epic",
        "unlock_condition": {"type": "cumulative", "metric": "helps_provided", "threshold": 10},
        "points_reward": 300,
    },
    {
        "name": "百日传说",
        "description": "累计登录 100 天",
        "category": "social",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/centurion.png",
        "badge_color": "#b45309",
        "badge_rarity": "legendary",
        "unlock_condition": {"type": "cumulative", "metric": "total_active_days", "threshold": 100},
        "points_reward": 2000,
    },
    # special 分类
    {
        "name": "首位学生",
        "description": "成为平台首位学生用户",
        "category": "special",
        "achievement_type": "single",
        "badge_icon": "/badges/first_student.png",
        "badge_color": "#94a3b8",
        "badge_rarity": "common",
        "unlock_condition": {"type": "single", "event": "first_user_signup"},
        "points_reward": 100,
    },
    {
        "name": "早期支持者",
        "description": "平台上线首月加入",
        "category": "special",
        "achievement_type": "single",
        "badge_icon": "/badges/early_adopter.png",
        "badge_color": "#3b82f6",
        "badge_rarity": "rare",
        "unlock_condition": {"type": "single", "event": "early_adopter"},
        "points_reward": 200,
    },
    {
        "name": "反馈专家",
        "description": "提交 5 条有意义的反馈",
        "category": "special",
        "achievement_type": "cumulative",
        "badge_icon": "/badges/feedback.png",
        "badge_color": "#7c3aed",
        "badge_rarity": "epic",
        "unlock_condition": {"type": "cumulative", "metric": "feedback_submitted", "threshold": 5},
        "points_reward": 250,
    },
    {
        "name": "?????",
        "description": "隐藏成就",
        "category": "special",
        "achievement_type": "hidden",
        "badge_icon": "/badges/hidden.png",
        "badge_color": "#1c1917",
        "badge_rarity": "legendary",
        "unlock_condition": {"type": "hidden", "event": "secret_action"},
        "points_reward": 500,
        "is_hidden": True,
    },
]


# =============================================================================
# 工具函数
# =============================================================================

async def get_or_create_organization(db, name: str = TEST_ORG_NAME):
    """获取或创建测试组织"""
    from models.organization import Organization

    stmt = select(Organization).where(Organization.name == name)
    result = await db.execute(stmt)
    org = result.scalar_one_or_none()
    if org:
        logger.info(f"  ✓ 组织已存在：{org.name} (id={org.id})")
        return org

    org = Organization(
        name=name,
        code="TEST-ORG",
        description="iMato 测试组织",
        is_active=True,
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)
    logger.info(f"  ✓ 组织已创建：{org.name} (id={org.id})")
    return org


async def get_user_by_username(db, username: str):
    """通过用户名获取用户"""
    from models.user import User

    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_user_org(db, user, org, role_value: str = "STUDENT", is_primary: bool = False):
    """获取或创建用户-组织关联"""
    from models.user_organization import (
        UserOrganization,
        UserOrganizationRole,
        UserOrganizationStatus,
    )

    stmt = select(UserOrganization).where(
        UserOrganization.user_id == user.id,
        UserOrganization.org_id == org.id,
    )
    result = await db.execute(stmt)
    assoc = result.scalar_one_or_none()
    if assoc:
        return assoc

    role_map = {
        "ADMIN": UserOrganizationRole.ADMIN,
        "TEACHER": UserOrganizationRole.TEACHER,
        "STUDENT": UserOrganizationRole.STUDENT,
        "PARENT": UserOrganizationRole.PARENT,
    }
    # 默认回退：未识别角色按 STUDENT 处理（避免 MEMBER/PARENT 缺失时崩溃）
    role_enum = role_map.get(role_value, UserOrganizationRole.STUDENT)
    assoc = UserOrganization(
        user_id=user.id,
        org_id=org.id,
        role=role_enum,
        is_primary=is_primary,
        status=UserOrganizationStatus.ACTIVE,
    )
    db.add(assoc)
    await db.commit()
    await db.refresh(assoc)
    return assoc


# =============================================================================
# 主流程
# =============================================================================

async def seed_organizations(db, student, teacher, admin):
    """创建/获取组织"""
    org = await get_or_create_organization(db)
    # 关联 3 个用户到组织
    await get_or_create_user_org(db, admin, org, "ADMIN", is_primary=True)
    await get_or_create_user_org(db, teacher, org, "TEACHER", is_primary=False)
    await get_or_create_user_org(db, student, org, "STUDENT", is_primary=False)
    return {"organization": org}


async def seed_learning_sources(db, student, org):
    """创建 3 个学习来源"""
    from models.learning_source import (
        LearningSource,
        LearningSourceStatus,
        LearningSourceType,
    )

    created = []
    for source_data in LEARNING_SOURCES_DATA:
        stmt = select(LearningSource).where(
            LearningSource.user_id == student.id,
            LearningSource.name == source_data["name"],
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            created.append(existing)
            continue

        source = LearningSource(
            user_id=student.id,
            org_id=org.id if source_data["is_primary"] else org.id,
            source_type=LearningSourceType(source_data["source_type"]),
            status=LearningSourceStatus.ACTIVE,
            name=source_data["name"],
            source_detail={
                "role": "student",
                "initialized_by": "seed_demo_data.py",
            },
            start_date=date.today() - timedelta(days=120),
            role="student",
            is_primary=source_data["is_primary"],
            notes=source_data["notes"],
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)
        created.append(source)

    return created


async def seed_courses(db, teacher, org, sources):
    """创建 8 门课程"""
    from models.course import Course

    course_ids = []
    created_courses = []
    for idx, course_data in enumerate(COURSES_DATA):
        stmt = select(Course).where(Course.title == course_data["title"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            course_ids.append(existing.id)
            created_courses.append(existing)
            continue

        source_idx = course_data.get("source_idx", 0)
        source = sources[source_idx] if source_idx < len(sources) else None

        course = Course(
            title=course_data["title"],
            description=course_data["description"],
            cover_image_url=f"/covers/course_{idx + 1}.jpg",
            category=course_data["category"],
            difficulty=course_data["difficulty"],
            duration_minutes=course_data["duration_minutes"],
            status="published",
            teacher_id=teacher.id,
            org_id=org.id,
            tags=course_data["tags"],
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=90 - idx * 5),
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
        course_ids.append(course.id)
        created_courses.append(course)

    return created_courses


async def seed_lessons(db, courses):
    """为每门课程创建 4-6 个课时"""
    from models.course import CourseLesson

    created = 0
    for course in courses:
        lessons = LESSON_TEMPLATES.get(course.category, [
            f"第 {i + 1} 课：{course.title} - 单元 {i + 1}"
            for i in range(4)
        ])
        for order_idx, lesson_title in enumerate(lessons):
            stmt = select(CourseLesson).where(
                CourseLesson.course_id == course.id,
                CourseLesson.order_index == order_idx,
            )
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                continue

            lesson = CourseLesson(
                course_id=course.id,
                title=lesson_title,
                description=f"{course.title} 课程的第 {order_idx + 1} 单元",
                order_index=order_idx,
                duration_minutes=course.duration_minutes // max(len(lessons), 1),
                content_type="video" if order_idx % 3 != 2 else "project",
                content_url=f"/lessons/{course.id}_{order_idx + 1}.mp4",
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=80 - order_idx),
            )
            db.add(lesson)
            created += 1
        await db.commit()
    return created


async def seed_assignments(db, courses):
    """为每门课程创建 2-3 个作业"""
    from models.course import CourseAssignment

    assignment_titles = [
        "课后练习：基础概念回顾",
        "动手项目：综合应用挑战",
        "单元测验：检验学习成果",
    ]
    created = 0
    for course in courses:
        num_assignments = random.randint(2, 3)
        for i in range(num_assignments):
            stmt = select(CourseAssignment).where(
                CourseAssignment.course_id == course.id,
                CourseAssignment.title == assignment_titles[i],
            )
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                continue

            assignment = CourseAssignment(
                course_id=course.id,
                title=assignment_titles[i],
                description=f"完成 {course.title} 的 {assignment_titles[i]}",
                assignment_type=["homework", "project", "quiz"][i],
                max_score=100.0,
                pass_score=60.0,
                deadline=datetime.utcnow() + timedelta(days=14),
                is_required=True,
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=20 + i),
            )
            db.add(assignment)
            created += 1
        await db.commit()
    return created


async def seed_enrollments(db, student, courses, sources):
    """创建 3 门报名：75% / 100% / 30% 进度"""
    from models.course import CourseEnrollment

    progress_map = [0.75, 1.0, 0.30]
    created = 0
    # 选择 3 门课程报名（按 category 排序的初中高）
    selected_courses = []
    for cat in ["robotics", "programming", "ai"]:
        for c in courses:
            if c.category == cat:
                selected_courses.append(c)
                break

    for i, course in enumerate(selected_courses[:3]):
        source = sources[i % len(sources)]
        stmt = select(CourseEnrollment).where(
            CourseEnrollment.user_id == student.id,
            CourseEnrollment.course_id == course.id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            continue

        progress = progress_map[i]
        completed = progress >= 1.0
        enrollment = CourseEnrollment(
            user_id=student.id,
            course_id=course.id,
            learning_source_id=source.id,
            org_id=source.org_id,
            progress_percentage=progress * 100,
            score=95.5 if completed else None,
            status="completed" if completed else "active",
            enrolled_at=datetime.utcnow() - timedelta(days=60 - i * 10),
            completed_at=datetime.utcnow() - timedelta(days=5) if completed else None,
        )
        db.add(enrollment)
        created += 1
    await db.commit()
    return created


async def seed_learning_records(db, student, sources, courses):
    """创建 30 天 × 2-3 条学习记录（热力图数据）"""
    from models.unified_learning_record import (
        LearningRecordStatus,
        UnifiedLearningRecord,
    )

    # 先找已存在的数量
    stmt = select(func.count(UnifiedLearningRecord.id)).where(
        UnifiedLearningRecord.user_id == student.id
    )
    result = await db.execute(stmt)
    existing_count = result.scalar() or 0
    if existing_count >= 60:
        logger.info(f"  ⏭ 已有 {existing_count} 条学习记录，跳过")
        return 0

    created = 0
    status_choices = [
        LearningRecordStatus.COMPLETED,
        LearningRecordStatus.IN_PROGRESS,
        LearningRecordStatus.COMPLETED,
        LearningRecordStatus.COMPLETED,
    ]
    for day_offset in range(30):
        # 模拟真实学习模式：周末更多，工作日较少
        weekday = (datetime.utcnow() - timedelta(days=day_offset)).weekday()
        records_today = random.randint(1, 3) if weekday < 5 else random.randint(2, 3)
        for _ in range(records_today):
            course = random.choice(courses)
            source = random.choice(sources)
            status = random.choice(status_choices)
            progress = random.uniform(60, 100) if status == LearningRecordStatus.COMPLETED else random.uniform(10, 80)
            minutes = random.randint(15, 60)
            score = random.uniform(70, 100) if status == LearningRecordStatus.COMPLETED else None

            record = UnifiedLearningRecord(
                user_id=student.id,
                course_id=course.id,
                learning_source_id=source.id,
                enrollment_id=None,
                status=status,
                progress_percentage=progress,
                total_time_minutes=minutes,
                score=score,
                max_score=100.0,
                grade_letter="A" if score and score >= 90 else "B" if score and score >= 80 else "C" if score else None,
                completion_date=datetime.utcnow() - timedelta(days=day_offset) if status == LearningRecordStatus.COMPLETED else None,
                activity_detail={
                    "device": "desktop",
                    "browser": "Chrome",
                    "session_type": "self_study",
                },
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=day_offset),
            )
            db.add(record)
            created += 1
    await db.commit()
    return created


async def seed_achievements(db, student):
    """尝试创建 20 个成就 + 8 个 user_achievements"""
    try:
        from models.achievement import Achievement, AchievementCategory, AchievementType, UserAchievement
    except Exception as e:
        logger.warning(f"  ⚠️ 跳过成就数据：{e}")
        return 0, 0

    achievement_ids = []
    created_achievements = 0
    for ach_data in ACHIEVEMENTS_DATA:
        stmt = select(Achievement).where(Achievement.name == ach_data["name"])
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            achievement_ids.append(existing.id)
            continue

        try:
            ach = Achievement(
                name=ach_data["name"],
                description=ach_data["description"],
                category=AchievementCategory(ach_data["category"]),
                achievement_type=AchievementType(ach_data["achievement_type"]),
                badge_icon=ach_data["badge_icon"],
                badge_color=ach_data["badge_color"],
                badge_rarity=ach_data["badge_rarity"],
                unlock_condition=ach_data["unlock_condition"],
                points_reward=ach_data["points_reward"],
                is_hidden=ach_data.get("is_hidden", False),
                is_active=True,
                display_order=len(achievement_ids),
            )
            db.add(ach)
            await db.commit()
            await db.refresh(ach)
            achievement_ids.append(ach.id)
            created_achievements += 1
        except SQLAlchemyError as e:
            logger.warning(f"  ⚠️ 成就 {ach_data['name']} 插入失败：{e}")
            await db.rollback()
            continue

    # 8 个已解锁（取前 8 个非隐藏）
    unlocked_count = 0
    for i, ach_id in enumerate(achievement_ids[:8]):
        stmt = select(UserAchievement).where(
            UserAchievement.user_id == student.id,
            UserAchievement.achievement_id == ach_id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            continue

        try:
            ua = UserAchievement(
                user_id=student.id,
                achievement_id=ach_id,
                progress=100.0,
                current_value=1,
                target_value=1,
                is_unlocked=True,
                is_claimed=True,
                unlocked_at=datetime.utcnow() - timedelta(days=20 - i),
                notification_sent=True,
                extra_metadata={"unlocked_via": "seed_demo"},
            )
            db.add(ua)
            unlocked_count += 1
        except SQLAlchemyError as e:
            logger.warning(f"  ⚠️ user_achievement 插入失败：{e}")
            await db.rollback()
    await db.commit()
    return created_achievements, unlocked_count


async def seed_points(db, student):
    """尝试创建 user_points + 30 条流水"""
    try:
        from models.leaderboard import UserPoints, PointsTransaction
    except Exception as e:
        logger.warning(f"  ⚠️ 跳过积分数据：{e}")
        return 0, 0

    # UserPoints
    stmt = select(UserPoints).where(UserPoints.user_id == student.id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if not existing:
        try:
            points = UserPoints(
                user_id=student.id,
                total_points=1250,
                available_points=800,
                consumed_points=450,
                points_breakdown={
                    "course": 600,
                    "quiz": 300,
                    "achievement": 250,
                    "social": 100,
                },
            )
            db.add(points)
            await db.commit()
        except SQLAlchemyError as e:
            logger.warning(f"  ⚠️ user_points 插入失败：{e}")
            await db.rollback()

    # 30 条流水
    stmt = select(func.count(PointsTransaction.id)).where(
        PointsTransaction.user_id == student.id
    )
    result = await db.execute(stmt)
    existing_count = result.scalar() or 0
    if existing_count >= 25:
        logger.info(f"  ⏭ 已有 {existing_count} 条积分流水，跳过")
        return 1, 0

    balance = 0
    created = 0
    reasons = [
        ("earn", "完成课程章节", 30, 60),
        ("earn", "完成作业", 20, 50),
        ("earn", "完成测验", 30, 70),
        ("earn", "解锁成就", 50, 200),
        ("earn", "每日打卡", 10, 20),
        ("spend", "兑换学习资料", -30, -100),
    ]
    for day_offset in range(30):
        for _ in range(random.randint(1, 2)):
            txn_type, reason, min_amt, max_amt = random.choice(reasons)
            amount = random.randint(min_amt, max_amt)
            if txn_type == "spend":
                amount = -amount
            balance += amount
            try:
                txn = PointsTransaction(
                    user_id=student.id,
                    transaction_type=txn_type,
                    points_amount=amount,
                    balance_after=max(balance, 0),
                    reason=reason,
                    reference_type=random.choice(["course", "quiz", "achievement", "daily_task"]),
                    description=reason,
                    extra_metadata={"seed": True},
                )
                db.add(txn)
                created += 1
            except SQLAlchemyError as e:
                logger.warning(f"  ⚠️ points_transaction 失败：{e}")
                await db.rollback()
                continue
    await db.commit()
    return 1, created


async def seed_leaderboard(db, student):
    """尝试创建排行榜：20 条周榜 + 20 条总榜"""
    try:
        from models.leaderboard import LeaderboardRecord, LeaderboardPeriod, LeaderboardType
    except Exception as e:
        logger.warning(f"  ⚠️ 跳过排行榜：{e}")
        return 0

    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    all_time_start = now - timedelta(days=180)

    # 用斐波那契式递减生成 20 个分数（1250 → ...）
    fib_points = []
    a, b = 1250, 1180
    for _ in range(20):
        fib_points.append(a)
        a, b = b, b - 70

    created = 0
    # 周榜 20 条 + 总榜 20 条
    for period_name, period_start, period_value in [
        ("weekly", week_start, LeaderboardPeriod.WEEKLY),
        ("all_time", all_time_start, LeaderboardPeriod.ALL_TIME),
    ]:
        for rank, score in enumerate(fib_points, start=1):
            # 检查是否已存在
            stmt = select(LeaderboardRecord).where(
                LeaderboardRecord.user_id == student.id,
                LeaderboardRecord.period == period_value.value,
                LeaderboardRecord.period_start == period_start,
                LeaderboardRecord.rank == rank,
            )
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                continue

            # 用同一学生填充 20 个不同 rank 是一种 hack，但能展示排行榜视图
            try:
                record = LeaderboardRecord(
                    user_id=student.id,
                    leaderboard_type=LeaderboardType.TOTAL_POINTS.value,
                    period=period_value.value,
                    period_start=period_start,
                    period_end=now,
                    rank=rank,
                    score=float(score),
                    rank_change=random.randint(-3, 5),
                    score_change=random.uniform(-50, 80),
                )
                db.add(record)
                created += 1
            except SQLAlchemyError as e:
                logger.warning(f"  ⚠️ leaderboard 失败：{e}")
                await db.rollback()
                continue
    await db.commit()
    return created


async def seed_recommendations(db, student, courses):
    """尝试创建 AI 推荐 + 学习画像"""
    try:
        from models.recommendation import (
            RecommendationAlgorithm,
            RecommendationRecord,
            UserLearningProfile,
        )
    except Exception as e:
        logger.warning(f"  ⚠️ 跳过推荐：{e}")
        return 0, 0

    # 学习画像
    stmt = select(UserLearningProfile).where(UserLearningProfile.user_id == student.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        try:
            profile = UserLearningProfile(
                user_id=student.id,
                grade_level="G7",
                age_group="12-14",
                learning_style="visual",
                preferred_content_type="video",
                ability_dimensions={
                    "programming": {"score": 75, "level": "intermediate"},
                    "robotics": {"score": 60, "level": "beginner"},
                    "math": {"score": 80, "level": "intermediate"},
                    "creativity": {"score": 85, "level": "intermediate"},
                },
                interest_preferences=[
                    {"category": "robotics", "score": 0.9},
                    {"category": "ai", "score": 0.8},
                    {"category": "programming", "score": 0.85},
                ],
                knowledge_mastery={
                    "python_basics": 0.7,
                    "robotics_basics": 0.5,
                    "ai_ml": 0.3,
                },
                total_study_time_minutes=2400,
                completed_courses_count=2,
                average_quiz_score=88.5,
                current_streak_days=15,
                longest_streak_days=22,
                learning_goals=["完成 AI 入门课", "参加机器人竞赛"],
                recommendation_weights={
                    "interest": 0.4,
                    "ability_match": 0.3,
                    "popularity": 0.2,
                    "novelty": 0.1,
                },
            )
            db.add(profile)
            await db.commit()
        except SQLAlchemyError as e:
            logger.warning(f"  ⚠️ user_learning_profile 失败：{e}")
            await db.rollback()

    # 3 条推荐
    rec_created = 0
    recommend_courses = [c for c in courses if c.category in ["ai", "robotics", "arts"]][:3]
    for course in recommend_courses:
        stmt = select(RecommendationRecord).where(
            RecommendationRecord.user_id == student.id,
            RecommendationRecord.course_id == course.id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            continue
        try:
            rec = RecommendationRecord(
                user_id=student.id,
                course_id=course.id,
                algorithm_type=RecommendationAlgorithm.HYBRID,
                recommendation_score=random.uniform(0.75, 0.95),
                reason={
                    "interest_match": "符合你对 AI 与机器人的兴趣",
                    "difficulty_fit": "难度适合你当前水平",
                    "skill_gap": "可补足你 AI 学习的薄弱环节",
                },
                context={"surface": "creation_center_card", "ab_group": "B"},
                user_clicked=False,
                user_completed=False,
            )
            db.add(rec)
            rec_created += 1
        except SQLAlchemyError as e:
            logger.warning(f"  ⚠️ recommendation 失败：{e}")
            await db.rollback()
    await db.commit()
    return 1, rec_created


# =============================================================================
# 入口函数
# =============================================================================

async def seed_test_student_data():
    """为 test_student 填充冷启动数据（幂等）"""
    logger.info("=" * 60)
    logger.info("🌱 开始填充 test_student 冷启动数据...")
    logger.info("=" * 60)

    async with AsyncSessionLocal() as db:
        # 1. 找到测试账号
        student = await get_user_by_username(db, TEST_STUDENT_USERNAME)
        teacher = await get_user_by_username(db, TEST_TEACHER_USERNAME)
        admin = await get_user_by_username(db, TEST_ADMIN_USERNAME)

        if not student:
            logger.error(f"❌ 测试账号 {TEST_STUDENT_USERNAME} 不存在，请先运行 create_test_accounts.py")
            return False
        if not teacher:
            logger.error(f"❌ 测试账号 {TEST_TEACHER_USERNAME} 不存在")
            return False
        if not admin:
            logger.error(f"❌ 测试账号 {TEST_ADMIN_USERNAME} 不存在")
            return False

        logger.info(f"✓ 找到 3 个测试账号 (student_id={student.id}, teacher_id={teacher.id}, admin_id={admin.id})")

        # 2. 组织 + 关联
        try:
            org_data = await seed_organizations(db, student, teacher, admin)
            org = org_data["organization"]
        except Exception as e:
            logger.error(f"❌ 组织初始化失败：{e}")
            await db.rollback()
            return False

        # 3. 学习来源
        try:
            sources = await seed_learning_sources(db, student, org)
            logger.info(f"✓ 学习来源: {len(sources)} 个")
        except Exception as e:
            logger.error(f"❌ 学习来源失败：{e}")
            await db.rollback()
            sources = []

        # 4. 课程 + 课时 + 作业
        try:
            courses = await seed_courses(db, teacher, org, sources)
            logger.info(f"✓ 课程: {len(courses)} 门")
        except Exception as e:
            logger.error(f"❌ 课程失败：{e}")
            await db.rollback()
            courses = []

        try:
            lessons_count = await seed_lessons(db, courses)
            logger.info(f"✓ 课时: {lessons_count} 个")
        except Exception as e:
            logger.warning(f"⚠️ 课时失败：{e}")
            await db.rollback()

        try:
            assignments_count = await seed_assignments(db, courses)
            logger.info(f"✓ 作业: {assignments_count} 个")
        except Exception as e:
            logger.warning(f"⚠️ 作业失败：{e}")
            await db.rollback()

        # 5. 报名
        try:
            enrollments_count = await seed_enrollments(db, student, courses, sources)
            logger.info(f"✓ 报名: {enrollments_count} 门")
        except Exception as e:
            logger.warning(f"⚠️ 报名失败：{e}")
            await db.rollback()

        # 6. 学习记录
        try:
            records_count = await seed_learning_records(db, student, sources, courses)
            logger.info(f"✓ 学习记录: {records_count} 条")
        except Exception as e:
            logger.warning(f"⚠️ 学习记录失败：{e}")
            await db.rollback()

        # 7. 成就（可选表）
        try:
            ach_count, ua_count = await seed_achievements(db, student)
            logger.info(f"✓ 成就: {ach_count} 个定义 / {ua_count} 个已解锁")
        except Exception as e:
            logger.warning(f"⚠️ 成就跳过：{e}")

        # 8. 积分 + 流水（可选表）
        try:
            up_count, txn_count = await seed_points(db, student)
            logger.info(f"✓ 积分: {up_count} 账户 / {txn_count} 条流水")
        except Exception as e:
            logger.warning(f"⚠️ 积分跳过：{e}")

        # 9. 排行榜（可选表）
        try:
            lb_count = await seed_leaderboard(db, student)
            logger.info(f"✓ 排行榜: {lb_count} 条")
        except Exception as e:
            logger.warning(f"⚠️ 排行榜跳过：{e}")

        # 10. 推荐 + 画像（可选表）
        try:
            prof_count, rec_count = await seed_recommendations(db, student, courses)
            logger.info(f"✓ 学习画像: {prof_count} 个 / 推荐: {rec_count} 条")
        except Exception as e:
            logger.warning(f"⚠️ 推荐跳过：{e}")

    logger.info("=" * 60)
    logger.info("✅ test_student 冷启动数据填充完成！")
    logger.info("=" * 60)
    return True


if __name__ == "__main__":
    asyncio.run(seed_test_student_data())