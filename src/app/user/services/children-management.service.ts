/**
 * 孩子管理服务
 *
 * 提供家长管理孩子相关的 HTTP 请求服务，包括：
 * - 获取孩子列表
 * - 绑定孩子
 * - 解绑孩子
 * - 查询绑定申请状态
 * - 获取孩子详情
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { delay, Observable, of, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

/**
 * 是否使用模拟数据
 */
const USE_MOCK_DATA = true;

/**
 * 孩子学习信息
 */
export interface ChildLearningInfo {
  /** 学习来源类型 */
  learningSourceType: string;
  /** 学习来源名称 */
  learningSourceName: string;
  /** 课程数量 */
  courseCount: number;
  /** 已完成课程数 */
  completedCourseCount: number;
  /** 学习时长（小时） */
  totalLearningHours: number;
  /** 平均成绩 */
  averageScore?: number;
  /** 最近学习时间 */
  lastLearningAt?: string;
}

/**
 * 孩子详细信息
 */
export interface ChildDetail {
  /** 孩子ID */
  id: string;
  /** 昵称 */
  nickname: string;
  /** 真实姓名 */
  realName?: string;
  /** 头像URL */
  avatarUrl?: string;
  /** 年级 */
  grade?: string;
  /** 学校 */
  school?: string;
  /** 联系电话 */
  phoneNumber?: string;
  /** 邮箱 */
  email?: string;
  /** 标签 */
  tags?: string[];
  /** 绑定时间 */
  bindTime: string;
  /** 最近活跃时间 */
  lastActiveTime?: string;
  /** 总学习时长 */
  totalStudyTime?: string;
  /** 完成课程数 */
  completedCourses?: number;
  /** 平均分数 */
  averageScore?: number;
  /** 连续学习天数 */
  learningStreak?: number;
  /** 学习来源 */
  learningSources?: Array<{
    id: string;
    name: string;
    type: string;
    progress: number;
  }>;
}

/**
 * 绑定孩子请求
 */
export interface BindChildRequest {
  /** 孩子学号或用户ID */
  childIdentifier: string;
  /** 关系描述（如：父亲、母亲、监护人） */
  relationship: string;
  /** 验证信息（如：孩子姓名、手机号） */
  verificationInfo?: string;
}

/**
 * 绑定申请状态
 */
export type BindingStatus = 'pending' | 'approved' | 'rejected' | 'cancelled';

/**
 * 绑定申请记录
 */
export interface BindApplication {
  /** 申请ID */
  id: string;
  /** 家长ID */
  parentId: string;
  /** 孩子ID */
  childId: string;
  /** 孩子姓名 */
  childName: string;
  /** 关系 */
  relationship: string;
  /** 申请状态 */
  status: BindingStatus;
  /** 是否是接收的申请 */
  isIncoming: boolean;
  /** 申请描述 */
  description?: string;
  /** 申请时间 */
  createdAt: string;
  /** 处理时间 */
  processedAt?: string;
  /** 拒绝原因 */
  rejectionReason?: string;
}

/**
 * 孩子基本信息（用于列表展示）
 */
export interface ChildProfile {
  id: string;
  nickname: string;
  realName?: string;
  avatarUrl?: string;
  grade?: string;
  school?: string;
  phoneNumber?: string;
  email?: string;
  tags?: string[];
  bindTime: string;
  lastActiveTime?: string;
  totalStudyTime?: string;
  completedCourses?: number;
  averageScore?: number;
  learningStreak?: number;
  learningSources?: Array<{
    id: string;
    name: string;
    type: string;
    progress: number;
  }>;
}

/**
 * 孩子学习统计
 */
export interface ChildLearningStats {
  /** 孩子ID */
  childId: string;
  /** 总课程数 */
  totalCourses: number;
  /** 已完成课程数 */
  completedCourses: number;
  /** 总学习时长（小时） */
  totalLearningHours: number;
  /** 平均成绩 */
  averageScore: number;
  /** 学习连续天数 */
  learningStreak: number;
  /** 获得徽章数 */
  badgeCount: number;
}

/**
 * 孩子管理服务
 */
@Injectable({
  providedIn: 'root',
})
export class ChildrenManagementService {
  private readonly API_BASE_URL = '/api/parent/children';

  constructor(private http: HttpClient) {}

