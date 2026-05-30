"""
语音奖励规则模板配置
定义各种语音纠错场景的奖励规则和触发条件
"""

from datetime import datetime
import json
from typing import Any, Dict, List


class VoiceRewardRuleTemplate:
    """语音奖励规则模板"""

    def __init__(self, template_id: str, name: str, description: str):
        self.template_id = template_id
        self.name = name
        self.description = description
        self.conditions = []
        self.rewards = []
        self.created_at = datetime.now().isoformat()

    def add_condition(
        self, condition_type: str, operator: str, value: Any, field_name: str = None
    ):
        """添加触发条件"""
        condition = {
            "type": condition_type,
            "operator": operator,
            "value": value,
            "field_name": field_name,
        }
        self.conditions.append(condition)
        return self

    def add_reward(self, reward_type: str, amount: int, description: str = None):
        """添加奖励"""
        reward = {
            "type": reward_type,
            "amount": amount,
            "description": description or f"{reward_type}奖励",
        }
        self.rewards.append(reward)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "conditions": self.conditions,
            "rewards": self.rewards,
            "created_at": self.created_at,
        }


# 预定义的语音奖励规则模板
VOICE_REWARD_TEMPLATES = {
    # D9引脚连接纠错模板
    "d9_pin_correction": VoiceRewardRuleTemplate(
        "d9_pin_correction", "D9引脚连接纠错奖励", "用户正确纠正D9引脚连接时奖励50积分"
    )
    .add_condition("pin_name", "equals", "D9")
    .add_condition("correction_type", "equals", "pin_connection")
    .add_condition("accuracy_score", "greater_than_equal", 0.8)
    .add_reward("integral", 50, "正确连接D9引脚奖励")
    .add_reward("notification", 0, "恭喜！正确连接D9引脚获得50积分奖励！"),
    # A0模拟引脚纠错模板
    "a0_pin_correction": VoiceRewardRuleTemplate(
        "a0_pin_correction", "A0引脚连接纠错奖励", "用户正确纠正A0引脚连接时奖励40积分"
    )
    .add_condition("pin_name", "equals", "A0")
    .add_condition("correction_type", "equals", "pin_connection")
    .add_condition("accuracy_score", "greater_than_equal", 0.75)
    .add_reward("integral", 40, "正确连接A0引脚奖励")
    .add_reward("notification", 0, "很好！正确连接A0引脚获得40积分奖励！"),
    # I2C总线连接纠错模板
    "i2c_connection_correction": VoiceRewardRuleTemplate(
        "i2c_connection_correction",
        "I2C总线连接纠错奖励",
        "用户正确纠正SDA/SCL引脚连接时奖励60积分",
    )
    .add_condition("pin_name", "in", ["SDA", "SCL"])
    .add_condition("correction_type", "equals", "pin_connection")
    .add_condition("accuracy_score", "greater_than_equal", 0.85)
    .add_reward("integral", 60, "正确连接I2C总线奖励")
    .add_reward("badge", 0, "I2C专家"),
    # 元件识别纠错模板
    "component_identification": VoiceRewardRuleTemplate(
        "component_identification",
        "元件识别纠错奖励",
        "用户正确识别元件类型时奖励30积分",
    )
    .add_condition("correction_type", "equals", "component_identification")
    .add_condition("accuracy_score", "greater_than_equal", 0.7)
    .add_reward("integral", 30, "元件识别正确奖励")
    .add_reward("notification", 0, "元件识别准确！获得30积分奖励！"),
    # 接线顺序纠错模板
    "wiring_sequence_correction": VoiceRewardRuleTemplate(
        "wiring_sequence_correction",
        "接线顺序纠错奖励",
        "用户正确纠正接线顺序时奖励70积分",
    )
    .add_condition("correction_type", "equals", "wiring_sequence")
    .add_condition("accuracy_score", "greater_than_equal", 0.8)
    .add_reward("integral", 70, "接线顺序正确奖励")
    .add_reward("badge", 0, "接线大师"),
    # 电路配置纠错模板
    "circuit_configuration_correction": VoiceRewardRuleTemplate(
        "circuit_configuration_correction",
        "电路配置纠错奖励",
        "用户正确纠正电路配置时奖励80积分",
    )
    .add_condition("correction_type", "equals", "circuit_configuration")
    .add_condition("accuracy_score", "greater_than_equal", 0.85)
    .add_reward("integral", 80, "电路配置正确奖励")
    .add_reward("badge", 0, "电路专家")
    .add_reward("special_effect", 0, "解锁高级电路模式"),
    # 连续纠错奖励模板
    "consecutive_corrections": VoiceRewardRuleTemplate(
        "consecutive_corrections",
        "连续纠错奖励",
        "用户连续进行多次有效纠错时给予额外奖励",
    )
    .add_condition("consecutive_corrections", "greater_than_equal", 3)
    .add_condition("average_accuracy", "greater_than_equal", 0.8)
    .add_reward("integral", 100, "连续纠错达人奖励")
    .add_reward("badge", 0, "纠错达人")
    .add_reward("multiplier", 1.5, "1.5倍积分加成"),
    # 高难度纠错模板
    "complex_correction": VoiceRewardRuleTemplate(
        "complex_correction", "复杂纠错奖励", "用户完成复杂纠错任务时给予高额奖励"
    )
    .add_condition("correction_complexity", "greater_than_equal", 0.8)
    .add_condition("accuracy_score", "greater_than_equal", 0.9)
    .add_condition("time_efficiency", "less_than_equal", 30)  # 30秒内完成
    .add_reward("integral", 150, "复杂纠错高手奖励")
    .add_reward("badge", 0, "纠错高手")
    .add_reward("unlock_feature", 0, "解锁专家模式"),
    # 新手引导纠错模板
    "beginner_guidance": VoiceRewardRuleTemplate(
        "beginner_guidance", "新手引导纠错奖励", "帮助新手用户进行纠错时给予鼓励奖励"
    )
    .add_condition("user_level", "less_than_equal", 2)  # 新手级别
    .add_condition("correction_helpfulness", "greater_than_equal", 0.7)
    .add_reward("integral", 25, "新手进步奖励")
    .add_reward("notification", 0, "很棒的进步！继续保持！"),
    # 团队协作纠错模板
    "team_collaboration": VoiceRewardRuleTemplate(
        "team_collaboration", "团队协作纠错奖励", "多人协作完成纠错任务时给予团队奖励"
    )
    .add_condition("collaborators_count", "greater_than_equal", 2)
    .add_condition("team_accuracy", "greater_than_equal", 0.85)
    .add_reward("integral", 200, "团队协作优秀奖励")
    .add_reward("badge", 0, "协作之星")
    .add_reward("team_bonus", 50, "团队额外奖励"),
}


