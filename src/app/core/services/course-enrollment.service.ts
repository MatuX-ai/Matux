/**
 * 课程报名服务
 * 管理用户的课程报名相关操作
 */

import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, of, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';

import { environment } from '../../../environments/environment';
import type { CourseEnrollment } from '../../../shared/models/course.models';

/** Mock 选课数据集（学生ID → 选课列表） */
const MOCK_ENROLLMENTS: Record<number, CourseEnrollment[]> = {
  1: [
    {
      id: 101,
      user_id: 1,
      course_id: 1,
      org_id: 1,
      progress_percentage: 72,
      score: 85,
      status: 'active',
      enrolled_at: '2026-02-01T00:00:00Z',
      completed_at: null,
    },
    {
      id: 102,
      user_id: 1,
      course_id: 2,
      org_id: 1,
      progress_percentage: 35,
      score: null,
      status: 'active',
      enrolled_at: '2026-03-01T00:00:00Z',
      completed_at: null,
    },
    {
      id: 103,
      user_id: 1,
      course_id: 3,
      org_id: 1,
      progress_percentage: 100,
      score: 92,
      status: 'completed',
      enrolled_at: '2026-02-10T00:00:00Z',
      completed_at: '2026-04-10T00:00:00Z',
    },
    {
      id: 104,
      user_id: 1,
      course_id: 4,
      org_id: 2,
      progress_percentage: 15,
      score: null,
      status: 'active',
      enrolled_at: '2026-03-15T00:00:00Z',
      completed_at: null,
    },
    {
      id: 105,
      user_id: 1,
      course_id: 6,
      org_id: 1,
      progress_percentage: 50,
      score: 78,
      status: 'active',
      enrolled_at: '2026-02-20T00:00:00Z',
      completed_at: null,
    },
    {
      id: 106,
      user_id: 1,
      course_id: 8,
      org_id: 1,
      progress_percentage: 100,
      score: 95,
      status: 'completed',
      enrolled_at: '2026-01-15T00:00:00Z',
      completed_at: '2026-03-20T00:00:00Z',
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
  page?: number;
  page_size?: number;
  status?: 'active' | 'completed' | 'suspended';
}

@Injectable({
  providedIn: 'root',
})
export class CourseEnrollmentService {
  constructor(private http: HttpClient) {}

  /**
   * 获取用户的课程报名列表
   * @param userId 用户ID
   * @param query 查询参数（支持分页和状态筛选）
   *
   * 【P4-A】接入真实 API。优先级：
   *   1. environment.enrollmentsApiUrl (由 angular.json / env mock 配置)
   *   2. 兜底返回 mock 数据（保持以前开发体验）
   *
   *   若后端端点不存在 / 报错 → throwError，让组件进入 error 分支并触发
   *   RetryCardComponent，这是 P3-1 重试卡片端到端验证所必需的。
   */
  getUserEnrollments(
    userId: number,
    query?: EnrollmentQuery
  ): Observable<PaginatedResponse<CourseEnrollment>> {
    const realApiBase = (environment as { enrollmentsApiUrl?: string }).enrollmentsApiUrl;
    const useReal = (environment as { useRealEnrollmentsApi?: boolean }).useRealEnrollmentsApi;

    // 【P4-A】userId 必须为有效数字，否则组件会拿到 NaN/空响应但没明确错误提示。
    if (!Number.isFinite(userId) || userId <= 0) {
      return throwError(() => new Error(`无效的 userId: ${userId}`));
    }

    if (useReal && realApiBase) {
      let params = new HttpParams().set('user_id', String(userId));
      if (query?.page) params = params.set('page', String(query.page));
      if (query?.page_size) params = params.set('page_size', String(query.page_size));
      if (query?.status) params = params.set('status', query.status);
      return this.http
        .get<{ total: number; page: number; page_size: number; items: CourseEnrollment[] } | CourseEnrollment[]>(
          realApiBase,
          { params }
        )
        .pipe(
          map((raw) => {
            if (Array.isArray(raw)) {
              return {
                total: raw.length,
                page: 1,
                page_size: raw.length,
                items: raw,
              };
            }
            return raw;
          }),
          catchError((err) =>
            throwError(() => new Error(`加载选课记录失败: ${err?.message || err?.statusText || String(err)}`))
          )
        );
    }

    // 兑底：未启用真实 API 时走 mock，避免本地开发环境突兀报 error。
    let enrollments = MOCK_ENROLLMENTS[userId] ?? [];

    // 【Sprint 4 修复】根据 status 参数过滤数据
    if (query?.status) {
      enrollments = enrollments.filter((e) => e.status === query.status);
    }

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
   * 【P4-A】走真实 HTTP POST（后端 /api/v1/auth/enrollments 等），
   *   未配置 enrollmentsApiUrl 时兑底返回 mock 对象。
   */
  enrollInCourse(courseId: number, userId: number, orgId: number): Observable<CourseEnrollment> {
    const realApiBase = (environment as { enrollmentsApiUrl?: string }).enrollmentsApiUrl;
    const useReal = (environment as { useRealEnrollmentsApi?: boolean }).useRealEnrollmentsApi;

    if (useReal && realApiBase) {
      return this.http
        .post<CourseEnrollment>(realApiBase, { course_id: courseId, user_id: userId, org_id: orgId })
        .pipe(
          catchError((err) =>
            throwError(() => new Error(`报名课程失败: ${err?.message || err?.statusText || String(err)}`))
          )
        );
    }

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
