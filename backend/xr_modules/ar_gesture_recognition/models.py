"""
AR手势识别数据模型
定义手势识别相关的数据结构和枚举类型
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class GestureType(str, Enum):
    """手势类型枚举"""

    CIRCLE = "circle"  # 画圆 - 保存项目
    SWIPE_RIGHT = "swipe_right"  # 右滑 - 下一步
    SWIPE_LEFT = "swipe_left"  # 左滑 - 上一步
    PINCH_IN = "pinch_in"  # 捏合 - 放大
    PINCH_OUT = "pinch_out"  # 展开 - 缩小
    FIST = "fist"  # 握拳 - 确认/选择
    PALM = "palm"  # 手掌 - 取消/停止
    THUMB_UP = "thumb_up"  # 竖拇指 - 赞同/继续
    THUMB_DOWN = "thumb_down"  # 竖食指 - 反对/暂停
    VICTORY = "victory"  # 胜利手势 - 完成/成功
    POINT = "point"  # 指向 - 选择对象
    OK_SIGN = "ok_sign"  # OK手势 - 确认操作
    ROCK_ON = "rock_on"  # 摇滚手势 - 激活功能
    SPIDERMAN = "spiderman"  # 蜘蛛侠手势 - 特殊功能
    UNKNOWN = "unknown"  # 未知手势


class HandSide(str, Enum):
    """手部方向枚举"""

    LEFT = "left"  # 左手
    RIGHT = "right"  # 右手
    BOTH = "both"  # 双手


class GestureCommandMapping(BaseModel):
    """手势与命令映射模型"""

    gesture_type: GestureType
    command: str
    description: str
    enabled: bool = True
    priority: int = 0  # 优先级，数值越大优先级越高


class HandLandmark(BaseModel):
    """手部关键点模型"""

    x: float  # 归一化坐标 (0-1)
    y: float  # 归一化坐标 (0-1)
    z: float  # 深度坐标
    visibility: float = 1.0


class HandDetectionResult(BaseModel):
    """手部检测结果模型"""

    hand_side: HandSide
    landmarks: List[HandLandmark]
    confidence: float
    bounding_box: Dict[
        str, float
    ]  # {'x': float, 'y': float, 'width': float, 'height': float}
    timestamp: datetime


class GestureRecognitionResult(BaseModel):
    """手势识别结果模型"""

    gesture_type: GestureType
    confidence: float
    hand_side: HandSide
    hand_detection: HandDetectionResult
    recognition_time: datetime
    frame_number: int


class GestureEvent(BaseModel):
    """手势事件模型"""

    event_id: str
    gesture_result: GestureRecognitionResult
    mapped_command: Optional[str] = None
    user_id: Optional[int] = None
    session_id: str
    device_id: str
    created_at: datetime


class ARGestureConfig(BaseModel):
    """AR手势识别配置模型"""

    # 检测参数
    min_detection_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    min_tracking_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # 手势识别参数
    gesture_timeout: float = Field(default=2.0, description="手势超时时间(秒)")
    gesture_cooldown: float = Field(default=0.5, description="手势冷却时间(秒)")
    continuous_gesture_threshold: int = Field(default=3, description="连续手势阈值")

    # 图像处理参数
    image_width: int = Field(default=640)
    image_height: int = Field(default=480)
    flip_horizontal: bool = Field(default=True)
    flip_vertical: bool = Field(default=False)

    # 启用的功能
    enable_multi_hand: bool = Field(default=True)
    enable_gesture_smoothing: bool = Field(default=True)
    enable_dynamic_threshold: bool = Field(default=True)

    # 自定义手势映射
    gesture_mappings: List[GestureCommandMapping] = Field(default_factory=list)


# 默认手势命令映射表
DEFAULT_GESTURE_COMMANDS = [
    GestureCommandMapping(
        gesture_type=GestureType.CIRCLE,
        command="save_project",
        description="保存当前项目",
        priority=10,
    ),
    GestureCommandMapping(
        gesture_type=GestureType.SWIPE_RIGHT,
        command="next_step",
        description="进入下一步",
        priority=8,
    ),
    GestureCommandMapping(
        gesture_type=GestureType.PINCH_IN,
        command="zoom_in",
        description="放大视图",
        priority=7,
    ),
    GestureCommandMapping(
        gesture_type=GestureType.FIST,
        command="confirm_action",
        description="确认当前操作",
        priority=9,
    ),
    GestureCommandMapping(
        gesture_type=GestureType.PALM,
        command="cancel_action",
        description="取消当前操作",
        priority=9,
    ),
    GestureCommandMapping(
        gesture_type=GestureType.THUMB_UP,
        command="continue_process",
        description="继续执行",
        priority=6,
    ),
    GestureCommandMapping(
        gesture_type=GestureType.VICTORY,
        command="complete_task",
        description="完成当前任务",
        priority=8,
    ),
]


class GestureStatistics(BaseModel):
    """手势统计信息模型"""

    total_gestures: int = 0
    gesture_counts: Dict[GestureType, int] = {}
    average_confidence: float = 0.0
    recognition_rate: float = 0.0
    average_response_time: float = 0.0
    most_used_gesture: Optional[GestureType] = None
    session_duration: float = 0.0
    start_time: datetime
    end_time: Optional[datetime] = None


class GestureSessionInfo(BaseModel):
    """手势会话信息模型"""

    session_id: str
    user_id: Optional[int] = None
    device_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    is_active: bool = True
    config: ARGestureConfig
    statistics: GestureStatistics = GestureStatistics(start_time=datetime.utcnow())
