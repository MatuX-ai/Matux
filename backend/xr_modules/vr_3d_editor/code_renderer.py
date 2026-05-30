"""
代码渲染器
负责在VR环境中渲染代码内容
"""

import logging
from typing import Dict, List, Tuple

from .models import CodeFile, CodeLanguage, EditorTheme, VREditorConfig

logger = logging.getLogger(__name__)


class CodeRenderer:
    """代码渲染器类"""

    def __init__(self, config: VREditorConfig):
        """
        初始化代码渲染器

        Args:
            config: 编辑器配置
        """
        self.config = config

        # 主题颜色配置
        self.themes = {
            EditorTheme.DARK: {
                "background": (0.1, 0.1, 0.1, 1.0),
                "text": (1.0, 1.0, 1.0, 1.0),
                "keyword": (0.67, 0.83, 0.47, 1.0),
                "string": (0.82, 0.47, 0.47, 1.0),
                "comment": (0.5, 0.5, 0.5, 1.0),
                "number": (0.92, 0.67, 0.47, 1.0),
                "operator": (0.8, 0.8, 0.8, 1.0),
                "line_numbers": (0.4, 0.4, 0.4, 1.0),
            },
            EditorTheme.LIGHT: {
                "background": (1.0, 1.0, 1.0, 1.0),
                "text": (0.0, 0.0, 0.0, 1.0),
                "keyword": (0.0, 0.0, 0.8, 1.0),
                "string": (0.8, 0.0, 0.0, 1.0),
                "comment": (0.5, 0.5, 0.5, 1.0),
                "number": (0.8, 0.4, 0.0, 1.0),
                "operator": (0.3, 0.3, 0.3, 1.0),
                "line_numbers": (0.7, 0.7, 0.7, 1.0),
            },
        }

        # 语法高亮规则
        self.syntax_rules = {
            CodeLanguage.PYTHON: {
                "keywords": [
                    "def",
                    "class",
                    "import",
                    "from",
                    "if",
                    "else",
                    "elif",
                    "for",
                    "while",
                    "try",
                    "except",
                    "finally",
                    "with",
                    "as",
                    "return",
                    "yield",
                    "lambda",
                    "and",
                    "or",
                    "not",
                    "in",
                    "is",
                ],
                "builtins": [
                    "print",
                    "len",
                    "range",
                    "enumerate",
                    "zip",
                    "map",
                    "filter",
                ],
                "decorators": ["@", "@property", "@staticmethod", "@classmethod"],
            },
            CodeLanguage.JAVASCRIPT: {
                "keywords": [
                    "function",
                    "const",
                    "let",
                    "var",
                    "if",
                    "else",
                    "for",
                    "while",
                    "try",
                    "catch",
                    "finally",
                    "return",
                    "break",
                    "continue",
                    "switch",
                    "case",
                    "default",
                    "new",
                    "this",
                    "typeof",
                    "instanceof",
                    "await",
                    "async",
                ],
                "builtins": [
                    "console",
                    "window",
                    "document",
                    "Array",
                    "Object",
                    "String",
                ],
                "globals": ["undefined", "null", "true", "false"],
            },
        }

        # 字体和布局参数
        self.char_width = 0.1
        self.line_height = 0.15
        self.padding = 0.2

        logger.info("CodeRenderer初始化完成")

    def render_code_panel(
        self,
        code_file: CodeFile,
        position: Tuple[float, float, float] = (0, 0, 0),
        rotation: Tuple[float, float, float] = (0, 0, 0),
    ) -> List[Dict]:
        """
        渲染代码面板

        Args:
            code_file: 代码文件
            position: 面板位置
            rotation: 面板旋转

        Returns:
            List[Dict]: 渲染元素列表
        """
        try:
            render_elements = []

            # 获取当前主题
            theme = self.themes.get(self.config.theme, self.themes[EditorTheme.DARK])

            # 计算面板尺寸
            panel_width = self.config.panel_width
            panel_height = self.config.panel_height

            # 渲染背景面板
            background_element = {
                "type": "panel",
                "position": position,
                "rotation": rotation,
                "scale": (panel_width, panel_height, 0.01),
                "color": theme["background"],
                "material": "standard",
            }
            render_elements.append(background_element)

            # 分割代码行
            lines = code_file.content.split("\n")

            # 计算可显示的行数
            max_lines = int((panel_height - 2 * self.padding) / self.line_height)
            start_line = 0  # TODO: 根据滚动位置计算

            # 渲染可见行
            visible_lines = lines[start_line : start_line + max_lines]

            for i, line in enumerate(visible_lines):
                y_offset = panel_height / 2 - self.padding - i * self.line_height

                # 渲染行号
                if self.config.line_numbers:
                    line_number_element = self._render_line_number(
                        start_line + i + 1,
                        (
                            position[0] - panel_width / 2 + self.padding,
                            position[1] + y_offset,
                            position[2] + 0.01,
                        ),
                        theme["line_numbers"],
                    )
                    render_elements.append(line_number_element)

                # 渲染代码行
                code_elements = self._render_code_line(
                    line,
                    code_file.language,
                    (
                        position[0]
                        - panel_width / 2
                        + self.padding
                        + (2 if self.config.line_numbers else 0) * self.char_width,
                        position[1] + y_offset,
                        position[2] + 0.01,
                    ),
                    theme,
                )
                render_elements.extend(code_elements)

            # 渲染光标
            cursor_elements = self._render_cursor(position, theme)
            render_elements.extend(cursor_elements)

            return render_elements

        except Exception as e:
            logger.error(f"代码面板渲染失败: {e}")
            return []

    def _render_line_number(
        self,
        line_number: int,
        position: Tuple[float, float, float],
        color: Tuple[float, float, float, float],
    ) -> Dict:
        """渲染行号"""
        return {
            "type": "text",
            "content": str(line_number),
            "position": position,
            "color": color,
            "font_size": self.config.font_size * 0.8,
            "align": "right",
        }

    def _render_code_line(
        self,
        line: str,
        language: CodeLanguage,
        position: Tuple[float, float, float],
        theme: Dict,
    ) -> List[Dict]:
        """渲染代码行"""
        elements = []
        x_offset = 0

        # 简单的语法高亮（实际应用中需要更复杂的词法分析）
        tokens = self._tokenize_line(line, language)

        for token_type, token_text in tokens:
            color = self._get_token_color(token_type, theme)

            text_element = {
                "type": "text",
                "content": token_text,
                "position": (position[0] + x_offset, position[1], position[2]),
                "color": color,
                "font_size": self.config.font_size,
                "word_wrap": self.config.word_wrap,
            }

            elements.append(text_element)
            x_offset += len(token_text) * self.char_width

        return elements

    def _tokenize_line(
        self, line: str, language: CodeLanguage
    ) -> List[Tuple[str, str]]:
        """简单的行分词（实际应用中需要专业的词法分析器）"""
        if language not in self.syntax_rules:
            return [("text", line)]

        rules = self.syntax_rules[language]
        tokens = []
        current_token = ""
        i = 0

        while i < len(line):
            char = line[i]

            # 处理字符串
            if char in ['"', "'"]:
                if current_token:
                    tokens.append(("text", current_token))
                    current_token = ""

                quote = char
                string_content = quote
                i += 1

                while i < len(line) and line[i] != quote:
                    if line[i] == "\\" and i + 1 < len(line):
                        string_content += line[i : i + 2]
                        i += 2
                    else:
                        string_content += line[i]
                        i += 1

                if i < len(line):
                    string_content += quote
                    i += 1

                tokens.append(("string", string_content))
                continue

            # 处理注释
            if char == "#" or (
                language == CodeLanguage.JAVASCRIPT
                and i + 1 < len(line)
                and line[i : i + 2] == "//"
            ):
                if current_token:
                    tokens.append(("text", current_token))
                    current_token = ""

                if char == "#":
                    comment = line[i:]
                    i = len(line)
                else:
                    comment = line[i:]
                    i = len(line)

                tokens.append(("comment", comment))
                break

            # 处理数字
            if char.isdigit():
                if current_token:
                    tokens.append(("text", current_token))
                    current_token = ""

                number = char
                i += 1

                while i < len(line) and (line[i].isdigit() or line[i] == "."):
                    number += line[i]
                    i += 1

                tokens.append(("number", number))
                continue

            # 处理关键字和标识符
            if char.isalpha() or char == "_":
                identifier = char
                i += 1

                while i < len(line) and (line[i].isalnum() or line[i] == "_"):
                    identifier += line[i]
                    i += 1

                # 判断标识符类型
                if identifier in rules.get("keywords", []):
                    token_type = "keyword"
                elif identifier in rules.get("builtins", []):
                    token_type = "builtin"
                else:
                    token_type = "identifier"

                tokens.append((token_type, identifier))
                continue

            # 处理操作符
            if char in "+-*/=<>!&|%^~":
                if current_token:
                    tokens.append(("text", current_token))
                    current_token = ""

                operator = char
                i += 1

                # 处理双字符操作符
                if i < len(line) and line[i] in "=<>+-":
                    operator += line[i]
                    i += 1

                tokens.append(("operator", operator))
                continue

            # 普通字符
            current_token += char
            i += 1

        # 添加剩余的令牌
        if current_token:
            tokens.append(("text", current_token))

        return tokens

    def _get_token_color(
        self, token_type: str, theme: Dict
    ) -> Tuple[float, float, float, float]:
        """获取令牌颜色"""
        color_map = {
            "keyword": "keyword",
            "builtin": "keyword",
            "string": "string",
            "comment": "comment",
            "number": "number",
            "operator": "operator",
        }

        color_key = color_map.get(token_type, "text")
        return theme.get(color_key, theme["text"])

    def _render_cursor(
        self, panel_position: Tuple[float, float, float], theme: Dict
    ) -> List[Dict]:
        """渲染光标"""
        # TODO: 根据实际光标位置计算坐标
        cursor_elements = []

        cursor_element = {
            "type": "rectangle",
            "position": (
                panel_position[0],
                panel_position[1],
                panel_position[2] + 0.02,
            ),
            "scale": (0.02, self.line_height * 0.8, 0.01),
            "color": theme["text"],
            "material": "standard",
        }
        cursor_elements.append(cursor_element)

        return cursor_elements

    def update_theme(self, theme: EditorTheme):
        """更新主题"""
        self.config.theme = theme
        logger.info(f"渲染器主题已更新: {theme}")

    def calculate_text_bounds(self, text: str) -> Tuple[float, float]:
        """计算文本边界"""
        width = len(text) * self.char_width
        height = self.line_height
        return (width, height)

    def get_syntax_highlight_info(self, language: CodeLanguage) -> Dict:
        """获取语法高亮信息"""
        if language in self.syntax_rules:
            return self.syntax_rules[language]
        return {}
