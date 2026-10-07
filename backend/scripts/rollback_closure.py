"""
课件图谱闭包表 - 回滚机制

提供从闭包表结构回滚到原始扁平结构的能力。

使用方法：
    python -m scripts.rollback_closure [--backup] [--force]

回滚策略：
1. 备份模式：将闭包表数据导出为 JSON 备份文件
2. 回滚模式：删除所有闭包表数据，恢复原始 CourseLesson 结构
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select, text, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from utils.database import AsyncSessionLocal, engine
from models.courseware_clousure import CoursewareNode, CoursewareClosure
from models.course import Course, CourseLesson

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rollback_closure")


class ClosureTableRollback:
    """闭包表回滚器"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.backup_dir = Path(__file__).resolve().parent.parent / "data" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def backup(self) -> Dict[str, Any]:
        """备份闭包表数据到 JSON 文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"closure_backup_{timestamp}.json"

        logger.info(f"开始备份闭包表数据到: {backup_file}")

        # 导出节点数据
        nodes_result = await self.session.execute(
            select(CoursewareNode).order_by(CoursewareNode.id)
        )
        nodes = nodes_result.scalars().all()

        nodes_data = []
        for n in nodes:
            nodes_data.append({
                "id": n.id,
                "title": n.title,
                "description": n.description,
                "node_type": n.node_type,
                "content_type": n.content_type,
                "content_url": n.content_url,
                "duration_minutes": n.duration_minutes,
                "cover_image_url": n.cover_image_url,
                "order_index": n.order_index,
                "difficulty": n.difficulty,
                "tags": n.tags,
                "extra_data": n.extra_data,
                "course_id": n.course_id,
                "material_id": n.material_id,
                "is_active": n.is_active,
                "is_published": n.is_published,
                "status": n.status,
                "org_id": n.org_id,
                "created_by": n.created_by,
                "updated_by": n.updated_by,
                "created_at": str(n.created_at) if n.created_at else None,
                "updated_at": str(n.updated_at) if n.updated_at else None,
            })

        # 导出闭包关系数据
        closure_result = await self.session.execute(
            select(CoursewareClosure).order_by(CoursewareClosure.id)
        )
        closures = closure_result.scalars().all()

        closure_data = []
        for c in closures:
            closure_data.append({
                "id": c.id,
                "ancestor_id": c.ancestor_id,
                "descendant_id": c.descendant_id,
                "depth": c.depth,
                "created_at": str(c.created_at) if c.created_at else None,
            })

        backup = {
            "version": "1.0",
            "created_at": timestamp,
            "source": "closure_table",
            "stats": {
                "total_nodes": len(nodes_data),
                "total_closure_entries": len(closure_data),
            },
            "nodes": nodes_data,
            "closures": closure_data,
        }

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup, f, ensure_ascii=False, indent=2)

        file_size = backup_file.stat().st_size
        logger.info(f"备份完成: {len(nodes_data)} 个节点, "
                    f"{len(closure_data)} 条闭包关系, "
                    f"文件大小: {file_size / 1024:.1f} KB")

        return {
            "success": True,
            "backup_file": str(backup_file),
            "nodes": len(nodes_data),
            "closures": len(closure_data),
            "file_size_bytes": file_size,
        }

    async def restore_from_backup(self, backup_file: str) -> Dict[str, Any]:
        """从备份文件恢复闭包表数据"""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            return {"success": False, "error": f"备份文件不存在: {backup_file}"}

        logger.info(f"从备份文件恢复: {backup_file}")

        with open(backup_path, "r", encoding="utf-8") as f:
            backup = json.load(f)

        nodes_restored = 0
        closures_restored = 0

        # 恢复节点
        for node_data in backup.get("nodes", []):
            node = CoursewareNode(
                title=node_data["title"],
                description=node_data.get("description"),
                node_type=node_data.get("node_type", "lesson"),
                content_type=node_data.get("content_type"),
                content_url=node_data.get("content_url"),
                duration_minutes=node_data.get("duration_minutes", 0),
                cover_image_url=node_data.get("cover_image_url"),
                order_index=node_data.get("order_index", 0),
                difficulty=node_data.get("difficulty", "intermediate"),
                tags=node_data.get("tags", []),
                extra_data=node_data.get("extra_data", {}),
                course_id=node_data.get("course_id"),
                material_id=node_data.get("material_id"),
                is_active=node_data.get("is_active", True),
                is_published=node_data.get("is_published", False),
                status=node_data.get("status", "draft"),
                org_id=node_data.get("org_id"),
                created_by=node_data.get("created_by"),
                updated_by=node_data.get("updated_by"),
            )
            self.session.add(node)
            nodes_restored += 1

        await self.session.flush()

        # 恢复闭包关系
        for closure_data in backup.get("closures", []):
            closure = CoursewareClosure(
                ancestor_id=closure_data["ancestor_id"],
                descendant_id=closure_data["descendant_id"],
                depth=closure_data["depth"],
            )
            self.session.add(closure)
            closures_restored += 1

        logger.info(f"恢复完成: {nodes_restored} 个节点, {closures_restored} 条闭包关系")
        return {
            "success": True,
            "nodes_restored": nodes_restored,
            "closures_restored": closures_restored,
        }

    async def rollback(self) -> Dict[str, Any]:
        """执行回滚：删除所有闭包表数据"""
        start_time = time.time()

        logger.info("开始回滚：删除所有闭包表数据...")

        # 统计要删除的数据量
        closure_count_result = await self.session.execute(
            select(func.count()).select_from(CoursewareClosure)
        )
        closure_count = closure_count_result.scalar() or 0

        node_count_result = await self.session.execute(
            select(func.count()).select_from(CoursewareNode)
        )
        node_count = node_count_result.scalar() or 0

        logger.info(f"将删除 {node_count} 个节点和 {closure_count} 条闭包关系")

        # 先删除闭包关系（外键约束）
        await self.session.execute(delete(CoursewareClosure))
        # 再删除节点
        await self.session.execute(delete(CoursewareNode))

        duration = round(time.time() - start_time, 2)

        logger.info(f"回滚完成: 删除 {node_count} 个节点, "
                    f"{closure_count} 条闭包关系, 耗时 {duration} 秒")

        return {
            "success": True,
            "nodes_deleted": node_count,
            "closure_entries_deleted": closure_count,
            "duration_seconds": duration,
            "errors": [],
        }

    async def verify_rollback(self) -> Dict[str, Any]:
        """验证回滚后的数据完整性"""
        logger.info("验证回滚后数据完整性...")

        # 检查 CourseLesson 表是否完好
        lessons_result = await self.session.execute(
            select(func.count()).select_from(CourseLesson)
        )
        lessons_count = lessons_result.scalar() or 0

        # 检查 CoursewareNode 表是否已清空
        nodes_result = await self.session.execute(
            select(func.count()).select_from(CoursewareNode)
        )
        nodes_count = nodes_result.scalar() or 0

        # 检查 CoursewareClosure 表是否已清空
        closure_result = await self.session.execute(
            select(func.count()).select_from(CoursewareClosure)
        )
        closure_count = closure_result.scalar() or 0

        return {
            "course_lessons_remaining": lessons_count,
            "courseware_nodes_remaining": nodes_count,
            "courseware_closures_remaining": closure_count,
            "is_clean": nodes_count == 0 and closure_count == 0,
        }

    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有备份文件"""
        backups = []
        if self.backup_dir.exists():
            for f in sorted(self.backup_dir.glob("closure_backup_*.json"), reverse=True):
                stat = f.stat()
                backups.append({
                    "filename": f.name,
                    "path": str(f),
                    "size_bytes": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                })
        return backups


