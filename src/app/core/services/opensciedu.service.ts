/**
 * OpenSciEDU 公共课程服务
 *
 * 提供与 OpenSciEDU (https://opensciedu.matux.tech/) API 的对接
 * 支持课程目录、知识图谱和搜索功能
 * 当 API 不可用时，自动降级到模拟数据
 *
 * 基于 PRD F-18: OpenSciEDU 公共课程自动接入
 *
 * 【Neo4j 依赖说明】
 *  OpenSciEDU 后端依赖 Neo4j 数据库，当前使用云服务存在 DNS 问题:
 *  - 错误: ENOTFOUND 4abd5ef9.databases.neo4j.io
 *  - 部署自有 Neo4j 服务器后，设置环境变量即可:
 *    NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
 *  - 参考: g:\OpenMTSciEd\backend-next\lib\neo4j.ts
 */

import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of, forkJoin } from 'rxjs';
import { catchError, map, tap, finalize } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

// 延迟导入模拟服务（避免循环依赖）
let OpenSciEDUMockService: any = null;

/**
 * 课程分类
 */
export interface CourseCategory {
  id: string;
  name: string;
  icon?: string;
  description?: string;
}

/**
 * 课程讲师
 */
export interface CourseInstructor {
  id: string;
  name: string;
  avatar?: string;
  title?: string;
}

/**
 * 课程章节
 */
export interface CourseChapter {
  id: string;
  title: string;
  order: number;
  lessons: CourseLesson[];
  durationMinutes?: number;
}

/**
 * 课程课时
 */
export interface CourseLesson {
  id: string;
  title: string;
  durationMinutes?: number;
  type: 'video' | 'text' | 'quiz' | 'exercise';
}

/**
 * 公共课程
 */
export interface PublicCourse {
  id: string;
  title: string;
  description: string;
  coverImage?: string;
  category: CourseCategory;
  instructor: CourseInstructor;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  durationMinutes: number;
  lessonCount: number;
  studentCount: number;
  rating: number;
  tags: string[];
  createdAt: string;
  updatedAt: string;
  isFree: boolean;
  certificateAvailable: boolean;
}

/**
 * 课程列表响应
 */
export interface CourseListResponse {
  courses: PublicCourse[];
  total: number;
  page: number;
  pageSize: number;
  hasNext: boolean;
}

/**
 * 课程列表响应（API 原始格式，使用 snake_case）
 */
