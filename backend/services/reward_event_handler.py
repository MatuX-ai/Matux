"""
奖励事件处理器
处理来自事件总线的各种奖励事件并执行相应操作
"""

import asyncio
from datetime import datetime
import logging
from typing import Any, Dict, Optional

from gamification.services.rule_engine_service import RuleEngineService
from services.blockchain.gateway_service import BlockchainGatewayService
from .reward_event_bus import (
    RewardEvent,
    RewardEventBus,
    RewardEventType,
    get_event_bus,
    reward_event_handler,
)

logger = logging.getLogger(__name__)


class RewardEventHandler:
    """奖励事件处理器"""

    def __init__(
        self,
        rule_engine: RuleEngineService,
        blockchain_service: BlockchainGatewayService,
    ):
        self.rule_engine = rule_engine
        self.blockchain_service = blockchain_service
        self.event_bus = get_event_bus()
        self._setup_handlers()

    def _setup_handlers(self):
        """设置事件处理器"""
        # 语音纠错奖励处理器
        self.event_bus.subscribe(
            RewardEventType.VOICE_CORRECTION,
            self._handle_voice_correction,
            self._voice_correction_filter,
        )

        # AR元件放置奖励处理器
        self.event_bus.subscribe(
            RewardEventType.AR_COMPONENT_PLACEMENT,
            self._handle_ar_placement,
            self._ar_placement_filter,
        )

        # 手势序列奖励处理器
        self.event_bus.subscribe(
            RewardEventType.GESTURE_SEQUENCE,
            self._handle_gesture_sequence,
            self._gesture_sequence_filter,
        )

        # 多模态任务完成处理器
        self.event_bus.subscribe(
            RewardEventType.MULTIMODAL_COMPLETION,
            self._handle_multimodal_completion,
            self._multimodal_completion_filter,
        )

        # 隐藏任务触发处理器
        self.event_bus.subscribe(
            RewardEventType.HIDDEN_TASK_TRIGGER,
            self._handle_hidden_task,
            self._hidden_task_filter,
        )

    async def _handle_voice_correction(self, event: RewardEvent):
        """处理语音纠错事件"""
        try:
            payload = event.payload
            correction_type = payload.get("correction_type", "")
            accuracy = payload.get("accuracy", 0.0)
            pin_name = payload.get("pin_name", "")

            logger.info(f"处理语音纠错: {correction_type} - 准确率: {accuracy}")

            # 构建游戏化上下文
            context_data = {
                "voice_correction": True,
                "correction_type": correction_type,
                "accuracy": accuracy,
                "pin_name": pin_name,
                "timestamp": event.timestamp.isoformat(),
            }

            # 触发游戏化规则
            rule_results = await self.rule_engine.process_user_event(
                user_id=event.user_id,
                event_type="voice_correction",
                event_data=context_data,
            )

            # 处理积分奖励
            points_awarded = 0
            for result in rule_results:
                if "action_results" in result:
                    for action_result in result["action_results"]:
                        if action_result.get("action_type") == "issue_integral":
                            points_awarded += action_result.get("amount", 0)

            # 如果有积分奖励，通过区块链发放
            if points_awarded > 0:
                try:
                    tx_result = await self.blockchain_service.issue_integral(
                        student_id=event.user_id,
                        amount=points_awarded,
                        issuer_id=1,  # 系统ID
                        description=f"语音纠错奖励 - {correction_type}",
                    )
                    logger.info(f"区块链积分发放成功: {tx_result}")
                except Exception as e:
                    logger.error(f"区块链积分发放失败: {e}")

            return {
                "success": True,
                "points_awarded": points_awarded,
                "rule_results": len(rule_results),
                "correction_type": correction_type,
            }

        except Exception as e:
            logger.error(f"处理语音纠错事件失败: {e}")
            raise

    def _voice_correction_filter(self, event: RewardEvent) -> bool:
        """语音纠错事件过滤器"""
        payload = event.payload
        accuracy = payload.get("accuracy", 0.0)
        correction_type = payload.get("correction_type", "")

        # 只处理准确率大于80%的纠错事件
        return accuracy >= 0.8 and correction_type in [
            "pin_connection",
            "component_identification",
        ]

    async def _handle_ar_placement(self, event: RewardEvent):
        """处理AR元件放置事件"""
        try:
            payload = event.payload
            component_type = payload.get("component_type", "")
            placement_accuracy = payload.get("placement_accuracy", 0.0)
            scene_id = payload.get("scene_id", "")

            logger.info(
                f"处理AR元件放置: {component_type} - 精度: {placement_accuracy}"
            )

            # 构建游戏化上下文
            context_data = {
                "ar_component_placement": True,
                "component_type": component_type,
                "placement_accuracy": placement_accuracy,
                "scene_id": scene_id,
                "timestamp": event.timestamp.isoformat(),
            }

            # 触发游戏化规则
            rule_results = await self.rule_engine.process_user_event(
                user_id=event.user_id,
                event_type="ar_component_placement",
                event_data=context_data,
            )

            # 处理奖励
            points_awarded = 0
            badges_granted = []

            for result in rule_results:
                if "action_results" in result:
                    for action_result in result["action_results"]:
                        if action_result.get("action_type") == "issue_integral":
                            points_awarded += action_result.get("amount", 0)
                        elif action_result.get("action_type") == "grant_badge":
                            badges_granted.append(action_result.get("badge_name", ""))

            # 发放积分奖励
            if points_awarded > 0:
                try:
                    await self.blockchain_service.issue_integral(
                        student_id=event.user_id,
                        amount=points_awarded,
                        issuer_id=1,
                        description=f"AR元件放置奖励 - {component_type}",
                    )
                except Exception as e:
                    logger.error(f"AR奖励积分发放失败: {e}")

            return {
                "success": True,
                "points_awarded": points_awarded,
                "badges_granted": badges_granted,
                "component_type": component_type,
                "placement_accuracy": placement_accuracy,
            }

        except Exception as e:
            logger.error(f"处理AR元件放置事件失败: {e}")
            raise

    def _ar_placement_filter(self, event: RewardEvent) -> bool:
        """AR元件放置事件过滤器"""
        payload = event.payload
        placement_accuracy = payload.get("placement_accuracy", 0.0)
        component_type = payload.get("component_type", "")

        # 只处理精度大于90%的放置事件
        valid_components = ["esp32", "sensor", "actuator", "display"]
        return placement_accuracy >= 0.9 and component_type.lower() in valid_components

    async def _handle_gesture_sequence(self, event: RewardEvent):
        """处理手势序列事件"""
        try:
            payload = event.payload
            gesture_sequence = payload.get("gesture_sequence", "")
            sequence_length = payload.get("sequence_length", 0)
            completion_time = payload.get("completion_time", 0)

            logger.info(f"处理手势序列: {gesture_sequence} - 长度: {sequence_length}")

            # 构建游戏化上下文
            context_data = {
                "gesture_sequence": True,
                "sequence_pattern": gesture_sequence,
                "sequence_length": sequence_length,
                "completion_time": completion_time,
                "timestamp": event.timestamp.isoformat(),
            }

            # 触发游戏化规则
            rule_results = await self.rule_engine.process_user_event(
                user_id=event.user_id,
                event_type="gesture_sequence",
                event_data=context_data,
            )

            # 处理隐藏任务奖励
            hidden_features_unlocked = []
            points_awarded = 0

            for result in rule_results:
                if "action_results" in result:
                    for action_result in result["action_results"]:
                        if action_result.get("action_type") == "issue_integral":
                            points_awarded += action_result.get("amount", 0)
                        elif (
                            action_result.get("action_type") == "unlock_hidden_feature"
                        ):
                            hidden_features_unlocked.append(
                                action_result.get("feature_name", "")
                            )

            # 发放奖励
            if points_awarded > 0:
                try:
                    await self.blockchain_service.issue_integral(
                        student_id=event.user_id,
                        amount=points_awarded,
                        issuer_id=1,
                        description=f"手势序列奖励 - {gesture_sequence}",
                    )
                except Exception as e:
                    logger.error(f"手势奖励积分发放失败: {e}")

            return {
                "success": True,
                "points_awarded": points_awarded,
                "hidden_features_unlocked": hidden_features_unlocked,
                "gesture_sequence": gesture_sequence,
            }

        except Exception as e:
            logger.error(f"处理手势序列事件失败: {e}")
            raise

    def _gesture_sequence_filter(self, event: RewardEvent) -> bool:
        """手势序列事件过滤器"""
        payload = event.payload
        sequence_length = payload.get("sequence_length", 0)
        gesture_sequence = payload.get("gesture_sequence", "")

        # 只处理长度大于等于2的手势序列
        valid_sequences = [
            "spiderman_then_ok",
            "victory_then_thumb_up",
            "point_then_circle",
        ]
        return sequence_length >= 2 and gesture_sequence in valid_sequences

    async def _handle_multimodal_completion(self, event: RewardEvent):
        """处理多模态任务完成事件"""
        try:
            payload = event.payload
            task_id = payload.get("task_id", "")
            modalities_used = payload.get("modalities_used", [])
            completion_score = payload.get("completion_score", 0.0)

            logger.info(
                f"处理多模态任务完成: {task_id} - 模态数: {len(modalities_used)}"
            )

            # 构建游戏化上下文
            context_data = {
                "multimodal_completion": True,
                "task_id": task_id,
                "modalities_count": len(modalities_used),
                "modalities_used": modalities_used,
                "completion_score": completion_score,
                "timestamp": event.timestamp.isoformat(),
            }

            # 触发游戏化规则
            rule_results = await self.rule_engine.process_user_event(
                user_id=event.user_id,
                event_type="multimodal_completion",
                event_data=context_data,
            )

            # 处理奖励
            points_awarded = 0
            achievements_granted = []

            for result in rule_results:
                if "action_results" in result:
                    for action_result in result["action_results"]:
                        if action_result.get("action_type") == "issue_integral":
                            points_awarded += action_result.get("amount", 0)
                        elif action_result.get("action_type") == "grant_achievement":
                            achievements_granted.append(
                                action_result.get("achievement_name", "")
                            )

            # 发放奖励
            if points_awarded > 0:
                try:
                    await self.blockchain_service.issue_integral(
                        student_id=event.user_id,
                        amount=points_awarded,
                        issuer_id=1,
                        description=f"多模态任务完成奖励 - {task_id}",
                    )
                except Exception as e:
                    logger.error(f"多模态奖励积分发放失败: {e}")

            return {
                "success": True,
                "points_awarded": points_awarded,
                "achievements_granted": achievements_granted,
                "modalities_used": modalities_used,
            }

        except Exception as e:
            logger.error(f"处理多模态任务完成事件失败: {e}")
            raise

    def _multimodal_completion_filter(self, event: RewardEvent) -> bool:
        """多模态任务完成事件过滤器"""
        payload = event.payload
        modalities_used = payload.get("modalities_used", [])
        completion_score = payload.get("completion_score", 0.0)

        # 只处理使用至少2种模态且完成度大于80%的任务
        return len(modalities_used) >= 2 and completion_score >= 0.8

    async def _handle_hidden_task(self, event: RewardEvent):
        """处理隐藏任务触发事件"""
        try:
            payload = event.payload
            hidden_task_id = payload.get("hidden_task_id", "")
            trigger_condition = payload.get("trigger_condition", "")
            discovery_method = payload.get("discovery_method", "")

            logger.info(f"处理隐藏任务触发: {hidden_task_id}")

            # 构建游戏化上下文
            context_data = {
                "hidden_task_trigger": True,
                "hidden_task_id": hidden_task_id,
                "trigger_condition": trigger_condition,
                "discovery_method": discovery_method,
                "timestamp": event.timestamp.isoformat(),
            }

            # 触发游戏化规则
            rule_results = await self.rule_engine.process_user_event(
                user_id=event.user_id,
                event_type="hidden_task_trigger",
                event_data=context_data,
            )

            # 处理特殊奖励
            special_rewards = []
            points_awarded = 0

            for result in rule_results:
                if "action_results" in result:
                    for action_result in result["action_results"]:
                        if action_result.get("action_type") == "issue_integral":
                            points_awarded += action_result.get("amount", 0)
                        elif (
                            action_result.get("action_type") == "trigger_special_effect"
                        ):
                            special_rewards.append(
                                {
                                    "effect": action_result.get("effect_name", ""),
                                    "duration": action_result.get("duration", 0),
                                }
                            )

            # 发放奖励
            if points_awarded > 0:
                try:
                    await self.blockchain_service.issue_integral(
                        student_id=event.user_id,
                        amount=points_awarded,
                        issuer_id=1,
                        description=f"隐藏任务奖励 - {hidden_task_id}",
                    )
                except Exception as e:
                    logger.error(f"隐藏任务奖励积分发放失败: {e}")

            return {
                "success": True,
                "points_awarded": points_awarded,
                "special_rewards": special_rewards,
                "hidden_task_id": hidden_task_id,
            }

        except Exception as e:
            logger.error(f"处理隐藏任务触发事件失败: {e}")
            raise

    def _hidden_task_filter(self, event: RewardEvent) -> bool:
        """隐藏任务触发事件过滤器"""
        payload = event.payload
        hidden_task_id = payload.get("hidden_task_id", "")

        # 只处理有效的隐藏任务
        valid_tasks = ["secret_lab_access", "advanced_mode_unlock", "easter_egg_found"]
        return hidden_task_id in valid_tasks


