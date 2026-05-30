/*
 * 系统配置定义文件
 * 包含硬件引脚定义、系统参数和枚举类型
 */

#ifndef SYSTEM_CONFIG_H
#define SYSTEM_CONFIG_H

#include <Arduino.h>
#include <string>

// 硬件引脚定义
#define PIN_LED_STATUS      2      // 状态指示LED
#define PIN_LED_BUILTIN     2      // ESP32内置LED
#define PIN_MICROPHONE      34     // 麦克风输入引脚
#define PIN_LIGHT_CONTROL   18     // 灯光控制输出引脚
#define PIN_BUTTON_CONFIG   0      // 配置按钮(BOOT键)

// LED状态定义
enum LedState {
    LED_OFF = 0,
    LED_READY,      // 系统就绪
    LED_ACTIVE,     // 正在处理
    LED_WARNING,    // 警告状态
    LED_ERROR       // 错误状态
};

// 语音命令类型
enum CommandType {
    COMMAND_UNKNOWN = 0,
    COMMAND_LIGHT_ON,   // 开灯
    COMMAND_LIGHT_OFF,  // 关灯
    COMMAND_CUSTOM_1,   // 自定义命令1
    COMMAND_CUSTOM_2    // 自定义命令2
};

// 语音命令结构体
struct VoiceCommand {
    bool isValid = false;
    CommandType type = COMMAND_UNKNOWN;
    std::string text = "";
    float confidence = 0.0f;
    uint32_t timestamp = 0;
};

// 系统配置参数
namespace SystemConfig {
    // 音频采样参数
    constexpr int SAMPLE_RATE = 16000;      // 采样率 16kHz
    constexpr int AUDIO_BUFFER_SIZE = 512;  // 音频缓冲区大小
    constexpr int FFT_SIZE = 256;           // FFT大小
    
    // 语音检测参数
    constexpr int VOLUME_THRESHOLD = 500;   // 音量阈值
    constexpr int SILENCE_TIMEOUT = 2000;   // 静音超时(ms)
    constexpr int MIN_COMMAND_DURATION = 500; // 最小命令持续时间(ms)
    
    // 模型参数
    constexpr int FEATURE_SIZE = 40;        // 特征向量大小
    constexpr int MODEL_OUTPUT_CLASSES = 5; // 模型输出类别数
    
    // BLE参数
    constexpr const char* BLE_DEVICE_NAME = "iMato-VoiceAI";
    constexpr const char* BLE_SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b";
    constexpr const char* BLE_MODEL_CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8";
    constexpr const char* BLE_STATUS_CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a9";
    
    // 系统参数
    constexpr int MAX_RECOGNITION_HISTORY = 10;  // 最大识别历史记录数
    constexpr int WAKEUP_TIMEOUT = 30000;        // 唤醒超时(ms)
    constexpr int RECOGNITION_COOLDOWN = 1000;   // 识别冷却时间(ms)
}

// 模型文件路径
namespace ModelPaths {
    constexpr const char* DEFAULT_MODEL = "/model.tflite";
    constexpr const char* TEMP_MODEL = "/temp_model.tflite";
    constexpr const char* BACKUP_MODEL = "/backup_model.tflite";
    constexpr const char* MODEL_METADATA = "/model_meta.json";
    constexpr const char* MODEL_CHECKSUM = "/model_checksum.sha256";
    constexpr const char* MODEL_PATCH = "/model_patch.diff";
}

// 预定义命令词典
namespace CommandDictionary {
    // 中文命令
    constexpr const char* CHINESE_LIGHT_ON[] = {"开灯", "打开灯", "亮灯"};
    constexpr const char* CHINESE_LIGHT_OFF[] = {"关灯", "关闭灯", "灭灯"};
    
    // 英文命令
    constexpr const char* ENGLISH_LIGHT_ON[] = {"turn on", "light on", "open light"};
    constexpr const char* ENGLISH_LIGHT_OFF[] = {"turn off", "light off", "close light"};
    
    // 命令数量
    constexpr int CHINESE_LIGHT_ON_COUNT = sizeof(CHINESE_LIGHT_ON) / sizeof(const char*);
    constexpr int CHINESE_LIGHT_OFF_COUNT = sizeof(CHINESE_LIGHT_OFF) / sizeof(const char*);
    constexpr int ENGLISH_LIGHT_ON_COUNT = sizeof(ENGLISH_LIGHT_ON) / sizeof(const char*);
    constexpr int ENGLISH_LIGHT_OFF_COUNT = sizeof(ENGLISH_LIGHT_OFF) / sizeof(const char*);
}

#endif // SYSTEM_CONFIG_H