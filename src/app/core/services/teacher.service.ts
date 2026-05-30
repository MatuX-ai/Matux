/**
 * @deprecated 教师管理功能属于机构端，将逐步迁移到 OpenMTEduInst 子项目。
 * 当前保留用于 iMato 学习端的教师数据读取需求。
 * 未来版本中此服务将移至 OpenMTEduInst 项目维护。
 * 教师服务
 * 提供教师相关API调用封装，包括课程管理、学生管理、教学进度等
 */

import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { forkJoin, Observable, of } from 'rxjs';
import { catchError, delay, map, switchMap } from 'rxjs/operators';

import {
  extractOrganizationInfo,
  MultiSourceTeacherData,
  Organization,
} from '../../models/education-management.models';

import { MultiSourceLearningService } from './multi-source-learning.service';

// ==================== 数据模型接口 ====================

export interface TeacherCourse {
  id: number;
  name: string;
  organizationId: number;
  organizationName: string;
  studentCount: number;
  schedule: string;
  assignmentCount: number;
  status: 'active' | 'paused' | 'completed' | 'draft';
  startDate: string | null;
  endDate: string | null;
  completedLessons?: number;
  totalLessons?: number;
  progress?: number;
}

export interface TeacherStudent {
  id: number;
  name: string;
  organizationId: number;
  organizationName: string;
  className: string;
  grade: number;
  status: 'active' | 'inactive' | 'graduated' | 'transferred';
  progress: number;
  lastActivity: string | null;
  attendanceRate?: number;
  recentAssignments?: StudentAssignment[];
}

export interface TeacherStats {
  classCount: number;
  studentCount: number;
  pendingAssignments: number;
  tokenBalance: number;
  activeCourses: number;
  completedLessons: number;
  totalLessons: number;
  averageProgress: number;
  recentActivities?: DashboardActivity[];
}

export interface StudentAssignment {
  id: number;
  title: string;
  courseName: string;
  submittedAt: string | null;
  dueDate: string;
  status: 'pending' | 'submitted' | 'graded' | 'overdue';
  score?: number;
  maxScore: number;
}

export interface DashboardActivity {
  id: number;
  type:
    | 'assignment_submitted'
    | 'course_completed'
    | 'lesson_started'
    | 'attendance_recorded'
    | 'grade_updated';
  title: string;
  description: string;
  timestamp: string;
  userId: number;
  userName: string;
  courseId?: number;
  courseName?: string;
}

export interface OrganizationDashboardData {
  overview: {
    teacherCount: number;
    studentCount: number;
    courseCount: number;
    classroomCount: number;
    activeLessonsToday: number;
  };
  todaySchedules: number;
  recentActivities: DashboardActivity[];
  alerts: DashboardAlert[];
  generatedAt: string;
}

export interface DashboardAlert {
  id: number;
  type: 'maintenance_due' | 'course_completion' | 'attendance_low' | 'assignment_overdue';
  title: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  createdAt: string;
  resolved: boolean;
}

export interface CourseListResponse {
  total: number;
  items: TeacherCourse[];
}

export interface StudentListResponse {
  total: number;
  items: TeacherStudent[];
}

export interface CourseListResponse {
  total: number;
  items: TeacherCourse[];
}

export interface TeacherDashboardResponse {
  stats: TeacherStats;
  recentCourses: TeacherCourse[];
  recentStudents: TeacherStudent[];
  pendingAssignments: StudentAssignment[];
  activities: DashboardActivity[];
  lastUpdated: string;
}

// 从教育管理模型导入MultiSourceTeacherData
export { MultiSourceTeacherData } from '../../models/education-management.models';

@Injectable({
  providedIn: 'root',
})
export class TeacherService {
  private readonly API_BASE = '/api/v1';

  constructor(
    private http: HttpClient,
    private multiSourceService: MultiSourceLearningService
  ) {}

  /**
   * 获取教师统计数据（增强版，调用真实后端API）
   */
  getTeacherStats(teacherId: number, orgId?: number): Observable<TeacherStats> {
    // 如果提供了orgId，优先使用真实API
    if (orgId) {
      return this.http
        .get<OrganizationDashboardData>(`${this.API_BASE}/org/${orgId}/dashboard`)
        .pipe(
          map((dashboard) => {
            const overview = dashboard.overview;
            return {
              classCount: overview?.classroomCount || 0,
              studentCount: overview?.studentCount || 0,
              pendingAssignments: this.getPendingAssignmentsCount(dashboard.alerts || []),
              tokenBalance: 0, // TODO: 待Token系统支持
              activeCourses: overview?.courseCount || 0,
              completedLessons: 0, // TODO: 待API支持
              totalLessons: 0, // TODO: 待API支持
              averageProgress: 0, // TODO: 待API支持
              recentActivities: dashboard.recentActivities || [],
            } as TeacherStats;
          }),
          catchError((err) => {
            console.warn('获取真实教师统计数据失败，回退到多源学习服务:', err);
            // 回退到多源学习服务
            return this.getTeacherStatsFromMultiSource(teacherId);
          })
        );
    } else {
      // 使用多源学习服务（兼容模式）
      return this.getTeacherStatsFromMultiSource(teacherId);
    }
  }