# 全局事件处理器实例
_global_event_handler: Optional[RewardEventHandler] = None


def get_event_handler() -> Optional[RewardEventHandler]:
    """获取全局事件处理器实例"""
    global _global_event_handler
    return _global_event_handler


def set_event_handler(handler: RewardEventHandler):
    """设置全局事件处理器实例"""
    global _global_event_handler
    _global_event_handler = handler


# 便捷函数
async def emit_voice_correction_event(
    user_id: str, correction_type: str, accuracy: float, pin_name: str = ""
):
    """发出语音纠错事件"""
    event_bus = get_event_bus()
    return await event_bus.publish_simple(
        RewardEventType.VOICE_CORRECTION,
        user_id,
        {
            "correction_type": correction_type,
            "accuracy": accuracy,
            "pin_name": pin_name,
        },
    )


async def emit_ar_placement_event(
    user_id: str, component_type: str, placement_accuracy: float, scene_id: str = ""
):
    """发出AR元件放置事件"""
    event_bus = get_event_bus()
    return await event_bus.publish_simple(
        RewardEventType.AR_COMPONENT_PLACEMENT,
        user_id,
        {
            "component_type": component_type,
            "placement_accuracy": placement_accuracy,
            "scene_id": scene_id,
        },
    )


async def emit_gesture_sequence_event(
    user_id: str,
    gesture_sequence: str,
    sequence_length: int,
    completion_time: float = 0,
):
    """发出手势序列事件"""
    event_bus = get_event_bus()
    return await event_bus.publish_simple(
        RewardEventType.GESTURE_SEQUENCE,
        user_id,
        {
            "gesture_sequence": gesture_sequence,
            "sequence_length": sequence_length,
            "completion_time": completion_time,
        },
    )
