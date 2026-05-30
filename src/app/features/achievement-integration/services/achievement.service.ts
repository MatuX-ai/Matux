import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
  Achievement,
  AchievementActivity,
  AchievementFile,
  AchievementFilter,
  AchievementProgress,
  AchievementReview,
  AchievementSort,
  AchievementStats,
  AchievementTemplate,
} from '../models/achievement.model';

import { AchievementMockService } from './achievement-mock.service';

/**
 * 学员成果服务
 * 支持真实 API 和 Mock 数据两种模式
 */
@Injectable({
  providedIn: 'root',
})
export class AchievementService {
  private readonly API_BASE = 'http://localhost:8000/api/v1/achievements';
  private readonly USE_MOCK = true; // 设置为 false 使用真实 API

  constructor(
    private http: HttpClient,
    private mockService: AchievementMockService
  ) {}

  /**
   * 获取学员成果列表
   */
  getAchievements(
    filter?: AchievementFilter,
    sort?: AchievementSort,
    page = 1,
    pageSize = 20
  ): Observable<{ data: Achievement[]; total: number }> {
    if (this.USE_MOCK) {
      return this.mockService.getAchievements(filter, sort, page, pageSize);
    }

    const params: any = { page, page_size: pageSize };

    if (filter) {
      if (filter.status?.length) params.status = filter.status.join(',');
      if (filter.type?.length) params.type = filter.type.join(',');
      if (filter.moduleId?.length) params.module_id = filter.moduleId.join(',');
      if (filter.lessonId?.length) params.lesson_id = filter.lessonId.join(',');
      if (filter.userId?.length) params.user_id = filter.userId.join(',');
      if (filter.dateFrom) params.date_from = filter.dateFrom;
      if (filter.dateTo) params.date_to = filter.dateTo;
      if (filter.tags?.length) params.tags = filter.tags.join(',');
      if (filter.searchQuery) params.search = filter.searchQuery;
    }

    if (sort) {
      params.sort_by = sort.field;
      params.sort_dir = sort.direction;
    }

    return this.http.get<{ data: Achievement[]; total: number }>(`${this.API_BASE}/achievements`, {
      params,
    });
  }

  /**
   * 获取单个成果详情
   */
  getAchievementById(id: number): Observable<Achievement> {
    return this.http.get<Achievement>(`${this.API_BASE}/achievements/${id}`);
  }

  /**
   * 获取用户的成果列表
   */
  getUserAchievements(userId: number, filter?: AchievementFilter): Observable<Achievement[]> {
    const params: any = {};

    if (filter) {
      if (filter.status?.length) params.status = filter.status.join(',');
      if (filter.type?.length) params.type = filter.type.join(',');
      if (filter.moduleId?.length) params.module_id = filter.moduleId.join(',');
      if (filter.lessonId?.length) params.lesson_id = filter.lessonId.join(',');
      if (filter.tags?.length) params.tags = filter.tags.join(',');
    }

    return this.http.get<Achievement[]>(`${this.API_BASE}/users/${userId}/achievements`, {
      params,
    });
  }

  /**
   * 创建新成果
   */
  createAchievement(achievement: Partial<Achievement>): Observable<Achievement> {
    return this.http.post<Achievement>(`${this.API_BASE}/achievements`, achievement);
  }

  /**
   * 更新成果
   */
  updateAchievement(id: number, achievement: Partial<Achievement>): Observable<Achievement> {
    return this.http.put<Achievement>(`${this.API_BASE}/achievements/${id}`, achievement);
  }

