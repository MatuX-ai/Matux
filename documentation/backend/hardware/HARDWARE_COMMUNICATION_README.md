# 📡 硬件通信原型说明文档

## 🎯 项目概述

本项目实现了基于浏览器原生WebUSB的硬件通信功能，作为iMatuProject硬件交互系统的原型。后续将扩展支持BLE（蓝牙低功耗）通信。

## 🏗️ 技术架构

### 核心组件

1. **HardwareCommunicationService** (`hardware_communication_service.dart`)
   - 单例模式的硬件通信核心服务
   - 封装WebUSB API调用
   - 提供连接管理、数据收发等基础功能

2. **HardwareDebugPanel** (`hardware_debug_panel.dart`)
   - 可视化调试界面组件
   - 实时显示连接状态和通信日志
   - 支持预设命令和自定义命令发送

3. **HardwareDemoScreen** (`hardware_demo_screen.dart`)
   - 完整的演示界面
   - 包含使用说明和操作指南
   - 集成调试面板功能

4. **UsbDeviceUtils** (`usb_device_utils.dart`)
   - USB设备信息管理工具
   - 常见设备ID数据库
   - 数据格式转换和校验功能

## 🔧 功能特性

### ✅ 已实现功能

- **WebUSB原生支持**: 利用现代浏览器的WebUSB API
- **设备连接管理**: 支持指定Vendor ID和Product ID的设备连接
- **双向数据通信**: 支持数据发送和接收
- **多种数据格式**: 支持十六进制、十进制、ASCII格式
- **实时调试界面**: 图形化操作界面和日志显示
- **预设命令系统**: 快速发送常用硬件命令
- **连接状态监控**: 实时显示设备连接状态

### 🔮 待扩展功能

- **BLE蓝牙支持**: 扩展到蓝牙低功耗通信
- **协议栈完善**: 实现完整的通信协议
- **自动重连机制**: 断线自动重连功能
- **批量数据传输**: 支持大数据量传输
- **安全认证**: 设备身份验证机制

## 🚀 快速开始

### 1. 环境要求

- Flutter 3.0+
- 支持WebUSB的现代浏览器（Chrome 61+, Edge 79+）
- USB硬件设备（如Arduino、ESP32等）

### 2. 安装依赖

```yaml
dependencies:
  provider: ^6.1.1
  http: ^0.13.6
```

### 3. 运行应用

```bash
cd flutter_app
flutter pub get
flutter run -d chrome
```

### 4. 硬件准备

使用提供的Arduino测试固件：
1. 将 `arduino_test_sketch.ino` 上传到Arduino设备
2. 通过USB连接设备到电脑
3. 在Flutter应用中连接并测试通信

## 💡 使用示例

### 基础使用

```dart
final hwService = HardwareCommunicationService();

// 连接设备
await hwService.connectToDevice(
  vendorId: 0x2341,  // Arduino Vendor ID
  productId: 0x0043, // Arduino Product ID
);

// 发送命令
await hwService.sendCommand([0x01, 0x02, 0x03]);

// 读取数据
final data = await hwService.readData();
```

### 预设命令

1. **初始化命令**: `[0x01, 0x02, 0x03]`
2. **状态查询**: `[0x10, 0x00]`
3. **LED控制**: `[0x20, 0x01, 0xFF]`

## 📊 支持的设备

### 常见USB设备ID

| 设备类型 | Vendor ID | Product ID | 描述 |
|---------|-----------|------------|------|
| Arduino Uno | 0x2341 | 0x0043 | 标准Arduino Uno |
| Arduino Nano | 0x2341 | 0x0043 | Arduino Nano |
| Arduino Mega | 0x2341 | 0x0042 | Arduino Mega 2560 |
| ESP32 DevKit | 0x10C4 | 0xEA60 | ESP32开发板 |
| FTDI Basic | 0x0403 | 0x6001 | USB转串口适配器 |

## 🔒 安全注意事项

1. **权限管理**: WebUSB需要用户明确授权才能访问设备
2. **HTTPS要求**: 生产环境中需要HTTPS才能使用WebUSB
3. **设备过滤**: 建议使用具体的Vendor ID和Product ID过滤设备
4. **数据验证**: 对接收的数据进行格式和范围验证

## 🐛 故障排除

### 常见问题

1. **浏览器不支持WebUSB**
   - 确保使用Chrome 61+或Edge 79+
   - 检查是否在HTTPS环境下运行

2. **找不到设备**
   - 确认设备已正确连接
   - 检查Vendor ID和Product ID是否匹配
   - 查看浏览器控制台是否有错误信息

3. **连接失败**
   - 确保没有其他程序占用该USB设备
   - 检查设备驱动是否正常安装
   - 尝试重新插拔USB设备

## 📈 性能优化建议

1. **连接复用**: 避免频繁建立和断开连接
2. **批量传输**: 合并小数据包减少传输次数
3. **异步处理**: 使用Future避免阻塞UI线程
4. **内存管理**: 及时释放不需要的数据缓冲区

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进这个硬件通信原型！

### 开发规范

- 遵循Dart编码规范
- 添加适当的注释和文档
- 编写单元测试覆盖核心功能
- 保持向后兼容性

---

*本项目是iMatuProject的一部分，旨在提供跨平台的硬件交互解决方案。*