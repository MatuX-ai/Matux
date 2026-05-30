"""
OpenCL图像处理流水线
提供基于OpenCL的图像处理功能
"""

import logging
from typing import Optional, Dict, Any
import numpy as np
from datetime import datetime

from .context_manager import default_context_manager, OpenCLContextManager
from ..hal.hal_interface import HardwareAccelerator, AcceleratorType, AcceleratorStatus

logger = logging.getLogger(__name__)


class OpenCLPipeline(HardwareAccelerator):
    """OpenCL图像处理流水线"""
    
    def __init__(self, context_manager: Optional[OpenCLContextManager] = None):
        super().__init__(AcceleratorType.GPU_OPENCL)
        self.context_manager = context_manager or default_context_manager
        self.kernels = {}
        self.buffers = {}
        self.performance_stats = {
            "operations_count": 0,
            "total_processing_time": 0.0,
            "average_operation_time": 0.0,
            "kernel_compilation_time": 0.0
        }
        
    def initialize(self) -> bool:
        """初始化OpenCL流水线"""
        try:
            self.status = AcceleratorStatus.INITIALIZING
            logger.info("正在初始化OpenCL图像处理流水线...")
            
            # 初始化OpenCL上下文
            if not self.context_manager.is_initialized:
                if not self.context_manager.initialize():
                    raise RuntimeError("OpenCL上下文初始化失败")
            
            # 编译内核程序
            self._compile_kernels()
            
            self.initialized_at = datetime.now()
            self.status = AcceleratorStatus.READY
            
            logger.info("OpenCL图像处理流水线初始化成功")
            return True
            
        except Exception as e:
            self.status = AcceleratorStatus.ERROR
            self.last_error = str(e)
            logger.error(f"OpenCL流水线初始化失败: {str(e)}")
            return False
    
    def _compile_kernels(self):
        """编译OpenCL内核"""
        start_time = datetime.now()
        
        # 边缘检测内核
        edge_kernel_source = """
        __kernel void edge_detection_kernel(
            __global const uchar* input_image,
            __global uchar* output_image,
            const int width,
            const int height,
            const uchar threshold
        ) {
            int x = get_global_id(0);
            int y = get_global_id(1);
            
            if (x < width && y < height) {
                int idx = y * width + x;
                uchar pixel = input_image[idx];
                output_image[idx] = (pixel > threshold) ? 255 : 0;
            }
        }
        """
        
        # 矩阵乘法内核
        matrix_kernel_source = """
        __kernel void matrix_multiply_kernel(
            __global const float* matrix_a,
            __global const float* matrix_b,
            __global float* result,
            const int rows_a,
            const int cols_a,
            const int cols_b
        ) {
            int row = get_global_id(0);
            int col = get_global_id(1);
            
            if (row < rows_a && col < cols_b) {
                float sum = 0.0f;
                for (int k = 0; k < cols_a; k++) {
                    sum += matrix_a[row * cols_a + k] * matrix_b[k * cols_b + col];
                }
                result[row * cols_b + col] = sum;
            }
        }
        """
        
        try:
            # 编译边缘检测内核
            edge_program = self.context_manager.create_program(edge_kernel_source)
            self.kernels['edge_detection'] = edge_program.edge_detection_kernel
            
            # 编译矩阵乘法内核
            matrix_program = self.context_manager.create_program(matrix_kernel_source)
            self.kernels['matrix_multiply'] = matrix_program.matrix_multiply_kernel
            
            compilation_time = (datetime.now() - start_time).total_seconds()
            self.performance_stats["kernel_compilation_time"] = compilation_time
            
            logger.info(f"OpenCL内核编译完成，耗时: {compilation_time:.4f}秒")
            
        except Exception as e:
            logger.error(f"内核编译失败: {str(e)}")
            raise
    
    def detect_edges(self, image: np.ndarray, threshold: int = 128) -> np.ndarray:
        """OpenCL硬件加速边缘检测"""
        if not self.is_available():
            raise RuntimeError("OpenCL流水线不可用")
            
        start_time = datetime.now()
        self.status = AcceleratorStatus.BUSY
        
        try:
            logger.debug(f"开始OpenCL边缘检测，图像尺寸: {image.shape}")
            
            # 确保输入是灰度图像
            if len(image.shape) == 3:
                if image.shape[2] == 3:  # RGB
                    gray_image = np.dot(image[...,:3], [0.2989, 0.5870, 0.1140])
                else:
                    gray_image = np.dot(image[...,:3], [0.2989, 0.5870, 0.1140])
                gray_image = gray_image.astype(np.uint8)
            else:
                gray_image = image.astype(np.uint8)
            
            height, width = gray_image.shape
            
            # 创建缓冲区
            input_buffer = self.context_manager.create_buffer(gray_image.flatten())
            output_buffer = self.context_manager.create_buffer(
                np.empty_like(gray_image.flatten())
            )
            
            # 执行内核
            kernel = self.kernels['edge_detection']
            execution_time = self.context_manager.execute_kernel(
                kernel,
                (width, height),
                None,
                input_buffer,
                output_buffer,
                np.int32(width),
                np.int32(height),
                np.uint8(threshold)
            )
            
            # 获取结果
            result_flat = self.context_manager.copy_buffer_to_host(
                output_buffer, (height * width,), np.uint8
            )
            result = result_flat.reshape((height, width))
            
            # 更新性能统计
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_stats(processing_time)
            
            self.status = AcceleratorStatus.READY
            logger.debug(f"OpenCL边缘检测完成，执行时间: {execution_time:.4f}秒")
            
            return result
            
        except Exception as e:
            self.status = AcceleratorStatus.ERROR
            self.last_error = str(e)
            logger.error(f"OpenCL边缘检测失败: {str(e)}")
            raise
    
    def matrix_multiply(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """OpenCL硬件加速矩阵乘法"""
        if not self.is_available():
            raise RuntimeError("OpenCL流水线不可用")
            
        start_time = datetime.now()
        self.status = AcceleratorStatus.BUSY
        
        try:
            logger.debug(f"开始OpenCL矩阵乘法，A形状: {a.shape}, B形状: {b.shape}")
            
            # 验证矩阵维度
            if a.shape[1] != b.shape[0]:
                raise ValueError(f"矩阵维度不匹配: {a.shape} × {b.shape}")
            
            rows_a, cols_a = a.shape
            cols_b = b.shape[1]
            
            # 创建缓冲区
            buffer_a = self.context_manager.create_buffer(a.astype(np.float32).flatten())
            buffer_b = self.context_manager.create_buffer(b.astype(np.float32).flatten())
            result_buffer = self.context_manager.create_buffer(
                np.empty((rows_a, cols_b), dtype=np.float32).flatten()
            )
            
            # 执行内核
            kernel = self.kernels['matrix_multiply']
            execution_time = self.context_manager.execute_kernel(
                kernel,
                (rows_a, cols_b),
                None,
                buffer_a,
                buffer_b,
                result_buffer,
                np.int32(rows_a),
                np.int32(cols_a),
                np.int32(cols_b)
            )
            
            # 获取结果
            result_flat = self.context_manager.copy_buffer_to_host(
                result_buffer, (rows_a * cols_b,), np.float32
            )
            result = result_flat.reshape((rows_a, cols_b))
            
            # 更新性能统计
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_performance_stats(processing_time)
            
            self.status = AcceleratorStatus.READY
            logger.debug(f"OpenCL矩阵乘法完成，执行时间: {execution_time:.4f}秒")
            
            return result
            
        except Exception as e:
            self.status = AcceleratorStatus.ERROR
            self.last_error = str(e)
            logger.error(f"OpenCL矩阵乘法失败: {str(e)}")
            raise
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取OpenCL性能统计信息"""
        base_stats = super().get_performance_stats()
        opencl_stats = self.context_manager.get_performance_stats()
        
        return {
            **base_stats,
            **self.performance_stats,
            "opencl_stats": opencl_stats,
            "compiled_kernels": list(self.kernels.keys())
        }
    
    def _update_performance_stats(self, operation_time: float):
        """更新性能统计数据"""
        self.performance_stats["operations_count"] += 1
        self.performance_stats["total_processing_time"] += operation_time
        
        if self.performance_stats["operations_count"] > 0:
            self.performance_stats["average_operation_time"] = (
                self.performance_stats["total_processing_time"] / 
                self.performance_stats["operations_count"]
            )
    
    def cleanup(self):
        """清理OpenCL流水线资源"""
        try:
            # 清理缓冲区
            self.buffers.clear()
            self.kernels.clear()
            
            # 调用父类清理
            super().cleanup()
            
        except Exception as e:
            logger.error(f"OpenCL流水线资源清理失败: {str(e)}")


# 注册OpenCL加速器
from ..hal.hal_interface import AcceleratorFactory
AcceleratorFactory.register_accelerator("gpu_opencl", OpenCLPipeline)