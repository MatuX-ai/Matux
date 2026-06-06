# .mxp 插件包格式规范 (Mato eXtension Package)

> **版本**: 1.0.0  
> **创建日期**: 2026-06-06  
> **状态**: Phase 2 基础规范  
> **适用范围**: 所有 iMato 学习端插件包

---

## 📋 目录

1. [概述](#概述)
2. [插件包结构](#插件包结构)
3. [Manifest 规范](#manifest-规范)
4. [设备兼容性声明](#设备兼容性声明)
5. [插件生命周期钩子](#插件生命周期钩子)
6. [打包规范](#打包规范)
7. [签名与验证](#签名与验证)
8. [版本控制](#版本控制)
9. [示例插件包](#示例插件包)
10. [常见问题](#常见问题)

---

## 概述

`.mxp` (Mato eXtension Package) 是 iMato 学习端的插件包格式，基于 ZIP 压缩格式，包含插件运行所需的所有代码、资源、依赖声明和元数据。

### 设计目标

- **自包含**: 插件包包含所有运行时依赖，无需额外安装
- **可验证**: 支持数字签名，确保插件来源可信
- **设备感知**: 声明设备兼容性，与设备评估框架集成
- **跨平台**: 支持 Windows/macOS/Linux 平台特定代码
- **懒加载**: 支持按需加载模块，减少内存占用

### 命名约定

```
{plugin-id}-{version}-{platform}.mxp

示例:
- ai-coding-assistant-1.2.0-all.mxp          (跨平台)
- ar-chemistry-lab-2.0.1-win32-x64.mxp      (Windows x64)
- ml-training-module-1.0.0-linux-x64.mxp    (Linux x64)
```

**平台标识**:
- `all`: 跨平台通用
- `win32-x64`: Windows 64位
- `win32-arm64`: Windows ARM64
- `darwin-x64`: macOS Intel
- `darwin-arm64`: macOS Apple Silicon
- `linux-x64`: Linux 64位

---

## 插件包结构

### 标准目录布局

```
{plugin-id}-{version}-{platform}.mxp (ZIP)
├── manifest.json                    # [必需] 插件元数据和配置
├── README.md                        # [推荐] 插件说明文档
├── LICENSE                          # [推荐] 许可证文件
├── icon.png                         # [推荐] 插件图标 (256x256 PNG)
│
├── backend/                         # [可选] 后端代码
│   ├── routes/                      # FastAPI 路由
│   │   └── {plugin}_routes.py
│   ├── services/                    # 业务逻辑服务
│   │   └── {plugin}_service.py
│   ├── models/                      # SQLAlchemy 模型
│   │   └── {plugin}_model.py
│   ├── tasks/                       # Celery 异步任务
│   │   └── {plugin}_tasks.py
│   ├── migrations/                  # Alembic 数据库迁移
│   │   └── versions/
│   ├── hooks/                       # 生命周期钩子脚本
│   │   ├── on_install.py
│   │   ├── on_uninstall.py
│   │   ├── on_enable.py
│   │   └── on_disable.py
│   └── requirements.txt             # Python 依赖列表
│
├── frontend/                        # [可选] 前端代码
│   ├── components/                  # Angular 组件
│   │   ├── {plugin}.component.ts
│   │   ├── {plugin}.component.html
│   │   └── {plugin}.component.scss
│   ├── services/                    # Angular 服务
│   │   └── {plugin}.service.ts
│   ├── models/                      # TypeScript 类型定义
│   │   └── {plugin}.model.ts
│   ├── routes/                      # 路由配置
│   │   └── {plugin}-routes.ts
│   ├── assets/                      # 静态资源
│   │   ├── images/
│   │   ├── i18n/
│   │   │   ├── zh-CN.json
│   │   │   └── en-US.json
│   │   └── styles/
│   └── module.ts                    # Angular 模块入口
│
├── electron/                        # [可选] Electron 主进程代码
│   ├── main.js                      # Electron 主进程入口
│   ├── preload.js                   # 预加载脚本
│   ├── ipc-handlers.js              # IPC 处理器
│   └── native/                      # 原生模块 (可选)
│       ├── win32-x64/
│       │   └── {module}.node
│       └── darwin-arm64/
│           └── {module}.node
│
├── python-deps/                     # [可选] 预编译 Python 依赖
│   ├── wheels/                      # .whl 文件
│   │   └── {package}-{version}-*.whl
│   └── requirements-installed.txt   # 已安装的依赖清单
│
├── resources/                       # [可选] 插件资源文件
│   ├── data/                        # 初始数据
│   │   └── seed-data.json
│   ├── templates/                   # 模板文件
│   │   └── report-template.html
│   ├── models/                      # ML 模型文件
│   │   └── model.onnx
│   └── configs/                     # 配置文件
│       └── default-config.json
│
├── tests/                           # [推荐] 测试文件
│   ├── backend/
│   │   └── test_{plugin}.py
│   ├── frontend/
│   │   └── {plugin}.spec.ts
│   └── integration/
│       └── test_{plugin}_integration.py
│
├── docs/                            # [推荐] 文档
│   ├── API.md                       # API 文档
│   ├── USER_GUIDE.md                # 用户指南
│   └── CHANGELOG.md                 # 变更日志
│
└── signatures/                      # [可选] 数字签名
    ├── manifest.sig                 # manifest.json 签名
    └── package.sig                  # 完整包签名
```

### 必需文件

以下文件是插件包的**最低要求**：

```
✓ manifest.json          (必需)
✓ README.md              (强烈推荐)
```

### 可选目录规则

- 如果插件仅提供后端功能，可省略 `frontend/` 和 `electron/`
- 如果插件仅提供前端 UI，可省略 `backend/` 和 `electron/`
- 如果插件不需要特殊权限，可省略 `electron/`
- `python-deps/` 仅在需要预编译依赖时使用（如 numpy、torch）

---

## Manifest 规范

`manifest.json` 是插件的核心元数据文件，定义插件的身份、功能、依赖和兼容性。

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MXP Manifest",
  "type": "object",
  "required": [
    "manifestVersion",
    "id",
    "name",
    "version",
    "description",
    "author",
    "license",
    "deviceCompatibility",
    "entryPoints"
  ],
  "properties": {
    "manifestVersion": {
      "type": "string",
      "enum": ["1.0"],
      "description": "Manifest 格式版本"
    },
    "id": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9-]{2,63}$",
      "description": "插件唯一标识符 (kebab-case, 3-64 字符)"
    },
    "name": {
      "type": "string",
      "minLength": 2,
      "maxLength": 100,
      "description": "插件显示名称"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+(-[a-z0-9.]+)?$",
      "description": "语义化版本号 (SemVer)"
    },
    "description": {
      "type": "string",
      "maxLength": 500,
      "description": "插件简短描述"
    },
    "author": {
      "type": "object",
      "required": ["name", "email"],
      "properties": {
        "name": { "type": "string" },
        "email": { "type": "string", "format": "email" },
        "url": { "type": "string", "format": "uri" },
        "organization": { "type": "string" }
      }
    },
    "license": {
      "type": "string",
      "description": "SPDX 许可证标识符",
      "examples": ["MIT", "Apache-2.0", "GPL-3.0", "Proprietary"]
    },
    "repository": {
      "type": "object",
      "properties": {
        "type": { "type": "string", "enum": ["git", "svn", "hg"] },
        "url": { "type": "string", "format": "uri" }
      }
    },
    "homepage": {
      "type": "string",
      "format": "uri",
      "description": "插件主页 URL"
    },
    "bugs": {
      "type": "object",
      "properties": {
        "url": { "type": "string", "format": "uri" },
        "email": { "type": "string", "format": "email" }
      }
    },
    "keywords": {
      "type": "array",
      "items": { "type": "string" },
      "maxItems": 20,
      "description": "搜索关键词"
    },
    "categories": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "ai-assistant",
          "ar-vr-lab",
          "coding-tools",
          "data-analysis",
          "education",
          "gamification",
          "hardware",
          "ml-training",
          "visualization",
          "productivity",
          "other"
        ]
      },
      "description": "插件分类"
    },
    "icon": {
      "type": "string",
      "description": "图标文件路径 (相对于包根目录)",
      "default": "icon.png"
    },
    "deviceCompatibility": {
      "$ref": "#/definitions/DeviceCompatibility"
    },
    "entryPoints": {
      "$ref": "#/definitions/EntryPoints"
    },
    "dependencies": {
      "$ref": "#/definitions/Dependencies"
    },
    "permissions": {
      "$ref": "#/definitions/Permissions"
    },
    "settings": {
      "$ref": "#/definitions/Settings"
    },
    "localization": {
      "$ref": "#/definitions/Localization"
    },
    "updateInfo": {
      "$ref": "#/definitions/UpdateInfo"
    }
  },
  "definitions": {
    "DeviceCompatibility": {
      "type": "object",
      "required": ["compatibleTiers"],
      "properties": {
        "compatibleTiers": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["tier-a", "tier-b", "tier-c", "tier-d"]
          },
          "description": "兼容的设备等级"
        },
        "minDeviceScore": {
          "type": "integer",
          "minimum": 0,
          "maximum": 100,
          "description": "最低设备评分要求"
        },
        "requiredHardware": {
          "type": "object",
          "properties": {
            "minMemoryMB": { "type": "integer" },
            "minStorageMB": { "type": "integer" },
            "requireGPU": { "type": "boolean" },
            "minVRAM_MB": { "type": "integer" },
            "requireCUDA": { "type": "boolean" },
            "requireDocker": { "type": "boolean" },
            "requireRedis": { "type": "boolean" }
          }
        },
        "incompatibleWith": {
          "type": "array",
          "items": { "type": "string" },
          "description": "不兼容的插件 ID 列表"
        }
      }
    },
    "EntryPoints": {
      "type": "object",
      "properties": {
        "backend": {
          "type": "object",
          "properties": {
            "routes": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["file", "prefix", "tags"],
                "properties": {
                  "file": { "type": "string" },
                  "prefix": { "type": "string" },
                  "tags": {
                    "type": "array",
                    "items": { "type": "string" }
                  },
                  "tier": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 4,
                    "description": "模块层级 (1-4)"
                  },
                  "lazyLoad": {
                    "type": "boolean",
                    "default": true
                  }
                }
              }
            },
            "services": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["name", "file"],
                "properties": {
                  "name": { "type": "string" },
                  "file": { "type": "string" },
                  "autoStart": { "type": "boolean", "default": false }
                }
              }
            },
            "migrations": {
              "type": "boolean",
              "description": "是否包含数据库迁移"
            },
            "hooks": {
              "type": "object",
              "properties": {
                "onInstall": { "type": "string" },
                "onUninstall": { "type": "string" },
                "onEnable": { "type": "string" },
                "onDisable": { "type": "string" }
              }
            }
          }
        },
        "frontend": {
          "type": "object",
          "properties": {
            "module": {
              "type": "string",
              "description": "Angular 模块文件路径"
            },
            "routes": {
              "type": "string",
              "description": "路由配置文件路径"
            },
            "components": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["selector", "file"],
                "properties": {
                  "selector": { "type": "string" },
                  "file": { "type": "string" },
                  "lazyLoad": { "type": "boolean", "default": true }
                }
              }
            },
            "menuItems": {
              "type": "array",
              "items": {
                "type": "object",
                "required": ["label", "route", "icon"],
                "properties": {
                  "label": { "type": "string" },
                  "route": { "type": "string" },
                  "icon": { "type": "string" },
                  "parentMenu": { "type": "string" },
                  "order": { "type": "integer" }
                }
              }
            }
          }
        },
        "electron": {
          "type": "object",
          "properties": {
            "main": {
              "type": "string",
              "description": "Electron 主进程入口"
            },
            "preload": {
              "type": "string",
              "description": "预加载脚本"
            },
            "ipcHandlers": {
              "type": "array",
              "items": { "type": "string" },
              "description": "注册的 IPC 通道名称"
            }
          }
        }
      }
    },
    "Dependencies": {
      "type": "object",
      "properties": {
        "plugins": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["id", "version"],
            "properties": {
              "id": { "type": "string" },
              "version": { "type": "string" },
              "optional": { "type": "boolean", "default": false }
            }
          }
        },
        "python": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Python 包依赖 (requirements.txt 格式)"
        },
        "system": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name"],
            "properties": {
              "name": { "type": "string" },
              "version": { "type": "string" },
              "optional": { "type": "boolean" }
            }
          }
        }
      }
    },
    "Permissions": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "filesystem:read",
          "filesystem:write",
          "network:external",
          "database:read",
          "database:write",
          "electron:ipc",
          "electron:native",
          "gpu:compute",
          "docker:access",
          "redis:access",
          "system:info"
        ]
      }
    },
    "Settings": {
      "type": "object",
      "properties": {
        "schema": {
          "type": "object",
          "description": "JSON Schema 定义设置项"
        },
        "defaults": {
          "type": "object",
          "description": "默认设置值"
        }
      }
    },
    "Localization": {
      "type": "object",
      "properties": {
        "defaultLocale": {
          "type": "string",
          "default": "zh-CN"
        },
        "supportedLocales": {
          "type": "array",
          "items": { "type": "string" }
        },
        "resourcePath": {
          "type": "string",
          "default": "frontend/assets/i18n"
        }
      }
    },
    "UpdateInfo": {
      "type": "object",
      "properties": {
        "updateUrl": {
          "type": "string",
          "format": "uri",
          "description": "插件更新检查 URL"
        },
        "changelog": {
          "type": "string",
          "description": "当前版本变更日志"
        },
        "autoUpdate": {
          "type": "boolean",
          "default": false
        }
      }
    }
  }
}
```

### Manifest 示例

```json
{
  "manifestVersion": "1.0",
  "id": "ai-coding-assistant",
  "name": "AI 编程助手",
  "version": "1.2.0",
  "description": "基于大语言模型的智能代码补全、审查和重构工具",
  "author": {
    "name": "iMato Team",
    "email": "plugins@imato.edu",
    "url": "https://imato.edu",
    "organization": "iMato Education"
  },
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/imato/ai-coding-assistant"
  },
  "homepage": "https://imato.edu/plugins/ai-coding-assistant",
  "keywords": ["ai", "coding", "assistant", "llm", "code-completion"],
  "categories": ["ai-assistant", "coding-tools", "productivity"],
  "icon": "icon.png",
  
  "deviceCompatibility": {
    "compatibleTiers": ["tier-b", "tier-c", "tier-d"],
    "minDeviceScore": 35,
    "requiredHardware": {
      "minMemoryMB": 8192,
      "minStorageMB": 2048,
      "requireGPU": false
    }
  },
  
  "entryPoints": {
    "backend": {
      "routes": [
        {
          "file": "backend/routes/ai_coding_routes.py",
          "prefix": "/api/v1/ai-coding",
          "tags": ["AI 编程"],
          "tier": 2,
          "lazyLoad": true
        }
      ],
      "services": [
        {
          "name": "AICodingService",
          "file": "backend/services/ai_coding_service.py",
          "autoStart": false
        }
      ],
      "hooks": {
        "onInstall": "backend/hooks/on_install.py",
        "onUninstall": "backend/hooks/on_uninstall.py"
      }
    },
    "frontend": {
      "module": "frontend/module.ts",
      "routes": "frontend/routes/ai-coding-routes.ts",
      "components": [
        {
          "selector": "app-ai-coding-panel",
          "file": "frontend/components/ai-coding-panel.component.ts",
          "lazyLoad": true
        }
      ],
      "menuItems": [
        {
          "label": "AI 编程助手",
          "route": "/ai-coding",
          "icon": "smart_toy",
          "parentMenu": "tools",
          "order": 10
        }
      ]
    },
    "electron": {
      "main": "electron/main.js",
      "preload": "electron/preload.js",
      "ipcHandlers": ["ai-coding:complete", "ai-coding:review"]
    }
  },
  
  "dependencies": {
    "plugins": [],
    "python": [
      "openai>=1.0.0",
      "tiktoken>=0.5.0"
    ]
  },
  
  "permissions": [
    "network:external",
    "database:read",
    "electron:ipc"
  ],
  
  "settings": {
    "schema": {
      "type": "object",
      "properties": {
        "model": {
          "type": "string",
          "enum": ["gpt-4", "gpt-3.5-turbo", "claude-3"],
          "default": "gpt-4",
          "title": "AI 模型",
          "description": "选择使用的 AI 模型"
        },
        "autoComplete": {
          "type": "boolean",
          "default": true,
          "title": "自动补全",
          "description": "启用代码自动补全"
        },
        "maxTokens": {
          "type": "integer",
          "minimum": 100,
          "maximum": 4000,
          "default": 2000,
          "title": "最大 Token 数"
        }
      }
    },
    "defaults": {
      "model": "gpt-4",
      "autoComplete": true,
      "maxTokens": 2000
    }
  },
  
  "localization": {
    "defaultLocale": "zh-CN",
    "supportedLocales": ["zh-CN", "en-US", "ja-JP"],
    "resourcePath": "frontend/assets/i18n"
  },
  
  "updateInfo": {
    "updateUrl": "https://plugins.imato.edu/api/v1/plugins/ai-coding-assistant/updates",
    "changelog": "### 1.2.0\n- 新增代码重构功能\n- 优化补全性能\n- 修复已知问题",
    "autoUpdate": true
  }
}
```

---

## 设备兼容性声明

插件必须在 `manifest.json` 的 `deviceCompatibility` 字段中声明设备要求。

### 兼容性等级

| 等级 | Tier 标识 | 最低设备评分 | 典型硬件要求 | 适用插件类型 |
|------|----------|------------|------------|------------|
| **Tier A** | `tier-a` | 0+ | 任意设备 | 通用工具、文档查看器 |
| **Tier B** | `tier-b` | 35+ | 4核 CPU, 8GB RAM | AI 助手、数据分析 |
| **Tier C** | `tier-c` | 60+ | 6核 CPU, 16GB RAM, 独显 2GB | ML 训练、AR/VR 实验室 |
| **Tier D** | `tier-d` | 80+ | 8核 CPU, 32GB RAM, 独显 6GB, CUDA | 大规模训练、3D 渲染 |

### 兼容性检查流程

```
1. 读取 manifest.json → deviceCompatibility
2. 检查 compatibleTiers 是否包含当前设备等级
3. 检查 minDeviceScore ≤ 当前设备评分
4. 检查 requiredHardware 是否满足
   - minMemoryMB ≤ 实际内存
   - minStorageMB ≤ 可用存储
   - requireGPU → 检查是否有独显
   - minVRAM_MB ≤ 实际 VRAM
   - requireCUDA → 检查 CUDA 支持
   - requireDocker → 检查 Docker 可用性
   - requireRedis → 检查 Redis 可用性
