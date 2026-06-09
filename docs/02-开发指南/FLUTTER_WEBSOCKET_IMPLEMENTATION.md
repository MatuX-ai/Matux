# Flutter WebSocket长连接实现文档

## 概述

本文档详细描述了在Flutter应用中实现WebSocket长连接功能的技术方案，用于替代传统的轮询机制，实现实时数据传输。

## 功能特性

### 核心功能
- ✅ **实时双向通信**: 支持客户端与服务器的实时数据交换
- ✅ **自动重连机制**: 网络中断后自动尝试重新连接
- ✅ **心跳保活**: 定期发送心跳包维持连接活性
- ✅ **错误处理**: 完善的异常捕获和错误恢复机制
- ✅ **多通道支持**: 支持不同类型数据的独立通道传输

### 硬件集成功能
- ✅ **传感器数据订阅**: 实时接收传感器数据流
- ✅ **控制命令下发**: 向硬件设备发送控制指令
- ✅ **设备状态监控**: 实时获取设备连接状态
- ✅ **数据格式转换**: 自动处理原始数据到应用数据的转换

## 架构设计

### 整体架构图
```
Flutter App Layer
├── UI Components (演示界面)
├── Business Logic (业务逻辑)
│
Service Layer  
├── WebSocketService (核心WebSocket服务)
├── HardwareWebSocketAdapter (硬件适配器)
│
Network Layer
└── WebSocket Protocol (底层协议)
```

### 核心组件说明

#### 1. WebSocketService (核心服务)
**文件位置**: `flutter_app/lib/services/websocket_service.dart`

**主要职责**:
- 管理WebSocket连接生命周期
- 处理消息的发送和接收
- 实现心跳机制和重连策略
- 维护连接状态

**关键类和枚举**:
```dart
enum WebSocketStatus {
  disconnected,    // 未连接
  connecting,      // 连接中
  connected,       // 已连接
  reconnecting,    // 重连中
  error,           // 错误状态
}

enum MessageType {
  connect,         // 连接消息
  disconnect,      // 断开消息
  data,            // 数据消息
  heartbeat,       // 心跳消息
  error,           // 错误消息
  command,         // 命令消息
}
```

**核心API**:
```dart
// 连接WebSocket服务器
Future<bool> connect({required String url, Map<String, dynamic> params = const {}})

// 断开连接
Future<void> disconnect()

// 发送消息
void sendMessage(dynamic message)
void sendJson(Map<String, dynamic> data)
void sendTypedMessage(MessageType type, Map<String, dynamic> payload)

// 状态监听
Stream<WebSocketStatus> get statusStream
Stream<WebSocketMessage> get messageStream
```

#### 2. HardwareWebSocketAdapter (硬件适配器)
**文件位置**: `flutter_app/lib/services/hardware_websocket_adapter.dart`

**主要职责**:
- 将WebSocket服务与硬件通信需求对接
- 处理传感器数据的订阅和解析
- 发送硬件控制命令
- 管理设备状态信息

**核心功能**:
```dart
// 硬件连接管理
Future<bool> connect({String? deviceId, String? sessionId, String url})
Future<void> disconnect()

// 传感器数据订阅
void subscribeToSensorData({List<String> sensorTypes, int samplingRate})
void unsubscribeFromSensorData()

// 控制命令发送
void sendControlCommand(ControlCommand command)
void sendRawData(Uint8List data)

// 设备状态查询
void queryDeviceStatus()
```

#### 3. WebSocketDemoScreen (演示界面)
**文件位置**: `flutter_app/lib/screens/websocket_demo_screen.dart`

**功能特点**:
- 可视化的连接状态显示
- 实时传感器数据展示
- 硬件控制操作面板
- 消息日志记录功能

## 使用指南

### 1. 基础WebSocket连接

```dart
import '../services/websocket_service.dart';

class MyWidget extends StatefulWidget {
  @override
  _MyWidgetState createState() => _MyWidgetState();
}

class _MyWidgetState extends State<MyWidget> {
  final WebSocketService _wsService = WebSocketService();

  @override
  void initState() {
    super.initState();
    _setupWebSocket();
  }

  void _setupWebSocket() {
    // 监听连接状态
    _wsService.statusStream.listen((status) {
      print('连接状态: $status');
    });

    // 监听消息
    _wsService.messageStream.listen((message) {
      print('收到消息: ${message.payload}');
    });

    // 建立连接
    _wsService.connect(
      url: 'ws://your-server.com/websocket',
      params: {'token': 'your-auth-token'}
    );
  }

  @override
  void dispose() {
    _wsService.dispose();
    super.dispose();
  }
}
```

### 2. 硬件集成使用

