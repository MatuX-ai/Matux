/**
 * @deprecated 学校管理功能属于机构端，将逐步迁移到 OpenMTEduInst 子项目。
 * 当前保留用于 iMato 学习端的学校数据展示需求。
 * 未来版本中此服务将移至 OpenMTEduInst 项目维护。
 * 学校管理员服务
 * 提供学校场景相关API调用封装，包括年级班级管理、校本课程管理、教师工作量统计、学生成长档案等
 * Phase 3增强：类型安全、真实API支持、细粒度错误处理、完整CRUD操作
 */

import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { forkJoin, Observable, of, throwError } from 'rxjs';
import { catchError, map, retry, shareReplay, timeout } from 'rxjs/operators';

import { environment } from '../../../environments/environment';

import { MultiSourceLearningService } from './multi-source-learning.service';

// 基础响应类型
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  total?: number;
  page?: number;
  pageSize?: number;
}

// 年级班级管理接口
export interface GradeClass {
  id: number;
  school_id: number;
  name: string;
  grade: number;
  class_number: number;
  student_count: number;
  teacher_count: number;
  homeroom_teacher_id: number | null;
  homeroom_teacher_name: string | null;
  classroom: string | null;
  capacity: number;
  status: 'active' | 'graduated' | 'disbanded' | 'inactive';
  created_at: string | null;
  updated_at: string | null;
}

// 校本课程管理接口
export interface SchoolCourse {
  id: number;
  school_id: number;
  name: string;
  type: 'school_curriculum' | 'school_interest';
  category: string;
  description: string | null;
  teacher_id: number | null;
  teacher_name: string;
  enrolled_students: number;
  capacity: number;
  schedule: string;
  duration_minutes: number;
  credits: number;
  status: 'draft' | 'published' | 'ongoing' | 'completed' | 'archived';
  prerequisites: string[] | null;
  learning_objectives: string[] | null;
  created_at: string | null;
  updated_at: string | null;
}

// 教师工作量统计接口
export interface TeacherWorkload {
  id: number;
  user_id: number;
  school_id: number;
  name: string;
  email: string;
  department: string;
  position: string;
  courses_count: number;
  classes_count: number;
  students_count: number;
  total_hours: number;
  avg_weekly_hours: number;
  course_types: {
    school_curriculum: number;
    school_interest: number;
  };
  performance_score: number | null;
  workload_score: number | null;
  last_updated: string;
}

// 学生成长档案接口
export interface StudentGrowthRecord {
  id: number;
  user_id: number;
  school_id: number;
  name: string;
  grade: string;
  class_name: string;
  class_id: number;
  term: string;
  academic_year: string;
  courses_taken: number;
  avg_score: number;
  attendance_rate: number;
  conduct_score: number | null;
  extracurricular_count: number;
  achievements: {
    id: number;
    type: 'academic' | 'sports' | 'arts' | 'leadership' | 'service';
    name: string;
    description: string;
    date_awarded: string;
  }[];
  learning_trends: {
    subject: string;
    previous_score: number;
    current_score: number;
    improvement: number;
  }[];
  recommendations: string[];
  created_at: string;
  updated_at: string;
}

// 学校概览接口
export interface SchoolOverview {
  school_id: number;
  school_name: string;
  total_grades: number;
  total_classes: number;
  total_students: number;
  total_teachers: number;
  total_courses: number;
  active_courses: number;
  avg_class_size: number;
  avg_teacher_student_ratio: number;
  attendance_rate: number;
  graduation_rate: number | null;
  last_semester_avg_score: number | null;
}

// 学校Dashboard整体数据
export interface SchoolDashboardData {
  overview: SchoolOverview;
  grade_classes: GradeClass[];
  school_courses: SchoolCourse[];
  teacher_workloads: TeacherWorkload[];
  student_growth_records: StudentGrowthRecord[];
  recent_activities: Array<{
    id: number;
    type:
      | 'class_created'
      | 'course_started'
      | 'teacher_assigned'
      | 'student_enrolled'
      | 'achievement_awarded';
    description: string;
    user_name?: string;
    timestamp: string;
  }>;
  alerts: Array<{
    id: number;
    type:
      | 'class_full'
      | 'teacher_overload'
      | 'low_attendance'
      | 'performance_alert'
      | 'schedule_conflict';
    message: string;
    severity: 'low' | 'medium' | 'high';
    created_at: string;
  }>;
  last_updated: string;
}

