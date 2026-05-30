"""
VR代码编辑器数据模型
定义VR编辑器相关的数据结构和配置
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EditorTheme(str, Enum):
    """编辑器主题"""

    DARK = "dark"
    LIGHT = "light"
    MATRIX = "matrix"
    OCEAN = "ocean"
    SPACE = "space"


class CodeLanguage(str, Enum):
    """编程语言"""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    CSHARP = "csharp"
    GO = "go"
    RUST = "rust"
    HTML = "html"
    CSS = "css"
    SQL = "sql"


class VRInteractionMode(str, Enum):
    """VR交互模式"""

    HAND_TRACKING = "hand_tracking"  # 手势追踪
    CONTROLLER = "controller"  # 控制器操作
    GAZE_SELECTION = "gaze_selection"  # 注视选择
    VOICE_COMMAND = "voice_command"  # 语音命令


class EditorLayout(str, Enum):
    """编辑器布局模式"""

    SINGLE_PANEL = "single_panel"  # 单面板
    DUAL_PANEL = "dual_panel"  # 双面板
    GRID_LAYOUT = "grid_layout"  # 网格布局
    SPHERICAL = "spherical"  # 球形布局


class CodeBlock(BaseModel):
    """代码块模型"""

    id: str
    content: str
    language: CodeLanguage
    line_start: int
    line_end: int
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    rotation: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    scale: Dict[str, float] = Field(default_factory=lambda: {"x": 1, "y": 1, "z": 1})


class VREditorConfig(BaseModel):
    """VR编辑器配置模型"""

    # 基本设置
    theme: EditorTheme = EditorTheme.DARK
    language: CodeLanguage = CodeLanguage.PYTHON
    font_size: int = Field(default=16, ge=12, le=32)
    line_numbers: bool = True
    word_wrap: bool = True

    # VR设置
    interaction_mode: VRInteractionMode = VRInteractionMode.HAND_TRACKING
    layout_mode: EditorLayout = EditorLayout.SPHERICAL
    render_distance: float = Field(default=5.0, ge=2.0, le=20.0)
    movement_speed: float = Field(default=2.0, ge=0.5, le=10.0)

    # 显示设置
    panel_width: float = Field(default=3.0, ge=1.0, le=10.0)
    panel_height: float = Field(default=2.0, ge=1.0, le=8.0)
    panel_spacing: float = Field(default=1.5, ge=0.5, le=5.0)

    # 功能设置
    auto_complete: bool = True
    syntax_highlighting: bool = True
    error_detection: bool = True
    collaboration_enabled: bool = False

    # 性能设置
    max_rendered_lines: int = Field(default=1000, ge=100, le=10000)
    update_frequency: int = Field(default=60, ge=30, le=120)  # FPS
    anti_aliasing: bool = True


class VREditorState(BaseModel):
    """VR编辑器状态模型"""

    # 编辑器状态
    current_file: Optional[str] = None
    cursor_position: Dict[str, int] = Field(
        default_factory=lambda: {"line": 0, "column": 0}
    )
    scroll_position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0})
    zoom_level: float = 1.0

    # VR状态
    head_position: Dict[str, float] = Field(
        default_factory=lambda: {"x": 0, "y": 0, "z": 0}
    )
    head_rotation: Dict[str, float] = Field(
        default_factory=lambda: {"x": 0, "y": 0, "z": 0}
    )
    left_controller: Optional[Dict[str, Any]] = None
    right_controller: Optional[Dict[str, Any]] = None

    # 交互状态
    selected_element: Optional[str] = None
    drag_active: bool = False
    hover_target: Optional[str] = None

    # 时间戳
    last_update: datetime = Field(default_factory=datetime.utcnow)


class CodeFile(BaseModel):
    """代码文件模型"""

    id: str
    name: str
    path: str
    content: str
    language: CodeLanguage
    size: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    modified_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1


class VREditorSession(BaseModel):
    """VR编辑器会话模型"""

    session_id: str
    user_id: Optional[int] = None
    device_id: str
    config: VREditorConfig
    state: VREditorState = VREditorState()
    opened_files: List[CodeFile] = []
    active_file_id: Optional[str] = None
    collaborators: List[int] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class VREditorAction(BaseModel):
    """VR编辑器操作模型"""

    action_id: str
    session_id: str
    action_type: str  # "cursor_move", "text_insert", "text_delete", "file_open", etc.
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[int] = None


class CollaborationEvent(BaseModel):
    """协作事件模型"""

    event_id: str
    session_id: str
    user_id: int
    event_type: str  # "user_join", "user_leave", "cursor_move", "text_change"
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class VRRenderingStats(BaseModel):
    """VR渲染统计"""

    fps: float = 0.0
    frame_time: float = 0.0  # ms
    draw_calls: int = 0
    triangles_rendered: int = 0
    texture_memory: int = 0  # bytes
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# 默认配置
DEFAULT_VR_EDITOR_CONFIG = VREditorConfig(
    theme=EditorTheme.DARK,
    language=CodeLanguage.PYTHON,
    font_size=16,
    line_numbers=True,
    word_wrap=True,
    interaction_mode=VRInteractionMode.HAND_TRACKING,
    layout_mode=EditorLayout.SPHERICAL,
    render_distance=5.0,
    movement_speed=2.0,
    panel_width=3.0,
    panel_height=2.0,
    panel_spacing=1.5,
    auto_complete=True,
    syntax_highlighting=True,
    error_detection=True,
    collaboration_enabled=False,
    max_rendered_lines=1000,
    update_frequency=60,
    anti_aliasing=True,
)


class LanguageSupport(BaseModel):
    """语言支持配置"""

    language: CodeLanguage
    extensions: List[str]
    syntax_rules: Dict[str, Any]  # 语法高亮规则
    auto_complete_triggers: List[str]
    snippet_templates: Dict[str, str]


# 支持的语言配置
LANGUAGE_CONFIGS = {
    CodeLanguage.PYTHON: LanguageSupport(
        language=CodeLanguage.PYTHON,
        extensions=[".py", ".pyw"],
        syntax_rules={
            "keywords": [
                "def",
                "class",
                "import",
                "from",
                "if",
                "else",
                "for",
                "while",
            ],
            "types": ["int", "str", "list", "dict", "tuple"],
            "operators": ["+", "-", "*", "/", "=", "==", "!=", "<", ">"],
        },
        auto_complete_triggers=[".", "(", ":"],
        snippet_templates={
            "class": "class {name}:\n    def __init__(self):\n        pass\n",
            "function": "def {name}():\n    pass\n",
        },
    ),
    CodeLanguage.JAVASCRIPT: LanguageSupport(
        language=CodeLanguage.JAVASCRIPT,
        extensions=[".js", ".jsx"],
        syntax_rules={
            "keywords": [
                "function",
                "const",
                "let",
                "var",
                "if",
                "else",
                "for",
                "while",
            ],
            "types": ["string", "number", "boolean", "object", "array"],
            "operators": ["+", "-", "*", "/", "=", "===", "!==", "<", ">"],
        },
        auto_complete_triggers=[".", "(", "{"],
        snippet_templates={
            "function": "function {name}() {\n    \n}\n",
            "arrow": "const {name} = () => {\n    \n};\n",
        },
    ),
}
