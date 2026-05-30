# AI-Edu-for-Kids 前端组件使用指南

**日期**: 2026-03-03  
**版本**: v1.0  
**状态**: ✅ 完成

---

## 📦 组件清单

### 已创建组件

| 组件 | 选择器 | 文件路径 | 行数 | 功能 |
|------|--------|----------|------|------|
| **AIEduCourseListComponent** | `app-ai-edu-course-list` | `components/ai-edu-course-list/` | 253 行 | 课程列表展示 |
| **AIEduStatisticsComponent** | `app-ai-edu-statistics` | `components/ai-edu-statistics/` | 162 行 | 学习统计展示 |
| **AIEduModule** | - | `components/ai-edu-module.ts` | 32 行 | 功能模块整合 |

### 服务

| 服务 | 注入范围 | 文件路径 | 行数 | 功能 |
|------|----------|----------|------|------|
| **AIEduService** | root | `core/services/ai-edu.service.ts` | 253 行 | API 数据访问 |

### 模型

| 模型 | 文件路径 | 行数 | 类型 |
|------|----------|------|------|
| **ai-edu.models.ts** | `models/ai-edu.models.ts` | 149 行 | TypeScript 接口 |

---

## 🚀 快速开始

### 1. 导入模块

在 `app.module.ts` 中导入:

```typescript
import { AIEduModule } from './components/ai-edu-module';
import { AIEduService } from './core/services/ai-edu.service';

@NgModule({
  declarations: [...],
  imports: [
    BrowserModule,
    AIEduModule,  // 添加这里
    ...
  ],
  providers: [AIEduService],
  bootstrap: [AppComponent]
})
export class AppModule { }
```

### 2. 配置路由

在 `app-routing.module.ts` 中添加路由:

```typescript
const routes: Routes = [
  {
    path: 'courses',
    component: AIEduCourseListComponent
  },
  {
    path: 'statistics',
    component: AIEduStatisticsComponent
  }
];
```

### 3. 使用组件

#### 方式一：独立使用

```html
<!-- 课程列表 -->
<app-ai-edu-course-list></app-ai-edu-course-list>

<!-- 学习统计 -->
<app-ai-edu-statistics></app-ai-edu-statistics>
```

#### 方式二：组合使用

```html
<div class="ai-edu-dashboard">
  <!-- 顶部统计卡片 -->
  <app-ai-edu-statistics [orgId]="1" [userId]="currentUserId"></app-ai-edu-statistics>
  
  <!-- 课程列表 -->
  <app-ai-edu-course-list [orgId]="1"></app-ai-edu-course-list>
</div>
```

---

## 📖 API 文档

### AIEduCourseListComponent

**选择器**: `app-ai-edu-course-list`

**输入属性**:
```typescript
@Input() orgId: number = 1;  // 组织 ID
```

**功能**:
- 显示所有课程模块
- 点击模块查看课时列表
- 显示每个课时的进度状态
- 支持响应式布局

**使用示例**:
```html
<app-ai-edu-course-list [orgId]="1"></app-ai-edu-course-list>
```

---

### AIEduStatisticsComponent

**选择器**: `app-ai-edu-statistics`

**输入属性**:
```typescript
@Input() orgId: number = 1;   // 组织 ID
@Input() userId: number = 1;  // 用户 ID
```

**功能**:
- 8 个统计数据卡片
- 实时从后端加载数据
- 自动刷新
- 渐变色彩设计

**统计指标**:
1. 📚 总课程数
2. ✅ 已完成
3. ⏳ 进行中
4. 🎯 完成率 (%)
5. ⏱️ 学习时长 (小时)
6. 🏆 总积分
7. 📝 平均测验分
8. 💻 平均代码分

**使用示例**:
```html
<app-ai-edu-statistics [orgId]="1" [userId]="123"></app-ai-edu-statistics>
```

---

## 🔧 AIEduService 方法

