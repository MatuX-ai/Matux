"""
VR代码编辑器核心类
管理VR环境中的代码编辑功能
"""

from datetime import datetime
import logging
from typing import Callable, Dict, List, Optional
import uuid

from .models import (
    CodeFile,
    CodeLanguage,
    VREditorConfig,
    VREditorSession,
    VREditorState,
    VRRenderingStats,
)

logger = logging.getLogger(__name__)


class VREditorCore:
    """VR代码编辑器核心类"""

    def __init__(self, config: Optional[VREditorConfig] = None):
        """
        初始化VR编辑器核心

        Args:
            config: 编辑器配置
        """
        self.config = config or VREditorConfig()
        self.session: Optional[VREditorSession] = None
        self.state = VREditorState()
        self.rendering_stats = VRRenderingStats()

        # 文件管理
        self.opened_files: Dict[str, CodeFile] = {}
        self.file_versions: Dict[str, int] = {}

        # 回调函数
        self.state_change_callback: Optional[Callable[[VREditorState], None]] = None
        self.file_change_callback: Optional[Callable[[CodeFile], None]] = None
        self.render_callback: Optional[Callable[[], None]] = None

        # VR组件引用（将在初始化时设置）
        self.vr_renderer = None
        self.input_handler = None
        self.ui_components = None

        logger.info("VREditorCore初始化完成")

    def initialize_session(
        self, user_id: Optional[int] = None, device_id: str = "default_vr_device"
    ) -> str:
        """
        初始化编辑器会话

        Args:
            user_id: 用户ID
            device_id: 设备ID

        Returns:
            str: 会话ID
        """
        session_id = str(uuid.uuid4())

        self.session = VREditorSession(
            session_id=session_id,
            user_id=user_id,
            device_id=device_id,
            config=self.config,
            state=self.state,
        )

        logger.info(f"VR编辑器会话初始化: {session_id}")
        return session_id

    def open_file(
        self,
        file_path: str,
        content: str = "",
        language: CodeLanguage = CodeLanguage.PYTHON,
    ) -> str:
        """
        打开文件

        Args:
            file_path: 文件路径
            content: 文件内容
            language: 编程语言

        Returns:
            str: 文件ID
        """
        if not self.session:
            raise RuntimeError("编辑器会话未初始化")

        file_id = str(uuid.uuid4())
        file_name = file_path.split("/")[-1]

        code_file = CodeFile(
            id=file_id,
            name=file_name,
            path=file_path,
            content=content,
            language=language,
            size=len(content.encode("utf-8")),
        )

        self.opened_files[file_id] = code_file
        self.file_versions[file_id] = 1
        self.session.opened_files.append(code_file)
        self.session.active_file_id = file_id
        self.session.state.current_file = file_path

        logger.info(f"文件已打开: {file_path}")

        # 触发文件变更回调
        if self.file_change_callback:
            try:
                self.file_change_callback(code_file)
            except Exception as e:
                logger.error(f"文件变更回调执行失败: {e}")

        return file_id

    def close_file(self, file_id: str) -> bool:
        """
        关闭文件

        Args:
            file_id: 文件ID

        Returns:
            bool: 是否成功关闭
        """
        if file_id not in self.opened_files:
            return False

        # 从打开文件列表中移除
        del self.opened_files[file_id]
        del self.file_versions[file_id]

        # 从会话中移除
        self.session.opened_files = [
            f for f in self.session.opened_files if f.id != file_id
        ]

        # 如果关闭的是当前活动文件，切换到下一个文件
        if self.session.active_file_id == file_id:
            if self.session.opened_files:
                self.session.active_file_id = self.session.opened_files[0].id
                self.session.state.current_file = self.session.opened_files[0].path
            else:
                self.session.active_file_id = None
                self.session.state.current_file = None

        logger.info(f"文件已关闭: {file_id}")
        return True

    def update_file_content(
        self, file_id: str, content: str, cursor_line: int = 0, cursor_column: int = 0
    ) -> bool:
        """
        更新文件内容

        Args:
            file_id: 文件ID
            content: 新内容
            cursor_line: 光标行号
            cursor_column: 光标列号

        Returns:
            bool: 是否更新成功
        """
        if file_id not in self.opened_files:
            return False

        file_obj = self.opened_files[file_id]
        file_obj.content

        # 更新文件内容
        file_obj.content = content
        file_obj.size = len(content.encode("utf-8"))
        file_obj.modified_at = datetime.utcnow()
        file_obj.version += 1

        # 更新光标位置
        self.session.state.cursor_position = {
            "line": cursor_line,
            "column": cursor_column,
        }

        # 更新文件版本
        self.file_versions[file_id] = file_obj.version

        logger.debug(f"文件内容已更新: {file_id} (版本: {file_obj.version})")

        # 触发文件变更回调
        if self.file_change_callback:
            try:
                self.file_change_callback(file_obj)
            except Exception as e:
                logger.error(f"文件变更回调执行失败: {e}")

        return True

    def get_active_file(self) -> Optional[CodeFile]:
        """获取当前活动文件"""
        if not self.session or not self.session.active_file_id:
            return None

        return self.opened_files.get(self.session.active_file_id)

    def set_cursor_position(self, line: int, column: int):
        """设置光标位置"""
        if self.session:
            self.session.state.cursor_position = {"line": line, "column": column}
            self._trigger_state_change()

    def move_cursor(self, delta_line: int, delta_column: int):
        """移动光标"""
        if self.session:
            current_pos = self.session.state.cursor_position
            new_line = max(0, current_pos["line"] + delta_line)
            new_column = max(0, current_pos["column"] + delta_column)

            self.set_cursor_position(new_line, new_column)

    def set_zoom_level(self, zoom: float):
        """设置缩放级别"""
        if self.session:
            self.session.state.zoom_level = max(0.5, min(3.0, zoom))
            self._trigger_state_change()

    def update_vr_state(
        self,
        head_position: Dict[str, float],
        head_rotation: Dict[str, float],
        left_controller: Optional[Dict] = None,
        right_controller: Optional[Dict] = None,
    ):
        """
        更新VR状态

        Args:
            head_position: 头部位置
            head_rotation: 头部旋转
            left_controller: 左控制器状态
            right_controller: 右控制器状态
        """
        if self.session:
            self.session.state.head_position = head_position
            self.session.state.head_rotation = head_rotation
            self.session.state.left_controller = left_controller
            self.session.state.right_controller = right_controller

            self._trigger_state_change()

    def set_state_change_callback(self, callback: Callable[[VREditorState], None]):
        """设置状态变更回调"""
        self.state_change_callback = callback

    def set_file_change_callback(self, callback: Callable[[CodeFile], None]):
        """设置文件变更回调"""
        self.file_change_callback = callback

    def set_render_callback(self, callback: Callable[[], None]):
        """设置渲染回调"""
        self.render_callback = callback

    def _trigger_state_change(self):
        """触发状态变更"""
        if self.state_change_callback and self.session:
            try:
                self.state_change_callback(self.session.state)
            except Exception as e:
                logger.error(f"状态变更回调执行失败: {e}")

    def trigger_render(self):
        """触渲染"""
        if self.render_callback:
            try:
                self.render_callback()
            except Exception as e:
                logger.error(f"渲染回调执行失败: {e}")

    def get_session_info(self) -> Optional[VREditorSession]:
        """获取会话信息"""
        return self.session

    def get_rendering_stats(self) -> VRRenderingStats:
        """获取渲染统计信息"""
        return self.rendering_stats

    def update_rendering_stats(
        self, fps: float, frame_time: float, draw_calls: int, triangles: int
    ):
        """更新渲染统计"""
        self.rendering_stats.fps = fps
        self.rendering_stats.frame_time = frame_time
        self.rendering_stats.draw_calls = draw_calls
        self.rendering_stats.triangles_rendered = triangles
        self.rendering_stats.last_updated = datetime.utcnow()

    def save_session(self) -> Dict:
        """保存会话状态"""
        if not self.session:
            return {}

        return {
            "session_id": self.session.session_id,
            "config": self.session.config.dict(),
            "state": self.session.state.dict(),
            "opened_files": [f.dict() for f in self.session.opened_files],
            "active_file_id": self.session.active_file_id,
        }

    def restore_session(self, session_data: Dict) -> bool:
        """恢复会话状态"""
        try:
            # 恢复基本会话信息
            self.session = VREditorSession(**session_data)
            self.state = self.session.state

            # 恢复打开的文件
            self.opened_files = {
                f.id: CodeFile(**f.dict()) for f in session_data.get("opened_files", [])
            }

            logger.info(f"会话已恢复: {session_data.get('session_id')}")
            return True

        except Exception as e:
            logger.error(f"恢复会话失败: {e}")
            return False

    def close_session(self):
        """关闭会话"""
        if self.session:
            self.session.is_active = False
            self.session.last_activity = datetime.utcnow()
            logger.info(f"编辑器会话已关闭: {self.session.session_id}")

        self.session = None
        self.opened_files.clear()
        self.file_versions.clear()

    def get_supported_languages(self) -> List[str]:
        """获取支持的编程语言"""
        return [lang.value for lang in CodeLanguage]

    def change_language(self, language: CodeLanguage):
        """更改当前语言"""
        if self.session:
            self.session.config.language = language
            active_file = self.get_active_file()
            if active_file:
                active_file.language = language
            self._trigger_state_change()