interface CourseListResponseApi {
  courses: PublicCourse[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

/**
 * 课程详情
 */
export interface CourseDetail {
  id: string;
  title: string;
  description: string;
  coverImage?: string;
  category: CourseCategory;
  instructor: CourseInstructor;
  difficulty: string;
  durationMinutes: number;
  chapters: CourseChapter[];
  studentCount: number;
  rating: number;
  tags: string[];
  learningOutcomes: string[];
  prerequisites: string[];
  createdAt: string;
  updatedAt: string;
  isFree: boolean;
  certificateAvailable: boolean;
}

/**
 * 知识图谱节点
 */
export interface KnowledgeNode {
  id: string;
  name: string;
  category: string;
  level: number;
  description?: string;
  courseCount: number;
  positionX?: number;
  positionY?: number;
}

/**
 * 知识图谱边
 */
export interface KnowledgeEdge {
  source: string;
  target: string;
  relationType: 'prerequisite' | 'related' | 'extends';
}

/**
 * 知识图谱数据
 */
export interface KnowledgeGraphData {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
  categories: string[];
}

/**
 * 搜索结果
 */
export interface SearchResult {
  courses: PublicCourse[];
  total: number;
  query: string;
  suggestions: string[];
}

/**
 * OpenSciEDU 服务
 */
@Injectable({
  providedIn: 'root',
})
export class OpenSciEDUService {
  private readonly API_BASE = '/api/v1/opensciedu';

  // API 可用性状态
  private apiAvailable: boolean | null = null;
  private healthCheckInProgress = false;

  constructor(private http: HttpClient) {}

  /**
   * 懒加载模拟服务
   */
  private getMockService(): any {
    if (!OpenSciEDUMockService) {
      // 动态导入避免循环依赖
      import('./opensciedu-mock.service').then(module => {
        OpenSciEDUMockService = module.OpenSciEDUMockService;
      });
    }
    return OpenSciEDUMockService;
  }

  /**
   * 检查 API 可用性
   */
  private checkApiAvailability(): Observable<boolean> {
    if (this.apiAvailable === false) {
      return of(false);
    }

    if (this.healthCheckInProgress) {
      return of(true);
    }

    this.healthCheckInProgress = true;

    return this.http.get<{ status: string }>(`${this.API_BASE}/health`).pipe(
      map(() => {
        this.apiAvailable = true;
        this.healthCheckInProgress = false;
        console.log('[OpenSciEDU] API 可用');
        return true;
      }),
      catchError(() => {
        this.apiAvailable = false;
        this.healthCheckInProgress = false;
        console.warn('[OpenSciEDU] API 不可用，启用模拟数据模式');
        return of(false);
      })
    );
  }

  /**
   * 获取模拟服务实例（创建新实例避免状态问题）
   */
  private createMockServiceInstance(): any {
    const mockServiceClass = this.getMockService();
    if (mockServiceClass) {
      return new mockServiceClass();
    }
    return null;
  }

  /**
   * 获取公共课程列表
   *
   * @param page 页码（从 1 开始）
   * @param pageSize 每页数量
   * @param category 分类筛选
   * @param difficulty 难度筛选
   * @param sortBy 排序字段
   */
  getPublicCourses(params: {
    page?: number;
    pageSize?: number;
    category?: string;
    difficulty?: string;
    sortBy?: string;
  }): Observable<CourseListResponse> {
    // 如果 API 已知不可用，直接使用模拟数据
    if (this.apiAvailable === false) {
      const mockService = this.createMockServiceInstance();
      if (mockService) {
        return mockService.getPublicCourses(
          params.page ?? 1,
          params.pageSize ?? 20,
          params.category,
          params.difficulty
        );
      }
    }

    let httpParams = new HttpParams()
      .set('page', String(params.page ?? 1))
      .set('page_size', String(params.pageSize ?? 20));

    if (params.category) {
      httpParams = httpParams.set('category', params.category);
    }
    if (params.difficulty) {
      httpParams = httpParams.set('difficulty', params.difficulty);
    }
    if (params.sortBy) {
      httpParams = httpParams.set('sort_by', params.sortBy);
    }

    return this.http
      .get<CourseListResponseApi>(`${this.API_BASE}/courses`, {
        params: httpParams,
      })
      .pipe(
        tap(() => {
          this.apiAvailable = true;
        }),
        map((response) => ({
          courses: response.courses,
          total: response.total,
          page: response.page,
          pageSize: response.page_size,
          hasNext: response.has_next,
        })),
        catchError((error) => {
          this.apiAvailable = false;
          console.warn('[OpenSciEDU] API 请求失败，使用模拟数据:', error.message);

          // 降级到模拟数据
          const mockService = this.createMockServiceInstance();
          if (mockService) {
            return mockService.getPublicCourses(
              params.page ?? 1,
              params.pageSize ?? 20,
              params.category,
              params.difficulty
            ) as Observable<CourseListResponse>;
          }

          return of({
            courses: [],
            total: 0,
            page: params.page ?? 1,
            pageSize: params.pageSize ?? 20,
            hasNext: false,
          });
        })
      );
  }

  /**
   * 获取课程详情
   *
   * @param courseId 课程 ID
   */
  getCourseDetail(courseId: string): Observable<CourseDetail | null> {
    return this.http
      .get<CourseDetail>(`${this.API_BASE}/courses/${courseId}`)
      .pipe(catchError(() => of(null as CourseDetail | null)));
  }

  /**
   * 获取知识图谱数据
   *
   * @param forceRefresh 强制刷新缓存
   */
  getKnowledgeGraph(forceRefresh = false): Observable<KnowledgeGraphData | null> {
    let params = new HttpParams();
    if (forceRefresh) {
      params = params.set('refresh', 'true');
    }

    return this.http
      .get<KnowledgeGraphData>(`${this.API_BASE}/knowledge-graph`, { params })
      .pipe(catchError(() => of(null as KnowledgeGraphData | null)));
  }

  /**
   * 搜索课程
   *
   * @param keyword 搜索关键词
   * @param page 页码
   * @param pageSize 每页数量
   */
  searchCourses(params: {
    keyword: string;
    page?: number;
    pageSize?: number;
  }): Observable<SearchResult> {
    let httpParams = new HttpParams()
      .set('keyword', params.keyword)
      .set('page', String(params.page ?? 1))
      .set('page_size', String(params.pageSize ?? 20));

    return this.http
      .get<SearchResult>(`${this.API_BASE}/search`, { params: httpParams })
      .pipe(catchError(() => of({ courses: [], total: 0, query: params.keyword, suggestions: [] } as SearchResult)));
  }

  /**
   * 获取课程分类列表
   */
  getCategories(): Observable<CourseCategory[]> {
    return this.http
      .get<CourseCategory[]>(`${this.API_BASE}/categories`)
      .pipe(catchError(() => of([] as CourseCategory[])));
  }

  /**
   * 健康检查
   */
  healthCheck(): Observable<{ status: string; service: string; apiUrl: string }> {
    return this.http
      .get<{ status: string; service: string; api_url: string }>(
        `${this.API_BASE}/health`
      )
      .pipe(
        map((response) => ({
          status: response.status,
          service: response.service,
          apiUrl: response.api_url,
        }))
      )
      .pipe(catchError(() => of({ status: 'offline', service: 'OpenSciEDU', apiUrl: '' })));
  }

  /**
   * 清除缓存
   */
  clearCache(): Observable<{ success: boolean; message: string }> {
    return this.http
      .post<{ success: boolean; message: string }>(
        `${this.API_BASE}/cache/clear`,
        {}
      )
      .pipe(catchError(() => of({ success: false, message: 'API unavailable' })));
  }

  /**
   * 获取难度标签
   */
  getDifficultyLabel(difficulty: string): string {
    const labels: Record<string, string> = {
      beginner: '入门',
      intermediate: '进阶',
      advanced: '高级',
    };
    return labels[difficulty] || difficulty;
  }

  /**
   * 获取难度颜色
   */
  getDifficultyColor(difficulty: string): string {
    const colors: Record<string, string> = {
      beginner: '#22c55e', // green
      intermediate: '#f59e0b', // amber
      advanced: '#ef4444', // red
    };
    return colors[difficulty] || '#6b7280';
  }

  /**
   * 格式化时长
   */
  formatDuration(minutes: number): string {
    if (minutes < 60) {
      return `${minutes} 分钟`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours} 小时 ${mins} 分钟` : `${hours} 小时`;
  }

  /**
   * 格式化学生数量
   */
  formatStudentCount(count: number): string {
    if (count >= 10000) {
      return `${(count / 10000).toFixed(1)} 万`;
    }
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)} k`;
    }
    return String(count);
  }

  /**
   * 错误处理
   */
  private handleError<T>(operation: string, error: unknown): Observable<T> {
    console.error(`[OpenSciEDU] ${operation} failed:`, error);
    // 返回空结果而不是抛出错误，避免组件崩溃
    return of(null as unknown as T);
  }
}
