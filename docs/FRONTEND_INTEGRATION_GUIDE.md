# OpenMTSciEd API 前端集成指南

## 📋 集成步骤

### 1. 配置环境变量

编辑 `g:\iMato\src\environments\environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  wsUrl: 'ws://localhost:8000',
  openMtSciEdApiUrl: 'http://localhost:3000/api/v1',  // 新增
};
```

生产环境 (`environment.prod.ts`):
```typescript
export const environment = {
  production: true,
  apiUrl: 'https://your-backend.com',
  wsUrl: 'wss://your-backend.com',
  openMtSciEdApiUrl: 'https://your-openmtscied-api.com/api/v1',  // 生产API地址
};
```

---

### 2. 创建OpenMTSciEd服务

创建文件: `g:\iMato\src\app\services\openmt-scied.service.ts`

```typescript
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface Tutorial {
  id: string;
  title: string;
  description: string;
  grade_level: string;
  subject: string;
  duration_minutes: number;
  difficulty_level: string;
  created_at?: string;
}

export interface TutorialListResponse {
  items: Tutorial[];
  total: number;
  page: number;
  size: number;
  total_pages: number;
}

export interface Courseware {
  id: string;
  title: string;
  description: string;
  type: string;
  grade_level: string;
  subject: string;
  difficulty_level: string;
  file_url: string;
  thumbnail_url: string;
  duration_minutes: number;
  knowledge_points: Array<{id: string; name: string}>;
  created_at?: string;
}

export interface HardwareProject {
  id: string;
  title: string;
  description: string;
  difficulty_level: string;
  category: string;
  subject: string;
  estimated_time_hours: number;
  thumbnail_url: string;
  hardware_required: Array<{id: string; name: string; quantity: number}>;
  knowledge_points: Array<{id: string; name: string}>;
  created_at?: string;
}

export interface LearningPathNode {
  id: string;
  type: string;
  resource_id: string;
  title: string;
  prerequisites: string[];
  next_steps: string[];
  estimated_time_minutes: number;
  difficulty_level?: string;
}

export interface LearningPath {
  path_id: string;
  nodes: LearningPathNode[];
  estimated_duration_hours: number;
  difficulty_progression: string;
  message?: string;
}

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  subject: string;
  grade_level: string;
  difficulty_level: string;
  type: string;
  recommendation_reason: string;
  score: number;
}

@Injectable({
  providedIn: 'root'
})
export class OpenMtSciEdService {
  private baseUrl = environment.openMtSciEdApiUrl;

  constructor(private http: HttpClient) {}

  // ==================== 教程管理 ====================

  /**
   * 获取教程列表
   */
  getTutorials(
    page: number = 1,
    size: number = 20,
    subject?: string,
    gradeLevel?: string
  ): Observable<TutorialListResponse> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('size', size.toString());

    if (subject) {
      params = params.set('subject', subject);
    }
    if (gradeLevel) {
      params = params.set('grade_level', gradeLevel);
    }

    return this.http.get<TutorialListResponse>(`${this.baseUrl}/tutorials`, { params });
  }

  /**
   * 获取教程详情
   */
  getTutorialById(id: string): Observable<Tutorial> {
    return this.http.get<Tutorial>(`${this.baseUrl}/tutorials/${id}`);
  }

  /**
   * 创建教程
   */
  createTutorial(tutorial: Partial<Tutorial>): Observable<any> {
    return this.http.post(`${this.baseUrl}/tutorials`, tutorial);
  }

  /**
   * 更新教程
   */
  updateTutorial(id: string, tutorial: Partial<Tutorial>): Observable<any> {
    return this.http.put(`${this.baseUrl}/tutorials/${id}`, tutorial);
  }

  /**
   * 删除教程
   */
  deleteTutorial(id: string): Observable<any> {
    return this.http.delete(`${this.baseUrl}/tutorials/${id}`);
  }

  // ==================== 课件管理 ====================

  /**
   * 获取课件列表
   */
  getCoursewares(
    page: number = 1,
    size: number = 20,
    subject?: string,
    gradeLevel?: string,
    type?: string
  ): Observable<{items: Courseware[]; total: number; page: number; size: number; total_pages: number}> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('size', size.toString());

    if (subject) params = params.set('subject', subject);
    if (gradeLevel) params = params.set('grade_level', gradeLevel);
    if (type) params = params.set('type', type);

    return this.http.get<any>(`${this.baseUrl}/coursewares`, { params });
  }

  /**
   * 创建课件
   */
  createCourseware(courseware: Partial<Courseware>): Observable<any> {
    return this.http.post(`${this.baseUrl}/coursewares`, courseware);
  }

  // ==================== 知识图谱 - 学习路径 ====================

  /**
   * 生成学习路径
   */
  generateLearningPath(
    userId: number,
    currentGrade: string,
    subjects: string[],
    learningGoals?: string[]
  ): Observable<LearningPath> {
    const body = {
      user_id: userId,
      current_grade: currentGrade,
      subjects,
      learning_goals: learningGoals || []
    };

    return this.http.post<LearningPath>(`${this.baseUrl}/knowledge-graph/path`, body);
  }

  /**
   * 获取用户学习进度
   */
  getUserProgress(userId: number): Observable<any> {
    const params = new HttpParams().set('user_id', userId.toString());
    return this.http.get(`${this.baseUrl}/knowledge-graph/path`, { params });
  }

  // ==================== 知识图谱 - 资源推荐 ====================

  /**
   * 获取个性化推荐
   */
  getRecommendations(
    userId: number,
    limit: number = 10,
    subjects?: string[]
  ): Observable<{user_id: number; recommendations: Recommendation[]; strategy: string; message: string}> {
    const body = {
      user_id: userId,
      limit,
      subjects: subjects || []
    };

    return this.http.post<any>(`${this.baseUrl}/knowledge-graph/recommend`, body);
  }

  /**
   * 获取课件推荐
   */
  getCoursewareRecommendations(
    userId: number,
    subject?: string,
    limit: number = 10
  ): Observable<any> {
    let params = new HttpParams()
      .set('user_id', userId.toString())
      .set('limit', limit.toString());

    if (subject) {
      params = params.set('subject', subject);
    }

    return this.http.get(`${this.baseUrl}/knowledge-graph/recommend`, { params });
  }

  // ==================== 硬件项目管理 ====================

  /**
   * 获取硬件项目列表
   */
  getHardwareProjects(
    page: number = 1,
    size: number = 20,
    difficulty?: string,
    category?: string,
    subject?: string
  ): Observable<{items: HardwareProject[]; total: number; page: number; size: number; total_pages: number}> {
    let params = new HttpParams()
      .set('page', page.toString())
      .set('size', size.toString());

    if (difficulty) params = params.set('difficulty', difficulty);
    if (category) params = params.set('category', category);
    if (subject) params = params.set('subject', subject);

    return this.http.get<any>(`${this.baseUrl}/hardware-projects`, { params });
  }

  /**
   * 创建硬件项目
   */
  createHardwareProject(project: Partial<HardwareProject>): Observable<any> {
    return this.http.post(`${this.baseUrl}/hardware-projects`, project);
  }
}
```

