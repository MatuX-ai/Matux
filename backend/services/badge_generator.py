"""
徽章生成服务
负责生成SVG格式的认证徽章
"""

from datetime import datetime
from typing import Optional

from models.hardware_certification import BadgeConfig, BadgeStyle, CertificationStatus
from utils.logger import setup_logger

logger = setup_logger("INFO")


class BadgeGenerator:
    """徽章生成器"""

    def __init__(self):
        self._status_colors = {
            CertificationStatus.CERTIFIED: "#4CAF50",  # 绿色
            CertificationStatus.FAILED: "#F44336",  # 红色
            CertificationStatus.PENDING: "#FFC107",  # 黄色
            CertificationStatus.EXPIRED: "#9E9E9E",  # 灰色
        }

        self._status_labels = {
            CertificationStatus.CERTIFIED: "CERTIFIED",
            CertificationStatus.FAILED: "FAILED",
            CertificationStatus.PENDING: "PENDING",
            CertificationStatus.EXPIRED: "EXPIRED",
        }

    def generate_badge_svg(
        self,
        hw_id: str,
        status: CertificationStatus,
        config: BadgeConfig,
        firmware_version: Optional[str] = None,
        certified_at: Optional[datetime] = None,
    ) -> str:
        """
        生成SVG徽章

        Args:
            hw_id: 硬件ID
            status: 认证状态
            config: 徽章配置
            firmware_version: 固件版本（可选）
            certified_at: 认证时间（可选）

        Returns:
            str: SVG徽章内容
        """
        try:
            # 根据样式选择生成方法
            if config.style == BadgeStyle.COMPACT:
                return self._generate_compact_badge(hw_id, status, config)
            elif config.style == BadgeStyle.DETAILED:
                return self._generate_detailed_badge(
                    hw_id, status, config, firmware_version, certified_at
                )
            else:
                return self._generate_standard_badge(
                    hw_id, status, config, firmware_version, certified_at
                )

        except Exception as e:
            logger.error(f"生成徽章失败: {str(e)}")
            return self._generate_error_badge(str(e))

    def _generate_standard_badge(
        self,
        hw_id: str,
        status: CertificationStatus,
        config: BadgeConfig,
        firmware_version: Optional[str] = None,
        certified_at: Optional[datetime] = None,
    ) -> str:
        """生成标准样式徽章"""
        color = self._status_colors.get(status, "#9E9E9E")
        label = self._status_labels.get(status, "UNKNOWN")

        # 构建徽章文本
        badge_text = f"HW:{hw_id[:8]}"
        if config.show_version and firmware_version:
            badge_text += f" v{firmware_version}"

        status_text = label

        # 计算宽度
        left_width = self._calculate_text_width(badge_text) + 20
        right_width = self._calculate_text_width(status_text) + 20
        total_width = left_width + right_width

        # 添加时间戳
        timestamp_text = ""
        if config.show_timestamp and certified_at:
            timestamp_text = certified_at.strftime("%Y-%m-%d")
            timestamp_width = self._calculate_text_width(timestamp_text) + 10
            total_width += timestamp_width

        svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="40" viewBox="0 0 {total_width} 40">
  <style>
    .label {{ font: bold 11px sans-serif; fill: #fff; }}
    .status {{ font: bold 11px sans-serif; fill: #fff; }}
    .timestamp {{ font: 10px sans-serif; fill: #666; }}
  </style>
  
  <!-- 左侧背景 -->
  <rect x="0" y="0" width="{left_width}" height="20" fill="#555" rx="3" ry="3"/>
  <rect x="0" y="20" width="{left_width}" height="20" fill="#444" rx="3" ry="3"/>
  
  <!-- 右侧背景 -->
  <rect x="{left_width}" y="0" width="{right_width}" height="40" fill="{color}" rx="3" ry="3"/>
  
  <!-- 文本 -->
  <text x="10" y="14" class="label">{badge_text}</text>
  <text x="10" y="34" class="label">认证徽章</text>
  <text x="{left_width + 10}" y="25" class="status">{status_text}</text>
"""

        # 添加时间戳
        if timestamp_text:
            svg += f"""  <!-- 时间戳 -->
  <rect x="{left_width + right_width}" y="0" width="{timestamp_width}" height="40" fill="#f8f8f8" rx="3" ry="3" stroke="#ddd"/>
  <text x="{left_width + right_width + 5}" y="20" class="timestamp">{timestamp_text}</text>
"""

        svg += "</svg>"
        return svg

    def _generate_compact_badge(
        self, hw_id: str, status: CertificationStatus, config: BadgeConfig
    ) -> str:
        """生成紧凑样式徽章"""
        color = self._status_colors.get(status, "#9E9E9E")
        label = self._status_labels.get(status, "UNKNOWN")

        # 紧凑版本只显示状态
        badge_text = label
        width = self._calculate_text_width(badge_text) + 20

        svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" viewBox="0 0 {width} 20">
  <style>
    .text {{ font: bold 11px sans-serif; fill: #fff; }}
  </style>
  <rect width="{width}" height="20" fill="{color}" rx="3" ry="3"/>
  <text x="{width/2}" y="14" class="text" text-anchor="middle">{badge_text}</text>
</svg>"""

        return svg

    def _generate_detailed_badge(
        self,
        hw_id: str,
        status: CertificationStatus,
        config: BadgeConfig,
        firmware_version: Optional[str] = None,
        certified_at: Optional[datetime] = None,
    ) -> str:
        """生成详细样式徽章"""
        color = self._status_colors.get(status, "#9E9E9E")
        label = self._status_labels.get(status, "UNKNOWN")

        # 详细信息
        lines = [f"Hardware: {hw_id[:12]}"]
        if config.show_version and firmware_version:
            lines.append(f"Firmware: v{firmware_version}")
        lines.append(f"Status: {label}")

        if config.show_timestamp and certified_at:
            lines.append(f"Date: {certified_at.strftime('%Y-%m-%d')}")

        # 计算尺寸
        max_width = max(self._calculate_text_width(line) for line in lines)
        width = max_width + 20
        height = len(lines) * 18 + 10
        line_height = 18

        svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <style>
    .text {{ font: 12px sans-serif; fill: #333; }}
    .title {{ font: bold 12px sans-serif; fill: #fff; }}
  </style>
  <!-- 背景 -->
  <rect width="{width}" height="{height}" fill="#f8f8f8" rx="5" ry="5" stroke="#ddd"/>
  
  <!-- 标题栏 -->
  <rect width="{width}" height="25" fill="{color}" rx="5" ry="5"/>
  <text x="{width/2}" y="17" class="title" text-anchor="middle">认证徽章</text>
"""

        # 添加文本行
        for i, line in enumerate(lines):
            y_pos = 40 + i * line_height
            svg += f'  <text x="10" y="{y_pos}" class="text">{line}</text>\n'

        svg += "</svg>"
        return svg

    def _calculate_text_width(self, text: str) -> int:
        """
        估算文本宽度（简化计算）

        Args:
            text: 文本内容

        Returns:
            int: 估算宽度
        """
        # 简单的字符宽度估算
        width = 0
        for char in text:
            if char.isascii() and char.isalnum():
                width += 7  # 数字和英文字母
            elif char in [" ", "-", "_", "."]:
                width += 4  # 空格和标点
            else:
                width += 10  # 中文等宽字符
        return width

    def _generate_error_badge(self, error_message: str) -> str:
        """生成错误徽章"""
        error_text = "ERROR"
        width = self._calculate_text_width(error_text) + 20

        return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" viewBox="0 0 {width} 20">
  <style>
    .text {{ font: bold 11px sans-serif; fill: #fff; }}
  </style>
  <rect width="{width}" height="20" fill="#F44336" rx="3" ry="3"/>
  <text x="{width/2}" y="14" class="text" text-anchor="middle">{error_text}</text>
</svg>"""

    def get_badge_url_template(self) -> str:
        """
        获取徽章URL模板

        Returns:
            str: URL模板
        """
        return "https://badges.imatuproject.org/cert/{hw_id}.svg"


# 单例实例
badge_generator = BadgeGenerator()
