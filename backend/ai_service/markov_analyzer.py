"""
Markov Chain用户行为分析器
用于分析用户学习行为模式，识别失败次数、跳过节点等行为特征
"""

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class BehaviorType(Enum):
    """用户行为类型枚举"""

    SUCCESS = "success"  # 学习成功
    FAILURE = "failure"  # 学习失败
    SKIP = "skip"  # 跳过节点
    REPEAT = "repeat"  # 重复学习
    ABANDON = "abandon"  # 放弃学习
    PROGRESS = "progress"  # 正常进展


@dataclass
class BehaviorEvent:
    """用户行为事件数据类"""

    user_id: str
    course_id: str
    lesson_id: str
    behavior_type: BehaviorType
    timestamp: datetime
    success_rate: float = 0.0
    time_spent: int = 0
    attempt_count: int = 1
    metadata: Dict[str, Any] = None


@dataclass
class BehaviorPattern:
    """行为模式数据类"""

    pattern_id: str
    description: str
    frequency: int
    confidence: float
    affected_users: List[str]
    impact_score: float


@dataclass
class BehaviorAnalysis:
    """用户行为分析结果"""

    user_id: str
    total_events: int
    failure_rate: float
    skip_rate: float
    average_success_rate: float
    most_common_pattern: Optional[BehaviorPattern]
    transition_matrix: Dict[Tuple[str, str], float]
    anomaly_detected: bool
    recommendations: List[str]


