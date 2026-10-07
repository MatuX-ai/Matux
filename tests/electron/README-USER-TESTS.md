# 用户桌面端测试说明

本目录包含针对 MatuX 桌面端应用的用户功能测试用例。

## 测试文件

| 文件名 | 描述 |
|--------|------|
| `test-user-desktop.spec.js` | 用户核心功能测试：认证、会话、界面交互、数据同步 |
| `test-user-permissions.spec.js` | 用户权限与数据访问控制测试 |
| `test-user-data.spec.js` | 用户数据管理测试：资料、进度、收藏、消息 |
| `test-user-desktop.config.js` | Playwright 测试配置 |
| `run-user-tests.js` | 测试运行辅助脚本 |

## 测试覆盖范围

### 1. 用户认证功能
- [x] 登录页面显示
- [x] 有效凭证登录
- [x] 无效凭证拒绝
- [x] 用户注册
- [x] 用户登出

### 2. 用户会话管理
- [x] 登录状态保持
- [x] 页面刷新后会话保持
- [x] 多窗口会话同步

### 3. 用户界面交互
- [x] 页面导航
- [x] 搜索功能
- [x] 模态框操作
- [x] 下拉菜单操作

### 4. 用户数据同步
- [x] 后端数据同步
- [x] 本地偏好设置保存
- [x] 网络恢复后同步

### 5. 错误处理
- [x] 网络错误处理
- [x] 认证失败处理
- [x] 友好错误消息显示

### 6. 性能测试
- [x] 页面加载时间
- [x] 交互响应时间

### 7. 用户权限管理
- [x] 角色权限验证
- [x] 数据访问控制
- [x] 功能权限验证
- [x] 资源访问限制

### 8. 用户数据管理
- [x] 个人资料查看/修改
- [x] 头像修改
- [x] 密码修改
- [x] 学习进度追踪
- [x] 收藏功能
- [x] 历史记录
- [x] 消息通知

## 运行测试

### 方式一：使用 Playwright CLI

```bash
# 运行所有用户测试
npx playwright test tests/electron/test-user-desktop.spec.js --headed

# 运行特定测试文件
npx playwright test tests/electron/test-user-permissions.spec.js --headed

# 使用配置文件运行
npx playwright test --config tests/electron/test-user-desktop.config.js
```

### 方式二：使用辅助脚本

```bash
# 运行所有测试
node tests/electron/run-user-tests.js

# 仅运行认证测试
node tests/electron/run-user-tests.js --auth

# 仅运行权限测试
node tests/electron/run-user-tests.js --permissions

# 仅运行数据管理测试
node tests/electron/run-user-tests.js --data
```

### 方式三：使用 npm 脚本

在项目根目录的 `package.json` 中添加：

```json
{
  "scripts": {
    "test:user:desktop": "playwright test tests/electron/test-user-*.spec.js --headed",
    "test:user:auth": "playwright test tests/electron/test-user-desktop.spec.js --headed",
    "test:user:permissions": "playwright test tests/electron/test-user-permissions.spec.js --headed",
    "test:user:data": "playwright test tests/electron/test-user-data.spec.js --headed"
  }
}
```

然后运行：
```bash
npm run test:user:desktop
```

## 前置条件

1. **安装 Playwright 依赖**
   ```bash
   npx playwright install chromium
   ```

2. **启动后端服务**
   确保后端服务运行在 `http://localhost:8000`

3. **启动桌面端应用**
   确保 Electron 应用可以正常启动

## 测试环境变量

测试支持以下环境变量：

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `BACKEND_URL` | http://localhost:8000 | 后端服务地址 |
| `NODE_ENV` | test | 运行环境 |
| `CI` | - | CI 模式下会启用更多重试 |

## 测试输出

测试结果将保存在：
- `test-results/user-desktop/results.json` - JSON 格式结果
- `test-results/user-desktop/html` - HTML 报告

## 注意事项

1. 测试使用 Playwright 的 Electron 支持，需要确保 Electron 可执行
2. 部分测试需要用户登录状态，请确保测试环境中有可用的测试账户
3. 测试超时时间默认为 60 秒，可以根据需要调整
4. 截图和视频仅在测试失败时保留

## 故障排查

### 问题：Electron 启动失败
- 确认 Electron 依赖已正确安装
- 检查 `node_modules/.bin/electron` 是否存在

### 问题：测试超时
- 增加配置文件中的 `timeout` 值
- 检查后端服务是否正常运行

### 问题：找不到元素
- 检查页面是否完全加载
- 可能需要增加等待时间
- 检查选择器是否正确
