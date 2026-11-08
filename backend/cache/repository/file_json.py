"""
【P3-D-1】文件仓储实现

继承 Repository[T] 抽象接口，提供 JSON 文件持久化的具体实现。

特点：
- 内存 dict 提供快速读写
- debounced 异步 flush 到磁盘（默认 2s）
- 启动时从磁盘加载（如果存在）
- 写时按 key 加锁（线程安全）
- 优雅降级：磁盘不可用时回退到纯内存

使用：
    repo = FileJsonRepository("ai_teacher_profiles.json")
    repo.set("user_1", {"name": "Alice"})
    val = repo.get("user_1")
    repo.flush()  # 强制落盘
"""

import json
import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from cache.repository.base import Repository

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
"""持久化文件默认存放目录（backend/data）"""


def _resolve_data_dir() -> Path:
    """
    解析持久化目录
    优先级：环境变量 AI_TEACHER_DATA_DIR > 默认 backend/data
    """
    env = os.getenv("AI_TEACHER_DATA_DIR")
    if env:
        return Path(env)
    return _DEFAULT_DATA_DIR


class FileJsonRepository(Repository[Any]):
    """
    通用文件持久化仓储

    - 内存 dict 提供快速读写
    - debounced 异步 flush 到磁盘（默认 2s）
    - 启动时从磁盘加载（如果存在）
    - 写时按 key 加锁（线程安全）
    """

    def __init__(
        self,
        filename: str,
        default_factory: Any = dict,
        flush_debounce_seconds: float = 2.0,
        data_dir: Optional[Path] = None,
    ) -> None:
        self._data_dir = data_dir or _resolve_data_dir()
        self._file_path = self._data_dir / filename
        self._default_factory = default_factory
        self._flush_debounce_seconds = flush_debounce_seconds
        self._lock = threading.RLock()
        self._flush_timer: Optional[threading.Timer] = None
        self._store: Dict[str, Any] = default_factory()
        # 启动时尝试加载
        self._load_from_disk()
        logger.debug(
            f"FileJsonRepository 已初始化：{filename} "
            f"({len(self._store)} 条历史数据)"
        )

    # ---------- 公共 API（Repository 接口） ----------

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """写入并触发 debounced flush"""
        with self._lock:
            self._store[key] = value
        self._schedule_flush()

    def delete(self, key: str) -> bool:
        """删除并触发 flush"""
        with self._lock:
            existed = key in self._store
            self._store.pop(key, None)
        if existed:
            self._schedule_flush()
        return existed

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

    def clear(self) -> None:
        """清空所有数据（主要用于测试）"""
        with self._lock:
            self._store = self._default_factory()
        self._schedule_flush()

    def snapshot(self) -> Dict[str, Any]:
        """返回当前内存状态的深拷贝快照"""
        with self._lock:
            return json.loads(json.dumps(self._store, default=str))

    def flush(self) -> None:
        """强制立即落盘"""
        self._do_flush()

    def replace_all(self, data: Dict[str, Any]) -> None:
        """整体替换（用于测试或迁移）"""
        with self._lock:
            self._store = data
        self._schedule_flush()

    # ---------- 内部：磁盘 I/O ----------

    def _load_from_disk(self) -> None:
        """从磁盘加载初始数据"""
        try:
            if self._file_path.exists():
                raw = self._file_path.read_text(encoding="utf-8")
                if raw.strip():
                    data = json.loads(raw)
                    if isinstance(data, dict):
                        with self._lock:
                            self._store = data
                        logger.info(
                            f"从磁盘加载 {self._file_path.name}：{len(data)} 条"
                        )
                    else:
                        logger.warning(
                            f"{self._file_path.name} 顶层不是 dict，已忽略"
                        )
        except Exception as e:
            logger.warning(f"加载 {self._file_path.name} 失败：{e}")

    def _schedule_flush(self) -> None:
        """
        调度一次 debounced flush

        距离上次调度 < flush_debounce_seconds 时，复用同一个 Timer
        """
        with self._lock:
            if self._flush_timer is not None and self._flush_timer.is_alive():
                # 已存在活跃 timer，本次写入会被它捕获
                return
            self._flush_timer = threading.Timer(
                self._flush_debounce_seconds, self._do_flush
            )
            self._flush_timer.daemon = True
            self._flush_timer.start()

    def _do_flush(self) -> None:
        """执行 flush（线程安全，原子写入）"""
        with self._lock:
            snapshot = json.loads(json.dumps(self._store, default=str))
            timer = self._flush_timer
            self._flush_timer = None
        # 在锁外执行 I/O，避免长时间阻塞读
        try:
            self._data_dir.mkdir(parents=True, exist_ok=True)
            # 原子写入（写临时文件 + rename 替换）
            fd, tmp_path = tempfile.mkstemp(
                dir=str(self._data_dir),
                prefix=f".{self._file_path.name}.",
                suffix=".tmp",
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(snapshot, f, ensure_ascii=False, indent=2)
                os.replace(tmp_path, self._file_path)
            except Exception:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise
        except Exception as e:
            logger.warning(f"持久化 {self._file_path.name} 失败：{e}")
        finally:
            if timer is not None:
                timer.cancel()