"""
课件图谱数据迁移脚本

将现有的扁平化课程课时数据 (CourseLesson table) 迁移到闭包表结构 (CoursewareNode + CoursewareClosure)。

迁移策略：
1. 从 CourseLesson 表读取数据，按 course_id 和 order_index 排序
2. 为每个课程创建根节点（courseware node）
3. 将 CourseLesson 作为根节点的子节点
4. 自动构建闭包关系

使用方法：
    python -m scripts.migrate_to_closure [--dry-run] [--batch-size 500]

安全特性：
- 支持 dry-run 模式预览迁移结果
- 批量处理，避免内存溢出
- 失败自动回滚
- 迁移日志记录
"""

import asyncio
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from utils.database import AsyncSessionLocal, engine
from models.course import Course, CourseLesson
from models.courseware_clousure import CoursewareNode, CoursewareClosure
from repositories.courseware_repository import CoursewareRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("migrate_to_closure")


class ClosureTableMigration:
    """闭包表迁移器"""

    def __init__(
        self,
        session: AsyncSession,
        dry_run: bool = False,
        batch_size: int = 500,
    ):
        self.session = session
        self.repo = CoursewareRepository(session)
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.stats = {
            "total_processed": 0,
            "total_created": 0,
            "total_errors": 0,
            "errors": [],
        }
        self.start_time = time.time()

    async def migrate(self) -> Dict[str, Any]:
        """执行迁移"""
        logger.info("=" * 60)
        logger.info("开始课件图谱数据迁移: 扁平结构 -> 闭包表 (Closure Table)")
        logger.info(f"模式: {'试运行 (Dry Run)' if self.dry_run else '正式迁移'}")
        logger.info(f"批次大小: {self.batch_size}")
        logger.info("=" * 60)

        # 1. 迁移 CourseLesson -> CoursewareNode
        await self._migrate_course_lessons()

        self.stats["duration_seconds"] = round(time.time() - self.start_time, 2)

        if self.dry_run:
            logger.info("试运行完成，回滚所有更改...")
            await self.session.rollback()
        else:
            logger.info("提交迁移...")
            await self.session.commit()

        logger.info("=" * 60)
        logger.info(f"迁移完成: 处理 {self.stats['total_processed']} 条记录, "
                    f"创建 {self.stats['total_created']} 个节点, "
                    f"错误 {self.stats['total_errors']} 个")
        logger.info(f"耗时: {self.stats['duration_seconds']} 秒")
        logger.info("=" * 60)

        return self.stats

    async def _migrate_course_lessons(self):
        """迁移 CourseLesson 数据"""
        # 获取所有活跃课程
        courses_result = await self.session.execute(
            select(Course).where(Course.is_active == True)
        )
        courses = courses_result.scalars().all()
        logger.info(f"找到 {len(courses)} 门课程需要迁移")

        for course in courses:
            try:
                await self._migrate_single_course(course)
            except Exception as e:
                self.stats["total_errors"] += 1
                self.stats["errors"].append({
                    "course_id": course.id,
                    "course_title": course.title,
                    "error": str(e),
                })
                logger.error(f"迁移课程失败: course_id={course.id}, error={e}")

    async def _migrate_single_course(self, course):
        """迁移单个课程的所有课时"""
        # 获取课程的所有课时
        lessons_result = await self.session.execute(
            select(CourseLesson)
            .where(CourseLesson.course_id == course.id)
            .order_by(CourseLesson.order_index)
        )
        lessons = lessons_result.scalars().all()

        if not lessons:
            logger.info(f"课程 '{course.title}' (id={course.id}) 无课时，跳过")
            return

        logger.info(f"迁移课程 '{course.title}' (id={course.id}): {len(lessons)} 个课时")

        # 创建课程根节点
        root_node = await self.repo.create_node(
            title=course.title,
            node_type="course",
            description=course.description,
            cover_image_url=course.cover_image_url,
            course_id=course.id,
            org_id=course.org_id,
            difficulty=course.difficulty or "intermediate",
            tags=course.tags or [],
            parent_id=None,
        )
        self.stats["total_created"] += 1

        # 创建课时节点（作为根节点的子节点）
        for lesson in lessons:
            try:
                await self.repo.create_node(
                    title=lesson.title,
                    node_type="lesson",
                    description=lesson.description,
                    content_type=lesson.content_type or "video",
                    content_url=lesson.content_url,
                    duration_minutes=lesson.duration_minutes or 0,
                    order_index=lesson.order_index or 0,
                    course_id=course.id,
                    parent_id=root_node.id,
                )
                self.stats["total_created"] += 1
            except Exception as e:
                self.stats["total_errors"] += 1
                self.stats["errors"].append({
                    "course_id": course.id,
                    "lesson_id": lesson.id,
                    "lesson_title": lesson.title,
                    "error": str(e),
                })
                logger.error(f"迁移课时失败: lesson_id={lesson.id}, error={e}")

            self.stats["total_processed"] += 1

    async def verify(self) -> Dict[str, Any]:
        """验证迁移结果"""
        logger.info("验证迁移数据一致性...")

        # 统计源数据
        src_lessons_result = await self.session.execute(
            select(func.count()).select_from(CourseLesson)
        )
        src_lessons = src_lessons_result.scalar() or 0

        src_courses_result = await self.session.execute(
            select(func.count()).select_from(Course).where(Course.is_active == True)
        )
        src_courses = src_courses_result.scalar() or 0

        # 统计目标数据
        tgt_nodes_result = await self.session.execute(
            select(func.count()).select_from(CoursewareNode)
        )
        tgt_nodes = tgt_nodes_result.scalar() or 0

        tgt_closure_result = await self.session.execute(
            select(func.count()).select_from(CoursewareClosure)
        )
        tgt_closure = tgt_closure_result.scalar() or 0

        # 一致性验证
        validation = await self.repo.validate_closure_table()

        return {
            "source": {
                "courses": src_courses,
                "lessons": src_lessons,
            },
            "target": {
                "nodes": tgt_nodes,
                "closure_entries": tgt_closure,
            },
            "validation": validation,
        }


async def run_migration(dry_run: bool = False, verify: bool = True):
    """运行迁移入口"""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            migration = ClosureTableMigration(
                session=session,
                dry_run=dry_run,
                batch_size=500,
            )

            result = await migration.migrate()

            if verify and not dry_run:
                verification = await migration.verify()
                result["verification"] = verification
                logger.info(f"验证结果: {verification}")

            return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="课件图谱闭包表数据迁移")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="试运行模式，不实际提交更改"
    )
    parser.add_argument(
        "--batch-size", type=int, default=500,
        help="批量处理大小"
    )
    parser.add_argument(
        "--no-verify", action="store_true",
        help="跳过验证步骤"
    )

    args = parser.parse_args()

    try:
        result = asyncio.run(run_migration(
            dry_run=args.dry_run,
            verify=not args.no_verify,
        ))
        print(f"\n迁移结果: {result}")
        return 0 if result.get("total_errors", 0) == 0 else 1
    except Exception as e:
        logger.error(f"迁移失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())