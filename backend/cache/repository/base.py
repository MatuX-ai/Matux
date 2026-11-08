"""
【P3-D-1】仓储抽象接口

设计目标：
- 抽象 AI 教师持久化层的实现细节（File / SQLite / Redis）
- 提供与 P3-B FileJsonRepository 一致的公共 API
- 调用方（routes / services）依赖接口而非实现

使用场景：
    repo: Repository = create_repository("profiles")
    repo.set("user_1", {"name": "Alice"})
    val = repo.get("user_1")

实现：
- FileJsonRepository（cache.repository.file_json）
- SqlAlchemyRepository（cache.repository.sql）

演进路径：
- P3-D-2：可引入 RedisRepository（缓存优先 + DB 兜底）
- P3-E：可引入分布式 Repository
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """
    仓储抽象基类

    所有持久化实现必须实现以下公共 API。调用方只依赖此接口，
    不直接依赖具体实现，便于切换 backend 与单元测试。
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取 key 对应的 value，缺失时返回 default"""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """写入 key-value，对应可能触发异步刷盘"""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除 key，返回是否原本存在"""

    @abstractmethod
    def has(self, key: str) -> bool:
        """判断 key 是否存在"""

    @abstractmethod
    def keys(self) -> List[str]:
        """返回所有 key 的列表（快照）"""

    @abstractmethod
    def values(self) -> List[Any]:
        """返回所有 value 的列表（快照）"""

    @abstractmethod
    def items(self) -> List[Any]:
        """返回所有 (key, value) 元组的列表（快照）"""

    @abstractmethod
    def __len__(self) -> int:
        """返回条目数量"""

    @abstractmethod
    def clear(self) -> None:
        """清空所有数据（主要用于测试）"""

    @abstractmethod
    def snapshot(self) -> Dict[str, Any]:
        """返回当前状态的深拷贝快照"""

    @abstractmethod
    def flush(self) -> None:
        """
        强制刷盘（用于优雅关闭 / 测试）

        - FileJsonRepository：立即写入磁盘
        - SqlAlchemyRepository：清空缓存标记（无 debounce，写入已即时落库）
        """

    @abstractmethod
    def replace_all(self, data: Dict[str, Any]) -> None:
        """整体替换数据（用于测试或迁移）"""

    # ---------- 辅助方法（基于以上 API 的默认实现）----------

    def is_empty(self) -> bool:
        """仓储是否为空"""
        return len(self) == 0

    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """批量获取多个 key"""
        return {k: self.get(k) for k in keys if self.has(k)}

    def to_dict(self) -> Dict[str, Any]:
        """导出为 dict（等价于 snapshot()）"""
        return self.snapshot()

    def __contains__(self, key: str) -> bool:
        """支持 in 操作符"""
        return self.has(key)

    def __getitem__(self, key: str) -> Any:
        """支持索引访问，缺失时抛 KeyError"""
        value = self.get(key, default=None)
        if value is None and not self.has(key):
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any) -> None:
        """支持索引赋值"""
        self.set(key, value)

    def __delitem__(self, key: str) -> None:
        """支持 del 操作"""
        if not self.delete(key):
            raise KeyError(key)

    def __iter__(self):
        """支持迭代 keys()"""
        return iter(self.keys())