  /**
   * 从多源学习服务获取教师统计数据（向后兼容）
   */
  private getTeacherStatsFromMultiSource(teacherId: number): Observable<TeacherStats> {
    return this.multiSourceService.getUserOrganizationStats(teacherId).pipe(
      map((stats) => ({
        classCount: stats.total || 0,
        studentCount: stats.by_role?.['student'] || 0,
        pendingAssignments: 0, // TODO: 待API支持
        tokenBalance: 0, // TODO: 待API支持
        activeCourses: stats.by_source_type
          ? Object.values(stats.by_source_type).reduce((a: number, b: number) => a + b, 0)
          : 0,
        completedLessons: 0,
        totalLessons: 0,
        averageProgress: 0,
      })),
      catchError((err) => {
        console.error('获取教师统计数据失败:', err);
        return of({
          classCount: 0,
          studentCount: 0,
          pendingAssignments: 0,
          tokenBalance: 0,
          activeCourses: 0,
          completedLessons: 0,
          totalLessons: 0,
          averageProgress: 0,
        });
      })
    );
  }

  /**
   * 计算待批改作业数量
   */
  private getPendingAssignmentsCount(alerts: DashboardAlert[]): number {
    return alerts.filter((alert) => alert.type === 'assignment_overdue' && !alert.resolved).length;
  }

  /**
   * 获取教师课程列表（增强类型安全版本）
   */
  getTeacherCourses(teacherId: number): Observable<TeacherCourse[]> {
    return this.multiSourceService.getUserLearningSources(teacherId).pipe(
      map((response) => {
        const sources = response?.items || [];

        // 使用类型安全的转换
        return sources.map((source) => {
          const sourceDetail = source.source_detail || {};
          const orgInfo = extractOrganizationInfo(sourceDetail);

          return {
            id: source.id,
            name: source.name || sourceDetail['source_name'] || '未命名课程',
            organizationId: source.org_id || orgInfo.organization_id || 0,
            organizationName: orgInfo.organization_name || sourceDetail['org_name'] || '未分配',
            studentCount: sourceDetail['member_count'] || 0,
            schedule: sourceDetail['schedule'] || '待设置',
            assignmentCount: sourceDetail['assignment_count'] || 0,
            status: (source.status || 'active') as 'active' | 'paused' | 'completed' | 'draft',
            startDate: source.start_date,
            endDate: source.end_date,
            completedLessons: sourceDetail['completed_lessons'],
            totalLessons: sourceDetail['total_lessons'],
            progress: sourceDetail['progress'],
          } as TeacherCourse;
        });
      }),
      catchError((err) => {
        console.error('获取课程列表失败:', err);
        return of([]);
      })
    );
  }

  /**
   * 获取教师学生列表（增强类型安全版本）
   */
  getTeacherStudents(teacherId: number): Observable<TeacherStudent[]> {
    return this.multiSourceService.getUserOrganizations(teacherId).pipe(
      map((orgResponse) => {
        const orgs = orgResponse?.items || [];
        if (orgs.length === 0) {
          return [];
        }

        // 收集所有组织下的学生（简化实现）
        return this.getStudentsFromOrganizations(orgs).pipe(
          map((students) => students.flat()),
          catchError(() => of([]))
        );
      }),
      switchMap((studentObservable) => studentObservable),
      catchError((err) => {
        console.error('获取学生列表失败:', err);
        return of([]);
      })
    );
  }

  /**
   * 从组织中获取学生列表
   */
  private getStudentsFromOrganizations(orgs: any[]): Observable<TeacherStudent[][]> {
    const studentRequests = orgs.slice(0, 5).map((org) =>
      this.multiSourceService.getOrganizationUsers(org.id, { role: 'student' }).pipe(
        map((userResponse) => {
          const students = userResponse?.items || [];
          return students.map((student) => {
            const studentDetail = student.metadata || {};
            const orgMetadata = org.metadata || {};

            return {
              id: student.id,
              name: studentDetail['name'] || studentDetail['username'] || `学生${student.id}`,
              organizationId: org.id,
              organizationName: orgMetadata['name'] || orgMetadata['organization_name'] || '未分配',
              className: studentDetail['class_name'] || student.class_name || '未分配',
              grade: studentDetail['grade'] || this.getRandomGrade(),
              status: (student.status || 'active') as
                | 'active'
                | 'inactive'
                | 'graduated'
                | 'transferred',
              progress: studentDetail['progress'] || this.getRandomProgress(),
              lastActivity: studentDetail['last_activity'] || student.updated_at,
              attendanceRate: studentDetail['attendance_rate'],
              recentAssignments: studentDetail['recent_assignments'] || [],
            } as TeacherStudent;
          });
        }),
        catchError(() => of([]))
      )
    );

    // 使用forkJoin并行获取所有组织下的学生
    return studentRequests.length > 0 ? forkJoin(studentRequests) : of([]);
  }