async def run_rollback(backup_first: bool = True, force: bool = False):
    """执行回滚"""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            rollback = ClosureTableRollback(session)

            # 先备份
            if backup_first:
                backup_result = await rollback.backup()
                logger.info(f"备份结果: {backup_result}")

            # 执行回滚
            result = await rollback.rollback()

            # 验证
            verification = await rollback.verify_rollback()
            result["verification"] = verification

            return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="课件图谱闭包表回滚")
    parser.add_argument(
        "--backup", action="store_true", default=True,
        help="回滚前先备份数据"
    )
    parser.add_argument(
        "--no-backup", action="store_true",
        help="不备份直接回滚"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="强制回滚，不确认"
    )
    parser.add_argument(
        "--list-backups", action="store_true",
        help="列出所有备份文件"
    )
    parser.add_argument(
        "--restore", type=str, metavar="FILE",
        help="从指定备份文件恢复"
    )

    args = parser.parse_args()

    try:
        if args.list_backups:
            async def list_backups():
                async with AsyncSessionLocal() as session:
                    rollback = ClosureTableRollback(session)
                    return rollback.list_backups()
            backups = asyncio.run(list_backups())
            print(f"\n备份文件列表 ({len(backups)} 个):")
            for b in backups:
                print(f"  {b['filename']} ({b['size_bytes'] / 1024:.1f} KB) - {b['created_at']}")
            return 0

        if args.restore:
            async def restore():
                async with AsyncSessionLocal() as session:
                    async with session.begin():
                        rollback = ClosureTableRollback(session)
                        return await rollback.restore_from_backup(args.restore)
            result = asyncio.run(restore())
            print(f"\n恢复结果: {result}")
            return 0 if result.get("success") else 1

        if not args.force:
            confirm = input("确定要回滚闭包表数据吗？此操作不可逆！(y/N): ")
            if confirm.lower() != "y":
                print("已取消")
                return 0

        result = asyncio.run(run_rollback(
            backup_first=not args.no_backup,
            force=args.force,
        ))
        print(f"\n回滚结果: {result}")
        return 0 if result.get("success") else 1

    except Exception as e:
        logger.error(f"回滚失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())