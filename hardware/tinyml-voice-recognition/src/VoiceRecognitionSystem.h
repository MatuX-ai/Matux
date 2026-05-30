/*
 * 语音识别系统头文件
 * 声明语音识别核心接口
 */

#ifndef VOICE_RECOGNITION_SYSTEM_H
#define VOICE_RECOGNITION_SYSTEM_H

#include <Arduino.h>
#include "SystemConfig.h"

// 前向声明
namespace tflite {
    class MicroInterpreter;
    class Model;
}

class VoiceRecognitionSystem {
private:
    bool isInitialized;
    uint32_t recognitionCount;
    unsigned long lastRecognitionTime;
    
    // 音频和特征缓冲区
    int16_t* audioBuffer;
    float* featureBuffer;
    
    // TensorFlow Lite相关
    const tflite::Model* model;
    tflite::MicroInterpreter* interpreter;
    
    // 私有方法
    bool setupI2S();
    bool loadModel();
    void setupFeatureExtractor();
    int calculateVolume(int16_t* samples, int sampleCount);
    void extractFeatures(int16_t* samples, int sampleCount);
    VoiceCommand classifyCommand();

public:
    VoiceRecognitionSystem();
    
    // 系统初始化和清理
    bool initialize();
    void cleanup();
    
    // 音频处理主循环
    VoiceCommand processAudio();
    
    // 状态查询
    bool isReady() const { return isInitialized; }
    uint32_t getRecognitionCount() const { return recognitionCount; }
    unsigned long getLastRecognitionTime() const { return lastRecognitionTime; }
    
    // 系统诊断
    void printModelInfo();
    void runDiagnostics();
};

#endif // VOICE_RECOGNITION_SYSTEM_H