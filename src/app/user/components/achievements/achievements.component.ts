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
import { MatTabsModule } from '@angular/material/tabs';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { User } from '../../../core/models/auth.models';
import { AuthService } from '../../../core/services/auth.service';
import { AchievementGalleryComponent } from '../../../features/achievement-integration/components/achievement-gallery/achievement-gallery.component';
import { AchievementProgressComponent } from '../../../features/achievement-integration/components/achievement-progress/achievement-progress.component';
import { AchievementUploadComponent } from '../../../features/achievement-integration/components/achievement-upload/achievement-upload.component';

@Component({
  selector: 'app-achievements',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatCardModule,
    MatProgressBarModule,
    AchievementGalleryComponent,
    AchievementProgressComponent,
    AchievementUploadComponent,
  ],
  template: `
    <div class="achievements-container">
      <h1 class="page-title">成就系统</h1>

      <!-- 用户成就进度 -->
      <div class="section" *ngIf="hasValidUserId; else noUser">
        <app-achievement-progress [userId]="currentUserId"></app-achievement-progress>

        <!-- 成就展示和上传 -->
        <mat-tab-group animationDuration="300ms">
          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon>emoji_events</mat-icon>
              <span>我的成就</span>
            </ng-template>
            <div class="tab-content">
              <app-achievement-gallery [userId]="currentUserId"></app-achievement-gallery>
            </div>
          </mat-tab>

          <mat-tab>
            <ng-template mat-tab-label>
              <mat-icon>cloud_upload</mat-icon>
              <span>上传成就</span>
            </ng-template>
            <div class="tab-content">
              <app-achievement-upload [userId]="currentUserId"></app-achievement-upload>
            </div>
          </mat-tab>
        </mat-tab-group>
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

      .tab-content {
        padding: 24px 0;
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
