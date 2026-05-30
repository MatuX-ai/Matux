/**
 * 统一课程服务
 * 跨来源课程的统一查询接口
 */

import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

import type { UnifiedCourse } from '../../../shared/models/course.models';

@Injectable({
  providedIn: 'root',
})
export class UnifiedCourseService {
  /**
   * 获取单个课程详情
   */
  getCourse(courseId: number): Observable<UnifiedCourse> {
    return of({
      id: courseId,
      org_id: 1,
      title: '课程',
      description: '课程详情',
      cover_image_url: null,
      category: 'general',
      difficulty: 'beginner',
      duration_minutes: 60,
      status: 'published',
      source_type: 'school_curriculum',
      teacher_name: null,
      tags: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });
  }

  /**
   * 获取推荐课程列表
   */
  getRecommendedCourses(userId: number, limit: number): Observable<UnifiedCourse[]> {
    return of([]);
  }

  /**
   * 获取最新课程列表
   */
  getNewestCourses(limit: number): Observable<UnifiedCourse[]> {
    return of([]);
  }
}