5. 全部通过 → compatible = true
   任一失败 → compatible = false, 生成警告信息
```

### 示例：高级 AR 实验室插件

```json
{
  "deviceCompatibility": {
    "compatibleTiers": ["tier-c", "tier-d"],
    "minDeviceScore": 65,
    "requiredHardware": {
      "minMemoryMB": 16384,
      "minStorageMB": 5120,
      "requireGPU": true,
      "minVRAM_MB": 2048,
      "requireCUDA": false,
      "requireDocker": true
    },
    "incompatibleWith": ["legacy-3d-viewer"]
  }
}
```

---

## 插件生命周期钩子

插件可以在关键生命周期节点执行自定义脚本。

### 钩子类型

| 钩子 | 触发时机 | 超时 | 失败处理 |
|------|---------|------|---------|
| `onInstall` | 插件安装完成后 | 60 秒 | 回滚安装 |
| `onUninstall` | 插件卸载前 | 30 秒 | 继续卸载 |
| `onEnable` | 插件启用时 | 15 秒 | 禁用插件 |
| `onDisable` | 插件禁用前 | 15 秒 | 继续禁用 |

### 钩子脚本规范

#### Python 钩子 (后端)

```python
# backend/hooks/on_install.py
"""
插件安装钩子
环境变量:
  - PLUGIN_ID: 插件 ID
  - PLUGIN_VERSION: 插件版本
  - PLUGIN_DIR: 插件安装目录
  - DATA_DIR: 插件数据目录
"""

