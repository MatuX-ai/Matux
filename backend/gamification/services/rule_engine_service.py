"""
规则引擎服务
实现游戏化规则的核心执行逻辑和管理功能
"""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Set

# 添加项目根目录到路径
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from gamification.models.difficulty_level import DifficultyLevel
from gamification.models.rule_engine import (
    PREDEFINED_RULE_TEMPLATES,
    GamificationRule,
    RuleActionType,
    RuleConditionType,
    RuleEngineConfig,
    RuleExecutionContext,
)
from gamification.models.task_adjustment import (
    AdjustmentReason,
    AdjustmentType,
    StreakCounter,
)

logger = logging.getLogger(__name__)


class RuleEngineService:
    """规则引擎服务类"""

    def __init__(self, config: Optional[RuleEngineConfig] = None):
        self.config = config or RuleEngineConfig()
        self.streak_counters: Dict[str, StreakCounter] = {}
        self.last_execution_times: Dict[str, datetime] = {}
        self.rule_execution_counts: Dict[str, int] = defaultdict(int)
        self._load_default_rules()

    def _load_default_rules(self):
        """加载默认规则"""
        for template_name, template_rule in PREDEFINED_RULE_TEMPLATES.items():
            # 为每个模板创建具体规则实例
            rule_copy = self._clone_rule(template_rule)
            rule_copy.rule_id = f"default_{template_name}"
            self.config.add_rule(rule_copy)

        logger.info(f"加载了 {len(PREDEFINED_RULE_TEMPLATES)} 个默认规则")

    def _clone_rule(self, rule: GamificationRule) -> GamificationRule:
        """克隆规则对象"""
        from copy import deepcopy

        return deepcopy(rule)

    def create_streak_counter(self, user_id: str) -> StreakCounter:
        """创建或获取连胜计数器"""
        if user_id not in self.streak_counters:
            self.streak_counters[user_id] = StreakCounter(user_id=user_id)
        return self.streak_counters[user_id]

    async def process_user_event(
        self,
        user_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        task_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        处理用户事件并执行相应的规则

        Args:
            user_id: 用户ID
            event_type: 事件类型
            event_data: 事件数据
            task_id: 关联的任务ID

        Returns:
            执行结果列表
        """
        # 更新连胜计数器
        streak_counter = self.create_streak_counter(user_id)

        if event_type == "task_completed":
            success = event_data.get("success", False)
            if success:
                streak_triggered = streak_counter.record_success()
                event_data["consecutive_success"] = streak_counter.success_streak
                if streak_triggered:
                    event_data["success_streak_triggered"] = True
            else:
                streak_triggered = streak_counter.record_failure()
                event_data["consecutive_failure"] = streak_counter.failure_streak
                if streak_triggered:
                    event_data["failure_streak_triggered"] = True

        # 构建执行上下文
        context = RuleExecutionContext(
            user_id=user_id, task_id=task_id, event_type=event_type, metrics=event_data
        )

        # 执行匹配的规则
        results = await self._execute_matching_rules(context)

        return results

    async def _execute_matching_rules(
        self, context: RuleExecutionContext
    ) -> List[Dict[str, Any]]:
        """执行匹配的规则"""
        results = []
        current_time = datetime.now()
        active_rules = self.config.get_active_rules()

        # 按优先级排序执行
        for rule in active_rules:
            # 检查冷却期
            if not rule.can_execute(current_time):
                continue

            # 评估条件
            if rule.evaluate_conditions(context.to_dict()):
                try:
                    # 执行动作
                    action_results = rule.execute_actions(context.to_dict())

                    # 更新执行统计
                    rule.increment_execution_count()
                    self.rule_execution_counts[rule.rule_id] += 1

                    # 记录执行结果
                    execution_result = {
                        "rule_id": rule.rule_id,
                        "rule_name": rule.name,
                        "actions_executed": len(action_results),
                        "action_results": action_results,
                        "timestamp": current_time.isoformat(),
                    }
                    results.append(execution_result)

                    logger.info(f"规则 '{rule.name}' 执行成功，用户: {context.user_id}")

                except Exception as e:
                    logger.error(f"规则 '{rule.name}' 执行失败: {e}")
                    results.append(
                        {
                            "rule_id": rule.rule_id,
                            "rule_name": rule.name,
                            "error": str(e),
                            "timestamp": current_time.isoformat(),
                        }
                    )

        return results

    def get_user_streak_info(self, user_id: str) -> Dict[str, Any]:
        """获取用户连胜信息"""
        counter = self.streak_counters.get(user_id)
        if not counter:
            return {
                "success_streak": 0,
                "failure_streak": 0,
                "last_activity_time": None,
            }

        return {
            "success_streak": counter.success_streak,
            "failure_streak": counter.failure_streak,
            "last_activity_time": (
                counter.last_activity_time.isoformat()
                if counter.last_activity_time
                else None
            ),
        }

    def reset_user_streak(self, user_id: str):
        """重置用户连胜计数"""
        counter = self.streak_counters.get(user_id)
        if counter:
            counter.reset_counters()
            logger.info(f"重置用户 {user_id} 的连胜计数")

    def add_custom_rule(self, rule: GamificationRule) -> bool:
        """添加自定义规则"""
        try:
            self.config.add_rule(rule)
            logger.info(f"添加自定义规则: {rule.name}")
            return True
        except Exception as e:
            logger.error(f"添加规则失败: {e}")
            return False

    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        return self.config.remove_rule(rule_id)

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """更新规则配置"""
        for rule in self.config.rules:
            if rule.rule_id == rule_id:
                # 更新规则属性
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                rule.updated_at = datetime.now()
                logger.info(f"更新规则: {rule.name}")
                return True
        return False

    def get_rule_statistics(self) -> Dict[str, Any]:
        """获取规则执行统计"""
        return {
            "total_rules": len(self.config.rules),
            "active_rules": len(self.config.get_active_rules()),
            "rule_execution_counts": dict(self.rule_execution_counts),
            "streak_counter_count": len(self.streak_counters),
        }

    async def bulk_process_events(
        self, events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量处理用户事件

        Args:
            events: 事件列表 [{'user_id': str, 'event_type': str, 'event_data': dict}, ...]

        Returns:
            所有执行结果
        """
        tasks = []
        for event in events:
            task = self.process_user_event(
                user_id=event["user_id"],
                event_type=event["event_type"],
                event_data=event["event_data"],
                task_id=event.get("task_id"),
            )
            tasks.append(task)

        # 并发执行所有事件处理
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"事件 {i} 处理失败: {result}")
                processed_results.append(
                    {"event_index": i, "error": str(result), "success": False}
                )
            else:
                processed_results.extend(result)

        return processed_results

    def export_rules_config(self) -> str:
        """导出规则配置为JSON字符串"""
        config_dict = self.config.to_dict()
        return json.dumps(config_dict, indent=2, ensure_ascii=False)

    def import_rules_config(self, config_json: str) -> bool:
        """从JSON字符串导入规则配置"""
        try:
            config_dict = json.loads(config_json)
            new_config = RuleEngineConfig.from_dict(config_dict)
            self.config = new_config
            logger.info("规则配置导入成功")
            return True
        except Exception as e:
            logger.error(f"规则配置导入失败: {e}")
            return False

    def get_rules_by_condition_type(
        self, condition_type: RuleConditionType
    ) -> List[GamificationRule]:
        """根据条件类型获取规则"""
        matching_rules = []
        for rule in self.config.rules:
            for condition in rule.conditions:
                if condition.condition_type == condition_type:
                    matching_rules.append(rule)
                    break
        return matching_rules


