"""
加速器管理器
负责多个硬件加速器的统一管理和调度
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
import threading

from .hal_interface import HardwareAccelerator, AcceleratorFactory, AcceleratorType, AcceleratorStatus

logger = logging.getLogger(__name__)


class AcceleratorManager:
    """硬件加速器管理器"""
    
    def __init__(self):
        self.accelerators: Dict[str, HardwareAccelerator] = {}
        self.active_accelerator: Optional[HardwareAccelerator] = None
        self.lock = threading.RLock()
        self.operation_history: List[Dict] = []
        self.max_history_size = 1000
        
    def initialize_accelerators(self, accelerator_configs: List[Dict]) -> bool:
        """
        初始化所有配置的加速器
        
        Args:
            accelerator_configs: 加速器配置列表
                [
                    {
                        "type": "fpga",
                        "name": "primary_fpga",
                        "config": {...}
                    },
                    {
                        "type": "gpu_opencl", 
                        "name": "secondary_gpu",
                        "config": {...}
                    }
                ]
                
        Returns:
            bool: 是否至少有一个加速器初始化成功
        """
        with self.lock:
            success_count = 0
            
            for config in accelerator_configs:
                accel_type = config.get("type")
                name = config.get("name", accel_type)
                accel_config = config.get("config", {})
                
                try:
                    # 创建加速器实例
                    accelerator = AcceleratorFactory.create_accelerator(
                        accel_type, **accel_config
                    )
                    
                    if accelerator and accelerator.initialize():
                        self.accelerators[name] = accelerator
                        success_count += 1
                        logger.info(f"加速器 {name} ({accel_type}) 初始化成功")
                    else:
                        logger.warning(f"加速器 {name} ({accel_type}) 初始化失败")
                        
                except Exception as e:
                    logger.error(f"创建加速器 {name} 失败: {str(e)}")
            
            # 设置主加速器
            if success_count > 0:
                self._select_primary_accelerator()
                logger.info(f"成功初始化 {success_count} 个加速器")
                return True
            else:
                logger.error("没有加速器初始化成功")
                return False
    
    def _select_primary_accelerator(self):
        """选择主加速器（优先级：FPGA > GPU > CPU）"""
        priority_order = [
            AcceleratorType.FPGA,
            AcceleratorType.GPU_OPENCL, 
            AcceleratorType.CPU_FALLBACK
        ]
        
        for accel_type in priority_order:
            for accelerator in self.accelerators.values():
                if (accelerator.type == accel_type and 
                    accelerator.is_available()):
                    self.active_accelerator = accelerator
                    logger.info(f"选定主加速器: {accelerator.type.value}")
                    return
        
        self.active_accelerator = None
        logger.warning("未找到可用的主加速器")
    
    def detect_edges(self, image, threshold: int = 128, accelerator_name: Optional[str] = None):
        """使用指定或默认加速器进行边缘检测"""
        accelerator = self._get_accelerator(accelerator_name)
        if not accelerator:
            raise RuntimeError("没有可用的加速器")
        
        start_time = datetime.now()
        
        try:
            result = accelerator.detect_edges(image, threshold)
            
            # 记录操作历史
            self._record_operation(
                operation="edge_detection",
                accelerator=accelerator.type.value,
                input_shape=image.shape,
                output_shape=result.shape,
                start_time=start_time,
                end_time=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"边缘检测失败: {str(e)}")
            raise
    
    def matrix_multiply(self, a, b, accelerator_name: Optional[str] = None):
        """使用指定或默认加速器进行矩阵乘法"""
        accelerator = self._get_accelerator(accelerator_name)
        if not accelerator:
            raise RuntimeError("没有可用的加速器")
        
        start_time = datetime.now()
        
        try:
            result = accelerator.matrix_multiply(a, b)
            
            # 记录操作历史
            self._record_operation(
                operation="matrix_multiply",
                accelerator=accelerator.type.value,
                input_shape=(a.shape, b.shape),
                output_shape=result.shape,
                start_time=start_time,
                end_time=datetime.now()
            )
            
            return result
            
        except Exception as e:
            logger.error(f"矩阵乘法失败: {str(e)}")
            raise
    
    def _get_accelerator(self, name: Optional[str] = None) -> Optional[HardwareAccelerator]:
        """获取指定名称的加速器或默认加速器"""
        with self.lock:
            if name:
                return self.accelerators.get(name)
            else:
                # 检查主加速器是否仍然可用
                if self.active_accelerator and self.active_accelerator.is_available():
                    return self.active_accelerator
                else:
                    # 重新选择主加速器
                    self._select_primary_accelerator()
                    return self.active_accelerator
    
    def _record_operation(self, operation: str, accelerator: str, 
                         input_shape: Any, output_shape: Any,
                         start_time: datetime, end_time: datetime):
        """记录操作历史"""
        record = {
            "operation": operation,
            "accelerator": accelerator,
            "input_shape": input_shape,
            "output_shape": output_shape,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_ms": (end_time - start_time).total_seconds() * 1000
        }
        
        with self.lock:
            self.operation_history.append(record)
            # 限制历史记录大小
            if len(self.operation_history) > self.max_history_size:
                self.operation_history = self.operation_history[-self.max_history_size:]
    
    def get_accelerator_status(self) -> Dict[str, Any]:
        """获取所有加速器的状态信息"""
        with self.lock:
            status = {
                "active_accelerator": self.active_accelerator.type.value if self.active_accelerator else None,
                "total_accelerators": len(self.accelerators),
                "available_accelerators": [],
                "accelerator_details": {}
            }
            
            for name, accelerator in self.accelerators.items():
                accel_status = accelerator.get_status()
                status["accelerator_details"][name] = accel_status
                
                if accelerator.is_available():
                    status["available_accelerators"].append({
                        "name": name,
                        "type": accelerator.type.value
                    })
            
            return status
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能汇总信息"""
        with self.lock:
            summary = {
                "total_operations": len(self.operation_history),
                "recent_operations": self.operation_history[-10:] if self.operation_history else [],
                "accelerator_performance": {}
            }
            
            # 统计各加速器的性能
            for name, accelerator in self.accelerators.items():
                summary["accelerator_performance"][name] = accelerator.get_performance_stats()
            
            return summary
    
    def cleanup(self):
        """清理所有加速器资源"""
        with self.lock:
            for accelerator in self.accelerators.values():
                try:
                    accelerator.cleanup()
                except Exception as e:
                    logger.error(f"清理加速器失败: {str(e)}")
            
            self.accelerators.clear()
            self.active_accelerator = None
            self.operation_history.clear()
            logger.info("加速器管理器资源已清理")


# 默认全局加速器管理器实例
default_manager = AcceleratorManager()