# 路由配置管理指南

## 概述

本项目采用配置化的方式管理可选功能模块，通过环境变量控制各个功能模块的启用/禁用状态。

> **模块解耦说明**: 课件管理模块已解耦至 OpenMTSciEd，机构管理模块已解耦至 OpenMTEduInst。以下标记为「已解耦」的模块仅保留 API 存根用于兼容性，新功能请在对应项目中开发。

## 核心功能模块 (默认启用)

以下模块始终启用，无需额外配置:

- ✅ AI 服务
- ✅ 认证系统
- ✅ 推荐系统
- ✅ 支付系统
- ✅ 订阅系统
- ✅ 硬件认证
- ✅ 课程管理
- ✅ 课程版本控制
- ✅ 协作编辑
- ✅ 多媒体资源
- ✅ 创意引擎
- ✅ AR 实验室
- ✅ 模型基准测试
- ✅ 区块链网关
- ✅ 学习行为特征
- ✅ 手势识别系统 (gesture_recognition)
- ✅ AR 奖励系统
- ✅ AI 教育学习进度
- ✅ AI 个性化教师
- ✅ 向量知识库 (RAG)
- ✅ 本地知识图谱

## 已解耦模块 (保留兼容存根)

> ⚠️ 以下模块已解耦至独立项目，MatuX 仅保留 API 存根用于兼容性。新功能请在对应项目中开发，避免重复开发。

| 模块 | 路由文件 | 目标项目 | 说明 |
|------|----------|----------|------|
| 课件管理 | `material_routes.py` | **OpenMTSciEd** | 教程/课件/知识图谱 → localhost:3000/api/v1 |
| 机构管理 | `educational_institution_routes.py` | **OpenMTEduInst** | 机构/教师/排课/设备管理 |
| 多租户配置 | `tenant_config_routes.py` | **OpenMTEduInst** | SaaS 多租户权限控制 |
| 许可证管理 | (集成在license模块) | **OpenMTEduInst** | 软件授权方案 |
| 权限管理 | `permission_routes.py` | **OpenMTEduInst** | 多租户权限体系 |

## 外部项目 API 集成

MatuX 通过 HTTP API 调用以下外部项目服务：

### OpenMTSciEd (课件资源)
- **端点**: `localhost:3000/api/v1`
- **功能**: 教程、课件、知识图谱、硬件项目资源
- **环境变量**: `OPENMTSCIED_API_URL=http://localhost:3000/api/v1`

### OpenMTEduInst (机构管理)
- **端点**: 独立部署（通过环境变量配置）
- **功能**: 机构、教师、排课、校区、设备管理
- **环境变量**: `OPENMTEDUINST_API_URL=http://localhost:8001/api/v1`

## 可选功能模块 (需配置启用)

以下模块默认禁用，可通过环境变量启用:

### 1. AR/VR 课程内容管理

**环境变量**: `ENABLE_AR_VR_ROUTES=True`

**功能描述**: 
- AR/VR 课程内容管理、传感器数据传输和交互控制
- 支持 Unity WebGL 构建上传
- 提供 WebSocket 实时数据流

**依赖**: 
- `models/ar_vr_content.py`
- `services/ar_vr_content_service.py`
- `services/ar_physics_service.py`

**注意**: 该模块与 `ar_lab_routes` 功能有部分重叠，请根据需求选择使用

---

### 2. AR/VR Mock服务

**环境变量**: `ENABLE_AR_VR_MOCK_ROUTES=True`

**功能描述**: 
- 提供 AR/VR 环境的 Mock 测试服务
- 支持多种测试场景模拟 (理想条件、硬件故障、网络问题等)
- 性能基准测试工具

**依赖**: 
- `services/ar_vr_mock_service.py`

**使用场景**: 开发和测试环境，无需真实硬件即可测试 AR/VR 功能

---

### 3. 数字孪生实验室

**环境变量**: `ENABLE_DIGITAL_TWIN_ROUTES=True`

**功能描述**: 
- 物理状态同步和多人协作接口
- 电路状态实时更新
- 设备状态管理
- WebSocket 实时通信

**依赖**: 
- Redis (用于状态缓存)
- WebSocket 支持

**注意**: 需要配置 Redis 服务

---

### 4. 联邦学习 API

**环境变量**: `ENABLE_FEDERATED_ROUTES=True`

**功能描述**: 
- 联邦学习训练管理
- 参与者注册和管理
- 集群状态监控
- 性能指标追踪

**依赖**: 
- `services/federated_service.py`
- `fl_models.py`

