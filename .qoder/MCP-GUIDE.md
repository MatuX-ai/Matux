# MatuX 项目 MCP 配置指南

## 📋 概述

本项目配置了 **browser-use** MCP 服务器，提供完整的浏览器自动化能力，专门适配 MatuX 的前端测试需求。

## 🎯 适用场景

### 1. **登录功能测试**
- ✅ 一键登录流程验证
- ✅ 测试账号自动登录
- ✅ 登录性能分析
- ✅ OAuth 流程测试（需要手动授权）

### 2. **UI 验证**
- ✅ 页面截图对比
- ✅ DOM 结构检查
- ✅ 组件渲染验证
- ✅ 响应式布局测试

### 3. **性能监控**
- ✅ API 请求耗时分析
- ✅ 页面加载时间测量
- ✅ Dashboard 数据加载验证
- ✅ 网络请求监控

### 4. **自动化测试**
- ✅ 端到端登录测试
- ✅ 仪表板功能验证
- ✅ 用户流程自动化

## 🚀 快速开始

### 方式一：使用 Browser Subagent（推荐）

```
使用 Browser subagent 执行自动化测试任务
```

### 方式二：手动调用 MCP 工具

```javascript
// 示例：测试一键登录
1. navigate_page("http://localhost:4200/auth/login")
2. take_screenshot()  // 确认登录页面
3. click(".test-login-button")  // 点击一键登录
4. wait_for({seconds: 3})  // 等待登录完成
5. navigate_page("http://localhost:4200/user/dashboard")
6. take_screenshot()  // 验证 Dashboard
```

## 📁 配置说明

### 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 学生 | test_student | TestStudent123! | 学习端主要测试 |
| 教师 | test_teacher | TestTeacher123! | 教师功能测试 |
| 管理员 | test_admin | TestAdmin123! | 管理功能测试 |

### API 端点

| 端点 | 方法 | 用途 |
|------|------|------|
| /api/v1/auth/token | POST | 获取认证 Token |
| /api/v1/auth/me | GET | 获取当前用户信息 |
| /api/v1/ai-edu/progress/stats | GET | 学习进度统计 |
| /api/v1/ai-edu/learning-sources | GET | 学习源列表 |
| /api/v1/courses/enrollments | GET | 课程列表 |

## 🔧 可用工具列表

### 导航与交互
| 工具 | 功能 | 示例 |
|------|------|------|
| navigate_page | 页面导航 | navigate_page({url: "http://localhost:4200"}) |
| click | 点击元素 | click({selector: ".login-button"}) |
| fill | 填写表单 | fill({selector: "#email", value: "test@example.com"}) |
| press_key | 按键操作 | press_key({key: "Enter"}) |
| hover | 悬停 | hover({selector: ".dropdown"}) |

### 验证与分析
| 工具 | 功能 | 示例 |
|------|------|------|
| take_screenshot | 页面截图 | take_screenshot() |
| take_snapshot | DOM 快照 | take_snapshot() |
| list_network_requests | 网络请求 | list_network_requests() |
| list_console_messages | 控制台消息 | list_console_messages() |
| evaluate_script | 执行 JS | evaluate_script({script: "localStorage.getItem('access_token')"}) |

### 辅助功能
| 工具 | 功能 | 示例 |
|------|------|------|
| wait_for | 等待 | wait_for({selector: ".dashboard-loaded"}) |
| handle_dialog | 处理弹窗 | handle_dialog({accept: true}) |
| list_pages | 页面列表 | list_pages() |
| select_page | 选择页面 | select_page({index: 1}) |

## 📊 预定义自动化场景

### 场景 1：一键登录验证
```javascript
// 完整的一键登录测试流程
navigate_page("http://localhost:4200/auth/login")
take_screenshot()
click(".test-login-button")
wait_for({seconds: 3})
navigate_page("http://localhost:4200/user/dashboard")
take_screenshot()
```

### 场景 2：登录性能分析
```javascript
// 分析登录各环节耗时
list_network_requests()  // 开始监控
click(".test-login-button")
// 分析 /api/v1/auth/token 请求
// 分析 /api/v1/auth/me 请求
// 生成性能报告
```

### 场景 3：Dashboard 数据验证
```javascript
// 验证 Dashboard 组件
navigate_page("http://localhost:4200/user/dashboard")
take_snapshot()  // 获取 DOM 结构
evaluate_script({script: `
  document.querySelectorAll('.stats-card').length
`})  // 检查统计卡片数量
list_console_messages()  // 检查控制台错误
```

## 🎓 高级用法

### 1. 检查认证状态
```javascript
evaluate_script({
  script: `
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user_data');
    return { token: !!token, user: user ? JSON.parse(user) : null };
  `
})
```

### 2. 测量页面加载时间
```javascript
const start = Date.now();
navigate_page("http://localhost:4200/user/dashboard")
wait_for({selector: ".student-dashboard"})
const loadTime = Date.now() - start;
console.log(`页面加载耗时: ${loadTime}ms`);
```

### 3. 批量截图对比
```javascript
navigate_page("http://localhost:4200/user/dashboard")
take_screenshot({filename: "dashboard-v1"})

// 修改代码后...
navigate_page("http://localhost:4200/user/dashboard")
take_screenshot({filename: "dashboard-v2"})

// 对比两个截图
```

## ⚠️ 注意事项

1. **开发服务器**：确保 `npm run start` 已运行（端口 4200）
2. **后端服务**：确保后端已启动（端口 8000）
3. **测试账号**：使用 `test_student` 账号进行学习端测试
4. **清理状态**：测试前建议清除浏览器缓存和 localStorage
5. **权限**：首次使用可能需要授权浏览器访问

## 🔍 故障排查

### 问题：MCP 工具无法连接浏览器
**解决方案**：
1. 确保有打开的浏览器标签页
2. 使用 `list_pages()` 确认浏览器连接
3. 重新打开浏览器标签页

### 问题：截图模糊
**解决方案**：
1. 使用 `take_snapshot()` 获取高清 DOM 快照
2. 调整浏览器缩放级别为 100%

### 问题：元素选择失败
**解决方案**：
1. 先用 `take_snapshot()` 查看当前页面结构
2. 使用 `evaluate_script` 调试选择器
3. 等待元素加载完成：`wait_for({selector: ".target"})`

## 📚 更多资源

- [Browser Use 官方文档](https://github.com/browser-use/browser-use)
- [MCP 协议规范](https://modelcontextprotocol.io)
- [MatuX 项目文档](https://github.com/your-repo/README.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进本配置！
