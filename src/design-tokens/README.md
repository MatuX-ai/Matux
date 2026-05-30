# Design Tokens 设计变量系统

## 简介

Design Tokens 是 iMatuProject 项目的原子化设计变量系统，为整个项目提供一致的设计规范。该系统包含颜色、字体、间距、圆角和阴影等核心设计变量，支持 TypeScript 和 SCSS 双格式输出。

## 目录结构

```
src/
├── design-tokens/                 # TypeScript 设计变量
│   ├── colors.ts                 # 颜色变量
│   ├── fonts.ts                  # 字体变量
│   ├── spacing.ts                # 间距变量
│   ├── border-radius.ts          # 圆角变量
│   ├── shadows.ts                # 阴影变量
│   ├── index.ts                  # 系统入口文件
│   └── usage-example.ts          # 使用示例
└── styles/
    └── design-tokens/             # SCSS 设计变量
        ├── _colors.scss          # 颜色变量
        ├── _fonts.scss           # 字体变量
        ├── _spacing.scss         # 间距变量
        ├── _border-radius.scss   # 圆角变量
        ├── _shadows.scss         # 阴影变量
        └── _index.scss           # 系统入口文件
```

## 核心特性

### 🎨 颜色系统 (Colors)
- **主色系列**: primary, primary-light, primary-dark
- **辅助色系列**: secondary, secondary-light, secondary-dark
- **状态色**: success, warning, error, info
- **中性色**: black, white, gray 50-900
- **文本色**: text-primary, text-secondary, text-disabled
- **背景色**: background, surface, divider

### 🔤 字体系统 (Fonts)
- **字体族**: sans-serif, serif, mono, system
- **字号层级**: h1-h6, body-large/medium/small, caption
- **行高**: tight, snug, normal, relaxed, loose
- **字重**: thin, light, regular, medium, bold, black

### 📏 间距系统 (Spacing)
- **基础网格**: 基于 8px 网格系统
- **微小间距**: xxs (2px), xs (4px)
- **基础间距**: sm (8px) 到 xxl (32px)
- **大间距**: xxxl (40px) 到 xxxxxxl (64px)
- **特大间距**: huge (80px), giant (96px), massive (128px)

### 🔄 圆角系统 (Border Radius)
- **基础圆角**: none, xs, sm, md, lg, xl, full
- **组件圆角**: button, input, card, modal, badge, avatar
- **方向性圆角**: top, bottom, left, right
- **响应式圆角**: mobile, desktop

###  shadows 阴影系统 (Shadows)
- **基础阴影**: none, xs, sm, md, lg, xl
- **组件阴影**: button, card, modal, dropdown, tooltip
- **状态阴影**: focus, error, success, warning
- **方向性阴影**: down, up, inner

## 使用方法

### TypeScript 使用

```typescript
import { colors, fonts, spacing, borderRadii, shadows } from './design-tokens';

// 颜色使用
const buttonStyle = {
  backgroundColor: colors.primary,
  color: colors.textWhite,
  borderRadius: borderRadii.borderRadius.sm,
};

// 字体使用
const textStyle = {
  fontFamily: fonts.families.system,
  fontSize: fonts.sizes.h3,
  fontWeight: fonts.weights.bold,
};

// 间距使用
const layoutStyle = {
  padding: spacing.lg,
  margin: spacing.xl,
  gap: spacing.md,
};
```

### SCSS 使用

```scss
@import 'styles/design-tokens/index';

// 使用颜色变量
.my-button {
  background-color: $primary-color;
  color: $text-white-color;
  border: 1px solid $border-color;
}

// 使用间距 mixins
.card {
  @include padding(lg);
  @include margin(xl);
  @include gap(md);
}

// 使用圆角 mixins
.rounded-element {
  @include border-radius(md);
}

// 使用阴影 mixins
.shadowed-box {
  @include shadow(lg);
}
```

## 响应式支持

系统内置响应式设计支持：

```typescript
// TypeScript 响应式间距
const responsivePadding = {
  mobile: spacing.responsive.mobile.md,
  tablet: spacing.responsive.tablet.lg,
  desktop: spacing.responsive.desktop.xl,
};

// SCSS 响应式 mixins
@include responsive-padding(mobile, md);
@include responsive-border-radius(desktop, card);
```

## 工具函数

### TypeScript 工具函数

```typescript
// 间距工具
const customSpacing = spacingUtils.scale(2); // 1rem
const horizontalGap = spacingUtils.horizontal('lg'); // 1rem

// 圆角工具
const borderRadiusValue = borderRadii.utils.get('md'); // '0.5rem'
const combinedRadius = borderRadii.utils.combine('sm', 'md', 'lg', 'xl');

// 阴影工具
const customShadow = shadows.utils.create('0px', '4px', '8px', '0px', 'rgba(0,0,0,0.1)');
const multipleShadows = shadows.utils.multiple(shadows.baseShadows.sm, shadows.stateShadows.focus);
```

### SCSS 工具函数

```scss
// 函数调用
.custom-element {
  border-radius: get-border-radius(md);
  box-shadow: get-shadow(lg);
  padding: spacing-scale(2); // 1rem
}

// Mixin 组合
.complex-component {
  @include component-border-radius(card);
  @include directional-shadow(down, md);
  @include state-shadow(focus);
}
```

## 验收标准

✅ 所有颜色值使用 HEX 格式（特殊情况可用 RGBA）  
✅ 关键颜色（如主色）提供深浅两个变体  
✅ 文档注释说明颜色用途  
✅ 变量命名语义清晰  
✅ 支持主题切换扩展  
✅ TypeScript 类型安全  
✅ SCSS 语法正确  

## 维护指南

1. **新增变量**: 在对应文件中添加新变量，确保遵循命名规范
2. **修改现有变量**: 考虑向后兼容性，必要时提供迁移路径
3. **删除变量**: 标记为废弃，提供替代方案
4. **版本控制**: 重大变更需要版本升级

## 贡献

欢迎提交 Issue 和 PR 来改进 Design Token 系统！

---

*iMatuProject Design System v1.0*