  /**
   * 获取家长绑定的孩子列表
   */
  getChildren(): Observable<ChildDetail[]> {
    if (USE_MOCK_DATA) {
      const mockChildren: ChildDetail[] = [
        {
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
        {
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
      ];
      return of(mockChildren).pipe(delay(100));
    }
    return this.http.get<ChildDetail[]>(`${this.API_BASE_URL}`).pipe(catchError(this.handleError));
  }

  /**
   * 获取孩子详情
   * @param childId 孩子ID
   */
  getChildDetail(childId: string): Observable<ChildDetail> {
    if (USE_MOCK_DATA) {
      const mockChildren: Record<string, ChildDetail> = {
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
      const child = mockChildren[childId];
      if (child) {
        return of(child).pipe(delay(300));
      }
      return throwError(() => new Error('孩子信息不存在'));
    }
    return this.http
      .get<ChildDetail>(`${this.API_BASE_URL}/${childId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * 通过邀请码绑定孩子
   * @param inviteCode 邀请码
   */
  bindChildByInviteCode(inviteCode: string): Observable<BindApplication> {
    return this.http
      .post<BindApplication>(`${this.API_BASE_URL}/bind/invite`, { inviteCode })
      .pipe(catchError(this.handleError));
  }

  /**
   * 绑定孩子
   * @param bindRequest 绑定请求
   */
  bindChild(bindRequest: BindChildRequest): Observable<BindApplication> {
    return this.http
      .post<BindApplication>(`${this.API_BASE_URL}/bind`, bindRequest)
      .pipe(catchError(this.handleError));
  }

  /**
   * 解绑孩子
   * @param childId 孩子ID
   */
  unbindChild(childId: string): Observable<{ message: string }> {
    return this.http
      .delete<{ message: string }>(`${this.API_BASE_URL}/${childId}/unbind`)
      .pipe(catchError(this.handleError));
  }

  /**
   * 获取绑定申请列表
   */
  getBindingRequests(): Observable<BindApplication[]> {
    if (USE_MOCK_DATA) {
      const mockRequests: BindApplication[] = [
        {
          id: 'app001',
          parentId: 'user001',
          childId: 'child003',
          childName: '王小红',
          relationship: '母亲',
          status: 'pending',
          isIncoming: true,
          description: '通过学号绑定',
          createdAt: '2025-03-18T10:00:00',
          processedAt: undefined,
          rejectionReason: undefined,
        },
      ];
      return of(mockRequests).pipe(delay(300));
    }
    return this.http
      .get<BindApplication[]>(`${this.API_BASE_URL}/applications`)
      .pipe(catchError(this.handleError));
  }

  /**
   * 同意/拒绝绑定申请
   * @param applicationId 申请ID
   * @param approve 是否同意
   */
  approveBindingRequest(applicationId: string, approve: boolean): Observable<{ message: string }> {
    return this.http
      .post<{ message: string }>(`${this.API_BASE_URL}/applications/${applicationId}/respond`, {
        approve,
      })
      .pipe(catchError(this.handleError));
  }

  /**
   * 取消绑定申请
   * @param applicationId 申请ID
   */
  cancelBindingRequest(applicationId: string): Observable<{ message: string }> {
    return this.http
      .post<{ message: string }>(`${this.API_BASE_URL}/applications/${applicationId}/cancel`, {})
      .pipe(catchError(this.handleError));
  }

  /**
   * 搜索孩子（用于绑定）
   * @param searchTerm 搜索关键词（学号、手机号或姓名）
   */
  searchChildren(searchTerm: string): Observable<ChildProfile[]> {
    return this.http
      .get<ChildProfile[]>(`${this.API_BASE_URL}/search`, {
        params: { q: searchTerm },
      })
      .pipe(catchError(this.handleError));
  }

  /**
   * 获取孩子学习统计
   * @param childId 孩子ID
   */
  getChildLearningStats(childId: string): Observable<ChildLearningStats> {
    return this.http
      .get<ChildLearningStats>(`${this.API_BASE_URL}/${childId}/stats`)
      .pipe(catchError(this.handleError));
  }

  /**
   * 批量获取孩子学习统计
   * @param childIds 孩子ID列表
   */
  getChildrenLearningStats(childIds: string[]): Observable<Record<string, ChildLearningStats>> {
    return this.http
      .post<Record<string, ChildLearningStats>>(`${this.API_BASE_URL}/stats/batch`, {
        childIds,
      })
      .pipe(catchError(this.handleError));
  }

  /**
   * 错误处理
   * @param error HTTP 错误响应
   */
  private handleError(error: any): Observable<never> {
    let errorMessage = '操作失败';

    if (error.error instanceof ErrorEvent) {
      // 客户端错误
      errorMessage = `客户端错误: ${error.error.message}`;
    } else {
      // 服务端错误
      if (error.status === 400) {
        errorMessage = error.error?.message || '请求参数错误';
      } else if (error.status === 401) {
        errorMessage = '未授权，请重新登录';
      } else if (error.status === 403) {
        errorMessage = '无权执行此操作';
      } else if (error.status === 404) {
        errorMessage = '孩子信息不存在';
      } else if (error.status === 409) {
        errorMessage = error.error?.message || '孩子已绑定或存在冲突';
      } else if (error.status === 422) {
        errorMessage = error.error?.message || '验证信息不正确';
      } else if (error.status === 500) {
        errorMessage = '服务器错误，请稍后重试';
      } else {
        errorMessage = error.error?.message || `错误码: ${error.status}`;
      }
    }

    console.error('ChildrenManagementService Error:', error);
    return throwError(() => new Error(errorMessage));
  }
}
