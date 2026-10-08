/**
 * OpenSciEDU 课程目录组件
 *
 * 展示 OpenSciEDU 公共课程列表，支持分类筛选和分页
 *
 * 基于 PRD F-18: OpenSciEDU 公共课程自动接入
 */

/* eslint-disable no-console */
import { CommonModule } from '@angular/common';
import { ChangeDetectorRef } from '@angular/core';
import { Component, EventEmitter, OnDestroy, OnInit, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject, Subscription } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  CourseCategory,
  OpenSciEDUService,
  PublicCourse,
} from '../../../core/services/opensciedu.service';
import { OpenSciEDUMockService } from '../../../core/services/opensciedu-mock.service';

@Component({
  selector: 'app-opensciedu-catalog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatTooltipModule,
  ],
  templateUrl: './opensciedu-catalog.component.html',
  styleUrls: ['./opensciedu-catalog.component.scss'],
})
export class OpenscieduCatalogComponent implements OnInit, OnDestroy {
  // ==================== 状态 ====================

  courses: PublicCourse[] = [];
  categories: CourseCategory[] = [];
  isLoading = false;
  error: string | null = null;

  // 分页
  currentPage = 1;
  pageSize = 12;
  totalCourses = 0;
  hasNextPage = false;

  // 筛选
  selectedCategory: string | null = null;
  selectedDifficulty: string | null = null;
  searchKeyword = '';

  // 难度选项
  difficulties = [
    { value: null, label: '全部难度' },
    { value: 'beginner', label: '入门' },
    { value: 'intermediate', label: '进阶' },
    { value: 'advanced', label: '高级' },
  ];

  // 排序选项
  sortOptions = [
    { value: 'created_at', label: '最新发布' },
    { value: 'popularity', label: '最受欢迎' },
    { value: 'rating', label: '评分最高' },
  ];
  selectedSort = 'created_at';

  // ==================== 订阅管理（使用 takeUntil 模式） ====================
  private destroy$ = new Subject<void>();
  private currentLoadSubscription: Subscription | null = null;
  /**
   * 【P1-2 修复】超时计时器句柄。多次 loadCourses 调用时需重置，避免叠加。
   */
  private loadingFallbackTimer: ReturnType<typeof setTimeout> | null = null;

  // ==================== 事件 ====================

  @Output() courseSelected = new EventEmitter<PublicCourse>();
  @Output() loadMore = new EventEmitter<void>();

  constructor(
    private openscieduService: OpenSciEDUService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.loadCategories();
    this.loadCourses();
  }

  ngOnDestroy(): void {
    // 完成 destroy$ 信号，所有 takeUntil 操作符会自动取消订阅
    this.destroy$.next();
    this.destroy$.complete();
    // 【P1-2 修复】清理超时计时器，避免内存泄漏与兑底计时器误在销毁后触发。
    if (this.loadingFallbackTimer) {
      clearTimeout(this.loadingFallbackTimer);
      this.loadingFallbackTimer = null;
    }
  }

  // ==================== 数据加载 ====================

