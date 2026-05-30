/**
 * 多来源学习关联管理服务
 * 提供学习来源、用户组织关联、统一学习记录等API调用
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

import {
  Course,
  CourseChapter,
  CourseLibraryResponse,
  Lesson,
} from '../../models/education-management.models';
import {
  LearningSource,
  LearningSourceCreate,
  LearningSourceListResponse,
  LearningSourceStats,
  LearningSourceUpdate,
  UnifiedLearningRecord,
  UnifiedLearningRecordCreate,
  UnifiedLearningRecordListResponse,
  UnifiedLearningRecordUpdate,
  UnifiedProgressStats,
  UserOrganization,
  UserOrganizationCreate,
  UserOrganizationListResponse,
  UserOrganizationStats,
  UserOrganizationUpdate,
} from '../../models/multi-source-learning.models';

@Injectable({
  providedIn: 'root',
})
export class MultiSourceLearningService {
  private readonly API_BASE = '/api/v1';

  constructor(private http: HttpClient) {}

  // ============ 课程库管理 ============

  /**
   * 获取课程库列表 (学生端)
   */
  getCourseLibrary(filters?: {
    search?: string;
    source_type?: 'school_curriculum' | 'school_interest' | 'institution';
    difficulty?: 'beginner' | 'intermediate' | 'advanced';
    page?: number;
    size?: number;
  }): Observable<CourseLibraryResponse> {
    let params = new HttpParams();

    if (filters?.search) {
      params = params.set('search', filters.search);
    }
    if (filters?.source_type) {
      params = params.set('source_type', filters.source_type);
    }
    if (filters?.difficulty) {
      params = params.set('difficulty', filters.difficulty);
    }
    if (filters?.page) {
      params = params.set('page', filters.page.toString());
    }
    if (filters?.size) {
      params = params.set('size', filters.size.toString());
    }

    const url = `${this.API_BASE}/courses/library`;
    return this.http.get<CourseLibraryResponse>(url, { params }).pipe(
      catchError((error) => {
        console.error('获取课程库失败:', error);
        // 返回模拟数据作为降级
        return of(this.getMockCourseLibrary());
      })
    );
  }

  /**
   * 获取课程详情
   */
  getCourseDetail(courseId: number): Observable<Course> {
    const url = `${this.API_BASE}/courses/${courseId}`;
    return this.http.get<Course>(url).pipe(
      catchError((error) => {
        console.error('获取课程详情失败:', error);
        // 返回模拟数据作为降级
        return of(this.getMockCourseDetail());
      })
    );
  }

  /**
   * 获取课程章节（包含课时列表）
   */
  getCourseChapters(courseId: number): Observable<CourseChapter[]> {
    const url = `${this.API_BASE}/courses/${courseId}/chapters`;
    return this.http.get<CourseChapter[]>(url).pipe(
      catchError((error) => {
        console.error('获取课程章节失败:', error);
        // 返回模拟数据作为降级
        return of(this.getMockCourseChapters(courseId));
      })
    );
  }

  /**
   * 报名课程
   */
  enrollCourse(courseId: number): Observable<{ success: boolean; message: string }> {
    const url = `${this.API_BASE}/courses/${courseId}/enroll`;
    return this.http.post<{ success: boolean; message: string }>(url, {}).pipe(
      catchError((error) => {
        console.error('报名课程失败:', error);
        return of({ success: false, message: '报名失败，请稍后重试' });
      })
    );
  }

  /**
   * 获取学生的学习进度
   */
  getStudentProgress(
    courseId: number
  ): Observable<{ progress: number; completed_lessons: number; total_lessons: number }> {
    const url = `${this.API_BASE}/courses/${courseId}/progress`;
    return this.http
      .get<{ progress: number; completed_lessons: number; total_lessons: number }>(url)
      .pipe(
        catchError((error) => {
          console.error('获取学习进度失败:', error);
          return of({ progress: 0, completed_lessons: 0, total_lessons: 0 });
        })
      );
  }

  /**
   * 模拟课程库数据 (降级用)
   */
  // eslint-disable-next-line max-lines-per-function
  private getMockCourseLibrary(): CourseLibraryResponse {
    return {
      courses: [
        this.createMockCourse(
          1,
          '高等数学 - 微积分基础',
          '高等数学',
          '系统讲解微积分的基础概念和应用，包括极限、导数、积分等内容',
          '张教授',
          '第一大学',
          'school_curriculum',
          'intermediate',
          64,
          32,
          256,
          4.8,
          ['数学', '微积分', '大学课程'],
          '2026-01-01T00:00:00Z',
          '2026-03-20T00:00:00Z'
        ),
        this.createMockCourse(
          2,
          '大学物理 - 力学篇',
          '大学物理',
          '深入探讨经典力学原理，包含运动学、动力学、能量守恒等核心内容',
          '李副教授',
          '第一大学',
          'school_curriculum',
          'intermediate',
          48,
          24,
          189,
          4.6,
          ['物理', '力学', '大学课程'],
          '2026-01-05T00:00:00Z',
          '2026-03-19T00:00:00Z'
        ),
        this.createMockCourse(
          3,
          'Python 编程入门',
          'Python 编程',
          '从零开始学习 Python 编程语言，掌握基础语法和实用技能',
          '王讲师',
          '创新编程培训中心',
          'institution',
          'beginner',
          32,
          16,
          423,
          4.9,
          ['编程', 'Python', '入门'],
          '2026-01-10T00:00:00Z',
          '2026-03-21T00:00:00Z'
        ),
        this.createMockCourse(
          4,
          '英语写作技巧提升',
          '英语写作',
          '提升英语写作能力，学习各种文体的写作技巧和表达方式',
          '赵老师',
          '第一大学',
          'school_interest',
          'intermediate',
          24,
          12,
          145,
          4.7,
          ['英语', '写作', '兴趣课程'],
          '2026-01-15T00:00:00Z',
          '2026-03-18T00:00:00Z'
        ),
        this.createMockCourse(
          5,
          '机器人设计与制作',
          '机器人设计',
          '学习机器人的基本原理、设计和制作方法，培养动手实践能力',
          '陈工程师',
          '青少年科技创新中心',
          'institution',
          'advanced',
          40,
          20,
          78,
          4.9,
          ['机器人', 'STEM', '创新'],
          '2026-01-20T00:00:00Z',
          '2026-03-22T00:00:00Z'
        ),
        this.createMockCourse(
          6,
          '化学实验基础',
          '化学实验',
          '掌握化学实验的基本操作和安全规范，进行有趣的化学实验',
          '刘教授',
          '第一大学',
          'school_curriculum',
          'beginner',
          32,
          16,
          203,
          4.5,
          ['化学', '实验', '基础'],
          '2026-01-25T00:00:00Z',
          '2026-03-17T00:00:00Z'
        ),
      ],
      total: 6,
      page: 1,
      page_size: 12,
      total_pages: 1,
    };
  }

  /**
   * 创建模拟课程数据
   */
  private createMockCourse(
    id: number,
    title: string,
    name: string,
    description: string,
    instructor_name: string,
    institution: string,
    source_type: 'school_curriculum' | 'school_interest' | 'institution',
    difficulty: 'beginner' | 'intermediate' | 'advanced',
    credit_hours: number,
    total_lessons: number,
    enrolled_students: number,
    rating: number,
    tags: string[],
    created_at: string,
    updated_at: string
  ): Course {
    return {
      id,
      org_id: source_type === 'institution' ? 2 : 1,
      title,
      name,
      description,
      instructor_name,
      institution,
      source_type,
      difficulty,
      level: difficulty,
      credit_hours,
      total_lessons,
      enrolled_students,
      current_students: enrolled_students,
      rating,
      thumbnail_url: '',
      tags,
      status: 'published',
      is_enrolled: false,
      student_progress: 0,
      created_at,
      updated_at,
    };
  }

  /**
   * 模拟课程详情数据 (降级用)
   */
  private getMockCourseDetail(): Course {
    return {
      id: 1,
      org_id: 1,
      title: '高等数学 - 微积分基础',
      name: '高等数学',
      description: '系统讲解微积分的基础概念和应用，包括极限、导数、积分等内容',
      instructor_name: '张教授',
      institution: '第一大学',
      source_type: 'school_curriculum',
      difficulty: 'intermediate',
      level: 'intermediate',
      credit_hours: 64,
      total_lessons: 32,
      enrolled_students: 256,
      current_students: 256,
      rating: 4.8,
      thumbnail_url: '',
      tags: ['数学', '微积分', '大学课程'],
      status: 'published',
      is_enrolled: false,
      student_progress: 0,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-03-20T00:00:00Z',
    };
  }

  /**
   * 模拟课程章节数据 (降级用)
   */
  private getMockCourseChapters(_courseId: number): CourseChapter[] {
    return [
      {
        id: 1,
        course_id: _courseId,
        title: '第一章：课程介绍与基础概念',
        description: '了解课程概述和核心概念',
        order_number: 1,
        lessons: [
          this.createMockLesson(1, 1, '课程导学', '课程目标和学习方法介绍', 'lecture', 15, true, 1),
          this.createMockLesson(2, 1, '核心概念解析', '深入理解关键概念', 'lecture', 30, false, 2),
        ],
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-03-20T00:00:00Z',
      },
      {
        id: 2,
        course_id: _courseId,
        title: '第二章：实践应用',
        description: '动手实践所学知识',
        order_number: 2,
        lessons: [
          this.createMockLesson(3, 2, '案例分析', '真实案例深度剖析', 'workshop', 45, false, 1),
          this.createMockLesson(4, 2, '实战练习', '独立完成实践项目', 'lab', 60, false, 2),
        ],
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-03-20T00:00:00Z',
      },
    ];
  }

  /**
   * 创建模拟课时数据
   */
  private createMockLesson(
    id: number,
    courseId: number,
    title: string,
    description: string,
    contentType: Lesson['content_type'],
    duration: number,
    isFreePreview: boolean,
    orderNumber: number
  ): Lesson {
    return {
      id,
      course_id: courseId,
      title,
      description,
      content_type: contentType,
      duration_minutes: duration,
      is_required: !isFreePreview,
      order_number: orderNumber,
      status: 'scheduled',
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-03-20T00:00:00Z',
    };
  }

  // ============ 学习来源管理 ============

  /**
   * 创建学习来源
   */
  createLearningSource(data: LearningSourceCreate): Observable<LearningSource> {
    const url = `${this.API_BASE}/learning-sources`;
    return this.http.post<LearningSource>(url, data);
  }

  /**
   * 获取学习来源详情
   */
  getLearningSource(sourceId: number): Observable<LearningSource> {
    const url = `${this.API_BASE}/learning-sources/${sourceId}`;
    return this.http.get<LearningSource>(url);
  }

  /**
   * 获取用户的学习来源列表
   */
  getUserLearningSources(
    userId: number,
    options?: {
      sourceType?: string;
      status?: string;
      includeInactive?: boolean;
    }
  ): Observable<LearningSourceListResponse> {
    let params = new HttpParams();
    if (options?.sourceType) {
      params = params.set('source_type', options.sourceType);
    }
    if (options?.status) {
      params = params.set('status', options.status);
    }
    if (options?.includeInactive) {
      params = params.set('include_inactive', 'true');
    }

    const url = `${this.API_BASE}/learning-sources/user/${userId}`;
    return this.http.get<LearningSourceListResponse>(url, { params });
  }

  /**
   * 更新学习来源
   */
  updateLearningSource(sourceId: number, data: LearningSourceUpdate): Observable<LearningSource> {
    const url = `${this.API_BASE}/learning-sources/${sourceId}`;
    return this.http.put<LearningSource>(url, data);
  }

  /**
   * 删除学习来源
   */
  deleteLearningSource(sourceId: number, soft: boolean = true): Observable<unknown> {
    const url = `${this.API_BASE}/learning-sources/${sourceId}`;
    return this.http.delete<unknown>(url, { params: { soft: soft.toString() } });
  }

  /**
   * 获取用户学习来源统计
   */
  getUserLearningSourceStats(userId: number): Observable<LearningSourceStats> {
    const url = `${this.API_BASE}/learning-sources/user/${userId}/stats`;
    return this.http.get<LearningSourceStats>(url);
  }

  // ============ 用户组织关联管理 ============

  /**
   * 创建用户-组织关联
   */
  createUserOrganization(data: UserOrganizationCreate): Observable<UserOrganization> {
    const url = `${this.API_BASE}/user-organizations`;
    return this.http.post<UserOrganization>(url, data);
  }

  /**
   * 获取用户-组织关联详情
   */
  getUserOrganization(orgRelId: number): Observable<UserOrganization> {
    const url = `${this.API_BASE}/user-organizations/${orgRelId}`;
    return this.http.get<UserOrganization>(url);
  }

  /**
   * 获取用户的所有组织关联
   */
  getUserOrganizations(
    userId: number,
    options?: {
      role?: string;
      status?: string;
      includeInactive?: boolean;
    }
  ): Observable<UserOrganizationListResponse> {
    let params = new HttpParams();
    if (options?.role) {
      params = params.set('role', options.role);
    }
    if (options?.status) {
      params = params.set('status', options.status);
    }
    if (options?.includeInactive) {
      params = params.set('include_inactive', 'true');
    }

    const url = `${this.API_BASE}/user-organizations/user/${userId}`;
    return this.http.get<UserOrganizationListResponse>(url, { params });
  }

  /**
   * 获取组织的所有用户
   */
  getOrganizationUsers(
    orgId: number,
    options?: {
      role?: string;
      status?: string;
    }
  ): Observable<UserOrganizationListResponse> {
    let params = new HttpParams();
    if (options?.role) {
      params = params.set('role', options.role);
    }
    if (options?.status) {
      params = params.set('status', options.status);
    }

    const url = `${this.API_BASE}/user-organizations/org/${orgId}`;
    return this.http.get<UserOrganizationListResponse>(url, { params });
  }

  /**
   * 更新用户-组织关联
   */
  updateUserOrganization(
    orgRelId: number,
    data: UserOrganizationUpdate
  ): Observable<UserOrganization> {
    const url = `${this.API_BASE}/user-organizations/${orgRelId}`;
    return this.http.put<UserOrganization>(url, data);
  }

  /**
   * 删除用户-组织关联
   */
  deleteUserOrganization(orgRelId: number, soft: boolean = true): Observable<unknown> {
    const url = `${this.API_BASE}/user-organizations/${orgRelId}`;
    return this.http.delete<unknown>(url, { params: { soft: soft.toString() } });
  }

  /**
   * 设置用户主组织
   */
  setPrimaryOrganization(userId: number, orgId: number): Observable<UserOrganization> {
    const url = `${this.API_BASE}/user-organizations/user/${userId}/set-primary/${orgId}`;
    return this.http.post<UserOrganization>(url, {});
  }

  /**
   * 获取用户主组织
   */
  getUserPrimaryOrganization(userId: number): Observable<UserOrganization> {
    const url = `${this.API_BASE}/user-organizations/user/${userId}/primary`;
    return this.http.get<UserOrganization>(url);
  }

  /**
   * 获取用户组织统计
   */
  getUserOrganizationStats(userId: number): Observable<UserOrganizationStats> {
    const url = `${this.API_BASE}/user-organizations/user/${userId}/stats`;
    return this.http.get<UserOrganizationStats>(url);
  }

  // ============ 统一学习记录管理 ============

  /**
   * 创建统一学习记录
   */
  createUnifiedLearningRecord(
    data: UnifiedLearningRecordCreate
  ): Observable<UnifiedLearningRecord> {
    const url = `${this.API_BASE}/unified-learning-records`;
    return this.http.post<UnifiedLearningRecord>(url, data);
  }

  /**
   * 获取统一学习记录详情
   */
  getUnifiedLearningRecord(recordId: number): Observable<UnifiedLearningRecord> {
    const url = `${this.API_BASE}/unified-learning-records/${recordId}`;
    return this.http.get<UnifiedLearningRecord>(url);
  }

  /**
   * 获取用户的统一学习记录列表
   */
  getUserUnifiedLearningRecords(
    userId: number,
    options?: {
      learningSourceId?: number;
      courseId?: number;
      status?: string;
    }
  ): Observable<UnifiedLearningRecordListResponse> {
    let params = new HttpParams();
    if (options?.learningSourceId) {
      params = params.set('learning_source_id', options.learningSourceId.toString());
    }
    if (options?.courseId) {
      params = params.set('course_id', options.courseId.toString());
    }
    if (options?.status) {
      params = params.set('status', options.status);
    }

    const url = `${this.API_BASE}/unified-learning-records/user/${userId}`;
    return this.http.get<UnifiedLearningRecordListResponse>(url, { params });
  }

  /**
   * 更新统一学习记录
   */
  updateUnifiedLearningRecord(
    recordId: number,
    data: UnifiedLearningRecordUpdate
  ): Observable<UnifiedLearningRecord> {
    const url = `${this.API_BASE}/unified-learning-records/${recordId}`;
    return this.http.put<UnifiedLearningRecord>(url, data);
  }

  /**
   * 删除统一学习记录
   */
  deleteUnifiedLearningRecord(recordId: number, soft: boolean = true): Observable<unknown> {
    const url = `${this.API_BASE}/unified-learning-records/${recordId}`;
    return this.http.delete<unknown>(url, { params: { soft: soft.toString() } });
  }

  /**
   * 获取用户跨来源学习进度统计
   */
  getUserUnifiedProgress(userId: number): Observable<UnifiedProgressStats> {
    const url = `${this.API_BASE}/unified-learning/progress/${userId}`;
    return this.http.get<UnifiedProgressStats>(url);
  }
}
