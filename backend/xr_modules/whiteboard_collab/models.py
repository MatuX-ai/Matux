"""
白板协作数据模型
定义白板相关的数据结构和配置
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import uuid

from pydantic import BaseModel, Field


class StrokeType(str, Enum):
    """笔画类型"""

    PEN = "pen"  # 钢笔
    MARKER = "marker"  # 马克笔
    HIGHLIGHTER = "highlighter"  # 荧光笔
    ERASER = "eraser"  # 橡皮擦
    BRUSH = "brush"  # 画笔


class ToolType(str, Enum):
    """工具类型"""

    STROKE = "stroke"  # 笔画工具
    SHAPE = "shape"  # 形状工具
    TEXT = "text"  # 文本工具
    SELECT = "select"  # 选择工具
    ERASE = "erase"  # 擦除工具


class ShapeType(str, Enum):
    """形状类型"""

    LINE = "line"  # 直线
    RECTANGLE = "rectangle"  # 矩形
    CIRCLE = "circle"  # 圆形
    ARROW = "arrow"  # 箭头
    FREEFORM = "freeform"  # 自由形状


class WhiteboardColor(str, Enum):
    """白板颜色"""

    BLACK = "#000000"
    WHITE = "#FFFFFF"
    RED = "#FF0000"
    GREEN = "#00FF00"
    BLUE = "#0000FF"
    YELLOW = "#FFFF00"
    PURPLE = "#800080"
    ORANGE = "#FFA500"


class Point(BaseModel):
    """点坐标模型"""

    x: float
    y: float
    pressure: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Stroke(BaseModel):
    """笔画模型"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stroke_type: StrokeType
    color: WhiteboardColor
    width: float = Field(default=2.0, ge=0.1, le=50.0)
    opacity: float = Field(default=1.0, ge=0.1, le=1.0)
    points: List[Point] = Field(default_factory=list)
    user_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_complete: bool = False


class Shape(BaseModel):
    """形状模型"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    shape_type: ShapeType
    stroke_type: StrokeType
    color: WhiteboardColor
    stroke_width: float = Field(default=2.0, ge=0.1, le=20.0)
    fill_color: Optional[WhiteboardColor] = None
    fill_opacity: float = Field(default=0.3, ge=0.0, le=1.0)

    # 形状几何属性
    start_point: Point
    end_point: Point
    control_points: List[Point] = Field(default_factory=list)

    user_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TextElement(BaseModel):
    """文本元素模型"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    font_family: str = "Arial"
    font_size: int = Field(default=16, ge=8, le=72)
    color: WhiteboardColor = WhiteboardColor.BLACK
    bold: bool = False
    italic: bool = False
    underline: bool = False

    # 位置属性
    position: Point
    width: Optional[float] = None
    height: Optional[float] = None

    user_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WhiteboardElement(BaseModel):
    """白板元素基类"""

    id: str
    element_type: str  # "stroke", "shape", "text"
    data: Dict[str, Any]  # 具体元素数据
    layer_index: int = 0
    is_selected: bool = False
    is_locked: bool = False
    user_id: Optional[int] = None
    created_at: datetime


class WhiteboardPage(BaseModel):
    """白板页面模型"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    page_number: int
    elements: List[WhiteboardElement] = Field(default_factory=list)
    background_color: WhiteboardColor = WhiteboardColor.WHITE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)


class WhiteboardSession(BaseModel):
    """白板会话模型"""

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    board_name: str = "协作白板"
    owner_id: int
    participants: List[int] = Field(default_factory=list)
    current_page: int = 0
    pages: List[WhiteboardPage] = Field(
        default_factory=lambda: [WhiteboardPage(page_number=0)]
    )
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)


class WhiteboardConfig(BaseModel):
    """白板配置模型"""

    # 显示设置
    canvas_width: int = Field(default=1920, ge=800, le=3840)
    canvas_height: int = Field(default=1080, ge=600, le=2160)
    background_color: WhiteboardColor = WhiteboardColor.WHITE
    grid_visible: bool = False
    grid_size: int = Field(default=20, ge=10, le=100)

    # 工具设置
    default_stroke_type: StrokeType = StrokeType.PEN
    default_color: WhiteboardColor = WhiteboardColor.BLACK
    default_width: float = Field(default=2.0, ge=0.1, le=50.0)

    # 协作设置
    real_time_sync: bool = True
    sync_interval: float = Field(default=0.1, ge=0.01, le=1.0)  # 秒
    conflict_resolution: str = "last_write_wins"  # "last_write_wins", "merge", "manual"

    # 性能设置
    max_stroke_points: int = Field(default=1000, ge=100, le=10000)
    compression_enabled: bool = True
    compression_threshold: float = Field(default=0.5, ge=0.1, le=2.0)


class CollaborationEvent(BaseModel):
    """协作事件模型"""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: int
    event_type: str  # "stroke_start", "stroke_update", "stroke_end", "element_add", "element_modify", "element_remove"
    element_id: Optional[str] = None
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RecognitionResult(BaseModel):
    """手写识别结果模型"""

    recognized_text: str
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    alternatives: List[str] = Field(default_factory=list)
    bounding_box: Dict[str, float] = Field(
        default_factory=dict
    )  # {"x": float, "y": float, "width": float, "height": float}
    processing_time: float = 0.0  # 毫秒


class WhiteboardExportOptions(BaseModel):
    """白板导出选项"""

    format: str = "png"  # "png", "jpg", "pdf", "svg"
    quality: int = Field(default=90, ge=1, le=100)  # JPEG质量
    include_background: bool = True
    dpi: int = Field(default=300, ge=72, le=1200)
    page_range: Optional[Tuple[int, int]] = None  # (start_page, end_page)


# 默认工具配置
DEFAULT_TOOLS = {
    "pen": {
        "type": StrokeType.PEN,
        "color": WhiteboardColor.BLACK,
        "width": 2.0,
        "opacity": 1.0,
    },
    "marker": {
        "type": StrokeType.MARKER,
        "color": WhiteboardColor.BLUE,
        "width": 5.0,
        "opacity": 0.8,
    },
    "highlighter": {
        "type": StrokeType.HIGHLIGHTER,
        "color": WhiteboardColor.YELLOW,
        "width": 10.0,
        "opacity": 0.3,
    },
    "eraser": {
        "type": StrokeType.ERASER,
        "color": WhiteboardColor.WHITE,
        "width": 20.0,
        "opacity": 1.0,
    },
}


class UserPresence(BaseModel):
    """用户在线状态"""

    user_id: int
    username: str
    cursor_position: Optional[Point] = None
    current_tool: ToolType = ToolType.STROKE
    is_typing: bool = False
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class WhiteboardStatistics(BaseModel):
    """白板统计信息"""

    total_strokes: int = 0
    total_shapes: int = 0
    total_text_elements: int = 0
    total_pages: int = 1
    session_duration: float = 0.0  # 分钟
    participant_count: int = 1
    average_stroke_length: float = 0.0
    most_used_color: Optional[WhiteboardColor] = None
