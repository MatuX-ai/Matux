"""
向量知识库服务 (RAG Pipeline)

基于 PRD F-08-AI.3 个性化知识库设计，提供：
- 分层知识库管理（全局/阶段/个人）
- FAISS 向量检索（替代 ChromaDB，使用已有的 faiss-cpu 依赖）
- RAG 检索增强生成
- 知识库内容动态调整

技术选型：
- faiss-cpu: 向量相似性搜索（已在 requirements.txt 中声明）
- sentence-transformers: 文本嵌入（已在 requirements.txt 中声明）
- 利用现有 AIManager 进行 LLM 生成
"""

import logging
import json
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

class KnowledgeItem:
    """知识条目"""
    def __init__(
        self,
        item_id: str,
        content: str,
        category: str,
        layer: str,  # global / stage / personal
        difficulty: str = "intermediate",  # beginner / intermediate / advanced
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ):
        self.item_id = item_id
        self.content = content
        self.category = category
        self.layer = layer
        self.difficulty = difficulty
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.access_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "content": self.content,
            "category": self.category,
            "layer": self.layer,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
        }


class RAGQueryResult:
    """RAG 检索结果"""
    def __init__(
        self,
        items: List[Dict[str, Any]],
        context: str,
        sources: List[str],
        total_score: float,
    ):
        self.items = items
        self.context = context
        self.sources = sources
        self.total_score = total_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": self.items,
            "context": self.context,
            "sources": self.sources,
            "total_score": self.total_score,
        }


# ==================== 向量知识库服务 ====================

