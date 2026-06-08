# 学习端路由结构分析与重构方案

> **文档状态**：待执行  
> **创建日期**：2026-06-08  
> **版本**：v1.0

---

## 一、文档目的

本文档针对 MatuX 学习端（Angular 前端）的路由结构进行全面分析，结合：
1. **桌面端需求**（PRD 第 6.10 节规范）
2. **原型统一样式要求**（edu-proto 设计规范）

识别当前路由结构存在的问题，制定系统性重构方案。

---

## 二、当前路由结构总览

### 2.1 主路由 (`src/app/app-routing.module.ts`)

| 路径 | 功能 | 状态 | 优先级 |
|------|------|------|--------|
| `/dashboard` | 最小化仪表板 | ⚠️ 与 `/user/dashboard` 冲突 | P0 |
| `/learning-path` | 学习路径地图 | ⚠️ 调试路由，不应暴露 | P0 |
| `/openmt-demo` | OpenMT Demo | ⚠️ 调试路由，不应暴露 | P0 |
| `/ar-lab` | AR 实验室 | ✅ 独立模块 | - |
| `/offline-mode/*` | 离线模式 | ✅ | - |
| `/ai-edu/*` | AI 教育 | ⚠️ 路由层级不清晰 | P1 |
| `/arvr-course/:id` | ARVR 课程播放器 | ✅ | - |
| `/digital-twin-lab/*` | 数字孪生实验室 | ✅ | - |
| `/content-store/*` | 内容商店 | ⚠️ 功能层级需确认 | P1 |
| `/creativity-engine/*` | 创意引擎 | ⚠️ 功能层级需确认 | P1 |
| `/auth/*` | 认证模块 | ✅ | - |
| `/user/*` | 用户中心 | ⚠️ 嵌套过深 | P1 |
| `/exam/*` | 在线测验 | ✅ | - |
| `/vircadia/*` | 元宇宙教室 | ✅ | - |
| `/icon-debug` | 图标调试 | 🔴 **调试路由必须移除** | P0 |
| `/icon-test` | 图标测试 | 🔴 **调试路由必须移除** | P0 |

### 2.2 用户中心路由 (`src/app/user/user-routing.module.ts`)

| 路径 | 功能 | 组件 | 状态 |
|------|------|------|------|
| `/user/dashboard` | 学习仪表板 | UserCenterComponent | ✅ |
| `/user/profile` | 个人资料 | UserProfileComponent | ✅ |
| `/user/token` | Token 管理 | TokenDashboardModule | ✅ |
| `/user/achievements` | 成就系统 | AchievementsComponent | ✅ |
| `/user/courses` | 我的课程 | MyCoursesComponent | ✅ |
| `/user/learning-profile` | 学习画像 | LearningProfileComponent | ✅ |
| `/user/growth-trajectory` | 成长轨迹 | GrowthTrajectoryPageComponent | ✅ |
| `/user/reports` | 学习报告 | LearningReportsComponent | ✅ |
| `/user/teaching-suggestions` | 教学建议 | TeachingSuggestionsComponent | ✅ |
| `/user/emotional-companion` | 情感陪伴 | EmotionalCompanionComponent | ✅ |
| `/user/ai-teacher-settings` | AI 教师设置 | AITeacherSettingsComponent | ✅ |

### 2.3 导航菜单来源

路由通过 `UserCenterService.getSidebarMenu()` 动态生成侧边栏菜单：

```typescript
// src/app/user/services/user-center.service.ts
getSidebarMenu(): UserCenterMenuItem[] {
  return [
    { icon: 'dashboard', label: '学习仪表板', route: '/user/dashboard' },
    { icon: 'menu_book', label: '我的课程', route: '/user/courses' },
    { icon: 'psychology', label: '学习画像', route: '/user/learning-profile' },
    { icon: 'trending_up', label: '我的成长', route: '/user/growth-trajectory' },
    { icon: 'assessment', label: '学习报告', route: '/user/reports' },
    { icon: 'tips_and_updates', label: '教学建议', route: '/user/teaching-suggestions' },
    { icon: 'emoji_events', label: '成就系统', route: '/user/achievements' },
    { icon: 'token', label: 'Token管理', route: '/user/token' },
    { icon: 'person', label: '个人资料', route: '/user/profile' },
    { icon: 'smart_toy', label: 'AI教师设置', route: '/user/ai-teacher-settings' },
    { icon: 'favorite', label: '情感陪伴', route: '/user/emotional-companion' },
  ];
}
```

---

## 三、问题清单

### 3.1 P0 - 严重问题（必须修复）

#### 问题 1：调试路由泄露
- `/icon-debug` - 图标调试页面
- `/icon-test` - 图标测试页面
- `/openmt-demo` - OpenMT Demo 页面
- `/dashboard` - 与 `/user/dashboard` 功能重复

**影响**：生产环境暴露内部调试功能，存在安全隐患。

#### 问题 2：根路由 `/dashboard` 与用户路由冲突
```
/dashboard          → MinimalDashboardComponent (根路由)
/user/dashboard     → UserCenterComponent (用户路由)
```

