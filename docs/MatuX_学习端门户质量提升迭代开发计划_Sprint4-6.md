# MatuX 学习端门户质量提升迭代开发计划 Sprint4-6

> **编制日期**：2026-06-10  
> **前置任务**：首页 dashboard 系统性修复（2026-06-10）+ Sprint0-3 P0 级缺口修复  
> **审计角色**：项目经理 + Senior Engineer 联合审计  
> **目标读者**：开发团队、PM、验收测试工程师  
> **后续文档**：`docs/MatuX_桌面端迭代开发计划_Sprint0-3.md`（已完成）

---

## 一、审计结论摘要

| Sprint | 功能域 | 计划状态 | 当前完成度 | 阻塞级缺陷 | 判定 |
|--------|--------|----------|------------|------------|------|
| Sprint 4 | Dashboard 真实 API 接入 (F-21, F-28) | P0 | **30%** | 2 | 需启动 |
| Sprint 5 | 课件库独立 + AI 教师接入 (F-22, F-24) | P1 | **15%** | 1 | 需启动 |
| Sprint 6 | 性能优化 + 跨模块联动 (F-23, F-25-F-27) | P2 | **0%** | 0 | 规划中 |

**审计结论**：Sprint 4-6 聚焦 dashboard 真实化、课件库独立、AI 教师真实接入三大目标。基于 2026-06-10 首页系统性修复的成果，进一步消除 mock 数据和死链问题，提升学习端门户数据真实性和用户体验完整性。

---

## 二、需求背景

2026-06-10 完成首页（`/user/dashboard/student`）系统性修复：
- 删除冗余 H1、迁移布局按钮
- 新增 4 个状态化大卡片（PRD 6.10 节规范）
- 完整恢复 8 个 widget（全模块保留）
- 删除过度动画、补齐快捷工具标签

**修复后遗留问题**（本次迭代要解决）：

| 序号 | 问题 | 严重度 | 当前状态 | 对应 Sprint |
|------|------|--------|----------|------------|
| **F-21** | dashboard 8 个 widget 中 4 个仍使用 mock 数据 | P0 | Sprint4 处理 | Sprint 4 |
| **F-22** | 课件库无独立路由，仅首页 widget 嵌入 6 张素材卡 | P1 | Sprint5 处理 | Sprint 5 |
| **F-23** | `app-learning-calendar-heatmap` 同步 import，dashboard bundle 体积过大 | P2 | Sprint6 处理 | Sprint 6 |
| **F-24** | AI 教师聊天面板用 setTimeout 模拟响应，未接入真实 LLM | P1 | Sprint5 处理 | Sprint 5 |
| **F-25** | 推荐课程数据为静态 mock，无个性化算法 | P2 | Sprint6 处理 | Sprint 6 |
| **F-26** | dashboard 与学习画像（`/user/learning-profile`）无联动 | P2 | Sprint6 处理 | Sprint 6 |
| **F-27** | dashboard 与学习报告（`/user/reports`）无联动 | P2 | Sprint6 处理 | Sprint 6 |
| **F-28** | 推荐课程跳转按钮无 onClick 处理（"开始学习" 死链） | P0 | Sprint4 处理 | Sprint 4 |

---

## 三、迭代排期

| Sprint | 周期 | 目标 | 核心交付 | 前置依赖 |
|--------|------|------|----------|----------|
| **Sprint 4** | 1 周（2026-06-11 ~ 2026-06-17） | dashboard 数据真实化 | 8 个 widget 全部接入真实 API；修复跳转死链 | 后端 API 已就绪 |
| **Sprint 5** | 1.5 周（2026-06-18 ~ 2026-07-02） | 课件库独立 + AI 教师接入 | `/user/materials` 全功能页；AI 教师面板真实 LLM | Sprint 4 完成 |
| **Sprint 6** | 1 周（2026-07-03 ~ 2026-07-09） | 性能优化 + 跨模块联动 | Heatmap lazy load；推荐算法；学习画像/报告联动 | Sprint 5 完成 |

**总周期**：3.5 周（2026-06-11 ~ 2026-07-09）

---

## 四、详细任务分解

### 4.1 Sprint 4：dashboard 真实 API 接入（1 周）

| Task | 功能点 | 严重度 | 文件位置 | 工作量 |
|------|--------|--------|----------|--------|
| Task 4.1 | 推荐课程跳转死链修复 | P0 | student-dashboard.component.html/ts | 0.75 人天 |
| Task 4.2 | 状态卡 4 卡真实数据接入 | P0 | student-dashboard.component.ts | 1.5 人天 |
| Task 4.3 | 统计卡片真实数据接入 | P0 | student-dashboard.component.ts | 1.5 人天 |
| Task 4.4 | 成就墙真实数据接入 | P0 | student-dashboard.component.ts | 1.25 人天 |
| Task 4.5 | 学习日历热力图真实数据接入 | P0 | student-dashboard.component.ts | 1.25 人天 |
| Task 4.6 | 统一数据加载编排 | P0 | student-dashboard.component.ts | 0.75 人天 |
| **Sprint 4 合计** | | | | **7 人天** |

---

### Task 4.1：推荐课程跳转死链修复（F-28 P0）

**文件**：
- `src/app/user/student/student-dashboard.component.html`（推荐课程区块第 396-435 行）
- `src/app/user/student/student-dashboard.component.ts`

**问题**：第 414 行 `<button mat-raised-button color="primary">` 没有 `(click)` 事件处理，"开始学习"按钮为死链。

