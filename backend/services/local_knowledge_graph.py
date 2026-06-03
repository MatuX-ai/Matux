"""
本地知识图谱服务
基于ChromaDB和NetworkX的本地知识图谱实现
用于桌面端离线知识管理和个性化学习路径推荐
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib

import networkx as nx
import chromadb

logger = logging.getLogger(__name__)


class LocalKnowledgeGraph:
    """本地知识图谱管理器"""

    def __init__(self, data_dir: str = "./local_knowledge_graph"):
        """
        初始化本地知识图谱

        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # 初始化向量数据库
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.data_dir / "chroma_db")
        )

        # 初始化图数据库
        self.graph = nx.DiGraph()

        # 知识节点集合
        self.collections: Dict[str, chromadb.Collection] = {}

        # 加载已有数据
        self._load_existing_data()

        logger.info(f"本地知识图谱初始化完成，数据目录: {self.data_dir}")

    def _generate_embedding(self, text: str) -> List[float]:
        """
        生成文本嵌入向量（使用简单的哈希方法）

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        # 使用简单的哈希方法生成固定长度向量
        text_bytes = text.encode('utf-8')
        hash_obj = hashlib.sha256(text_bytes)
        hash_hex = hash_obj.hexdigest()

        # 将哈希转换为向量
        vector = []
        for i in range(0, len(hash_hex), 2):
            byte_val = int(hash_hex[i:i+2], 16)
            normalized = byte_val / 255.0  # 归一化到 [0, 1]
            vector.append(normalized)

        # 确保向量长度为128
        while len(vector) < 128:
            vector.append(0.0)
        return vector[:128]

    def _load_existing_data(self):
        """加载已有数据"""
        try:
            # 加载图数据
            graph_file = self.data_dir / "knowledge_graph.gml"
            if graph_file.exists():
                self.graph = nx.read_gml(graph_file)
                logger.info(
                    f"加载知识图谱: {self.graph.number_of_nodes()} 个节点, {self.graph.number_of_edges()} 条边")

            # 加载集合信息
            collections_file = self.data_dir / "collections.json"
            if collections_file.exists():
                with open(collections_file, 'r', encoding='utf-8') as f:
                    collections_data = json.load(f)
                    for name, metadata in collections_data.items():
                        try:
                            self.collections[name] = self.chroma_client.get_or_create_collection(
                                name=name,
                                metadata=metadata
                            )
                        except Exception as e:
                            logger.warning(f"加载集合 {name} 失败: {e}")

        except Exception as e:
            logger.warning(f"加载已有数据失败: {e}")

    def _save_data(self):
        """保存数据"""
        try:
            # 保存图数据
            graph_file = self.data_dir / "knowledge_graph.gml"
            nx.write_gml(self.graph, str(graph_file))

            # 保存集合信息
            collections_file = self.data_dir / "collections.json"
            collections_data = {
                name: collection.metadata
                for name, collection in self.collections.items()
            }
            with open(collections_file, 'w', encoding='utf-8') as f:
                json.dump(collections_data, f, ensure_ascii=False, indent=2)

            logger.info("知识图谱数据保存成功")

        except Exception as e:
            logger.error(f"保存数据失败: {e}")

    def add_knowledge_node(
        self,
        node_id: str,
        title: str,
        content: str,
        knowledge_type: str,
        difficulty: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加知识节点

        Args:
            node_id: 节点唯一标识
            title: 知识点标题
            content: 知识点内容
            knowledge_type: 知识类型 (concept, skill, practice, etc.)
            difficulty: 难度等级 (0.0-1.0)
            metadata: 额外元数据

        Returns:
            是否添加成功
        """
        try:
            # 添加到图数据库
            self.graph.add_node(
                node_id,
                title=title,
                content=content,
                knowledge_type=knowledge_type,
                difficulty=difficulty,
                created_at=datetime.now().isoformat(),
                **(metadata or {})
            )

            # 添加到向量数据库
            collection_name = knowledge_type
            if collection_name not in self.collections:
                self.collections[collection_name] = self.chroma_client.get_or_create_collection(
                    name=collection_name,
                    metadata={"type": knowledge_type}
                )

            # 生成嵌入向量
            embedding = self._generate_embedding(f"{title} {content}")

            # 添加到集合
            self.collections[collection_name].add(
                documents=[content],
                metadatas=[{
                    "node_id": node_id,
                    "title": title,
                    "knowledge_type": knowledge_type,
                    "difficulty": difficulty,
                    "created_at": datetime.now().isoformat(),
                    **(metadata or {})
                }],
                ids=[node_id],
                embeddings=[embedding]
            )

            self._save_data()
            logger.info(f"添加知识节点: {node_id} - {title}")
            return True

        except Exception as e:
            logger.error(f"添加知识节点失败: {e}")
            return False

    def add_knowledge_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str = "prerequisite",
        weight: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加知识关系边

        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            edge_type: 边类型 (prerequisite, related, contains, etc.)
            weight: 关系权重
            metadata: 额外元数据

        Returns:
            是否添加成功
        """
        try:
            self.graph.add_edge(
                source_id,
                target_id,
                edge_type=edge_type,
                weight=weight,
                created_at=datetime.now().isoformat(),
                **(metadata or {})
            )

            self._save_data()
            logger.info(f"添加知识关系: {source_id} -> {target_id} ({edge_type})")
            return True

        except Exception as e:
            logger.error(f"添加知识关系失败: {e}")
            return False

    def get_knowledge_path(
        self,
        start_node: str,
        end_node: str,
        max_difficulty: float = 0.8
    ) -> Optional[List[str]]:
        """
        获取学习路径

        Args:
            start_node: 起始节点ID
            end_node: 目标节点ID
            max_difficulty: 最大难度等级

        Returns:
            学习路径节点ID列表
        """
        try:
            # 过滤难度过高的节点
            valid_nodes = [
                node for node in self.graph.nodes()
                if self.graph.nodes[node].get('difficulty', 0.5) <= max_difficulty
            ]

            # 创建子图
            subgraph = self.graph.subgraph(valid_nodes)

            # 查找最短路径
            if nx.has_path(subgraph, start_node, end_node):
                path = nx.shortest_path(
                    subgraph, start_node, end_node, weight='weight')
                logger.info(f"找到学习路径: {len(path)} 个节点")
                return path
            else:
                logger.warning(f"未找到从 {start_node} 到 {end_node} 的路径")
                return None

        except Exception as e:
            logger.error(f"获取学习路径失败: {e}")
            return None

    def get_related_knowledge(
        self,
        query: str,
        knowledge_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        基于语义搜索获取相关知识

        Args:
            query: 查询文本
            knowledge_type: 知识类型过滤
            top_k: 返回结果数量

        Returns:
            相关知识列表
        """
        try:
            # 生成查询嵌入
            query_embedding = self._generate_embedding(query)

            # 搜索相关集合
            results = []
            collections_to_search = (
                [self.collections[knowledge_type]] if knowledge_type
                else self.collections.values()
            )

            for collection in collections_to_search:
                try:
                    search_results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=top_k
                    )

                    for i, node_id in enumerate(search_results['ids'][0]):
                        metadata = search_results['metadatas'][0][i]
                        results.append({
                            'node_id': node_id,
                            'title': metadata.get('title', ''),
                            'content': search_results['documents'][0][i],
                            'knowledge_type': metadata.get('knowledge_type', ''),
                            'difficulty': metadata.get('difficulty', 0.5),
                            'distance': search_results['distances'][0][i]
                        })
                except Exception as e:
                    logger.warning(f"搜索集合失败: {e}")

            # 按距离排序
            results.sort(key=lambda x: x['distance'])
            return results[:top_k]

        except Exception as e:
            logger.error(f"搜索相关知识失败: {e}")
            return []

    def get_student_knowledge_gaps(
        self,
        mastered_nodes: Set[str],
        target_nodes: Set[str]
    ) -> List[str]:
        """
        获取学生知识缺口

        Args:
            mastered_nodes: 已掌握的节点集合
            target_nodes: 目标节点集合

        Returns:
            需要学习的节点列表
        """
        try:
            gaps = []

            for target_node in target_nodes:
                if target_node not in mastered_nodes:
                    # 查找前置知识
                    prerequisites = set()
                    if target_node in self.graph:
                        for source, _, data in self.graph.in_edges(target_node, data=True):
                            if data.get('edge_type') == 'prerequisite':
                                prerequisites.add(source)

                    # 检查前置知识是否掌握
                    missing_prereqs = prerequisites - mastered_nodes
                    if missing_prereqs:
                        gaps.extend(missing_prereqs)
                    else:
                        gaps.append(target_node)

            logger.info(f"发现 {len(gaps)} 个知识缺口")
            return list(set(gaps))

        except Exception as e:
            logger.error(f"获取知识缺口失败: {e}")
            return []

    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """
        获取知识图谱统计信息

        Returns:
            统计信息字典
        """
        try:
            stats = {
                'total_nodes': self.graph.number_of_nodes(),
                'total_edges': self.graph.number_of_edges(),
                'collections': len(self.collections),
                'knowledge_types': {},
                'difficulty_distribution': {}
            }

            # 统计知识类型
            for node_id, data in self.graph.nodes(data=True):
                knowledge_type = data.get('knowledge_type', 'unknown')
                stats['knowledge_types'][knowledge_type] = stats['knowledge_types'].get(
                    knowledge_type, 0) + 1

                difficulty = data.get('difficulty', 0.5)
                difficulty_level = 'easy' if difficulty < 0.3 else 'medium' if difficulty < 0.7 else 'hard'
                stats['difficulty_distribution'][difficulty_level] = stats['difficulty_distribution'].get(
                    difficulty_level, 0) + 1

            return stats

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}

    def export_knowledge_graph(self, output_file: str) -> bool:
        """
        导出知识图谱

        Args:
            output_file: 输出文件路径

        Returns:
            是否导出成功
        """
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(exist_ok=True)

            # 导出为JSON格式
            graph_data = {
                'nodes': [
                    {
                        'id': node_id,
                        **data
                    }
                    for node_id, data in self.graph.nodes(data=True)
                ],
                'edges': [
                    {
                        'source': source,
                        'target': target,
                        **data
                    }
                    for source, target, data in self.graph.edges(data=True)
                ],
                'metadata': {
                    'exported_at': datetime.now().isoformat(),
                    'total_nodes': self.graph.number_of_nodes(),
                    'total_edges': self.graph.number_of_edges()
                }
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, ensure_ascii=False, indent=2)

            logger.info(f"知识图谱导出成功: {output_file}")
            return True

        except Exception as e:
            logger.error(f"导出知识图谱失败: {e}")
            return False

    def import_knowledge_graph(self, input_file: str) -> bool:
        """
        导入知识图谱

        Args:
            input_file: 输入文件路径

        Returns:
            是否导入成功
        """
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                logger.error(f"文件不存在: {input_file}")
                return False

            with open(input_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)

            # 导入节点
            for node in graph_data.get('nodes', []):
                node_id = node.pop('id')
                self.graph.add_node(node_id, **node)

            # 导入边
            for edge in graph_data.get('edges', []):
                source = edge.pop('source')
                target = edge.pop('target')
                self.graph.add_edge(source, target, **edge)

            self._save_data()
            logger.info(f"知识图谱导入成功: {input_file}")
            return True

        except Exception as e:
            logger.error(f"导入知识图谱失败: {e}")
            return False