  /**
   * 生成随机成绩（模拟数据，待API支持）
   */
  private getRandomGrade(): number {
    return Math.floor(Math.random() * 30 + 70); // 70-100之间的成绩
  }

  /**
   * 生成随机学习进度（模拟数据，待API支持）
   */
  private getRandomProgress(): number {
    return Math.floor(Math.random() * 40 + 60); // 60-100之间的进度
  }

  /**
   * 获取跨机构教学进度（类型安全版本）
   */
  getUnifiedProgress(userId: number): Observable<MultiSourceTeacherData | null> {
    return this.multiSourceService.getUserUnifiedProgress(userId).pipe(
      switchMap((progressData) => {
        // 类型转换，确保返回类型安全的数据
        if (!progressData) {
          return of(null);
        }

        // 获取教师的组织关联
        return this.getTeacherOrganizations(userId).pipe(
          map((organizations) => {
            // 构造MultiSourceTeacherData
            return {
              teacher_id: userId,
              organizations: organizations.map((org) => ({
                org_id: org.id,
                org_name: org.name,
                role: 'teacher', // 默认角色
                stats: {
                  teacher_count: 0,
                  student_count: 0,
                  course_count: 0,
                  classroom_count: 0,
                  active_lessons_today: 0,
                  pending_assignments: 0,
                  average_attendance_rate: 0,
                  average_progress_rate: progressData.average_score || 0,
                },
              })),
              unified_progress: {
                total_students: 0, // 需要额外API支持
                average_progress_across_orgs: progressData.average_score || 0,
                active_courses_count: progressData.in_progress_courses || 0,
                pending_assignments_count: 0, // 需要额外API支持
              },
              learning_sources: [],
            } as MultiSourceTeacherData;
          })
        );
      }),
      catchError((err) => {
        console.error('获取跨机构进度失败:', err);
        return of(null);
      })
    );
  }

  /**
   * 获取教师关联的组织（类型安全版本）
   */
  getTeacherOrganizations(teacherId: number): Observable<Organization[]> {
    return this.multiSourceService.getUserOrganizations(teacherId).pipe(
      map((response) => {
        const items = response?.items || [];

        return items.map((item) => {
          const metadata = item.metadata || {};

          return {
            id: item.id || 0,
            name: metadata['name'] || metadata['organization_name'] || '未命名组织',
            type: (metadata['type'] || 'training_institution') as
              | 'school'
              | 'training_institution'
              | 'online_platform'
              | 'competition_center',
            logo_url: metadata['logo_url'] || metadata['logo'],
            description: metadata['description'],
            contact_email: metadata['contact_email'],
            contact_phone: metadata['contact_phone'],
            address: metadata['address'],
            status: (item.status || 'active') as 'active' | 'inactive' | 'pending_review',
            created_at: item.created_at || new Date().toISOString(),
            updated_at: item.updated_at || new Date().toISOString(),
          } as Organization;
        });
      }),
      catchError((err) => {
        console.error('获取组织列表失败:', err);
        return of([]);
      })
    );
  }

  /**
   * 获取教师完整Dashboard数据（真实API版本）
   */
  getTeacherDashboard(teacherId: number, orgId?: number): Observable<TeacherDashboardResponse> {
    // 如果提供了orgId，尝试调用真实API
    if (orgId) {
      return this.http
        .get<OrganizationDashboardData>(`${this.API_BASE}/org/${orgId}/dashboard`)
        .pipe(
          map((dashboard) => {
            // 转换后端数据为前端格式
            return this.transformDashboardData(dashboard, teacherId, orgId);
          }),
          catchError((err) => {
            console.warn('获取真实Dashboard数据失败，回退到模拟数据:', err);
            return this.getSimulatedTeacherDashboard(teacherId);
          })
        );
    } else {
      // 使用模拟数据（向后兼容）
      return this.getSimulatedTeacherDashboard(teacherId);
    }
  }

