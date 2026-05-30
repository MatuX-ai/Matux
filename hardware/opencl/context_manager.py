"""
OpenCL上下文管理器
负责OpenCL环境的初始化和资源管理
"""

import logging
from typing import Optional, Dict, Any, List
import numpy as np
from datetime import datetime

try:
    import pyopencl as cl
    OPENCL_AVAILABLE = True
except ImportError:
    OPENCL_AVAILABLE = False
    cl = None

logger = logging.getLogger(__name__)


class OpenCLContextManager:
    """OpenCL上下文管理器"""
    
    def __init__(self):
        self.context: Optional[cl.Context] = None
        self.queue: Optional[cl.CommandQueue] = None
        self.devices: List[cl.Device] = []
        self.platforms: List[cl.Platform] = []
        self.is_initialized = False
        self.performance_stats = {
            "kernel_executions": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0
        }
        
    def initialize(self, platform_index: int = 0, device_type: str = "gpu") -> bool:
        """
        初始化OpenCL环境
        
        Args:
            platform_index: 平台索引
            device_type: 设备类型 ("gpu", "cpu", "all")
            
        Returns:
            bool: 初始化成功返回True
        """
        if not OPENCL_AVAILABLE:
            logger.error("PyOpenCL未安装，无法初始化OpenCL环境")
            return False
            
        try:
            logger.info("正在初始化OpenCL环境...")
            
            # 获取平台信息
            self.platforms = cl.get_platforms()
            logger.info(f"发现 {len(self.platforms)} 个OpenCL平台")
            
            if not self.platforms:
                logger.error("未找到OpenCL平台")
                return False
                
            if platform_index >= len(self.platforms):
                logger.warning(f"平台索引 {platform_index} 超出范围，使用平台 0")
                platform_index = 0
            
            platform = self.platforms[platform_index]
            logger.info(f"使用平台: {platform.name}")
            
            # 获取设备
            device_types = {
                "gpu": cl.device_type.GPU,
                "cpu": cl.device_type.CPU,
                "all": cl.device_type.ALL
            }
            
            device_type_flag = device_types.get(device_type.lower(), cl.device_type.GPU)
            self.devices = platform.get_devices(device_type=device_type_flag)
            
            if not self.devices:
                logger.error(f"在平台 {platform.name} 上未找到 {device_type} 设备")
                return False
                
            logger.info(f"发现 {len(self.devices)} 个 {device_type} 设备")
            
            # 创建上下文
            self.context = cl.Context(devices=self.devices)
            
            # 创建命令队列
            self.queue = cl.CommandQueue(self.context, self.devices[0])
            
            self.is_initialized = True
            logger.info("OpenCL环境初始化成功")
            self._log_device_info()
            
            return True
            
        except Exception as e:
            logger.error(f"OpenCL初始化失败: {str(e)}")
            self.cleanup()
            return False
    
    def _log_device_info(self):
        """记录设备详细信息"""
        for i, device in enumerate(self.devices):
            logger.info(f"设备 {i}: {device.name}")
            logger.info(f"  类型: {cl.device_type.to_string(device.type)}")
            logger.info(f"  计算单元: {device.max_compute_units}")
            logger.info(f"  全局内存: {device.global_mem_size / (1024**3):.2f} GB")
            logger.info(f"  本地内存: {device.local_mem_size / 1024:.2f} KB")
            logger.info(f"  最大工作组大小: {device.max_work_group_size}")
    
    def create_buffer(self, data: np.ndarray, flags: int = None) -> cl.Buffer:
        """创建OpenCL缓冲区"""
        if not self.is_initialized:
            raise RuntimeError("OpenCL环境未初始化")
            
        if flags is None:
            flags = cl.mem_flags.READ_WRITE | cl.mem_flags.COPY_HOST_PTR
            
        return cl.Buffer(self.context, flags, hostbuf=data)
    
    def create_program(self, kernel_source: str) -> cl.Program:
        """编译OpenCL程序"""
        if not self.is_initialized:
            raise RuntimeError("OpenCL环境未初始化")
            
        try:
            program = cl.Program(self.context, kernel_source)
            program.build()
            return program
        except cl.RuntimeError as e:
            logger.error(f"内核编译失败: {str(e)}")
            raise
    
    def execute_kernel(self, kernel: cl.Kernel, global_size: tuple, 
                      local_size: tuple = None, *args) -> float:
        """执行OpenCL内核并返回执行时间"""
        if not self.is_initialized:
            raise RuntimeError("OpenCL环境未初始化")
            
        start_time = datetime.now()
        
        try:
            # 设置内核参数
            for i, arg in enumerate(args):
                kernel.set_arg(i, arg)
            
            # 执行内核
            cl.enqueue_nd_range_kernel(self.queue, kernel, global_size, local_size)
            
            # 等待完成
            self.queue.finish()
            
            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 更新性能统计
            self._update_performance_stats(execution_time)
            
            return execution_time
            
        except Exception as e:
            logger.error(f"内核执行失败: {str(e)}")
            raise
    
    def _update_performance_stats(self, execution_time: float):
        """更新性能统计数据"""
        self.performance_stats["kernel_executions"] += 1
        self.performance_stats["total_execution_time"] += execution_time
        
        if self.performance_stats["kernel_executions"] > 0:
            self.performance_stats["average_execution_time"] = (
                self.performance_stats["total_execution_time"] / 
                self.performance_stats["kernel_executions"]
            )
    
    def copy_buffer_to_host(self, buffer: cl.Buffer, shape: tuple, 
                           dtype: np.dtype = np.float32) -> np.ndarray:
        """将OpenCL缓冲区数据复制到主机内存"""
        if not self.is_initialized:
            raise RuntimeError("OpenCL环境未初始化")
            
        result = np.empty(shape, dtype=dtype)
        cl.enqueue_copy(self.queue, result, buffer)
        self.queue.finish()
        return result
    
    def get_device_info(self) -> List[Dict[str, Any]]:
        """获取设备信息"""
        info_list = []
        
        for device in self.devices:
            info = {
                "name": device.name,
                "type": cl.device_type.to_string(device.type),
                "compute_units": device.max_compute_units,
                "global_memory_gb": device.global_mem_size / (1024**3),
                "local_memory_kb": device.local_mem_size / 1024,
                "max_work_group_size": device.max_work_group_size,
                "max_work_item_sizes": device.max_work_item_sizes
            }
            info_list.append(info)
            
        return info_list
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return {
            **self.performance_stats,
            "devices_count": len(self.devices),
            "is_initialized": self.is_initialized
        }
    
    def cleanup(self):
        """清理OpenCL资源"""
        try:
            if self.queue:
                self.queue.finish()
                self.queue = None
                
            self.context = None
            self.devices = []
            self.platforms = []
            self.is_initialized = False
            
            logger.info("OpenCL资源已清理")
            
        except Exception as e:
            logger.error(f"清理OpenCL资源时发生错误: {str(e)}")


# 全局OpenCL上下文管理器实例
default_context_manager = OpenCLContextManager()