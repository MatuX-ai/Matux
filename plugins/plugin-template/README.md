# 我的插件 (My Plugin)

这是一个 iMato 插件开发模板，展示如何创建一个完整的插件。

## 📋 目录

- [功能特性](#功能特性)
- [目录结构](#目录结构)
- [快速开始](#快速开始)
- [开发指南](#开发指南)
- [构建和打包](#构建和打包)
- [安装和测试](#安装和测试)
- [API 参考](#api-参考)
- [许可证](#许可证)

---

## 功能特性

- ✅ 后端 API 路由（FastAPI）
- ✅ 前端 UI 组件（Angular）
- ✅ Electron IPC 通信
- ✅ 生命周期钩子（安装/卸载）
- ✅ 设备兼容性声明
- ✅ 多语言支持

---

## 目录结构

```
my-plugin/
├── manifest.json                    # 插件元数据
├── README.md                        # 说明文档
├── icon.png                         # 插件图标
│
├── backend/                         # 后端代码
│   ├── routes/
│   │   └── my_plugin_routes.py     # API 路由
│   ├── services/
│   │   └── my_plugin_service.py    # 业务逻辑
│   ├── hooks/
│   │   ├── on_install.py           # 安装钩子
│   │   └── on_uninstall.py         # 卸载钩子
│   └── requirements.txt            # Python 依赖
│
├── frontend/                        # 前端代码
│   ├── components/
│   │   ├── my-plugin.component.ts  # 组件
│   │   ├── my-plugin.component.html # 模板
│   │   └── my-plugin.component.scss # 样式
│   ├── module.ts                   # Angular 模块
│   └── assets/
│       └── i18n/                   # 国际化文件
│
├── electron/                        # Electron 代码
│   ├── main.js                     # 主进程
│   └── preload.js                  # 预加载脚本
│
└── docs/                            # 文档
    └── API.md                      # API 文档
```

---

## 快速开始

### 1. 克隆模板

```bash
# 复制插件模板
cp -r plugins/plugin-template plugins/my-new-plugin
cd plugins/my-new-plugin
```

### 2. 修改 manifest.json

编辑 `manifest.json`，修改以下字段：

```json
{
  "id": "my-new-plugin",
  "name": "我的新插件",
  "version": "1.0.0",
  "description": "插件描述",
  "author": {
    "name": "你的名字",
    "email": "your@email.com"
  }
}
```

### 3. 开发插件

#### 后端开发

```python
# backend/routes/my_plugin_routes.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/hello")
async def hello():
    return {"message": "Hello from my plugin!"}
```

#### 前端开发

```typescript
// frontend/components/my-plugin.component.ts
import { Component } from '@angular/core';

@Component({
  selector: 'app-my-plugin',
  template: '<h1>My Plugin</h1>',
})
export class MyPluginComponent {}
```

#### Electron 开发

```javascript
// electron/main.js
const { ipcMain } = require('electron');

ipcMain.handle('my-plugin:action', async (event, data) => {
  return { success: true, data };
});
```

---

## 开发指南

### 后端路由

创建 FastAPI 路由：

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class MyRequest(BaseModel):
    name: str
    value: str

class MyResponse(BaseModel):
    success: bool
    message: str
    data: dict

@router.post("/process", response_model=MyResponse)
async def process(request: MyRequest):
    try:
        # 业务逻辑
        result = {"name": request.name, "value": request.value}
        return MyResponse(success=True, message="成功", data=result)
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))
```

### 前端组件

创建 Angular 独立组件：

```typescript
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-my-component',
  standalone: true,
  imports: [CommonModule],
  template: '<div>{{ message }}</div>',
})
export class MyComponent implements OnInit {
  message = '';
  
  constructor(private http: HttpClient) {}
  
  async ngOnInit() {
    const response = await this.http.get('/api/v1/my-plugin/hello').toPromise();
    this.message = response.message;
  }
}
```

### 生命周期钩子

#### 安装钩子

```python
# backend/hooks/on_install.py
import os
from pathlib import Path

def main():
    data_dir = Path(os.environ['DATA_DIR'])
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化配置
    config = {"enabled": True}
    with open(data_dir / 'config.json', 'w') as f:
        json.dump(config, f)
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
```

#### 卸载钩子

```python
# backend/hooks/on_uninstall.py
import os
import shutil
from pathlib import Path

def main():
    data_dir = Path(os.environ['DATA_DIR'])
    keep_data = os.environ.get('KEEP_DATA', 'false') == 'true'
    
    if not keep_data:
        shutil.rmtree(data_dir, ignore_errors=True)
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
```

---

## 构建和打包

### 1. 验证 manifest

```bash
npm run build-plugin ./plugins/my-plugin --validate
```

### 2. 打包插件

```bash
# 基本打包
npm run build-plugin ./plugins/my-plugin

# 指定平台和输出目录
npm run build-plugin ./plugins/my-plugin -o ./dist -p all

# 带签名打包
npm run build-plugin ./plugins/my-plugin --sign --key ./keys/private.pem

# 最大压缩
npm run build-plugin ./plugins/my-plugin -c 9
```

### 3. 输出文件

打包后生成：

```
dist/my-plugin-1.0.0-all.mxp
```

---

## 安装和测试

### 开发模式测试

```bash
# 符号链接到插件目录（开发模式）
ln -s /path/to/my-plugin ~/.imato/plugins/my-plugin/dev

# 重启 Electron 应用
npm run electron:dev
```

### 安装 .mxp 包

通过 Electron 应用安装：

1. 打开插件商店
2. 搜索插件
3. 点击安装
4. 查看安装进度

### 测试 API

```bash
# 测试后端 API
curl http://localhost:8000/api/v1/my-plugin/hello

# 预期响应
{
  "success": true,
  "message": "Hello from my plugin!",
  "data": {"version": "1.0.0"}
}
```

---

## API 参考

### 后端 API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/v1/my-plugin/hello` | GET | Hello World |
| `/api/v1/my-plugin/process` | POST | 处理数据 |
| `/api/v1/my-plugin/items` | GET | 获取列表 |
| `/api/v1/my-plugin/health` | GET | 健康检查 |

### Electron IPC

| 通道 | 类型 | 描述 |
|------|------|------|
| `my-plugin:action1` | invoke | 执行动作 1 |
| `my-plugin:action2` | invoke | 执行动作 2 |
| `my-plugin:event` | on | 监听事件 |

### 前端 API

```typescript
// 通过 window.myPluginAPI 访问
const result = await window.myPluginAPI.action1({ data: 'test' });
```

---

## 设备兼容性

本插件兼容以下设备等级：

- ✅ Tier A（Basic）- 2核/4GB
- ✅ Tier B（Standard）- 4核/8GB
- ✅ Tier C（Advanced）- 6核/16GB/独显
- ✅ Tier D（Professional）- 8核/32GB/独显+CUDA

---

## 权限声明

本插件需要以下权限：

- 无特殊权限

---

## 依赖

### Python 依赖

无

### 插件依赖

无

---

## 常见问题

### Q1: 如何调试插件？

**A**: 使用开发模式，符号链接插件目录到 `~/.imato/plugins/`，然后重启应用。

### Q2: 如何更新插件版本？

**A**: 修改 `manifest.json` 中的 `version` 字段，遵循语义化版本（SemVer）。

### Q3: 如何添加 Python 依赖？

**A**: 在 `backend/requirements.txt` 中添加依赖，或在 `manifest.json` 的 `dependencies.python` 中声明。

---

## 许可证

MIT License

---

## 贡献

欢迎提交 Issue 和 Pull Request！

---

## 联系方式

- 邮箱: developer@example.com
- GitHub: https://github.com/username/my-plugin

---

**插件版本**: 1.0.0  
**最后更新**: 2026-06-06  
**维护者**: iMato 开发团队
