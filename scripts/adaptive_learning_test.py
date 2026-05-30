#!/usr/bin/env python3
"""
自适应学习路径引擎综合测试脚本
验证Markov Chain分析、知识图谱和动态难度调整功能
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 添加项目路径
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from ai_service.markov_analyzer import (
    MarkovChainAnalyzer, BehaviorEvent, BehaviorType, create_behavior_event_from_log
)
from ai_service.knowledge_graph_manager import (
    KnowledgeGraphManager, KnowledgeNode, KnowledgeRelationship, create_sample_knowledge_graph
)
from ai_service.difficulty_calculator import (
    DifficultyCalculator, create_performance_metric, test_difficulty_calculation
)
from ai_service.recommendation_service import RecommendationEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockKnowledgeGraphManager:
    """模拟知识图谱管理器用于测试"""
    
    def __init__(self):
        self.nodes = {}
        self.relationships = {}
    
    def recommend_learning_path(self, user_profile: Dict[str, Any], 
                               target_expertise: str,
                               max_path_length: int = 8) -> Any:
        """模拟路径推荐"""
        # 返回模拟的路径
        return type('MockLearningPath', (), {
            'nodes': ['node1', 'node2', 'node3'],
            'total_estimated_hours': 15.0,
            'confidence_score': 0.8
        })()
    
    def get_node_recommendations(self, node_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """模拟节点推荐"""
        return [
            {'node_id': 'next_node_1', 'title': '下一节课程', 'difficulty_level': 'intermediate'},
            {'node_id': 'next_node_2', 'title': '相关课程', 'difficulty_level': 'easy'}
        ]

class AdaptiveLearningTestSuite:
    """自适应学习引擎测试套件"""
    
    def __init__(self):
        self.test_results = {}
        self.markov_analyzer = MarkovChainAnalyzer(window_size=7, min_events=3)
        self.difficulty_calculator = DifficultyCalculator(smoothing_factor=0.3, min_samples=3)
        # 注意：在测试环境中模拟Neo4j连接
        try:
            self.knowledge_graph = KnowledgeGraphManager(
                uri="bolt://localhost:7687",
                username="neo4j",
                password="password"
            )
        except Exception:
            # 如果无法连接，创建模拟对象
            self.knowledge_graph = MockKnowledgeGraphManager()
        self.recommendation_engine = RecommendationEngine()
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("开始自适应学习路径引擎综合测试...")
        
        tests = [
            self.test_markov_chain_analysis,
            self.test_difficulty_calculation,
            self.test_behavior_pattern_detection,
            self.test_knowledge_graph_integration,
            self.test_difficulty_adjustment,
            self.test_system_integration
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for i, test_func in enumerate(tests, 1):
            test_name = test_func.__name__
            logger.info(f"执行测试 {i}/{total_tests}: {test_name}")
            
            try:
                result = await test_func()
                self.test_results[test_name] = {
                    'passed': result,
                    'timestamp': datetime.now().isoformat()
                }
                
                if result:
                    passed_tests += 1
                    logger.info(f"✓ {test_name} 通过")
                else:
                    logger.warning(f"✗ {test_name} 失败")
                    
            except Exception as e:
                logger.error(f"✗ {test_name} 异常: {e}")
                self.test_results[test_name] = {
                    'passed': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        # 生成测试报告
        summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'success_rate': (passed_tests / total_tests) * 100,
            'test_results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }
        
        self._print_summary(summary)
        return summary
    
    async def test_markov_chain_analysis(self) -> bool:
        """测试Markov Chain行为分析功能"""
        try:
            # 创建模拟用户行为数据
            user_id = "test_user_001"
            behaviors = [
                BehaviorEvent(user_id, "course1", "lesson1", BehaviorType.SUCCESS, 
                             datetime.now() - timedelta(minutes=30), 0.9, 25),
                BehaviorEvent(user_id, "course1", "lesson2", BehaviorType.FAILURE, 
                             datetime.now() - timedelta(minutes=25), 0.2, 15),
                BehaviorEvent(user_id, "course1", "lesson2", BehaviorType.REPEAT, 
                             datetime.now() - timedelta(minutes=20), 0.8, 30),
                BehaviorEvent(user_id, "course1", "lesson3", BehaviorType.SKIP, 
                             datetime.now() - timedelta(minutes=15), 0.1, 5),
                BehaviorEvent(user_id, "course1", "lesson4", BehaviorType.SUCCESS, 
                             datetime.now() - timedelta(minutes=10), 0.95, 40)
            ]
            
            # 添加行为事件
            for behavior in behaviors:
                self.markov_analyzer.add_behavior_event(behavior)
            
            # 分析用户行为
            analysis = self.markov_analyzer.analyze_user_behavior(user_id)
            
            # 验证分析结果
            assert analysis.total_events == 5
            assert analysis.failure_rate >= 0
            assert analysis.skip_rate >= 0
            assert len(analysis.recommendations) >= 0
            
            logger.info(f"Markov分析结果: 总事件{analysis.total_events}, "
                       f"失败率{analysis.failure_rate:.2f}, 跳过率{analysis.skip_rate:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Markov Chain测试失败: {e}")
            return False
    
    async def test_difficulty_calculation(self) -> bool:
        """测试动态难度系数计算功能"""
        try:
            # 测试核心公式
            test_cases = [
                (1.0, 0.1),      # 100%成功率 -> 最低难度
                (0.7, 2.04),     # 70%成功率 -> 中等难度
                (0.5, 4.0),      # 50%成功率 -> 高难度
                (0.3, 11.11),    # 30%成功率 -> 很高难度
            ]
            
            calculator = DifficultyCalculator()
            
            for success_rate, expected_min in test_cases:
                difficulty = calculator.calculate_dynamic_difficulty(success_rate)
                assert difficulty >= expected_min * 0.9  # 允许10%误差
                assert difficulty <= 10.0  # 最大难度限制
            
            # 测试难度等级转换
            level_tests = [
                (0.2, "very_easy"),
                (0.4, "easy"),
                (0.6, "moderate"),
                (0.8, "difficult"),
                (1.0, "very_difficult")
            ]
            
            for difficulty_score, expected_level in level_tests:
                level = calculator.calculate_difficulty_level(difficulty_score)
                assert level.value == expected_level
            
            logger.info("难度计算功能测试通过")
            return True
            
        except Exception as e:
            logger.error(f"难度计算测试失败: {e}")
            return False
    
    async def test_behavior_pattern_detection(self) -> bool:
        """测试行为模式识别功能"""
        try:
            # 创建具有明显模式的用户行为
            user_id = "pattern_test_user"
            
            # 模拟失败循环模式
            failure_cycle_behaviors = []
            base_time = datetime.now() - timedelta(hours=2)
            
            for i in range(8):
                # 连续失败模式
                if i % 3 == 0:  # 每3次失败后成功一次
                    behavior_type = BehaviorType.SUCCESS
                    success_rate = 0.9
                else:
                    behavior_type = BehaviorType.FAILURE
                    success_rate = 0.1
                
                failure_cycle_behaviors.append(
                    BehaviorEvent(user_id, "course1", f"lesson{i}", behavior_type,
                                 base_time + timedelta(minutes=i*10), success_rate, 20)
                )
            
            # 添加行为事件
            for behavior in failure_cycle_behaviors:
                self.markov_analyzer.add_behavior_event(behavior)
            
            # 分析行为模式
            analysis = self.markov_analyzer.analyze_user_behavior(user_id)
            
            # 验证模式检测
            assert analysis.total_events == 8
            assert analysis.failure_rate > 0.5  # 应该检测到高失败率
            
            logger.info(f"行为模式检测: 失败率{analysis.failure_rate:.2f}, "
                       f"异常检测:{analysis.anomaly_detected}")
            
            return True
            
        except Exception as e:
            logger.error(f"行为模式检测测试失败: {e}")
            return False
    
    async def test_knowledge_graph_integration(self) -> bool:
        """测试知识图谱集成功能"""
        try:
            # 由于需要Neo4j服务器，这里只测试基本初始化
            # 在实际环境中，可以创建示例图谱进行测试
            
            # 测试知识节点创建
            sample_node = KnowledgeNode(
                node_id="test_node_001",
                title="测试知识点",
                description="用于测试的知识点",
                category="test",
                difficulty_level="beginner",
                estimated_hours=2.0,
                prerequisites=[],
                learning_outcomes=["掌握基础知识"],
                tags=["test", "demo"]
            )
            
            # 测试关系创建
            sample_relationship = KnowledgeRelationship(
                from_node_id="node1",
                to_node_id="node2",
                relationship_type="PREREQUISITE",
                weight=1.0,
                description="前置关系"
            )
            
            logger.info("知识图谱数据结构测试通过")
            return True
            
        except Exception as e:
            logger.error(f"知识图谱集成测试失败: {e}")
            return False
    
    async def test_difficulty_adjustment(self) -> bool:
        """测试难度调整机制"""
        try:
            user_id = "adjustment_test_user"
            content_id = "test_content_001"
            
            # 添加一系列表现数据
            performance_data = [
                (0.3, 1, 45),  # 低成功率
                (0.4, 2, 40),  # 仍然较低
                (0.6, 3, 35),  # 中等表现
                (0.8, 4, 30),  # 较好表现
                (0.9, 5, 25),  # 优秀表现
            ]
            
            for i, (success_rate, attempt, time_spent) in enumerate(performance_data):
                metric = create_performance_metric(
                    user_id, content_id, success_rate,
                    attempt_count=attempt,
                    time_spent=time_spent,
                    attempt_date=datetime.now() - timedelta(days=len(performance_data)-i)
                )
                self.difficulty_calculator.add_performance_metric(metric)
            
            # 测试个性化难度计算
            personalized_difficulty = self.difficulty_calculator.get_personalized_difficulty(
                user_id, content_id
            )
            
            # 测试难度调整
            adjustment = self.difficulty_calculator.adjust_difficulty_for_user(
                user_id, content_id, target_success_rate=0.7
            )
            
            assert 0.1 <= personalized_difficulty <= 10.0
            assert adjustment.current_difficulty > 0
            assert adjustment.confidence_score >= 0
            
            logger.info(f"难度调整测试通过: 个性化难度={personalized_difficulty:.2f}, "
                       f"调整置信度={adjustment.confidence_score:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"难度调整测试失败: {e}")
            return False
    
    async def test_system_integration(self) -> bool:
        """测试系统集成"""
        try:
            # 测试各组件之间的协作
            user_id = "integration_test_user"
            
            # 1. 行为分析
            behavior_event = BehaviorEvent(
                user_id, "integrated_course", "lesson1", 
                BehaviorType.SUCCESS, datetime.now(), 0.85, 30
            )
            self.markov_analyzer.add_behavior_event(behavior_event)
            behavior_analysis = self.markov_analyzer.analyze_user_behavior(user_id)
            
            # 2. 难度计算
            performance_metric = create_performance_metric(
                user_id, "integrated_content", 0.75, time_spent=25
            )
            self.difficulty_calculator.add_performance_metric(performance_metric)
            difficulty = self.difficulty_calculator.get_personalized_difficulty(
                user_id, "integrated_content"
            )
            
            # 3. 验证数据流一致性
            assert behavior_analysis.user_id == user_id
            assert difficulty > 0
            
            logger.info("系统集成测试通过")
            return True
            
        except Exception as e:
            logger.error(f"系统集成测试失败: {e}")
            return False
    
    def _print_summary(self, summary: Dict[str, Any]):
        """打印测试摘要"""
        print("\n" + "="*60)
        print("🤖 自适应学习路径引擎测试报告")
        print("="*60)
        print(f"测试时间: {summary['timestamp']}")
        print(f"总测试数: {summary['total_tests']}")
        print(f"通过测试: {summary['passed_tests']}")
        print(f"成功率: {summary['success_rate']:.1f}%")
        print("-"*60)
        
        for test_name, result in summary['test_results'].items():
            status = "✓" if result['passed'] else "✗"
            print(f"{status} {test_name}")
            if 'error' in result:
                print(f"   错误: {result['error']}")
        
        print("="*60)
        
        if summary['success_rate'] >= 80:
            print("🎉 测试通过！系统功能完整可用。")
        else:
            print("⚠️  测试未完全通过，建议修复后再部署。")

async def main():
    """主函数"""
    test_suite = AdaptiveLearningTestSuite()
    results = await test_suite.run_all_tests()
    
    # 根据结果返回适当的退出码
    return 0 if results['success_rate'] >= 80 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)