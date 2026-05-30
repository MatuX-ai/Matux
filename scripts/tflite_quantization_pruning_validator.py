#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TensorFlow Lite量化剪枝验证器
专门验证模型是否满足≤280KB的内存限制要求
"""

import os
import sys
import json
import numpy as np
import tensorflow as tf
from pathlib import Path
import argparse
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tflite_validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TFLiteQuantizationPruningValidator:
    """TensorFlow Lite量化剪枝验证器"""
    
    def __init__(self, target_size_kb=280):
        self.target_size_kb = target_size_kb
        self.validation_results = {}
        self.start_time = datetime.now()
        
    def validate_model_compliance(self, model_path):
        """验证模型是否符合内存限制要求"""
        logger.info(f"=== 验证模型合规性 (目标: ≤{self.target_size_kb}KB) ===")
        
        if not Path(model_path).exists():
            logger.error(f"模型文件不存在: {model_path}")
            return False
            
        # 获取文件大小信息
        file_size = os.path.getsize(model_path)
        file_size_kb = file_size / 1024
        
        logger.info(f"模型文件: {model_path}")
        logger.info(f"文件大小: {file_size:,} bytes ({file_size_kb:.2f} KB)")
        
        # 合规性检查
        is_compliant = file_size_kb <= self.target_size_kb
        if is_compliant:
            logger.info(f"✅ 模型合规 (≤{self.target_size_kb}KB)")
        else:
            logger.warning(f"❌ 模型超限 ({file_size_kb:.2f}KB > {self.target_size_kb}KB)")
            
        self.validation_results['file_compliance'] = {
            'model_path': str(model_path),
            'file_size_bytes': file_size,
            'file_size_kb': round(file_size_kb, 2),
            'target_size_kb': self.target_size_kb,
            'is_compliant': is_compliant,
            'size_difference_kb': round(file_size_kb - self.target_size_kb, 2)
        }
        
        return is_compliant
    
    def analyze_model_structure(self, model_path):
        """分析模型结构和组成"""
        logger.info("=== 模型结构分析 ===")
        
        try:
            # 加载TFLite模型
            interpreter = tf.lite.Interpreter(model_path=str(model_path))
            interpreter.allocate_tensors()
            
            # 获取模型信息
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            tensor_details = interpreter.get_tensor_details()
            
            # 统计信息
            total_tensors = len(tensor_details)
            total_parameters = 0
            
            layer_info = []
            for tensor in tensor_details:
                shape = tensor['shape']
                size = np.prod(shape) if len(shape) > 0 else 1
                total_parameters += size
                
                layer_info.append({
                    'name': tensor['name'],
                    'shape': shape.tolist() if hasattr(shape, 'tolist') else shape,
                    'size': int(size),
                    'dtype': str(tensor['dtype'])
                })
            
            self.validation_results['model_structure'] = {
                'input_details': input_details,
                'output_details': output_details,
                'total_tensors': total_tensors,
                'total_parameters': int(total_parameters),
                'layers': layer_info
            }
            
            logger.info(f"输入形状: {input_details[0]['shape']}")
            logger.info(f"输出形状: {output_details[0]['shape']}")
            logger.info(f"总张量数: {total_tensors}")
            logger.info(f"总参数量: {total_parameters:,}")
            
            return True
            
        except Exception as e:
            logger.error(f"模型结构分析失败: {e}")
            self.validation_results['model_structure'] = {'error': str(e)}
            return False
    
    def benchmark_performance(self, model_path, num_iterations=100):
        """基准测试模型性能"""
        logger.info("=== 性能基准测试 ===")
        
        try:
            interpreter = tf.lite.Interpreter(model_path=str(model_path))
            interpreter.allocate_tensors()
            
            input_details = interpreter.get_input_details()
            output_details = interpreter.get_output_details()
            
            # 准备测试数据
            input_shape = input_details[0]['shape']
            test_input = np.random.random(input_shape).astype(np.float32)
            
            # 执行多次推理
            latencies = []
            for i in range(num_iterations):
                start_time = tf.timestamp()
                interpreter.set_tensor(input_details[0]['index'], test_input)
                interpreter.invoke()
                output = interpreter.get_tensor(output_details[0]['index'])
                end_time = tf.timestamp()
                
                latency = (end_time - start_time) * 1000  # 转换为毫秒
                latencies.append(latency)
            
            # 计算统计信息
            avg_latency = np.mean(latencies)
            std_latency = np.std(latencies)
            min_latency = np.min(latencies)
            max_latency = np.max(latencies)
            throughput = 1000 / avg_latency  # FPS
            
            self.validation_results['performance'] = {
                'iterations': num_iterations,
                'avg_latency_ms': round(avg_latency, 3),
                'std_latency_ms': round(std_latency, 3),
                'min_latency_ms': round(min_latency, 3),
                'max_latency_ms': round(max_latency, 3),
                'throughput_fps': round(throughput, 1),
                'latency_percentiles': {
                    '50th': round(np.percentile(latencies, 50), 3),
                    '90th': round(np.percentile(latencies, 90), 3),
                    '95th': round(np.percentile(latencies, 95), 3),
                    '99th': round(np.percentile(latencies, 99), 3)
                }
            }
            
            logger.info(f"平均延迟: {avg_latency:.3f} ms (±{std_latency:.3f})")
            logger.info(f"最小/最大延迟: {min_latency:.3f} / {max_latency:.3f} ms")
            logger.info(f"吞吐量: {throughput:.1f} FPS")
            logger.info(f"95%分位延迟: {np.percentile(latencies, 95):.3f} ms")
            
            return True
            
        except Exception as e:
            logger.error(f"性能测试失败: {e}")
            self.validation_results['performance'] = {'error': str(e)}
            return False
    
    def validate_quantization_effectiveness(self, model_path):
        """验证量化效果"""
        logger.info("=== 量化效果验证 ===")
        
        try:
            interpreter = tf.lite.Interpreter(model_path=str(model_path))
            tensor_details = interpreter.get_tensor_details()
            
            # 分析数据类型分布
            dtype_counts = {}
            quantized_layers = 0
            total_layers = len(tensor_details)
            
            for tensor in tensor_details:
                dtype = str(tensor['dtype'])
                dtype_counts[dtype] = dtype_counts.get(dtype, 0) + 1
                
                # 检查是否为量化类型
                if 'int8' in dtype.lower() or 'uint8' in dtype.lower():
                    quantized_layers += 1
            
            quantization_ratio = quantized_layers / total_layers if total_layers > 0 else 0
            
            self.validation_results['quantization_analysis'] = {
                'dtype_distribution': dtype_counts,
                'quantized_layers': quantized_layers,
                'total_layers': total_layers,
                'quantization_ratio': round(quantization_ratio, 3),
                'is_fully_quantized': quantization_ratio >= 0.8  # 80%以上层被量化
            }
            
            logger.info(f"数据类型分布: {dtype_counts}")
            logger.info(f"量化层比例: {quantization_ratio:.1%} ({quantized_layers}/{total_layers})")
            
            if quantization_ratio >= 0.8:
                logger.info("✅ 模型已充分量化")
            else:
                logger.warning("⚠️ 模型量化程度较低")
            
            return True
            
        except Exception as e:
            logger.error(f"量化分析失败: {e}")
            self.validation_results['quantization_analysis'] = {'error': str(e)}
            return False
    
    def generate_comprehensive_report(self, model_path, output_dir="./validation_reports"):
        """生成综合验证报告"""
        logger.info("=== 生成综合验证报告 ===")
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 执行所有验证步骤
        compliance_check = self.validate_model_compliance(model_path)
        structure_analysis = self.analyze_model_structure(model_path)
        performance_test = self.benchmark_performance(model_path)
        quantization_check = self.validate_quantization_effectiveness(model_path)
        
        # 添加元信息
        self.validation_results['validation_metadata'] = {
            'model_path': str(model_path),
            'target_size_kb': self.target_size_kb,
            'validation_timestamp': datetime.now().isoformat(),
            'validation_duration_seconds': (datetime.now() - self.start_time).total_seconds(),
            'steps_completed': {
                'compliance_check': compliance_check,
                'structure_analysis': structure_analysis,
                'performance_test': performance_test,
                'quantization_check': quantization_check
            }
        }
        
        # 生成报告文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = Path(model_path).stem
        report_filename = f"tflite_validation_{model_name}_{timestamp}.json"
        report_path = output_path / report_filename
        
        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)
        
        # 输出摘要
        self._print_validation_summary()
        logger.info(f"验证报告已保存到: {report_path}")
        
        return self.validation_results
    
    def _print_validation_summary(self):
        """打印验证摘要"""
        logger.info("\n" + "="*60)
        logger.info("验证摘要")
        logger.info("="*60)
        
        # 合规性状态
        file_compliance = self.validation_results.get('file_compliance', {})
        if file_compliance:
            is_compliant = file_compliance.get('is_compliant', False)
            size_kb = file_compliance.get('file_size_kb', 0)
            target_kb = file_compliance.get('target_size_kb', 0)
            
            if is_compliant:
                logger.info(f"✅ 内存合规: {size_kb}KB ≤ {target_kb}KB")
            else:
                excess = file_compliance.get('size_difference_kb', 0)
                logger.info(f"❌ 内存超限: {size_kb}KB > {target_kb}KB (+{excess}KB)")
        
        # 性能指标
        performance = self.validation_results.get('performance', {})
        if performance and 'error' not in performance:
            avg_latency = performance.get('avg_latency_ms', 0)
            throughput = performance.get('throughput_fps', 0)
            logger.info(f"⏱️  平均延迟: {avg_latency}ms")
            logger.info(f"⚡ 吞吐量: {throughput}FPS")
        
        # 量化效果
        quantization = self.validation_results.get('quantization_analysis', {})
        if quantization and 'error' not in quantization:
            quant_ratio = quantization.get('quantization_ratio', 0)
            is_fully_quantized = quantization.get('is_fully_quantized', False)
            status = "✅" if is_fully_quantized else "⚠️"
            logger.info(f"{status} 量化程度: {quant_ratio:.1%}")

def main():
    parser = argparse.ArgumentParser(description='TensorFlow Lite量化剪枝验证器')
    parser.add_argument('--model-path', type=str, required=True, help='TFLite模型路径')
    parser.add_argument('--target-size-kb', type=int, default=280, help='目标模型大小(KB)')
    parser.add_argument('--output-dir', type=str, default='./validation_reports', help='报告输出目录')
    parser.add_argument('--iterations', type=int, default=100, help='性能测试迭代次数')
    
    args = parser.parse_args()
    
    # 初始化验证器
    validator = TFLiteQuantizationPruningValidator(target_size_kb=args.target_size_kb)
    
    # 执行验证
    try:
        results = validator.generate_comprehensive_report(
            model_path=args.model_path,
            output_dir=args.output_dir
        )
        
        # 返回码表示合规性
        file_compliance = results.get('file_compliance', {})
        return 0 if file_compliance.get('is_compliant', False) else 1
        
    except Exception as e:
        logger.error(f"验证过程中发生错误: {e}")
        return 2

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)