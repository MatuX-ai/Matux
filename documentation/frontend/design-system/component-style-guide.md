# iMatuProject 组件样式指南

本文档详细说明了如何在Flutter和Angular框架中实现组件样式的一致性和隔离性。

## 目录

1. [设计原则](#设计原则)
2. [Flutter样式策略](#flutter样式策略)
3. [Angular样式策略](#angular样式策略)
4. [跨框架一致性](#跨框架一致性)
5. [最佳实践](#最佳实践)
6. [组件示例](#组件示例)

## 设计原则

### 核心理念
- **一致性**: 确保跨框架组件外观和行为统一
- **可维护性**: 样式易于修改和扩展
- **性能优化**: 避免样式冗余和重复计算
- **可访问性**: 支持无障碍标准和用户偏好

### 设计令牌优先
所有样式都应该基于Design Tokens系统：
- 颜色使用 `$color-*` 变量
- 间距使用 `$spacing-*` 变量  
- 字体使用 `$font-*` 变量
- 圆角使用 `$border-radius-*` 变量

## Flutter样式策略

### 主题+TextStyle组合模式

#### 基础主题配置
```dart
// lib/theme/component_styles.dart
import 'package:flutter/material.dart';
import 'app_theme.dart';

class ComponentStyles {
  // 按钮样式
  static ButtonStyle primaryButtonStyle(BuildContext context) {
    return ElevatedButton.styleFrom(
      foregroundColor: Theme.of(context).colorScheme.onPrimary,
      backgroundColor: Theme.of(context).colorScheme.primary,
      textStyle: Theme.of(context).textTheme.labelLarge,
      padding: EdgeInsets.symmetric(
        horizontal: Spacing.lg,
        vertical: Spacing.md,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(BorderRadius.md),
      ),
    );
  }
  
  // 卡片样式
  static CardTheme cardTheme(BuildContext context) {
    return CardTheme(
      color: Theme.of(context).colorScheme.surface,
      elevation: 2,
      shadowColor: Theme.of(context).shadowColor,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(BorderRadius.lg),
      ),
    );
  }
}
```

#### 自定义组件样式
```dart
// 使用主题样式创建自定义组件
class CustomButton extends StatelessWidget {
  final VoidCallback onPressed;
  final String text;
  
  const CustomButton({
    Key? key,
    required this.onPressed,
    required this.text,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onPressed,
      style: ComponentStyles.primaryButtonStyle(context),
      child: Text(text),
    );
  }
}
```

### 样式隔离最佳实践

1. **使用Theme.of(context)获取主题值**
2. **避免硬编码颜色和尺寸**
3. **创建可复用的样式函数**
4. **利用BuildContext传递主题上下文**

## Angular样式策略

### CSS Modules + BEM命名法

#### 组件样式结构
```scss
// src/app/shared/components/button/button.component.scss
@import '../../../styles/design-tokens/tokens';

// 块 (Block)
.btn {
  // 基础样式
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: $border-radius-md;
  padding: $spacing-sm $spacing-lg;
  font-family: $font-family-system;
  font-size: $font-size-body-medium;
  font-weight: $font-weight-medium;
  cursor: pointer;
  transition: all $transition-normal;
  
  // 元素 (Element)
  &__icon {
    margin-right: $spacing-xs;
  }
  
  &__text {
    // 文本样式
  }
  
  // 修饰符 (Modifier)
  &--primary {
    background-color: $color-primary;
    color: $color-text-white;
    
    &:hover {
      background-color: $color-primary-dark;
      transform: translateY(-1px);
    }
    
    &:active {
      transform: translateY(0);
    }
    
    &:disabled {
      background-color: $color-gray-300;
      cursor: not-allowed;
      transform: none;
    }
  }
  
  &--secondary {
    background-color: transparent;
    color: $color-primary;
    border: 1px solid $color-primary;
    
    &:hover {
      background-color: $color-primary;
      color: $color-text-white;
    }
  }
  
  // 尺寸变体
  &--small {
    padding: $spacing-xs $spacing-md;
    font-size: $font-size-body-small;
  }
  
  &--large {
    padding: $spacing-md $spacing-xl;
    font-size: $font-size-body-large;
  }
  
  // 状态变体
  &--loading {
    opacity: 0.7;
    pointer-events: none;
  }
}
```

#### 组件实现
```typescript
// src/app/shared/components/button/button.component.ts
import { Component, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: 'app-button',
  templateUrl: './button.component.html',
  styleUrls: ['./button.component.scss'],
  host: {
    'class': 'btn',
    '[class.btn--primary]': 'variant === "primary"',
    '[class.btn--secondary]': 'variant === "secondary"',
    '[class.btn--small]': 'size === "small"',
    '[class.btn--large]': 'size === "large"',
    '[class.btn--loading]': 'loading',
    '[attr.disabled]': 'disabled || loading ? true : null'
  }
})
export class ButtonComponent {
  @Input() variant: 'primary' | 'secondary' = 'primary';
  @Input() size: 'small' | 'medium' | 'large' = 'medium';
  @Input() disabled = false;
  @Input() loading = false;
  @Output() clicked = new EventEmitter<void>();
  
  onClick(): void {
    if (!this.disabled && !this.loading) {
      this.clicked.emit();
    }
  }
}
```

### ViewEncapsulation策略

```typescript
import { Component, ViewEncapsulation } from '@angular/core';

@Component({
  selector: 'app-isolated-component',
  templateUrl: './isolated-component.component.html',
  styleUrls: ['./isolated-component.component.scss'],
  encapsulation: ViewEncapsulation.Emulated // 默认值，提供样式隔离
})
export class IsolatedComponent {
  // 组件逻辑
}
```

## 跨框架一致性

### 样式映射对照表

| 属性 | Flutter | Angular SCSS | Design Token |
|------|---------|--------------|--------------|
| 主色 | `Theme.of(context).colorScheme.primary` | `$color-primary` | `#2196F3` |
| 背景色 | `Theme.of(context).colorScheme.background` | `$color-background` | `#FFFFFF` |
| 主要文字 | `Theme.of(context).textTheme.bodyLarge` | `$font-size-body-large` | `1rem` |
| 圆角 | `BorderRadius.circular(8)` | `$border-radius-md` | `0.5rem` |
| 阴影 | `BoxShadow` | `$shadow-md` | `0 4px 6px...` |

### 响应式设计一致性

#### Flutter响应式
```dart
// 使用LayoutBuilder实现响应式
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth < 768) {
      // 移动端样式
      return MobileComponent();
    } else {
      // 桌面端样式
      return DesktopComponent();
    }
  },
);
```

#### Angular响应式
```scss
// SCSS媒体查询
.component {
  // 默认样式
  padding: $spacing-lg;
  
  @media (max-width: $breakpoint-tablet) {
    // 平板样式
    padding: $spacing-md;
  }
  
  @media (max-width: $breakpoint-mobile) {
    // 移动端样式
    padding: $spacing-sm;
  }
}
```

## 最佳实践

### 1. 样式组织原则

**Flutter:**
- 主题相关样式放在 `theme/` 目录
- 组件特定样式放在组件内部
- 公共样式函数集中管理

**Angular:**
- 使用CSS Modules实现样式隔离
- 遵循BEM命名规范
- 组件样式与模板同目录

### 2. 性能优化

**避免:**
- 过度嵌套的选择器
- 重复的样式声明
- 频繁的主题计算

**推荐:**
- 使用CSS变量减少计算
- 缓存复杂样式计算结果
- 利用框架的样式优化机制

### 3. 可访问性考虑

```scss
// Angular - 高对比度支持
@media (prefers-contrast: high) {
  .component {
    border-width: 2px;
    outline: 2px solid currentColor;
  }
}

// 减少动画偏好
@media (prefers-reduced-motion: reduce) {
  .component {
    transition: none;
    animation: none;
  }
}
```

```dart
// Flutter - 无障碍支持
Semantics(
  label: '重要操作按钮',
  button: true,
  child: ElevatedButton(
    onPressed: onPressed,
    child: Text('点击我'),
  ),
);
```

### 4. 主题切换平滑过渡

```scss
// Angular - 主题切换动画
:root {
  transition: background-color 0.3s ease, color 0.3s ease;
}

.theme-transition {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

```dart
// Flutter - 主题动画
AnimatedTheme(
  data: theme,
  duration: Duration(milliseconds: 300),
  curve: Curves.easeInOut,
  child: MyAppContent(),
);
```

## 组件示例

### 按钮组件完整示例

#### Flutter版本
```dart
// lib/components/universal_button.dart
import 'package:flutter/material.dart';

class UniversalButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final ButtonVariant variant;
  final ButtonSize size;
  final bool loading;
  
  const UniversalButton({
    Key? key,
    required this.text,
    this.onPressed,
    this.variant = ButtonVariant.primary,
    this.size = ButtonSize.medium,
    this.loading = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final buttonStyle = _getButtonStyle(context);
    
    return ElevatedButton(
      onPressed: loading ? null : onPressed,
      style: buttonStyle,
      child: loading 
        ? SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(
                Theme.of(context).colorScheme.onPrimary,
              ),
            ),
          )
        : Text(text),
    );
  }
  
  ButtonStyle _getButtonStyle(BuildContext context) {
    switch (variant) {
      case ButtonVariant.primary:
        return ComponentStyles.primaryButtonStyle(context);
      case ButtonVariant.secondary:
        return ComponentStyles.secondaryButtonStyle(context);
    }
  }
}

enum ButtonVariant { primary, secondary }
enum ButtonSize { small, medium, large }
```

#### Angular版本
```html
<!-- src/app/shared/components/universal-button/universal-button.component.html -->
<button
  class="btn"
  [class.btn--primary]="variant === 'primary'"
  [class.btn--secondary]="variant === 'secondary'"
  [class.btn--small]="size === 'small'"
  [class.btn--large]="size === 'large'"
  [class.btn--loading]="loading"
  [disabled]="disabled || loading"
  (click)="onClick()">
  
  <span class="btn__spinner" *ngIf="loading"></span>
  <span class="btn__text">{{ text }}</span>
</button>
```

```scss
// src/app/shared/components/universal-button/universal-button.component.scss
@import '../../../styles/design-tokens/tokens';

.btn {
  // ... 基础样式同前面示例
  
  &__spinner {
    width: 20px;
    height: 20px;
    border: 2px solid transparent;
    border-top-color: currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

### 卡片组件示例

#### Flutter版本
```dart
class UniversalCard extends StatelessWidget {
  final Widget child;
  final EdgeInsets? padding;
  final double? elevation;
  
  const UniversalCard({
    Key? key,
    required this.child,
    this.padding,
    this.elevation,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: elevation ?? 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(BorderRadius.lg),
      ),
      child: Padding(
        padding: padding ?? EdgeInsets.all(Spacing.lg),
        child: child,
      ),
    );
  }
}
```

#### Angular版本
```scss
.card {
  background: $color-surface;
  border-radius: $border-radius-lg;
  box-shadow: $shadow-card;
  padding: $spacing-lg;
  transition: box-shadow $transition-normal;
  
  &:hover {
    box-shadow: $shadow-card-hover;
  }
  
  &--elevated {
    box-shadow: $shadow-lg;
  }
  
  &__content {
    // 卡片内容区域
  }
}
```

## 测试和验证

### 视觉回归测试
- 使用Storybook进行跨框架组件对比
- 建立设计系统组件库
- 定期进行视觉审查

### 主题一致性检查
- 验证颜色在不同主题下的表现
- 测试组件在各种状态下的样式
- 确保响应式断点的一致性

### 性能监控
- 监控样式计算性能
- 跟踪主题切换的流畅度
- 优化大型组件树的渲染

---

*本文档将持续更新，以反映最新的设计系统实践和框架特性。*