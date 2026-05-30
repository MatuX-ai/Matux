"""
语音纠错检测服务
专门用于检测用户通过语音指令进行的硬件连接纠错行为
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CorrectionType(str, Enum):
    """纠错类型枚举"""

    PIN_CONNECTION = "pin_connection"  # 引脚连接纠错
    COMPONENT_IDENTIFICATION = "component_identification"  # 元件识别纠错
    WIRING_SEQUENCE = "wiring_sequence"  # 接线顺序纠错
    CIRCUIT_CONFIGURATION = "circuit_configuration"  # 电路配置纠错
    GENERAL_CORRECTION = "general_correction"  # 一般性纠错


@dataclass
class PinConnectionCorrection:
    """引脚连接纠错数据"""

    pin_name: str  # 引脚名称 (如 D9, A0, SDA等)
    from_component: str  # 原始连接元件
    to_component: str  # 纠正后连接元件
    connection_type: str  # 连接类型 (input/output/power/ground)
    is_corrected: bool = False  # 是否已纠正


@dataclass
class VoiceCorrectionResult:
    """语音纠错检测结果"""

    correction_type: CorrectionType
    confidence: float  # 纠错置信度 (0-1)
    detected_corrections: List[Any]  # 检测到的纠错项
    accuracy_score: float  # 纠错准确度评分
    timestamp: float  # 检测时间戳
    raw_transcript: str  # 原始语音转录
    parsed_commands: List[str]  # 解析出的命令列表


class VoiceCorrectionDetector:
    """语音纠错检测器"""

    def __init__(self):
        # 引脚名称模式
        self.pin_patterns = [
            r"\b(D\d{1,2})\b",  # 数字引脚 D0-D53
            r"\b(A\d{1,2})\b",  # 模拟引脚 A0-A15
            r"\b(GPIO\d{1,2})\b",  # GPIO引脚
            r"\b(SDA|SCL)\b",  # I2C引脚
            r"\b(MOSI|MISO|SCK|CS)\b",  # SPI引脚
            r"\b(RX|TX)\b",  # 串口引脚
            r"\b(VCC|GND|VIN|3V3|5V)\b",  # 电源引脚
        ]

        # 元件名称模式
        self.component_patterns = [
            r"\b(LED|灯|发光二极管)\b",
            r"\b(电阻|resistor|R\d+)\b",
            r"\b(电容|capacitor|C\d+)\b",
            r"\b(按键|button|开关|switch)\b",
            r"\b(传感器|sensor)\b",
            r"\b(ESP32|Arduino|单片机|微控制器)\b",
            r"\b(电机|motor)\b",
            r"\b(舵机|servo)\b",
            r"\b(显示屏|display|LCD|OLED)\b",
        ]

        # 连接动作关键词
        self.connection_keywords = [
            "连接",
            "接到",
            "接到",
            "连到",
            "接",
            "connect",
            "wire",
            "attach",
        ]

        # 纠正关键词
        self.correction_keywords = [
            "应该是",
            "应该连接",
            "正确的连接是",
            "改成",
            "改为",
            "修正为",
            "should be",
            "correct connection is",
            "change to",
            "modify to",
        ]

        # 确认关键词
        self.confirmation_keywords = ["正确", "对", "没错", "yes", "correct", "right"]

        # 错误关键词
        self.error_keywords = ["错误", "错了", "不对", "wrong", "incorrect", "mistake"]

    def detect_corrections(self, voice_transcript: str) -> VoiceCorrectionResult:
        """
        检测语音中的纠错行为

        Args:
            voice_transcript: 语音转录文本

        Returns:
            VoiceCorrectionResult: 纠错检测结果
        """
        try:
            # 预处理文本
            cleaned_text = self._preprocess_text(voice_transcript)

            # 检测纠错类型
            correction_type = self._detect_correction_type(cleaned_text)

            # 提取纠错信息
            corrections = self._extract_corrections(cleaned_text, correction_type)

            # 计算置信度
            confidence = self._calculate_confidence(cleaned_text, corrections)

            # 计算准确度评分
            accuracy_score = self._calculate_accuracy_score(corrections)

            return VoiceCorrectionResult(
                correction_type=correction_type,
                confidence=confidence,
                detected_corrections=corrections,
                accuracy_score=accuracy_score,
                timestamp=asyncio.get_event_loop().time(),
                raw_transcript=voice_transcript,
                parsed_commands=self._parse_commands(cleaned_text),
            )

        except Exception as e:
            logger.error(f"语音纠错检测失败: {e}")
            return VoiceCorrectionResult(
                correction_type=CorrectionType.GENERAL_CORRECTION,
                confidence=0.0,
                detected_corrections=[],
                accuracy_score=0.0,
                timestamp=asyncio.get_event_loop().time(),
                raw_transcript=voice_transcript,
                parsed_commands=[],
            )

    def _preprocess_text(self, text: str) -> str:
        """预处理语音文本"""
        # 转换为小写
        text = text.lower()

        # 标准化常见表达
        text = re.sub(r"[，。！？；：]", " ", text)  # 替换标点符号为空格
        text = re.sub(r"\s+", " ", text)  # 合并多个空格
        text = text.strip()

        # 标准化英文表达
        text = re.sub(r"d nine", "d9", text)
        text = re.sub(r"a zero", "a0", text)
        text = re.sub(r"ground", "gnd", text)
        text = re.sub(r"power", "vcc", text)

        return text

    def _detect_correction_type(self, text: str) -> CorrectionType:
        """检测纠错类型"""
        # 检查是否包含引脚连接相关词汇
        pin_matches = []
        for pattern in self.pin_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            pin_matches.extend(matches)

        component_matches = []
        for pattern in self.component_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            component_matches.extend(matches)

        # 根据匹配结果判断纠错类型
        if len(pin_matches) >= 2 and len(component_matches) >= 2:
            # 包含多个引脚和元件，可能是引脚连接纠错
            if any(keyword in text for keyword in self.connection_keywords):
                return CorrectionType.PIN_CONNECTION

        if "识别" in text or "identify" in text:
            return CorrectionType.COMPONENT_IDENTIFICATION

        if "顺序" in text or "sequence" in text:
            return CorrectionType.WIRING_SEQUENCE

        if "配置" in text or "configuration" in text:
            return CorrectionType.CIRCUIT_CONFIGURATION

        return CorrectionType.GENERAL_CORRECTION

    def _extract_corrections(
        self, text: str, correction_type: CorrectionType
    ) -> List[Any]:
        """提取具体的纠错信息"""
        corrections = []

        if correction_type == CorrectionType.PIN_CONNECTION:
            pin_corrections = self._extract_pin_corrections(text)
            corrections.extend(pin_corrections)

        elif correction_type == CorrectionType.COMPONENT_IDENTIFICATION:
            component_corrections = self._extract_component_corrections(text)
            corrections.extend(component_corrections)

        # 提取通用纠正信息
        general_corrections = self._extract_general_corrections(text)
        corrections.extend(general_corrections)

        return corrections

    def _extract_pin_corrections(self, text: str) -> List[PinConnectionCorrection]:
        """提取引脚连接纠错"""
        corrections = []

        # 查找"应该是"模式
        should_be_pattern = (
            r"(d\d+|a\d+|sda|scl)\s*(?:应该是|应该连接|改成)\s*(.+?)(?:\s|$)"
        )
        matches = re.findall(should_be_pattern, text, re.IGNORECASE)

        for pin_match, component_desc in matches:
            # 提取元件信息
            component = self._extract_component_from_description(component_desc)
            if component:
                correction = PinConnectionCorrection(
                    pin_name=pin_match.upper(),
                    from_component="",  # 需要从上下文获取
                    to_component=component,
                    connection_type=self._infer_connection_type(pin_match),
                    is_corrected=True,
                )
                corrections.append(correction)

        return corrections

    def _extract_component_corrections(self, text: str) -> List[Dict[str, str]]:
        """提取元件识别纠错"""
        corrections = []

        # 查找元件纠正模式
        component_patterns = [
            r"(这个|这个元件|这个东西)\s*(?:应该是|其实是|正确的是)\s*(.+)",
            r"(识别错误|认错了)\s*(?:应该是|正确的是)\s*(.+)",
        ]

        for pattern in component_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                corrections.append(
                    {
                        "original_description": match[0],
                        "corrected_component": match[1].strip(),
                        "correction_type": "component_identification",
                    }
                )

        return corrections

    def _extract_general_corrections(self, text: str) -> List[Dict[str, Any]]:
        """提取通用纠错信息"""
        corrections = []

        # 检查确认和否定表达
        has_confirmation = any(
            keyword in text for keyword in self.confirmation_keywords
        )
        has_error = any(keyword in text for keyword in self.error_keywords)

        if has_confirmation:
            corrections.append(
                {
                    "type": "confirmation",
                    "confidence_boost": 0.2,
                    "description": "用户确认了某个操作的正确性",
                }
            )

        if has_error:
            corrections.append(
                {
                    "type": "error_identification",
                    "confidence_boost": 0.1,
                    "description": "用户识别出了错误",
                }
            )

        return corrections

    def _extract_component_from_description(self, description: str) -> Optional[str]:
        """从描述中提取元件名称"""
        for pattern in self.component_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _infer_connection_type(self, pin_name: str) -> str:
        """推断连接类型"""
        pin_lower = pin_name.lower()

        if (
            "vcc" in pin_lower
            or "vin" in pin_lower
            or "3v3" in pin_lower
            or "5v" in pin_lower
        ):
            return "power"
        elif "gnd" in pin_lower:
            return "ground"
        elif pin_lower.startswith("d"):
            return "digital"
        elif pin_lower.startswith("a"):
            return "analog"
        elif "sda" in pin_lower or "scl" in pin_lower:
            return "i2c"
        elif "mosi" in pin_lower or "miso" in pin_lower or "sck" in pin_lower:
            return "spi"
        elif "rx" in pin_lower or "tx" in pin_lower:
            return "serial"
        else:
            return "general"

    def _calculate_confidence(self, text: str, corrections: List[Any]) -> float:
        """计算纠错置信度"""
        base_confidence = 0.5

        # 根据关键词加分
        keyword_score = 0.0
        for keyword in self.correction_keywords:
            if keyword in text:
                keyword_score += 0.1

        # 根据检测到的纠错数量加分
        correction_score = min(len(corrections) * 0.1, 0.3)

        # 根据文本长度调整
        length_factor = min(len(text.split()) / 10.0, 1.0) * 0.1

        total_confidence = (
            base_confidence + keyword_score + correction_score + length_factor
        )
        return min(total_confidence, 1.0)

    def _calculate_accuracy_score(self, corrections: List[Any]) -> float:
        """计算准确度评分"""
        if not corrections:
            return 0.0

        # 基于纠错质量和完整性计算评分
        score = 0.5  # 基础分

        # 每个有效的纠错加0.1分
        valid_corrections = [
            c for c in corrections if hasattr(c, "is_corrected") and c.is_corrected
        ]
        score += len(valid_corrections) * 0.1

        # 最高不超过0.9分
        return min(score, 0.9)

    def _parse_commands(self, text: str) -> List[str]:
        """解析出具体的命令"""
        commands = []

        # 分割句子
        sentences = re.split(r"[.!?;]", text)

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                # 提取包含纠正意图的句子
                if any(keyword in sentence for keyword in self.correction_keywords):
                    commands.append(sentence)

        return commands


# 硬件连接状态检查器
class HardwareConnectionChecker:
    """硬件连接状态检查器"""

    def __init__(self):
        self.known_pins = {
            "D9": {"type": "digital", "usage": "PWM"},
            "D10": {"type": "digital", "usage": "SPI_CS"},
            "A0": {"type": "analog", "usage": "sensor_input"},
            "SDA": {"type": "i2c", "usage": "data"},
            "SCL": {"type": "i2c", "usage": "clock"},
            "VCC": {"type": "power", "usage": "3.3V"},
            "GND": {"type": "power", "usage": "ground"},
        }

    def validate_pin_connection(self, pin_name: str, component: str) -> Dict[str, Any]:
        """
        验证引脚连接是否合理

        Args:
            pin_name: 引脚名称
            component: 连接的元件

        Returns:
            Dict: 验证结果
        """
        pin_name = pin_name.upper()

        if pin_name not in self.known_pins:
            return {
                "valid": False,
                "reason": f"未知引脚: {pin_name}",
                "suggestion": "请检查引脚名称是否正确",
            }

        pin_info = self.known_pins[pin_name]
        component_lower = component.lower()

        # 基本验证规则
        validation_rules = {
            "VCC": ["led", "电阻", "传感器", "esp32"],
            "GND": ["led", "电阻", "传感器", "esp32"],
            "D9": ["led", "电机", "舵机"],
            "A0": ["传感器", "电位器"],
            "SDA": ["传感器", "显示屏"],
            "SCL": ["传感器", "显示屏"],
        }

        allowed_components = validation_rules.get(pin_name, [])
        is_valid = any(comp in component_lower for comp in allowed_components)

        return {
            "valid": is_valid,
            "pin_info": pin_info,
            "component": component,
            "reason": "连接合理" if is_valid else "连接可能不合理",
            "suggestion": (
                ""
                if is_valid
                else f'{pin_name}通常连接到: {", ".join(allowed_components)}'
            ),
        }


# 测试代码
if __name__ == "__main__":
    import asyncio

    async def test_voice_correction():
        detector = VoiceCorrectionDetector()
        checker = HardwareConnectionChecker()

        # 测试用例
        test_cases = [
            "D9引脚应该连接到LED",
            "我刚才把A0接到错误的地方，应该是连接温度传感器",
            "SDA和SCL应该连接到OLED显示屏",
            "VCC接到3.3V，GND接地，这样连接是对的",
            "这个元件识别错误，应该是湿度传感器不是温度传感器",
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n=== 测试用例 {i} ===")
            print(f"输入: {test_case}")

            # 检测纠错
            result = detector.detect_corrections(test_case)
            print(f"纠错类型: {result.correction_type.value}")
            print(f"置信度: {result.confidence:.2f}")
            print(f"准确度: {result.accuracy_score:.2f}")
            print(f"检测到的纠错: {len(result.detected_corrections)} 项")

            # 验证硬件连接
            for correction in result.detected_corrections:
                if isinstance(correction, PinConnectionCorrection):
                    validation = checker.validate_pin_connection(
                        correction.pin_name, correction.to_component
                    )
                    print(
                        f"  {correction.pin_name} -> {correction.to_component}: "
                        f"{'✓' if validation['valid'] else '✗'} {validation['reason']}"
                    )

    # 运行测试
    asyncio.run(test_voice_correction())
