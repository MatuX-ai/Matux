# iMato Windows 本地版 - 开发文档

**版本**: v1.0  
**类型**: 免费安装 + Token 消耗模式  
**目标用户**: 个人教师、小型培训机构

---

## 📦 项目说明

Windows 本地版是一个完全离线的桌面应用，基于 Electron 技术构建。用户免费下载安装，使用 AI 功能时按 Token 消耗量计费。

### **核心特点**
- ✅ 一键安装，无需复杂配置
- ✅ 完全离线运行（AI 调用除外）
- ✅ 本地数据库（SQLite）
- ✅ 自动更新机制
- ✅ AI 功能按需付费

---

## 🏗️ 目录结构

```
windows_local/
├── electron/                   # Electron 主应用
│   ├── main.js                # 主进程入口
│   ├── preload.js             # 预加载脚本
│   ├── package.json           # Electron 配置
│   └── assets/                # 图标和启动画面
│       ├── icon.ico
│       └── splash.html
│
├── installer/                  # NSIS 安装脚本
│   ├── installer.nsi          # 安装器配置
│   └── uninstaller.nsi        # 卸载器配置
│
├── docs/                       # 文档
│   ├── INSTALLATION.md        # 安装指南
│   ├── USER_GUIDE.md          # 用户手册
│   └── TOKEN_GUIDE.md         # Token 使用说明
│
└── electron-builder.yml        # 打包配置文件
```

---

## 🚀 开发流程

### **Week 3: Electron 开发计划**

#### **任务 3.1: 初始化 Electron 项目**
```bash
cd pricing_modes/windows_local/electron
npm init -y
npm install electron --save-dev
npm install electron-builder --save-dev
```

#### **任务 3.2: 创建主进程文件**
- `main.js` - 主进程入口
- `preload.js` - 预加载脚本
- 窗口管理、菜单、系统托盘

#### **任务 3.3: 集成后端服务**
- 使用 Python 打包工具（PyInstaller）
- 主进程启动时自动运行后端
- 健康检查和错误重启

#### **任务 3.4: 打包配置**
- 配置 `electron-builder.yml`
- NSIS 安装脚本定制
- 代码签名证书（可选）

---

## 📦 安装包特性

### **安装流程**
1. 下载 `iMato-Windows-Setup.exe` (~300MB)
2. 双击运行安装向导
3. 选择安装路径（默认 C:\Program Files\iMato）
4. 创建桌面快捷方式
5. 完成安装并首次启动

### **包含内容**
- Electron 运行时
- Python 3.11 精简版
- SQLite 数据库引擎
- Angular前端静态文件
- FastAPI 后端服务
- 示例课程和数据

---

## 💰 Token 计费说明

### **套餐价格**
| 套餐类型 | Token 数量 | 价格 | 有效期 |
|---------|-----------|------|--------|
| 免费版 | 100/月 | ¥0 | 每月刷新 |
| 标准包 | 1000 | ¥99 | 1 年 |
| 高级包 | 3000 | ¥249 | 1 年 |
| 企业包 | 10000 | ¥699 | 1 年 |

### **消耗场景**
- AI 课程生成：50-500 tokens/次
- AI 对话辅导：10 tokens/100 字符
- 智能推荐：20 tokens/次
- 语音识别：30 tokens/分钟

详见：`docs/TOKEN_GUIDE.md`

---

## 🔧 技术栈

- **桌面框架**: Electron 27+
- **打包工具**: electron-builder
- **安装器**: NSIS (Nullsoft Scriptable Install System)
- **Python 打包**: PyInstaller
- **数据库**: SQLite 3
- **自动更新**: electron-updater

---

## 📞 支持与反馈

- **安装问题**: 查看 `docs/INSTALLATION.md`
- **使用帮助**: 查看 `docs/USER_GUIDE.md`
- **Token 充值**: 访问官网或应用内购买
- **技术支持**: support@imato.com

---

## 📄 许可协议

本软件为**免费软件**，但 AI 功能需消耗 Token。

- ✅ 可自由安装使用
- ✅ 基础功能完全免费
- ⚠️ AI 功能需购买 Token
- ❌ 禁止反向工程
- ❌ 禁止商业转售
