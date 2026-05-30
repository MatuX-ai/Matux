# iMato Electron Desktop 应用

iMato Windows 桌面应用程序，基于 Electron 框架实现。

## 📦 项目结构

```
electron/
├── main.js           # Electron 主进程
├── preload.js        # 预加载脚本
├── package.json      # NPM 配置
└── README.md         # 本文档
```

## 🚀 快速开始

### 安装依赖

```bash
cd electron
npm install
```

### 开发模式运行

```bash
# 1. 启动前端开发服务器（在另一个终端）
cd ..
ng serve

# 2. 启动 Electron（在当前终端）
cd electron
npm start
```

### 构建安装包

```bash
# 构建 Windows 安装包
npm run build

# 构建便携版（无需安装）
npm run build:portable
```

生成的安装包位于 `dist/` 目录。

## 🔧 核心功能

### 1. 后端服务管理

- ✅ 自动启动 Python 后端服务
- ✅ 等待后端就绪后再显示窗口
- ✅ 优雅关闭后端进程
- ✅ 健康检查机制

### 2. 进程通信

通过 IPC（进程间通信）实现前后端交互：

```typescript
// 在 Angular 组件中使用
const backendUrl = await window.electronAPI.getBackendUrl();
const isHealthy = await window.electronAPI.healthCheck();
```

### 3. 离线运行

所有资源本地化，无需网络连接即可使用。

## 📝 配置说明

### 环境变量

- `NODE_ENV=development`: 开发模式（打开 DevTools）
- `NODE_ENV=production`: 生产模式（使用本地文件）

### 后端配置

- 默认端口：`8000`
- 默认地址：`http://localhost:8000`
- 健康检查端点：`/health`

## 🛠️ 故障排除

### 问题 1: 后端启动失败

**症状**: 应用闪退或显示"后端服务启动失败"

**解决方案**:
1. 检查 Python 是否安装
2. 确认后端依赖已安装：`pip install -r requirements.txt`
3. 查看控制台错误日志

### 问题 2: 窗口显示空白

**症状**: Electron 窗口打开但内容为空

**解决方案**:
1. 检查前端是否正在运行：`ng serve`
2. 确认端口正确（默认 4200）
3. 检查浏览器控制台错误

### 问题 3: 打包后无法运行

**症状**: 双击无反应或报错

**解决方案**:
1. 确保打包完整：`npm run build`
2. 检查防火墙设置
3. 以管理员身份运行

## 📊 技术栈

- **Electron**: v28.0.0
- **electron-builder**: v24.9.1
- **Node.js**: v18+
- **Python**: v3.9+

## 🔐 安全特性

- ✅ 禁用 nodeIntegration
- ✅ 启用 contextIsolation
- ✅ 使用 preload 脚本桥接
- ✅ 限制 IPC 通信频道

## 📄 许可证

GPL-3.0 License

---

**开发团队**: iMatu Development Team  
**版本**: 1.0.0  
**更新时间**: 2026-03-14
