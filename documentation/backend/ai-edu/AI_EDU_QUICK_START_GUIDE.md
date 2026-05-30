# AI-Edu-for-Kids 功能扩展 - 快速使用指南

## 📋 新增功能概览

本次更新为 AI-Edu-for-Kids 平台添加了以下核心功能:

### ✅ P0 - 课程模块扩展
- **Module 02**: 数据感知与采集 (2 个课时)
- **Module 03**: 机器学习入门 (1 个课时)
- 数据库模块总数：**4 个**
- 课时总数：**9 个**

### ✅ P1 - 课程播放器
- 支持视频、代码、HTML 交互、文档多种资源类型
- 集成 Monaco Editor 代码编辑器
- 学习笔记功能
- 学习进度自动跟踪

### ✅ P2 - 在线测验系统
- 选择题、填空题、编程题多种题型
- 实时计时和进度管理
- 自动判分和积分奖励
- 答题卡导航

### ✅ P3 - 优化改进
- **数据缓存**: 双层缓存架构 (内存 + IndexedDB)
- **加载动画**: 4 种加载效果 (旋转器、脉冲、骨架屏、进度条)
- **错误处理**: 智能错误分类和友好的用户提示

---

## 🚀 快速开始

### 1. 查看数据库中的课程模块

```bash
cd g:\iMato
python -c "from pathlib import Path; from sqlalchemy import create_engine, text; db_path = Path('data/ai_edu_standalone.db'); engine = create_engine(f'sqlite:///{db_path}'); conn = engine.connect(); result = conn.execute(text('SELECT module_code, name FROM ai_edu_modules ORDER BY display_order')); print('\n'.join([f'{r.module_code}: {r.name}' for r in result.fetchall()]))"
```

**预期输出**:
```
demo_module_01: AI 基本概念入门
basic_concepts_01: AI 基本概念入门
data_perception_01: 数据感知与采集
ml_basics_01: 机器学习入门
```

### 2. 导入更多课程模块 (可选)

如果之前未执行导入，可以运行:

```bash
python scripts/import_new_ai_edu_modules.py
```

---

## 💻 前端组件使用示例

### 课程播放器组件

```typescript
// app.module.ts 或独立路由模块
import { AIEduCoursePlayerComponent } from './components/ai-edu-course-player/ai-edu-course-player.component';

@NgModule({
  declarations: [
    AIEduCoursePlayerComponent,
    // ... 其他组件
  ]
})
```

**路由配置**:

```typescript
// app-routing.module.ts
const routes: Routes = [
  {
    path: 'course/:moduleId/lesson/:lessonId',
    component: AIEduCoursePlayerComponent
  }
];
```

**使用示例**:

```html
<!-- 在模板中使用 -->
<app-ai-edu-course-player
  [moduleId]="1"
  [lessonId]="2">
</app-ai-edu-course-player>
```

### 在线测验组件

```typescript
import { AIEduQuizComponent } from './components/ai-edu-quiz/ai-edu-quiz.component';

// 路由配置
{
  path: 'quiz/:lessonId',
  component: AIEduQuizComponent
}
```

**使用示例**:

```html
<app-ai-edu-quiz
  [lessonId]="1"
  [userId]="currentUser.id">
</app-ai-edu-quiz>
```

### 加载动画组件

```typescript
import { AIEduLoadingComponent } from './components/ai-edu-loading/ai-edu-loading.component';
```

**使用场景 1**: 全屏加载遮罩

```html
<app-ai-edu-loading
  type="spinner"
  overlay="true"
  message="正在加载课程...">
</app-ai-edu-loading>
```

**使用场景 2**: 骨架屏占位

```html
<app-ai-edu-loading
  type="skeleton"
  [overlay]="false"
  [skeletonLines]="[1,2,3,4,5]">
</app-ai-edu-loading>
```

**使用场景 3**: 进度条

```html
<app-ai-edu-loading
  type="progress"
  [progress]="downloadProgress"
  message="下载资源中...">
</app-ai-edu-loading>
```

---

## 🔧 服务层 API

### 1. 学习服务 (AIEduLearningService)

