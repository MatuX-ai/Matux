/**
 * 成长轨迹页面（包装组件）
 *
 * PRD 6.6 关键页面线框 - "我的成长"
 * 使用共享组件 GrowthTrajectoryComponent 渲染内容
 */

import { CommonModule } from '@angular/common';
import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
} from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import type { GrowthTrajectory } from '../../../core/models/ai-teacher.models';
import { AITeacherService } from '../../../core/services/ai-teacher.service';
import { AuthService } from '../../../core/services/auth.service';
import { GrowthTrajectoryComponent } from '../../../shared/components/growth-trajectory/growth-trajectory.component';

@Component({
  selector: 'app-growth-trajectory-page',
  standalone: true,
  imports: [CommonModule, MatIconModule, GrowthTrajectoryComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="growth-page">
      <div class="page-header">
        <h1 class="page-title">我的成长轨迹</h1>
        <span class="update-time" *ngIf="currentDate">{{ currentDate }}</span>
      </div>

      <app-growth-trajectory *ngIf="trajectory" [trajectory]="trajectory"></app-growth-trajectory>

      <div class="loading-state" *ngIf="!trajectory && !error">
        <mat-icon>hourglass_empty</mat-icon>
        <p>正在加载你的成长数据...</p>
      </div>

      <div class="error-state" *ngIf="error">
        <mat-icon>error_outline</mat-icon>
        <p>无法加载成长数据，请稍后重试</p>
      </div>
    </div>
  `,
  styles: [
    `
      /* K12 STEM 探索绿主题 */
      :host {
        --stem-primary: #059669;
        --stem-primary-light: #10b981;
        --stem-text-primary: #1c1917;
        --stem-text-secondary: #57534e;
        --stem-bg-page: #fafaf9;
        --stem-radius-lg: 20px;
        --stem-shadow-sm: 0 1px 3px rgba(5, 150, 105, 0.08);
      }

      .growth-page {
        max-width: 1200px;
        margin: 0 auto;
        padding: 24px;
        background: var(--stem-bg-page, #fafaf9);
        min-height: 100vh;
      }
      .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      .page-title {
        font-size: 28px;
        font-weight: 700;
        // STEM 探索绿主题色
        color: var(--stem-primary, #059669);
        margin: 0;
      }
      .update-time {
        font-size: 13px;
        color: var(--stem-text-secondary, #57534e);
      }
      .loading-state,
      .error-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 80px;
        color: var(--stem-text-secondary, #57534e);
      }
      .loading-state mat-icon,
      .error-state mat-icon {
        font-size: 48px;
        width: 48px;
        height: 48px;
        margin-bottom: 16px;
        color: var(--stem-primary, #059669);
      }
      .error-state {
        // 【对比度修复 #1】原 var(--stem-error, #ef4444) on $stem-bg-page 仅 3.60:1
        // 改用 var(--stem-error-dark, #dc2626) = 4.59:1 AA
        color: var(--stem-error-dark, #dc2626);
      }
      .error-state mat-icon {
        // 【对比度修复 #1】同步加深图标色，保持一致性
        color: var(--stem-error-dark, #dc2626);
      }
    `,
  ],
})
export class GrowthTrajectoryPageComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();

  trajectory: GrowthTrajectory | null = null;
  error = false;
  currentDate = '';

  constructor(
    private aiTeacherService: AITeacherService,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    const now = new Date();
    this.currentDate = `${now.getFullYear()}年${now.getMonth() + 1}月`;

    this.authService.currentUser$.pipe(takeUntil(this.destroy$)).subscribe((user) => {
      if (user?.id) {
        this.loadGrowthTrajectory(Number(user.id));
      }
    });
  }

  private loadGrowthTrajectory(userId: number): void {
    this.error = false;
    this.aiTeacherService
      .getGrowthTrajectory(String(userId))
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (trajectory) => {
          this.trajectory = trajectory;
          this.cdr.markForCheck();
        },
        error: () => {
          this.error = true;
          this.cdr.markForCheck();
        },
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }
}
