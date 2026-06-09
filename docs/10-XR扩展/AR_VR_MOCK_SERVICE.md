# AR/VR Mock接口服务文档

## 概述

AR/VR Mock接口服务为AR/VR模块提供完整的模拟实现，确保在硬件设备不可用或开发阶段时，主线功能开发能够正常进行。该服务支持多种模拟场景，帮助开发者测试不同的边界条件和错误处理。

## 核心特性

### 1. 多场景模拟
- **理想条件**: 高成功率，低延迟的正常操作环境
- **硬件故障**: 模拟传感器失效和数据异常
- **网络问题**: 模拟高延迟和间歇性连接
- **部分降级**: 模拟部分功能失效的情况
- **高延迟环境**: 模拟弱网环境下的性能表现

### 2. 完整的传感器模拟
- **加速度计**: 模拟三轴加速度数据，包含重力补偿
- **陀螺仪**: 模拟设备旋转和姿态变化
- **GPS**: 模拟地理位置和移动轨迹
- **摄像头**: 模拟图像数据和目标检测

### 3. 交互行为模拟
- **手势识别**: 点击、滑动、捏合、旋转等手势
- **语音控制**: 自然语言命令处理
- **物理交互**: 力的作用和物体运动模拟

### 4. 实时数据流
- WebSocket实时数据推送
- 可配置的采样频率
- 数据质量模拟

## 服务架构

```
AR/VR Mock Service
├── ARVRMockService          # 核心Mock服务
├── SensorMockGenerator      # 传感器数据生成器
├── InteractionMockHandler   # 交互处理器
├── PhysicsMockEngine        # 物理引擎模拟
└── ARVRMockOrchestrator     # 服务编排器
```

## API端点

### 会话管理
```
POST    /api/v1/mock/arvr/sessions              # 启动Mock会话
DELETE  /api/v1/mock/arvr/sessions/{session_id}  # 停止Mock会话
GET     /api/v1/mock/arvr/sessions               # 获取活跃会话列表
```

### 传感器数据
```
GET     /api/v1/mock/arvr/sessions/{session_id}/sensor-data  # 获取传感器数据
WS      /api/v1/mock/arvr/sessions/{session_id}/ws/sensor-stream  # WebSocket实时流
```

### 交互处理
```
POST    /api/v1/mock/arvr/sessions/{session_id}/interactions  # 处理交互请求
```

### 物理状态
```
GET     /api/v1/mock/arvr/sessions/{session_id}/physics-state  # 获取物理状态
```

### 系统管理
```
GET     /api/v1/mock/arvr/scenarios              # 获取场景列表
GET     /api/v1/mock/arvr/health                 # 健康检查
GET     /api/v1/mock/arvr/performance/benchmark  # 性能基准测试
POST    /api/v1/mock/arvr/maintenance/cleanup    # 清理会话
```

## 使用示例

### Python后端使用
```python
from services.ar_vr_mock_service import ARVRMockOrchestrator, MockScenario

# 创建编排器
orchestrator = ARVRMockOrchestrator(db_session)

# 启动会话
session_id = await orchestrator.start_mock_session(
    content_id=1,
    user_id=123,
    scenario=MockScenario.SUCCESSFUL_INTERACTION
)

# 获取传感器数据
sensor_data = await orchestrator.get_sensor_data_stream(
    session_id, 
    ['accelerometer', 'gyroscope']
)

# 处理交互
result = await orchestrator.handle_interaction(
    session_id,
    'gesture',
    {'type': 'tap', 'position': [1, 2, 3]}
)

# 获取物理状态
physics_state = await orchestrator.get_physics_state(session_id)
```

### JavaScript前端使用
```javascript
import { ARVRMockClient } from './ar-vr-mock-client.js';

// 创建客户端
const mockClient = new ARVRMockClient('http://localhost:8000');

// 启动会话
await mockClient.startSession(1, 123, 'ideal_conditions');

// 获取传感器数据
const sensorData = await mockClient.getSensorData(['accelerometer']);

// 处理手势
const result = await mockClient.simulateTap([1, 2, 3]);

// 连接实时数据流
mockClient.connectWebSocket(['accelerometer'], (data) => {
    console.log('实时数据:', data);
});

// 监听事件
mockClient.on('sensorDataReceived', (data) => {
    // 处理传感器数据
});
```

