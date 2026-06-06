/**
 * 成就画廊组件
 *
 * 以网格形式展示所有成就，支持筛选、排序和搜索
 */

import { CommonModule } from '@angular/common';
import { Component, Input, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  Achievement,
  AchievementBadge,
  AchievementCategory,
  AchievementFilter,
  AchievementRarity,
  AchievementSort,
  AchievementSortBy,
  AchievementStatus,
  AchievementType,
} from '../../models/achievement.model';
import { AchievementService } from '../../services/achievement.service';

@Component({
  selector: 'app-achievement-gallery',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatFormFieldModule,
    MatSelectModule,
    MatInputModule,
    MatChipsModule,
  ],
  template: `
    <div class="gallery-container">
      <!-- 工具栏 -->
      <div class="toolbar">
        <mat-form-field appearance="outline" class="search-field">
          <mat-label>搜索成就</mat-label>
          <input
            matInput
            [(ngModel)]="filter.searchQuery"
            (ngModelChange)="onFilterChange()"
            placeholder="输入名称搜索..."
          />
          <mat-icon matSuffix>search</mat-icon>
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>分类</mat-label>
          <mat-select [(ngModel)]="filter.category" (ngModelChange)="onFilterChange()">
            <mat-option [value]="undefined">全部</mat-option>
            <mat-option *ngFor="let cat of categories" [value]="cat">
              {{ getCategoryLabel(cat) }}
            </mat-option>
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>状态</mat-label>
          <mat-select [(ngModel)]="filter.status" (ngModelChange)="onFilterChange()">
            <mat-option [value]="undefined">全部</mat-option>
            <mat-option value="locked">未解锁</mat-option>
            <mat-option value="in_progress">进行中</mat-option>
            <mat-option value="completed">已完成</mat-option>
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="filter-field">
          <mat-label>排序</mat-label>
          <mat-select
            [(ngModel)]="currentSort.sortBy"
            (ngModelChange)="onSortChange()"
          >
            <mat-option [value]="sortByName">名称</mat-option>
            <mat-option [value]="sortByDate">日期</mat-option>
            <mat-option [value]="sortByRarity">稀有度</mat-option>
            <mat-option [value]="sortByProgress">进度</mat-option>
          </mat-select>
        </mat-form-field>
      </div>

      <!-- 成就网格 -->
      <div class="achievements-grid">
        <div
          class="achievement-card"
          *ngFor="let achievement of filteredAchievements"
          [class.completed]="achievement.status === 'completed'"
          [class.locked]="achievement.status === 'locked'"
        >
          <div
            class="card-icon"
            [class.rarity-common]="achievement.rarity === 'common'"
            [class.rarity-uncommon]="achievement.rarity === 'uncommon'"
            [class.rarity-rare]="achievement.rarity === 'rare'"
            [class.rarity-epic]="achievement.rarity === 'epic'"
            [class.rarity-legendary]="achievement.rarity === 'legendary'"
          >
            <mat-icon>{{ achievement.icon }}</mat-icon>
          </div>
          <div class="card-body">
            <h4 class="card-title">{{ achievement.name }}</h4>
            <p class="card-desc">{{ achievement.description }}</p>
            <div class="card-progress">
              <mat-progress-bar
                mode="determinate"
                [value]="(achievement.progress / achievement.target) * 100"
              ></mat-progress-bar>
              <span class="progress-text">
                {{ achievement.progress }}/{{ achievement.target }}
              </span>
            </div>
            <div class="card-meta">
              <span class="meta-points">{{ achievement.points }} 积分</span>
              <span class="meta-date" *ngIf="achievement.unlockedDate">
                {{ achievement.unlockedDate | date: 'shortDate' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="empty-state" *ngIf="filteredAchievements.length === 0">
        <mat-icon>search_off</mat-icon>
        <p>未找到匹配的成就</p>
      </div>
    </div>
  `,
  styles: [
    `
      .gallery-container {
        padding: 16px;
        max-width: 1000px;
        margin: 0 auto;
      }

      .toolbar {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-bottom: 24px;
        align-items: flex-start;
      }

      .search-field {
        flex: 1;
        min-width: 200px;
      }

      .filter-field {
        width: 150px;
      }

      .achievements-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 16px;
      }

      .achievement-card {
        display: flex;
        gap: 12px;
        padding: 16px;
        border-radius: 12px;
        background: var(--color-surface, #fff);
        border: 1px solid var(--color-border, #e0e0e0);
        transition: transform 0.2s, box-shadow 0.2s;
      }

      .achievement-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      .achievement-card.locked {
        opacity: 0.5;
        filter: grayscale(1);
      }

      .achievement-card.completed {
        border-color: var(--color-success, #4caf50);
      }

      .card-icon {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
      }

      .card-icon mat-icon {
        font-size: 24px;
        width: 24px;
        height: 24px;
      }

      .rarity-common { background: #e0e0e0; color: #616161; }
      .rarity-uncommon { background: #c8e6c9; color: #2e7d32; }
      .rarity-rare { background: #bbdefb; color: #1565c0; }
      .rarity-epic { background: #e1bee7; color: #7b1fa2; }
      .rarity-legendary { background: #fff3e0; color: #e65100; }

      .card-body {
        flex: 1;
        min-width: 0;
      }

      .card-title {
        margin: 0 0 4px;
        font-size: 14px;
        font-weight: 600;
      }

      .card-desc {
        margin: 0 0 8px;
        font-size: 12px;
        color: var(--color-text-secondary, #666);
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }

      .card-progress {
        margin-bottom: 8px;
      }

      .progress-text {
        font-size: 11px;
        color: var(--color-text-secondary, #999);
      }

      .card-meta {
        display: flex;
        justify-content: space-between;
        font-size: 11px;
        color: var(--color-text-secondary, #999);
      }

      .empty-state {
        text-align: center;
        padding: 64px 16px;
        color: var(--color-text-secondary, #999);
      }

      .empty-state mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        margin-bottom: 12px;
      }
    `,
  ],
})
export class AchievementGalleryComponent implements OnInit, OnDestroy {
  @Input() userId!: number;