def get_template_by_id(template_id: str) -> VoiceRewardRuleTemplate:
    """根据ID获取模板"""
    return VOICE_REWARD_TEMPLATES.get(template_id)


def get_templates_by_category(category: str) -> List[VoiceRewardRuleTemplate]:
    """根据分类获取模板"""
    category_mapping = {
        "pin_connection": [
            "d9_pin_correction",
            "a0_pin_correction",
            "i2c_connection_correction",
        ],
        "component_identification": ["component_identification"],
        "wiring": ["wiring_sequence_correction"],
        "circuit": ["circuit_configuration_correction"],
        "achievement": ["consecutive_corrections", "complex_correction"],
        "social": ["beginner_guidance", "team_collaboration"],
    }

    template_ids = category_mapping.get(category, [])
    return [
        VOICE_REWARD_TEMPLATES[tid]
        for tid in template_ids
        if tid in VOICE_REWARD_TEMPLATES
    ]


def export_templates_to_json() -> str:
    """导出所有模板为JSON格式"""
    templates_dict = {}
    for template_id, template in VOICE_REWARD_TEMPLATES.items():
        templates_dict[template_id] = template.to_dict()

    return json.dumps(templates_dict, indent=2, ensure_ascii=False)


def load_templates_from_json(json_str: str) -> Dict[str, VoiceRewardRuleTemplate]:
    """从JSON加载模板"""
    data = json.loads(json_str)
    loaded_templates = {}

    for template_id, template_data in data.items():
        template = VoiceRewardRuleTemplate(
            template_data["template_id"],
            template_data["name"],
            template_data["description"],
        )
        template.conditions = template_data["conditions"]
        template.rewards = template_data["rewards"]
        template.created_at = template_data["created_at"]
        loaded_templates[template_id] = template

    return loaded_templates