### 课程相关

```typescript
// 获取模块列表
getModules(orgId: number): Observable<AIEduModule[]>

// 获取模块详情
getModuleById(orgId: number, moduleId: number): Observable<AIEduModule>

// 获取课时列表
getLessonsByModule(orgId: number, moduleId: number): Observable<AIEduLesson[]>

// 获取课时详情
getLessonById(orgId: number, lessonId: number): Observable<AIEduLesson>
```

### 进度相关

```typescript
// 更新学习进度
updateProgress(
  orgId: number,
  request: ProgressUpdateRequest
): Observable<{ progress_id: number; status: string }>

// 获取用户进度
getUserProgress(
  orgId: number,
  userId: number,
  lessonId?: number
): Observable<LearningProgress[]>

// 完成课程并获得积分
completeLesson(
  orgId: number,
  request: LessonCompletionRequest
): Observable<{ points_earned: number }>

// 获取统计数据
getStatistics(
  orgId: number,
  userId: number
): Observable<LearningStatistics>
```

---

## 📊 数据模型

### AIEduModule

```typescript
interface AIEduModule {
  id: number;
  module_code: string;
  name: string;
  description: string;
  category: string;
  grade_ranges: GradeRange[];
  expected_lessons: number;
  expected_duration_minutes: number;
  is_active: boolean;
  display_order: number;
}
```

### AIEduLesson

```typescript
interface AIEduLesson {
  id: number;
  lesson_code: string;
  title: string;
  subtitle: string;
  content_type: string;
  content_url: string;
  resources: Resource[];
  learning_objectives: string[];
  knowledge_points: string[];
  estimated_duration_minutes: number;
  has_quiz: boolean;
  quiz_passing_score: number;
  has_practice: boolean;
  practice_type: string;
  base_points: number;
  is_active: boolean;
  display_order: number;
}
```

### LearningProgress

```typescript
interface LearningProgress {
  progress_id: number;
  lesson_id: number;
  progress_percentage: number;
  status: 'not_started' | 'in_progress' | 'completed';
  time_spent_seconds: number;
  quiz_score?: number;
  code_quality_score?: number;
  last_accessed_time: string;
}
```

### LearningStatistics

```typescript
interface LearningStatistics {
  total_courses: number;
  completed_courses: number;
  in_progress_courses: number;
  not_started_courses: number;
  total_time_hours: number;
  average_quiz_score: number;
  average_code_score: number;
  total_points: number;
  completion_rate: number;
}
```

---

## 🎨 样式定制

### 修改主题色

在组件 SCSS 文件中修改 CSS 变量:

```scss
:host {
  --primary-color: #667eea;
  --secondary-color: #764ba2;
  --accent-color: #f093fb;
}
```

### 响应式断点

```scss
// 移动端
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

// 平板
@media (min-width: 769px) and (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

// 桌面端
@media (min-width: 1025px) {
  .stats-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

---

## 🔍 调试技巧

### 1. 启用详细日志

在 `AIEduService` 中添加日志:

```typescript
getModules(orgId: number): Observable<AIEduModule[]> {
  const url = `${this.API_BASE}/${orgId}/ai-edu/modules`;
  console.log('Fetching modules from:', url);
  
  return this.http.get<ApiResponse<AIEduModule[]>>(url).pipe(
    tap(response => console.log('Modules response:', response)),
    map(response => response.data),
    catchError(error => {
      console.error('Error fetching modules:', error);
      return of([]);
    })
  );
}
```

### 2. 检查 API 连接

在浏览器控制台测试:

```typescript
// 打开开发者工具 (F12)
// 在 Console 中执行:
fetch('/api/v1/org/1/ai-edu/modules')
  .then(res => res.json())
  .then(data => console.log('API Response:', data));