# 测试代码
if __name__ == "__main__":
    import asyncio

    async def test_rule_engine():
        # 创建规则引擎服务
        service = RuleEngineService()

        print("=== 规则引擎服务测试 ===")

        # 测试用户事件处理
        event_data = {
            "success": True,
            "completion_time": 25,
            "hint_used": False,
            "success_count": 1,
        }

        # 模拟用户连续完成任务
        for i in range(4):
            results = await service.process_user_event(
                user_id="test_user_001",
                event_type="task_completed",
                event_data=event_data,
                task_id=f"task_{i+1:03d}",
            )

            print(f"第{i+1}次任务完成:")
            streak_info = service.get_user_streak_info("test_user_001")
            print(
                f"  连胜信息: 成功{streak_info['success_streak']}次, 失败{streak_info['failure_streak']}次"
            )

            if results:
                for result in results:
                    print(f"  触发规则: {result.get('rule_name', '未知')}")

        # 测试统计信息
        stats = service.get_rule_statistics()
        print(f"\n规则统计: {stats}")

        # 测试配置导出/导入
        config_str = service.export_rules_config()
        print(f"配置大小: {len(config_str)} 字符")

        # 测试批量处理
        bulk_events = [
            {
                "user_id": "bulk_user_001",
                "event_type": "task_completed",
                "event_data": {"success": True, "completion_time": 20},
                "task_id": "bulk_task_001",
            },
            {
                "user_id": "bulk_user_002",
                "event_type": "task_completed",
                "event_data": {"success": False, "completion_time": 45},
                "task_id": "bulk_task_002",
            },
        ]

        bulk_results = await service.bulk_process_events(bulk_events)
        print(f"批量处理结果数量: {len(bulk_results)}")

    # 运行测试
    asyncio.run(test_rule_engine())
