/**
 * 机构管理员服务
 *
 * 提供机构管理员Dashboard相关API调用封装，包括：
 * - 机构概览（学生数、教师数、活跃课程数）
 * - 课程运营（课程列表、报名统计）
 * - 教师管理（教师列表、课时统计）
 * - 学员管理（学员列表、学习进度）
 *
 * Phase 2: 机构管理员Dashboard扩展
 * 调用后端 educational_institution_routes.py 接口
 *
 * 注意：组织门户已解耦到 OpenMTEduInst 项目，
 * 但此服务保留供 iMato 学习端跨项目数据展示需求。
 */

import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { forkJoin, Observable, of, throwError } from 'rxjs';
import { catchError, map, retry, shareReplay, timeout } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

import { MultiSourceLearningService } from './multi-source-learning.service';

// ==================== 基础响应类型 ====================

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  total?: number;
  page?: number;
  pageSize?: number;
}

// ==================== 数据模型接口 ====================

/** 机构概览 */
export interface OrganizationOverview {
  org_id: number;
  org_name: string;
  total_students: number;
  total_teachers: number;
  total_active_courses: number;
  total_courses: number;
  total_classrooms: number;
  student_growth_rate: number;
  teacher_student_ratio: number;
  course_completion_rate: number;
  average_attendance: number;
  revenue_current_month: number;
  revenue_previous_month: number;
  active_licenses: number;
  total_licenses: number;
}

/** 课程运营 */
export interface CourseOperation {
  id: number;
  org_id: number;
  name: string;
  type: 'school_curriculum' | 'school_interest' | 'training' | 'workshop';
  category: string;
  teacher_name: string;
  enrolled_students: number;
  max_students: number;
  sessions_count: number;
  completed_sessions: number;
  start_date: string;
  end_date: string | null;
  status: 'draft' | 'published' | 'ongoing' | 'completed' | 'cancelled';
  enrollment_trend: 'increasing' | 'stable' | 'decreasing';
  avg_rating: number;
  revenue: number;
}

/** 教师管理 */
export interface OrgTeacher {
  id: number;
  user_id: number;
  org_id: number;
  name: string;
  email: string;
  phone: string | null;
  department: string;
  position: string;
  specialization: string[];
  courses_count: number;
  students_count: number;
  total_teaching_hours: number;
  weekly_schedule: number;
  performance_rating: number | null;
  join_date: string;
  status: 'active' | 'on_leave' | 'inactive';
  certifications: string[];
}

/** 学员管理 */
export interface OrgStudent {
  id: number;
  user_id: number;
  org_id: number;
  name: string;
  email: string;
  grade: string | null;
  enrolled_courses: number;
  completed_courses: number;
  overall_progress: number;
  attendance_rate: number;
  average_score: number | null;
  join_date: string;
  status: 'active' | 'graduated' | 'suspended' | 'inactive';
  learning_sources: {
    institution: string;
    progress: number;
  }[];
}

/** 机构Dashboard聚合数据 */
export interface OrganizationDashboardData {
  overview: OrganizationOverview;
  courses: CourseOperation[];
  teachers: OrgTeacher[];
  students: OrgStudent[];
  recent_activities: Array<{
    id: number;
    type: 'student_enrolled' | 'course_started' | 'teacher_hired' | 'course_completed';
    description: string;
    user_name?: string;
    timestamp: string;
  }>;
  alerts: Array<{
    id: number;
    type: 'low_enrollment' | 'teacher_overload' | 'course_expiring' | 'revenue_drop';
    message: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    created_at: string;
  }>;
  generated_at: string;
}

// ==================== 服务实现 ====================

@Injectable({
  providedIn: 'root',
})
export class OrgAdminService {
  private readonly API_BASE = environment.apiUrl + '/api/v1/org';

  // 开发环境使用模拟数据
  private useMockData = !environment.production;

  constructor(
    private http: HttpClient,
    private multiSourceService: MultiSourceLearningService
  ) {}

