/**
 * 用户成就系统组件
 *
 * 集成成就展示、进度统计、徽章画廊等功能
 * 复用 features/achievement-integration 的成熟组件
 *
 * @author iMatu Development Team
 * @version 1.0.0
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { User } from '../../../core/models/auth.models';
import { AuthService } from '../../../core/services/auth.service';
import { AchievementGalleryComponent } from '../../../features/achievement-integration/components/achievement-gallery/achievement-gallery.component';

@Component({
  selector: 'app-achievements',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatProgressBarModule,
    AchievementGalleryComponent,
  ],
  template: `
    <div class="achievements-page">
      <!-- 页面标题 -->
      <div class="page-header">
        <h1 class="page-title">成就系统</h1>
        <p class="page-subtitle">解锁徽章，记录成长历程</p>
      </div>

      <!-- 未登录状态 -->
      <ng-container *ngIf="!hasValidUserId; else loggedIn">
        <mat-card class="info-card">
          <mat-card-content>
            <div class="empty-state">
              <mat-icon class="empty-icon">account_circle</mat-icon>
              <p>请先登录后查看成就信息</p>
            </div>
          </mat-card-content>
        </mat-card>
      </ng-container>

      <!-- 已登录状态：显示成就画廊 -->
      <ng-template #loggedIn>
        <div class="achievements-content">
          <!-- 成就画廊组件 -->
          <app-achievement-gallery [userId]="currentUserId"></app-achievement-gallery>
        </div>
      </ng-template>
    </div>
  `,
  styles: [
    `
      /* K12 STEM 探索绿主题 */
      :host {
        --stem-primary: #059669;
        --stem-primary-light: #10b981;
        --stem-secondary: #0ea5e9;
        --stem-text-primary: #1c1917;
        --stem-text-secondary: #57534e;
        --stem-bg-page: #fafaf9;
        --stem-gradient-explore: linear-gradient(135deg, #059669 0%, #0ea5e9 100%);
      }

      .achievements-page {
        max-width: 1400px;
        margin: 0 auto;
        padding: 24px;
        background: var(--stem-bg-page);
        min-height: 100vh;
      }

      .page-header {
        margin-bottom: 32px;
      }

      .page-title {
        font-size: 28px;
        font-weight: 700;
        margin: 0 0 8px 0;

        // 【对比度修复 #1】原 var(--stem-primary, #059669) on $stem-bg-page 仅 3.61:1 (边缘)
        // 改用 $stem-primary-dark (#047857) = 6.45:1 AAA
        color: var(--stem-primary-dark, #047857);
      }

      .page-subtitle {
        font-size: 14px;
        color: var(--stem-text-secondary, #57534e);
        margin: 0;
      }

      .info-card {
        max-width: 500px;
        margin: 64px auto;
        border-radius: 20px;
        box-shadow: 0 1px 3px rgba(5, 150, 105, 0.08);
      }

      .empty-state {
        text-align: center;
        padding: 48px 24px;
      }

      .empty-icon {
        font-size: 64px;
        width: 64px;
        height: 64px;
        // STEM 探索绿主题色
        color: var(--stem-primary, #059669);
        margin-bottom: 16px;
      }

      .empty-state p {
        font-size: 16px;
        color: var(--stem-text-secondary, #57534e);
        margin: 0;
      }

      .achievements-content {
        background: transparent;
      }
    `,
  ],
})
export class AchievementsComponent implements OnInit, OnDestroy {
  currentUserId: number = 0;

  private destroy$ = new Subject<void>();

  constructor(private authService: AuthService) {}

  get hasValidUserId(): boolean {
    return this.currentUserId > 0 && !Number.isNaN(this.currentUserId);
  }

  ngOnInit(): void {
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user: User | null) => {
      if (user?.id) {
        const parsed = Number(user.id);
        this.currentUserId = !Number.isNaN(parsed) ? parsed : 0;
      }
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
