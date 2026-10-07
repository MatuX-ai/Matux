# 项目概述

## 项目简介

**MatuX** 是一个面向学生的 STEM 学习工具，由 **MatuX Lab** 团队打造。平台融合 AI 编程教育、虚拟实验室、3D 元件库、多模态激励等前沿技术，为学生提供桌面端（Electron）与移动端（Flutter）双端沉浸式学习体验。

> **定位**: STEM 学习工具（学生学习端）。课件管理已解耦至 OpenMTSciEd，机构管理已解耦至 OpenMTEduInst，MatuX 通过 API 与其互联互通。

## 三项目生态

MatuX 与以下独立开源项目互联互通，共同构成完整的 STEM 教育解决方案：

| 项目 | 定位 | 技术栈 | 仓库 |
|------|------|--------|------|
| **MatuX** | STEM 学习工具（学生端） | Angular + FastAPI + Electron + Flutter | 本仓库 |
| **OpenMTSciEd** | 开放 STEM 教育资源平台（课件管理） | Next.js + Neo4j | `G:\OpenMTSciEd` |
| **OpenMTEduInst** | STEM 教育机构管理工具（机构管理） | Angular + FastAPI | `G:\OpenMTEduInst` |

## 核心价值

- **学生为本**: 仅有学生一个主角色，专注学习体验
- **STEM 专注**: 虚拟实验室（电路仿真/AR/数字孪生）、硬件实践（ESP32 TinyML/BLE 热更新）、3D 电子元件库
- **AI 驱动**: 多模型 AI 代码生成、个性化教师、智能推荐、学习画像
- **全平台适配**: 桌面端（Electron 编程+实验主力）、移动端（Flutter 课程学习+日常练习）、离线模式
- **沉浸式体验**: AR/VR 教学、Vircadia 元宇宙集成、多模态激励（语音/AR/手势）

## 技术亮点

### 边缘计算与本地 AI
- ESP32 TinyML 语音识别系统（95% 准确率，640ms 延迟）
- 基于 TensorFlow Lite Micro 的端侧推理
- BLE 模型热更新能力

### 区块链技术
- Hyperledger Fabric 企业级网络（三组织 Raft 共识）
- 智能合约积分管理系统
- 完善的权限控制体系

### AI 模型热更新
- 后端动态加载/卸载 TensorFlow/ONNX/PyTorch 模型
- A/B 测试与资源监控
- 边缘端无线推送新模型权重

### 元宇宙集成
- Vircadia 虚拟世界平台集成方案
- 去中心化联邦服务器架构
- 百人同服的实时交互能力
- 虚拟教室、虚拟实验室、Avatar 换装

### 防作弊测验与离线学习
- 随机抽题、计时、屏幕切换检测、剪贴板禁用
- IndexedDB v3 大容量离线存储 + Service Worker 缓存策略
- 冲突解决（local_wins/remote_wins/merged）+ 指数退避重试

## 团队与许可

- **团队**: MatuX Lab
- **许可**: GPL-3.0

## 文档导航

- [架构设计](架构设计.md) - 系统整体架构和技术选型
- [技术栈说明](技术栈说明.md) - 详细的技术组件介绍
- [发展历程](发展历程.md) - 项目里程碑和演进路线
- [项目文档中心](../INDEX.md) - 完整文档导航入口
- [技术文档中心](../../documentation/README.md) - 面向开发者的详细技术文档

---
*MatuX STEM 学习工具 | 维护团队: MatuX Lab | 版本 v2.0*
