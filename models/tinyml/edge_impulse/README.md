# Edge Impulse 模型目录

此目录包含通过Edge Impulse平台训练和导出的TinyML模型。

## 目录结构

```
edge_impulse/
├── voice_commands/           # 语音命令识别模型
│   ├── ei-voice-model-v1.0.0/
│   │   ├── ei-voice-model-v1.0.0.tflite     # TFLite模型文件
│   │   ├── ei-voice-model-v1.0.0.json       # 模型元数据
│   │   ├── ei-voice-model-v1.0.0-arduino.zip # Arduino库
│   │   └── README.md                        # 模型说明
│   └── ei-voice-model-v1.1.0/
│       ├── ei-voice-model-v1.1.0.tflite
│       ├── ei-voice-model-v1.1.0.json
│       ├── ei-voice-model-v1.1.0-arduino.zip
│       └── README.md
├── gesture_recognition/      # 手势识别模型
│   └── ei-gesture-model-v1.0.0/
│       ├── ei-gesture-model-v1.0.0.tflite
│       ├── ei-gesture-model-v1.0.0.json
│       └── README.md
├── anomaly_detection/        # 异常检测模型
│   └── ei-anomaly-model-v1.0.0/
│       ├── ei-anomaly-model-v1.0.0.tflite
│       ├── ei-anomaly-model-v1.0.0.json
│       └── README.md
└── templates/               # 模板文件
    ├── model_template.json
    └── deployment_template.md
```

## 模型命名规范

- 格式: `ei-{功能}-{版本号}`
- 示例: `ei-voice-model-v1.0.0`
- 版本号遵循语义化版本控制 (SemVer)

## 文件说明

### .tflite 文件
- TensorFlow Lite格式的量化模型
- 已针对微控制器优化
- 包含完整的模型架构和权重

### .json 文件
- 模型元数据和配置信息
- 包含输入输出规格、标签映射等
- Edge Impulse特定的模型信息

### -arduino.zip 文件
- 为Arduino平台准备的完整库
- 包含模型文件和必要的C++包装器
- 可直接导入Arduino IDE使用

## 部署指南

### ESP32部署
```bash
# 1. 下载Arduino库
# 2. 解压到Arduino库目录
# 3. 在Arduino IDE中包含库
#include <EI-VOICE-MODEL-V1-0-0.h>

# 4. 使用示例代码
VoiceInference inference;
float predictions[5];
inference.classify(features, predictions);
```

### 平台要求
- **ESP32**: 至少4MB Flash, 520KB RAM
- **Arduino Nano 33 BLE**: 1MB Flash, 256KB RAM
- **其他MCU**: 根据模型大小调整

## 性能基准

每个模型目录应包含对应的基准测试结果：
- 推理时间 (ms)
- 内存占用 (KB)
- 模型大小 (KB)
- 准确率 (%)

## 更新日志

### v1.0.0 (2026-02-28)
- 初始版本发布
- 支持基本语音命令识别
- 针对ESP32优化

### v1.1.0 (待发布)
- 改进的准确性
- 更小的模型尺寸
- 支持更多命令类别