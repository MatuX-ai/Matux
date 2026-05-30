# 学员成果集成模块 (Achievement Integration Module)

## 📋 模块概述

该模块用于将学员的学习成果（项目、作品、证书等）无缝集成到现有课程体系中，支持成果上传、审核、展示和进度追踪。

## ✨ 核心功能

### 1. 成果上传 (AchievementUploadComponent)
- 支持多种文件类型：图片、PDF、Word、PPT、ZIP、视频等
- 拖拽上传和点击上传
- 文件类型和大小验证（单文件最大50MB）
- 成果类型分类：项目案例、证书、作业、作品集、案例研究
- 标签管理和公开设置
- 实时上传进度显示

### 2. 成果展示 (AchievementGalleryComponent & AchievementDisplayComponent)
- 多种布局：网格视图、列表视图、时间线视图
- 筛选功能：按类型、状态、时间范围筛选
- 搜索功能：支持标题和描述搜索
- 排序功能：按时间、评分、标题排序
- 成果模板系统：支持自定义展示样式
- 分页加载
- 文件预览和下载
- 社交分享功能

### 3. 成果审核 (AchievementReviewComponent)
- 教师和管理员审核功能
- 三种审核状态：通过、拒绝、需要修改
- 评分系统：1-5分星级评价
- 反馈意见输入
- 审核历史记录
- 审核统计和报告

### 4. 学习进度关联 (AchievementProgressComponent)
- 学习进度可视化
- 里程碑达成追踪
- 成果完成度统计
- 平均评分计算
- 进度趋势分析

## 🗂️ 数据模型

### Achievement（成果）
```typescript
interface Achievement {
  id: number;
  userId: number;
  moduleId?: number;
  lessonId?: number;
  type: AchievementType;
  title: string;
  description: string;
  files: AchievementFile[];
  status: AchievementStatus;
  score?: number;
  feedback?: string;
  reviewedBy?: number;
  reviewedAt?: string;
  submittedAt: string;
  updatedAt: string;
  tags: string[];
  isPublic: boolean;
}
```

### AchievementProgress（学习进度）
```typescript
interface AchievementProgress {
  achievementId: number;
  userId: number;
  courseId?: number;
  moduleId?: number;
  lessonId?: number;
  completionPercentage: number;
  totalAchievements: number;
  completedAchievements: number;
  averageScore: number;
  lastUpdated: string;
  milestones: ProgressMilestone[];
}
```

### AchievementTemplate（展示模板）
```typescript
interface AchievementTemplate {
  id: number;
  name: string;
  type: AchievementType;
  layout: 'card' | 'grid' | 'timeline' | 'masonry';
  styles: TemplateStyle;
  fields: TemplateField[];
}
```

## 📂 目录结构

```
achievement-integration/
├── achievement-integration.module.ts          # 主模块
├── achievement-integration-routing.module.ts  # 路由配置
├── models/
│   └── achievement.model.ts                    # 数据模型
├── services/
│   └── achievement.service.ts                # 后端服务
├── components/
│   ├── achievement-upload/                    # 上传组件
│   │   ├── achievement-upload.component.ts
│   │   ├── achievement-upload.component.html
│   │   └── achievement-upload.component.scss
│   ├── achievement-gallery/                   # 展示廊组件
│   │   ├── achievement-gallery.component.ts
│   │   ├── achievement-gallery.component.html
│   │   └── achievement-gallery.component.scss
│   ├── achievement-review/                   # 审核组件
│   │   ├── achievement-review.component.ts
│   │   ├── achievement-review.component.html
│   │   └── achievement-review.component.scss
│   ├── achievement-display/                  # 展示组件
│   │   ├── achievement-display.component.ts
│   │   ├── achievement-display.component.html
│   │   └── achievement-display.component.scss
│   └── achievement-progress/                 # 进度组件
│       ├── achievement-progress.component.ts
│       ├── achievement-progress.component.html
│       └── achievement-progress.component.scss
└── README.md
```

## 🚀 使用方法

### 1. 导入模块

```typescript
import { AchievementIntegrationModule } from './features/achievement-integration/achievement-integration.module';

@NgModule({
  imports: [
    AchievementIntegrationModule,
    // ...
  ],
})
export class AppModule {}
```

### 2. 使用上传组件

```html
<app-achievement-upload
  [moduleId]="moduleId"
  [lessonId]="lessonId"
  (uploadSuccess)="onUploadSuccess($event)"
></app-achievement-upload>
```

