/**
 * 课程详情页面
 *
 * 展示单门课程的元信息、章节列表、学习进度，并提供"继续学习"入口
 * 路由: ROUTES.USER.COURSE_DETAIL (即 /user/courses/:courseId)
 * 子路由 ROUTES.USER.COURSE_LEARN 渲染本组件并直接定位到学习面板
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
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { of, Subject } from 'rxjs';
import { catchError, takeUntil } from 'rxjs/operators';

import { AuthService } from '../../../core/services/auth.service';
import { CourseEnrollmentService } from '../../../core/services/course-enrollment.service';
import { UnifiedCourseService } from '../../../core/services/unified-course.service';
import type { UnifiedCourse } from '../../../models/unified-course.models';
import { ROUTES } from '../../../routes.const';

interface CourseChapter {
  id: number;
  title: string;
  duration_minutes: number;
  completed: boolean;
}

@Component({
  selector: 'app-course-detail',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    CommonModule,
    RouterModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatDividerModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
    MatTabsModule,
    MatTooltipModule,
    MatSnackBarModule,
  ],
  templateUrl: './course-detail.component.html',
  styleUrls: ['./course-detail.component.scss'],
})
export class CourseDetailComponent implements OnInit, OnDestroy {
  courseId = 0;
  // 使用 UnifiedCourse 类型,缺失字段全部可选
  course: UnifiedCourse | null = null;
  chapters: CourseChapter[] = [];
  progressPercent = 0;
  loading = true;
  error: string | null = null;
  enrolled = false;

  private destroy$ = new Subject<void>();
  readonly ROUTES = ROUTES;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService,
    private unifiedCourseService: UnifiedCourseService,
    private courseEnrollmentService: CourseEnrollmentService,
    private snackBar: MatSnackBar,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.courseId = Number(this.route.snapshot.paramMap.get('courseId'));

    if (!this.courseId || Number.isNaN(this.courseId)) {
      this.error = '课程 ID 无效';
      this.loading = false;
      this.cdr.markForCheck();
      return;
    }

    this.loadCourse();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadCourse(): void {
    this.loading = true;
    this.error = null;

    this.unifiedCourseService
      .getCoursesBatch([this.courseId])
      .pipe(
        catchError((err: Error) => {
          console.error('[CourseDetail] 加载课程失败:', err);
          this.error = '加载课程失败，请稍后重试';
          this.loading = false;
          this.cdr.markForCheck();
          return of([]);
        }),
        takeUntil(this.destroy$)
      )
      .subscribe((courses) => {
        const course = courses.find((c) => c.id === this.courseId) ?? null;
        if (!course) {
          this.error = '未找到该课程';
          this.loading = false;
          this.cdr.markForCheck();
          return;
        }

        this.course = course;
        this.chapters = this.buildMockChapters(course);
        this.loading = false;
        this.cdr.markForCheck();
        this.loadEnrollment();
      });
  }

  private loadEnrollment(): void {
    const user = this.authService.getCurrentUser();
    if (!user?.id) {
      this.enrolled = false;
      this.progressPercent = 0;
      this.cdr.markForCheck();
      return;
    }

    this.courseEnrollmentService
      .getUserEnrollments(Number(user.id))
      .pipe(
        catchError(() => of({ items: [] })),
        takeUntil(this.destroy$)
      )
      .subscribe((response) => {
        const enrollment = response.items.find((e) => e.course_id === this.courseId);
        this.enrolled = !!enrollment;
        this.progressPercent = Math.round(enrollment?.progress_percentage ?? 0);
        this.cdr.markForCheck();
      });
  }

  /**
   * 后端暂无章节 API，使用基于课程难度的占位章节列表
   * 后续接入后端 `course_chapters` 表后替换
   */
  private buildMockChapters(course: {
    duration_minutes?: number;
    difficulty?: string;
  }): CourseChapter[] {
    const totalMinutes = course.duration_minutes ?? 60;
    const chapterCount = Math.max(3, Math.min(8, Math.round(totalMinutes / 30)));
    const list: CourseChapter[] = [];
    for (let i = 0; i < chapterCount; i++) {
      list.push({
        id: i + 1,
        title: `第 ${i + 1} 章 · ${this.chapterTitleByDifficulty(course.difficulty, i)}`,
        duration_minutes: Math.round(totalMinutes / chapterCount),
        completed: i < 1, // 默认第一节完成，提供可视化进度
      });
    }
    return list;
  }

  private chapterTitleByDifficulty(difficulty: string | undefined, index: number): string {
    const labels = ['入门', '基础', '进阶', '实践', '综合', '挑战', '拓展', '总结'];
    const key = (difficulty ?? 'beginner') + ':' + (index % labels.length);
    const map: Record<string, string> = {
      'beginner:0': '环境搭建',
      'beginner:1': '第一个示例',
      'beginner:2': '动手练习',
      'intermediate:0': '核心概念',
      'intermediate:1': 'API 实战',
      'intermediate:2': '进阶技巧',
      'advanced:0': '架构设计',
      'advanced:1': '性能优化',
      'advanced:2': '源码剖析',
    };
    return map[key] ?? labels[index % labels.length] ?? '章节内容';
  }

  difficultyLabel(d: string | undefined): string {
    const map: Record<string, string> = {
      beginner: '入门',
      intermediate: '进阶',
      advanced: '高级',
    };
    return map[d ?? ''] ?? '入门';
  }

  /**
   * 【P3 修复】获取分类的语义化标签(用于 aria-label 与图标映射)
   */
  getCategoryAriaLabel(category: string | undefined): string {
    const map: Record<string, string> = {
      programming: '编程开发',
      science: '科学实验',
      math: '数学',
      art: '艺术设计',
      music: '音乐',
      language: '语言',
      general: '通用',
    };
    return map[category ?? ''] ?? '通用';
  }

  continueLearning(): void {
    if (!this.enrolled) {
      this.enrollAndLearn();
      return;
    }
    void this.router.navigate([
      ROUTES.USER.COURSE_LEARN.replace(':courseId', String(this.courseId)),
    ]);
  }

  enrollAndLearn(): void {
    const user = this.authService.getCurrentUser();
    if (!user?.id) {
      this.snackBar.open('请先登录后再报名', '关闭', { duration: 2000 });
      void this.router.navigate([ROUTES.AUTH.LOGIN]);
      return;
    }

    this.courseEnrollmentService
      .enrollInCourse(this.courseId, Number(user.id), 1)
      .pipe(
        catchError((err: Error) => {
          this.snackBar.open(`报名失败：${err.message}`, '关闭', { duration: 3000 });
          return of(null);
        }),
        takeUntil(this.destroy$)
      )
      .subscribe((res) => {
        if (res) {
          this.enrolled = true;
          this.progressPercent = 0;
          this.snackBar.open('报名成功，开始学习', '关闭', { duration: 2000 });
          void this.router.navigate([
            ROUTES.USER.COURSE_LEARN.replace(':courseId', String(this.courseId)),
          ]);
        }
      });
  }

  goBack(): void {
    void this.router.navigate([ROUTES.USER.COURSES]);
  }
}