**使用场景**: 分布式机器学习训练场景

---

### 5. AI 模型热更新

**环境变量**: `ENABLE_MODEL_UPDATE_ROUTES=True`

**功能描述**: 
- 模型版本管理
- 模型文件上传和压缩
- BLE 分块传输支持
- 模型完整性验证

**依赖**: 
- `services/model_update_service.py`
- `models/model_version.py`

**注意**: 需要充足的磁盘空间存储模型文件

---

### 6. XR 手势识别

**环境变量**: `ENABLE_XR_GESTURE_ROUTES=True`

**功能描述**: 
- AR 手势识别服务
- 手势命令映射
- WebSocket 实时手势事件推送

**依赖**: 
- `xr_modules/ar_gesture_recognition/`

**⚠️ 重要提示**: 该模块与已启用的 `gesture_recognition.py` 功能重复

**建议**: 
- 优先使用 `gesture_recognition.py` (已在 main.py 中注册)
- 仅在需要对比测试时启用此模块

---

## 配置方法

### 开发环境

1. 复制环境变量示例文件:
```bash
cd backend
cp .env.example .env
```

2. 编辑 `.env` 文件，设置需要启用的功能:
```bash
# 可选路由配置
ENABLE_AR_VR_ROUTES=False
ENABLE_AR_VR_MOCK_ROUTES=True  # 启用 Mock服务用于测试
ENABLE_DIGITAL_TWIN_ROUTES=False
ENABLE_FEDERATED_ROUTES=False
ENABLE_MODEL_UPDATE_ROUTES=False
ENABLE_XR_GESTURE_ROUTES=False
```

3. 重启应用，配置生效

### 生产环境

通过 Docker 环境变量或部署平台配置:

```yaml
# docker-compose.yml
services:
  backend:
    environment:
      - ENABLE_AR_VR_ROUTES=False
      - ENABLE_AR_VR_MOCK_ROUTES=False
      - ENABLE_DIGITAL_TWIN_ROUTES=True
      - ENABLE_FEDERATED_ROUTES=False
      - ENABLE_MODEL_UPDATE_ROUTES=False
      - ENABLE_XR_GESTURE_ROUTES=False
```

## 验证配置

启动应用后，访问根路径查看已激活的功能:

```bash
curl http://localhost:8000/
```

响应示例:
```json
{
  "message": "Welcome to MatuX STEM Learning Platform",
  "version": "1.0.0",
  "status": "healthy",
  "core_features": [...],
  "optional_features": [
    "AR/VR Mock服务 (已启用)",
    "数字孪生实验室 (已启用)"
  ],
  "configuration_note": "可选功能通过环境变量控制，详见.env.example"
}
```

## 日志监控

应用启动时会记录哪些路由被激活:

```
✅ AR/VR Mock服务路由已启用
✅ 数字孪生实验室路由已启用
⚠️ XR 手势识别路由与 gesture_recognition 功能重复，请确认是否需要启用
```

## 最佳实践

1. **最小化启用**: 生产环境只启用实际需要的功能模块
2. **资源隔离**: 某些模块 (如数字孪生) 需要额外资源 (Redis)，确保资源充足
3. **避免冲突**: 不要同时启用 `XR_GESTURE_ROUTES` 和已有的 `gesture_recognition`
4. **测试验证**: 启用新模块后，通过 API 文档 (`/docs`) 验证端点正常
5. **性能监控**: 关注启用多个模块后的系统性能表现

## 故障排查

### 模块未生效

检查项:
1. 环境变量是否正确设置
2. 应用是否重启
3. 日志中是否有对应的启用信息
4. 依赖服务是否运行 (如 Redis)

### 端口冲突

某些模块可能使用特殊端口，检查防火墙和端口占用情况

### 依赖缺失

确保所有必要的 Python 包和系统服务已安装

## 历史清理记录

### 已删除的废弃组件

- ❌ `dark-mode-demo` 组件 (演示性质，非生产功能)
- ❌ `simple-dashboard` 模块 (已被 `minimal-dashboard` 替代)
- ❌ `enhanced-admin-dashboard` 组件 (旧版本仪表板)
- ❌ `xr_gesture_routes.py` (与 `gesture_recognition.py` 功能重复)

这些文件已从代码库中移除，如需使用可从 Git 历史记录恢复。

## 相关文档

- [API 文档](http://localhost:8000/docs)
- [环境配置指南](../backend/.env.example)
- [部署手册](./DEPLOYMENT.md)

---

最后更新：2026-03-02
