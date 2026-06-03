"""
AI 模型管理器 - 动态模型加载/卸载/版本管理

支持多种模型类型：TensorFlow, ONNX, PyTorch
提供模型热加载、A/B 测试、资源监控等功能
"""

import asyncio
import hashlib
import importlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """模型状态"""
    REGISTERED = "registered"       # 已注册，未加载
    LOADING = "loading"              # 加载中
    LOADED = "loaded"                # 已加载
    ACTIVE = "active"                # 活跃使用中
    UNLOADING = "unloading"          # 卸载中
    UNLOADED = "unloaded"            # 已卸载
    ERROR = "error"                  # 错误状态
    DEPRECATED = "deprecated"        # 已废弃


class ModelType(Enum):
    """模型类型"""
    TENSORFLOW = "tensorflow"
    ONNX = "onnx"
    PYTORCH = "pytorch"
    CUSTOM = "custom"


@dataclass
class ModelMetadata:
    """模型元数据"""
    model_id: str
    name: str
    version: str
    model_type: ModelType
    status: ModelStatus = ModelStatus.REGISTERED
    source_path: str = ""
    source_url: str = ""
    checksum: str = ""
    file_size: int = 0
    description: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    loaded_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    use_count: int = 0
    avg_inference_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    gpu_memory_usage_mb: float = 0.0
    config: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""


@dataclass
class InferenceRequest:
    """推理请求"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_id: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class InferenceResult:
    """推理结果"""
    request_id: str
    model_id: str
    output_data: Dict[str, Any]
    inference_time_ms: float
    success: bool
    error_message: str = ""


class BaseModelWrapper:
    """模型包装器基类"""

    def __init__(self, metadata: ModelMetadata):
        self.metadata = metadata
        self._model: Any = None
        self._loaded = False

    async def load(self) -> bool:
        """加载模型"""
        raise NotImplementedError

    async def unload(self) -> bool:
        """卸载模型"""
        self._model = None
        self._loaded = False
        return True

    async def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行推理"""
        raise NotImplementedError

    def is_loaded(self) -> bool:
        return self._loaded

    def get_model(self) -> Any:
        return self._model


