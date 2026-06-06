# iMato 插件开发指南

> **版本**: 1.0.0  
> **更新日期**: 2026-06-06  
> **适用对象**: 插件开发者

---

## 📋 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [插件结构](#插件结构)
4. [Manifest 配置](#manifest-配置)
5. [后端开发](#后端开发)
6. [前端开发](#前端开发)
7. [Electron 开发](#electron-开发)
8. [生命周期钩子](#生命周期钩子)
9. [设备兼容性](#设备兼容性)
10. [打包和发布](#打包和发布)
11. [调试技巧](#调试技巧)
12. [最佳实践](#最佳实践)
13. [常见问题](#常见问题)

---

## 概述

iMato 插件系统允许开发者创建可扩展的功能模块，通过插件化方式增强学习平台的能力。

### 插件类型

- **纯前端插件**: 仅提供 UI 组件
- **纯后端插件**: 仅提供 API 路由
- **全栈插件**: 包含前端 + 后端 + Electron
- **工具插件**: 提供辅助功能（如数据处理、文件转换等）

### 设备等级

| 等级 | Tier | 最低硬件 | 适用插件 |
|------|------|---------|---------|
| Basic | A | 2核/4GB | 简单工具、文档查看器 |
| Standard | B | 4核/8GB | AI 助手、数据分析 |
| Advanced | C | 6核/16GB/独显 | ML 训练、AR/VR |
| Professional | D | 8核/32GB/独显+CUDA | 大规模训练、3D 渲染 |

---

## 快速开始

### 1. 环境准备

```bash
# 确保已安装
- Node.js >= 18
- Python >= 3.9
- Angular CLI >= 17
```

### 2. 创建插件

```bash
# 复制插件模板
cp -r plugins/plugin-template plugins/my-awesome-plugin
cd plugins/my-awesome-plugin
```

### 3. 修改配置

编辑 `manifest.json`:

```json
{
  "id": "my-awesome-plugin",
  "name": "我的超棒插件",
  "version": "1.0.0",
  "description": "这是一个超棒的插件",
  "author": {
    "name": "你的名字",
    "email": "you@example.com"
  }
}
```

### 4. 开发插件

```bash
# 编辑后端路由
code backend/routes/my_plugin_routes.py

# 编辑前端组件
code frontend/components/my-plugin.component.ts

# 编辑 Electron 代码
code electron/main.js
```

### 5. 测试插件

```bash
# 符号链接（开发模式）
ln -s $(pwd) ~/.imato/plugins/my-awesome-plugin/dev

# 启动应用
npm run electron:dev
```

### 6. 打包插件

```bash
npm run build-plugin ./plugins/my-awesome-plugin -o ./dist
```

---

## 插件结构

### 标准目录布局

```
my-plugin/
├── manifest.json                    # [必需] 插件元数据
├── README.md                        # [推荐] 说明文档
├── LICENSE                          # [推荐] 许可证
├── icon.png                         # [推荐] 图标 (256x256)
│
├── backend/                         # [可选] 后端代码
│   ├── routes/                      # API 路由
│   ├── services/                    # 业务逻辑
│   ├── models/                      # 数据模型
│   ├── tasks/                       # 异步任务
│   ├── migrations/                  # 数据库迁移
│   ├── hooks/                       # 生命周期钩子
│   └── requirements.txt             # Python 依赖
│
├── frontend/                        # [可选] 前端代码
│   ├── components/                  # Angular 组件
│   ├── services/                    # Angular 服务
│   ├── models/                      # TypeScript 类型
│   ├── routes/                      # 路由配置
│   ├── assets/                      # 静态资源
│   └── module.ts                    # Angular 模块
│
├── electron/                        # [可选] Electron 代码
│   ├── main.js                      # 主进程
│   ├── preload.js                   # 预加载脚本
│   └── native/                      # 原生模块
│
├── python-deps/                     # [可选] Python 依赖
│   └── wheels/                      # .whl 文件
│
├── resources/                       # [可选] 资源文件
│   ├── data/                        # 初始数据
│   ├── templates/                   # 模板
│   └── configs/                     # 配置
│
└── docs/                            # [推荐] 文档
    ├── API.md                       # API 文档
    └── USER_GUIDE.md                # 用户指南
```

### 最小插件

最简单的插件只需：

```
minimal-plugin/
├── manifest.json
└── README.md
```

---

## Manifest 配置

### 必需字段

```json
{
  "manifestVersion": "1.0",
  "id": "my-plugin",
  "name": "我的插件",
  "version": "1.0.0",
  "description": "插件描述",
  "author": {
    "name": "开发者",
    "email": "dev@example.com"
  },
  "license": "MIT",
  "deviceCompatibility": {
    "compatibleTiers": ["tier-a", "tier-b", "tier-c", "tier-d"]
  },
  "entryPoints": {}
}
```

### 插件 ID 规则

- 小写字母、数字、连字符
- 3-64 个字符
- 以字母或数字开头
- 示例: `ai-coding-assistant`, `ar-chemistry-lab`

### 版本号规则

遵循语义化版本 (SemVer):

```
主版本号.次版本号.修订号

1.0.0      # 首个稳定版本
1.2.3      # 功能新增和 bug 修复
2.0.0      # 不兼容的 API 修改
1.0.0-beta.1  # 预发布版本
```

### 设备兼容性

```json
{
  "deviceCompatibility": {
    "compatibleTiers": ["tier-b", "tier-c", "tier-d"],
    "minDeviceScore": 35,
    "requiredHardware": {
      "minMemoryMB": 8192,
      "minStorageMB": 2048,
      "requireGPU": false,
      "requireCUDA": false,
      "requireDocker": false
    }
  }
}
```

### 入口点配置

```json
{
  "entryPoints": {
    "backend": {
      "routes": [{
        "file": "backend/routes/my_routes.py",
        "prefix": "/api/v1/my-plugin",
        "tags": ["我的插件"],
        "tier": 2,
        "lazyLoad": true
      }],
      "services": [{
        "name": "MyService",
        "file": "backend/services/my_service.py",
        "autoStart": false
      }],
      "hooks": {
        "onInstall": "backend/hooks/on_install.py",
        "onUninstall": "backend/hooks/on_uninstall.py"
      }
    },
    "frontend": {
      "module": "frontend/module.ts",
      "menuItems": [{
        "label": "我的插件",
        "route": "/my-plugin",
        "icon": "extension"
      }]
    },
    "electron": {
      "main": "electron/main.js",
      "preload": "electron/preload.js",
      "ipcHandlers": ["my-plugin:action"]
    }
  }
}
```

### 权限声明

```json
{
  "permissions": [
    "filesystem:read",
    "network:external",
    "database:read",
    "electron:ipc"
  ]
}
```

可用权限：
- `filesystem:read` - 读取文件
- `filesystem:write` - 写入文件
- `network:external` - 访问网络
- `database:read` - 读取数据库
- `database:write` - 写入数据库
- `electron:ipc` - IPC 通信
- `electron:native` - 原生 API
- `gpu:compute` - GPU 计算
- `docker:access` - Docker 访问
- `redis:access` - Redis 访问
- `system:info` - 系统信息

---

## 后端开发

### 创建路由

```python
# backend/routes/my_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# 数据模型
class MyRequest(BaseModel):
    name: str
    value: Optional[str] = None

class MyResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# API 端点
@router.get("/hello", response_model=MyResponse)
async def hello():
    """Hello World 端点"""
    return MyResponse(
        success=True,
        message="Hello from my plugin!",
        data={"version": "1.0.0"}
    )

@router.post("/process", response_model=MyResponse)
async def process(request: MyRequest):
    """处理数据端点"""
    try:
        result = {
            "name": request.name,
            "value": request.value,
            "processed": True
        }
        return MyResponse(success=True, message="成功", data=result)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
```

### 创建服务

```python
# backend/services/my_service.py
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MyService:
    """我的插件服务"""
    
    def __init__(self):
        self.config = {}
        self.data = {}
        logger.info("MyService 初始化")
    
    async def start(self):
        """启动服务"""
        logger.info("MyService 启动")
        # 初始化资源
    
    async def stop(self):
        """停止服务"""
        logger.info("MyService 停止")
        # 清理资源
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理数据"""
        logger.info(f"处理数据: {data}")
        return {"processed": True, **data}
```

### 访问数据库

```python
# backend/services/db_service.py
from sqlalchemy.orm import Session
from database.session import get_db

class DBService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_items(self):
        return self.db.query(MyModel).all()
    
    def create_item(self, data):
        item = MyModel(**data)
        self.db.add(item)
        self.db.commit()
        return item
```

---

## 前端开发

### 创建组件

```typescript
// frontend/components/my-component.component.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-my-component',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatButtonModule],
  templateUrl: './my-component.component.html',
  styleUrls: ['./my-component.component.scss'],
})
export class MyComponent implements OnInit, OnDestroy {
  data: any = null;
  loading = false;
  private destroy$ = new Subject<void>();
  
  constructor(private http: HttpClient) {}
  
  ngOnInit(): void {
    this.loadData();
  }
  
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
  
  async loadData(): Promise<void> {
    this.loading = true;
    try {
      const response = await this.http.get('/api/v1/my-plugin/hello')
        .pipe(takeUntil(this.destroy$))
        .toPromise();
      this.data = response;
    } finally {
      this.loading = false;
    }
  }
}
```

### 创建模板

```html
<!-- frontend/components/my-component.component.html -->
<mat-card>
  <mat-card-header>
    <mat-card-title>我的插件</mat-card-title>
  </mat-card-header>
  <mat-card-content>
    <div *ngIf="loading">加载中...</div>
    <div *ngIf="!loading && data">
      <p>{{ data.message }}</p>
      <pre>{{ data | json }}</pre>
    </div>
  </mat-card-content>
  <mat-card-actions>
    <button mat-raised-button color="primary" (click)="loadData()">
      刷新
    </button>
  </mat-card-actions>
</mat-card>
```

### 创建样式

```scss
// frontend/components/my-component.component.scss
mat-card {
  border-radius: 12px;
  
  mat-card-title {
    font-size: 18px;
    font-weight: 600;
  }
  
  pre {
    background: #f5f5f5;
    padding: 16px;
    border-radius: 8px;
    font-size: 12px;
    overflow-x: auto;
  }
}
```

---

## Electron 开发

### 主进程

```javascript
// electron/main.js
const { ipcMain } = require('electron');

function registerIPCHandlers() {
  // 注册 IPC 处理器
  ipcMain.handle('my-plugin:action', async (event, data) => {
    try {
      // 业务逻辑
      const result = {
        success: true,
        data: { ...data, processed: true }
      };
      return result;
    } catch (err) {
      return { success: false, error: err.message };
    }
  });
}

function unregisterIPCHandlers() {
  // 卸载处理器
  ipcMain.removeHandler('my-plugin:action');
}

module.exports = { registerIPCHandlers, unregisterIPCHandlers };
```

### 预加载脚本

```javascript
// electron/preload.js
const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的 API
contextBridge.exposeInMainWorld('myPluginAPI', {
  action: (data) => ipcRenderer.invoke('my-plugin:action', data),
  
  onEvent: (callback) => {
    const subscription = (event, data) => callback(data);
    ipcRenderer.on('my-plugin:event', subscription);
    return () => ipcRenderer.removeListener('my-plugin:event', subscription);
  },
});
```

### 前端调用

```typescript
// 在 Angular 组件中使用
declare global {
  interface Window {
    myPluginAPI?: {
      action: (data: any) => Promise<any>;
      onEvent: (callback: (data: any) => void) => () => void;
    };
  }
}

// 调用 IPC
const result = await window.myPluginAPI?.action({ test: 'data' });

// 监听事件
const unsubscribe = window.myPluginAPI?.onEvent((data) => {
  console.log('收到事件:', data);
});

// 取消监听
unsubscribe?.();
```

---

## 生命周期钩子

### 安装钩子

```python
# backend/hooks/on_install.py
import os
import json
from pathlib import Path

def main():
    plugin_id = os.environ['PLUGIN_ID']
    data_dir = Path(os.environ['DATA_DIR'])
    
    # 创建数据目录
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建默认配置
    config = {"enabled": True, "version": os.environ['PLUGIN_VERSION']}
    with open(data_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ {plugin_id} 安装完成")
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
```

### 卸载钩子

```python
# backend/hooks/on_uninstall.py
import os
import shutil
from pathlib import Path

def main():
    data_dir = Path(os.environ['DATA_DIR'])
    keep_data = os.environ.get('KEEP_DATA', 'false') == 'true'
    
    if not keep_data:
        # 清理数据
        shutil.rmtree(data_dir, ignore_errors=True)
        print("✓ 数据已清理")
    else:
        print("✓ 保留数据")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
```

### 环境变量

钩子脚本可用的环境变量：

- `PLUGIN_ID` - 插件 ID
- `PLUGIN_VERSION` - 插件版本
- `PLUGIN_DIR` - 插件安装目录
- `DATA_DIR` - 插件数据目录
- `PLATFORM` - 操作系统（win32/darwin/linux）
- `ARCH` - 系统架构（x64/arm64）
- `KEEP_DATA` - 是否保留数据（仅卸载时）

---

## 设备兼容性

### Tier 等级选择

根据插件的资源需求选择合适的 Tier：

| Tier | 适用场景 | 示例插件 |
|------|---------|---------|
| A | 轻量级，无特殊要求 | Markdown 编辑器、计算器 |
| B | 中等资源需求 | AI 代码补全、数据可视化 |
| C | 需要 GPU | ML 模型训练、AR 实验室 |
| D | 高性能计算 | 大规模训练、3D 渲染 |

### 硬件要求声明

```json
{
  "requiredHardware": {
    "minMemoryMB": 8192,
    "minStorageMB": 2048,
    "requireGPU": true,
    "minVRAM_MB": 2048,
    "requireCUDA": false,
    "requireDocker": true,
    "requireRedis": false
  }
}
```

---

## 打包和发布

### 1. 验证插件

```bash
npm run build-plugin ./plugins/my-plugin --validate
```

### 2. 打包插件

```bash
# 基本打包
npm run build-plugin ./plugins/my-plugin

# 指定输出目录
npm run build-plugin ./plugins/my-plugin -o ./releases

# 指定平台
npm run build-plugin ./plugins/my-plugin -p win32-x64

# 带签名
npm run build-plugin ./plugins/my-plugin --sign --key ./private.pem

# 最大压缩
npm run build-plugin ./plugins/my-plugin -c 9
```

### 3. 测试安装包

```bash
# 通过 Electron 应用安装
# 或手动安装
cp dist/my-plugin-1.0.0-all.mxp ~/.imato/downloads/
```

### 4. 发布到插件商店

1. 注册开发者账号
2. 上传 .mxp 文件
3. 填写插件信息
4. 提交审核
5. 审核通过后上架

---

## 调试技巧

### 开发模式

```bash
# 符号链接插件
ln -s /path/to/plugin ~/.imato/plugins/my-plugin/dev

# 启动开发模式
npm run electron:dev
```

### 查看日志

```bash
# Electron 日志
# 打开开发者工具 → Console

# 后端日志
tail -f backend/logs/plugin.log

# 安装日志
cat ~/.imato/plugins/my-plugin/install.log
```

### 热重载

- **前端**: 修改代码后刷新页面
- **后端**: 修改代码后重启服务
- **Electron**: 修改代码后重启应用

### 调试工具

```javascript
// Electron 主进程
console.log('[MyPlugin] 调试信息:', data);

// 前端
console.log('[MyPlugin] 组件状态:', this.state);

// 后端
import logging
logger = logging.getLogger(__name__)
logger.debug('调试信息: %s', data)
```

---

## 最佳实践

### 1. 代码组织

- 按功能模块划分目录
- 使用清晰的命名规范
- 保持代码简洁可读

### 2. 错误处理

```python
# 后端
try:
    result = process_data(data)
except Exception as err:
    logger.error(f"处理失败: {err}")
    raise HTTPException(status_code=500, detail=str(err))
```

```typescript
// 前端
try {
  const response = await this.http.get('/api/...').toPromise();
} catch (err) {
  this.snackBar.open(`错误: ${err.message}`, '关闭');
}
```

### 3. 资源清理

```python
# 钩子中清理资源
def on_uninstall():
    # 停止服务
    service.stop()
    
    # 清理缓存
    shutil.rmtree(cache_dir, ignore_errors=True)
    
    # 根据用户选择清理数据
    if not keep_data:
        shutil.rmtree(data_dir, ignore_errors=True)
```

### 4. 性能优化

- 使用懒加载
- 缓存计算结果
- 避免阻塞操作
- 合理使用异步

### 5. 安全性

- 验证用户输入
- 限制文件访问
- 使用 HTTPS
- 声明所需权限

---

## 常见问题

### Q1: 如何创建新插件？

**A**: 复制 `plugins/plugin-template` 目录，修改 `manifest.json` 和代码。

### Q2: 插件 ID 命名规则？

**A**: 小写字母、数字、连字符，3-64 字符，如 `my-awesome-plugin`。

### Q3: 如何选择设备等级？

**A**: 根据插件的资源需求选择，尽量兼容更多设备。

### Q4: 如何调试插件？

**A**: 使用开发模式（符号链接），查看控制台日志。

### Q5: 如何处理依赖？

**A**: Python 依赖在 `requirements.txt` 中声明，插件依赖在 `manifest.json` 中声明。

### Q6: 如何更新插件？

**A**: 修改版本号，重新打包，上传到插件商店。

### Q7: 插件可以访问数据库吗？

**A**: 可以，声明 `database:read` 或 `database:write` 权限。

### Q8: 如何国际化？

**A**: 在 `frontend/assets/i18n/` 中添加语言文件。

---

## 参考文档

- [.mxp 格式规范](../../docs/MXP_FORMAT_SPEC.md)
- [插件化架构指南](../../docs/PLUGIN_ARCHITECTURE_COMPLETE_GUIDE.md)
- [插件商店](../../docs/PLUGIN_PHASE3_IMPLEMENTATION_SUMMARY.md)

---

**文档版本**: 1.0.0  
**最后更新**: 2026-06-06  
**维护者**: iMato 开发团队
