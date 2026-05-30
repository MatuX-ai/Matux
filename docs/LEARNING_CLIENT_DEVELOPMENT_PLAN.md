# 学习端开发计划（桌面端 + 移动端）

## 📋 项目概述

**开发目标**：构建完整的学习端应用（桌面端 Electron + 移动端 Flutter）
**预计用时**：8周
**技术栈**：
- 桌面端：Electron + Angular（复用现有Web组件）
- 移动端：Flutter + Hive本地数据库
- 后端：FastAPI（增强数据同步API）

---

## 🎯 开发策略

由于项目规模较大，采用**增量交付**策略，优先实现核心功能：

1. **P0 核心功能**（必须完成）：移动端学习基础功能
2. **P1 重要功能**（应该完成）：桌面端离线学习、移动端特色功能
3. **P2 增强功能**（可以完成）：手势识别、AR实验室
4. **P3 优化功能**（锦上添花）：性能优化、文档完善

---

## 📊 本期开发范围（阶段一：移动端P0核心功能）

### 1.1 学习Dashboard页面
- ✅ 学习统计展示（总课程数、进行中、已完成）
- ✅ 推荐课程列表
- ✅ 最近学习课程
- ✅ 学习进度可视化

### 1.2 课程列表页面
- ✅ 课程筛选（类别、难度、时长）
- ✅ 搜索功能
- ✅ 课程卡片展示
- ✅ 分页加载

### 1.3 课程详情页面
- ✅ 课程信息展示
- ✅ 课程大纲（模块-课时结构）
- ✅ 开始学习入口
- ✅ 相关课程推荐

### 1.4 后端API集成
- ✅ 复用现有Web端API
- ✅ 统一课程服务集成
- ✅ 学习进度查询

---

## 🏗️ 技术选型理由

### Flutter技术栈
- **跨平台**：一套代码支持iOS/Android
- **性能优异**：原生编译，接近原生应用体验
- **丰富的UI组件**：Material Design 3开箱即用
- **已有基础**：项目已有Design System架构

### Hive本地数据库
- **轻量快速**：适合移动端本地存储
- **类型安全**：支持Dart类型系统
- **离线优先**：支持离线学习场景

### Dio网络库
- **功能完整**：支持拦截器、请求取消、超时配置
- **易于使用**：API设计简洁
- **广泛使用**：Flutter社区首选HTTP库

---

## 📦 模块划分与依赖关系

```
flutter_app/
├── lib/
│   ├── main.dart                 # 应用入口
│   ├── models/                   # 数据模型
│   │   ├── course.models.dart    # 课程模型
│   │   ├── progress.models.dart  # 进度模型
│   │   └── user.models.dart      # 用户模型
│   ├── services/                 # 业务服务
│   │   ├── api.service.dart      # 网络请求服务
│   │   ├── course.service.dart   # 课程业务逻辑
│   │   ├── auth.service.dart     # 认证服务
│   │   └── storage.service.dart  # 本地存储服务
│   ├── screens/                  # 页面组件
│   │   ├── dashboard/            # 学习仪表板
│   │   ├── courses/              # 课程相关页面
│   │   └── auth/                 # 认证页面
│   ├── widgets/                  # 可复用组件
│   │   ├── course-card/          # 课程卡片
│   │   ├── progress-bar/         # 进度条
│   │   └── loading/              # 加载组件
│   └── utils/                    # 工具函数
│       ├── api-client.dart       # API客户端
│       ├── constants.dart        # 常量定义
│       └── validators.dart       # 验证器
├── assets/                       # 资源文件
│   └── tokens/                   # Design Tokens
└── pubspec.yaml                  # 依赖配置
```

**依赖关系**：
- Services依赖Models
- Screens依赖Services和Widgets
- Widgets依赖Utils
- Models独立（无依赖）

---

## 🗄️ 数据库设计（本地Hive）

### 课程缓存表（courses）
```dart
class CachedCourse {
  final int id;
  final String title;
  final String description;
  final String category;
  final String difficulty;
  final int durationMinutes;
  final String coverImageUrl;
  final DateTime cachedAt;
  final DateTime expiresAt;
}
```

### 学习进度表（progress）
```dart
class LearningProgress {
  final int courseId;
  final int moduleId;
  final int lessonId;
  final double progressPercentage;
  final DateTime lastAccessTime;
  final bool isCompleted;
}
```

### 用户偏好表（preferences）
```dart
class UserPreferences {
  final String themeMode; // light/dark/system
  final String language; // zh/en
  final bool autoPlayVideo;
  final int videoQuality; // 720/1080
}
```

---

