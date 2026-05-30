import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { shareReplay } from 'rxjs/operators';

/**
 * AI-Edu 学习服务
 * 提供课程学习、进度跟踪、积分管理等功能
 */
@Injectable({
  providedIn: 'root',
})
export class AIEduLearningService {
  private readonly API_BASE = 'http://localhost:8000/api/v1/org/1/ai-edu';

  // 缓存机制
  private cache = new Map<string, { data: any; timestamp: number }>();
  private readonly CACHE_TTL = 5 * 60 * 1000; // 5 分钟缓存时间

  // 学习进度主题
  private progressSubject = new BehaviorSubject<any>(null);
  public progress$ = this.progressSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * 从缓存获取数据
   */
  private getFromCache(key: string): any | null {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.CACHE_TTL) {
      return cached.data;
    }
    this.cache.delete(key);
    return null;
  }

  /**
   * 设置缓存
   */
  private setCache(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
    });
  }

  /**
   * 清除缓存
   */
  clearCache(pattern?: string): void {
    if (pattern) {
      this.cache.forEach((_, key) => {
        if (key.includes(pattern)) {
          this.cache.delete(key);
        }
      });
    } else {
      this.cache.clear();
    }
  }

  /**
   * 获取课程模块详情
   */
  getModule(moduleId: number): Observable<any> {
    const cacheKey = `module_${moduleId}`;
    const cached = this.getFromCache(cacheKey);

    if (cached) {
      return new Observable((observer) => {
        observer.next(cached);
        observer.complete();
      });
    }

    return this.http.get(`${this.API_BASE}/modules/${moduleId}`).pipe(
      tap((data) => this.setCache(cacheKey, data)),
      shareReplay(1)
    );
  }

  /**
   * 获取课时详情
   */
  getLesson(lessonId: number): Observable<any> {
    const cacheKey = `lesson_${lessonId}`;
    const cached = this.getFromCache(cacheKey);

    if (cached) {
      return new Observable((observer) => {
        observer.next(cached);
        observer.complete();
      });
    }

    return this.http.get(`${this.API_BASE}/lessons/${lessonId}`).pipe(
      tap((data) => this.setCache(cacheKey, data)),
      shareReplay(1)
    );
  }

  /**
   * 更新学习进度
   */
  updateProgress(
    userId: number,
    lessonId: number,
    completionStatus: string,
    score?: number
  ): Observable<any> {
    this.clearCache(`progress_${userId}`);

    return this.http
      .post(`${this.API_BASE}/progress/update`, {
        user_id: userId,
        lesson_id: lessonId,
        completion_status: completionStatus,
        score,
      })
      .pipe(
        tap(() => {
          // 触发进度更新通知
          this.progressSubject.next({
            userId,
            lessonId,
            status: completionStatus,
            timestamp: Date.now(),
          });
        })
      );
  }

  /**
   * 完成课程
   */
  completeLesson(userId: number, lessonId: number, score = 100): Observable<any> {
    return this.updateProgress(userId, lessonId, 'completed', score);
  }

  /**
   * 获取用户学习进度
   */
  getUserProgress(userId: number, moduleId?: number): Observable<any> {
    const cacheKey = `progress_${userId}_${moduleId || 'all'}`;
    const cached = this.getFromCache(cacheKey);

    if (cached) {
      return new Observable((observer) => {
        observer.next(cached);
        observer.complete();
      });
    }

    let params = new HttpParams();
    if (moduleId) {
      params = params.set('module_id', moduleId.toString());
    }

    return this.http.get(`${this.API_BASE}/progress/user/${userId}`, { params }).pipe(
      tap((data) => this.setCache(cacheKey, data)),
      shareReplay(1)
    );
  }

  /**
   * 运行代码
   */
  executeCode(code: string, language: string): Observable<any> {
    return this.http.post(`${this.API_BASE}/execute-code`, {
      code,
      language,
    });
  }

  /**
   * 保存学习笔记
   */
  saveNote(userId: number, lessonId: number, content: string): Observable<any> {
    this.clearCache(`notes_${userId}_${lessonId}`);

    return this.http.post(`${this.API_BASE}/notes/save`, {
      user_id: userId,
      lesson_id: lessonId,
      content,
    });
  }

  /**
   * 获取学习笔记
   */
  getNote(userId: number, lessonId: number): Observable<any> {
    const cacheKey = `notes_${userId}_${lessonId}`;
    const cached = this.getFromCache(cacheKey);

    if (cached) {
      return new Observable((observer) => {
        observer.next(cached);
        observer.complete();
      });
    }

    return this.http.get(`${this.API_BASE}/notes/${userId}/${lessonId}`).pipe(
      tap((data) => this.setCache(cacheKey, data)),
      shareReplay(1)
    );
  }

  /**
   * 开始测验
   */
  startQuiz(lessonId: number): Observable<any> {
    return this.http.post(`${this.API_BASE}/quiz/start`, {
      lesson_id: lessonId,
    });
  }

  /**
   * 提交测验答案
   */
  submitQuiz(quizId: number, answers: any[]): Observable<any> {
    return this.http.post(`${this.API_BASE}/quiz/submit`, {
      quiz_id: quizId,
      answers,
    });
  }

  /**
   * 获取积分统计
   */
  getPointsStats(userId: number): Observable<any> {
    const cacheKey = `points_${userId}`;
    const cached = this.getFromCache(cacheKey);

    if (cached) {
      return new Observable((observer) => {
        observer.next(cached);
        observer.complete();
      });
    }

    return this.http.get(`${this.API_BASE}/points/${userId}`).pipe(
      tap((data) => this.setCache(cacheKey, data)),
      shareReplay(1)
    );
  }

  /**
   * 获取成就徽章
   */
  getAchievements(userId: number): Observable<any> {
    const cacheKey = `achievements_${userId}`;
    const cached = this.getFromCache(cacheKey);

    if (cached) {
      return new Observable((observer) => {
        observer.next(cached);
        observer.complete();
      });
    }

    return this.http.get(`${this.API_BASE}/achievements/${userId}`).pipe(
      tap((data) => this.setCache(cacheKey, data)),
      shareReplay(1)
    );
  }
}

// RxJS 操作符导入
import { tap } from 'rxjs/operators';
