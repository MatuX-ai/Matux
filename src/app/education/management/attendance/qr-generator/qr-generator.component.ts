/**
 * 签到二维码生成组件 - 教师端使用
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

interface QRCodeData {
  imageUrl: string;
  token: string;
  expiresAt: Date;
  courseScheduleId: string;
}

@Component({
  selector: 'app-qr-generator',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatDialogModule,
    MatSnackBarModule,
  ],
  template: `
    <div class="qr-generator-container">
      <mat-card class="qr-card">
        <mat-card-header>
          <mat-card-title>课堂签到二维码</mat-card-title>
          <mat-card-subtitle>学生扫码即可完成签到</mat-card-subtitle>
        </mat-card-header>

        <mat-card-content>
          <!-- 加载状态 -->
          <div *ngIf="loading" class="loading-state">
            <mat-progress-bar mode="indeterminate"></mat-progress-bar>
            <p>正在生成二维码...</p>
          </div>

          <!-- 二维码显示 -->
          <div *ngIf="!loading && qrCodeData" class="qr-content">
            <div class="qr-image-wrapper">
              <img [src]="qrCodeData.imageUrl" alt="签到二维码" class="qr-image" />
              <div class="qr-overlay" *ngIf="isExpired">
                <mat-icon>warning</mat-icon>
                <p>二维码已过期</p>
              </div>
            </div>

            <div class="qr-info">
              <div class="info-item">
                <mat-icon>schedule</mat-icon>
                <span>有效期：{{ getRemainingTime() }}</span>
              </div>
              <div class="info-item">
                <mat-icon>event</mat-icon>
                <span>课程 ID: {{ qrCodeData.courseScheduleId | slice: 0 : 8 }}...</span>
              </div>
            </div>

            <div class="action-buttons">
              <button mat-flat-button color="primary" (click)="downloadQR()">
                <mat-icon>download</mat-icon>
                下载二维码
              </button>
              <button mat-stroked-button (click)="refreshQR()">
                <mat-icon>refresh</mat-icon>
                刷新二维码
              </button>
            </div>
          </div>

          <!-- 错误状态 -->
          <div *ngIf="error" class="error-state">
            <mat-icon color="warn">error</mat-icon>
            <p>{{ error }}</p>
            <button mat-raised-button color="primary" (click)="generateQR()">重新生成</button>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [
    `
      .qr-generator-container {
        padding: 20px;
        max-width: 600px;
        margin: 0 auto;
      }

      .qr-card {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }

      .loading-state {
        text-align: center;
        padding: 40px 20px;

        p {
          margin-top: 16px;
          color: #666;
        }
      }

      .qr-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 20px;
      }

      .qr-image-wrapper {
        position: relative;
        border: 4px solid #3f51b5;
        border-radius: 8px;
        overflow: hidden;
        max-width: 300px;

        .qr-image {
          width: 100%;
          height: auto;
          display: block;
        }

        .qr-overlay {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.7);
          display: flex;
          flex-direction: column;
          justify-content: center;
          align-items: center;
          color: white;
          gap: 8px;

          mat-icon {
            font-size: 48px;
            width: 48px;
            height: 48px;
          }
        }
      }

      .qr-info {
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 12px;

        .info-item {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          background: #f5f5f5;
          border-radius: 4px;

          mat-icon {
            color: #3f51b5;
          }
        }
      }

      .action-buttons {
        display: flex;
        gap: 12px;
        width: 100%;

        button {
          flex: 1;
        }
      }

      .error-state {
        text-align: center;
        padding: 40px 20px;

        mat-icon {
          font-size: 48px;
          width: 48px;
          height: 48px;
        }

        p {
          color: #f44336;
          margin: 16px 0;
        }
      }
    `,
  ],
})
export class QrGeneratorComponent implements OnInit {
  loading = false;
  error: string | null = null;
  qrCodeData: QRCodeData | null = null;
  isExpired = false;
  private countdownTimer: ReturnType<typeof setInterval> | undefined;

  constructor(private snackBar: MatSnackBar) {}

  ngOnInit(): void {
    this.generateQR();
  }

  /**
   * 生成二维码
   */
  generateQR(): void {
    this.loading = true;
    this.error = null;

    // TODO: 调用后端 API 生成二维码
    // 模拟数据
    setTimeout(() => {
      const now = new Date();
      const expiresAt = new Date(now.getTime() + 5 * 60 * 1000); // 5 分钟后过期

      this.qrCodeData = {
        imageUrl: '/assets/placeholder-qr.png', // 实际应从后端获取
        token: 'uuid-token-example',
        expiresAt,
        courseScheduleId: 'course-schedule-id',
      };

      this.loading = false;
      this.startCountdown();
    }, 1000);
  }

  /**
   * 刷新二维码
   */
  refreshQR(): void {
    this.generateQR();
    this.snackBar.open('二维码已刷新', '确定', { duration: 2000 });
  }

  /**
   * 下载二维码
   */
  downloadQR(): void {
    if (!this.qrCodeData) return;

    // TODO: 实现下载功能
    this.snackBar.open('开始下载二维码...', '确定', { duration: 2000 });
  }

  /**
   * 获取剩余时间
   */
  getRemainingTime(): string {
    if (!this.qrCodeData) return '';

    const now = new Date();
    const diff = this.qrCodeData.expiresAt.getTime() - now.getTime();

    if (diff <= 0) {
      this.isExpired = true;
      return '已过期';
    }

    const minutes = Math.floor(diff / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);

    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  /**
   * 开始倒计时
   */
  private startCountdown(): void {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
    }

    this.countdownTimer = setInterval(() => {
      const remaining = this.getRemainingTime();
      if (remaining === '已过期') {
        clearInterval(this.countdownTimer);
        this.snackBar.open('二维码已过期，请刷新', '确定', { duration: 5000 });
      }
    }, 1000);
  }

  ngOnDestroy(): void {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
    }
  }
}
