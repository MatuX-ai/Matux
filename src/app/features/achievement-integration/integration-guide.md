# 学员成果集成模块 - 集成指南

## 📦 前置要求

- Angular 16+
- Angular Material 16+
- 后端 API 服务器运行在 `http://localhost:8000`
- 已配置文件存储服务（如腾讯云COS、AWS S3）

## 🔧 快速集成

### 步骤 1: 注册模块

在 `app.module.ts` 中导入模块：

```typescript
import { NgModule } from '@angular/core';
import { AchievementIntegrationModule } from './features/achievement-integration/achievement-integration.module';

@NgModule({
  declarations: [/* ... */],
  imports: [
    /* ... */
    AchievementIntegrationModule,
  ],
  providers: [/* ... */],
  bootstrap: [AppComponent]
})
export class AppModule {}
```

### 步骤 2: 配置路由

在主路由配置中添加成就模块路由：

```typescript
// app-routing.module.ts
const routes: Routes = [
  // ... 其他路由
  {
    path: 'achievements',
    loadChildren: () =>
      import('./features/achievement-integration/achievement-integration-routing.module').then(
        m => m.AchievementIntegrationRoutingModule
      ),
    canActivate: [AuthGuard] // 需要认证
  },
];
```

### 步骤 3: 在课程播放器中集成成果上传

修改 `ai-edu-course-player.component.ts`：

```typescript
import { MatDialog } from '@angular/material/dialog';
import { AchievementUploadComponent } from './features/achievement-integration/components/achievement-upload/achievement-upload.component';

export class AIEduCoursePlayerComponent implements OnInit, OnDestroy {
  // ... 现有代码

  constructor(
    // ... 现有依赖
    private dialog: MatDialog
  ) {}

  /**
   * 打开成果上传对话框
   */
  openAchievementUpload(): void {
    const dialogRef = this.dialog.open(AchievementUploadComponent, {
      width: '800px',
      maxHeight: '90vh',
      data: {
        moduleId: this.moduleId,
        lessonId: this.lessonId,
        userId: this.userId
      }
    });

    dialogRef.componentInstance.uploadSuccess.subscribe((achievement: Achievement) => {
      // 上传成功后的处理
      console.log('成果上传成功:', achievement);
      this.snackBar.open('🎉 成果上传成功！', '关闭', { duration: 3000 });
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log('对话框关闭', result);
    });
  }
}
```

在 `ai-edu-course-player.component.html` 中添加上传按钮：

```html
<!-- 在工具栏或操作区域添加 -->
<button
  mat-button
  color="primary"
  (click)="openAchievementUpload()"
  class="upload-achievement-btn">
  <mat-icon>cloud_upload</mat-icon>
  上传学习成果
</button>
```

### 步骤 4: 在课程列表中展示成果

修改课程播放器的资源导航组件：

```typescript
// resource-navigator.component.ts
import { AchievementGalleryComponent } from './features/achievement-integration/components/achievement-gallery/achievement-gallery.component';
import { Achievement, AchievementStatus } from './features/achievement-integration/models/achievement.model';

export class ResourceNavigatorComponent {
  // ... 现有代码

  showAchievements = false;
  achievements: Achievement[] = [];
  loadingAchievements = false;

  /**
   * 切换成果展示
   */
  toggleAchievements(): void {
    this.showAchievements = !this.showAchievements;
    if (this.showAchievements && this.achievements.length === 0) {
      this.loadAchievements();
    }
  }

  /**
   * 加载课程成果
   */
  loadAchievements(): void {
    this.loadingAchievements = true;
    this.achievementService.getLessonAchievements(this.lessonId).subscribe({
      next: (achievements: Achievement[]) => {
        this.achievements = achievements.filter(a => a.status === 'approved');
        this.loadingAchievements = false;
      },
      error: () => {
        this.loadingAchievements = false;
      }
    });
  }
}
```

### 步骤 5: 在用户仪表板中添加进度追踪

创建或修改用户仪表板组件：

```typescript
import { Component, OnInit } from '@angular/core';
import { AchievementProgressComponent } from './features/achievement-integration/components/achievement-progress/achievement-progress.component';

@Component({
  selector: 'app-user-dashboard',
  standalone: true,
  imports: [AchievementProgressComponent],
  template: `
    <div class="dashboard">
      <h2>我的学习进度</h2>
      <app-achievement-progress
        [userId]="currentUserId"
        [displayMode]="'full'"
      ></app-achievement-progress>
    </div>
  `
})
export class UserDashboardComponent implements OnInit {
  currentUserId!: number;

  ngOnInit(): void {
    // 获取当前用户ID
    this.currentUserId = this.getCurrentUserId();
  }

  private getCurrentUserId(): number {
    // 从认证服务获取用户ID
    return 1; // 示例值
  }
}
```

