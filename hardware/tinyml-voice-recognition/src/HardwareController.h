/*
 * 硬件控制器头文件
 * 声明硬件控制接口
 */

#ifndef HARDWARE_CONTROLLER_H
#define HARDWARE_CONTROLLER_H

#include <Arduino.h>
#include "SystemConfig.h"

class HardwareController {
private:
    LedState ledState;
    bool lightState;
    unsigned long lastButtonPress;
    bool buttonPressed;

public:
    HardwareController();
    
    // 初始化硬件
    bool initialize();
    
    // LED控制
    void setLedState(LedState state);
    LedState getLedState() const { return ledState; }
    
    // 灯光控制
    void controlLight(bool turnOn);
    bool getLightState() const { return lightState; }
    
    // 按钮检测
    bool isButtonPressed();
    uint32_t getButtonPressDuration();
    
    // 系统信息显示
    void displaySystemInfo();
    
    // 麦克风输入
    int getMicrophoneLevel();
    
    // 硬件自检
    void performSelfTest();
};

#endif // HARDWARE_CONTROLLER_H