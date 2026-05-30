#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TinyML模型基准测试使用示例
演示如何使用model_benchmark.py进行模型性能对比测试
"""

import os
import sys
import json
from pathlib import Path

# 添加脚本目录到路径
sys.path.append(str(Path(__file__).parent))

def demo_basic_benchmark():
    """演示基础基准测试"""
    print("🎯 基础基准测试演示")
    print("=" * 50)
    
    # 导入基准测试模块
    try:
        from model_benchmark import ModelBenchmark
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return
    
    # 创建基准测试实例
    benchmark = ModelBenchmark()
    
    # 测试模型路径
    model_paths = [
        "models/tinyml/tensorflow_lite/voice_model.tflite",
        "models/tinyml/edge_impulse/voice_commands/ei-voice-model-v1.0.0/ei-voice-model-v1.0.0.tflite"
    ]
    
    # 过滤存在的模型
    existing_models = [path for path in model_paths if os.path.exists(path)]
    
    if not existing_models:
        print("⚠️  没有找到测试模型文件，创建示例结果...")
        # 创建模拟结果
        sample_results = {
            "tensorflow_lite_model": {
                "size_metrics": {"file_size_kb": 185.2, "file_size_mb": 0.18},
                "speed_metrics": {"avg_latency_ms": 2.1, "throughput_fps": 476},
                "overall_score": 79.1
            },
            "edge_impulse_model": {
                "size_metrics": {"file_size_kb": 156.7, "file_size_mb": 0.15},
                "speed_metrics": {"avg_latency_ms": 1.8, "throughput_fps": 556},
                "overall_score": 87.3
            }
        }
        print_sample_comparison(sample_results)
        return
    
    print(f"🔬 测试模型: {existing_models}")
    
    # 执行对比测试
    try:
        results = benchmark.compare_models(existing_models, (1, 40))
        print("\n📊 测试结果:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")

def print_sample_comparison(results):
    """打印示例对比结果"""
    print("\n📊 模型性能对比示例:")
    print("-" * 60)
    
    print(f"{'指标':<20} {'TensorFlow Lite':<15} {'Edge Impulse':<15}")
    print("-" * 60)
    
    tf_result = results["tensorflow_lite_model"]
    ei_result = results["edge_impulse_model"]
    
    print(f"{'模型大小 (MB)':<20} {tf_result['size_metrics']['file_size_mb']:<15} {ei_result['size_metrics']['file_size_mb']:<15}")
    print(f"{'平均延迟 (ms)':<20} {tf_result['speed_metrics']['avg_latency_ms']:<15} {ei_result['speed_metrics']['avg_latency_ms']:<15}")
    print(f"{'吞吐量 (FPS)':<20} {tf_result['speed_metrics']['throughput_fps']:<15.0f} {ei_result['speed_metrics']['throughput_fps']:<15.0f}")
    print(f"{'综合评分':<20} {tf_result['overall_score']:<15.1f} {ei_result['overall_score']:<15.1f}")
    
    winner = "Edge Impulse" if ei_result['overall_score'] > tf_result['overall_score'] else "TensorFlow Lite"
    print("-" * 60)
    print(f"🏆 推荐选择: {winner}")

def demo_hardware_simulation():
    """演示硬件平台性能仿真"""
    print("\n📱 硬件平台性能仿真演示")
    print("=" * 50)
    
    try:
        from model_benchmark import ModelBenchmark
        benchmark = ModelBenchmark()
        
        # 模拟测试结果
        mock_metrics = {
            'avg_latency_ms': 2.1,
            'throughput_fps': 476,
            'file_size_mb': 0.18
        }
        
        platforms = ['esp32', 'nano', 'desktop']
        
        print(f"{'硬件平台':<20} {'估计延迟(ms)':<15} {'估计吞吐量(FPS)':<20} {'适用性评分':<10}")
        print("-" * 75)
        
        for platform in platforms:
            hw_perf = benchmark.simulate_hardware_performance(platform, mock_metrics)
            print(f"{hw_perf['hardware_platform']:<20} {hw_perf['estimated_latency_ms']:<15.1f} {hw_perf['estimated_throughput_fps']:<20.0f} {hw_perf['suitability_score']:<10.1f}")
            
    except Exception as e:
        print(f"❌ 硬件仿真演示失败: {e}")

def demo_temperature_test():
    """演示温度稳定性测试"""
    print("\n🌡️  温度稳定性测试演示")
    print("=" * 50)
    
    try:
        from model_benchmark import ModelBenchmark
        benchmark = ModelBenchmark()
        
        # 使用模拟模型路径进行测试
        test_model = "models/tinyml/tensorflow_lite/voice_model.tflite"
        
        if os.path.exists(test_model):
            print(f"🔬 对模型 {test_model} 进行2分钟温度稳定性测试...")
            results = benchmark.run_temperature_stress_test(test_model, duration_minutes=2)
            
            print(f"总推理次数: {results['total_inferences']}")
            print(f"错误次数: {results['errors']}")
            print(f"错误率: {results['error_rate_percent']:.2f}%")
            print(f"平均延迟: {results['avg_latency_ms']:.2f} ms")
            print(f"稳定性评分: {results['stability_score']:.1f}/100")
        else:
            print("⚠️  测试模型不存在，显示模拟结果...")
            print("总推理次数: 2847")
            print("错误次数: 23")
            print("错误率: 0.81%")
            print("平均延迟: 2.30 ms")
            print("稳定性评分: 82.0/100")
            
    except Exception as e:
        print(f"❌ 温度测试演示失败: {e}")

def demo_cli_usage():
    """演示命令行使用方法"""
    print("\n💻 命令行使用示例")
    print("=" * 50)
    
    examples = [
        "# 基础使用 - 对比两个模型",
        "python scripts/model_benchmark.py --models model1.tflite model2.tflite",
        "",
        "# 指定输入形状和迭代次数",
        "python scripts/model_benchmark.py --models model.tflite --input-shape '(1,60)' --iterations 200",
        "",
        "# 自定义输出报告文件",
        "python scripts/model_benchmark.py --models *.tflite --output my_report.json",
        "",
        "# 长时间温度测试",
        "python scripts/model_benchmark.py --models model.tflite --temp-test-minutes 10"
    ]
    
    for example in examples:
        if example.startswith("#"):
            print(f"\n{example}")
        else:
            print(f"  {example}")

def demo_api_usage():
    """演示API使用方法"""
    print("\n🌐 API使用示例")
    print("=" * 50)
    
    api_examples = {
        "启动基准测试": """
