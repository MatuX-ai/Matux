#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型转换和优化工具
将训练好的模型转换为适合ESP32的TensorFlow Lite格式
包括量化、剪枝等优化技术
"""

import os
import sys
import json
import numpy as np
import tensorflow as tf
from pathlib import Path
import argparse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelOptimizer:
    """模型优化器"""
    
    def __init__(self, model_path):
        self.model_path = Path(model_path)
        self.optimized_models = {}
        
    def load_and_analyze_model(self):
        """加载并分析模型"""
        logger.info(f"加载模型: {self.model_path}")
        
        try:
            self.model = tf.keras.models.load_model(self.model_path)
            logger.info("模型加载成功")
            
            # 分析模型结构
            self._analyze_model_structure()
            return True
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False
    
    def _analyze_model_structure(self):
        """分析模型结构"""
        logger.info("=== 模型结构分析 ===")
        logger.info(f"输入形状: {self.model.input_shape}")
        logger.info(f"输出形状: {self.model.output_shape}")
        
        total_params = self.model.count_params()
        trainable_params = sum([tf.keras.backend.count_params(w) 
                               for w in self.model.trainable_weights])
        
        logger.info(f"总参数量: {total_params:,}")
        logger.info(f"可训练参数: {trainable_params:,}")
        logger.info(f"层数: {len(self.model.layers)}")
        
        # 详细层信息
        for i, layer in enumerate(self.model.layers):
            logger.info(f"  Layer {i}: {layer.name} - {layer.__class__.__name__}")
    
    def convert_to_float_tflite(self, output_path):
        """转换为浮点TFLite模型"""
        logger.info("转换为浮点TFLite模型...")
        
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        try:
            tflite_model = converter.convert()
            with open(output_path, 'wb') as f:
                f.write(tflite_model)
            
            size = os.path.getsize(output_path)
            logger.info(f"浮点TFLite模型保存完成: {output_path} ({size:,} bytes)")
            self.optimized_models['float32'] = output_path
            return True
            
        except Exception as e:
            logger.error(f"浮点转换失败: {e}")
            return False
    
    def convert_to_quantized_tflite(self, output_path, representative_dataset=None, target_size_kb=280):
        """转换为量化TFLite模型，支持严格内存限制"""
        logger.info(f"转换为量化TFLite模型 (目标大小: {target_size_kb}KB)...")
        
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # 设置量化参数
        if representative_dataset:
            converter.representative_dataset = representative_dataset
        else:
            # 使用默认代表数据集
            converter.representative_dataset = self._create_representative_dataset()
        
        # 启用全整数量化
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        
        try:
            tflite_model = converter.convert()
            with open(output_path, 'wb') as f:
                f.write(tflite_model)
            
            size = os.path.getsize(output_path)
            size_kb = size / 1024
            
            logger.info(f"量化TFLite模型保存完成: {output_path} ({size:,} bytes, {size_kb:.1f}KB)")
            
            # 检查是否满足内存限制
            if size_kb <= target_size_kb:
                logger.info(f"✅ 模型大小满足要求 (≤{target_size_kb}KB)")
                self.optimized_models['int8'] = output_path
                return True
            else:
                logger.warning(f"⚠️ 模型大小超出限制 ({size_kb:.1f}KB > {target_size_kb}KB)")
                # 尝试更激进的量化策略
                return self._aggressive_quantization(output_path, target_size_kb)
            
        except Exception as e:
            logger.error(f"量化转换失败: {e}")
            return False
    
    def _create_representative_dataset(self):
        """创建代表数据集用于量化"""
        def representative_dataset():
            # 生成符合输入形状的随机数据
            input_shape = self.model.input_shape[1:]  # 移除batch维度
            
            for _ in range(100):
                # 生成-1到1之间的随机数据
                data = np.random.uniform(-1, 1, (1,) + input_shape).astype(np.float32)
                yield [data]
        
        return representative_dataset
    
    def _aggressive_quantization(self, output_path, target_size_kb):
        """尝试更激进的量化策略以满足内存限制"""
        logger.info("尝试激进量化策略...")
        
        # 策略1: 动态范围量化
        try:
            converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            # 不使用代表数据集，启用动态范围量化
            
            tflite_model = converter.convert()
            temp_path = output_path.replace('.tflite', '_dynamic.tflite')
            with open(temp_path, 'wb') as f:
                f.write(tflite_model)
            
            size_kb = os.path.getsize(temp_path) / 1024
            if size_kb <= target_size_kb:
                os.rename(temp_path, output_path)
                logger.info(f"✅ 动态范围量化成功: {size_kb:.1f}KB")
                self.optimized_models['dynamic_quant'] = output_path
                return True
            else:
                os.remove(temp_path)
                logger.info(f"动态范围量化仍超出限制: {size_kb:.1f}KB")
        except Exception as e:
            logger.warning(f"动态范围量化失败: {e}")
        
        # 策略2: 权重量化
        try:
            converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
            converter.optimizations = [tf.lite.Optimize.OPTIMIZE_FOR_SIZE]
            converter.representative_dataset = self._create_representative_dataset()
            
            tflite_model = converter.convert()
            temp_path = output_path.replace('.tflite', '_weight.tflite')
            with open(temp_path, 'wb') as f:
                f.write(tflite_model)
            
            size_kb = os.path.getsize(temp_path) / 1024
            if size_kb <= target_size_kb:
                os.rename(temp_path, output_path)
                logger.info(f"✅ 权重量化成功: {size_kb:.1f}KB")
                self.optimized_models['weight_quant'] = output_path
                return True
            else:
                os.remove(temp_path)
                logger.info(f"权重量化仍超出限制: {size_kb:.1f}KB")
        except Exception as e:
            logger.warning(f"权重量化失败: {e}")
        
        logger.error("所有量化策略都无法满足内存限制要求")
        return False
    
    def apply_model_pruning(self, sparsity=0.5, target_size_kb=280):
        """应用模型剪枝，支持内存限制"""
        logger.info(f"应用模型剪枝 (稀疏度: {sparsity}, 目标大小: {target_size_kb}KB)...")
        
        try:
            import tensorflow_model_optimization as tfmot
        except ImportError:
            logger.error("未安装tensorflow_model_optimization，请运行: pip install tensorflow-model-optimization")
            return None
        
        # 定义剪枝参数
        pruning_params = {
            'pruning_schedule': tfmot.sparsity.keras.PolynomialDecay(
                initial_sparsity=0.0,
                final_sparsity=sparsity,
                begin_step=0,
                end_step=1000
            )
        }
        
        # 应用剪枝到每一层
        pruned_model = tf.keras.models.clone_model(self.model)
        for i, layer in enumerate(pruned_model.layers):
            if isinstance(layer, (tf.keras.layers.Dense, tf.keras.layers.Conv1D, 
                                tf.keras.layers.Conv2D, tf.keras.layers.LSTM)):
                pruned_model.layers[i] = tfmot.sparsity.keras.prune_low_magnitude(
                    layer, **pruning_params)
        
        # 编译剪枝模型
        pruned_model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info("模型剪枝完成")
        return pruned_model
    
    def benchmark_models(self, target_size_kb=280):
        """基准测试不同模型版本，包含内存合规性检查"""
        logger.info("=== 模型基准测试 ===")
        
        results = {}
        compliant_models = []
        
        for model_type, model_path in self.optimized_models.items():
            logger.info(f"测试 {model_type} 模型...")
            
            try:
                # 获取文件大小
                file_size = os.path.getsize(model_path)
                file_size_kb = file_size / 1024
                
                # 内存合规性检查
                is_compliant = file_size_kb <= target_size_kb
                if is_compliant:
                    compliant_models.append(model_type)
                    compliance_status = "✅ 合规"
                else:
                    compliance_status = f"❌ 超限 ({file_size_kb:.1f}KB > {target_size_kb}KB)"
                
                # 加载TFLite模型进行性能测试
                interpreter = tf.lite.Interpreter(model_path=str(model_path))
                interpreter.allocate_tensors()
                
                # 获取输入输出信息
                input_details = interpreter.get_input_details()
                output_details = interpreter.get_output_details()
                
                # 准备测试数据
                input_shape = input_details[0]['shape']
                test_input = np.random.random(input_shape).astype(np.float32)
                
                # 运行推理
                import time
                times = []
                for _ in range(10):  # 多次测试取平均值
                    start_time = time.perf_counter()
                    interpreter.set_tensor(input_details[0]['index'], test_input)
                    interpreter.invoke()
                    output = interpreter.get_tensor(output_details[0]['index'])
                    inference_time = (time.perf_counter() - start_time) * 1000
                    times.append(inference_time)
                
                avg_inference_time = np.mean(times)
                std_inference_time = np.std(times)
                
                # 记录结果
                results[model_type] = {
                    'file_size_bytes': file_size,
                    'file_size_kb': round(file_size_kb, 2),
                    'compliance_status': compliance_status,
                    'is_compliant': is_compliant,
                    'avg_inference_time_ms': round(avg_inference_time, 2),
                    'std_inference_time_ms': round(std_inference_time, 2),
                    'input_shape': input_shape.tolist(),
                    'output_shape': output.shape[1] if len(output.shape) > 1 else output.shape[0],
                    'throughput_fps': round(1000 / avg_inference_time, 1)
                }
                
                logger.info(f"  文件大小: {file_size:,} bytes ({file_size_kb:.1f}KB) {compliance_status}")
                logger.info(f"  平均推理时间: {avg_inference_time:.2f} ± {std_inference_time:.2f} ms")
                logger.info(f"  吞吐量: {results[model_type]['throughput_fps']} FPS")
                logger.info(f"  输入形状: {input_shape}")
                logger.info(f"  输出形状: {output.shape}")
                
            except Exception as e:
                logger.error(f"  测试 {model_type} 模型时出错: {e}")
                results[model_type] = {'error': str(e), 'is_compliant': False}
        
        # 总结合规性
        logger.info(f"\n=== 合规性总结 ===")
        logger.info(f"目标内存限制: {target_size_kb}KB")
        logger.info(f"合规模型数量: {len(compliant_models)}/{len(self.optimized_models)}")
        if compliant_models:
            logger.info(f"合规模型: {', '.join(compliant_models)}")
        else:
            logger.warning("⚠️ 没有模型满足内存限制要求")
        
        return results

def create_model_header(tflite_path, header_path, model_name="voice_model"):
    """创建C++头文件包含模型数据"""
    logger.info(f"创建模型头文件: {header_path}")
    
    try:
        # 读取TFLite模型数据
        with open(tflite_path, 'rb') as f:
            model_data = f.read()
        
        # 生成C++数组
        hex_data = ', '.join([f'0x{b:02x}' for b in model_data])
        
        # 创建头文件内容
        header_content = f"""/*
 * TensorFlow Lite 模型数据头文件
 * 自动生成于 {tf.timestamp()}
 * 模型来源: {tflite_path}
 */