## 🎯 使用场景

### 场景 1: 课程章节完成后的成果提交

```typescript
// ai-edu-course-player.component.ts
completeLesson(): void {
  // ... 现有完成逻辑

  // 自动打开成果上传对话框
  this.openAchievementUpload();
}
```

### 场景 2: 教师审核界面

创建教师审核页面：

```typescript
import { Component } from '@angular/core';
import { AchievementService } from './features/achievement-integration/services/achievement.service';
import { Achievement, AchievementStatus } from './features/achievement-integration/models/achievement.model';

@Component({
  selector: 'app-teacher-review-dashboard',
  template: `
    <div class="teacher-dashboard">
      <h2>待审核成果</h2>
      <app-achievement-gallery
        [filter]="{ status: ['pending'] }"
      ></app-achievement-gallery>
    </div>
  `
})
export class TeacherReviewDashboardComponent {
  constructor(private achievementService: AchievementService) {}

  // 管理员可以看到所有待审核的成果
}
```

### 场景 3: 学习路径展示

创建学习路径组件，展示学员在整个课程中的成果：

```typescript
import { Component, Input } from '@angular/core';
import { AchievementGalleryComponent } from './features/achievement-integration/components/achievement-gallery/achievement-gallery.component';

@Component({
  selector: 'app-learning-path',
  template: `
    <div class="learning-path">
      <h2>我的学习成果</h2>
      <app-achievement-gallery
        [userId]="userId"
        [layout]="'timeline'"
      ></app-achievement-gallery>
    </div>
  `
})
export class LearningPathComponent {
  @Input() userId!: number;
}
```

## 🎨 自定义样式

### 覆盖默认样式

在全局样式中自定义成果组件样式：

```scss
// styles.scss

// 自定义成果卡片样式
.achievement-card {
  border-radius: 16px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;

  &:hover {
    transform: translateY(-8px) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2) !important;
  }
}

// 自定义进度条
app-achievement-progress {
  .progress-bar {
    height: 12px !important;
    border-radius: 6px !important;

    .progress-fill {
      background: linear-gradient(90deg, #4285f4, #34a853) !important;
    }
  }
}

// 自定义上传区域
.achievement-upload-container {
  .upload-area {
    border-color: #4285f4 !important;
    background: linear-gradient(135deg, rgba(66, 133, 244, 0.05), rgba(66, 133, 244, 0.1)) !important;

    &:hover {
      border-color: #34a853 !important;
    }
  }
}
```

## 🔌 API 配置

### 修改 API 基础 URL

如果后端 API 不在 `http://localhost:8000`，需要修改 `achievement.service.ts`：

```typescript
// achievement.service.ts
export class AchievementService {
  private readonly API_BASE = environment.production
    ? 'https://api.yourdomain.com/api/v1/achievements'
    : 'http://localhost:8000/api/v1/achievements';

  // ...
}
```

或在 `environment.ts` 中配置：

```typescript
// environment.ts
export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8000/api/v1'
};

// environment.prod.ts
export const environment = {
  production: true,
  apiBaseUrl: 'https://api.yourdomain.com/api/v1'
};
```

然后在服务中使用：

```typescript
export class AchievementService {
  private readonly API_BASE = `${environment.apiBaseUrl}/achievements`;
}
```

## 📱 响应式设计

所有组件都支持响应式设计，自动适配不同屏幕尺寸：

- **桌面端** (> 1200px): 完整功能展示
- **平板端** (768px - 1200px): 简化布局，保持核心功能
- **移动端** (< 768px): 单列布局，触摸优化

## 🧪 测试集成

### 单元测试示例

```typescript
// achievement-upload.component.spec.ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

import { AchievementUploadComponent } from './achievement-upload.component';

describe('AchievementUploadComponent', () => {
  let component: AchievementUploadComponent;
  let fixture: ComponentFixture<AchievementUploadComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        NoopAnimationsModule,
        AchievementUploadComponent
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(AchievementUploadComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should validate file type', () => {
    const validFile = new File([''], 'test.pdf', { type: 'application/pdf' });
    expect(component['isFileTypeAllowed'](validFile)).toBeTrue();
  });

  it('should reject invalid file type', () => {
    const invalidFile = new File([''], 'test.exe', { type: 'application/x-msdownload' });
    expect(component['isFileTypeAllowed'](invalidFile)).toBeFalse();
  });
});
```

