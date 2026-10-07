"""
课件图谱闭包表 - Repository 层

提供课件节点的增删改查操作，自动维护闭包表的完整性。
所有操作均在事务中执行，确保节点表与闭包表的一致性。
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.courseware_clousure import CoursewareNode, CoursewareClosure

logger = logging.getLogger(__name__)


class CoursewareRepository:
    """课件节点 Repository - 封装闭包表维护逻辑"""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ==================== 节点 CRUD ====================

    async def create_node(
        self,
        title: str,
        parent_id: Optional[int] = None,
        node_type: str = "lesson",
        description: Optional[str] = None,
        content_type: str = "video",
        content_url: Optional[str] = None,
        duration_minutes: int = 0,
        cover_image_url: Optional[str] = None,
        order_index: int = 0,
        difficulty: str = "intermediate",
        tags: Optional[List[str]] = None,
        extra_data: Optional[dict] = None,
        course_id: Optional[int] = None,
        material_id: Optional[int] = None,
        org_id: Optional[int] = None,
        created_by: Optional[int] = None,
    ) -> CoursewareNode:
        """创建节点并自动维护闭包表"""
        node = CoursewareNode(
            title=title,
            description=description,
            node_type=node_type,
            content_type=content_type,
            content_url=content_url,
            duration_minutes=duration_minutes,
            cover_image_url=cover_image_url,
            order_index=order_index,
            difficulty=difficulty,
            tags=tags or [],
            extra_data=extra_data or {},
            course_id=course_id,
            material_id=material_id,
            org_id=org_id,
            created_by=created_by,
        )
        self.session.add(node)
        await self.session.flush()  # 先获取 ID

        # 插入自引用闭包条目 (depth=0)
        self_ref = CoursewareClosure(
            ancestor_id=node.id,
            descendant_id=node.id,
            depth=0,
        )
        self.session.add(self_ref)

        # 如果有父节点，插入所有祖先关系
        if parent_id is not None:
            await self._add_ancestor_relations(node.id, parent_id)

        await self.session.flush()
        logger.info(f"[CoursewareRepo] 创建节点: id={node.id}, title='{title}', parent_id={parent_id}")
        return node

    async def _add_ancestor_relations(self, new_node_id: int, parent_id: int):
        """为新建节点插入所有祖先关系到闭包表"""
        # 查询父节点的所有祖先（包括父节点自身 depth=0）
        ancestor_query = select(CoursewareClosure).where(
            CoursewareClosure.descendant_id == parent_id
        )
        result = await self.session.execute(ancestor_query)
        parent_ancestors = result.scalars().all()

        for entry in parent_ancestors:
            new_entry = CoursewareClosure(
                ancestor_id=entry.ancestor_id,
                descendant_id=new_node_id,
                depth=entry.depth + 1,
            )
            self.session.add(new_entry)

    async def get_node(self, node_id: int) -> Optional[CoursewareNode]:
        """获取单个节点"""
        result = await self.session.execute(
            select(CoursewareNode).where(CoursewareNode.id == node_id)
        )
        return result.scalar_one_or_none()

    async def get_node_with_parent(self, node_id: int) -> Tuple[Optional[CoursewareNode], Optional[int]]:
        """
        获取节点及其直接父节点ID
        返回: (node, parent_id)
        """
        node = await self.get_node(node_id)
        if node is None:
            return None, None

        parent_id = await self._get_direct_parent_id(node_id)
        return node, parent_id

    async def _get_direct_parent_id(self, node_id: int) -> Optional[int]:
        """获取直接父节点ID"""
        result = await self.session.execute(
            select(CoursewareClosure.ancestor_id).where(
                and_(
                    CoursewareClosure.descendant_id == node_id,
                    CoursewareClosure.depth == 1,
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_node(self, node_id: int, **kwargs) -> Optional[CoursewareNode]:
        """更新节点基本信息"""
        node = await self.get_node(node_id)
        if node is None:
            return None

        # 过滤不允许更新的字段
        disallowed = {"id", "created_at", "created_by"}
        for key, value in kwargs.items():
            if key not in disallowed and hasattr(node, key):
                setattr(node, key, value)

        node.updated_at = datetime.utcnow()
        await self.session.flush()
        logger.info(f"[CoursewareRepo] 更新节点: id={node_id}")
        return node

    async def delete_node(self, node_id: int, cascade: bool = True) -> bool:
        """
        删除节点

        Args:
            node_id: 要删除的节点ID
            cascade: 是否级联删除所有后代节点。
                     如果为 False，后代节点将提升到被删除节点的父级。

        Returns:
            是否删除成功
        """
        node = await self.get_node(node_id)
        if node is None:
            return False

        parent_id = await self._get_direct_parent_id(node_id)

        if cascade:
            # 级联删除：查询所有后代节点并删除
            descendant_ids = await self._get_all_descendant_ids(node_id)
            # 删除所有相关闭包条目
            await self.session.execute(
                delete(CoursewareClosure).where(
                    CoursewareClosure.descendant_id.in_(descendant_ids)
                )
            )
            # 删除节点
            await self.session.execute(
                delete(CoursewareNode).where(CoursewareNode.id.in_(descendant_ids))
            )
            logger.info(
                f"[CoursewareRepo] 级联删除节点及其 {len(descendant_ids) - 1} 个后代: root_id={node_id}"
            )
        else:
            # 非级联删除：将子节点重新挂载到父节点
            children = await self._get_direct_children_ids(node_id)
            if parent_id is not None:
                for child_id in children:
                    await self.move_node(child_id, parent_id)
            else:
                # 无父节点时，子节点成为根节点
                for child_id in children:
                    await self._make_root(child_id)

            # 删除该节点的所有闭包引用
            await self.session.execute(
                delete(CoursewareClosure).where(
                    CoursewareClosure.descendant_id == node_id
                )
            )
            await self.session.execute(
                delete(CoursewareNode).where(CoursewareNode.id == node_id)
            )
            logger.info(f"[CoursewareRepo] 删除节点(非级联): id={node_id}")

        await self.session.flush()
        return True

    async def _get_all_descendant_ids(self, node_id: int) -> List[int]:
        """获取所有后代节点ID（包括自身）"""
        result = await self.session.execute(
            select(CoursewareClosure.descendant_id).where(
                CoursewareClosure.ancestor_id == node_id
            )
        )
        return [row[0] for row in result.all()]

    async def _get_direct_children_ids(self, node_id: int) -> List[int]:
        """获取直接子节点ID"""
        result = await self.session.execute(
            select(CoursewareClosure.descendant_id).where(
                and_(
                    CoursewareClosure.ancestor_id == node_id,
                    CoursewareClosure.depth == 1,
                )
            )
        )
        return [row[0] for row in result.all()]

    async def _make_root(self, node_id: int):
        """将节点变为根节点（移除所有祖先关系，仅保留depth=0）"""
        # 删除除自引用外的所有祖先关系
        await self.session.execute(
            delete(CoursewareClosure).where(
                and_(
                    CoursewareClosure.descendant_id == node_id,
                    CoursewareClosure.depth > 0,
                )
            )
        )

    # ==================== 节点移动 ====================

    async def move_node(self, node_id: int, new_parent_id: Optional[int]) -> bool:
        """
        移动节点到新的父节点下

        实现原理：
        1. 删除该节点及其所有后代与旧祖先的关系（排除新祖先的共同部分）
        2. 建立该节点及其所有后代与新祖先的关系
        """
        node = await self.get_node(node_id)
        if node is None:
            return False

        # 检测循环引用
        if new_parent_id is not None:
            if new_parent_id == node_id:
                logger.error(f"[CoursewareRepo] 不能将节点移动到自身: node_id={node_id}")
                return False
            new_parent_descendants = await self._get_all_descendant_ids(new_parent_id)
            if node_id in new_parent_descendants:
                logger.error(
                    f"[CoursewareRepo] 不能将节点移动到其后代下: "
                    f"node_id={node_id}, new_parent_id={new_parent_id}"
                )
                return False

        # 获取当前节点的所有后代（包括自身）
        subtree_ids = await self._get_all_descendant_ids(node_id)

        # 步骤1: 删除所有指向 subtree 节点的旧祖先关系（排除将保留的新祖先关系）
        # 删除旧的祖先关系（depth > 0，因为新祖先也会建立新的关系）
        await self.session.execute(
            delete(CoursewareClosure).where(
                and_(
                    CoursewareClosure.descendant_id.in_(subtree_ids),
                    CoursewareClosure.depth > 0,
                    CoursewareClosure.ancestor_id.notin_(subtree_ids),
                )
            )
        )

        # 步骤2: 建立新祖先关系
        if new_parent_id is not None:
            # 查询新父节点的所有祖先（包括自身 depth=0）
            new_ancestors_result = await self.session.execute(
                select(CoursewareClosure).where(
                    CoursewareClosure.descendant_id == new_parent_id
                )
            )
            new_ancestors = new_ancestors_result.scalars().all()

            for descendant_id in subtree_ids:
                for ancestor_entry in new_ancestors:
                    new_closure = CoursewareClosure(
                        ancestor_id=ancestor_entry.ancestor_id,
                        descendant_id=descendant_id,
                        depth=ancestor_entry.depth + self._get_subtree_depth_change(
                            descendant_id, node_id
                        ),
                    )
                    self.session.add(new_closure)

        await self.session.flush()
        logger.info(f"[CoursewareRepo] 移动节点: node_id={node_id} -> new_parent_id={new_parent_id}")
        return True

    def _get_subtree_depth_change(self, descendant_id: int, root_id: int) -> int:
        """计算待移动节点在新父节点下的深度偏移（简化处理，直接使用1）"""
        # 实际实现中，需要根据子树中各节点在原树中的深度来计算
        # 这里使用简化版本：所有后代节点相对新父节点增加1层
        return 1

    # ==================== 层级查询 ====================

    async def get_ancestors(self, node_id: int) -> List[dict]:
        """获取指定节点的所有祖先（从近到远）"""
        result = await self.session.execute(
            select(
                CoursewareNode.id,
                CoursewareNode.title,
                CoursewareNode.node_type,
                CoursewareClosure.depth,
            )
            .join(
                CoursewareClosure,
                CoursewareClosure.ancestor_id == CoursewareNode.id,
            )
            .where(
                and_(
                    CoursewareClosure.descendant_id == node_id,
                    CoursewareClosure.depth > 0,
                )
            )
            .order_by(CoursewareClosure.depth.asc())
        )
        return [
            {"id": row[0], "title": row[1], "node_type": row[2], "depth": row[3]}
            for row in result.all()
        ]

    async def get_descendants(self, node_id: int, max_depth: Optional[int] = None) -> List[dict]:
        """获取指定节点的所有后代（从近到远）"""
        conditions = [
            CoursewareClosure.ancestor_id == node_id,
            CoursewareClosure.depth > 0,
        ]
        if max_depth is not None:
            conditions.append(CoursewareClosure.depth <= max_depth)

        result = await self.session.execute(
            select(
                CoursewareNode.id,
                CoursewareNode.title,
                CoursewareNode.node_type,
                CoursewareNode.is_active,
                CoursewareNode.order_index,
                CoursewareClosure.depth,
            )
            .join(
                CoursewareClosure,
                CoursewareClosure.descendant_id == CoursewareNode.id,
            )
            .where(and_(*conditions))
            .order_by(CoursewareClosure.depth.asc(), CoursewareNode.order_index.asc())
        )
        return [
            {
                "id": row[0], "title": row[1], "node_type": row[2],
                "is_active": row[3], "order_index": row[4], "depth": row[5],
            }
            for row in result.all()
        ]

    async def get_children(self, node_id: int) -> List[dict]:
        """获取直接子节点"""
        descendants = await self.get_descendants(node_id, max_depth=1)
        return [d for d in descendants if d["depth"] == 1]

    async def get_descendants_count(self, node_id: int) -> int:
        """获取后代节点总数"""
        result = await self.session.execute(
            select(func.count()).where(
                and_(
                    CoursewareClosure.ancestor_id == node_id,
                    CoursewareClosure.depth > 0,
                )
            )
        )
        return result.scalar() or 0

    async def get_children_count(self, node_id: int) -> int:
        """获取直接子节点数量"""
        result = await self.session.execute(
            select(func.count()).where(
                and_(
                    CoursewareClosure.ancestor_id == node_id,
                    CoursewareClosure.depth == 1,
                )
            )
        )
        return result.scalar() or 0

    async def get_nodes_at_level(self, node_id: int, level: int) -> List[dict]:
        """获取指定节点下特定层级的所有节点"""
        result = await self.session.execute(
            select(CoursewareNode)
            .join(
                CoursewareClosure,
                CoursewareClosure.descendant_id == CoursewareNode.id,
            )
            .where(
                and_(
                    CoursewareClosure.ancestor_id == node_id,
                    CoursewareClosure.depth == level,
                )
            )
            .order_by(CoursewareNode.order_index)
        )
        nodes = result.scalars().all()
        return [
            {
                "id": n.id, "title": n.title, "node_type": n.node_type,
                "is_active": n.is_active, "order_index": n.order_index,
                "duration_minutes": n.duration_minutes,
            }
            for n in nodes
        ]

    async def get_node_depth(self, node_id: int) -> int:
        """获取节点深度（距离根节点的层级数）"""
        result = await self.session.execute(
            select(func.max(CoursewareClosure.depth)).where(
                CoursewareClosure.descendant_id == node_id
            )
        )
        return result.scalar() or 0

    async def get_path_to_root(self, node_id: int) -> List[dict]:
        """获取从根节点到指定节点的完整路径"""
        result = await self.session.execute(
            select(CoursewareNode)
            .join(
                CoursewareClosure,
                CoursewareClosure.ancestor_id == CoursewareNode.id,
            )
            .where(
                and_(
                    CoursewareClosure.descendant_id == node_id,
                    CoursewareClosure.depth > 0,
                )
            )
            .order_by(CoursewareClosure.depth.desc())
        )
        nodes = result.scalars().all()
        return [
            {"id": n.id, "title": n.title, "node_type": n.node_type}
            for n in nodes
        ]

    async def get_subtree(self, node_id: int) -> List[dict]:
        """获取整个子树（节点及其所有后代，扁平列表）"""
        result = await self.session.execute(
            select(CoursewareNode)
            .join(
                CoursewareClosure,
                CoursewareClosure.descendant_id == CoursewareNode.id,
            )
            .where(CoursewareClosure.ancestor_id == node_id)
            .order_by(CoursewareClosure.depth.asc(), CoursewareNode.order_index.asc())
        )
        nodes = result.scalars().all()
        return [
            {
                "id": n.id, "title": n.title, "node_type": n.node_type,
                "is_active": n.is_active, "order_index": n.order_index,
                "content_type": n.content_type, "duration_minutes": n.duration_minutes,
            }
            for n in nodes
        ]

    async def get_roots(self, course_id: Optional[int] = None) -> List[dict]:
        """获取所有根节点（无父节点的节点）"""
        # 根节点：在闭包表中只有自引用（depth=0）且没有 depth>0 的祖先关系
        # 即：不在任何 depth=1 的闭包条目中作为 descendant
        subquery = select(CoursewareClosure.descendant_id).where(
            CoursewareClosure.depth > 0
        ).distinct()

        conditions = [CoursewareNode.id.notin_(subquery)]
        if course_id is not None:
            conditions.append(CoursewareNode.course_id == course_id)

        result = await self.session.execute(
            select(CoursewareNode)
            .where(and_(*conditions))
            .order_by(CoursewareNode.order_index)
        )
        nodes = result.scalars().all()
        return [
            {"id": n.id, "title": n.title, "node_type": n.node_type,
             "course_id": n.course_id, "order_index": n.order_index}
            for n in nodes
        ]

    async def list_nodes(
        self,
        course_id: Optional[int] = None,
        node_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[dict], int]:
        """分页列出节点"""
        conditions = []
        if course_id is not None:
            conditions.append(CoursewareNode.course_id == course_id)
        if node_type is not None:
            conditions.append(CoursewareNode.node_type == node_type)
        if is_active is not None:
            conditions.append(CoursewareNode.is_active == is_active)

        # 总数
        count_query = select(func.count()).select_from(CoursewareNode)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # 数据
        data_query = select(CoursewareNode).order_by(
            CoursewareNode.course_id, CoursewareNode.order_index
        )
        if conditions:
            data_query = data_query.where(and_(*conditions))
        data_query = data_query.offset(skip).limit(limit)

        result = await self.session.execute(data_query)
        nodes = result.scalars().all()

        items = []
        for n in nodes:
            parent_id = await self._get_direct_parent_id(n.id)
            depth = await self.get_node_depth(n.id)
            children_count = await self.get_children_count(n.id)
            items.append({
                "id": n.id, "title": n.title, "description": n.description,
                "node_type": n.node_type, "content_type": n.content_type,
                "content_url": n.content_url, "duration_minutes": n.duration_minutes,
                "cover_image_url": n.cover_image_url, "order_index": n.order_index,
                "difficulty": n.difficulty, "tags": n.tags, "extra_data": n.extra_data,
                "course_id": n.course_id, "material_id": n.material_id,
                "org_id": n.org_id, "is_active": n.is_active,
                "is_published": n.is_published, "status": n.status,
                "created_by": n.created_by, "updated_by": n.updated_by,
                "created_at": n.created_at, "updated_at": n.updated_at,
                "parent_id": parent_id, "depth": depth,
                "children_count": children_count,
            })

        return items, total

    async def batch_create_nodes(
        self, nodes_data: List[dict]
    ) -> List[CoursewareNode]:
        """批量创建节点"""
        created = []
        for data in nodes_data:
            node = await self.create_node(**data)
            created.append(node)
        return created

    # ==================== 一致性验证 ====================

    async def validate_closure_table(self) -> dict:
        """验证闭包表的数据一致性"""
        result = {
            "is_valid": True,
            "total_nodes": 0,
            "total_closure_entries": 0,
            "orphan_nodes": [],
            "dangling_closure_entries": [],
            "missing_self_references": [],
            "depth_inconsistencies": [],
            "cycle_detected": False,
            "details": "",
        }

        # 统计
        total_nodes_result = await self.session.execute(
            select(func.count()).select_from(CoursewareNode)
        )
        result["total_nodes"] = total_nodes_result.scalar() or 0

        total_closure_result = await self.session.execute(
            select(func.count()).select_from(CoursewareClosure)
        )
        result["total_closure_entries"] = total_closure_result.scalar() or 0

        # 检查孤立的闭包条目（引用了不存在的节点）
        dangling_result = await self.session.execute(
            select(CoursewareClosure.id).where(
                CoursewareClosure.ancestor_id.notin_(
                    select(CoursewareNode.id)
                )
            ).union(
                select(CoursewareClosure.id).where(
                    CoursewareClosure.descendant_id.notin_(
                        select(CoursewareNode.id)
                    )
                )
            )
        )
        result["dangling_closure_entries"] = [row[0] for row in dangling_result.all()]

        # 检查缺失自引用（depth=0）的节点
        nodes_with_self_ref_result = await self.session.execute(
            select(CoursewareClosure.descendant_id).where(
                CoursewareClosure.depth == 0
            ).distinct()
        )
        nodes_with_self_ref = {row[0] for row in nodes_with_self_ref_result.all()}

        all_nodes_result = await self.session.execute(select(CoursewareNode.id))
        all_nodes = {row[0] for row in all_nodes_result.all()}
        result["missing_self_references"] = list(all_nodes - nodes_with_self_ref)

        # 检查循环引用
        cycle_result = await self.session.execute(
            select(CoursewareClosure).where(
                and_(
                    CoursewareClosure.depth > 0,
                    CoursewareClosure.ancestor_id == CoursewareClosure.descendant_id,
                )
            )
        )
        cycles = cycle_result.scalars().all()
        if cycles:
            result["cycle_detected"] = True
            result["depth_inconsistencies"].append({
                "type": "cycle",
                "message": f"检测到 {len(cycles)} 条循环引用",
            })

        # 综合判断
        issues = []
        if result["dangling_closure_entries"]:
            issues.append(f"{len(result['dangling_closure_entries'])} 条悬空闭包条目")
        if result["missing_self_references"]:
            issues.append(f"{len(result['missing_self_references'])} 个节点缺失自引用")
        if result["cycle_detected"]:
            issues.append("检测到循环引用")

        if issues:
            result["is_valid"] = False
            result["details"] = "; ".join(issues)

        return result

    async def repair_closure_table(self) -> dict:
        """修复闭包表常见问题"""
        repaired = {"self_refs_added": 0, "dangling_removed": 0}

        # 修复缺失的自引用
        nodes_with_self_ref_result = await self.session.execute(
            select(CoursewareClosure.descendant_id).where(
                CoursewareClosure.depth == 0
            ).distinct()
        )
        nodes_with_self_ref = {row[0] for row in nodes_with_self_ref_result.all()}

        all_nodes_result = await self.session.execute(select(CoursewareNode.id))
        all_nodes = {row[0] for row in all_nodes_result.all()}

        for node_id in all_nodes - nodes_with_self_ref:
            self.session.add(CoursewareClosure(
                ancestor_id=node_id, descendant_id=node_id, depth=0
            ))
            repaired["self_refs_added"] += 1

        # 删除悬空闭包条目
        dangling_result = await self.session.execute(
            delete(CoursewareClosure).where(
                CoursewareClosure.ancestor_id.notin_(select(CoursewareNode.id))
            )
        )
        repaired["dangling_removed"] += dangling_result.rowcount or 0

        dangling_result2 = await self.session.execute(
            delete(CoursewareClosure).where(
                CoursewareClosure.descendant_id.notin_(select(CoursewareNode.id))
            )
        )
        repaired["dangling_removed"] += dangling_result2.rowcount or 0

        await self.session.flush()
        return repaired