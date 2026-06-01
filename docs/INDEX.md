# MatuX STEM 学习平台 - 项目文档中心

欢迎来到 MatuX STEM 学习平台的完整文档中心！本文档为您提供了项目的全面技术资料和使用指南。

## 🌐 三项目生态

MatuX 是 STEM 学习生态系统的学生端项目，与以下独立项目互联互通：

| 项目 | 定位 | 技术栈 | 仓库路径 |
|------|------|--------|----------|
| **MatuX** | STEM 学习平台（学生端） | Angular 21 + FastAPI + Electron + Flutter | 本项目 |
| **OpenMTSciEd** | 开放STEM教育资源平台（课件管理） | Next.js + Neo4j | G:\OpenMTSciEd |
| **OpenMTEduInst** | STEM教育机构管理工具 | FastAPI + Angular | G:\OpenMTEduInst |

> 学生账号在三项目间互联互通，通过共享 JWT 实现单点登录。

## 📢 重要通知 - 文档结构优化（2026-03-04）

为了提供更好的开发体验，我们已对文档结构进行了优化重组：

### 🎯 双轨制文档体系

**对外文档** (`docs/`) - 本目录  
面向用户、管理者、新手，提供：
- 项目概览和快速入门
- 用户使用指南
- 演示资源和示例
- API 接口文档

**技术文档** (`documentation/`) - 新增  
面向开发者、维护者，提供：
- 模块实现细节（与代码结构对齐）
- 详细 API 规范
- 开发指南和最佳实践
- 架构设计文档

👉 **开发者请查看**: [documentation/README.md](../documentation/README.md)  
👉 **文档迁移详情**: [documentation/MIGRATION_GUIDE.md](../documentation/MIGRATION_GUIDE.md)

---

## 📚 文档分类导航

### 🏗️ 项目概览与架构
- [**项目概览**](../documentation/shared/architecture/project-overview.md) - 项目整体介绍、价值主张和功能模块（已迁移）
- [**系统架构**](../documentation/shared/architecture/system-architecture.md) - 详细的技术架构设计和组件关系（已迁移）
- [**网站地图**](SITE_MAP.md) - 完整的前端页面和 API 端点映射
- [**项目需求文档**](PROJECT_REQUIREMENTS.md) - MatuX 功能需求与模块定义
- [**项目路线图**](PROJECT_ROADMAP.md) - 开发里程碑与进度追踪
- [**桌面端 PRD**](MatuX_Desktop_PRD.md) - Electron 桌面端产品需求文档

### 🎯 开发指南
- [**快速开始**](../documentation/shared/guides/quick-start.md) - 项目搭建和环境配置指南（已迁移）
- [**前端路由详解**](FRONTEND_ROUTING.md) - Angular 路由结构和组件映射
- [**后端 API 映射**](../documentation/backend/routes/api-mapping.md) - FastAPI 端点和服务模块对照（已迁移）

### 🔧 技术专项文档
- [**AI 推荐系统**](../documentation/backend/services/recommendation-service.md) - 智能推荐算法实现（已迁移）
- [**硬件认证系统**](../documentation/backend/hardware/certification-system.md) - IoT 设备接入管理（已迁移）
- [**区块链网关**](../documentation/backend/blockchain/gateway-technical-documentation.md) - Fabric 网络接入方案（已迁移）
- [**多模态激励系统**](../documentation/shared/architecture/multimodal-incentive.md) - 语音/AR/手势激励平台（已迁移）
- [**全局技术架构**](../documentation/shared/architecture/global-technical-architecture.md) - 系统整体架构演进（已迁移）
- [**Vircadia 元宇宙集成**](../documentation/shared/architecture/vircadia/integration-plan.md) - 虚拟世界平台集成方案（已迁移）
- [**OpenHydra + XEdu AI 教育平台**](../FINAL_COMPLETION_REPORT.md) - OpenHydra 与 XEdu 深度融合
  - [微课程转化系统](../reports/O2_3_O2_4_TASK_COMPLETE_REPORT.md) - 游戏化课程设计
  - [AI 学习助手](../reports/O2_3_O2_4_TASK_COMPLETE_REPORT.md) - 对话式 AI 辅导
  - [联动任务开发](../O3.1_COMPLETE_SUMMARY.md) - 软硬结合综合实践
  - [智能温室监控系统](../docs/O3.1_LINKED_TASK_DESIGN.md) - 示范任务案例

