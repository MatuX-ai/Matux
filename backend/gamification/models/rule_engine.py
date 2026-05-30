"""
规则引擎模型
定义游戏化规则引擎的核心数据结构和配置
"""

from dataclasses import dataclass, field
from datetime import datetime
import enum
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class RuleConditionType(str, enum.Enum):
    """规则条件类型枚举"""

    SUCCESS_COUNT = "success_count"  # 成功次数
    FAILURE_COUNT = "failure_count"  # 失败次数
    SUCCESS_RATE = "success_rate"  # 成功率
    TIME_SPENT = "time_spent"  # 花费时间
    CONSECUTIVE_SUCCESS = "consecutive_success"  # 连续成功
    CONSECUTIVE_FAILURE = "consecutive_failure"  # 连续失败
    HINT_USAGE = "hint_usage"  # 提示使用
    RETRY_COUNT = "retry_count"  # 重试次数
    CUSTOM_METRIC = "custom_metric"  # 自定义指标

    # 多模态激励新增条件类型
    VOICE_CORRECTION = "voice_correction"  # 语音纠错
    AR_COMPONENT_PLACEMENT = "ar_component_placement"  # AR元件放置
    GESTURE_SEQUENCE = "gesture_sequence"  # 手势序列
    MULTIMODAL_COMPLETION = "multimodal_completion"  # 多模态任务完成
    HIDDEN_TASK_TRIGGER = "hidden_task_trigger"  # 隐藏任务触发


class RuleOperator(str, enum.Enum):
    """规则操作符枚举"""

    EQUAL = "=="  # 等于
    NOT_EQUAL = "!="  # 不等于
    GREATER_THAN = ">"  # 大于
    LESS_THAN = "<"  # 小于
    GREATER_EQUAL = ">="  # 大于等于
    LESS_EQUAL = "<="  # 小于等于
    BETWEEN = "between"  # 在范围内


class RuleActionType(str, enum.Enum):
    """规则动作类型枚举"""

    ADJUST_DIFFICULTY = "adjust_difficulty"  # 调整难度
    SEND_NOTIFICATION = "send_notification"  # 发送通知
    GRANT_ACHIEVEMENT = "grant_achievement"  # 授予成就
    UPDATE_USER_PROFILE = "update_user_profile"  # 更新用户档案
    TRIGGER_EVENT = "trigger_event"  # 触发事件
    CUSTOM_ACTION = "custom_action"  # 自定义动作

    # 多模态激励新增动作类型
    ISSUE_INTEGRAL = "issue_integral"  # 发放积分
    GRANT_BADGE = "grant_badge"  # 授予徽章
    UNLOCK_HIDDEN_FEATURE = "unlock_hidden_feature"  # 解锁隐藏功能
    TRIGGER_SPECIAL_EFFECT = "trigger_special_effect"  # 触发特殊效果


@dataclass
class RuleCondition:
    """规则条件"""

    condition_type: RuleConditionType
    operator: RuleOperator
    value: Union[int, float, str, List]  # 比较值
    field_name: Optional[str] = None  # 字段名(用于自定义指标)

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """评估条件是否满足"""
        try:
            # 获取上下文中的值
            if self.field_name:
                actual_value = context.get(self.field_name)
            else:
                actual_value = context.get(self.condition_type.value)

            if actual_value is None:
                return False

            # 根据操作符进行比较
            if self.operator == RuleOperator.EQUAL:
                return actual_value == self.value
            elif self.operator == RuleOperator.NOT_EQUAL:
                return actual_value != self.value
            elif self.operator == RuleOperator.GREATER_THAN:
                return actual_value > self.value
            elif self.operator == RuleOperator.LESS_THAN:
                return actual_value < self.value
            elif self.operator == RuleOperator.GREATER_EQUAL:
                return actual_value >= self.value
            elif self.operator == RuleOperator.LESS_EQUAL:
                return actual_value <= self.value
            elif self.operator == RuleOperator.BETWEEN:
                if isinstance(self.value, list) and len(self.value) == 2:
                    return self.value[0] <= actual_value <= self.value[1]
                return False

            return False
        except Exception as e:
            logger.error(f"条件评估失败: {e}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "condition_type": self.condition_type.value,
            "operator": self.operator.value,
            "value": self.value,
            "field_name": self.field_name,
        }


@dataclass
class RuleAction:
    """规则动作"""

    action_type: RuleActionType
    parameters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {"action_type": self.action_type.value, "parameters": self.parameters}