class ModelManager:
    """
    模型管理器

    负责模型的注册、加载、卸载、版本管理等功能。
    支持后台线程异步加载，不阻塞 API。
    """

    def __init__(self, cache_dir: Optional[str] = None):
        self._models: Dict[str, ModelMetadata] = {}
        self._wrappers: Dict[str, BaseModelWrapper] = {}
        self._lock = asyncio.Lock()
        self._cache_dir = Path(cache_dir) if cache_dir else Path("/tmp/model_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._background_tasks: set = set()
        self._inference_history: list[InferenceResult] = []
        self._max_history = 1000

        # 默认配置
        self.config = {
            "max_loaded_models": 5,       # 最大同时加载模型数
            "unload_idle_seconds": 3600,   # 闲置卸载时间(1小时)
            "auto_load_retry": 3,          # 自动重试加载次数
            "health_check_interval": 60,   # 健康检查间隔(秒)
        }

    async def register_model(
        self,
        name: str,
        version: str,
        model_type: ModelType,
        source_path: str = "",
        source_url: str = "",
        description: str = "",
        tags: Optional[list[str]] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> ModelMetadata:
        """
        注册新模型

        Args:
            name: 模型名称
            version: 版本号
            model_type: 模型类型
            source_path: 本地文件路径
            source_url: 远程 URL
            description: 描述
            tags: 标签
            config: 配置

        Returns:
            模型元数据
        """
        model_id = f"{name}_{version}_{uuid.uuid4().hex[:8]}"

        metadata = ModelMetadata(
            model_id=model_id,
            name=name,
            version=version,
            model_type=model_type,
            source_path=source_path,
            source_url=source_url,
            description=description,
            tags=tags or [],
            config=config or {},
        )

        # 计算文件校验和
        if source_path and Path(source_path).exists():
            metadata.checksum = await self._calculate_checksum(source_path)
            metadata.file_size = Path(source_path).stat().st_size

        async with self._lock:
            self._models[model_id] = metadata

        logger.info(f"模型注册成功: {name} v{version} ({model_id})")
        return metadata

    async def load_model(self, model_id: str) -> bool:
        """
        加载模型（异步，后台执行）

        Args:
            model_id: 模型 ID

        Returns:
            是否成功启动加载
        """
        async with self._lock:
            if model_id not in self._models:
                raise ValueError(f"模型不存在: {model_id}")

            metadata = self._models[model_id]
            if metadata.status in (ModelStatus.LOADED, ModelStatus.ACTIVE):
                logger.info(f"模型已加载: {model_id}")
                return True

            if metadata.status == ModelStatus.LOADING:
                logger.warning(f"模型正在加载中: {model_id}")
                return False

            # 检查已加载模型数量
            loaded_count = sum(
                1 for m in self._models.values()
                if m.status in (ModelStatus.LOADED, ModelStatus.ACTIVE)
            )
            if loaded_count >= self.config["max_loaded_models"]:
                # 自动卸载最久未使用的模型
                await self._unload_idlest_model()

            metadata.status = ModelStatus.LOADING

        # 后台异步加载
        task = asyncio.create_task(self._load_model_task(model_id))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        return True

    async def unload_model(self, model_id: str) -> bool:
        """
        卸载模型

        Args:
            model_id: 模型 ID

        Returns:
            是否成功
        """
        async with self._lock:
            if model_id not in self._models:
                return False

            metadata = self._models[model_id]
            metadata.status = ModelStatus.UNLOADING

            wrapper = self._wrappers.pop(model_id, None)
            if wrapper:
                try:
                    await wrapper.unload()
                except Exception as e:
                    logger.error(f"卸载模型失败: {model_id}, error: {e}")

            metadata.status = ModelStatus.UNLOADED
            metadata.loaded_at = None

        logger.info(f"模型已卸载: {model_id}")
        return True

    async def predict(
        self,
        model_id: str,
        input_data: Dict[str, Any],
        parameters: Optional[Dict[str, Any]] = None,
    ) -> InferenceResult:
        """
        使用模型进行推理

        Args:
            model_id: 模型 ID
            input_data: 输入数据
            parameters: 推理参数

        Returns:
            推理结果
        """
        request = InferenceRequest(
            model_id=model_id,
            input_data=input_data,
            parameters=parameters or {},
        )

        wrapper = self._wrappers.get(model_id)
        if not wrapper or not wrapper.is_loaded():
            return InferenceResult(
                request_id=request.request_id,
                model_id=model_id,
                output_data={},
                inference_time_ms=0,
                success=False,
                error_message="模型未加载",
            )

        start_time = time.time()
        try:
            output = await wrapper.predict(input_data)
            elapsed = (time.time() - start_time) * 1000

            result = InferenceResult(
                request_id=request.request_id,
                model_id=model_id,
                output_data=output,
                inference_time_ms=elapsed,
                success=True,
            )

            # 更新统计
            metadata = self._models.get(model_id)
            if metadata:
                metadata.last_used_at = datetime.utcnow()
                metadata.use_count += 1
                metadata.avg_inference_time_ms = (
                    (metadata.avg_inference_time_ms * (metadata.use_count - 1) + elapsed)
                    / metadata.use_count
                )
                metadata.status = ModelStatus.ACTIVE

            self._record_inference(result)
            return result

        except Exception as e:
            logger.error(f"推理失败: {model_id}, error: {e}")
            return InferenceResult(
                request_id=request.request_id,
                model_id=model_id,
                output_data={},
                inference_time_ms=(time.time() - start_time) * 1000,
                success=False,
                error_message=str(e),
            )

    def list_models(self, status: Optional[ModelStatus] = None) -> list[ModelMetadata]:
        """
        列出所有模型

        Args:
            status: 按状态筛选

        Returns:
            模型元数据列表
        """
        models = list(self._models.values())
        if status:
            models = [m for m in models if m.status == status]
        return sorted(models, key=lambda m: m.created_at, reverse=True)

    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """获取模型详情"""
        return self._models.get(model_id)

    async def unload_idle_models(self, max_idle_seconds: Optional[int] = None) -> int:
        """
        卸载闲置模型

        Args:
            max_idle_seconds: 最大闲置时间

        Returns:
            卸载的模型数量
        """
        idle_seconds = max_idle_seconds or self.config["unload_idle_seconds"]
        now = time.time()
        unloaded = 0

        for model_id, metadata in list(self._models.items()):
            if metadata.status in (ModelStatus.LOADED, ModelStatus.ACTIVE):
                if metadata.last_used_at:
                    idle = (datetime.utcnow() - metadata.last_used_at).total_seconds()
                    if idle > idle_seconds:
                        await self.unload_model(model_id)
                        unloaded += 1

        return unloaded

    async def validate_checksum(self, model_id: str) -> bool:
        """验证模型文件完整性"""
        metadata = self._models.get(model_id)
        if not metadata or not metadata.source_path:
            return False

        current_checksum = await self._calculate_checksum(metadata.source_path)
        return current_checksum == metadata.checksum

    async def ab_test(
        self,
        model_a_id: str,
        model_b_id: str,
        input_data: Dict[str, Any],
        ratio: float = 0.5,
    ) -> InferenceResult:
        """
        A/B 测试 - 按比例将请求分发到不同模型

        Args:
            model_a_id: 模型 A
            model_b_id: 模型 B
            input_data: 输入数据
            ratio: 模型 A 的流量比例

        Returns:
            推理结果
        """
        if hash(str(input_data)) % 100 < ratio * 100:
            return await self.predict(model_a_id, input_data)
        return await self.predict(model_b_id, input_data)

    async def _load_model_task(self, model_id: str) -> None:
        """后台加载模型任务"""
        try:
            metadata = self._models.get(model_id)
            if not metadata:
                return

            # 获取模型文件
            source = metadata.source_path or metadata.source_url
            if not source:
                raise ValueError("模型源路径/URL 为空")

            # 验证文件完整性
            if metadata.source_path and not await self.validate_checksum(model_id):
                logger.warning(f"模型文件校验和不匹配: {model_id}")

            # 创建模型包装器
            wrapper = self._create_wrapper(metadata)
            success = await wrapper.load()

            async with self._lock:
                if success:
                    self._wrappers[model_id] = wrapper
                    metadata.status = ModelStatus.LOADED
                    metadata.loaded_at = datetime.utcnow()
                    logger.info(f"模型加载成功: {model_id}")
                else:
                    metadata.status = ModelStatus.ERROR
                    metadata.error_message = "模型加载失败"

        except Exception as e:
            logger.error(f"模型加载任务失败: {model_id}, error: {e}")
            async with self._lock:
                if model_id in self._models:
                    self._models[model_id].status = ModelStatus.ERROR
                    self._models[model_id].error_message = str(e)

    def _create_wrapper(self, metadata: ModelMetadata) -> BaseModelWrapper:
        """根据模型类型创建对应的包装器"""
        if metadata.model_type == ModelType.TENSORFLOW:
            return TensorFlowModelWrapper(metadata)
        elif metadata.model_type == ModelType.ONNX:
            return ONNXModelWrapper(metadata)
        elif metadata.model_type == ModelType.PYTORCH:
            return PyTorchModelWrapper(metadata)
        else:
            return CustomModelWrapper(metadata)

    async def _unload_idlest_model(self) -> None:
        """卸载最久未使用的模型"""
        idlest = None
        idlest_time = float("inf")

        for metadata in self._models.values():
            if metadata.status in (ModelStatus.LOADED, ModelStatus.ACTIVE):
                last_used = metadata.last_used_at or metadata.loaded_at or datetime.min
                idle_time = (datetime.utcnow() - last_used).total_seconds()
                if idle_time < idlest_time:
                    idlest_time = idle_time
                    idlest = metadata.model_id

        if idlest:
            await self.unload_model(idlest)

    async def _calculate_checksum(self, file_path: str) -> str:
        """计算文件 SHA256 校验和"""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""

    def _record_inference(self, result: InferenceResult) -> None:
        """记录推理历史"""
        self._inference_history.append(result)
        if len(self._inference_history) > self._max_history:
            self._inference_history = self._inference_history[-self._max_history:]

    def get_inference_stats(self) -> Dict[str, Any]:
        """获取推理统计"""
        total = len(self._inference_history)
        if total == 0:
            return {"total": 0}

        success = sum(1 for r in self._inference_history if r.success)
        avg_time = sum(r.inference_time_ms for r in self._inference_history) / total

        return {
            "total": total,
            "success": success,
            "failed": total - success,
            "success_rate": round(success / total * 100, 2),
            "avg_inference_time_ms": round(avg_time, 2),
        }

    def get_resource_usage(self) -> Dict[str, Any]:
        """获取资源使用情况"""
        loaded_models = [
            m for m in self._models.values()
            if m.status in (ModelStatus.LOADED, ModelStatus.ACTIVE)
        ]
        return {
            "loaded_count": len(loaded_models),
            "max_loaded": self.config["max_loaded_models"],
            "total_memory_mb": sum(m.memory_usage_mb for m in loaded_models),
            "total_gpu_memory_mb": sum(m.gpu_memory_usage_mb for m in loaded_models),
            "status": "healthy" if len(loaded_models) <= self.config["max_loaded_models"] else "overloaded",
        }


class TensorFlowModelWrapper(BaseModelWrapper):
    """TensorFlow 模型包装器"""

    async def load(self) -> bool:
        try:
            import tensorflow as tf
            self._model = tf.saved_model.load(self.metadata.source_path)
            self._loaded = True
            return True
        except ImportError:
            logger.error("TensorFlow 未安装")
            return False
        except Exception as e:
            logger.error(f"TensorFlow 模型加载失败: {e}")
            return False

    async def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        import tensorflow as tf
        tensor = tf.constant(input_data.get("data", []))
        result = self._model(tensor)
        return {"output": result.numpy().tolist()}


class ONNXModelWrapper(BaseModelWrapper):
    """ONNX 模型包装器"""

    async def load(self) -> bool:
        try:
            import onnxruntime as ort
            self._model = ort.InferenceSession(self.metadata.source_path)
            self._loaded = True
            return True
        except ImportError:
            logger.error("ONNX Runtime 未安装")
            return False
        except Exception as e:
            logger.error(f"ONNX 模型加载失败: {e}")
            return False

    async def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        input_name = self._model.get_inputs()[0].name
        result = self._model.run(None, {input_name: input_data.get("data", [])})
        return {"output": result[0].tolist() if hasattr(result[0], 'tolist') else result[0]}


class PyTorchModelWrapper(BaseModelWrapper):
    """PyTorch 模型包装器"""

    async def load(self) -> bool:
        try:
            import torch
            self._model = torch.jit.load(self.metadata.source_path)
            self._model.eval()
            self._loaded = True
            return True
        except ImportError:
            logger.error("PyTorch 未安装")
            return False
        except Exception as e:
            logger.error(f"PyTorch 模型加载失败: {e}")
            return False

    async def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        import torch
        tensor = torch.tensor(input_data.get("data", []))
        with torch.no_grad():
            result = self._model(tensor)
        return {"output": result.tolist() if hasattr(result, 'tolist') else result}


class CustomModelWrapper(BaseModelWrapper):
    """自定义模型包装器"""

    async def load(self) -> bool:
        try:
            spec = importlib.util.spec_from_file_location(
                "custom_model", self.metadata.source_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, "create_model"):
                    self._model = module.create_model()
                    self._loaded = True
                    return True
            return False
        except Exception as e:
            logger.error(f"自定义模型加载失败: {e}")
            return False

    async def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if hasattr(self._model, "predict"):
            result = self._model.predict(input_data)
            return {"output": result}
        return {"output": input_data}