class MarkovChainAnalyzer:
    """Markov链用户行为分析器"""

    def __init__(self, window_size: int = 30, min_events: int = 10):
        """
        初始化分析器

        Args:
            window_size: 分析时间窗口（天数）
            min_events: 最小事件数量阈值
        """
        self.window_size = window_size
        self.min_events = min_events
        self.behavior_sequences = defaultdict(list)
        self.transition_counts = defaultdict(lambda: defaultdict(int))
        self.state_mappings = {}
        self.pattern_library = self._initialize_pattern_library()

    def _initialize_pattern_library(self) -> Dict[str, BehaviorPattern]:
        """初始化行为模式库"""
        return {
            "high_failure_cycle": BehaviorPattern(
                pattern_id="high_failure_cycle",
                description="高频失败循环模式",
                frequency=0,
                confidence=0.0,
                affected_users=[],
                impact_score=0.8,
            ),
            "skip_abandon_pattern": BehaviorPattern(
                pattern_id="skip_abandon_pattern",
                description="跳过后放弃模式",
                frequency=0,
                confidence=0.0,
                affected_users=[],
                impact_score=0.7,
            ),
            "repeat_learning_efficient": BehaviorPattern(
                pattern_id="repeat_learning_efficient",
                description="高效重复学习模式",
                frequency=0,
                confidence=0.0,
                affected_users=[],
                impact_score=0.9,
            ),
        }

    def add_behavior_event(self, event: BehaviorEvent):
        """
        添加用户行为事件

        Args:
            event: 行为事件对象
        """
        try:
            # 过滤过期事件
            if datetime.now() - event.timestamp > timedelta(days=self.window_size):
                return

            # 添加到序列
            state_key = (
                f"{event.course_id}_{event.lesson_id}_{event.behavior_type.value}"
            )
            self.behavior_sequences[event.user_id].append(
                {"state": state_key, "timestamp": event.timestamp, "event": event}
            )

            # 更新状态映射
            if state_key not in self.state_mappings:
                self.state_mappings[state_key] = len(self.state_mappings)

            logger.debug(f"添加用户 {event.user_id} 的行为事件: {state_key}")

        except Exception as e:
            logger.error(f"添加行为事件失败: {e}")

    def analyze_user_behavior(self, user_id: str) -> BehaviorAnalysis:
        """
        分析指定用户的行文模式

        Args:
            user_id: 用户ID

        Returns:
            BehaviorAnalysis: 行为分析结果
        """
        if user_id not in self.behavior_sequences:
            return self._create_empty_analysis(user_id)

        user_events = self.behavior_sequences[user_id]

        # 如果事件太少，返回基础分析
        if len(user_events) < self.min_events:
            return self._create_basic_analysis(user_id, user_events)

        # 构建状态转移矩阵
        transition_matrix = self._build_transition_matrix(user_events)

        # 计算行为统计
        stats = self._calculate_behavior_statistics(user_events)

        # 识别行为模式
        patterns = self._identify_behavior_patterns(user_events)
        most_common_pattern = self._get_most_significant_pattern(patterns)

        # 检测异常行为
        anomaly_detected = self._detect_anomalies(user_events, stats)

        # 生成推荐建议
        recommendations = self._generate_recommendations(
            stats, patterns, anomaly_detected
        )

        return BehaviorAnalysis(
            user_id=user_id,
            total_events=len(user_events),
            failure_rate=stats["failure_rate"],
            skip_rate=stats["skip_rate"],
            average_success_rate=stats["avg_success_rate"],
            most_common_pattern=most_common_pattern,
            transition_matrix=transition_matrix,
            anomaly_detected=anomaly_detected,
            recommendations=recommendations,
        )

    def _build_transition_matrix(
        self, events: List[Dict]
    ) -> Dict[Tuple[str, str], float]:
        """构建状态转移矩阵"""
        transitions = defaultdict(int)
        total_transitions = 0

        # 统计状态转移
        for i in range(len(events) - 1):
            current_state = events[i]["state"]
            next_state = events[i + 1]["state"]
            transitions[(current_state, next_state)] += 1
            total_transitions += 1

        # 转换为概率矩阵
        transition_matrix = {}
        for (from_state, to_state), count in transitions.items():
            transition_matrix[(from_state, to_state)] = count / total_transitions

        return transition_matrix

    def _calculate_behavior_statistics(self, events: List[Dict]) -> Dict[str, float]:
        """计算行为统计指标"""
        behavior_counter = Counter()
        success_rates = []
        time_spent_list = []

        for event_data in events:
            event = event_data["event"]
            behavior_counter[event.behavior_type] += 1
            success_rates.append(event.success_rate)
            time_spent_list.append(event.time_spent)

        total_events = len(events)

        return {
            "failure_rate": behavior_counter[BehaviorType.FAILURE] / total_events,
            "skip_rate": behavior_counter[BehaviorType.SKIP] / total_events,
            "success_rate": behavior_counter[BehaviorType.SUCCESS] / total_events,
            "avg_success_rate": np.mean(success_rates) if success_rates else 0.0,
            "avg_time_spent": np.mean(time_spent_list) if time_spent_list else 0.0,
            "total_attempts": sum(event["event"].attempt_count for event in events),
        }

    def _identify_behavior_patterns(self, events: List[Dict]) -> List[BehaviorPattern]:
        """识别行为模式"""
        patterns = []

        # 检测高频失败循环
        failure_pattern = self._detect_failure_cycles(events)
        if failure_pattern:
            patterns.append(failure_pattern)

        # 检测跳过放弃模式
        skip_pattern = self._detect_skip_abandon_pattern(events)
        if skip_pattern:
            patterns.append(skip_pattern)

        # 检测高效重复学习
        repeat_pattern = self._detect_repeat_learning_pattern(events)
        if repeat_pattern:
            patterns.append(repeat_pattern)

        return patterns

    def _detect_failure_cycles(self, events: List[Dict]) -> Optional[BehaviorPattern]:
        """检测失败循环模式"""
        failure_streak = 0
        max_failure_streak = 0

        for event_data in events:
            event = event_data["event"]
            if event.behavior_type == BehaviorType.FAILURE:
                failure_streak += 1
                max_failure_streak = max(max_failure_streak, failure_streak)
            else:
                failure_streak = 0

        # 如果连续失败超过3次，认为是问题模式
        if max_failure_streak >= 3:
            return BehaviorPattern(
                pattern_id="detected_failure_cycle",
                description=f"检测到连续{max_failure_streak}次失败的循环模式",
                frequency=max_failure_streak,
                confidence=min(0.9, max_failure_streak * 0.2),
                affected_users=[events[0]["event"].user_id],
                impact_score=0.8,
            )

        return None

    def _detect_skip_abandon_pattern(
        self, events: List[Dict]
    ) -> Optional[BehaviorPattern]:
        """检测跳过后放弃模式"""
        skip_then_abandon = 0

        for i in range(len(events) - 1):
            current_event = events[i]["event"]
            next_event = events[i + 1]["event"]

            if (
                current_event.behavior_type == BehaviorType.SKIP
                and next_event.behavior_type == BehaviorType.ABANDON
            ):
                skip_then_abandon += 1

        if skip_then_abandon > 0:
            return BehaviorPattern(
                pattern_id="detected_skip_abandon",
                description=f"检测到{skip_then_abandon}次跳过后放弃的行为模式",
                frequency=skip_then_abandon,
                confidence=min(0.8, skip_then_abandon * 0.3),
                affected_users=[events[0]["event"].user_id],
                impact_score=0.7,
            )

        return None

    def _detect_repeat_learning_pattern(
        self, events: List[Dict]
    ) -> Optional[BehaviorPattern]:
        """检测高效重复学习模式"""
        repeat_success_count = 0
        total_repeats = 0

        for event_data in events:
            event = event_data["event"]
            if event.behavior_type == BehaviorType.REPEAT:
                total_repeats += 1
                if event.success_rate > 0.8:  # 重复学习且成功率高
                    repeat_success_count += 1

        if total_repeats > 0 and repeat_success_count / total_repeats > 0.6:
            return BehaviorPattern(
                pattern_id="efficient_repeat_learning",
                description=f"高效的重复学习模式 ({repeat_success_count}/{total_repeats}次成功)",
                frequency=repeat_success_count,
                confidence=min(0.9, repeat_success_count / total_repeats),
                affected_users=[events[0]["event"].user_id],
                impact_score=0.9,
            )

        return None

    def _get_most_significant_pattern(
        self, patterns: List[BehaviorPattern]
    ) -> Optional[BehaviorPattern]:
        """获取最具显著性的行为模式"""
        if not patterns:
            return None

        return max(patterns, key=lambda p: p.impact_score * p.confidence)

    def _detect_anomalies(self, events: List[Dict], stats: Dict) -> bool:
        """检测异常行为"""
        # 异常检测规则
        anomaly_indicators = [
            stats["failure_rate"] > 0.5,  # 失败率过高
            stats["skip_rate"] > 0.4,  # 跳过率过高
            stats["avg_success_rate"] < 0.3,  # 平均成功率过低
            len(events) > 50 and stats["success_rate"] < 0.1,  # 大量尝试但成功率极低
        ]

        return any(anomaly_indicators)

    def _generate_recommendations(
        self, stats: Dict, patterns: List[BehaviorPattern], anomaly_detected: bool
    ) -> List[str]:
        """生成个性化推荐建议"""
        recommendations = []

        # 基于统计指标的建议
        if stats["failure_rate"] > 0.3:
            recommendations.append("建议降低当前学习内容难度")

        if stats["skip_rate"] > 0.2:
            recommendations.append("建议提供更多引导性学习材料")

        if stats["avg_time_spent"] < 30:  # 平均学习时间过短
            recommendations.append("建议延长学习时间，深入理解知识点")

        # 基于模式的建议
        for pattern in patterns:
            if pattern.pattern_id == "high_failure_cycle":
                recommendations.append(
                    "检测到重复失败模式，建议寻求额外帮助或调整学习策略"
                )
            elif pattern.pattern_id == "skip_abandon_pattern":
                recommendations.append("频繁跳过内容可能影响学习效果，建议按顺序学习")
            elif pattern.pattern_id == "repeat_learning_efficient":
                recommendations.append("您的重复学习策略很有效，继续保持")

        # 异常处理建议
        if anomaly_detected:
            recommendations.append("检测到异常学习行为，建议联系学习顾问获得个性化指导")

        return recommendations[:3]  # 限制建议数量

    def _create_empty_analysis(self, user_id: str) -> BehaviorAnalysis:
        """创建空的分析结果"""
        return BehaviorAnalysis(
            user_id=user_id,
            total_events=0,
            failure_rate=0.0,
            skip_rate=0.0,
            average_success_rate=0.0,
            most_common_pattern=None,
            transition_matrix={},
            anomaly_detected=False,
            recommendations=["暂无足够数据进行行为分析"],
        )

    def _create_basic_analysis(
        self, user_id: str, events: List[Dict]
    ) -> BehaviorAnalysis:
        """创建基础分析结果"""
        stats = self._calculate_behavior_statistics(events)

        return BehaviorAnalysis(
            user_id=user_id,
            total_events=len(events),
            failure_rate=stats["failure_rate"],
            skip_rate=stats["skip_rate"],
            average_success_rate=stats["avg_success_rate"],
            most_common_pattern=None,
            transition_matrix={},
            anomaly_detected=False,
            recommendations=["数据量较少，建议继续学习以获得更多分析洞察"],
        )

    def get_population_insights(self) -> Dict[str, Any]:
        """获取整体用户群体行为洞察"""
        if not self.behavior_sequences:
            return {"message": "暂无用户行为数据"}

        # 统计各行为类型的总体分布
        behavior_distribution = defaultdict(int)
        user_stats = []

        for user_id, events in self.behavior_sequences.items():
            if len(events) >= self.min_events:
                stats = self._calculate_behavior_statistics(events)
                user_stats.append(stats)

                # 累计行为分布
                for event_data in events:
                    behavior_distribution[event_data["event"].behavior_type] += 1

        # 计算群体统计
        population_stats = {
            "total_users_analyzed": len(user_stats),
            "behavior_distribution": dict(behavior_distribution),
            "average_failure_rate": np.mean([s["failure_rate"] for s in user_stats]),
            "average_skip_rate": np.mean([s["skip_rate"] for s in user_stats]),
            "average_success_rate": np.mean(
                [s["avg_success_rate"] for s in user_stats]
            ),
        }

        return population_stats


# 便捷函数
def create_behavior_event_from_log(log_entry: Dict) -> BehaviorEvent:
    """从日志条目创建行为事件"""
    return BehaviorEvent(
        user_id=log_entry["user_id"],
        course_id=log_entry["course_id"],
        lesson_id=log_entry["lesson_id"],
        behavior_type=BehaviorType(log_entry["behavior_type"]),
        timestamp=datetime.fromisoformat(log_entry["timestamp"]),
        success_rate=log_entry.get("success_rate", 0.0),
        time_spent=log_entry.get("time_spent", 0),
        attempt_count=log_entry.get("attempt_count", 1),
        metadata=log_entry.get("metadata", {}),
    )