## 🔌 API端点设计（复用现有Web端API）

### 课程相关
```
GET  /api/v1/org/{org_id}/unified/courses          # 获取课程列表
GET  /api/v1/org/{org_id}/unified/courses/{id}     # 获取课程详情
GET  /api/v1/org/{org_id}/unified/courses/recommended  # 推荐课程
GET  /api/v1/org/{org_id}/course-enrollments/user/{user_id}  # 用户报名课程
```

### 学习进度相关
```
GET  /api/v1/org/{org_id}/ai-edu/progress          # 获取学习进度
POST /api/v1/org/{org_id}/ai-edu/progress          # 更新学习进度
GET  /api/v1/org/{org_id}/ai-edu/statistics        # 学习统计
```

### 认证相关
```
POST /api/v1/auth/login                             # 登录
POST /api/v1/auth/logout                            # 登出
GET  /api/v1/auth/me                                # 获取当前用户
```

---

## ⏱️ 预计用时与风险点

### 时间估算

| 任务 | 预计用时 | 优先级 |
|------|---------|--------|
| 项目配置与环境搭建 | 0.5天 | P0 |
| 数据模型定义 | 0.5天 | P0 |
| API服务层开发 | 1天 | P0 |
| 学习Dashboard页面 | 1天 | P0 |
| 课程列表页面 | 1天 | P0 |
| 课程详情页面 | 1天 | P0 |
| 本地存储与缓存 | 0.5天 | P0 |
| 单元测试 | 0.5天 | P0 |
| 集成测试与修复 | 0.5天 | P0 |
| 文档编写 | 0.5天 | P0 |
| **合计** | **7天** | - |

### 风险点

| 风险 | 影响 | 缓解方案 |
|------|------|---------|
| Web端API响应格式不兼容 | 高 | 先进行API联调测试，必要时添加适配层 |
| Flutter版本兼容性问题 | 中 | 锁定Flutter版本，使用稳定版 |
| 本地数据库迁移问题 | 中 | 设计版本化数据模型，支持平滑升级 |
| iOS真机调试环境配置 | 低 | 优先使用Android模拟器开发，iOS稍后适配 |

---

## 🚀 开发流程

### 第一阶段：基础设施（0.5天）
- [ ] 配置Flutter项目依赖（Dio、Hive、Provider等）
- [ ] 定义数据模型（Course、Progress、User等）
- [ ] 创建API客户端基础类

### 第二阶段：服务层开发（1.5天）
- [ ] 实现认证服务（登录/登出/获取当前用户）
- [ ] 实现课程服务（列表/详情/推荐）
- [ ] 实现进度服务（查询/更新）
- [ ] 实现本地存储服务（缓存/读取/过期清理）

### 第三阶段：页面开发（3天）
- [ ] 开发学习Dashboard页面
- [ ] 开发课程列表页面（带筛选和搜索）
- [ ] 开发课程详情页面（带大纲展示）

### 第四阶段：测试与优化（1.5天）
- [ ] 编写单元测试（服务层）
- [ ] 编写Widget测试（UI组件）
- [ ] 集成测试（端到端流程）
- [ ] 性能优化（加载速度、内存占用）

### 第五阶段：文档与交付（0.5天）
- [ ] 编写API文档
- [ ] 编写用户使用手册
- [ ] 代码审查与重构

---

## 📝 验收标准

### 功能完整性
- [ ] 用户可以登录系统
- [ ] 用户可以查看学习Dashboard（统计、推荐、最近学习）
- [ ] 用户可以浏览课程列表（筛选、搜索、分页）
- [ ] 用户可以查看课程详情（大纲、开始学习）
- [ ] 学习进度正确同步到后端

### 性能指标
- [ ] 应用启动时间 < 3秒
- [ ] 页面加载时间 < 2秒
- [ ] 内存占用 < 150MB
- [ ] 列表滑动流畅（60fps）

### 代码质量
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] 所有测试通过
- [ ] 代码注释率 ≥ 15%
- [ ] 遵循Flutter代码规范

---

## 🔄 后续扩展计划

**下一阶段**（桌面端核心功能）：
- Electron本地数据层构建
- 离线学习功能
- 桌面端UI优化

**未来扩展**：
- 手势识别学习
- AR实验室体验
- 语音学习助手

---

## 📞 技术支持

- **Flutter官方文档**：https://flutter.dev/docs
- **Hive文档**：https://docs.hivedb.dev/
- **Dio文档**：https://pub.dev/packages/dio
- **Material Design 3**：https://m3.material.io/

---

**计划版本**：v1.0  
**创建日期**：2026-05-28  
**最后更新**：2026-05-28
