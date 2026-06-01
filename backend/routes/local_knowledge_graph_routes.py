"""
本地知识图谱API路由
提供桌面端本地知识图谱管理的HTTP接口
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Set
import logging

from services.local_knowledge_graph import LocalKnowledgeGraph, StudentLearningProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/local-knowledge-graph", tags=["本地知识图谱"])

# 全局知识图谱实例
_knowledge_graph: Optional[LocalKnowledgeGraph] = None
_student_profiles: Dict[str, StudentLearningProfile] = {}


def get_knowledge_graph() -> LocalKnowledgeGraph:
    """获取知识图谱实例"""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = LocalKnowledgeGraph()
    return _knowledge_graph


def get_student_profile(
    student_id: str,
    kg: LocalKnowledgeGraph = Depends(get_knowledge_graph)
) -> StudentLearningProfile:
    """获取学生画像实例"""
    global _student_profiles
    if student_id not in _student_profiles:
        _student_profiles[student_id] = StudentLearningProfile(student_id, kg)
    return _student_profiles[student_id]


# ============ 请求模型 ============

class KnowledgeNodeRequest(BaseModel):
    """知识节点创建请求"""
    node_id: str = Field(..., description="节点唯一标识")
    title: str = Field(..., description="知识点标题")
    content: str = Field(..., description="知识点内容")
    knowledge_type: str = Field(..., description="知识类型")
    difficulty: float = Field(default=0.5, ge=0.0, le=1.0, description="难度等级")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


class KnowledgeEdgeRequest(BaseModel):
    """知识关系创建请求"""
    source_id: str = Field(..., description="源节点ID")
    target_id: str = Field(..., description="目标节点ID")
    edge_type: str = Field(default="prerequisite", description="边类型")
    weight: float = Field(default=1.0, ge=0.0, description="关系权重")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


class LearningPathRequest(BaseModel):
    """学习路径请求"""
    start_node: str = Field(..., description="起始节点ID")
    end_node: str = Field(..., description="目标节点ID")
    max_difficulty: float = Field(default=0.8, ge=0.0, le=1.0, description="最大难度")


class RelatedKnowledgeRequest(BaseModel):
    """相关知识搜索请求"""
    query: str = Field(..., description="查询文本")
    knowledge_type: Optional[str] = Field(default=None, description="知识类型过滤")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")


class StudentLearningRecord(BaseModel):
    """学生学习记录"""
    node_id: str = Field(..., description="知识节点ID")
    performance: float = Field(..., ge=0.0, le=1.0, description="学习表现")
    time_spent: int = Field(..., ge=0, description="学习时间（秒）")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="额外元数据")


class KnowledgeGapsRequest(BaseModel):
    """知识缺口分析请求"""
    mastered_nodes: List[str] = Field(..., description="已掌握的节点ID列表")
    target_nodes: List[str] = Field(..., description="目标节点ID列表")


# ============ 响应模型 ============

class KnowledgeNodeResponse(BaseModel):
    """知识节点响应"""
    success: bool
    message: str
    node_id: Optional[str] = None


class KnowledgeEdgeResponse(BaseModel):
    """知识关系响应"""
    success: bool
    message: str
    edge_info: Optional[Dict[str, Any]] = None


class LearningPathResponse(BaseModel):
    """学习路径响应"""
    success: bool
    message: str
    path: Optional[List[str]] = None
    path_length: Optional[int] = None


class RelatedKnowledgeResponse(BaseModel):
    """相关知识响应"""
    success: bool
    message: str
    results: List[Dict[str, Any]]


class StatisticsResponse(BaseModel):
    """统计信息响应"""
    success: bool
    message: str
    statistics: Dict[str, Any]


class StudentProgressResponse(BaseModel):
    """学生学习进度响应"""
    success: bool
    message: str
    progress: Dict[str, Any]


class RecommendationsResponse(BaseModel):
    """个性化推荐响应"""
    success: bool
    message: str
    recommendations: List[Dict[str, Any]]


# ============ API端点 ============

@router.post("/nodes", response_model=KnowledgeNodeResponse)
async def add_knowledge_node(
    request: KnowledgeNodeRequest,
    kg: LocalKnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    添加知识节点

    - **node_id**: 节点唯一标识
    - **title**: 知识点标题
    - **content**: 知识点内容
    - **knowledge_type**: 知识类型 (concept, skill, practice, etc.)
    - **difficulty**: 难度等级 (0.0-1.0)
    """
    try:
        success = kg.add_knowledge_node(
            node_id=request.node_id,
            title=request.title,
            content=request.content,
            knowledge_type=request.knowledge_type,
            difficulty=request.difficulty,
            metadata=request.metadata
        )

        if success:
            return KnowledgeNodeResponse(
                success=True,
                message="知识节点添加成功",
                node_id=request.node_id
            )
        else:
            raise HTTPException(status_code=500, detail="知识节点添加失败")

    except Exception as e:
        logger.error(f"添加知识节点失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/edges", response_model=KnowledgeEdgeResponse)