**修复方案**：
```typescript
// 在 TS 类中新增方法
onRecommendedCourseClick(course: RecommendedCourse): void {
  void this.router.navigate(['/user/courses'], {
    queryParams: { courseTitle: course.title, level: course.level },
  });
}
```

```html
<!-- HTML 修改 -->
<button
  mat-raised-button
  color="primary"
  (click)="onRecommendedCourseClick(course)"
>
  <mat-icon>play_arrow</mat-icon>
  开始学习
</button>
```

**验收**：
- [ ] 点击"开始学习"按钮跳转到 `/user/courses`，URL 携带课程标题和难度参数
- [ ] 课程列表页接收参数后自动搜索并定位目标课程

---

### Task 4.2：状态卡 4 卡真实数据接入（F-21 P0）

**文件**：`src/app/user/student/student-dashboard.component.ts`

**当前状态**：
- `recentAiWork = { title: '智能感应小夜灯', daysAgo: 3 }`（硬编码 mock）
- `recentArExperiment = { title: '巡线小车', pendingReview: 2 }`（硬编码 mock）
- `learningStreak = { days: 12, ... }`（硬编码 mock）

**修复方案**：

**Step 1**：扩展现有服务接口

```typescript
// src/app/core/services/ai-edu-websocket.service.ts 新增方法
interface RecentAiWork {
  workId: string;
  title: string;
  daysAgo: number;
  score?: number;
}

interface RecentArExperiment {
  experimentId: string;
  title: string;
  pendingReview: number;
}

interface LearningStreak {
  days: number;
  unlockedCount: number;
  total: number;
}

@Injectable({ providedIn: 'root' })
export class AiEduDashboardService {
  getRecentAiWork(userId: number): Observable<RecentAiWork | null>;
  getRecentArExperiment(userId: number): Observable<RecentArExperiment | null>;
  getLearningStreak(userId: number): Observable<LearningStreak>;
}
```

**Step 2**：在 `triggerDataLoad()` 中并行加载

```typescript
forkJoin({
  aiWork: this.aiEduService.getRecentAiWork(userId).pipe(
    catchError(() => of({ workId: '', title: '尚无作品', daysAgo: 0 }))
  ),
  arExperiment: this.arLabService.getRecentExperiment(userId).pipe(
    catchError(() => of({ experimentId: '', title: '尚无实验', pendingReview: 0 }))
  ),
  streak: this.achievementService.getLearningStreak(userId).pipe(
    catchError(() => of({ days: 0, unlockedCount: 0, total: this.achievementBadges.length }))
  ),
}).pipe(takeUntil(this.destroy$)).subscribe(({ aiWork, arExperiment, streak }) => {
  this.recentAiWork = aiWork;
  this.recentArExperiment = arExperiment;
  this.learningStreak = streak;
  this.cdr.markForCheck();
});
```

**Step 3**：新增空状态文案

```html
<!-- 卡片 1 空态 -->
<span class="status-card-title" *ngIf="!recentCourses[0]">
  开始你的第一门课程
</span>
<span class="status-card-meta">点击浏览课程库</span>
```

**验收**：
- [ ] 真实账号登录后，4 个状态卡显示真实学习数据
- [ ] 后端 API 失败时降级为 mock 或空态文案，不出现 undefined 或崩溃
- [ ] API 响应超时（5s）正确降级
- [ ] 切换账号后数据刷新

---

### Task 4.3：统计卡片真实数据接入（F-21 P0）

**文件**：`src/app/user/student/student-dashboard.component.ts`

**当前状态**：`progressStats` 已通过 `MultiSourceLearningService.getUserUnifiedProgress()` 接入，但**未覆盖 source_breakdown**（学习来源分项）。

**修复方案**：

**Step 1**：扩展统计卡片为 4 + 1 模式（增加「来源分项」折叠面板）

```html
<mat-card class="stat-card stat-card--neutral">
  <mat-card-content>
    <mat-icon class="stat-icon">school</mat-icon>
    <div class="stat-value">{{ progressStats?.total_courses ?? 0 }}</div>
    <div class="stat-label">总课程数</div>
  </mat-card-content>
</mat-card>
<!-- 其余 3 个 stat-card 不变 -->

<!-- 新增来源分项 -->
<div class="source-breakdown" *ngIf="progressStats?.source_breakdown?.length">
  <h3>学习来源分项</h3>
  <div class="source-breakdown-grid">
    <div *ngFor="let item of progressStats.source_breakdown" class="source-item">
      <span class="source-name">{{ item.source_name }}</span>
      <span class="source-courses">{{ item.courses }} 门 · 完成 {{ item.completed }}</span>
      <mat-progress-bar mode="determinate" [value]="getSourceProgress(item)"></mat-progress-bar>
    </div>
  </div>
</div>
```

**Step 2**：TS 辅助方法

```typescript
getSourceProgress(item: SourceBreakdown): number {
  return item.courses > 0 ? Math.round((item.completed / item.courses) * 100) : 0;
}
```

**验收**：
- [ ] 4 个统计卡片显示真实数据（来源：mock 或真实 API）
- [ ] 来源分项折叠面板可展开/收起
- [ ] 空数据时不渲染来源分项（避免显示 0）

---

### Task 4.4：成就墙真实数据接入（F-21 P0）

**文件**：`src/app/user/student/student-dashboard.component.ts`

**当前状态**：`achievementBadges` 已通过 `getMockAchievementBadges()` 初始化（12 个 mock）。

**修复方案**：

**Step 1**：新建 `AchievementService`

