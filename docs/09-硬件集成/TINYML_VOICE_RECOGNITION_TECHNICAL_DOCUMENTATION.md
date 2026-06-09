# ESP32 TinyML 语音识别系统技术文档

## 📋 项目概述

本项目实现了基于TensorFlow Lite Micro的ESP32边缘计算语音识别系统，支持离线中文/英文语音指令识别，并具备BLE模型热更新功能。

## 🏗️ 系统架构

### 整体架构图
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   麦克风输入    │───▶│  音频预处理模块  │───▶│ 特征提取(MFCC)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                    │
                                                    ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ TensorFlow Lite │◀───│  模型推理引擎    │◀───│   特征向量      │
│    模型         │    │                  │    │  (40维)         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  BLE通信模块    │    │ 硬件控制模块     │    │  系统状态管理   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 核心模块说明

#### 1. 语音识别系统 (VoiceRecognitionSystem)
- **功能**: 音频采集、特征提取、模型推理
- **关键技术**: I2S音频接口、MFCC特征提取、TensorFlow Lite Micro
- **主要方法**:
  - `initialize()`: 系统初始化
  - `processAudio()`: 音频处理主循环
  - `classifyCommand()`: 命令分类

#### 2. BLE模型更新器 (BLEModelUpdater)
- **功能**: 无线模型更新、状态监控
- **关键技术**: NimBLE协议栈、OTA更新机制
- **主要方法**:
  - `initialize()`: BLE服务初始化
  - `handleModelData()`: 模型数据处理
  - `activateNewModel()`: 新模型激活

#### 3. 硬件控制器 (HardwareController)
- **功能**: LED指示、灯光控制、按钮处理
- **主要方法**:
  - `setLedState()`: LED状态控制
  - `controlLight()`: 灯光开关控制
  - `getMicrophoneLevel()`: 麦克风电平读取

## 🔧 技术规格

### 硬件要求
- **主控芯片**: ESP32-D0WDQ6 (双核 240MHz)
- **内存配置**: 520KB SRAM + 4MB Flash
- **音频输入**: I2S数字麦克风接口
- **通信接口**: BLE 4.2 (NimBLE)
- **电源要求**: 3.3V ±5%, 最大电流 500mA

### 软件环境
- **开发框架**: PlatformIO + Arduino Core
- **AI框架**: TensorFlow Lite Micro v2.12.0
- **蓝牙协议**: NimBLE-Arduino v1.4.1
- **音频处理**: ESP8266Audio库
- **数据格式**: JSON + Protocol Buffers

### 性能指标
| 指标 | 数值 | 说明 |
|------|------|------|
| 识别准确率 | ≥85% | 在安静环境下 |
| 响应延迟 | ≤1000ms | 从语音输入到输出响应 |
| 模型大小 | ≤200KB | 量化后的TFLite模型 |
| 功耗 | ≤150mA | 正常工作状态 |
| 工作温度 | -10°C ~ 60°C | 工业级工作范围 |

## 📊 模型架构

### 神经网络结构
```
Input (40,) → Reshape → Conv1D(16) → MaxPool → Dropout(0.2)
                    ↓
              Conv1D(32) → MaxPool → Dropout(0.2)
                    ↓
              Conv1D(64) → GlobalAvgPool → Dropout(0.3)
                    ↓
              Dense(64) → Dropout(0.4) → Dense(5) → Softmax
```

### 特征工程
- **特征类型**: MFCC (Mel-frequency cepstral coefficients)
- **特征维度**: 40维 (13个系数的均值和标准差)
- **采样率**: 16kHz
- **帧长**: 25ms (400样本)
- **帧移**: 10ms (160样本)

## 🔌 接口定义

### 硬件接口
```cpp
// 引脚定义
#define PIN_LED_STATUS      2      // 状态LED
#define PIN_MICROPHONE      34     // 麦克风输入 (I2S_SD)
#define PIN_LIGHT_CONTROL   18     // 灯光控制输出
#define PIN_BUTTON_CONFIG   0      // 配置按钮

// I2S配置
#define I2S_SCK_PIN         26     // 时钟线
#define I2S_WS_PIN          25     // 字选择线
```

### BLE服务接口
```cpp
// 服务UUID
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define MODEL_CHAR_UUID     "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define STATUS_CHAR_UUID    "beb5483e-36e1-4688-b7f5-ea07361b26a9"

// 控制命令格式 (JSON)
{
  "command": "START_TRANSFER",
  "model_name": "voice_model_v1.1.0",
  "version": "1.1.0",
  "size": 156789
}
```

