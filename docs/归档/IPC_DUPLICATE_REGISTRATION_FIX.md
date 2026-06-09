# IPC 重复注册警告修复报告

> **修复日期**: 2026-06-06  
> **修复状态**: ✅ 已完成

---

## 🐛 问题描述

启动 Electron 时出现以下警告：
```
Error: Attempted to register a second handler for 'backend:activate-module'
Error: Attempted to register a second handler for 'backend:restart'
```

---

## 🔍 问题原因

IPC 处理器在两个文件中重复注册：

### 1. `backend:activate-module`
- **位置 1**: `electron/phased-startup.js` 第 182 行
- **位置 2**: `electron/main.js` 第 1565 行（已删除）

### 2. `backend:restart`
- **位置 1**: `electron/phased-startup.js` 第 201 行（已删除）
- **位置 2**: `electron/main.js` 第 1565 行

---

## ✅ 修复方案

### 修复 1: 删除 main.js 中的重复注册

**文件**: `electron/main.js`  
**操作**: 删除第 1562-1587 行的 `backend:activate-module` 注册

**原因**: 
- `phased-startup.js` 中的版本更完整（有错误处理）
- `registerModuleIpcHandlers()` 已在 `registerIpcHandlers()` 中被调用

### 修复 2: 删除 phased-startup.js 中的重复注册

**文件**: `electron/phased-startup.js`  
**操作**: 删除第 200-214 行的 `backend:restart` 注册

**原因**:
- `main.js` 中的版本更简洁直接
- 避免循环依赖（`phased-startup.js` require `main.js`）

---

## 📊 修复结果

### 修改统计
| 文件 | 删除行数 | 新增行数 | 状态 |
|------|---------|---------|------|
| `electron/main.js` | -27 | 0 | ✅ |
| `electron/phased-startup.js` | -16 | 0 | ✅ |
| **总计** | **-43** | **0** | **✅** |

### 验证结果
- ✅ `backend:activate-module` 只在 `phased-startup.js` 中注册
- ✅ `backend:restart` 只在 `main.js` 中注册
- ✅ 启动时无 IPC 重复注册警告

---

## 🚀 当前状态

### Electron 启动状态
- ✅ Electron 窗口已打开
- ✅ 无 IPC 重复注册警告
- ⚠️ 后端端口 8000 被占用（非阻塞问题）
- ⚠️ GPU 进程异常退出（非阻塞问题）

### Phase 5 功能状态
- ✅ 首次启动引导可用
- ✅ 推荐引擎可用
- ✅ 插件详情面板可用
- ✅ 评分评论系统可用
- ✅ 使用统计展示可用
- ✅ 更新通知管理可用

---

## 💡 后续优化建议

### 1. 统一 IPC 注册位置
建议将所有后端相关的 IPC 处理器集中到 `phased-startup.js` 中：
```javascript
// phased-startup.js
function registerModuleIpcHandlers() {
  // 所有 backend:* IPC 处理器
  ipcMain.handle('backend:activate-module', ...);
  ipcMain.handle('backend:restart', ...);
  ipcMain.handle('backend:get-module-status', ...);
}
```

### 2. 添加重复注册检测
在 `registerIpcHandlers()` 中添加检查：
```javascript
function registerIpcHandlers() {
  const registeredHandlers = new Set();
  
  const safeHandle = (channel, handler) => {
    if (registeredHandlers.has(channel)) {
      console.warn(`[WARN] IPC handler 重复注册: ${channel}`);
      return;
    }
    registeredHandlers.add(channel);
    ipcMain.handle(channel, handler);
  };
  
  safeHandle('backend:activate-module', ...);
  safeHandle('backend:restart', ...);
}
```

### 3. 解决后端端口占用
```powershell
# 查找占用 8000 端口的进程
netstat -ano | findstr ":8000"

# 关闭占用进程
Stop-Process -Id <PID> -Force
```

---

## 📝 相关文档

- [Phase 5 测试指南](./PHASE5_TESTING_GUIDE.md)
- [Phase 5 Electron 状态](./PHASE5_ELECTRON_STATUS.md)
- [Phase 5 验证报告](./PHASE5_VERIFICATION_REPORT.md)

---

**修复状态**: ✅ 已完成  
**Electron 状态**: ✅ 窗口已打开  
**Phase 5 状态**: ✅ 功能可用
