/*
 * iMatuProject 硬件通信测试固件
 * 用于测试WebUSB通信功能
 */

// 定义命令类型
#define CMD_INIT        0x01
#define CMD_STATUS      0x10
#define CMD_LED_CONTROL 0x20

// LED引脚定义
const int ledPin = 13;  // 内置LED
const int ledBrightnessPin = 9; // PWM LED控制引脚

// 通信缓冲区
byte commandBuffer[64];
int bufferIndex = 0;

void setup() {
  // 初始化串口通信
  Serial.begin(9600);
  while (!Serial) {
    ; // 等待串口连接
  }
  
  // 初始化LED引脚
  pinMode(ledPin, OUTPUT);
  pinMode(ledBrightnessPin, OUTPUT);
  
  // 初始状态
  digitalWrite(ledPin, LOW);
  analogWrite(ledBrightnessPin, 0);
  
  Serial.println("iMatuProject硬件通信测试固件已启动");
  Serial.println("支持命令:");
  Serial.println("- 0x01 0x02 0x03 : 初始化");
  Serial.println("- 0x10 0x00 : 查询状态");
  Serial.println("- 0x20 0x01 0xFF : LED控制(开启,亮度255)");
  Serial.println("=========================");
}

void loop() {
  // 检查串口数据
  if (Serial.available() > 0) {
    byte receivedByte = Serial.read();
    commandBuffer[bufferIndex++] = receivedByte;
    
    // 处理完整命令
    if (bufferIndex >= 2) { // 至少需要命令码和参数
      processCommand();
      bufferIndex = 0; // 重置缓冲区
    }
  }
  
  // 心跳LED闪烁
  heartbeatBlink();
  
  delay(10); // 短暂延迟
}

void processCommand() {
  byte command = commandBuffer[0];
  byte param1 = (bufferIndex > 1) ? commandBuffer[1] : 0;
  byte param2 = (bufferIndex > 2) ? commandBuffer[2] : 0;
  
  Serial.print("收到命令: ");
  Serial.print(command, HEX);
  Serial.print(" 参数: ");
  Serial.print(param1, HEX);
  Serial.print(" ");
  Serial.println(param2, HEX);
  
  switch (command) {
    case CMD_INIT:
      handleInitCommand();
      break;
      
    case CMD_STATUS:
      handleStatusCommand();
      break;
      
    case CMD_LED_CONTROL:
      handleLedControlCommand(param1, param2);
      break;
      
    default:
      Serial.println("未知命令");
      sendResponse(0xFF, "Unknown command");
      break;
  }
}

void handleInitCommand() {
  Serial.println("执行初始化命令");
  digitalWrite(ledPin, HIGH);
  delay(500);
  digitalWrite(ledPin, LOW);
  
  sendResponse(0x01, "Initialization complete");
}

void handleStatusCommand() {
  Serial.println("查询设备状态");
  
  // 构建状态响应
  byte statusResponse[] = {
    0x10,           // 状态命令回应
    0x01,           // 版本号
    digitalRead(ledPin),  // LED状态
    0x00            // 保留字段
  };
  
  Serial.write(statusResponse, sizeof(statusResponse));
  Serial.println("状态已发送");
}

void handleLedControlCommand(byte action, byte brightness) {
  Serial.print("LED控制 - 动作: ");
  Serial.print(action);
  Serial.print(", 亮度: ");
  Serial.println(brightness);
  
  if (action == 0x01) { // 开启LED
    analogWrite(ledBrightnessPin, brightness);
    digitalWrite(ledPin, HIGH);
    Serial.println("LED已开启");
    sendResponse(0x20, "LED ON");
  } else if (action == 0x00) { // 关闭LED
    analogWrite(ledBrightnessPin, 0);
    digitalWrite(ledPin, LOW);
    Serial.println("LED已关闭");
    sendResponse(0x20, "LED OFF");
  } else {
    Serial.println("无效的LED控制动作");
    sendResponse(0xFE, "Invalid LED action");
  }
}

void sendResponse(byte responseType, const char* message) {
  Serial.print("响应类型: ");
  Serial.print(responseType, HEX);
  Serial.print(" - ");
  Serial.println(message);
}

void heartbeatBlink() {
  static unsigned long lastBlink = 0;
  static bool blinkState = false;
  
  if (millis() - lastBlink > 2000) { // 每2秒心跳一次
    blinkState = !blinkState;
    digitalWrite(ledPin, blinkState ? HIGH : LOW);
    lastBlink = millis();
  }
}