```typescript
// src/app/core/services/achievement.service.ts（新建）
@Injectable({ providedIn: 'root' })
export class AchievementService {
  constructor(private http: HttpClient) {}
  
  getUserAchievements(userId: number): Observable<MockAchievementBadge[]> {
    return this.http.get<ApiResponse<MockAchievementBadge[]>>(
      `/api/v1/users/${userId}/achievements`
    ).pipe(
      map(res => res.success ? res.data : []),
      catchError(() => of(getMockAchievementBadges()))
    );
  }
}
```

**Step 2**：在 dashboard `triggerDataLoad` 中加载

```typescript
achievements: this.achievementService.getUserAchievements(userId).pipe(
  catchError(() => of(getMockAchievementBadges()))
)
```

**Step 3**：订阅后赋值

```typescript
.subscribe(result => {
  if (result.achievements) {
    this.achievementBadges = result.achievements;
  }
});
```

**验收**：
- [ ] 真实账号登录后成就墙显示用户实际解锁的徽章
- [ ] 后端无徽章数据时降级为 mock（开发环境）
- [ ] 已解锁/未解锁状态视觉区分正确

---

### Task 4.5：学习日历热力图真实数据接入（F-21 P0）

**文件**：`src/app/user/student/student-dashboard.component.ts`

**当前状态**：`initHeatmapConfig()` 生成随机 mock 数据（120 天）。

**修复方案**：

**Step 1**：新建 `LearningRecordService`

```typescript
// src/app/core/services/learning-record.service.ts（新建）
@Injectable({ providedIn: 'root' })
export class LearningRecordService {
  getDailyRecords(userId: number, year: number): Observable<DailyLearningRecord[]> {
    return this.http.get<ApiResponse<DailyLearningRecord[]>>(
      `/api/v1/users/${userId}/learning-records`,
      { params: { year: year.toString() } }
    ).pipe(
      map(res => res.success ? res.data : []),
      catchError(() => of([]))
    );
  }
}
```

**Step 2**：替换 `initHeatmapConfig` 为 API 调用

```typescript
private initHeatmapConfig(): void {
  const year = new Date().getFullYear();
  const userIdNum = this.getUserIdAsNumber();
  if (!userIdNum) return;

  this.learningRecordService.getDailyRecords(userIdNum, year).pipe(
    takeUntil(this.destroy$),
    catchError(() => of([]))
  ).subscribe(records => {
    this.heatmapConfig = {
      year,
      data: records,
      maxValue: 240,
      loading: false,
      emptyMessage: records.length === 0 ? '暂无学习记录' : undefined,
    };
  });
}
```

**Step 3**：`onHeatmapYearChange` 同样调用 API

```typescript
onHeatmapYearChange(newYear: number): void {
  const userIdNum = this.getUserIdAsNumber();
  if (!userIdNum) return;

  this.learningRecordService.getDailyRecords(userIdNum, newYear).pipe(
    takeUntil(this.destroy$)
  ).subscribe(records => {
    this.heatmapConfig = { year: newYear, data: records, maxValue: 240 };
  });
}
```

**验收**：
- [ ] 热力图显示用户真实学习日历数据
- [ ] 切换年份（2024 ↔ 2025 ↔ 2026）正确加载对应年份数据
- [ ] 无数据年份显示"暂无学习记录"空状态
- [ ] API 失败时降级为 mock（开发环境）

---

### Task 4.6：统一数据加载编排

**文件**：`src/app/user/student/student-dashboard.component.ts`

**问题**：当前 `triggerDataLoad` 仅加载 `progress / sources / courses` 三项；Sprint 4 扩展后需加载 6+ 项。

**修复方案**：

**Step 1**：使用 enum 统一管理加载状态

```typescript
enum LoadingKey {
  Progress = 'progress',
  Sources = 'sources',
  Courses = 'courses',
  Achievements = 'achievements',
  AiWork = 'aiWork',
  ArExperiment = 'arExperiment',
  Streak = 'streak',
  Heatmap = 'heatmap',
}

loadingState: Record<LoadingKey, boolean> = {
  progress: false, sources: false, courses: false,
  achievements: false, aiWork: false, arExperiment: false,
  streak: false, heatmap: false,
};
```

**Step 2**：并行 forkJoin 加载 6 项（关键路径）

```typescript
forkJoin({
  progress: this.loadProgressStats(userId),
  sources: this.loadLearningSources(userId),
  courses: this.loadUnifiedCourses(userId),
  achievements: this.achievementService.getUserAchievements(userId).pipe(
    catchError(() => of(getMockAchievementBadges())),
    tap(badges => { this.achievementBadges = badges; this.cdr.markForCheck(); })
  ),
  aiWork: this.aiEduService.getRecentAiWork(userId).pipe(
    catchError(() => of(null)),
    tap(work => { if (work) this.recentAiWork = work; this.cdr.markForCheck(); })
  ),
  streak: this.achievementService.getLearningStreak(userId).pipe(
    catchError(() => of({ days: 0, unlockedCount: 0, total: 12 })),
    tap(s => { this.learningStreak = s; this.cdr.markForCheck(); })
  ),
})
```

**Step 3**：失败容忍 - 任一失败不影响其他项加载

```typescript
.pipe(
  takeUntil(this.destroy$),
  catchError(err => {
    console.error('[Dashboard] 部分加载失败:', err);
    return of(null);
  })
)
.subscribe(result => {
  if (result) {
    // 逐项赋值（已通过 tap 处理）
    this.progressStats = result.progress ?? this.progressStats;
    this.learningSources = result.sources?.items ?? this.learningSources;
    this.connectWebSocket(userId);
  }
});
```

