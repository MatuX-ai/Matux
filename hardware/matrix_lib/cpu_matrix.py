"""
CPU矩阵实现
作为硬件加速的软件备份方案
"""

import logging
import time
import numpy as np
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CPUMatrix:
    """CPU矩阵实现类"""
    
    def __init__(self, data: np.ndarray):
        """
        初始化CPU矩阵
        
        Args:
            data: 矩阵数据
        """
        self.data = np.array(data, dtype=np.float64)  # 使用更高精度
        self.shape = self.data.shape
        self.creation_time = datetime.now()
        
        # 性能统计
        self.stats = {
            "operations_count": 0,
            "total_time": 0.0,
            "operation_history": []
        }
        
    @classmethod
    def zeros(cls, shape: tuple):
        """创建零矩阵"""
        return cls(np.zeros(shape, dtype=np.float64))
    
    @classmethod
    def ones(cls, shape: tuple):
        """创建全1矩阵"""
        return cls(np.ones(shape, dtype=np.float64))
    
    @classmethod
    def eye(cls, n: int):
        """创建单位矩阵"""
        return cls(np.eye(n, dtype=np.float64))
    
    @classmethod
    def random(cls, shape: tuple):
        """创建随机矩阵"""
        return cls(np.random.random(shape).astype(np.float64))
    
    def __mul__(self, other):
        """矩阵乘法运算符重载"""
        return self.multiply(other)
    
    def __add__(self, other):
        """矩阵加法运算符重载"""
        return self.add(other)
    
    def multiply(self, other):
        """
        CPU矩阵乘法
        
        Args:
            other: 另一个矩阵或标量
            
        Returns:
            CPUMatrix: 乘法结果
        """
        start_time = time.time()
        
        try:
            if isinstance(other, (int, float)):
                result_data = self.data * other
            elif isinstance(other, CPUMatrix):
                result_data = np.dot(self.data, other.data)
            elif isinstance(other, np.ndarray):
                result_data = np.dot(self.data, other)
            else:
                raise TypeError(f"不支持的乘法操作类型: {type(other)}")
            
            execution_time = time.time() - start_time
            self._update_stats("multiplication", execution_time)
            
            return CPUMatrix(result_data)
            
        except Exception as e:
            logger.error(f"CPU矩阵乘法失败: {str(e)}")
            raise
    
    def add(self, other):
        """
        CPU矩阵加法
        
        Args:
            other: 另一个矩阵或标量
            
        Returns:
            CPUMatrix: 加法结果
        """
        start_time = time.time()
        
        try:
            if isinstance(other, (int, float)):
                result_data = self.data + other
            elif isinstance(other, CPUMatrix):
                if self.shape != other.shape:
                    raise ValueError(f"矩阵形状不匹配: {self.shape} vs {other.shape}")
                result_data = self.data + other.data
            elif isinstance(other, np.ndarray):
                if self.shape != other.shape:
                    raise ValueError(f"矩阵形状不匹配: {self.shape} vs {other.shape}")
                result_data = self.data + other
            else:
                raise TypeError(f"不支持的加法操作类型: {type(other)}")
            
            execution_time = time.time() - start_time
            self._update_stats("addition", execution_time)
            
            return CPUMatrix(result_data)
            
        except Exception as e:
            logger.error(f"CPU矩阵加法失败: {str(e)}")
            raise
    
    def transpose(self):
        """矩阵转置"""
        return CPUMatrix(self.data.T)
    
    def inverse(self):
        """矩阵求逆"""
        try:
            result_data = np.linalg.inv(self.data)
            return CPUMatrix(result_data)
        except Exception as e:
            logger.error(f"矩阵求逆失败: {str(e)}")
            raise
    
    def determinant(self):
        """计算矩阵行列式"""
        try:
            return np.linalg.det(self.data)
        except Exception as e:
            logger.error(f"计算行列式失败: {str(e)}")
            raise
    
    def eigenvalues(self):
        """计算特征值"""
        try:
            return np.linalg.eigvals(self.data)
        except Exception as e:
            logger.error(f"计算特征值失败: {str(e)}")
            raise
    
    def eigenvectors(self):
        """计算特征向量和特征值"""
        try:
            eigenvals, eigenvecs = np.linalg.eig(self.data)
            return eigenvals, CPUMatrix(eigenvecs)
        except Exception as e:
            logger.error(f"计算特征向量失败: {str(e)}")
            raise
    
    def svd(self):
        """奇异值分解"""
        try:
            u, s, vh = np.linalg.svd(self.data)
            return CPUMatrix(u), CPUMatrix(np.diag(s)), CPUMatrix(vh)
        except Exception as e:
            logger.error(f"SVD分解失败: {str(e)}")
            raise
    
    def lu_decomposition(self):
        """LU分解"""
        try:
            from scipy.linalg import lu
            p, l, u = lu(self.data)
            return CPUMatrix(p), CPUMatrix(l), CPUMatrix(u)
        except ImportError:
            logger.warning("scipy未安装，无法执行LU分解")
            raise
        except Exception as e:
            logger.error(f"LU分解失败: {str(e)}")
            raise
    
    def qr_decomposition(self):
        """QR分解"""
        try:
            q, r = np.linalg.qr(self.data)
            return CPUMatrix(q), CPUMatrix(r)
        except Exception as e:
            logger.error(f"QR分解失败: {str(e)}")
            raise
    
    def cholesky_decomposition(self):
        """Cholesky分解"""
        try:
            result = np.linalg.cholesky(self.data)
            return CPUMatrix(result)
        except Exception as e:
            logger.error(f"Cholesky分解失败: {str(e)}")
            raise
    
    def solve_linear_system(self, b):
        """
        解线性方程组 Ax = b
        
        Args:
            b: 右侧向量或矩阵
            
        Returns:
            CPUMatrix: 解向量x
        """
        try:
            if isinstance(b, CPUMatrix):
                b_data = b.data
            elif isinstance(b, np.ndarray):
                b_data = b
            else:
                b_data = np.array(b)
            
            solution = np.linalg.solve(self.data, b_data)
            return CPUMatrix(solution)
            
        except Exception as e:
            logger.error(f"解线性方程组失败: {str(e)}")
            raise
    
    def _update_stats(self, operation: str, execution_time: float):
        """更新操作统计信息"""
        self.stats["operations_count"] += 1
        self.stats["total_time"] += execution_time
        
        # 记录操作历史
        self.stats["operation_history"].append({
            "operation": operation,
            "shape": self.shape,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制历史记录大小
        if len(self.stats["operation_history"]) > 100:
            self.stats["operation_history"] = self.stats["operation_history"][-100:]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            "shape": self.shape,
            "dtype": str(self.data.dtype),
            "creation_time": self.creation_time.isoformat(),
            "operations": {
                "count": self.stats["operations_count"],
                "total_time": self.stats["total_time"],
                "average_time": self.stats["total_time"] / max(self.stats["operations_count"], 1)
            },
            "recent_operations": self.stats["operation_history"][-5:] if self.stats["operation_history"] else []
        }
    
    def compare_with(self, other_matrix, rtol: float = 1e-5, atol: float = 1e-8):
        """
        与另一个矩阵比较
        
        Args:
            other_matrix: 要比较的矩阵
            rtol: 相对容差
            atol: 绝对容差
            
        Returns:
            dict: 比较结果
        """
        if isinstance(other_matrix, CPUMatrix):
            other_data = other_matrix.data
        elif isinstance(other_matrix, np.ndarray):
            other_data = other_matrix
        else:
            raise TypeError("只能与CPUMatrix或numpy数组比较")
        
        # 检查形状
        shape_match = self.shape == other_data.shape
        
        # 数值比较
        if shape_match:
            diff = np.abs(self.data - other_data)
            max_diff = np.max(diff)
            mean_diff = np.mean(diff)
            relative_error = np.mean(diff / (np.abs(self.data) + np.abs(other_data) + 1e-12))
            
            is_close = np.allclose(self.data, other_data, rtol=rtol, atol=atol)
        else:
            max_diff = mean_diff = relative_error = float('inf')
            is_close = False
        
        return {
            "shapes_match": shape_match,
            "is_numerically_close": is_close,
            "max_difference": max_diff,
            "mean_difference": mean_diff,
            "relative_error": relative_error,
            "tolerances": {
                "relative_tolerance": rtol,
                "absolute_tolerance": atol
            }
        }
    
    def to_accelerated(self, accelerator_name: Optional[str] = None):
        """转换为硬件加速矩阵"""
        from .accelerated_matrix import AcceleratedMatrix
        return AcceleratedMatrix(self.data.astype(np.float32), accelerator_name)
    
    def to_numpy(self) -> np.ndarray:
        """转换为NumPy数组"""
        return self.data.copy()
    
    def __str__(self) -> str:
        return f"CPUMatrix(shape={self.shape}, dtype={self.data.dtype})"
    
    def __repr__(self) -> str:
        return self.__str__()