---

### 3. 在模块中导入HttpClient

确保 `app.module.ts` 或 standalone component 配置中包含:

```typescript
import { HttpClientModule } from '@angular/common/http';

// 在 imports 数组中添加
imports: [
  HttpClientModule,
  // ... 其他模块
]
```

---

### 4. 创建示例组件

创建文件: `g:\iMato\src\app\components\openmt-demo\openmt-demo.component.ts`

```typescript
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { OpenMtSciEdService, Tutorial, HardwareProject, Recommendation } from '../../services/openmt-scied.service';

@Component({
  selector: 'app-openmt-demo',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="openmt-demo">
      <h1>OpenMTSciEd API 演示</h1>

      <!-- 教程列表 -->
      <section>
        <h2>教程列表</h2>
        <button (click)="loadTutorials()">加载教程</button>
        <div *ngIf="loading" class="loading">加载中...</div>
        <div *ngIf="error" class="error">{{ error }}</div>
        <ul *ngIf="tutorials.length > 0">
          <li *ngFor="let tutorial of tutorials">
            <strong>{{ tutorial.title }}</strong>
            <span>[{{ tutorial.subject }}]</span>
            <p>{{ tutorial.description }}</p>
          </li>
        </ul>
      </section>

      <!-- 硬件项目 -->
      <section>
        <h2>硬件项目</h2>
        <button (click)="loadHardwareProjects()">加载硬件项目</button>
        <ul *ngIf="hardwareProjects.length > 0">
          <li *ngFor="let project of hardwareProjects">
            <strong>{{ project.title }}</strong>
            <span>[{{ project.difficulty_level }}]</span>
          </li>
        </ul>
      </section>

      <!-- 学习路径 -->
      <section>
        <h2>生成学习路径</h2>
        <button (click)="generatePath()">为9-12年级物理生成路径</button>
        <div *ngIf="learningPath">
          <p>路径ID: {{ learningPath.path_id }}</p>
          <p>预计时长: {{ learningPath.estimated_duration_hours }}小时</p>
          <ol>
            <li *ngFor="let node of learningPath.nodes">
              {{ node.title }} ({{ node.estimated_time_minutes }}分钟)
            </li>
          </ol>
        </div>
      </section>

      <!-- 推荐 -->
      <section>
        <h2>资源推荐</h2>
        <button (click)="getRecommendations()">获取推荐</button>
        <ul *ngIf="recommendations.length > 0">
          <li *ngFor="let rec of recommendations">
            <strong>{{ rec.title }}</strong>
            <span>评分: {{ rec.score }}</span>
          </li>
        </ul>
      </section>
    </div>
  `,
  styles: [`
    .openmt-demo { padding: 20px; max-width: 1200px; margin: 0 auto; }
    section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
    button { padding: 10px 20px; margin: 10px 0; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; }
    button:hover { background: #0056b3; }
    .loading { color: #666; font-style: italic; }
    .error { color: red; padding: 10px; background: #ffe6e6; border-radius: 4px; }
    ul { list-style: none; padding: 0; }
    li { padding: 10px; margin: 5px 0; background: #f5f5f5; border-radius: 4px; }
    strong { color: #333; }
    span { color: #666; font-size: 0.9em; margin-left: 10px; }
  `]
})
export class OpenMtDemoComponent implements OnInit {
  tutorials: Tutorial[] = [];
  hardwareProjects: HardwareProject[] = [];
  recommendations: Recommendation[] = [];
  learningPath: any = null;
  loading = false;
  error: string | null = null;

