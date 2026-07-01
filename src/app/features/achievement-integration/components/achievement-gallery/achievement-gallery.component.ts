/**
 * 成就画廊组件
 *
 * 以网格形式展示所有成就，支持筛选、排序和搜索
 * 点击徽章弹出详情弹窗（条件清单/进度条/区块链认证/分享下载）
 * 传说徽章带旋转光效
 */

import { animate, state, style, transition, trigger } from '@angular/animations';
import { CommonModule } from '@angular/common';
import { Component, Inject, Input, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MAT_DIALOG_DATA, MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  Achievement,
  AchievementBadge,
  AchievementCategory,
  AchievementCondition,
  AchievementFilter,
  AchievementRarity,
  AchievementSort,
  AchievementSortBy,
  AchievementStatus,
  AchievementType,
} from '../../models/achievement.model';
import { AchievementService } from '../../services/achievement.service';

// ============ 稀有度配置 ============
const RARITY_CONFIG: Record<AchievementRarity, { label: string; color: string; bg: string; border: string; glow: string }> = {
  common: { label: '普通', color: '#64748b', bg: '#f1f5f9', border: '#e2e8f0', glow: '' },
  uncommon: { label: '少见', color: '#047857', bg: '#d1fae5', border: '#a7f3d0', glow: '' },
  rare: { label: '稀有', color: '#0284c7', bg: '#bae6fd', border: '#7dd3fc', glow: '0 0 12px rgba(2,132,199,0.2)' },
  epic: { label: '史诗', color: '#7c3aed', bg: '#ede9fe', border: '#c4b5fd', glow: '0 0 16px rgba(124,58,237,0.3)' },
  legendary: { label: '传说', color: '#b45309', bg: '#fef3c7', border: '#fcd34d', glow: '0 0 20px rgba(245,158,11,0.4)' },
};

const CATEGORY_LABELS: Record<AchievementCategory, string> = {
  [AchievementCategory.LEARNING]: '学习',
  [AchievementCategory.EXPERIMENT]: '实验',
  [AchievementCategory.SOCIAL]: '社交',
  [AchievementCategory.CHALLENGE]: '挑战',
  [AchievementCategory.HIDDEN]: '隐藏',
};

// ============ 弹窗数据接口 ============
export interface AchievementDialogData {
  id: string;
  name: string;
  icon: string;
  description: string;
  status: AchievementStatus;
  category: AchievementCategory;
  rarity: AchievementRarity;
  progress: number;
  target: number;
  unlockedDate?: string;
  conditions?: AchievementCondition[];
  txHash?: string;
}