```

### 3. 模拟数据

开发时可以使用模拟数据:

```typescript
// 临时模拟数据
const mockModules: AIEduModule[] = [
  {
    id: 1,
    module_code: 'basic_concepts_01',
    name: 'AI 基本概念入门',
    description: '人工智能基础概念介绍',
    category: 'basic_concepts',
    grade_ranges: [{ min: 1, max: 6 }],
    expected_lessons: 3,
    expected_duration_minutes: 60,
    is_active: true,
    display_order: 1
  }
];

// 返回模拟数据
return of(mockModules);
```

---

## 🐛 常见问题

### Q1: 组件不显示数据？

**A**: 检查以下几点:
1. 后端服务是否启动 (`http://localhost:8000`)
2. API 地址是否正确
3. 浏览器控制台是否有错误信息
4. 网络请求是否成功 (Network 标签)

### Q2: 样式显示异常？

**A**: 
1. 确认 SCSS 文件已正确编译
2. 检查 CSS 选择器是否匹配
3. 查看是否有全局样式冲突

### Q3: 数据类型错误？

**A**:
1. 检查后端返回的数据格式
2. 确认 TypeScript 接口定义
3. 使用可选链操作符 (`?.`) 处理可能为空的数据

---

## 📈 性能优化建议

### 1. 懒加载模块

```typescript
const routes: Routes = [
  {
    path: 'courses',
    loadChildren: () => import('./components/ai-edu-module').then(m => m.AIEduModule)
  }
];
```

### 2. 缓存数据

```typescript
private modulesCache: AIEduModule[] | null = null;

getModules(orgId: number): Observable<AIEduModule[]> {
  if (this.modulesCache) {
    return of(this.modulesCache);
  }
  
  return this.http.get<ApiResponse<AIEduModule[]>>(url).pipe(
    map(response => {
      this.modulesCache = response.data;
      return response.data;
    })
  );
}
```

### 3. 防抖处理

```typescript
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

searchControl.valueChanges.pipe(
  debounceTime(300),
  distinctUntilChanged()
).subscribe(value => {
  this.search(value);
});
```

---

## 🎯 最佳实践

### 1. 错误处理

```typescript
this.aiEduService.getModules(this.orgId).subscribe({
  next: (modules) => {
    this.modules = modules;
  },
  error: (error) => {
    console.error('加载失败:', error);
    this.errorMessage = '加载课程失败，请稍后重试';
  },
  complete: () => {
    console.log('加载完成');
  }
});
```

### 2. 内存管理

```typescript
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

private destroy$ = new Subject<void>();

ngOnInit(): void {
  this.aiEduService.getModules(this.orgId)
    .pipe(takeUntil(this.destroy$))
    .subscribe(modules => this.modules = modules);
}

ngOnDestroy(): void {
  this.destroy$.next();
  this.destroy$.complete();
}
```

### 3. TrackBy 优化

```html
<div *ngFor="let module of modules; trackBy: trackByModuleId">
  {{ module.name }}
</div>
```

```typescript
trackByModuleId(index: number, module: AIEduModule): number {
  return module.id;
}
```

---

## 📞 技术支持

### API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 后端服务
- 健康检查：http://localhost:8000/health
- 基础地址：http://localhost:8000

### 数据库
- 文件位置：`G:\iMato\data\ai_edu_standalone.db`
- 查看工具：SQLite Browser

---

## 🚀 下一步扩展

### 计划中的组件

1. **课程播放器组件** - 视频播放 + 代码编辑器
2. **在线测验组件** - 交互式测验功能
3. **成就徽章组件** - 展示用户获得的徽章
4. **学习路径组件** - 可视化学习进度路径

### 计划中的功能

1. **离线模式** - Service Worker 缓存
2. **PWA 支持** - 添加到主屏幕
3. **深色模式** - 主题切换
4. **多语言** - i18n 国际化

---

**文档版本**: v1.0  
**最后更新**: 2026-03-03  
**维护者**: AI-Edu Team  

🎉 **祝使用愉快!**
