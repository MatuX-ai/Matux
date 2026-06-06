/**
 * 学习报告服务
 *
 * 提供家长查看孩子学习报告相关的 HTTP 请求服务，包括：
 * - 获取学习报告列表
 * - 获取报告详情
 * - 获取学习统计数据
 * - 导出报告
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { delay, Observable, of, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

/**
 * 是否使用模拟数据
 */
const USE_MOCK_DATA = true;

/**
 * 报告类型
 */
export type ReportType = 'weekly' | 'monthly' | 'quarterly' | 'custom';

/**
 * 报告状态
 */
export type ReportStatus = 'draft' | 'published' | 'archived';

/**
 * 成绩等级
 */
export type GradeLevel = 'excellent' | 'good' | 'average' | 'needs_improvement';

/**
 * 报告筛选器
 */
export interface ReportFilter {
  childId: string | null;
  sourceType: string | null;
  startDate: Date | null;
  endDate: Date | null;
}

/**
 * 学习趋势
 */
export interface LearningTrend {
  childId: string;
  totalStudyTime: string;
  completedCourses: number;
  averageScore: number;
  learningStreak: number;
  chartData: Array<{
    date: string;
    studyMinutes: number;
    score: number;
  }>;
}

/**
 * 课程成绩
 */
export interface CourseGrade {
  courseId: string;
  courseName: string;
  score: number;
  gradeLevel: GradeLevel;
  completionStatus: 'completed' | 'in_progress' | 'not_started';
  completedAt?: string;
  teacherComment?: string;
}

/**
 * 学习行为统计
 */
export interface LearningBehaviorStats {
  totalLearningMinutes: number;
  avgDailyLearningMinutes: number;
  learningDays: number;
  loginCount: number;
  homeworkSubmitted: number;
  questionsAsked: number;
  discussionsParticipated: number;
}

/**
 * 能力评估
 */
export interface CompetencyAssessment {
  dimension: string;
  score: number;
  level: string;
  description?: string;
}

/**
 * 学习报告
 */
export interface LearningReport {
  id: string;
  childId: string;
  childName: string;
  reportType: ReportType;
  title: string;
  period: string;
  startDate: string;
  endDate: string;
  generatedAt: string;
  status: ReportStatus;
  totalStudyTime: string;
  completedCourses: number;
  completedHomeworks: number;
  learningStreak: number;
  averageScore: number;
  sources?: Array<{
    type: string;
    name: string;
  }>;
  courseGrades?: CourseGrade[];
  behaviorStats?: LearningBehaviorStats;
  competencyAssessments?: CompetencyAssessment[];
  teacherComments?: string;
  aiRecommendations?: string[];
}

/**
 * 学习报告查询参数
 */
export interface ReportQueryParams {
  childId?: string;
  reportType?: ReportType;
  startDate?: string;
  endDate?: string;
  page?: number;
  limit?: number;
  sortBy?: 'generatedAt' | 'startDate';
  sortOrder?: 'asc' | 'desc';
}

/**
 * 学习报告列表响应
 */
export interface ReportListResponse {
  data: LearningReport[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}

/**
 * 导出格式
 */
export type ExportFormat = 'pdf' | 'excel' | 'csv';

/**
 * 导出请求
 */
export interface ExportReportRequest {
  reportIds: string[];
  format: ExportFormat;
}

/**
 * 学习报告服务
 */
@Injectable({
  providedIn: 'root',
})
export class LearningReportsService {
  private readonly API_BASE_URL = '/api/parent/reports';

  constructor(private http: HttpClient) {}