**验收**：
- [ ] 6 项并行加载，单项失败不影响其他项
- [ ] 总加载时间 ≤ 3 秒（API 健康情况下）
- [ ] 加载失败时显示骨架屏或保留旧数据，不出现白屏

---

### 4.2 Sprint 5：课件库独立 + AI 教师真实接入（1.5 周）

| Task | 功能点 | 严重度 | 文件位置 | 工作量 |
|------|--------|--------|----------|--------|
| Task 5.1 | 新建 `/user/materials` 路由 | P1 | user-routing.module.ts | 0.75 人天 |
| Task 5.2 | 课件库独立页面（CRUD） | P1 | materials-library.component.ts | 4 人天 |
| Task 5.3 | 首页 widget 跳转独立页面 | P1 | student-dashboard.component.html | 0.75 人天 |
| Task 5.4 | AI 教师面板真实接入 LLM | P1 | ai-teacher-chat.service.ts | 4.5 人天 |
| **Sprint 5 合计** | | | | **10 人天** |

---

### Task 5.1：新建 `/user/materials` 路由

**文件**：
- `src/app/user/user-routing.module.ts`（新增路由）
- `src/app/user/services/user-center.service.ts`（新增菜单项）

**修复方案**：

**Step 1**：在 `user-routing.module.ts` 中添加 children 路由

```typescript
{
  path: 'materials',
  loadComponent: () =>
    import('./components/materials-library/materials-library.component').then(
      (m) => m.MaterialsLibraryComponent
    ),
}
```

**Step 2**：在 `user-center.service.ts` 中添加用户菜单项

```typescript
{
  route: '/user/materials',
  label: '课件库',
  icon: 'folder',
  // ...
}
```

**Step 3**：在 dashboard widget 中跳转路径修正

```html
<!-- src/app/user/student/student-dashboard.component.html -->
<button mat-button (click)="navigateTo('/user/materials')">
  查看全部
  <mat-icon iconPositionEnd>arrow_forward</mat-icon>
</button>
```

**验收**：
- [ ] 路由 `/user/materials` 可访问，无白屏
- [ ] 用户菜单"课件库"项点击正确跳转
- [ ] dashboard 课件库 widget"查看全部"按钮跳转正确
- [ ] 路由懒加载生效（首次访问才下载 chunk）

---

### Task 5.2：课件库独立页面（增删改查）

**文件**：新建 `src/app/user/components/materials-library/materials-library.component.ts`

**实现内容**（完整页面，非 widget 嵌入版）：

```typescript
@Component({
  selector: 'app-materials-library',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatPaginatorModule, /* ... */],
  template: `
    <div class="materials-library">
      <header class="page-header">
        <h1>课件库</h1>
        <div class="header-actions">
          <mat-form-field>
            <input matInput placeholder="搜索课件..." [(ngModel)]="searchTerm">
          </mat-form-field>
          <button mat-raised-button color="primary" (click)="openUploadDialog()">
            <mat-icon>upload</mat-icon>
            上传课件
          </button>
        </div>
      </header>

      <mat-tab-group>
        <mat-tab label="全部 ({{ totalCount }})">
          <ng-container *ngTemplateOutlet="materialListTpl"></ng-container>
        </mat-tab>
        <mat-tab label="PDF ({{ pdfCount }})">
          <ng-container *ngTemplateOutlet="materialListTpl"></ng-container>
        </mat-tab>
        <mat-tab label="视频 ({{ videoCount }})">
          <ng-container *ngTemplateOutlet="materialListTpl"></ng-container>
        </mat-tab>
        <mat-tab label="文档 ({{ docCount }})">
          <ng-container *ngTemplateOutlet="materialListTpl"></ng-container>
        </mat-tab>
        <mat-tab label="幻灯片 ({{ slidesCount }})">
          <ng-container *ngTemplateOutlet="materialListTpl"></ng-container>
        </mat-tab>
      </mat-tab-group>

      <ng-template #materialListTpl>
        <mat-table [dataSource]="materials">
          <!-- 列定义 -->
        </mat-table>
        <mat-paginator [length]="totalCount" [pageSize]="20"></mat-paginator>
      </ng-template>
    </div>
  `,
})
export class MaterialsLibraryComponent implements OnInit {
  materials: MaterialItem[] = [];
  searchTerm = '';
  // CRUD 操作
}
```

**功能清单**：
- [ ] 列表展示（分页 20 条/页）
- [ ] 按类型筛选（全部/PDF/视频/文档/幻灯片）
- [ ] 关键字搜索（标题、课程）
- [ ] 上传课件（拖拽上传 + 进度条）
- [ ] 下载课件（按权限）
- [ ] 删除课件（确认对话框）
- [ ] 批量操作（多选 + 批量下载/删除）

**验收**：
- [ ] 列表、筛选、搜索、上传、下载、删除全功能可用
- [ ] 上传 PDF/视频/文档/幻灯片 4 种类型均成功
- [ ] 上传 100MB 视频显示进度条
- [ ] 删除二次确认对话框
- [ ] 空状态、加载状态、错误状态三态完整

---

### Task 5.3：从首页 widget 跳转独立页面（与 Task 5.1 协同）

**文件**：`src/app/user/student/student-dashboard.component.html`（课件库 widget 第 442-449 行）

**修复方案**：将 widget 内的"查看全部"按钮改为跳转 `/user/materials`（Task 5.1 已实现）

**验收**：同 Task 5.1 验收标准

---

### Task 5.4：AI 教师面板真实接入（F-24 P1）

