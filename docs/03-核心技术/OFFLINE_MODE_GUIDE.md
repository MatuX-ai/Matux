# 离线模式开发指南

## 概述

本文档详细介绍如何开发、配置和使用iMatuProject平台的离线模式功能。离线模式旨在为用户提供在网络不稳定或无网络环境下依然能够正常使用核心功能的能力。

## 目录

1. [架构设计](#架构设计)
2. [核心组件](#核心组件)
3. [开发环境配置](#开发环境配置)
4. [功能实现详解](#功能实现详解)
5. [测试与验证](#测试与验证)
6. [部署指南](#部署指南)
7. [最佳实践](#最佳实践)
8. [故障排除](#故障排除)

## 架构设计

### 整体架构图

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   前端应用层     │    │   离线服务层      │    │   数据存储层     │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ 离线路由模块 │ │◄──►│ │ 网络监控服务 │ │◄──►│ │ IndexedDB   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ 离线UI组件   │ │◄──►│ │ 离线存储服务 │ │◄──►│ │ 缓存管理    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Service     │ │    │ │ 数据同步机制 │ │    │ │ 本地文件系统 │ │
│ │ Worker      │ │    │ └─────────────┘ │    │ └─────────────┘ │
│ └─────────────┘ │    │                 │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 核心设计理念

1. **渐进式增强**: 应用在有网络时提供完整功能，在离线时优雅降级
2. **数据一致性**: 确保离线操作在网络恢复后能正确同步
3. **用户体验优先**: 提供清晰的网络状态反馈和操作指引
4. **性能优化**: 最小化资源加载，优化首屏渲染时间

## 核心组件

### 1. 网络监控服务 (NetworkMonitorService)

**文件位置**: `src/app/core/services/network-monitor.service.ts`

**主要功能**:
- 实时监测网络连接状态
- 评估网络质量等级
- 提供网络状态变化通知
- 支持手动状态检查

**使用示例**:
```typescript
constructor(private networkMonitor: NetworkMonitorService) {
  // 订阅网络状态变化
  this.networkMonitor.networkStatus$.subscribe(status => {
    console.log('网络状态:', status);
  });
  
  // 检查是否为低质量网络
  if (this.networkMonitor.isLowQualityNetwork()) {
    // 启用轻量化模式
  }
}
```

### 2. 离线存储服务 (OfflineStorageService)

**文件位置**: `src/app/core/services/offline-storage.service.ts`

**主要功能**:
- 管理IndexedDB数据库
- 提供数据的CRUD操作
- 维护离线操作队列
- 处理数据同步逻辑

**使用示例**:
```typescript
// 存储数据
await this.offlineStorage.setData(OfflineStorageKey.USER_DATA, userData);

// 获取数据
const userData = await this.offlineStorage.getData<OfflineUserData>(
  OfflineStorageKey.USER_DATA, 
  userId
);

// 添加离线操作
await this.offlineStorage.addOperation({
  type: OfflineOperationType.UPDATE,
  tableName: 'tasks',
  recordId: taskId,
  data: updatedTask
});
```

### 3. 离线模式路由模块

**文件位置**: `src/app/offline-mode/`

**模块结构**:
```
offline-mode/
├── offline-mode-routing.module.ts    # 路由配置
├── offline-mode.module.ts           # 模块定义
├── components/
│   ├── offline-dashboard/          # 离线仪表板
│   ├── offline-task-list/          # 离线任务列表
│   └── network-status-indicator/   # 网络状态指示器
└── services/
    └── (共享服务)
```

## 开发环境配置

### 1. 依赖安装

```bash
# 安装Angular Service Worker
npm install @angular/service-worker@^17.3.0 --save

# 安装其他必要依赖
npm install rxjs @angular/material
```

### 2. Angular配置

**angular.json** 配置:
```json
{
  "projects": {
    "imatuproject": {
      "architect": {
        "build": {
          "configurations": {
            "production": {
              "serviceWorker": true,
              "assets": [
                "src/favicon.ico",
                "src/assets",
                "src/manifest.webmanifest"
              ]
            }
          }
        }
      }
    }
  }
}
```

### 3. Service Worker配置

**ngsw-config.json**:
```json
{
  "$schema": "./node_modules/@angular/service-worker/config/schema.json",
  "index": "/index.html",
  "assetGroups": [{
    "name": "app",
    "installMode": "prefetch",
    "resources": {
      "files": [
        "/favicon.ico",
        "/index.html",
        "/*.css",
        "/*.js"
      ]
    }
  }],
  "dataGroups": [{
    "name": "api-performance",
    "urls": ["/api/**"],
    "cacheConfig": {
      "strategy": "performance",
      "maxSize": 100,
      "maxAge": "1h"
    }
  }]
}
```

## 功能实现详解

### 1. 网络状态检测

**实现原理**:
- 使用 `navigator.onLine` API检测基础连接状态
- 结合 Network Information API获取详细网络信息
- 定期ping检测验证网络连通性

**质量等级划分**:
```typescript
export enum NetworkQuality {
  OFFLINE = 'offline',      // 离线
  SLOW_2G = 'slow-2g',      // 极慢网络
  SLOW_3G = 'slow-3g',      // 慢速网络
  FAST_4G = 'fast-4g',      // 正常网络
  FAST_WIFI = 'fast-wifi'   // 快速网络
}
```

### 2. 数据缓存策略

**缓存层级**:
1. **静态资源**: 预缓存核心JS/CSS文件
2. **动态数据**: 运行时缓存API响应
3. **用户数据**: IndexedDB持久化存储
4. **临时数据**: 内存缓存短期数据

**缓存更新机制**:
```typescript
// 版本控制
const CACHE_VERSION = 'v1.0.0';

// 增量更新
async updateCache(newData: any[]) {
  const existingData = await this.getCache();
  const mergedData = this.mergeData(existingData, newData);
  await this.setCache(mergedData);
}
```

### 3. 离线操作队列

**队列管理**:
```typescript
interface OfflineOperation {
  id: string;
  type: OfflineOperationType;
  status: OfflineOperationStatus;
  tableName: string;
  recordId: string;
  data: any;
  createdAt: Date;
  retryCount: number;
}
```

**同步策略**:
- 网络恢复时自动触发同步
- 支持批量处理提高效率
- 失败操作自动重试（最多3次）
- 冲突解决机制

## 测试与验证

### 1. 自动化测试脚本

**使用Python回测脚本**:
```bash
# 运行回测验证
python scripts/offline_mode_backtest.py
```

**测试覆盖范围**:
- ✅ 网络状态检测准确性
- ✅ Service Worker注册状态
- ✅ 离线路由可访问性
- ✅ 离线数据存储功能
- ✅ 不同网络环境下的性能表现

### 2. 手动测试方法

**Chrome DevTools网络模拟**:
1. 打开开发者工具 (F12)
2. 进入 Network 标签页
3. 选择 Throttling 下拉菜单
4. 选择预设网络条件（如 Fast 3G、Slow 3G、Offline）

**测试场景**:
- 网络从在线切换到离线
- 离线状态下执行各种操作
- 网络恢复后的数据同步
- 长时间离线后的状态恢复

### 3. 性能基准测试

**关键指标**:
- 首屏加载时间：< 5秒（2G网络）
- 关键操作响应时间：< 2秒
- 离线缓存占用：< 50MB
- 数据同步成功率：> 95%

## 部署指南

### 1. 生产环境配置

**nginx配置示例**:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend-server;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # 启用gzip压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
}
```

### 2. HTTPS配置

**重要**: PWA功能需要HTTPS环境

```bash
# 使用Let's Encrypt免费SSL证书
sudo certbot --nginx -d your-domain.com
```

### 3. Service Worker部署

**构建命令**:
```bash
# 生产环境构建
ng build --prod --service-worker

# 验证Service Worker
npx http-server dist/ -p 8080 -c-1
```

## 最佳实践

### 1. 用户体验优化

**状态反馈**:
```html
<!-- 网络状态指示器 -->
<app-network-status-indicator></app-network-status-indicator>

<!-- 离线提示 -->
<div class="offline-banner" *ngIf="isOffline">
  您当前处于离线模式，部分功能可能受限
</div>
```

**渐进式加载**:
- 优先加载核心功能
- 延迟加载非必需资源
- 提供骨架屏占位符

### 2. 性能优化

**资源优化**:
```typescript
// 图片懒加载
<img [loading]="'lazy'" [src]="imageUrl">

// 代码分割
const module = await import('./heavy-feature.module');

// 缓存策略
const cacheFirst = [
  '/assets/**',
  '/**/*.css',
  '/**/*.js'
];
```

**数据优化**:
- 压缩传输数据
- 分页加载大数据集
- 智能预加载用户可能需要的数据

### 3. 错误处理

**优雅降级**:
```typescript
try {
  // 尝试在线操作
  await this.apiService.getData();
} catch (error) {
  if (this.networkMonitor.isOffline()) {
    // 切换到离线模式
    return this.offlineStorage.getData(key, id);
  }
  throw error;
}
```

## 故障排除

### 常见问题及解决方案

**1. Service Worker未注册**
```
问题: 控制台显示Service Worker注册失败
解决方案: 
- 检查HTTPS配置
- 确认ngsw.json文件存在
- 清除浏览器缓存重新加载
```

**2. 离线数据不同步**
```
问题: 网络恢复后数据未同步
解决方案:
- 检查同步队列状态
- 验证API连接配置
- 查看浏览器控制台错误信息
```

**3. 缓存更新延迟**
```
问题: 新版本应用更新缓慢
解决方案:
- 配置合理的缓存策略
- 实现主动缓存清除机制
- 添加版本检查功能
```

### 调试工具

**浏览器开发者工具**:
- Application → Service Workers
- Application → Cache Storage
- Application → IndexedDB

**日志监控**:
```typescript
// 启用详细日志
localStorage.setItem('debug', 'offline:*');

// 查看Service Worker状态
navigator.serviceWorker.getRegistrations().then(registrations => {
  console.log('Service Worker registrations:', registrations);
});
```

## 附录

### 相关资源

- [Angular Service Worker官方文档](https://angular.io/guide/service-worker-intro)
- [Web App Manifest规范](https://developer.mozilla.org/zh-CN/docs/Web/Manifest)
- [IndexedDB API参考](https://developer.mozilla.org/zh-CN/docs/Web/API/IndexedDB_API)
- [Network Information API](https://developer.mozilla.org/zh-CN/docs/Web/API/Network_Information_API)

### 版本历史

- v1.0.0 (2026-02-28): 初始版本发布
  - 基础离线功能实现
  - 网络状态监控
  - 离线路由模块
  - 核心UI组件

---

**注意**: 本文档将持续更新以反映最新的开发实践和功能改进。如有疑问或建议，请联系开发团队。