  /**
   * 删除成果
   */
  deleteAchievement(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_BASE}/achievements/${id}`);
  }

  /**
   * 上传成果文件
   */
  uploadAchievementFile(achievementId: number, file: File): Observable<AchievementFile> {
    const formData = new FormData();
    formData.append('file', file);

    return this.http.post<AchievementFile>(
      `${this.API_BASE}/achievements/${achievementId}/files`,
      formData
    );
  }

  /**
   * 删除成果文件
   */
  deleteAchievementFile(fileId: number): Observable<void> {
    return this.http.delete<void>(`${this.API_BASE}/files/${fileId}`);
  }

  /**
   * 提交成果审核
   */
  submitAchievement(id: number): Observable<Achievement> {
    return this.http.post<Achievement>(`${this.API_BASE}/achievements/${id}/submit`, {});
  }

  /**
   * 审核成果（教师/管理员）
   */
  reviewAchievement(
    id: number,
    review: {
      status: 'approved' | 'rejected' | 'revision';
      score: number;
      feedback: string;
    }
  ): Observable<Achievement> {
    return this.http.post<Achievement>(`${this.API_BASE}/achievements/${id}/review`, review);
  }

  /**
   * 获取成果审核记录
   */
  getAchievementReviews(achievementId: number): Observable<AchievementReview[]> {
    return this.http.get<AchievementReview[]>(
      `${this.API_BASE}/achievements/${achievementId}/reviews`
    );
  }

  /**
   * 获取成果模板列表
   */
  getTemplates(): Observable<AchievementTemplate[]> {
    return this.http.get<AchievementTemplate[]>(`${this.API_BASE}/templates`);
  }

  /**
   * 获取模板详情
   */
  getTemplateById(id: number): Observable<AchievementTemplate> {
    return this.http.get<AchievementTemplate>(`${this.API_BASE}/templates/${id}`);
  }

  /**
   * 创建成果模板
   */
  createTemplate(template: Partial<AchievementTemplate>): Observable<AchievementTemplate> {
    return this.http.post<AchievementTemplate>(`${this.API_BASE}/templates`, template);
  }

  /**
   * 更新成果模板
   */
  updateTemplate(
    id: number,
    template: Partial<AchievementTemplate>
  ): Observable<AchievementTemplate> {
    return this.http.put<AchievementTemplate>(`${this.API_BASE}/templates/${id}`, template);
  }

  /**
   * 删除成果模板
   */
  deleteTemplate(id: number): Observable<void> {
    return this.http.delete<void>(`${this.API_BASE}/templates/${id}`);
  }

  /**
   * 获取用户的成果进度
   */
  getUserAchievementProgress(
    userId: number,
    courseId?: number,
    moduleId?: number
  ): Observable<AchievementProgress> {
    const params: any = {};
    if (courseId) params.course_id = courseId;
    if (moduleId) params.module_id = moduleId;

    return this.http.get<AchievementProgress>(`${this.API_BASE}/users/${userId}/progress`, {
      params,
    });
  }

  /**
   * 获取成果统计信息
   */
  getAchievementStats(filter?: AchievementFilter): Observable<AchievementStats> {
    if (this.USE_MOCK) {
      return this.mockService.getAchievementStats(filter);
    }

    const params: any = {};

    if (filter) {
      if (filter.moduleId?.length) params.module_id = filter.moduleId.join(',');
      if (filter.userId?.length) params.user_id = filter.userId.join(',');
      if (filter.dateFrom) params.date_from = filter.dateFrom;
      if (filter.dateTo) params.date_to = filter.dateTo;
    }

    return this.http.get<AchievementStats>(`${this.API_BASE}/stats`, { params });
  }

  /**
   * 获取最近活动
   */
  getRecentActivity(limit = 10): Observable<AchievementActivity[]> {
    return this.http.get<AchievementActivity[]>(`${this.API_BASE}/activity`, {
      params: { limit },
    });
  }

  /**
   * 获取课程相关的成果
   */
  getCourseAchievements(courseId: number, filter?: AchievementFilter): Observable<Achievement[]> {
    const params: any = {};

    if (filter) {
      if (filter.status?.length) params.status = filter.status.join(',');
      if (filter.type?.length) params.type = filter.type.join(',');
      if (filter.lessonId?.length) params.lesson_id = filter.lessonId.join(',');
    }

    return this.http.get<Achievement[]>(`${this.API_BASE}/courses/${courseId}/achievements`, {
      params,
    });
  }

  /**
   * 获取模块相关的成果
   */
  getModuleAchievements(moduleId: number, filter?: AchievementFilter): Observable<Achievement[]> {
    const params: any = {};

    if (filter) {
      if (filter.status?.length) params.status = filter.status.join(',');
      if (filter.type?.length) params.type = filter.type.join(',');
      if (filter.lessonId?.length) params.lesson_id = filter.lessonId.join(',');
    }

    return this.http.get<Achievement[]>(`${this.API_BASE}/modules/${moduleId}/achievements`, {
      params,
    });
  }

  /**
   * 获取课程章节相关的成果
   */
  getLessonAchievements(lessonId: number, filter?: AchievementFilter): Observable<Achievement[]> {
    const params: any = {};

    if (filter) {
      if (filter.status?.length) params.status = filter.status.join(',');
      if (filter.type?.length) params.type = filter.type.join(',');
    }

    return this.http.get<Achievement[]>(`${this.API_BASE}/lessons/${lessonId}/achievements`, {
      params,
    });
  }

  /**
   * 导出成果数据
   */
  exportAchievements(filter?: AchievementFilter, format = 'csv'): Observable<Blob> {
    const params: any = { format };

    if (filter) {
      if (filter.status?.length) params.status = filter.status.join(',');
      if (filter.type?.length) params.type = filter.type.join(',');
      if (filter.moduleId?.length) params.module_id = filter.moduleId.join(',');
      if (filter.userId?.length) params.user_id = filter.userId.join(',');
    }

    return this.http.get(`${this.API_BASE}/export`, {
      params,
      responseType: 'blob',
    });
  }
}
