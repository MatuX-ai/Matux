#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TinyML语音识别模型训练和转换脚本
支持中文和英文语音指令的端到端训练流程
"""

import os
import sys
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import librosa
import soundfile as sf
from pathlib import Path
import argparse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VoiceDatasetGenerator:
    """语音数据集生成器"""
    
    def __init__(self, sample_rate=16000, duration=1.0):
        self.sample_rate = sample_rate
        self.duration = duration
        self.samples_per_audio = int(sample_rate * duration)
        
    def generate_synthetic_data(self, num_samples_per_class=1000):
        """生成合成语音数据用于演示"""
        logger.info("生成合成语音数据...")
        
        # 定义命令类别
        commands = {
            'light_on': ['开灯', '打开灯', '亮灯', 'turn on', 'light on'],
            'light_off': ['关灯', '关闭灯', '灭灯', 'turn off', 'light off'],
            'custom_1': ['播放音乐', 'play music'],
            'custom_2': ['停止播放', 'stop playing']
        }
        
        X = []  # 特征数据
        y = []  # 标签
        
        # 为每个命令生成样本
        for class_name, phrases in commands.items():
            logger.info(f"生成 {class_name} 类别数据 ({len(phrases)} 个短语)")
            
            for i in range(num_samples_per_class):
                # 随机选择一个短语
                phrase = np.random.choice(phrases)
                
                # 生成合成音频特征
                features = self._generate_audio_features(phrase, i)
                X.append(features)
                y.append(class_name)
                
                if (i + 1) % 200 == 0:
                    logger.info(f"  已生成 {i + 1}/{num_samples_per_class} 样本")
        
        X = np.array(X)
        y = np.array(y)
        
        logger.info(f"数据生成完成: {X.shape[0]} 样本, {X.shape[1]} 特征维度")
        return X, y
    
    def _generate_audio_features(self, text, seed):
        """生成音频特征（简化版MFCC）"""
        np.random.seed(seed)
        
        # 模拟语音信号
        t = np.linspace(0, self.duration, self.samples_per_audio)
        
        # 基频和谐波
        fundamental_freq = 100 + np.random.randint(0, 200)
        signal = np.sin(2 * np.pi * fundamental_freq * t)
        
        # 添加谐波
        for harmonic in range(2, 5):
            amplitude = 0.3 / harmonic
            phase = np.random.random() * 2 * np.pi
            signal += amplitude * np.sin(2 * np.pi * fundamental_freq * harmonic * t + phase)
        
        # 添加噪声
        noise_level = 0.1 + np.random.random() * 0.2
        signal += np.random.normal(0, noise_level, len(signal))
        
        # 提取MFCC特征（简化版）
        mfcc_features = self._extract_mfcc(signal)
        
        return mfcc_features
    
    def _extract_mfcc(self, signal):
        """提取MFCC特征"""
        try:
            # 使用librosa提取MFCC
            mfcc = librosa.feature.mfcc(
                y=signal,
                sr=self.sample_rate,
                n_mfcc=13,
                n_fft=512,
                hop_length=256
            )
            
            # 计算统计特征
            mfcc_mean = np.mean(mfcc, axis=1)
            mfcc_std = np.std(mfcc, axis=1)
            
            # 组合特征
            features = np.concatenate([mfcc_mean, mfcc_std])
            
            # 确保特征维度一致
            target_size = 40  # 与系统配置匹配
            if len(features) < target_size:
                features = np.pad(features, (0, target_size - len(features)))
            elif len(features) > target_size:
                features = features[:target_size]
                
            return features.astype(np.float32)
            
        except Exception as e:
            logger.warning(f"MFCC提取失败，使用随机特征: {e}")
            return np.random.random(40).astype(np.float32)

class VoiceRecognitionModel:
    """语音识别模型"""
    
    def __init__(self, input_shape=(40,), num_classes=5):
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.model = None
        self.label_encoder = LabelEncoder()
        
    def build_model(self):
        """构建轻量级CNN模型"""
        logger.info("构建语音识别模型...")
        
        model = models.Sequential([
            # 输入层
            layers.Input(shape=self.input_shape),
            
            # 重塑为2D进行卷积
            layers.Reshape((self.input_shape[0], 1)),
            
            # 第一个卷积块
            layers.Conv1D(16, 3, activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling1D(2),
            layers.Dropout(0.2),
            
            # 第二个卷积块
            layers.Conv1D(32, 3, activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.MaxPooling1D(2),
            layers.Dropout(0.2),
            
            # 第三个卷积块
            layers.Conv1D(64, 3, activation='relu', padding='same'),
            layers.BatchNormalization(),
            layers.GlobalAveragePooling1D(),
            layers.Dropout(0.3),
            
            # 全连接层
            layers.Dense(64, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.4),
            
            # 输出层
            layers.Dense(self.num_classes, activation='softmax')
        ])
        
        model.compile(
            optimizer='adam',
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        logger.info("模型构建完成")
        return model
    
    def train(self, X_train, y_train, X_val, y_val, epochs=50, batch_size=32):
        """训练模型"""
        logger.info("开始训练模型...")
        
        # 编译标签
        y_train_encoded = self.label_encoder.fit_transform(y_train)
        y_val_encoded = self.label_encoder.transform(y_val)
        
        # 训练模型
        history = self.model.fit(
            X_train, y_train_encoded,
            validation_data=(X_val, y_val_encoded),
            epochs=epochs,
            batch_size=batch_size,
            verbose=1,
            callbacks=[
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_accuracy',
                    patience=10,
                    restore_best_weights=True
                ),
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-7
                )
            ]
        )
        
        logger.info("训练完成")
        return history
    
    def evaluate(self, X_test, y_test):
        """评估模型"""
        logger.info("评估模型性能...")
        
        y_test_encoded = self.label_encoder.transform(y_test)
        test_loss, test_accuracy = self.model.evaluate(X_test, y_test_encoded, verbose=0)
        
        logger.info(f"测试准确率: {test_accuracy:.4f}")
        logger.info(f"测试损失: {test_loss:.4f}")
        
        return test_accuracy, test_loss
    
    def save_model(self, model_path, tflite_path=None):
        """保存模型"""
        logger.info(f"保存模型到: {model_path}")
        
        # 保存Keras模型
        self.model.save(model_path)
        
        # 转换为TensorFlow Lite格式
        if tflite_path:
            self.convert_to_tflite(model_path, tflite_path)
    
    def convert_to_tflite(self, model_path, tflite_path):
        """转换为TensorFlow Lite格式"""
        logger.info("转换为TensorFlow Lite格式...")
        
        # 加载模型
        model = tf.keras.models.load_model(model_path)
        
        # 转换为TFLite
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        # 量化选项（可选）
        converter.representative_dataset = self._representative_dataset_gen()
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        
        tflite_model = converter.convert()
        
        # 保存TFLite模型
        with open(tflite_path, 'wb') as f:
            f.write(tflite_model)
        
        # 获取模型大小信息
        original_size = os.path.getsize(model_path)
        tflite_size = os.path.getsize(tflite_path)
        
        logger.info(f"TFLite模型保存到: {tflite_path}")
        logger.info(f"原始模型大小: {original_size:,} bytes")
        logger.info(f"TFLite模型大小: {tflite_size:,} bytes")
        logger.info(f"压缩比例: {tflite_size/original_size:.2%}")
    
    def _representative_dataset_gen(self):
        """代表数据集生成器（用于量化）"""
        def representative_dataset():
            for _ in range(100):
                # 生成随机数据作为代表数据集
                data = np.random.random((1,) + self.input_shape).astype(np.float32)
                yield [data]
        return representative_dataset

def main():
    parser = argparse.ArgumentParser(description='TinyML语音识别模型训练')
    parser.add_argument('--samples', type=int, default=1000, help='每类样本数量')
    parser.add_argument('--epochs', type=int, default=50, help='训练轮数')
    parser.add_argument('--batch-size', type=int, default=32, help='批次大小')
    parser.add_argument('--output-dir', type=str, default='./models', help='输出目录')
    parser.add_argument('--test-mode', action='store_true', help='测试模式（少量数据）')
    
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 如果是测试模式，减少数据量
    if args.test_mode:
        args.samples = 100
        args.epochs = 10
        logger.info("运行测试模式...")
    
    try:
        # 1. 生成数据集
        dataset_gen = VoiceDatasetGenerator()
        X, y = dataset_gen.generate_synthetic_data(args.samples)
        
        # 2. 划分数据集
        X_temp, X_test, y_temp, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
        )
        
        logger.info(f"训练集: {len(X_train)}, 验证集: {len(X_val)}, 测试集: {len(X_test)}")
        
        # 3. 构建和训练模型
        model = VoiceRecognitionModel(input_shape=(40,), num_classes=len(np.unique(y)))
        model.build_model()
        model.train(X_train, y_train, X_val, y_val, 
                   epochs=args.epochs, batch_size=args.batch_size)
        
        # 4. 评估模型
        accuracy, loss = model.evaluate(X_test, y_test)
        
        # 5. 保存模型
        keras_model_path = output_dir / 'voice_model.h5'
        tflite_model_path = output_dir / 'voice_model.tflite'
        model.save_model(str(keras_model_path), str(tflite_model_path))
        
        # 6. 保存元数据
        metadata = {
            'model_version': '1.0.0',
            'input_shape': [40],
            'num_classes': len(np.unique(y)),
            'class_labels': model.label_encoder.classes_.tolist(),
            'test_accuracy': float(accuracy),
            'test_loss': float(loss),
            'training_samples': len(X_train),
            'feature_type': 'MFCC_40D'
        }
        
        metadata_path = output_dir / 'model_metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info("=== 训练完成 ===")
        logger.info(f"模型版本: {metadata['model_version']}")
        logger.info(f"类别数: {metadata['num_classes']}")
        logger.info(f"测试准确率: {accuracy:.4f}")
        logger.info(f"模型文件: {tflite_model_path}")
        logger.info(f"元数据文件: {metadata_path}")
        
    except Exception as e:
        logger.error(f"训练过程中发生错误: {e}")
        raise

if __name__ == '__main__':
    main()