# 动态规则生成器
class DynamicVoiceRuleGenerator:
    """动态语音规则生成器"""

    @staticmethod
    def generate_adaptive_rule(
        user_performance: Dict[str, Any],
    ) -> VoiceRewardRuleTemplate:
        """
        根据用户表现生成自适应规则

        Args:
            user_performance: 用户表现数据
                {
                    'average_accuracy': 0.85,
                    'correction_frequency': 10,
                    'preferred_pins': ['D9', 'A0'],
                    'skill_level': 'intermediate'
                }
        """
        avg_accuracy = user_performance.get("average_accuracy", 0.5)
        frequency = user_performance.get("correction_frequency", 1)
        skill_level = user_performance.get("skill_level", "beginner")

        # 根据技能水平调整奖励
        base_points = {"beginner": 25, "intermediate": 40, "advanced": 60}[skill_level]

        # 根据准确度调整奖励倍数
        accuracy_multiplier = min(avg_accuracy * 2, 2.0)

        # 根据频率调整奖励
        frequency_bonus = min(frequency * 2, 20)

        final_points = int(base_points * accuracy_multiplier + frequency_bonus)

        template = VoiceRewardRuleTemplate(
            f'adaptive_rule_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            f"{skill_level.capitalize()}用户自适应奖励",
            f"根据用户表现动态生成的奖励规则",
        )

        template.add_condition(
            "accuracy_score", "greater_than_equal", avg_accuracy - 0.1
        )
        template.add_condition("user_level", "equals", skill_level)
        template.add_reward("integral", final_points, f"自适应奖励 - {skill_level}")

        return template


# 规则验证器
class VoiceRuleValidator:
    """语音规则验证器"""

    @staticmethod
    def validate_template(template: VoiceRewardRuleTemplate) -> Dict[str, Any]:
        """验证模板的有效性"""
        issues = []

        # 检查必要字段
        if not template.template_id:
            issues.append("模板ID不能为空")

        if not template.name:
            issues.append("模板名称不能为空")

        if not template.conditions:
            issues.append("必须至少有一个触发条件")

        if not template.rewards:
            issues.append("必须至少有一个奖励")

        # 检查条件有效性
        for i, condition in enumerate(template.conditions):
            if not condition.get("type"):
                issues.append(f"条件 {i+1}: 条件类型不能为空")

            if not condition.get("operator"):
                issues.append(f"条件 {i+1}: 操作符不能为空")

            if condition.get("value") is None:
                issues.append(f"条件 {i+1}: 比较值不能为空")

        # 检查奖励有效性
        for i, reward in enumerate(template.rewards):
            if not reward.get("type"):
                issues.append(f"奖励 {i+1}: 奖励类型不能为空")

            if reward.get("amount", 0) <= 0:
                issues.append(f"奖励 {i+1}: 奖励数量必须大于0")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "template_id": template.template_id,
        }


# 测试代码
if __name__ == "__main__":
    print("=== 语音奖励规则模板测试 ===")

    # 显示所有模板
    print(f"\n可用模板数量: {len(VOICE_REWARD_TEMPLATES)}")

    for template_id, template in VOICE_REWARD_TEMPLATES.items():
        print(f"\n模板: {template.name}")
        print(f"ID: {template.template_id}")
        print(f"描述: {template.description}")
        print(f"条件数量: {len(template.conditions)}")
        print(f"奖励数量: {len(template.rewards)}")

        # 验证模板
        validation = VoiceRuleValidator.validate_template(template)
        print(f"验证结果: {'✓ 有效' if validation['valid'] else '✗ 无效'}")
        if not validation["valid"]:
            for issue in validation["issues"]:
                print(f"  - {issue}")

    # 导出测试
    json_export = export_templates_to_json()
    print(f"\nJSON导出长度: {len(json_export)} 字符")

    # 动态规则生成测试
    user_perf = {
        "average_accuracy": 0.87,
        "correction_frequency": 15,
        "skill_level": "intermediate",
    }

    adaptive_rule = DynamicVoiceRuleGenerator.generate_adaptive_rule(user_perf)
    print(f"\n自适应规则生成:")
    print(f"规则名称: {adaptive_rule.name}")
    print(
        f"预计奖励: {[r['amount'] for r in adaptive_rule.rewards if r['type'] == 'integral'][0]} 积分"
    )