import os
import sys
from pathlib import Path

def main():
    plugin_dir = Path(os.environ['PLUGIN_DIR'])
    data_dir = Path(os.environ['DATA_DIR'])
    
    # 创建数据目录
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化数据库
    # (如果 manifest 声明了 migrations，会自动执行)
    
    # 下载额外资源
    # download_resources(data_dir)
    
    print(f"✓ {os.environ['PLUGIN_ID']} 安装完成")
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

#### JavaScript 钩子 (Electron)

```javascript
// electron/hooks/on-install.js
/**
 * 插件安装钩子
 * @param {Object} context - 上下文对象
 * @param {string} context.pluginId - 插件 ID
 * @param {string} context.pluginDir - 插件安装目录
 * @param {string} context.dataDir - 插件数据目录
 * @param {Function} context.log - 日志函数
 * @returns {Promise<void>}
 */
module.exports = async function onInstall(context) {
  const { pluginId, pluginDir, dataDir, log } = context;
  
  log(`正在初始化 ${pluginId}...`);
  
  // 创建必要的目录
  const fs = require('fs').promises;
  await fs.mkdir(dataDir, { recursive: true });
  
  // 注册 IPC 处理器
  // await registerIPCHandlers();
  
  log(`✓ ${pluginId} 初始化完成`);
};
```