  /**
   * 获取学习报告列表
   * @param params 查询参数
   */
  // eslint-disable-next-line max-lines-per-function
  getReports(params: ReportQueryParams): Observable<ReportListResponse> {
    if (USE_MOCK_DATA) {
      const mockReports: LearningReport[] = [
        {
          id: 'report001',
          childId: 'child001',
          childName: '小明',
          reportType: 'monthly',
          title: '2025年3月学习报告',
          period: '2025年3月',
          startDate: '2025-03-01',
          endDate: '2025-03-31',
          generatedAt: '2025-03-18T17:00:00',
          status: 'published',
          totalStudyTime: '32小时',
          completedCourses: 5,
          completedHomeworks: 20,
          learningStreak: 7,
          averageScore: 92,
          sources: [
            { type: 'school_curriculum', name: '阳光小学' },
            { type: 'school_interest', name: '数学兴趣班' },
          ],
          courseGrades: [
            {
              courseId: 'course001',
              courseName: '数学基础',
              score: 95,
              gradeLevel: 'excellent',
              completionStatus: 'completed',
              completedAt: '2025-03-15T10:00:00',
              teacherComment: '表现优秀，继续保持',
            },
            {
              courseId: 'course002',
              courseName: '语文阅读',
              score: 88,
              gradeLevel: 'good',
              completionStatus: 'completed',
              completedAt: '2025-03-14T15:30:00',
              teacherComment: '理解能力较好，需要多练习',
            },
            {
              courseId: 'course003',
              courseName: '英语口语',
              score: 90,
              gradeLevel: 'good',
              completionStatus: 'in_progress',
            },
          ],
          behaviorStats: {
            totalLearningMinutes: 1920,
            avgDailyLearningMinutes: 64,
            learningDays: 30,
            loginCount: 45,
            homeworkSubmitted: 20,
            questionsAsked: 15,
            discussionsParticipated: 8,
          },
          competencyAssessments: [
            { dimension: '逻辑思维', score: 92, level: '优秀', description: '逻辑推理能力强' },
            { dimension: '语言表达', score: 88, level: '良好', description: '表达能力有待提高' },
            { dimension: '创新思维', score: 90, level: '优秀', description: '富有创意' },
          ],
          teacherComments: '小明本月学习表现优秀，各科目成绩均衡。建议继续加强英语口语练习。',
          aiRecommendations: [
            '建议增加英语口语练习时间',
            '可以尝试一些编程课程培养逻辑思维',
            '保持良好的学习习惯',
          ],
        },
        {
          id: 'report002',
          childId: 'child002',
          childName: '小芳',
          reportType: 'monthly',
          title: '2025年3月学习报告',
          period: '2025年3月',
          startDate: '2025-03-01',
          endDate: '2025-03-31',
          generatedAt: '2025-03-18T17:00:00',
          status: 'published',
          totalStudyTime: '35小时',
          completedCourses: 6,
          completedHomeworks: 25,
          learningStreak: 12,
          averageScore: 91,
          sources: [
            { type: 'school_curriculum', name: '阳光小学' },
            { type: 'school_interest', name: '英语兴趣班' },
            { type: 'org_course', name: '新东方少儿编程' },
          ],
          courseGrades: [
            {
              courseId: 'course004',
              courseName: '数学进阶',
              score: 92,
              gradeLevel: 'excellent',
              completionStatus: 'completed',
              completedAt: '2025-03-16T10:00:00',
              teacherComment: '进步明显',
            },
            {
              courseId: 'course005',
              courseName: '英语听说',
              score: 90,
              gradeLevel: 'good',
              completionStatus: 'completed',
              completedAt: '2025-03-15T14:00:00',
            },
          ],
          behaviorStats: {
            totalLearningMinutes: 2100,
            avgDailyLearningMinutes: 70,
            learningDays: 30,
            loginCount: 50,
            homeworkSubmitted: 25,
            questionsAsked: 20,
            discussionsParticipated: 12,
          },
          competencyAssessments: [
            { dimension: '逻辑思维', score: 90, level: '优秀' },
            { dimension: '语言表达', score: 92, level: '优秀' },
            { dimension: '创新思维', score: 88, level: '良好' },
          ],
          teacherComments: '小芳学习态度认真，各科目都有不错的表现。建议多参与课堂讨论。',
          aiRecommendations: ['可以尝试更具挑战性的数学题目', '继续保持良好的学习习惯'],
        },
        {
          id: 'report003',
          childId: 'child001',
          childName: '小明',
          reportType: 'weekly',
          title: '2025年第11周学习报告',
          period: '2025年第11周',
          startDate: '2025-03-10',
          endDate: '2025-03-16',
          generatedAt: '2025-03-17T09:00:00',
          status: 'published',
          totalStudyTime: '8小时',
          completedCourses: 2,
          completedHomeworks: 5,
          learningStreak: 7,
          averageScore: 90,
          sources: [{ type: 'school_curriculum', name: '阳光小学' }],
          courseGrades: [
            {
              courseId: 'course001',
              courseName: '数学基础',
              score: 90,
              gradeLevel: 'good',
              completionStatus: 'completed',
              completedAt: '2025-03-14T10:00:00',
            },
          ],
          teacherComments: '本周学习进度正常，建议保持。',
          aiRecommendations: ['适当增加练习时间'],
        },
      ];

      // 筛选
      let filteredReports = mockReports;
      if (params.childId) {
        filteredReports = filteredReports.filter((r) => r.childId === params.childId);
      }
      if (params.reportType) {
        filteredReports = filteredReports.filter((r) => r.reportType === params.reportType);
      }

      return of({
        data: filteredReports,
        total: filteredReports.length,
        page: params.page ?? 1,
        limit: params.limit ?? 20,
        totalPages: 1,
      }).pipe(delay(100));
    }
    return this.http
      .get<ReportListResponse>(`${this.API_BASE_URL}`, {
        params: Object.entries(params ?? {}).reduce((p, [key, value]) => {
          if (value !== undefined && value !== null) {
            return p.set(key, String(value));
          }
          return p;
        }, new HttpParams()),
      })
      .pipe(catchError(this.handleError));
  }

