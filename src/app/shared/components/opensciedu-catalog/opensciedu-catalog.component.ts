/**
 * OpenSciEDU 课程目录组件
 *
 * 展示 OpenSciEDU 公共课程列表，支持分类筛选和分页
 *
 * 基于 PRD F-18: OpenSciEDU 公共课程自动接入
 */

import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
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

import {
  CourseCategory,
  CourseDetail,
  OpenSciEDUService,
  PublicCourse,
} from '../../../core/services/opensciedu.service';

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
export class OpenscieduCatalogComponent implements OnInit {
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

  // ==================== 事件 ====================

  @Output() courseSelected = new EventEmitter<PublicCourse>();
  @Output() loadMore = new EventEmitter<void>();

  constructor(private openscieduService: OpenSciEDUService) {}

  ngOnInit(): void {
    this.loadCategories();
    this.loadCourses();
  }

  // ==================== 数据加载 ====================

  loadCategories(): void {
    this.openscieduService.getCategories().subscribe({
      next: (categories) => {
        this.categories = categories;
      },
      error: (err) => {
        console.error('加载分类失败:', err);
      },
    });
  }

  loadCourses(resetPage = true): void {
    if (resetPage) {
      this.currentPage = 1;
      this.courses = [];
    }

    this.isLoading = true;
    this.error = null;

    this.openscieduService
      .getPublicCourses({
        page: this.currentPage,
        pageSize: this.pageSize,
        category: this.selectedCategory || undefined,
        difficulty: this.selectedDifficulty || undefined,
        sortBy: this.selectedSort,
      })
      .subscribe({
        next: (response) => {
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
        },
        error: (err) => {
          this.error = '加载课程失败，请稍后重试';
          this.isLoading = false;
          console.error('加载课程失败:', err);
        },
      });
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
