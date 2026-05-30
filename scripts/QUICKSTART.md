# iMato 营销页面监控 - 快速开始指南

## 🚀 5分钟快速上手

### 步骤 1: 进入脚本目录

```bash
cd scripts
```

### 步骤 2: 安装依赖

```bash
npm install
```

这将自动安装 Playwright 和所需的浏览器驱动。

### 步骤 3: 确保应用正在运行

```bash
# 在另一个终端窗口中
cd ..
npm start
```

等待应用启动完成（通常需要 30-60 秒）。

### 步骤 4: 运行监控

```bash
# 方式 1: 使用npm脚本
npm run monitor

# 方式 2: 直接运行
node marketing-page-monitor.js

# 方式 3: Windows用户双击运行
双击 run-monitor.bat
```

### 步骤 5: 查看结果

监控完成后，会自动打开报告：

```bash
# 报告位置
monitoring-reports/
  ├── monitor-report-{timestamp}.html  ← 在浏览器中打开这个文件
  ├── monitor-report-{timestamp}.json
  └── screenshots/
      └── ...页面截图...
```

## 🎯 常用命令速查

### 基础监控

```bash
# 快速检查所有页面
npm run monitor

# 可视化模式（查看浏览器操作）
npm run monitor:visible

# 测试移动端显示
npm run monitor:mobile

# 完整测试（桌面+移动）
npm run monitor:all
```

### 高级选项

```bash
# 测试生产环境
node marketing-page-monitor.js --base-url=https://your-domain.com

# 增加超时时间（适用于慢速网络）
node marketing-page-monitor.js --timeout=60000

# 自定义输出文件名
node marketing-page-monitor.js --output=my-report.json

# 组合选项
node marketing-page-monitor.js --mobile --timeout=60000 --output=mobile-test.json
```

### 自动修复

```bash
# 1. 先运行监控生成报告
npm run monitor

# 2. 分析并应用自动修复（干运行模式）
node marketing-page-fixes.js monitoring-reports/monitor-report-xxx.json --dry-run

# 3. 确认无误后，应用修复
node marketing-page-fixes.js monitoring-reports/monitor-report-xxx.json
```

## 📊 解读报告

### 报告摘要

```
📊 监控报告摘要
========================================
⏰ 测试时间: 2024-01-01T00:00:00.000Z
📄 监控页面: 9 个 (关键页面: 5)
❌ 总错误数: 3
⚠️  总警告数: 5
🔴 关键错误: 2
✅ 成功率: 66.67%
⚡ 平均加载时间: 1250ms
```

**关键指标：**
- ✅ **成功率**: 目标 >95%
- ⚡ **加载时间**: 目标 <3000ms
- 🔴 **关键错误**: 必须为 0

### 错误类型说明

| 类型 | 说明 | 优先级 |
|------|------|--------|
| `js_error` | JavaScript运行时错误 | 🔴 高 |
| `resource_error` | 资源加载失败(404等) | 🔴 高 |
| `http_error` | HTTP请求错误 | 🟡 中 |
| `console_error` | 控制台错误 | 🟡 中 |
| `console_warning` | 控制台警告 | 🟢 低 |

### 常见问题及处理

#### ❌ JavaScript错误

**示例**: `Cannot read property 'length' of undefined`

**处理**:
1. 查看错误堆栈定位文件
2. 使用自动修复工具（推荐）
3. 手动添加空值检查

```bash
# 自动修复
node marketing-page-fixes.js monitoring-reports/xxx.json
```

#### ❌ 资源加载失败(404)

**示例**: `Failed to load resource: 404 images/logo.png`

**处理**:
1. 检查文件路径是否正确
2. 确认文件存在于public/assets目录
3. 添加备用图片

#### ⚠️ 控制台警告

**处理**:
- 非阻塞问题，可后续优化
- 记录到技术债务，安排修复

## 🔧 故障排除

### 问题 1: Playwright安装失败

```bash
# 手动安装
npm install playwright
npx playwright install

# 如果仍然失败，尝试清除缓存
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### 问题 2: 端口被占用

```bash
# 使用自定义端口
node marketing-page-monitor.js --base-url=http://localhost:3000
```

### 问题 3: 测试超时

```bash
# 增加超时时间
node marketing-page-monitor.js --timeout=60000
```

### 问题 4: 权限错误（Linux/Mac）

```bash
# 添加执行权限
chmod +x marketing-page-monitor.js
chmod +x marketing-page-fixes.js
```

## 🛡️ 安全建议

### 自动修复注意事项

1. **总是先使用 `--dry-run`**
   ```bash
   node marketing-page-fixes.js report.json --dry-run
   ```

2. **检查备份文件**
   - 自动修复会创建 `.backup-timestamp` 文件
   - 如需回滚，恢复备份文件即可

3. **代码审查**
   - 自动修复后，务必进行代码审查
   - 运行测试验证功能正常

### 配置管理

**敏感配置**: `monitor-config.json`

```json
{
  "notifications": {
    "enabled": true,
    "webhookUrl": "YOUR_WEBHOOK_URL",  // 生产环境使用环境变量
    "notifyOnCriticalOnly": true
  }
}
```

**环境变量方式**:
```bash
export MONITOR_WEBHOOK_URL="your-webhook-url"
```

## 🔄 集成到开发流程

### 开发阶段

```bash
# 每次修改营销页面后运行
npm run monitor
```

### 提交代码前

```bash
# 在git hooks中添加
npm run monitor

# 如果有错误，阻止提交
if [ $? -ne 0 ]; then
  echo "❌ 监控发现错误，请修复后再提交"
  exit 1
fi
```

### 部署前检查

```bash
# 测试生产环境
node marketing-page-monitor.js --base-url=https://production.com

# 确认无错误后再部署
```

## 📚 下一步

- 📖 [完整文档](README.md) - 详细了解所有功能
- 🔧 [配置指南](monitor-config.json) - 自定义监控配置
- 💻 [API文档](marketing-page-monitor.js) - 集成到CI/CD
- 🤝 [贡献指南](../CONTRIBUTING.md) - 参与项目开发

## 🆘 需要帮助？

- 查看 [故障排除](#故障排除) 部分
- 提交 Issue: 项目GitHub Issues
- 联系团队: support@imato.com

---

**快速提示**: 将以下命令添加到 `package.json` 方便使用：

```json
{
  "scripts": {
    "monitor": "cd scripts && npm run monitor",
    "monitor:all": "cd scripts && npm run monitor:all",
    "monitor:fix": "cd scripts && node marketing-page-fixes.js"
  }
}
```

现在你可以直接在项目根目录运行：

```bash
npm run monitor
```