class StudentLearningProfile:
    """学生学习画像管理"""

    def __init__(self, student_id: str, knowledge_graph: LocalKnowledgeGraph):
        """
        初始化学生学习画像

        Args:
            student_id: 学生ID
            knowledge_graph: 知识图谱实例
        """
        self.student_id = student_id
        self.knowledge_graph = knowledge_graph
        self.profile_dir = knowledge_graph.data_dir / "student_profiles" / student_id
        self.profile_dir.mkdir(parents=True, exist_ok=True)

        # 学习数据
        self.mastered_nodes: Set[str] = set()
        self.learning_history: List[Dict[str, Any]] = []
        self.learning_preferences: Dict[str, Any] = {}

        # 加载已有数据
        self._load_profile()

        logger.info(f"学生学习画像初始化完成: {student_id}")

    def _load_profile(self):
        """加载学生画像数据"""
        try:
            profile_file = self.profile_dir / "profile.json"
            if profile_file.exists():
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.mastered_nodes = set(data.get('mastered_nodes', []))
                    self.learning_history = data.get('learning_history', [])
                    self.learning_preferences = data.get(
                        'learning_preferences', {})

        except Exception as e:
            logger.warning(f"加载学生画像失败: {e}")

    def _save_profile(self):
        """保存学生画像数据"""
        try:
            profile_file = self.profile_dir / "profile.json"
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'student_id': self.student_id,
                    'mastered_nodes': list(self.mastered_nodes),
                    'learning_history': self.learning_history,
                    'learning_preferences': self.learning_preferences,
                    'updated_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存学生画像失败: {e}")

    def record_learning(
        self,
        node_id: str,
        performance: float,
        time_spent: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        记录学习行为

        Args:
            node_id: 知识节点ID
            performance: 学习表现 (0.0-1.0)
            time_spent: 学习时间（秒）
            metadata: 额外元数据
        """
        try:
            # 记录学习历史
            self.learning_history.append({
                'node_id': node_id,
                'performance': performance,
                'time_spent': time_spent,
                'timestamp': datetime.now().isoformat(),
                **(metadata or {})
            })

            # 如果表现良好，标记为已掌握
            if performance >= 0.8:
                self.mastered_nodes.add(node_id)

            # 更新学习偏好
            self._update_preferences(node_id, performance, time_spent)

            self._save_profile()
            logger.info(f"记录学习行为: {node_id} (表现: {performance:.2f})")

        except Exception as e:
            logger.error(f"记录学习行为失败: {e}")

    def _update_preferences(self, node_id: str, performance: float, time_spent: int):
        """更新学习偏好"""
        try:
            node_data = self.knowledge_graph.graph.nodes.get(node_id, {})
            knowledge_type = node_data.get('knowledge_type', 'unknown')
            difficulty = node_data.get('difficulty', 0.5)

            # 更新类型偏好
            if knowledge_type not in self.learning_preferences:
                self.learning_preferences[knowledge_type] = {
                    'total_attempts': 0,
                    'avg_performance': 0.0,
                    'avg_time': 0.0
                }

            prefs = self.learning_preferences[knowledge_type]
            prefs['total_attempts'] += 1
            prefs['avg_performance'] = (
                (prefs['avg_performance'] * (prefs['total_attempts'] - 1) + performance) /
                prefs['total_attempts']
            )
            prefs['avg_time'] = (
                (prefs['avg_time'] * (prefs['total_attempts'] - 1) + time_spent) /
                prefs['total_attempts']
            )

        except Exception as e:
            logger.warning(f"更新学习偏好失败: {e}")

    def get_personalized_recommendations(
        self,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        获取个性化推荐

        Args:
            top_k: 推荐数量

        Returns:
            推荐列表
        """
        try:
            # 获取知识缺口
            all_nodes = set(self.knowledge_graph.graph.nodes())
            target_nodes = all_nodes - self.mastered_nodes
            gaps = self.knowledge_graph.get_student_knowledge_gaps(
                self.mastered_nodes,
                target_nodes
            )

            # 基于学习偏好排序
            recommendations = []
            for node_id in gaps[:top_k * 2]:  # 获取更多候选
                node_data = self.knowledge_graph.graph.nodes.get(node_id, {})
                knowledge_type = node_data.get('knowledge_type', 'unknown')

                # 计算推荐分数
                score = 0.0
                if knowledge_type in self.learning_preferences:
                    prefs = self.learning_preferences[knowledge_type]
                    score += prefs['avg_performance'] * 0.4  # 表现权重
                    score += (1.0 / (prefs['avg_time'] + 1)) * 0.3  # 时间权重
                    score += prefs['total_attempts'] * 0.1  # 熟悉度权重

                score += (1.0 - node_data.get('difficulty', 0.5)) * 0.2  # 难度权重

                recommendations.append({
                    'node_id': node_id,
                    'title': node_data.get('title', ''),
                    'knowledge_type': knowledge_type,
                    'difficulty': node_data.get('difficulty', 0.5),
                    'score': score
                })

            # 按分数排序
            recommendations.sort(key=lambda x: x['score'], reverse=True)
            return recommendations[:top_k]

        except Exception as e:
            logger.error(f"获取个性化推荐失败: {e}")
            return []

    def get_learning_progress(self) -> Dict[str, Any]:
        """
        获取学习进度

        Returns:
            学习进度信息
        """
        try:
            total_nodes = self.knowledge_graph.graph.number_of_nodes()
            mastered_count = len(self.mastered_nodes)
            progress_rate = mastered_count / total_nodes if total_nodes > 0 else 0.0

            # 计算平均表现
            if self.learning_history:
                avg_performance = sum(
                    h['performance'] for h in self.learning_history
                ) / len(self.learning_history)
                total_time = sum(h['time_spent']
                                 for h in self.learning_history)
            else:
                avg_performance = 0.0
                total_time = 0

            return {
                'student_id': self.student_id,
                'total_nodes': total_nodes,
                'mastered_nodes': mastered_count,
                'progress_rate': progress_rate,
                'avg_performance': avg_performance,
                'total_learning_time': total_time,
                'learning_sessions': len(self.learning_history)
            }

        except Exception as e:
            logger.error(f"获取学习进度失败: {e}")
            return {}
