# iMato (MatuX) 教育平台 - 项目需求文档

> **版本**: v4.2  
> **最后更新**: 2026-05-30  
> **状态**: 持续迭代开发中

---

## 目录

1. [项目概述](#1-项目概述)
2. [核心价值主张](#2-核心价值主张)
3. [目标用户群体](#3-目标用户群体)
4. [技术架构](#4-技术架构)
5. [功能需求矩阵](#5-功能需求矩阵)
6. [后端服务模块](#6-后端服务模块)
7. [前端应用模块](#7-前端应用模块)
8. [Flutter 移动端模块](#8-flutter-移动端模块)
9. [区块链模块](#9-区块链模块)
10. [硬件与边缘计算模块](#10-硬件与边缘计算模块)
11. [AI 与机器学习模块](#11-ai-与机器学习模块)
12. [多角色仪表板开发](#12-多角色仪表板开发)
13. [基础设施与部署](#13-基础设施与部署)
14. [代码质量与测试](#14-代码质量与测试)
15. [文档体系](#15-文档体系)
16. [开发优先级与路线图](#16-开发优先级与路线图)
17. [附录](#17-附录)

---

## 1. 项目概述

### 1.1 项目名称
**iMato (MatuX)** — 基于微服务架构的现代化 AI 驱动教育平台

### 1.2 项目定位
融合边缘计算、区块链、AR/VR、3D 虚拟实验室、多模态激励联动等前沿技术的全栈教育科技平台，为教师、学生、家长、机构管理员、学校管理员和教育局提供一站式教育管理与学习体验解决方案。

### 1.3 开源协议
GPL-3.0

### 1.4 当前完成度
- 核心功能模块：22 个已完成
- 测试覆盖率：约 80%
- 代码质量：通过 ESLint / Stylelint / Flake8 / Mypy 全量检查
- TypeScript 编译：零错误

---

## 2. 核心价值主张

| 维度 | 描述 |
|------|------|
| **AI 驱动教学** | 集成 5 家 AI 提供商（OpenAI、Anthropic、DeepSeek、Google Gemini、Lingma），支持代码生成、创意激发、智能推荐 |
| **跨机构学习** | 统一学习记录系统，支持学生在不同教育机构间的学习数据无缝流转 |
| **多角色管理** | 为教师、机构管理员、学校管理员、教育局提供专属仪表板和数据视图 |
| **硬件实践教学** | ESP32 TinyML 语音识别、硬件认证、AR/VR 虚拟实验室，实现软硬结合教学 |
| **区块链积分** | Hyperledger Fabric 三组织 Raft 共识网络，Go 链码积分管理系统 |
| **游戏化激励** | 多模态激励联动（语音/AR/手势），积分衰减机制，成就徽章系统 |
| **开放生态** | OpenHydra 沙箱环境、XEdu AI 能力组件、Vircadia 元宇宙集成 |

---

## 3. 目标用户群体

### 3.1 角色与需求

| 角色 | 核心需求 | 对应模块 |
|------|---------|---------|
| **学生** | 课程学习、学习进度追踪、AI 学习助手、AR/VR 实验 | 学生仪表板、学习进度屏幕 |
| **教师** | 跨机构教学管理、学生学情分析、课程创建 | 教师仪表板、课程管理 |
| **家长** | 孩子学习进度监控、多子女切换查看 | 家长仪表板 |
| **机构管理员** | 课程运营、教师管理、学员管理 | 机构管理仪表板 |
| **学校管理员** | 年级/班级管理、校本课程、教师工作量统计 | 学校管理仪表板 |
| **教育局** | 区域数据概览、学校对比、教学质量监控 | 教育局仪表板 |
| **开发者** | API 集成、SDK 使用、代码沙箱 | TypeScript SDK、OpenHydra |

### 3.2 权限模型
基于 RBAC 的权限管理体系，支持：
- JWT HS256 认证（30 分钟过期）
- 多租户隔离
- MSP 身份认证（区块链层）
- 细粒度 API 权限控制

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
│  ┌──────────┬──────────┬──────────┬──────────────────┐  │
│  │ 学生门户  │ 教师门户  │ 管理后台  │ 营销页面         │  │
│  └──────────┴──────────┴──────────┴──────────────────┘  │
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
│  │ AI 服务   │ 教育服务  │ 支付服务  │ 区块链网关       │  │
│  ├──────────┼──────────┼──────────┼──────────────────┤  │
│  │ 课程服务  │ 认证服务  │ 硬件服务  │ 多媒体服务       │  │
│  └──────────┴──────────┴──────────┴──────────────────┘  │
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

### 5.1 核心功能模块（22 个）

| # | 模块名称 | 完成状态 | 优先级 | 说明 |
|---|---------|---------|--------|------|
| 1 | AI 代码生成服务 | ✅ 完成 | P0 | 多模型代码生成与优化 |
| 2 | 智能推荐系统 | ✅ 完成 | P0 | 课程与学习路径推荐 |
| 3 | 电商支付系统 | ✅ 完成 | P1 | 课程购买与订阅管理 |
| 4 | 硬件认证服务 | ✅ 完成 | P1 | IoT 设备接入与认证 |
| 5 | 多租户管理系统 | ✅ 完成 | P1 | SaaS 多租户隔离 |
| 6 | AI 创意激发引擎 | ✅ 完成 | P0 | AI 驱动的创意生成 |
| 7 | 协作编辑系统 | ✅ 完成 | P1 | OT 算法实时协作 |
| 8 | 许可证管理系统 | ⚠️ 已解耦 | P2 | 迁移至 OpenMTEduInst |
| 9 | XR 远程教学系统 | 🔧 开发中 | P2 | AR/VR 远程互动 |
| 10 | 教育机构管理 | ✅ 完成 | P0 | 机构 CRUD 与配置 |
| 11 | 课程版本控制 | ✅ 完成 | P1 | 课程版本管理与回滚 |
| 12 | RBAC 权限管理 | ✅ 完成 | P0 | 角色访问控制 |
| 13 | AR/VR 课程集成 | ✅ 完成 | P1 | 3D 模型与虚拟实验 |
| 14 | 企业级区块链平台 | ✅ 完成 | P1 | Fabric 积分管理 |
| 15 | 多模态激励联动 | ✅ 完成 | P1 | 语音/AR/手势激励 |
| 16 | AI 模型热更新 | 🔧 开发中 | P2 | BLE 无线推送模型 |
| 17 | OpenHydra 集成平台 | ✅ 完成 | P1 | AI 沙箱与微课程 |
| 18 | AI 学习助手 | ✅ 完成 | P0 | LangChain 对话辅导 |
| 19 | 联动任务系统 | ✅ 完成 | P1 | 软硬结合综合实践 |
| 20 | 错误日志收集 | ✅ 完成 | P2 | 全局错误追踪 |
| 21 | 赞助活动管理 | ✅ 完成 | P2 | 活动创建与统计 |
| 22 | Avatar 管理 | 🔧 开发中 | P2 | Vircadia 虚拟形象 |

### 5.2 教育场景专属功能

| 功能 | 目标角色 | 状态 |
|------|---------|------|
| 跨机构学习进度追踪 | 学生/教师/家长 | ✅ 完成 |
| 学习来源标签卡片 | 学生 | ✅ 完成 |
| 按机构/兴趣班分类进度 | 家长 | ✅ 完成 |
| 多子女进度切换 | 家长 | ✅ 完成 |
| 跨机构教学进度展示 | 教师 | 🔧 Phase 1 |
| 学生学情总览 | 教师 | 🔧 Phase 1 |
| 机构概览（学生/教师/课程数） | 机构管理员 | 📋 Phase 2 |
| 课程运营管理 | 机构管理员 | 📋 Phase 2 |
| 年级/班级管理 | 学校管理员 | 📋 Phase 3 |
| 校本课程管理 | 学校管理员 | 📋 Phase 3 |
| 区域数据概览 | 教育局 | 📋 Phase 4 |
| 学校数据对比 | 教育局 | 📋 Phase 4 |
| 教学质量监控 | 教育局 | 📋 Phase 4 |

---

## 6. 后端服务模块

### 6.1 API 路由（34 个已启用）

| 路由模块 | 功能 | 文件 |
|---------|------|------|
| `auth_routes` | 用户认证与授权 | `routes/auth_routes.py` |
| `ai_routes` | AI 代码生成与对话 | `routes/ai_routes.py` |
| `ai_recommend_routes` | 智能推荐 | `routes/ai_recommend_routes.py` |
| `ai_capabilities_routes` | XEduHub AI 能力组件 | `routes/ai_capabilities_routes.py` |
| `ai_edu_progress_routes` | AI 教育学习进度 | `routes/ai_edu_progress_routes.py` |
| `course_routes` | 课程 CRUD | `routes/course_routes.py` |
| `course_version_routes` | 课程版本控制 | `routes/course_version_routes.py` |
| `dynamic_course_routes` | 动态课程生成 | `routes/dynamic_course_routes.py` |
| `material_routes` | 统一课件库 | `routes/material_routes.py` |
| `learning_source_routes` | 学习来源管理 | `routes/learning_source_routes.py` |
| `learning_behavior_routes` | 学习行为分析 | `routes/learning_behavior_routes.py` |
| `unified_learning_record_routes` | 统一学习记录 | `routes/unified_learning_record_routes.py` |
| `educational_institution_routes` | 教育机构管理 | `routes/educational_institution_routes.py` |
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
| `permission_routes` | 权限管理 | `routes/permission_routes.py` |
| `tenant_config_routes` | 租户配置 | `routes/tenant_config_routes.py` |
| `openhydra_routes` | OpenHydra 沙箱 | `routes/openhydra_routes.py` |
| `admin_settings_routes` | Admin 全局设置 | `routes/admin_settings_routes.py` |
| `unified_auth_router` | 统一认证（模块化） | `modules/auth/auth_routes.py` |
| `aggregation_router` | 课程聚合 | `modules/learning/aggregation_routes.py` |

### 6.2 业务服务层（76 个服务文件）

涵盖：AI 服务、课程服务、用户服务、支付服务、区块链服务、硬件服务、多媒体服务、分析服务等。

### 6.3 中间件（15 个）

| 中间件 | 功能 |
|--------|------|
| `APMMiddleware` | 应用性能监控 |
| `PermissionMiddleware` | 权限验证 |
| `LicenseMiddleware` | 许可证校验 |
| `CircuitBreakerMiddleware` | 熔断器保护（5 次失败/60s 超时） |
| `CORS` | 跨域配置（localhost:3000/4200） |

### 6.4 AI 提供商配置

| 提供商 | 默认模型 | 用途 |
|--------|---------|------|
| OpenAI | `gpt-4-turbo` | 通用 AI 对话与代码生成 |
| Lingma | `lingma-code-pro` | 专业代码生成 |
| DeepSeek | `deepseek-coder` | 代码理解与优化 |
| Anthropic | `claude-3-opus-20240229` | 复杂推理任务 |
| Google | `gemini-pro` | 多模态分析 |

### 6.5 可选功能路由（按需启用）

以下路由因依赖或环境原因暂时注释，按需启用：
- `federated_routes` — 联邦学习
- `gesture_recognition` — XR 手势识别
- `hardware_alert_routes` — MQTT 硬件告警
- `pretrain_model_routes` — 预训练模型服务
- `recommendation_routes` — 旧版推荐服务
- `celery_monitoring_routes` — Celery 监控

---

## 7. 前端应用模块

### 7.1 Angular 应用结构

| 模块目录 | 功能 | 文件数 |
|---------|------|--------|
| `admin/` | 管理后台（布局/路由/模块） | 多个 |
| `ai-code-generator/` | AI 代码生成器界面 | 多个 |
| `ar-lab/` | AR 实验室界面 | 多个 |
| `auth/` | 登录/注册 | 多个 |
| `creativity-engine/` | AI 创意引擎界面 | 多个 |
| `education/` | 教育模块（路由+模块） | 多个 |
| `license-management/` | 许可证管理 | 多个 |
| `management/` | 管理门户（教育局/学校/用户） | 多个 |
| `offline-mode/` | 离线模式支持 | 多个 |
| `user/` | 用户中心（学生/教师/家长/教育局/学校管理/Token） | 多个 |
| `dark-mode-demo/` | 暗色模式演示 | 多个 |

### 7.2 共享与核心层

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

### 7.3 共享 SCSS 样式体系

| 文件 | 用途 |
|------|------|
| `_buttons.scss` | 按钮样式规范 |
| `_cards.scss` | 卡片组件样式 |
| `_forms.scss` | 表单样式 |
| `_marketing.scss` | 营销页面样式 |
| `_editor-components.scss` | 编辑器组件样式 |
| `_multimedia-components.scss` | 多媒体组件样式 |

---

## 8. Flutter 移动端模块

### 8.1 应用信息
- **包名**: `imatuproject_flutter`
- **版本**: 1.0.0+1
- **Dart SDK**: ^3.11.1
- **UI 框架**: Material Design

### 8.2 屏幕与页面

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

### 8.3 服务层

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

### 8.4 数据模型

| 模型 | 说明 |
|------|------|
| `course.dart` | 课程模型 |
| `progress.dart` | 学习进度模型 |
| `user.dart` | 用户模型 |
| `professional_instruments.dart` | 专业仪器模型（含 `.g.dart` 序列化） |

---

## 9. 区块链模块

### 9.1 架构

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 区块链平台 | Hyperledger Fabric 2.x | 企业级联盟链 |
| 共识算法 | Raft | 三组织集群 |
| 智能合约 | Go 语言链码 | 积分管理系统 |
| 身份认证 | MSP (Membership Service Provider) | 基于证书的身份管理 |

### 9.2 目录结构

| 目录 | 内容 |
|------|------|
| `blockchain/chaincode/` | Go 链码实现 |
| `blockchain/config/` | 网络配置文件 |
| `blockchain/fabric-network/` | 网络拓扑定义 |
| `blockchain/scripts/` | 部署与运维脚本 |

### 9.3 文档

- `FABRIC_DEVELOPER_DOCUMENTATION.md` — 开发者手册
- `API_REFERENCE_MANUAL.md` — 链码 API 参考
- `TECHNICAL_ARCHITECTURE_DIAGRAMS.md` — 架构图

---

## 10. 硬件与边缘计算模块

### 10.1 ESP32 TinyML 语音识别

| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| 识别准确率 | ≥85% | 95% | ✅ |
| 响应延迟 | ≤1000ms | 640ms | ✅ |
| 内存使用 | ≤520KB | 335KB (62.9%) | ✅ |
| 电池续航 | ≥8小时 | 22.7小时 | ✅ |

**技术栈**: TensorFlow Lite Micro + BLE 模型热更新 + 离线推理

### 10.2 硬件目录结构

| 目录 | 内容 |
|------|------|
| `hardware/tinyml-voice-recognition/` | TinyML 语音识别代码 |
| `hardware/fpga/` | FPGA 开发 |
| `hardware/hal/` | 硬件抽象层 |
| `hardware/matrix_lib/` | 矩阵运算库 |
| `hardware/opencl/` | OpenCL 加速 |
| `hardware/tests/` | 硬件测试 |

---

## 11. AI 与机器学习模块

### 11.1 AI 服务核心

| 服务 | 说明 |
|------|------|
| 创意激发引擎 | AI 驱动的多维度创意生成 |
| 智能推荐系统 | 基于用户画像的个性化推荐 |
| 知识图谱 | Neo4j 图数据库驱动的知识关联 |
| AI 学习助手 | LangChain 驱动的对话式辅导 |

### 11.2 OpenHydra + XEdu 集成

| 功能 | 说明 |
|------|------|
| 微课程转化 | 游戏化课程设计与转化 |
| AI 沙箱环境 | 安全的代码执行环境 |
| XEduHub AI 能力 | 教育专属 AI 能力组件 |
| 联动任务系统 | 软硬结合的综合实践（如智能温室案例） |

### 11.3 模型管理

| 功能 | 说明 |
|------|------|
| 模型基准测试 | 多模型性能对比 |
| 模型热更新 | BLE 无线推送新模型 |
| 模型优化 | 量化/剪枝/蒸馏 |
| 回测系统 | 29 个回测报告 |

---

## 12. 多角色仪表板开发

> **基于工作区规则：多角色仪表板开发实施规则**

### 12.1 Phase 1: 教师 Dashboard 增强（🔧 进行中）

| 任务 | 状态 |
|------|------|
| 注入 MultiSourceLearningService | 🔧 |
| 跨机构教学进度展示模块 | 🔧 |
| 学生学情总览模块 | 🔧 |
| 创建 TeacherService | 🔧 |
| 抽取共享仪表板组件（stats-card, progress-chart） | 🔧 |

### 12.2 Phase 2: 机构管理员 Dashboard 扩展（📋 计划中）

| 任务 | 状态 |
|------|------|
| 机构概览模块（学生数/教师数/活跃课程数） | 📋 |
| 课程运营模块（课程列表/报名统计） | 📋 |
| 教师管理模块（教师列表/课时统计） | 📋 |
| 学员管理模块（学员列表/学习进度） | 📋 |
| 创建 OrgAdminService | 📋 |

### 12.3 Phase 3: 学校管理员 Dashboard 新建（📋 计划中）

| 任务 | 状态 |
|------|------|
| 年级/班级管理模块 | 📋 |
| 校本课程管理模块（school_curriculum / school_interest） | 📋 |
| 教师工作量统计模块 | 📋 |
| 学生成长档案模块 | 📋 |
| 创建 SchoolAdminService | 📋 |

### 12.4 Phase 4: 教育局 Dashboard 新建（📋 计划中）

| 任务 | 状态 |
|------|------|
| 区域数据概览模块 | 📋 |
| 学校数据对比模块 | 📋 |
| 教学质量监控模块 | 📋 |
| 资源调配建议模块（AI 辅助） | 📋 |
| 创建 EducationBureauService | 📋 |
| 数据导出（Excel 报表） | 📋 |

---

## 13. 基础设施与部署

### 13.1 容器化

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

### 13.2 反向代理与负载均衡

| 文件 | 用途 |
|------|------|
| `nginx/nginx.conf` | Nginx 主配置 |
| `nginx/nginx-proxy.conf` | 反向代理配置 |

### 13.3 监控与告警

| 组件 | 用途 |
|------|------|
| Prometheus | 指标采集（`/metrics` 端点） |
| Grafana | 可视化面板 |
| Alertmanager | 告警管理 |
| APM Middleware | 应用性能监控 |

### 13.4 编排与 CI/CD

| 组件 | 用途 |
|------|------|
| Jenkins | CI/CD 流水线 |
| Kubernetes (k8s/) | 容器编排（7 个 YAML） |
| Husky + lint-staged | Git 提交钩子 |
| SonarQube | 代码质量平台 |

### 13.5 开发命令

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

## 14. 代码质量与测试

### 14.1 代码质量工具链

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

### 14.2 测试要求

| 指标 | 目标 | 当前 |
|------|------|------|
| 单元测试覆盖率 | ≥80% | ~80% |
| 测试用例数 | - | 61+ |
| TypeScript 编译错误 | 0 | 0 |

### 14.3 SCSS 预算规范

- 单个组件 SCSS 文件 ≤ 4KB
- 共享样式抽取到 `shared-styles/`
- CSS 自定义属性体系减少重复定义
- Smart/Dumb 组件架构分离

---

## 15. 文档体系

### 15.1 双轨制文档

| 文档类型 | 目录 | 面向受众 |
|---------|------|---------|
| 对外文档 | `docs/` | 用户、管理者、新手 |
| 技术文档 | `documentation/` | 开发者、维护者 |

### 15.2 文档分类

| 分类 | 位置 | 内容 |
|------|------|------|
| 项目概述 | `docs/01-项目概述/`, `documentation/shared/architecture/` | 项目介绍、架构设计 |
| 开发指南 | `docs/02-开发指南/`, `documentation/shared/guides/` | 快速开始、路由映射 |
| 核心技术 | `docs/03-核心技术/`, `documentation/backend/` | 区块链、AR/VR、AI |
| API 参考 | `docs/04-API参考/`, `documentation/backend/routes/` | 接口规范 |
| 部署运维 | `docs/05-部署运维/`, `documentation/deployment/` | 部署、CI/CD |
| 测试质量 | `docs/06-测试质量/`, `documentation/tests/` | 测试报告 |

### 15.3 关键文档清单

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

## 16. 开发优先级与路线图

### 16.1 当前 Sprint（2026-05）

| 优先级 | 模块 | 状态 |
|--------|------|------|
| **P0** | 教师 Dashboard Phase 1 | 🔧 开发中 |
| **P0** | 共享仪表板组件抽取 | 🔧 开发中 |
| **P1** | 机构管理员 Dashboard Phase 2 | 📋 待开始 |
| **P1** | 学校管理员 Dashboard Phase 3 | 📋 待开始 |
| **P2** | 教育局 Dashboard Phase 4 | 📋 待开始 |
| **P2** | XR 远程教学完善 | 🔧 开发中 |
| **P2** | AI 模型热更新完善 | 🔧 开发中 |
| **P2** | Vircadia Avatar 管理 | 🔧 开发中 |

### 16.2 技术债务

| 项目 | 说明 | 优先级 |
|------|------|--------|
| 数据库迁移 | SQLite → PostgreSQL（生产环境） | P1 |
| 被注释路由恢复 | federated/gesture/hardware_alert 等路由 | P2 |
| 文档版本更新 | INDEX.md 仍标注 Angular 16，实际为 21 | P2 |
| Neo4j 集成 | 知识图谱功能完善 | P3 |

### 16.3 未来规划

- 成就系统与积分排行榜
- AI 驱动的个性化学习路径推荐
- 协作学习功能增强
- 移动端（Flutter）功能对齐 Web 端
- 国际化多语言扩展
- 无障碍访问（a11y）支持

---

## 17. 附录

### 17.1 项目目录总览

```
iMato/
├── src/                    # Angular 前端源码
│   ├── app/
│   │   ├── admin/          # 管理后台
│   │   ├── components/     # 67 个可复用组件
│   │   ├── core/           # 核心服务（50 个）/守卫/模型
│   │   ├── shared/         # 共享模块
│   │   ├── styles/         # SCSS 主题
│   │   └── user/           # 用户中心（多角色）
│   └── styles/             # 全局样式
├── backend/                # FastAPI 后端
│   ├── main.py             # 主入口
│   ├── routes/             # 60 个路由
│   ├── services/           # 76 个服务
│   ├── models/             # 35+ 个数据模型
│   ├── middleware/         # 15 个中间件
│   └── config/             # 配置模块
├── flutter_app/            # Flutter 移动端
│   └── lib/
│       ├── screens/        # 8 个页面
│       ├── services/       # 10 个服务
│       ├── models/         # 4 个模型
│       └── widgets/        # 5 个组件
├── blockchain/             # Hyperledger Fabric
│   ├── chaincode/          # Go 链码
│   ├── config/             # 网络配置
│   └── scripts/            # 部署脚本
├── hardware/               # 硬件模块
│   └── tinyml-voice-recognition/
├── docker/                 # Docker 编排（20 个文件）
├── k8s/                    # Kubernetes 配置（7 个 YAML）
├── scripts/                # 工具脚本（231 个）
├── docs/                   # 对外文档
├── documentation/          # 技术文档
├── tests/                  # 测试代码
├── sdk/                    # TypeScript SDK
└── models/                 # AI 模型文件
```

### 17.2 环境要求

| 组件 | 最低版本 |
|------|---------|
| Node.js | 18+ |
| Python | 3.8 - 3.11 |
| Dart | 3.11+ |
| Docker | 20.10+ |
| PostgreSQL | 14+ (生产) |
| Redis | 6+ |

### 17.3 关键配置文件

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
> **最后更新**: 2026-05-30  
> **版本**: v4.2

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
