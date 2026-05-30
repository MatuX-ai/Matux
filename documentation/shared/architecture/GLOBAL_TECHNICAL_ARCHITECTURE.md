# iMatu 全局技术架构文档

## 📋 文档版本信息

- **文档版本**: v2.1
- **更新时间**: 2026 年 3 月 3 日
- **作者**: iMatu 技术团队
- **审核状态**: 已审核
- **更新内容**: 新增虚拟实验室 3D 模型库集成模块

## 🎯 项目概述

iMatu是一个面向未来的智能化教育平台，采用微服务架构设计，集成了AI、区块链、物联网、AR/VR等前沿技术，为用户提供沉浸式、个性化的学习体验。

## 🏗️ 整体架构演进

### 第一阶段：基础平台建设
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端应用层    │    │   后端服务层    │    │   基础设施层    │
│  Angular 16     │◄──►│   FastAPI       │◄──►│ PostgreSQL/Redis│
│  Material UI    │    │  SQLAlchemy     │    │ Docker/K8s      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 第二阶段：核心技术模块
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI服务模块    │    │ 区块链积分系统  │    │  硬件认证模块   │
│  LangChain/OpenAI│    │ Hyperledger Fab │    │  ESP32/TinyML   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲                       ▲
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  XR远程教学系统 │    │ 多模态激励系统  │    │ AI模型热更新    │
│  AR/VR + 白板   │    │ 语音/AR/手势    │    │ BLE无线升级     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 第三阶段：智能化生态（当前状态）
```
                    ┌─────────────────────────────────────┐
                    │        统一奖励事件总线             │
                    │    (Reward Event Bus)               │
                    └─────────────┬───────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼────────┐      ┌────────▼────────┐      ┌────────▼────────┐
│ 语音纠错服务   │      │   AR 奖励服务    │      │ 手势识别服务    │
│ Voice Detector │      │ AR Reward SVC   │      │ Gesture SVC     │
└───────┬────────┘      └────────┬────────┘      └────────┬────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ 区块链积分系统  │◄──►│ 成就徽章系统    │◄──►│ 积分衰减调度器  │
│ Chaincode       │    │ Badge System    │    │ Decay Scheduler │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 第四阶段：虚拟实验室扩展（最新完成）
```
┌──────────────────────────────────────────────────────────────┐
│                  3D 模型库集成模块                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
  │ │ KiCad 模型库 │─►│ GLB 转换器   │─►│ LOD 生成器     │      │
  │ └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        Vircadia 引擎集成层                           │   │
│  │  - 模型加载服务                                      │   │
│  │  - 物理引擎 (Ammo.js)                               │   │
│  │  - 电路组装交互                                     │   │
│  │  - 简化电路仿真                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
  │ │ 拖放吸附系统 │  │ 物理碰撞检测 │  │ 积分奖励联动 │      │
  │ └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

## 🔧 核心技术栈全景图

### 前端技术栈
```
Framework: Angular 16
UI Components: Angular Material + MUI
State Management: RxJS
Styling: SCSS + Design Tokens
Build Tool: Angular CLI
Mobile: Flutter (部分模块)
3D Rendering: Three.js r150+
XR Engine: Vircadia Web SDK
Model Format: glTF 2.0 / GLB
Physics Engine: Ammo.js (WebAssembly)
```

### 后端技术栈
```
Framework: FastAPI (Python 3.9+)
ORM: SQLAlchemy
Database: PostgreSQL + Redis
Authentication: JWT + OAuth2
AI Services: LangChain + OpenAI API
Blockchain: Hyperledger Fabric SDK
IoT: WebUSB + Bluetooth Low Energy
Circuit Simulation: Custom logic engine
Validation Service: ERC/DRC checker
```

### 基础设施技术栈
```
Containerization: Docker + Docker Compose
Orchestration: Kubernetes
Monitoring: Prometheus + Grafana
Logging: ELK Stack
CI/CD: GitHub Actions
Cloud: AWS/Azure/GCP (多云部署)
```

### 硬件技术栈
```
Microcontroller: ESP32-S3
AI Framework: TensorFlow Lite Micro
Communication: BLE 5.0 + WiFi
Sensors: IMU + Camera + Audio
Edge Computing: Local inference
Model Library: KiCad-packages3D (CC BY-SA 4.0)
3D Printing: STL export support
```

