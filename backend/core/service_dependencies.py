"""
服务依赖管理器

管理外部服务的可用性检测与降级策略：
- Redis → 内存缓存 (MemoryCacheBackend)
- Neo4j → 禁用知识图谱
- OpenAI → 本地模板 (LocalTemplateResponder)
- RabbitMQ → 同步处理
- SMTP → 记录日志
- 硬件认证 → 离线模拟
- Docker → 受限执行模式
- Vircadia → 2D 模拟返回
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ==================== 降级后端实现 ====================


class MemoryCacheBackend:
    """
    内存缓存后端（Redis 降级方案）

    提供与 Redis 相同的 get/set/delete 接口，
    但数据存储在内存中，支持 TTL 过期。
    """

    def __init__(self, max_size: int = 1000):
        self._store: Dict[str, tuple] = {}  # key -> (value, expire_at)
        self._max_size = max_size

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expire_at = entry
        if expire_at and time.time() > expire_at:
            del self._store[key]
            return None
        return value

    def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> None:
        """设置缓存值"""
        # 超过容量时清除最旧的条目
        if len(self._store) >= self._max_size:
            oldest_key = next(iter(self._store))
            del self._store[oldest_key]

        expire_at = time.time() + ttl if ttl else None
        self._store[key] = (value, expire_at)

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if key in self._store:
            del self._store[key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return self.get(key) is not None

    def clear(self) -> None:
        """清除所有缓存"""
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)

    def ping(self) -> bool:
        return True


class LocalTemplateResponder:
    """
    本地模板响应器（OpenAI 降级方案）

    当 OpenAI API 不可用时，返回预设的模板响应。
    """

    # 预设模板库
    TEMPLATES = {
        "code_generation": {
            "message": "AI 代码生成暂时不可用，已返回模板代码",
            "templates": {
                "python": "# TODO: AI 服务不可用，请手动编写代码\ndef solution():\n    pass",
                "javascript": "// TODO: AI 服务不可用，请手动编写代码\nfunction solution() {\n  // ...\n}",
                "java": "// TODO: AI 服务不可用，请手动编写代码\npublic class Solution {\n  // ...\n}",
            },
        },
        "recommendation": {
            "message": "AI 推荐系统暂时不可用，已返回默认推荐",
            "default_items": [],
        },
        "chat": {
            "message": "AI 对话暂时不可用，请使用模板回复",
            "response": "抱歉，AI 服务暂时不可用。请稍后再试或使用其他功能。",
        },
    }

    def get_template(
        self, category: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """获取模板响应"""
        template = self.TEMPLATES.get(
            category, self.TEMPLATES["chat"]
        )
        return {
            "degraded": True,
            "category": category,
            "fallback": "local_template",
            **template,
        }


class ReadOnlyMode:
    """
    只读模式（Docker / 执行类服务降级方案）

    禁止写操作，仅允许读取预置数据。
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._presets: Dict[str, Any] = {}

    def set_preset(self, key: str, data: Any) -> None:
        """设置预置数据"""
        self._presets[key] = data

    def get(self, key: str) -> Optional[Any]:
        """读取预置数据"""
        return self._presets.get(key)

    def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """禁止执行操作"""
        return {
            "degraded": True,
            "message": f"{self.service_name} 处于只读模式，禁止执行操作",
            "mode": "read_only",
        }


class DisabledService:
    """
    禁用服务（完全不可用时的占位符）
    """

    def __init__(self, service_name: str, reason: str = ""):
        self.service_name = service_name
        self.reason = reason or "服务不可用"

    def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return {
            "degraded": True,
            "available": False,
            "service": self.service_name,
            "message": f"{self.service_name} 不可用: {self.reason}",
        }


class ServiceStatus:
    """服务状态"""

    def __init__(
        self,
        name: str,
        available: bool = True,
        fallback: str = "",
        fallback_instance: Any = None,
    ):
        self.name = name
        self.available = available
        self.fallback = fallback
        self.fallback_instance = fallback_instance
        self.last_check: Optional[float] = None
        self.check_count: int = 0
        self.failure_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "available": self.available,
            "fallback": self.fallback,
            "last_check": self.last_check,
            "check_count": self.check_count,
            "failure_count": self.failure_count,
            "has_fallback": self.fallback_instance is not None,
        }


