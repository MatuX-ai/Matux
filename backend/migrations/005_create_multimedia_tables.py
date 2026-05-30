"""
多媒体资源管理数据库迁移脚本
创建多媒体资源表及相关索引
"""

import logging

from sqlalchemy import MetaData, Table

logger = logging.getLogger(__name__)


def upgrade():
    """升级数据库 - 创建多媒体资源表"""
    from utils.database import Base, engine

    try:
        # 创建多媒体资源相关表
        Base.metadata.create_all(
            bind=engine,
            tables=[
                Base.metadata.tables["multimedia_resources"],
                Base.metadata.tables["media_transcoding_jobs"],
            ],
        )

        logger.info("多媒体资源表创建成功")

        # 创建索引
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_multimedia_org_course ON multimedia_resources(org_id, course_id)",
            "CREATE INDEX IF NOT EXISTS idx_multimedia_media_type ON multimedia_resources(media_type)",
            "CREATE INDEX IF NOT EXISTS idx_multimedia_status ON multimedia_resources(video_status)",
            "CREATE INDEX IF NOT EXISTS idx_transcoding_resource ON media_transcoding_jobs(resource_id)",
            "CREATE INDEX IF NOT EXISTS idx_transcoding_status ON media_transcoding_jobs(status)",
        ]

        with engine.connect() as conn:
            for sql in indexes_sql:
                conn.execute(sql)
            conn.commit()

        logger.info("多媒体资源索引创建成功")

    except Exception as e:
        logger.error(f"创建多媒体资源表失败: {e}")
        raise


def downgrade():
    """降级数据库 - 删除多媒体资源表"""
    from utils.database import engine

    try:
        # 删除索引
        indexes_to_drop = [
            "DROP INDEX IF EXISTS idx_multimedia_org_course",
            "DROP INDEX IF EXISTS idx_multimedia_media_type",
            "DROP INDEX IF EXISTS idx_multimedia_status",
            "DROP INDEX IF EXISTS idx_transcoding_resource",
            "DROP INDEX IF EXISTS idx_transcoding_status",
        ]

        with engine.connect() as conn:
            for sql in indexes_to_drop:
                conn.execute(sql)
            conn.commit()

        # 删除表
        table_names = ["media_transcoding_jobs", "multimedia_resources"]
        for table_name in table_names:
            if engine.dialect.has_table(engine, table_name):
                table = Table(table_name, MetaData(), autoload_with=engine)
                table.drop(engine)
                logger.info(f"表 {table_name} 删除成功")

    except Exception as e:
        logger.error(f"删除多媒体资源表失败: {e}")
        raise


def seed_sample_data():
    """插入示例数据"""
    from models.multimedia import (
        DocumentFormat,
        MediaType,
        MultimediaResource,
        VideoStatus,
    )
    from utils.database import get_db

    try:
        db = next(get_db())

        # 创建示例多媒体资源
        sample_resources = [
            MultimediaResource(
                org_id=1,
                course_id=1,
                title="课程介绍视频",
                description="本课程的介绍视频",
                media_type=MediaType.VIDEO,
                file_name="course_intro.mp4",
                file_size=1024000,
                mime_type="video/mp4",
                duration_seconds=300.0,
                video_status=VideoStatus.READY,
                is_public=True,
                access_level="public",
            ),
            MultimediaResource(
                org_id=1,
                course_id=1,
                title="课程大纲PDF",
                description="详细的课程大纲文档",
                media_type=MediaType.DOCUMENT,
                file_name="course_outline.pdf",
                file_size=204800,
                mime_type="application/pdf",
                document_format=DocumentFormat.PDF,
                page_count=15,
                is_public=True,
                access_level="course",
            ),
            MultimediaResource(
                org_id=1,
                course_id=1,
                lesson_id=1,
                title="3D分子模型",
                description="水分子的3D可视化模型",
                media_type=MediaType.THREE_D_MODEL,
                file_name="water_molecule.glb",
                file_size=51200,
                mime_type="model/gltf-binary",
                model_format="glb",
                model_dimensions={"width": 100, "height": 100, "depth": 100},
                is_public=False,
                access_level="lesson",
            ),
        ]

        for resource in sample_resources:
            db.add(resource)

        db.commit()
        logger.info("示例多媒体资源数据插入成功")

    except Exception as e:
        logger.error(f"插入示例数据失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="多媒体资源数据库迁移")
    parser.add_argument(
        "action", choices=["upgrade", "downgrade", "seed"], help="执行的操作"
    )
    parser.add_argument("--sync", action="store_true", help="使用同步方式执行")

    args = parser.parse_args()

    if args.action == "upgrade":
        if args.sync:
            upgrade()
        else:
            asyncio.run(asyncio.to_thread(upgrade))
    elif args.action == "downgrade":
        if args.sync:
            downgrade()
        else:
            asyncio.run(asyncio.to_thread(downgrade))
    elif args.action == "seed":
        seed_sample_data()
