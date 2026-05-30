import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import json
import logging
import statistics
import threading
import time
import tracemalloc
from typing import Any, Dict, List

import psutil

from backend.services.complex_gesture_recognizer import (
    GesturePoint,
    complex_gesture_recognizer,
)
from backend.services.integral_decay_calculator import decay_calculator

# 导入被测试的模块
from backend.services.reward_event_bus import RewardEvent, reward_event_bus
from backend.services.voice_correction_detector import VoiceCorrectionDetector
from backend.utils.blockchain_client import BlockchainClient

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self):
        self.metrics = {
            "latency": [],
            "throughput": [],
            "memory_usage": [],
            "cpu_usage": [],
            "error_rates": [],
        }
        self.start_time = None
        self.end_time = None

    def start_monitoring(self):
        """开始监控"""
        self.start_time = datetime.now()
        tracemalloc.start()

    def stop_monitoring(self):
        """停止监控"""
        self.end_time = datetime.now()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        self.metrics["memory_peak"] = peak / 1024 / 1024  # MB
        self.metrics["memory_current"] = current / 1024 / 1024  # MB

    def record_latency(self, latency_ms: float):
        """记录延迟"""
        self.metrics["latency"].append(latency_ms)

    def record_throughput(self, requests_per_second: float):
        """记录吞吐量"""
        self.metrics["throughput"].append(requests_per_second)

    def record_error(self, error_info: Dict[str, Any]):
        """记录错误"""
        self.metrics["error_rates"].append(error_info)

    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.start_time or not self.end_time:
            return {}

        duration = (self.end_time - self.start_time).total_seconds()

        summary = {
            "test_duration_seconds": duration,
            "total_requests": len(self.metrics["latency"]),
            "latency_stats": self._calculate_latency_stats(),
            "throughput_stats": self._calculate_throughput_stats(),
            "memory_stats": {
                "peak_mb": self.metrics.get("memory_peak", 0),
                "current_mb": self.metrics.get("memory_current", 0),
            },
            "error_count": len(self.metrics["error_rates"]),
            "error_rate": len(self.metrics["error_rates"])
            / max(len(self.metrics["latency"]), 1),
        }

        return summary

    def _calculate_latency_stats(self) -> Dict[str, float]:
        """计算延迟统计"""
        if not self.metrics["latency"]:
            return {}

        latencies = self.metrics["latency"]
        return {
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "avg_ms": statistics.mean(latencies),
            "median_ms": statistics.median(latencies),
            "p95_ms": self._percentile(latencies, 95),
            "p99_ms": self._percentile(latencies, 99),
        }

    def _calculate_throughput_stats(self) -> Dict[str, float]:
        """计算吞吐量统计"""
        if not self.metrics["throughput"]:
            return {}

        throughputs = self.metrics["throughput"]
        return {
            "min_rps": min(throughputs),
            "max_rps": max(throughputs),
            "avg_rps": statistics.mean(throughputs),
            "median_rps": statistics.median(throughputs),
        }

    def _percentile(self, data: List[float], percentile: float) -> float:
        """计算百分位数"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class StressTestRunner:
    """压力测试运行器"""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.blockchain_client = BlockchainClient()
        self.test_results = []

    async def run_voice_correction_stress_test(
        self, concurrent_users: int = 100, requests_per_user: int = 50
    ) -> Dict[str, Any]:
        """运行语音纠错压力测试"""
        logger.info(
            f"开始语音纠错压力测试: {concurrent_users}并发用户, 每用户{requests_per_user}请求"
        )

        self.metrics.start_monitoring()

        # 测试数据
        test_commands = [
            "正确连接D9引脚到LED正极",
            "将电阻连接到D8引脚",
            "检查电路连接是否正确",
            "确认电源电压为3.3伏特",
            "验证接地连接良好",
        ]

        # 并发执行测试
        start_time = time.time()
        tasks = []

        for user_id in range(1, concurrent_users + 1):
            task = self._run_voice_user_session(
                user_id, requests_per_user, test_commands
            )
            tasks.append(task)

        # 执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        # 分析结果
        successful_requests = 0
        total_requests = concurrent_users * requests_per_user

        for result in results:
            if not isinstance(result, Exception):
                successful_requests += result.get("successful_requests", 0)

        throughput = total_requests / total_time if total_time > 0 else 0

        self.metrics.record_throughput(throughput)
        self.metrics.stop_monitoring()

        return {
            "test_type": "voice_correction",
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": successful_requests / total_requests,
            "total_time_seconds": total_time,
            "throughput_rps": throughput,
            "performance_metrics": self.metrics.get_summary(),
        }

    async def _run_voice_user_session(
        self, user_id: int, request_count: int, commands: List[str]
    ) -> Dict[str, Any]:
        """运行单个用户的语音会话测试"""
        successful_requests = 0
        detector = VoiceCorrectionDetector()

        with patch(
            "backend.utils.blockchain_client.BlockchainClient.invoke_integral_chaincode"
        ) as mock_invoke:
            mock_invoke.return_value = {"success": True, "message": "积分发放成功"}

            for i in range(request_count):
                try:
                    start_time = time.time()

                    # 模拟语音命令处理
                    command = commands[i % len(commands)]
                    correction_result = detector.detect_corrections(command)

                    if correction_result.is_correction:
                        event = RewardEvent(
                            event_type="voice_correction",
                            user_id=user_id,
                            data={
                                "correction_type": correction_result.correction_type,
                                "confidence": correction_result.confidence,
                                "accuracy": correction_result.accuracy,
                                "command": command,
                            },
                            timestamp=datetime.now(),
                        )

                        await reward_event_bus.publish(event)
                        successful_requests += 1

                    # 记录延迟
                    latency = (time.time() - start_time) * 1000  # 转换为毫秒
                    self.metrics.record_latency(latency)

                    # 模拟真实请求间隔
                    await asyncio.sleep(0.01)  # 10ms间隔

                except Exception as e:
                    logger.error(f"用户{user_id}请求{i}失败: {e}")
                    self.metrics.record_error(
                        {
                            "user_id": user_id,
                            "request_id": i,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        return {
            "user_id": user_id,
            "successful_requests": successful_requests,
            "total_requests": request_count,
        }

    async def run_gesture_recognition_stress_test(
        self, gesture_sequences: int = 1000
    ) -> Dict[str, Any]:
        """运行手势识别压力测试"""
        logger.info(f"开始手势识别压力测试: {gesture_sequences}个手势序列")

        self.metrics.start_monitoring()

        start_time = time.time()
        processed_sequences = 0

        # 生成测试手势数据
        for i in range(gesture_sequences):
            try:
                # 模拟手势点序列
                gesture_points = self._generate_gesture_points(i)
                complex_gesture_recognizer.add_gesture_points(gesture_points)

                # 检测复杂序列
                sequences = complex_gesture_recognizer.detect_complex_sequences()
                processed_sequences += 1

                # 记录处理时间
                latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(latency)

            except Exception as e:
                logger.error(f"手势序列{i}处理失败: {e}")
                self.metrics.record_error(
                    {
                        "sequence_id": i,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        end_time = time.time()
        total_time = end_time - start_time
        throughput = processed_sequences / total_time if total_time > 0 else 0

        self.metrics.record_throughput(throughput)
        self.metrics.stop_monitoring()

        return {
            "test_type": "gesture_recognition",
            "total_sequences": gesture_sequences,
            "processed_sequences": processed_sequences,
            "success_rate": processed_sequences / gesture_sequences,
            "total_time_seconds": total_time,
            "throughput_sequences_per_second": throughput,
            "performance_metrics": self.metrics.get_summary(),
        }

    def _generate_gesture_points(self, sequence_id: int) -> List[GesturePoint]:
        """生成测试手势点"""
        points = []
        base_time = time.time()

        # 生成5-10个手势点
        point_count = 5 + (sequence_id % 6)

        for i in range(point_count):
            point = GesturePoint(
                x=0.1 + (sequence_id * 0.01) % 0.8,
                y=0.2 + (i * 0.1) % 0.6,
                z=0.0,
                timestamp=base_time + i * 0.1,
                confidence=0.8 + (i * 0.02) % 0.2,
            )
            points.append(point)

        return points

    async def run_decay_calculation_stress_test(
        self, user_count: int = 10000
    ) -> Dict[str, Any]:
        """运行积分衰减计算压力测试"""
        logger.info(f"开始积分衰减计算压力测试: {user_count}个用户")

        self.metrics.start_monitoring()

        # 生成测试用户数据
        user_points = {i: 1000 + (i % 2000) for i in range(1, user_count + 1)}
        user_levels = {
            i: "standard" if i % 3 != 0 else "vip" for i in range(1, user_count + 1)
        }

        start_time = time.time()

        # 批量计算衰减
        decay_results = decay_calculator.bulk_calculate_decay(user_points, user_levels)

        end_time = time.time()
        total_time = end_time - start_time

        # 统计结果
        users_with_decay = sum(1 for decay in decay_results.values() if decay > 0)
        total_decay_points = sum(decay_results.values())

        throughput = user_count / total_time if total_time > 0 else 0

        self.metrics.record_throughput(throughput)
        self.metrics.stop_monitoring()

        return {
            "test_type": "decay_calculation",
            "user_count": user_count,
            "users_with_decay": users_with_decay,
            "total_decay_points": total_decay_points,
            "total_time_seconds": total_time,
            "throughput_users_per_second": throughput,
            "average_decay_per_user": total_decay_points / max(users_with_decay, 1),
            "performance_metrics": self.metrics.get_summary(),
        }

    async def run_concurrent_event_processing_test(
        self, event_count: int = 5000
    ) -> Dict[str, Any]:
        """运行并发事件处理压力测试"""
        logger.info(f"开始并发事件处理压力测试: {event_count}个事件")

        self.metrics.start_monitoring()

        # 准备测试事件
        events = []
        for i in range(event_count):
            event = RewardEvent(
                event_type=[
                    "voice_correction",
                    "ar_scene_completed",
                    "complex_gesture_sequence",
                ][i % 3],
                user_id=(i % 1000) + 1,
                data={
                    "test_data": f"event_{i}",
                    "timestamp": datetime.now().isoformat(),
                },
                timestamp=datetime.now(),
            )
            events.append(event)

        start_time = time.time()

        # 并发处理事件
        with patch(
            "backend.utils.blockchain_client.BlockchainClient.invoke_integral_chaincode"
        ) as mock_invoke:
            mock_invoke.return_value = {"success": True}

            # 分批处理以避免内存问题
            batch_size = 100
            successful_events = 0

            for i in range(0, len(events), batch_size):
                batch = events[i : i + batch_size]
                tasks = [reward_event_bus.publish(event) for event in batch]

                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    successful_events += len(batch)
                except Exception as e:
                    logger.error(f"事件批次{i}-{i+len(batch)}处理失败: {e}")

                # 记录批次延迟
                batch_latency = (time.time() - start_time) * 1000
                self.metrics.record_latency(batch_latency / len(batch))

        end_time = time.time()
        total_time = end_time - start_time
        throughput = event_count / total_time if total_time > 0 else 0

        self.metrics.record_throughput(throughput)
        self.metrics.stop_monitoring()

        return {
            "test_type": "concurrent_event_processing",
            "total_events": event_count,
            "successful_events": successful_events,
            "success_rate": successful_events / event_count,
            "total_time_seconds": total_time,
            "throughput_events_per_second": throughput,
            "performance_metrics": self.metrics.get_summary(),
        }

    async def run_comprehensive_load_test(self) -> List[Dict[str, Any]]:
        """运行综合性负载测试"""
        test_results = []

        # 测试场景1: 语音纠错高并发
        result1 = await self.run_voice_correction_stress_test(
            concurrent_users=50, requests_per_user=20
        )
        test_results.append(result1)
        await asyncio.sleep(2)  # 休息间隔

        # 测试场景2: 手势识别大量序列
        result2 = await self.run_gesture_recognition_stress_test(gesture_sequences=500)
        test_results.append(result2)
        await asyncio.sleep(2)

        # 测试场景3: 积分衰减批量计算
        result3 = await self.run_decay_calculation_stress_test(user_count=5000)
        test_results.append(result3)
        await asyncio.sleep(2)

        # 测试场景4: 并发事件处理
        result4 = await self.run_concurrent_event_processing_test(event_count=2000)
        test_results.append(result4)

        return test_results

    def generate_test_report(self, results: List[Dict[str, Any]]) -> str:
        """生成测试报告"""
        report = {
            "test_suite": "Multimodal Incentive System Performance Test",
            "generated_at": datetime.now().isoformat(),
            "test_results": results,
            "overall_summary": self._generate_overall_summary(results),
        }

        return json.dumps(report, indent=2, ensure_ascii=False)

    def _generate_overall_summary(
        self, results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成总体摘要"""
        if not results:
            return {}

        total_success_rate = sum(r.get("success_rate", 0) for r in results) / len(
            results
        )
        avg_throughput = sum(
            r.get("throughput_events_per_second", r.get("throughput_rps", 0))
            for r in results
        ) / len(results)

        return {
            "average_success_rate": total_success_rate,
            "average_throughput": avg_throughput,
            "total_test_scenarios": len(results),
            "passed_scenarios": sum(
                1 for r in results if r.get("success_rate", 0) >= 0.95
            ),
            "failed_scenarios": sum(
                1 for r in results if r.get("success_rate", 0) < 0.95
            ),
        }


# 用于mock的装饰器
from unittest.mock import patch


async def main():
    """主测试函数"""
    logging.basicConfig(level=logging.INFO)

    runner = StressTestRunner()

    logger.info("开始多模态激励系统性能压力测试...")

    # 运行综合性负载测试
    results = await runner.run_comprehensive_load_test()

    # 生成测试报告
    report = runner.generate_test_report(results)

    # 保存报告
    with open("multimodal_performance_test_report.json", "w", encoding="utf-8") as f:
        f.write(report)

    logger.info("性能压力测试完成，报告已保存")

    # 打印摘要
    summary = json.loads(report)["overall_summary"]
    logger.info(
        f"测试摘要: 成功率 {summary['average_success_rate']:.2%}, "
        f"平均吞吐量 {summary['average_throughput']:.2f} req/sec"
    )


if __name__ == "__main__":
    asyncio.run(main())