**文件**：
- `src/app/user/components/user-page-layout/user-page-layout.component.ts`（第 117-136 行 `sendAIMessage`）
- 新建 `src/app/core/services/ai-teacher-chat.service.ts`

**当前状态**：`sendAIMessage()` 用 setTimeout 1 秒后返回 mock 字符串 `"好的，你说的是："${userMessage}"\n\n让我帮你解答..."`。

**修复方案**：

**Step 1**：新建 `AiTeacherChatService`

```typescript
@Injectable({ providedIn: 'root' })
export class AiTeacherChatService {
  constructor(private http: HttpClient, private auth: AuthService) {}
  
  sendMessage(message: string, context?: ChatContext): Observable<AiChatResponse> {
    return this.http.post<ApiResponse<AiChatResponse>>(
      '/api/v1/ai-teacher/chat',
      {
        message,
        context: {
          userId: this.auth.getCurrentUser()?.id,
          currentCourse: context?.courseTitle,
          recentAchievements: context?.recentBadges,
        },
      }
    ).pipe(
      map(res => res.success ? res.data : { reply: '抱歉，AI 教师暂时不可用，请稍后重试。' }),
      catchError(() => of({ reply: '网络错误，请检查连接后重试。' }))
    );
  }
  
  // 流式响应（可选，使用 SSE 或 WebSocket）
  sendMessageStream(message: string): Observable<string> {
    return new Observable(observer => {
      const eventSource = new EventSource(`/api/v1/ai-teacher/chat/stream?msg=${encodeURIComponent(message)}`);
      eventSource.onmessage = (event) => observer.next(event.data);
      eventSource.onerror = () => { observer.complete(); eventSource.close(); };
      return () => eventSource.close();
    });
  }
}
```

**Step 2**：改造 `sendAIMessage`

```typescript
sendAIMessage(): void {
  if (!this.aiMessage.trim()) return;
  
  const userMessage = this.aiMessage;
  this.aiMessages.push({ role: 'user', content: userMessage });
  this.aiMessage = '';
  
  // 显示加载状态
  this.aiMessages.push({ role: 'ai', content: '', loading: true });
  
  this.aiTeacherService.sendMessage(userMessage).pipe(
    takeUntil(this.destroy$)
  ).subscribe(response => {
    // 移除加载占位，添加真实回复
    const loadingIndex = this.aiMessages.findIndex(m => m.loading);
    if (loadingIndex >= 0) {
      this.aiMessages[loadingIndex] = { role: 'ai', content: response.reply };
    } else {
      this.aiMessages.push({ role: 'ai', content: response.reply });
    }
    this.cdr.markForCheck();
  });
}
```

**Step 3**：UI 增强

- 添加打字指示器（三个跳动圆点）
- 添加消息时间戳
- 添加 Markdown 渲染（代码块高亮）
- 添加快捷提问按钮（基于当前课程上下文）

**验收**：
- [ ] 发送消息后 3 秒内收到真实 AI 回复
- [ ] 回复支持 Markdown 格式（代码块、列表、链接）
- [ ] API 失败时显示友好降级文案
- [ ] 流式响应（SSE）打字效果正常
- [ ] 长消息自动滚动到底部

---

### 4.3 Sprint 6：性能优化 + 跨模块联动（1 周）

| Task | 功能点 | 严重度 | 文件位置 | 工作量 |
|------|--------|--------|----------|--------|
| Task 6.1 | Heatmap lazy load | P2 | student-dashboard.component.ts | 1.25 人天 |
| Task 6.2 | 推荐课程算法接入 | P2 | unified-course.service.ts | 1.75 人天 |
| Task 6.3 | dashboard 跳学习画像联动 | P2 | student-dashboard.component.html | 0.5 人天 |
| Task 6.4 | dashboard 跳学习报告联动 | P2 | student-dashboard.component.html | 0.5 人天 |
| Task 6.5 | 跨模块跳转路由审计 | P2 | 全部 widget | 0.75 人天 |
| **Sprint 6 合计** | | | | **4.75 人天** |

---

### Task 6.1：Heatmap lazy load（F-23 P2）

**文件**：
- `src/app/user/student/student-dashboard.component.ts`（移除 `LearningCalendarHeatmapComponent` 静态 import）
- `src/app/shared/components/learning-calendar-heatmap/`（新增独立路由）

**问题**：`LearningCalendarHeatmapComponent` 同步 import，ECharts 依赖（~250KB gzipped）会进入 dashboard 主 chunk。

**修复方案**：

**Step 1**：dashboard 中改为动态 import + 自定义占位组件

```typescript
// student-dashboard.component.ts
@Component({
  selector: 'app-student-dashboard',
  imports: [
    // 移除 LearningCalendarHeatmapComponent 静态导入
    // ...
  ],
  template: `
    <!-- 替换为懒加载占位 -->
    <ng-container *ngIf="heatmapVisible">
      <ng-container *ngComponentOutlet="heatmapCmp"></ng-container>
    </ng-container>
  `,
})
export class StudentDashboardComponent {
  heatmapVisible = false;
  heatmapCmp: Type<unknown> | null = null;
  
  async loadHeatmapLazy() {
    if (this.heatmapCmp) return;
    const m = await import('../../shared/components/learning-calendar-heatmap/learning-calendar-heatmap.component');
    this.heatmapCmp = m.LearningCalendarHeatmapComponent;
    this.heatmapVisible = true;
    this.cdr.markForCheck();
  }
}
```

**Step 2**：widget 可见时加载（IntersectionObserver）

