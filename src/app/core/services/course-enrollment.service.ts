/**
 * 课程报名服务
 * 管理用户的课程报名相关操作
 */

import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

import type { CourseEnrollment } from '../../../shared/models/course.models';

/** Mock 选课数据集（学生ID → 选课列表） */
const MOCK_ENROLLMENTS: Record<number, CourseEnrollment[]> = {
  1: [
    {
      id: 101, user_id: 1, course_id: 1, org_id: 1,
      progress_percentage: 72, score: 85, status: 'active',
      enrolled_at: '2026-02-01T00:00:00Z', completed_at: null,
    },
    {
      id: 102, user_id: 1, course_id: 2, org_id: 1,
      progress_percentage: 35, score: null, status: 'active',
      enrolled_at: '2026-03-01T00:00:00Z', completed_at: null,
    },
    {
      id: 103, user_id: 1, course_id: 3, org_id: 1,
      progress_percentage: 100, score: 92, status: 'completed',
      enrolled_at: '2026-02-10T00:00:00Z', completed_at: '2026-04-10T00:00:00Z',
    },
    {
      id: 104, user_id: 1, course_id: 4, org_id: 2,
      progress_percentage: 15, score: null, status: 'active',
      enrolled_at: '2026-03-15T00:00:00Z', completed_at: null,
    },
    {
      id: 105, user_id: 1, course_id: 6, org_id: 1,
      progress_percentage: 50, score: 78, status: 'active',
      enrolled_at: '2026-02-20T00:00:00Z', completed_at: null,
    },
    {
      id: 106, user_id: 1, course_id: 8, org_id: 1,
      progress_percentage: 100, score: 95, status: 'completed',
      enrolled_at: '2026-01-15T00:00:00Z', completed_at: '2026-03-20T00:00:00Z',
    },
  ],
};

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface EnrollmentQuery {
  page: number;
  page_size: number;
}

@Injectable({
  providedIn: 'root',
})
export class CourseEnrollmentService {
  /**
   * 获取用户的课程报名列表
   */
  getUserEnrollments(userId: number, query?: EnrollmentQuery): Observable<PaginatedResponse<CourseEnrollment>> {
    const enrollments = MOCK_ENROLLMENTS[userId] ?? [];
    const page = query?.page ?? 1;
    const pageSize = query?.page_size ?? 20;
    const start = (page - 1) * pageSize;
    const paged = enrollments.slice(start, start + pageSize);
    return of({
      total: enrollments.length,
      page,
      page_size: pageSize,
      items: paged,
    });
  }

  /**
   * 报名课程
   */
  enrollInCourse(courseId: number, userId: number, orgId: number): Observable<CourseEnrollment> {
    return of({
      id: 0,
      user_id: userId,
      course_id: courseId,
      org_id: orgId,
      progress_percentage: 0,
      score: null,
      status: 'active',
      enrolled_at: new Date().toISOString(),
      completed_at: null,
    });
  }
}