  constructor(private openMtService: OpenMtSciEdService) {}

  ngOnInit() {
    // 可选: 组件初始化时自动加载数据
  }

  loadTutorials() {
    this.loading = true;
    this.error = null;
    
    this.openMtService.getTutorials(1, 5, 'physics').subscribe({
      next: (response) => {
        this.tutorials = response.items;
        this.loading = false;
      },
      error: (err) => {
        this.error = '加载教程失败: ' + err.message;
        this.loading = false;
      }
    });
  }

  loadHardwareProjects() {
    this.loading = true;
    this.error = null;
    
    this.openMtService.getHardwareProjects(1, 5).subscribe({
      next: (response) => {
        this.hardwareProjects = response.items;
        this.loading = false;
      },
      error: (err) => {
        this.error = '加载硬件项目失败: ' + err.message;
        this.loading = false;
      }
    });
  }

  generatePath() {
    this.loading = true;
    this.error = null;
    
    this.openMtService.generateLearningPath(1, '9-12', ['physics']).subscribe({
      next: (path) => {
        this.learningPath = path;
        this.loading = false;
      },
      error: (err) => {
        this.error = '生成学习路径失败: ' + err.message;
        this.loading = false;
      }
    });
  }

  getRecommendations() {
    this.loading = true;
    this.error = null;
    
    this.openMtService.getRecommendations(1, 5).subscribe({
      next: (response) => {
        this.recommendations = response.recommendations;
        this.loading = false;
      },
      error: (err) => {
        this.error = '获取推荐失败: ' + err.message;
        this.loading = false;
      }
    });
  }
}
```

---

### 5. 添加路由 (可选)

在 `app.routes.ts` 或路由配置中添加:

```typescript
{
  path: 'openmt-demo',
  loadComponent: () => import('./components/openmt-demo/openmt-demo.component')
    .then(m => m.OpenMtDemoComponent)
}
```

---

## 🧪 测试集成

1. **启动后端**:
   ```bash
   cd G:\OpenMTSciEd\backend-next
   npm run dev
   ```

2. **启动前端**:
   ```bash
   cd g:\iMato
   ng serve
   ```

3. **访问演示页面**:
   ```
   http://localhost:4200/openmt-demo
   ```

4. **点击各个按钮测试API调用**

---

## 📝 使用示例

### 在现有组件中使用

```typescript
import { Component, OnInit } from '@angular/core';
import { OpenMtSciEdService } from '../services/openmt-scied.service';

@Component({
  selector: 'app-learning-path',
  template: `...`
})
export class LearningPathComponent implements OnInit {
  constructor(private openMtService: OpenMtSciEdService) {}

  ngOnInit() {
    // 生成学习路径
    this.openMtService.generateLearningPath(
      userId,
      '9-12',
      ['physics', 'mathematics']
    ).subscribe(path => {
      console.log('学习路径:', path);
    });
  }
}
```

---

## ⚠️ 注意事项

1. **CORS配置**: 确保Next.js后端允许来自Angular开发服务器的跨域请求
2. **错误处理**: 所有API调用都应包含错误处理
3. **类型安全**: 使用TypeScript接口确保类型安全
4. **性能**: 考虑添加缓存机制避免重复请求

---

## 🔗 相关文档

- **API文档**: `G:\OpenMTSciEd\backend-next\API_DOCUMENTATION.md`
- **快速参考**: `G:\OpenMTSciEd\backend-next\API_QUICK_REFERENCE.md`
- **测试报告**: `G:\OpenMTSciEd\backend-next\API_FINAL_TEST_REPORT.md`

---

**集成完成!** 🎉