### 3. 使用展示廊组件

```html
<app-achievement-gallery
  [userId]="userId"
  [moduleId]="moduleId"
  [layout]="'grid'"
></app-achievement-gallery>
```

### 4. 使用审核组件

```html
<app-achievement-review
  [achievement]="selectedAchievement"
  (reviewComplete)="onReviewComplete($event)"
></app-achievement-review>
```

### 5. 使用进度组件

```html
<app-achievement-progress
  [userId]="userId"
  [courseId]="courseId"
  [displayMode]="'full'"
></app-achievement-progress>
```

## 🎨 自定义模板

创建自定义展示模板：

```typescript
const customTemplate: AchievementTemplate = {
  id: 1,
  name: 'custom-card',
  type: 'project',
  layout: 'card',
  styles: {
    backgroundColor: '#ffffff',
    textColor: '#333333',
    accentColor: '#4285f4',
    cardStyle: 'elevated',
    borderRadius: 12,
    showProgress: true,
    showTags: true,
    showDate: true,
  },
  fields: [
    { key: 'title', label: '标题', type: 'text', required: true, displayInCard: true, displayInDetail: true },
    // ... 更多字段配置
  ],
};
```

## 🔌 API 端点

### 成果管理
- `GET /api/v1/achievements/achievements` - 获取成果列表
- `GET /api/v1/achievements/achievements/:id` - 获取单个成果
- `POST /api/v1/achievements/achievements` - 创建成果
- `PUT /api/v1/achievements/achievements/:id` - 更新成果
- `DELETE /api/v1/achievements/achievements/:id` - 删除成果
- `POST /api/v1/achievements/achievements/:id/submit` - 提交审核
- `POST /api/v1/achievements/achievements/:id/review` - 审核成果

### 文件管理
- `POST /api/v1/achievements/achievements/:id/files` - 上传文件
- `DELETE /api/v1/achievements/files/:id` - 删除文件

### 进度和统计
- `GET /api/v1/achievements/users/:userId/progress` - 获取用户进度
- `GET /api/v1/achievements/stats` - 获取统计信息
- `GET /api/v1/achievements/activity` - 获取最近活动

### 模板管理
- `GET /api/v1/achievements/templates` - 获取模板列表
- `POST /api/v1/achievements/templates` - 创建模板
- `PUT /api/v1/achievements/templates/:id` - 更新模板
- `DELETE /api/v1/achievements/templates/:id` - 删除模板

## 📊 权限说明

### 学员
- 上传自己的学习成果
- 查看自己的成果和进度
- 查看公开的他人成果
- 编辑和删除自己的草稿

### 教师
- 审核学员成果
- 提供评分和反馈
- 查看所教课程的成果
- 查看学员进度

### 管理员
- 审核所有成果
- 管理成果模板
- 查看所有统计信息
- 导出成果数据
- 管理课程和模块关联

## 🔧 配置说明

### 文件上传配置
- 支持的文件类型在 `achievement-upload.component.ts` 中的 `allowedFileTypes` 配置
- 文件大小限制默认为 50MB，可在组件中调整

### 成果类型配置
- 在 `achievement-upload.component.ts` 中的 `achievementTypes` 配置

### 状态配置
- 成果状态：`pending`（待审核）、`approved`（已通过）、`rejected`（已拒绝）、`revision`（需修改）
- 可根据需求扩展

## 🎯 最佳实践

1. **成果命名规范**：使用清晰、描述性的标题
2. **文件组织**：按项目或章节组织文件
3. **标签使用**：使用相关标签便于搜索和分类
4. **审核反馈**：提供具体的建设性反馈
5. **进度追踪**：定期查看和更新学习进度

## 🐛 常见问题

### Q: 上传的文件大小超过限制怎么办？
A: 可在代码中调整文件大小限制，或将大文件压缩后上传。

### Q: 如何自定义成果展示模板？
A: 使用模板管理API或直接在数据库中创建自定义模板。

### Q: 审核后可以修改吗？
A: 审核后可提交修改版本，但原审核记录会保留。

### Q: 如何导出成果数据？
A: 使用 `/api/v1/achievements/export` 端点导出CSV或Excel格式。

## 🔄 更新日志

### v1.0.0 (2026-03-17)
- 初始版本发布
- 实现成果上传、展示、审核功能
- 实现学习进度追踪
- 实现成果模板系统

## 📞 技术支持

如有问题或建议，请联系开发团队。
