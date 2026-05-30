#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型量化和剪枝优化器
针对硬件操作识别模型进行量化和剪枝，确保模型大小≤250KB且准确率≥85%
T5.2: 模型量化和剪枝优化
"""

import os
import sys
import json
import numpy as np
import tensorflow as tf
from datetime import datetime
import logging
from pathlib import Path
import shutil
from typing import Dict, List, Tuple, Any, Optional
import tempfile

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_optimization.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ModelQuantizerPruner:
    """模型量化剪枝优化器"""
    
    def __init__(self, target_size_kb: int = 250, target_accuracy: float = 0.85):
        self.target_size_kb = target_size_kb
        self.target_accuracy = target_accuracy
        self.optimization_dir = Path('models/optimized_hardware_classifier')
        self.optimization_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化TensorFlow Lite优化工具
        try:
            import tensorflow_model_optimization as tfmot
            self.tfmot = tfmot
            logger.info("TensorFlow Model Optimization工具包已加载")
        except ImportError:
            logger.warning("未安装tensorflow_model_optimization，某些功能可能受限")
            self.tfmot = None
    
    def create_baseline_model(self) -> tf.keras.Model:
        """
        创建基线模型用于优化实验
        """
        logger.info("=== 创建基线模型 ===")
        
        # 创建一个适合硬件操作识别的CNN模型
        model = tf.keras.Sequential([
            # 输入层
            tf.keras.layers.InputLayer(input_shape=(20,)),  # 20个传感器特征
            
            # 特征提取层
            tf.keras.layers.Dense(128, activation='relu', name='dense_1'),
            tf.keras.layers.BatchNormalization(name='bn_1'),
            tf.keras.layers.Dropout(0.3, name='dropout_1'),
            
            tf.keras.layers.Dense(64, activation='relu', name='dense_2'),
            tf.keras.layers.BatchNormalization(name='bn_2'),
            tf.keras.layers.Dropout(0.2, name='dropout_2'),
            
            tf.keras.layers.Dense(32, activation='relu', name='dense_3'),
            tf.keras.layers.BatchNormalization(name='bn_3'),
            
            # 输出层
            tf.keras.layers.Dense(6, activation='softmax', name='output')  # 6个硬件操作类别
        ])
        
        # 编译模型
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info("基线模型创建完成")
        logger.info(f"模型参数数量: {model.count_params():,}")
        return model
    
    def generate_training_data(self, num_samples: int = 5000) -> Tuple[np.ndarray, np.ndarray]:
        """
        生成训练数据
        """
        logger.info(f"生成 {num_samples} 个训练样本...")
        
        # 生成特征数据 (20个特征)
        X = np.random.randn(num_samples, 20).astype(np.float32)
        
        # 生成标签 (6个类别)
        y = np.random.randint(0, 6, num_samples)
        
        # 添加一些模式使分类有意义
        for i in range(6):
            mask = y == i
            # 为每个类别添加特定的特征模式
            feature_offset = i * 0.5
            X[mask, :5] += feature_offset  # 前5个特征偏移
        
        logger.info(f"训练数据生成完成: {X.shape}, 标签分布: {np.bincount(y)}")
        return X, y
    
    def train_baseline_model(self, model: tf.keras.Model) -> Dict[str, Any]:
        """
        训练基线模型
        """
        logger.info("=== 训练基线模型 ===")
        
        # 生成训练数据
        X_train, y_train = self.generate_training_data(4000)
        X_val, y_val = self.generate_training_data(1000)
        
        # 训练模型
        history = model.fit(
            X_train, y_train,
            epochs=30,
            batch_size=32,
            validation_data=(X_val, y_val),
            verbose=1
        )
        
        # 评估模型
        val_loss, val_accuracy = model.evaluate(X_val, y_val, verbose=0)
        
        training_result = {
            'epochs_trained': len(history.history['loss']),
            'final_loss': float(history.history['loss'][-1]),
            'final_accuracy': float(history.history['accuracy'][-1]),
            'val_loss': float(val_loss),
            'val_accuracy': float(val_accuracy),
            'training_history': history.history
        }
        
        logger.info(f"训练完成 - 验证准确率: {val_accuracy:.2%}")
        return training_result
    
    def apply_post_training_quantization(self, model: tf.keras.Model) -> bytes:
        """
        应用训练后量化
        """
        logger.info("=== 应用训练后量化 ===")
        
        # 创建代表数据集用于量化
        def representative_dataset():
            X, _ = self.generate_training_data(100)
            for i in range(100):
                yield [X[i:i+1].astype(np.float32)]
        
        # 转换为TensorFlow Lite模型
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = representative_dataset
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        
        tflite_model = converter.convert()
        logger.info("训练后量化完成")
        return tflite_model
    
    def apply_structured_pruning(self, model: tf.keras.Model) -> tf.keras.Model:
        """
        应用结构化剪枝
        """
        if not self.tfmot:
            logger.warning("跳过剪枝优化 - 未安装tfmot")
            return model
            
        logger.info("=== 应用结构化剪枝 ===")
        
        # 定义剪枝配置
        pruning_params = {
            'pruning_schedule': self.tfmot.sparsity.keras.PolynomialDecay(
                initial_sparsity=0.30,
                final_sparsity=0.70,
                begin_step=1000,
                end_step=5000
            )
        }
        
        # 对Dense层应用剪枝
        pruned_model = tf.keras.models.clone_model(
            model,
            clone_function=lambda layer: self.tfmot.sparsity.keras.prune_low_magnitude(layer, **pruning_params)
            if isinstance(layer, tf.keras.layers.Dense) and layer.name != 'output'
            else layer
        )
        
        # 编译剪枝模型
        pruned_model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        # 微调剪枝模型
        X_finetune, y_finetune = self.generate_training_data(1000)
        pruned_model.fit(
            X_finetune, y_finetune,
            epochs=5,
            batch_size=32,
            verbose=0
        )
        
        # 移除剪枝包装器
        stripped_model = self.tfmot.sparsity.keras.strip_pruning(pruned_model)
        
        logger.info("结构化剪枝完成")
        return stripped_model
    
    def apply_knowledge_distillation(self, teacher_model: tf.keras.Model) -> tf.keras.Model:
        """
        应用知识蒸馏创建学生模型
        """
        logger.info("=== 应用知识蒸馏 ===")
        
        # 创建更小的学生模型
        student_model = tf.keras.Sequential([
            tf.keras.layers.InputLayer(input_shape=(20,)),
            tf.keras.layers.Dense(64, activation='relu', name='student_dense_1'),
            tf.keras.layers.Dropout(0.2, name='student_dropout_1'),
            tf.keras.layers.Dense(32, activation='relu', name='student_dense_2'),
            tf.keras.layers.Dense(6, activation='softmax', name='student_output')
        ])
        
        # 编译学生模型
        student_model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.002),
            loss=tf.keras.losses.KLDivergence(),
            metrics=['accuracy']
        )
        
        # 生成软标签用于知识蒸馏
        X_distill, _ = self.generate_training_data(2000)
        teacher_predictions = teacher_model.predict(X_distill, verbose=0)
        
        # 使用软标签训练学生模型
        student_model.fit(
            X_distill, teacher_predictions,
            epochs=20,
            batch_size=32,
            verbose=0
        )
        
        logger.info("知识蒸馏完成")
        return student_model
    
    def optimize_model_pipeline(self) -> Dict[str, Any]:
        """
        执行完整的模型优化流水线
        """
        logger.info("=== 开始模型优化流水线 ===")
        
        optimization_results = {
            'timestamp': datetime.now().isoformat(),
            'target_requirements': {
                'max_size_kb': self.target_size_kb,
                'min_accuracy': self.target_accuracy
            },
            'optimization_steps': []
        }
        
        # 1. 创建和训练基线模型
        baseline_model = self.create_baseline_model()
        baseline_training = self.train_baseline_model(baseline_model)
        
        baseline_size = self._get_model_size_keras(baseline_model)
        baseline_result = {
            'step': 'baseline',
            'model_size_kb': baseline_size,
            'accuracy': baseline_training['val_accuracy'],
            'meets_requirements': baseline_training['val_accuracy'] >= self.target_accuracy and baseline_size <= self.target_size_kb
        }
        optimization_results['optimization_steps'].append(baseline_result)
        
        logger.info(f"基线模型 - 大小: {baseline_size}KB, 准确率: {baseline_training['val_accuracy']:.2%}")
        
        # 2. 应用训练后量化
        try:
            quantized_tflite = self.apply_post_training_quantization(baseline_model)
            quantized_size = len(quantized_tflite) / 1024
            
            # 评估量化模型准确率
            quantized_accuracy = self._evaluate_tflite_model(quantized_tflite)
            
            quantized_result = {
                'step': 'post_training_quantization',
                'model_size_kb': quantized_size,
                'accuracy': quantized_accuracy,
                'compression_ratio': baseline_size / quantized_size,
                'meets_requirements': quantized_accuracy >= self.target_accuracy and quantized_size <= self.target_size_kb
            }
            optimization_results['optimization_steps'].append(quantized_result)
            
            logger.info(f"量化模型 - 大小: {quantized_size:.1f}KB, 准确率: {quantized_accuracy:.2%}")
            
            # 保存量化模型
            quantized_path = self.optimization_dir / 'quantized_model.tflite'
            with open(quantized_path, 'wb') as f:
                f.write(quantized_tflite)
            logger.info(f"量化模型已保存到: {quantized_path}")
            
        except Exception as e:
            logger.error(f"量化过程失败: {e}")
            quantized_result = None
        
        # 3. 应用结构化剪枝
        try:
            pruned_model = self.apply_structured_pruning(baseline_model)
            pruned_size = self._get_model_size_keras(pruned_model)
            
            # 评估剪枝模型
            X_test, y_test = self.generate_training_data(500)
            _, pruned_accuracy = pruned_model.evaluate(X_test, y_test, verbose=0)
            
            pruned_result = {
                'step': 'structured_pruning',
                'model_size_kb': pruned_size,
                'accuracy': float(pruned_accuracy),
                'sparsity_ratio': 0.70,  # 剪枝率
                'meets_requirements': pruned_accuracy >= self.target_accuracy and pruned_size <= self.target_size_kb
            }
            optimization_results['optimization_steps'].append(pruned_result)
            
            logger.info(f"剪枝模型 - 大小: {pruned_size}KB, 准确率: {pruned_accuracy:.2%}")
            
        except Exception as e:
            logger.error(f"剪枝过程失败: {e}")
            pruned_result = None
        
        # 4. 应用知识蒸馏
        try:
            distilled_model = self.apply_knowledge_distillation(baseline_model)
            distilled_size = self._get_model_size_keras(distilled_model)
            
            # 评估蒸馏模型
            X_test, y_test = self.generate_training_data(500)
            _, distilled_accuracy = distilled_model.evaluate(X_test, y_test, verbose=0)
            
            distilled_result = {
                'step': 'knowledge_distillation',
                'model_size_kb': distilled_size,
                'accuracy': float(distilled_accuracy),
                'compression_ratio': baseline_size / distilled_size,
                'meets_requirements': distilled_accuracy >= self.target_accuracy and distilled_size <= self.target_size_kb
            }
            optimization_results['optimization_steps'].append(distilled_result)
            
            logger.info(f"蒸馏模型 - 大小: {distilled_size}KB, 准确率: {distilled_accuracy:.2%}")
            
        except Exception as e:
            logger.error(f"蒸馏过程失败: {e}")
            distilled_result = None
        
        # 5. 组合优化（量化+剪枝）
        if quantized_result and pruned_result:
            try:
                # 对剪枝模型应用量化
                pruned_quantized_tflite = self.apply_post_training_quantization(pruned_model)
                combined_size = len(pruned_quantized_tflite) / 1024
                combined_accuracy = self._evaluate_tflite_model(pruned_quantized_tflite)
                
                combined_result = {
                    'step': 'combined_optimization',
                    'model_size_kb': combined_size,
                    'accuracy': combined_accuracy,
                    'techniques_used': ['structured_pruning', 'post_training_quantization'],
                    'meets_requirements': combined_accuracy >= self.target_accuracy and combined_size <= self.target_size_kb
                }
                optimization_results['optimization_steps'].append(combined_result)
                
                logger.info(f"组合优化 - 大小: {combined_size:.1f}KB, 准确率: {combined_accuracy:.2%}")
                
                # 保存最佳模型
                if combined_result['meets_requirements']:
                    best_model_path = self.optimization_dir / 'best_optimized_model.tflite'
                    with open(best_model_path, 'wb') as f:
                        f.write(pruned_quantized_tflite)
                    optimization_results['best_model_path'] = str(best_model_path)
                    
            except Exception as e:
                logger.error(f"组合优化失败: {e}")
        
        # 确定最佳模型
        valid_models = [step for step in optimization_results['optimization_steps'] 
                       if step['meets_requirements']]
        
        if valid_models:
            # 选择满足要求且最小的模型
            best_model = min(valid_models, key=lambda x: x['model_size_kb'])
            optimization_results['best_model'] = best_model
            optimization_results['optimization_success'] = True
            logger.info(f"✓ 优化成功！最佳模型: {best_model['step']}")
        else:
            optimization_results['optimization_success'] = False
            logger.warning("✗ 没有模型满足所有要求")
        
        return optimization_results
    
    def _get_model_size_keras(self, model: tf.keras.Model) -> float:
        """获取Keras模型大小(KB)"""
        with tempfile.NamedTemporaryFile(suffix='.h5') as tmp:
            model.save(tmp.name, save_format='h5')
            return os.path.getsize(tmp.name) / 1024
    
    def _evaluate_tflite_model(self, tflite_model: bytes) -> float:
        """评估TensorFlow Lite模型准确率"""
        try:
            # 创建解释器
            interpreter = tf.lite.Interpreter(model_content=tflite_model)
            interpreter.allocate_tensors()
            
            # 获取输入输出张量
            input_details = interpreter.get_input_details()[0]
            output_details = interpreter.get_output_details()[0]
            
            # 生成测试数据
            X_test, y_test = self.generate_training_data(500)
            
            # 执行推理
            correct_predictions = 0
            for i in range(len(X_test)):
                # 设置输入
                input_data = X_test[i:i+1].astype(input_details['dtype'])
                interpreter.set_tensor(input_details['index'], input_data)
                
                # 运行推理
                interpreter.invoke()
                
                # 获取输出
                output_data = interpreter.get_tensor(output_details['index'])
                predicted_class = np.argmax(output_data[0])
                
                if predicted_class == y_test[i]:
                    correct_predictions += 1
            
            accuracy = correct_predictions / len(X_test)
            return accuracy
            
        except Exception as e:
            logger.error(f"TFLite模型评估失败: {e}")
            return 0.0
    
    def generate_optimization_report(self, optimization_results: Dict[str, Any]) -> str:
        """
        生成优化报告
        """
        logger.info("=== 生成优化报告 ===")
        
        report_filename = f"model_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.optimization_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(optimization_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"优化报告已保存到: {report_path}")
        return str(report_path)

def main():
    """主函数"""
    logger.info("🚀 模型量化剪枝优化器启动")
    logger.info("版本: 1.0.0")
    logger.info("目标: 模型大小≤250KB，准确率≥85%")
    
    # 创建优化器实例
    optimizer = ModelQuantizerPruner(target_size_kb=250, target_accuracy=0.85)
    
    try:
        # 执行优化流水线
        results = optimizer.optimize_model_pipeline()
        
        # 生成报告
        report_path = optimizer.generate_optimization_report(results)
        
        # 输出摘要
        logger.info("\n" + "="*60)
        logger.info("🎯 模型优化结果摘要")
        logger.info("="*60)
        
        if results['optimization_success']:
            best_model = results['best_model']
            logger.info(f"✅ 优化成功!")
            logger.info(f"🏆 最佳模型: {best_model['step']}")
            logger.info(f"📊 模型大小: {best_model['model_size_kb']:.1f}KB")
            logger.info(f"📈 准确率: {best_model['accuracy']:.2%}")
            
            techniques = best_model.get('techniques_used', [best_model['step']])
            logger.info(f"🔧 使用技术: {', '.join(techniques)}")
            
            if 'best_model_path' in results:
                logger.info(f"📁 模型文件: {results['best_model_path']}")
        else:
            logger.warning("❌ 优化失败 - 没有模型满足所有要求")
            logger.info("建议:")
            logger.info("  1. 收集更多训练数据")
            logger.info("  2. 调整模型架构")
            logger.info("  3. 降低准确率要求")
            logger.info("  4. 增加模型大小限制")
        
        logger.info(f"📄 详细报告: {report_path}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"优化过程出现错误: {e}")
        raise

if __name__ == "__main__":
    main()