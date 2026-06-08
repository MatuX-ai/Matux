# MatuX MCP 快速参考卡片

## 🚀 立即开始

### 前置条件
- [ ] 启动前端：`npm run start` (端口 4200)
- [ ] 启动后端：`cd backend && python run.py` (端口 8000)
- [ ] 打开浏览器标签页（用于 MCP 连接）

---

## 📋 常用 MCP 命令

### 🔐 登录测试

```
1. navigate_page({url: "http://localhost:4200/auth/login"})
2. take_screenshot({filename: "login-page"})
3. click({selector: ".test-login-button"})
4. wait_for({seconds: 3})
5. navigate_page({url: "http://localhost:4200/user/dashboard"})
6. take_screenshot({filename: "dashboard"})
```

### 📊 性能分析

```
1. list_network_requests()
2. click({selector: ".test-login-button"})
3. wait_for({seconds: 5})
4. list_network_requests()
```

### 🔍 调试认证状态

```
1. navigate_page({url: "http://localhost:4200/user/dashboard"})
2. evaluate_script({
   script: `
     JSON.stringify({
       hasToken: !!localStorage.getItem('access_token'),
       user: localStorage.getItem('user_data')
     })
   `
 })
```

### 📸 UI 验证

```
1. take_snapshot()
2. list_console_messages()
3. take_screenshot()
```

---

## 🎯 自动化场景

### 场景 1：一键登录完整测试

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 1 | navigate_page(login) | 显示登录页 |
| 2 | click(test-login) | 触发一键登录 |
| 3 | wait(3s) | 等待登录完成 |
| 4 | navigate(dashboard) | 跳转 Dashboard |
| 5 | screenshot | 验证界面 |

### 场景 2：登录性能监控

| 步骤 | 操作 | 检查项 |
|------|------|--------|
| 1 | 清空网络日志 | - |
| 2 | 点击登录 | - |
| 3 | 等待 3s | - |
| 4 | 获取网络日志 | 分析 API 耗时 |

### 场景 3：Dashboard 数据加载验证

| 组件 | 检查项 | 验证方法 |
|------|--------|---------|
| 统计卡片 | 数量 >= 3 | DOM 查询 |
| 学习源 | 列表加载 | API 响应 |
| 课程 | 卡片渲染 | 截图验证 |

---

## 🔧 故障排查

### ❌ MCP 工具不工作

**检查清单**：
1. [ ] 浏览器已打开且有标签页
2. [ ] 使用 `list_pages()` 确认连接
3. [ ] 浏览器未被其他工具占用

**解决步骤**：
```bash
# 1. 确认浏览器连接
list_pages()

# 2. 如果没有页面，重新打开标签页
# 3. 在新标签页打开 http://localhost:4200
# 4. 重新尝试 MCP 命令
```

### ❌ 元素选择失败

**解决步骤**：
1. 先获取页面快照：`take_snapshot()`
2. 检查元素是否存在
3. 使用 `evaluate_script` 调试选择器

```javascript
// 在 evaluate_script 中测试选择器
document.querySelector('.test-login-button')?.tagName
```

### ❌ 截图模糊

**解决方案**：
- 确保浏览器缩放为 100%
- 使用 `take_snapshot()` 获取高清 DOM

---

## 📊 API 端点参考

| 功能 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 获取 Token | /api/v1/auth/token | POST | 登录 |
| 用户信息 | /api/v1/auth/me | GET | 当前用户 |
| 学习进度 | /api/v1/ai-edu/progress/stats | GET | 统计数据 |
| 学习源 | /api/v1/ai-edu/learning-sources | GET | 源列表 |
| 课程 | /api/v1/courses/enrollments | GET | 已选课程 |

---

## 🎨 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 学生 | test_student | TestStudent123! | 主要测试 |
| 教师 | test_teacher | TestTeacher123! | 功能测试 |
| 管理员 | test_admin | TestAdmin123! | 管理测试 |

---

## 📝 常用选择器

### 登录页面
- `.login-card` - 登录卡片
- `.test-login-button` - 一键登录按钮
- `input[name="email"]` - 邮箱输入框
- `input[name="password"]` - 密码输入框

### Dashboard
- `.user-center-container` - 主容器
- `.student-dashboard` - 学生仪表板
- `.stats-card` - 统计卡片
- `.course-card` - 课程卡片
- `.sidebar` - 侧边栏

### 导航
- `app-user-navbar` - 顶部导航栏
- `app-user-sidebar` - 侧边导航
- `app-user-sub-nav` - 子导航

---

## ⚡ 性能基准

### 登录时间（优化后）
| 环节 | 目标时间 | 警告阈值 |
|------|---------|---------|
| Token 获取 | < 300ms | > 500ms |
| 用户信息 | < 200ms | > 400ms |
| Dashboard 加载 | < 500ms | > 800ms |
| 总计 | < 1s | > 1.5s |

---

## 📌 快捷命令

```bash
# 快速启动测试工具
cd .qoder
python mcp-test-tool.py quick

# 查看所有场景
python mcp-test-tool.py scenarios

# 生成登录测试命令
python mcp-test-tool.py test 一键登录验证
```

---

## 🆘 获取帮助

- 查看详细指南：`.qoder/MCP-GUIDE.md`
- 查看配置：`.qoder/mcp-config.json`
- 运行交互模式：`python mcp-test-tool.py interactive`