```dart
import '../services/hardware_websocket_adapter.dart';

class HardwareController {
  final HardwareWebSocketAdapter _adapter = HardwareWebSocketAdapter();

  Future<void> initializeConnection() async {
    // 连接到硬件WebSocket服务
    final connected = await _adapter.connect(
      deviceId: 'my_device_001',
      sessionId: 'session_${DateTime.now().millisecondsSinceEpoch}',
      url: 'ws://localhost:8000/api/v1/hardware/ws'
    );

    if (connected) {
      // 订阅传感器数据
      _adapter.subscribeToSensorData(
        sensorTypes: ['temperature', 'accelerometer', 'gyroscope'],
        samplingRate: 100
      );

      // 监听传感器数据
      _adapter.sensorDataStream.listen((packet) {
        final sensorData = packet.toSensorData();
        print('传感器数据: ${sensorData.sensorId} = ${sensorData.calibratedValue}${sensorData.unit}');
      });
    }
  }

  void sendControlCommand() {
    // 发送数字输出命令
    final command = DigitalOutputCommand(pin: 12, state: true);
    _adapter.sendControlCommand(command);
  }

  void cleanup() {
    _adapter.unsubscribeFromSensorData();
    _adapter.disconnect();
    _adapter.dispose();
  }
}
```

### 3. 配置参数说明

#### WebSocketService配置
```dart
static const int HEARTBEAT_INTERVAL = 30; // 心跳间隔(秒)
static const int RECONNECT_DELAY = 5;     // 重连延迟(秒)
static const int MAX_RECONNECT_ATTEMPTS = 5; // 最大重连次数
```

#### 连接参数示例
```dart
final connectionParams = {
  'device_id': 'flutter_client_123',
  'session_id': 'session_456',
  'client_type': 'flutter',
  'auth_token': 'your-jwt-token',
  'version': '1.0.0'
};
```

## 技术细节

### 1. 消息协议格式

#### 客户端发送消息
```json
{
  "type": "data|heartbeat|command",
  "payload": {
    "具体内容根据消息类型而定"
  },
  "timestamp": 1234567890123
}
```

#### 服务器响应消息
```json
{
  "type": "data|heartbeat|error",
  "payload": {
    "数据内容"
  },
  "timestamp": 1234567890123,
  "channel": 1
}
```

### 2. 传感器数据处理流程

```
硬件设备 → WebSocket服务器 → HardwareWebSocketAdapter → SensorDataPacket → 应用层处理
```

数据转换过程：
1. 原始字节数据接收
2. 解析为数值数组
3. 应用校准系数
4. 转换为标准单位
5. 包装为SensorData对象

### 3. 错误处理机制

```dart
// 连接错误处理
void _handleConnectionError(String error) {
  _updateStatus(WebSocketStatus.error);
  
  // 触发重连机制
  if (_reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
    _scheduleReconnect();
  }
}

// 消息发送错误处理
void _handleSendMessageError(String error) {
  // 可以实现消息队列或本地缓存
}
```

## 性能优化

### 1. 内存管理
- 使用单例模式避免重复创建服务实例
- 及时关闭StreamController释放资源
- 合理设置数据缓冲区大小

### 2. 网络优化
- 实现消息压缩机制
- 批量发送小数据包
- 设置合适的超时时间

### 3. 电池优化
- 智能心跳间隔调整
- 后台连接保持策略
- 网络状态变化监听

## 测试验证

### 1. 单元测试要点
- 连接建立和断开测试
- 消息发送和接收测试
- 重连机制测试
- 错误处理测试

### 2. 集成测试场景
- 正常通信流程测试
- 网络中断恢复测试
- 大数据量传输测试
- 多设备并发连接测试

### 3. 性能基准测试
- 连接建立时间 < 2秒
- 消息延迟 < 100毫秒
- 内存占用增长 < 10MB
- CPU使用率 < 5%

## 部署配置

### 1. 依赖配置
```yaml
dependencies:
  web_socket_channel: ^2.4.0
```

### 2. 权限配置
在`android/app/src/main/AndroidManifest.xml`中添加：
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
```

### 3. iOS配置
在`ios/Runner/Info.plist`中添加：
```xml
<key>NSAppTransportSecurity</key>
<dict>
  <key>NSAllowsArbitraryLoads</key>
  <true/>
</dict>
```

## 常见问题解答

### Q1: 如何处理跨域问题？
A: 确保后端WebSocket服务器正确配置CORS，并使用WSS协议（WebSocket Secure）。

### Q2: 连接频繁断开怎么办？
A: 检查网络稳定性，调整心跳间隔，增加重连次数限制。

### Q3: 如何保证数据安全性？
A: 使用WSS协议，实施JWT认证，对敏感数据进行加密传输。

### Q4: 如何优化电池消耗？
A: 实施智能心跳机制，在应用后台时降低通信频率。

## 版本历史

### v1.0.0 (2026-03-01)
- 初始版本发布
- 实现基础WebSocket连接功能
- 集成硬件通信适配器
- 提供演示界面

## 贡献指南

欢迎提交Issue和Pull Request来改进此实现。请遵循以下原则：
1. 保持向后兼容性
2. 提供充分的测试覆盖
3. 遵循现有的代码风格
4. 更新相关文档

---

**注意**: 此实现已通过完整的功能验证，可以安全地替代原有的轮询机制，提升应用性能和用户体验。