```typescript
ngAfterViewInit() {
  const heatmapSection = document.querySelector('.section-heatmap');
  if (!heatmapSection) return;
  
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      this.loadHeatmapLazy();
      observer.disconnect();
    }
  }, { rootMargin: '200px' });
  
  observer.observe(heatmapSection);
}
```

**Step 3**：保留 fallback（不依赖 IntersectionObserver 时立即加载）

**验收**：
- [ ] dashboard 主 bundle 体积减少 ≥ 200KB
- [ ] 滚动到热力图位置时延迟加载（首次滚动到位 200px 内触发）
- [ ] 加载完成后无缝显示，无闪烁
- [ ] 重复进入页面不会重复加载（已加载组件复用）

---

### Task 6.2：推荐课程算法接入（F-25 P2）

**文件**：`src/app/core/services/unified-course.service.ts`（已存在 `getRecommendedCourses`）

**当前状态**：`getRecommendedCourses(userId, 8)` 返回通用推荐课程（无个性化）。

**修复方案**：

**Step 1**：后端 API 扩展（已有则跳过）

```
GET /api/v1/courses/recommendations?user_id={id}&limit={n}
Response:
{
  "success": true,
  "data": [
    {
      "courseId": 1,
      "title": "ROS 机器人操作系统",
      "matchScore": 0.92,
      "reason": "基于你最近学习「机器人基础入门」推荐",
      "difficulty": "advanced",
      "tags": ["ROS", "机器人"],
    },
    ...
  ]
}
```

**Step 2**：前端展示"推荐理由" chip

```html
<mat-card *ngFor="let course of recommendedCourses" class="course-card recommended-course-card">
  <div class="course-cover recommended-cover">
    <mat-icon>auto_awesome</mat-icon>
  </div>
  <mat-card-header>
    <mat-card-title>{{ course.title }}</mat-card-title>
    <mat-card-subtitle>
      <span class="course-teacher">{{ course.teacher }}</span>
      <mat-chip class="match-score-chip" *ngIf="course.matchScore">
        匹配度 {{ (course.matchScore * 100).toFixed(0) }}%
      </mat-chip>
    </mat-card-subtitle>
  </mat-card-header>
  <mat-card-content>
    <p class="recommend-reason" *ngIf="course.reason">
      <mat-icon>auto_awesome</mat-icon>
      {{ course.reason }}
    </p>
    <p class="course-description">{{ course.description }}</p>
  </mat-card-content>
  <mat-card-actions>
    <button mat-raised-button color="primary" (click)="onRecommendedCourseClick(course)">
      <mat-icon>play_arrow</mat-icon>
      开始学习
    </button>
  </mat-card-actions>
</mat-card>
```

**Step 3**：添加 A/B 测试框架（可选）

- 新建 `experiments.service.ts`
- 注册 experiment `recommendation_v2_2026q3`
- 50% 用户使用新算法，50% 保留旧算法

**验收**：
- [ ] 推荐课程显示"匹配度 X%" + 推荐理由文案
- [ ] 推荐理由文案贴合用户最近学习内容
- [ ] 跳转按钮（Task 4.1 修复后）正常工作
- [ ] A/B 测试开关可配置

---

### Task 6.3：dashboard 跳学习画像联动（F-26 P2）

**文件**：`src/app/user/student/student-dashboard.component.html`

**实现内容**：在统计卡片区块或欢迎区添加"查看学习画像"按钮

```html
<!-- 统计卡片区块底部 -->
<div class="section-footer">
  <button mat-stroked-button (click)="navigateTo('/user/learning-profile')">
    <mat-icon>person_search</mat-icon>
    查看完整学习画像
  </button>
</div>
```

**验收**：
- [ ] 点击按钮跳转到 `/user/learning-profile`
- [ ] 学习画像页正确接收并显示该用户的画像数据
- [ ] 跳转后 Navbar 高亮切换到对应入口（如果有）

---

### Task 6.4：dashboard 跳学习报告联动（F-27 P2）

**文件**：`src/app/user/student/student-dashboard.component.html`

**实现内容**：在成就墙区块或统计区块添加"生成本周报告"按钮

```html
<!-- 成就墙区块底部 -->
<div class="section-footer">
  <button mat-stroked-button (click)="navigateTo('/user/reports')">
    <mat-icon>assessment</mat-icon>
    查看学习报告
  </button>
</div>
```

**验收**：同 Task 6.3

---

### Task 6.5：跨模块跳转路由审计

**文件**：所有 dashboard widget 的"查看全部"按钮

**审计清单**：

| Widget | 当前跳转目标 | 应跳转目标 | 修复 | 状态 |
|--------|-------------|-----------|------|------|
| 统计卡片 | （无） | `/user/reports` | Sprint 6 新增 | ⏳ |
| 正在学习 | `/user/courses` | `/user/courses` | ✅ 正确 | ✅ |
| 成就墙 | `/user/achievements` | `/user/achievements` | ✅ 正确 | ✅ |
| 学习来源 | （无） | `/user/learning-profile` | Sprint 6 新增 | ⏳ |
| AI 推荐 | （无，widget 嵌入） | `/ai-edu/coding` | Sprint 4 已修复 | ✅ |
| 推荐课程 | （死链） | `/user/courses` + queryParams | Sprint 4 修复 | ✅ |
| 课件库 | （无） | `/user/materials` | Sprint 5 修复 | ✅ |
| 热力图 | （无，widget 嵌入） | `/user/reports` | Sprint 6 新增 | ⏳ |
| 学习状态 4 卡 | 各有目标 | 全部正确 | ✅ 正确 | ✅ |

**验收**：所有跳转路径审计完成，无死链

---

## 五、资源估算

### 5.1 各 Sprint 工作量汇总

