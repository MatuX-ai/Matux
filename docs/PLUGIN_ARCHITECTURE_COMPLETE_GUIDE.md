# 插件化模块交付架构 - 完整实施指南

> **项目**: iMato 学习端插件化架构  
> **版本**: 1.0.0  
> **完成日期**: 2026-06-06  
> **状态**: Phase 1-3 完成，Phase 4-5 待开始  
> **总代码量**: ~10,023 行

---

## 📋 目录

1. [架构概述](#架构概述)
2. [Phase 1: 设备评估框架](#phase-1-设备评估框架)
3. [Phase 2: 插件包格式与管理器](#phase-2-插件包格式与管理器)
4. [Phase 3: 插件商店 UI](#phase-3-插件商店-ui)
5. [核心架构设计](#核心架构设计)
6. [开发指南](#开发指南)
7. [API 参考](#api-参考)
8. [部署与运维](#部署与运维)
9. [未来规划](#未来规划)

---

## 架构概述

### 设计理念

iMato 插件化模块交付架构基于**"设备感知 + 按需下载 + 动态加载"**的核心理念：

1. **设备感知**: 首次启动自动评估设备能力（CPU/内存/GPU/存储/网络/外设）
2. **按需下载**: 根据设备等级推荐兼容插件，用户按需下载安装
3. **动态加载**: 插件安装后动态注册路由和服务，无需重启应用
4. **分级管理**: 4 层设备等级（Basic/Standard/Advanced/Professional）+ 4 层插件 Tier（A/B/C/D）

### 核心价值

- ✅ **主包瘦身**: 基础安装包 < 100MB，可选功能通过插件补充
- ✅ **设备适配**: 低端设备不卡顿，高端设备充分发挥能力
- ✅ **生态扩展**: 第三方开发者可开发插件，丰富功能生态
- ✅ **热更新**: 插件独立更新，不影响主应用
- ✅ **按需付费**: 用户仅下载需要的功能模块

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Angular)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  插件商店 UI  │  │ 设备评估报告 │  │ 插件管理面板 │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│         └──────────────────┼──────────────────┘          │
│                            │                             │
│              window.pluginAPI (IPC)                      │
└────────────────────────────┼─────────────────────────────┘
                             │
┌────────────────────────────┼─────────────────────────────┐
│              Electron 主进程                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 设备评估引擎  │  │ 插件安装器   │  │ 插件下载器   │  │
│  │device-profiler│  │plugin-installer│ │plugin-downloader│ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│  ┌──────┴──────────────────┴──────────────────┴───────┐  │
│  │              插件注册表 (plugin-registry)            │  │
│  └──────────────────────────┬─────────────────────────┘  │
│                             │                             │
│  文件系统: ~/.imato/plugins/ + plugin-data/              │
└─────────────────────────────┼─────────────────────────────┘
                              │
┌─────────────────────────────┼─────────────────────────────┐
│              后端 (FastAPI)                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ 设备评估 API │  │ 插件管理 API │  │ 插件管理器   │  │
│  │/api/v1/device│  │/api/v1/plugins│ │plugin_manager │  │
│  └──────────────┘  └──────────────┘  └──────┬───────┘  │
│                                              │          │
│                          动态加载插件路由和服务           │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1: 设备评估框架

### 完成内容

| 模块 | 文件 | 行数 | 功能 |
|------|------|------|------|
| 设备评估引擎 | `electron/device-profiler.js` | 952 | 硬件/软件检测 + 评级算法 |
| IPC 集成 | `electron/main.js` | +92 | 3 个 IPC handlers + 启动集成 |
| Preload API | `electron/preload.js` | +104 | window.pluginAPI 命名空间 |
| 前端组件 | `src/app/shared/components/device-profile/` | 770 | 设备评估报告展示 |
| TypeScript 类型 | `src/app/core/models/electron-api.model.ts` | +98 | PluginAPI/DeviceProfile 等 |
| 后端 API | `backend/routes/device_profile_routes.py` | 159 | 3 个端点 |
| 模块注册 | `backend/core/module_registry.py` | +13 | Tier 0 核心模块 |
| 单元测试 | `electron/test-device-profiler.js` | 159 | 评级算法测试 |

**总计**: ~2,500 行代码

### 核心功能

#### 1. 设备评级系统

4 级评级，基于 6 维度加权评分：

| 等级 | 最低评分 | 典型硬件 | 支持 Tier |
|------|---------|---------|----------|
| **Basic** | 0+ | 2核/4GB/集显 | Tier A |
| **Standard** | 35+ | 4核/8GB/集显 | Tier A-B |
| **Advanced** | 60+ | 6核/16GB/独显 2GB | Tier A-C |
| **Professional** | 80+ | 8核/32GB/独显 6GB+CUDA | Tier A-D |

#### 2. 评分算法

```javascript
// 6 维度加权
总分 = CPU 20% + 内存 25% + GPU 25% + 存储 15% + 网络 5% + 外设 10%

// CPU 评分
cpuScore = min(100, (benchmarkScore / 1000) * 100)

// 内存评分
4GB=20, 8GB=40, 16GB=70, 32GB=90, 64GB=100

// GPU 评分
独显 + VRAM + CUDA 加分
2GB=50, 4GB=70, 6GB=85, 8GB=100, CUDA +10

// 存储评分
10GB=20, 50GB=50, 100GB=70, 500GB=90, 1TB=100
```

#### 3. 检测维度

**硬件**:
- CPU（核心数/频率/基准分数）
- 内存（总容量/可用量）
- GPU（独显/VRAM/CUDA 支持）
- 存储（总容量/可用量/类型 SSD/HDD）
- 网络（带宽/延迟）
- 外设（摄像头/麦克风/扬声器）
- 显示器（分辨率/刷新率）

**软件**:
- 操作系统（平台/版本）
- 运行时（Node.js/Python 版本）
- 容器（Docker 可用性）
- 缓存（Redis 可用性）
- CLI 工具（git/npm/pip 等）

#### 4. API 端点

```
GET  /api/v1/device/profile              # 获取设备评估报告
POST /api/v1/device/reassess             # 重新评估设备
GET  /api/v1/device/compatibility/{id}   # 检查插件兼容性
```

#### 5. IPC 通道

```javascript
// Electron 主进程
ipcMain.handle('plugin:device-profile', ...)    // 获取设备报告
ipcMain.handle('plugin:reassess-device', ...)   // 重新评估
ipcMain.handle('plugin:assess', ...)            // 评估插件兼容性

// 渲染进程
window.pluginAPI.getDeviceProfile()
window.pluginAPI.reassessDevice()
window.pluginAPI.assessPlugin(pluginId)
```

### 使用示例

```typescript
// 前端获取设备评估报告
const result = await window.pluginAPI.getDeviceProfile();

if (result.success && result.profile) {
  console.log(`设备等级: ${result.profile.assessment.deviceClass}`);
  console.log(`设备评分: ${result.profile.assessment.score}`);
  console.log(`兼容插件: ${result.profile.assessment.compatiblePluginTiers}`);
}
```

---

## Phase 2: 插件包格式与管理器

### 完成内容

| 模块 | 文件 | 行数 | 功能 |
|------|------|------|------|
| 格式规范 | `docs/MXP_FORMAT_SPEC.md` | 1,368 | .mxp 包格式完整规范 |
| 打包工具 | `scripts/build-plugin.ts` | 727 | CLI 验证 + 打包 + 签名 |
| 安装器 | `electron/plugin-installer.js` | 936 | 12 步安装流程 |
| 下载器 | `electron/plugin-downloader.js` | 716 | 断点续传 + 队列 |
| 后端管理器 | `backend/core/plugin_manager.py` | 737 | 动态模块加载 |
| 后端 API | `backend/routes/plugin_routes.py` | 721 | 10 个 RESTful 端点 |
| 注册表 | `electron/plugin-registry.js` | 644 | 元数据管理 |
| IPC 集成 | `electron/main.js` | +41 | 10 个 IPC handlers |

**总计**: ~5,890 行代码

### 核心功能

#### 1. .mxp 插件包格式

**目录结构**:
```
plugin-id-1.0.0-all.mxp (ZIP)
├── manifest.json              # 插件元数据
├── README.md                  # 说明文档
├── icon.png                   # 图标 (256x256)
├── backend/                   # 后端代码
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── tasks/
│   ├── migrations/
│   ├── hooks/                 # 生命周期钩子
│   └── requirements.txt
├── frontend/                  # 前端代码
│   ├── components/
│   ├── services/
│   ├── models/
│   └── module.ts
├── electron/                  # Electron 代码
│   ├── main.js
│   └── preload.js
├── python-deps/               # Python 依赖
│   └── wheels/
├── resources/                 # 资源文件
└── signatures/                # 数字签名
```

**Manifest 核心字段**:
```json
{
  "manifestVersion": "1.0",
  "id": "ai-coding-assistant",
  "name": "AI 编程助手",
  "version": "1.2.0",
  "deviceCompatibility": {
    "compatibleTiers": ["tier-b", "tier-c", "tier-d"],
    "minDeviceScore": 35,
    "requiredHardware": {
      "minMemoryMB": 8192,
      "requireGPU": false
    }
  },
  "entryPoints": {
    "backend": {
      "routes": [...],
      "services": [...],
      "hooks": {...}
    },
    "frontend": {
      "module": "frontend/module.ts",
      "menuItems": [...]
    },
    "electron": {
      "main": "electron/main.js",
      "ipcHandlers": [...]
    }
  },
  "permissions": ["network:external", "database:read"],
  "dependencies": {
    "python": ["openai>=1.0.0"]
  }
}
```

#### 2. 插件打包工具

```bash
# 基本打包
npm run build-plugin ./plugins/ai-coding-assistant

# 指定平台和输出
npm run build-plugin ./plugins/ar-lab -o ./releases -p win32-x64

# 带签名
npm run build-plugin ./plugins/ml-studio --sign --key ./keys/private.pem

# 仅验证
npm run build-plugin ./plugins/my-plugin --validate
```

#### 3. 插件安装流程（12 步）

```
1. 检查文件存在性
2. 解压 .mxp 包
3. 读取 manifest.json
4. 检查是否已安装
5. 验证数字签名（可选）
6. 检查设备兼容性
   - Tier 等级
   - 最低评分
   - 硬件要求
   - 软件环境
7. 安装文件到 ~/.imato/plugins/
8. 创建数据目录 ~/.imato/plugin-data/
9. 安装 Python 依赖（wheel + requirements.txt）
10. 执行 onInstall 钩子（60s 超时）
11. 注册到 ModuleRegistry
12. 保存安装信息
```

**回滚机制**: 任何步骤失败自动回滚已安装的文件。

#### 4. 插件下载器

**核心特性**:
- HTTP/HTTPS 支持 + 自动重定向
- 断点续传（HTTP Range 请求）
- 下载队列（最大并发 3 个）
- 速度限制（bytes/sec）
- 实时进度（每 0.5 秒更新）
- SHA-256 完整性验证
- 缓存管理（7 天过期）

**IPC 通道**:
```javascript
window.pluginAPI.downloadPlugin(pluginId, version, url)
window.pluginAPI.cancelDownload(pluginId, version)
window.pluginAPI.pauseDownload(pluginId, version)
window.pluginAPI.resumeDownload(pluginId, version)
```

#### 5. 后端插件管理器

**动态模块加载**:
```python
# 扫描已安装插件
await plugin_manager.scan_installed_plugins()

# 解析依赖关系（拓扑排序）
plugin_manager._resolve_dependencies()

# 加载所有插件
await plugin_manager.load_all_plugins()

# 动态加载单个插件
result = await plugin_manager.load_plugin("ai-coding-assistant")

# 卸载插件
result = await plugin_manager.unload_plugin("ai-coding-assistant")
```

**路由注册**:
```python
# 从 manifest 读取路由配置
for route_config in plugin.routes:
    router = await plugin_manager._load_route_module(plugin, route_config)
    app.include_router(router, prefix=prefix, tags=tags)
```

#### 6. 后端 API 端点

```
GET    /api/v1/plugins                      # 插件列表
GET    /api/v1/plugins/{id}                 # 插件详情
POST   /api/v1/plugins/install              # 安装插件
POST   /api/v1/plugins/uninstall            # 卸载插件
POST   /api/v1/plugins/toggle               # 启用/禁用
POST   /api/v1/plugins/update               # 更新插件
GET    /api/v1/plugins/{id}/compatibility   # 兼容性检查
GET    /api/v1/plugins/search?q=...         # 搜索插件
GET    /api/v1/plugins/stats                # 统计信息
POST   /api/v1/plugins/reload               # 重新加载（开发）
```

#### 7. 本地插件注册表

**存储位置**: `~/.imato/plugin-registry.json`

**核心功能**:
- 插件元数据管理
- 依赖图构建
- 搜索和过滤
- 状态跟踪
- 配置管理
- 备份和恢复

---

## Phase 3: 插件商店 UI

### 完成内容

| 模块 | 文件 | 行数 | 功能 |
|------|------|------|------|
| 服务层 | `src/app/core/services/plugin-store.service.ts` | 458 | HTTP + IPC + 进度跟踪 |
| 商店主页 | `plugin-store.component.ts/html/scss` | 709 | 搜索/过滤/分类/标签页 |
| 插件卡片 | `plugin-card.component.ts/html/scss` | 466 | 信息展示/安装进度/操作 |

**总计**: ~1,633 行代码

### 核心功能

#### 1. 插件商店主页面

**功能**:
- 实时搜索（300ms 防抖）
- 分类过滤（10 个分类）
- 兼容性过滤
- 标签页（全部/已安装/兼容设备）
- 统计信息（可用/已安装/已启用）
- 响应式网格布局

**UI 特性**:
- Material Design 3 风格
- CSS Grid `auto-fill` + `minmax(320px, 1fr)`
- 暗色模式支持（CSS 变量）
- Hover 效果（阴影 + 上移）
- 加载/错误/空状态

#### 2. 插件卡片组件

**信息展示**:
- 插件图标（图片/占位符）
- 名称和作者
- 描述（2 行截断）
- 版本号
- 分类标签
- 兼容性标识（绿/红/灰）
- 状态徽章（已安装/已启用/已禁用）

**交互功能**:
- 查看详情按钮
- 安装按钮（带进度条）
- 管理按钮（已安装）
- 不兼容提示（禁用）

**进度跟踪**:
- 实时进度条
- 安装中旋转动画
- Snackbar 通知

#### 3. 插件服务层

**HTTP API**:
```typescript
getPlugins(options)           // 获取插件列表
getPluginDetail(pluginId)     // 获取插件详情
searchPlugins(query, options) // 搜索插件
getPluginStats()              // 获取统计信息
checkCompatibility(pluginId)  // 检查兼容性
```

**Electron IPC**:
```typescript
installPlugin(pluginId, version)    // 安装插件
uninstallPlugin(pluginId, keepData) // 卸载插件
togglePlugin(pluginId, enabled)     // 启用/禁用
downloadPlugin(pluginId, version, url) // 下载插件
```

**进度跟踪**:
```typescript
getDownloadProgress(pluginId, version) // 下载进度 Observable
getInstallProgress(pluginId)           // 安装进度 Observable
```

---

## 核心架构设计

### 数据流

```
用户操作（点击安装）
  ↓
前端插件卡片组件
  ↓ 调用 pluginService.installPlugin()
插件服务层
  ↓ 调用 window.pluginAPI.installPlugin()
Electron IPC (preload.js)
  ↓ ipcMain.handle('plugin:install')
Electron 主进程 (plugin-installer.js)
  ├─ 解压 .mxp 包
  ├─ 验证 manifest 和签名
  ├─ 检查设备兼容性
  ├─ 安装文件
  ├─ 安装 Python 依赖
  ├─ 执行 onInstall 钩子
  ├─ 注册到 plugin-registry.js
  └─ 发送进度事件
  ↓ ipcRenderer.send('plugin:install-progress')
前端监听进度
  ↓ pluginService.getInstallProgress()
实时更新 UI（进度条/状态）
```

### 设备兼容性检查流程

```
1. 读取 manifest.json → deviceCompatibility
2. 加载设备评估报告（~/.imato/device-profile.json）
3. 检查 compatibleTiers 是否包含当前设备等级
   - Basic → tier-a
   - Standard → tier-a, tier-b
   - Advanced → tier-a, tier-b, tier-c
   - Professional → tier-a, tier-b, tier-c, tier-d
4. 检查 minDeviceScore ≤ 当前设备评分
5. 检查 requiredHardware
   - minMemoryMB ≤ 实际内存
   - minStorageMB ≤ 可用存储
   - requireGPU → 检查独显
   - minVRAM_MB ≤ 实际 VRAM
   - requireCUDA → 检查 CUDA
   - requireDocker → 检查 Docker
   - requireRedis → 检查 Redis
6. 全部通过 → compatible = true
   任一失败 → compatible = false, 生成错误信息
```

### 插件生命周期

```
开发阶段:
  开发者编写代码 → 创建 manifest.json
  ↓
  npm run build-plugin → 生成 .mxp 包
  ↓
  上传到插件商店服务器

安装阶段:
  用户浏览插件商店 → 搜索/过滤
  ↓
  查看插件详情 → 检查兼容性
  ↓
  点击安装 → 下载 .mxp（断点续传）
  ↓
  解压 → 验证签名 → 检查兼容性
  ↓
  安装文件 → 安装依赖 → 执行钩子
  ↓
  注册到注册表 → 动态加载路由/服务
  ↓
  插件可用

运行阶段:
  前端路由 → 加载插件组件
  后端 API → 调用插件路由
  Electron IPC → 调用插件功能

卸载阶段:
  用户点击卸载 → 执行 onUninstall 钩子
  ↓
  取消注册 → 删除文件 → 删除数据（可选）
  ↓
  从注册表移除
```

### 目录结构

```
~/.imato/ (userData)
├── device-profile.json              # 设备评估报告
├── plugin-registry.json             # 插件注册表
├── plugin-registry.backup.json      # 注册表备份
├── plugins/                         # 插件安装目录
│   ├── ai-coding-assistant/        # 插件文件
│   │   ├── manifest.json
│   │   ├── backend/
│   │   │   ├── routes/
│   │   │   ├── services/
│   │   │   └── requirements.txt
│   │   ├── frontend/
│   │   │   ├── components/
│   │   │   └── module.ts
│   │   └── electron/
│   │       └── main.js
│   └── ai-coding-assistant.json    # 安装信息
├── plugin-data/                     # 插件数据目录
│   └── ai-coding-assistant/
│       ├── config.json
│       └── cache/
└── plugin-downloads/                # 下载缓存
    └── ai-coding-assistant-1.2.0-all.mxp
```

---

## 开发指南

### 创建新插件

#### 1. 初始化插件目录

```bash
mkdir my-plugin
cd my-plugin

# 创建目录结构
mkdir -p backend/routes backend/services frontend/components electron
```

#### 2. 创建 manifest.json

```json
{
  "manifestVersion": "1.0",
  "id": "my-plugin",
  "name": "我的插件",
  "version": "1.0.0",
  "description": "插件描述",
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "license": "MIT",
  "deviceCompatibility": {
    "compatibleTiers": ["tier-a", "tier-b", "tier-c", "tier-d"],
    "minDeviceScore": 0
  },
  "entryPoints": {
    "backend": {
      "routes": [{
        "file": "backend/routes/my_routes.py",
        "prefix": "/api/v1/my-plugin",
        "tags": ["我的插件"],
        "tier": 2,
        "lazyLoad": true
      }]
    },
    "frontend": {
      "module": "frontend/module.ts"
    }
  },
  "permissions": [],
  "dependencies": {}
}
```

#### 3. 编写后端路由

```python
# backend/routes/my_routes.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/hello")
async def hello():
    return {"message": "Hello from my plugin!"}
```

#### 4. 编写前端组件

```typescript
// frontend/components/my-component.component.ts
import { Component } from '@angular/core';

@Component({
  selector: 'app-my-component',
  template: '<h1>My Plugin Component</h1>',
})
export class MyComponent {}
```

#### 5. 打包插件

```bash
npm run build-plugin ./my-plugin -o ./dist
```

#### 6. 测试安装

```bash
# 通过 Electron 应用安装
# 或在开发模式下符号链接
ln -s /path/to/my-plugin ~/.imato/plugins/my-plugin/dev
```

### 生命周期钩子

#### onInstall 钩子

```python
# backend/hooks/on_install.py
import os
from pathlib import Path

def main():
    plugin_dir = Path(os.environ['PLUGIN_DIR'])
    data_dir = Path(os.environ['DATA_DIR'])
    
    # 创建数据目录
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化配置
    config = {
        "enabled": True,
        "settings": {}
    }
    
    import json
    with open(data_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ {os.environ['PLUGIN_ID']} 安装完成")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
```

#### onUninstall 钩子

```python
# backend/hooks/on_uninstall.py
import os
from pathlib import Path

def main():
    data_dir = Path(os.environ['DATA_DIR'])
    keep_data = os.environ.get('KEEP_DATA', 'false') == 'true'
    
    if not keep_data:
        import shutil
        shutil.rmtree(data_dir, ignore_errors=True)
        print("✓ 数据已清理")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
```

### 调试插件

#### 开发模式

```bash
# 符号链接到插件目录
ln -s /path/to/my-plugin ~/.imato/plugins/my-plugin/dev

# 重启 Electron 应用
npm run electron:dev
```

#### 查看日志

```bash
# Electron 日志（开发者工具）
# 后端日志
tail -f backend/logs/plugin.log

# 安装日志
cat ~/.imato/plugins/my-plugin/install.log
```

---

## API 参考

### 前端 API (window.pluginAPI)

#### 设备评估

```typescript
// 获取设备评估报告
getDeviceProfile(): Promise<{
  success: boolean;
  profile?: DeviceProfile;
  error?: string;
}>

// 重新评估设备
reassessDevice(): Promise<{
  success: boolean;
  profile?: DeviceProfile;
  error?: string;
}>

// 评估插件兼容性
assessPlugin(pluginId: string): Promise<PluginCompatibilityResult>
```

#### 插件管理

```typescript
// 安装插件
installPlugin(pluginId: string, version?: string): Promise<{
  success: boolean;
  pluginId?: string;
  version?: string;
  error?: string;
}>

// 卸载插件
uninstallPlugin(pluginId: string, keepData?: boolean): Promise<{
  success: boolean;
  error?: string;
}>

// 获取已安装插件
getInstalledPlugins(): Promise<{
  success: boolean;
  plugins?: PluginInfo[];
  error?: string;
}>

// 启用/禁用插件
togglePlugin(pluginId: string, enabled: boolean): Promise<{
  success: boolean;
  enabled?: boolean;
  error?: string;
}>
```

#### 下载管理

```typescript
// 下载插件
downloadPlugin(pluginId: string, version: string, url: string): Promise<{
  success: boolean;
  filePath?: string;
  error?: string;
}>

// 取消下载
cancelDownload(pluginId: string, version: string): Promise<void>

// 暂停下载
pauseDownload(pluginId: string, version: string): Promise<void>

// 恢复下载
resumeDownload(pluginId: string, version: string): Promise<void>
```

#### 事件监听

```typescript
// 安装进度
onInstallProgress(callback: (data: InstallProgress) => void): Function

// 下载进度
onDownloadProgress(callback: (data: DownloadProgress) => void): Function

// 插件状态变化
onPluginStatusChange(callback: (data: PluginStatus) => void): Function
```

### 后端 API (/api/v1)

#### 设备评估

```http
GET /api/v1/device/profile
Response: {
  "success": true,
  "profile": {
    "assessment": {
      "deviceClass": "advanced",
      "score": 72,
      "compatiblePluginTiers": ["tier-a", "tier-b", "tier-c"]
    }
  }
}

POST /api/v1/device/reassess
Response: { "success": true, "profile": {...} }

GET /api/v1/device/compatibility/{plugin_id}
Response: {
  "success": true,
  "compatible": true,
  "isRecommended": true
}
```

#### 插件管理

```http
GET /api/v1/plugins?state=enabled&category=ai-assistant&compatible_only=true
Response: [
  {
    "id": "ai-coding-assistant",
    "name": "AI 编程助手",
    "version": "1.2.0",
    "compatible": true,
    "state": "enabled"
  }
]

GET /api/v1/plugins/{plugin_id}
Response: {
  "id": "ai-coding-assistant",
  "name": "AI 编程助手",
  "version": "1.2.0",
  "description": "...",
  "device_compatibility": {...},
  "permissions": [...]
}

POST /api/v1/plugins/install
Body: { "plugin_id": "ai-coding-assistant", "version": "1.2.0" }
Response: { "success": true, "action": "electron:plugin:install" }

POST /api/v1/plugins/uninstall
Body: { "plugin_id": "ai-coding-assistant", "keep_data": true }
Response: { "success": true, "action": "electron:plugin:uninstall" }

POST /api/v1/plugins/toggle
Body: { "plugin_id": "ai-coding-assistant", "enabled": false }
Response: { "success": true, "enabled": false }

GET /api/v1/plugins/{plugin_id}/compatibility
Response: {
  "compatible": true,
  "device_class": "advanced",
  "device_score": 72,
  "required_tiers": ["tier-b"],
  "compatible_tiers": ["tier-a", "tier-b", "tier-c"]
}

GET /api/v1/plugins/search?q=ai&category=ai-assistant
Response: {
  "total": 5,
  "plugins": [...],
  "query": "ai"
}

GET /api/v1/plugins/stats
Response: {
  "total_installed": 12,
  "total_enabled": 10,
  "total_disabled": 2,
  "categories": {
    "ai-assistant": 3,
    "coding-tools": 2
  }
}

POST /api/v1/plugins/reload
Response: {
  "success": true,
  "total_loaded": 10
}
```

---

## 部署与运维

### 插件商店服务器

#### 架构

```
插件商店服务器
  ├─ 插件存储（S3/OSS）
  ├─ 插件元数据库（PostgreSQL）
  ├─ 搜索索引（Elasticsearch）
  ├─ CDN 分发
  └─ 签名验证服务
```

#### API 设计

```http
# 获取插件列表
GET https://plugins.imato.edu/api/v1/plugins

# 获取插件详情
GET https://plugins.imato.edu/api/v1/plugins/{id}

# 下载插件
GET https://plugins.imato.edu/api/v1/plugins/{id}/versions/{version}/download

# 搜索插件
GET https://plugins.imato.edu/api/v1/plugins/search?q=ai

# 检查更新
GET https://plugins.imato.edu/api/v1/plugins/{id}/updates?current_version=1.0.0
```

### 监控指标

#### 关键指标

- 插件安装成功率
- 插件卸载率
- 平均下载时间
- 设备等级分布
- 插件使用频率
- 错误率

#### 日志收集

```javascript
// Electron 主进程日志
console.log('[Plugin] Install:', pluginId, 'Result:', result);

// 后端日志
logger.info(f"Plugin loaded: {plugin_id}")

// 前端日志
console.log('[Plugin Store] Search:', query, 'Results:', count);
```

### 安全考虑

#### 插件签名验证

```bash
# 开发者签名
openssl dgst -sha256 -sign private-key.pem \
  -out signatures/manifest.sig manifest.json

# 客户端验证
openssl dgst -sha256 -verify public-key.pem \
  -signature signatures/manifest.sig manifest.json
```

#### 权限控制

- 插件必须声明权限（manifest.permissions）
- 用户安装时查看权限列表
- 运行时检查权限（Electron IPC 拦截）

#### 沙箱隔离

- 插件代码运行在独立进程
- 文件系统访问受限（仅插件目录和数据目录）
- 网络访问需声明权限

---

## 未来规划

### Phase 4: 模块迁移（第 8-10 周）

**目标**: 将现有模块迁移为插件格式

**任务**:
1. 迁移 AI 编程助手模块
2. 迁移 AR/VR 实验室模块
3. 迁移数据分析模块
4. 迁移机器学习模块
5. 创建插件开发模板
6. 编写插件开发文档
7. 创建示例插件
8. 开发者工具链

### Phase 5: 推荐引擎与包瘦身（第 11 周）

**目标**: 基于设备评级的智能推荐 + 主包瘦身

**任务**:
1. 推荐算法（基于设备等级/使用历史）
2. 主包瘦身（移除可选模块）
3. 按需下载统计
4. 性能优化（启动时间 < 3 秒）

### 长期规划

1. **插件市场**: 第三方插件审核和分发
2. **插件 monetization**: 付费插件和订阅
3. **插件协作**: 插件间通信和依赖
4. **插件模板**: 可视化插件创建工具
5. **插件分析**: 使用统计和性能监控
6. **跨平台**: 支持 Web/Mobile 插件

---

## 📚 相关文档

- [Phase 1 实施总结](./PLUGIN_PHASE1_IMPLEMENTATION_SUMMARY.md)
- [Phase 2 实施总结](./PLUGIN_PHASE2_IMPLEMENTATION_SUMMARY.md)
- [Phase 3 实施总结](./PLUGIN_PHASE3_IMPLEMENTATION_SUMMARY.md)
- [.mxp 格式规范](./MXP_FORMAT_SPEC.md)
- [插件化模块交付需求](./PLUGIN_BASED_MODULE_DELIVERY.md)
- [懒加载架构设计](./MODULAR_LAZY_LOADING_ARCHITECTURE.md)
- [开发计划](../plans/插件化模块交付开发计划_5a6d979c.md)

---

## 🎯 项目里程碑

| 阶段 | 时间 | 状态 | 交付物 |
|------|------|------|--------|
| **Phase 1** | 第 1-2 周 | ✅ 完成 | 设备评估框架 |
| **Phase 2** | 第 3-5 周 | ✅ 完成 | 插件包格式与管理器 |
| **Phase 3** | 第 6-7 周 | ✅ 完成 | 插件商店 UI |
| **Phase 4** | 第 8-10 周 | ⏳ 待开始 | 模块迁移 |
| **Phase 5** | 第 11 周 | ⏳ 待开始 | 推荐引擎与包瘦身 |

**总进度**: 3/5 阶段完成（60%）  
**总代码量**: ~10,023 行  
**预计完成**: 第 11 周

---

**文档版本**: 1.0.0  
**最后更新**: 2026-06-06  
**维护者**: iMato 架构团队
