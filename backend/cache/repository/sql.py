"""
【P3-D-1】SQLAlchemy 仓储实现

继承 Repository[T] 抽象接口，提供 SQLAlchemy ORM + SQLite 持久化。

特点：
- 内存缓存（dict）加速读写（同 P3-B FileJsonRepository）
- 写入时同时更新内存和数据库（同步 ORM session）
- 启动时从数据库加载所有行到内存缓存
- 优雅降级：DB 不可用时回退到纯内存模式（与 P3-B 行为一致）
- flush() 主要清缓存标识（无 debounce，因为写入已即时落库）

使用：
    repo = SqlAlchemyRepository("profiles")
    repo.set("user_1", {"name": "Alice"})
    val = repo.get("user_1")
    repo.flush()
"""

import logging
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from cache.repository.base import Repository
from models.ai_teacher_persistence import get_row_model_by_name

logger = logging.getLogger(__name__)


class SqlAlchemyRepository(Repository[Any]):
    """
    SQLAlchemy ORM 仓储实现（KV 模型）

    - 7 张 AI 教师持久化表均采用 KV 模型
    - 内存缓存 + 数据库双写（写穿透）
    - 优雅降级：DB 不可用 → 仅内存
    """

    def __init__(
        self,
        name: str,
        session_factory: Optional[sessionmaker] = None,
    ) -> None:
        self._name = name
        self._row_model = get_row_model_by_name(name)
        self._session_factory = session_factory
        self._lock = threading.RLock()
        self._store: Dict[str, Any] = {}
        # 启动时尝试加载
        self._load_from_disk()
        logger.info(
            f"SqlAlchemyRepository 已初始化：{self._row_model.__tablename__} "
            f"({len(self._store)} 条历史数据)"
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def table_name(self) -> str:
        return self._row_model.__tablename__

    def _ensure_session_factory(self) -> Optional[sessionmaker]:
        """延迟获取 session factory（避免循环导入）"""
        if self._session_factory is None:
            try:
                from utils.database import SyncSessionLocal

                self._session_factory = SyncSessionLocal
            except Exception as e:
                logger.warning(
                    f"SqlAlchemyRepository[{self._name}] 无法获取 SessionLocal：{e}"
                )
                return None
        return self._session_factory

    def _load_from_disk(self) -> None:
        """从数据库加载初始数据到内存缓存"""
        session_factory = self._ensure_session_factory()
        if session_factory is None:
            logger.warning(
                f"SqlAlchemyRepository[{self._name}] 数据库不可用，纯内存模式"
            )
            return
        try:
            with session_factory() as session:
                rows = session.query(self._row_model).all()
                loaded = {row.user_id: row.value for row in rows}
                with self._lock:
                    self._store = loaded
                logger.info(
                    f"从数据库加载 {self.table_name}：{len(loaded)} 条"
                )
        except (OperationalError, SQLAlchemyError) as e:
            logger.warning(
                f"SqlAlchemyRepository[{self._name}] 加载失败：{e}（纯内存模式）"
            )

    # ---------- 公共 API（Repository 接口） ----------

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._store.get(key, default)

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._store

    def keys(self) -> List[str]:
        with self._lock:
            return list(self._store.keys())

    def values(self) -> List[Any]:
        with self._lock:
            return list(self._store.values())

    def items(self) -> List[Any]:
        with self._lock:
            return list(self._store.items())

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)

    def snapshot(self) -> Dict[str, Any]:
        """返回深拷贝快照"""
        with self._lock:
            import json

            return json.loads(json.dumps(self._store, default=str))

    # ---------- 写操作（同步双写） ----------

    def set(self, key: str, value: Any) -> None:
        """写入：内存 + 数据库（写穿透）"""
        with self._lock:
            self._store[key] = value
        self._persist(key, value)

    def delete(self, key: str) -> bool:
        """删除：内存 + 数据库"""
        with self._lock:
            existed = key in self._store
            self._store.pop(key, None)
        if existed:
            self._persist_delete(key)
        return existed

    def clear(self) -> None:
        """清空：内存 + 数据库"""
        with self._lock:
            keys_to_delete = list(self._store.keys())
            self._store = {}
        # 删除数据库中所有行
        session_factory = self._ensure_session_factory()
        if session_factory is None:
            return
        try:
            with session_factory() as session:
                session.query(self._row_model).delete()
                session.commit()
                logger.debug(
                    f"SqlAlchemyRepository[{self._name}] 清空 {len(keys_to_delete)} 条"
                )
        except (OperationalError, SQLAlchemyError) as e:
            logger.warning(
                f"SqlAlchemyRepository[{self._name}] 清空失败：{e}"
            )

    def flush(self) -> None:
        """
        强制刷盘（SQL 模式下写入已即时落库，本方法主要用于清缓存标识）

        - 校验内存与数据库一致性
        - 如果发现不一致（如外部修改），重新加载
        """
        # 简单实现：暂不强制 reload（因为 set/delete 都是同步落库的）
        # 预留接口以便未来实现真正 flush（如批量写入场景）
        logger.debug(f"SqlAlchemyRepository[{self._name}] flush() 完成（无操作）")

    def replace_all(self, data: Dict[str, Any]) -> None:
        """整体替换：清空 + 批量写入"""
        with self._lock:
            self._store = dict(data)
        session_factory = self._ensure_session_factory()
        if session_factory is None:
            return
        try:
            with session_factory() as session:
                # 先删除所有现有行
                session.query(self._row_model).delete()
                # 批量插入新数据
                for key, value in data.items():
                    row = self._row_model(user_id=key, value=value)
                    session.add(row)
                session.commit()
                logger.debug(
                    f"SqlAlchemyRepository[{self._name}] replace_all：{len(data)} 条"
                )
        except (OperationalError, SQLAlchemyError) as e:
            logger.warning(
                f"SqlAlchemyRepository[{self._name}] replace_all 失败：{e}"
            )

    # ---------- 内部：数据库持久化 ----------

    def _persist(self, key: str, value: Any) -> None:
        """写入单条记录（upsert）"""
        session_factory = self._ensure_session_factory()
        if session_factory is None:
            return
        try:
            with session_factory() as session:
                # 尝试查询现有行
                existing = (
                    session.query(self._row_model)
                    .filter_by(user_id=key)
                    .first()
                )
                if existing is not None:
                    existing.value = value
                    existing.updated_at = datetime.utcnow()
                else:
                    row = self._row_model(user_id=key, value=value)
                    session.add(row)
                session.commit()
        except (OperationalError, SQLAlchemyError) as e:
            logger.warning(
                f"SqlAlchemyRepository[{self._name}] _persist({key}) 失败：{e}"
            )

    def _persist_delete(self, key: str) -> None:
        """删除单条记录"""
        session_factory = self._ensure_session_factory()
        if session_factory is None:
            return
        try:
            with session_factory() as session:
                row = (
                    session.query(self._row_model)
                    .filter_by(user_id=key)
                    .first()
                )
                if row is not None:
                    session.delete(row)
                    session.commit()
        except (OperationalError, SQLAlchemyError) as e:
            logger.warning(
                f"SqlAlchemyRepository[{self._name}] _persist_delete({key}) 失败：{e}"
            )