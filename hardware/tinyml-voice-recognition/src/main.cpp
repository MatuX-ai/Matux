/*
 * ESP32 TensorFlow Lite 语音识别系统
 * 基于TinyML的离线语音指令识别
 * 支持中文/英文指令识别和BLE模型热更新
 */

#include <Arduino.h>
#include "VoiceRecognitionSystem.h"
#include "BLEModelUpdater.h"
#include "HardwareController.h"
#include "SystemConfig.h"

// 全局系统对象
VoiceRecognitionSystem* voiceSystem = nullptr;
BLEModelUpdater* bleUpdater = nullptr;
HardwareController* hardwareController = nullptr;

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== ESP32 TinyML 语音识别系统启动 ===");
  
  // 初始化硬件控制器
  hardwareController = new HardwareController();
  if (!hardwareController->initialize()) {
    Serial.println("硬件控制器初始化失败!");
    while(1) delay(1000);
  }
  
  // 显示系统信息
  hardwareController->displaySystemInfo();
  
  // 初始化语音识别系统
  voiceSystem = new VoiceRecognitionSystem();
  if (!voiceSystem->initialize()) {
    Serial.println("语音识别系统初始化失败!");
    hardwareController->setLedState(LED_ERROR);
    while(1) delay(1000);
  }
  
  // 初始化BLE模型更新器
  bleUpdater = new BLEModelUpdater(voiceSystem);
  if (!bleUpdater->initialize()) {
    Serial.println("BLE更新器初始化警告 - 继续运行");
  }
  
  // 系统就绪指示
  hardwareController->setLedState(LED_READY);
  Serial.println("系统初始化完成，等待语音指令...");
  Serial.println("支持指令: 开灯/关灯 | Turn on/Turn off");
}

void loop() {
  // 处理语音识别
  if (voiceSystem && voiceSystem->isReady()) {
    VoiceCommand command = voiceSystem->processAudio();
    
    if (command.isValid) {
      Serial.printf("识别到指令: %s (置信度: %.2f%%)\n", 
                   command.text.c_str(), command.confidence * 100);
      
      // 执行对应的动作
      switch(command.type) {
        case COMMAND_LIGHT_ON:
          hardwareController->controlLight(true);
          hardwareController->setLedState(LED_ACTIVE);
          break;
          
        case COMMAND_LIGHT_OFF:
          hardwareController->controlLight(false);
          hardwareController->setLedState(LED_READY);
          break;
          
        case COMMAND_UNKNOWN:
        default:
          Serial.println("未识别的指令");
          hardwareController->setLedState(LED_WARNING);
          delay(500);
          hardwareController->setLedState(LED_READY);
          break;
      }
    }
  }
  
  // 处理BLE通信
  if (bleUpdater) {
    bleUpdater->handleClientConnections();
  }
  
  // 系统状态监控
  static unsigned long lastStatusCheck = 0;
  if (millis() - lastStatusCheck > 30000) { // 每30秒报告一次状态
    reportSystemStatus();
    lastStatusCheck = millis();
  }
  
  delay(10); // 短暂延迟以节省功耗
}

void reportSystemStatus() {
  Serial.println("\n--- 系统状态报告 ---");
  Serial.printf("运行时间: %lu 秒\n", millis() / 1000);
  Serial.printf("内存可用: %d bytes\n", ESP.getFreeHeap());
  Serial.printf("识别次数: %d\n", voiceSystem ? voiceSystem->getRecognitionCount() : 0);
  Serial.printf("BLE连接状态: %s\n", bleUpdater ? (bleUpdater->isConnected() ? "已连接" : "未连接") : "不可用");
  Serial.println("------------------\n");
}