## 🚀 性能优化

### 1. 懒加载

使用 Angular 的懒加载优化性能：

```typescript
const routes: Routes = [
  {
    path: 'achievements',
    loadChildren: () =>
      import('./features/achievement-integration/achievement-integration.module').then(
        m => m.AchievementIntegrationModule
      )
  }
];
```

### 2. 虚拟滚动

对于大量成果列表，使用虚拟滚动：

```typescript
import { ScrollingModule } from '@angular/cdk/scrolling';

@NgModule({
  imports: [
    // ...
    ScrollingModule
  ]
})
```

### 3. 图片懒加载

使用 Intersection Observer API 实现图片懒加载：

```typescript
lazyLoadImages(): void {
  const images = document.querySelectorAll('.achievement-image');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement;
        img.src = img.dataset.src || '';
        observer.unobserve(img);
      }
    });
  });

  images.forEach(img => observer.observe(img));
}
```

## 🔒 安全考虑

### 1. 文件上传验证

前端验证（必须配合后端验证）：

```typescript
validateFile(file: File): boolean {
  // 验证文件类型
  const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
  if (!allowedTypes.includes(file.type)) {
    return false;
  }

  // 验证文件大小
  const maxSize = 50 * 1024 * 1024; // 50MB
  if (file.size > maxSize) {
    return false;
  }

  return true;
}
```

### 2. XSS 防护

Angular 默认启用 XSS 防护，但要注意：

```typescript
// 使用 DomSanitizer 安全绑定 HTML
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

export class AchievementDisplayComponent {
  constructor(private sanitizer: DomSanitizer) {}

  getSafeHtml(html: string): SafeHtml {
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }
}
```

### 3. CSRF 防护

确保所有 POST/PUT/DELETE 请求包含 CSRF token：

```typescript
import { HttpClientXsrfModule } from '@angular/common/http';

@NgModule({
  imports: [
    HttpClientModule,
    HttpClientXsrfModule.withOptions({
      cookieName: 'XSRF-TOKEN',
      headerName: 'X-XSRF-TOKEN'
    })
  ]
})
```

## 📊 监控和日志

### 集成 Google Analytics

```typescript
import { Injectable } from '@angular/core';
import { GoogleAnalyticsService } from 'ngx-google-analytics';

@Injectable()
export class AchievementAnalyticsService {
  constructor(private gaService: GoogleAnalyticsService) {}

  trackAchievementUpload(achievementType: string): void {
    this.gaService.event('achievement_upload', 'achievements', achievementType);
  }

  trackAchievementView(achievementId: number): void {
    this.gaService.pageView(`/achievements/${achievementId}`, 'Achievement View');
  }
}
```

## 🔄 迁移指南

如果从旧系统迁移：

### 1. 数据迁移

```python
# 后端迁移脚本示例
def migrate_achievements():
    old_data = OldAchievement.query.all()

    for old in old_data:
        new = Achievement(
            user_id=old.user_id,
            type=old.type,
            title=old.title,
            description=old.description,
            files=convert_files(old.files),
            status=convert_status(old.status),
            created_at=old.created_at
        )
        db.session.add(new)

    db.session.commit()
```

### 2. API 兼容性

保持旧 API 的兼容性：

```typescript
// achievement.service.ts
export class AchievementService {
  // 旧方法（保持兼容）
  getOldAchievements(): Observable<OldAchievement[]> {
    return this.http.get<OldAchievement[]>(`${this.OLD_API_BASE}/achievements`).pipe(
      map(data => data.map(item => this.convertToNewFormat(item)))
    );
  }

  private convertToNewFormat(old: OldAchievement): Achievement {
    return {
      id: old.id,
      userId: old.userId,
      type: old.type as AchievementType,
      title: old.title,
      description: old.description,
      files: [],
      status: 'pending',
      tags: [],
      isPublic: true,
      submittedAt: old.createdAt,
      updatedAt: old.updatedAt
    };
  }
}
```

## 📞 获取帮助

- 查看模块文档: `README.md`
- 查看 API 设计: `backend/api_design_achievement_integration.md`
- 提交问题: 项目 Issue Tracker
- 联系支持: support@yourdomain.com