**影响**：用户访问 `/dashboard` 会进入最小化仪表板，而非学习仪表板。

#### 问题 3：Navbar 导航与 Sidebar 导航不一致

**Navbar** (`user-navbar.component.ts` 第 49-59 行)：
```html
<!-- 移动端导航 -->
<a routerLink="/user/dashboard" ...> 首页 </a>
<a routerLink="/ai-edu" ...> 课程 </a>
<a routerLink="/ar-lab" ...> AR实验室 </a>

<!-- 桌面端导航 -->
<a routerLink="/user/dashboard" ...> 首页 </a>
<a routerLink="/ai-edu" ...> 课程 </a>
```

**Sidebar** (`user-center.service.ts`)：
- `/user/dashboard` - 学习仪表板
- `/user/courses` - 我的课程
- `/user/learning-profile` - 学习画像
- ...

**问题**：Navbar 只显示 2 个链接，Sidebar 显示 11 个链接，职责不清。

### 3.2 P1 - 重要问题（应尽快修复）

#### 问题 4：路由层级混乱

学习模块分布在三个不同层级：

| 层级 | 路由示例 | 问题 |
|------|---------|------|
| 根层级 | `/ai-edu`, `/ar-lab`, `/creativity-engine` | 与用户中心路由分离 |
| 用户层级 | `/user/*` | 嵌套过深 |
| 混合层级 | `/exam`, `/vircadia` | 无统一归属 |

#### 问题 5：原型设计未完全落地

| 原型 Tab | 应有路由 | 当前状态 |
|----------|---------|---------|
| home | `/home` 或默认首页 | ❌ 缺失统一首页 |
| learn | `/learn` | ⚠️ 路由存在但分散 |
| community | `/community` | ❌ **完全缺失** |
| profile | `/profile` 或 `/user/profile` | ✅ 已实现 |

#### 问题 6：路由命名规范不一致

- `growth-trajectory` - kebab-case ✅
- `learning-profile` - kebab-case ✅
- `ai-teacher-settings` - kebab-case ✅
- `emotional-companion` - kebab-case ✅

**状态**：命名规范已统一，无需修改。

### 3.3 P2 - 改进建议

#### 问题 7：硬编码路由路径
- 多处使用字符串字面量而非 `ROUTES` 常量
- 建议统一使用 `src/app/routes.const.ts` 中的常量

#### 问题 8：路由守卫不完整
- 仅 `UserCenterGuard` 保护用户中心路由
- 其他模块缺少统一的认证守卫

---

## 四、解决方案

### 4.1 重构目标

根据 PRD 第 6.10 节桌面端 vs 移动端差异规范：

| 设计维度 | 桌面端目标 | 路由重构方向 |
|----------|----------|-------------|
| 导航方式 | 顶部 Navbar（文字链接 + 搜索 + 头像） | 统一 Navbar 导航 |
| 快捷入口 | 1×4 网格 (4 个大卡片) | Dashboard 整合 |
| AI 助手 | 右侧浮窗面板 | 路由外组件 |
| 底部状态 | 状态栏（在线状态 + 版本号） | 保持 StatusBar |

### 4.2 重构方案：渐进式修复

#### Phase 1：立即修复 P0 问题

**Step 1.1：删除调试路由**

修改 `src/app/app-routing.module.ts`：
```typescript
// 移除以下路由：
// - /dashboard (MinimalDashboardComponent)
// - /openmt-demo (OpenMtDemoComponent)
// - /icon-debug (IconDebugComponent)
// - /icon-test (IconSimpleTestComponent)
```

**Step 1.2：修复根路由默认跳转**

```typescript
{
  path: '',
  redirectTo: '/user/dashboard',  // 改为重定向到用户仪表板
  pathMatch: 'full',
},
```

**Step 1.3：统一导航菜单**

在 `UserNavbarComponent` 中精简导航，保持与 Sidebar 一致。

#### Phase 2：清理路由层级 P1 问题

**Step 2.1：创建统一的学习中心路由**

```typescript
// 新增 /learn 路由组
{
  path: 'learn',
  loadChildren: () => import('./learn/learn.module').then(m => m.LearnModule),
}
```

**Step 2.2：添加缺失的社区路由**

```typescript
// 新增 /community 路由
{
  path: 'community',
  loadChildren: () => import('./community/community.module').then(m => m.CommunityModule),
}
```

#### Phase 3：完善优化 P2 问题

**Step 3.1：统一使用 ROUTES 常量**

**Step 3.2：完善路由守卫**

---

## 五、重构后的目标路由结构

