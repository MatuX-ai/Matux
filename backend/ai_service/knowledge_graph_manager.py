"""
知识图谱管理器 (基于Neo4j)
用于构建知识点关联关系和实现智能路径推荐
"""

try:
    from neo4j import Driver, GraphDatabase, Session

    NEO4J_AVAILABLE = True
except ImportError:
    # 如果没有安装neo4j，使用模拟实现
    GraphDatabase = None
    Driver = None
    Session = None
    NEO4J_AVAILABLE = False

from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeNode:
    """知识点节点"""

    node_id: str
    title: str
    description: str
    category: str
    difficulty_level: str  # beginner, intermediate, advanced, expert
    estimated_hours: float
    prerequisites: List[str]  # 先修知识点ID列表
    learning_outcomes: List[str]
    tags: List[str]
    created_at: datetime = None


@dataclass
class KnowledgeRelationship:
    """知识点关系"""

    from_node_id: str
    to_node_id: str
    relationship_type: str  # PREREQUISITE, SIMILAR, DEPENDS_ON, EXTENDS
    weight: float = 1.0  # 关系权重
    description: str = ""


@dataclass
class LearningPath:
    """学习路径"""

    path_id: str
    nodes: List[str]  # 知识点ID列表
    total_estimated_hours: float
    difficulty_progression: List[str]
    confidence_score: float
    alternative_paths: List[List[str]]


