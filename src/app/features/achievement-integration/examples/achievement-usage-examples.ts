/**
 * 学员成果集成模块 - 使用示例
 *
 * 本文件包含各种使用场景的代码示例
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatBadgeModule } from '@angular/material/badge';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

import { AchievementGalleryComponent } from '../components/achievement-gallery/achievement-gallery.component';
import { AchievementUploadComponent } from '../components/achievement-upload/achievement-upload.component';
import {
  Achievement,
  AchievementFilter,
  AchievementProgress,
  AchievementStats,
  AchievementStatus,
  AchievementType,
} from '../models/achievement.model';
import { AchievementService } from '../services/achievement.service';
// import { AchievementReviewComponent } from '../components/achievement-review/achievement-review.component';
// import { AchievementProgressComponent } from '../components/achievement-progress/achievement-progress.component';
// import { AchievementDisplayComponent } from '../components/achievement-display/achievement-display.component';

/**
 * 示例 1: 在课程页面中集成成果上传
 */
@Component({
  selector: 'app-course-achievements',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatSnackBarModule,
    AchievementGalleryComponent,
  ],
  template: `
    <div class="course-achievements">
      <div class="header">
        <h2>课程成果</h2>
        <button mat-raised-button color="primary" (click)="openUploadDialog()">
          <mat-icon>cloud_upload</mat-icon>
          上传成果
        </button>
      </div>

      <app-achievement-gallery [moduleId]="courseId" [layout]="'grid'"></app-achievement-gallery>
    </div>
  `,
})
export class CourseAchievementsExampleComponent implements OnInit {
  courseId = 123;
  userId = 456;

  constructor(
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {}

  openUploadDialog(): void {
    const dialogRef = this.dialog.open(AchievementUploadComponent, {
      width: '800px',
      data: { moduleId: this.courseId },
    });

    dialogRef.componentInstance?.uploadSuccess?.subscribe((achievement: Achievement) => {
      this.snackBar.open(`🎉 成果 "${achievement.title}" 上传成功！`, '关闭', {
        duration: 3000,
      });
    });
  }
}

/**
 * 示例 2: 教师审核面板
 */
@Component({
  selector: 'app-teacher-review-panel',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatDialogModule, MatSnackBarModule, AchievementGalleryComponent],
  template: `
    <div class="teacher-review-panel">
      <div class="tabs">
        <button [class.active]="activeTab === 'pending'" (click)="activeTab = 'pending'">
          待审核 ({{ stats.pendingReviews }})
        </button>
        <button [class.active]="activeTab === 'all'" (click)="activeTab = 'all'">全部</button>
      </div>

      <div class="content">
        <div *ngIf="activeTab === 'pending'">
          <app-achievement-gallery
            [filter]="{ status: ['pending'] }"
            [sortBy]="{ field: 'submittedAt', direction: 'asc' }"
          ></app-achievement-gallery>
        </div>

        <div *ngIf="activeTab === 'all'">
          <app-achievement-gallery [filter]="{}"></app-achievement-gallery>
        </div>
      </div>
    </div>
  `,
})
export class TeacherReviewPanelExampleComponent implements OnInit {
  activeTab = 'pending';
  stats: AchievementStats = {
    totalAchievements: 0,
    pendingReviews: 0,
    approvedAchievements: 0,
    rejectedAchievements: 0,
    averageScore: 0,
    recentActivity: [],
    byType: {},
    byStatus: { pending: 0, approved: 0, rejected: 0, revision: 0 },
  };

  constructor(private achievementService: AchievementService) {}

  ngOnInit(): void {
    this.loadStats();
  }

  loadStats(): void {
    this.achievementService.getAchievementStats().subscribe((stats) => {
      this.stats = stats;
    });
  }
}

/**
 * 示例 3: 用户学习进度仪表板
 */
