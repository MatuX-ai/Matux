"""
奖励事件总线服务
统一管理多模态激励系统的事件通信和分发
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class RewardEventType(str, Enum):
    """奖励事件类型枚举"""

    VOICE_CORRECTION = "voice_correction"  # 语音纠错事件
    AR_COMPONENT_PLACEMENT = "ar_component_placement"  # AR元件放置事件
    GESTURE_SEQUENCE = "gesture_sequence"  # 手势序列事件
    MULTIMODAL_COMPLETION = "multimodal_completion"  # 多模态任务完成事件
    HIDDEN_TASK_TRIGGER = "hidden_task_trigger"  # 隐藏任务触发事件
    INTEGRAL_DECAY = "integral_decay"  # 积分衰减事件
    SYSTEM_NOTIFICATION = "system_notification"  # 系统通知事件


@dataclass
class RewardEvent:
    """奖励事件数据结构"""

    event_id: str  # 事件ID
    event_type: RewardEventType  # 事件类型
    user_id: str  # 用户ID
    timestamp: datetime = field(default_factory=datetime.now)  # 时间戳
    payload: Dict[str, Any] = field(default_factory=dict)  # 事件负载数据
    priority: int = 0  # 事件优先级
    processed: bool = False  # 是否已处理
    processing_result: Optional[Dict[str, Any]] = None  # 处理结果


class EventSubscription:
    """事件订阅"""

    def __init__(
        self,
        event_type: RewardEventType,
        callback: Callable,
        filter_func: Optional[Callable] = None,
    ):
        self.event_type = event_type
        self.callback = callback
        self.filter_func = filter_func or (lambda event: True)
        self.subscription_id = f"sub_{id(self)}"


class RewardEventBus:
    """奖励事件总线"""

    def __init__(self):
        self.subscribers: Dict[RewardEventType, List[EventSubscription]] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_tasks: List[asyncio.Task] = []
        self.is_running = False
        self.max_concurrent_processors = 10

    async def start(self):
        """启动事件总线"""
        if self.is_running:
            logger.warning("事件总线已在运行中")
            return

        self.is_running = True
        logger.info("启动奖励事件总线")

        # 启动事件处理任务
        for i in range(self.max_concurrent_processors):
            task = asyncio.create_task(self._event_processor(f"processor_{i}"))
            self.processing_tasks.append(task)

    async def stop(self):
        """停止事件总线"""
        if not self.is_running:
            return

        self.is_running = False
        logger.info("停止奖励事件总线")

        # 取消所有处理任务
        for task in self.processing_tasks:
            task.cancel()

        # 等待任务完成
        await asyncio.gather(*self.processing_tasks, return_exceptions=True)
        self.processing_tasks.clear()

    def subscribe(
        self,
        event_type: RewardEventType,
        callback: Callable,
        filter_func: Optional[Callable] = None,
    ) -> str:
        """订阅事件"""
        subscription = EventSubscription(event_type, callback, filter_func)

        if event_type not in self.subscribers:
            self.subscribers[event_type] = []

        self.subscribers[event_type].append(subscription)
        logger.info(f"订阅事件 {event_type.value}: {subscription.subscription_id}")

        return subscription.subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """取消订阅"""
        for event_type, subscriptions in self.subscribers.items():
            for i, subscription in enumerate(subscriptions):
                if subscription.subscription_id == subscription_id:
                    subscriptions.pop(i)
                    logger.info(f"取消订阅: {subscription_id}")
                    return True
        return False

    async def publish(self, event: RewardEvent):
        """发布事件"""
        if not self.is_running:
            logger.warning("事件总线未运行，事件将被丢弃")
            return

        # 验证事件
        if not event.event_id or not event.user_id:
            logger.error("事件数据不完整")
            return

        await self.event_queue.put(event)
        logger.debug(f"发布事件: {event.event_type.value} - {event.event_id}")

    async def publish_simple(
        self,
        event_type: RewardEventType,
        user_id: str,
        payload: Dict[str, Any] = None,
        priority: int = 0,
    ) -> str:
        """简化版事件发布"""
        event_id = f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(self) % 10000}"

        event = RewardEvent(
            event_id=event_id,
            event_type=event_type,
            user_id=user_id,
            payload=payload or {},
            priority=priority,
        )

        await self.publish(event)
        return event_id

    async def _event_processor(self, processor_id: str):
        """事件处理器"""
        logger.info(f"启动事件处理器: {processor_id}")

        while self.is_running:
            try:
                # 从队列获取事件
                event = await self.event_queue.get()

                # 处理事件
                await self._process_event(event)

                # 标记任务完成
                self.event_queue.task_done()

            except asyncio.CancelledError:
                logger.info(f"事件处理器 {processor_id} 被取消")
                break
            except Exception as e:
                logger.error(f"事件处理器 {processor_id} 发生错误: {e}")

    async def _process_event(self, event: RewardEvent):
        """处理单个事件"""
        try:
            logger.debug(f"处理事件: {event.event_type.value} - {event.event_id}")

            # 查找订阅者
            subscribers = self.subscribers.get(event.event_type, [])

            if not subscribers:
                logger.debug(f"无订阅者处理事件: {event.event_type.value}")
                return

            # 并发通知所有符合条件的订阅者
            tasks = []
            for subscription in subscribers:
                if subscription.filter_func(event):
                    task = asyncio.create_task(
                        self._notify_subscriber(subscription, event)
                    )
                    tasks.append(task)

            # 等待所有通知完成
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            # 标记事件已处理
            event.processed = True

        except Exception as e:
            logger.error(f"处理事件失败 {event.event_id}: {e}")
            event.processing_result = {"error": str(e)}

    async def _notify_subscriber(
        self, subscription: EventSubscription, event: RewardEvent
    ):
        """通知订阅者"""
        try:
            logger.debug(f"通知订阅者: {subscription.subscription_id}")
            await subscription.callback(event)
        except Exception as e:
            logger.error(f"订阅者回调失败 {subscription.subscription_id}: {e}")

    def get_queue_size(self) -> int:
        """获取队列大小"""
        return self.event_queue.qsize()

    def get_subscription_stats(self) -> Dict[str, int]:
        """获取订阅统计"""
        stats = {}
        for event_type, subscriptions in self.subscribers.items():
            stats[event_type.value] = len(subscriptions)
        return stats

    async def wait_for_empty_queue(self, timeout: float = 30.0):
        """等待队列清空"""
        try:
            await asyncio.wait_for(self.event_queue.join(), timeout)
        except asyncio.TimeoutError:
            logger.warning("等待队列清空超时")


# 全局事件总线实例
_global_event_bus: Optional[RewardEventBus] = None


def get_event_bus() -> RewardEventBus:
    """获取全局事件总线实例"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = RewardEventBus()
    return _global_event_bus


