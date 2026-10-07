#!/usr/bin/env python3
"""
Seed sample AR/VR course data for testing.

This script populates the ar_vr_contents table with sample courses so the
frontend can actually load real data and verify the new endpoints.

Usage:
    python seed_arvr_courses.py
"""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.settings import settings
from models.ar_vr_content import ARVRContent, ARVRContentType, ARVRPlatform


def seed():
    """Insert sample AR/VR courses into the database."""
    # Sync engine (SQLite)
    db_url = settings.DATABASE_URL.replace("+aiosqlite", "")
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)

    session = Session()

    try:
        # Check existing
        existing_count = session.query(ARVRContent).count()
        if existing_count > 0:
            print(f"Database already has {existing_count} ARVR contents. Skipping seed.")
            return

        # Sample course 1: 机器人基础入门
        c1 = ARVRContent(
            org_id=1,
            course_id=1,
            lesson_id=None,
            title="机器人基础入门：3D 演示",
            description=(
                "通过 AR/VR 技术可视化机器人结构，理解舵机、传感器与控制器"
                "如何协同工作。适合 3-6 年级 STEM 入门。"
            ),
            content_type=ARVRContentType.THREEJS_SCENE,
            platform=ARVRPlatform.WEB_BROWSER,
            build_file_url="/arvr/builds/seed_robot/index.html",
            manifest_url='{"camera":{"position":[5,5,5]},"objects":[{"type":"robot","color":"#3d5a80"}]}',
            thumbnail_url="/arvr/thumbnails/seed_robot.png",
            config={
                "scene": "robot_lab",
                "physics": True,
                "controls": ["orbit", "reset", "auto_rotate"],
                "hints": ["点击机器人查看部件名称", "拖拽旋转视角"],
            },
            required_sensors=["touch"],
            interaction_modes=["gesture", "controller"],
            is_public=True,
            access_level="course",
            tags=["机器人", "STEM", "3D建模", "入门"],
            custom_metadata={"difficulty": "beginner", "estimated_minutes": 30},
            view_count=0,
            completion_count=0,
            average_rating=0.0,
            is_active=True,
            is_featured=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Sample course 2: Python 编程可视化
        c2 = ARVRContent(
            org_id=1,
            course_id=2,
            lesson_id=None,
            title="Python 编程可视化：代码如何变成动画",
            description=(
                "把 Python 代码执行过程用 3D 场景呈现：变量是发光的盒子，"
                "循环是旋转的齿轮，函数是组合的积木。寓教于乐。"
            ),
            content_type=ARVRContentType.INTERACTIVE_DEMO,
            platform=ARVRPlatform.WEB_BROWSER,
            build_file_url="/arvr/builds/seed_python/index.html",
            manifest_url='{"theme":"code_repr","interactive":true}',
            thumbnail_url="/arvr/thumbnails/seed_python.png",
            config={
                "scene": "code_lab",
                "interactive": True,
                "examples": ["hello", "for_loop", "function"],
            },
            required_sensors=["touch", "microphone"],
            interaction_modes=["controller", "voice"],
            is_public=True,
            access_level="course",
            tags=["Python", "编程", "可视化", "交互"],
            custom_metadata={"difficulty": "beginner", "estimated_minutes": 45},
            view_count=0,
            completion_count=0,
            average_rating=0.0,
            is_active=True,
            is_featured=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Sample course 3: 3D 建模与打印
        c3 = ARVRContent(
            org_id=1,
            course_id=5,
            lesson_id=None,
            title="3D 建模演示：从创意到实体",
            description=(
                "在 VR 中雕刻 3D 模型，体验从设计 → 切片 → 打印的全流程。"
                "需要 VR 头显或桌面端 3D 查看器。"
            ),
            content_type=ARVRContentType.MODEL_VIEWER,
            platform=ARVRPlatform.WEB_BROWSER,
            build_file_url="/arvr/builds/seed_3dprint/index.html",
            manifest_url='{"model_format":"glb","interactive":true}',
            thumbnail_url="/arvr/thumbnails/seed_3dprint.png",
            config={
                "scene": "maker_space",
                "tools": ["sculpt", "extrude", "slice"],
            },
            required_sensors=["touch"],
            interaction_modes=["gesture", "controller"],
            is_public=True,
            access_level="course",
            tags=["3D建模", "3D打印", "设计"],
            custom_metadata={"difficulty": "intermediate", "estimated_minutes": 60},
            view_count=0,
            completion_count=0,
            average_rating=0.0,
            is_active=True,
            is_featured=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session.add_all([c1, c2, c3])
        session.commit()

        print(f"✅ Seeded {session.query(ARVRContent).count()} ARVR courses:")
        for c in session.query(ARVRContent).all():
            print(f"  - ID {c.id}: {c.title} ({c.content_type.value})")
    except Exception as e:
        session.rollback()
        print(f"❌ Seed failed: {e}", file=sys.stderr)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()
