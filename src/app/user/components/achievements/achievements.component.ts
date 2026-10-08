/**
 * 用户成就系统组件
 *
 * 集成成就展示、进度统计、徽章画廊等功能
 * 复用 features/achievement-integration 的成熟组件
 *
 * @author MatuX Lab
 * @version 1.0.0
 */

import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnDestroy, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
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
    MatSnackBarModule,
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
              <button
                mat-stroked-button
                color="primary"
                class="login-cta"
                (click)="goToLogin()"
              >
                <mat-icon>login</mat-icon>
                去登录
              </button>
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

  constructor(
    private authService: AuthService,
    private cdr: ChangeDetectorRef,
    private snackBar: MatSnackBar,
    private router: Router
  ) {}

  get hasValidUserId(): boolean {
    return this.currentUserId > 0 && !Number.isNaN(this.currentUserId);
  }

  ngOnInit(): void {
    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user: User | null) => {
      if (user?.id) {
        const parsed = Number(user.id);
        this.currentUserId = !Number.isNaN(parsed) ? parsed : 0;
      } else {
        // 【P2-1 修复】仅依靠 currentUser$ 可能错过已登录用户的初始化：
        //   - 路由刷新后 currentUser$ 还未发射，或 user 对象被清理。
        //   - 改用同时从 AuthService 同步读取 currentUser，避免出现 “已登录但页面说请先登录”。
        const snapshot = this.authService.getCurrentUser?.();
        if (snapshot?.id) {
          const parsed = Number(snapshot.id);
          this.currentUserId = !Number.isNaN(parsed) ? parsed : 0;
        }
      }
      // 【P2-1 修复】使用 ChangeDetectorRef.markForCheck() 主动推动变更检测，
      //   防止路由复用（OnPush + reuseStrategy）下 currentUser 状态不反映到模板。
      this.cdr.markForCheck();
    });
  }

  /** 【P2-1 修复】未登录提示 “去登录” 按钮跳转到登录页 */
  goToLogin(): void {
    void this.router.navigate(['/auth/login']);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
