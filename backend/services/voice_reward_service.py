"""
语音奖励服务
专门处理语音纠错相关的积分奖励发放和区块链集成
"""

import asyncio
from datetime import datetime
import json
import logging
from typing import Any, Dict, List, Optional

from services.blockchain.gateway_service import BlockchainGatewayService
from services.reward_event_bus import RewardEventBus, RewardEventType, get_event_bus
from services.voice_correction_detector import (
    CorrectionType,
    VoiceCorrectionDetector,
    VoiceCorrectionResult,
)

logger = logging.getLogger(__name__)


class VoiceRewardService:
    """语音奖励服务"""

    def __init__(self, blockchain_service: BlockchainGatewayService):
        self.blockchain_service = blockchain_service
        self.event_bus = get_event_bus()
        self.correction_detector = VoiceCorrectionDetector()
        self._setup_event_handlers()

        # 奖励配置
        self.reward_configs = {
            CorrectionType.PIN_CONNECTION: {
                "base_points": 50,
                "accuracy_multiplier": 20,
                "max_points": 100,
                "description": "引脚连接纠错奖励",
            },
            CorrectionType.COMPONENT_IDENTIFICATION: {
                "base_points": 30,
                "accuracy_multiplier": 15,
                "max_points": 80,
                "description": "元件识别纠错奖励",
            },
            CorrectionType.WIRING_SEQUENCE: {
                "base_points": 70,
                "accuracy_multiplier": 25,
                "max_points": 120,
                "description": "接线顺序纠错奖励",
            },
            CorrectionType.CIRCUIT_CONFIGURATION: {
                "base_points": 80,
                "accuracy_multiplier": 30,
                "max_points": 150,
                "description": "电路配置纠错奖励",
            },
            CorrectionType.GENERAL_CORRECTION: {
                "base_points": 20,
                "accuracy_multiplier": 10,
                "max_points": 50,
                "description": "一般性纠错奖励",
            },
        }

    def _setup_event_handlers(self):
        """设置事件处理器"""
        self.event_bus.subscribe(
            RewardEventType.VOICE_CORRECTION,
            self._handle_voice_correction_event,
            self._voice_correction_event_filter,
        )

    async def _handle_voice_correction_event(self, event):
        """处理语音纠错事件"""
        try:
            user_id = event.user_id
            payload = event.payload

            logger.info(f"处理语音纠错事件: 用户 {user_id}")

            # 计算奖励积分
            points_awarded = await self._calculate_voice_reward(payload)

            if points_awarded > 0:
                # 发放积分奖励
                tx_result = await self._issue_voice_reward(
                    user_id, points_awarded, payload
                )

                # 记录奖励历史
                await self._record_voice_reward_history(
                    user_id, points_awarded, payload, tx_result
                )

                logger.info(
                    f"语音纠错奖励发放成功: 用户 {user_id}, 积分 {points_awarded}"
                )

                return {
                    "success": True,
                    "points_awarded": points_awarded,
                    "transaction_id": tx_result.get("tx_id"),
                    "user_id": user_id,
                }
            else:
                logger.info(f"语音纠错未达到奖励标准: 用户 {user_id}")
                return {
                    "success": True,
                    "points_awarded": 0,
                    "message": "纠错准确度不够，未获得奖励",
                }

        except Exception as e:
            logger.error(f"处理语音纠错事件失败: {e}")
            return {"success": False, "error": str(e)}

    def _voice_correction_event_filter(self, event) -> bool:
        """语音纠错事件过滤器"""
        payload = event.payload
        accuracy_score = payload.get("accuracy_score", 0.0)
        confidence = payload.get("confidence", 0.0)

        # 只处理准确度大于0.7且置信度大于0.6的纠错事件
        return accuracy_score >= 0.7 and confidence >= 0.6

    async def _calculate_voice_reward(self, payload: Dict[str, Any]) -> int:
        """计算语音纠错奖励积分"""
        try:
            correction_type_str = payload.get("correction_type", "general_correction")
            accuracy_score = payload.get("accuracy_score", 0.0)
            pin_name = payload.get("pin_name", "")

            # 转换纠错类型
            try:
                correction_type = CorrectionType(correction_type_str)
            except ValueError:
                correction_type = CorrectionType.GENERAL_CORRECTION

            # 获取奖励配置
            config = self.reward_configs.get(
                correction_type, self.reward_configs[CorrectionType.GENERAL_CORRECTION]
            )

            # 计算基础积分
            base_points = config["base_points"]

            # 根据准确度计算奖励倍数
            accuracy_bonus = int(config["accuracy_multiplier"] * accuracy_score)

            # 特殊引脚奖励加成
            special_pin_bonus = 0
            if pin_name.upper() in ["D9", "A0", "SDA", "SCL"]:
                special_pin_bonus = 10  # 特殊引脚额外奖励

            total_points = base_points + accuracy_bonus + special_pin_bonus

            # 限制最大奖励
            total_points = min(total_points, config["max_points"])

            logger.debug(
                f"语音奖励计算: 类型={correction_type.value}, "
                f"准确度={accuracy_score:.2f}, 基础={base_points}, "
                f"准确度奖励={accuracy_bonus}, 特殊奖励={special_pin_bonus}, "
                f"总计={total_points}"
            )

            return total_points

        except Exception as e:
            logger.error(f"计算语音奖励失败: {e}")
            return 0

    async def _issue_voice_reward(
        self, user_id: str, points: int, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """发放语音纠错奖励积分"""
        try:
            correction_type = payload.get("correction_type", "general")
            description = f"语音纠错奖励 - {correction_type}"

            # 通过区块链服务发放积分
            tx_result = await self.blockchain_service.issue_integral(
                student_id=user_id,
                amount=points,
                issuer_id=1,  # 系统ID
                description=description,
            )

            return tx_result

        except Exception as e:
            logger.error(f"发放语音奖励积分失败: {e}")
            raise

    async def _record_voice_reward_history(
        self,
        user_id: str,
        points: int,
        payload: Dict[str, Any],
        tx_result: Dict[str, Any],
    ):
        """记录语音奖励历史"""
        try:
            reward_record = {
                "user_id": user_id,
                "points_awarded": points,
                "correction_type": payload.get("correction_type"),
                "accuracy_score": payload.get("accuracy_score"),
                "confidence": payload.get("confidence"),
                "pin_name": payload.get("pin_name"),
                "transaction_id": tx_result.get("tx_id"),
                "timestamp": datetime.now().isoformat(),
                "reward_type": "voice_correction",
            }

            # 这里可以保存到数据库或文件
            logger.debug(
                f"记录语音奖励历史: {json.dumps(reward_record, ensure_ascii=False)}"
            )

        except Exception as e:
            logger.error(f"记录语音奖励历史失败: {e}")

    async def process_voice_correction(
        self, user_id: str, voice_transcript: str
    ) -> Dict[str, Any]:
        """
        处理语音纠错并发放奖励

        Args:
            user_id: 用户ID
            voice_transcript: 语音转录文本

        Returns:
            Dict: 处理结果和奖励信息
        """
        try:
            # 检测语音纠错
            correction_result = self.correction_detector.detect_corrections(
                voice_transcript
            )

            if correction_result.confidence < 0.6:
                return {
                    "success": True,
                    "message": "未检测到有效的纠错行为",
                    "confidence": correction_result.confidence,
                }

            # 计算奖励积分
            points_awarded = await self._calculate_voice_reward(
                {
                    "correction_type": correction_result.correction_type.value,
                    "accuracy_score": correction_result.accuracy_score,
                    "confidence": correction_result.confidence,
                    "pin_name": "",  # 可以从detected_corrections中提取
                }
            )

            result = {
                "success": True,
                "correction_detected": True,
                "correction_type": correction_result.correction_type.value,
                "confidence": correction_result.confidence,
                "accuracy_score": correction_result.accuracy_score,
                "points_calculated": points_awarded,
            }

            # 如果有奖励，发放积分
            if points_awarded > 0:
                tx_result = await self._issue_voice_reward(
                    user_id,
                    points_awarded,
                    {
                        "correction_type": correction_result.correction_type.value,
                        "accuracy_score": correction_result.accuracy_score,
                    },
                )

                await self._record_voice_reward_history(
                    user_id,
                    points_awarded,
                    {
                        "correction_type": correction_result.correction_type.value,
                        "accuracy_score": correction_result.accuracy_score,
                    },
                    tx_result,
                )

                result.update(
                    {
                        "points_awarded": points_awarded,
                        "transaction_id": tx_result.get("tx_id"),
                        "message": f"恭喜！语音纠错成功，获得 {points_awarded} 积分奖励！",
                    }
                )
            else:
                result["message"] = "检测到纠错行为，但准确度不够获得奖励"

            return result

        except Exception as e:
            logger.error(f"处理语音纠错失败: {e}")
            return {"success": False, "error": str(e)}

    def get_voice_reward_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的语音奖励统计

        Args:
            user_id: 用户ID

        Returns:
            Dict: 统计信息
        """
        # 这里可以从数据库查询用户的语音奖励历史
        # 暂时返回示例数据
        return {
            "user_id": user_id,
            "total_voice_rewards": 0,
            "total_points_earned": 0,
            "favorite_correction_type": "unknown",
            "recent_rewards": [],
        }

    async def batch_process_voice_corrections(
        self, corrections_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量处理语音纠错

        Args:
            corrections_data: 纠错数据列表

        Returns:
            List[Dict]: 处理结果列表
        """
        tasks = []
        for data in corrections_data:
            task = self.process_voice_correction(
                data["user_id"], data["voice_transcript"]
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {"index": i, "success": False, "error": str(result)}
                )
            else:
                processed_results.append(result)

        return processed_results


# 全局语音奖励服务实例
_global_voice_reward_service: Optional[VoiceRewardService] = None


def get_voice_reward_service(
    blockchain_service: BlockchainGatewayService = None,
) -> VoiceRewardService:
    """获取全局语音奖励服务实例"""
    global _global_voice_reward_service
    if _global_voice_reward_service is None:
        if blockchain_service is None:
            raise ValueError("首次获取服务时必须提供blockchain_service")
        _global_voice_reward_service = VoiceRewardService(blockchain_service)
    return _global_voice_reward_service


# 便捷函数
async def process_voice_correction_with_reward(
    user_id: str, voice_transcript: str, blockchain_service: BlockchainGatewayService
) -> Dict[str, Any]:
    """处理语音纠错并发放奖励的便捷函数"""
    service = get_voice_reward_service(blockchain_service)
    return await service.process_voice_correction(user_id, voice_transcript)


# 测试代码
if __name__ == "__main__":
    import asyncio

    async def test_voice_reward_service():
        # 模拟区块链服务
        class MockBlockchainService:
            async def issue_integral(
                self, student_id: str, amount: int, issuer_id: int, description: str
            ):
                return {
                    "tx_id": f"tx_mock_{datetime.now().timestamp()}",
                    "student_id": student_id,
                    "amount": amount,
                    "timestamp": datetime.now().isoformat(),
                }

        # 创建服务实例
        mock_blockchain = MockBlockchainService()
        service = VoiceRewardService(mock_blockchain)

        # 测试用例
        test_cases = [
            {"user_id": "test_user_001", "voice_transcript": "D9引脚应该连接到LED"},
            {"user_id": "test_user_002", "voice_transcript": "A0应该连接温度传感器"},
            {"user_id": "test_user_003", "voice_transcript": "这个连接是错误的"},
        ]

        print("=== 语音奖励服务测试 ===")

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}:")
            print(f"用户: {test_case['user_id']}")
            print(f"语音: {test_case['voice_transcript']}")

            result = await service.process_voice_correction(
                test_case["user_id"], test_case["voice_transcript"]
            )

            print(f"结果: {result}")

    # 运行测试
    asyncio.run(test_voice_reward_service())