POST /api/v1/model-benchmark/start
Content-Type: application/json

{
  "model_paths": ["model1.tflite", "model2.tflite"],
  "input_shape": "(1,40)",
  "iterations": 100,
  "temp_test_minutes": 2
}
        """,
        
        "获取测试结果": """
GET /api/v1/model-benchmark/{test_id}
        """,
        
        "列出测试历史": """
GET /api/v1/model-benchmark/results?limit=10
        """,
        
        "获取硬件配置": """
GET /api/v1/model-benchmark/hardware-profiles
        """
    }
    
    for name, example in api_examples.items():
        print(f"\n{name}:")
        print(example.strip())

def main():
    """主函数"""
    print("🚀 TinyML模型基准测试系统演示")
    print("版本: 1.0.0")
    print("日期: 2026年2月28日")
    print()
    
    # 运行各个演示
    demo_basic_benchmark()
    demo_hardware_simulation()
    demo_temperature_test()
    demo_cli_usage()
    demo_api_usage()
    
    print("\n" + "=" * 50)
    print("✨ 演示完成！")
    print("\n📚 相关文档:")
    print("  - 技术文档: docs/MODEL_COMPARISON_REPORT.md")
    print("  - API文档: http://localhost:8000/docs (启动后端服务后)")
    print("  - 模型目录: models/tinyml/edge_impulse/")
    
    print("\n🔧 快速开始:")
    print("  1. 准备TFLite模型文件")
    print("  2. 运行: python scripts/model_benchmark.py --models your_model.tflite")
    print("  3. 查看生成的JSON报告文件")

if __name__ == "__main__":
    main()