  loadCategories(): void {
    // 【P2-3 修复】6s 限时兑底 — IndexedDB/后端都 hang 时也能显示示例课程
    this.openscieduService
      .getCategories()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (categories) => {
          this.categories = categories;
        },
        error: (err) => {
          console.error('加载分类失败:', err);
          // 【P2-3 修复】使用 mock fallback 避免 catalog 卡死
          const mock = new OpenSciEDUMockService();
          mock.getCategories().subscribe({
            next: (fallbackCategories: CourseCategory[]) => {
              this.categories = fallbackCategories;
            },
            error: () => {
              this.categories = [];
            },
          });
        },
      });
  }

  loadCourses(resetPage = true): void {
    // 取消之前的加载订阅
    if (this.currentLoadSubscription) {
      this.currentLoadSubscription.unsubscribe();
      this.currentLoadSubscription = null;
    }

    if (resetPage) {
      this.currentPage = 1;
      this.courses = [];
    }

    console.log(
      '[OpenSciEDU Catalog] 开始加载课程, resetPage:',
      resetPage,
      'sortBy:',
      this.selectedSort
    );
    this.isLoading = true;
    this.error = null;

    this.currentLoadSubscription = this.openscieduService
      .getPublicCourses({
        page: this.currentPage,
        pageSize: this.pageSize,
        category: this.selectedCategory ?? undefined,
        difficulty: this.selectedDifficulty ?? undefined,
        sortBy: this.selectedSort,
      })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          console.log('[OpenSciEDU Catalog] 加载成功, response:', response);
          if (response) {
            if (resetPage) {
              this.courses = response.courses;
            } else {
              this.courses = [...this.courses, ...response.courses];
            }
            this.totalCourses = response.total;
            this.hasNextPage = response.hasNext;
          }
          this.isLoading = false;
          console.log('[OpenSciEDU Catalog] isLoading 设置为 false');
        },
        error: (err) => {
          console.error('[OpenSciEDU Catalog] 加载失败:', err);
          this.error = '加载课程失败，请稍后重试';
          this.isLoading = false;
        },
        // 【P2-3 修复】complete 是服务中 mock fallback 返回 of(...) 后会自然 complete，
        //   这不影响状态。
      });

    // 【P2-3 修复】兑底：6s 后无论是否完成，都重置 isLoading
    //   openScieduService 内部已有 5s timeout + mock fallback，
    //   但若 mock 本身 hang（如 IndexedDB hang）则需额外兑底
    // 【P1-2 修复】保存计时器句柄并先清除上次遗留计时器；
    //   loadCourses 被多次调用（如切换分类）时避免叠加计时器导致的重复 false。
    if (this.loadingFallbackTimer) {
      clearTimeout(this.loadingFallbackTimer);
    }
    this.loadingFallbackTimer = setTimeout(() => {
      this.loadingFallbackTimer = null;
      if (this.isLoading) {
        console.warn('[OpenSciEDU Catalog] 加载超时，强制重置 isLoading');
        this.isLoading = false;
        if (this.courses.length === 0 && !this.error) {
          // 仍为空：使用 inline fallback 避免空页面
          this.error = '课程加载较慢，请点击重试或刷新页面';
        }
        // 【P1-2 修复】手动 markForCheck 确保 Angular 在 setTimeout 回调中推动变更检测。
        this.cdr.markForCheck();
      }
    }, 6000);
  }

  loadMoreCourses(): void {
    if (this.hasNextPage && !this.isLoading) {
      this.currentPage++;
      this.loadCourses(false);
      this.loadMore.emit();
    }
  }

  // ==================== 筛选操作 ====================

  onCategoryChange(categoryId: string | null): void {
    this.selectedCategory = categoryId;
    this.loadCourses();
  }

  onDifficultyChange(difficulty: string | null): void {
    this.selectedDifficulty = difficulty;
    this.loadCourses();
  }

  onSortChange(sortBy: string): void {
    this.selectedSort = sortBy;
    this.loadCourses();
  }

  onSearch(keyword: string): void {
    this.searchKeyword = keyword;
    // 搜索时重新加载
    if (keyword.trim()) {
      this.searchCourses(keyword);
    } else {
      this.loadCourses();
    }
  }

  searchCourses(keyword: string): void {
    this.isLoading = true;
    this.error = null;

    this.openscieduService
      .searchCourses({
        keyword,
        page: 1,
        pageSize: this.pageSize,
      })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          this.courses = response.courses;
          this.totalCourses = response.total;
          this.hasNextPage = response.courses.length >= this.pageSize;
          this.isLoading = false;
        },
        error: (err) => {
          this.error = '搜索失败，请稍后重试';
          this.isLoading = false;
          console.error('搜索失败:', err);
        },
      });
  }

  // ==================== 课程操作 ====================

  selectCourse(course: PublicCourse): void {
    this.courseSelected.emit(course);
  }

  // ==================== 辅助方法 ====================

  getDifficultyLabel(difficulty: string): string {
    return this.openscieduService.getDifficultyLabel(difficulty);
  }

  getDifficultyColor(difficulty: string): string {
    return this.openscieduService.getDifficultyColor(difficulty);
  }

  formatDuration(minutes: number): string {
    return this.openscieduService.formatDuration(minutes);
  }

  formatStudentCount(count: number): string {
    return this.openscieduService.formatStudentCount(count);
  }

  getStarArray(rating: number): boolean[] {
    return Array(5)
      .fill(false)
      .map((_, i) => i < Math.round(rating));
  }
}