### 🔗 跨项目集成
- [**机构模块迁移记录**](INSTITUTION_MODULE_MIGRATION.md) - 机构管理解耦至 OpenMTEduInst 的迁移文档
- [**前端集成文档**](FRONTEND_INTEGRATION_README.md) - 前端与外部项目 API 集成指南
- [**路由配置文档**](ROUTE_CONFIGURATION.md) - API 路由配置与解耦存根说明
- [**电商支付系统**](E_COMMERCE_PAYMENT_SYSTEM.md) - 支付流程和集成方案
- [**联邦学习部署**](FEDERATED_LEARNING_DEPLOYMENT_GUIDE.md) - 分布式机器学习方案

### ⚠️ 已解耦模块文档（仅供参考，新功能在对应项目开发）
- ~~[**多租户部署**](MULTITENANT_DEPLOYMENT_GUIDE.md)~~ → 已迁移至 **OpenMTEduInst**
- ~~[**许可证管理**](API_LICENSE_MANAGEMENT.md)~~ → 已迁移至 **OpenMTEduInst**
- ~~[**组织仪表板**](ORGANIZATION_DASHBOARD_GUIDE.md)~~ → 已迁移至 **OpenMTEduInst**

### 🔐 安全与认证
- [**认证系统实现**](../documentation/frontend/components/auth/system-implementation-report.md) - JWT 和 OAuth2 集成（已迁移）
- [**权限控制**](../documentation/frontend/components/auth/system-documentation.md) - 学生/家长角色权限（已迁移）
- [**AI 认证集成**](API_AUTH_INTEGRATION.md) - AI 服务的安全接入

### 📊 API文档
- [**API总览**](API_DOCUMENTATION.md) - RESTful API设计规范
- [**用户批量导入**](API_USER_BULK_IMPORT.md) - 批量数据处理接口

### 🎨 设计系统
- [**组件样式指南**](../documentation/frontend/design-system/component-guide.md) - Design System 使用手册（已迁移）
- [**样式 CI/CD**](../documentation/frontend/design-system/style-ci-cd.md) - 前端样式自动化流程（已迁移）
- [**暗色模式实现**](DARK_MODE_IMPLEMENTATION_REPORT.md) - 主题切换方案

### 🚀 部署与运维
- [**部署指南**](../documentation/deployment/guide.md) - 生产环境部署流程（已迁移）
- [**Jenkins CI/CD 配置**](../documentation/deployment/jenkins-ci-cd.md) - Jenkins 流水线完整配置指南（已迁移）
- [**许可证系统部署**](../documentation/deployment/license-system.md) - 授权系统的上线方案（已迁移）
- [**微信 QQ 集成**](WECHAT_QQ_INTEGRATION_GUIDE.md) - 第三方登录集成
- [**区块链部署**](../documentation/deployment/blockchain.md) - Fabric 网络生产部署（已迁移）
- [**联邦学习部署**](FEDERATED_LEARNING_DEPLOYMENT_GUIDE.md) - 分布式机器学习方案

### 🧪 测试与质量
- [**认证模块测试**](AUTH_MODULE_TEST_SUMMARY.md) - 安全模块测试报告
- [**支付系统测试**](PAYMENT_SYSTEM_TEST_REPORT.md) - 电商功能验证
- [**用户导入测试**](USER_BULK_IMPORT_GUIDE.md) - 数据迁移测试

## 🗺️ 快速查找指引

### 我是...
- **新开发者** → 从 [快速开始](QUICK_START.md) 和 [项目概览](PROJECT_OVERVIEW.md) 开始
- **前端工程师** → 查看 [前端路由](FRONTEND_ROUTING.md) 和 [设计系统](component-style-guide.md)
- **后端工程师** → 阅读 [后端API映射](BACKEND_API_MAPPING.md) 和 [系统架构](SYSTEM_ARCHITECTURE.md)
- **AI 工程师** → 查看 [多模态激励系统](MULTIMODAL_INCENTIVE_SYSTEM_TECHNICAL_DOC.md)、[OpenHydra+XEdu 集成](../FINAL_COMPLETION_REPORT.md) 和相关 AI 文档
- **STEM 教育开发者** → 查看 [OpenHydra 集成计划](../OPENHYDRA_XEDU_INTEGRATION_PLAN.md)、[微课程转化系统](../reports/O2_3_O2_4_TASK_COMPLETE_REPORT.md)
- **桌面端开发者** → 查看 [桌面端 PRD](MatuX_Desktop_PRD.md) 和 Electron 相关文档
- **移动端开发者** → 查看 Flutter 移动端相关文档
- **产品经理** → 参考 [项目需求文档](PROJECT_REQUIREMENTS.md) 和 [项目路线图](PROJECT_ROADMAP.md)
- **架构师** → 阅读 [全局技术架构](GLOBAL_TECHNICAL_ARCHITECTURE.md) 和 [系统架构](SYSTEM_ARCHITECTURE.md)
- **运维工程师** → 查看 [部署指南](DEPLOYMENT_GUIDE.md) 和相关运维文档
- **测试工程师** → 关注各模块的测试报告和指南

