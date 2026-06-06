/**
 * 成就展示组件
 *
 * 展示用户成就徽章、进度和统计数据
 * 支持分类筛选、进度可视化和成就解锁动画
 */

import { CommonModule } from '@angular/common';
import {
  Component,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  SimpleChanges,
} from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  AchievementBadge,
  AchievementCategory,
  AchievementProgress,
  AchievementRarity,
  AchievementStats,
} from '../../models/achievement.model';
import { AchievementService } from '../../services/achievement.service';

@Component({
  selector: 'app-achievement-display',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTabsModule,
    MatTooltipModule,
  ],
  template: `
    <div class="achievement-display">
      <!-- 概览卡片 -->
      <mat-card class="overview-card">
        <mat-card-content>
          <div class="stats-row">
            <div class="stat-item">
              <span class="stat-value">{{ stats.badgesCount }}</span>
              <span class="stat-label">成就数</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.totalPoints }}</span>
              <span class="stat-label">总积分</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ stats.currentStreak }}</span>
              <span class="stat-label">连续天数</span>
            </div>
          </div>

          <!-- 总体进度 -->
          <div class="progress-section">
            <div class="progress-header">
              <span>总体进度</span>
              <span>{{ progress.unlockedBadges }}/{{ progress.totalBadges }}</span>
            </div>
            <mat-progress-bar
              mode="determinate"
              [value]="progress.overallProgress"
            ></mat-progress-bar>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- 分类标签 -->
      <mat-tab-group
        (selectedTabChange)="onCategoryChange($event.index)"
        [selectedIndex]="selectedCategoryIndex"
      >
        <mat-tab label="全部">
          <div class="badges-grid">
            <div
              class="badge-card"
              *ngFor="let badge of filteredBadges"
              [class.unlocked]="badge.unlocked"
              [class.locked]="!badge.unlocked"
              [matTooltip]="badge.description"
            >
              <div class="badge-icon" [class.rarity-common]="badge.rarity === 'common'"
                   [class.rarity-uncommon]="badge.rarity === 'uncommon'"
                   [class.rarity-rare]="badge.rarity === 'rare'"
                   [class.rarity-epic]="badge.rarity === 'epic'"
                   [class.rarity-legendary]="badge.rarity === 'legendary'">
                <mat-icon>{{ badge.icon }}</mat-icon>
              </div>
              <div class="badge-name">{{ badge.name }}</div>
              <div class="badge-date" *ngIf="badge.unlockedDate">
                {{ badge.unlockedDate | date:'shortDate' }}
              </div>
            </div>

            <div class="empty-state" *ngIf="filteredBadges.length === 0">
              <mat-icon>emoji_events</mat-icon>
              <p>暂无成就数据</p>
            </div>
          </div>
        </mat-tab>

        <mat-tab *ngFor="let cat of categories" [label]="getCategoryLabel(cat)">
          <div class="badges-grid">
            <div
              class="badge-card"
              *ngFor="let badge of getBadgesByCategory(cat)"
              [class.unlocked]="badge.unlocked"
              [class.locked]="!badge.unlocked"
              [matTooltip]="badge.description"
            >
              <div class="badge-icon" [class.rarity-common]="badge.rarity === 'common'"
                   [class.rarity-uncommon]="badge.rarity === 'uncommon'"
                   [class.rarity-rare]="badge.rarity === 'rare'"
                   [class.rarity-epic]="badge.rarity === 'epic'"
                   [class.rarity-legendary]="badge.rarity === 'legendary'">
                <mat-icon>{{ badge.icon }}</mat-icon>
              </div>
              <div class="badge-name">{{ badge.name }}</div>
              <div class="badge-date" *ngIf="badge.unlockedDate">
                {{ badge.unlockedDate | date:'shortDate' }}
              </div>
            </div>
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [
    `
      .achievement-display {
        padding: 16px;
        max-width: 900px;
        margin: 0 auto;
      }

      .overview-card {
        margin-bottom: 24px;
      }

      .stats-row {
        display: flex;
        justify-content: space-around;
        margin-bottom: 16px;
      }

      .stat-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
      }

      .stat-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--color-primary, #1976d2);
      }

      .stat-label {
        font-size: 14px;
        color: var(--color-text-secondary, #666);
      }

      .progress-section {
        padding-top: 8px;
        border-top: 1px solid var(--color-border, #e0e0e0);
      }

      .progress-header {
        display: flex;
        justify-content: space-between;
        margin-bottom: 8px;
        font-size: 14px;
        color: var(--color-text-secondary, #666);
      }

      .badges-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 16px;
        padding: 16px 0;
      }

      .badge-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 16px 8px;
        border-radius: 12px;
        background: var(--color-surface, #fff);
        border: 1px solid var(--color-border, #e0e0e0);
        transition: transform 0.2s, box-shadow 0.2s;
        cursor: pointer;
        text-align: center;
      }

      .badge-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      }

      .badge-card.unlocked {
        opacity: 1;
      }

      .badge-card.locked {
        opacity: 0.45;
        filter: grayscale(1);
      }

      .badge-icon {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 8px;
      }

      .badge-icon mat-icon {
        font-size: 28px;
        width: 28px;
        height: 28px;
      }

      .rarity-common { background: #e0e0e0; color: #616161; }
      .rarity-uncommon { background: #c8e6c9; color: #2e7d32; }
      .rarity-rare { background: #bbdefb; color: #1565c0; }
      .rarity-epic { background: #e1bee7; color: #7b1fa2; }
      .rarity-legendary { background: #fff3e0; color: #e65100; }

      .badge-name {
        font-size: 13px;
        font-weight: 500;
        line-height: 1.3;
        color: var(--color-text-primary, #212121);
      }

      .badge-date {
        font-size: 11px;
        color: var(--color-text-secondary, #999);
        margin-top: 4px;
      }

      .empty-state {
        grid-column: 1 / -1;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 48px;
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
export class AchievementDisplayComponent implements OnInit, OnChanges, OnDestroy {
  @Input() userId!: number;

  badges: AchievementBadge[] = [];
  filteredBadges: AchievementBadge[] = [];
  progress: AchievementProgress = {
    totalBadges: 0,
    unlockedBadges: 0,
    overallProgress: 0,
    completionPercentage: 0,
    averageScore: 0,
    totalAchievements: 0,
    completedAchievements: 0,
    categoryProgress: {} as Record<AchievementCategory, number>,
    recentUnlocks: [],
    milestones: [],
  };
  stats: AchievementStats = {
    totalPoints: 0,
    badgesCount: 0,
    currentStreak: 0,
    longestStreak: 0,
    lastActiveDate: '',
  };

  categories = Object.values(AchievementCategory);
  selectedCategoryIndex = 0;

  private destroy$ = new Subject<void>();

  constructor(private achievementService: AchievementService) {}

  ngOnInit(): void {
    this.loadData();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['userId'] && !changes['userId'].isFirstChange()) {
      this.loadData();
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * 加载所有成就数据
   */
  private loadData(): void {
    if (!this.userId) {
      return;
    }

    this.achievementService
      .getAchievements(this.userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe((badges) => {
        this.badges = badges;
        this.filteredBadges = badges;
      });

    this.achievementService
      .getProgress(this.userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe((progress) => {
        this.progress = progress;
      });

    this.achievementService
      .getStats(this.userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe((stats) => {
        this.stats = stats;
      });
  }

  /**
   * 分类切换
   */
  onCategoryChange(index: number): void {
    this.selectedCategoryIndex = index;
    if (index === 0) {
      this.filteredBadges = this.badges;
    }
  }

  /**
   * 按分类获取徽章
   */
  getBadgesByCategory(category: AchievementCategory): AchievementBadge[] {
    return this.badges.filter((b) => b.category === category);
  }

  /**
   * 获取分类显示名称
   */
  getCategoryLabel(category: AchievementCategory): string {
    const labels: Record<AchievementCategory, string> = {
      [AchievementCategory.LEARNING]: '学习',
      [AchievementCategory.EXPERIMENT]: '实验',
      [AchievementCategory.SOCIAL]: '社交',
      [AchievementCategory.CHALLENGE]: '挑战',
      [AchievementCategory.HIDDEN]: '隐藏',
    };
    return labels[category];
  }
}