### 钩子执行环境

- **工作目录**: 插件安装目录
- **环境变量**: 
  - `PLUGIN_ID`, `PLUGIN_VERSION`, `PLUGIN_DIR`, `DATA_DIR`
  - `PLATFORM` (win32/darwin/linux)
  - `ARCH` (x64/arm64)
- **可用模块**: 
  - Python: 标准库 + 已安装的依赖
  - Node.js: Electron 内置模块 + 插件 `node_modules/`
- **权限**: 与主进程相同（受 manifest `permissions` 限制）

---

## 打包规范

### ZIP 压缩参数

```bash
# 使用标准 ZIP 格式（非 ZIP64）
zip -r {plugin-id}-{version}-{platform}.mxp \
  -x "*.git*" \
  -x "*.DS_Store" \
  -x "__pycache__/*" \
  -x "*.pyc" \
  -x "node_modules/*" \
  -x ".env*" \
  -x "test-results/*" \
  -x "coverage/*" \
  -x "*.log" \
  .
```

### 压缩级别

- **推荐**: `-6` (平衡速度和大小)
- **最大压缩**: `-9` (发布时使用)
- **快速打包**: `-1` (开发测试)

### 排除规则

以下文件/目录**不应**包含在插件包中：

```
.git/
.gitignore
.vscode/
.idea/
__pycache__/
*.pyc
*.pyo
node_modules/
.env
.env.*
*.log
.DS_Store
Thumbs.db
test-results/
coverage/
dist/
build/
*.swp
*.swo
*~
```

