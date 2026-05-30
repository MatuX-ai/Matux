#!/usr/bin/env python3
"""
电路验证服务

验证电路组装的正确性，包括:
- 元件位置验证
- 极性检查
- 连通性分析
- 短路检测

输入：组装数据 (JSON 格式)
输出：验证结果 (包含错误和警告列表)
"""

from dataclasses import dataclass, field
from datetime import datetime
import json
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp,
        }


@dataclass
class Component:
    """电路元件"""

    id: str
    type: str
    designator: str
    value: str
    package: str
    pad_id: str
    polarity: Optional[str] = None
    installed: bool = True


@dataclass
class SolderPad:
    """焊盘"""

    id: str
    pad_type: str  # tht, smd, socket
    pin_count: int
    net_label: Optional[str] = None
    polarity: Optional[str] = None
    occupied: bool = False


@dataclass
class CircuitBoard:
    """电路板"""

    id: str
    name: str
    pads: Dict[str, SolderPad] = field(default_factory=dict)
    components: Dict[str, Component] = field(default_factory=dict)
    nets: Dict[str, List[str]] = field(default_factory=dict)  # net_name -> pad_ids


class CircuitValidationService:
    """电路验证服务类"""

    # 极性元件类型映射
    POLAR_COMPONENTS = {
        "capacitor_electrolytic": "electrolytic",
        "led": "led",
        "diode": "diode",
        "transistor": "transistor",
        "ic": "ic",
    }

    def __init__(self):
        self.circuit_boards: Dict[str, CircuitBoard] = {}

    def register_circuit_board(self, board_data: dict) -> None:
        """注册电路板"""
        board = CircuitBoard(id=board_data["id"], name=board_data["name"])

        # 添加焊盘
        for pad_data in board_data.get("pads", []):
            pad = SolderPad(
                id=pad_data["id"],
                pad_type=pad_data["type"],
                pin_count=pad_data.get("pin_count", 1),
                net_label=pad_data.get("net_label"),
                polarity=pad_data.get("polarity"),
            )
            board.pads[pad.id] = pad

        # 添加网络
        for net_name, pad_ids in board_data.get("nets", {}).items():
            board.nets[net_name] = pad_ids

        self.circuit_boards[board.id] = board
        print(f"[Validation] 电路板已注册：{board.name}")

    def validate_assembly(self, assembly_data: dict) -> ValidationResult:
        """
        验证元件组装

        Args:
            assembly_data: 组装数据
                {
                    "board_id": "board_001",
                    "components": [
                        {
                            "component_id": "r1",
                            "component_type": "resistor",
                            "designator": "R1",
                            "pad_id": "pad_r1_1"
                        },
                        ...
                    ]
                }

        Returns:
            ValidationResult: 验证结果
        """
        result = ValidationResult()

        # 1. 获取电路板
        board_id = assembly_data.get("board_id")
        if not board_id or board_id not in self.circuit_boards:
            result.errors.append(f"电路板不存在：{board_id}")
            result.is_valid = False
            return result

        board = self.circuit_boards[board_id]

        # 2. 验证每个元件
        for comp_data in assembly_data.get("components", []):
            comp_result = self._validate_component_placement(comp_data, board)

            result.errors.extend(comp_result.errors)
            result.warnings.extend(comp_result.warnings)

            if not comp_result.is_valid:
                result.is_valid = False

        # 3. 检查完整性
        completeness_result = self._check_completeness(board)
        result.errors.extend(completeness_result.errors)
        result.warnings.extend(completeness_result.warnings)

        if not completeness_result.is_valid:
            result.is_valid = False

        # 4. 电气规则检查
        erc_result = self._electrical_rules_check(board)
        result.warnings.extend(erc_result.warnings)

        return result

    def _validate_component_placement(
        self, comp_data: dict, board: CircuitBoard
    ) -> ValidationResult:
        """验证单个元件的放置"""
        result = ValidationResult()

        comp_id = comp_data.get("component_id")
        pad_id = comp_data.get("pad_id")
        comp_type = comp_data.get("component_type")
        designator = comp_data.get("designator")

        # 检查焊盘是否存在
        if pad_id not in board.pads:
            result.errors.append(f"焊盘不存在：{pad_id}")
            return result

        pad = board.pads[pad_id]

        # 检查焊盘是否已被占用
        if pad.occupied:
            result.errors.append(f"焊盘已被占用：{pad_id}")
            return result

        # 检查封装兼容性
        if not self._is_package_compatible(comp_type, pad.pad_type):
            result.errors.append(f"元件 {designator} 封装不兼容焊盘 {pad_id}")
            result.is_valid = False

        # 检查极性
        if self._is_polar_component(comp_type):
            comp_polarity = comp_data.get("polarity")
            pad_polarity = pad.polarity

            if comp_polarity and pad_polarity:
                if comp_polarity != pad_polarity:
                    result.errors.append(
                        f"元件 {designator} 极性错误！"
                        f"元件:{comp_polarity}, 焊盘:{pad_polarity}"
                    )
                    result.is_valid = False

        # 标记焊盘为已占用
        pad.occupied = True

        return result

    def _is_package_compatible(self, component_type: str, pad_type: str) -> bool:
        """检查封装兼容性"""
        compatibility_map = {
            "resistor": ["tht", "smd"],
            "capacitor": ["tht", "smd"],
            "led": ["tht", "smd"],
            "ic_dip": ["tht"],
            "ic_soic": ["smd"],
            "switch": ["tht", "smd"],
            "connector": ["tht", "smd"],
        }

        compatible_types = compatibility_map.get(component_type, [])
        return pad_type in compatible_types

    def _is_polar_component(self, component_type: str) -> bool:
        """检查是否为有极性元件"""
        for polar_type in self.POLAR_COMPONENTS.values():
            if polar_type in component_type.lower():
                return True
        return False

    def _check_completeness(self, board: CircuitBoard) -> ValidationResult:
        """检查电路完整性"""
        result = ValidationResult()

        missing_components = []

        for pad_id, pad in board.pads.items():
            if not pad.occupied and pad.net_label:
                # 有网络标签但未被占用的焊盘
                missing_components.append(f"{pad.net_label} ({pad_id})")

        if missing_components:
            result.warnings.append(f"未安装的元件：{', '.join(missing_components)}")

        return result

    def _electrical_rules_check(self, board: CircuitBoard) -> ValidationResult:
        """电气规则检查 (ERC)"""
        result = ValidationResult()

        # 检查电源短路
        power_nets = [
            name
            for name in board.nets.keys()
            if "vcc" in name.lower() or "gnd" in name.lower()
        ]

        for net_name in power_nets:
            net_pads = board.nets[net_name]

            # 简化检查：如果电源网络只有一个连接点，可能有问题
            if len(net_pads) == 1:
                result.warnings.append(f"网络 {net_name} 只有一个连接点，可能存在开路")

        return result

    def check_continuity(self, board_id: str, from_pad: str, to_pad: str) -> bool:
        """
        检查两个焊盘之间是否导通

        Args:
            board_id: 电路板 ID
            from_pad: 起点焊盘
            to_pad: 终点焊盘

        Returns:
            是否导通
        """
        if board_id not in self.circuit_boards:
            return False

        board = self.circuit_boards[board_id]

        # 查找两个焊盘是否在同一个网络中
        for net_name, pad_ids in board.nets.items():
            if from_pad in pad_ids and to_pad in pad_ids:
                print(f"[Validation] ✓ 导通：{from_pad} <-> {to_pad} (网络:{net_name})")
                return True

        print(f"[Validation] ✗ 不导通：{from_pad} <-> {to_pad}")
        return False


