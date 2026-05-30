"""
AR/VR课程内容表结构迁移
创建支持AR/VR课程内容管理的相关数据库表
"""

import logging
import os
import sys

from sqlalchemy.exc import SQLAlchemyError

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.ar_vr_content import (
    ARVRContent,
    ARVRInteractionLog,
    ARVRProgressTracking,
    ARVRSensorData,
)
from utils.database import get_db

logger = logging.getLogger(__name__)


def upgrade():
    """升级数据库 - 创建AR/VR相关表"""
    try:
        logger.info("开始创建AR/VR课程内容表...")

        # 获取数据库连接
        db = next(get_db())

        # 创建表
        tables_to_create = [
            ARVRContent.__table__,
            ARVRSensorData.__table__,
            ARVRInteractionLog.__table__,
            ARVRProgressTracking.__table__,
        ]

        for table in tables_to_create:
            if not table.exists(db.bind):
                table.create(db.bind)
                logger.info(f"表 {table.name} 创建成功")
            else:
                logger.info(f"表 {table.name} 已存在")

        # 插入示例数据
        insert_sample_data(db)

        db.commit()
        logger.info("AR/VR课程内容表创建完成")

    except SQLAlchemyError as e:
        logger.error(f"数据库操作失败: {e}")
        if "db" in locals():
            db.rollback()
        raise
    except Exception as e:
        logger.error(f"创建AR/VR表失败: {e}")
        raise
    finally:
        if "db" in locals():
            db.close()


def downgrade():
    """降级数据库 - 删除AR/VR相关表"""
    try:
        logger.info("开始删除AR/VR课程内容表...")

        db = next(get_db())

        # 删除表（按依赖顺序）
        tables_to_drop = [
            ARVRProgressTracking.__table__,
            ARVRInteractionLog.__table__,
            ARVRSensorData.__table__,
            ARVRContent.__table__,
        ]

        for table in reversed(tables_to_drop):
            if table.exists(db.bind):
                table.drop(db.bind)
                logger.info(f"表 {table.name} 删除成功")
            else:
                logger.info(f"表 {table.name} 不存在")

        db.commit()
        logger.info("AR/VR课程内容表删除成功")

    except SQLAlchemyError as e:
        logger.error(f"数据库操作失败: {e}")
        if "db" in locals():
            db.rollback()
        raise
    except Exception as e:
        logger.error(f"删除AR/VR表失败: {e}")
        raise
    finally:
        if "db" in locals():
            db.close()


