"""
规则评估引擎
实现规则条件评估、决策树执行等核心逻辑
"""

import asyncio
from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List, Optional, Set

from ..models.rule_engine import (
    GamificationRule,
    RuleAction,
    RuleCondition,
    RuleExecutionContext,
)
from ..models.task_adjustment import StreakCounter

logger = logging.getLogger(__name__)


class RuleEvaluationEngine:
    """规则评估引擎"""

    def __init__(self):
        self.evaluation_cache: Dict[str, Any] = {}
        self.streak_trackers: Dict[str, StreakCounter] = {}
        self.rule_hit_counts: Dict[str, int] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def evaluate_rule_set(
        self, rules: List[GamificationRule], context: RuleExecutionContext
    ) -> List[Dict[str, Any]]:
        """
        评估规则集合

        Args:
            rules: 规则列表
            context: 执行上下文

        Returns:
            匹配的规则及其执行结果
        """
        matched_rules = []

        # 按优先级排序
        sorted_rules = sorted(rules, key=lambda r: r.priority, reverse=True)

        for rule in sorted_rules:
            if not rule.is_active:
                continue

            # 检查冷却期
            if not self._check_cooldown(rule):
                continue

            # 评估规则条件
            if self._evaluate_rule_conditions(rule, context):
                # 执行规则动作
                execution_result = self._execute_rule_actions(rule, context)

                # 记录执行历史
                self._record_execution(rule, context, execution_result)

                # 更新统计
                self._update_statistics(rule.rule_id)

                matched_rules.append(
                    {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "execution_result": execution_result,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return matched_rules

    def _evaluate_rule_conditions(
        self, rule: GamificationRule, context: RuleExecutionContext
    ) -> bool:
        """评估单个规则的所有条件"""
        try:
            context_dict = context.to_dict()

            # 所有条件必须满足(AND关系)
            for condition in rule.conditions:
                if not self._evaluate_single_condition(condition, context_dict):
                    return False

            return True

        except Exception as e:
            logger.error(f"规则条件评估失败: {e}")
            return False

    def _evaluate_single_condition(
        self, condition: RuleCondition, context: Dict[str, Any]
    ) -> bool:
        """评估单个条件"""
        try:
            # 获取比较值
            if condition.field_name:
                actual_value = context.get("metrics", {}).get(condition.field_name)
            else:
                actual_value = context.get("metrics", {}).get(
                    condition.condition_type.value
                )

            if actual_value is None:
                return False

            # 执行比较操作
            return self._perform_comparison(
                actual_value, condition.operator, condition.value
            )

        except Exception as e:
            logger.error(f"条件评估失败: {e}")
            return False

    def _perform_comparison(
        self, actual_value: Any, operator: str, expected_value: Any
    ) -> bool:
        """执行比较操作"""
        try:
            if operator == "==":
                return actual_value == expected_value
            elif operator == "!=":
                return actual_value != expected_value
            elif operator == ">":
                return actual_value > expected_value
            elif operator == "<":
                return actual_value < expected_value
            elif operator == ">=":
                return actual_value >= expected_value
            elif operator == "<=":
                return actual_value <= expected_value
            elif operator == "between":
                if isinstance(expected_value, list) and len(expected_value) == 2:
                    return expected_value[0] <= actual_value <= expected_value[1]
                return False
            else:
                logger.warning(f"未知的操作符: {operator}")
                return False

        except Exception as e:
            logger.error(f"比较操作失败: {e}")
            return False

    def _execute_rule_actions(
        self, rule: GamificationRule, context: RuleExecutionContext
    ) -> List[Dict[str, Any]]:
        """执行规则动作"""
        results = []

        for action in rule.actions:
            try:
                result = self._execute_single_action(action, context)
                results.append(result)
            except Exception as e:
                logger.error(f"执行动作失败: {e}")
                results.append(
                    {
                        "action_type": action.action_type.value,
                        "success": False,
                        "error": str(e),
                    }
                )

        return results

    def _execute_single_action(
        self, action: RuleAction, context: RuleExecutionContext
    ) -> Dict[str, Any]:
        """执行单个动作"""
        result = {
            "action_type": action.action_type.value,
            "parameters": action.parameters,
            "success": True,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # 根据动作类型执行不同的逻辑
            if action.action_type.value == "adjust_difficulty":
                self._handle_difficulty_adjustment(action, context, result)
            elif action.action_type.value == "send_notification":
                self._handle_send_notification(action, context, result)
            elif action.action_type.value == "grant_achievement":
                self._handle_grant_achievement(action, context, result)
            elif action.action_type.value == "update_user_profile":
                self._handle_update_user_profile(action, context, result)
            elif action.action_type.value == "trigger_event":
                self._handle_trigger_event(action, context, result)

        except Exception as e:
            logger.error(f"动作执行异常: {e}")
            result["success"] = False
            result["error"] = str(e)

        return result

    def _handle_difficulty_adjustment(
        self, action: RuleAction, context: RuleExecutionContext, result: Dict[str, Any]
    ):
        """处理难度调整动作"""
        adjustment_value = action.parameters.get("adjustment_value", 0)
        direction = action.parameters.get("direction", "increase")

        # 这里应该调用难度服务进行实际调整
        # 暂时只是记录
        result["adjustment_details"] = {
            "value": adjustment_value,
            "direction": direction,
            "user_id": context.user_id,
        }

        logger.info(
            f"执行难度调整: 用户={context.user_id}, 调整值={adjustment_value}, 方向={direction}"
        )

    def _handle_send_notification(
        self, action: RuleAction, context: RuleExecutionContext, result: Dict[str, Any]
    ):
        """处理发送通知动作"""
        message = action.parameters.get("message", "")
        notification_type = action.parameters.get("type", "info")

        # 这里应该调用通知服务
        result["notification_details"] = {
            "message": message,
            "type": notification_type,
            "user_id": context.user_id,
        }

        logger.info(f"发送通知: 用户={context.user_id}, 消息={message}")

    def _handle_grant_achievement(
        self, action: RuleAction, context: RuleExecutionContext, result: Dict[str, Any]
    ):
        """处理授予成就动作"""
        achievement_id = action.parameters.get("achievement_id", "")
        achievement_name = action.parameters.get("achievement_name", "")

        # 这里应该调用成就服务
        result["achievement_details"] = {
            "achievement_id": achievement_id,
            "achievement_name": achievement_name,
            "user_id": context.user_id,
        }

        logger.info(f"授予成就: 用户={context.user_id}, 成就={achievement_name}")

    def _handle_update_user_profile(
        self, action: RuleAction, context: RuleExecutionContext, result: Dict[str, Any]
    ):
        """处理更新用户档案动作"""
        updates = action.parameters.get("updates", {})

        # 这里应该调用用户服务
        result["profile_updates"] = {"updates": updates, "user_id": context.user_id}

        logger.info(f"更新用户档案: 用户={context.user_id}, 更新={updates}")

    def _handle_trigger_event(
        self, action: RuleAction, context: RuleExecutionContext, result: Dict[str, Any]
    ):
        """处理触发事件动作"""
        event_name = action.parameters.get("event_name", "")
        event_data = action.parameters.get("event_data", {})

        # 这里应该调用事件总线
        result["event_details"] = {
            "event_name": event_name,
            "event_data": event_data,
            "user_id": context.user_id,
        }

        logger.info(f"触发事件: 用户={context.user_id}, 事件={event_name}")

    def _check_cooldown(self, rule: GamificationRule) -> bool:
        """检查规则冷却期"""
        if rule.cooldown_seconds <= 0:
            return True

        if rule.last_execution_time is None:
            return True

        time_since_last = datetime.now() - rule.last_execution_time
        return time_since_last.total_seconds() >= rule.cooldown_seconds

    def _record_execution(
        self,
        rule: GamificationRule,
        context: RuleExecutionContext,
        result: List[Dict[str, Any]],
    ):
        """记录执行历史"""
        execution_record = {
            "rule_id": rule.rule_id,
            "user_id": context.user_id,
            "task_id": context.task_id,
            "event_type": context.event_type,
            "results": result,
            "timestamp": datetime.now().isoformat(),
        }

        self.execution_history.append(execution_record)

        # 限制历史记录数量
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

    def _update_statistics(self, rule_id: str):
        """更新统计信息"""
        self.rule_hit_counts[rule_id] = self.rule_hit_counts.get(rule_id, 0) + 1

    def get_rule_statistics(self) -> Dict[str, Any]:
        """获取规则执行统计"""
        return {
            "total_executions": len(self.execution_history),
            "rule_hit_counts": self.rule_hit_counts,
            "recent_executions": len(
                [
                    record
                    for record in self.execution_history
                    if datetime.fromisoformat(record["timestamp"])
                    > datetime.now() - timedelta(hours=1)
                ]
            ),
        }

    def get_execution_history(
        self, user_id: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """获取执行历史"""
        filtered_history = self.execution_history

        if user_id:
            filtered_history = [
                record for record in filtered_history if record["user_id"] == user_id
            ]

        return filtered_history[-limit:]


# 测试代码
if __name__ == "__main__":
    # 创建引擎实例
    engine = RuleEvaluationEngine()

    # 创建测试规则
    from ..models.rule_engine import RuleActionType, RuleConditionType, RuleOperator

    test_condition = RuleCondition(
        condition_type=RuleConditionType.SUCCESS_COUNT,
        operator=RuleOperator.GREATER_EQUAL,
        value=3,
    )

    test_action = RuleAction(
        action_type=RuleActionType.ADJUST_DIFFICULTY,
        parameters={"adjustment_value": 0.5, "direction": "increase"},
    )

    test_rule = GamificationRule(
        rule_id="test_rule_001",
        name="测试规则",
        description="用于测试的规则",
        conditions=[test_condition],
        actions=[test_action],
        priority=5,
    )

    # 创建测试上下文
    test_context = RuleExecutionContext(
        user_id="test_user_001",
        task_id="test_task_001",
        event_type="task_completed",
        metrics={"success_count": 5, "completion_time": 25},
    )

    print("=== 规则评估引擎测试 ===")

    # 测试规则评估
    results = engine.evaluate_rule_set([test_rule], test_context)
    print(f"匹配规则数量: {len(results)}")

    if results:
        print(f"执行结果: {results[0]}")

    # 测试统计信息
    stats = engine.get_rule_statistics()
    print(f"统计信息: {stats}")
