/**
 * 成就审核组件
 *
 * 提供成就审核列表、审核操作（批准/拒绝/退回修改）功能
 * 对应后端审核流程
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
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBarModule } from '@angular/material/snack-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import {
  AchievementReview,
  AchievementStatus,
} from '../../models/achievement.model';
import { AchievementService } from '../../services/achievement.service';

@Component({
  selector: 'app-achievement-review',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSnackBarModule,
  ],
  template: `
    <div class="achievement-review">
      <h2 class="review-title">成就审核</h2>

      <!-- 审核列表 -->
      <div class="review-list" *ngIf="reviews.length > 0">
        <mat-card
          class="review-card"
          *ngFor="let review of reviews"
          [class.expanded]="selectedReviewId === review.id"
        >
          <mat-card-content>
            <div class="review-header" (click)="toggleReview(review.id)">
              <div class="review-info">
                <span class="achievement-name">{{ review.achievementName }}</span>
                <span class="user-name">{{ review.userName }}</span>
              </div>
              <div class="review-meta">
                <mat-chip
                  [class.status-pending]="review.status === 'pending'"
                  [class.status-approved]="review.status === 'approved'"
                  [class.status-rejected]="review.status === 'rejected'"
                  [class.status-revision]="review.status === 'revision'"
                >
                  {{ getStatusLabel(review.status) }}
                </mat-chip>
                <span class="submitted-date">{{ review.submittedAt | date:'shortDate' }}</span>
              </div>
            </div>

            <!-- 展开的审核详情 -->
            <div class="review-detail" *ngIf="selectedReviewId === review.id">
              <div class="comment-section" *ngIf="review.comment">
                <label>用户说明</label>
                <p>{{ review.comment }}</p>
              </div>

              <div class="review-action" *ngIf="review.status === 'pending'">
                <mat-form-field appearance="outline" class="full-width">
                  <mat-label>审核意见</mat-label>
                  <textarea
                    matInput
                    [(ngModel)]="reviewComment"
                    placeholder="请输入审核意见..."
                    rows="3"
                  ></textarea>
                </mat-form-field>

                <div class="action-buttons">
                  <button
                    mat-raised-button
                    color="primary"
                    (click)="submitReview(review, 'approved')"
                  >
                    <mat-icon>check_circle</mat-icon>
                    批准
                  </button>
                  <button
                    mat-raised-button
                    color="warn"
                    (click)="submitReview(review, 'rejected')"
                  >
                    <mat-icon>cancel</mat-icon>
                    拒绝
                  </button>
                  <button
                    mat-stroked-button
                    (click)="submitReview(review, 'revision')"
                  >
                    <mat-icon>refresh</mat-icon>
                    退回修改
                  </button>
                </div>
              </div>

              <div class="review-result" *ngIf="review.status !== 'pending' && review.reviewerName">
                <label>审核结果</label>
                <p>
                  由 {{ review.reviewerName }}
                  于 {{ review.reviewedAt | date:'shortDate' }} 审核
                </p>
              </div>
            </div>
          </mat-card-content>
        </mat-card>
      </div>

      <!-- 空状态 -->
      <div class="empty-state" *ngIf="reviews.length === 0">
        <mat-icon>fact_check</mat-icon>
        <p>暂无待审核的成就记录</p>
      </div>
    </div>
  `,
  styles: [
    `
      .achievement-review {
        padding: 16px;
        max-width: 800px;
        margin: 0 auto;
      }

      .review-title {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 20px;
        color: var(--color-text-primary, #212121);
      }

      .review-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .review-card {
        cursor: pointer;
        transition: box-shadow 0.2s;
      }

      .review-card:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }

      .review-card.expanded {
        border-left: 3px solid var(--color-primary, #1976d2);
      }

      .review-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 0;
      }

      .review-info {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }

      .achievement-name {
        font-size: 16px;
        font-weight: 500;
        color: var(--color-text-primary, #212121);
      }

      .user-name {
        font-size: 13px;
        color: var(--color-text-secondary, #666);
      }

      .review-meta {
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .status-pending {
        background: #fff3e0;
        color: #e65100;
      }

      .status-approved {
        background: #e8f5e9;
        color: #2e7d32;
      }

      .status-rejected {
        background: #ffebee;
        color: #c62828;
      }

      .status-revision {
        background: #e3f2fd;
        color: #1565c0;
      }

      .submitted-date {
        font-size: 12px;
        color: var(--color-text-secondary, #999);
      }

      .review-detail {
        padding-top: 16px;
        border-top: 1px solid var(--color-border, #e0e0e0);
        margin-top: 12px;
      }

      .comment-section {
        margin-bottom: 16px;
      }

      .comment-section label,
      .review-result label {
        display: block;
        font-size: 13px;
        font-weight: 500;
        color: var(--color-text-secondary, #666);
        margin-bottom: 6px;
      }

      .comment-section p {
        font-size: 14px;
        color: var(--color-text-primary, #212121);
        line-height: 1.5;
        margin: 0;
        padding: 8px 12px;
        background: var(--color-surface, #f5f5f5);
        border-radius: 8px;
      }

      .review-action {
        margin-bottom: 12px;
      }

      .full-width {
        width: 100%;
      }

      .action-buttons {
        display: flex;
        gap: 12px;
        margin-top: 12px;
      }

      .action-buttons button {
        display: flex;
        align-items: center;
        gap: 4px;
      }

      .review-result p {
        font-size: 14px;
        color: var(--color-text-primary, #212121);
        margin: 0;
      }

      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 64px 0;
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
export class AchievementReviewComponent implements OnInit, OnDestroy {
  @Input() userId!: number;

  reviews: AchievementReview[] = [];
  selectedReviewId: string | null = null;
  reviewComment = '';

  private readonly statusLabels: Record<AchievementStatus, string> = {
    [AchievementStatus.LOCKED]: '锁定',
    [AchievementStatus.IN_PROGRESS]: '进行中',
    [AchievementStatus.COMPLETED]: '已完成',
    [AchievementStatus.EXPIRED]: '已过期',
    [AchievementStatus.PENDING]: '待审核',
    [AchievementStatus.APPROVED]: '已批准',
    [AchievementStatus.REJECTED]: '已拒绝',
    [AchievementStatus.REVISION]: '需修改',
  };

  private destroy$ = new Subject<void>();

  constructor(private achievementService: AchievementService) {}

  ngOnInit(): void {
    this.loadReviews();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * 加载审核列表
   */
  private loadReviews(): void {
    if (!this.userId) {
      return;
    }

    this.achievementService
      .getAchievementReviews(this.userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe((reviews) => {
        this.reviews = reviews;
      });
  }

  /**
   * 切换展开/折叠审核详情
   */
  toggleReview(reviewId: string): void {
    this.selectedReviewId =
      this.selectedReviewId === reviewId ? null : reviewId;
    this.reviewComment = '';
  }

  /**
   * 提交审核
   */
  submitReview(
    review: AchievementReview,
    status: 'approved' | 'rejected' | 'revision'
  ): void {
    this.achievementService
      .reviewAchievement(review.id, status, this.reviewComment, this.userId)
      .pipe(takeUntil(this.destroy$))
      .subscribe((result) => {
        if (result) {
          // 更新本地状态
          const index = this.reviews.findIndex((r) => r.id === review.id);
          if (index !== -1) {
            this.reviews[index] = result;
          }
          this.selectedReviewId = null;
          this.reviewComment = '';
        }
      });
  }

  /**
   * 获取状态显示文本
   */
  getStatusLabel(status: AchievementStatus): string {
    return this.statusLabels[status] || status;
  }
}
