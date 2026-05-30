# iMatuProject Flutter Design System

This Flutter application demonstrates the integration of Design Tokens with Flutter's ThemeData system.

## 项目结构

```
flutter_app/
├── lib/
│   ├── theme/
│   │   ├── app_theme.dart          # 主题配置入口
│   │   ├── color_scheme.dart       # 颜色系统映射
│   │   ├── typography.dart         # 字体系统映射
│   │   └── tokens_loader.dart      # JSON token加载器
│   └── main.dart                   # 应用入口
├── assets/
│   └── tokens/                     # Design Tokens (JSON格式)
│       ├── colors.json
│       ├── fonts.json
│       ├── spacing.json
│       ├── border-radius.json
│       ├── shadows.json
│       └── index.json
└── pubspec.yaml                    # Flutter配置文件
```

## 功能特性

### 🎨 Design Tokens集成
- 自动从JSON tokens加载颜色、字体、间距等设计变量
- 支持亮色和暗色主题
- 实时主题切换功能

### 📱 组件演示
- 主题化按钮样式
- 卡片组件展示
- 颜色调色板预览
- 响应式布局

### 🔧 技术实现
- 异步token加载
- 缓存机制优化性能
- Material Design 3 组件
- 自适应颜色对比度

## 快速开始

1. 确保已安装Flutter SDK (3.0.0+)
2. 在项目根目录运行：
   ```bash
   cd flutter_app
   flutter pub get
   flutter run
   ```

## 主题使用说明

### 基本用法
```dart
// 在Widget中使用主题
Text(
  'Hello World',
  style: Theme.of(context).textTheme.headlineMedium,
)

// 使用主题颜色
Container(
  color: Theme.of(context).colorScheme.primary,
  child: Text(
    'Primary Color',
    style: TextStyle(
      color: Theme.of(context).colorScheme.onPrimary,
    ),
  ),
)
```

### 自定义组件样式
```dart
// 使用预定义的按钮样式
ElevatedButton(
  onPressed: () {},
  style: AppTheme.getPrimaryButtonStyle(context),
  child: Text('Click Me'),
)
```

## Design Tokens来源

Tokens来自项目根目录的 `dist/tokens/` 目录，由TypeScript tokens自动转换为JSON格式。

## 开发说明

- 所有设计变量都通过 `TokensLoader` 从assets加载
- 颜色和字体系统分别由 `ColorSchemeMapper` 和 `TypographyMapper` 处理
- 主题配置集中在 `AppTheme` 类中管理
- 支持热重载开发体验

## 注意事项

- 确保 `assets/tokens/` 目录下的JSON文件是最新的
- 修改tokens后需要重新构建应用
- 暗色主题会自动调整颜色对比度以确保可读性