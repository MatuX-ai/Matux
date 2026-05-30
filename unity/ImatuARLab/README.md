# ImatuARLab - AR虚拟实验室

## 项目概述
基于Unity WebGL的AR虚拟实验室系统，集成ESP32硬件模型，通过ARKit/ARCore实现虚实结合的接线指引功能。

## 目录结构
```
ImatuARLab/
├── Assets/
│   ├── Scenes/              # 场景文件
│   ├── Scripts/             # C#脚本
│   │   ├── AR/              # AR相关脚本
│   │   ├── Hardware/        # 硬件模型脚本
│   │   └── WebGL/           # WebGL接口脚本
│   ├── Models/              # 3D模型资源
│   │   ├── ESP32/           # ESP32开发板模型
│   │   ├── Sensors/         # 传感器模块模型
│   │   └── Components/      # 电子元件模型
│   ├── Materials/           # 材质资源
│   ├── Textures/            # 纹理资源
│   └── Plugins/             # 插件资源
├── Packages/                # Unity包管理
├── ProjectSettings/         # 项目设置
└── Builds/                  # 构建输出目录
```

## 技术栈
- Unity 2021.3 LTS
- AR Foundation 4.2.x
- ARCore XR Plugin (Android)
- ARKit XR Plugin (iOS)
- WebGL Build Support
- C# .NET 4.x

## 开发环境要求
- Unity Hub 3.0+
- Visual Studio 2019/2022 或 Rider
- Android SDK (用于Android构建)
- Xcode (用于iOS构建，仅Mac可用)

## 构建配置
### WebGL设置
- Target Platform: WebGL
- Compression Format: Brotli
- Template: Minimal
- Memory Size: 256MB
- Exception Support: Full With Stacktrace

### 移动端设置
- Android: API Level 24+, ARM64
- iOS: iOS 11.0+, ARKit 2.0+

## 项目规范
- 脚本命名：PascalCase
- 变量命名：camelCase
- 常量命名：UPPER_SNAKE_CASE
- 文件夹结构：按功能模块组织
- 注释规范：所有公共方法和类必须添加XML文档注释

## 开发流程
1. 功能开发在feature分支进行
2. 代码审查后合并到develop分支
3. 发布版本从develop合并到main分支
4. 每次提交需包含单元测试

---
**项目创建时间**: 2026年2月28日
**项目负责人**: iMatuProject开发团队