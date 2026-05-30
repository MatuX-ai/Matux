"""
硬件加速矩阵类
提供基于硬件加速器的矩阵运算功能
"""

import logging
import time
import numpy as np
from typing import Optional, Dict, Any
from datetime import datetime

from ..hal.accelerator_manager import default_manager

logger = logging.getLogger(__name__)


class AcceleratedMatrix:
    """硬件加速矩阵类"""
    
    def __init__(self, data: np.ndarray, accelerator_name: Optional[str] = None):
        """
        初始化加速矩阵
        
        Args:
            data: 矩阵数据
            accelerator_name: 指定使用的加速器名称
        """
        self.data = np.array(data, dtype=np.float32)
        self.shape = self.data.shape
        self.accelerator_name = accelerator_name
        self.creation_time = datetime.now()
        
        # 性能统计
        self.operation_stats = {
            "multiplications": 0,
            "additions": 0,
            "total_time": 0.0,
            "operations_history": []
        }
        
    @classmethod
    def zeros(cls, shape: tuple, accelerator_name: Optional[str] = None):
        """创建零矩阵"""
        return cls(np.zeros(shape, dtype=np.float32), accelerator_name)
    
    @classmethod
    def ones(cls, shape: tuple, accelerator_name: Optional[str] = None):
        """创建全1矩阵"""
        return cls(np.ones(shape, dtype=np.float32), accelerator_name)
    
    @classmethod
    def random(cls, shape: tuple, accelerator_name: Optional[str] = None):
        """创建随机矩阵"""
        return cls(np.random.random(shape).astype(np.float32), accelerator_name)
    
    def __mul__(self, other):
        """矩阵乘法运算符重载"""
        return self.multiply(other)
    
    def __add__(self, other):
        """矩阵加法运算符重载"""
        return self.add(other)
    
    def multiply(self, other):
        """
        硬件加速矩阵乘法
        
        Args:
            other: 另一个矩阵或标量
            
        Returns:
            AcceleratedMatrix: 乘法结果
        """
        start_time = time.time()
        
        try:
            if isinstance(other, (int, float)):
                # 标量乘法
                result_data = self.data * other
                execution_time = time.time() - start_time
            elif isinstance(other, AcceleratedMatrix):
                # 矩阵乘法
                result_data = default_manager.matrix_multiply(
                    self.data, other.data, self.accelerator_name
                )
                execution_time = time.time() - start_time
            elif isinstance(other, np.ndarray):
                # NumPy数组乘法
                result_data = default_manager.matrix_multiply(
                    self.data, other, self.accelerator_name
                )
                execution_time = time.time() - start_time
            else:
                raise TypeError(f"不支持的乘法操作类型: {type(other)}")
            
            # 更新统计信息
            self._update_stats("multiplication", execution_time, self.shape, other.shape if hasattr(other, 'shape') else None)
            
            return AcceleratedMatrix(result_data, self.accelerator_name)
            
        except Exception as e:
            logger.error(f"矩阵乘法失败: {str(e)}")
            raise
    
    def add(self, other):
        """
        硬件加速矩阵加法
        
        Args:
            other: 另一个矩阵或标量
            
        Returns:
            AcceleratedMatrix: 加法结果
        """
        start_time = time.time()
        
        try:
            if isinstance(other, (int, float)):
                # 标量加法
                result_data = self.data + other
            elif isinstance(other, AcceleratedMatrix):
                # 矩阵加法
                if self.shape != other.shape:
                    raise ValueError(f"矩阵形状不匹配: {self.shape} vs {other.shape}")
                result_data = self.data + other.data
            elif isinstance(other, np.ndarray):
                # NumPy数组加法
                if self.shape != other.shape:
                    raise ValueError(f"矩阵形状不匹配: {self.shape} vs {other.shape}")
                result_data = self.data + other
            else:
                raise TypeError(f"不支持的加法操作类型: {type(other)}")
            
            execution_time = time.time() - start_time
            
            # 更新统计信息
            self._update_stats("addition", execution_time, self.shape, other.shape if hasattr(other, 'shape') else None)
            
            return AcceleratedMatrix(result_data, self.accelerator_name)
            
        except Exception as e:
            logger.error(f"矩阵加法失败: {str(e)}")
            raise
    
    def transpose(self):
        """矩阵转置"""
        return AcceleratedMatrix(self.data.T, self.accelerator_name)
    
    def inverse(self):
        """矩阵求逆（使用CPU计算）"""
        try:
            # 矩阵求逆通常在CPU上更高效
            result_data = np.linalg.inv(self.data)
            return AcceleratedMatrix(result_data, self.accelerator_name)
        except Exception as e:
            logger.error(f"矩阵求逆失败: {str(e)}")
            raise
    
    def determinant(self):
        """计算矩阵行列式（使用CPU计算）"""
        try:
            return np.linalg.det(self.data)
        except Exception as e:
            logger.error(f"计算行列式失败: {str(e)}")
            raise
    
    def eigenvalues(self):
        """计算特征值（使用CPU计算）"""
        try:
            return np.linalg.eigvals(self.data)
        except Exception as e:
            logger.error(f"计算特征值失败: {str(e)}")
            raise
    
    def svd(self):
        """奇异值分解（使用CPU计算）"""
        try:
            u, s, vh = np.linalg.svd(self.data)
            return (
                AcceleratedMatrix(u, self.accelerator_name),
                AcceleratedMatrix(np.diag(s), self.accelerator_name),
                AcceleratedMatrix(vh, self.accelerator_name)
            )
        except Exception as e:
            logger.error(f"SVD分解失败: {str(e)}")
            raise
    
    def _update_stats(self, operation: str, execution_time: float, 
                     input_shape1: tuple, input_shape2: Optional[tuple] = None):
        """更新操作统计信息"""
        self.operation_stats["total_time"] += execution_time
        
        if operation == "multiplication":
            self.operation_stats["multiplications"] += 1
        elif operation == "addition":
            self.operation_stats["additions"] += 1
        
        # 记录操作历史
        self.operation_stats["operations_history"].append({
            "operation": operation,
            "input_shapes": [input_shape1, input_shape2] if input_shape2 else [input_shape1],
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制历史记录大小
        if len(self.operation_stats["operations_history"]) > 100:
            self.operation_stats["operations_history"] = \
                self.operation_stats["operations_history"][-100:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取矩阵操作统计信息"""
        return {
            "shape": self.shape,
            "creation_time": self.creation_time.isoformat(),
            "operations": {
                "multiplications": self.operation_stats["multiplications"],
                "additions": self.operation_stats["additions"],
                "total_operations": self.operation_stats["multiplications"] + self.operation_stats["additions"]
            },
            "performance": {
                "total_time": self.operation_stats["total_time"],
                "average_time_per_operation": (
                    self.operation_stats["total_time"] / 
                    max(self.operation_stats["multiplications"] + self.operation_stats["additions"], 1)
                )
            },
            "recent_operations": self.operation_stats["operations_history"][-10:] if self.operation_stats["operations_history"] else []
        }
    
    def to_numpy(self) -> np.ndarray:
        """转换为NumPy数组"""
        return self.data.copy()
    
    def __str__(self) -> str:
        return f"AcceleratedMatrix(shape={self.shape}, dtype={self.data.dtype})"
    
    def __repr__(self) -> str:
        return self.__str__()