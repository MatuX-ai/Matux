/**
 * 家长模块模拟数据服务
 *
 * 提供家长用户中心相关的模拟数据，用于开发和测试
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { Injectable } from '@angular/core';
import { delay, Observable, of, throwError } from 'rxjs';

import {
  BindApplication,
  BindChildRequest,
  ChildDetail,
  ChildLearningStats,
  ChildProfile,
} from './children-management.service';
import {
  GradeLevel,
  LearningReport,
  LearningTrend,
  ReportListResponse,
} from './learning-reports.service';

/**
 * 孩子列表模拟数据
 */
const MOCK_CHILDREN: ChildProfile[] = [
  {
    id: 'child001',
    nickname: '小明',
    realName: '张小明',
    avatarUrl: '/assets/images/child-avatar-1.jpg',
    grade: '三年级',
    school: '阳光小学',
    phoneNumber: '138****1234',
    email: 'xiaoming@school.com',
    tags: ['积极', '爱学习'],
    bindTime: '2024-09-01T08:00:00',
    lastActiveTime: '2025-03-18T14:30:00',
    totalStudyTime: '128小时',
    completedCourses: 15,
    averageScore: 92,
    learningStreak: 7,
    learningSources: [
      {
        id: 'source001',
        name: '阳光小学',
        type: 'school_curriculum',
        progress: 85,
      },
      {
        id: 'source002',
        name: '数学兴趣班',
        type: 'school_interest',
        progress: 72,
      },
    ],
  },
  {
    id: 'child002',
    nickname: '小芳',
    realName: '李小芳',
    avatarUrl: '/assets/images/child-avatar-2.jpg',
    grade: '五年级',
    school: '阳光小学',
    phoneNumber: '139****5678',
    email: 'xiaofang@school.com',
    tags: ['专注', '细心'],
    bindTime: '2024-08-15T10:00:00',
    lastActiveTime: '2025-03-18T16:45:00',
    totalStudyTime: '156小时',
    completedCourses: 22,
    averageScore: 88,
    learningStreak: 12,
    learningSources: [
      {
        id: 'source003',
        name: '阳光小学',
        type: 'school_curriculum',
        progress: 92,
      },
      {
        id: 'source004',
        name: '英语兴趣班',
        type: 'school_interest',
        progress: 68,
      },
      {
        id: 'source005',
        name: '新东方少儿编程',
        type: 'org_course',
        progress: 45,
      },
    ],
  },
];

/**
 * 孩子详情模拟数据
 */
const MOCK_CHILD_DETAILS: Record<string, ChildDetail> = {
  child001: {
    id: 'child001',
    nickname: '小明',
    realName: '张小明',
    avatarUrl: '/assets/images/child-avatar-1.jpg',
    grade: '三年级',
    school: '阳光小学',
    phoneNumber: '138****1234',
    email: 'xiaoming@school.com',
    tags: ['积极', '爱学习', '乐于助人'],
    bindTime: '2024-09-01T08:00:00',
    lastActiveTime: '2025-03-18T14:30:00',
    totalStudyTime: '128小时',
    completedCourses: 15,
    averageScore: 92,
    learningStreak: 7,
    learningSources: [
      {
        id: 'source001',
        name: '阳光小学',
        type: 'school_curriculum',
        progress: 85,
      },
      {
        id: 'source002',
        name: '数学兴趣班',
        type: 'school_interest',
        progress: 72,
      },
    ],
  },
  child002: {
    id: 'child002',
    nickname: '小芳',
    realName: '李小芳',
    avatarUrl: '/assets/images/child-avatar-2.jpg',
    grade: '五年级',
    school: '阳光小学',
    phoneNumber: '139****5678',
    email: 'xiaofang@school.com',
    tags: ['专注', '细心', '勤奋'],
    bindTime: '2024-08-15T10:00:00',
    lastActiveTime: '2025-03-18T16:45:00',
    totalStudyTime: '156小时',
    completedCourses: 22,
    averageScore: 88,
    learningStreak: 12,
    learningSources: [
      {
        id: 'source003',
        name: '阳光小学',
        type: 'school_curriculum',
        progress: 92,
      },
      {
        id: 'source004',
        name: '英语兴趣班',
        type: 'school_interest',
        progress: 68,
      },
      {
        id: 'source005',
        name: '新东方少儿编程',
        type: 'org_course',
        progress: 45,
      },
    ],
  },
};

