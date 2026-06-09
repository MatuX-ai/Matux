# ESP32 TinyML 语音识别系统用户手册

## 🎯 产品简介

iMato ESP32 TinyML语音识别系统是一款基于边缘人工智能的智能语音控制设备，能够在本地实现离线语音指令识别，无需网络连接即可控制各种智能设备。

### 主要特点
- 🎙️ **离线语音识别**: 支持中英文语音指令，无需联网
- 🚀 **边缘AI**: 基于TensorFlow Lite Micro，实时响应
- 📱 **无线升级**: 通过BLE蓝牙进行模型热更新
- ⚡ **低功耗设计**: 优化的功耗管理，延长使用时间
- 🔧 **易于集成**: 标准化接口，便于二次开发

## 📦 产品规格

### 硬件规格
| 项目 | 规格 |
|------|------|
| 主控芯片 | ESP32-D0WDQ6 双核处理器 |
| 工作频率 | 240MHz |
| 存储容量 | 4MB Flash + 520KB SRAM |
| 音频接口 | I2S数字麦克风输入 |
| 通信接口 | BLE 4.2 低功耗蓝牙 |
| 工作电压 | 3.3V DC |
| 工作电流 | 80-150mA |
| 工作温度 | -10°C ~ 60°C |
| 尺寸 | 50mm × 30mm × 15mm |

### 功能规格
| 功能 | 性能指标 |
|------|----------|
| 语音识别准确率 | ≥85% (安静环境) |
| 响应时间 | ≤1000ms |
| 支持指令 | 开灯/关灯、自定义指令 |
| 语言支持 | 中文、英文 |
| 模型大小 | ≤200KB |
| 电池续航 | 8-12小时 (典型使用) |

## 🔧 快速开始

### 1. 硬件连接

#### 基本连接示意图
```
    ESP32开发板
   ┌─────────────┐
   │             │
MIC│  ○   ○   ○  │LED
───┤  ○   ○   ○  ├───○
   │  ○   ○   ○  │
   │    ESP32    │
   └─────────────┘
       │     │
     GND   3.3V
```

#### 引脚连接表
| 功能 | ESP32引脚 | 连接设备 |
|------|-----------|----------|
| 麦克风数据 | GPIO34 | I2S_SD |
| 麦克风时钟 | GPIO26 | I2S_SCK |
| 麦克风WS | GPIO25 | I2S_WS |
| 状态LED | GPIO2 | LED正极 |
| 灯光控制 | GPIO18 | 继电器/LED负载 |
| 配置按钮 | GPIO0 | 按钮开关 |

### 2. 系统安装

#### 固件烧录步骤
1. 下载最新固件文件 `firmware.bin`
2. 安装ESP32 USB驱动程序
3. 使用烧录工具(如esptool)烧录固件：
```bash
esptool.py --chip esp32 --port COM3 write_flash 0x1000 firmware.bin
```

#### 首次启动配置
1. 连接电源，观察LED状态指示
2. 等待系统自检完成(约10秒)
3. LED变为蓝色常亮表示系统就绪

### 3. 基本使用

#### LED状态指示
| LED颜色 | 闪烁模式 | 系统状态 |
|---------|----------|----------|
| 蓝色 | 常亮 | 系统就绪，等待指令 |
| 绿色 | 常亮 | 正在处理语音指令 |
| 黄色 | 闪烁 | 系统警告 |
| 红色 | 快闪 | 系统错误 |
| 熄灭 | - | 系统关闭 |

#### 语音指令示例
**中文指令:**
- "开灯" / "打开灯" / "亮灯"
- "关灯" / "关闭灯" / "灭灯"

**英文指令:**
- "Turn on" / "Light on" / "Open light"
- "Turn off" / "Light off" / "Close light"

#### 操作步骤
1. 确保LED为蓝色常亮状态
2. 清晰说出指令(距离设备30-50cm)
3. 等待LED变为绿色表示正在处理
4. 看到灯光变化表示执行成功

## 📱 移动端APP控制

### Android/iOS应用程序
可通过专用APP进行以下操作：

#### 基本功能
- 🔍 **设备发现**: 自动搜索附近的语音识别设备
- 📊 **状态监控**: 实时查看设备工作状态
- 🎛️ **参数调节**: 调整灵敏度、音量阈值等
- 📈 **统计数据**: 查看识别成功率、使用次数等

#### 模型更新功能
1. 连接到目标设备
2. 选择新模型文件(.tflite)
3. 点击"开始更新"
4. 等待传输完成
5. 确认激活新模型

### BLE通信协议

#### 连接建立
```javascript
// 设备发现
const serviceUUID = '4fafc201-1fb5-459e-8fcc-c5c9c331914b';
const device = await navigator.bluetooth.requestDevice({
  filters: [{ services: [serviceUUID] }]
});

// 建立连接
const server = await device.gatt.connect();
const service = await server.getPrimaryService(serviceUUID);
```

