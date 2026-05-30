# 学员成果模块 - 冷启动数据使用指南

## 📋 概述

本指南说明如何使用冷启动数据在开发环境中测试学员成果模块，无需实际后端。

## 🚀 快速开始

### 1. 启用 Mock 模式

在 `achievement.service.ts` 中设置：

```typescript
export class AchievementService {
  private readonly USE_MOCK = true; // 设置为 true 使用 Mock 数据
  // ...
}
```

### 2. 自动加载数据

访问营销页面或任何使用成果模块的页面，Mock 数据会自动加载。

## 📊 可用的 Mock 数据

### 成果数据（8个示例成果）

| ID | 标题 | 类型 | 评分 | 状态 |
|----|------|------|------|------|
| 1 | 智能温室监控系统 | project | 5 | approved |
| 2 | 循迹机器人控制系统 | project | 4 | approved |
| 3 | Python编程认证证书 | certificate | 5 | approved |
| 4 | 全栈Web开发作品集 | portfolio | 5 | approved |
| 5 | 语音控制机器人 | project | 4 | approved |
| 6 | AR增强现实教学系统 | case_study | 5 | approved |
| 7 | 机器学习图像识别系统 | project | 5 | approved |
| 8 | 电路仿真实验报告 | assignment | 4 | approved |

### 统计数据

```typescript
{
  totalAchievements: 1234,      // 总成果数
  pendingReviews: 45,           // 待审核
  approvedAchievements: 1100,    // 已通过
  rejectedAchievements: 89,       // 已拒绝
  averageScore: 4.3,           // 平均评分
  // ... 其他数据
}
```

### 用户进度数据

```typescript
{
  completionPercentage: 85,      // 完成百分比
  totalAchievements: 20,        // 总成果数
  completedAchievements: 17,     // 已完成
  averageScore: 4.6,           // 平均评分
  milestones: [...]              // 里程碑
}
```

## 🔧 Mock 服务功能

### AchievementMockService

提供完整的 API 模拟实现：

#### 成果管理
```typescript
// 获取成果列表
mockService.getAchievements(filter, sort, page, pageSize)

// 获取单个成果
mockService.getAchievementById(id)

// 创建成果
mockService.createAchievement(achievementData)

// 更新成果
mockService.updateAchievement(id, achievementData)

// 删除成果
mockService.deleteAchievement(id)
```

#### 文件管理
```typescript
// 上传文件
mockService.uploadAchievementFile(achievementId, file)

// 删除文件
mockService.deleteAchievementFile(fileId)
```

#### 审核功能
```typescript
// 提交审核
mockService.submitAchievement(id)

// 审核成果
mockService.reviewAchievement(id, reviewData)

// 获取审核记录
mockService.getAchievementReviews(achievementId)
```

#### 模板管理
```typescript
// 获取模板列表
mockService.getTemplates()

// 获取模板详情
mockService.getTemplateById(id)

// 创建模板
mockService.createTemplate(templateData)

// 更新模板
mockService.updateTemplate(id, templateData)

// 删除模板
mockService.deleteTemplate(id)
```

#### 进度和统计
```typescript
// 获取用户进度
mockService.getUserAchievementProgress(userId, courseId, moduleId)

// 获取统计信息
mockService.getAchievementStats(filter)

// 获取最近活动
mockService.getRecentActivity(limit)
```

#### 导出功能
```typescript
// 导出数据
mockService.exportAchievements(filter, format)
```

## 🎨 数据使用示例

### 在营销页面使用

```typescript
export class MarketingAchievementsComponent implements OnInit {
  achievements: Achievement[] = [];
  stats: AchievementStats | null = null;

  constructor(private achievementService: AchievementService) {}

  ngOnInit(): void {
    // 加载数据（自动使用 Mock 数据）
    this.loadData();
  }

  loadData(): void {
    // 获取已审核通过的公开成果
    this.achievementService.getAchievements(
      { status: ['approved'], isPublic: true },
      { field: 'score', direction: 'desc' },
      1,
      6
    ).subscribe({
      next: (response) => {
        this.achievements = response.data;
      }
    });

    // 获取统计数据
    this.achievementService.getAchievementStats().subscribe({
      next: (stats) => {
        this.stats = stats;
      }
    });
  }
}
```

### 在课程页面使用

```typescript
export class CourseAchievementsComponent {
  lessonId = 123;

  constructor(private achievementService: AchievementService) {}

  loadLessonAchievements(): void {
    this.achievementService.getLessonAchievements(
      this.lessonId,
      { status: ['approved'] }
    ).subscribe({
      next: (achievements: Achievement[]) => {
        // 处理课程成果
      }
    });
  }
}
```

### 在用户仪表板使用

```typescript
export class UserDashboardComponent {
  userId = 1001;

  constructor(private achievementService: AchievementService) {}

  loadUserProgress(): void {
    this.achievementService.getUserAchievementProgress(
      this.userId,
      1 // courseId
    ).subscribe({
      next: (progress: AchievementProgress) => {
        // 展示用户进度
      }
    });
  }
}
```

## ⚙️ 配置选项

### 冷启动配置

在 `cold-start-data.ts` 中可以配置：

```typescript
export const COLD_START_CONFIG = {
  enabled: true,              // 是否启用冷启动数据
  autoLoad: true,            // 自动加载数据
  mockDelay: 500,           // 模拟网络延迟（毫秒）
  maxAchievements: 100,       // 最大展示成果数
  refreshInterval: 300000     // 数据刷新间隔（5分钟）
};
```

### 自定义 Mock 数据

修改 `MOCK_ACHIEVEMENTS` 数组：

