# iMato 营销页面监控工具

一套完整的营销页面自动化监控和修复工具，用于检测JavaScript错误、资源加载问题，并提供自动修复建议。

## 🚀 快速开始

### 前置条件

- Node.js 16+
- npm 或 yarn

### 安装依赖

```bash
cd scripts
npm install
```

第一次运行时会自动安装 Playwright 浏览器驱动。

## 📋 监控脚本使用

### 基本用法

```bash
# 监控所有营销页面（无头模式）
node marketing-page-monitor.js

# 可视化模式（查看浏览器操作）
node marketing-page-monitor.js --no-headless

# 移动端测试
node marketing-page-monitor.js --mobile

# 自定义输出文件
node marketing-page-monitor.js --output=my-report.json

# 测试生产环境
node marketing-page-monitor.js --base-url=https://your-domain.com

# 自定义超时时间
node marketing-page-monitor.js --timeout=60000
```

### 命令行选项

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `--headless` | 无头模式（不显示浏览器） | `true` |
| `--no-headless` | 可视化模式 | - |
| `--mobile` | 移动端视口测试 | `false` |
| `--timeout` | 页面加载超时时间（毫秒） | `30000` |
| `--output` | 报告输出路径 | `monitoring-reports/monitor-report-{timestamp}.json` |
| `--base-url` | 测试的基础URL | `http://localhost:4200` |

### npm 快捷命令

```bash
# 监控所有页面
npm run monitor

# 可视化监控
npm run monitor:visible

# 移动端监控
npm run monitor:mobile

# 执行所有测试（桌面+移动）
npm run monitor:all
```

## 🔧 自动修复工具

### 基本用法

```bash
# 分析并应用修复
node marketing-page-fixes.js <report-file>

# 仅分析，不应用修复
node marketing-page-fixes.js <report-file> --dry-run

# 示例
node marketing-page-fixes.js ../monitoring-reports/monitor-report-12345.json
```

### 支持的自动修复

| 修复类型 | 说明 | 适用场景 |
|----------|------|----------|
| `null-check` | 添加可选链操作符（?.） | 访问未定义对象属性 |
| `function-check` | 函数调用前检查类型 | 调用不存在的方法 |
| `missing-image` | 添加图片加载失败回退 | 图片404错误 |
| `unhandled-promise` | 添加try-catch处理 | 未处理的Promise拒绝 |
| `event-listener-cleanup` | 添加事件监听器清理注释 | 内存泄漏风险 |

### 修复流程

1. **加载报告**: 读取监控生成的JSON报告
2. **分析错误**: 识别可自动修复的问题
3. **生成计划**: 创建修复计划，包含置信度评估
4. **创建备份**: 自动备份原始文件
5. **应用修复**: 智能应用修复模式
6. **生成报告**: 记录所有修改操作

## 📊 监控报告

### 报告结构

监控脚本生成JSON和HTML两种格式的报告：

```json
{
  "summary": {
    "timestamp": "2024-01-01T00:00:00.000Z",
    "totalPages": 9,
    "totalErrors": 3,
    "totalWarnings": 5,
    "successRate": "66.67%",
    "avgLoadTime": "1250ms"
  },
  "results": [
    {
      "name": "营销首页",
      "path": "/marketing",
      "status": "success",
      "errors": [],
      "warnings": [],
      "performance": {
        "loadTime": 1200,
        "domContentLoaded": 800
      },
      "fixSuggestions": []
    }
  ]
}
```

### HTML报告

HTML报告包含：
- 📊 监控摘要仪表板
- 📄 每个页面的详细结果
- ❌ 错误和警告详情
- 🔧 具体的修复建议（含代码示例）
- 📸 页面截图

## 🎯 监控内容

### 错误类型

1. **JavaScript错误**
   - 未定义变量/属性
   - 类型错误
   - 未处理的Promise拒绝
   - 异步错误

2. **资源加载错误**
   - 图片404
   - CSS/JS文件加载失败
   - API请求失败
   - 跨域(CORS)错误

3. **性能问题**
   - 加载时间过长
   - 资源阻塞渲染
   - 内存泄漏迹象

### 可访问性检查

- ARIA标签完整性
- 键盘导航支持
- 屏幕阅读器兼容性

### 移动端检查

- 响应式布局
- 触摸交互
- 视口配置

## 🔍 故障排除

### Playwright安装失败

```bash
# 手动安装Playwright
npm install playwright
npx playwright install
```

### 端口被占用

```bash
# 修改默认端口
node marketing-page-monitor.js --base-url=http://localhost:3000
```

### 超时问题

```bash
# 增加超时时间
node marketing-page-monitor.js --timeout=60000
```

### 权限问题（Linux/Mac）

```bash
# 添加执行权限
chmod +x marketing-page-monitor.js
chmod +x marketing-page-fixes.js
```

## 📂 输出文件

### 监控报告

```
monitoring-reports/
├── monitor-report-{timestamp}.json    # 详细数据
├── monitor-report-{timestamp}.html    # HTML报告
└── screenshots/
    ├── 营销首页-{timestamp}.png
    ├── 产品展示页-{timestamp}.png
    └── ...
```

### 修复报告

```
monitoring-reports/
├── fix-report-{timestamp}.json        # 修复详情
├── fix-script-{timestamp}.sh          # 修复脚本
└── *.backup-{timestamp}               # 文件备份
```

## 🔄 集成到CI/CD

### GitHub Actions 示例

```yaml
name: Marketing Pages Monitor

on:
  schedule:
    - cron: '0 9 * * *'  # 每天9点执行
  workflow_dispatch:

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd scripts
          npm install
      
      - name: Run monitor
        run: |
          cd scripts
          npm run monitor:all
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: monitoring-reports
          path: monitoring-reports/
```

## 🛡️ 安全注意事项

1. **备份文件**: 自动修复会创建备份，可随时回滚
2. **置信度检查**: 只应用置信度>70%的修复
3. **干运行模式**: 先使用`--dry-run`预览修改
4. **代码审查**: 自动修复后务必进行代码审查

## 📚 最佳实践

### 监控策略

- **开发阶段**: 每次重大修改后运行
- **预发布**: 部署前全面检查
- **生产环境**: 定期监控（每日/每周）

### 错误处理

1. **优先处理**: 关键页面（首页、产品、定价）的错误
2. **分类处理**: 按错误类型和影响范围排序
3. **验证修复**: 修复后重新运行监控确认

### 性能优化

- 设置合理的超时时间
- 无头模式提高执行速度
- 并行执行多个页面（高级用法）

## 🤝 贡献指南

欢迎提交问题和功能建议！

## 📄 许可证

GPL-3.0
