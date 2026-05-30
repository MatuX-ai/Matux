# MatuX Project 样式文档中心

欢迎来到 iMatuProject 设计系统的样式文档中心！这里包含了所有关于我们的 SCSS 架构、组件和设计规范的详细信息。

## 📚 文档目录

### 🎨 [Design Tokens](./sassdoc/#group-design-tokens)
- [颜色系统](./sassdoc/#variable-$color-primary) - 品牌色彩和语义化颜色
- [字体系统](./sassdoc/#variable-$font-family-system) - 字体族和排版规范
- [间距系统](./sassdoc/#variable-$spacing-xs) - 统一的间距和尺寸规范
- [圆角系统](./sassdoc/#variable-$border-radius-sm) - 一致的圆角规范
- [阴影系统](./sassdoc/#variable-$shadow-sm) - 层次化的阴影效果

### 🧩 [Components](./sassdoc/#group-components)
- [按钮组件](./sassdoc/#mixin-button-base) - 各种按钮样式和变体
- [卡片组件](./sassdoc/#mixin-card-base) - 卡片布局和样式
- [输入框组件](./sassdoc/#mixin-input-base) - 表单元素样式
- [图标组件](./sassdoc/#mixin-icon-base) - 图标系统和大小规范

### 🔧 [Mixins & Functions](./sassdoc/#group-mixins)
- [布局 Mixins](./sassdoc/#mixin-flex-center) - 强大的布局工具
- [响应式 Mixins](./sassdoc/#mixin-breakpoint) - 响应式设计工具
- [工具函数](./sassdoc/#function-strip-unit) - 实用的 SCSS 函数

### 🖋️ [Typography](./sassdoc/#group-typography)
- [标题样式](./sassdoc/#mixin-typography-h1) - 各级标题规范
- [正文样式](./sassdoc/#mixin-typography-body) - 正文排版规范
- [字体工具](./sassdoc/#mixin-font-smoothing) - 字体渲染优化

### 📐 [Layout System](./sassdoc/#group-layout)
- [网格系统](./sassdoc/#mixin-grid-container) - 响应式网格布局
- [容器系统](./sassdoc/#mixin-container) - 内容容器规范
- [间距工具](./sassdoc/#mixin-margin) - 间距和填充工具

### 🌗 [Themes](./sassdoc/#group-themes)
- [主题变量](./sassdoc/#variable-$theme-light) - 主题色彩配置
- [主题切换](./sassdoc/#mixin-theme-transition) - 主题切换动画

## 🚀 快速开始

### 1. 安装依赖
```bash
npm install
```

### 2. 生成文档
```bash
npm run docs:styles
```

### 3. 查看文档
打开 `docs/styles/sassdoc/index.html` 在浏览器中查看

## 📖 使用指南

### 基础引入
```scss
// 在你的主 SCSS 文件中引入设计系统
@import 'src/styles/main';
```

### 使用 Design Tokens
```scss
.my-component {
  background-color: $color-primary;
  padding: $spacing-lg;
  border-radius: $border-radius-md;
  font-family: $font-family-system;
}
```

### 使用 Mixins
```scss
.button {
  @include button-base($color-primary);
  @include button-size(large);
  @include hover-effect();
}
```

### 响应式设计
```scss
.responsive-card {
  @include breakpoint(desktop) {
    max-width: 800px;
  }
  
  @include breakpoint(tablet) {
    padding: $spacing-md;
  }
  
  @include breakpoint(mobile) {
    padding: $spacing-sm;
  }
}
```

## 🛠️ 开发工具

### Stylelint 代码检查
```bash
# 检查样式代码
npm run lint:css

# 自动修复问题
npm run lint:css-fix

# 生成详细报告
npm run lint:css-report
```

### 文档生成
```bash
# 生成 SassDoc 文档
npm run docs:styles

# 重新生成所有文档
npm run docs:build
```

## 📊 设计规范

### 命名约定
- **组件类名**: `c-component-name` (BEM Block)
- **元素类名**: `c-component__element` (BEM Element)
- **修饰符类名**: `c-component--modifier` (BEM Modifier)
- **工具类名**: `u-utility-name` (Utility classes)
- **状态类名**: `is-state` (State classes)

### SCSS 结构
```
src/styles/
├── design-tokens/     # 设计变量系统
├── components/        # 组件样式
├── layout/           # 布局系统
├── themes/           # 主题样式
├── utilities/        # 工具类
└── main.scss         # 主入口文件
```

### 文件组织原则
1. **单一职责**: 每个文件只负责一个特定的功能
2. **清晰命名**: 文件名应该清楚地表达其用途
3. **逻辑分组**: 相关功能的文件放在同一目录下
4. **易于维护**: 结构应该便于团队成员理解和修改

## 🔍 最佳实践

### ✅ 推荐做法
- 始终使用 Design Tokens 而不是硬编码值
- 遵循 BEM 命名规范
- 使用 Mixins 来提高代码复用性
- 保持选择器的简洁性
- 添加适当的注释和文档

### ❌ 避免做法
- 不要在 CSS 中使用 `!important`
- 避免过深的嵌套层级（建议不超过 3 层）
- 不要重复定义相同的样式
- 避免使用 ID 选择器进行样式定义
- 不要忽略浏览器兼容性

## 🤝 贡献指南

我们欢迎所有的贡献！在提交 Pull Request 之前，请确保：

1. 遵循项目的代码风格和命名规范
2. 添加适当的文档注释
3. 通过所有 Stylelint 检查
4. 更新相关文档
5. 添加测试用例（如适用）

详细的贡献指南请查看 [CONTRIBUTING_STYLES.md](../CONTRIBUTING_STYLES.md)。

## 📞 技术支持

如果你有任何问题或建议：

- 📧 发送邮件到: team@imatuproject.com
- 💬 加入我们的开发者群聊
- 🐛 提交 Issue: [GitHub Issues](https://github.com/iMatuProject/design-system/issues)
- 📚 查看完整文档: [在线文档](https://docs.imatuproject.com)

---

*iMatuProject Design System - 让设计更简单，让开发更高效*