```typescript
import { AIEduLearningService } from './services/ai-edu-learning.service';

constructor(private learningService: AIEduLearningService) {}

// 获取课程详情
this.learningService.getLesson(lessonId).subscribe(lesson => {
  console.log('课程数据:', lesson);
});

// 完成课程
this.learningService.completeLesson(userId, lessonId, score=100)
  .subscribe(() => {
    console.log('课程已完成!');
  });

// 获取学习进度
this.learningService.getUserProgress(userId, moduleId)
  .subscribe(progress => {
    console.log('学习进度:', progress);
  });
```

### 2. 缓存服务 (AIEduCacheService)

```typescript
import { AIEduCacheService } from './services/ai-edu-cache.service';

constructor(private cacheService: AIEduCacheService) {}

// HTTP GET 请求 (自动缓存)
this.cacheService.httpGet('/api/v1/org/1/ai-edu/lessons/1')
  .subscribe(lesson => {
    console.log('课程数据:', lesson);
  });

// 自定义缓存配置
const customConfig: CacheConfig = {
  ttl: 10 * 60 * 1000,     // 10 分钟
  maxSize: 50              // 最多 50 条
};

this.cacheService.set('user_progress_1', progressData, customConfig);

// 预加载数据
this.cacheService.preload(
  'all_modules',
  () => this.http.get('/api/v1/org/1/ai-edu/modules'),
  { ttl: 30 * 60 * 1000 }
).subscribe();

// 清除缓存
this.cacheService.clear('lesson_');  // 清除所有包含'lesson_'的缓存
```

### 3. 错误处理服务 (AIEduErrorHandlerService)

```typescript
import { AIEduErrorHandlerService, ErrorType } 
  from './services/ai-edu-error-handler.service';

constructor(private errorHandler: AIEduErrorHandlerService) {}

// 显示错误提示
try {
  this.http.get('/api/some-endpoint').subscribe();
} catch (error) {
  this.errorHandler.showToast(error, {
    duration: 5000,
    position: 'top'
  });
}

// 显示成功提示
this.errorHandler.showSuccess('保存成功!');

// 显示警告
this.errorHandler.showWarning('数据未保存，确定要离开吗？');

// 监听错误流
this.errorHandler.error$.subscribe(error => {
  console.log('收到错误通知:', error);
});
```

---

## 📊 后端 API 需求

以下是新增组件需要的 API 接口。如果后端尚未实现，需要创建这些端点:

### 课程相关 API

```python
# backend/routes/ai_edu_routes.py

@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: int):
    """获取课时详情 (包含资源列表)"""
    # TODO: 实现
    pass

@router.post("/execute-code")
async def execute_code(code: str, language: str):
    """运行代码并返回结果"""
    # TODO: 实现
    pass
```

### 测验相关 API

```python
@router.post("/quiz/start")
async def start_quiz(lesson_id: int, user_id: int):
    """开始测验，返回题目列表"""
    # TODO: 实现
    pass

@router.post("/quiz/submit")
async def submit_quiz(quiz_id: int, answers: list):
    """提交测验答案，返回成绩"""
    # TODO: 实现
    pass

@router.get("/quiz/{quiz_id}/review")
async def review_quiz(quiz_id: int):
    """查看测验答案解析"""
    # TODO: 实现
    pass
```

### 笔记相关 API

```python
@router.get("/notes/{user_id}/{lesson_id}")
async def get_note(user_id: int, lesson_id: int):
    """获取用户的学习笔记"""
    # TODO: 实现
    pass

@router.post("/notes/save")
async def save_note(user_id: int, lesson_id: int, content: str):
    """保存学习笔记"""
    # TODO: 实现
    pass
```

---

## 🧪 测试验证

### 单元测试示例

```typescript
// ai-edu-course-player.component.spec.ts
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { AIEduCoursePlayerComponent } from './ai-edu-course-player.component';

describe('AIEduCoursePlayerComponent', () => {
  let component: AIEduCoursePlayerComponent;
  let fixture: ComponentFixture<AIEduCoursePlayerComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [ AIEduCoursePlayerComponent ]
    })
    .compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AIEduCoursePlayerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('应该创建组件', () => {
    expect(component).toBeTruthy();
  });

  it('应该能加载课程数据', () => {
    component.lessonId = 1;
    component.loadLesson();
    // TODO: 添加更多断言
  });
});
```