### 文件大小限制

| 类型 | 限制 | 说明 |
|------|------|------|
| 单个文件 | 500 MB | 超过需分片或使用外部 CDN |
| 插件包总大小 | 2 GB | 超过需优化或使用流式下载 |
| manifest.json | 50 KB | 元数据应保持精简 |
| icon.png | 1 MB | 推荐 256x256 PNG |

---

## 签名与验证

### 数字签名机制

插件包支持 ECDSA (secp256k1) 数字签名，确保插件来源可信和完整性。

### 签名流程

```bash
# 1. 生成密钥对（插件开发者）
openssl ecparam -genkey -name secp256k1 -out private-key.pem
openssl ec -in private-key.pem -pubout -out public-key.pem

# 2. 计算 manifest.json 的 SHA-256 哈希
sha256sum manifest.json > manifest.sha256

# 3. 签名 manifest
openssl dgst -sha256 -sign private-key.pem \
  -out signatures/manifest.sig manifest.json

# 4. 计算整个包的 SHA-256 哈希（排除 signatures/ 目录）
zip -d plugin.mxp "signatures/*"
sha256sum plugin.mxp > package.sha256

# 5. 签名包
openssl dgst -sha256 -sign private-key.pem \
  -out signatures/package.sig plugin.mxp

# 6. 重新打包（包含签名）
zip -u plugin.mxp signatures/*
```

