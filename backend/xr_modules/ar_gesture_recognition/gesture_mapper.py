"""
手势映射器
将识别的手势映射到具体的系统命令
"""

import logging
from typing import Dict, List, Optional

from .models import (
    DEFAULT_GESTURE_COMMANDS,
    ARGestureConfig,
    GestureCommandMapping,
    GestureEvent,
    GestureType,
)

logger = logging.getLogger(__name__)


class GestureMapper:
    """手势映射器类"""

    def __init__(self, config: ARGestureConfig):
        """
        初始化手势映射器

        Args:
            config: 手势识别配置
        """
        self.config = config
        self.custom_mappings = {
            mapping.gesture_type: mapping for mapping in config.gesture_mappings
        }

        # 合并默认映射和自定义映射
        self.mappings = self._merge_mappings()

        logger.info("GestureMapper初始化完成")

    def _merge_mappings(self) -> Dict[GestureType, GestureCommandMapping]:
        """
        合并默认映射和自定义映射

        Returns:
            Dict[GestureType, GestureCommandMapping]: 合并后的映射表
        """
        # 从默认映射开始
        merged = {mapping.gesture_type: mapping for mapping in DEFAULT_GESTURE_COMMANDS}

        # 用自定义映射覆盖默认映射
        for gesture_type, custom_mapping in self.custom_mappings.items():
            if custom_mapping.enabled:
                merged[gesture_type] = custom_mapping
            elif gesture_type in merged:
                # 如果自定义映射禁用了某个手势，则移除它
                del merged[gesture_type]

        return merged

    def map_gesture_to_command(self, gesture_event: GestureEvent) -> Optional[str]:
        """
        将手势事件映射到系统命令

        Args:
            gesture_event: 手势事件

        Returns:
            Optional[str]: 映射的命令，如果没有映射则返回None
        """
        try:
            gesture_type = gesture_event.gesture_result.gesture_type

            # 查找对应的映射
            if gesture_type in self.mappings:
                mapping = self.mappings[gesture_type]
                if mapping.enabled:
                    logger.info(f"手势映射: {gesture_type} -> {mapping.command}")
                    return mapping.command
                else:
                    logger.debug(f"手势映射已禁用: {gesture_type}")
            else:
                logger.debug(f"未找到手势映射: {gesture_type}")

            return None

        except Exception as e:
            logger.error(f"手势映射失败: {e}")
            return None

    def get_available_commands(self) -> List[Dict]:
        """
        获取可用的命令列表

        Returns:
            List[Dict]: 命令信息列表
        """
        commands = []
        for gesture_type, mapping in self.mappings.items():
            if mapping.enabled:
                commands.append(
                    {
                        "gesture_type": str(gesture_type),
                        "command": mapping.command,
                        "description": mapping.description,
                        "priority": mapping.priority,
                    }
                )

        # 按优先级排序
        commands.sort(key=lambda x: x["priority"], reverse=True)
        return commands

    def update_mapping(
        self,
        gesture_type: GestureType,
        command: str = None,
        description: str = None,
        enabled: bool = None,
        priority: int = None,
    ) -> bool:
        """
        更新手势映射

        Args:
            gesture_type: 手势类型
            command: 新命令
            description: 新描述
            enabled: 是否启用
            priority: 新优先级

        Returns:
            bool: 更新是否成功
        """
        try:
            if gesture_type not in self.mappings:
                # 创建新的映射
                if command is None or description is None:
                    return False

                new_mapping = GestureCommandMapping(
                    gesture_type=gesture_type,
                    command=command,
                    description=description,
                    enabled=enabled if enabled is not None else True,
                    priority=priority if priority is not None else 0,
                )
                self.mappings[gesture_type] = new_mapping
                self.custom_mappings[gesture_type] = new_mapping
            else:
                # 更新现有映射
                mapping = self.mappings[gesture_type]

                if command is not None:
                    mapping.command = command
                if description is not None:
                    mapping.description = description
                if enabled is not None:
                    mapping.enabled = enabled
                if priority is not None:
                    mapping.priority = priority

                # 同步更新自定义映射
                if gesture_type in self.custom_mappings:
                    self.custom_mappings[gesture_type] = mapping

            logger.info(f"手势映射已更新: {gesture_type}")
            return True

        except Exception as e:
            logger.error(f"更新手势映射失败: {e}")
            return False

    def remove_mapping(self, gesture_type: GestureType) -> bool:
        """
        移除手势映射

        Args:
            gesture_type: 手势类型

        Returns:
            bool: 移除是否成功
        """
        try:
            if gesture_type in self.mappings:
                del self.mappings[gesture_type]

            if gesture_type in self.custom_mappings:
                del self.custom_mappings[gesture_type]

            logger.info(f"手势映射已移除: {gesture_type}")
            return True

        except Exception as e:
            logger.error(f"移除手势映射失败: {e}")
            return False

    def reset_to_defaults(self):
        """重置为默认映射"""
        self.mappings = {
            mapping.gesture_type: mapping for mapping in DEFAULT_GESTURE_COMMANDS
        }
        self.custom_mappings.clear()
        logger.info("手势映射已重置为默认值")

    def get_mapping_stats(self) -> Dict:
        """
        获取映射统计信息

        Returns:
            Dict: 统计信息
        """
        total_mappings = len(self.mappings)
        enabled_mappings = len([m for m in self.mappings.values() if m.enabled])
        custom_mappings = len(self.custom_mappings)

        return {
            "total_mappings": total_mappings,
            "enabled_mappings": enabled_mappings,
            "custom_mappings": custom_mappings,
            "default_mappings": total_mappings - custom_mappings,
        }


# 全局默认手势命令映射表
GESTURE_COMMANDS = {
    "circle": "save_project",  # 画圆 - 保存项目
    "swipe_right": "next_step",  # 右滑 - 下一步
    "pinch_in": "zoom_in",  # 捏合 - 放大
    "fist": "confirm_action",  # 握拳 - 确认操作
    "palm": "cancel_action",  # 手掌 - 取消操作
    "thumb_up": "continue_process",  # 竖拇指 - 继续执行
    "victory": "complete_task",  # 胜利手势 - 完成任务
}