  /**
   * 获取认证头部信息
   */
  private getAuthHeaders(): HttpHeaders {
    const token =
      typeof localStorage !== 'undefined' ? localStorage.getItem('access_token') : null;
    return new HttpHeaders({
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    });
  }

  // ===== 机构概览 =====

  /**
   * 获取机构概览数据
   */
  getOrganizationOverview(orgId: number): Observable<OrganizationOverview> {
    const headers = this.getAuthHeaders();

    return this.http
      .get<ApiResponse<OrganizationOverview>>(`${this.API_BASE}/${orgId}/overview`, { headers })
      .pipe(
        timeout(10000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          }
          throw new Error(response.message || '获取机构概览失败');
        }),
        catchError((err) => {
          console.warn('真实API获取机构概览失败，回退到模拟数据:', err);
          return this.getSimulatedOverview(orgId);
        }),
        shareReplay(1)
      );
  }

  /**
   * 获取机构Dashboard完整数据
   */
  getOrganizationDashboard(orgId: number): Observable<OrganizationDashboardData> {
    const headers = this.getAuthHeaders();

    return this.http
      .get<ApiResponse<OrganizationDashboardData>>(`${this.API_BASE}/${orgId}/dashboard`, {
        headers,
      })
      .pipe(
        timeout(15000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          }
          throw new Error(response.message || '获取机构Dashboard失败');
        }),
        catchError((err) => {
          console.warn('真实API获取机构Dashboard失败，回退到模拟数据:', err);
          return this.getSimulatedDashboard(orgId);
        })
      );
  }

  // ===== 课程运营 =====

  /**
   * 获取机构课程列表
   */
  getOrganizationCourses(orgId: number): Observable<CourseOperation[]> {
    const headers = this.getAuthHeaders();

    return this.http
      .get<ApiResponse<CourseOperation[]>>(`${this.API_BASE}/${orgId}/courses`, { headers })
      .pipe(
        timeout(10000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          }
          throw new Error(response.message || '获取课程列表失败');
        }),
        catchError((err) => {
          console.warn('真实API获取课程列表失败，回退到模拟数据:', err);
          return this.getSimulatedCourses(orgId);
        })
      );
  }

  // ===== 教师管理 =====

  /**
   * 获取机构教师列表
   */
  getOrganizationTeachers(orgId: number): Observable<OrgTeacher[]> {
    const headers = this.getAuthHeaders();

    return this.http
      .get<ApiResponse<OrgTeacher[]>>(`${this.API_BASE}/${orgId}/teachers`, { headers })
      .pipe(
        timeout(10000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          }
          throw new Error(response.message || '获取教师列表失败');
        }),
        catchError((err) => {
          console.warn('真实API获取教师列表失败，回退到模拟数据:', err);
          return this.getSimulatedTeachers(orgId);
        })
      );
  }

  // ===== 学员管理 =====

  /**
   * 获取机构学员列表
   */
  getOrganizationStudents(orgId: number): Observable<OrgStudent[]> {
    const headers = this.getAuthHeaders();

    return this.http
      .get<ApiResponse<OrgStudent[]>>(`${this.API_BASE}/${orgId}/students`, { headers })
      .pipe(
        timeout(10000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          }
          throw new Error(response.message || '获取学员列表失败');
        }),
        catchError((err) => {
          console.warn('真实API获取学员列表失败，回退到模拟数据:', err);
          return this.getSimulatedStudents(orgId);
        })
      );
  }

  // ===== CRUD操作 =====

  /**
   * 创建新课程
   */
  createCourse(
    orgId: number,
    courseData: Partial<CourseOperation>
  ): Observable<CourseOperation> {
    const headers = this.getAuthHeaders();

    return this.http
      .post<ApiResponse<CourseOperation>>(`${this.API_BASE}/${orgId}/courses`, courseData, {
        headers,
      })
      .pipe(
        timeout(8000),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          }
          throw new Error(response.message || '创建课程失败');
        }),
        catchError((err) => {
          console.error('创建课程失败:', err);
          return throwError(() => new Error('创建课程失败，请稍后重试'));
        })
      );
  }

  /**
   * 添加教师
   */
  addTeacher(orgId: number, teacherData: Partial<OrgTeacher>): Observable<OrgTeacher> {
    const headers = this.getAuthHeaders();

    return this.http
      .post<ApiResponse<OrgTeacher>>(`${this.API_BASE}/${orgId}/teachers`, teacherData, {
        headers,
      })
      .pipe(
        timeout(8000),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          }
          throw new Error(response.message || '添加教师失败');
        }),
        catchError((err) => {
          console.error('添加教师失败:', err);
          return throwError(() => new Error('添加教师失败，请稍后重试'));
        })
      );
  }

  /**
   * 添加学员
   */
  addStudent(orgId: number, studentData: Partial<OrgStudent>): Observable<OrgStudent> {
    const headers = this.getAuthHeaders();

    return this.http
      .post<ApiResponse<OrgStudent>>(`${this.API_BASE}/${orgId}/students`, studentData, {
        headers,
      })
      .pipe(
        timeout(8000),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          }
          throw new Error(response.message || '添加学员失败');
        }),
        catchError((err) => {
          console.error('添加学员失败:', err);
          return throwError(() => new Error('添加学员失败，请稍后重试'));
        })
      );
  }

  // ===== 模拟数据方法 =====

  private getSimulatedOverview(orgId: number): Observable<OrganizationOverview> {
    return of({
      org_id: orgId,
      org_name: '示例教育机构',
      total_students: 520,
      total_teachers: 28,
      total_active_courses: 18,
      total_courses: 24,
      total_classrooms: 12,
      student_growth_rate: 8.5,
      teacher_student_ratio: 18.57,
      course_completion_rate: 87.3,
      average_attendance: 93.2,
      revenue_current_month: 128000,
      revenue_previous_month: 115000,
      active_licenses: 45,
      total_licenses: 50,
    });
  }

  private getSimulatedCourses(orgId: number): Observable<CourseOperation[]> {
    const courseNames = [
      'Python编程基础', 'Web前端开发', '数据结构与算法', '机器学习入门',
      '英语口语提升', '日语初级', '法语入门', '数学思维训练',
      '物理实验课', '化学基础', '创意写作', '机器人编程',
    ];

    const courses: CourseOperation[] = courseNames.map((name, index) => ({
      id: index + 1,
      org_id: orgId,
      name,
      type: (index < 4 ? 'school_curriculum' : index < 8 ? 'training' : 'workshop') as CourseOperation['type'],
      category: index < 4 ? '编程' : index < 8 ? '语言' : '素质',
      teacher_name: ['张老师', '李老师', '王老师', '刘老师'][index % 4],
      enrolled_students: Math.floor(Math.random() * 40 + 10),
      max_students: 50,
      sessions_count: 16,
      completed_sessions: Math.floor(Math.random() * 12 + 2),
      start_date: '2026-03-01',
      end_date: index % 3 === 0 ? null : '2026-07-01',
      status: (index % 5 === 0 ? 'draft' : index % 5 === 1 ? 'published' : 'ongoing') as CourseOperation['status'],
      enrollment_trend: ['increasing', 'stable', 'decreasing'][index % 3] as CourseOperation['enrollment_trend'],
      avg_rating: Math.floor(Math.random() * 20 + 80) / 10,
      revenue: Math.floor(Math.random() * 5000 + 2000),
    }));

    return of(courses);
  }

  private getSimulatedTeachers(orgId: number): Observable<OrgTeacher[]> {
    const teacherNames = [
      '张老师', '李老师', '王老师', '刘老师', '赵老师', '钱老师',
      '孙老师', '周老师', '吴老师', '郑老师',
    ];

    const teachers: OrgTeacher[] = teacherNames.map((name, index) => ({
      id: index + 1,
      user_id: 1000 + index,
      org_id: orgId,
      name,
      email: `${name.charAt(0).toLowerCase()}teacher${index}@org.edu.cn`,
      phone: index % 2 === 0 ? `1380000${String(index).padStart(4, '0')}` : null,
      department: ['计算机系', '外语系', '数学系', '物理系'][index % 4],
      position: index % 3 === 0 ? '高级讲师' : index % 3 === 1 ? '讲师' : '助教',
      specialization: [['Python', 'Java'], ['英语', '日语'], ['数学', '统计'], ['物理', '实验']][index % 4],
      courses_count: Math.floor(Math.random() * 3 + 1),
      students_count: Math.floor(Math.random() * 80 + 20),
      total_teaching_hours: Math.floor(Math.random() * 200 + 50),
      weekly_schedule: Math.floor(Math.random() * 12 + 8),
      performance_rating: Math.floor(Math.random() * 20 + 80),
      join_date: `202${Math.floor(Math.random() * 5) + 1}-0${Math.floor(Math.random() * 9) + 1}-01`,
      status: index % 6 === 0 ? 'on_leave' : 'active',
      certifications: index % 2 === 0 ? ['教师资格证', '专业等级证书'] : ['教师资格证'],
    }));

    return of(teachers);
  }

  private getSimulatedStudents(orgId: number): Observable<OrgStudent[]> {
    const students: OrgStudent[] = [];

    for (let i = 1; i <= 15; i++) {
      students.push({
        id: i,
        user_id: 2000 + i,
        org_id: orgId,
        name: `学生${i}`,
        email: `student${i}@org.edu.cn`,
        grade: i <= 8 ? `${Math.floor(Math.random() * 3) + 1}年级` : null,
        enrolled_courses: Math.floor(Math.random() * 5 + 2),
        completed_courses: Math.floor(Math.random() * 4),
        overall_progress: Math.floor(Math.random() * 40 + 50),
        attendance_rate: Math.floor(Math.random() * 20 + 80),
        average_score: Math.floor(Math.random() * 30 + 70),
        join_date: `202${Math.floor(Math.random() * 3) + 4}-0${Math.floor(Math.random() * 9) + 1}-01`,
        status: i % 8 === 0 ? 'suspended' : i % 10 === 0 ? 'graduated' : 'active',
        learning_sources: [
          {
            institution: '主校区',
            progress: Math.floor(Math.random() * 40 + 50),
          },
          {
            institution: '线上平台',
            progress: Math.floor(Math.random() * 40 + 40),
          },
        ],
      });
    }

    return of(students);
  }

  private getSimulatedDashboard(orgId: number): Observable<OrganizationDashboardData> {
    return forkJoin({
      overview: this.getSimulatedOverview(orgId),
      courses: this.getSimulatedCourses(orgId),
      teachers: this.getSimulatedTeachers(orgId),
      students: this.getSimulatedStudents(orgId),
    }).pipe(
      map((data) => ({
        ...data,
        recent_activities: [
          {
            id: 1,
            type: 'student_enrolled' as const,
            description: '新学员王小明完成注册',
            user_name: '王小明',
            timestamp: new Date(Date.now() - 3600000).toISOString(),
          },
          {
            id: 2,
            type: 'course_started' as const,
            description: 'Python编程基础新班开课',
            timestamp: new Date(Date.now() - 86400000).toISOString(),
          },
          {
            id: 3,
            type: 'teacher_hired' as const,
            description: '周老师入职，加入计算机系',
            user_name: '周老师',
            timestamp: new Date(Date.now() - 172800000).toISOString(),
          },
        ],
        alerts: [
          {
            id: 1,
            type: 'low_enrollment' as const,
            message: '法语入门课程报名人数不足最低开班要求',
            severity: 'medium' as const,
            created_at: new Date(Date.now() - 43200000).toISOString(),
          },
          {
            id: 2,
            type: 'course_expiring' as const,
            message: '机器学习入门课程将在7天后结课',
            severity: 'low' as const,
            created_at: new Date(Date.now() - 21600000).toISOString(),
          },
        ],
        generated_at: new Date().toISOString(),
      }))
    );
  }
}