// ============ 详情弹窗组件 ============
@Component({
  selector: 'app-achievement-detail-dialog',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatProgressBarModule, MatDialogModule, MatSnackBarModule],
  template: `
    <div class="dialog-wrapper">
      <!-- 头部渐变背景 -->
      <div class="dialog-header" [style.background]="headerGradient">
        <button mat-icon-button class="close-btn" (click)="close()">
          <mat-icon>close</mat-icon>
        </button>

        <!-- 徽章图标 -->
        <div class="badge-icon-circle">
          <span class="badge-emoji">{{ data.icon }}</span>
        </div>

        <h3 class="badge-name">{{ data.name }}</h3>
        <div class="badge-tags">
          <span class="tag-rarity" [style.color]="rarityCfg.color" [style.background]="rarityCfg.bg">
            {{ rarityCfg.label }}
          </span>
          <span class="tag-category">{{ getCategoryLabel(data.category) }}</span>
        </div>
        <p class="badge-date" *ngIf="data.unlockedDate">获得于 {{ data.unlockedDate | date: 'yyyy-MM-dd' }}</p>
      </div>

      <!-- 内容区 -->
      <div class="dialog-body">
        <!-- 描述 -->
        <div class="section">
          <h4 class="section-label">描述</h4>
          <p class="section-text">{{ data.description }}</p>
        </div>

        <!-- 获得条件 -->
        <div class="section">
          <h4 class="section-label">{{ data.status === 'completed' ? '获得条件' : '解锁条件' }}</h4>
          <ul class="conditions-list">
            <li *ngFor="let cond of data.conditions || []" class="condition-item">
              <div class="cond-check" [class.done]="cond.done">
                <mat-icon *ngIf="cond.done" class="check-icon">check</mat-icon>
              </div>
              <span [class.done]="cond.done">{{ cond.text }}</span>
            </li>
          </ul>
        </div>

        <!-- 进度（未解锁时） -->
        <div class="section" *ngIf="data.status !== 'completed'">
          <div class="progress-box">
            <div class="progress-header">
              <span class="progress-label">当前进度</span>
              <span class="progress-value">{{ data.progress }} / {{ data.target }}</span>
            </div>
            <mat-progress-bar
              mode="determinate"
              [value]="(data.progress / data.target) * 100"
              class="progress-bar"
            ></mat-progress-bar>
            <p class="progress-hint">还差 {{ data.target - data.progress }} 步即可解锁</p>
          </div>
        </div>

        <!-- 区块链认证（已解锁时） -->
        <div class="section" *ngIf="data.status === 'completed' && data.txHash">
          <div class="cert-box">
            <div class="cert-header">
              <mat-icon>verified</mat-icon>
              <span class="cert-label">区块链认证</span>
            </div>
            <p class="cert-hash">TxHash: {{ data.txHash }}</p>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="dialog-actions">
          <ng-container *ngIf="data.status === 'completed'; else unlockTpl">
            <button mat-stroked-button class="action-btn share-btn" (click)="onShare()">
              <mat-icon>share</mat-icon> 分享
            </button>
            <button mat-stroked-button class="action-btn cert-btn" (click)="onDownload()">
              <mat-icon>download</mat-icon> 证书
            </button>
          </ng-container>
          <ng-template #unlockTpl>
            <button mat-flat-button color="primary" class="action-btn unlock-btn" (click)="onUnlock()">
              <mat-icon>auto_awesome</mat-icon> 去解锁
            </button>
          </ng-template>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dialog-wrapper {
      max-width: 400px;
      border-radius: 24px;
      overflow: hidden;
      background: #fff;
    }
    .dialog-header {
      padding: 32px 24px 24px;
      text-align: center;
      position: relative;
      color: #fff;
    }
    .close-btn {
      position: absolute;
      top: 8px;
      right: 8px;
      color: rgba(255,255,255,0.8);
    }
    .close-btn:hover { color: #fff; }
    .badge-icon-circle {
      width: 96px;
      height: 96px;
      border-radius: 50%;
      background: rgba(255,255,255,0.2);
      backdrop-filter: blur(8px);
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 12px;
      border: 2px solid rgba(255,255,255,0.4);
    }
    .badge-emoji {
      font-size: 48px;
    }
    .badge-name {
      font-size: 20px;
      font-weight: 700;
      margin: 0 0 8px;
      color: #fff;
    }
    .badge-tags {
      display: flex;
      gap: 6px;
      justify-content: center;
    }
    .tag-rarity {
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 12px;
      font-weight: 600;
    }
    .tag-category {
      font-size: 10px;
      padding: 2px 8px;
      border-radius: 12px;
      background: rgba(255,255,255,0.2);
      color: #fff;
    }
    .badge-date {
      font-size: 12px;
      color: rgba(255,255,255,0.8);
      margin: 8px 0 0;
    }

    .dialog-body {
      padding: 20px 24px 24px;
    }
    .section {
      margin-bottom: 16px;
    }
    .section-label {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #94a3b8;
      margin: 0 0 8px;
    }
    .section-text {
      font-size: 14px;
      color: #334155;
      line-height: 1.6;
      margin: 0;
    }
    .conditions-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .condition-item {
      display: flex;
      align-items: flex-start;
      gap: 8px;
      padding: 6px 0;
      font-size: 13px;
    }
    .condition-item span { flex: 1; }
    .condition-item span.done { color: #334155; }
    .condition-item span:not(.done) { color: #94a3b8; }
    .cond-check {
      width: 20px;
      height: 20px;
      border-radius: 50%;
      border: 2px solid #cbd5e1;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      margin-top: 1px;
    }
    .cond-check.done {
      background: #dcfce7;
      border-color: #22c55e;
    }
    .check-icon {
      font-size: 14px;
      width: 14px;
      height: 14px;
      color: #16a34a;
    }

    .progress-box {
      background: #f8fafc;
      border-radius: 12px;
      padding: 12px 16px;
    }
    .progress-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
    }
    .progress-label { font-size: 12px; color: #64748b; }
    .progress-value { font-size: 12px; font-weight: 700; color: #0f172a; }
    .progress-bar { margin-bottom: 8px; }
    .progress-hint {
      font-size: 10px;
      color: #94a3b8;
      margin: 0;
    }

    .cert-box {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 12px 16px;
    }
    .cert-header {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 4px;
    }
    .cert-header mat-icon { font-size: 16px; width: 16px; height: 16px; color: #3b82f6; }
    .cert-label { font-size: 12px; font-weight: 700; color: #475569; }
    .cert-hash {
      font-size: 10px;
      color: #94a3b8;
      font-family: monospace;
      margin: 0;
      word-break: break-all;
    }

    .dialog-actions {
      display: flex;
      gap: 8px;
      padding-top: 8px;
    }
    .action-btn {
      flex: 1;
      border-radius: 12px;
      font-weight: 600;
      font-size: 13px;
    }
    .share-btn { color: #7c3aed; border-color: #ede9fe; }
    .cert-btn { color: #4338ca; border-color: #e0e7ff; }
    .unlock-btn { background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: #fff; }
  `],
})
export class AchievementDetailDialogComponent {
  constructor(
    @Inject(MAT_DIALOG_DATA) public data: AchievementDialogData,
    private dialogRef: MatDialogRef<AchievementDetailDialogComponent>,
    private snackBar: MatSnackBar,
  ) {}

  get rarityCfg() { return RARITY_CONFIG[this.data.rarity]; }