  /**
   * 获取单个学习报告详情
   * @param reportId 报告ID
   */
  getReportDetail(reportId: string): Observable<LearningReport> {
    return this.http
      .get<LearningReport>(`${this.API_BASE_URL}/${reportId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * 批量获取学习报告
   * @param reportIds 报告ID列表
   */
  getReportsBatch(reportIds: string[]): Observable<LearningReport[]> {
    return this.http
      .post<LearningReport[]>(`${this.API_BASE_URL}/batch`, { reportIds })
      .pipe(catchError(this.handleError));
  }

  /**
   * 生成新的学习报告
   * @param childId 孩子ID
   * @param reportType 报告类型
   * @param dateRange 日期范围
   */
  generateReport(
    childId: string,
    reportType: ReportType,
    dateRange: { startDate: string; endDate: string }
  ): Observable<{ message: string; reportId: string }> {
    return this.http
      .post<{ message: string; reportId: string }>(`${this.API_BASE_URL}/generate`, {
        childId,
        reportType,
        dateRange,
      })
      .pipe(catchError(this.handleError));
  }

  /**
   * 获取学习趋势统计
   * @param childId 孩子ID
   * @param days 统计天数（默认30天）
   */
  getLearningTrend(childId: string, days: number = 30): Observable<LearningTrend> {
    if (USE_MOCK_DATA) {
      const mockTrends: Record<string, LearningTrend> = {
        child001: {
          childId: 'child001',
          totalStudyTime: '32小时',
          completedCourses: 5,
          averageScore: 92,
          learningStreak: 7,
          chartData: Array.from({ length: 30 }, (_, i) => ({
            date: `2025-03-${(i + 1).toString().padStart(2, '0')}`,
            studyMinutes: Math.floor(Math.random() * 90) + 30,
            score: Math.floor(Math.random() * 20) + 80,
          })),
        },
        child002: {
          childId: 'child002',
          totalStudyTime: '35小时',
          completedCourses: 6,
          averageScore: 91,
          learningStreak: 12,
          chartData: Array.from({ length: 30 }, (_, i) => ({
            date: `2025-03-${(i + 1).toString().padStart(2, '0')}`,
            studyMinutes: Math.floor(Math.random() * 120) + 40,
            score: Math.floor(Math.random() * 20) + 81,
          })),
        },
      };

      const trend = mockTrends[childId];
      if (trend) {
        return of(trend).pipe(delay(500));
      }
      return throwError(() => new Error('学习趋势数据不存在'));
    }
    return this.http
      .get<LearningTrend>(`${this.API_BASE_URL}/trend/${childId}`, {
        params: { days: days.toString() },
      })
      .pipe(catchError(this.handleError));
  }

  /**
   * 批量获取多个孩子的学习趋势
   * @param childIds 孩子ID列表
   * @param days 统计天数（默认30天）
   */
  getLearningTrendBatch(
    childIds: string[],
    days: number = 30
  ): Observable<Record<string, LearningTrend>> {
    return this.http
      .post<Record<string, LearningTrend>>(`${this.API_BASE_URL}/trend/batch`, {
        childIds,
        days,
      })
      .pipe(catchError(this.handleError));
  }

  /**
   * 导出学习报告
   * @param exportRequest 导出请求
   */
  exportReports(exportRequest: ExportReportRequest): Observable<Blob> {
    return this.http
      .post(`${this.API_BASE_URL}/export`, exportRequest, {
        responseType: 'blob',
      })
      .pipe(catchError(this.handleError));
  }

  /**
   * 导出单个学习报告
   * @param reportId 报告ID
   * @param format 导出格式
   */
  exportReport(reportId: string, format: 'pdf' | 'excel'): Observable<Blob> {
    return this.http
      .post(
        `${this.API_BASE_URL}/${reportId}/export`,
        { format },
        {
          responseType: 'blob',
        }
      )
      .pipe(catchError(this.handleError));
  }

  /**
   * 分享学习报告
   * @param reportId 报告ID
   * @param expiresIn 有效期（小时，可选）
   */
  shareReport(
    reportId: string,
    expiresIn?: number
  ): Observable<{ shareUrl: string; shareCode: string }> {
    const params: { [key: string]: number } = {};
    if (expiresIn) {
      params['expiresIn'] = expiresIn;
    }

    return this.http
      .post<{
        shareUrl: string;
        shareCode: string;
      }>(`${this.API_BASE_URL}/${reportId}/share`, {}, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * 删除学习报告
   * @param reportId 报告ID
   */
  deleteReport(reportId: string): Observable<{ message: string }> {
    return this.http
      .delete<{ message: string }>(`${this.API_BASE_URL}/${reportId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * 错误处理
   * @param error HTTP 错误响应
   */
  // eslint-disable-next-line complexity
  private handleError = (error: unknown): Observable<never> => {
    const httpError = error as { error?: ErrorEvent | { message?: string }; status?: number };
    let errorMessage = '操作失败';

    if (httpError.error instanceof ErrorEvent) {
      errorMessage = `客户端错误: ${httpError.error.message}`;
    } else {
      if (httpError.status === 400) {
        errorMessage = httpError.error?.message ?? '请求参数错误';
      } else if (httpError.status === 401) {
        errorMessage = '未授权，请重新登录';
      } else if (httpError.status === 403) {
        errorMessage = '无权查看此报告';
      } else if (httpError.status === 404) {
        errorMessage = '学习报告不存在';
      } else if (httpError.status === 422) {
        errorMessage = httpError.error?.message ?? '数据验证失败';
      } else if (httpError.status === 500) {
        errorMessage = '服务器错误，请稍后重试';
      } else {
        errorMessage = httpError.error?.message ?? `错误码: ${httpError.status}`;
      }
    }

    console.error('LearningReportsService Error:', error);
    return throwError(() => new Error(errorMessage));
  };
}
