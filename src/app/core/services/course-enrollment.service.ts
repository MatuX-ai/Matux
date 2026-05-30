/**
 * 课程报名服务
 * 管理用户的课程报名相关操作
 */

import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

import type { CourseEnrollment } from '../../../shared/models/course.models';

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
    return of({
      total: 0,
      page: query?.page ?? 1,
      page_size: query?.page_size ?? 10,
      items: [],
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
