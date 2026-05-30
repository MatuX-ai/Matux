"""
白板协作模块
支持手写笔迹的实时协作白板系统
"""

from .collaboration_manager import CollaborationManager
from .handwriting_recognizer import HandwritingRecognizer
from .stroke_renderer import StrokeRenderer
from .whiteboard_core import WhiteboardCore
from .whiteboard_service import WhiteboardService

__all__ = [
    "WhiteboardCore",
    "StrokeRenderer",
    "CollaborationManager",
    "HandwritingRecognizer",
    "WhiteboardService",
]
