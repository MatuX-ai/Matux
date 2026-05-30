"""
白板核心类
管理白板的基本功能和状态
"""

from datetime import datetime
import logging
from typing import Callable, Dict, List, Optional
import uuid

from .models import (
    Point,
    Shape,
    Stroke,
    StrokeType,
    TextElement,
    ToolType,
    WhiteboardColor,
    WhiteboardConfig,
    WhiteboardElement,
    WhiteboardPage,
    WhiteboardSession,
)

logger = logging.getLogger(__name__)


class WhiteboardCore:
    """白板核心类"""

    def __init__(self, config: Optional[WhiteboardConfig] = None):
        """
        初始化白板核心

        Args:
            config: 白板配置
        """
        self.config = config or WhiteboardConfig()
        self.session: Optional[WhiteboardSession] = None
        self.current_tool = ToolType.STROKE
        self.current_stroke: Optional[Stroke] = None
        self.current_shape: Optional[Shape] = None

        # 回调函数
        self.element_added_callback: Optional[Callable[[WhiteboardElement], None]] = (
            None
        )
        self.element_modified_callback: Optional[
            Callable[[WhiteboardElement], None]
        ] = None
        self.element_removed_callback: Optional[Callable[[str], None]] = None
        self.page_changed_callback: Optional[Callable[[int], None]] = None

        logger.info("WhiteboardCore初始化完成")

    def create_session(self, owner_id: int, board_name: str = "协作白板") -> str:
        """
        创建白板会话

        Args:
            owner_id: 创建者ID
            board_name: 白板名称

        Returns:
            str: 会话ID
        """
        session_id = str(uuid.uuid4())

        self.session = WhiteboardSession(
            session_id=session_id,
            board_name=board_name,
            owner_id=owner_id,
            participants=[owner_id],
        )

        logger.info(f"白板会话已创建: {session_id}")
        return session_id

    def join_session(self, session_id: str, user_id: int) -> bool:
        """
        加入白板会话

        Args:
            session_id: 会话ID
            user_id: 用户ID

        Returns:
            bool: 是否成功加入
        """
        if not self.session or self.session.session_id != session_id:
            logger.error("会话不存在或不匹配")
            return False

        if user_id not in self.session.participants:
            self.session.participants.append(user_id)
            self.session.last_activity = datetime.utcnow()
            logger.info(f"用户 {user_id} 已加入会话 {session_id}")

        return True

    def start_stroke(
        self,
        x: float,
        y: float,
        pressure: float = 1.0,
        stroke_type: StrokeType = None,
        color: WhiteboardColor = None,
        width: float = None,
        user_id: int = None,
    ) -> str:
        """
        开始绘制笔画

        Args:
            x: 起始X坐标
            y: 起始Y坐标
            pressure: 压感值
            stroke_type: 笔画类型
            color: 颜色
            width: 宽度
            user_id: 用户ID

        Returns:
            str: 笔画ID
        """
        if not self.session:
            raise RuntimeError("白板会话未初始化")

        # 使用默认值或传入值
        stroke_type = stroke_type or self.config.default_stroke_type
        color = color or self.config.default_color
        width = width or self.config.default_width

        # 创建新笔画
        self.current_stroke = Stroke(
            stroke_type=stroke_type, color=color, width=width, user_id=user_id
        )

        # 添加起始点
        start_point = Point(x=x, y=y, pressure=pressure)
        self.current_stroke.points.append(start_point)

        logger.debug(f"开始绘制笔画: {self.current_stroke.id}")
        return self.current_stroke.id

    def add_stroke_point(self, x: float, y: float, pressure: float = 1.0) -> bool:
        """
        添加笔画点

        Args:
            x: X坐标
            y: Y坐标
            pressure: 压感值

        Returns:
            bool: 是否成功添加
        """
        if not self.current_stroke:
            return False

        # 压缩点数据（减少冗余点）
        if self.config.compression_enabled and len(self.current_stroke.points) > 1:
            last_point = self.current_stroke.points[-1]
            distance = ((x - last_point.x) ** 2 + (y - last_point.y) ** 2) ** 0.5

            if distance < self.config.compression_threshold:
                # 更新最后一个点而不是添加新点
                self.current_stroke.points[-1] = Point(x=x, y=y, pressure=pressure)
                return True

        # 添加新点
        point = Point(x=x, y=y, pressure=pressure)
        self.current_stroke.points.append(point)

        # 限制最大点数
        if len(self.current_stroke.points) > self.config.max_stroke_points:
            self.current_stroke.points.pop(0)

        return True

    def end_stroke(self) -> Optional[WhiteboardElement]:
        """
        结束笔画绘制

        Returns:
            Optional[WhiteboardElement]: 创建的白板元素
        """
        if not self.current_stroke or len(self.current_stroke.points) < 2:
            self.current_stroke = None
            return None

        # 标记笔画完成
        self.current_stroke.is_complete = True
        self.current_stroke.created_at = datetime.utcnow()

        # 创建白板元素
        element = WhiteboardElement(
            id=self.current_stroke.id,
            element_type="stroke",
            data=self.current_stroke.dict(),
            user_id=self.current_stroke.user_id,
            created_at=datetime.utcnow(),
        )

        # 添加到当前页面
        current_page = self._get_current_page()
        if current_page:
            current_page.elements.append(element)
            current_page.modified_at = datetime.utcnow()

        # 触发回调
        if self.element_added_callback:
            try:
                self.element_added_callback(element)
            except Exception as e:
                logger.error(f"元素添加回调执行失败: {e}")

        logger.debug(f"笔画绘制完成: {self.current_stroke.id}")

        self.current_stroke
        self.current_stroke = None
        return element

    def add_shape(
        self,
        shape_type: str,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        user_id: int = None,
    ) -> str:
        """
        添加形状

        Args:
            shape_type: 形状类型
            start_x: 起始X坐标
            start_y: 起始Y坐标
            end_x: 结束X坐标
            end_y: 结束Y坐标
            user_id: 用户ID

        Returns:
            str: 形状ID
        """
        if not self.session:
            raise RuntimeError("白板会话未初始化")

        shape = Shape(
            shape_type=shape_type,
            stroke_type=self.config.default_stroke_type,
            color=self.config.default_color,
            stroke_width=self.config.default_width,
            start_point=Point(x=start_x, y=start_y),
            end_point=Point(x=end_x, y=end_y),
            user_id=user_id,
        )

        element = WhiteboardElement(
            id=shape.id,
            element_type="shape",
            data=shape.dict(),
            user_id=user_id,
            created_at=datetime.utcnow(),
        )

        # 添加到当前页面
        current_page = self._get_current_page()
        if current_page:
            current_page.elements.append(element)
            current_page.modified_at = datetime.utcnow()

        # 触发回调
        if self.element_added_callback:
            try:
                self.element_added_callback(element)
            except Exception as e:
                logger.error(f"元素添加回调执行失败: {e}")

        logger.debug(f"形状已添加: {shape.id}")
        return shape.id

    def add_text(self, x: float, y: float, content: str, user_id: int = None) -> str:
        """
        添加文本

        Args:
            x: X坐标
            y: Y坐标
            content: 文本内容
            user_id: 用户ID

        Returns:
            str: 文本元素ID
        """
        if not self.session:
            raise RuntimeError("白板会话未初始化")

        text_element = TextElement(
            content=content,
            position=Point(x=x, y=y),
            color=self.config.default_color,
            user_id=user_id,
        )

        element = WhiteboardElement(
            id=text_element.id,
            element_type="text",
            data=text_element.dict(),
            user_id=user_id,
            created_at=datetime.utcnow(),
        )

        # 添加到当前页面
        current_page = self._get_current_page()
        if current_page:
            current_page.elements.append(element)
            current_page.modified_at = datetime.utcnow()

        # 触发回调
        if self.element_added_callback:
            try:
                self.element_added_callback(element)
            except Exception as e:
                logger.error(f"元素添加回调执行失败: {e}")

        logger.debug(f"文本已添加: {text_element.id}")
        return text_element.id

    def modify_element(self, element_id: str, updates: Dict) -> bool:
        """
        修改元素属性

        Args:
            element_id: 元素ID
            updates: 更新数据

        Returns:
            bool: 是否修改成功
        """
        if not self.session:
            return False

        current_page = self._get_current_page()
        if not current_page:
            return False

        # 查找元素
        element = None
        for elem in current_page.elements:
            if elem.id == element_id:
                element = elem
                break

        if not element:
            return False

        # 更新元素数据
        element.data.update(updates)
        element.modified_at = datetime.utcnow()

        # 触发回调
        if self.element_modified_callback:
            try:
                self.element_modified_callback(element)
            except Exception as e:
                logger.error(f"元素修改回调执行失败: {e}")

        logger.debug(f"元素已修改: {element_id}")
        return True

    def remove_element(self, element_id: str) -> bool:
        """
        删除元素

        Args:
            element_id: 元素ID

        Returns:
            bool: 是否删除成功
        """
        if not self.session:
            return False

        current_page = self._get_current_page()
        if not current_page:
            return False

        # 查找并删除元素
        initial_length = len(current_page.elements)
        current_page.elements = [
            elem for elem in current_page.elements if elem.id != element_id
        ]

        removed = len(current_page.elements) < initial_length
        if removed:
            current_page.modified_at = datetime.utcnow()

            # 触发回调
            if self.element_removed_callback:
                try:
                    self.element_removed_callback(element_id)
                except Exception as e:
                    logger.error(f"元素删除回调执行失败: {e}")

            logger.debug(f"元素已删除: {element_id}")

        return removed

    def clear_page(self, page_number: int = None) -> bool:
        """
        清空页面

        Args:
            page_number: 页面编号，None表示当前页面

        Returns:
            bool: 是否清空成功
        """
        if not self.session:
            return False

        page_num = page_number if page_number is not None else self.session.current_page
        page = self._get_page(page_num)

        if not page:
            return False

        # 记录被删除的元素ID
        removed_ids = [elem.id for elem in page.elements]

        # 清空元素
        page.elements.clear()
        page.modified_at = datetime.utcnow()

        # 触发删除回调
        if self.element_removed_callback:
            for element_id in removed_ids:
                try:
                    self.element_removed_callback(element_id)
                except Exception as e:
                    logger.error(f"元素删除回调执行失败: {e}")

        logger.info(f"页面已清空: {page_num}")
        return True

    def add_page(self) -> int:
        """
        添加新页面

        Returns:
            int: 新页面编号
        """
        if not self.session:
            raise RuntimeError("白板会话未初始化")

        new_page_number = len(self.session.pages)
        new_page = WhiteboardPage(page_number=new_page_number)
        self.session.pages.append(new_page)
        self.session.modified_at = datetime.utcnow()

        logger.info(f"新页面已添加: {new_page_number}")
        return new_page_number

    def switch_page(self, page_number: int) -> bool:
        """
        切换页面

        Args:
            page_number: 目标页面编号

        Returns:
            bool: 是否切换成功
        """
        if not self.session:
            return False

        if 0 <= page_number < len(self.session.pages):
            old_page = self.session.current_page
            self.session.current_page = page_number
            self.session.last_activity = datetime.utcnow()

            # 触发页面切换回调
            if self.page_changed_callback:
                try:
                    self.page_changed_callback(page_number)
                except Exception as e:
                    logger.error(f"页面切换回调执行失败: {e}")

            logger.debug(f"页面已切换: {old_page} -> {page_number}")
            return True

        return False

    def _get_current_page(self) -> Optional[WhiteboardPage]:
        """获取当前页面"""
        if not self.session:
            return None
        return self._get_page(self.session.current_page)

    def _get_page(self, page_number: int) -> Optional[WhiteboardPage]:
        """获取指定页面"""
        if (
            not self.session
            or page_number < 0
            or page_number >= len(self.session.pages)
        ):
            return None
        return self.session.pages[page_number]

    def get_session_info(self) -> Optional[WhiteboardSession]:
        """获取会话信息"""
        return self.session

    def set_element_callbacks(
        self,
        added: Callable = None,
        modified: Callable = None,
        removed: Callable = None,
    ):
        """设置元素操作回调"""
        if added:
            self.element_added_callback = added
        if modified:
            self.element_modified_callback = modified
        if removed:
            self.element_removed_callback = removed

    def set_page_callback(self, callback: Callable[[int], None]):
        """设置页面切换回调"""
        self.page_changed_callback = callback

    def get_tool(self) -> ToolType:
        """获取当前工具"""
        return self.current_tool

    def set_tool(self, tool: ToolType):
        """设置当前工具"""
        self.current_tool = tool
        logger.debug(f"工具已设置: {tool}")

    def get_elements(self, page_number: int = None) -> List[WhiteboardElement]:
        """获取页面元素"""
        page = (
            self._get_page(page_number)
            if page_number is not None
            else self._get_current_page()
        )
        return page.elements if page else []

    def close_session(self):
        """关闭会话"""
        if self.session:
            self.session.is_active = False
            self.session.last_activity = datetime.utcnow()
            logger.info(f"白板会话已关闭: {self.session.session_id}")
        self.session = None
        self.current_stroke = None
        self.current_shape = None