class KnowledgeGraphManager:
    """知识图谱管理器"""

    def __init__(
        self,
        uri: str = None,
        username: str = None,
        password: str = None,
        database: str = None,
    ):
        """
        初始化知识图谱管理器

        Args:
            uri: Neo4j数据库URI (默认使用配置值)
            username: 用户名 (默认使用配置值)
            password: 密码 (默认使用配置值)
            database: 数据库名称 (Neo4j Desktop 实例名称)
        """
        # 使用配置值作为默认值
        if uri is None:
            uri = settings.NEO4J_URI
        if username is None:
            username = settings.NEO4J_USERNAME
        if password is None:
            password = settings.NEO4J_PASSWORD
        if database is None:
            database = settings.NEO4J_DATABASE

        # 如果禁用了 Neo4j，直接使用模拟模式
        if not settings.NEO4J_ENABLED:
            logger.warning("Neo4j 功能已禁用，使用模拟模式")
            self.driver = None
            self._mock_mode = True
            self.database = database
            return

        if not NEO4J_AVAILABLE:
            logger.warning("Neo4j驱动未安装，使用模拟模式")
            self.driver = None
            self._mock_mode = True
            self.database = database
            return

        try:
            self.driver: Driver = GraphDatabase.driver(uri, auth=(username, password))
            self.database = database
            self._mock_mode = False
            self._initialize_schema()
            logger.info(f"知识图谱管理器初始化成功 (数据库: {database})")
        except Exception as e:
            logger.error(f"Neo4j连接失败: {e}")
            logger.info("将使用模拟模式继续运行")
            self.driver = None
            self._mock_mode = True
            self.database = database

    def _initialize_schema(self):
        """初始化数据库模式和约束"""
        if not self.driver:
            return

        with self.driver.session() as session:
            # 创建约束确保节点唯一性
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:KnowledgeNode) REQUIRE n.node_id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:UserNode) REQUIRE n.user_id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (n:SkillNode) REQUIRE n.skill_name IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    logger.warning(f"约束创建失败: {e}")

            # 创建索引提高查询性能
            indexes = [
                "CREATE INDEX IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.category)",
                "CREATE INDEX IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.difficulty_level)",
                "CREATE INDEX IF NOT EXISTS FOR (n:KnowledgeNode) ON (n.tags)",
                "CREATE INDEX IF NOT EXISTS FOR ()-[r:PREREQUISITE]-() ON (r.weight)",
            ]

            for index in indexes:
                try:
                    session.run(index)
                except Exception as e:
                    logger.warning(f"索引创建失败: {e}")

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j连接已关闭")

    def create_knowledge_node(self, node: KnowledgeNode) -> bool:
        """
        创建知识点节点

        Args:
            node: 知识点对象

        Returns:
            bool: 创建是否成功
        """
        if not self.driver:
            return False

        query = """
        MERGE (n:KnowledgeNode {node_id: $node_id})
        SET n.title = $title,
            n.description = $description,
            n.category = $category,
            n.difficulty_level = $difficulty_level,
            n.estimated_hours = $estimated_hours,
            n.prerequisites = $prerequisites,
            n.learning_outcomes = $learning_outcomes,
            n.tags = $tags,
            n.created_at = $created_at,
            n.updated_at = timestamp()
        RETURN n
        """

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    {
                        "node_id": node.node_id,
                        "title": node.title,
                        "description": node.description,
                        "category": node.category,
                        "difficulty_level": node.difficulty_level,
                        "estimated_hours": node.estimated_hours,
                        "prerequisites": node.prerequisites,
                        "learning_outcomes": node.learning_outcomes,
                        "tags": node.tags,
                        "created_at": node.created_at or datetime.now().isoformat(),
                    },
                )

                logger.info(f"知识点节点创建成功: {node.node_id}")
                return True

        except Exception as e:
            logger.error(f"创建知识点节点失败 {node.node_id}: {e}")
            return False

    def create_relationship(self, relationship: KnowledgeRelationship) -> bool:
        """
        创建知识点间的关系

        Args:
            relationship: 关系对象

        Returns:
            bool: 创建是否成功
        """
        if not self.driver:
            return False

        query = """
        MATCH (from:KnowledgeNode {node_id: $from_node_id})
        MATCH (to:KnowledgeNode {node_id: $to_node_id})
        MERGE (from)-[r:PREREQUISITE]->(to)
        SET r.type = $relationship_type,
            r.weight = $weight,
            r.description = $description,
            r.created_at = timestamp()
        RETURN r
        """

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    {
                        "from_node_id": relationship.from_node_id,
                        "to_node_id": relationship.to_node_id,
                        "relationship_type": relationship.relationship_type,
                        "weight": relationship.weight,
                        "description": relationship.description,
                    },
                )

                logger.info(
                    f"关系创建成功: {relationship.from_node_id} -> {relationship.to_node_id}"
                )
                return True

        except Exception as e:
            logger.error(
                f"创建关系失败 {relationship.from_node_id}->{relationship.to_node_id}: {e}"
            )
            return False

    def batch_create_nodes(self, nodes: List[KnowledgeNode]) -> Dict[str, int]:
        """
        批量创建知识点节点

        Args:
            nodes: 知识点列表

        Returns:
            Dict: 成功/失败统计
        """
        results = {"success": 0, "failed": 0}

        for node in nodes:
            if self.create_knowledge_node(node):
                results["success"] += 1
            else:
                results["failed"] += 1

        logger.info(f"批量创建完成: 成功{results['success']}, 失败{results['failed']}")
        return results

    def batch_create_relationships(
        self, relationships: List[KnowledgeRelationship]
    ) -> Dict[str, int]:
        """
        批量创建关系

        Args:
            relationships: 关系列表

        Returns:
            Dict: 成功/失败统计
        """
        results = {"success": 0, "failed": 0}

        for rel in relationships:
            if self.create_relationship(rel):
                results["success"] += 1
            else:
                results["failed"] += 1

        logger.info(
            f"批量关系创建完成: 成功{results['success']}, 失败{results['failed']}"
        )
        return results

    def find_shortest_path(
        self, start_node_id: str, end_node_id: str, max_depth: int = 10
    ) -> Optional[List[str]]:
        """
        查找两个知识点间的最短路径 (基于Dijkstra算法)

        Args:
            start_node_id: 起始节点ID
            end_node_id: 目标节点ID
            max_depth: 最大搜索深度

        Returns:
            List[str]: 路径节点ID列表，如果找不到则返回None
        """
        if not self.driver:
            return None

        query = """
        MATCH path = shortestPath(
            (start:KnowledgeNode {node_id: $start_id})-[:PREREQUISITE*1..$max_depth]->(end:KnowledgeNode {node_id: $end_id})
        )
        RETURN [node IN nodes(path) | node.node_id] AS path_nodes
        """

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    {
                        "start_id": start_node_id,
                        "end_id": end_node_id,
                        "max_depth": max_depth,
                    },
                )

                record = result.single()
                if record:
                    path = record["path_nodes"]
                    logger.info(f"找到最短路径: {len(path)} 个节点")
                    return path
                else:
                    logger.warning(f"未找到从 {start_node_id} 到 {end_node_id} 的路径")
                    return None

        except Exception as e:
            logger.error(f"路径查找失败: {e}")
            return None

    def recommend_learning_path(
        self,
        user_profile: Dict[str, Any],
        target_expertise: str,
        max_path_length: int = 8,
    ) -> Optional[LearningPath]:
        """
        基于用户画像推荐学习路径
        实现: graph.shortest_path(current_node, 'expert')

        Args:
            user_profile: 用户画像信息
            target_expertise: 目标专业领域
            max_path_length: 最大路径长度

        Returns:
            LearningPath: 推荐的学习路径
        """
        if not self.driver:
            return None

        user_id = user_profile.get("user_id", "anonymous")
        current_skills = user_profile.get("skills", {})
        user_profile.get("interests", [])

        # 查找用户当前水平对应的知识点
        current_node = self._find_current_knowledge_node(user_id, current_skills)
        if not current_node:
            # 如果找不到当前节点，使用入门级别节点
            current_node = self._find_entry_point(target_expertise)

        # 查找专家级别的目标节点
        target_node = self._find_expert_node(target_expertise)
        if not target_node:
            logger.warning(f"未找到 {target_expertise} 领域的专家节点")
            return None

        # 查找最短路径
        path_nodes = self.find_shortest_path(current_node, target_node, max_path_length)
        if not path_nodes:
            return None

        # 计算路径属性
        path_details = self._calculate_path_details(path_nodes)

        # 生成替代路径
        alternative_paths = self._generate_alternative_paths(
            current_node, target_node, path_nodes, max_path_length
        )

        return LearningPath(
            path_id=f"path_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            nodes=path_nodes,
            total_estimated_hours=path_details["total_hours"],
            difficulty_progression=path_details["difficulty_sequence"],
            confidence_score=path_details["confidence"],
            alternative_paths=alternative_paths[:2],  # 限制替代路径数量
        )

    def _find_current_knowledge_node(
        self, user_id: str, skills: Dict[str, float]
    ) -> Optional[str]:
        """查找用户当前知识水平对应的节点"""
        if not self.driver or not skills:
            return None

        # 查找用户已掌握的技能对应的知识点
        skill_names = list(skills.keys())

        query = """
        MATCH (n:KnowledgeNode)
        WHERE ANY(skill IN $skills WHERE skill IN n.tags)
        RETURN n.node_id, n.difficulty_level
        ORDER BY 
            CASE n.difficulty_level 
                WHEN 'beginner' THEN 1
                WHEN 'intermediate' THEN 2
                WHEN 'advanced' THEN 3
                WHEN 'expert' THEN 4
                ELSE 0
            END DESC
        LIMIT 1
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, {"skills": skill_names})
                record = result.single()
                if record:
                    return record["n.node_id"]
        except Exception as e:
            logger.error(f"查找当前节点失败: {e}")

        return None

    def _find_entry_point(self, expertise_area: str) -> Optional[str]:
        """查找指定领域的入门节点"""
        if not self.driver:
            return None

        query = """
        MATCH (n:KnowledgeNode)
        WHERE n.category = $category AND n.difficulty_level = 'beginner'
        RETURN n.node_id
        ORDER BY n.created_at
        LIMIT 1
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, {"category": expertise_area})
                record = result.single()
                if record:
                    return record["n.node_id"]
        except Exception as e:
            logger.error(f"查找入口节点失败: {e}")

        return None

    def _find_expert_node(self, expertise_area: str) -> Optional[str]:
        """查找指定领域的专家节点"""
        if not self.driver:
            return None

        query = """
        MATCH (n:KnowledgeNode)
        WHERE n.category = $category AND n.difficulty_level = 'expert'
        RETURN n.node_id
        ORDER BY n.created_at DESC
        LIMIT 1
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, {"category": expertise_area})
                record = result.single()
                if record:
                    return record["n.node_id"]
        except Exception as e:
            logger.error(f"查找专家节点失败: {e}")

        return None

    def _calculate_path_details(self, path_nodes: List[str]) -> Dict[str, Any]:
        """计算路径详细信息"""
        if not self.driver or not path_nodes:
            return {"total_hours": 0, "difficulty_sequence": [], "confidence": 0.0}

        query = """
        MATCH (n:KnowledgeNode)
        WHERE n.node_id IN $node_ids
        RETURN n.node_id, n.estimated_hours, n.difficulty_level
        ORDER BY CASE n.node_id 
            WHEN $first_node THEN 0
            WHEN $second_node THEN 1
            WHEN $third_node THEN 2
            ELSE 999
        END
        """

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    {
                        "node_ids": path_nodes,
                        "first_node": path_nodes[0] if path_nodes else "",
                        "second_node": path_nodes[1] if len(path_nodes) > 1 else "",
                        "third_node": path_nodes[2] if len(path_nodes) > 2 else "",
                    },
                )

                records = list(result)
                total_hours = sum(
                    record["n.estimated_hours"] or 0 for record in records
                )
                difficulty_sequence = [
                    record["n.difficulty_level"] for record in records
                ]

                # 计算置信度（基于路径完整性）
                confidence = min(1.0, len(records) / len(path_nodes))

                return {
                    "total_hours": total_hours,
                    "difficulty_sequence": difficulty_sequence,
                    "confidence": confidence,
                }

        except Exception as e:
            logger.error(f"计算路径详情失败: {e}")
            return {"total_hours": 0, "difficulty_sequence": [], "confidence": 0.0}

    def _generate_alternative_paths(
        self, start_node: str, end_node: str, main_path: List[str], max_length: int
    ) -> List[List[str]]:
        """生成替代学习路径"""
        alternative_paths = []

        if not self.driver:
            return alternative_paths

        # 查找具有相同起点和终点但不同的中间节点的路径
        query = """
        MATCH path = (start:KnowledgeNode {node_id: $start_id})-[:PREREQUISITE*2..$max_length]->(end:KnowledgeNode {node_id: $end_id})
        WHERE NONE(n IN nodes(path)[1..-1] WHERE n.node_id IN $exclude_nodes)
        RETURN [node IN nodes(path) | node.node_id] AS alt_path
        LIMIT 3
        """

        try:
            with self.driver.session() as session:
                result = session.run(
                    query,
                    {
                        "start_id": start_node,
                        "end_id": end_node,
                        "max_length": max_length,
                        "exclude_nodes": main_path[1:-1] if len(main_path) > 2 else [],
                    },
                )

                for record in result:
                    alt_path = record["alt_path"]
                    if alt_path and alt_path != main_path:
                        alternative_paths.append(alt_path)

        except Exception as e:
            logger.error(f"生成替代路径失败: {e}")

        return alternative_paths

    def get_node_recommendations(
        self, node_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """获取指定节点的推荐后续学习内容"""
        if not self.driver:
            return []

        query = """
        MATCH (current:KnowledgeNode {node_id: $node_id})-[:PREREQUISITE]->(next:KnowledgeNode)
        RETURN next.node_id, next.title, next.difficulty_level, next.estimated_hours
        ORDER BY next.difficulty_level, next.estimated_hours
        LIMIT $limit
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, {"node_id": node_id, "limit": limit})
                recommendations = []

                for record in result:
                    recommendations.append(
                        {
                            "node_id": record["next.node_id"],
                            "title": record["next.title"],
                            "difficulty_level": record["next.difficulty_level"],
                            "estimated_hours": record["next.estimated_hours"],
                        }
                    )

                return recommendations

        except Exception as e:
            logger.error(f"获取节点推荐失败: {e}")
            return []


