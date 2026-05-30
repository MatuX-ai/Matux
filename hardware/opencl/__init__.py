"""
OpenCL图像处理模块
提供基于OpenCL的图像处理流水线
"""

from .pipeline import OpenCLPipeline
from .context_manager import OpenCLContextManager

__all__ = [
    'OpenCLPipeline',
    'OpenCLContextManager'
]