  /**
   * 获取教师待批改作业列表
   */
  getPendingAssignments(teacherId: number, orgId?: number): Observable<StudentAssignment[]> {
    // 这里应该调用真实API，暂时返回模拟数据
    const mockAssignments: StudentAssignment[] = [
      {
        id: 1,
        title: '函数与极限作业',
        courseName: '高等数学',
        submittedAt: '2026-03-20T14:30:00Z',
        dueDate: '2026-03-25T23:59:00Z',
        status: 'submitted',
        score: undefined,
        maxScore: 100,
      },
      {
        id: 2,
        title: '力学实验报告',
        courseName: '大学物理',
        submittedAt: '2026-03-21T09:15:00Z',
        dueDate: '2026-03-22T23:59:00Z',
        status: 'submitted',
        score: undefined,
        maxScore: 100,
      },
      {
        id: 3,
        title: '英语写作练习',
        courseName: '大学英语',
        submittedAt: null,
        dueDate: '2026-03-24T23:59:00Z',
        status: 'overdue',
        score: undefined,
        maxScore: 100,
      },
    ];

    return of(mockAssignments).pipe(
      delay(300) // 模拟API延迟
    );
  }

  /**
   * 获取教师近期的活动记录
   */
  getRecentActivities(teacherId: number, orgId?: number): Observable<DashboardActivity[]> {
    // 这里应该调用真实API，暂时返回模拟数据
    const mockActivities: DashboardActivity[] = [
      {
        id: 1,
        type: 'assignment_submitted',
        title: '作业提交',
        description: '学生张三提交了高等数学作业',
        timestamp: '2026-03-21T10:30:00Z',
        userId: 101,
        userName: '张三',
        courseId: 1,
        courseName: '高等数学',
      },
      {
        id: 2,
        type: 'grade_updated',
        title: '成绩更新',
        description: '更新了王五的物理实验成绩',
        timestamp: '2026-03-20T16:45:00Z',
        userId: 102,
        userName: '王五',
        courseId: 2,
        courseName: '大学物理',
      },
      {
        id: 3,
        type: 'lesson_started',
        title: '课程开始',
        description: '开始了新的一节英语课程',
        timestamp: '2026-03-20T09:00:00Z',
        userId: teacherId,
        userName: '当前教师',
        courseId: 3,
        courseName: '大学英语',
      },
    ];

    return of(mockActivities).pipe(
      delay(200) // 模拟API延迟
    );
  }

  // ==================== 私有工具方法 ====================

  /**
   * 转换后端Dashboard数据为前端格式
   */
  private transformDashboardData(
    dashboard: OrganizationDashboardData,
    teacherId: number,
    orgId: number
  ): TeacherDashboardResponse {
    const now = new Date().toISOString();

    return {
      stats: {
        classCount: dashboard.overview.classroomCount,
        studentCount: dashboard.overview.studentCount,
        pendingAssignments: this.getPendingAssignmentsCount(dashboard.alerts || []),
        tokenBalance: 0,
        activeCourses: dashboard.overview.courseCount,
        completedLessons: 0,
        totalLessons: 0,
        averageProgress: 0,
        recentActivities: dashboard.recentActivities || [],
      },
      recentCourses: [], // 需要额外的API调用
      recentStudents: [], // 需要额外的API调用
      pendingAssignments: [], // 需要额外的API调用
      activities: dashboard.recentActivities || [],
      lastUpdated: now,
    };
  }

  /**
   * 生成模拟的TeacherDashboard数据（向后兼容）
   */
  private getSimulatedTeacherDashboard(teacherId: number): Observable<TeacherDashboardResponse> {
    const now = new Date().toISOString();

    return forkJoin({
      stats: this.getTeacherStats(teacherId),
      recentCourses: this.getTeacherCourses(teacherId).pipe(map((courses) => courses.slice(0, 3))),
      recentStudents: this.getTeacherStudents(teacherId).pipe(
        map((students) => students.slice(0, 5))
      ),
      activities: this.getRecentActivities(teacherId),
    }).pipe(
      map(({ stats, recentCourses, recentStudents, activities }) => ({
        stats: {
          ...stats,
          completedLessons: 12,
          totalLessons: 20,
          averageProgress: 65,
        } as TeacherStats,
        recentCourses,
        recentStudents,
        pendingAssignments: [], // 单独调用
        activities,
        lastUpdated: now,
      })),
      catchError((err) => {
        console.error('生成模拟Dashboard数据失败:', err);
        return of({
          stats: {
            classCount: 0,
            studentCount: 0,
            pendingAssignments: 0,
            tokenBalance: 0,
            activeCourses: 0,
            completedLessons: 0,
            totalLessons: 0,
            averageProgress: 0,
          },
          recentCourses: [],
          recentStudents: [],
          pendingAssignments: [],
          activities: [],
          lastUpdated: now,
        });
      })
    );
  }
}