```
/
├── /                                    # 默认 → 重定向到 /user/dashboard
│
├── /auth/*                             # 认证模块
│   ├── /auth/login                     # 登录页
│   ├── /auth/register                   # 注册页
│   └── /auth/callback                  # OAuth 回调
│
├── /user/*                             # 用户中心（现有路由保留）
│   ├── /user/dashboard                 # 学习仪表板 ← 首页
│   ├── /user/profile                   # 个人资料
│   ├── /user/token                    # Token 管理
│   ├── /user/achievements             # 成就系统
│   ├── /user/courses                  # 我的课程
│   ├── /user/learning-profile         # 学习画像
│   ├── /user/growth-trajectory        # 成长轨迹
│   ├── /user/reports                 # 学习报告
│   ├── /user/teaching-suggestions     # 教学建议
│   ├── /user/emotional-companion      # 情感陪伴
│   └── /user/ai-teacher-settings     # AI 教师设置
│
├── /ai-edu/*                          # AI 编程教育
│   ├── /ai-edu/dashboard              # AI 教育仪表板
│   └── /ai-edu/course/:id            # 课程详情
│
├── /lab/*                             # 实验室模块（统一入口）
│   ├── /lab/ar-lab                   # AR 实验室
│   ├── /lab/digital-twin-lab         # 数字孪生实验室
│   ├── /lab/creativity-engine        # 创意引擎
│   ├── /lab/vircadia                 # 元宇宙教室
│   └── /lab/arvr-course/:id          # ARVR 课程播放器
│
├── /community/*                       # 创客社区
│   ├── /community/explore             # 发现作品
│   └── /community/my-projects        # 我的项目
│
├── /exam/*                            # 在线测验
│
├── /offline-mode/*                   # 离线模式
│
└── /content-store/*                  # 内容商店
```

---

## 六、执行计划

### 6.1 Phase 1：P0 修复（✅ 已完成）

| 序号 | 任务 | 文件 | 状态 |
|------|------|------|------|
| 1.1 | 删除调试路由 | `app-routing.module.ts` | ✅ 已完成 |
| 1.2 | 修复默认路由跳转 | `app-routing.module.ts` | ✅ 已完成 |
| 1.3 | 清理根目录 dashboard 路由 | `app-routing.module.ts` | ✅ 已完成 |
| 1.4 | 统一 Navbar 导航 | `user-navbar.component.ts` | ✅ 已完成 |

### 6.2 Phase 2：P1 清理（✅ 已完成）

| 序号 | 任务 | 文件 | 状态 |
|------|------|------|------|
| 2.1 | 删除调试组件文件 | `minimal-dashboard/*`, `path-map/*`, `openmt-demo/*`, `icon-debug/*`, `icon-simple-test/*` | ✅ 已完成 |
| 2.2 | 清理空目录 | `components/` 下的空目录 | ✅ 已完成 |
| 2.3 | 验证路由完整性 | `app-routing.module.ts` | ✅ 已完成 |

### 6.3 Phase 3：P2 优化（✅ 已完成）

| 序号 | 任务 | 文件 | 状态 |
|------|------|------|------|
| 3.1 | 更新 ROUTES 常量 | `routes.const.ts` | ✅ 已完成 |
| 3.2 | 使用 ROUTES 常量 | `user-center.service.ts` | ✅ 已完成 |
| 3.3 | 使用 ROUTES 常量 | `user-navbar.component.ts` | ✅ 已完成 |
| 3.4 | 使用 ROUTES 常量 | `auth.service.ts` | ✅ 已完成 |
| 3.5 | 使用 ROUTES 常量 | `login.component.ts` | ✅ 已完成 |
| 3.6 | 使用 ROUTES 常量 | `register.component.ts` | ✅ 已完成 |
| 3.7 | 使用 ROUTES 常量 | `user-center.guard.ts` | ✅ 已完成 |

---

## 七、风险与注意事项

### 7.1 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 路由变更导致现有链接失效 | 高 | 保留旧路由别名，设置临时重定向 |
| 导航菜单变更影响用户体验 | 中 | 先在测试环境验证 |

### 7.2 注意事项

1. **保持向后兼容**：删除旧路由前先添加重定向
2. **测试环境验证**：所有修改先在本地验证
3. **Electron 打包测试**：路由变更后需完整测试 Electron 应用

---

## 八、验收标准

- [ ] 所有调试路由已删除
- [ ] 访问 `/` 自动跳转到 `/user/dashboard`
- [ ] Navbar 和 Sidebar 导航一致
- [ ] 无路由冲突或重复定义
- [ ] 原有功能不受影响

---

## 九、变更记录

| 日期 | 版本 | 变更内容 | 作者 |
|------|------|---------|------|
| 2026-06-08 | v1.0 | 初始版本 | Qoder |
| 2026-06-08 | v1.1 | **Phase 1 P0 修复完成**：删除调试路由（/dashboard, /openmt-demo, /icon-debug, /icon-test, /learning-path），修复默认路由跳转至 /user/dashboard，统一 Navbar 导航 | Qoder |
| 2026-06-08 | v1.2 | **Phase 2 清理完成**：删除遗留调试组件文件（minimal-dashboard, path-map, openmt-demo, icon-debug, icon-simple-test）及其目录，清理空目录 | Qoder |
| 2026-06-08 | v1.5 | **二次验证修复**：app-routing.module.ts, ai-edu-error-handler.service.ts, oauth-callback.component.ts, user-token-dashboard.component.{ts,html}, login.component.html, register.component.html 使用 ROUTES 常量 | Qoder |
