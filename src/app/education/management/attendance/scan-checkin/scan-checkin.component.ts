/**
 * 扫码签到组件 - 学生端使用
 */

import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';

@Component({
  selector: 'app-scan-checkin',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatSnackBarModule,
    MatProgressBarModule,
    FormsModule,
  ],
  template: `
    <div class="scan-checkin-container">
      <mat-card class="checkin-card">
        <mat-card-header>
          <mat-card-title>课堂签到</mat-card-title>
          <mat-card-subtitle>扫描二维码或手动输入 Token</mat-card-subtitle>
        </mat-card-header>

        <mat-card-content>
          <!-- 扫码区域 -->
          <div class="scan-area" *ngIf="!showManualInput">
            <div class="camera-placeholder">
              <mat-icon>qr_code_scanner</mat-icon>
              <p>请对准二维码进行扫描</p>
              <button mat-raised-button color="primary" (click)="startScanning()">开始扫描</button>
              <button mat-stroked-button (click)="showManualInput = true">手动输入 Token</button>
            </div>
          </div>

          <!-- 手动输入 -->
          <div class="manual-input" *ngIf="showManualInput">
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Token</mat-label>
              <input matInput [(ngModel)]="token" placeholder="请输入二维码中的 Token" />
              <mat-icon matPrefix>fingerprint</mat-icon>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-width">
              <mat-label>学生 ID</mat-label>
              <input matInput [(ngModel)]="studentId" placeholder="请输入您的学号" />
              <mat-icon matPrefix>badge</mat-icon>
            </mat-form-field>

            <div class="action-buttons">
              <button
                mat-flat-button
                color="primary"
                [disabled]="!token || !studentId"
                (click)="submitCheckin()"
              >
                确认签到
              </button>
              <button mat-stroked-button (click)="showManualInput = false">返回扫码</button>
            </div>
          </div>

          <!-- 处理状态 -->
          <div *ngIf="processing" class="processing-state">
            <mat-progress-bar mode="indeterminate"></mat-progress-bar>
            <p>正在处理签到...</p>
          </div>

          <!-- 成功状态 -->
          <div *ngIf="successResult" class="success-state">
            <mat-icon color="accent">check_circle</mat-icon>
            <h3>签到成功!</h3>
            <div class="result-info">
              <p>扣减课时：{{ successResult.deducted_hours }} 课时</p>
              <p>剩余课时：{{ successResult.remaining_hours }} 课时</p>
            </div>
            <button mat-raised-button color="primary" (click)="reset()">完成</button>
          </div>

          <!-- 错误状态 -->
          <div *ngIf="errorMessage" class="error-state">
            <mat-icon color="warn">error</mat-icon>
            <h3>签到失败</h3>
            <p>{{ errorMessage }}</p>
            <button mat-raised-button color="primary" (click)="reset()">重试</button>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [
    `
      .scan-checkin-container {
        padding: 20px;
        max-width: 500px;
        margin: 0 auto;
      }

      .checkin-card {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
      }

      .scan-area {
        text-align: center;
        padding: 40px 20px;
      }

      .camera-placeholder {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 16px;

        mat-icon {
          font-size: 64px;
          width: 64px;
          height: 64px;
          color: #3f51b5;
        }

        button {
          margin-top: 8px;
        }
      }

      .manual-input {
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 16px;

        .full-width {
          width: 100%;
        }

        .action-buttons {
          display: flex;
          gap: 12px;
          margin-top: 16px;

          button {
            flex: 1;
          }
        }
      }

      .processing-state {
        text-align: center;
        padding: 40px 20px;

        p {
          margin-top: 16px;
          color: #666;
        }
      }

      .success-state {
        text-align: center;
        padding: 40px 20px;

        mat-icon {
          font-size: 64px;
          width: 64px;
          height: 64px;
        }

        h3 {
          color: #4caf50;
          margin: 16px 0;
        }

        .result-info {
          background: #f5f5f5;
          padding: 16px;
          border-radius: 4px;
          margin: 16px 0;

          p {
            margin: 8px 0;
          }
        }
      }

      .error-state {
        text-align: center;
        padding: 40px 20px;

        mat-icon {
          font-size: 64px;
          width: 64px;
          height: 64px;
        }

        h3 {
          color: #f44336;
          margin: 16px 0;
        }

        p {
          color: #666;
        }
      }
    `,
  ],
})
export class ScanCheckinComponent implements OnInit {
  showManualInput = false;
  token = '';
  studentId = '';
  processing = false;
  successResult: {
    deducted_hours: number;
    remaining_hours: number;
    student_name: string;
  } | null = null;
  errorMessage: string | null = null;

  constructor(private snackBar: MatSnackBar) {}

  ngOnInit(): void {}

  /**
   * 开始扫描
   */
  startScanning(): void {
    // TODO: 调用摄像头扫描二维码
    this.snackBar.open('模拟扫码成功', '确定', { duration: 2000 });

    // 模拟扫码结果
    setTimeout(() => {
      this.token = 'scanned-token-uuid';
      this.showManualInput = true;
    }, 1000);
  }

  /**
   * 提交签到
   */
  submitCheckin(): void {
    if (!this.token || !this.studentId) return;

    this.processing = true;
    this.errorMessage = null;

    // TODO: 调用后端 API 签到
    setTimeout(() => {
      this.successResult = {
        deducted_hours: 2,
        remaining_hours: 48,
        student_name: '张三',
      };
      this.processing = false;
    }, 1500);
  }

  /**
   * 重置状态
   */
  reset(): void {
    this.token = '';
    this.studentId = '';
    this.showManualInput = false;
    this.successResult = null;
    this.errorMessage = null;
  }
}
