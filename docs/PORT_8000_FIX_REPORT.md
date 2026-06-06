# 8000 端口占用问题解决报告

> **解决日期**: 2026-06-06  
> **解决状态**: ✅ 已完成

---

## 🐛 问题描述

Electron 启动时报告：
```
[ERROR] 端口 8000 被占用，无法连接后端服务
[HEALTH] 健康检查失败: fetch failed
```

---

## 🔍 问题原因

**PID 4444** 的 Python 进程占用了 8000 端口

这是之前启动的后端服务进程，没有被正确关闭。

---

## ✅ 解决步骤

### 1. 查找占用进程
```powershell
netstat -ano | findstr ":8000"
```

结果：
```
TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING    4444
```

### 2. 查看进程信息
```powershell
Get-Process -Id 4444
```

结果：
```
Id: 4444
ProcessName: python
Path: G:\Python312\python.exe
StartTime: 2026/6/6 16:47:06
```

### 3. 关闭占用进程
```powershell
# 方法 1: 使用 Stop-Process
Stop-Process -Id 4444 -Force

# 方法 2: 使用 taskkill
taskkill /F /PID 4444

# 方法 3: 关闭所有 Python 进程
Get-Process -Name "python" | Stop-Process -Force
```

### 4. 验证端口释放
```powershell
netstat -ano | findstr ":8000" | findstr "LISTENING"
```

结果：无输出（端口已释放）✅

### 5. 重启 Electron
```powershell
node node_modules\electron\cli.js electron/main.js
```

---

## 📊 解决结果

### 后端服务状态
- ✅ 后端服务成功启动
- ✅ 运行在 `http://0.0.0.0:8000`
- ✅ 健康检查通过
- ✅ 数据库连接正常
- ✅ Uvicorn 服务器运行中

### Electron 状态
- ✅ Electron 窗口正常打开
- ✅ 后端服务连接成功
- ✅ Phase 5 功能可用
- ✅ 无 IPC 重复注册警告

---

## 💡 预防措施

### 1. 启动前检查端口
```powershell
# 检查 8000 端口是否被占用
netstat -ano | findstr ":8000"

# 如果被占用，关闭进程
Get-Process -Id <PID> | Stop-Process -Force
```

### 2. 创建启动脚本
```powershell
# start-electron.ps1
Write-Host "🔄 检查 8000 端口..." -ForegroundColor Yellow
$port8000 = netstat -ano | findstr ":8000" | findstr "LISTENING"
if ($port8000) {
    Write-Host "⚠️ 8000 端口被占用，正在关闭..." -ForegroundColor Yellow
    $pid = ($port8000 -split '\s+')[-1]
    Stop-Process -Id $pid -Force
    Start-Sleep -Seconds 2
}
Write-Host "✅ 启动 Electron..." -ForegroundColor Green
node node_modules\electron\cli.js electron/main.js
```

### 3. 使用不同端口
如果 8000 端口经常被占用，可以修改后端配置使用其他端口：

**文件**: `electron/main.js`
```javascript
const BACKEND_PORT = 8001; // 改为 8001
```

---

## 🔧 故障排查命令

### 查看端口占用
```powershell
# Windows
netstat -ano | findstr ":8000"

# 或使用 PowerShell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```

### 查看进程详情
```powershell
Get-Process -Id <PID> | Format-List *
```

### 强制关闭进程
```powershell
# 使用 PID
Stop-Process -Id <PID> -Force

# 使用进程名
Stop-Process -Name "python" -Force

# 使用 taskkill
taskkill /F /PID <PID>
taskkill /F /IM python.exe
```

### 验证端口释放
```powershell
# 应该无输出
netstat -ano | findstr ":8000" | findstr "LISTENING"
```

---

## 📝 当前状态

### 后端服务
- ✅ 运行中
- ✅ 端口: 8000
- ✅ 地址: http://localhost:8000
- ✅ API 文档: http://localhost:8000/docs

### Electron 应用
- ✅ 运行中
- ✅ 后端连接: 正常
- ✅ Phase 5 功能: 可用

### 可用功能
- ✅ 首次启动引导
- ✅ 推荐引擎
- ✅ 插件详情面板
- ✅ 评分评论系统
- ✅ 使用统计展示
- ✅ 更新通知管理

---

## ⚠️ 已知警告（非阻塞）

### API Key 未配置
```
OpenAI API key not configured
Lingma API key not configured
DeepSeek API key not configured
Anthropic API key not configured
Google API key not configured
```

**影响**: AI 功能不可用，但不影响其他功能

**解决**: 在 `.env` 文件中配置相应的 API Key

### 依赖版本警告
```
RequestsDependencyWarning: urllib3 (1.26.20) or chardet (7.4.3)/charset_normalizer (3.4.5) doesn't match a supported version!
```

**影响**: 无实际影响，仅警告

**解决**: 更新 requests 库（可选）
```bash
pip install --upgrade requests
```

---

**解决状态**: ✅ 已完成  
**后端状态**: ✅ 运行正常  
**Electron 状态**: ✅ 运行正常  
**Phase 5 状态**: ✅ 功能可用