def insert_sample_data(db):
    """插入示例数据"""
    try:
        logger.info("插入AR/VR示例数据...")

        from models.ar_vr_content import (
            ARVRContentType,
            ARVRPlatform,
            InteractionMode,
            SensorType,
        )

        # 示例AR/VR内容
        sample_contents = [
            ARVRContent(
                org_id=1,
                course_id=1,
                lesson_id=1,
                title="Unity WebGL 3D分子模型",
                description="基于Unity WebGL构建的交互式3D分子结构可视化",
                content_type=ARVRContentType.UNITY_WEBGL,
                platform=ARVRPlatform.WEB_BROWSER,
                build_file_url="/arvr/builds/molecular_structure/index.html",
                manifest_url="/arvr/builds/molecular_structure/Build/molecular_structure.json",
                thumbnail_url="/arvr/thumbnails/molecular_structure.jpg",
                config={
                    "width": 800,
                    "height": 600,
                    "backgroundColor": "#000000",
                    "loadingBar": True,
                },
                required_sensors=[SensorType.TOUCH],
                interaction_modes=[InteractionMode.GESTURE, InteractionMode.CONTROLLER],
                file_size=15728640,  # 15MB
                estimated_load_time=3.5,
                performance_profile={
                    "min_fps": 30,
                    "recommended_fps": 60,
                    "graphics_quality": "high",
                },
                is_public=True,
                access_level="lesson",
                tags=["chemistry", "3d", "molecular", "interactive"],
                custom_metadata={
                    "subject": "化学",
                    "grade_level": "高中",
                    "learning_objectives": ["理解分子结构", "掌握化学键概念"],
                },
            ),
            ARVRContent(
                org_id=1,
                course_id=1,
                title="AR增强现实太阳系",
                description="移动端AR应用，展示太阳系行星运动",
                content_type=ARVRContentType.AR_MARKER,
                platform=ARVRPlatform.MOBILE_AR,
                build_file_url="/arvr/builds/solar_system/ar_app.apk",
                config={
                    "marker_pattern": "solar_system_marker",
                    "tracking_accuracy": "high",
                    "render_distance": 10,
                },
                required_sensors=[
                    SensorType.CAMERA,
                    SensorType.GYROSCOPE,
                    SensorType.ACCELEROMETER,
                ],
                interaction_modes=[InteractionMode.GESTURE, InteractionMode.VOICE],
                file_size=26214400,  # 25MB
                estimated_load_time=5.0,
                is_public=False,
                access_level="course",
                tags=["astronomy", "ar", "solar-system", "mobile"],
                custom_metadata={
                    "subject": "天文学",
                    "target_devices": ["iOS", "Android"],
                    "minimum_os_version": "iOS 12+/Android 8+",
                },
            ),
            ARVRContent(
                org_id=1,
                course_id=2,
                lesson_id=3,
                title="虚拟物理实验室",
                description="基于Web的虚拟物理实验环境",
                content_type=ARVRContentType.VIRTUAL_LAB,
                platform=ARVRPlatform.WEB_BROWSER,
                build_file_url="/arvr/builds/physics_lab/index.html",
                config={
                    "experiments": ["pendulum", "spring_mass", "wave_simulation"],
                    "physics_engine": "cannon.js",
                    "real_time_rendering": True,
                },
                required_sensors=[SensorType.MOUSE, SensorType.KEYBOARD],
                interaction_modes=[InteractionMode.CONTROLLER],
                file_size=10485760,  # 10MB
                estimated_load_time=2.8,
                is_public=True,
                access_level="lesson",
                tags=["physics", "lab", "simulation", "experiment"],
                custom_metadata={
                    "subject": "物理",
                    "experiments_count": 15,
                    "supported_browsers": ["Chrome", "Firefox", "Edge"],
                },
            ),
        ]

        # 插入示例内容
        for content in sample_contents:
            db.add(content)

        db.flush()  # 获取生成的ID

        # 示例进度跟踪数据
        sample_progress = [
            ARVRProgressTracking(
                content_id=sample_contents[0].id,
                user_id=2,  # 假设用户ID为2的学生
                org_id=1,
                progress_percentage=75.0,
                current_state={
                    "current_molecule": "H2O",
                    "view_mode": "wireframe",
                    "rotation_speed": 1.0,
                },
                milestones_reached=["water_molecule_loaded", "bond_angles_measured"],
                time_spent=15.5,  # 15.5分钟
                interaction_count=42,
                assessment_score=85.0,
            ),
            ARVRProgressTracking(
                content_id=sample_contents[2].id,
                user_id=3,  # 假设用户ID为3的学生
                org_id=1,
                progress_percentage=30.0,
                current_state={"experiment": "pendulum", "length": 1.0, "gravity": 9.8},
                milestones_reached=["pendulum_setup"],
                time_spent=8.2,
                interaction_count=18,
            ),
        ]

        for progress in sample_progress:
            db.add(progress)

        db.commit()
        logger.info("AR/VR示例数据插入成功")

    except Exception as e:
        logger.error(f"插入示例数据失败: {e}")
        db.rollback()
        raise


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 执行升级
    try:
        upgrade()
        print("✅ AR/VR数据库表创建成功")
    except Exception as e:
        print(f"❌ AR/VR数据库表创建失败: {e}")
        sys.exit(1)