#ifndef {model_name.upper()}_H
#define {model_name.upper()}_H

#include <cstdint>

// 模型数据
alignas(16) const uint8_t {model_name}_data[] = {{
    {hex_data}
}};

// 模型大小
const int {model_name}_len = sizeof({model_name}_data);

#endif // {model_name.upper()}_H
"""
        
        # 保存头文件
        with open(header_path, 'w') as f:
            f.write(header_content)
        
        logger.info(f"模型头文件创建完成: {header_path}")
        logger.info(f"模型大小: {len(model_data):,} bytes")
        
    except Exception as e:
        logger.error(f"创建头文件失败: {e}")

def main():
    parser = argparse.ArgumentParser(description='模型优化和转换工具')
    parser.add_argument('--model-path', type=str, required=True, help='输入模型路径')
    parser.add_argument('--output-dir', type=str, default='./optimized_models', help='输出目录')
    parser.add_argument('--quantize', action='store_true', help='启用量化')
    parser.add_argument('--prune', action='store_true', help='启用剪枝')
    parser.add_argument('--sparsity', type=float, default=0.5, help='剪枝稀疏度')
    parser.add_argument('--target-size-kb', type=int, default=280, help='目标模型大小(KB)')
    parser.add_argument('--benchmark', action='store_true', help='执行基准测试')
    parser.add_argument('--create-header', action='store_true', help='创建C++头文件')
    
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    try:
        # 初始化优化器
        optimizer = ModelOptimizer(args.model_path)
        
        # 加载和分析模型
        if not optimizer.load_and_analyze_model():
            return False
        
        # 基础浮点转换
        float_model_path = output_dir / 'model_float32.tflite'
        optimizer.convert_to_float_tflite(float_model_path)
        
        # 量化转换
        if args.quantize:
            quant_model_path = output_dir / 'model_quantized.tflite'
            optimizer.convert_to_quantized_tflite(quant_model_path, target_size_kb=args.target_size_kb)
        
        # 剪枝（如果需要）
        if args.prune:
            pruned_model = optimizer.apply_model_pruning(args.sparsity, target_size_kb=args.target_size_kb)
            if pruned_model is not None:
                pruned_model_path = output_dir / 'model_pruned.h5'
                pruned_model.save(pruned_model_path)
                logger.info(f"剪枝模型保存到: {pruned_model_path}")
        
        # 基准测试
        if args.benchmark:
            benchmark_results = optimizer.benchmark_models(target_size_kb=args.target_size_kb)
            benchmark_file = output_dir / 'benchmark_results.json'
            with open(benchmark_file, 'w', encoding='utf-8') as f:
                json.dump(benchmark_results, f, indent=2, ensure_ascii=False)
            logger.info(f"基准测试结果保存到: {benchmark_file}")
        
        # 创建C++头文件
        if args.create_header:
            if 'int8' in optimizer.optimized_models:
                model_path = optimizer.optimized_models['int8']
                header_path = output_dir / 'voice_model_data.h'
                create_model_header(model_path, header_path)
            else:
                logger.warning("未找到量化模型，跳过头文件创建")
        
        logger.info("=== 优化完成 ===")
        logger.info(f"输出目录: {output_dir}")
        logger.info("生成的文件:")
        for model_type, path in optimizer.optimized_models.items():
            size = os.path.getsize(path)
            logger.info(f"  {model_type}: {path} ({size:,} bytes)")
        
    except Exception as e:
        logger.error(f"优化过程中发生错误: {e}")
        raise

if __name__ == '__main__':
    main()