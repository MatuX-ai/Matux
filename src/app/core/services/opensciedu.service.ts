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

/* eslint-disable no-console, max-lines-per-function, @typescript-eslint/no-non-null-assertion */
import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of, timeout } from 'rxjs';
import { catchError, map, switchMap, tap } from 'rxjs/operators';

import { OpenSciEDUMockService } from './opensciedu-mock.service';

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

  // IndexedDB 配置
  private static readonly DB_NAME = 'OpenSciEDUCache';
  private static readonly DB_VERSION = 1;
  private static readonly STORE_NAME = 'cache';
  private static readonly CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 小时

  private db: IDBDatabase | null = null;

  constructor(private http: HttpClient) {
    this.initIndexedDB();
  }

  // ==================== IndexedDB 缓存层 ====================

  private initIndexedDB(): void {
    if (typeof indexedDB === 'undefined') return;
    try {
      const request = indexedDB.open(OpenSciEDUService.DB_NAME, OpenSciEDUService.DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(OpenSciEDUService.STORE_NAME)) {
          db.createObjectStore(OpenSciEDUService.STORE_NAME);
        }
      };
      request.onsuccess = () => {
        this.db = request.result;
      };
      request.onerror = () => {
        console.warn('[OpenSciEDU] IndexedDB 初始化失败');
      };
    } catch {
      console.warn('[OpenSciEDU] IndexedDB 不可用');
    }
  }

  private cacheSet(key: string, value: unknown): void {
    if (!this.db) return;
    try {
      const tx = this.db.transaction(OpenSciEDUService.STORE_NAME, 'readwrite');
      const store = tx.objectStore(OpenSciEDUService.STORE_NAME);
      store.put({ data: value, timestamp: Date.now() }, key);
    } catch (err) {
      console.warn('[OpenSciEDU] 缓存写入失败:', err);
    }
  }

  private cacheGet(key: string): Observable<unknown> {
    if (!this.db) return of(null);
    return new Observable<unknown>((subscriber) => {
      try {
        const tx = this.db!.transaction(OpenSciEDUService.STORE_NAME, 'readonly');
        const store = tx.objectStore(OpenSciEDUService.STORE_NAME);
        const request = store.get(key);
        request.onsuccess = () => {
          const result = request.result as { timestamp?: number; data?: unknown } | undefined;
          if (result && Date.now() - (result.timestamp ?? 0) < OpenSciEDUService.CACHE_TTL_MS) {
            subscriber.next(result.data);
          } else {
            subscriber.next(null);
          }
          subscriber.complete();
        };
        request.onerror = () => {
          subscriber.next(null);
          subscriber.complete();
        };
      } catch {
        subscriber.next(null);
        subscriber.complete();
      }
    });
  }

  /**
   * 清除本地 IndexedDB 缓存
   */
  clearLocalCache(): Observable<boolean> {
    if (!this.db) return of(false);
    return new Observable<boolean>((subscriber) => {
      try {
        const tx = this.db!.transaction(OpenSciEDUService.STORE_NAME, 'readwrite');
        tx.objectStore(OpenSciEDUService.STORE_NAME).clear();
        tx.oncomplete = () => {
          subscriber.next(true);
          subscriber.complete();
        };
        tx.onerror = () => {
          subscriber.next(false);
          subscriber.complete();
        };
      } catch {
        subscriber.next(false);
        subscriber.complete();
      }
    });
  }

  /**
   * 获取模拟服务实例（创建新实例避免状态问题）
   */
  private createMockServiceInstance(): OpenSciEDUMockService {
    return new OpenSciEDUMockService();
  }

  /**
   * 获取公共课程列表
   *
   * 降级策略: API → IndexedDB 缓存 → Mock 数据
   */
  getPublicCourses(params: {
    page?: number;
    pageSize?: number;
    category?: string;
    difficulty?: string;
    sortBy?: string;
  }): Observable<CourseListResponse> {
    // 构建缓存键（包含 sortBy）
    const cacheKey = `courses_${params.page}_${params.pageSize}_${params.category ?? ''}_${params.difficulty ?? ''}_${params.sortBy ?? ''}`;

    // 如果 API 已知不可用，先尝试缓存再使用模拟数据
    if (this.apiAvailable === false) {
      return this.cacheGet(cacheKey).pipe(
        switchMap((cached) => {
          if (cached) return of(cached as CourseListResponse);
          return this.createMockServiceInstance().getPublicCourses(
            params.page ?? 1,
            params.pageSize ?? 20,
            params.category,
            params.difficulty
          );
        })
      );
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
        // 【P2-3 修复】5 秒超时兑底，避免 stuck loading
        timeout({ each: 5000 }),
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
        tap((result) => this.cacheSet(cacheKey, result)),
        catchError((error) => {
          this.apiAvailable = false;
          const errorObj = error as { message?: string };
          console.warn('[OpenSciEDU] API 请求失败，尝试缓存或模拟数据:', errorObj.message);

          // 尝试 IndexedDB 缓存
          return this.cacheGet(cacheKey).pipe(
            switchMap((cached) => {
              if (cached) return of(cached as CourseListResponse);
              // 降级到模拟数据
              return this.createMockServiceInstance().getPublicCourses(
                params.page ?? 1,
                params.pageSize ?? 20,
                params.category,
                params.difficulty
              );
            })
          );
        })
      );
  }

  /**
   * 获取课程详情
   *
   * 降级策略: API → IndexedDB 缓存 → Mock 数据
   */
  getCourseDetail(courseId: string): Observable<CourseDetail | null> {
    if (this.apiAvailable === false) {
      // 先尝试 IndexedDB 缓存，再降级到 Mock
      return this.cacheGet(`course_detail_${courseId}`).pipe(
        switchMap((cached) => {
          if (cached) return of(cached as CourseDetail);
          return this.createMockServiceInstance().getCourseDetail(courseId);
        })
      );
    }

    return this.http.get<CourseDetail>(`${this.API_BASE}/courses/${courseId}`).pipe(
      tap((detail) => this.cacheSet(`course_detail_${courseId}`, detail)),
      catchError(() => {
        this.apiAvailable = false;
        // 尝试 IndexedDB 缓存
        return this.cacheGet(`course_detail_${courseId}`).pipe(
          switchMap((cached) => {
            if (cached) return of(cached as CourseDetail);
            // 降级到 Mock
            return this.createMockServiceInstance().getCourseDetail(courseId);
          })
        );
      })
    );
  }

  /**
   * 获取知识图谱数据
   *
   * 降级策略: API → IndexedDB 缓存 → Mock 数据
   */
  getKnowledgeGraph(forceRefresh = false): Observable<KnowledgeGraphData | null> {
    if (this.apiAvailable === false && !forceRefresh) {
      // 先尝试 IndexedDB 缓存，再降级到 Mock
      return this.cacheGet('knowledge_graph').pipe(
        switchMap((cached) => {
          if (cached) return of(cached as KnowledgeGraphData);
          return this.createMockServiceInstance().getKnowledgeGraph();
        })
      );
    }

    let params = new HttpParams();
    if (forceRefresh) {
      params = params.set('refresh', 'true');
    }

    return this.http.get<KnowledgeGraphData>(`${this.API_BASE}/knowledge-graph`, { params }).pipe(
      tap((data) => this.cacheSet('knowledge_graph', data)),
      catchError(() => {
        this.apiAvailable = false;
        return this.cacheGet('knowledge_graph').pipe(
          switchMap((cached) => {
            if (cached) return of(cached as KnowledgeGraphData);
            return this.createMockServiceInstance().getKnowledgeGraph();
          })
        );
      })
    );
  }

  /**
   * 搜索课程
   *
   * 降级策略: API → Mock 数据（搜索结果时效性强，不缓存 IndexedDB）
   */
  searchCourses(params: {
    keyword: string;
    page?: number;
    pageSize?: number;
  }): Observable<SearchResult> {
    if (this.apiAvailable === false) {
      return this.createMockServiceInstance().searchCourses(
        params.keyword,
        params.page ?? 1,
        params.pageSize ?? 20
      );
    }

    const httpParams = new HttpParams()
      .set('keyword', params.keyword)
      .set('page', String(params.page ?? 1))
      .set('page_size', String(params.pageSize ?? 20));

    return this.http.get<SearchResult>(`${this.API_BASE}/search`, { params: httpParams }).pipe(
      tap(() => {
        this.apiAvailable = true;
      }),
      catchError(() => {
        this.apiAvailable = false;
        return this.createMockServiceInstance().searchCourses(
          params.keyword,
          params.page ?? 1,
          params.pageSize ?? 20
        );
      })
    );
  }

  /**
   * 获取课程分类列表
   *
   * 降级策略: API → Mock 数据
   */
  getCategories(): Observable<CourseCategory[]> {
    if (this.apiAvailable === false) {
      return this.createMockServiceInstance().getCategories();
    }

    return this.http.get<CourseCategory[]>(`${this.API_BASE}/categories`).pipe(
      tap(() => {
        this.apiAvailable = true;
      }),
      catchError(() => {
        this.apiAvailable = false;
        return this.createMockServiceInstance().getCategories();
      })
    );
  }

  /**
   * 健康检查
   */
  healthCheck(): Observable<{ status: string; service: string; apiUrl: string }> {
    return this.http
      .get<{ status: string; service: string; api_url: string }>(`${this.API_BASE}/health`)
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
      .post<{ success: boolean; message: string }>(`${this.API_BASE}/cache/clear`, {})
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
}