def create_reward_event(
    event_type: RewardEventType, user_id: str, payload: Dict[str, Any] = None
) -> RewardEvent:
    """创建奖励事件"""
    event_id = (
        f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(str(payload)) % 10000}"
    )

    return RewardEvent(
        event_id=event_id,
        event_type=event_type,
        user_id=user_id,
        payload=payload or {},
        timestamp=datetime.now(),
    )


# 预定义的事件处理器装饰器
def reward_event_handler(event_type: RewardEventType, priority: int = 0):
    """奖励事件处理器装饰器"""

    def decorator(func):
        async def wrapper(event: RewardEvent):
            try:
                logger.info(f"处理 {event_type.value} 事件: {event.event_id}")
                result = await func(event)
                event.processing_result = {
                    "success": True,
                    "handler": func.__name__,
                    "result": result,
                }
                return result
            except Exception as e:
                logger.error(f"事件处理器 {func.__name__} 执行失败: {e}")
                event.processing_result = {
                    "success": False,
                    "handler": func.__name__,
                    "error": str(e),
                }
                raise

        return wrapper

    return decorator


# 测试代码
if __name__ == "__main__":
    import asyncio

    async def test_event_bus():
        # 创建事件总线
        bus = RewardEventBus()

        # 定义事件处理器
        @reward_event_handler(RewardEventType.VOICE_CORRECTION)
        async def handle_voice_correction(event: RewardEvent):
            print(f"处理语音纠错事件: {event.payload}")
            return {"status": "processed", "points_awarded": 50}

        @reward_event_handler(RewardEventType.AR_COMPONENT_PLACEMENT)
        async def handle_ar_placement(event: RewardEvent):
            print(f"处理AR放置事件: {event.payload}")
            return {"status": "processed", "points_awarded": 100}

        # 启动事件总线
        await bus.start()

        # 订阅事件
        bus.subscribe(RewardEventType.VOICE_CORRECTION, handle_voice_correction)
        bus.subscribe(RewardEventType.AR_COMPONENT_PLACEMENT, handle_ar_placement)

        # 发布测试事件
        await bus.publish_simple(
            RewardEventType.VOICE_CORRECTION,
            "test_user_001",
            {"correction": "D9引脚连接正确", "accuracy": 0.95},
        )

        await bus.publish_simple(
            RewardEventType.AR_COMPONENT_PLACEMENT,
            "test_user_001",
            {"component": "ESP32", "placement_accuracy": 0.98},
        )

        # 等待处理完成
        await bus.wait_for_empty_queue()

        # 显示统计信息
        stats = bus.get_subscription_stats()
        print(f"订阅统计: {stats}")

        # 停止事件总线
        await bus.stop()

    # 运行测试
    asyncio.run(test_event_bus())


# 创建全局事件总线实例
reward_event_bus = RewardEventBus()