# 便捷函数
def create_sample_knowledge_graph(kgm: KnowledgeGraphManager) -> bool:
    """创建示例知识图谱用于测试"""
    try:
        # 创建示例知识点
        nodes = [
            KnowledgeNode(
                node_id="python_basics",
                title="Python基础语法",
                description="Python编程语言基础概念和语法",
                category="programming",
                difficulty_level="beginner",
                estimated_hours=10.0,
                prerequisites=[],
                learning_outcomes=["掌握变量和数据类型", "理解基本语法结构"],
                tags=["python", "programming", "basics"],
            ),
            KnowledgeNode(
                node_id="python_oop",
                title="Python面向对象编程",
                description="Python中的类和对象概念",
                category="programming",
                difficulty_level="intermediate",
                estimated_hours=15.0,
                prerequisites=["python_basics"],
                learning_outcomes=["理解类和对象", "掌握继承和多态"],
                tags=["python", "oop", "programming"],
            ),
            KnowledgeNode(
                node_id="python_advanced",
                title="Python高级特性",
                description="Python高级特性和最佳实践",
                category="programming",
                difficulty_level="advanced",
                estimated_hours=20.0,
                prerequisites=["python_oop"],
                learning_outcomes=["掌握装饰器和生成器", "理解并发编程"],
                tags=["python", "advanced", "programming"],
            ),
            KnowledgeNode(
                node_id="python_expert",
                title="Python专家级应用",
                description="Python在实际项目中的专家级应用",
                category="programming",
                difficulty_level="expert",
                estimated_hours=25.0,
                prerequisites=["python_advanced"],
                learning_outcomes=["构建大型应用", "性能优化"],
                tags=["python", "expert", "applications"],
            ),
        ]

        # 批量创建节点
        node_results = kgm.batch_create_nodes(nodes)
        if node_results["failed"] > 0:
            logger.warning(f"节点创建失败: {node_results['failed']} 个")

        # 创建关系
        relationships = [
            KnowledgeRelationship("python_basics", "python_oop", "PREREQUISITE", 1.0),
            KnowledgeRelationship("python_oop", "python_advanced", "PREREQUISITE", 1.0),
            KnowledgeRelationship(
                "python_advanced", "python_expert", "PREREQUISITE", 1.0
            ),
        ]

        rel_results = kgm.batch_create_relationships(relationships)
        if rel_results["failed"] > 0:
            logger.warning(f"关系创建失败: {rel_results['failed']} 个")

        logger.info("示例知识图谱创建完成")
        return True

    except Exception as e:
        logger.error(f"创建示例知识图谱失败: {e}")
        return False