/**
 * 绑定申请模拟数据
 */
const MOCK_BINDING_REQUESTS: BindApplication[] = [
  {
    id: 'bind001',
    parentId: 'parent001',
    childId: 'child003',
    childName: '王小红',
    relationship: '父亲',
    status: 'pending',
    isIncoming: true,
    description: '家长账号绑定了孩子学号20230001',
    createdAt: '2025-03-15T09:30:00',
  },
  {
    id: 'bind002',
    parentId: 'parent001',
    childId: 'child004',
    childName: '李小刚',
    relationship: '母亲',
    status: 'approved',
    isIncoming: false,
    description: '通过邀请码绑定孩子',
    createdAt: '2025-02-20T14:00:00',
    processedAt: '2025-02-21T10:30:00',
  },
];

/**
 * 学习报告模拟数据
 */
const MOCK_LEARNING_REPORTS: LearningReport[] = [
  {
    id: 'report001',
    childId: 'child001',
    childName: '小明',
    reportType: 'monthly',
    title: '2025年3月学习报告',
    period: '2025-03-01 至 2025-03-31',
    startDate: '2025-03-01',
    endDate: '2025-03-31',
    generatedAt: '2025-04-01T08:00:00',
    status: 'published',
    totalStudyTime: '32小时',
    completedCourses: 5,
    completedHomeworks: 12,
    learningStreak: 7,
    averageScore: 92,
    sources: [
      { type: 'school_curriculum', name: '阳光小学' },
      { type: 'school_interest', name: '数学兴趣班' },
    ],
    courseGrades: [
      {
        courseId: 'course001',
        courseName: '数学-分数与百分数',
        score: 95,
        gradeLevel: 'excellent' as GradeLevel,
        completionStatus: 'completed',
        completedAt: '2025-03-20',
        teacherComment: '小明在分数计算方面表现出色，继续保持！',
      },
      {
        courseId: 'course002',
        courseName: '语文-古诗词鉴赏',
        score: 90,
        gradeLevel: 'good' as GradeLevel,
        completionStatus: 'completed',
        completedAt: '2025-03-25',
      },
      {
        courseId: 'course003',
        courseName: '英语-Unit 5',
        score: 88,
        gradeLevel: 'good' as GradeLevel,
        completionStatus: 'in_progress',
      },
    ],
    behaviorStats: {
      totalLearningMinutes: 1920,
      avgDailyLearningMinutes: 64,
      learningDays: 18,
      loginCount: 25,
      homeworkSubmitted: 12,
      questionsAsked: 8,
      discussionsParticipated: 5,
    },
    competencyAssessments: [
      {
        dimension: '逻辑思维',
        score: 9,
        level: '优秀',
      },
      {
        dimension: '语言表达',
        score: 8,
        level: '良好',
      },
      {
        dimension: '动手能力',
        score: 7,
        level: '良好',
        description: '建议多进行实际操作练习',
      },
    ],
    aiRecommendations: [
      '建议加强对英语词汇的日常积累',
      '可以适当增加数学应用题的练习量',
      '保持良好的学习习惯，继续保持！',
    ],
  },
  {
    id: 'report002',
    childId: 'child001',
    childName: '小明',
    reportType: 'monthly',
    title: '2025年2月学习报告',
    period: '2025-02-01 至 2025-02-28',
    startDate: '2025-02-01',
    endDate: '2025-02-28',
    generatedAt: '2025-03-01T08:00:00',
    status: 'published',
    totalStudyTime: '28小时',
    completedCourses: 4,
    completedHomeworks: 10,
    learningStreak: 5,
    averageScore: 89,
    sources: [{ type: 'school_curriculum', name: '阳光小学' }],
    courseGrades: [
      {
        courseId: 'course004',
        courseName: '数学-小数的认识',
        score: 92,
        gradeLevel: 'good' as GradeLevel,
        completionStatus: 'completed',
        completedAt: '2025-02-20',
      },
    ],
    aiRecommendations: ['继续保持学习热情', '多参与课堂互动'],
  },
  {
    id: 'report003',
    childId: 'child002',
    childName: '小芳',
    reportType: 'monthly',
    title: '2025年3月学习报告',
    period: '2025-03-01 至 2025-03-31',
    startDate: '2025-03-01',
    endDate: '2025-03-31',
    generatedAt: '2025-04-01T08:00:00',
    status: 'published',
    totalStudyTime: '35小时',
    completedCourses: 6,
    completedHomeworks: 15,
    learningStreak: 12,
    averageScore: 91,
    sources: [
      { type: 'school_curriculum', name: '阳光小学' },
      { type: 'school_interest', name: '英语兴趣班' },
      { type: 'org_course', name: '新东方少儿编程' },
    ],
    courseGrades: [
      {
        courseId: 'course005',
        courseName: '英语-Unit 8',
        score: 94,
        gradeLevel: 'excellent' as GradeLevel,
        completionStatus: 'completed',
        completedAt: '2025-03-28',
      },
      {
        courseId: 'course006',
        courseName: '编程-循环结构',
        score: 88,
        gradeLevel: 'good' as GradeLevel,
        completionStatus: 'completed',
        completedAt: '2025-03-25',
        teacherComment: '逻辑思维能力提升明显',
      },
    ],
    competencyAssessments: [
      {
        dimension: '编程思维',
        score: 8,
        level: '良好',
      },
      {
        dimension: '英语水平',
        score: 9,
        level: '优秀',
      },
    ],
    aiRecommendations: ['可以尝试更有挑战性的编程题目', '英语口语表达可以进一步加强'],
  },
];

