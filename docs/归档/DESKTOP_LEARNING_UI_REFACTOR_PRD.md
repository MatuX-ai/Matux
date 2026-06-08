# 桌面端学习端 UI 重构 PRD

> **版本**：v1.0  
> **文档状态**：进行中  
> **创建日期**：2026-06-08  
> **依据**：MatuX_Desktop_PRD.md 第 6.5 节页面布局规范

---

## 1. 背景与问题

### 1.1 当前实现问题

当前桌面端学习端 UI 采用**左侧边栏 + 主内容区**的布局，与 PRD 原型规范严重不符：

| 特性 | PRD 原型要求 | 当前实现 | 严重程度 |
|------|-------------|----------|----------|
| 导航方式 | 顶部水平导航 | 左侧垂直边栏 | P0 严重 |
| 布局结构 | 无侧边栏，单列内容 | 左侧边栏 260px | P0 严重 |
| AI 助手 | 右下角浮动按钮 | 嵌入侧边栏 | P1 不符 |
| 快捷入口 | 4 个卡片入口 | 分散在侧边栏 | P1 不符 |
| 底部状态栏 | 显示运行状态 | 缺失 | P1 缺失 |

### 1.2 重构目标

按照 **MatuX_Desktop_PRD.md 第 6.5 节页面布局规范** 重构桌面端学习端 UI，实现与 PRD 原型一致的体验。

---

## 2. 设计规范

### 2.1 目标布局结构

```
┌──────────────────────────────────────────────────────────────────┐
│  [🧊 MatuX]  首页  课程  AR实验室  项目  创作  [🔍]  [🔔] [👤 小明] │ ← Navbar 64px
│                                                  bg-primary text-white│
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  👋 你好，小明！                              2026年6月8日     │ │
│  │  准备好开始今天的实验了吗？                                     │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │  📚        │ │  🥽        │ │  🚀        │ │  🏆        │ │
│  │  我的课程   │ │  AR 实验室  │ │  实战项目   │ │  学习成就   │ │
│  │  ───────   │ │  ───────   │ │  ───────   │ │  ───────   │ │
│  │  进度 75%  │ │  探索 12个  │ │  创建 3个  │ │  8/12 徽章 │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────┐ ┌──────────────────────────┐│
│  │  今日学习任务                     │ │  本周学习统计              ││
│  │                                  │ │                          ││
│  │  ○ Python 变量与数据类型  75%    │ │  12.5h  8任务  450分  3天││
│  │  ✓ Arduino LED 控制     100%    │ │                          ││
│  │  ○ 机器学习基础          30%    │ │                          ││
│  └──────────────────────────────────┘ └──────────────────────────┘│
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  为你推荐                                                     │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │ │
│  │  │ 🤖 机器人进阶 │  │ 👁️ AI视觉识别 │  │ 🎨 3D建模设计 │      │ │
│  │  │ 中级·12课时   │  │ 高级·16课时   │  │ 初级·10课时   │      │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
│                                    ┌──────────────────┐           │
│                                    │  💬 AI 老师      │ ← 浮动按钮 │
│                                    └──────────────────┘           │
├──────────────────────────────────────────────────────────────────┤
│  🟢 在线  |  ESP32 已连接  |  v1.0.0                              │ ← 状态栏 28px
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 布局规格

| 元素 | 规格 |
|------|------|
| 顶部导航栏 | 高度 64px，深色背景 (#0f172a)，Logo + 水平菜单 + 搜索/通知/用户 |
| 主内容区 | 最大宽度 1400px，居中，左右 padding 24px |
| 快捷入口卡片 | 4 列网格，间距 20px，圆角 16px |
| 浮动 AI 按钮 | 56×56px，右下角固定定位，距底部 24px，距右侧 24px |
| 底部状态栏 | 高度 28px，显示设备状态、版本信息 |

### 2.3 响应式策略

| 屏幕宽度 | 布局策略 |
|----------|----------|
| ≥ 1400px | 全宽布局，固定最大宽度 1400px |
| 1024px - 1399px | 自适应宽度，减少 padding |
| < 1024px | 保留顶部导航，隐藏次要元素 |

---

## 3. 组件重构任务

### 3.1 UserCenterComponent（主布局容器）

**文件**：`src/app/user/user-center.component.ts`

**修改**：
- [ ] 移除左侧边栏组件 `app-user-sidebar`
- [ ] 移除子导航组件 `app-user-sub-nav`
- [ ] 保留顶部导航 `app-user-navbar`
- [ ] 保留页脚 `app-user-footer`
- [ ] 简化 Grid 布局为单列 Flex 布局

**目标模板结构**：
```html
<div class="user-center-container">
  <!-- 顶部导航栏 -->
  <app-user-navbar></app-user-navbar>
  
  <!-- 主内容区 -->
  <main class="main-content">
    <router-outlet></router-outlet>
    <app-user-footer></app-user-footer>
  </main>
  
  <!-- 浮动 AI 助手按钮 -->
  <button class="ai-assistant-fab">💬</button>
  
  <!-- 底部状态栏 -->
  <footer class="status-bar">...</footer>