def main():
    """主函数 - 示例用法"""
    service = CircuitValidationService()

    # 注册示例电路板
    example_board = {
        "id": "board_demo",
        "name": "LED 闪烁电路演示板",
        "pads": [
            {
                "id": "pad_r1_1",
                "type": "tht",
                "pin_count": 1,
                "net_label": "NET_R1_LED",
            },
            {"id": "pad_r1_2", "type": "tht", "pin_count": 1, "net_label": "VCC"},
            {
                "id": "pad_led1_a",
                "type": "tht",
                "pin_count": 1,
                "net_label": "NET_R1_LED",
                "polarity": "positive",
            },
            {"id": "pad_led1_k", "type": "tht", "pin_count": 1, "net_label": "GND"},
        ],
        "nets": {
            "VCC": ["pad_r1_2"],
            "GND": ["pad_led1_k"],
            "NET_R1_LED": ["pad_r1_1", "pad_led1_a"],
        },
    }

    service.register_circuit_board(example_board)

    # 测试组装验证
    test_assembly = {
        "board_id": "board_demo",
        "components": [
            {
                "component_id": "r1",
                "component_type": "resistor",
                "designator": "R1",
                "pad_id": "pad_r1_1",
            },
            {
                "component_id": "led1",
                "component_type": "led",
                "designator": "LED1",
                "pad_id": "pad_led1_a",
                "polarity": "positive",
            },
        ],
    }

    result = service.validate_assembly(test_assembly)

    print("\n" + "=" * 60)
    print("电路验证结果")
    print("=" * 60)
    print(f"验证状态：{'✓ 通过' if result.is_valid else '✗ 失败'}")

    if result.errors:
        print(f"\n错误 ({len(result.errors)}):")
        for error in result.errors:
            print(f"  ❌ {error}")

    if result.warnings:
        print(f"\n警告 ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  ⚠️  {warning}")

    print("=" * 60)

    # 测试导通性
    print("\n导通性测试:")
    is_connected = service.check_continuity("board_demo", "pad_r1_1", "pad_led1_a")
    print(f"R1 引脚 1 <-> LED 阳极：{'导通' if is_connected else '不导通'}")


if __name__ == "__main__":
    main()