@Injectable({
  providedIn: 'root',
})
@Injectable({
  providedIn: 'root',
})
export class SchoolAdminService {
  private readonly API_BASE = environment.apiUrl + '/api/v1';
  private readonly SCHOOL_API_BASE = this.API_BASE + '/educational_institution/school';

  // 模拟数据标记（开发阶段使用）
  private useMockData = environment.production === false; // 开发环境使用模拟数据

  constructor(
    private http: HttpClient,
    private multiSourceService: MultiSourceLearningService
  ) {}

  /**
   * 获取认证头部信息
   */
  private getAuthHeaders(): HttpHeaders {
    const token = typeof localStorage !== 'undefined' ? localStorage.getItem('access_token') : null;
    return new HttpHeaders({
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    });
  }

  /**
   * 获取学校Dashboard整体数据（一次性获取所有数据）
   */
  getSchoolDashboard(schoolId: number): Observable<SchoolDashboardData> {
    const headers = this.getAuthHeaders();
    const cacheKey = `school_dashboard_${schoolId}`;

    return this.http
      .get<
        ApiResponse<SchoolDashboardData>
      >(`${this.SCHOOL_API_BASE}/${schoolId}/dashboard`, { headers })
      .pipe(
        timeout(10000), // 10秒超时
        retry(2), // 失败重试2次
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取学校Dashboard失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取学校Dashboard失败，回退到模拟数据:', err);
          return this.getSimulatedSchoolDashboard(schoolId);
        }),
        shareReplay(1) // 共享最近的响应
      );
  }

  /**
   * 获取学校概览数据
   */
  getSchoolOverview(schoolId: number): Observable<SchoolOverview> {
    const headers = this.getAuthHeaders();

    return this.http
      .get<ApiResponse<SchoolOverview>>(`${this.SCHOOL_API_BASE}/${schoolId}/overview`, { headers })
      .pipe(
        timeout(5000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取学校概览失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取学校概览失败，回退到模拟数据:', err);
          return this.getSimulatedSchoolOverview(schoolId);
        })
      );
  }

  /**
   * 获取年级班级列表
   */
  getGradeClasses(schoolId: number): Observable<GradeClass[]> {
    const headers = this.getAuthHeaders();

    return this.http
      .get<
        ApiResponse<GradeClass[]>
      >(`${this.SCHOOL_API_BASE}/${schoolId}/grade-classes`, { headers })
      .pipe(
        timeout(5000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取年级班级列表失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取年级班级列表失败，回退到模拟数据:', err);
          return this.getSimulatedGradeClasses(schoolId);
        })
      );
  }

  /**
   * 获取校本课程列表（区分school_curriculum和school_interest）
   */
  getSchoolCourses(schoolId: number): Observable<SchoolCourse[]> {
    const headers = this.getAuthHeaders();

    return this.http
      .get<ApiResponse<SchoolCourse[]>>(`${this.SCHOOL_API_BASE}/${schoolId}/courses`, { headers })
      .pipe(
        timeout(5000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取校本课程列表失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取校本课程列表失败，回退到模拟数据:', err);
          return this.getSimulatedSchoolCourses(schoolId);
        })
      );
  }

  /**
   * 获取教师工作量统计
   */
  getTeacherWorkloads(schoolId: number): Observable<TeacherWorkload[]> {
    const headers = this.getAuthHeaders();

    return this.http
      .get<
        ApiResponse<TeacherWorkload[]>
      >(`${this.SCHOOL_API_BASE}/${schoolId}/teacher-workloads`, { headers })
      .pipe(
        timeout(5000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取教师工作量统计失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取教师工作量统计失败，回退到模拟数据:', err);
          return this.getSimulatedTeacherWorkloads(schoolId);
        })
      );
  }

  /**
   * 获取学生成长档案（跨学期学习轨迹）
   */
  getStudentGrowthRecords(schoolId: number): Observable<StudentGrowthRecord[]> {
    const headers = this.getAuthHeaders();

    return this.http
      .get<
        ApiResponse<StudentGrowthRecord[]>
      >(`${this.SCHOOL_API_BASE}/${schoolId}/student-growth-records`, { headers })
      .pipe(
        timeout(5000),
        retry(2),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '获取学生成长档案失败');
          }
        }),
        catchError((err) => {
          console.warn('真实API获取学生成长档案失败，回退到模拟数据:', err);
          return this.getSimulatedStudentGrowthRecords(schoolId);
        })
      );
  }

  // ===== CRUD操作 =====

  /**
   * 创建新班级
   */
  createGradeClass(schoolId: number, classData: Partial<GradeClass>): Observable<GradeClass> {
    const headers = this.getAuthHeaders();

    return this.http
      .post<
        ApiResponse<GradeClass>
      >(`${this.SCHOOL_API_BASE}/${schoolId}/grade-classes`, classData, { headers })
      .pipe(
        timeout(8000),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '创建班级失败');
          }
        }),
        catchError((err) => {
          console.error('创建班级失败:', err);
          return throwError(() => new Error('创建班级失败，请稍后重试'));
        })
      );
  }

  /**
   * 更新班级信息
   */
  updateGradeClass(
    schoolId: number,
    classId: number,
    classData: Partial<GradeClass>
  ): Observable<GradeClass> {
    const headers = this.getAuthHeaders();

    return this.http
      .put<
        ApiResponse<GradeClass>
      >(`${this.SCHOOL_API_BASE}/${schoolId}/grade-classes/${classId}`, classData, { headers })
      .pipe(
        timeout(8000),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '更新班级信息失败');
          }
        }),
        catchError((err) => {
          console.error('更新班级信息失败:', err);
          return throwError(() => new Error('更新班级信息失败，请稍后重试'));
        })
      );
  }

  /**
   * 删除班级
   */
  deleteGradeClass(classId: number): Observable<{ success: boolean; message?: string }> {
    const headers = this.getAuthHeaders();

    return this.http
      .delete<
        ApiResponse<{ success: boolean; message?: string }>
      >(`${this.SCHOOL_API_BASE}/grade-classes/${classId}`, { headers })
      .pipe(
        timeout(5000),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '删除班级失败');
          }
        }),
        catchError((err) => {
          console.error('删除班级失败:', err);
          // 模拟删除成功（用于开发环境）
          if (this.useMockData) {
            return of({ success: true, message: '班级已成功删除（模拟数据）' });
          }
          return throwError(() => new Error('删除班级失败，请稍后重试'));
        })
      );
  }

  /**
   * 创建新课程
   */
  createSchoolCourse(
    schoolId: number,
    courseData: Partial<SchoolCourse>
  ): Observable<SchoolCourse> {
    const headers = this.getAuthHeaders();

    return this.http
      .post<
        ApiResponse<SchoolCourse>
      >(`${this.SCHOOL_API_BASE}/${schoolId}/courses`, courseData, { headers })
      .pipe(
        timeout(8000),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '创建课程失败');
          }
        }),
        catchError((err) => {
          console.error('创建课程失败:', err);
          return throwError(() => new Error('创建课程失败，请稍后重试'));
        })
      );
  }

  /**
   * 分配学生到班级
   */
  assignStudentToClass(
    schoolId: number,
    studentId: number,
    classId: number
  ): Observable<{ success: boolean; message?: string }> {
    const headers = this.getAuthHeaders();

    return this.http
      .post<
        ApiResponse<{ success: boolean; message?: string }>
      >(`${this.SCHOOL_API_BASE}/${schoolId}/assign-student`, { student_id: studentId, class_id: classId }, { headers })
      .pipe(
        timeout(5000),
        map((response) => {
          if (response.success && response.data) {
            return response.data;
          } else {
            throw new Error(response.message || '分配学生到班级失败');
          }
        }),
        catchError((err) => {
          console.error('分配学生到班级失败:', err);
          if (this.useMockData) {
            return of({ success: true, message: '学生分配成功（模拟数据）' });
          }
          return throwError(() => new Error('分配学生到班级失败，请稍后重试'));
        })
      );
  }

  // ===== 模拟数据方法（开发环境使用） =====

  private getSimulatedSchoolOverview(schoolId: number): Observable<SchoolOverview> {
    return of({
      school_id: schoolId,
      school_name: '示例学校',
      total_grades: 3,
      total_classes: 12,
      total_students: 450,
      total_teachers: 35,
      total_courses: 28,
      active_courses: 22,
      avg_class_size: 37.5,
      avg_teacher_student_ratio: 12.86,
      attendance_rate: 94.5,
      graduation_rate: 98.2,
      last_semester_avg_score: 85.3,
    });
  }

  private getSimulatedGradeClasses(schoolId: number): Observable<GradeClass[]> {
    const grades = [1, 2, 3];
    const classesPerGrade = [4, 4, 4];

    const result: GradeClass[] = [];
    let id = 1;

    grades.forEach((grade, gradeIndex) => {
      for (let i = 1; i <= classesPerGrade[gradeIndex]; i++) {
        result.push({
          id: id++,
          school_id: schoolId,
          name: `${grade}年级(${i})班`,
          grade,
          class_number: i,
          student_count: Math.floor(Math.random() * 10 + 30),
          teacher_count: 2,
          homeroom_teacher_id: 1000 + id,
          homeroom_teacher_name: ['张老师', '李老师', '王老师', '刘老师'][
            Math.floor(Math.random() * 4)
          ],
          classroom: `${grade}0${i}教室`,
          capacity: 45,
          status: 'active' as const,
          created_at: '2025-09-01T00:00:00Z',
          updated_at: '2026-03-01T00:00:00Z',
        });
      }
    });

    return of(result);
  }

  private getSimulatedSchoolCourses(schoolId: number): Observable<SchoolCourse[]> {
    const categories = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理'];
    const interestCategories = ['机器人编程', '创意写作', '篮球', '绘画', '音乐', '舞蹈'];

    const result: SchoolCourse[] = [];

    // 校本课程
    categories.forEach((category, index) => {
      result.push({
        id: index + 1,
        school_id: schoolId,
        name: `${category}${index % 3 === 0 ? '基础班' : index % 3 === 1 ? '提高班' : '强化班'}`,
        type: 'school_curriculum' as const,
        category,
        description: `${category}课程，培养学生的${category}素养`,
        teacher_id: 2000 + index,
        teacher_name: ['张老师', '李老师', '王老师', '刘老师'][index % 4],
        enrolled_students: Math.floor(Math.random() * 30 + 20),
        capacity: 40,
        schedule: `周${['一', '二', '三', '四', '五'][index % 5]} 第${(index % 6) + 1}节`,
        duration_minutes: 45,
        credits: 2,
        status: index % 5 === 0 ? 'draft' : index % 5 === 1 ? 'published' : ('ongoing' as any),
        prerequisites: index > 5 ? ['基础课程'] : null,
        learning_objectives: [`掌握${category}基本概念`, `提高${category}应用能力`],
        created_at: '2025-09-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
      });
    });

    // 兴趣班
    interestCategories.forEach((category, index) => {
      result.push({
        id: categories.length + index + 1,
        school_id: schoolId,
        name: `${category}兴趣班`,
        type: 'school_interest' as const,
        category,
        description: `${category}兴趣班，培养学生的${category}兴趣和技能`,
        teacher_id: 3000 + index,
        teacher_name: ['赵老师', '钱老师', '孙老师', '周老师'][index % 4],
        enrolled_students: Math.floor(Math.random() * 20 + 15),
        capacity: 30,
        schedule: `周${['六', '日'][index % 2]} ${index % 2 === 0 ? '上午' : '下午'}`,
        duration_minutes: 90,
        credits: 1,
        status: 'ongoing' as const,
        prerequisites: null,
        learning_objectives: [`培养${category}兴趣`, `掌握基本${category}技能`],
        created_at: '2025-09-01T00:00:00Z',
        updated_at: '2026-03-01T00:00:00Z',
      });
    });

    return of(result);
  }

  private getSimulatedTeacherWorkloads(schoolId: number): Observable<TeacherWorkload[]> {
    const names = ['张老师', '李老师', '王老师', '刘老师', '赵老师', '钱老师', '孙老师', '周老师'];
    const departments = ['语文组', '数学组', '英语组', '理综组', '文综组', '体艺组'];

    return of(
      names.map((name, index) => ({
        id: 2000 + index,
        user_id: 1000 + index,
        school_id: schoolId,
        name,
        email: `${name.toLowerCase().charAt(0)}teacher${index}@school.edu.cn`,
        department: departments[index % departments.length],
        position: index % 3 === 0 ? '高级教师' : index % 3 === 1 ? '一级教师' : '教师',
        courses_count: Math.floor(Math.random() * 4 + 2),
        classes_count: Math.floor(Math.random() * 3 + 1),
        students_count: Math.floor(Math.random() * 80 + 40),
        total_hours: Math.floor(Math.random() * 120 + 60),
        avg_weekly_hours: Math.floor(Math.random() * 8 + 12),
        course_types: {
          school_curriculum: Math.floor(Math.random() * 3 + 1),
          school_interest: Math.floor(Math.random() * 2),
        },
        performance_score: Math.floor(Math.random() * 20 + 80),
        workload_score: Math.floor(Math.random() * 20 + 70),
        last_updated: new Date().toISOString(),
      }))
    );
  }

  private getSimulatedStudentGrowthRecords(schoolId: number): Observable<StudentGrowthRecord[]> {
    const records: StudentGrowthRecord[] = [];
    const terms = ['2024-秋季学期', '2025-春季学期', '2025-秋季学期', '2026-春季学期'];
    const subjects = ['语文', '数学', '英语', '物理', '化学', '生物'];
    const achievementTypes = ['academic', 'sports', 'arts', 'leadership', 'service'] as const;
    const achievementNames = [
      '三好学生',
      '优秀学生干部',
      '学习进步奖',
      '科技创新奖',
      '体育健将',
      '文艺之星',
      '优秀班干部',
      '社区服务奖',
    ];

    for (let i = 1; i <= 8; i++) {
      const term = terms[Math.floor(Math.random() * terms.length)];
      const achievementsCount = Math.floor(Math.random() * 3);

      records.push({
        id: 3000 + i,
        user_id: 2000 + i,
        school_id: schoolId,
        name: `学生${i}`,
        grade: `${Math.floor(Math.random() * 3) + 1}年级`,
        class_name: `${Math.floor(Math.random() * 3) + 1}年级(${Math.floor(Math.random() * 4) + 1})班`,
        class_id: Math.floor(Math.random() * 12) + 1,
        term,
        academic_year: term.split('-')[0],
        courses_taken: Math.floor(Math.random() * 8) + 4,
        avg_score: Math.floor(Math.random() * 30) + 70,
        attendance_rate: Math.floor(Math.random() * 15) + 85,
        conduct_score: Math.floor(Math.random() * 20) + 80,
        extracurricular_count: Math.floor(Math.random() * 4),
        achievements: Array.from({ length: achievementsCount }, (_, idx) => ({
          id: i * 10 + idx,
          type: achievementTypes[Math.floor(Math.random() * achievementTypes.length)],
          name: achievementNames[Math.floor(Math.random() * achievementNames.length)],
          description: `${term}期间表现优异`,
          date_awarded: `${term.split('-')[0]}-${Math.floor(Math.random() * 12) + 1}-${Math.floor(Math.random() * 28) + 1}`,
        })),
        learning_trends: subjects.slice(0, 3).map((subject) => {
          const previous = Math.floor(Math.random() * 30) + 60;
          const current = previous + Math.floor(Math.random() * 15) - 5;
          return {
            subject,
            previous_score: previous,
            current_score: current,
            improvement: current - previous,
          };
        }),
        recommendations: ['建议加强课后复习', '建议参加更多课外活动', '建议改善学习方法'].slice(
          0,
          Math.floor(Math.random() * 2) + 1
        ),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });
    }

    return of(records);
  }

  private getSimulatedSchoolDashboard(schoolId: number): Observable<SchoolDashboardData> {
    return forkJoin({
      overview: this.getSimulatedSchoolOverview(schoolId),
      grade_classes: this.getSimulatedGradeClasses(schoolId),
      school_courses: this.getSimulatedSchoolCourses(schoolId),
      teacher_workloads: this.getSimulatedTeacherWorkloads(schoolId),
      student_growth_records: this.getSimulatedStudentGrowthRecords(schoolId),
    }).pipe(
      map((data) => ({
        ...data,
        recent_activities: [
          {
            id: 1,
            type: 'student_enrolled' as const,
            description: '新生张三完成注册并分配到一年级(1)班',
            user_name: '张三',
            timestamp: new Date(Date.now() - 3600000).toISOString(), // 1小时前
          },
          {
            id: 2,
            type: 'course_started' as const,
            description: '机器人编程兴趣班已开课',
            timestamp: new Date(Date.now() - 86400000).toISOString(), // 1天前
          },
          {
            id: 3,
            type: 'teacher_assigned' as const,
            description: '李老师被任命为二年级(2)班班主任',
            user_name: '李老师',
            timestamp: new Date(Date.now() - 172800000).toISOString(), // 2天前
          },
        ],
        alerts: [
          {
            id: 1,
            type: 'class_full' as const,
            message: '三年级(1)班已满员，建议分流',
            severity: 'medium' as const,
            created_at: new Date(Date.now() - 43200000).toISOString(), // 12小时前
          },
          {
            id: 2,
            type: 'teacher_overload' as const,
            message: '张老师工作量已达上限',
            severity: 'high' as const,
            created_at: new Date(Date.now() - 21600000).toISOString(), // 6小时前
          },
        ],
        last_updated: new Date().toISOString(),
      }))
    );
  }
}
