"""
课件图谱闭包表 - Pydantic Schema 定义
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ==================== 节点 Schema ====================

class CoursewareNodeBase(BaseModel):
    """课件节点基础字段"""
    title: str = Field(..., min_length=1, max_length=255, description="节点标题")
    description: Optional[str] = Field(None, description="节点描述")
    node_type: str = Field(default="lesson", description="节点类型: course/chapter/section/lesson/quiz")
    content_type: Optional[str] = Field(default="video", description="内容类型")
    content_url: Optional[str] = Field(None, max_length=500, description="内容URL")
    duration_minutes: int = Field(default=0, ge=0, description="时长(分钟)")
    cover_image_url: Optional[str] = Field(None, max_length=500, description="封面图URL")
    order_index: int = Field(default=0, ge=0, description="同级排序序号")
    difficulty: str = Field(default="intermediate", description="难度等级")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")
    course_id: Optional[int] = Field(None, description="关联课程ID")
    material_id: Optional[int] = Field(None, description="关联课件资源ID")
    org_id: Optional[int] = Field(None, description="所属组织")


class CoursewareNodeCreate(CoursewareNodeBase):
    """创建课件节点"""
    parent_id: Optional[int] = Field(None, description="父节点ID（null 表示根节点）")
    created_by: Optional[int] = Field(None, description="创建者")


class CoursewareNodeUpdate(BaseModel):
    """更新课件节点"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    node_type: Optional[str] = None
    content_type: Optional[str] = None
    content_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    cover_image_url: Optional[str] = None
    order_index: Optional[int] = None
    difficulty: Optional[str] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None
    course_id: Optional[int] = None
    material_id: Optional[int] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None
    status: Optional[str] = None
    updated_by: Optional[int] = None


class CoursewareNodeMove(BaseModel):
    """移动节点"""
    new_parent_id: Optional[int] = Field(None, description="新父节点ID（null 表示移动到根级）")
    new_order_index: Optional[int] = Field(None, description="新排序序号")


class CoursewareNodeResponse(BaseModel):
    """课件节点响应"""
    id: int
    title: str
    description: Optional[str] = None
    node_type: str
    content_type: Optional[str] = None
    content_url: Optional[str] = None
    duration_minutes: int
    cover_image_url: Optional[str] = None
    order_index: int
    difficulty: str
    tags: List[str]
    extra_data: Dict[str, Any]
    course_id: Optional[int] = None
    material_id: Optional[int] = None
    org_id: Optional[int] = None
    is_active: bool
    is_published: bool
    status: str
    created_by: Optional[int] = None
    updated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # 层级信息
    parent_id: Optional[int] = Field(None, description="直接父节点ID")
    depth: int = Field(0, description="当前节点深度")
    children_count: int = Field(0, description="直接子节点数量")

    class Config:
        from_attributes = True


class CoursewareTreeNode(BaseModel):
    """树形节点（含子节点）"""
    node: CoursewareNodeResponse
    children: List["CoursewareTreeNode"] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CoursewareNodeListResponse(BaseModel):
    """节点列表响应"""
    total: int
    items: List[CoursewareNodeResponse]


# ==================== 层级查询 Schema ====================

class AncestorNode(BaseModel):
    """祖先节点"""
    id: int
    title: str
    node_type: str
    depth: int = Field(..., description="与查询节点的层级距离（1=父节点, 2=祖父节点...）")


class DescendantNode(BaseModel):
    """后代节点"""
    id: int
    title: str
    node_type: str
    depth: int = Field(..., description="与查询节点的层级距离（1=子节点, 2=孙子节点...）")
    is_active: bool
    order_index: int


class LevelNodesResponse(BaseModel):
    """特定层级节点响应"""
    level: int = Field(..., description="层级深度")
    nodes: List[CoursewareNodeResponse]


class HierarchyResponse(BaseModel):
    """层级查询响应"""
    node: CoursewareNodeResponse
    ancestors: List[AncestorNode] = Field(default_factory=list)
    descendants: List[DescendantNode] = Field(default_factory=list)
    children: List[CoursewareNodeResponse] = Field(default_factory=list)
    total_descendants: int = 0


class CoursewareSubtreeResponse(BaseModel):
    """子树响应"""
    root: CoursewareNodeResponse
    tree: CoursewareTreeNode
    total_nodes: int


# ==================== 路径查询 Schema ====================

class NodePath(BaseModel):
    """节点路径"""
    path: List[CoursewareNodeResponse] = Field(..., description="从根到目标节点的完整路径")
    depth: int = Field(..., description="路径深度")


# ==================== 批量操作 Schema ====================

class BatchNodeCreate(BaseModel):
    """批量创建节点"""
    nodes: List[CoursewareNodeCreate] = Field(..., min_length=1, max_length=500)


class BatchNodeCreateResponse(BaseModel):
    """批量创建响应"""
    created: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    nodes: List[CoursewareNodeResponse] = Field(default_factory=list)


class BatchDeleteResponse(BaseModel):
    """批量删除响应"""
    deleted: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# ==================== 一致性验证 Schema ====================

class ClosureValidationResult(BaseModel):
    """闭包表一致性验证结果"""
    is_valid: bool
    total_nodes: int
    total_closure_entries: int
    orphan_nodes: List[int] = Field(default_factory=list, description="孤立节点（无闭包条目）")
    dangling_closure_entries: List[int] = Field(default_factory=list, description="悬空闭包条目（引用不存在的节点）")
    missing_self_references: List[int] = Field(default_factory=list, description="缺失自引用（depth=0）的节点")
    depth_inconsistencies: List[Dict[str, Any]] = Field(default_factory=list, description="深度不一致的条目")
    cycle_detected: bool = False
    details: str = ""


# ==================== 迁移 Schema ====================

class MigrationResult(BaseModel):
    """迁移结果"""
    success: bool
    source_type: str = Field(..., description="数据来源类型: flat/course_lessons")
    total_processed: int
    total_created: int
    total_errors: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    duration_seconds: float


class RollbackResult(BaseModel):
    """回滚结果"""
    success: bool
    nodes_deleted: int
    closure_entries_deleted: int
    errors: List[str] = Field(default_factory=list)
    duration_seconds: float