### 验证流程

```python
# backend/core/plugin_signature.py
import hashlib
import zipfile
from ecdsa import VerifyingKey, SECP256k1

def verify_plugin_signature(mxp_path: str, public_key_pem: str) -> bool:
    """验证插件包签名"""
    
    # 1. 提取签名文件
    with zipfile.ZipFile(mxp_path, 'r') as zf:
        manifest_sig = zf.read('signatures/manifest.sig')
        package_sig = zf.read('signatures/package.sig')
        manifest_data = zf.read('manifest.json')
    
    # 2. 加载公钥
    vk = VerifyingKey.from_pem(public_key_pem)
    
    # 3. 验证 manifest 签名
    if not vk.verify(manifest_sig, manifest_data, hashlib.sha256):
        return False
    
    # 4. 验证包签名（需临时移除签名文件）
    # ... (实现略)
    
    return True
```

### 信任链

```
iMato 官方插件
  → 使用 iMato 官方私钥签名
  → 公钥内置于客户端
  
认证开发者插件
  → 开发者使用自己的私钥签名
  → 公钥在 iMato 插件商店注册
  → 客户端从商店 API 获取公钥
  
第三方插件
  → 无签名或自签名
  → 安装时显示警告
  → 用户需手动确认
```

---

## 版本控制

### 语义化版本 (SemVer)