| 角色 | Sprint 4 | Sprint 5 | Sprint 6 | 总计 |
|------|----------|----------|----------|------|
| **前端开发** | 4.5 人天 | 5.5 人天 | 3 人天 | **13 人天** |
| **后端支持** | 1 人天 | 3 人天 | 0.5 人天 | **4.5 人天** |
| **测试** | 1.5 人天 | 1.5 人天 | 1.25 人天 | **4.25 人天** |
| **总计** | **7 人天** | **10 人天** | **4.75 人天** | **21.75 人天** |

> 约 **4.35 人周**（按 5 人天/周计算）

### 5.2 资源分布图

```
Sprint 4 资源分布:
┌──────────────────────────────────────┐
│  前端开发  ████████████████████ 64%  │
│  后端支持  ██████░░░░░░░░░░░░░ 14%  │
│  测试      ████████████░░░░░░░ 22%  │
└──────────────────────────────────────┘

Sprint 5 资源分布:
┌──────────────────────────────────────┐
│  前端开发  ████████████████░░░░ 55%  │
│  后端支持  ████████████░░░░░░░ 30%  │
│  测试      ████████████░░░░░░░ 15%  │
└──────────────────────────────────────┘

Sprint 6 资源分布:
┌──────────────────────────────────────┐
│  前端开发  ████████████████████ 63%  │
│  后端支持  ████░░░░░░░░░░░░░░░ 11%  │
│  测试      ████████████████░░░░ 26%  │
└──────────────────────────────────────┘
```

---

## 六、里程碑验收标准

### 6.1 里程碑时间表

| 里程碑 | 日期目标 | Sprint | 验收条件 |
|--------|----------|--------|----------|
| **Sprint 4 启动** | 2026-06-11（周四） | Sprint 4 Day 1 | 任务分配完成，后端 API 接口文档就绪 |
| **Sprint 4 完成** | 2026-06-17（周三） | Sprint 4 Day 5 | 全部 6 个 Task 验收通过，8 个 widget 真实数据 |
| **Sprint 5 启动** | 2026-06-18（周四） | Sprint 5 Day 1 | 前序依赖完成，路由注册生效 |
| **Sprint 5 完成** | 2026-07-02（周四） | Sprint 5 Day 10 | 课件库 CRUD + AI 教师 LLM 接入验收通过 |
| **Sprint 6 启动** | 2026-07-03（周五） | Sprint 6 Day 1 | Sprint 5 验收通过 |
| **Sprint 6 完成** | 2026-07-09（周三） | Sprint 6 Day 5 | 性能优化 + 跨模块联动全部验收通过 |

### 6.2 Sprint 4 详细验收标准

| 验收项 | 验收条件 | 验证方法 | 通过标准 |
|--------|----------|----------|----------|
| **Task 4.1 死链修复** | 推荐课程"开始学习"按钮可跳转 | E2E 测试 | 点击跳转 `/user/courses`，URL 携带参数 |
| **Task 4.2 状态卡** | 4 个状态卡显示真实数据 | 账号登录验证 | 测试账号数据与页面一致 |
| **Task 4.3 统计卡片** | 4+1 模式正常工作 | 页面加载验证 | 来源分项可展开/收起 |
| **Task 4.4 成就墙** | 成就墙真实数据 | API 拦截验证 | 调试验证 API 调用 |
| **Task 4.5 热力图** | 热力图真实数据 + 年份切换 | 多年份切换验证 | 2024/2025/2026 数据加载正确 |
| **Task 4.6 数据编排** | 6 项并行加载，失败容忍 | 网络干扰测试 | 单项失败不影响其他项 |
| **性能指标** | Dashboard 首屏加载 | Lighthouse | ≤ 2.5s（不含 heatmap） |
| **端到端验证** | 测试账号登录完整流程 | E2E | `test_student/TestStudent123!` 全部 widget 真实数据 |

### 6.3 Sprint 5 详细验收标准

| 验收项 | 验收条件 | 验证方法 | 通过标准 |
|--------|----------|----------|----------|
| **Task 5.1 路由** | `/user/materials` 可访问 | 路由导航测试 | 无白屏，路由懒加载生效 |
| **Task 5.2 课件库** | CRUD + 筛选 + 搜索全功能 | 功能测试 | 上传/下载/删除/搜索均可用 |
| **Task 5.3 Widget 跳转** | 首页 widget 跳转正确 | 点击测试 | 跳转 `/user/materials` |
| **Task 5.4 AI 教师** | LLM 真实响应 | 对话测试 | 3 秒内收到 Markdown 回复 |
| **上传功能** | 100MB 视频进度条 | 文件上传测试 | 进度条正常显示 |
| **AI 响应时间** | 回复时间 | 响应计时 | ≤ 5s（含网络延迟） |

### 6.4 Sprint 6 详细验收标准

| 验收项 | 验收条件 | 验证方法 | 通过标准 |
|--------|----------|----------|----------|
| **Task 6.1 Lazy Load** | Bundle 体积减少 | Bundle 分析 | dashboard chunk 减少 ≥ 200KB |
| **Task 6.2 推荐算法** | 匹配度 + 推荐理由展示 | 页面验证 | 显示匹配度百分比 + 推荐理由 |
| **Task 6.3 学习画像联动** | 跳转学习画像 | 导航测试 | 跳转 `/user/learning-profile` |
| **Task 6.4 学习报告联动** | 跳转学习报告 | 导航测试 | 跳转 `/user/reports` |
| **Task 6.5 路由审计** | 无死链 | 全链路测试 | 全部 widget 跳转正常 |
| **Lighthouse Performance** | 性能评分 | Lighthouse | ≥ 90 |
| **Lighthouse Accessibility** | 无障碍评分 | Lighthouse | ≥ 95 |