class VectorKnowledgeService:
    """
    向量知识库服务

    实现分层知识库 + FAISS 向量检索 + RAG 管道：
    - Layer 1: 全局知识库（编程概念、STEM 知识、学习方法论）
    - Layer 2: 阶段知识库（按年级/难度分层 L1-L4）
    - Layer 3: 个人知识库（每个学生独有）
    """

    def __init__(self, data_dir: str = None):
        self.data_dir = Path(data_dir or os.path.join(os.getcwd(), "data", "knowledge_base"))
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # FAISS 索引和映射
        self._index = None
        self._id_to_item: Dict[int, KnowledgeItem] = {}
        self._next_id = 0

        # 嵌入模型（延迟加载）
        self._embedding_model = None
        self._dimension = 384  # BGE-small-zh / text2vec-base-chinese 默认维度

        # 初始化
        self._initialize_knowledge_base()

    # ==================== 初始化 ====================

    def _initialize_knowledge_base(self) -> None:
        """初始化知识库：加载已有索引或创建默认知识"""
        index_path = self.data_dir / "faiss_index.bin"
        mapping_path = self.data_dir / "id_mapping.pkl"

        if index_path.exists() and mapping_path.exists():
            self._load_index(index_path, mapping_path)
            logger.info(f"已加载知识库索引，共 {len(self._id_to_item)} 条知识")
        else:
            self._create_default_knowledge()
            logger.info("已创建默认知识库")

    def _load_index(self, index_path: Path, mapping_path: Path) -> None:
        """加载已有的 FAISS 索引"""
        try:
            import faiss
            self._index = faiss.read_index(str(index_path))
            with open(mapping_path, "rb") as f:
                data = pickle.load(f)
                self._id_to_item = data.get("mapping", {})
                self._next_id = data.get("next_id", 0)
        except Exception as e:
            logger.warning(f"加载索引失败: {e}，将创建新索引")
            self._create_default_knowledge()

    def _save_index(self) -> None:
        """保存 FAISS 索引到磁盘"""
        try:
            import faiss
            index_path = self.data_dir / "faiss_index.bin"
            mapping_path = self.data_dir / "id_mapping.pkl"

            if self._index is not None:
                faiss.write_index(self._index, str(index_path))
            with open(mapping_path, "wb") as f:
                pickle.dump({"mapping": self._id_to_item, "next_id": self._next_id}, f)
        except Exception as e:
            logger.error(f"保存索引失败: {e}")

    def _create_default_knowledge(self) -> None:
        """创建默认分层知识库内容"""
        default_items = [
            # Layer 1: 全局知识库
            KnowledgeItem("g_python_basics", "Python 基础语法：变量、数据类型、运算符、输入输出", "programming", "global", "beginner", ["python", "基础"]),
            KnowledgeItem("g_python_conditions", "条件判断：if/elif/else 语句，比较运算符，逻辑运算符", "programming", "global", "beginner", ["python", "条件"]),
            KnowledgeItem("g_python_loops", "循环结构：for 循环、while 循环、range() 函数、break/continue", "programming", "global", "intermediate", ["python", "循环"]),
            KnowledgeItem("g_python_functions", "函数定义：def 关键字、参数、返回值、作用域", "programming", "global", "intermediate", ["python", "函数"]),
            KnowledgeItem("g_python_oop", "面向对象编程：类、对象、继承、封装、多态", "programming", "global", "advanced", ["python", "面向对象"]),
            KnowledgeItem("g_circuit_basics", "电路基础：电压、电流、电阻，欧姆定律 V=IR", "stem", "global", "beginner", ["电路", "物理"]),
            KnowledgeItem("g_circuit_components", "电路元件：电阻、电容、电感、LED、传感器", "stem", "global", "intermediate", ["电路", "元件"]),
            KnowledgeItem("g_learning_methods", "学习方法论：费曼技巧、间隔重复、主动回忆", "methodology", "global", "beginner", ["学习方法"]),
            KnowledgeItem("g_common_errors", "Python 常见错误：IndentationError、TypeError、IndexError 及解决方法", "programming", "global", "beginner", ["python", "错误"]),

            # Layer 2: 阶段知识库 L2 (G4-G6)
            KnowledgeItem("l2_blockly_to_python", "从 Blockly 到 Python 的过渡：积木块与代码的对应关系", "programming", "stage", "beginner", ["blockly", "过渡"], metadata={"stage": "L2"}),
            KnowledgeItem("l2_simple_loops", "简单循环：用 Blockly 理解重复执行的概念，翻译为 Python for 循环", "programming", "stage", "beginner", ["循环", "入门"], metadata={"stage": "L2"}),

            # Layer 2: 阶段知识库 L3 (G7-G9)
            KnowledgeItem("l3_range_detail", "range() 函数详解：range(n)、range(start, stop)、range(start, stop, step) 的区别与用法", "programming", "stage", "intermediate", ["python", "range", "循环"], metadata={"stage": "L3"}),
            KnowledgeItem("l3_list_operations", "列表操作：创建、索引、切片、append/pop/sort 方法", "programming", "stage", "intermediate", ["python", "列表"], metadata={"stage": "L3"}),
            KnowledgeItem("l3_data_structures", "数据结构对比：list vs tuple vs dict vs set 的特点和适用场景", "programming", "stage", "intermediate", ["python", "数据结构"], metadata={"stage": "L3"}),

            # Layer 2: 阶段知识库 L4 (G10-G12)
            KnowledgeItem("l4_algorithms", "算法入门：时间复杂度、排序算法、二分查找", "programming", "stage", "advanced", ["算法"], metadata={"stage": "L4"}),
            KnowledgeItem("l4_ai_basics", "AI 入门：机器学习概念、训练数据、模型推理", "ai", "stage", "advanced", ["AI", "机器学习"], metadata={"stage": "L4"}),
        ]

        for item in default_items:
            self._add_item_to_index(item)

        self._save_index()

    # ==================== 嵌入模型 ====================

    def _get_embedding_model(self):
        """延迟加载嵌入模型"""
        if self._embedding_model is not None:
            return self._embedding_model

        try:
            from sentence_transformers import SentenceTransformer
            # 优先使用中文模型
            model_name = os.environ.get("EMBEDDING_MODEL", "shibing624/text2vec-base-chinese")
            self._embedding_model = SentenceTransformer(model_name)
            self._dimension = self._embedding_model.get_sentence_embedding_dimension()
            logger.info(f"嵌入模型已加载: {model_name}, 维度: {self._dimension}")
        except ImportError:
            logger.warning("sentence-transformers 未安装，使用简单 TF-IDF 向量化作为降级方案")
            self._embedding_model = None
        except Exception as e:
            logger.warning(f"嵌入模型加载失败: {e}，使用降级方案")
            self._embedding_model = None

        return self._embedding_model

    def _embed_text(self, text: str) -> List[float]:
        """将文本向量化"""
        model = self._get_embedding_model()
        if model is not None:
            embedding = model.encode(text, normalize_embeddings=True)
            return embedding.tolist()

        # 降级方案：简单哈希向量（仅供开发测试，不可用于生产）
        import hashlib
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        vector = [0.0] * self._dimension
        for i in range(min(len(hash_bytes), self._dimension)):
            vector[i] = hash_bytes[i % len(hash_bytes)] / 255.0
        # 归一化
        norm = sum(x * x for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]
        return vector

    # ==================== 知识库操作 ====================

    def _add_item_to_index(self, item: KnowledgeItem) -> None:
        """将知识条目添加到 FAISS 索引"""
        try:
            import faiss
            import numpy as np

            embedding = self._embed_text(item.content)
            vector = np.array([embedding], dtype=np.float32)

            if self._index is None:
                self._index = faiss.IndexFlatIP(self._dimension)

            self._index.add(vector)
            self._id_to_item[self._next_id] = item
            self._next_id += 1
        except ImportError:
            # faiss 不可用时仅存储映射
            self._id_to_item[self._next_id] = item
            self._next_id += 1

    def add_knowledge(self, item: KnowledgeItem) -> str:
        """添加知识到知识库"""
        self._add_item_to_index(item)
        self._save_index()
        return item.item_id

    def add_personal_knowledge(
        self,
        user_id: str,
        content: str,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """添加个人知识（Layer 3）"""
        item_id = f"personal_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        item = KnowledgeItem(
            item_id=item_id,
            content=content,
            category="personal",
            layer="personal",
            tags=tags or [],
            metadata=metadata or {"user_id": user_id},
        )
        return self.add_knowledge(item)

    # ==================== RAG 检索 ====================

    def search(
        self,
        query: str,
        user_id: str = None,
        top_k: int = 5,
        layer_filter: str = None,
        stage: str = None,
    ) -> List[Dict[str, Any]]:
        """
        检索相关知识

        Args:
            query: 查询文本
            user_id: 学生ID（用于检索个人知识）
            top_k: 返回结果数量
            layer_filter: 层级过滤 (global/stage/personal)
            stage: 学习阶段 (L1-L4)
        """
        try:
            import faiss
            import numpy as np

            query_embedding = self._embed_text(query)
            query_vector = np.array([query_embedding], dtype=np.float32)

            if self._index is None or self._index.ntotal == 0:
                return self._keyword_search(query, top_k, layer_filter, stage)

            scores, indices = self._index.search(query_vector, min(top_k * 3, self._index.ntotal))

            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0 or idx not in self._id_to_item:
                    continue

                item = self._id_to_item[idx]

                # 层级过滤
                if layer_filter and item.layer != layer_filter:
                    continue

                # 阶段过滤
                if stage and item.metadata.get("stage") != stage:
                    if item.layer == "stage":
                        continue

                # 个人知识过滤
                if item.layer == "personal" and user_id:
                    if item.metadata.get("user_id") != user_id:
                        continue

                # 更新访问计数
                item.access_count += 1

                results.append({
                    **item.to_dict(),
                    "relevance_score": float(score),
                })

                if len(results) >= top_k:
                    break

            return results

        except ImportError:
            return self._keyword_search(query, top_k, layer_filter, stage)
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return self._keyword_search(query, top_k, layer_filter, stage)

    def _keyword_search(
        self,
        query: str,
        top_k: int,
        layer_filter: str = None,
        stage: str = None,
    ) -> List[Dict[str, Any]]:
        """关键词检索降级方案"""
        query_words = set(query.lower().split())
        results = []

        for item in self._id_to_item.values():
            # 层级过滤
            if layer_filter and item.layer != layer_filter:
                continue
            if stage and item.layer == "stage" and item.metadata.get("stage") != stage:
                continue

            # 关键词匹配
            content_words = set(item.content.lower().split())
            tag_words = set(t.lower() for t in item.tags)
            all_words = content_words | tag_words

            overlap = len(query_words & all_words)
            if overlap > 0:
                score = overlap / max(len(query_words), 1)
                results.append({**item.to_dict(), "relevance_score": score})

        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:top_k]

    def rag_retrieve(
        self,
        query: str,
        user_id: str,
        profile_seed: str = "",
        stage: str = None,
        top_k: int = 3,
    ) -> RAGQueryResult:
        """
        RAG 检索增强流程（PRD F-08-AI.3）

        1. 检索 Layer 1 全局知识库
        2. 检索 Layer 2 阶段知识库
        3. 检索 Layer 3 个人知识库
        4. 融合上下文
        """
        all_items = []

        # Layer 1: 全局知识
        global_results = self.search(query, top_k=top_k, layer_filter="global")
        all_items.extend(global_results)

        # Layer 2: 阶段知识
        stage_results = self.search(query, top_k=top_k, layer_filter="stage", stage=stage)
        all_items.extend(stage_results)

        # Layer 3: 个人知识
        if user_id:
            personal_results = self.search(query, user_id=user_id, top_k=top_k, layer_filter="personal")
            all_items.extend(personal_results)

        # 按相关性排序
        all_items.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        top_items = all_items[:top_k * 2]

        # 构建上下文
        context_parts = []
        sources = []
        for item in top_items:
            layer_label = {"global": "全局知识库", "stage": "阶段知识库", "personal": "个人知识库"}.get(item["layer"], "知识库")
            context_parts.append(f"[{layer_label}] {item['content']}")
            sources.append(item["item_id"])

        context = "\n".join(context_parts) if context_parts else "未找到相关知识"

        total_score = sum(item.get("relevance_score", 0) for item in top_items) / max(len(top_items), 1)

        return RAGQueryResult(
            items=top_items,
            context=context,
            sources=sources,
            total_score=total_score,
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计信息"""
        layer_counts = {"global": 0, "stage": 0, "personal": 0}
        category_counts: Dict[str, int] = {}

        for item in self._id_to_item.values():
            layer_counts[item.layer] = layer_counts.get(item.layer, 0) + 1
            category_counts[item.category] = category_counts.get(item.category, 0) + 1

        return {
            "total_items": len(self._id_to_item),
            "layer_counts": layer_counts,
            "category_counts": category_counts,
            "index_size": self._index.ntotal if self._index is not None else 0,
            "embedding_dimension": self._dimension,
            "has_embedding_model": self._embedding_model is not None,
        }


# 单例实例
_vector_knowledge_service: Optional[VectorKnowledgeService] = None


def get_vector_knowledge_service() -> VectorKnowledgeService:
    """获取向量知识库服务单例"""
    global _vector_knowledge_service
    if _vector_knowledge_service is None:
        _vector_knowledge_service = VectorKnowledgeService()
    return _vector_knowledge_service