```typescript
export const MOCK_ACHIEVEMENTS: Achievement[] = [
  {
    id: 1,
    userId: 1001,
    type: 'project',
    title: '你的自定义成果',
    description: '详细描述...',
    files: [],
    status: 'approved',
    score: 5,
    // ... 其他字段
  },
  // 添加更多自定义数据
];
```

### 添加自定义统计

修改 `MOCK_STATS`：

```typescript
export const MOCK_STATS: AchievementStats = {
  totalAchievements: 2000,
  pendingReviews: 50,
  approvedAchievements: 1800,
  rejectedAchievements: 150,
  averageScore: 4.5,
  // ... 自定义统计
};
```

## 🔄 切换到真实 API

### 开发环境 → 生产环境

1. 修改 `achievement.service.ts`：

```typescript
export class AchievementService {
  private readonly USE_MOCK = false; // 设置为 false 使用真实 API
  // ...
}
```

2. 确保后端 API 已部署并可访问

3. 重启应用

### 环境变量配置

可以在 `environment.ts` 中配置：

```typescript
// environment.ts
export const environment = {
  production: false,
  useMockData: true  // 开发环境使用 Mock
};

// environment.prod.ts
export const environment = {
  production: true,
  useMockData: false // 生产环境使用真实 API
};
```

然后在服务中使用：

```typescript
import { environment } from '../../environments/environment';

export class AchievementService {
  private readonly USE_MOCK = environment.useMockData;
  // ...
}
```

## 📝 数据持久化（可选）

### 使用 localStorage 保存 Mock 数据

```typescript
@Injectable()
export class MockStorageService {
  private readonly STORAGE_KEY = 'mock_achievements';

  saveAchievements(achievements: Achievement[]): void {
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(achievements));
  }

  loadAchievements(): Achievement[] | null {
    const data = localStorage.getItem(this.STORAGE_KEY);
    return data ? JSON.parse(data) : null;
  }

  clearAchievements(): void {
    localStorage.removeItem(this.STORAGE_KEY);
  }
}
```

## 🧪 测试 Mock 数据

### 单元测试示例

```typescript
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { AchievementService } from './achievement.service';
import { MOCK_ACHIEVEMENTS, MOCK_STATS } from '../mock-data/cold-start-data';

describe('AchievementService (Mock Mode)', () => {
  let service: AchievementService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        AchievementService,
        // Mock dependencies
      ]
    });
    service = TestBed.inject(AchievementService);
    // 启用 Mock 模式
    (service as any).USE_MOCK = true;
  });

  it('should return mock achievements', (done) => {
    service.getAchievements().subscribe({
      next: (response) => {
        expect(response.data.length).toBe(MOCK_ACHIEVEMENTS.length);
        expect(response.data[0].id).toBe(MOCK_ACHIEVEMENTS[0].id);
        done();
      }
    });
  });

  it('should return mock stats', (done) => {
    service.getAchievementStats().subscribe({
      next: (stats) => {
        expect(stats.totalAchievements).toBe(MOCK_STATS.totalAchievements);
        expect(stats.averageScore).toBe(MOCK_STATS.averageScore);
        done();
      }
    });
  });
});
```

## 🎯 使用场景

### 场景 1：前端开发测试

```typescript
// 开发时启用 Mock
export class AchievementService {
  private readonly USE_MOCK = true; // 快速开发和测试
}
```

### 场景 2：演示环境

```typescript
// 演示环境使用 Mock 数据，展示完整功能
export class AchievementService {
  private readonly USE_MOCK = true;
}
```

### 场景 3：生产环境

```typescript
// 生产环境使用真实 API
export class AchievementService {
  private readonly USE_MOCK = false;
}
```

## 📈 性能优化

### 减少 Mock 延迟

```typescript
export const COLD_START_CONFIG = {
  mockDelay: 100, // 减少延迟，更快响应
};
```

### 禁用 Mock 延迟

```typescript
export const COLD_START_CONFIG = {
  mockDelay: 0, // 无延迟，即时响应
};
```

## 🐛 常见问题

### Q1: Mock 数据不显示？

**A:** 检查以下内容：
1. 确认 `USE_MOCK = true`
2. 检查 `COLD_START_CONFIG.enabled = true`
3. 查看浏览器控制台是否有错误

### Q2: 如何添加新的 Mock 数据？

**A:** 直接修改 `cold-start-data.ts` 中的 `MOCK_ACHIEVEMENTS` 数组。

### Q3: Mock 数据会保存到数据库吗？

**A:** 不会，Mock 数据只存在于内存中，刷新页面会重置。如需持久化，使用 localStorage。

### Q4: 如何切换回真实 API？

**A:** 修改 `USE_MOCK = false`，确保后端 API 可访问。

### Q5: Mock 数据可以修改吗？

**A:** 可以，Mock 数据支持增删改查操作，修改会保存在内存中。

## 📚 相关文档

- **模块文档**: `src/app/features/achievement-integration/README.md`
- **集成指南**: `src/app/features/achievement-integration/integration-guide.md`
- **API 设计**: `backend/api_design_achievement_integration.md`
- **营销集成**: `src/app/features/achievement-integration/MARKETING_INTEGRATION_GUIDE.md`

## 🎉 总结

**冷启动数据已准备就绪！**

- ✅ 8个示例成果数据
- ✅ 完整的统计数据
- ✅ 用户进度数据
- ✅ 活动记录
- ✅ 完整的 Mock 服务
- ✅ 自动延迟模拟
- ✅ 支持所有 API 操作

**启用方式**：将 `achievement.service.ts` 中的 `USE_MOCK` 设置为 `true`

**切换方式**：修改 `USE_MOCK` 的值即可切换 Mock/真实 API

---

**最后更新**: 2026-03-17
**维护团队**: 开发团队
