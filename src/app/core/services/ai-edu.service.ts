/**
 * AI-Edu-for-Kids 课程学习服务
 * 提供课程学习、进度追踪、积分统计等功能
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import {
  Achievement,
  AIEduLesson,
  AIEduModule,
  ApiResponse,
  LearningProgress,
  LearningStatistics,
  LessonCompletionRequest,
  ProgressUpdateRequest,
} from '../../models/ai-edu.models';

@Injectable({
  providedIn: 'root',
})
export class AIEduService {
  private readonly API_BASE = '/api/v1/org';

  constructor(private http: HttpClient) {}

  /**
   * 获取课程模块列表
   */
  getModules(orgId: number = 1): Observable<AIEduModule[]> {
    const url = `${this.API_BASE}/${orgId}/ai-edu/modules`;
    return this.http.get<ApiResponse<AIEduModule[]>>(url).pipe(
      map((response) => response.data),
      catchError((_error) => {
        return of([]);
      })
    );
  }

  /**
   * 获取模块详情
   */
  getModuleById(orgId: number, moduleId: number): Observable<AIEduModule> {
    const url = `${this.API_BASE}/${orgId}/ai-edu/modules/${moduleId}`;
    return this.http.get<ApiResponse<AIEduModule>>(url).pipe(map((response) => response.data));
  }

  /**
   * 获取模块下的课程列表
   */
  getLessonsByModule(orgId: number, moduleId: number): Observable<AIEduLesson[]> {
    const url = `${this.API_BASE}/${orgId}/ai-edu/modules/${moduleId}/lessons`;
    return this.http.get<ApiResponse<AIEduLesson[]>>(url).pipe(map((response) => response.data));
  }

  /**
   * 获取课程详情
   */
  getLessonById(orgId: number, lessonId: number): Observable<AIEduLesson> {
    const url = `${this.API_BASE}/${orgId}/ai-edu/lessons/${lessonId}`;
    return this.http.get<ApiResponse<AIEduLesson>>(url).pipe(map((response) => response.data));
  }

  /**
   * 更新学习进度
   */
  updateProgress(
    orgId: number,
    request: ProgressUpdateRequest
  ): Observable<{ progress_id: number; status: string }> {
    const url = `${this.API_BASE}/${orgId}/ai-edu/progress`;
    return this.http.post<ApiResponse<{ progress_id: number; status: string }>>(url, request).pipe(
      map((response) => ({
        progress_id: response.data.progress_id,
        status: response.data.status,
      }))
    );
  }

  /**
   * 获取用户学习进度列表
   */
  getUserProgress(
    orgId: number,
    moduleId?: number,
    statusFilter?: string
  ): Observable<LearningProgress[]> {
    let params = new HttpParams();

    if (moduleId) {
      params = params.set('module_id', moduleId.toString());
    }

    if (statusFilter) {
      params = params.set('status_filter', statusFilter);
    }

    const url = `${this.API_BASE}/${orgId}/ai-edu/progress`;
    return this.http
      .get<ApiResponse<LearningProgress[]>>(url, { params })
      .pipe(map((response) => response.data));
  }

  /**
   * 完成课程并获得积分
   */
  completeLesson(
    orgId: number,
    request: LessonCompletionRequest
  ): Observable<{ points_earned: number; status: string }> {
    const url = `${this.API_BASE}/${orgId}/ai-edu/progress/complete`;
    return this.http.post<ApiResponse<{ points: number; status: string }>>(url, request).pipe(
      map((response) => ({
        points_earned: response.data.points,
        status: response.data.status,
      }))
    );
  }

  /**
   * 获取学习统计信息
   */
  getStatistics(orgId: number): Observable<LearningStatistics> {
    const url = `${this.API_BASE}/${orgId}/ai-edu/progress/statistics`;
    return this.http
      .get<ApiResponse<LearningStatistics>>(url)
      .pipe(map((response) => response.data));
  }

  /**
   * 获取成就列表
   */
  getAchievements(orgId: number, userId: number): Observable<Achievement[]> {
    const url = `${this.API_BASE}/${orgId}/ai-edu/achievements`;
    const params = new HttpParams().set('user_id', userId.toString());

    return this.http
      .get<ApiResponse<Achievement[]>>(url, { params })
      .pipe(map((response) => response.data));
  }

  /**
   * 重置学习进度（重新开始课程）
   */
  resetProgress(orgId: number, lessonId: number): Observable<void> {
    const url = `${this.API_BASE}/${orgId}/ai-edu/progress/${lessonId}`;
    return this.http.delete<ApiResponse<void>>(url).pipe(map((response) => response.data));
  }

  /**
   * 计算预计获得的积分
   */
  calculateExpectedPoints(
    basePoints: number,
    gradeLevel: string,
    qualityScore: number,
    timeSavedMinutes: number = 0
  ): number {
    // 学段系数
    const gradeMultipliers: Record<string, number> = {
      'G1-G2': 1.0,
      'G3-G4': 1.2,
      'G5-G6': 1.5,
      'G7-G9': 2.0,
    };

    const gradeMult = gradeMultipliers[gradeLevel] || 1.0;

    // 质量系数
    let qualityMult = 1.0;
    if (qualityScore >= 90) {
      qualityMult = 1.2;
    } else if (qualityScore >= 80) {
      qualityMult = 1.1;
    }

    // 时间奖励
    const timeBonus = timeSavedMinutes * 0.5;

    // 总积分
    const total = Math.floor(basePoints * gradeMult * qualityMult) + timeBonus;

    return total;
  }

  /**
   * 将秒数转换为可读格式
   */
  formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}小时${minutes}分钟`;
    } else if (minutes > 0) {
      return `${minutes}分钟`;
    } else {
      return `${secs}秒`;
    }
  }

  /**
   * 获取成就稀有度颜色
   */
  getRarityColor(rarity: string): string {
    const colors: Record<string, string> = {
      common: '#4CAF50', // 绿色
      rare: '#2196F3', // 蓝色
      epic: '#9C27B0', // 紫色
      legendary: '#FF9800', // 橙色
      mythic: '#F44336', // 红色
    };
    return colors[rarity] || '#9E9E9E';
  }

  /**
   * 获取进度状态标签
   */
  getStatusLabel(status: string): string {
    const labels: Record<string, string> = {
      not_started: '未开始',
      in_progress: '进行中',
      completed: '已完成',
    };
    return labels[status] || status;
  }

  /**
   * 获取进度状态颜色
   */
  getStatusColor(status: string): string {
    const colors: Record<string, string> = {
      not_started: '#9E9E9E',
      in_progress: '#2196F3',
      completed: '#4CAF50',
    };
    return colors[status] || '#9E9E9E';
  }
}
