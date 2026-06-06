/**
 * 成就系统组件（学生）
 * 集成成就展示、成就进度、成就上传等功能
 */

import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { User } from '../../../core/models/auth.models';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-achievements',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatProgressBarModule,
  ],
  template: `
    <div class="achievements-container">
      <h1 class="page-title">成就系统</h1>

      <div class="section" *ngIf="hasValidUserId; else noUser">
        <!-- 成就进度 -->
        <mat-card class="info-card">
          <mat-card-content>
            <p>成就系统功能正在开发中，敬请期待。</p>
          </mat-card-content>
        </mat-card>
      </div>

      <ng-template #noUser>
        <mat-card class="info-card">
          <mat-card-content>
            <p>请先登录后查看成就信息</p>
          </mat-card-content>
        </mat-card>
      </ng-template>
    </div>
  `,
  styles: [
    `
      .achievements-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 24px;
      }

      .page-title {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 24px;
        color: var(--color-text-primary);
      }

      .section {
        margin-bottom: 32px;
      }
    `,
  ],
})
export class AchievementsComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  currentUserId: number = 0;

  get hasValidUserId(): boolean {
    return this.currentUserId > 0 && !Number.isNaN(this.currentUserId);
  }

  constructor(private authService: AuthService) {}

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
