"""
硬件抽象层(HAL)模块
提供统一的硬件加速器接口
"""

from .hal_interface import HardwareAccelerator
from .fpga_driver import FPGADriver
from .accelerator_manager import AcceleratorManager
from .performance_monitor import PerformanceMonitor

__all__ = [
    'HardwareAccelerator',
    'FPGADriver',
    'AcceleratorManager',
    'PerformanceMonitor'
]