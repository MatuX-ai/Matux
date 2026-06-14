/* eslint-disable max-lines-per-function */
/**
 * 我的课程页面
 *
 * PRD 6.6 关键页面线框 - "我的课程"
 * 展示：已选课程列表、学习进度、课程分类筛选
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import type { CourseEnrollment, UnifiedCourse } from '../../../../shared/models/course.models';
import type { User } from '../../../core/models/auth.models';
import { AuthService } from '../../../core/services/auth.service';
import { CourseEnrollmentService } from '../../../core/services/course-enrollment.service';
import { UnifiedCourseService } from '../../../core/services/unified-course.service';

interface EnrolledCourse {
  course: UnifiedCourse;
  enrollment: CourseEnrollment;
}

@Component({
  selector: 'app-my-courses',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatButtonModule,
    MatProgressBarModule,
    MatChipsModule,
    MatTabsModule,
    MatTooltipModule,
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './my-courses.component.html',
  styleUrls: ['./my-courses.component.scss'],
})
export class MyCoursesComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  enrolledCourses: EnrolledCourse[] = [];
  filteredCourses: EnrolledCourse[] = [];
  activeTab = 0;
  loading = true;
  loadingSources = false;
  loadingRecommendations = false;

  // 学习来源数据
  learningSources: Array<{
    id: number;
    name: string;
    source_type: string;
    is_primary: boolean;
    start_date?: string;
    end_date?: string;
    courses?: number;
    completed?: number;
    avg_score?: number;
  }> = [];

  // 推荐课程数据
  recommendedCourses: UnifiedCourse[] = [];

  currentUser: User | null = null;

  readonly Math = Math;

  readonly categoryIcon: Record<string, string> = {
    programming: '💻',
    science: '🔬',
    math: '📐',
    art: '🎨',
    music: '🎵',
    language: '🌍',
    general: '📚',
  };

  constructor(
    private courseEnrollmentService: CourseEnrollmentService,
    private unifiedCourseService: UnifiedCourseService,
    private authService: AuthService,
    private router: Router,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      this.currentUser = user;
      if (user?.id) {
        const userId = Number(user.id);
        this.loadCourses(userId);
        this.loadLearningSources(userId);
        this.loadRecommendations(userId);
      }
    });
  }

  /**
   * 加载学习来源数据
   */
  private loadLearningSources(_userId: number): void {
    this.loadingSources = true;
    // TODO: 替换为实际的API调用
    // 暂时使用Mock数据
    setTimeout(() => {
      this.learningSources = [
        {
          id: 1,
          name: '校本部',
          source_type: 'school_curriculum',
          is_primary: true,
          start_date: '2025-09-01',
          end_date: '2026-07-31',
          courses: 3,
          completed: 1,
          avg_score: 88,
        },
        {
          id: 2,
          name: '创新机器人培训中心',
          source_type: 'institution',
          is_primary: false,
          start_date: '2025-10-15',
          end_date: '2026-06-30',
          courses: 2,
          completed: 0,
          avg_score: 83,
        },
        {
          id: 3,
          name: '校内兴趣班',
          source_type: 'school_interest',
          is_primary: false,
          start_date: '2025-11-01',
          end_date: '2026-05-31',
          courses: 1,
          completed: 0,
          avg_score: undefined,
        },
      ];
      this.loadingSources = false;
      this.cdr.markForCheck();
    }, 500);
  }

  /**
   * 加载推荐课程数据
   */
  private loadRecommendations(_userId: number): void {
    this.loadingRecommendations = true;
    // TODO: 替换为实际的API调用
    // 暂时使用Mock数据
    setTimeout(() => {
      this.recommendedCourses = [
        {
          id: 201,
          org_id: 1,
          title: 'ROS机器人操作系统',
          description: '学习ROS机器人操作系统的核心概念，包括节点通信、导航SLAM、机械臂控制等。',
          cover_image_url: null,
          category: 'programming',
          difficulty: 'advanced',
          duration_minutes: 2400,
          status: 'published',
          source_type: 'institution',
          teacher_name: '博士坦老师',
          tags: ['ROS', '机器人', 'SLAM'],
          created_at: '2025-01-01',
          updated_at: '2025-06-01',
        },
        {
          id: 202,
          org_id: 1,
          title: 'Python机器学习入门',
          description: '掌握Python和Scikit-Learn基础，学习监督学习和无监督学习的核心算法。',
          cover_image_url: null,
          category: 'science',
          difficulty: 'intermediate',
          duration_minutes: 1800,
          status: 'published',
          source_type: 'institution',
          teacher_name: '小M老师',
          tags: ['Python', '机器学习', 'AI'],
          created_at: '2025-01-01',
          updated_at: '2025-06-01',
        },
        {
          id: 203,
          org_id: 1,
          title: 'Arduino智能硬件开发',
          description: '从零开始学习Arduino开发板，掌握传感器、执行器的编程控制。',
          cover_image_url: null,
          category: 'programming',
          difficulty: 'beginner',
          duration_minutes: 1200,
          status: 'published',
          source_type: 'institution',
          teacher_name: '小X老师',
          tags: ['Arduino', '硬件', '物联网'],
          created_at: '2025-01-01',
          updated_at: '2025-06-01',
        },
      ];
      this.loadingRecommendations = false;
      this.cdr.markForCheck();
    }, 500);
  }

  private loadCourses(userId: number): void {
    this.loading = true;
    this.courseEnrollmentService
      .getUserEnrollments(userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          const enrollments = response.items;
          if (enrollments.length === 0) {
            this.enrolledCourses = [];
            this.applyFilter();
            this.loading = false;
            this.cdr.markForCheck();
            return;
          }

          const courseIds = enrollments
            .map((e) => e.course_id)
            .filter((id): id is number => id != null);

          // 【P2修复】处理空课程ID数组
          if (courseIds.length === 0) {
            console.warn('[MyCourses] 所有选课记录都缺少课程ID');
            this.enrolledCourses = [];
            this.applyFilter();
            this.loading = false;
            this.cdr.markForCheck();
            return;
          }

          this.unifiedCourseService
            .getCoursesBatch(courseIds)
            .pipe(takeUntil(this.destroy$))
            .subscribe({
              next: (courses) => {
                const courseMap = new Map(courses.map((c) => [c.id, c]));
                this.enrolledCourses = enrollments
                  .map((enrollment) => {
                    const course = courseMap.get(enrollment.course_id);
                    return course ? { course, enrollment } : null;
                  })
                  .filter((item): item is EnrolledCourse => item !== null);
                this.applyFilter();
                this.loading = false;
                this.cdr.markForCheck();
              },
              error: (err) => {
                console.error('[MyCourses] 加载课程失败:', err);
                this.enrolledCourses = [];
                this.applyFilter();
                this.loading = false;
                this.cdr.markForCheck();
              },
            });
        },
        error: (err) => {
          console.error('[MyCourses] 加载选课记录失败:', err);
          this.enrolledCourses = [];
          this.applyFilter();
          this.loading = false;
          this.cdr.markForCheck();
        },
      });
  }

  onTabChange(_index: number): void {
    this.applyFilter();
  }

  private applyFilter(): void {
    if (this.activeTab === 0) {
      this.filteredCourses = [...this.enrolledCourses];
    } else {
      const status = this.activeTab === 1 ? 'active' : 'completed';
      this.filteredCourses = this.getCoursesByStatus(status);
    }
  }

  getCoursesByStatus(status: string): EnrolledCourse[] {
    return this.enrolledCourses.filter((item) => item.enrollment.status === status);
  }

  difficultyLabel(d: string): string {
    const map: Record<string, string> = {
      beginner: '入门',
      intermediate: '进阶',
      advanced: '高级',
    };
    return map[d] ?? d;
  }

  sourceTypeLabel(t: string): string {
    const map: Record<string, string> = {
      school_curriculum: '校本课程',
      school_interest: '校内兴趣班',
      institution: '培训机构',
      self_study: '自学',
      online_platform: '在线平台',
      competition: '竞赛',
    };
    return map[t] ?? t;
  }

  isHighScore(score: number | null | undefined): boolean {
    return (score ?? 0) >= 80;
  }

  getCategoryIcon(category: string): string {
    return this.categoryIcon[category] || '📘';
  }

  /**
   * 获取学习来源图标
   */
  getSourceIcon(type: string): string {
    const icons: Record<string, string> = {
      school_curriculum: 'school',
      school_interest: 'palette',
      institution: 'business',
      self_study: 'self_improvement',
      online_platform: 'computer',
      competition: 'emoji_events',
    };
    return icons[type] || 'source';
  }

  /**
   * 报名推荐课程 - 跳转到内容商店
   */
  enrollCourse(course: UnifiedCourse): void {
    // 跳转到内容商店并携带课程信息
    void this.router.navigate(['/content-store'], {
      queryParams: { courseId: course.id },
    });
  }

  /**
   * 获取学习来源类型标签
   */
  getSourceTypeLabel(type: string): string {
    const labels: Record<string, string> = {
      school_curriculum: '校本课程',
      school_interest: '校内兴趣班',
      institution: '培训机构',
      self_study: '自学',
      online_platform: '在线平台',
      competition: '竞赛',
    };
    return labels[type] || type;
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
