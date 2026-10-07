"""
课件图谱闭包表 - Service 层

业务逻辑封装，包括：
- 节点的增删改查
- 层级查询（祖先、后代、子树、路径）
- 树形结构构建
- 数据一致性验证
- 批量操作
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.courseware_repository import CoursewareRepository
from schemas.courseware_closure import (
    AncestorNode,
    BatchNodeCreate,
    BatchNodeCreateResponse,
    CoursewareNodeResponse,
    CoursewareTreeNode,
    ClosureValidationResult,
    DescendantNode,
    HierarchyResponse,
    LevelNodesResponse,
    NodePath,
    CoursewareSubtreeResponse,
)

logger = logging.getLogger(__name__)


class CoursewareService:
    """课件图谱服务"""

    def __init__(self, session: AsyncSession):
        self.repo = CoursewareRepository(session)

    # ==================== 节点 CRUD ====================

    async def create_node(self, data: dict) -> Optional[CoursewareNodeResponse]:
        """创建节点"""
        parent_id = data.pop("parent_id", None)
        node = await self.repo.create_node(parent_id=parent_id, **data)
        if node:
            return await self._build_node_response(node)
        return None

    async def get_node(self, node_id: int) -> Optional[CoursewareNodeResponse]:
        """获取节点"""
        node = await self.repo.get_node(node_id)
        if node is None:
            return None
        return await self._build_node_response(node)

    async def update_node(self, node_id: int, data: dict) -> Optional[CoursewareNodeResponse]:
        """更新节点"""
        node = await self.repo.update_node(node_id, **data)
        if node is None:
            return None
        return await self._build_node_response(node)

    async def delete_node(self, node_id: int, cascade: bool = True) -> bool:
        """删除节点"""
        return await self.repo.delete_node(node_id, cascade=cascade)

    async def move_node(self, node_id: int, new_parent_id: Optional[int]) -> bool:
        """移动节点"""
        return await self.repo.move_node(node_id, new_parent_id)

    # ==================== 层级查询 ====================

    async def get_hierarchy(self, node_id: int) -> Optional[HierarchyResponse]:
        """获取节点的完整层级信息"""
        node = await self.repo.get_node(node_id)
        if node is None:
            return None

        node_resp = await self._build_node_response(node)

        ancestors_raw = await self.repo.get_ancestors(node_id)
        ancestors = [AncestorNode(**a) for a in ancestors_raw]

        descendants_raw = await self.repo.get_descendants(node_id)
        descendants = [DescendantNode(**d) for d in descendants_raw]

        children = [d for d in descendants if d.depth == 1]
        children_resp = [
            await self._build_node_response(await self.repo.get_node(c.id))
            for c in children
        ]

        total_descendants = await self.repo.get_descendants_count(node_id)

        return HierarchyResponse(
            node=node_resp,
            ancestors=ancestors,
            descendants=descendants,
            children=children_resp,
            total_descendants=total_descendants,
        )

    async def get_ancestors(self, node_id: int) -> List[AncestorNode]:
        """获取祖先节点"""
        raw = await self.repo.get_ancestors(node_id)
        return [AncestorNode(**a) for a in raw]

    async def get_descendants(self, node_id: int, max_depth: Optional[int] = None) -> List[DescendantNode]:
        """获取后代节点"""
        raw = await self.repo.get_descendants(node_id, max_depth=max_depth)
        return [DescendantNode(**d) for d in raw]

    async def get_nodes_at_level(self, node_id: int, level: int) -> LevelNodesResponse:
        """获取特定层级节点"""
        raw = await self.repo.get_nodes_at_level(node_id, level)
        nodes = []
        for n in raw:
            node = await self.repo.get_node(n["id"])
            if node:
                nodes.append(await self._build_node_response(node))
        return LevelNodesResponse(level=level, nodes=nodes)

    async def get_path(self, node_id: int) -> Optional[NodePath]:
        """获取从根到节点的路径"""
        path = await self.repo.get_path_to_root(node_id)
        if not path:
            return None
        nodes = []
        for p in path:
            node = await self.repo.get_node(p["id"])
            if node:
                nodes.append(await self._build_node_response(node))
        return NodePath(path=nodes, depth=len(nodes))

    async def get_subtree(self, node_id: int) -> Optional[CoursewareSubtreeResponse]:
        """获取子树"""
        root = await self.repo.get_node(node_id)
        if root is None:
            return None

        subtree_raw = await self.repo.get_subtree(node_id)
        tree = await self._build_tree(node_id, subtree_raw)
        root_resp = await self._build_node_response(root)

        return CoursewareSubtreeResponse(
            root=root_resp,
            tree=tree,
            total_nodes=len(subtree_raw),
        )

    async def get_roots(self, course_id: Optional[int] = None) -> List[dict]:
        """获取根节点"""
        return await self.repo.get_roots(course_id=course_id)

    async def list_nodes(
        self,
        course_id: Optional[int] = None,
        node_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        """分页列出节点"""
        items, total = await self.repo.list_nodes(
            course_id=course_id,
            node_type=node_type,
            is_active=is_active,
            skip=skip,
            limit=limit,
        )
        return {"total": total, "items": items}

    # ==================== 批量操作 ====================

    async def batch_create_nodes(self, data: BatchNodeCreate) -> BatchNodeCreateResponse:
        """批量创建节点"""
        created_nodes = []
        errors = []

        for i, node_data in enumerate(data.nodes):
            try:
                node_dict = node_data.model_dump()
                node = await self.create_node(node_dict)
                if node:
                    created_nodes.append(node)
            except Exception as e:
                errors.append({"index": i, "error": str(e)})

        return BatchNodeCreateResponse(
            created=len(created_nodes),
            errors=errors,
            nodes=created_nodes,
        )

    # ==================== 一致性验证 ====================

    async def validate(self) -> ClosureValidationResult:
        """验证闭包表一致性"""
        result = await self.repo.validate_closure_table()
        return ClosureValidationResult(**result)

    async def repair(self) -> dict:
        """修复闭包表"""
        return await self.repo.repair_closure_table()

    # ==================== 内部辅助方法 ====================

    async def _build_node_response(self, node) -> CoursewareNodeResponse:
        """构建节点响应对象"""
        parent_id = await self.repo._get_direct_parent_id(node.id)
        depth = await self.repo.get_node_depth(node.id)
        children_count = await self.repo.get_children_count(node.id)

        return CoursewareNodeResponse(
            id=node.id,
            title=node.title,
            description=node.description,
            node_type=node.node_type,
            content_type=node.content_type,
            content_url=node.content_url,
            duration_minutes=node.duration_minutes,
            cover_image_url=node.cover_image_url,
            order_index=node.order_index,
            difficulty=node.difficulty,
            tags=node.tags or [],
            extra_data=node.extra_data or {},
            course_id=node.course_id,
            material_id=node.material_id,
            org_id=node.org_id,
            is_active=node.is_active,
            is_published=node.is_published,
            status=node.status,
            created_by=node.created_by,
            updated_by=node.updated_by,
            created_at=node.created_at,
            updated_at=node.updated_at,
            parent_id=parent_id,
            depth=depth,
            children_count=children_count,
        )

    async def _build_tree(
        self, root_id: int, flat_nodes: List[dict]
    ) -> CoursewareTreeNode:
        """从扁平列表构建树形结构"""
        # 构建节点映射
        node_map: Dict[int, dict] = {n["id"]: n for n in flat_nodes}

        # 构建父子关系
        children_map: Dict[int, List[int]] = {}
        for n in flat_nodes:
            # 通过闭包表查询直接子节点
            children = await self.repo.get_children(n["id"])
            children_map[n["id"]] = [c["id"] for c in children]

        async def build_recursive(node_id: int) -> CoursewareTreeNode:
            node_data = node_map.get(node_id)
            if node_data is None:
                node = await self.repo.get_node(node_id)
                if node is None:
                    return CoursewareTreeNode(
                        node=CoursewareNodeResponse(
                            id=node_id, title="未知", node_type="unknown",
                            description=None, content_type=None, content_url=None,
                            duration_minutes=0, cover_image_url=None, order_index=0,
                            difficulty="intermediate", tags=[], extra_data={},
                            course_id=None, material_id=None, org_id=None,
                            is_active=False, is_published=False, status="unknown",
                            created_by=None, updated_by=None,
                            created_at=node.created_at if node else None,
                            updated_at=node.updated_at if node else None,
                            parent_id=None, depth=0, children_count=0,
                        ),
                        children=[],
                    )
                node_resp = await self._build_node_response(node)
            else:
                node_resp = CoursewareNodeResponse(
                    id=node_data["id"], title=node_data["title"],
                    node_type=node_data["node_type"],
                    description=None, content_type=node_data.get("content_type"),
                    content_url=None, duration_minutes=node_data.get("duration_minutes", 0),
                    cover_image_url=None, order_index=node_data.get("order_index", 0),
                    difficulty="intermediate", tags=[], extra_data={},
                    course_id=None, material_id=None, org_id=None,
                    is_active=node_data.get("is_active", True),
                    is_published=False, status="draft",
                    created_by=None, updated_by=None,
                    created_at=datetime.min, updated_at=datetime.min,
                    parent_id=None, depth=0, children_count=0,
                )

            child_ids = children_map.get(node_id, [])
            child_nodes = []
            for child_id in child_ids:
                child_tree = await build_recursive(child_id)
                child_nodes.append(child_tree)

            return CoursewareTreeNode(node=node_resp, children=child_nodes)

        return await build_recursive(root_id)