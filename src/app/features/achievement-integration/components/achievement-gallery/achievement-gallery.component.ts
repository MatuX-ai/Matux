import { CommonModule } from '@angular/common';
import { Component, EventEmitter, inject, Input, OnInit, Output } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule } from '@angular/forms';

import {
  Achievement,
  AchievementFilter,
  AchievementSort,
  AchievementSortBy,
  AchievementStatus,
  AchievementType,
} from '../../models/achievement.model';
import { AchievementService } from '../../services/achievement.service';

@Component({
  selector: 'app-achievement-gallery',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './achievement-gallery.component.html',
  styleUrls: ['./achievement-gallery.component.scss'],
})
export class AchievementGalleryComponent implements OnInit {
  @Input() userId?: number;
  @Input() moduleId?: number;
  @Input() lessonId?: number;
  @Input() layout: 'grid' | 'list' | 'timeline' = 'grid';
  @Input() filter: AchievementFilter = {};
  @Input() sortBy?: AchievementSort;
  @Output() selectionChange = new EventEmitter<Achievement[]>();

  private achievementService = inject(AchievementService);
  private fb = inject(FormBuilder);

  achievements: Achievement[] = [];
  loading = false;
  currentPage = 1;
  pageSize = 12;
  totalItems = 0;

  filterForm: FormGroup;
  activeFilters: AchievementFilter = {};

  achievementTypes: { value: AchievementType; label: string }[] = [
    { value: 'project', label: '🚀 项目案例' },
    { value: 'certificate', label: '🎓 证书' },
    { value: 'assignment', label: '📝 作业' },
    { value: 'portfolio', label: '🎨 作品集' },
    { value: 'case_study', label: '📊 案例研究' },
    { value: 'other', label: '📎 其他' },
  ];

  statusOptions: { value: AchievementStatus; label: string; color: string }[] = [
    { value: 'pending', label: '待审核', color: '#ff9800' },
    { value: 'approved', label: '已通过', color: '#4caf50' },
    { value: 'rejected', label: '已拒绝', color: '#f44336' },
    { value: 'revision', label: '需修改', color: '#ff9800' },
  ];

  selectedAchievement: Achievement | null = null;

  constructor() {
    this.filterForm = this.fb.group({
      status: [],
      type: [],
      searchQuery: [''],
    });
  }

  ngOnInit(): void {
    this.loadAchievements();
  }

  /**
   * 加载成果列表
   */
  loadAchievements(): Promise<void> {
    return new Promise((resolve) => {
      this.loading = true;

      this.achievementService
        .getAchievements(
          { ...this.activeFilters, ...this.buildContextFilter() },
          this.sortBy,
          this.currentPage,
          this.pageSize
        )
        .subscribe({
          next: (response: any) => {
            this.achievements = response.data;
            this.totalItems = response.total;
            this.loading = false;
            resolve();
          },
          error: (error: any) => {
            this.loading = false;
            resolve();
          },
        });
    });
  }

  /**
   * 构建上下文筛选
   */
  private buildContextFilter(): AchievementFilter {
    const filter: AchievementFilter = {};
    if (this.userId) filter.userId = [this.userId];
    if (this.moduleId) filter.moduleId = [this.moduleId];
    if (this.lessonId) filter.lessonId = [this.lessonId];
    return filter;
  }

  /**
   * 应用筛选
   */
  applyFilters(): void {
    this.activeFilters = {
      status: this.filterForm.value.status?.length ? this.filterForm.value.status : undefined,
      type: this.filterForm.value.type?.length ? this.filterForm.value.type : undefined,
      searchQuery: this.filterForm.value.searchQuery || undefined,
    };
    this.currentPage = 1;
    this.loadAchievements();
  }

  /**
   * 重置筛选
   */
  resetFilters(): void {
    this.filterForm.reset({
      status: [],
      type: [],
      searchQuery: '',
    });
    this.activeFilters = {};
    this.currentPage = 1;
    this.loadAchievements();
  }

  /**
   * 切换排序
   */
  sortByField(field: AchievementSortBy): void {
    if (!this.sortBy) {
      this.sortBy = { field, direction: 'desc' };
    } else if (this.sortBy.field === field) {
      this.sortBy.direction = this.sortBy.direction === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortBy.field = field;
      this.sortBy.direction = 'desc';
    }
    this.loadAchievements();
  }

  /**
   * 切换布局
   */
  changeLayout(layout: 'grid' | 'list' | 'timeline'): void {
    this.layout = layout;
  }

  /**
   * 翻页
   */
  changePage(page: number): void {
    if (page >= 1 && page <= this.getTotalPages()) {
      this.currentPage = page;
      this.loadAchievements();
    }
  }

  /**
   * 获取总页数
   */
  getTotalPages(): number {
    return Math.ceil(this.totalItems / this.pageSize);
  }

  /**
   * 选中成果
   */
  selectAchievement(achievement: Achievement): void {
    this.selectedAchievement = achievement;
  }

  /**
   * 获取成果类型标签
   */
  getTypeLabel(type: AchievementType): string {
    const typeOption = this.achievementTypes.find((t) => t.value === type);
    return typeOption?.label || type;
  }

  /**
   * 获取状态标签
   */
  getStatusLabel(status: AchievementStatus): string {
    const statusOption = this.statusOptions.find((s) => s.value === status);
    return statusOption?.label || status;
  }

  /**
   * 获取状态颜色
   */
  getStatusColor(status: AchievementStatus): string {
    const statusOption = this.statusOptions.find((s) => s.value === status);
    return statusOption?.color || '#757575';
  }

  /**
   * 格式化日期
   */
  formatDate(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      if (diffHours === 0) {
        const diffMins = Math.floor(diffMs / (1000 * 60));
        return `${diffMins} 分钟前`;
      }
      return `${diffHours} 小时前`;
    } else if (diffDays === 1) {
      return '昨天';
    } else if (diffDays < 7) {
      return `${diffDays} 天前`;
    } else {
      return date.toLocaleDateString('zh-CN');
    }
  }

  /**
   * 格式化文件大小
   */
  formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
  }

  /**
   * 获取文件图标
   */
  getFileIcon(fileName: string): string {
    const ext = fileName.split('.').pop()?.toLowerCase();
    const iconMap: { [key: string]: string } = {
      pdf: '📕',
      doc: '📘',
      docx: '📘',
      jpg: '🖼️',
      jpeg: '🖼️',
      png: '🖼️',
      gif: '🖼️',
      mp4: '🎬',
      zip: '📦',
    };
    return iconMap[ext || ''] || '📄';
  }

  /**
   * 获取分数星级
   */
  getStarRating(score: number): string {
    return '⭐'.repeat(score) + '☆'.repeat(5 - score);
  }

  /**
   * 获取摘要
   */
  getSummary(description: string, maxLength = 100): string {
    if (description.length <= maxLength) return description;
    return description.substring(0, maxLength) + '...';
  }
}