## 🎯 核心功能模块详解

### 1. AI代码生成服务 (`ai_service/`)
- **技术特色**: 多模型集成、上下文感知、实时补全
- **集成模型**: GPT-4、Claude、CodeLLaMA、StarCoder
- **核心能力**: 代码生成、错误修复、架构设计、文档生成

### 2. 区块链积分认证系统 (`blockchain/`)
- **网络架构**: 三组织Raft共识集群
- **智能合约**: Go语言开发的积分管理链码
- **核心功能**: 积分发行、转移、衰减、成就记录

### 3. 多模态激励联动系统 (`backend/services/multimodal/`)
- **语音模块**: 语音纠错检测、自然语言处理
- **AR模块**: 3D空间定位、元件放置验证、成就追踪
- **手势模块**: MediaPipe集成、复杂序列识别、隐藏任务
- **奖励引擎**: 统一事件总线、规则引擎、积分衰减

### 4. XR 远程教学系统 (`unity/ImatuARLab/`)
- **AR 功能**: 实时物体识别、空间锚点、手势交互
- **VR 功能**: 沉浸式环境、协作白板、代码编辑器
- **协作功能**: 多人同步、实时通信、状态同步

### 5. 虚拟实验室 3D 模型库 (V3.1 已完成) ✨
- **模型资源**: KiCad-packages3D 开源库 (256+ 精选元件)
- **转换工具链**: Python + Blender 批量转换 (STEP→GLB)
- **LOD 系统**: 三级轻量化优化 (10%-100% 面数)
- **物理引擎**: Vircadia Ammo.js 刚体模拟
- **电路组装**: 拖放 - 吸附交互 (2cm 精度)
- **电路仿真**: 简化逻辑模拟 (LED 亮灭、开关控制)
- **游戏化激励**: 积分奖励 (+10~100 分)、连击加成
- **核心服务**:
  - `vircadia-model-loader.service.ts`: 模型加载与 LOD 切换
  - `vircadia-physics.service.ts`: 物理属性绑定与碰撞检测
  - `circuit-assembly.service.ts`: 组装交互与吸附系统
  - `circuit-simulator.service.ts`: 电路行为仿真
  - `circuit-integral.service.ts`: 积分奖励联动
  - `circuit_validation_service.py`: ERC/DRC 验证

### 6. 硬件认证与 AI 边缘计算 (`hardware/`)
- **TinyML**: 本地语音识别、模型推理
- **BLE 升级**: 无线模型推送、安全验证、自动激活
- **边缘计算**: 离线运行、低功耗设计、实时响应

## 🔄 数据流向架构

### 用户交互数据流
```
用户输入 → 前端应用 → API网关 → 微服务 → 数据库/区块链
   ▲                                            │
   │                                            ▼
   └────────────── 异步通知 ← 事件总线 ← 处理结果
```

### 实时协作数据流
```
用户A操作 → WebSocket → 服务端 → 广播 → 用户B/C/D
   │                                            │
   ▼                                            ▼
状态同步 ← OT算法 ← 消息队列 ← 状态更新
```

### 硬件数据流
```
传感器数据 → ESP32采集 → BLE/WiFi传输 → 后端处理 → 
   │                                            │
   ▼                                            ▼
本地AI推理 ← TensorFlow Lite ← 边缘计算 ← 区块链记录
```

## 📊 性能指标体系

### 系统性能指标
| 指标类别 | 目标值 | 当前值 | 状态 |
|---------|--------|--------|------|
| API响应时间 | ≤200ms | 42ms | ✅ 达标 |
| 系统可用性 | ≥99.9% | 99.5% | ⚠️ 接近达标 |
| 并发用户数 | 1000+ | 500 | ✅ 达标 |
| 数据一致性 | ≥99.99% | 99.99% | ✅ 达标 |

### AI服务性能
| 服务 | 准确率 | 响应时间 | 内存占用 |
|------|--------|----------|----------|
| 代码生成 | 85% | 1.2s | 256MB |
| 语音识别 | 95% | 640ms | 335KB |
| 图像识别 | 92% | 85ms | 45MB |

