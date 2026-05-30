# Admin 统一侧边栏使用指南

## 📋 概述

已成功为 Admin 管理后台创建统一侧边栏导航系统，实现以下功能：

- ✅ 统一的菜单配置管理
- ✅ 权限过滤支持
- ✅ 响应式设计（桌面端 + 移动端）
- ✅ 折叠/展开功能
- ✅ 分组显示
- ✅ 状态持久化

## 🗂️ 文件结构

```
src/app/admin/shared/components/
├── admin-sidebar/
│   ├── admin-sidebar.component.ts      # 侧边栏组件
│   ├── admin-sidebar.service.ts        # 菜单服务
│   └── admin-sidebar.config.ts         # 菜单配置
└── admin-mobile-nav/
    └── admin-mobile-nav.component.ts   # 移动端导航组件
```

## 🎯 核心功能

### 1. 菜单配置 (`admin-sidebar.config.ts`)

**可配置的菜单项：**
```typescript
export const ADMIN_MENU_ITEMS: MenuItem[] = [
  { id: 'dashboard', title: '仪表板', icon: 'dashboard', route: '/admin/dashboard' },
  { id: 'users', title: '用户管理', icon: 'people', route: '/admin/users' },
  // ... 更多菜单项
];
```

**支持的属性：**
- `id`: 唯一标识（用于权限匹配）
- `title`: 显示文本
- `icon`: Material Icon
- `route`: 路由路径
- `children`: 子菜单（可选）
- `permission`: 权限标识（可选）

**分组配置：**
```typescript
export const MENU_GROUPS = [
  { title: '核心功能', items: ['dashboard', 'users'] },
  { title: '资源管理', items: ['licenses', 'organizations', 'materials', 'courses'] },
  // ...
];
```

### 2. 菜单服务 (`admin-sidebar.service.ts`)

**主要方法：**
- `getAllMenuItems()`: 获取所有菜单项
- `getFilteredMenuItems(accessibleIds)`: 根据权限过滤
- `getFilteredMenuGroups(accessibleIds)`: 获取分组菜单
- `getActiveMenuItemId(currentRoute)`: 获取激活菜单 ID
- `searchMenuItems(keyword)`: 搜索菜单

### 3. 侧边栏组件 (`admin-sidebar.component.ts`)

**输入参数：**
```html
<app-admin-sidebar 
  [accessibleMenuIds]="['dashboard', 'users', ...]"
  [defaultCollapsed]="false"
  [useGroups]="true">
</app-admin-sidebar>
```

**特性：**
- 自动根据权限过滤菜单
- 支持折叠/展开
- 状态保存到 localStorage
- 按组显示菜单
- 当前激活项高亮

### 4. 移动端导航 (`admin-mobile-nav.component.ts`)

**自适应特性：**
- 仅在手柄设备（手机）上显示
- 抽屉式侧边栏
- 触摸友好的交互设计
- 包含用户信息卡片

## 🔧 使用方法

### 在布局中使用

`admin-layout.component.ts` 已集成：

```typescript
@Component({
  selector: 'app-admin-layout',
  standalone: true,
  imports: [
    AdminSidebarComponent,      // 桌面端侧边栏
    AdminMobileNavComponent,    // 移动端导航
    // ... 其他导入
  ],
  template: `
    <div class="admin-layout">
      <!-- 移动端导航 -->
      <app-admin-mobile-nav></app-admin-mobile-nav>
      
      <!-- 桌面端侧边栏 -->
      <app-admin-sidebar [defaultCollapsed]="false"></app-admin-sidebar>
      
      <!-- 主内容区 -->
      <div class="admin-content">
        <router-outlet></router-outlet>
      </div>
    </div>
  `
})
```

### 添加新菜单项

**步骤 1:** 编辑 `admin-sidebar.config.ts`

```typescript
export const ADMIN_MENU_ITEMS: MenuItem[] = [
  // ... 现有菜单
  {
    id: 'new-feature',
    title: '新功能管理',
    icon: 'stars',
    route: '/admin/new-feature',
  },
];
```

**步骤 2:** （可选）添加到分组

```typescript
export const MENU_GROUPS = [
  {
    title: '新功能',
    items: ['new-feature'],
  },
];
```

就这么简单！无需修改组件代码。