#### 模型传输流程
```javascript
// 1. 发送开始传输命令
const controlCommand = {
  "command": "START_TRANSFER",
  "model_name": "voice_model_v2.0",
  "version": "2.0.0",
  "size": modelFileSize
};
await modelCharacteristic.writeValue(JSON.stringify(controlCommand));

// 2. 分块传输模型数据
const chunkSize = 512;
for (let i = 0; i < modelData.length; i += chunkSize) {
  const chunk = modelData.slice(i, i + chunkSize);
  await modelCharacteristic.writeValue(chunk);
}

// 3. 激活新模型
const activateCommand = { "command": "ACTIVATE_MODEL" };
await modelCharacteristic.writeValue(JSON.stringify(activateCommand));
```

## ⚙️ 高级配置

### 系统参数调节

#### 通过串口命令调节
使用串口调试工具连接设备(波特率115200)：

```bash
# 查看当前配置
CONFIG_GET

# 设置音量阈值
CONFIG_SET VOLUME_THRESHOLD 600

# 设置静音超时
CONFIG_SET SILENCE_TIMEOUT 2500

# 设置置信度阈值
CONFIG_SET CONFIDENCE_THRESHOLD 0.8
```

#### 参数说明表
| 参数名 | 默认值 | 说明 | 调节建议 |
|--------|--------|------|----------|
| VOLUME_THRESHOLD | 500 | 音频触发阈值 | 400-800 |
| SILENCE_TIMEOUT | 2000 | 静音等待时间(ms) | 1500-3000 |
| CONFIDENCE_THRESHOLD | 0.7 | 识别置信度阈值 | 0.6-0.9 |
| WAKEUP_TIMEOUT | 30000 | 唤醒超时(ms) | 20000-60000 |

### 自定义指令扩展

#### 添加新指令步骤
1. **训练新模型**
```bash
# 修改训练脚本中的命令定义
commands = {
    'light_on': [...],
    'light_off': [...],
    'custom_command': ['自定义指令1', 'Custom Command 1']  # 添加新指令
}

# 重新训练模型
python scripts/tinyml_voice_training.py --samples 2000
```

2. **更新设备代码**
```cpp
// 在SystemConfig.h中添加新命令类型
enum CommandType {
    COMMAND_UNKNOWN = 0,
    COMMAND_LIGHT_ON,
    COMMAND_LIGHT_OFF,
    COMMAND_CUSTOM_1,  // 新增自定义命令
    COMMAND_CUSTOM_2
};

// 在main.cpp中添加处理逻辑
case COMMAND_CUSTOM_1:
    // 执行自定义动作
    customAction1();
    break;
```

3. **部署更新**
通过BLE将新模型推送到设备

## 🔧 故障排除

### 常见问题解决

#### 问题1: 设备无法开机
**现象**: LED完全不亮
**检查步骤**:
1. 检查电源连接是否正确
2. 测量供电电压是否为3.3V
3. 检查电源极性是否正确
4. 确认保险丝是否完好

#### 问题2: 语音识别不响应
**现象**: LED状态正常但不响应语音指令
**检查步骤**:
1. 检查麦克风连接是否牢固
2. 确认说话音量是否足够大
3. 检查周围环境噪声水平
4. 通过串口发送`TEST_AUDIO`查看音频输入

#### 问题3: 识别准确率低
**现象**: 经常误识别或无法识别正确指令
**解决方法**:
1. 调整音量阈值参数
2. 在相对安静的环境中使用
3. 说话语速放慢，发音清晰
4. 重新训练针对特定环境的模型

#### 问题4: BLE连接失败
**现象**: 手机APP无法连接到设备
**解决方法**:
1. 确认设备处于可连接状态
2. 检查手机蓝牙是否开启
3. 清除蓝牙缓存后重试
4. 确认设备未被其他设备连接

### 系统维护

#### 日常维护
- 定期清洁麦克风防尘网
- 检查各连接线缆是否松动
- 更新至最新固件版本
- 备份重要配置参数

#### 性能监控
通过串口命令监控系统状态：
```bash
# 系统健康检查
HEALTH_CHECK

# 内存使用情况
MEMORY_INFO

# 识别统计信息
STATS_GET

# 系统日志
LOG_DUMP
```

## 🔒 安全使用

### 使用注意事项
⚠️ **安全警告**
- 请勿在易燃易爆环境中使用
- 避免设备接触水或其他液体
- 不要在高温高湿环境下长时间工作
- 定期检查电气连接安全性

### 数据隐私
- 语音数据仅在本地处理，不会上传云端
- 设备不收集个人身份信息
- BLE传输采用基本的安全措施
- 建议定期更换默认设备名称

## 📞 技术支持

### 获取帮助
如遇到技术问题，请按以下顺序寻求帮助：

1. **查阅本文档** - 大部分问题可在文档中找到答案
2. **在线社区** - 访问官方论坛交流经验
3. **技术支持** - 联系技术支持团队
4. **维修服务** - 如需硬件维修请联系授权服务中心

### 联系方式
- 🌐 官方网站: www.imatoproject.com
- 📧 技术邮箱: support@imatoproject.com
- 📞 服务热线: 400-XXX-XXXX
- 💬 官方QQ群: XXXXXXXX

### 反馈建议
欢迎提出产品改进建议：
- 产品体验问卷
- GitHub Issues
- 用户需求调研

---

*感谢您选择iMato产品！*
*本手册适用于v1.0.0版本*
*最后更新日期: 2026年2月*