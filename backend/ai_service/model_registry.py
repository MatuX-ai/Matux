"""
模型注册中心 - 模型元数据存储与管理

支持模型元数据的持久化存储（数据库/Redis/文件），
模型来源管理（本地文件、远程 URL、对象存储），
模型签名验证等。
"""

import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    模型注册中心

    负责模型元数据的持久化存储和检索，支持：
    - 数据库存储（通过 SQLAlchemy）
    - Redis 缓存
    - JSON 文件存储（备用）
    - 模型签名验证
    - 版本管理
    """

    def __init__(
        self,
        storage_type: str = "json",
        db_session=None,
        redis_client=None,
        json_path: str = "./data/model_registry.json",
    ):
        self.storage_type = storage_type
        self.db_session = db_session
        self.redis_client = redis_client
        self.json_path = Path(json_path)
        self._in_memory: Dict[str, Dict[str, Any]] = {}
        self._initialized = False

    async def initialize(self) -> None:
        """初始化注册中心"""
        if self._initialized:
            return

        if self.storage_type == "json":
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
            await self._load_from_json()
        elif self.storage_type == "redis" and not self.redis_client:
            logger.warning("Redis 客户端未提供，回退到内存存储")
            self.storage_type = "memory"

        self._initialized = True
        logger.info(f"模型注册中心已初始化 (storage={self.storage_type})")

    async def register(
        self,
        name: str,
        version: str,
        model_type: str,
        source_path: str = "",
        source_url: str = "",
        description: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        checksum: str = "",
    ) -> Dict[str, Any]:
        """
        注册模型到注册中心

        Returns:
            模型记录
        """
        record = {
            "model_id": f"{name}_{version}_{uuid.uuid4().hex[:8]}",
            "name": name,
            "version": version,
            "model_type": model_type,
            "source_path": source_path,
            "source_url": source_url,
            "description": description,
            "tags": tags or [],
            "metadata": metadata or {},
            "checksum": checksum,
            "size_bytes": 0,
            "status": "registered",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_loaded_at": None,
            "load_count": 0,
        }

        # 计算文件大小
        if source_path and Path(source_path).exists():
            record["size_bytes"] = Path(source_path).stat().st_size

        await self._save(record)
        logger.info(f"模型已注册: {name} v{version} ({record['model_id']})")
        return record

    async def get(self, model_id: str) -> Optional[Dict[str, Any]]:
        """获取模型记录"""
        if self.storage_type == "redis" and self.redis_client:
            data = self.redis_client.get(f"model:{model_id}")
            if data:
                return json.loads(data)

        return self._in_memory.get(model_id)

    async def list(
        self,
        status: Optional[str] = None,
        model_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        列出模型

        Returns:
            (模型列表, 总数)
        """
        records = list(self._in_memory.values())

        if status:
            records = [r for r in records if r.get("status") == status]
        if model_type:
            records = [r for r in records if r.get("model_type") == model_type]
        if tags:
            records = [
                r for r in records
                if any(tag in r.get("tags", []) for tag in tags)
            ]

        records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        total = len(records)

        start = (page - 1) * page_size
        end = start + page_size
        return records[start:end], total

    async def update_status(self, model_id: str, status: str, error_message: str = "") -> bool:
        """更新模型状态"""
        record = await self.get(model_id)
        if not record:
            return False

        record["status"] = status
        record["updated_at"] = datetime.utcnow().isoformat()
        if status == "loaded":
            record["last_loaded_at"] = datetime.utcnow().isoformat()
            record["load_count"] = record.get("load_count", 0) + 1
        if error_message:
            record["error_message"] = error_message

        await self._save(record)
        return True

    async def update_checksum(self, model_id: str, checksum: str) -> bool:
        """更新模型校验和"""
        record = await self.get(model_id)
        if not record:
            return False

        record["checksum"] = checksum
        record["updated_at"] = datetime.utcnow().isoformat()
        await self._save(record)
        return True

    async def delete(self, model_id: str) -> bool:
        """删除模型记录"""
        if model_id in self._in_memory:
            del self._in_memory[model_id]
            await self._persist()
            return True
        return False

    async def find_by_name(self, name: str, version: Optional[str] = None) -> List[Dict[str, Any]]:
        """按名称查找模型"""
        records = [
            r for r in self._in_memory.values()
            if r.get("name") == name
        ]
        if version:
            records = [r for r in records if r.get("version") == version]
        return sorted(records, key=lambda r: r.get("created_at", ""), reverse=True)

    async def get_latest_version(self, name: str) -> Optional[Dict[str, Any]]:
        """获取最新版本"""
        versions = await self.find_by_name(name)
        return versions[0] if versions else None

    async def validate_signature(self, model_id: str, checksum: str) -> bool:
        """验证模型签名"""
        record = await self.get(model_id)
        if not record or not record.get("checksum"):
            return False
        return record["checksum"] == checksum

    async def _save(self, record: Dict[str, Any]) -> None:
        """保存记录"""
        model_id = record["model_id"]

        if self.storage_type == "redis" and self.redis_client:
            self.redis_client.setex(
                f"model:{model_id}",
                86400,  # 24小时过期
                json.dumps(record, default=str),
            )

        self._in_memory[model_id] = record
        await self._persist()

    async def _persist(self) -> None:
        """持久化到存储后端"""
        if self.storage_type == "json":
            await self._save_to_json()
        elif self.storage_type == "database" and self.db_session:
            await self._save_to_database()

    async def _load_from_json(self) -> None:
        """从 JSON 文件加载"""
        if self.json_path.exists():
            try:
                data = json.loads(self.json_path.read_text(encoding="utf-8"))
                self._in_memory = {r["model_id"]: r for r in data if "model_id" in r}
                logger.info(f"从 JSON 加载了 {len(self._in_memory)} 条模型记录")
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"JSON 加载失败: {e}")

    async def _save_to_json(self) -> None:
        """保存到 JSON 文件"""
        try:
            data = list(self._in_memory.values())
            self.json_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"JSON 保存失败: {e}")

    async def _save_to_database(self) -> None:
        """保存到数据库"""
        # 数据库存储由外部路由层处理
        pass

    def get_stats(self) -> Dict[str, Any]:
        """获取注册中心统计"""
        records = list(self._in_memory.values())
        return {
            "total": len(records),
            "by_status": {
                s: len([r for r in records if r.get("status") == s])
                for s in set(r.get("status", "unknown") for r in records)
            },
            "by_type": {
                t: len([r for r in records if r.get("model_type") == t])
                for t in set(r.get("model_type", "unknown") for r in records)
            },
        }