### 我想了解...
- **技术架构** → [系统架构文档](SYSTEM_ARCHITECTURE.md)
- **API 接口** → [后端API映射](BACKEND_API_MAPPING.md)
- **页面结构** → [网站地图](SITE_MAP.md)
- **开发环境** → [快速开始](QUICK_START.md)
- **安全机制** → [认证系统文档](AUTH_SYSTEM_DOCUMENTATION.md)
- **部署流程** → [部署指南](DEPLOYMENT_GUIDE.md)
- **CI/CD 配置** → [Jenkins 配置指南](JENKINS_CI_CD_CONFIGURATION.md)
- **区块链技术** → [Fabric 开发者文档](../blockchain/FABRIC_DEVELOPER_DOCUMENTATION.md)
- **链码开发** → [API参考手册](../blockchain/API_REFERENCE_MANUAL.md)
- **激励系统** → [多模态激励文档](MULTIMODAL_INCENTIVE_SYSTEM_TECHNICAL_DOC.md)
- **整体架构** → [全局技术架构](GLOBAL_TECHNICAL_ARCHITECTURE.md)
- **元宇宙集成** → [Vircadia 集成方案](VIRCADIA_INTEGRATION_PLAN.md)
- **AI 教育平台** → [OpenHydra+XEdu 完成报告](../FINAL_COMPLETION_REPORT.md)（新增）
- **微课程设计** → [游戏化转化系统](../reports/O2_3_O2_4_TASK_COMPLETE_REPORT.md)（新增）
- **AI 学习助手** → [对话式 AI 辅导](../reports/O2_3_O2_4_TASK_COMPLETE_REPORT.md)（新增）
- **联动任务** → [软硬结合实践](../O3.1_COMPLETE_SUMMARY.md)（新增）

## 📁 演示资源

### HTML演示页面
- [`auth-demo.html`](auth-demo.html) - 认证系统功能演示
- [`auth-interactive-demo.html`](auth-interactive-demo.html) - 交互式认证流程
- [`dashboard-demo.html`](dashboard-demo.html) - 仪表板界面展示
- [`playground.html`](playground.html) - Design System组件游乐场
- [`simple-playground.html`](simple-playground.html) - 精简版组件演示

### 代码示例
- [Arduino测试代码](arduino_test_sketch.ino) - 硬件认证示例
- [用户导入模板](user_import_template.csv) - 批量数据格式示例

## 🔧 开发工具

### 本地开发命令
```bash
# 前端开发
npm start                    # 启动开发服务器
npm run build               # 生产构建
npm run lint:css           # CSS代码检查

# 后端开发
cd backend
python main.py             # 启动后端服务
uvicorn main:app --reload  # 热重载模式

# 文档相关
npm run docs:styles        # 生成样式文档
npm run docs:serve         # 启动文档服务器
```

### 测试命令
```bash
# 运行测试
python -m pytest backend/tests/     # 后端测试
ng test                            # 前端单元测试
npm run e2e                       # 端到端测试
```

## 📊 项目统计信息

### 技术栈概览
- **前端**: Angular 21 + TypeScript + SCSS
- **后端**: FastAPI + Python 3.9
- **数据库**: PostgreSQL + Redis
- **桌面端**: Electron 28
- **移动端**: Flutter
- **部署**: Docker + Nginx

### 文档完整性
- ✅ 项目概览文档
- ✅ 系统架构文档  
- ✅ 前后端路由/API映射
- ✅ 专项技术文档
- ✅ 部署运维指南
- ✅ Jenkins CI/CD配置
- ✅ 测试质量报告
- ✅ 区块链技术文档
- ✅ API参考手册
- ✅ 架构图谱文档
- ✅ 多模态激励系统文档
- ✅ 全局技术架构文档

## 🔄 文档更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-02-26 | 初始文档集合创建，包含完整的技术文档体系 |
| v1.1 | 2026-03-01 | 新增多模态激励系统和全局技术架构文档 |
| v2.0 | 2026-05-31 | 模块解耦更新：添加三项目生态导航，标记已解耦模块文档 |

## 📞 技术支持

如需技术支持或发现文档问题，请联系：
- 技术负责人: [待填写]
- 文档维护: [待填写]
- 问题反馈: [待填写]

---
*MatuX STEM 学习平台文档中心 | 版本 v2.0 | 最后更新 2026年5月*