async def add_knowledge_edge(
    request: KnowledgeEdgeRequest,
    kg: LocalKnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    添加知识关系边

    - **source_id**: 源节点ID
    - **target_id**: 目标节点ID
    - **edge_type**: 边类型 (prerequisite, related, contains, etc.)
    - **weight**: 关系权重
    """
    try:
        success = kg.add_knowledge_edge(
            source_id=request.source_id,
            target_id=request.target_id,
            edge_type=request.edge_type,
            weight=request.weight,
            metadata=request.metadata
        )

        if success:
            return KnowledgeEdgeResponse(
                success=True,
                message="知识关系添加成功",
                edge_info={
                    "source": request.source_id,
                    "target": request.target_id,
                    "type": request.edge_type
                }
            )
        else:
            raise HTTPException(status_code=500, detail="知识关系添加失败")

    except Exception as e:
        logger.error(f"添加知识关系失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/learning-path", response_model=LearningPathResponse)
async def get_learning_path(
    request: LearningPathRequest,
    kg: LocalKnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    获取学习路径

    - **start_node**: 起始节点ID
    - **end_node**: 目标节点ID
    - **max_difficulty**: 最大难度等级
    """
    try:
        path = kg.get_knowledge_path(
            start_node=request.start_node,
            end_node=request.end_node,
            max_difficulty=request.max_difficulty
        )

        if path:
            return LearningPathResponse(
                success=True,
                message="学习路径获取成功",
                path=path,
                path_length=len(path)
            )
        else:
            return LearningPathResponse(
                success=False,
                message="未找到合适的学习路径",
                path=None,
                path_length=0
            )

    except Exception as e:
        logger.error(f"获取学习路径失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=RelatedKnowledgeResponse)
async def search_related_knowledge(
    request: RelatedKnowledgeRequest,
    kg: LocalKnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    基于语义搜索获取相关知识

    - **query**: 查询文本
    - **knowledge_type**: 知识类型过滤 (可选)
    - **top_k**: 返回结果数量
    """
    try:
        results = kg.get_related_knowledge(
            query=request.query,
            knowledge_type=request.knowledge_type,
            top_k=request.top_k
        )

        return RelatedKnowledgeResponse(
            success=True,
            message="相关知识搜索成功",
            results=results
        )

    except Exception as e:
        logger.error(f"搜索相关知识失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(
    kg: LocalKnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    获取知识图谱统计信息

    返回节点数量、边数量、知识类型分布等统计信息
    """
    try:
        statistics = kg.get_knowledge_statistics()

        return StatisticsResponse(
            success=True,
            message="统计信息获取成功",
            statistics=statistics
        )

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/students/{student_id}/learning-record")
async def record_learning(
    student_id: str,
    record: StudentLearningRecord,
    profile: StudentLearningProfile = Depends(get_student_profile)
):
    """
    记录学生学习行为

    - **student_id**: 学生ID
    - **node_id**: 知识节点ID
    - **performance**: 学习表现 (0.0-1.0)
    - **time_spent**: 学习时间（秒）
    """
    try:
        profile.record_learning(
            node_id=record.node_id,
            performance=record.performance,
            time_spent=record.time_spent,
            metadata=record.metadata
        )

        return {
            "success": True,
            "message": "学习记录保存成功",
            "student_id": student_id
        }

    except Exception as e:
        logger.error(f"记录学习行为失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/{student_id}/progress", response_model=StudentProgressResponse)
async def get_student_progress(
    student_id: str,
    profile: StudentLearningProfile = Depends(get_student_profile)
):
    """
    获取学生学习进度

    - **student_id**: 学生ID
    """
    try:
        progress = profile.get_learning_progress()

        return StudentProgressResponse(
            success=True,
            message="学习进度获取成功",
            progress=progress
        )

    except Exception as e:
        logger.error(f"获取学习进度失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/{student_id}/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(
    student_id: str,
    top_k: int = 5,
    profile: StudentLearningProfile = Depends(get_student_profile)
):
    """
    获取个性化学习推荐

    - **student_id**: 学生ID
    - **top_k**: 推荐数量
    """
    try:
        recommendations = profile.get_personalized_recommendations(top_k=top_k)

        return RecommendationsResponse(
            success=True,
            message="个性化推荐获取成功",
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"获取个性化推荐失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-gaps")
async def analyze_knowledge_gaps(
    request: KnowledgeGapsRequest,
    kg: LocalKnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    分析学生知识缺口

    - **mastered_nodes**: 已掌握的节点ID列表
    - **target_nodes**: 目标节点ID列表
    """
    try:
        mastered_set = set(request.mastered_nodes)
        target_set = set(request.target_nodes)

        gaps = kg.get_student_knowledge_gaps(mastered_set, target_set)

        return {
            "success": True,
            "message": "知识缺口分析完成",
            "gaps": gaps,
            "gap_count": len(gaps)
        }

    except Exception as e:
        logger.error(f"分析知识缺口失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_knowledge_graph(
    output_file: str = "knowledge_graph_export.json",
    kg: LocalKnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    导出知识图谱

    - **output_file**: 输出文件路径
    """
    try:
        success = kg.export_knowledge_graph(output_file)

        if success:
            return {
                "success": True,
                "message": "知识图谱导出成功",
                "output_file": output_file
            }
        else:
            raise HTTPException(status_code=500, detail="知识图谱导出失败")

    except Exception as e:
        logger.error(f"导出知识图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_knowledge_graph(
    input_file: str,
    kg: LocalKnowledgeGraph = Depends(get_knowledge_graph)
):
    """
    导入知识图谱

    - **input_file**: 输入文件路径
    """
    try:
        success = kg.import_knowledge_graph(input_file)

        if success:
            return {
                "success": True,
                "message": "知识图谱导入成功",
                "input_file": input_file
            }
        else:
            raise HTTPException(status_code=500, detail="知识图谱导入失败")

    except Exception as e:
        logger.error(f"导入知识图谱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "本地知识图谱服务",
        "features": [
            "本地向量存储",
            "知识图谱管理",
            "学习路径推荐",
            "个性化学习画像",
            "语义搜索",
            "知识缺口分析"
        ]
    }