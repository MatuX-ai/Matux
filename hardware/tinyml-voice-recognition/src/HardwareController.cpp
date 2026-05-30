/*
 * 硬件控制器模块
 * 管理LED指示、灯光控制和其他硬件外设
 */

#include "HardwareController.h"
#include "SystemConfig.h"

HardwareController::HardwareController() 
    : ledState(LED_OFF)
    , lightState(false)
    , lastButtonPress(0)
    , buttonPressed(false) {
}

bool HardwareController::initialize() {
    Serial.println("初始化硬件控制器...");
    
    // 初始化LED引脚
    pinMode(PIN_LED_STATUS, OUTPUT);
    pinMode(PIN_LED_BUILTIN, OUTPUT);
    
    // 初始化灯光控制引脚
    pinMode(PIN_LIGHT_CONTROL, OUTPUT);
    
    // 初始化按钮引脚（输入上拉）
    pinMode(PIN_BUTTON_CONFIG, INPUT_PULLUP);
    
    // 设置初始状态
    digitalWrite(PIN_LED_STATUS, LOW);
    digitalWrite(PIN_LED_BUILTIN, LOW);
    digitalWrite(PIN_LIGHT_CONTROL, LOW);
    
    Serial.println("硬件控制器初始化完成");
    return true;
}

void HardwareController::setLedState(LedState state) {
    ledState = state;
    
    switch(state) {
        case LED_OFF:
            digitalWrite(PIN_LED_STATUS, LOW);
            digitalWrite(PIN_LED_BUILTIN, LOW);
            break;
            
        case LED_READY:
            // 蓝色呼吸效果表示就绪
            ledcSetup(0, 1000, 8);
            ledcAttachPin(PIN_LED_STATUS, 0);
            ledcWrite(0, 128);
            digitalWrite(PIN_LED_BUILTIN, HIGH);
            break;
            
        case LED_ACTIVE:
            // 绿色常亮表示活动
            digitalWrite(PIN_LED_STATUS, HIGH);
            digitalWrite(PIN_LED_BUILTIN, HIGH);
            break;
            
        case LED_WARNING:
            // 黄色闪烁表示警告
            digitalWrite(PIN_LED_STATUS, millis() % 1000 < 500 ? HIGH : LOW);
            digitalWrite(PIN_LED_BUILTIN, millis() % 1000 < 500 ? HIGH : LOW);
            break;
            
        case LED_ERROR:
            // 红色快速闪烁表示错误
            digitalWrite(PIN_LED_STATUS, millis() % 200 < 100 ? HIGH : LOW);
            digitalWrite(PIN_LED_BUILTIN, millis() % 200 < 100 ? HIGH : LOW);
            break;
    }
}

void HardwareController::controlLight(bool turnOn) {
    lightState = turnOn;
    digitalWrite(PIN_LIGHT_CONTROL, turnOn ? HIGH : LOW);
    
    Serial.printf("灯光控制: %s\n", turnOn ? "开启" : "关闭");
}

bool HardwareController::isButtonPressed() {
    // 检测按钮按下（低电平有效）
    bool currentState = digitalRead(PIN_BUTTON_CONFIG) == LOW;
    
    if (currentState && !buttonPressed) {
        // 按钮刚被按下
        buttonPressed = true;
        lastButtonPress = millis();
        return true;
    } else if (!currentState && buttonPressed) {
        // 按钮释放
        buttonPressed = false;
    }
    
    return false;
}

uint32_t HardwareController::getButtonPressDuration() {
    if (buttonPressed) {
        return millis() - lastButtonPress;
    }
    return 0;
}

void HardwareController::displaySystemInfo() {
    Serial.println("\n=== 系统硬件信息 ===");
    Serial.printf("芯片型号: %s\n", ESP.getChipModel());
    Serial.printf("芯片版本: %d\n", ESP.getChipRevision());
    Serial.printf("CPU频率: %d MHz\n", ESP.getCpuFreqMHz());
    Serial.printf("Flash大小: %d MB\n", ESP.getFlashChipSize() / (1024 * 1024));
    Serial.printf("PSRAM大小: %d KB\n", ESP.getPsramSize() / 1024);
    Serial.printf("空闲堆空间: %d bytes\n", ESP.getFreeHeap());
    Serial.printf("最小空闲堆: %d bytes\n", ESP.getMinFreeHeap());
    Serial.println("==================\n");
}

int HardwareController::getMicrophoneLevel() {
    // 读取麦克风模拟输入
    int micValue = analogRead(PIN_MICROPHONE);
    return micValue;
}

void HardwareController::performSelfTest() {
    Serial.println("执行硬件自检...");
    
    // LED测试
    Serial.println("测试LED...");
    setLedState(LED_ACTIVE);
    delay(500);
    setLedState(LED_READY);
    delay(500);
    setLedState(LED_WARNING);
    delay(500);
    setLedState(LED_ERROR);
    delay(500);
    setLedState(LED_OFF);
    
    // 灯光控制测试
    Serial.println("测试灯光控制...");
    controlLight(true);
    delay(1000);
    controlLight(false);
    
    // 按钮测试
    Serial.println("测试按钮功能...");
    unsigned long startTime = millis();
    while (millis() - startTime < 5000) {
        if (isButtonPressed()) {
            Serial.println("检测到按钮按下");
            setLedState(LED_ACTIVE);
            delay(200);
            setLedState(LED_READY);
        }
        delay(50);
    }
    
    // 麦克风测试
    Serial.println("测试麦克风输入...");
    for (int i = 0; i < 10; i++) {
        int micLevel = getMicrophoneLevel();
        Serial.printf("麦克风电平: %d\n", micLevel);
        delay(100);
    }
    
    Serial.println("硬件自检完成");
}