### 串口调试接口
```cpp
// 系统命令
"VERSION"          // 查询系统版本
"STATUS"           // 查询系统状态
"HW_INFO"          // 硬件信息
"MODEL_INFO"       // 模型信息
"RECOGNITION_COUNT" // 识别次数统计
"TEST_LED"         // LED自检
"TEST_AUDIO"       // 音频测试
"TEST_BLE"         // BLE测试
```

## 🔄 工作流程

### 1. 系统启动流程
```
1. 硬件初始化 (LED, GPIO, I2S)
2. 系统信息显示
3. TensorFlow Lite模型加载
4. BLE服务启动
5. 系统就绪状态指示
```

### 2. 语音识别流程
```
1. 实时音频采集 (I2S)
2. 音量检测和静音过滤
3. MFCC特征提取
4. TFLite模型推理
5. 结果置信度过滤
6. 执行相应控制动作
7. 状态反馈和日志记录
```

### 3. BLE模型更新流程
```
1. 客户端连接BLE服务
2. 发送START_TRANSFER命令
3. 分块传输模型数据
4. 接收方验证数据完整性
5. 备份当前模型
6. 激活新模型
7. 重启语音识别服务
```

## 🛠️ 开发指南

### 环境搭建
```bash
# 1. 安装PlatformIO
pip install platformio

# 2. 克隆项目
git clone <repository-url>
cd hardware/tinyml-voice-recognition

# 3. 安装依赖库
pio lib install

# 4. 编译项目
pio run

# 5. 上传固件
pio run --target upload
```

### 模型训练流程
```bash
# 1. 生成训练数据
python scripts/tinyml_voice_training.py --samples 2000 --epochs 100

# 2. 优化和转换模型
python scripts/model_optimizer.py --model-path ./models/voice_model.h5 --quantize --benchmark

# 3. 生成嵌入式模型头文件
python scripts/model_optimizer.py --create-header
```

### 硬件测试
```bash
# 运行完整认证测试
python scripts/hardware_certification_framework.py --port COM3 --output test_report.json

# 模拟模式测试
python scripts/hardware_certification_framework.py --simulate
```

## ⚙️ 配置参数

### 系统配置 (SystemConfig.h)
```cpp
// 音频参数
constexpr int SAMPLE_RATE = 16000;      // 采样率
constexpr int AUDIO_BUFFER_SIZE = 512;  // 缓冲区大小
constexpr int VOLUME_THRESHOLD = 500;   // 音量阈值

// 模型参数
constexpr int FEATURE_SIZE = 40;        // 特征维度
constexpr int MODEL_OUTPUT_CLASSES = 5; // 输出类别数

// BLE参数
constexpr const char* BLE_DEVICE_NAME = "iMato-VoiceAI";
constexpr int WAKEUP_TIMEOUT = 30000;   // 唤醒超时(ms)
```

## 🔍 故障排除

### 常见问题及解决方案

#### 1. 音频识别不准确
```cpp
// 检查项:
- 麦克风增益设置
- 环境噪声水平
- 音量阈值配置
- 特征提取参数

// 调试命令:
TEST_AUDIO  // 检查音频输入电平
```

#### 2. BLE连接不稳定
```cpp
// 检查项:
- 天线连接质量
- 信号干扰源
- 发送功率设置
- 连接间隔参数

// 解决方案:
- 增加重传机制
- 优化数据包大小
- 调整天线位置
```

#### 3. 模型加载失败
```cpp
// 检查项:
- Flash存储空间
- 模型文件完整性
- 内存分配情况
- TFLite版本兼容性

// 调试命令:
MODEL_INFO  // 查看模型状态
MEMORY_INFO // 查看内存使用
```

## 🔒 安全考虑

### 数据安全
- 模型传输使用校验和验证
- 本地存储加密保护
- OTA更新完整性检查

### 系统安全
- 输入数据边界检查
- 内存访问安全防护
- 异常处理机制完善

## 📈 性能优化建议

### 1. 内存优化
- 使用静态内存分配
- 及时释放临时缓冲区
- 优化特征提取算法

### 2. 功耗优化
- 智能休眠唤醒机制
- 动态调整采样率
- 电源管理策略

### 3. 实时性优化
- 中断优先级调整
- DMA传输加速
- 任务调度优化

## 📚 参考资料

### 技术文档
- [TensorFlow Lite Micro官方文档](https://www.tensorflow.org/lite/microcontrollers)
- [ESP32技术参考手册](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/)
- [NimBLE用户指南](https://github.com/h2zero/NimBLE-Arduino)

### 相关论文
- "TinyML: Machine Learning with TensorFlow Lite on Arduino and Ultra-Low-Power Microcontrollers"
- "End-to-End Speech Recognition on Microcontrollers"
- "Efficient Keyword Spotting for Embedded Devices"

---
*本文档最后更新: 2026年2月*
*版本: v1.0.0*