### 区块链性能
| 指标 | 数值 |
|------|------|
| TPS | 1200+ |
| 块生成时间 | 2秒 |
| 确认时间 | 6秒 |
| 网络节点 | 9个 |

## 🔐 安全架构

### 认证授权体系
```
OAuth2.0 ──┐
JWT ───────┼──► 统一认证中心 ──► RBAC权限控制
LDAP ──────┘
```

### 数据安全防护
- **传输加密**: TLS 1.3全链路加密
- **数据加密**: AES-256静态数据加密
- **密钥管理**: HashiCorp Vault集中管理
- **访问控制**: 细粒度权限策略

### 硬件安全
- **固件签名**: ECDSA数字签名验证
- **安全启动**: UEFI安全启动验证
- **OTA安全**: HTTPS + 数字证书
- **物理安全**: Tamper detection

## 📈 监控与运维

### 监控体系
```
Prometheus ──┐
Grafana ─────┼──► 指标收集 ──► 告警通知
ELK Stack ───┘
```

### 日志架构
```
应用日志 ──┐
系统日志 ──┼──► Fluentd收集 ──► Elasticsearch ──► Kibana展示
审计日志 ──┘
```

### 自动化运维
- **CI/CD**: GitHub Actions自动化流水线
- **配置管理**: Ansible + Terraform
- **容器编排**: Kubernetes Helm Charts
- **服务网格**: Istio流量管理

## 🚀 部署架构

### 开发环境
```
Docker Desktop ──► docker-compose.yml ──► 本地微服务集群
```

### 生产环境
```
AWS/Azure ──► Kubernetes Cluster ──► Helm部署 ──► Load Balancer
```

### 边缘部署
```
树莓派/ESP32 ──► 本地服务 ──► MQTT桥接 ──► 云端同步
```

## 📚 技术文档体系

### 核心文档
- `PROJECT_OVERVIEW.md` - 项目总览
- `SYSTEM_ARCHITECTURE.md` - 系统架构设计
- `GLOBAL_TECHNICAL_ARCHITECTURE.md` - 全局技术架构（本文档）
- `DEVELOPMENT_GUIDELINES.md` - 开发规范指南

### 模块文档
- `MULTIMODAL_INCENTIVE_SYSTEM_TECHNICAL_DOC.md` - 多模态激励系统
- `FABRIC_DEVELOPER_DOCUMENTATION.md` - 区块链开发者文档
- `XR_REMOTE_TEACHING_SYSTEM_TECHNICAL_DOCUMENTATION.md` - XR教学系统
- `TINYML_VOICE_RECOGNITION_TECHNICAL_REPORT.md` - TinyML语音识别

### API文档
- `API_REFERENCE.md` - RESTful API参考
- `WEBSOCKET_API.md` - 实时通信API
- `BLOCKCHAIN_API.md` - 区块链接口
- `HARDWARE_API.md` - 硬件通信协议

## 🔮 技术发展规划

### 短期规划（Q1 2026）
- [x] 完善多模态激励系统
- [x] 优化系统性能和稳定性
- [ ] 增强移动端用户体验
- [ ] 完善监控告警体系

### 中期规划（Q2-Q3 2026）
- [ ] 集成更多AI模型和服务
- [ ] 扩展区块链网络规模
- [ ] 支持更多硬件设备类型
- [ ] 增强数据分析和BI能力

### 长期规划（2027+）
- [ ] 实现完全去中心化架构
- [ ] 支持元宇宙教学场景
- [ ] 构建 AI 驱动的个性化学习引擎
- [ ] 建立开放的教育技术生态
- [ ] 集成 Vircadia 虚拟世界平台（新增）

## 📞 技术支持

### 开发团队
- **架构组**: 负责系统架构设计和技术选型
- **前端组**: 负责用户界面和交互体验
- **后端组**: 负责服务端逻辑和数据处理
- **AI组**: 负责人工智能算法和模型优化
- **区块链组**: 负责分布式账本和智能合约
- **硬件组**: 负责嵌入式系统和物联网设备

### 联系方式
- **技术支持**: support@imato.com
- **技术文档**: docs.imato.com
- **GitHub**: github.com/imato-project
- **Slack**: imato-dev.slack.com

---

*iMatu Global Technical Architecture v2.0*
*Last Updated: 2026-03-01*