@dataclass
class GamificationRule:
    """游戏化规则"""

    rule_id: str
    name: str
    description: str
    conditions: List[RuleCondition]  # 条件列表(AND关系)
    actions: List[RuleAction]  # 动作列表
    priority: int = 0  # 优先级(数字越大优先级越高)
    is_active: bool = True  # 是否激活
    cooldown_seconds: int = 0  # 冷却时间(秒)
    max_executions: int = -1  # 最大执行次数(-1为无限制)
    execution_count: int = 0  # 已执行次数
    last_execution_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def can_execute(self, current_time: datetime) -> bool:
        """检查规则是否可以执行"""
        if not self.is_active:
            return False

        if self.max_executions > 0 and self.execution_count >= self.max_executions:
            return False

        if self.last_execution_time and self.cooldown_seconds > 0:
            time_since_last = (current_time - self.last_execution_time).total_seconds()
            if time_since_last < self.cooldown_seconds:
                return False

        return True

    def evaluate_conditions(self, context: Dict[str, Any]) -> bool:
        """评估所有条件是否满足(AND关系)"""
        return all(condition.evaluate(context) for condition in self.conditions)

    def execute_actions(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行所有动作"""
        results = []
        for action in self.actions:
            try:
                result = self._execute_single_action(action, context)
                results.append(result)
            except Exception as e:
                logger.error(f"执行动作失败: {action.action_type.value}, 错误: {e}")
                results.append(
                    {
                        "action_type": action.action_type.value,
                        "success": False,
                        "error": str(e),
                    }
                )
        return results

    def _execute_single_action(
        self, action: RuleAction, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个动作"""
        result = {
            "action_type": action.action_type.value,
            "parameters": action.parameters,
            "success": True,
            "timestamp": datetime.now().isoformat(),
        }

        # 这里可以实现具体的动作逻辑
        if action.action_type == RuleActionType.ADJUST_DIFFICULTY:
            # 调整难度逻辑
            adjustment_value = action.parameters.get("adjustment_value", 0)
            result["adjustment_value"] = adjustment_value
            logger.info(f"执行难度调整: {adjustment_value}")

        elif action.action_type == RuleActionType.SEND_NOTIFICATION:
            # 发送通知逻辑
            message = action.parameters.get("message", "")
            result["message"] = message
            logger.info(f"发送通知: {message}")

        elif action.action_type == RuleActionType.ISSUE_INTEGRAL:
            # 发放积分逻辑
            amount = action.parameters.get("amount", 0)
            reason = action.parameters.get("reason", "")
            result["amount"] = amount
            result["reason"] = reason
            logger.info(f"发放积分: {amount} - 原因: {reason}")

        elif action.action_type == RuleActionType.GRANT_BADGE:
            # 授予徽章逻辑
            badge_name = action.parameters.get("badge_name", "")
            badge_description = action.parameters.get("badge_description", "")
            result["badge_name"] = badge_name
            result["badge_description"] = badge_description
            logger.info(f"授予徽章: {badge_name}")

        elif action.action_type == RuleActionType.UNLOCK_HIDDEN_FEATURE:
            # 解锁隐藏功能逻辑
            feature_name = action.parameters.get("feature_name", "")
            unlock_condition = action.parameters.get("unlock_condition", "")
            result["feature_name"] = feature_name
            result["unlock_condition"] = unlock_condition
            logger.info(f"解锁隐藏功能: {feature_name}")

        return result

    def increment_execution_count(self):
        """增加执行计数"""
        self.execution_count += 1
        self.last_execution_time = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "conditions": [cond.to_dict() for cond in self.conditions],
            "actions": [act.to_dict() for act in self.actions],
            "priority": self.priority,
            "is_active": self.is_active,
            "cooldown_seconds": self.cooldown_seconds,
            "max_executions": self.max_executions,
            "execution_count": self.execution_count,
            "last_execution_time": (
                self.last_execution_time.isoformat()
                if self.last_execution_time
                else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class RuleExecutionContext:
    """规则执行上下文"""

    user_id: str
    task_id: Optional[str] = None
    event_type: Optional[str] = None  # 事件类型
    metrics: Dict[str, Any] = field(default_factory=dict)  # 相关指标
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "user_id": self.user_id,
            "task_id": self.task_id,
            "event_type": self.event_type,
            "metrics": self.metrics,
            "timestamp": self.timestamp.isoformat(),
        }


class RuleEngineConfig:
    """规则引擎配置"""

    def __init__(self):
        self.rules: List[GamificationRule] = []
        self.global_cooldown: int = 1  # 全局最小冷却时间(秒)
        self.max_concurrent_executions: int = 100  # 最大并发执行数
        self.enable_logging: bool = True
        self.log_level: str = "INFO"

    def add_rule(self, rule: GamificationRule):
        """添加规则"""
        self.rules.append(rule)
        # 按优先级排序
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        for i, rule in enumerate(self.rules):
            if rule.rule_id == rule_id:
                self.rules.pop(i)
                return True
        return False

    def get_active_rules(self) -> List[GamificationRule]:
        """获取激活的规则"""
        return [rule for rule in self.rules if rule.is_active]

    def get_rules_by_priority(self) -> List[GamificationRule]:
        """按优先级获取规则"""
        return sorted(self.rules, key=lambda r: r.priority, reverse=True)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "rules": [rule.to_dict() for rule in self.rules],
            "global_cooldown": self.global_cooldown,
            "max_concurrent_executions": self.max_concurrent_executions,
            "enable_logging": self.enable_logging,
            "log_level": self.log_level,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RuleEngineConfig":
        """从字典创建配置"""
        config = cls()
        config.global_cooldown = data.get("global_cooldown", 1)
        config.max_concurrent_executions = data.get("max_concurrent_executions", 100)
        config.enable_logging = data.get("enable_logging", True)
        config.log_level = data.get("log_level", "INFO")

        # 重建规则
        for rule_data in data.get("rules", []):
            conditions = [
                RuleCondition(
                    condition_type=RuleConditionType(cond["condition_type"]),
                    operator=RuleOperator(cond["operator"]),
                    value=cond["value"],
                    field_name=cond.get("field_name"),
                )
                for cond in rule_data.get("conditions", [])
            ]

            actions = [
                RuleAction(
                    action_type=RuleActionType(act["action_type"]),
                    parameters=act.get("parameters", {}),
                )
                for act in rule_data.get("actions", [])
            ]

            rule = GamificationRule(
                rule_id=rule_data["rule_id"],
                name=rule_data["name"],
                description=rule_data["description"],
                conditions=conditions,
                actions=actions,
                priority=rule_data.get("priority", 0),
                is_active=rule_data.get("is_active", True),
                cooldown_seconds=rule_data.get("cooldown_seconds", 0),
                max_executions=rule_data.get("max_executions", -1),
            )

            if "execution_count" in rule_data:
                rule.execution_count = rule_data["execution_count"]

            config.add_rule(rule)

        return config


# 预定义的常用规则模板
PREDEFINED_RULE_TEMPLATES = {
    "success_streak_increase": GamificationRule(
        rule_id="template_success_streak_increase",
        name="连续成功提升难度模板",
        description="用户连续成功完成任务时自动提升难度",
        conditions=[
            RuleCondition(
                condition_type=RuleConditionType.CONSECUTIVE_SUCCESS,
                operator=RuleOperator.GREATER_EQUAL,
                value=3,
            )
        ],
        actions=[
            RuleAction(
                action_type=RuleActionType.ADJUST_DIFFICULTY,
                parameters={"adjustment_value": 0.5, "direction": "increase"},
            )
        ],
        priority=10,
        cooldown_seconds=3600,
    ),
    "failure_streak_decrease": GamificationRule(
        rule_id="template_failure_streak_decrease",
        name="连续失败降低难度模板",
        description="用户连续失败时自动降低难度",
        conditions=[
            RuleCondition(
                condition_type=RuleConditionType.CONSECUTIVE_FAILURE,
                operator=RuleOperator.GREATER_EQUAL,
                value=2,
            )
        ],
        actions=[
            RuleAction(
                action_type=RuleActionType.ADJUST_DIFFICULTY,
                parameters={"adjustment_value": 0.5, "direction": "decrease"},
            )
        ],
        priority=10,
        cooldown_seconds=1800,
    ),
    # 多模态激励新增模板
    "voice_correction_reward": GamificationRule(
        rule_id="template_voice_correction_reward",
        name="语音纠错积分奖励模板",
        description="用户通过语音指令正确纠正硬件连接时奖励积分",
        conditions=[
            RuleCondition(
                condition_type=RuleConditionType.VOICE_CORRECTION,
                operator=RuleOperator.EQUAL,
                value=True,
            ),
            RuleCondition(
                condition_type=RuleConditionType.CUSTOM_METRIC,
                operator=RuleOperator.EQUAL,
                value="correct_pin_connection",
                field_name="correction_type",
            ),
        ],
        actions=[
            RuleAction(
                action_type=RuleActionType.ISSUE_INTEGRAL,
                parameters={"amount": 50, "reason": "正确连接D9引脚奖励"},
            ),
            RuleAction(
                action_type=RuleActionType.SEND_NOTIFICATION,
                parameters={"message": "恭喜！正确连接D9引脚获得50积分奖励！"},
            ),
        ],
        priority=20,
        cooldown_seconds=300,
    ),
    "ar_placement_completion": GamificationRule(
        rule_id="template_ar_placement_completion",
        name="AR元件放置完成奖励模板",
        description="用户在AR场景中正确放置虚拟元件时奖励积分和徽章",
        conditions=[
            RuleCondition(
                condition_type=RuleConditionType.AR_COMPONENT_PLACEMENT,
                operator=RuleOperator.EQUAL,
                value=True,
            ),
            RuleCondition(
                condition_type=RuleConditionType.CUSTOM_METRIC,
                operator=RuleOperator.GREATER_EQUAL,
                value=0.95,
                field_name="placement_accuracy",
            ),
        ],
        actions=[
            RuleAction(
                action_type=RuleActionType.ISSUE_INTEGRAL,
                parameters={"amount": 100, "reason": "AR元件正确放置奖励"},
            ),
            RuleAction(
                action_type=RuleActionType.GRANT_BADGE,
                parameters={
                    "badge_name": "AR工程师",
                    "badge_description": "成功完成AR元件放置任务",
                },
            ),
            RuleAction(
                action_type=RuleActionType.SEND_NOTIFICATION,
                parameters={"message": "太棒了！获得AR工程师徽章和100积分！"},
            ),
        ],
        priority=25,
        cooldown_seconds=600,
    ),
    "hidden_gesture_unlock": GamificationRule(
        rule_id="template_hidden_gesture_unlock",
        name="隐藏手势任务解锁模板",
        description="用户完成特定手势序列时解锁隐藏任务",
        conditions=[
            RuleCondition(
                condition_type=RuleConditionType.GESTURE_SEQUENCE,
                operator=RuleOperator.EQUAL,
                value=True,
            ),
            RuleCondition(
                condition_type=RuleConditionType.CUSTOM_METRIC,
                operator=RuleOperator.EQUAL,
                value="spiderman_then_ok",
                field_name="gesture_sequence",
            ),
        ],
        actions=[
            RuleAction(
                action_type=RuleActionType.UNLOCK_HIDDEN_FEATURE,
                parameters={
                    "feature_name": "秘密实验室",
                    "unlock_condition": "完成蜘蛛侠+OK手势组合",
                },
            ),
            RuleAction(
                action_type=RuleActionType.ISSUE_INTEGRAL,
                parameters={"amount": 200, "reason": "发现隐藏任务奖励"},
            ),
            RuleAction(
                action_type=RuleActionType.SEND_NOTIFICATION,
                parameters={"message": "恭喜发现秘密实验室！获得200积分奖励！"},
            ),
        ],
        priority=30,
        cooldown_seconds=3600,
        max_executions=1,
    ),
}

# 测试代码
if __name__ == "__main__":
    # 创建测试规则
    test_rule = GamificationRule(
        rule_id="test_rule_001",
        name="测试规则",
        description="用于测试的规则",
        conditions=[
            RuleCondition(
                condition_type=RuleConditionType.SUCCESS_COUNT,
                operator=RuleOperator.GREATER_EQUAL,
                value=5,
            ),
            RuleCondition(
                condition_type=RuleConditionType.TIME_SPENT,
                operator=RuleOperator.LESS_THAN,
                value=30,
            ),
        ],
        actions=[
            RuleAction(
                action_type=RuleActionType.ADJUST_DIFFICULTY,
                parameters={"adjustment_value": 1.0, "direction": "increase"},
            )
        ],
        priority=5,
        cooldown_seconds=600,
    )

    print("=== 规则测试 ===")
    print(f"规则ID: {test_rule.rule_id}")
    print(f"规则名称: {test_rule.name}")
    print(f"优先级: {test_rule.priority}")
    print(f"冷却时间: {test_rule.cooldown_seconds}秒")

    # 测试条件评估
    test_context = {"success_count": 6, "time_spent": 25}

    conditions_met = test_rule.evaluate_conditions(test_context)
    print(f"\n条件评估结果: {conditions_met}")

    if conditions_met:
        results = test_rule.execute_actions(test_context)
        print("动作执行结果:")
        for result in results:
            print(f"  - 动作类型: {result['action_type']}")
            print(f"  - 执行成功: {result['success']}")

    # 测试配置序列化
    config = RuleEngineConfig()
    config.add_rule(test_rule)

    config_dict = config.to_dict()
    print(f"\n配置序列化长度: {len(json.dumps(config_dict))} 字符")

    # 测试反序列化
    restored_config = RuleEngineConfig.from_dict(config_dict)
    print(f"恢复的规则数量: {len(restored_config.rules)}")
