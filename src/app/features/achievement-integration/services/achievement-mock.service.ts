import { Injectable } from '@angular/core';
import { from, Observable, throwError } from 'rxjs';
import { map } from 'rxjs/operators';

import {
  COLD_START_CONFIG,
  getMockAchievements,
  getMockStats,
  getRecentActivity,
  getUserProgress as getMockUserProgress,
  MOCK_ACHIEVEMENTS,
  mockApiDelay,
} from '../mock-data/cold-start-data';
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

/**
 * 学员成果 Mock 服务
 * 用于在开发环境和没有实际后端时提供模拟数据
 */
@Injectable({
  providedIn: 'root',
})
export class AchievementMockService {
  private enabled = COLD_START_CONFIG.enabled;

  /**
   * 将Promise转换为Observable的辅助方法
   */
  private delayToObservable<T>(data: T): Observable<T> {
    return from(mockApiDelay(data));
  }

  /**
   * 获取成果列表
   */
  getAchievements(
    filter?: AchievementFilter,
    sort?: AchievementSort,
    page = 1,
    pageSize = 20
  ): Observable<{ data: Achievement[]; total: number }> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    return this.delayToObservable(getMockAchievements(page, pageSize, this.convertFilter(filter)));
  }

  /**
   * 获取单个成果详情
   */
  getAchievementById(id: number): Observable<Achievement> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const achievement = MOCK_ACHIEVEMENTS.find((a) => a.id === id);
    if (achievement) {
      return this.delayToObservable(achievement);
    }
    return this.createNotFoundError(`Achievement ${id} not found`);
  }

  /**
   * 获取用户的成果列表
   */
  getUserAchievements(userId: number, filter?: AchievementFilter): Observable<Achievement[]> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const userAchievements = MOCK_ACHIEVEMENTS.filter((a) => a.userId === userId);

    let filtered = [...userAchievements];

    // 应用筛选
    if (filter?.status && filter.status.length > 0) {
      filtered = filtered.filter((a) => filter.status!.includes(a.status));
    }

    if (filter?.type && filter.type.length > 0) {
      filtered = filtered.filter((a) => filter.type!.includes(a.type));
    }

    if (filter?.moduleId && filter.moduleId.length > 0) {
      filtered = filtered.filter((a) => filter.moduleId!.includes(a.moduleId!));
    }

    if (filter?.lessonId && filter.lessonId.length > 0) {
      filtered = filtered.filter((a) => filter.lessonId!.includes(a.lessonId!));
    }

    // 按提交时间降序
    filtered.sort((a, b) => new Date(b.submittedAt).getTime() - new Date(a.submittedAt).getTime());

    return this.delayToObservable(filtered);
  }

  /**
   * 创建新成果
   */
  createAchievement(achievement: Partial<Achievement>): Observable<Achievement> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const newAchievement: Achievement = {
      id: MOCK_ACHIEVEMENTS.length + 1,
      userId: achievement.userId || 1001,
      moduleId: achievement.moduleId,
      lessonId: achievement.lessonId,
      type: achievement.type || 'project',
      title: achievement.title || '新成果',
      description: achievement.description || '',
      files: [],
      status: 'pending',
      submittedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      tags: achievement.tags || [],
      isPublic: achievement.isPublic ?? true,
    };

    MOCK_ACHIEVEMENTS.unshift(newAchievement);

    return this.delayToObservable(newAchievement);
  }

  /**
   * 更新成果
   */
  updateAchievement(id: number, achievement: Partial<Achievement>): Observable<Achievement> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const index = MOCK_ACHIEVEMENTS.findIndex((a) => a.id === id);
    if (index === -1) {
      return this.createNotFoundError(`Achievement ${id} not found`);
    }

    MOCK_ACHIEVEMENTS[index] = {
      ...MOCK_ACHIEVEMENTS[index],
      ...achievement,
      updatedAt: new Date().toISOString(),
    };

    return this.delayToObservable(MOCK_ACHIEVEMENTS[index]);
  }

  /**
   * 删除成果
   */
  deleteAchievement(id: number): Observable<void> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const index = MOCK_ACHIEVEMENTS.findIndex((a) => a.id === id);
    if (index === -1) {
      return this.createNotFoundError(`Achievement ${id} not found`);
    }

    MOCK_ACHIEVEMENTS.splice(index, 1);

    return this.delayToObservable(undefined);
  }

  /**
   * 上传成果文件
   */
  uploadAchievementFile(achievementId: number, file: File): Observable<AchievementFile> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const achievement = MOCK_ACHIEVEMENTS.find((a) => a.id === achievementId);
    if (!achievement) {
      return this.createNotFoundError(`Achievement ${achievementId} not found`);
    }

    const newFile: AchievementFile = {
      id: Math.floor(Math.random() * 10000),
      achievementId,
      fileName: file.name,
      fileType: file.type,
      fileSize: file.size,
      fileUrl: URL.createObjectURL(file),
      uploadedAt: new Date().toISOString(),
    };

    achievement.files.push(newFile);
    achievement.updatedAt = new Date().toISOString();

    return this.delayToObservable(newFile);
  }

  /**
   * 删除成果文件
   */
  deleteAchievementFile(fileId: number): Observable<void> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    for (const achievement of MOCK_ACHIEVEMENTS) {
      const fileIndex = achievement.files.findIndex((f) => f.id === fileId);
      if (fileIndex !== -1) {
        achievement.files.splice(fileIndex, 1);
        achievement.updatedAt = new Date().toISOString();
        return this.delayToObservable(undefined);
      }
    }

    return this.delayToObservable(undefined);
  }

  /**
   * 提交成果审核
   */
  submitAchievement(id: number): Observable<Achievement> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    return this.updateAchievement(id, { status: 'pending' });
  }

  /**
   * 审核成果
   */
  reviewAchievement(
    id: number,
    review: {
      status: 'approved' | 'rejected' | 'revision';
      score: number;
      feedback: string;
    }
  ): Observable<Achievement> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    return this.updateAchievement(id, {
      status: review.status,
      score: review.score,
      feedback: review.feedback,
      reviewedAt: new Date().toISOString(),
    });
  }

  /**
   * 获取成果审核记录
   */
  getAchievementReviews(achievementId: number): Observable<AchievementReview[]> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const achievement = MOCK_ACHIEVEMENTS.find((a) => a.id === achievementId);
    if (!achievement) {
      return this.createNotFoundError(`Achievement ${achievementId} not found`);
    }

    // 模拟审核记录
    const reviews: AchievementReview[] =
      achievement.status !== 'pending'
        ? [
            {
              id: 1,
              achievementId,
              reviewerId: 2001,
              reviewerName: '张老师',
              status: achievement.status as any,
              score: achievement.score || 0,
              feedback: achievement.feedback || '',
              reviewedAt: achievement.reviewedAt || new Date().toISOString(),
            },
          ]
        : [];

    return this.delayToObservable(reviews);
  }

  /**
   * 获取成果模板列表
   */
  getTemplates(): Observable<AchievementTemplate[]> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const templates: AchievementTemplate[] = [
      {
        id: 1,
        name: '项目卡片',
        type: 'project',
        layout: 'card',
        styles: {
          backgroundColor: '#ffffff',
          textColor: '#333333',
          accentColor: '#4285f4',
          cardStyle: 'elevated',
          borderRadius: 12,
          showProgress: true,
          showTags: true,
          showDate: true,
        },
        fields: [
          {
            key: 'title',
            label: '标题',
            type: 'text',
            required: true,
            displayInCard: true,
            displayInDetail: true,
          },
          {
            key: 'description',
            label: '描述',
            type: 'text',
            required: true,
            displayInCard: true,
            displayInDetail: true,
          },
          {
            key: 'files',
            label: '文件',
            type: 'file',
            required: true,
            displayInCard: false,
            displayInDetail: true,
          },
        ],
      },
    ];

    return this.delayToObservable(templates);
  }

  /**
   * 获取模板详情
   */
  getTemplateById(id: number): Observable<AchievementTemplate> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    return this.getTemplates().pipe(
      map((templates) => {
        const template = templates.find((t) => t.id === id);
        if (!template) {
          throw new Error(`Template ${id} not found`);
        }
        return template;
      })
    );
  }

  /**
   * 创建成果模板
   */
  createTemplate(template: Partial<AchievementTemplate>): Observable<AchievementTemplate> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const newTemplate: AchievementTemplate = {
      id: Math.floor(Math.random() * 10000),
      name: template.name || '新模板',
      type: template.type || 'project',
      layout: template.layout || 'card',
      styles: template.styles || {
        backgroundColor: '#ffffff',
        textColor: '#333333',
        accentColor: '#4285f4',
        cardStyle: 'elevated',
        borderRadius: 12,
        showProgress: true,
        showTags: true,
        showDate: true,
      },
      fields: template.fields || [],
    };

    return this.delayToObservable(newTemplate);
  }

  /**
   * 更新成果模板
   */
  updateTemplate(
    id: number,
    template: Partial<AchievementTemplate>
  ): Observable<AchievementTemplate> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    return this.delayToObservable({
      id,
      name: template.name || '模板',
      type: template.type || 'project',
      layout: template.layout || 'card',
      styles: template.styles || {},
      fields: template.fields || [],
    } as AchievementTemplate);
  }

  /**
   * 删除成果模板
   */
  deleteTemplate(id: number): Observable<void> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    return this.delayToObservable(undefined);
  }

  /**
   * 获取用户的成果进度
   */
  getUserAchievementProgress(
    userId: number,
    courseId?: number,
    moduleId?: number
  ): Observable<AchievementProgress> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const progress = getMockUserProgress(userId);
    if (progress) {
      return this.delayToObservable(progress);
    }

    return this.createNotFoundError(`User ${userId} progress not found`);
  }

  /**
   * 获取成果统计信息
   */
  getAchievementStats(filter?: AchievementFilter): Observable<AchievementStats> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    return this.delayToObservable(getMockStats());
  }

  /**
   * 获取最近活动
   */
  getRecentActivity(limit = 10): Observable<AchievementActivity[]> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    return this.delayToObservable(getRecentActivity(limit));
  }

  /**
   * 获取课程相关的成果
   */
  getCourseAchievements(courseId: number, filter?: AchievementFilter): Observable<Achievement[]> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    // 模拟课程成果
    const courseAchievements = MOCK_ACHIEVEMENTS.filter((a) => a.id % 2 === 0);

    let filtered = [...courseAchievements];

    if (filter?.status && filter.status.length > 0) {
      filtered = filtered.filter((a) => filter.status!.includes(a.status));
    }

    if (filter?.type && filter.type.length > 0) {
      filtered = filtered.filter((a) => filter.type!.includes(a.type));
    }

    return this.delayToObservable(filtered);
  }

  /**
   * 获取模块相关的成果
   */
  getModuleAchievements(moduleId: number, filter?: AchievementFilter): Observable<Achievement[]> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const moduleAchievements = MOCK_ACHIEVEMENTS.filter((a) => a.moduleId === moduleId);

    let filtered = [...moduleAchievements];

    if (filter?.status && filter.status.length > 0) {
      filtered = filtered.filter((a) => filter.status!.includes(a.status));
    }

    if (filter?.type && filter.type.length > 0) {
      filtered = filtered.filter((a) => filter.type!.includes(a.type));
    }

    return this.delayToObservable(filtered);
  }

  /**
   * 获取课程章节相关的成果
   */
  getLessonAchievements(lessonId: number, filter?: AchievementFilter): Observable<Achievement[]> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    const lessonAchievements = MOCK_ACHIEVEMENTS.filter((a) => a.lessonId === lessonId);

    let filtered = [...lessonAchievements];

    if (filter?.status && filter.status.length > 0) {
      filtered = filtered.filter((a) => filter.status!.includes(a.status));
    }

    if (filter?.type && filter.type.length > 0) {
      filtered = filtered.filter((a) => filter.type!.includes(a.type));
    }

    return this.delayToObservable(filtered);
  }

  /**
   * 导出成果数据
   */
  exportAchievements(filter?: AchievementFilter, format = 'csv'): Observable<Blob> {
    if (!this.enabled) {
      return this.createErrorResponse('Mock data disabled');
    }

    // 模拟导出
    let filtered = [...MOCK_ACHIEVEMENTS];

    if (filter?.status && filter.status.length > 0) {
      filtered = filtered.filter((a) => filter.status!.includes(a.status));
    }

    const csv = this.convertToCSV(filtered);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });

    return this.delayToObservable(blob);
  }

  /**
   * 切换 Mock 服务状态
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  /**
   * 检查是否启用
   */
  isEnabled(): boolean {
    return this.enabled;
  }

  /**
   * 私有方法：转换筛选条件
   */
  private convertFilter(filter?: AchievementFilter):
    | {
        status?: string[];
        type?: string[];
      }
    | undefined {
    if (!filter) return undefined;

    const result: any = {};

    if (filter.status && filter.status.length > 0) {
      result.status = filter.status;
    }

    if (filter.type && filter.type.length > 0) {
      result.type = filter.type;
    }

    return result;
  }

  /**
   * 私有方法：转换数据为 CSV
   */
  private convertToCSV(achievements: Achievement[]): string {
    const headers = ['ID', 'UserID', 'Type', 'Title', 'Status', 'Score', 'SubmittedAt'];
    const rows = achievements.map((a) =>
      [a.id, a.userId, a.type, a.title, a.status, a.score || '', a.submittedAt].join(',')
    );

    return [headers.join(','), ...rows].join('\n');
  }

  /**
   * 私有方法：创建错误响应
   */
  private createErrorResponse<T>(message: string): Observable<T> {
    return throwError(() => new Error(message));
  }

  /**
   * 私有方法：创建404错误
   */
  private createNotFoundError<T>(message: string): Observable<T> {
    return throwError(() => {
      const error = new Error(message);
      (error as any).status = 404;
      return error;
    });
  }
}
