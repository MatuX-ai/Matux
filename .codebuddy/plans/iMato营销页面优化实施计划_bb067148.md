---
name: iMato营销页面优化实施计划
overview: 实施iMato营销页面优化，包括SEO、可访问性、移动端和性能优化
todos:
  - id: create-seo-service
    content: 新建 SEO 服务 (seo.service.ts)，提供 setMetaInfo 方法设置页面标题和Meta描述
    status: completed
  - id: modify-routing-lazy-loading
    content: 修改 marketing-routing.module.ts，将所有路由改为 loadComponent 懒加载模式
    status: completed
    dependencies:
      - create-seo-service
  - id: enhance-accessibility
    content: 增强 marketing-layout.component.ts 可访问性，添加 nav[role="navigation"]、aria-label、aria-current 状态
    status: completed
    dependencies:
      - create-seo-service
  - id: add-mobile-hamburger-menu
    content: 为 marketing-layout 添加汉堡菜单按钮和移动端响应式CSS样式
    status: completed
    dependencies:
      - create-seo-service
  - id: add-micro-animations
    content: 在 marketing.scss 中添加 fadeInUp、slideInLeft、stagger-delay 等交互动画
    status: completed
    dependencies:
      - create-seo-service
  - id: enhance-cta-buttons
    content: 为首页和特性页的CTA按钮添加 aria-label 属性，提升屏幕阅读器兼容性
    status: completed
    dependencies:
      - create-seo-service
---

## 用户需求

基于之前对iMato项目营销页面设计的分析，制定具体的优化实施计划

## 核心功能

对营销页面进行五个方面的优化：

1. SEO优化 - 添加Meta标签服务、结构化数据支持
2. 可访问性增强 - ARIA标签、键盘导航
3. 移动端优化 - 汉堡菜单、触摸优化
4. 性能优化 - 路由懒加载、代码分割
5. 微交互动画 - 悬停动画、加载动画

## 优化范围

- 营销模块位于 src/app/marketing/，包含10个页面组件
- 统一布局组件: marketing-layout.component.ts
- 路由配置: marketing-routing.module.ts
- 共享样式: src/styles/shared/marketing.scss
- 需新建SEO服务: src/app/core/services/seo.service.ts

## 技术选型

- 前端框架: Angular 21 (Standalone Components)
- 样式系统: SCSS + Design Tokens
- 响应式断点: $breakpoint-mobile-max: 767px (来自 variables.scss)

## 实施方案

1. **SEO服务**: 新建 src/app/core/services/seo.service.ts，集成Title和Meta服务
2. **路由懒加载**: 修改 marketing-routing.module.ts，使用 loadComponent 实现代码分割
3. **可访问性**: 修改 marketing-layout.component.ts，添加 role、aria-label、键盘导航
4. **移动端菜单**: 添加汉堡菜单按钮和响应式CSS，使用 $breakpoint-mobile-max 断点
5. **动画增强**: 在 marketing.scss 中添加 fadeInUp、slideIn 等动画关键帧

## 目录结构

```
src/app/
├── core/services/
│   └── seo.service.ts          # [NEW] SEO服务
├── marketing/
│   ├── shared/marketing-layout/
│   │   └── marketing-layout.component.ts  # [MODIFY] 可访问性+移动端优化
│   ├── marketing-routing.module.ts        # [MODIFY] 路由懒加载
│   └── marketing-home/                    # [MODIFY] CTA按钮添加aria-label
src/styles/shared/
└── marketing.scss                        # [MODIFY] 添加动画样式
```

## 可用扩展

本计划无需使用额外的Agent扩展