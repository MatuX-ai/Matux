/**
 * 统一课程服务
 * 跨来源课程的统一查询接口
 */

import { Injectable } from '@angular/core';
import { Observable, of } from 'rxjs';

import type { UnifiedCourse } from '../../../shared/models/course.models';

/** Mock 课程数据集 */
const MOCK_COURSES: UnifiedCourse[] = [
  {
    id: 1,
    org_id: 1,
    title: 'Python 基础编程',
    description: '从零开始学习 Python 编程语言，掌握变量、循环、函数等核心概念。',
    cover_image_url: null,
    category: 'programming',
    difficulty: 'beginner',
    duration_minutes: 480,
    status: 'published',
    source_type: 'school_curriculum',
    teacher_name: '张老师',
    tags: ['python', '入门', '编程'],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-03-15T00:00:00Z',
  },
  {
    id: 2,
    org_id: 1,
    title: '数据结构入门',
    description: '学习数组、链表、栈、队列等基本数据结构及简单算法。',
    cover_image_url: null,
    category: 'programming',
    difficulty: 'intermediate',
    duration_minutes: 600,
    status: 'published',
    source_type: 'school_curriculum',
    teacher_name: '李老师',
    tags: ['dsa', '算法', '数据结构'],
    created_at: '2026-01-15T00:00:00Z',
    updated_at: '2026-04-01T00:00:00Z',
  },
  {
    id: 3,
    org_id: 1,
    title: 'STEM 科学实验',
    description: '通过动手实验探索物理、化学、生物等科学原理。',
    cover_image_url: null,
    category: 'science',
    difficulty: 'beginner',
    duration_minutes: 360,
    status: 'published',
    source_type: 'school_interest',
    teacher_name: '王老师',
    tags: ['stem', '实验', '科学'],
    created_at: '2026-02-01T00:00:00Z',
    updated_at: '2026-04-10T00:00:00Z',
  },
  {
    id: 4,
    org_id: 2,
    title: '3D 建模入门',
    description: '使用 Tinkercad 学习 3D 建模基础，创建属于自己的 3D 作品。',
    cover_image_url: null,
    category: 'art',
    difficulty: 'intermediate',
    duration_minutes: 420,
    status: 'published',
    source_type: 'institution',
    teacher_name: '赵老师',
    tags: ['3d', '建模', '设计'],
    created_at: '2026-03-01T00:00:00Z',
    updated_at: '2026-04-15T00:00:00Z',
  },
  {
    id: 5,
    org_id: 3,
    title: 'Scratch 游戏设计',
    description: '用 Scratch 制作互动游戏，培养逻辑思维和创造力。',
    cover_image_url: null,
    category: 'programming',
    difficulty: 'beginner',
    duration_minutes: 300,
    status: 'published',
    source_type: 'online_platform',
    teacher_name: '刘老师',
    tags: ['scratch', '游戏', '创意'],
    created_at: '2026-02-15T00:00:00Z',
    updated_at: '2026-04-20T00:00:00Z',
  },
  {
    id: 6,
    org_id: 1,
    title: '数学思维训练',
    description: '通过趣味数学题培养逻辑推理和数学思维能力。',
    cover_image_url: null,
    category: 'math',
    difficulty: 'beginner',
    duration_minutes: 360,
    status: 'published',
    source_type: 'school_curriculum',
    teacher_name: '陈老师',
    tags: ['数学', '逻辑', '思维'],
    created_at: '2026-01-20T00:00:00Z',
    updated_at: '2026-04-05T00:00:00Z',
  },
  {
    id: 7,
    org_id: 2,
    title: '机器人编程入门',
    description: '学习机器人硬件搭建和编程控制，参加机器人竞赛。',
    cover_image_url: null,
    category: 'science',
    difficulty: 'intermediate',
    duration_minutes: 540,
    status: 'published',
    source_type: 'institution',
    teacher_name: '周老师',
    tags: ['机器人', '硬件', '编程'],
    created_at: '2026-03-10T00:00:00Z',
    updated_at: '2026-04-18T00:00:00Z',
  },
  {
    id: 8,
    org_id: 1,
    title: '英语绘本阅读',
    description: '通过英文原版绘本提升英语阅读能力和语感。',
    cover_image_url: null,
    category: 'language',
    difficulty: 'beginner',
    duration_minutes: 240,
    status: 'published',
    source_type: 'school_interest',
    teacher_name: '吴老师',
    tags: ['英语', '阅读', '绘本'],
    created_at: '2026-02-01T00:00:00Z',
    updated_at: '2026-03-30T00:00:00Z',
  },
];

@Injectable({
  providedIn: 'root',
})
export class UnifiedCourseService {
  /**
   * 获取单个课程详情
   */
  getCourse(courseId: number): Observable<UnifiedCourse> {
    const found = MOCK_COURSES.find((c) => c.id === courseId);
    return of(
      found ?? {
        id: courseId,
        org_id: 1,
        title: '未知课程',
        description: '',
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
      }
    );
  }

  /**
   * 批量获取课程详情
   */
  getCoursesBatch(courseIds: number[]): Observable<UnifiedCourse[]> {
    const courses = MOCK_COURSES.filter((c) => courseIds.includes(c.id));
    return of(courses);
  }

  /**
   * 获取推荐课程列表
   */
  getRecommendedCourses(userId: number, limit: number): Observable<UnifiedCourse[]> {
    const recommended = MOCK_COURSES.filter((c) => c.status === 'published').slice(0, limit);
    return of(recommended);
  }

  /**
   * 获取最新课程列表
   */
  getNewestCourses(limit: number): Observable<UnifiedCourse[]> {
    const newest = [...MOCK_COURSES]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, limit);
    return of(newest);
  }
}