/**
 * 学习趋势模拟数据
 */
const MOCK_LEARNING_TRENDS: Record<string, LearningTrend> = {
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

/**
 * 学习统计模拟数据
 */
const MOCK_LEARNING_STATS: Record<string, ChildLearningStats> = {
  child001: {
    childId: 'child001',
    totalCourses: 20,
    completedCourses: 15,
    totalLearningHours: 128,
    averageScore: 92,
    learningStreak: 7,
    badgeCount: 8,
  },
  child002: {
    childId: 'child002',
    totalCourses: 28,
    completedCourses: 22,
    totalLearningHours: 156,
    averageScore: 88,
    learningStreak: 12,
    badgeCount: 12,
  },
};

/**
 * 模拟数据服务
 */
@Injectable({
  providedIn: 'root',
})
export class MockParentDataService {
  constructor() {}

  /**
   * 获取孩子列表
   */
  getChildren(): Observable<ChildProfile[]> {
    return of(MOCK_CHILDREN).pipe(delay(500));
  }

  /**
   * 获取孩子详情
   */
  getChildDetail(childId: string): Observable<ChildDetail> {
    const child = MOCK_CHILD_DETAILS[childId];
    if (child) {
      return of(child).pipe(delay(300));
    }
    return throwError(() => new Error('孩子信息不存在'));
  }

  /**
   * 绑定孩子
   */
  bindChild(bindRequest: BindChildRequest): Observable<BindApplication> {
    const newApplication: BindApplication = {
      id: `bind${Date.now()}`,
      parentId: 'parent001',
      childId: bindRequest.childIdentifier,
      childName: '新绑定孩子',
      relationship: bindRequest.relationship,
      status: 'pending',
      isIncoming: false,
      description: `通过${bindRequest.relationship}关系绑定孩子`,
      createdAt: new Date().toISOString(),
    };
    MOCK_BINDING_REQUESTS.push(newApplication);
    return of(newApplication).pipe(delay(800));
  }

  /**
   * 解绑孩子
   */
  unbindChild(childId: string): Observable<{ message: string }> {
    const index = MOCK_CHILDREN.findIndex((c) => c.id === childId);
    if (index !== -1) {
      MOCK_CHILDREN.splice(index, 1);
      return of({ message: '解绑成功' }).pipe(delay(400));
    }
    return throwError(() => new Error('孩子不存在'));
  }

  /**
   * 获取绑定申请列表
   */
  getBindingRequests(): Observable<BindApplication[]> {
    return of(MOCK_BINDING_REQUESTS).pipe(delay(400));
  }

  /**
   * 同意/拒绝绑定申请
   */
  approveBindingRequest(applicationId: string, approve: boolean): Observable<{ message: string }> {
    const application = MOCK_BINDING_REQUESTS.find((r) => r.id === applicationId);
    if (application) {
      application.status = approve ? 'approved' : 'rejected';
      application.processedAt = new Date().toISOString();
      return of({
        message: approve ? '已同意绑定' : '已拒绝绑定',
      }).pipe(delay(500));
    }
    return throwError(() => new Error('申请不存在'));
  }

  /**
   * 取消绑定申请
   */
  cancelBindingRequest(applicationId: string): Observable<{ message: string }> {
    const index = MOCK_BINDING_REQUESTS.findIndex((r) => r.id === applicationId);
    if (index !== -1) {
      MOCK_BINDING_REQUESTS.splice(index, 1);
      return of({ message: '已取消申请' }).pipe(delay(400));
    }
    return throwError(() => new Error('申请不存在'));
  }

  /**
   * 搜索孩子
   */
  searchChildren(searchTerm: string): Observable<ChildProfile[]> {
    const results = MOCK_CHILDREN.filter(
      (child) =>
        child.id.includes(searchTerm) ||
        child.nickname.includes(searchTerm) ||
        child.realName?.includes(searchTerm)
    );
    return of(results).pipe(delay(300));
  }

  /**
   * 获取孩子学习统计
   */
  getChildLearningStats(childId: string): Observable<ChildLearningStats> {
    const stats = MOCK_LEARNING_STATS[childId];
    if (stats) {
      return of(stats).pipe(delay(300));
    }
    return throwError(() => new Error('学习统计数据不存在'));
  }

  /**
   * 批量获取孩子学习统计
   */
  getChildrenLearningStats(childIds: string[]): Observable<Record<string, ChildLearningStats>> {
    const statsMap: Record<string, ChildLearningStats> = {};
    childIds.forEach((id) => {
      const stats = MOCK_LEARNING_STATS[id];
      if (stats) {
        statsMap[id] = stats;
      }
    });
    return of(statsMap).pipe(delay(500));
  }

  /**
   * 获取学习报告列表
   */
  getReports(params: { childId?: string; reportType?: string }): Observable<ReportListResponse> {
    let filteredReports = [...MOCK_LEARNING_REPORTS];

    if (params.childId) {
      filteredReports = filteredReports.filter((r) => r.childId === params.childId);
    }

    if (params.reportType) {
      filteredReports = filteredReports.filter((r) => r.reportType === params.reportType);
    }

    return of({
      data: filteredReports,
      total: filteredReports.length,
      page: 1,
      limit: 20,
      totalPages: 1,
    }).pipe(delay(600));
  }

  /**
   * 获取单个学习报告详情
   */
  getReportDetail(reportId: string): Observable<LearningReport> {
    const report = MOCK_LEARNING_REPORTS.find((r) => r.id === reportId);
    if (report) {
      return of(report).pipe(delay(300));
    }
    return throwError(() => new Error('学习报告不存在'));
  }

  /**
   * 批量获取学习报告
   */
  getReportsBatch(reportIds: string[]): Observable<LearningReport[]> {
    const reports = MOCK_LEARNING_REPORTS.filter((r) => reportIds.includes(r.id));
    return of(reports).pipe(delay(500));
  }

  /**
   * 生成新的学习报告
   */
  generateReport(
    childId: string,
    reportType: 'weekly' | 'monthly' | 'quarterly' | 'custom',
    dateRange: { startDate: string; endDate: string }
  ): Observable<{ message: string; reportId: string }> {
    const child = MOCK_CHILDREN.find((c) => c.id === childId);
    if (!child) {
      return throwError(() => new Error('孩子不存在'));
    }

    const newReport: LearningReport = {
      id: `report${Date.now()}`,
      childId,
      childName: child.nickname,
      reportType,
      title: `${dateRange.endDate.substring(0, 10)}学习报告`,
      period: `${dateRange.startDate.substring(0, 10)} 至 ${dateRange.endDate.substring(0, 10)}`,
      startDate: dateRange.startDate,
      endDate: dateRange.endDate,
      generatedAt: new Date().toISOString(),
      status: 'published',
      totalStudyTime: '0小时',
      completedCourses: 0,
      completedHomeworks: 0,
      learningStreak: 0,
      averageScore: 0,
    };

    MOCK_LEARNING_REPORTS.unshift(newReport);

    return of({
      message: '报告生成成功',
      reportId: newReport.id,
    }).pipe(delay(1000));
  }

  /**
   * 获取学习趋势统计
   */
  getLearningTrend(childId: string, _days: number = 30): Observable<LearningTrend> {
    const trend = MOCK_LEARNING_TRENDS[childId];
    if (trend) {
      return of(trend).pipe(delay(500));
    }
    return throwError(() => new Error('学习趋势数据不存在'));
  }

  /**
   * 批量获取多个孩子的学习趋势
   */
  getLearningTrendBatch(
    childIds: string[],
    _days: number = 30
  ): Observable<Record<string, LearningTrend>> {
    const trendMap: Record<string, LearningTrend> = {};
    childIds.forEach((id) => {
      const trend = MOCK_LEARNING_TRENDS[id];
      if (trend) {
        trendMap[id] = trend;
      }
    });
    return of(trendMap).pipe(delay(800));
  }

  /**
   * 导出学习报告
   */
  exportReports(_exportRequest: { reportIds: string[] }): Observable<Blob> {
    // 模拟生成 PDF 文件
    const pdfContent = `学习报告导出\n报告数量：${_exportRequest.reportIds.length}\n生成时间：${new Date().toISOString()}`;
    const blob = new Blob([pdfContent], { type: 'application/pdf' });
    return of(blob).pipe(delay(1500));
  }

  /**
   * 导出单个学习报告
   */
  exportReport(reportId: string, format: 'pdf' | 'excel'): Observable<Blob> {
    const report = MOCK_LEARNING_REPORTS.find((r) => r.id === reportId);
    if (!report) {
      return throwError(() => new Error('学习报告不存在'));
    }

    const content =
      format === 'pdf'
        ? `PDF报告\n${report.title}\n${report.childName}\n${report.period}`
        : `Excel报告\n${report.title}\n${report.childName}\n${report.period}`;

    const mimeType = format === 'pdf' ? 'application/pdf' : 'application/vnd.ms-excel';
    const blob = new Blob([content], { type: mimeType });
    return of(blob).pipe(delay(1000));
  }

  /**
   * 分享学习报告
   */
  shareReport(
    _reportId: string,
    _expiresIn?: number
  ): Observable<{ shareUrl: string; shareCode: string }> {
    const shareCode = Math.random().toString(36).substring(2, 10).toUpperCase();
    const shareUrl = `${window.location.origin}/shared/reports/${shareCode}`;
    return of({
      shareUrl,
      shareCode,
    }).pipe(delay(400));
  }

  /**
   * 删除学习报告
   */
  deleteReport(reportId: string): Observable<{ message: string }> {
    const index = MOCK_LEARNING_REPORTS.findIndex((r) => r.id === reportId);
    if (index !== -1) {
      MOCK_LEARNING_REPORTS.splice(index, 1);
      return of({ message: '删除成功' }).pipe(delay(400));
    }
    return throwError(() => new Error('学习报告不存在'));
  }
}