</div>
```

### 3.2 UserNavbarComponent（顶部导航栏）

**文件**：`src/app/user/components/user-navbar/user-navbar.component.ts`

**修改**：
- [ ] 扩展为完整顶部导航
- [ ] 添加水平菜单项：首页、课程、AR实验室、项目、创作
- [ ] 保留搜索、通知、用户菜单
- [ ] 添加移动端汉堡菜单（响应式）

**导航菜单项**：
| 路由 | 标签 | 图标 |
|------|------|------|
| `/user/dashboard` | 首页 | home |
| `/user/courses` | 课程 | book_open |
| `/ai-edu` | AI 编程 | code |
| `/ar-lab` | AR 实验室 | view_in_ar |
| `/creativity-engine` | 创作 | palette |

### 3.3 新增 AIAssistantFabComponent（浮动按钮）

**文件**：`src/app/user/components/ai-assistant-fab/ai-assistant-fab.component.ts`（新建）

**规格**：
- 56×56px 圆形按钮
- 渐变背景 `from-indigo-500 to-purple-600`
- 右下角固定定位 `position: fixed; bottom: 24px; right: 24px`
- 悬停放大 `scale(1.1)`
- 点击展开 AI 对话面板

### 3.4 新增 StatusBarComponent（状态栏）

**文件**：`src/app/user/components/status-bar/status-bar.component.ts`（新建）

**显示内容**：
- 设备连接状态（绿色/红色圆点）
- 硬件设备信息（如 ESP32 已连接）
- 应用版本号

### 3.5 移除废弃组件

| 组件/文件 | 状态 | 说明 |
|----------|------|------|
| `UserSidebarComponent` | ✅ 已废弃 | 标记 @deprecated，使用 UserNavbarComponent 替代 |
| `UserSubNavComponent` | ✅ 已废弃 | 标记 @deprecated，导航已整合到顶部 |
| `SidebarService` | ✅ 已废弃 | 标记 @deprecated，侧边栏状态管理不再需要 |
| `UserHeaderComponent` | ✅ 已废弃 | 标记 @deprecated，使用 UserNavbarComponent 替代 |
| `MatSidenavModule` | ✅ 已移除 | 不再需要侧边栏模块 |
| `MatListModule` | ✅ 已移除 | 不再需要列表模块 |
| `MatToolbarModule` | ✅ 已移除 | 不再需要工具栏模块 |

**清理完成日期**：2026-06-08

---

## 4. 路由配置

### 4.1 桌面端导航路由

```
/user/dashboard     → 学习仪表板（默认首页）
/user/courses       → 我的课程
/ai-edu            → AI 编程教育
/ar-lab            → AR 实验室
/creativity-engine  → 创意引擎
```

### 4.2 快捷入口路由映射

| 卡片 | 路由 |
|------|------|
| 我的课程 | `/user/courses` |
| AR 实验室 | `/ar-lab` |
| 实战项目 | `/creativity-engine` |
| 学习成就 | `/user/achievements` |

---

## 5. 实施计划

### Phase 1：基础布局重构
1. 创建 PRD 文档（本文档）
2. 修改 `user-center.component.ts` 简化布局
3. 扩展 `user-navbar.component.ts` 顶部导航

### Phase 2：新增组件
4. 创建 `ai-assistant-fab.component.ts`
5. 创建 `status-bar.component.ts`
6. 添加浮动按钮和状态栏到主布局

### Phase 3：内容页适配
7. 移除废弃组件导入
8. 适配各子页面样式

### Phase 4：测试验证
9. 手动测试导航功能
10. 截图对比 PRD 原型

---

## 6. 验收标准

### 6.1 布局验收

| 检查项 | 标准 |
|--------|------|
| 顶部导航栏 | 64px 高度，深色背景，Logo + 水平菜单 |
| 主内容区 | 无左侧边栏，单列布局 |
| 浮动 AI 按钮 | 右下角固定，56×56px |
| 状态栏 | 底部 28px，显示设备状态 |

### 6.2 功能验收

| 检查项 | 标准 |
|--------|------|
| 首页导航 | 点击菜单项正确跳转 |
| 快捷入口 | 4 个卡片可点击跳转 |
| AI 助手 | 点击浮动按钮打开对话 |
| 响应式 | 移动端显示汉堡菜单 |

### 6.3 视觉验收

| 检查项 | 标准 |
|--------|------|
| 色彩 | 深色导航栏 #0f172a |
| 字体 | 主标题 36px，子标题 18px |
| 间距 | 内容区 padding 24px，卡片间距 20px |
| 圆角 | 卡片 16px，按钮 8px |

---

## 7. 相关文件清单

### 7.1 需要修改的文件

| 文件路径 | 修改内容 |
|----------|----------|
| `src/app/user/user-center.component.ts` | 简化布局，移除侧边栏 |
| `src/app/user/components/user-navbar/user-navbar.component.ts` | 扩展为完整顶部导航 |
| `src/app/user/components/user-sidebar/user-sidebar.component.ts` | 移除导入 |

### 7.2 需要新建的文件

| 文件路径 | 说明 |
|----------|------|
| `src/app/user/components/ai-assistant-fab/` | 浮动 AI 助手按钮组件 |
| `src/app/user/components/status-bar/` | 底部状态栏组件 |

### 7.3 需要删除的组件引用

| 组件 | 引用位置 |
|------|----------|
| `UserSidebarComponent` | user-center.component.ts imports |
| `UserSubNavComponent` | user-center.component.ts imports |

---

## 8. 附录：组件代码模板

### 8.1 UserNavbarComponent 导航菜单模板

```typescript
// 导航菜单配置
navItems = [
  { route: ROUTES.USER.DASHBOARD, label: '首页', icon: 'home' },
  { route: ROUTES.USER.COURSES, label: '课程', icon: 'school' },
  { route: '/ai-edu', label: 'AI 编程', icon: 'code' },
  { route: '/ar-lab', label: 'AR 实验室', icon: 'view_in_ar' },
  { route: '/creativity-engine', label: '创作', icon: 'palette' },
];
```

### 8.2 浮动按钮样式

```scss
.ai-assistant-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4);
  // ...
}
```

---

## 9. 修复历史记录

| 日期 | 问题 | 修复方案 | 状态 |
|------|------|----------|------|
| 2026-06-08 | mat-icon 使用中文字符串 `'智能助手'` | 替换为 Material 图标 `'smart_toy'` | ✅ 已修复 |
| 2026-06-08 | FormsModule 缺失导致 ngModel 绑定失败 | 添加 FormsModule 导入 | ✅ 已修复 |
| 2026-06-08 | user-center.component.ts 未使用 StudentDashboardComponent | 移除未使用的导入 | ✅ 已修复 |

**修复完成日期**：2026-06-08

---

## 10. 最终验收状态

> **文档状态**：✅ 已完成

### 验收清单

| 验收项 | 状态 | 说明 |
|--------|------|------|
| 顶部导航栏 (64px) | ✅ 通过 | 深色背景，Logo + 水平菜单 |
| 主内容区单列布局 | ✅ 通过 | 无左侧边栏 |
| 导航菜单（5项） | ✅ 通过 | 首页、课程、AI编程、AR实验室、创作 |
| 浮动 AI 按钮 | ✅ 通过 | 56×56px，右下角固定 |
| 底部状态栏 | ✅ 通过 | 显示设备状态和版本号 |
| `<router-outlet>` 路由 | ✅ 通过 | 替代写死的子组件 |
| 废弃组件标记 | ✅ 通过 | 已标记 @deprecated |
| MatIcon 图标 | ✅ 通过 | 使用标准 Material 图标 |

### 遗留事项

| 事项 | 优先级 | 说明 |
|------|--------|------|
| 废弃组件文件未删除 | 低 | 已标记 @deprecated，可保留用于参考 |
| 浮动按钮底部间距 (48px vs 24px) | 低 | 设计决策，确保不与状态栏重叠 |

---

**文档版本历史**：
- v1.0 (2026-06-08) - 初始版本
- v1.1 (2026-06-08) - 修复 mat-icon 中文字符串问题