  get headerGradient(): string {
    if (this.data.status !== 'completed') {
      return 'linear-gradient(135deg, #94a3b8, #cbd5e1)';
    }
    const gradients: Record<AchievementRarity, string> = {
      common: 'linear-gradient(135deg, #94a3b8, #64748b)',
      uncommon: 'linear-gradient(135deg, #34d399, #059669)',
      rare: 'linear-gradient(135deg, #3b82f6, #06b6d4)',
      epic: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
      legendary: 'linear-gradient(135deg, #f59e0b, #f97316)',
    };
    return gradients[this.data.rarity];
  }

  getCategoryLabel(cat: AchievementCategory): string {
    return CATEGORY_LABELS[cat] || cat;
  }

  close(): void {
    this.dialogRef.close();
  }

  onShare(): void {
    this.snackBar.open('分享链接已复制到剪贴板', '知道了', { duration: 2000 });
  }

  onDownload(): void {
    this.snackBar.open('证书下载中...', '知道了', { duration: 2000 });
  }

  onUnlock(): void {
    this.dialogRef.close();
    this.snackBar.open('前往完成相关任务解锁', '知道了', { duration: 2000 });
  }
}

// ============ 成就画廊主组件 ============
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
    MatDialogModule,
  ],
  animations: [
    trigger('fadeIn', [
      state('void', style({ opacity: 0, transform: 'scale(0.9)' })),
      transition('void => *', animate('200ms ease-out')),
    ]),
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
          <mat-select [(ngModel)]="currentSort.sortBy" (ngModelChange)="onSortChange()">
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
          *ngFor="let achievement of filteredAchievements; let i = index"
          [class.completed]="achievement.status === 'completed'"
          [class.locked]="achievement.status === 'locked'"
          [class.rarity-legendary]="achievement.rarity === 'legendary' && achievement.status === 'completed'"
          (click)="openDetail(achievement)"
          [@fadeIn]
          [style.animationDelay]="i * 40 + 'ms'"
        >
          <!-- 稀有度标记 -->
          <div class="rarity-badge" [style.background]="rarityCfg(achievement.rarity).bg" [style.color]="rarityCfg(achievement.rarity).color">
            {{ rarityCfg(achievement.rarity).label }}
          </div>

          <div
            class="card-icon"
            [style.background]="rarityCfg(achievement.rarity).bg"
            [style.color]="rarityCfg(achievement.rarity).color"
          >
            <span class="icon-emoji">{{ achievement.status === 'completed' ? achievement.icon : '🔒' }}</span>
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

          <!-- 传说徽章旋转光效 -->
          <div class="legendary-glow" *ngIf="achievement.rarity === 'legendary' && achievement.status === 'completed'"></div>
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
        position: relative;
        display: flex;
        gap: 12px;
        padding: 16px;
        border-radius: 16px;
        background: var(--color-surface, #fff);
        border: 2px solid var(--color-border, #e2e8f0);
        transition:
          transform 0.2s,
          box-shadow 0.2s;
        cursor: pointer;
        overflow: hidden;
      }

      .achievement-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
      }

      .achievement-card.locked {
        opacity: 0.6;
      }
      .achievement-card.locked .card-icon {
        filter: grayscale(1);
      }

      .achievement-card.completed {
        border-color: #22c55e;
      }

      /* 稀有度标记 */
      .rarity-badge {
        position: absolute;
        top: 8px;
        right: 8px;
        font-size: 9px;
        padding: 2px 6px;
        border-radius: 8px;
        font-weight: 700;
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

      .icon-emoji {
        font-size: 24px;
      }

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

      /* 传说徽章旋转光效 */
      .legendary-glow {
        position: absolute;
        inset: 0;
        pointer-events: none;
        border-radius: 16px;
        background: conic-gradient(from 0deg, transparent, rgba(245,158,11,0.15), transparent);
        animation: legendarySpin 8s linear infinite;
      }
      @keyframes legendarySpin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
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

  constructor(
    private achievementService: AchievementService,
    private dialog: MatDialog,
  ) {}

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
      conditions: badge.unlocked ? [
        { text: badge.description, done: true },
      ] : [
        { text: badge.description, done: false },
      ],
    };
  }

  rarityCfg(rarity: AchievementRarity) {
    return RARITY_CONFIG[rarity];
  }

  openDetail(achievement: Achievement): void {
    this.dialog.open(AchievementDetailDialogComponent, {
      data: {
        id: achievement.id,
        name: achievement.name,
        icon: achievement.icon,
        description: achievement.description,
        status: achievement.status,
        category: achievement.category,
        rarity: achievement.rarity,
        progress: achievement.progress,
        target: achievement.target,
        unlockedDate: achievement.unlockedDate,
        conditions: achievement.conditions,
        txHash: achievement.txHash,
      },
      panelClass: 'achievement-detail-dialog',
      maxWidth: '90vw',
    });
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
        (a) => a.name.toLowerCase().includes(q) || a.description.toLowerCase().includes(q)
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
    return CATEGORY_LABELS[category] || category;
  }
}