class ServiceDependencyManager:
    """
    服务依赖管理器

    提供：
    1. 服务可用性检测
    2. 服务降级方案注册
    3. 降级状态查询
    """

    # 有效的服务名白名单（防止拼写错误被静默忽略）
    VALID_SERVICES = frozenset({
        "redis", "neo4j", "openai", "rabbitmq", "smtp",
        "hardware_auth", "docker", "vircadia", "openhydra", "hyperledger"
    })

    def __init__(self):
        self._services: Dict[str, ServiceStatus] = {}
        self._check_cache: Dict[str, bool] = {}
        self._cache_ttl = 30  # 检测结果缓存 30 秒
        self._cache_timestamps: Dict[str, float] = {}
        self._recheck_task: Optional[asyncio.Task] = None
        # 降级实例注册表
        self._fallback_instances: Dict[str, Any] = {}

    def register_service(
        self, name: str, fallback: str = ""
    ) -> None:
        """注册一个可降级的服务"""
        # 创建降级实例
        fallback_instance = self._create_fallback_instance(name, fallback)
        self._fallback_instances[name] = fallback_instance

        self._services[name] = ServiceStatus(
            name=name,
            available=True,
            fallback=fallback,
            fallback_instance=fallback_instance,
        )
        logger.debug(
            f"📋 注册服务: {name} "
            f"(降级: {fallback or '无'})"
        )

    def _create_fallback_instance(
        self, service_name: str, fallback_type: str
    ) -> Any:
        """根据降级类型创建降级实例"""
        factories = {
            "in_memory": lambda: MemoryCacheBackend(),
            "local_template": lambda: LocalTemplateResponder(),
            "read_only": lambda: ReadOnlyMode(service_name),
            "disabled": lambda: DisabledService(service_name),
            "sync_mode": lambda: DisabledService(
                service_name, "已降级为同步模式"
            ),
            "log_only": lambda: DisabledService(
                service_name, "已降级为日志模式"
            ),
            "offline_sim": lambda: DisabledService(
                service_name, "已降级为离线模拟"
            ),
            "2d_simulation": lambda: DisabledService(
                service_name, "已降级为 2D 模拟"
            ),
            "cache_mode": lambda: MemoryCacheBackend(),
        }
        factory = factories.get(fallback_type)
        if factory:
            return factory()
        return None

    def register_many(self, services: Dict[str, str]) -> None:
        """批量注册服务（带白名单验证）"""
        for name, fallback in services.items():
            if name not in self.VALID_SERVICES:
                raise ValueError(
                    f"Unknown service '{name}'. Valid services: {sorted(self.VALID_SERVICES)}"
                )
            self.register_service(name, fallback)

    async def check_service(self, service_name: str) -> bool:
        """
        检查服务是否可用

        使用缓存避免频繁检测。

        Returns:
            True 表示可用，False 表示不可用
        """
        # 检查缓存（带时间戳）
        cached = self._check_cache.get(service_name)
        cached_at = self._cache_timestamps.get(service_name, 0)
        if cached is not None and (time.time() - cached_at) < self._cache_ttl:
            return cached

        # 执行检测
        available = await self._do_check(service_name)

        # 更新服务状态
        if service_name in self._services:
            svc = self._services[service_name]
            svc.available = available
            svc.last_check = time.time()
            svc.check_count += 1
            if not available:
                svc.failure_count += 1

        # 缓存结果
        self._check_cache[service_name] = available
        self._cache_timestamps[service_name] = time.time()
        return available

    async def _do_check(self, service_name: str) -> bool:
        """实际执行服务可用性检测"""
        checks = {
            "redis": self._check_redis,
            "neo4j": self._check_neo4j,
            "openai": self._check_openai,
            "rabbitmq": self._check_rabbitmq,
            "smtp": self._check_smtp,
            "hardware_auth": self._check_hardware_auth,
            "docker": self._check_docker,
            "vircadia": self._check_vircadia,
            "openhydra": self._check_openhydra,
        }

        check_fn = checks.get(service_name)
        if check_fn is None:
            # 未知服务，假设可用
            return True

        try:
            result = await asyncio.wait_for(check_fn(), timeout=5.0)
            return result
        except asyncio.TimeoutError:
            logger.warning(f"⏱️  服务检测超时: {service_name}")
            return False
        except Exception as e:
            logger.warning(f"❌ 服务检测失败: {service_name} - {e}")
            return False

    # ==================== 服务检测方法 ====================

    async def _check_redis(self) -> bool:
        """检测 Redis 可用性"""
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379, db=0)
            r.ping()
            return True
        except Exception:
            return False

    async def _check_neo4j(self) -> bool:
        """检测 Neo4j 可用性"""
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                "bolt://localhost:7687", auth=("neo4j", "password")
            )
            with driver.session() as session:
                session.run("RETURN 1")
            driver.close()
            return True
        except Exception:
            return False

    async def _check_openai(self) -> bool:
        """检测 OpenAI API 可用性"""
        try:
            from config import settings

            if not settings.OPENAI_API_KEY:
                return False
            # 简单检测 API key 是否配置
            return True
        except Exception:
            return False

    async def _check_rabbitmq(self) -> bool:
        """检测 RabbitMQ 可用性"""
        try:
            import pika

            connection = pika.BlockingConnection(
                pika.ConnectionParameters("localhost")
            )
            connection.close()
            return True
        except Exception:
            return False

    async def _check_smtp(self) -> bool:
        """检测 SMTP 可用性"""
        # SMTP 非必须，始终标记可用
        return True

    async def _check_hardware_auth(self) -> bool:
        """检测硬件认证服务可用性"""
        # 硬件认证非必须，始终标记可用
        return True

    async def _check_docker(self) -> bool:
        """检测 Docker 可用性"""
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True, timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    async def _check_vircadia(self) -> bool:
        """检测 Vircadia 服务可用性"""
        try:
            from config import settings
            url = getattr(settings, "VIRCADIA_SERVER_URL", "")
            if not url:
                return False
            return True
        except Exception:
            return False

    async def _check_openhydra(self) -> bool:
        """检测 OpenHydra 服务可用性"""
        try:
            from config import settings
            url = getattr(settings, "OPENHYDRA_URL", "")
            if not url:
                return False
            return True
        except Exception:
            return False

    def get_fallback(self, service_name: str) -> Any:
        """获取服务的降级实例"""
        return self._fallback_instances.get(service_name)

    def get_all_status(self) -> Dict[str, Any]:
        """获取所有服务状态"""
        return {
            name: status.to_dict()
            for name, status in self._services.items()
        }

    def invalidate_cache(self) -> None:
        """清除检测结果缓存"""
        self._check_cache.clear()
        self._cache_timestamps.clear()
        logger.info("🔄 服务检测缓存已清除")

    async def start_periodic_check(
        self, interval: float = 30.0
    ) -> None:
        """启动定期服务检测后台任务"""
        if self._recheck_task and not self._recheck_task.done():
            logger.info("♻️  定期检测已在运行")
            return

        async def _periodic_check():
            while True:
                await asyncio.sleep(interval)
                self.invalidate_cache()
                for name in list(self._services.keys()):
                    try:
                        await self.check_service(name)
                    except Exception as e:
                        logger.warning(
                            f"定期检测异常: {name} - {e}"
                        )
                logger.debug("♻️  服务定期检测完成")

        self._recheck_task = asyncio.create_task(_periodic_check())
        logger.info(
            f"♻️  启动服务定期检测 (间隔: {interval}s)"
        )

    def stop_periodic_check(self) -> None:
        """停止定期检测"""
        if self._recheck_task and not self._recheck_task.done():
            self._recheck_task.cancel()
            logger.info("⏹  服务定期检测已停止")


# ==================== 全局实例 ====================

_manager_instance: Optional[ServiceDependencyManager] = None


def get_service_manager() -> ServiceDependencyManager:
    """获取全局 ServiceDependencyManager 实例"""
    if _manager_instance is None:
        raise RuntimeError(
            "ServiceDependencyManager 尚未初始化，"
            "请先调用 init_service_manager()"
        )
    return _manager_instance


def init_service_manager() -> ServiceDependencyManager:
    """初始化全局 ServiceDependencyManager 实例"""
    global _manager_instance
    _manager_instance = ServiceDependencyManager()
    logger.info("🔧 ServiceDependencyManager 已初始化")
    return _manager_instance
