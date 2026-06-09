# MatuX STEM 学习平台 - 项目需求文档

> **版本**: v5.0  
> **最后更新**: 2026-05-31  
> **状态**: 持续迭代开发中

---

## 目录

1. [项目概述](#1-项目概述)
2. [核心价值主张](#2-核心价值主张)
3. [目标用户群体](#3-目标用户群体)
4. [技术架构](#4-技术架构)
5. [功能需求矩阵](#5-功能需求矩阵)
6. [已解耦模块](#6-已解耦模块)
7. [后端服务模块](#7-后端服务模块)
8. [前端应用模块](#8-前端应用模块)
9. [Flutter 移动端模块](#9-flutter-移动端模块)
10. [区块链模块](#10-区块链模块)
11. [硬件与边缘计算模块](#11-硬件与边缘计算模块)
12. [AI 与机器学习模块](#12-ai-与机器学习模块)
13. [开发优先级与路线图](#13-开发优先级与路线图)
14. [基础设施与部署](#14-基础设施与部署)
15. [代码质量与测试](#15-代码质量与测试)
16. [文档体系](#16-文档体系)
17. [附录](#17-附录)

---

## 1. 项目概述

### 1.1 项目名称
**MatuX** — 面向学生的 STEM 学习平台

### 1.2 项目定位
MatuX 是面向学生的 STEM 学习平台，融合边缘计算、区块链、AR/VR、3D 虚拟实验室、多模态激励联动等前沿技术，为学生提供 AI 编程教育、虚拟实验和个性化学习体验。

> **角色范围**: MatuX 仅有 **学生** 一个角色。课件管理已解耦至独立项目 `OpenMTSciEd`，机构管理已解耦至独立项目 `OpenMTEduInst`。

### 1.3 开源协议
GPL-3.0

### 1.4 当前完成度
- 核心功能模块：18 个（MatuX 自有）
- 已解耦模块：4 个（迁移至 OpenMTSciEd / OpenMTEduInst）
- 测试覆盖率：约 80%
- 代码质量：通过 ESLint / Stylelint / Flake8 / Mypy 全量检查
- TypeScript 编译：零错误

---

## 2. 核心价值主张

| 维度 | 描述 |
|------|------|
| **AI 驱动学习** | 集成 5 家 AI 提供商（OpenAI、Anthropic、DeepSeek、Google Gemini、Lingma），支持代码生成、创意激发、智能推荐 |
| **STEM 专注** | 虚拟实验室、电路仿真、AR/VR 实验、3D 元件库，软硬结合教学 |
| **个性化学习** | AI 个性化教师（学习画像+上下文记忆+成长轨迹+智能诊断） |
| **游戏化激励** | 多模态激励联动（语音/AR/手势），积分衰减机制，成就徽章系统 |
| **跨项目互联** | 与 OpenMTSciEd（课件）、OpenMTEduInst（机构）互联互通 |
| **硬件实践** | ESP32 TinyML 语音识别、硬件认证、BLE 模型热更新 |
| **区块链积分** | Hyperledger Fabric 三组织 Raft 共识网络，Go 链码积分管理系统 |

---

## 3. 目标用户群体

### 3.1 角色与需求

| 角色 | 核心需求 | 对应模块 |
|------|---------|---------|
| **学生** | 课程学习、AI 编程、虚拟实验、学习进度追踪 | 学生仪表板、AI编程、STEM实验室 |
| **家长（监护）** | 孩子学习进度监控、多子女切换查看 | 家长视图 |
| **开发者** | API 集成、SDK 使用、代码沙箱 | TypeScript SDK、OpenHydra |

> **已解耦角色**: 教师、机构管理员、学校管理员、教育局的角色功能已迁移至 **OpenMTEduInst** 项目。

### 3.2 权限模型
基于 RBAC 的权限管理体系，MatuX 简化为：
- JWT HS256 认证（30 分钟过期）
- 学生角色 + 家长监护关联
- 家长可查看关联学生的学习数据

> 机构侧的细粒度权限管理（教师/管理员/学校/教育局）由 OpenMTEduInst 负责。

---

## 4. 技术架构

### 4.1 技术栈总览

| 层级 | 技术选型 |
|------|---------|
| **前端** | Angular 21, TypeScript 5.9, SCSS, Angular Material 21, RxJS |
| **后端** | FastAPI (Python 3.8+), SQLAlchemy, Celery, Redis |
| **数据库** | SQLite (开发) / PostgreSQL (生产), Neo4j (图数据库, 可选) |
| **移动端** | Flutter (Dart 3.11) |
| **3D/AR/VR** | Three.js 0.183, Vircadia, Unity (C#), MediaPipe |
| **AI/ML** | OpenAI GPT-4, Anthropic Claude-3, DeepSeek Coder, Google Gemini, LangChain, TensorFlow Lite Micro |
| **区块链** | Hyperledger Fabric 2.x (Go 链码), Raft 共识 |
| **硬件** | ESP32, TinyML, FPGA, OpenCL, BLE |
| **基础设施** | Docker Compose, Nginx, Prometheus, Grafana, MQTT, Jenkins |
| **代码质量** | ESLint, Prettier, Stylelint, Black, isort, Flake8, Mypy, pytest, SonarQube |

### 4.2 系统架构图（逻辑分层）

```
┌─────────────────────────────────────────────────────────┐
│                    前端应用层 (Angular 21)               │
│  ┌──────────┬──────────────────────┬──────────────────┐  │
│  │ 学生门户  │ 家长视图（学习监护）  │ 营销页面         │  │
│  └──────────┴──────────────────────┴──────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                  移动端应用层 (Flutter)                   │
│  ┌──────────┬──────────┬──────────┬──────────────────┐  │
│  │ 学习进度  │ 课程详情  │ 硬件演示  │ WebSocket 通信   │  │
│  └──────────┴──────────┴──────────┴──────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                     API 网关层 (Nginx)                    │
├─────────────────────────────────────────────────────────┤
│                   后端服务层 (FastAPI)                    │
│  ┌──────────┬──────────┬──────────┬──────────────────┐  │
│  │ AI 服务   │ 学习服务  │ 支付服务  │ 区块链网关       │  │
│  ├──────────┼──────────┼──────────┼──────────────────┤  │
│  │ 课程服务  │ 认证服务  │ 硬件服务  │ 多媒体服务       │  │
│  └──────────┴──────────┴──────────┴──────────────────┘  │
├─────────────────────────────────────────────────────────┤
│               外部项目 API 集成层                          │
│  ┌──────────────────┬────────────────────────────────┐  │
│  │ OpenMTSciEd API  │ OpenMTEduInst API              │  │
│  │ (课件/知识图谱)   │ (机构/教师/排课)               │  │
│  └──────────────────┴────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                    数据与基础设施层                       │
│  ┌──────────┬──────────┬──────────┬──────────────────┐  │
│  │PostgreSQL │  Redis   │  Neo4j   │  Celery Queue    │  │
│  ├──────────┼──────────┼──────────┼──────────────────┤  │
│  │Fabric 网络│Prometheus│ Grafana  │  Docker 集群     │  │
│  └──────────┴──────────┴──────────┴──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 5. 功能需求矩阵

### 5.1 核心功能模块（18 个 MatuX 自有）

| # | 模块名称 | 完成状态 | 优先级 | 说明 |
|---|---------|---------|--------|------|
| 1 | AI 代码生成服务 | ✅ 完成 | P0 | 多模型代码生成与优化 |
| 2 | 智能推荐系统 | ✅ 完成 | P0 | 课程与学习路径推荐 |
| 3 | 电商支付系统 | ✅ 完成 | P1 | Token 购买与订阅管理 |
| 4 | 硬件认证服务 | ✅ 完成 | P1 | IoT 设备接入与认证 |
| 5 | AI 创意激发引擎 | ✅ 完成 | P0 | AI 驱动的创意生成 |
| 6 | 协作编辑系统 | ✅ 完成 | P1 | OT 算法实时协作 |
| 7 | XR 远程教学系统 | 🔧 开发中 | P2 | AR/VR 远程互动 |
| 8 | 课程版本控制 | ✅ 完成 | P1 | 课程版本管理与回滚 |
| 9 | AR/VR 课程集成 | ✅ 完成 | P1 | 3D 模型与虚拟实验 |
| 10 | 区块链积分平台 | ✅ 完成 | P1 | Fabric 积分管理 |
| 11 | 多模态激励联动 | ✅ 完成 | P1 | 语音/AR/手势激励 |
| 12 | AI 模型热更新 | 🔧 开发中 | P2 | BLE 无线推送模型 |
| 13 | OpenHydra 集成平台 | ✅ 完成 | P1 | AI 沙箱与微课程 |
| 14 | AI 个性化教师 | ✅ 完成 | P0 | 学习画像+记忆+诊断 |
| 15 | 联动任务系统 | ✅ 完成 | P1 | 软硬结合综合实践 |
| 16 | 错误日志收集 | ✅ 完成 | P2 | 全局错误追踪 |
| 17 | 赞助活动管理 | ✅ 完成 | P2 | 活动创建与统计 |
| 18 | Avatar 管理 | 🔧 开发中 | P2 | Vircadia 虚拟形象 |

### 5.2 已解耦模块（4 个）

| # | 模块名称 | 目标项目 | 说明 |
|---|---------|---------|------|
| - | 课件管理 | OpenMTSciEd | 教程/课件/知识图谱/硬件项目资源 |
| - | 教育机构管理 | OpenMTEduInst | 机构/校区/教师/排课/设备管理 |
| - | 多租户管理 | OpenMTEduInst | SaaS 多租户权限控制 |
| - | 许可证管理 | OpenMTEduInst | 软件授权方案 |

> **避免重复开发**: 以上模块的功能请在对应项目中开发，MatuX 通过 API 调用对应服务。

### 5.3 学生场景专属功能

| 功能 | 目标角色 | 状态 |
|------|---------|------|
| 跨来源学习进度追踪 | 学生/家长 | ✅ 完成 |
| 学习来源标签卡片 | 学生 | ✅ 完成 |
| 按机构/兴趣班分类进度 | 家长 | ✅ 完成 |
| 多子女进度切换 | 家长 | ✅ 完成 |
| AI 个性化学习建议 | 学生 | ✅ 完成 |
| 学习画像与成长轨迹 | 学生/家长 | ✅ 完成 |

---

## 6. 已解耦模块

以下模块已从 MatuX 解耦至独立开源项目，MatuX 通过 API 调用对应服务：

| 模块 | 目标项目 | API 端点 | 说明 |
|------|---------|---------|------|
| 课件管理 | [OpenMTSciEd](G:\OpenMTSciEd) | `localhost:3000/api/v1` | 教程/课件/知识图谱/硬件项目资源 |
| 机构管理 | [OpenMTEduInst](G:\OpenMTEduInst) | 独立部署 | 机构/校区/教师/排课/设备/Token计费 |
| 多租户管理 | [OpenMTEduInst](G:\OpenMTEduInst) | 独立部署 | SaaS 多租户权限控制 |
| 许可证管理 | [OpenMTEduInst](G:\OpenMTEduInst) | 独立部署 | 软件授权方案 |

> **避免重复开发**: 以上模块的功能请在对应项目中开发，MatuX 不再实现这些功能。

---

## 7. 后端服务模块

### 7.1 API 路由（MatuX 自有）

| 路由模块 | 功能 | 文件 |
|---------|------|------|
| `auth_routes` | 用户认证与授权 | `routes/auth_routes.py` |
| `ai_routes` | AI 代码生成与对话 | `routes/ai_routes.py` |
| `ai_recommend_routes` | 智能推荐 | `routes/ai_recommend_routes.py` |
| `ai_capabilities_routes` | XEduHub AI 能力组件 | `routes/ai_capabilities_routes.py` |
| `ai_edu_progress_routes` | AI 教育学习进度 | `routes/ai_edu_progress_routes.py` |
| `ai_teacher_routes` | AI 个性化教师 | `routes/ai_teacher_routes.py` |
| `course_routes` | 课程 CRUD | `routes/course_routes.py` |
| `course_version_routes` | 课程版本控制 | `routes/course_version_routes.py` |
| `dynamic_course_routes` | 动态课程生成 | `routes/dynamic_course_routes.py` |
| `learning_source_routes` | 学习来源管理 | `routes/learning_source_routes.py` |
| `learning_behavior_routes` | 学习行为分析 | `routes/learning_behavior_routes.py` |
| `unified_learning_record_routes` | 统一学习记录 | `routes/unified_learning_record_routes.py` |
| `vector_knowledge_routes` | 向量知识库 (RAG) | `routes/vector_knowledge_routes.py` |
| `local_knowledge_graph_routes` | 本地知识图谱 | `routes/local_knowledge_graph_routes.py` |
| `creativity_routes` | AI 创意引擎 | `routes/creativity_routes.py` |
| `collaborative_editor_routes` | 协作编辑器 | `routes/collaborative_editor_routes.py` |
| `ar_lab_routes` | AR 实验室 | `routes/ar_lab_routes.py` |
| `ar_vr_routes` | AR/VR 课程 | `routes/ar_vr_routes.py` |
| `ar_vr_mock_routes` | AR/VR Mock | `routes/ar_vr_mock_routes.py` |
| `ar_rewards` | AR 奖励系统 | `routes/ar_rewards.py` |
| `digital_twin_routes` | 数字孪生 | `routes/digital_twin_routes.py` |
| `blockchain_gateway_routes` | 区块链网关 | `routes/blockchain_gateway_routes.py` |
| `payment_routes` | 支付系统 | `routes/payment_routes.py` |
| `subscription_routes` | 订阅管理 | `routes/subscription_routes.py` |
| `finance_routes` | 财务管理 | `routes/finance_routes.py` |
| `sponsorship_routes` | 赞助管理 | `routes/sponsorship_routes.py` |
| `hardware_certification_routes` | 硬件认证 | `routes/hardware_certification_routes.py` |
| `model_update_routes` | AI 模型更新 | `routes/model_update_routes.py` |
| `model_benchmark_routes` | 模型基准测试 | `routes/model_benchmark_routes.py` |
| `multimedia_routes` | 多媒体管理 | `routes/multimedia_routes.py` |
| `openhydra_routes` | OpenHydra 沙箱 | `routes/openhydra_routes.py` |
| `admin_settings_routes` | Admin 全局设置 | `routes/admin_settings_routes.py` |
| `unified_auth_router` | 统一认证（模块化） | `modules/auth/auth_routes.py` |
| `aggregation_router` | 课程聚合 | `modules/learning/aggregation_routes.py` |

### 7.2 已解耦路由（保留存根）

| 路由模块 | 原功能 | 状态 | 目标项目 |
|---------|--------|------|---------|
| `educational_institution_routes` | 教育机构管理 | 存根保留，已解耦 | OpenMTEduInst |
| `material_routes` | 统一课件库 | 存根保留，已解耦 | OpenMTSciEd |
| `permission_routes` | 机构侧权限管理 | 存根保留，已解耦 | OpenMTEduInst |
| `tenant_config_routes` | 租户配置 | 存根保留，已解耦 | OpenMTEduInst |

### 7.3 外部项目 API 集成

| 外部项目 | API 基地址 | 用途 |
|---------|-----------|------|
| OpenMTSciEd | `http://localhost:3000/api/v1` | 教程/课件/知识图谱/学习路径推荐 |
| OpenMTEduInst | 独立部署配置 | 机构/教师/排课/设备管理 |

### 7.2 业务服务层（70+ 个服务文件）

涵盖：AI 服务、课程服务、用户服务、支付服务、区块链服务、硬件服务、多媒体服务、分析服务等。

### 7.3 中间件

| 中间件 | 功能 |
|--------|------|
| `APMMiddleware` | 应用性能监控 |
| `PermissionMiddleware` | 权限验证 |
| `LicenseMiddleware` | 许可证校验 |
| `CircuitBreakerMiddleware` | 熔断器保护（5 次失败/60s 超时） |
| `CORS` | 跨域配置（localhost:3000/4200） |

### 7.4 AI 提供商配置

| 提供商 | 默认模型 | 用途 |
|--------|---------|------|
| OpenAI | `gpt-4-turbo` | 通用 AI 对话与代码生成 |
| Lingma | `lingma-code-pro` | 专业代码生成 |
| DeepSeek | `deepseek-coder` | 代码理解与优化 |
| Anthropic | `claude-3-opus-20240229` | 复杂推理任务 |
| Google | `gemini-pro` | 多模态分析 |

### 7.5 可选功能路由（按需启用）

以下路由因依赖或环境原因暂时注释，按需启用：
- `federated_routes` — 联邦学习
- `gesture_recognition` — XR 手势识别
- `hardware_alert_routes` — MQTT 硬件告警
- `pretrain_model_routes` — 预训练模型服务
- `recommendation_routes` — 旧版推荐服务
- `celery_monitoring_routes` — Celery 监控

---

## 8. 前端应用模块

### 8.1 Angular 应用结构

| 模块目录 | 功能 | 文件数 |
|---------|------|--------|
| `ar-lab/` | AR 实验室界面 | 多个 |
| `auth/` | 登录/注册 | 多个 |
| `ai-code-generator/` | AI 代码生成器界面 | 多个 |
| `creativity-engine/` | AI 创意引擎界面 | 多个 |
| `education/` | 教育模块（路由+模块） | 多个 |
| `offline-mode/` | 离线模式支持 | 多个 |
| `user/` | 用户中心（学生/家长/Token） | 多个 |
| `admin/` | 管理后台（系统配置，非机构管理） | 多个 |

> **注意**: 机构管理前端已迁移至 OpenMTEduInst，课件管理前端已迁移至 OpenMTSciEd。

### 8.2 共享与核心层

| 目录 | 内容 |
|------|------|
| `core/services/` | 50 个核心服务 |
| `core/guards/` | 路由守卫 |
| `core/models/` | 核心数据模型 |
| `shared/` | 共享模块/组件/指令/服务 |
| `components/` | 67 个可复用组件（AI Edu、Token、Vircadia 等） |
| `models/` | 前端数据模型 |
| `styles/` | SCSS 变量与主题（CSS 自定义属性体系） |
| `i18n/` | 国际化（中/英） |

### 8.3 共享 SCSS 样式体系

| 文件 | 用途 |
|------|------|
| `_buttons.scss` | 按钮样式规范 |
| `_cards.scss` | 卡片组件样式 |
| `_forms.scss` | 表单样式 |
| `_marketing.scss` | 营销页面样式 |
| `_editor-components.scss` | 编辑器组件样式 |
| `_multimedia-components.scss` | 多媒体组件样式 |

---

## 9. Flutter 移动端模块

### 9.1 应用信息
- **包名**: `matux_flutter`
- **版本**: 1.0.0+1
- **Dart SDK**: ^3.11.1
- **UI 框架**: Material Design

### 9.2 屏幕与页面

| 屏幕 | 文件 | 功能 |
|------|------|------|
| 首页 | `home_screen.dart` | 主导航入口 |
| 登录 | `login_screen.dart` | 用户认证 |
| 个人中心 | `profile_screen.dart` | 用户信息管理 |
| 学习进度 | `learning_progress_screen.dart` | 跨机构学习进度 |
| 课程列表 | `course_list_screen.dart` | 课程浏览 |
| 课程详情 | `course_detail_screen.dart` | 课程内容 |
| 硬件演示 | `hardware_demo_screen.dart` | 硬件交互 |
| WebSocket 演示 | `websocket_demo_screen.dart` | 实时通信 |

### 9.3 服务层

| 服务 | 文件 | 功能 |
|------|------|------|
| 认证服务 | `auth.service.dart` | 登录/注册/Token 管理 |
| 课程服务 | `course.service.dart` | 课程 CRUD |
| 进度服务 | `progress.service.dart` | 学习进度追踪 |
| 存储服务 | `storage.service.dart` | 本地数据持久化 |
| WebSocket | `websocket.service.dart` | 实时双向通信 |
| 硬件通信 | `hardware_communication.service.dart` | 硬件设备交互 |
| 硬件 WebSocket | `hardware_websocket_adapter.service.dart` | 硬件实时适配 |
| 桌面串口 | `desktop_serial.service.dart` | 桌面端串口通信 |
| 传感器集成 | `sensor_integration.service.dart` | 传感器数据采集 |
| WebUSB API | `webusb_api.service.dart` | WebUSB 接口 |

### 9.4 数据模型

| 模型 | 说明 |
|------|------|
| `course.dart` | 课程模型 |
| `progress.dart` | 学习进度模型 |
| `user.dart` | 用户模型 |
| `professional_instruments.dart` | 专业仪器模型（含 `.g.dart` 序列化） |

---

## 10. 区块链模块

### 10.1 架构

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 区块链平台 | Hyperledger Fabric 2.x | 企业级联盟链 |
| 共识算法 | Raft | 三组织集群 |
| 智能合约 | Go 语言链码 | 积分管理系统 |
| 身份认证 | MSP (Membership Service Provider) | 基于证书的身份管理 |

### 10.2 目录结构

| 目录 | 内容 |
|------|------|
| `blockchain/chaincode/` | Go 链码实现 |
| `blockchain/config/` | 网络配置文件 |
| `blockchain/fabric-network/` | 网络拓扑定义 |
| `blockchain/scripts/` | 部署与运维脚本 |

### 10.3 文档

- `FABRIC_DEVELOPER_DOCUMENTATION.md` — 开发者手册
- `API_REFERENCE_MANUAL.md` — 链码 API 参考
- `TECHNICAL_ARCHITECTURE_DIAGRAMS.md` — 架构图

---

## 11. 硬件与边缘计算模块

### 11.1 ESP32 TinyML 语音识别

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 识别准确率 | ≥85% | 95% | ✅ |
| 响应延迟 | ≤1000ms | 640ms | ✅ |
| 内存使用 | ≤520KB | 335KB (62.9%) | ✅ |
| 电池续航 | ≥8小时 | 22.7小时 | ✅ |

**技术栈**: TensorFlow Lite Micro + BLE 模型热更新 + 离线推理

### 11.2 硬件目录结构

| 目录 | 内容 |
|------|------|
| `hardware/tinyml-voice-recognition/` | TinyML 语音识别代码 |
| `hardware/fpga/` | FPGA 开发 |
| `hardware/hal/` | 硬件抽象层 |
| `hardware/matrix_lib/` | 矩阵运算库 |
| `hardware/opencl/` | OpenCL 加速 |
| `hardware/tests/` | 硬件测试 |

---

## 12. AI 与机器学习模块

### 12.1 AI 服务核心

| 服务 | 说明 |
|------|------|
| 创意激发引擎 | AI 驱动的多维度创意生成 |
| 智能推荐系统 | 基于用户画像的个性化推荐 |
| 知识图谱 | Neo4j 图数据库驱动的知识关联 |
| AI 学习助手 | LangChain 驱动的对话式辅导 |

### 12.2 OpenHydra + XEdu 集成

| 功能 | 说明 |
|------|------|
| 微课程转化 | 游戏化课程设计与转化 |
| AI 沙箱环境 | 安全的代码执行环境 |
| XEduHub AI 能力 | 教育专属 AI 能力组件 |
| 联动任务系统 | 软硬结合的综合实践（如智能温室案例） |

### 12.3 模型管理

| 功能 | 说明 |
|------|------|
| 模型基准测试 | 多模型性能对比 |
| 模型热更新 | BLE 无线推送新模型 |
| 模型优化 | 量化/剪枝/蒸馏 |
| 回测系统 | 29 个回测报告 |

---

## 13. 开发优先级与路线图

> ⚠️ **避免重复开发**: 课件管理功能在 **OpenMTSciEd** 中开发，机构管理功能在 **OpenMTEduInst** 中开发。MatuX 不再重复开发这些功能，通过 API 调用对应服务。

### 13.1 当前 Sprint（2026-06）

| 优先级 | 模块 | 状态 |
|--------|------|------|
| **P0** | Electron 桌面端 MVP | 🔧 开发中 |
| **P0** | AI 个性化教师完善 | 🔧 开发中 |
| **P1** | Flutter 移动端功能对齐 | 📋 待开始 |
| **P1** | 离线模式增强 | 📋 待开始 |
| **P2** | XR 远程教学完善 | 🔧 开发中 |
| **P2** | AI 模型热更新完善 | 🔧 开发中 |
| **P2** | Vircadia Avatar 管理 | 🔧 开发中 |

### 13.2 技术债务

| 项目 | 说明 | 优先级 |
|------|------|--------|
| 数据库迁移 | SQLite → PostgreSQL（生产环境） | P1 |
| 被注释路由恢复 | federated/gesture/hardware_alert 等路由 | P2 |
| 文档版本更新 | INDEX.md 仍标注 Angular 16，实际为 21 | P2 |
| Neo4j 集成 | 知识图谱功能完善（与 OpenMTSciEd 协作） | P3 |

### 13.3 未来规划

- AI 个性化教师增强（情感陪伴、智能诊断）
- 移动端（Flutter）功能对齐桌面端
- 国际化多语言扩展
- 无障碍访问（a11y）支持
- 与 OpenMTSciEd 知识图谱深度集成
- 与 OpenMTEduInst 学习进度互通增强

### 14.1 容器化

| 文件 | 用途 |
|------|------|
| `docker-compose.yml` | 主服务编排 |
| `docker-compose.override.yml` | 本地开发覆盖 |
| `docker-compose.cloud.yml` | 云部署 |
| `docker-compose.openhydra.yml` | OpenHydra 集成 |
| `docker-compose.vircadia.yml` | Vircadia 元宇宙 |
| `docker-compose.test.yml` | 测试环境 |
| `docker-compose.sonarqube.yml` | 代码质量分析 |
| `docker-compose.blog.yml` | 博客服务 |
| `docker-compose.3d-model.dev.yml` | 3D 模型开发 |

### 14.2 反向代理与负载均衡

| 文件 | 用途 |
|------|------|
| `nginx/nginx.conf` | Nginx 主配置 |
| `nginx/nginx-proxy.conf` | 反向代理配置 |

### 14.3 监控与告警

| 组件 | 用途 |
|------|------|
| Prometheus | 指标采集（`/metrics` 端点） |
| Grafana | 可视化面板 |
| Alertmanager | 告警管理 |
| APM Middleware | 应用性能监控 |

### 14.4 编排与 CI/CD

| 组件 | 用途 |
|------|------|
| Jenkins | CI/CD 流水线 |
| Kubernetes (k8s/) | 容器编排（7 个 YAML） |
| Husky + lint-staged | Git 提交钩子 |
| SonarQube | 代码质量平台 |

### 14.5 开发命令

```bash
# 前端
npm start              # 启动开发服务器
npm run build:prod     # 生产构建
npm run dev:all        # 同时启动前端+后端
npm run quality:check  # 全面质量检查

# 后端
cd backend
python main.py         # 启动后端服务
uvicorn main:app --reload  # 热重载模式

# 测试
python -m pytest backend/tests/
ng test
npm run e2e
```

---

## 15. 代码质量与测试

### 15.1 代码质量工具链

| 层级 | 工具 | 配置 |
|------|------|------|
| TypeScript | ESLint + Prettier | `package.json` |
| SCSS | Stylelint | 项目规则 |
| Python | Black (line-length=88) | `pyproject.toml` |
| Python | isort (profile=black) | `pyproject.toml` |
| Python | Flake8 (pycodestyle/pyflakes/bugbear) | `pyproject.toml` |
| Python | Mypy (strict mode) | `pyproject.toml` |
| 测试 | pytest >= 7.0 + pytest-cov + pytest-asyncio | `pyproject.toml` |
| 平台 | SonarQube | `sonar-project.properties` |

### 15.2 测试要求

| 指标 | 目标 | 当前 |
|------|------|------|
| 单元测试覆盖率 | ≥80% | ~80% |
| 测试用例数 | - | 61+ |
| TypeScript 编译错误 | 0 | 0 |

### 15.3 SCSS 预算规范

- 单个组件 SCSS 文件 ≤ 4KB
- 共享样式抽取到 `shared-styles/`
- CSS 自定义属性体系减少重复定义
- Smart/Dumb 组件架构分离

---

## 16. 文档体系

### 16.1 双轨制文档

| 文档类型 | 目录 | 面向受众 |
|---------|------|---------|
| 对外文档 | `docs/` | 用户、管理者、新手 |
| 技术文档 | `documentation/` | 开发者、维护者 |

### 16.2 文档分类

| 分类 | 位置 | 内容 |
|------|------|------|
| 项目概述 | `docs/01-项目概述/`, `documentation/shared/architecture/` | 项目介绍、架构设计 |
| 开发指南 | `docs/02-开发指南/`, `documentation/shared/guides/` | 快速开始、路由映射 |
| 核心技术 | `docs/03-核心技术/`, `documentation/backend/` | 区块链、AR/VR、AI |
| API 参考 | `docs/04-API参考/`, `documentation/backend/routes/` | 接口规范 |
| 部署运维 | `docs/05-部署运维/`, `documentation/deployment/` | 部署、CI/CD |
| 测试质量 | `docs/06-测试质量/`, `documentation/tests/` | 测试报告 |

### 16.3 关键文档清单

- `README.md` — 项目主 README
- `docs/PROJECT_REQUIREMENTS.md` — 本文档（项目需求文档）
- `docs/INDEX.md` — 文档中心索引
- `docs/SITE_MAP.md` — 网站地图
- `docs/FRONTEND_ROUTING.md` — 前端路由详解
- `documentation/shared/architecture/system-architecture.md` — 系统架构
- `documentation/shared/architecture/global-technical-architecture.md` — 全局技术架构
- `documentation/deployment/guide.md` — 部署指南
- `documentation/deployment/jenkins-ci-cd.md` — Jenkins 配置
- `blockchain/FABRIC_DEVELOPER_DOCUMENTATION.md` — 区块链开发文档

---



---

## 17. 附录

### 17.1 项目生态

| 项目 | 定位 | 仓库 |
|------|------|------|
| **MatuX** | STEM 学习平台（学生端） | 本仓库 |
| **OpenMTSciEd** | 开放 STEM 教育资源平台（课件管理） | `G:\OpenMTSciEd` |
| **OpenMTEduInst** | STEM 教育机构管理工具（机构管理） | `G:\OpenMTEduInst` |

### 17.2 项目目录总览

```
MatuX/
├── src/                    # Angular 前端源码（学生学习端）
│   ├── app/
│   │   ├── components/     # 67 个可复用组件
│   │   ├── core/           # 核心服务（50 个）/守卫/模型
│   │   ├── shared/         # 共享模块
│   │   ├── styles/         # SCSS 主题
│   │   └── user/           # 用户中心（学生/家长）
│   └── styles/             # 全局样式
├── backend/                # FastAPI 后端
│   ├── main.py             # 主入口
│   ├── routes/             # 路由（含已解耦存根）
│   ├── services/           # 服务
│   ├── models/             # 数据模型
│   ├── middleware/         # 中间件
│   └── config/             # 配置模块
├── electron/               # Electron 桌面端
├── flutter_app/            # Flutter 移动端
├── blockchain/             # Hyperledger Fabric
├── hardware/               # 硬件模块
├── docker/                 # Docker 编排
├── scripts/                # 工具脚本
├── docs/                   # 对外文档
├── documentation/          # 技术文档
└── sdk/                    # TypeScript SDK
```

### 17.3 环境要求

| 组件 | 最低版本 |
|------|---------|
| Node.js | 18+ |
| Python | 3.8 - 3.11 |
| Dart | 3.11+ |
| Docker | 20.10+ |
| PostgreSQL | 14+ (生产) |
| Redis | 6+ |

### 17.4 关键配置文件

| 文件 | 用途 |
|------|------|
| `package.json` | 前端依赖与脚本 |
| `angular.json` | Angular 项目配置 |
| `tsconfig.json` | TypeScript 配置 |
| `pyproject.toml` | Python 项目配置 |
| `pubspec.yaml` | Flutter 项目配置 |
| `backend/config/settings.py` | 后端配置中心 |
| `docker-compose.yml` | 容器编排 |
| `Jenkinsfile` | CI/CD 流水线 |
| `sonar-project.properties` | 代码质量分析 |

---

> **文档维护**: 本文档随项目开发进展持续更新  
> **最后更新**: 2026-05-31  
> **版本**: v5.0

### v5.0 更新记录 (2026-05-31)
- **项目定位重构**: 从"全栈教育科技平台"调整为"STEM 学习平台（学生端）"
- **模块解耦**: 课件管理解耦至 OpenMTSciEd，机构管理解耦至 OpenMTEduInst
- **角色简化**: 仅有学生角色（家长监护），移除教师/机构管理员/学校管理员/教育局角色
- **添加三项目生态说明**: MatuX + OpenMTSciEd + OpenMTEduInst
- **添加避免重复开发警告**

### v4.2 更新记录 (2026-05-30)
- **Electron 桌面端修复**:
  - 修复 `main.js` 致命 Bug: `require('main')` → `require('electron')`
  - 移动 `wait-port` 从 devDependencies 到 dependencies
  - 生成 `build/icon.ico` 图标文件
  - 修复 `renderer/**/*` 路径 → `../dist/imatuproject/**/*`
  - 修复前端加载路径: `imato-frontend` → `imatuproject`
  - 补充 `ipcMain.on()` 监听器（to-backend, app-event）
  - 新增 `get-backend-message` IPC handler
- **产品命名统一**: Flutter Windows/Linux/macOS Runner 全部统一为 "iMato"
- **新增**: `src/app/core/models/electron-api.model.ts` — Angular 端的 Electron API 类型定义