## 配置选项

### 场景配置
```python
MOCK_SCENARIOS = {
    'ideal_conditions': MockScenario.SUCCESSFUL_INTERACTION,     # 成功率95%
    'hardware_failure': MockScenario.SENSOR_ERROR,               # 成功率30%
    'network_issues': MockScenario.NETWORK_DELAY,                # 成功率80%
    'partial_degradation': MockScenario.PARTIAL_FAILURE,         # 成功率70%
    'high_latency_env': MockScenario.HIGH_LATENCY                # 成功率90%
}
```

### 传感器配置
```python
# 加速度计配置
{
    'noise_level': 0.1,           # 噪声水平
    'gravity_compensation': True, # 重力补偿
    'sampling_rate': 60           # 采样率(Hz)
}

# GPS配置  
{
    'base_latitude': 39.9042,     # 基准纬度
    'base_longitude': 116.4074,   # 基准经度
    'movement_radius': 0.001,     # 移动半径(度)
    'accuracy_range': (3, 10)     # 精度范围(米)
}
```

## 测试策略

### 单元测试
```bash
# 运行Mock服务单元测试
python backend/tests/test_ar_vr_mock_service.py
```

### 集成测试
```python
# 完整工作流测试
async def test_complete_workflow():
    orchestrator = ARVRMockOrchestrator(db)
    session_id = await orchestrator.start_mock_session(1, 123)
    
    # 测试数据流
    data = await orchestrator.get_sensor_data_stream(session_id, ['accelerometer'])
    assert len(data) == 1
    
    # 测试交互
    result = await orchestrator.handle_interaction(session_id, 'gesture', {'type': 'tap'})
    assert result['success']
    
    await orchestrator.stop_mock_session(session_id)
```

### 性能测试
```bash
# 性能基准测试
curl "http://localhost:8000/api/v1/mock/arvr/performance/benchmark?iterations=1000"
```

## 部署配置

### Docker配置
```dockerfile
FROM python:3.9-slim

COPY backend/ /app/
WORKDIR /app

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 环境变量
```bash
MOCK_SERVICE_ENABLED=true
MOCK_DEFAULT_SCENARIO=ideal_conditions
MOCK_SESSION_TIMEOUT_MINUTES=30
MOCK_WEBSOCKET_MAX_CONNECTIONS=100
```

## 监控和日志

### 关键指标
- 会话创建/销毁率
- 请求响应时间
- 错误率统计
- WebSocket连接数
- 数据吞吐量

### 日志级别
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('arvr_mock_service')
```

## 故障排除

### 常见问题

1. **会话超时**
   ```
   解决方案: 调整SESSION_TIMEOUT_MINUTES配置
   ```

2. **WebSocket连接失败**
   ```
   检查: 网络连接、防火墙设置、SSL证书
   ```

3. **性能瓶颈**
   ```
   优化: 减少同时活跃会话数、降低采样频率
   ```

4. **数据不一致**
   ```
   排查: 检查场景配置、验证数据生成逻辑
   ```

## 最佳实践

### 开发阶段
- 使用`ideal_conditions`场景进行功能开发
- 逐步引入其他场景测试边缘情况
- 定期运行性能基准测试

### 生产环境
- 启用详细的监控和告警
- 配置适当的会话超时时间
- 准备故障转移方案

### 团队协作
- 统一Mock场景使用规范
- 建立测试数据共享机制
- 定期评审和更新Mock逻辑

## 版本历史

### v1.0.0 (当前版本)
- 基础Mock服务实现
- 多场景支持
- 完整API端点
- WebSocket实时数据流
- 性能测试套件

### 未来规划
- 更丰富的传感器类型支持
- 高级物理仿真引擎
- 分布式部署支持
- 机器学习驱动的数据生成