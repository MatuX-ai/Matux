"""
硬件抽象层(HAL)接口定义
提供统一的硬件加速器抽象接口
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AcceleratorType(Enum):
    """硬件加速器类型枚举"""
    FPGA = "fpga"
    GPU_OPENCL = "gpu_opencl"
    CPU_FALLBACK = "cpu_fallback"


class AcceleratorStatus(Enum):
    """硬件加速器状态枚举"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


class HardwareAccelerator(ABC):
    """硬件加速器抽象基类"""
    
    def __init__(self, accelerator_type: AcceleratorType):
        self.type = accelerator_type
        self.status = AcceleratorStatus.UNINITIALIZED
        self.initialized_at: Optional[datetime] = None
        self.last_error: Optional[str] = None
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化硬件加速器
        
        Returns:
            bool: 初始化成功返回True，失败返回False
        """
        pass
    
    @abstractmethod
    def detect_edges(self, image: np.ndarray, threshold: int = 128) -> np.ndarray:
        """
        硬件加速边缘检测
        
        Args:
            image: 输入图像数组 (numpy array)
            threshold: 边缘检测阈值 (0-255)
            
        Returns:
            np.ndarray: 处理后的边缘图像
        """
        pass
    
    @abstractmethod
    def matrix_multiply(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """
        硬件加速矩阵乘法
        
        Args:
            a: 第一个矩阵
            b: 第二个矩阵
            
        Returns:
            np.ndarray: 矩阵乘法结果
        """
        pass
    
    @abstractmethod
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            Dict: 包含性能指标的字典
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取加速器状态信息"""
        return {
            "type": self.type.value,
            "status": self.status.value,
            "initialized_at": self.initialized_at.isoformat() if self.initialized_at else None,
            "last_error": self.last_error
        }
    
    def is_available(self) -> bool:
        """检查加速器是否可用"""
        return self.status in [AcceleratorStatus.READY, AcceleratorStatus.BUSY]
    
    def cleanup(self):
        """清理资源"""
        self.status = AcceleratorStatus.UNINITIALIZED
        self.initialized_at = None
        logger.info(f"{self.type.value} 加速器资源已清理")


class AcceleratorFactory:
    """硬件加速器工厂类"""
    
    _accelerators = {}
    
    @classmethod
    def register_accelerator(cls, name: str, accelerator_class):
        """注册加速器实现"""
        cls._accelerators[name] = accelerator_class
        logger.info(f"已注册加速器: {name}")
    
    @classmethod
    def create_accelerator(cls, name: str, **kwargs) -> Optional[HardwareAccelerator]:
        """创建指定类型的加速器实例"""
        if name in cls._accelerators:
            try:
                accelerator = cls._accelerators[name](**kwargs)
                logger.info(f"成功创建加速器实例: {name}")
                return accelerator
            except Exception as e:
                logger.error(f"创建加速器失败 {name}: {str(e)}")
                return None
        else:
            logger.error(f"未找到加速器类型: {name}")
            return None
    
    @classmethod
    def get_available_accelerators(cls) -> List[str]:
        """获取所有可用的加速器类型"""
        return list(cls._accelerators.keys())