### 集成权限控制

如果需要根据角色过滤菜单：

```typescript
// 在父组件中
const accessibleIds = this.permissionService.getAccessibleMenuIds();

// 传递给侧边栏
<app-admin-sidebar [accessibleMenuIds]="accessibleIds"></app-admin-sidebar>
```

## 🎨 样式定制

### 修改侧边栏宽度

```scss
.admin-sidebar {
  width: 280px; // 默认 256px
}

.admin-content {
  margin-left: 280px; // 与侧边栏宽度一致
}
```

### 修改主题色

```scss
.menu-item.active {
  background-color: #your-color;
  border-left-color: #your-color;
}

.logo-title {
  color: #your-color;
}
```

### 自定义折叠行为

```typescript
// 默认折叠状态
<app-admin-sidebar [defaultCollapsed]="true"></app-admin-sidebar>

// 禁用分组显示
<app-admin-sidebar [useGroups]="false"></app-admin-sidebar>
```

## 📱 响应式断点

- **桌面端**: > 1024px - 固定侧边栏
- **平板端**: 768px - 1024px - 可折叠侧边栏
- **移动端**: < 768px - 抽屉式导航

## ⚙️ 高级功能

### 1. 多级菜单（子菜单）

配置文件支持嵌套结构：

```typescript
{
  id: 'settings',
  title: '系统设置',
  icon: 'settings',
  route: '/admin/settings',
  children: [
    { id: 'general', title: '通用设置', icon: 'tune', route: '/admin/settings/general' },
    { id: 'security', title: '安全设置', icon: 'security', route: '/admin/settings/security' },
  ]
}
```

### 2. 动态菜单

可以在运行时动态修改菜单：

```typescript
// 在服务中
addMenuItem(item: MenuItem): void {
  this.menuItems.push(item);
}

removeMenuItem(id: string): void {
  this.menuItems = this.menuItems.filter(i => i.id !== id);
}
```

### 3. 菜单搜索

已内置搜索功能：

```typescript
const results = this.sidebarService.searchMenuItems('用户');
// 返回匹配的菜单项
```

## 🐛 常见问题

### Q: 如何隐藏某个菜单项？
A: 从 `ADMIN_MENU_ITEMS` 数组中删除该项，或传入 `accessibleMenuIds` 时排除该 ID。

### Q: 折叠状态保存在哪里？
A: 保存在 `localStorage` 的 `admin_sidebar_collapsed` 键中。

### Q: 如何禁用折叠功能？
A: 在组件中设置 `[defaultCollapsed]="false"` 并在样式中移除折叠相关代码。

### Q: 移动端导航不显示？
A: 检查断点观察器配置，确保屏幕宽度符合手柄设备标准。

## 📊 已集成的菜单项

| 模块 | 路由 | 图标 | 分组 |
|------|------|------|------|
| 仪表板 | `/admin/dashboard` | dashboard | 核心功能 |
| 用户管理 | `/admin/users` | people | 核心功能 |
| 许可证管理 | `/admin/licenses` | vpn_key | 资源管理 |
| 组织管理 | `/admin/organizations` | business | 资源管理 |
| 课件库管理 | `/admin/materials` | folder | 资源管理 |
| 课程库管理 | `/admin/courses` | school | 资源管理 |
| 支付管理 | `/admin/payments` | payment | 财务管理 |
| 赞助管理 | `/admin/sponsorship` | handshake | 财务管理 |
| 数据中心 | `/admin/database-registry` | storage | 数据中心 |
| 营销数据 | `/admin/marketing` | analytics | 数据中心 |

## 🚀 下一步优化建议

1. **权限深度集成**: 结合角色系统实现细粒度菜单控制
2. **面包屑导航**: 添加页面层级导航
3. **快捷操作**: 在侧边栏添加常用操作按钮
4. **通知徽章**: 显示未读消息数量
5. **主题切换**: 支持深色模式

## 📝 维护说明

- 所有菜单配置集中在 `admin-sidebar.config.ts`
- 修改菜单后无需重启，热更新生效
- 权限变更需要刷新页面
- 样式修改在 `admin.styles.scss`

---

**创建时间**: 2026-03-23  
**版本**: v1.0.0  
**维护者**: Development Team
