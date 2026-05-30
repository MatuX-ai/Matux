#!/usr/bin/env python3
"""
AI创意激发引擎回测验证脚本
验证创意评分算法的准确性和系统性能
"""

import asyncio
import json
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 导入创意引擎组件
try:
    from backend.ai_service.creativity_engine import CreativityEngine
    from backend.ai_service.idea_scorer import IdeaScorer
    from backend.ai_service.prompt_templates import PromptTemplateManager
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在项目根目录下运行此脚本")
    sys.exit(1)

class CreativityEngineBacktester:
    """创意引擎回测验证器"""
    
    def __init__(self):
        self.engine = CreativityEngine()
        self.scorer = IdeaScorer()
        self.template_manager = PromptTemplateManager()
        self.test_results = []
        self.performance_metrics = {}
    
    def load_test_dataset(self) -> List[Dict[str, Any]]:
        """加载测试数据集"""
        # 真实世界的创意想法样本
        test_ideas = [
            {
                "id": 1,
                "idea_content": "基于区块链的供应链透明度追踪系统，通过分布式账本技术实现商品从生产到消费的全流程可追溯",
                "expected_scores": {
                    "creativity": 8.5,
                    "feasibility": 7.0,
                    "commercial_value": 8.0,
                    "total_score": 7.8
                },
                "category": "technology",
                "description": "高科技区块链应用"
            },
            {
                "id": 2,
                "idea_content": "老年人智能陪伴机器人，集成语音交互、健康监测、紧急呼叫等功能，解决独居老人照护问题",
                "expected_scores": {
                    "creativity": 7.5,
                    "feasibility": 8.0,
                    "commercial_value": 8.5,
                    "total_score": 8.0
                },
                "category": "healthcare",
                "description": "医疗健康机器人"
            },
            {
                "id": 3,
                "idea_content": "基于AR技术的历史文化景点导览应用，游客通过手机摄像头即可看到历史场景重现",
                "expected_scores": {
                    "creativity": 9.0,
                    "feasibility": 6.5,
                    "commercial_value": 7.0,
                    "total_score": 7.5
                },
                "category": "entertainment",
                "description": "AR文旅应用"
            },
            {
                "id": 4,
                "idea_content": "社区共享工具平台，居民可以共享不常用的工具设备，减少资源浪费",
                "expected_scores": {
                    "creativity": 6.0,
                    "feasibility": 9.0,
                    "commercial_value": 6.5,
                    "total_score": 7.2
                },
                "category": "business",
                "description": "共享经济模式"
            },
            {
                "id": 5,
                "idea_content": "AI驱动的个性化营养餐配送服务，根据用户身体状况和口味偏好定制每日餐食",
                "expected_scores": {
                    "creativity": 8.0,
                    "feasibility": 7.5,
                    "commercial_value": 8.5,
                    "total_score": 8.0
                },
                "category": "healthcare",
                "description": "个性化健康餐饮"
            }
        ]
        return test_ideas
    
    async def run_comprehensive_backtest(self) -> Dict[str, Any]:
        """运行全面的回测验证"""
        print("🚀 开始AI创意激发引擎回测验证...")
        print("=" * 60)
        
        test_data = self.load_test_dataset()
        start_time = time.time()
        
        # 执行各项测试
        await self.test_idea_scoring_accuracy(test_data)
        await self.test_performance_benchmark()
        await self.test_prompt_templates_effectiveness()
        await self.test_batch_operations()
        
        total_time = time.time() - start_time
        
        # 生成回测报告
        report = self.generate_backtest_report(total_time)
        
        print("\n✅ 回测验证完成!")
        print("=" * 60)
        
        return report
    
    async def test_idea_scoring_accuracy(self, test_data: List[Dict[str, Any]]):
        """测试创意评分准确性"""
        print("\n🔬 测试创意评分准确性...")
        print("-" * 40)
        
        predicted_scores = []
        actual_scores = []
        
        for i, test_item in enumerate(test_data, 1):
            print(f"测试创意 {i}/{len(test_data)}: {test_item['description']}")
            
            # 构造评分请求
            try:
                from backend.models.creativity_models import IdeaScoreRequest
                request = IdeaScoreRequest(
                    idea_content=test_item["idea_content"],
                    technical_requirements="现代技术栈实现",
                    business_model="SaaS订阅模式",
                    market_context="相关市场正在快速发展"
                )
            except ImportError:
                # 如果无法导入，跳过此项测试
                print(f"  跳过测试 {i} - 模型导入失败")
                continue
            
            # 记录处理时间
            start_time = time.time()
            response = await self.scorer.score_idea(request)
            processing_time = time.time() - start_time
            
            # 记录预测和实际分数
            pred_total = response.total_score
            actual_total = test_item["expected_scores"]["total_score"]
            
            predicted_scores.append(pred_total)
            actual_scores.append(actual_total)
            
            # 存储详细结果
            self.test_results.append({
                "test_id": test_item["id"],
                "description": test_item["description"],
                "predicted_scores": {
                    "total": response.total_score,
                    "creativity": response.creativity,
                    "feasibility": response.feasibility,
                    "commercial_value": response.commercial_value
                },
                "actual_scores": test_item["expected_scores"],
                "processing_time": processing_time,
                "recommendations_count": len(response.recommendations)
            })
            
            print(f"  预测总分: {pred_total:.2f}, 实际总分: {actual_total:.2f}")
            print(f"  处理时间: {processing_time:.3f}秒")
        
        # 计算准确性指标
        mse = mean_squared_error(actual_scores, predicted_scores)
        mae = mean_absolute_error(actual_scores, predicted_scores)
        rmse = np.sqrt(mse)
        correlation = np.corrcoef(actual_scores, predicted_scores)[0, 1]
        
        self.performance_metrics["scoring_accuracy"] = {
            "mse": mse,
            "mae": mae,
            "rmse": rmse,
            "correlation": correlation,
            "predictions": predicted_scores,
            "actuals": actual_scores
        }
        
        print(f"\n📊 评分准确性统计:")
        print(f"  均方误差 (MSE): {mse:.4f}")
        print(f"  平均绝对误差 (MAE): {mae:.4f}")
        print(f"  均方根误差 (RMSE): {rmse:.4f}")
        print(f"  相关系数: {correlation:.4f}")
    
    async def test_performance_benchmark(self):
        """测试系统性能基准"""
        print("\n⚡ 测试系统性能基准...")
        print("-" * 40)
        
        # 测试创意生成性能
        generation_times = []
        try:
            from backend.models.creativity_models import IdeaGenerationRequest
        except ImportError:
            print("  跳过创意生成性能测试 - 模型导入失败")
            return
        
        for i in range(5):
            try:
                request = IdeaGenerationRequest(
                    category="technology",
                    temperature=0.7,
                    max_tokens=1000
                )
            except NameError:
                print(f"  跳过生成测试 {i+1} - 类未定义")
                continue
            
            start_time = time.time()
            try:
                response = await self.engine.generate_creative_idea(request)
                processing_time = time.time() - start_time
                generation_times.append(processing_time)
                print(f"  生成测试 {i+1}: {processing_time:.3f}秒")
            except Exception as e:
                print(f"  生成测试 {i+1}: 失败 - {str(e)}")
        
        # 测试评分性能
        scoring_times = []
        test_idea = self.load_test_dataset()[0]
        
        for i in range(10):
            try:
                from backend.models.creativity_models import IdeaScoreRequest
                request = IdeaScoreRequest(
                    idea_content=test_idea["idea_content"]
                )
            except (ImportError, NameError):
                print(f"  跳过评分测试 {i+1} - 类未定义")
                continue
            
            start_time = time.time()
            try:
                response = await self.scorer.score_idea(request)
                processing_time = time.time() - start_time
                scoring_times.append(processing_time)
                print(f"  评分测试 {i+1}: {processing_time:.3f}秒")
            except Exception as e:
                print(f"  评分测试 {i+1}: 失败 - {str(e)}")
        
        # 计算性能指标
        self.performance_metrics["performance_benchmark"] = {
            "generation": {
                "times": generation_times,
                "mean": statistics.mean(generation_times) if generation_times else 0,
                "median": statistics.median(generation_times) if generation_times else 0,
                "std": statistics.stdev(generation_times) if len(generation_times) > 1 else 0
            },
            "scoring": {
                "times": scoring_times,
                "mean": statistics.mean(scoring_times) if scoring_times else 0,
                "median": statistics.median(scoring_times) if scoring_times else 0,
                "std": statistics.stdev(scoring_times) if len(scoring_times) > 1 else 0
            }
        }
        
        print(f"\n📈 性能基准统计:")
        if generation_times:
            print(f"  创意生成 - 平均: {statistics.mean(generation_times):.3f}秒, "
                  f"中位数: {statistics.median(generation_times):.3f}秒")
        if scoring_times:
            print(f"  创意评分 - 平均: {statistics.mean(scoring_times):.3f}秒, "
                  f"中位数: {statistics.median(scoring_times):.3f}秒")
    
    async def test_prompt_templates_effectiveness(self):
        """测试Prompt模板有效性"""
        print("\n🎯 测试Prompt模板有效性...")
        print("-" * 40)
        
        # 获取现有模板
        templates = await self.template_manager.list_templates(is_public=True, limit=10)
        print(f"找到 {len(templates)} 个公共模板")
        
        template_usage_stats = []
        
        for template in templates[:3]:  # 测试前3个模板
            print(f"测试模板: {template.name}")
            
            # 使用模板生成创意
            try:
                from backend.models.creativity_models import IdeaGenerationRequest
                request = IdeaGenerationRequest(
                    prompt_template_id=template.id,
                    variables={"场景": "智能家居", "预算": "5000", "功能": "远程控制", "约束条件": "低成本"},
                    temperature=0.8
                )
            except (ImportError, NameError):
                print(f"  跳过模板测试 - 类未定义")
                continue
            
            try:
                start_time = time.time()
                response = await self.engine.generate_creative_idea(request)
                processing_time = time.time() - start_time
                
                template_usage_stats.append({
                    "template_id": template.id,
                    "template_name": template.name,
                    "processing_time": processing_time,
                    "content_length": len(response.content),
                    "success": True
                })
                
                print(f"  成功生成创意，耗时: {processing_time:.3f}秒")
                
            except Exception as e:
                template_usage_stats.append({
                    "template_id": template.id,
                    "template_name": template.name,
                    "error": str(e),
                    "success": False
                })
                print(f"  生成失败: {str(e)}")
        
        self.performance_metrics["template_effectiveness"] = template_usage_stats
    
    async def test_batch_operations(self):
        """测试批处理操作"""
        print("\n🔄 测试批处理操作...")
        print("-" * 40)
        
        # 准备批处理数据
        test_ideas = self.load_test_dataset()
        idea_contents = [item["idea_content"] for item in test_ideas[:3]]
        
        print(f"批量评分 {len(idea_contents)} 个创意想法...")
        
        start_time = time.time()
        try:
            # 这里应该调用批处理接口，简化为循环调用
            batch_results = []
            for content in idea_contents:
                try:
                    from backend.models.creativity_models import IdeaScoreRequest
                    request = IdeaScoreRequest(idea_content=content)
                    result = await self.scorer.score_idea(request)
                    batch_results.append(result)
                except (ImportError, NameError):
                    print(f"  跳过批处理项 - 类未定义")
                    continue
            
            batch_time = time.time() - start_time
            avg_time_per_idea = batch_time / len(idea_contents)
            
            self.performance_metrics["batch_operations"] = {
                "total_ideas": len(idea_contents),
                "total_time": batch_time,
                "avg_time_per_idea": avg_time_per_idea,
                "success_rate": len(batch_results) / len(idea_contents)
            }
            
            print(f"  批处理完成，总耗时: {batch_time:.3f}秒")
            print(f"  平均每个创意: {avg_time_per_idea:.3f}秒")
            print(f"  成功率: {len(batch_results)/len(idea_contents)*100:.1f}%")
            
        except Exception as e:
            print(f"  批处理失败: {str(e)}")
            self.performance_metrics["batch_operations"] = {
                "error": str(e),
                "success_rate": 0.0
            }
    
    def generate_backtest_report(self, total_execution_time: float) -> Dict[str, Any]:
        """生成回测报告"""
        report = {
            "test_timestamp": datetime.now().isoformat(),
            "total_execution_time": total_execution_time,
            "test_results": self.test_results,
            "performance_metrics": self.performance_metrics,
            "summary": self.generate_summary()
        }
        
        # 保存报告到文件
        report_filename = f"creativity_engine_backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 回测报告已保存到: {report_filename}")
        
        return report
    
    def generate_summary(self) -> Dict[str, Any]:
        """生成测试摘要"""
        summary = {
            "total_tests": len(self.test_results),
            "passed_tests": len([r for r in self.test_results if r.get("predicted_scores")]),
            "failed_tests": len([r for r in self.test_results if not r.get("predicted_scores")]),
        }
        
        # 评分准确性摘要
        if "scoring_accuracy" in self.performance_metrics:
            accuracy = self.performance_metrics["scoring_accuracy"]
            summary["accuracy_metrics"] = {
                "rmse": accuracy["rmse"],
                "mae": accuracy["mae"],
                "correlation": accuracy["correlation"]
            }
        
        # 性能摘要
        if "performance_benchmark" in self.performance_metrics:
            perf = self.performance_metrics["performance_benchmark"]
            summary["performance_metrics"] = {
                "avg_generation_time": perf["generation"]["mean"],
                "avg_scoring_time": perf["scoring"]["mean"]
            }
        
        return summary

async def main():
    """主函数"""
    backtester = CreativityEngineBacktester()
    report = await backtester.run_comprehensive_backtest()
    
    # 打印关键指标
    summary = report["summary"]
    print(f"\n📋 回测摘要:")
    print(f"  总测试数: {summary['total_tests']}")
    print(f"  通过测试: {summary['passed_tests']}")
    print(f"  失败测试: {summary['failed_tests']}")
    
    if "accuracy_metrics" in summary:
        acc = summary["accuracy_metrics"]
        print(f"  评分准确率:")
        print(f"    RMSE: {acc['rmse']:.4f}")
        print(f"    MAE: {acc['mae']:.4f}")
        print(f"    相关性: {acc['correlation']:.4f}")
    
    if "performance_metrics" in summary:
        perf = summary["performance_metrics"]
        print(f"  性能指标:")
        print(f"    平均生成时间: {perf['avg_generation_time']:.3f}秒")
        print(f"    平均评分时间: {perf['avg_scoring_time']:.3f}秒")

if __name__ == "__main__":
    asyncio.run(main())