@Component({
  selector: 'app-user-progress-dashboard',
  standalone: true,
  imports: [MatButtonModule, MatDialogModule, MatSnackBarModule, AchievementGalleryComponent],
  template: `
    <div class="user-progress-dashboard">
      <div class="overview">
        <h3>学习概览</h3>
        <div class="progress-cards">
          <div class="card">
            <h4>总成果数</h4>
            <p class="number">{{ progress?.totalAchievements || 0 }}</p>
          </div>
          <div class="card">
            <h4>已完成</h4>
            <p class="number">{{ progress?.completedAchievements || 0 }}</p>
          </div>
          <div class="card">
            <h4>平均评分</h4>
            <p class="number">{{ progress?.averageScore?.toFixed(1) || 0 }}</p>
          </div>
          <div class="card">
            <h4>完成度</h4>
            <p class="number">{{ getCompletionPercentage() }}%</p>
          </div>
        </div>
      </div>

      <!-- progress-detail section commented out as AchievementProgressComponent is not yet fully implemented -->
      <!-- <div class="progress-detail">
        <h3>详细进度</h3>
        <app-achievement-progress
          [userId]="currentUserId"
          [displayMode]="'full'"
        ></app-achievement-progress>
      </div> -->

      <div class="my-achievements">
        <h3>我的成果</h3>
        <app-achievement-gallery
          [userId]="currentUserId"
          [layout]="'timeline'"
        ></app-achievement-gallery>
      </div>
    </div>
  `,
  styles: [
    `
      .user-progress-dashboard {
        padding: 24px;
      }

      .overview,
      .progress-detail,
      .my-achievements {
        margin-bottom: 32px;
      }

      .progress-cards {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-top: 16px;
      }

      .card {
        background: white;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .card h4 {
        margin: 0 0 8px 0;
        font-size: 14px;
        color: #666;
      }

      .card .number {
        margin: 0;
        font-size: 32px;
        font-weight: 700;
        color: #4285f4;
      }
    `,
  ],
})
export class UserProgressDashboardExampleComponent implements OnInit {
  currentUserId = 456;
  progress?: AchievementProgress;

  constructor(private achievementService: AchievementService) {}

  ngOnInit(): void {
    this.loadProgress();
  }

  loadProgress(): void {
    this.achievementService
      .getUserAchievementProgress(this.currentUserId)
      .subscribe((data: AchievementProgress) => {
        this.progress = data;
      });
  }

  getCompletionPercentage(): number {
    return this.progress?.completionPercentage ?? 0;
  }
}

/**
 * 示例 4: 高级筛选和搜索
 */
@Component({
  selector: 'app-advanced-filter',
  standalone: true,
  imports: [
    FormsModule,
    ReactiveFormsModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatSnackBarModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    AchievementGalleryComponent,
  ],
  template: `
    <div class="advanced-filter">
      <div class="filter-bar">
        <mat-form-field>
          <input
            matInput
            placeholder="搜索成果..."
            [(ngModel)]="searchQuery"
            (keyup.enter)="applyFilters()"
          />
          <mat-icon matSuffix>search</mat-icon>
        </mat-form-field>

        <mat-select placeholder="类型" [(ngModel)]="selectedType">
          <mat-option [value]="null">全部</mat-option>
          <mat-option value="project">项目案例</mat-option>
          <mat-option value="certificate">证书</mat-option>
          <mat-option value="assignment">作业</mat-option>
        </mat-select>

        <mat-select placeholder="状态" [(ngModel)]="selectedStatus">
          <mat-option [value]="null">全部</mat-option>
          <mat-option value="pending">待审核</mat-option>
          <mat-option value="approved">已通过</mat-option>
          <mat-option value="rejected">已拒绝</mat-option>
        </mat-select>

        <mat-select placeholder="评分" [(ngModel)]="selectedScore">
          <mat-option [value]="null">全部</mat-option>
          <mat-option [value]="5">5星</mat-option>
          <mat-option [value]="4">4星</mat-option>
          <mat-option [value]="3">3星</mat-option>
          <mat-option [value]="2">2星</mat-option>
          <mat-option [value]="1">1星</mat-option>
        </mat-select>

        <mat-select placeholder="排序" [(ngModel)]="sortBy">
          <mat-option value="submittedAt">提交时间</mat-option>
          <mat-option value="score">评分</mat-option>
          <mat-option value="updatedAt">更新时间</mat-option>
        </mat-select>

        <button mat-button (click)="applyFilters()">筛选</button>
        <button mat-button (click)="resetFilters()">重置</button>
      </div>

      <app-achievement-gallery [filter]="currentFilter"></app-achievement-gallery>
    </div>
  `,
})
export class AdvancedFilterExampleComponent implements OnInit {
  searchQuery = '';
  selectedType: AchievementType | null = null;
  selectedStatus: AchievementStatus | null = null;
  selectedScore: number | null = null;
  sortBy = 'submittedAt';
  currentFilter: AchievementFilter = {};

  constructor(private achievementService: AchievementService) {}

  ngOnInit(): void {}

  applyFilters(): void {
    this.currentFilter = {
      type: this.selectedType ? [this.selectedType] : undefined,
      status: this.selectedStatus ? [this.selectedStatus] : undefined,
      searchQuery: this.searchQuery || undefined,
    };
  }

