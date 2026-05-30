# Shared Styles Library

跨框架共享样式组件库，为Flutter和Angular提供一致的UI组件和动画效果。

## 目录结构

```
shared-styles/
├── animations/                    # 通用动画组件
│   ├── loading-spinners/         # 加载动画
│   │   ├── flutter/              # Flutter版本
│   │   └── angular/              # Angular版本
│   └── transitions/              # 过渡动画
│       ├── fade-animation/
│       └── slide-animation/
├── components/                   # 通用UI组件
│   ├── modals/                  # 模态框组件
│   │   ├── flutter/
│   │   └── angular/
│   └── notifications/           # 通知组件
│       ├── flutter/
│       └── angular/
├── utils/                       # 工具函数和混入
│   ├── responsive-helpers/      # 响应式工具
│   └── accessibility-utils/     # 无障碍工具
└── README.md
```

## 设计原则

### 一致性
- 所有组件遵循相同的设计语言
- 跨框架保持视觉和交互一致性
- 基于统一的Design Tokens系统

### 可复用性
- 组件设计为高度可配置
- 支持主题定制和样式覆盖
- 提供清晰的API接口

### 性能优化
- 最小化bundle大小
- 优化渲染性能
- 支持懒加载和按需引入

## 使用指南

### Flutter集成

1. 将组件文件复制到Flutter项目的相应目录
2. 确保已配置Design Tokens
3. 导入并使用组件：

```dart
import 'package:your_app/shared_styles/loading_spinner.dart';

class MyWidget extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return UniversalLoadingSpinner(
      size: 40,
      color: Theme.of(context).colorScheme.primary,
    );
  }
}
```

### Angular集成

1. 将组件文件复制到Angular项目的相应目录
2. 确保SCSS变量已正确导入
3. 在模块中声明组件：

```typescript
import { UniversalLoadingSpinnerComponent } from './shared-styles/animations/loading-spinner.component';

@NgModule({
  declarations: [
    UniversalLoadingSpinnerComponent,
    // 其他组件
  ],
})
export class AppModule { }
```

在模板中使用：
```html
<universal-loading-spinner 
  [size]="40" 
  [color]="'var(--primary-color)'">
</universal-loading-spinner>
```

## 组件清单

### 动画组件

#### Loading Spinners (加载动画)
- **Flutter**: `UniversalLoadingSpinner`
- **Angular**: `<universal-loading-spinner>`
- 特性：可配置大小、颜色，支持主题适配

#### Transitions (过渡动画)
- Fade Animation (淡入淡出)
- Slide Animation (滑动效果)
- Scale Animation (缩放效果)

### UI组件

#### Modals (模态框)
- **Flutter**: `UniversalModal`
- **Angular**: `<universal-modal>`
- 特性：可配置标题、内容、按钮，支持键盘操作

#### Notifications (通知)
- **Flutter**: `ToastNotification`
- **Angular**: `<toast-notification>`
- 特性：多种类型（成功、警告、错误、信息），自动消失

## 开发规范

### 命名约定

**Flutter:**
- 组件类名：`Universal<ComponentName>`
- 文件名：`component_name.dart`
- 变量名：`camelCase`

**Angular:**
- 组件选择器：`universal-<component-name>`
- 文件名：`component-name.component.ts/html/scss`
- 类名：`Universal<ComponentName>Component`

### 样式规范

1. **必须使用Design Tokens**
   - 颜色：`$color-*` 或 `Theme.of(context).colorScheme.*`
   - 间距：`$spacing-*` 或 Design Tokens中的间距值
   - 字体：`$font-*` 或 `Theme.of(context).textTheme.*`

2. **响应式设计**
   - 支持移动、平板、桌面三种断点
   - 使用相对单位（rem、em）
   - 考虑触摸目标大小

3. **无障碍支持**
   - 提供适当的ARIA标签
   - 支持键盘导航
   - 考虑屏幕阅读器友好性

### 性能要求

- 组件初始化时间 < 50ms
- 动画帧率保持 60fps
- 内存泄漏检测通过
- Bundle大小增量 < 5KB

## 测试标准

### 单元测试
每个组件必须包含：
- 基本渲染测试
- 属性配置测试
- 事件处理测试
- 边界条件测试

### 集成测试
- 跨组件交互测试
- 主题切换兼容性测试
- 响应式行为测试

### 视觉回归测试
- 使用Storybook进行视觉对比
- 建立基准截图
- 自动化差异检测

## 贡献指南

### 开发流程

1. Fork仓库并创建功能分支
2. 按照规范实现组件
3. 编写完整测试用例
4. 更新文档和示例
5. 提交Pull Request

### 代码审查要点

- [ ] 符合命名规范
- [ ] 正确使用Design Tokens
- [ ] 包含必要测试
- [ ] 文档完整准确
- [ ] 性能符合要求
- [ ] 无障碍支持完善

### 发布流程

1. 版本号遵循SemVer规范
2. 更新CHANGELOG.md
3. 打tag并发布
4. 通知相关团队升级

## 版本历史

### v1.0.0 (2024-01-01)
- Initial release
- Loading spinner components
- Modal dialog components
- Notification components
- Basic animations

## 许可证

MIT License - 详见LICENSE文件

## 支持

如有问题，请提交Issue或联系设计系统团队。