---

## 七、风险与依赖

| 风险 | 影响 | 概率 | 缓解 |
|------|------|------|------|
| 后端 API 未提供 `/api/v1/users/{id}/achievements` | 成就墙接入失败 | 中 | 与后端协调；临时使用 mock；新建 migration |
| 后端 API 未提供 `/api/v1/users/{id}/learning-records` | 热力图数据为空 | 中 | 与后端协调；按日期聚合 `progress_logs` 表 |
| AI 教师后端 LLM 服务未就绪 | AI 聊天面板功能不可用 | 高 | 临时使用 mock + UI 优化；后端 Sprint 5 同步实现 |
| ECharts 依赖 lazy load 后兼容性 | 老浏览器不支持动态 import | 低 | 添加 fallback 同步加载（按需） |
| 推荐算法后端性能瓶颈 | dashboard 加载慢 | 低 | 前端缓存 5 分钟；后端异步返回 |
| 大屏（≥2000px）下热力图加载策略 | IntersectionObserver 失效 | 低 | 添加手动触发的"加载热力图"按钮 |
| **Sprint 4-6 周期跨越端午节假期** | 团队资源可用性降低 | 中 | 提前安排值班计划；关键任务前移 |
| **后端 API 文档缺失** | 前端开发等待 | 中 | Sprint 4 启动前完成 API 接口定义 |

---

## 八、关键决策记录

| 决策 | 选项 | 选定 | 理由 |
|------|------|------|------|
| Heatmap 加载策略 | A: 同步加载 / B: IntersectionObserver 懒加载 / C: 用户点击加载 | B | 平衡性能与体验，自动触发 |
| 推荐算法实施位置 | A: 前端规则 / B: 后端 ML / C: 后端规则引擎 | C | 后端已有规则引擎，前端无需重复实现 |
| 课件库独立页面 vs 增强 widget | A: 独立路由 / B: 增强 widget | A | widget 信息密度有限，独立页可承载 CRUD |
| AI 教师真实接入时机 | A: Sprint 4 / B: Sprint 5 / C: 后续 | B | 依赖后端 LLM 服务，建议后端同步开发 |
| dashboard bundle 优化优先级 | A: Heatmap / B: 推荐课程 / C: 课件库 | A | ECharts 最大（250KB），收益最高 |
| 推荐课程跳转行为 | A: 跳课程详情 / B: 跳课程列表 + query | B | 复用现有课程列表，自动搜索定位 |

---

## 九、验收清单（按 Sprint 划分）

### Sprint 4 验收
- [ ] Task 4.1：推荐课程"开始学习"按钮跳转正常
- [ ] Task 4.2：状态卡 4 卡真实数据接入，空态文案正确
- [ ] Task 4.3：统计卡片 4 + 1 模式正确，来源分项可展开
- [ ] Task 4.4：成就墙真实数据接入
- [ ] Task 4.5：热力图真实数据接入，年份切换正常
- [ ] Task 4.6：6 项并行加载，单项失败不影响整体
- [ ] 端到端测试：`test_student/TestStudent123!` 登录后所有 widget 显示真实数据
- [ ] 性能：dashboard 首屏加载 ≤ 2.5s（不包含 heatmap 懒加载）

### Sprint 5 验收
- [ ] Task 5.1：路由 `/user/materials` 可访问
- [ ] Task 5.2：课件库独立页面全功能（CRUD + 筛选 + 搜索）
- [ ] Task 5.3：首页 widget 跳转正确
- [ ] Task 5.4：AI 教师真实接入（LLM 调用 + Markdown + 流式打字）
- [ ] 上传 100MB 视频显示进度
- [ ] AI 聊天回复时间 ≤ 5s

### Sprint 6 验收
- [ ] Task 6.1：Heatmap lazy load 生效，bundle 体积减少 ≥ 200KB
- [ ] Task 6.2：推荐课程匹配度 + 推荐理由展示
- [ ] Task 6.3：dashboard 跳学习画像联动
- [ ] Task 6.4：dashboard 跳学习报告联动
- [ ] Task 6.5：所有跳转路径审计，无死链
- [ ] Lighthouse Performance ≥ 90
- [ ] Lighthouse Accessibility ≥ 95

---

## 十、文档关联

- **前置文档**：`docs/MatuX_桌面端迭代开发计划_Sprint0-3.md`（已完成）
- **本计划依据**：2026-06-10 首页修复（PR 标题：`fix(student-dashboard): restore 8 widgets per 全模块保留决策`）
- **项目路线图**：docs/07-产品文档/PROJECT_ROADMAP.md（M3.5 学生端功能完善子任务）
- **PRD 规范**：docs/归档/MatuX_Desktop_PRD.md（F-21 到 F-28 功能定义）
- **代码审计**：docs/归档/MatuX_桌面端学习端代码结构审查与完善报告（优先级任务清单）
- **后续文档**：Sprint 7+ 待规划（聚焦：管理端 v2 UI、跨平台一致性、AI 教师深度集成）

---

> **版本控制**：v1.1 / 2026-06-10 / PM + Senior Engineer 联合编制  
> **变更日志**：
> - v1.1 (2026-06-10)：新增审计结论摘要、资源估算表格、里程碑验收标准表格，与 Sprint 0-3 格式对齐  
> - v1.0 (2026-06-10)：初始版本，基于首页修复反馈 + 后续建议 3 项