  resetFilters(): void {
    this.searchQuery = '';
    this.selectedType = null;
    this.selectedStatus = null;
    this.selectedScore = null;
    this.currentFilter = {};
  }
}

/**
 * 示例 5: 批量操作
 */
@Component({
  selector: 'app-batch-operations',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatDialogModule, MatSnackBarModule, AchievementGalleryComponent],
  template: `
    <div class="batch-operations">
      <div class="toolbar" *ngIf="selectedAchievements.length > 0">
        <span>已选择 {{ selectedAchievements.length }} 项</span>
        <button mat-button color="primary" (click)="batchApprove()">批量通过</button>
        <button mat-button (click)="batchExport()">批量导出</button>
        <button mat-button (click)="clearSelection()">清除选择</button>
      </div>

      <app-achievement-gallery
        (selectionChange)="onSelectionChange($event)"
      ></app-achievement-gallery>
    </div>
  `,
})
export class BatchOperationsExampleComponent {
  selectedAchievements: Achievement[] = [];

  constructor(private achievementService: AchievementService) {}

  onSelectionChange(achievements: Achievement[]): void {
    this.selectedAchievements = achievements;
  }

  async batchApprove(): Promise<void> {
    for (const achievement of this.selectedAchievements) {
      await this.achievementService
        .reviewAchievement(achievement.id, {
          status: 'approved',
          score: 5,
          feedback: '批量审核通过',
        })
        .toPromise();
    }
  }

  batchExport(): void {
    this.achievementService
      .exportAchievements({
        status: ['approved'],
      })
      .subscribe((blob: Blob) => {
        // 下载文件
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `achievements_${Date.now()}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
      });
  }

  clearSelection(): void {
    this.selectedAchievements = [];
  }
}

/**
 * 示例 6: 实时通知
 */
@Component({
  selector: 'app-real-time-notifications',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatIconModule, MatBadgeModule, MatDialogModule, MatSnackBarModule],
  template: `
    <div class="real-time-notifications">
      <button mat-icon-button [matBadge]="unreadCount" (click)="toggleNotifications()">
        <mat-icon>notifications</mat-icon>
      </button>

      <div *ngIf="showNotifications" class="notification-panel">
        <h3>通知</h3>
        <div class="notification-list">
          <div
            *ngFor="let notification of notifications"
            class="notification-item"
            [class.unread]="!notification.read"
            (click)="markAsRead(notification)"
          >
            <span class="icon">{{ getNotificationIcon(notification.type) }}</span>
            <div class="content">
              <p class="message">{{ notification.message }}</p>
              <span class="time">{{ formatTime(notification.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
})
export class RealTimeNotificationsExampleComponent implements OnInit {
  showNotifications = false;
  unreadCount = 0;
  notifications: Array<{
    id?: string;
    type: string;
    message: string;
    timestamp: string;
    read?: boolean;
  }> = [];

  ngOnInit(): void {
    this.setupWebSocket();
  }

  private setupWebSocket(): void {
    const ws = new WebSocket('ws://localhost:8000/ws/notifications');

    ws.onmessage = (event: MessageEvent<string>) => {
      try {
        const notification = JSON.parse(event.data) as {
          id?: string;
          type: string;
          message: string;
          timestamp: string;
          read?: boolean;
        };
        this.notifications.unshift(notification);
        if (!notification.read) {
          this.unreadCount++;
        }
      } catch (error) {
        console.error('Failed to parse notification:', error);
      }
    };
  }

  toggleNotifications(): void {
    this.showNotifications = !this.showNotifications;
  }

  markAsRead(notification: {
    id?: string;
    type: string;
    message: string;
    timestamp: string;
    read?: boolean;
  }): void {
    notification.read = true;
    this.unreadCount--;
  }

  getNotificationIcon(type: string): string {
    const icons: Record<string, string> = {
      achievement_submitted: '📤',
      achievement_approved: '✅',
      achievement_rejected: '❌',
      milestone_achieved: '🏆',
      comment_added: '💬',
    };
    return icons[type] || '🔔';
  }

  formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));

    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)}小时前`;
    return date.toLocaleDateString('zh-CN');
  }
}

/**
 * 导出所有示例组件
 */
export const Examples = [
  CourseAchievementsExampleComponent,
  TeacherReviewPanelExampleComponent,
  UserProgressDashboardExampleComponent,
  AdvancedFilterExampleComponent,
  BatchOperationsExampleComponent,
  RealTimeNotificationsExampleComponent,
];