遵循 [Semantic Versioning 2.0.0](https://semver.org/) 规范：

```
主版本号.次版本号.修订号[-预发布标识]

示例:
1.0.0          # 首个稳定版本
1.2.3          # 向后兼容的功能新增和 bug 修复
2.0.0          # 不兼容的 API 修改
1.0.0-beta.1   # Beta 预发布版本
1.0.0-alpha.0  # Alpha 预发布版本
```

### 版本升级规则

| 变更类型 | 版本变化 | 示例 |
|---------|---------|------|
| 不兼容的 API 变更 | MAJOR++ | 1.5.2 → 2.0.0 |
| 向后兼容的功能新增 | MINOR++ | 1.5.2 → 1.6.0 |
| 向后兼容的 bug 修复 | PATCH++ | 1.5.2 → 1.5.3 |
| 预发布版本 | 添加后缀 | 1.6.0 → 1.6.0-beta.1 |

### 版本兼容性矩阵

```
客户端版本 vs 插件 manifestVersion

客户端 \ manifest | 1.0 | 2.0 | 3.0
------------------|-----|-----|-----
v1.x              |  ✓  |  ✗  |  ✗
v2.x              |  ✓  |  ✓  |  ✗
v3.x              |  ✓  |  ✓  |  ✓

规则: 客户端向后兼容旧版 manifest
```

---

## 示例插件包

### 示例 1: 简单工具插件 (Tier A)

```
markdown-editor-1.0.0-all.mxp
├── manifest.json
├── README.md
├── icon.png
├── frontend/
│   ├── module.ts
│   ├── components/
│   │   ├── markdown-editor.component.ts
│   │   ├── markdown-editor.component.html
│   │   └── markdown-editor.component.scss
│   └── assets/
│       └── i18n/
│           ├── zh-CN.json
│           └── en-US.json
└── docs/
    └── USER_GUIDE.md
```

**manifest.json 摘要**:
```json
{
  "id": "markdown-editor",
  "name": "Markdown 编辑器",
  "version": "1.0.0",
  "deviceCompatibility": {
    "compatibleTiers": ["tier-a", "tier-b", "tier-c", "tier-d"],
    "minDeviceScore": 0
  },
  "entryPoints": {
    "frontend": {
      "module": "frontend/module.ts",
      "components": [{
        "selector": "app-markdown-editor",
        "file": "frontend/components/markdown-editor.component.ts"
      }]
    }
  },
  "permissions": []
}
```

### 示例 2: AI 训练插件 (Tier D)

```
ml-training-studio-2.1.0-win32-x64.mxp
├── manifest.json
├── README.md
├── LICENSE
├── icon.png
├── backend/
│   ├── routes/
│   │   └── ml_training_routes.py
│   ├── services/
│   │   ├── training_service.py
│   │   └── model_service.py
│   ├── models/
│   │   └── training_job_model.py
│   ├── tasks/
│   │   └── training_tasks.py
│   ├── migrations/
│   │   └── versions/
│   │       └── 001_initial.py
│   ├── hooks/
│   │   ├── on_install.py
│   │   └── on_uninstall.py
│   └── requirements.txt
├── frontend/
│   ├── module.ts
│   ├── components/
│   │   ├── training-dashboard.component.ts
│   │   ├── training-dashboard.component.html
│   │   └── training-dashboard.component.scss
│   └── services/
│       └── training.service.ts
├── electron/
│   ├── main.js
│   └── ipc-handlers.js
├── python-deps/
│   ├── wheels/
│   │   ├── torch-2.1.0-cp311-cp311-win_amd64.whl
│   │   └── torchvision-0.16.0-cp311-cp311-win_amd64.whl
│   └── requirements-installed.txt
├── resources/
│   └── models/
│       └── pretrained-resnet50.onnx
└── signatures/
    ├── manifest.sig
    └── package.sig
```

**manifest.json 摘要**:
```json
{
  "id": "ml-training-studio",
  "name": "ML 训练工作室",
  "version": "2.1.0",
  "deviceCompatibility": {
    "compatibleTiers": ["tier-d"],
    "minDeviceScore": 80,
    "requiredHardware": {
      "minMemoryMB": 32768,
      "minStorageMB": 20480,
      "requireGPU": true,
      "minVRAM_MB": 6144,
      "requireCUDA": true
    }
  },
  "entryPoints": {
    "backend": {
      "routes": [{
        "file": "backend/routes/ml_training_routes.py",
        "prefix": "/api/v1/ml-training",
        "tier": 3
      }],
      "services": [{
        "name": "TrainingService",
        "file": "backend/services/training_service.py",
        "autoStart": true
      }],
      "migrations": true,
      "hooks": {
        "onInstall": "backend/hooks/on_install.py",
        "onUninstall": "backend/hooks/on_uninstall.py"
      }
    },
    "frontend": {
      "module": "frontend/module.ts",
      "menuItems": [{
        "label": "ML 训练",
        "route": "/ml-training",
        "icon": "model_training"
      }]
    },
    "electron": {
      "main": "electron/main.js",
      "ipcHandlers": ["ml-training:start", "ml-training:stop"]
    }
  },
  "dependencies": {
    "python": [
      "torch>=2.0.0",
      "torchvision>=0.15.0",
      "tensorboard>=2.12.0"
    ]
  },
  "permissions": [
    "filesystem:read",
    "filesystem:write",
    "gpu:compute",
    "database:read",
    "database:write",
    "electron:ipc"
  ]
}
```

---

## 常见问题

### Q1: 插件包应该包含 `node_modules/` 吗？

**A**: 不应该。前端代码通过 Angular 编译后打包，Electron 代码使用内置模块。如果确实需要第三方 npm 包，应在安装时通过 `onInstall` 钩子安装。

### Q2: Python 依赖如何处理？

**A**: 有三种方式：

1. **简单依赖**: 在 `manifest.json` → `dependencies.python` 中声明，安装时自动 pip install
2. **复杂依赖**: 在 `python-deps/wheels/` 中包含 .whl 文件，离线安装
3. **系统依赖**: 在 `dependencies.system` 中声明，由安装器检查

### Q3: 如何支持多平台？

**A**: 

- **纯代码插件**: 使用 `-all.mxp` 后缀，跨平台通用
- **含原生模块**: 为每个平台打包独立的 .mxp 文件
- **条件加载**: 在代码中检测平台，加载对应模块

```javascript
// electron/main.js
const platform = process.platform;
const arch = process.arch;

if (platform === 'win32' && arch === 'x64') {
  require('./native/win32-x64/module.node');
} else if (platform === 'darwin' && arch === 'arm64') {
  require('./native/darwin-arm64/module.node');
}
```

### Q4: 插件如何访问数据库？

**A**: 

1. 在 `permissions` 中声明 `database:read` 和/或 `database:write`
2. 在 `entryPoints.backend.services` 中声明服务
3. 服务通过依赖注入获取数据库 Session

```python
# backend/services/my_plugin_service.py
from database.session import get_db

class MyPluginService:
    def __init__(self, db_session):
        self.db = db_session
    
    def get_data(self):
        return self.db.query(MyModel).all()
```

### Q5: 如何调试插件？

**A**: 

1. **开发模式**: 将插件目录符号链接到 `~/.imato/plugins/{plugin-id}/dev/`
2. **热重载**: 修改前端代码后刷新页面，修改后端代码后重启服务
3. **日志**: 使用 `console.log()` (Electron) 或 `logging` (Python)，日志输出到开发者工具

### Q6: 插件可以依赖其他插件吗？

**A**: 可以。在 `dependencies.plugins` 中声明：

```json
{
  "dependencies": {
    "plugins": [
      {
        "id": "base-ml-framework",
        "version": "^1.0.0",
        "optional": false
      }
    ]
  }
}
```

安装器会自动先安装依赖插件。

### Q7: 如何卸载插件并清理数据？

**A**: 

1. 在 `backend/hooks/on_uninstall.py` 中清理数据
2. 用户可选择是否保留数据（`keepData` 选项）

```python
# backend/hooks/on_uninstall.py
import os
from pathlib import Path

def main():
    data_dir = Path(os.environ['DATA_DIR'])
    keep_data = os.environ.get('KEEP_DATA', 'false') == 'true'
    
    if not keep_data:
        # 清理数据库表
        # 清理文件
        import shutil
        shutil.rmtree(data_dir, ignore_errors=True)
    
    return 0
```

---

## 附录

### A. 插件 ID 命名规则

- 小写字母、数字、连字符
- 以字母或数字开头
- 3-64 个字符
- 不能使用下划线、空格、特殊字符
- 推荐格式: `{功能}-{子功能}` 或 `{组织}-{功能}`

**有效示例**:
- `ai-coding-assistant`
- `ar-chemistry-lab`
- `ml-training-studio`
- `data-visualizer`

**无效示例**:
- `AI_Coding` (包含大写字母和下划线)
- `my plugin` (包含空格)
- `a` (太短)
- `-plugin` (以连字符开头)

### B. 权限说明

| 权限 | 说明 | 风险等级 |
|------|------|---------|
| `filesystem:read` | 读取本地文件 | 低 |
| `filesystem:write` | 写入本地文件 | 中 |
| `network:external` | 访问外部网络 | 中 |
| `database:read` | 读取数据库 | 低 |
| `database:write` | 写入数据库 | 高 |
| `electron:ipc` | 使用 IPC 通信 | 低 |
| `electron:native` | 调用原生 API | 高 |
| `gpu:compute` | 使用 GPU 计算 | 中 |
| `docker:access` | 访问 Docker | 高 |
| `redis:access` | 访问 Redis | 中 |
| `system:info` | 读取系统信息 | 低 |

### C. 参考文档

- [插件化模块交付需求文档](./PLUGIN_BASED_MODULE_DELIVERY.md)
- [懒加载架构设计](./MODULAR_LAZY_LOADING_ARCHITECTURE.md)
- [插件开发指南](./PLUGIN_DEVELOPMENT_GUIDE.md) (待创建)
- [插件商店 UI 设计](./PLUGIN_STORE_UI_DESIGN.md) (Phase 3)

---

**文档版本**: 1.0.0  
**最后更新**: 2026-06-06  
**维护者**: iMato 架构团队