### 集成测试

运行现有的集成测试页面:

```bash
cd tests/integration
python start_integration_test.py
```

这将在浏览器中打开交互式测试页面，可以手动测试所有 API 端点。

---

## 📝 最佳实践

### 1. 缓存使用策略

```typescript
// ✅ 好的做法：为频繁访问的数据设置较长缓存时间
this.cacheService.set('user_profile_' + userId, profile, {
  ttl: 30 * 60 * 1000,  // 30 分钟
  maxSize: 100
});

// ✅ 好的做法：为实时性要求高的数据设置短缓存
this.cacheService.set('quiz_status_' + quizId, status, {
  ttl: 1 * 60 * 1000,   // 1 分钟
});

// ❌ 不好的做法：为敏感数据设置过长缓存
this.cacheService.set('user_password', password, {
  ttl: 60 * 60 * 1000   // 不应该！
});
```

### 2. 错误处理策略

```typescript
// ✅ 好的做法：区分错误类型进行处理
try {
  this.http.get('/api/data').subscribe();
} catch (error) {
  if (error.type === ErrorType.AUTH) {
    // 认证错误 → 跳转登录
    this.router.navigate(['/login']);
  } else if (error.type === ErrorType.NOT_FOUND) {
    // 资源不存在 → 显示友好提示
    this.errorHandler.showToast('数据不存在', { duration: 3000 });
  } else {
    // 其他错误 → 显示通用提示
    this.errorHandler.showToast('操作失败，请稍后重试');
  }
}

// ✅ 好的做法：禁用特定操作的错误提示
this.errorHandler.disableGlobalError();
this.riskyOperation().finally(() => {
  this.errorHandler.enableGlobalError();
});
```

### 3. 加载状态管理

```typescript
// ✅ 好的做法：使用路由守卫显示加载动画
canActivate(): Observable<boolean> {
  this.loadingService.show('验证登录状态...');
  
  return this.authService.checkAuth().pipe(
    tap(() => this.loadingService.hide()),
    catchError(() => {
      this.loadingService.hide();
      return of(false);
    })
  );
}

// ✅ 好的做法：HTTP 拦截器统一管理
intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
  this.loadingService.show();
  
  return next.handle(req).pipe(
    finalize(() => this.loadingService.hide())
  );
}

// ❌ 不好的做法：每个组件重复编写加载逻辑
loading = true;
setTimeout(() => loading = false, 1000);  // 不推荐
```

---

## 🔍 故障排查

### 问题 1: 组件无法加载

**症状**: 页面显示空白或控制台报错

**解决方案**:
1. 检查组件是否在 NgModule 中声明
2. 检查路由配置是否正确
3. 检查输入属性 (@Input) 是否传递了正确的值

### 问题 2: 缓存不生效

**症状**: 每次请求都调用 API

**解决方案**:
1. 检查缓存键是否一致
2. 检查 TTL 设置是否过短
3. 确认 IndexedDB 是否可用 (检查浏览器控制台)

### 问题 3: 错误提示不显示

**症状**: 错误发生了但没有 Toast 提示

**解决方案**:
1. 检查是否调用了 `disableGlobalError()`
2. 检查错误对象格式是否符合 AppError 接口
3. 确认 CSS 样式已正确注入

---

## 📚 相关文档

- [功能扩展完成报告](./AI_EDU_FEATURE_EXPANSION_REPORT.md)
- [前后端联调测试报告](./AI_EDU_INTEGRATION_TEST_REPORT.md)
- [选项 C 完成报告](./AI_EDU_OPTION_C_COMPLETE_REPORT.md)
- [B1 任务完成报告](./AI_EDU_B1_TASK_COMPLETE_REPORT.md)

---

## 🆘 获取帮助

如遇到问题:

1. **查看文档**: 先阅读本文档和相关报告
2. **检查控制台**: 查看浏览器开发者工具的错误信息
3. **搜索代码**: 使用 IDE 的全局搜索功能查找示例用法
4. **联系团队**: 在 GitHub 提 Issue 或联系开发团队

---

**最后更新时间**: 2026-03-03  
**版本**: v2.0.0
