"""
课件图谱闭包表 (Closure Table) 数据模型

闭包表结构设计：
- courseware_nodes: 课件节点基本信息表
- courseware_closures: 节点关系闭包表（存储所有祖先-后代关系）

Closure Table 优势：
1. 查询子树/祖先/后代只需单次 JOIN，O(1) 层级查询
2. 支持无限层级深度
3. 移动节点只需更新相关路径，无需重建整棵树
4. 相比邻接表模型，避免了递归 CTE 的性能问题
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON, Index, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from utils.database import Base


class CoursewareNode(Base):
    """课件节点基本信息表"""

    __tablename__ = "courseware_nodes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, comment="节点标题")
    description = Column(Text, nullable=True, comment="节点描述")
    node_type = Column(
        String(50), nullable=False, default="lesson", index=True,
        comment="节点类型: course/chapter/section/lesson/quiz"
    )
    content_type = Column(
        String(50), nullable=True, default="video",
        comment="内容类型: video/text/quiz/exercise/interactive"
    )
    content_url = Column(String(500), nullable=True, comment="内容URL")
    duration_minutes = Column(Integer, default=0, comment="时长(分钟)")
    cover_image_url = Column(String(500), nullable=True, comment="封面图URL")
    order_index = Column(Integer, default=0, comment="同级排序序号")
    difficulty = Column(String(50), default="intermediate", comment="难度等级")
    tags = Column(JSON, default=list, comment="标签列表")
    extra_data = Column(JSON, default=dict, comment="扩展元数据")

    # 关联课程（顶层节点）
    course_id = Column(
        Integer, ForeignKey("courses.id"), nullable=True, index=True,
        comment="关联课程ID"
    )
    # 关联课件资源
    material_id = Column(
        Integer, ForeignKey("unified_materials.id"), nullable=True,
        comment="关联统一课件资源ID"
    )

    # 状态控制
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_published = Column(Boolean, default=False, comment="是否发布")
    status = Column(String(50), default="draft", comment="状态: draft/published/archived")

    # 权限相关
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True, comment="所属组织")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="创建者")
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="更新者")

    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    course = relationship("Course", foreign_keys=[course_id])
    material = relationship("UnifiedMaterial", foreign_keys=[material_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    # 闭包表关系
    ancestors = relationship(
        "CoursewareClosure",
        foreign_keys="CoursewareClosure.descendant_id",
        back_populates="descendant",
        cascade="all, delete-orphan",
    )
    descendants = relationship(
        "CoursewareClosure",
        foreign_keys="CoursewareClosure.ancestor_id",
        back_populates="ancestor",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_cwn_course_id", "course_id"),
        Index("idx_cwn_node_type", "node_type"),
        Index("idx_cwn_org_id", "org_id"),
        Index("idx_cwn_active", "is_active"),
        Index("idx_cwn_order", "course_id", "order_index"),
        Index("idx_cwn_status", "status"),
    )

    def __repr__(self):
        return f"<CoursewareNode(id={self.id}, title='{self.title}', type='{self.node_type}')>"


class CoursewareClosure(Base):
    """
    课件节点关系闭包表

    存储所有祖先-后代关系对，包括自身到自身的关系（depth=0）。
    该表是 Closure Table 模式的核心，将树形结构的递归查询转化为等值查询。

    示例：对于层级结构 A -> B -> C
    | ancestor_id | descendant_id | depth |
    |-------------|---------------|-------|
    | A           | A             | 0     |
    | B           | B             | 0     |
    | C           | C             | 0     |
    | A           | B             | 1     |
    | B           | C             | 1     |
    | A           | C             | 2     |
    """

    __tablename__ = "courseware_closures"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ancestor_id = Column(
        Integer, ForeignKey("courseware_nodes.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="祖先节点ID"
    )
    descendant_id = Column(
        Integer, ForeignKey("courseware_nodes.id", ondelete="CASCADE"),
        nullable=False, index=True, comment="后代节点ID"
    )
    depth = Column(Integer, nullable=False, default=0, comment="层级深度（0表示自身）")

    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    # 关系
    ancestor = relationship(
        "CoursewareNode",
        foreign_keys=[ancestor_id],
        back_populates="descendants",
    )
    descendant = relationship(
        "CoursewareNode",
        foreign_keys=[descendant_id],
        back_populates="ancestors",
    )

    __table_args__ = (
        UniqueConstraint("ancestor_id", "descendant_id", name="uq_closure_pair"),
        Index("idx_closure_ancestor", "ancestor_id"),
        Index("idx_closure_descendant", "descendant_id"),
        Index("idx_closure_depth", "ancestor_id", "depth"),
        Index("idx_closure_pair_depth", "ancestor_id", "descendant_id", "depth"),
    )

    def __repr__(self):
        return f"<CoursewareClosure(ancestor={self.ancestor_id}, descendant={self.descendant_id}, depth={self.depth})>"