  categories = Object.values(AchievementCategory);

  badges: AchievementBadge[] = [];
  achievements: Achievement[] = [];

  filter: AchievementFilter = {};
  currentSort: AchievementSort = {
    sortBy: AchievementSortBy.DATE,
    ascending: false,
  };

  sortByName = AchievementSortBy.NAME;
  sortByDate = AchievementSortBy.DATE;
  sortByRarity = AchievementSortBy.RARITY;
  sortByProgress = AchievementSortBy.PROGRESS;

  filteredAchievements: Achievement[] = [];

  private destroy$ = new Subject<void>();

  constructor(private achievementService: AchievementService) {}

  ngOnInit(): void {
    this.loadAchievements();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private loadAchievements(): void {
    if (!this.userId) return;

    this.achievementService
      .getAchievements(this.userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe((badges) => {
        this.badges = badges;
        this.buildAchievements(badges);
        this.applyFilterAndSort();
      });
  }

  private buildAchievements(badges: AchievementBadge[]): void {
    this.achievements = badges.map((b) => this.mapToAchievement(b));
  }

  private mapToAchievement(badge: AchievementBadge): Achievement {
    return {
      id: badge.id,
      name: badge.name,
      icon: badge.icon,
      description: badge.description,
      type: AchievementType.BADGE,
      status: badge.unlocked ? AchievementStatus.COMPLETED : AchievementStatus.LOCKED,
      category: badge.category ?? AchievementCategory.LEARNING,
      rarity: badge.rarity ?? AchievementRarity.COMMON,
      progress: badge.unlocked ? 1 : 0,
      target: 1,
      unlockedDate: badge.unlockedDate,
      points: 0,
      tags: [],
      requirements: [],
    };
  }

  onFilterChange(): void {
    this.applyFilterAndSort();
  }

  onSortChange(): void {
    this.applyFilterAndSort();
  }

  private applyFilterAndSort(): void {
    let result = this.achievements;

    // 筛选
    if (this.filter.category) {
      result = result.filter((a) => a.category === this.filter.category);
    }
    if (this.filter.status) {
      result = result.filter((a) => a.status === this.filter.status);
    }
    if (this.filter.type) {
      result = result.filter((a) => a.type === this.filter.type);
    }
    if (this.filter.rarity) {
      result = result.filter((a) => a.rarity === this.filter.rarity);
    }
    if (this.filter.searchQuery) {
      const q = this.filter.searchQuery.toLowerCase();
      result = result.filter(
        (a) =>
          a.name.toLowerCase().includes(q) ||
          a.description.toLowerCase().includes(q)
      );
    }

    // 排序
    result.sort((a, b) => {
      let cmp = 0;
      switch (this.currentSort.sortBy) {
        case AchievementSortBy.NAME:
          cmp = a.name.localeCompare(b.name);
          break;
        case AchievementSortBy.DATE:
          cmp = (a.unlockedDate ?? '').localeCompare(b.unlockedDate ?? '');
          break;
        case AchievementSortBy.RARITY:
          cmp =
            Object.values(AchievementRarity).indexOf(a.rarity) -
            Object.values(AchievementRarity).indexOf(b.rarity);
          break;
        case AchievementSortBy.PROGRESS:
          cmp = a.progress / a.target - b.progress / b.target;
          break;
      }
      return this.currentSort.ascending ? cmp : -cmp;
    });

    this.filteredAchievements = result;
  }

  getCategoryLabel(category: AchievementCategory): string {
    const labels: Record<AchievementCategory, string> = {
      [AchievementCategory.LEARNING]: '学习',
      [AchievementCategory.EXPERIMENT]: '实验',
      [AchievementCategory.SOCIAL]: '社交',
      [AchievementCategory.CHALLENGE]: '挑战',
      [AchievementCategory.HIDDEN]: '隐藏',
    };
    return labels[category] || category;
  }
}
