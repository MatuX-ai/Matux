"""
硬件加速模块
提供FPGA和OpenCL硬件加速功能
"""

__version__ = "1.0.0"
__author__ = "iMato Team"

# 导出主要模块
from .hal import HardwareAccelerator
from .matrix_lib import AcceleratedMatrix
from .opencl import OpenCLPipeline

__all__ = [
    'HardwareAccelerator',
    'AcceleratedMatrix', 
    'OpenCLPipeline'
]